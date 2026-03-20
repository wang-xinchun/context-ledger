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
SQL_DSN = os.getenv(
    "CONTEXTLEDGER_SQL_DSN",
    f"sqlite:///{(Path('data') / 'contextledger.db').as_posix()}",
)
SQL_WRITE_ENABLED = _env_flag("CONTEXTLEDGER_SQL_WRITE_ENABLED", True)
SQL_READ_ENABLED = _env_flag("CONTEXTLEDGER_SQL_READ_ENABLED", False)
MEMORY_LEDGER_PATH = os.getenv(
    "CONTEXTLEDGER_MEMORY_LEDGER_PATH",
    str(Path("data") / "contextledger-memory.jsonl"),
)
