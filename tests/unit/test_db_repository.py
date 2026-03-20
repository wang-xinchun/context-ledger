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
