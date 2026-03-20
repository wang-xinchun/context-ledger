from __future__ import annotations

from pathlib import Path

from sqlalchemy import select

from app.core import settings
from app.db.models import AuditLog, Memory, TimelineEvent, Turn
from app.db.repositories import SqlLedgerRepository
from app.db.session import get_session_factory, reset_engine_state
from app.memory.ledger import MemoryLedger


def _sqlite_url(path: Path) -> str:
    return f"sqlite:///{path.as_posix()}"


def test_memory_ledger_dual_writes_to_sql(tmp_path, monkeypatch) -> None:
    db_path = tmp_path / "dual_write.db"
    monkeypatch.setattr(settings, "SQL_DSN", _sqlite_url(db_path))
    reset_engine_state()

    repository = SqlLedgerRepository()
    ledger = MemoryLedger(
        tmp_path / "memory.jsonl",
        sql_write_enabled=True,
        sql_writer=repository,
    )
    ledger.record_chat_turn(
        project_id="proj_sql",
        session_id="sess_sql",
        request_id="req_sql_1",
        user_message="we will choose postgres. next we need to add migration tests.",
        assistant_answer="ok",
        used_input_tokens=23,
    )
    # 相同 request_id 重放应被 SQL 侧幂等保护吞掉，避免重复写入。
    ledger.record_chat_turn(
        project_id="proj_sql",
        session_id="sess_sql",
        request_id="req_sql_1",
        user_message="we will choose postgres. next we need to add migration tests.",
        assistant_answer="ok",
        used_input_tokens=23,
    )

    session_factory = get_session_factory()
    with session_factory() as db:
        turn_rows = db.execute(select(Turn).order_by(Turn.id)).scalars().all()
        memory_rows = db.execute(select(Memory).order_by(Memory.id)).scalars().all()
        timeline_rows = db.execute(select(TimelineEvent).order_by(TimelineEvent.id)).scalars().all()
        audit_rows = db.execute(select(AuditLog).order_by(AuditLog.id)).scalars().all()

    assert len(turn_rows) == 2
    assert len(memory_rows) >= 2
    assert any(item.type == "decision" for item in memory_rows)
    assert any(item.type == "todo" for item in memory_rows)
    assert len(timeline_rows) >= 2
    assert len(audit_rows) == 1

    reset_engine_state()


def test_sql_read_projection_matches_memory_ledger_view(tmp_path, monkeypatch) -> None:
    db_path = tmp_path / "read_projection.db"
    monkeypatch.setattr(settings, "SQL_DSN", _sqlite_url(db_path))
    reset_engine_state()

    repository = SqlLedgerRepository()
    ledger = MemoryLedger(
        tmp_path / "memory.jsonl",
        sql_write_enabled=True,
        sql_writer=repository,
        sql_read_enabled=False,
    )
    project_id = "proj_read_consistency"
    session_id = "sess_read_consistency"

    ledger.record_chat_turn(
        project_id=project_id,
        session_id=session_id,
        request_id="req_1",
        user_message="we will choose postgres as default storage",
        assistant_answer="ok",
        used_input_tokens=13,
    )
    ledger.record_chat_turn(
        project_id=project_id,
        session_id=session_id,
        request_id="req_2",
        user_message="there is risk of migration drift",
        assistant_answer="ok",
        used_input_tokens=11,
    )
    ledger.record_chat_turn(
        project_id=project_id,
        session_id=session_id,
        request_id="req_3",
        user_message="next we need to add timeline endpoint tests",
        assistant_answer="ok",
        used_input_tokens=12,
    )

    expected_resume = ledger.build_resume(project_id)
    sql_resume = repository.build_resume(project_id=project_id)
    assert sql_resume == expected_resume

    expected_page_1 = ledger.build_timeline(project_id, limit=2)
    sql_page_1 = repository.build_timeline(project_id=project_id, limit=2)
    assert sql_page_1 == expected_page_1

    expected_page_2 = ledger.build_timeline(
        project_id,
        limit=2,
        cursor=expected_page_1["next_cursor"],
    )
    sql_page_2 = repository.build_timeline(
        project_id=project_id,
        limit=2,
        cursor=sql_page_1["next_cursor"],
    )
    assert sql_page_2 == expected_page_2

    # Unknown cursor should keep backward-compatible fallback to latest page.
    latest_page = repository.build_timeline(
        project_id=project_id,
        limit=2,
        cursor="unknown_cursor",
    )
    assert latest_page == sql_page_1

    reset_engine_state()


