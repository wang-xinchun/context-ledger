import json

import pytest
from fastapi.testclient import TestClient

from app.core import settings


def _stream_data_lines(response) -> list[str]:
    lines: list[str] = []
    append_line = lines.append
    for raw_line in response.iter_lines():
        if raw_line is None:
            continue
        if isinstance(raw_line, (bytes, bytearray)):
            line = raw_line.decode("utf-8")
        else:
            line = str(raw_line)
        if line:
            append_line(line)
    return lines


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


def test_openai_chat_completions_stream_returns_sse_chunks(client: TestClient) -> None:
    with client.stream(
        "POST",
        "/openai/v1/chat/completions",
        json={
            "model": "gpt-stream-test",
            "messages": [{"role": "user", "content": "please stream status update"}],
            "stream": True,
        },
    ) as response:
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/event-stream")
        data_lines = [line for line in _stream_data_lines(response) if line.startswith("data: ")]

    assert data_lines[-1] == "data: [DONE]"
    events = [json.loads(line[len("data: ") :]) for line in data_lines[:-1]]
    assert events[0]["object"] == "chat.completion.chunk"
    assert events[0]["choices"][0]["delta"]["role"] == "assistant"
    assert any(event["choices"][0]["finish_reason"] == "stop" for event in events)
    assert any("content" in event["choices"][0]["delta"] for event in events)


def test_openai_responses_returns_contract_compatible_payload(client: TestClient) -> None:
    response = client.post(
        "/openai/v1/responses",
        json={
            "model": "gpt-resp-test",
            "input": "summarize current project status",
            "max_output_tokens": 200,
            "project_id": "proj_resp",
            "session_id": "sess_resp",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["id"].startswith("resp_req_")
    assert payload["object"] == "response"
    assert payload["status"] == "completed"
    assert payload["model"] == "gpt-resp-test"
    assert isinstance(payload["created"], int)
    assert payload["output"][0]["type"] == "message"
    assert payload["output"][0]["role"] == "assistant"
    assert payload["output"][0]["content"][0]["type"] == "output_text"
    assert payload["output"][0]["content"][0]["text"] == payload["output_text"]
    assert payload["usage"]["input_tokens"] >= 1
    assert payload["usage"]["output_tokens"] >= 1
    assert payload["usage"]["total_tokens"] == (
        payload["usage"]["input_tokens"] + payload["usage"]["output_tokens"]
    )
    assert payload["x_contextledger"]["request_id"].startswith("req_")


def test_openai_responses_rejects_empty_input(client: TestClient) -> None:
    response = client.post(
        "/openai/v1/responses",
        json={"model": "gpt-resp-test", "input": "   "},
    )
    assert response.status_code == 400
    payload = response.json()
    assert payload["error"]["code"] == "INVALID_REQUEST"


def test_openai_responses_stream_returns_sse_events(client: TestClient) -> None:
    with client.stream(
        "POST",
        "/openai/v1/responses",
        json={
            "model": "gpt-response-stream",
            "input": "stream response protocol",
            "stream": True,
        },
    ) as response:
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/event-stream")
        data_lines = [line for line in _stream_data_lines(response) if line.startswith("data: ")]

    assert data_lines[-1] == "data: [DONE]"
    events = [json.loads(line[len("data: ") :]) for line in data_lines[:-1]]
    event_types = [event.get("type") for event in events]
    assert event_types[0] == "response.created"
    assert "response.output_text.delta" in event_types
    assert "response.output_text.done" in event_types
    assert event_types[-1] == "response.completed"
    completed = events[-1]["response"]
    assert completed["object"] == "response"
    assert completed["status"] == "completed"
    assert completed["id"].startswith("resp_req_")


def test_openai_embeddings_supports_single_string_input(client: TestClient) -> None:
    response = client.post(
        "/openai/v1/embeddings",
        json={"model": "embed-test", "input": "context ledger"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["object"] == "list"
    assert payload["model"] == "embed-test"
    assert len(payload["data"]) == 1
    first = payload["data"][0]
    assert first["object"] == "embedding"
    assert first["index"] == 0
    assert len(first["embedding"]) == 64
    assert payload["usage"]["prompt_tokens"] >= 1
    assert payload["usage"]["total_tokens"] == payload["usage"]["prompt_tokens"]


def test_openai_embeddings_supports_list_and_is_deterministic(client: TestClient) -> None:
    response = client.post(
        "/openai/v1/embeddings",
        json={
            "input": [
                "same text",
                "same text",
                "different text",
            ]
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert len(payload["data"]) == 3
    assert payload["data"][0]["embedding"] == payload["data"][1]["embedding"]
    assert payload["data"][0]["embedding"] != payload["data"][2]["embedding"]


@pytest.mark.parametrize("bad_input", [None, "", [], ["  "]])
def test_openai_embeddings_rejects_invalid_input(client: TestClient, bad_input) -> None:
    response = client.post(
        "/openai/v1/embeddings",
        json={"input": bad_input},
    )
    assert response.status_code == 400
    payload = response.json()
    assert payload["error"]["code"] == "INVALID_REQUEST"


def test_openai_models_returns_model_list(client: TestClient) -> None:
    response = client.get("/openai/v1/models")
    assert response.status_code == 200
    payload = response.json()
    assert payload["object"] == "list"
    assert isinstance(payload["data"], list)
    model_ids = {item["id"] for item in payload["data"]}
    assert settings.LMSTUDIO_DEFAULT_MODEL in model_ids
    assert settings.OLLAMA_DEFAULT_MODEL in model_ids
