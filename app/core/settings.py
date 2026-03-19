"""Runtime settings for ContextLedger."""

from __future__ import annotations

import os


APP_NAME = "ContextLedger"
APP_VERSION = "0.1.0"
DEFAULT_CHAT_PROVIDER = os.getenv("CONTEXTLEDGER_CHAT_PROVIDER", "lmstudio")
DEFAULT_EMBEDDING_PROVIDER = os.getenv("CONTEXTLEDGER_EMBEDDING_PROVIDER", "local")
DEFAULT_MAX_CONTEXT_TOKENS = int(os.getenv("CONTEXTLEDGER_MAX_CONTEXT_TOKENS", "4096"))
DEFAULT_RESERVED_OUTPUT_TOKENS = int(
    os.getenv("CONTEXTLEDGER_RESERVED_OUTPUT_TOKENS", "900")
)
