import pytest
from fastapi.testclient import TestClient

from app.core import settings


def test_openai_chat_completions_returns_contract_compatible_payload(client: TestClient) -> None:
    response = client.post(
        "/openai/v1/chat/completions",
        json={
            "model": "gpt-compat-test",
            "messages": [
                {"role": "system", "content": "You are helpful."},
                {"role": "user", "content": "continue yesterday task"},
            ],
            "max_tokens": 256,
            "stream": False,
            "project_id": "proj_compat",
            "session_id": "sess_compat",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["id"].startswith("chatcmpl_req_")
    assert payload["object"] == "chat.completion"
    assert payload["model"] == "gpt-compat-test"
    assert isinstance(payload["created"], int)
    assert payload["choices"][0]["index"] == 0
    assert payload["choices"][0]["message"]["role"] == "assistant"
    assert "continue yesterday task" in payload["choices"][0]["message"]["content"]
    assert payload["choices"][0]["finish_reason"] == "stop"
    assert payload["usage"]["prompt_tokens"] >= 1
    assert payload["usage"]["completion_tokens"] >= 1
    assert payload["usage"]["total_tokens"] == (
        payload["usage"]["prompt_tokens"] + payload["usage"]["completion_tokens"]
    )
    assert payload["x_contextledger"]["request_id"].startswith("req_")


def test_openai_chat_completions_rejects_empty_messages(client: TestClient) -> None:
    response = client.post(
        "/openai/v1/chat/completions",
        json={"model": "gpt-compat-test", "messages": []},
    )
    assert response.status_code == 400
    payload = response.json()
    assert payload["error"]["code"] == "INVALID_REQUEST"
    assert payload["error"]["request_id"].startswith("req_")


def test_openai_models_returns_model_list(client: TestClient) -> None:
    response = client.get("/openai/v1/models")
    assert response.status_code == 200
    payload = response.json()
    assert payload["object"] == "list"
    assert isinstance(payload["data"], list)
    model_ids = {item["id"] for item in payload["data"]}
    assert settings.LMSTUDIO_DEFAULT_MODEL in model_ids
    assert settings.OLLAMA_DEFAULT_MODEL in model_ids


@pytest.mark.parametrize(
    "path",
    [
        "/openai/v1/responses",
        "/openai/v1/embeddings",
    ],
)
def test_openai_gateway_remaining_endpoints_keep_501(client: TestClient, path: str) -> None:
    response = client.post(path)
    assert response.status_code == 501
    payload = response.json()
    assert payload["error"]["code"] == "NOT_IMPLEMENTED"
    assert payload["error"]["request_id"].startswith("req_")
    assert path in payload["error"]["message"]
