"""Repository helpers for staged SQL persistence integration."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from threading import Lock

from sqlalchemy import and_, func, insert, or_, select
from sqlalchemy.orm import Session, sessionmaker

from app.db.bootstrap import init_db
from app.db.models import AuditLog, ConversationSession, Memory, Project, TimelineEvent, Turn
from app.db.session import get_session_factory

TIMELINE_EVENT_TYPES = frozenset({"decision", "risk", "todo"})
MAX_DECISIONS_FOR_RESUME = 5
MAX_TODOS_FOR_RESUME = 10
MAX_TODO_WINDOW = 50
MAX_RESUME_CACHE_PROJECTS = 256
MAX_TIMELINE_CURSOR_CACHE_PER_PROJECT = 512


def _parse_iso_timestamp(value: str) -> datetime:
    try:
        return datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return datetime.now(tz=timezone.utc)


def _score_to_importance(score: float) -> int:
    return max(1, min(5, int(round(score * 5))))


def _trim_text(text: str, limit: int = 100) -> str:
    compact = " ".join(text.strip().split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3] + "..."


def _to_iso(dt_value: datetime) -> str:
    if dt_value.tzinfo is None:
        return dt_value.replace(tzinfo=timezone.utc).isoformat()
    return dt_value.isoformat()


@dataclass(frozen=True, slots=True)
class PersistedMemoryRecord:
    memory_id: str
    memory_type: str
    content: str
    score: float
    source_ref: str


class SqlLedgerRepository:
    def __init__(self, *, session_factory: sessionmaker[Session] | None = None) -> None:
        init_db()
        self._session_factory = session_factory or get_session_factory()
        self._cache_lock = Lock()
        self._known_projects: set[str] = set()
        self._known_sessions: set[tuple[str, str]] = set()
        # 读路径缓存：按项目缓存最新 resume 结果，避免重复聚合。
        self._resume_cache: dict[str, tuple[str, str, tuple[str, ...], tuple[str, ...]]] = {}
        # 游标定位缓存：减少 timeline 分页时重复的“游标反查”查询。
        self._timeline_cursor_cache: dict[str, dict[str, tuple[datetime, str]]] = {}

    def _invalidate_project_read_caches(self, project_id: str) -> None:
        # 写入成功后失效该项目读缓存，保证后续读取不返回旧快照。
        with self._cache_lock:
            self._resume_cache.pop(project_id, None)
            self._timeline_cursor_cache.pop(project_id, None)

    def _get_resume_cache(
        self,
        project_id: str,
        latest_request_id: str,
    ) -> dict[str, object] | None:
        with self._cache_lock:
            cached = self._resume_cache.get(project_id)
            if cached is None:
                return None
            marker, snapshot, decisions, todos = cached
            if marker != latest_request_id:
                return None

            return {
                "project_snapshot": snapshot,
                "recent_decisions": list(decisions),
                "open_todos": list(todos),
            }

    def _set_resume_cache(
        self,
        *,
        project_id: str,
        latest_request_id: str,
        snapshot: str,
        recent_decisions: list[str],
        open_todos: list[str],
    ) -> None:
        with self._cache_lock:
            if project_id not in self._resume_cache and len(self._resume_cache) >= MAX_RESUME_CACHE_PROJECTS:
                self._resume_cache.pop(next(iter(self._resume_cache)), None)
            self._resume_cache[project_id] = (
                latest_request_id,
                snapshot,
                tuple(recent_decisions),
                tuple(open_todos),
            )

    def _get_timeline_cursor_position(
        self,
        *,
        project_id: str,
        cursor: str,
    ) -> tuple[datetime, str] | None:
        with self._cache_lock:
            project_cache = self._timeline_cursor_cache.get(project_id)
            if project_cache is None:
                return None
            return project_cache.get(cursor)

    def _cache_timeline_cursor_positions(
        self,
        *,
        project_id: str,
        positions: list[tuple[str, datetime, str]],
    ) -> None:
        if not positions:
            return

        with self._cache_lock:
            project_cache = self._timeline_cursor_cache.get(project_id)
            if project_cache is None:
                project_cache = {}
                self._timeline_cursor_cache[project_id] = project_cache

            for cursor_id, created_at, sort_key in positions:
                if cursor_id not in project_cache and (
                    len(project_cache) >= MAX_TIMELINE_CURSOR_CACHE_PER_PROJECT
                ):
                    project_cache.pop(next(iter(project_cache)), None)
                project_cache[cursor_id] = (created_at, sort_key)

    def _mark_project_known(self, project_id: str) -> None:
        with self._cache_lock:
            self._known_projects.add(project_id)

    def _mark_session_known(self, project_id: str, session_id: str) -> None:
        with self._cache_lock:
            self._known_sessions.add((project_id, session_id))

    def _project_known(self, project_id: str) -> bool:
        with self._cache_lock:
            return project_id in self._known_projects

    def _session_known(self, project_id: str, session_id: str) -> bool:
        with self._cache_lock:
            return (project_id, session_id) in self._known_sessions

    def _ensure_project(self, db: Session, project_id: str) -> None:
        if self._project_known(project_id):
            return

        exists = db.get(Project, project_id)
        if exists is None:
            db.add(
                Project(
                    id=project_id,
                    name=project_id,
                    description="",
                )
            )
            # Flush before session insert to satisfy FK constraints.
            db.flush()

        self._mark_project_known(project_id)

    def _ensure_session(self, db: Session, project_id: str, session_id: str) -> None:
        if self._session_known(project_id, session_id):
            return

        exists = db.execute(
            select(ConversationSession.id)
            .where(
                ConversationSession.id == session_id,
                ConversationSession.project_id == project_id,
            )
            .limit(1)
        ).scalar_one_or_none()
        if exists is None:
            db.add(
                ConversationSession(
                    id=session_id,
                    project_id=project_id,
                    title="",
                    schema_version="v1",
                )
            )
            # Flush before turn insert to satisfy FK constraints.
            db.flush()

        self._mark_session_known(project_id, session_id)

    def persist_chat_turn(
        self,
        *,
        project_id: str,
        session_id: str,
        request_id: str,
        user_message: str,
        assistant_answer: str,
        used_input_tokens: int,
        provider_name: str,
        memory_records: list[PersistedMemoryRecord],
        created_at: str,
    ) -> None:
        created_at_dt = _parse_iso_timestamp(created_at)
        assistant_request_id = f"{request_id}:assistant"
        did_write = False

        with self._session_factory() as db:
            with db.begin():
                existing_turn_id = db.execute(
                    select(Turn.id).where(Turn.request_id == request_id).limit(1)
                ).scalar_one_or_none()
                if existing_turn_id is not None:
                    return

                self._ensure_project(db, project_id)
                self._ensure_session(db, project_id, session_id)

                # Batched Core insert keeps write path lightweight.
                user_turn_id = db.execute(
                    insert(Turn).returning(Turn.id),
                    {
                        "project_id": project_id,
                        "session_id": session_id,
                        "role": "user",
                        "content": user_message,
                        "token_count": used_input_tokens,
                        "request_id": request_id,
                        "created_at": created_at_dt,
                    },
                ).scalar_one()

                db.execute(
                    insert(Turn),
                    {
                        "project_id": project_id,
                        "session_id": session_id,
                        "role": "assistant",
                        "content": assistant_answer,
                        "token_count": 0,
                        "request_id": assistant_request_id,
                        "created_at": created_at_dt,
                    },
                )

                memory_rows: list[dict[str, object]] = []
                timeline_rows: list[dict[str, object]] = []
                append_memory_row = memory_rows.append
                append_timeline_row = timeline_rows.append
                for item in memory_records:
                    append_memory_row(
                        {
                            "id": item.memory_id,
                            "project_id": project_id,
                            "session_id": session_id,
                            "turn_id": user_turn_id,
                            "type": item.memory_type,
                            "content": item.content,
                            "importance": _score_to_importance(item.score),
                            "source_ref": item.source_ref,
                            "schema_version": "v1",
                            "created_at": created_at_dt,
                        }
                    )

                    if item.memory_type in TIMELINE_EVENT_TYPES:
                        append_timeline_row(
                            {
                                "id": f"evt_{item.memory_id}",
                                "project_id": project_id,
                                "memory_id": item.memory_id,
                                "event_type": item.memory_type,
                                "content": item.content,
                                "created_at": created_at_dt,
                            }
                        )

                if memory_rows:
                    db.execute(insert(Memory), memory_rows)
                if timeline_rows:
                    db.execute(insert(TimelineEvent), timeline_rows)

                db.execute(
                    insert(AuditLog),
                    {
                        "project_id": project_id,
                        "session_id": session_id,
                        "request_id": request_id,
                        "provider_name": provider_name,
                        "latency_ms": 0,
                        "continuations": 0,
                        "quality_score": 0.0,
                        "input_tokens": used_input_tokens,
                        "output_tokens": 0,
                        "status": "ok",
                        "created_at": created_at_dt,
                    },
                )
                did_write = True

        if did_write:
            self._invalidate_project_read_caches(project_id)

    def build_resume(self, *, project_id: str) -> dict[str, object]:
        with self._session_factory() as db:
            latest_user_row = db.execute(
                select(Turn.request_id, Turn.content)
                .where(
                    Turn.project_id == project_id,
                    Turn.role == "user",
                )
                .order_by(Turn.created_at.desc(), Turn.id.desc())
                .limit(1)
            ).first()
            if latest_user_row is None:
                return {
                    "project_snapshot": "No conversation history is available for this project yet.",
                    "recent_decisions": [],
                    "open_todos": [],
                }

            cached_resume = self._get_resume_cache(project_id, latest_user_row.request_id)
            if cached_resume is not None:
                # 同一 latest request_id 命中时，直接返回 O(1) 缓存结果。
                return cached_resume

            turn_count = db.execute(
                select(func.count())
                .select_from(Turn)
                .where(
                    Turn.project_id == project_id,
                    Turn.role == "user",
                )
            ).scalar_one()

            latest_user_message = latest_user_row.content
            assistant_request_id = f"{latest_user_row.request_id}:assistant"
            latest_assistant_answer = (
                db.execute(
                    select(Turn.content)
                    .where(Turn.request_id == assistant_request_id)
                    .limit(1)
                ).scalar_one_or_none()
                or ""
            )

            decision_rows = db.execute(
                select(Memory.content)
                .where(
                    Memory.project_id == project_id,
                    Memory.type == "decision",
                )
                .order_by(Memory.created_at.desc(), Memory.id.desc())
                .limit(MAX_DECISIONS_FOR_RESUME)
            ).scalars()
            recent_decisions = list(reversed(list(decision_rows)))

            todos = deque(maxlen=MAX_TODO_WINDOW)
            todo_set: set[str] = set()
            todo_rows = db.execute(
                select(Memory.content)
                .where(
                    Memory.project_id == project_id,
                    Memory.type == "todo",
                )
                .order_by(Memory.created_at.asc(), Memory.id.asc())
            ).scalars()
            for content in todo_rows:
                key = content.casefold()
                if key in todo_set:
                    continue
                if len(todos) == MAX_TODO_WINDOW:
                    evicted = todos.popleft()
                    todo_set.discard(evicted.casefold())
                todos.append(content)
                todo_set.add(key)

            snapshot = (
                f"Captured {turn_count} turns. "
                f"Latest user intent: {_trim_text(latest_user_message, limit=100)}. "
                f"Latest assistant response: {_trim_text(latest_assistant_answer, limit=100)}."
            )
            open_todos = list(todos)[-MAX_TODOS_FOR_RESUME:]
            payload = {
                "project_snapshot": snapshot,
                "recent_decisions": recent_decisions,
                "open_todos": open_todos,
            }
            self._set_resume_cache(
                project_id=project_id,
                latest_request_id=latest_user_row.request_id,
                snapshot=snapshot,
                recent_decisions=recent_decisions,
                open_todos=open_todos,
            )
            return payload

    def build_timeline(
        self,
        *,
        project_id: str,
        limit: int = 20,
        cursor: str | None = None,
    ) -> dict[str, object]:
        safe_limit = max(1, min(limit, 100))
        with self._session_factory() as db:
            cursor_position: tuple[datetime, str] | None = None
            if cursor:
                cached_cursor = self._get_timeline_cursor_position(
                    project_id=project_id,
                    cursor=cursor,
                )
                if cached_cursor is not None:
                    cursor_position = cached_cursor
                else:
                    cursor_row = db.execute(
                        select(
                            TimelineEvent.created_at,
                            TimelineEvent.memory_id,
                            TimelineEvent.id,
                        )
                        .where(
                            TimelineEvent.project_id == project_id,
                            or_(
                                TimelineEvent.memory_id == cursor,
                                TimelineEvent.id == cursor,
                            ),
                        )
                        .limit(1)
                    ).first()
                    if cursor_row is not None:
                        cursor_position = (
                            cursor_row.created_at,
                            cursor_row.memory_id or cursor_row.id,
                        )
                        self._cache_timeline_cursor_positions(
                            project_id=project_id,
                            positions=[
                                (
                                    cursor,
                                    cursor_position[0],
                                    cursor_position[1],
                                )
                            ],
                        )

            timeline_key = func.coalesce(TimelineEvent.memory_id, TimelineEvent.id)
            stmt = (
                select(
                    TimelineEvent.memory_id,
                    TimelineEvent.id,
                    TimelineEvent.event_type,
                    TimelineEvent.content,
                    TimelineEvent.created_at,
                )
                .where(TimelineEvent.project_id == project_id)
                .order_by(TimelineEvent.created_at.desc(), timeline_key.desc())
            )

            if cursor_position is not None:
                cursor_time, cursor_key = cursor_position
                stmt = stmt.where(
                    or_(
                        TimelineEvent.created_at < cursor_time,
                        and_(
                            TimelineEvent.created_at == cursor_time,
                            timeline_key < cursor_key,
                        ),
                    )
                )

            rows = db.execute(stmt.limit(safe_limit + 1)).all()
            if not rows:
                return {"items": [], "next_cursor": None}

            has_more = len(rows) > safe_limit
            selected_rows = rows[:safe_limit]
            self._cache_timeline_cursor_positions(
                project_id=project_id,
                positions=[
                    (row.memory_id or row.id, row.created_at, row.memory_id or row.id)
                    for row in rows
                ],
            )

            items: list[dict[str, str]] = []
            append_item = items.append
            for row in selected_rows:
                event_id = row.memory_id or row.id
                append_item(
                    {
                        "id": event_id,
                        "type": row.event_type,
                        "content": row.content,
                        "timestamp": _to_iso(row.created_at),
                    }
                )

            next_cursor = items[-1]["id"] if has_more and items else None
            return {"items": items, "next_cursor": next_cursor}