def test_resume_cache_is_invalidated_after_new_write(tmp_path, monkeypatch) -> None:
    db_path = tmp_path / "resume_cache_invalidate.db"
    monkeypatch.setattr(settings, "SQL_DSN", _sqlite_url(db_path))
    reset_engine_state()

    repository = SqlLedgerRepository()
    ledger = MemoryLedger(
        tmp_path / "memory.jsonl",
        sql_write_enabled=True,
        sql_writer=repository,
        sql_read_enabled=False,
    )
    project_id = "proj_resume_cache"
    session_id = "sess_resume_cache"

    ledger.record_chat_turn(
        project_id=project_id,
        session_id=session_id,
        request_id="req_1",
        user_message="we will choose postgres as storage",
        assistant_answer="ok",
        used_input_tokens=9,
    )
    snapshot_1 = repository.build_resume(project_id=project_id)
    # Hit resume cache once.
    snapshot_1_cached = repository.build_resume(project_id=project_id)
    assert snapshot_1_cached == snapshot_1
    assert "Captured 1 turns" in snapshot_1["project_snapshot"]

    ledger.record_chat_turn(
        project_id=project_id,
        session_id=session_id,
        request_id="req_2",
        user_message="next we need to add integration tests",
        assistant_answer="ok",
        used_input_tokens=8,
    )
    snapshot_2 = repository.build_resume(project_id=project_id)
    assert "Captured 2 turns" in snapshot_2["project_snapshot"]
    assert "next we need to add integration tests" in snapshot_2["open_todos"]

    reset_engine_state()


def test_clear_read_caches_keeps_query_result_stable(tmp_path, monkeypatch) -> None:
    db_path = tmp_path / "clear_cache.db"
    monkeypatch.setattr(settings, "SQL_DSN", _sqlite_url(db_path))
    reset_engine_state()

    repository = SqlLedgerRepository()
    ledger = MemoryLedger(
        tmp_path / "memory.jsonl",
        sql_write_enabled=True,
        sql_writer=repository,
        sql_read_enabled=False,
    )
    project_id = "proj_clear_cache"
    session_id = "sess_clear_cache"

    for idx, message in enumerate(
        [
            "we will choose postgres as default storage",
            "there is risk of migration drift",
            "next we need to add timeline endpoint tests",
        ],
        start=1,
    ):
        ledger.record_chat_turn(
            project_id=project_id,
            session_id=session_id,
            request_id=f"req_{idx}",
            user_message=message,
            assistant_answer="ok",
            used_input_tokens=10,
        )

    page_before_clear = repository.build_timeline(project_id=project_id, limit=2)
    repository.clear_read_caches(project_id=project_id)
    page_after_clear = repository.build_timeline(project_id=project_id, limit=2)
    assert page_before_clear == page_after_clear

    reset_engine_state()


def test_timeline_latest_cache_is_invalidated_after_new_write(tmp_path, monkeypatch) -> None:
    db_path = tmp_path / "timeline_latest_cache.db"
    monkeypatch.setattr(settings, "SQL_DSN", _sqlite_url(db_path))
    reset_engine_state()

    repository = SqlLedgerRepository()
    ledger = MemoryLedger(
        tmp_path / "memory.jsonl",
        sql_write_enabled=True,
        sql_writer=repository,
        sql_read_enabled=False,
    )
    project_id = "proj_timeline_latest_cache"
    session_id = "sess_timeline_latest_cache"

    for idx, message in enumerate(
        [
            "we will choose postgres as default storage",
            "there is risk of migration drift",
        ],
        start=1,
    ):
        ledger.record_chat_turn(
            project_id=project_id,
            session_id=session_id,
            request_id=f"req_{idx}",
            user_message=message,
            assistant_answer="ok",
            used_input_tokens=10,
        )

    latest_before = repository.build_timeline(project_id=project_id, limit=2)
    latest_before_cached = repository.build_timeline(project_id=project_id, limit=2)
    assert latest_before_cached == latest_before

    ledger.record_chat_turn(
        project_id=project_id,
        session_id=session_id,
        request_id="req_3",
        user_message="next we need to add timeline cache test",
        assistant_answer="ok",
        used_input_tokens=9,
    )
    latest_after = repository.build_timeline(project_id=project_id, limit=2)

    assert latest_after["items"][0]["type"] == "todo"
    assert latest_after != latest_before

    reset_engine_state()
