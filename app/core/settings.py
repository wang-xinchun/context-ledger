"""Runtime settings for ContextLedger."""

from __future__ import annotations

import os
from pathlib import Path


def _env_flag(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


APP_NAME = "ContextLedger"
APP_VERSION = "0.1.0"
DEFAULT_CHAT_PROVIDER = os.getenv("CONTEXTLEDGER_CHAT_PROVIDER", "lmstudio")
DEFAULT_EMBEDDING_PROVIDER = os.getenv("CONTEXTLEDGER_EMBEDDING_PROVIDER", "local")
DEFAULT_MAX_CONTEXT_TOKENS = int(os.getenv("CONTEXTLEDGER_MAX_CONTEXT_TOKENS", "4096"))
DEFAULT_RESERVED_OUTPUT_TOKENS = int(
    os.getenv("CONTEXTLEDGER_RESERVED_OUTPUT_TOKENS", "900")
)
LMSTUDIO_DEFAULT_MODEL = os.getenv("CONTEXTLEDGER_LMSTUDIO_MODEL", "qwen2.5-32b-instruct")
OLLAMA_DEFAULT_MODEL = os.getenv("CONTEXTLEDGER_OLLAMA_MODEL", "qwen2.5:32b")
COMPAT_CHAT_PERSIST_TURN = _env_flag("CONTEXTLEDGER_COMPAT_CHAT_PERSIST_TURN", False)
SQL_DSN = os.getenv(
    "CONTEXTLEDGER_SQL_DSN",
    f"sqlite:///{(Path('data') / 'contextledger.db').as_posix()}",
)
SQLITE_TIMEOUT_SECONDS = float(os.getenv("CONTEXTLEDGER_SQLITE_TIMEOUT_SECONDS", "2.0"))
SQL_WRITE_ENABLED = _env_flag("CONTEXTLEDGER_SQL_WRITE_ENABLED", True)
SQL_WRITE_BACKPRESSURE_ENABLED = _env_flag(
    "CONTEXTLEDGER_SQL_WRITE_BACKPRESSURE_ENABLED",
    True,
)
SQL_WRITE_LOCK_ACQUIRE_TIMEOUT_SECONDS = float(
    os.getenv("CONTEXTLEDGER_SQL_WRITE_LOCK_ACQUIRE_TIMEOUT_SECONDS", "0.0")
)
SQL_WRITE_RETRY_QUEUE_MAX = int(os.getenv("CONTEXTLEDGER_SQL_WRITE_RETRY_QUEUE_MAX", "2048"))
SQL_WRITE_RETRY_DRAIN_BATCH = int(os.getenv("CONTEXTLEDGER_SQL_WRITE_RETRY_DRAIN_BATCH", "0"))
SQL_WRITE_RETRY_DRAIN_BUDGET_MS = float(
    os.getenv("CONTEXTLEDGER_SQL_WRITE_RETRY_DRAIN_BUDGET_MS", "2.0")
)
SQL_READ_ENABLED = _env_flag("CONTEXTLEDGER_SQL_READ_ENABLED", False)
MEMORY_LEDGER_PATH = os.getenv(
    "CONTEXTLEDGER_MEMORY_LEDGER_PATH",
    str(Path("data") / "contextledger-memory.jsonl"),
)
