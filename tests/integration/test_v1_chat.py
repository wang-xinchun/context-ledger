from fastapi.testclient import TestClient


def test_chat_endpoint_returns_minimal_meta_and_answer(client: TestClient) -> None:
    response = client.post(
        "/v1/chat",
        json={
            "project_id": "proj_001",
            "session_id": "sess_001",
            "message": "continue yesterday task",
            "options": {"max_output_tokens": 700, "stream": False},
        },
    )
    assert response.status_code == 200

    payload = response.json()
    assert "continue yesterday task" in payload["answer"]

    meta = payload["meta"]
    assert meta["request_id"].startswith("req_")
    assert meta["continuations"] == 0
    assert meta["balance_mode"] == "balanced"
    assert meta["fallback_mode"] == "none"
    assert 0 <= meta["quality_score"] <= 1
    assert 0 <= meta["retrieval_quality_score"] <= 1
    assert 0 <= meta["context_growth_ratio"] <= 1
    assert meta["budget"]["max_context_tokens"] == 4096
    assert meta["budget"]["reserved_output_tokens"] == 700
    assert isinstance(payload["used_memories"], list)


def test_chat_budget_does_not_exceed_context_limit(client: TestClient) -> None:
    large_message = "x" * 50000
    response = client.post(
        "/v1/chat",
        json={
            "project_id": "proj_001",
            "session_id": "sess_001",
            "message": large_message,
            "options": {"max_output_tokens": 100000, "stream": False},
        },
    )
    assert response.status_code == 200

    meta = response.json()["meta"]
    budget = meta["budget"]
    assert budget["used_input_tokens"] + budget["reserved_output_tokens"] <= budget[
        "max_context_tokens"
    ]
    assert meta["fallback_mode"] == "output_clamped"
