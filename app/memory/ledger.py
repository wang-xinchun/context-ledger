"""In-process memory ledger with lightweight JSONL persistence."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from itertools import islice
import json
from pathlib import Path
import re
from threading import Lock
import time
from typing import TYPE_CHECKING, Protocol
from uuid import uuid4

from app.api.v1.schemas import UsedMemory
from app.core import settings

if TYPE_CHECKING:
    from app.db.repositories import PersistedMemoryRecord

MAX_MEMORIES_PER_TURN = 3
MAX_DECISIONS_PER_PROJECT = 30
MAX_TODOS_PER_PROJECT = 50
MAX_TIMELINE_EVENTS_PER_PROJECT = 200
STATE_LOCK_STRIPES = 64
MEMORY_EXTRACTION_CHAR_LIMIT = 4096

MEMORY_TYPE_PATTERN = re.compile(
    r"(?P<todo>\b(?:todo|next|need(?:\s+to)?|follow[-\s]?up)\b|\u5f85\u529e|\u4e0b\u4e00\u6b65|\u540e\u7eed|\u9700\u8981)"
    r"|(?P<decision>\b(?:decision|decide|decided|choose|chosen|we\s+will)\b|\u51b3\u5b9a|\u51b3\u7b56|\u91c7\u7528|\u9009\u62e9)"
    r"|(?P<risk>\b(?:risk|blocked|blocker|issue|problem)\b|\u98ce\u9669|\u963b\u585e|\u95ee\u9898)"
    r"|(?P<constraint>\b(?:constraint|must|cannot|can't|should\s+not)\b|\u5fc5\u987b|\u4e0d\u80fd|\u9650\u5236)",
    re.IGNORECASE,
)
SENTENCE_SPLIT_RE = re.compile(r"[.!?;\n\u3002\uff01\uff1f\uff1b]+")

TYPE_SCORE = {
    "decision": 0.88,
    "todo": 0.85,
    "risk": 0.9,
    "constraint": 0.82,
    "fact": 0.75,
}
TIMELINE_MEMORY_TYPES = frozenset({"decision", "risk", "todo"})


@dataclass(frozen=True, slots=True)
class TimelineEvent:
    seq: int
    id: str
    type: str
    content: str
    timestamp: str


@dataclass(slots=True)
class ProjectState:
    turn_count: int = 0
    last_session_id: str = ""
    last_user_message: str = ""
    last_assistant_answer: str = ""
    decisions: deque[str] = field(default_factory=lambda: deque(maxlen=MAX_DECISIONS_PER_PROJECT))
    todos: deque[str] = field(default_factory=lambda: deque(maxlen=MAX_TODOS_PER_PROJECT))
    todo_set: set[str] = field(default_factory=set)
    timeline_events: deque[TimelineEvent] = field(default_factory=deque)
    timeline_id_to_seq: dict[str, int] = field(default_factory=dict)
    timeline_next_seq: int = 0


class SqlWriter(Protocol):
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
        memory_records: list["PersistedMemoryRecord"],
        created_at: str,
    ) -> None: ...


class SqlReader(Protocol):
    def build_resume(self, *, project_id: str) -> dict[str, object]: ...

    def build_timeline(
        self,
        *,
        project_id: str,
        limit: int = 20,
        cursor: str | None = None,
    ) -> dict[str, object]: ...


def _now_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def _trim_text(text: str, limit: int = 120) -> str:
    compact = " ".join(text.strip().split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3] + "..."


def _classify_memory_type(sentence: str) -> str:
    match = MEMORY_TYPE_PATTERN.search(sentence)
    if match is None or match.lastgroup is None:
        return "fact"
    return match.lastgroup


def _iter_sentences(text: str):
    """
    流式切句：避免先 split 生成整段列表，
    对长输入可减少峰值内存并支持提前终止。
    """
    start = 0
    for split_match in SENTENCE_SPLIT_RE.finditer(text):
        fragment = text[start : split_match.start()]
        start = split_match.end()
        sentence = _trim_text(fragment)
        if sentence:
            yield sentence

    tail = _trim_text(text[start:])
    if tail:
        yield tail


def _extract_memory_contents(text: str) -> list[tuple[str, str]]:
    """
    提取候选 memory（type, content）。
    M1 采用轻量规则引擎，保证路径可控且易于回归验证。
    """
    if len(text) > MEMORY_EXTRACTION_CHAR_LIMIT:
        text = text[:MEMORY_EXTRACTION_CHAR_LIMIT]

    extracted: list[tuple[str, str]] = []
    seen: set[str] = set()

    for sentence in _iter_sentences(text):
        if len(sentence) < 8:
            continue

        memory_type = _classify_memory_type(sentence)
        key = f"{memory_type}:{sentence.casefold()}"
        if key in seen:
            continue

        seen.add(key)
        extracted.append((memory_type, sentence))
        if len(extracted) >= MAX_MEMORIES_PER_TURN:
            break

    return extracted


def _tail_items(items: deque[str], limit: int) -> list[str]:
    if limit <= 0:
        return []
    # 只取尾部窗口，避免 list(deque) 后再切片带来的整段复制。
    tail = list(islice(reversed(items), limit))
    tail.reverse()
    return tail


class MemoryLedger:
    def __init__(
        self,
        path: Path,
        *,
        sql_write_enabled: bool = False,
        sql_read_enabled: bool = False,
        sql_writer: SqlWriter | None = None,
        sql_reader: SqlReader | None = None,
    ) -> None:
        self._path = path
        self._load_lock = Lock()
        self._projects_lock = Lock()
        self._state_locks = tuple(Lock() for _ in range(STATE_LOCK_STRIPES))
        self._file_lock = Lock()
        self._loaded = False
        self._projects: dict[str, ProjectState] = {}
        self._path_dir_ready = path.parent.exists()
        self._sql_write_enabled = sql_write_enabled
        self._sql_read_enabled = sql_read_enabled
        self._sql_record_factory = None
        self._sql_writer = sql_writer or self._build_sql_writer(sql_write_enabled)
        self._sql_reader = sql_reader or self._build_sql_reader(
            sql_read_enabled,
            prefer=self._sql_writer,
        )
        self._sql_write_gate = Lock() if settings.SQL_WRITE_BACKPRESSURE_ENABLED else None
        self._sql_retry_queue: deque[dict[str, object]] = deque()
        self._sql_retry_lock = Lock()
        self._sql_skipped_writes = 0
        self._sql_enqueued_writes = 0
        self._sql_dropped_writes = 0
        self._sql_replayed_writes = 0
        self._sql_replay_failed_writes = 0
        self._sql_direct_failed_writes = 0
        if self._sql_writer is not None and self._sql_record_factory is None:
            try:
                from app.db.repositories import PersistedMemoryRecord

                self._sql_record_factory = PersistedMemoryRecord
            except Exception:
                self._sql_record_factory = None

    def _build_sql_writer(self, enabled: bool) -> SqlWriter | None:
        if not enabled:
            return None

        try:
            from app.db.repositories import PersistedMemoryRecord, SqlLedgerRepository

            self._sql_record_factory = PersistedMemoryRecord
            return SqlLedgerRepository()
        except Exception:
            # SQL 双写故障不应阻断主链路，初始化失败时自动降级。
            return None

    def _build_sql_reader(self, enabled: bool, prefer: object | None = None) -> SqlReader | None:
        if not enabled:
            return None

        if prefer is not None and hasattr(prefer, "build_resume") and hasattr(prefer, "build_timeline"):
            return prefer  # type: ignore[return-value]

        try:
            from app.db.repositories import SqlLedgerRepository

            return SqlLedgerRepository()
        except Exception:
            # SQL 读路径故障不应阻断主链路，初始化失败时自动降级。
            return None

    def _read_resume_from_sql(self, project_id: str) -> dict[str, object] | None:
        if not self._sql_read_enabled or self._sql_reader is None:
            return None
        try:
            return self._sql_reader.build_resume(project_id=project_id)
        except Exception:
            return None

    def _read_timeline_from_sql(
        self,
        project_id: str,
        *,
        limit: int = 20,
        cursor: str | None = None,
    ) -> dict[str, object] | None:
        if not self._sql_read_enabled or self._sql_reader is None:
            return None
        try:
            return self._sql_reader.build_timeline(
                project_id=project_id,
                limit=limit,
                cursor=cursor,
            )
        except Exception:
            return None

    def reset(self, clear_file: bool = False) -> None:
        with self._load_lock:
            acquired: list[Lock] = []
            try:
                for lock in self._state_locks:
                    lock.acquire()
                    acquired.append(lock)
                with self._projects_lock:
                    self._projects.clear()
                self._loaded = True
            finally:
                while acquired:
                    acquired.pop().release()
        if clear_file:
            with self._file_lock:
                if self._path.exists():
                    self._path.unlink()

    def _state_lock_for_project(self, project_id: str) -> Lock:
        return self._state_locks[hash(project_id) % STATE_LOCK_STRIPES]

    def _persist_sql_payload(self, payload: dict[str, object]) -> bool:
        writer = self._sql_writer
        if writer is None:
            return False
        try:
            writer.persist_chat_turn(
                project_id=str(payload["project_id"]),
                session_id=str(payload["session_id"]),
                request_id=str(payload["request_id"]),
                user_message=str(payload["user_message"]),
                assistant_answer=str(payload["assistant_answer"]),
                used_input_tokens=int(payload["used_input_tokens"]),
                provider_name=str(payload["provider_name"]),
                memory_records=payload["memory_records"],  # type: ignore[arg-type]
                created_at=str(payload["created_at"]),
            )
            return True
        except Exception:
            return False

    def _enqueue_sql_retry_payload(self, payload: dict[str, object]) -> None:
        max_queue = max(0, int(settings.SQL_WRITE_RETRY_QUEUE_MAX))
        with self._sql_retry_lock:
            self._sql_skipped_writes += 1
            if max_queue <= 0:
                self._sql_dropped_writes += 1
                return
            if len(self._sql_retry_queue) >= max_queue:
                self._sql_retry_queue.popleft()
                self._sql_dropped_writes += 1
            self._sql_retry_queue.append(payload)
            self._sql_enqueued_writes += 1

    def _pop_sql_retry_payload(self) -> dict[str, object] | None:
        with self._sql_retry_lock:
            if not self._sql_retry_queue:
                return None
            return self._sql_retry_queue.popleft()

    def _drain_sql_retry_queue(self) -> None:
        max_batch = max(0, int(settings.SQL_WRITE_RETRY_DRAIN_BATCH))
        if max_batch <= 0:
            return

        budget_ms = max(0.0, float(settings.SQL_WRITE_RETRY_DRAIN_BUDGET_MS))
        if budget_ms <= 0:
            return
        budget_ns = int(budget_ms * 1_000_000)
        started_ns = time.perf_counter_ns()

        drained = 0
        while drained < max_batch:
            if time.perf_counter_ns() - started_ns >= budget_ns:
                break

            payload = self._pop_sql_retry_payload()
            if payload is None:
                break

            if self._persist_sql_payload(payload):
                with self._sql_retry_lock:
                    self._sql_replayed_writes += 1
            else:
                with self._sql_retry_lock:
                    self._sql_replay_failed_writes += 1
            drained += 1

    def sql_write_backpressure_stats(self) -> dict[str, int | bool]:
        with self._sql_retry_lock:
            return {
                "enabled": self._sql_write_gate is not None,
                "pending_queue_size": len(self._sql_retry_queue),
                "skipped_writes": self._sql_skipped_writes,
                "enqueued_writes": self._sql_enqueued_writes,
                "dropped_writes": self._sql_dropped_writes,
                "replayed_writes": self._sql_replayed_writes,
                "replay_failed_writes": self._sql_replay_failed_writes,
                "direct_failed_writes": self._sql_direct_failed_writes,
            }

    def _ensure_loaded(self) -> None:
        if self._loaded:
            return

        with self._load_lock:
            if self._loaded:
                return

            if self._path.exists():
                with self._path.open("r", encoding="utf-8", errors="replace") as handle:
                    for line in handle:
                        if not line.strip():
                            continue
                        try:
                            record = json.loads(line)
                        except json.JSONDecodeError:
                            continue
                        self._apply_record(record)

            self._loaded = True

    def _append_turn_and_memories(
        self,
        turn_record: dict[str, object],
        memory_records: list[dict[str, object]],
    ) -> None:
        serialized_lines = [json.dumps(turn_record, ensure_ascii=False), "\n"]
        if memory_records:
            for record in memory_records:
                serialized_lines.append(json.dumps(record, ensure_ascii=False))
                serialized_lines.append("\n")

        with self._file_lock:
            if not self._path_dir_ready:
                self._path.parent.mkdir(parents=True, exist_ok=True)
                self._path_dir_ready = True

            with self._path.open("a", encoding="utf-8") as handle:
                handle.write("".join(serialized_lines))

    def _state(self, project_id: str) -> ProjectState:
        with self._projects_lock:
            state = self._projects.get(project_id)
            if state is None:
                state = ProjectState()
                self._projects[project_id] = state
            return state

    def _get_state(self, project_id: str) -> ProjectState | None:
        with self._projects_lock:
            return self._projects.get(project_id)

    def _append_todo(self, state: ProjectState, content: str) -> None:
        key = content.casefold()
        if key in state.todo_set:
            return

        # 与 deque 保持严格一致，避免 todo_set 无限增长影响查找与重入。
        if len(state.todos) == MAX_TODOS_PER_PROJECT:
            evicted = state.todos.popleft()
            state.todo_set.discard(evicted.casefold())

        state.todos.append(content)
        state.todo_set.add(key)

    def _append_timeline_event(
        self,
        state: ProjectState,
        *,
        event_id: str,
        memory_type: str,
        content: str,
        timestamp: str,
    ) -> None:
        # 手动维护窗口和索引映射，确保分页定位为 O(1)。
        if len(state.timeline_events) == MAX_TIMELINE_EVENTS_PER_PROJECT:
            evicted = state.timeline_events.popleft()
            state.timeline_id_to_seq.pop(evicted.id, None)

        seq = state.timeline_next_seq
        state.timeline_next_seq = seq + 1
        state.timeline_events.append(
            TimelineEvent(
                seq=seq,
                id=event_id,
                type=memory_type,
                content=content,
                timestamp=timestamp,
            )
        )
        state.timeline_id_to_seq[event_id] = seq

    def _apply_record(self, record: dict[str, object]) -> None:
        kind = record.get("kind")
        project_id = str(record.get("project_id", ""))
        if not project_id:
            return

        state = self._state(project_id)
        self._apply_record_to_state(state, record)

    def _apply_record_to_state(self, state: ProjectState, record: dict[str, object]) -> None:
        kind = record.get("kind")

        if kind == "turn":
            state.turn_count += 1
            state.last_session_id = str(record.get("session_id", ""))
            state.last_user_message = str(record.get("user_message", ""))
            state.last_assistant_answer = str(record.get("assistant_answer", ""))
            return

        if kind != "memory":
            return

        content = str(record.get("content", "")).strip()
        if not content:
            return

        memory_type = str(record.get("type", "fact"))
        if memory_type == "decision":
            state.decisions.append(content)
        elif memory_type == "todo":
            self._append_todo(state, content)

        if memory_type in TIMELINE_MEMORY_TYPES:
            event_id = str(record.get("memory_id", "")).strip()
            if not event_id:
                event_id = f"evt_{uuid4().hex[:12]}"
            timestamp = str(record.get("created_at", "")).strip() or _now_iso()
            self._append_timeline_event(
                state,
                event_id=event_id,
                memory_type=memory_type,
                content=content,
                timestamp=timestamp,
            )

    def record_chat_turn(
        self,
        *,
        project_id: str,
        session_id: str,
        request_id: str,
        user_message: str,
        assistant_answer: str,
        used_input_tokens: int,
        return_used_memories: bool = True,
    ) -> list[UsedMemory]:
        self._ensure_loaded()
        created_at = _now_iso()
        source_ref = f"{session_id}:{request_id}"

        turn_record = {
            "kind": "turn",
            "project_id": project_id,
            "session_id": session_id,
            "request_id": request_id,
            "user_message": user_message,
            "assistant_answer": assistant_answer,
            "used_input_tokens": used_input_tokens,
            "created_at": created_at,
        }

        extracted = _extract_memory_contents(user_message)
        memories: list[UsedMemory] = []
        append_memory = memories.append
        memory_records: list[dict[str, object]] = []
        sql_memory_records: list["PersistedMemoryRecord"] = []
        sql_record_factory = self._sql_record_factory
        for index, (memory_type, content) in enumerate(extracted):
            memory_id = f"mem_{request_id}_{index}"
            score = TYPE_SCORE.get(memory_type, TYPE_SCORE["fact"])
            if return_used_memories:
                append_memory(
                    UsedMemory(
                        memory_id=memory_id,
                        type=memory_type,
                        score=score,
                        source_ref=source_ref,
                    )
                )
            memory_records.append(
                {
                    "kind": "memory",
                    "project_id": project_id,
                    "session_id": session_id,
                    "request_id": request_id,
                    "memory_id": memory_id,
                    "type": memory_type,
                    "content": content,
                    "score": score,
                    "source_ref": source_ref,
                    "created_at": created_at,
                }
            )

            if sql_record_factory is not None:
                sql_memory_records.append(
                    sql_record_factory(
                        memory_id=memory_id,
                        memory_type=memory_type,
                        content=content,
                        score=score,
                        source_ref=source_ref,
                    )
                )

        state_lock = self._state_lock_for_project(project_id)
        with state_lock:
            state = self._state(project_id)
            self._apply_record_to_state(state, turn_record)
            for item in memory_records:
                self._apply_record_to_state(state, item)
        self._append_turn_and_memories(turn_record, memory_records)

        if self._sql_writer is not None:
            sql_payload: dict[str, object] = {
                "project_id": project_id,
                "session_id": session_id,
                "request_id": request_id,
                "user_message": user_message,
                "assistant_answer": assistant_answer,
                "used_input_tokens": used_input_tokens,
                "provider_name": settings.DEFAULT_CHAT_PROVIDER,
                "memory_records": sql_memory_records,
                "created_at": created_at,
            }
            gate = self._sql_write_gate
            acquired = False
            if gate is None:
                acquired = True
            else:
                acquire_timeout = max(0.0, float(settings.SQL_WRITE_LOCK_ACQUIRE_TIMEOUT_SECONDS))
                acquired = gate.acquire(timeout=acquire_timeout)

            if acquired:
                try:
                    if not self._persist_sql_payload(sql_payload):
                        with self._sql_retry_lock:
                            self._sql_direct_failed_writes += 1
                    self._drain_sql_retry_queue()
                finally:
                    if gate is not None:
                        gate.release()
            else:
                self._enqueue_sql_retry_payload(sql_payload)

        return memories

    def build_resume(self, project_id: str) -> dict[str, object]:
        sql_snapshot = self._read_resume_from_sql(project_id)
        if sql_snapshot is not None:
            return sql_snapshot

        self._ensure_loaded()
        state_lock = self._state_lock_for_project(project_id)
        with state_lock:
            state = self._get_state(project_id)
            if state is None or state.turn_count == 0:
                return {
                    "project_snapshot": "No conversation history is available for this project yet.",
                    "recent_decisions": [],
                    "open_todos": [],
                }

            user_hint = _trim_text(state.last_user_message, limit=100)
            assistant_hint = _trim_text(state.last_assistant_answer, limit=100)
            snapshot = (
                f"Captured {state.turn_count} turns. "
                f"Latest user intent: {user_hint}. "
                f"Latest assistant response: {assistant_hint}."
            )
            return {
                "project_snapshot": snapshot,
                "recent_decisions": _tail_items(state.decisions, 5),
                "open_todos": _tail_items(state.todos, 10),
            }

    def build_timeline(
        self,
        project_id: str,
        *,
        limit: int = 20,
        cursor: str | None = None,
    ) -> dict[str, object]:
        sql_timeline = self._read_timeline_from_sql(
            project_id,
            limit=limit,
            cursor=cursor,
        )
        if sql_timeline is not None:
            return sql_timeline

        self._ensure_loaded()
        safe_limit = max(1, min(limit, 100))

        state_lock = self._state_lock_for_project(project_id)
        with state_lock:
            state = self._get_state(project_id)
            if state is None or not state.timeline_events:
                return {"items": [], "next_cursor": None}

            events = state.timeline_events
            oldest_seq = events[0].seq
            newest_seq = events[-1].seq

            end_seq_exclusive = state.timeline_next_seq
            if cursor:
                cursor_seq = state.timeline_id_to_seq.get(cursor)
                if cursor_seq is not None:
                    end_seq_exclusive = cursor_seq

            start_seq = min(end_seq_exclusive - 1, newest_seq)
            if start_seq < oldest_seq:
                return {"items": [], "next_cursor": None}

            # 基于 seq 计算偏移，只做一次反向切片，避免“先找游标再二次遍历”。
            offset_from_newest = newest_seq - start_seq
            selected = list(
                islice(
                    reversed(events),
                    offset_from_newest,
                    offset_from_newest + safe_limit + 1,
                )
            )
            has_more = len(selected) > safe_limit
            if has_more:
                selected.pop()

            items: list[dict[str, str]] = []
            append_item = items.append
            for event in selected:
                # 仅在返回阶段投影为 dict，减少中间层对象复制。
                append_item(
                    {
                        "id": event.id,
                        "type": event.type,
                        "content": event.content,
                        "timestamp": event.timestamp,
                    }
                )

            next_cursor = items[-1]["id"] if has_more and items else None
            return {"items": items, "next_cursor": next_cursor}


ledger = MemoryLedger(
    Path(settings.MEMORY_LEDGER_PATH),
    sql_write_enabled=settings.SQL_WRITE_ENABLED,
    sql_read_enabled=settings.SQL_READ_ENABLED,
)
