from fastapi.testclient import TestClient


def test_health_endpoint_returns_expected_contract(client: TestClient) -> None:
    response = client.get("/v1/health")
    assert response.status_code == 200

    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["version"] == "0.1.0"
    assert payload["provider"]["chat"] == "lmstudio"
    assert payload["provider"]["embedding"] == "local"
