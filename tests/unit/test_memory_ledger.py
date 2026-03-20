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
