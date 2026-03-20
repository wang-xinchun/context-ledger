from __future__ import annotations

from app.memory.ledger import MAX_MEMORIES_PER_TURN, MAX_TODOS_PER_PROJECT, MemoryLedger, _extract_memory_contents


def test_extract_memory_contents_is_bounded_and_stable() -> None:
    text = (
        "we will choose postgres as default storage. "
        "next we need to add timeline tests. "
        "there is risk of migration drift. "
        "this extra sentence should be truncated by limit."
    )
    items = _extract_memory_contents(text)
    assert len(items) == MAX_MEMORIES_PER_TURN
    assert items[0][0] in {"decision", "todo", "risk", "constraint", "fact"}


def test_todo_set_keeps_in_sync_with_deque_window(tmp_path) -> None:
    ledger = MemoryLedger(tmp_path / "memory.jsonl")
    project_id = "proj_todo_window"

    for idx in range(MAX_TODOS_PER_PROJECT + 5):
        ledger.record_chat_turn(
            project_id=project_id,
            session_id="sess_1",
            request_id=f"req_{idx}",
            user_message=f"next todo item {idx}",
            assistant_answer="ok",
            used_input_tokens=1,
        )

    state = ledger._projects[project_id]
    assert len(state.todos) == MAX_TODOS_PER_PROJECT
    assert len(state.todo_set) == MAX_TODOS_PER_PROJECT

    # After window eviction, the previously dropped todo should be re-addable.
    ledger.record_chat_turn(
        project_id=project_id,
        session_id="sess_1",
        request_id="req_readd",
        user_message="next todo item 0",
        assistant_answer="ok",
        used_input_tokens=1,
    )
    assert "next todo item 0" in state.todos


def test_build_timeline_cursor_and_limit(tmp_path) -> None:
    ledger = MemoryLedger(tmp_path / "memory.jsonl")
    project_id = "proj_timeline_unit"

    ledger.record_chat_turn(
        project_id=project_id,
        session_id="sess_1",
        request_id="req_1",
        user_message="we will choose postgres",
        assistant_answer="ok",
        used_input_tokens=1,
    )
    ledger.record_chat_turn(
        project_id=project_id,
        session_id="sess_1",
        request_id="req_2",
        user_message="there is risk of migration drift",
        assistant_answer="ok",
        used_input_tokens=1,
    )
    ledger.record_chat_turn(
        project_id=project_id,
        session_id="sess_1",
        request_id="req_3",
        user_message="next we need to add timeline tests",
        assistant_answer="ok",
        used_input_tokens=1,
    )

    page_1 = ledger.build_timeline(project_id, limit=2)
    assert len(page_1["items"]) == 2
    assert page_1["items"][0]["type"] == "todo"
    assert page_1["items"][1]["type"] == "risk"
    assert page_1["next_cursor"] == page_1["items"][-1]["id"]

    page_2 = ledger.build_timeline(project_id, limit=2, cursor=page_1["next_cursor"])
    assert len(page_2["items"]) == 1
    assert page_2["items"][0]["type"] == "decision"
    assert page_2["next_cursor"] is None


def test_build_timeline_skips_fact_events_for_space_efficiency(tmp_path) -> None:
    ledger = MemoryLedger(tmp_path / "memory.jsonl")
    project_id = "proj_timeline_fact"

    ledger.record_chat_turn(
        project_id=project_id,
        session_id="sess_1",
        request_id="req_1",
        user_message="team sync completed and artifacts were archived successfully",
        assistant_answer="ok",
        used_input_tokens=1,
    )

    page = ledger.build_timeline(project_id, limit=10)
    assert page["items"] == []
    assert page["next_cursor"] is None


def test_sql_read_failure_falls_back_to_memory_view(tmp_path) -> None:
    class FailingReader:
        def build_resume(self, *, project_id: str) -> dict[str, object]:
            raise RuntimeError("sql read down")

        def build_timeline(
            self,
            *,
            project_id: str,
            limit: int = 20,
            cursor: str | None = None,
        ) -> dict[str, object]:
            raise RuntimeError("sql read down")

    ledger = MemoryLedger(
        tmp_path / "memory.jsonl",
        sql_read_enabled=True,
        sql_reader=FailingReader(),
    )
    project_id = "proj_sql_fallback"
    ledger.record_chat_turn(
        project_id=project_id,
        session_id="sess_1",
        request_id="req_1",
        user_message="we will choose postgres",
        assistant_answer="ok",
        used_input_tokens=1,
    )

    resume = ledger.build_resume(project_id)
    timeline = ledger.build_timeline(project_id, limit=5)

    assert "Captured 1 turns" in resume["project_snapshot"]
    assert len(timeline["items"]) == 1
    assert timeline["items"][0]["type"] == "decision"
