"""Database engine/session helpers."""

from __future__ import annotations

from collections.abc import Generator
from functools import lru_cache
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine, URL, make_url
from sqlalchemy.orm import Session, sessionmaker

from app.core import settings


def _is_sqlite(url: URL) -> bool:
    return url.get_backend_name() == "sqlite"


def _ensure_sqlite_parent_dir(url: URL) -> None:
    if not _is_sqlite(url):
        return

    db_path = url.database
    if db_path in {None, "", ":memory:"}:
        return

    target = Path(db_path)
    if not target.is_absolute():
        target = Path.cwd() / target
    target.parent.mkdir(parents=True, exist_ok=True)


def _sqlite_timeout_seconds() -> float:
    return max(0.1, float(settings.SQLITE_TIMEOUT_SECONDS))


def _connect_args(url: URL) -> dict[str, object]:
    if _is_sqlite(url):
        return {
            "check_same_thread": False,
            "timeout": _sqlite_timeout_seconds(),
        }
    return {}


def _configure_sqlite_pragma(engine: Engine, *, busy_timeout_ms: int) -> None:
    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, _connection_record) -> None:
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.execute(f"PRAGMA busy_timeout={busy_timeout_ms}")
        finally:
            cursor.close()


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    url = make_url(settings.SQL_DSN)
    _ensure_sqlite_parent_dir(url)

    engine = create_engine(
        url,
        future=True,
        pool_pre_ping=not _is_sqlite(url),
        connect_args=_connect_args(url),
    )
    if _is_sqlite(url):
        busy_timeout_ms = int(_sqlite_timeout_seconds() * 1000)
        _configure_sqlite_pragma(engine, busy_timeout_ms=busy_timeout_ms)
    return engine


@lru_cache(maxsize=1)
def get_session_factory() -> sessionmaker[Session]:
    return sessionmaker(
        bind=get_engine(),
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
        class_=Session,
    )


def reset_engine_state() -> None:
    """Clear engine/sessionmaker caches for tests and environment switching."""
    if get_engine.cache_info().currsize:
        get_engine().dispose()
    get_session_factory.cache_clear()
    get_engine.cache_clear()


def get_session() -> Generator[Session, None, None]:
    session_factory = get_session_factory()
    with session_factory() as session:
        yield session
