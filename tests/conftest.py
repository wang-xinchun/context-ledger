from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.memory import ledger as memory_ledger


@pytest.fixture(autouse=True)
def reset_memory_ledger() -> None:
    memory_ledger.reset(clear_file=True)
    yield
    memory_ledger.reset(clear_file=True)


@pytest.fixture()
def client() -> TestClient:
    with TestClient(app) as test_client:
        yield test_client
