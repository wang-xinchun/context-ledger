from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

from app.db.base import Base
from app.db import models as _models  # noqa: F401  # Ensure ORM metadata is loaded.


def _sqlite_url(path: Path) -> str:
    return f"sqlite:///{path.as_posix()}"


def test_metadata_create_all_includes_core_tables(tmp_path) -> None:
    db_path = tmp_path / "metadata.db"
    engine = create_engine(_sqlite_url(db_path))

    Base.metadata.create_all(bind=engine)
    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())

    assert {
        "projects",
        "sessions",
        "turns",
        "memories",
        "memory_vectors",
        "timeline_events",
        "audit_logs",
    }.issubset(table_names)


def test_alembic_upgrade_head_creates_expected_indexes(tmp_path, monkeypatch) -> None:
    db_path = tmp_path / "alembic.db"
    monkeypatch.setenv("CONTEXTLEDGER_SQL_DSN", _sqlite_url(db_path))

    repo_root = Path(__file__).resolve().parents[2]
    alembic_cfg = Config(str(repo_root / "alembic.ini"))
    command.upgrade(alembic_cfg, "head")

    engine = create_engine(_sqlite_url(db_path))
    inspector = inspect(engine)

    turns_indexes = {item["name"] for item in inspector.get_indexes("turns")}
    memories_indexes = {item["name"] for item in inspector.get_indexes("memories")}
    timeline_indexes = {item["name"] for item in inspector.get_indexes("timeline_events")}
    audit_indexes = {item["name"] for item in inspector.get_indexes("audit_logs")}

    assert "idx_turns_project_session_created_at" in turns_indexes
    assert "idx_memories_project_type_created_at" in memories_indexes
    assert "idx_timeline_project_created_at" in timeline_indexes
    assert "idx_audit_project_created_at" in audit_indexes

    command.downgrade(alembic_cfg, "base")
