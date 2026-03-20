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
from uuid import uuid4

from app.api.v1.schemas import UsedMemory
from app.core import settings

MAX_MEMORIES_PER_TURN = 3
MAX_DECISIONS_PER_PROJECT = 30
MAX_TODOS_PER_PROJECT = 50

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


@dataclass(slots=True)
class ProjectState:
    turn_count: int = 0
    last_session_id: str = ""
    last_user_message: str = ""
    last_assistant_answer: str = ""
    decisions: deque[str] = field(default_factory=lambda: deque(maxlen=MAX_DECISIONS_PER_PROJECT))
    todos: deque[str] = field(default_factory=lambda: deque(maxlen=MAX_TODOS_PER_PROJECT))
    todo_set: set[str] = field(default_factory=set)


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
    def __init__(self, path: Path) -> None:
        self._path = path
        self._lock = Lock()
        self._loaded = False
        self._projects: dict[str, ProjectState] = {}

    def reset(self, clear_file: bool = False) -> None:
        with self._lock:
            self._projects.clear()
            self._loaded = True
            if clear_file and self._path.exists():
                self._path.unlink()

    def _ensure_loaded(self) -> None:
        if self._loaded:
            return

        with self._lock:
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

    def _append_records(self, records: list[dict[str, object]]) -> None:
        if not records:
            return

        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("a", encoding="utf-8") as handle:
            # 生成器流式写入，减少中间列表分配。
            handle.writelines(json.dumps(record, ensure_ascii=False) + "\n" for record in records)

    def _state(self, project_id: str) -> ProjectState:
        state = self._projects.get(project_id)
        if state is None:
            state = ProjectState()
            self._projects[project_id] = state
        return state

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

    def _apply_record(self, record: dict[str, object]) -> None:
        kind = record.get("kind")
        project_id = str(record.get("project_id", ""))
        if not project_id:
            return

        state = self._state(project_id)

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

    def record_chat_turn(
        self,
        *,
        project_id: str,
        session_id: str,
        request_id: str,
        user_message: str,
        assistant_answer: str,
        used_input_tokens: int,
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
        memory_records: list[dict[str, object]] = []
        for memory_type, content in extracted:
            memory_id = f"mem_{uuid4().hex[:12]}"
            score = TYPE_SCORE.get(memory_type, TYPE_SCORE["fact"])
            memories.append(
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

        with self._lock:
            all_records = [turn_record, *memory_records]
            for item in all_records:
                self._apply_record(item)
            self._append_records(all_records)

        return memories

    def build_resume(self, project_id: str) -> dict[str, object]:
        self._ensure_loaded()
        with self._lock:
            state = self._projects.get(project_id)
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


ledger = MemoryLedger(Path(settings.MEMORY_LEDGER_PATH))
