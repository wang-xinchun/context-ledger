from __future__ import annotations

from pathlib import Path

from app.core import settings
from app.db import session as db_session


def _sqlite_url(path: Path) -> str:
    return f"sqlite:///{path.as_posix()}"


def test_get_engine_creates_sqlite_parent_dir(tmp_path, monkeypatch) -> None:
    db_path = tmp_path / "nested" / "ctx.db"
    monkeypatch.setattr(settings, "SQL_DSN", _sqlite_url(db_path))
    db_session.reset_engine_state()

    db_session.get_engine()
    assert db_path.parent.exists()

    db_session.reset_engine_state()


def test_sqlite_pragmas_are_applied(tmp_path, monkeypatch) -> None:
    db_path = tmp_path / "pragma.db"
    monkeypatch.setattr(settings, "SQL_DSN", _sqlite_url(db_path))
    db_session.reset_engine_state()

    engine = db_session.get_engine()
    with engine.connect() as conn:
        foreign_keys = conn.exec_driver_sql("PRAGMA foreign_keys").scalar_one()
        journal_mode = conn.exec_driver_sql("PRAGMA journal_mode").scalar_one()

    assert foreign_keys == 1
    assert str(journal_mode).lower() in {"wal", "memory"}

    db_session.reset_engine_state()


def test_reset_engine_state_rebuilds_engine(tmp_path, monkeypatch) -> None:
    db_path = tmp_path / "rebuild.db"
    monkeypatch.setattr(settings, "SQL_DSN", _sqlite_url(db_path))
    db_session.reset_engine_state()

    engine_1 = db_session.get_engine()
    db_session.reset_engine_state()
    engine_2 = db_session.get_engine()

    assert engine_1 is not engine_2

    db_session.reset_engine_state()
