"""Repository helpers for staged SQL persistence integration."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from threading import Lock

from sqlalchemy import insert, select
from sqlalchemy.orm import Session, sessionmaker

from app.db.bootstrap import init_db
from app.db.models import AuditLog, ConversationSession, Memory, Project, TimelineEvent, Turn
from app.db.session import get_session_factory

TIMELINE_EVENT_TYPES = frozenset({"decision", "risk", "todo"})


def _parse_iso_timestamp(value: str) -> datetime:
    try:
        return datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return datetime.now(tz=timezone.utc)


def _score_to_importance(score: float) -> int:
    return max(1, min(5, int(round(score * 5))))


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
            # 先落库 project，确保后续 session 外键可用。
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
            # 先落库 session，确保 turn 外键在 Core insert 路径下可用。
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

        with self._session_factory() as db:
            with db.begin():
                existing_turn_id = db.execute(
                    select(Turn.id).where(Turn.request_id == request_id).limit(1)
                ).scalar_one_or_none()
                if existing_turn_id is not None:
                    return

                self._ensure_project(db, project_id)
                self._ensure_session(db, project_id, session_id)

                # 批量 insert 比逐个 ORM add 更省内存且执行开销更低。
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
