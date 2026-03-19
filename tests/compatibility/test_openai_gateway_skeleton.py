import pytest
from fastapi.testclient import TestClient

@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("post", "/openai/v1/chat/completions"),
        ("post", "/openai/v1/responses"),
        ("post", "/openai/v1/embeddings"),
        ("get", "/openai/v1/models"),
    ],
)
def test_openai_gateway_skeleton_returns_501_with_error_model(
    client: TestClient, method: str, path: str
) -> None:
    response = getattr(client, method)(path)
    assert response.status_code == 501
    payload = response.json()
    assert payload["error"]["code"] == "NOT_IMPLEMENTED"
    assert payload["error"]["request_id"].startswith("req_")
    assert path in payload["error"]["message"]
