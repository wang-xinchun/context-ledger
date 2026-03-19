"""ASGI entrypoint for ContextLedger."""

from __future__ import annotations

from fastapi import FastAPI

from app.api.v1.router import router as v1_router
from app.compatibility.openai_router import router as openai_compat_router
from app.core import settings


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Local-first memory reliability layer for long-horizon LLM workflows.",
)

app.include_router(v1_router)
app.include_router(openai_compat_router)
