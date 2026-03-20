from fastapi.testclient import TestClient


def test_timeline_returns_empty_for_unknown_project(client: TestClient) -> None:
    response = client.get("/v1/timeline", params={"project_id": "proj_empty"})
    assert response.status_code == 200

    payload = response.json()
    assert payload["items"] == []
    assert payload["next_cursor"] is None


def test_timeline_returns_latest_first_and_supports_cursor(client: TestClient) -> None:
    project_id = "proj_timeline"
    session_id = "sess_timeline_1"

    response_1 = client.post(
        "/v1/chat",
        json={
            "project_id": project_id,
            "session_id": session_id,
            "message": "we will choose postgres as default storage",
            "options": {"max_output_tokens": 500, "stream": False},
        },
    )
    assert response_1.status_code == 200

    response_2 = client.post(
        "/v1/chat",
        json={
            "project_id": project_id,
            "session_id": session_id,
            "message": "there is risk of migration drift",
            "options": {"max_output_tokens": 500, "stream": False},
        },
    )
    assert response_2.status_code == 200

    response_3 = client.post(
        "/v1/chat",
        json={
            "project_id": project_id,
            "session_id": session_id,
            "message": "next we need to add timeline endpoint tests",
            "options": {"max_output_tokens": 500, "stream": False},
        },
    )
    assert response_3.status_code == 200

    page_1 = client.get(
        "/v1/timeline",
        params={"project_id": project_id, "limit": 2},
    )
    assert page_1.status_code == 200

    payload_1 = page_1.json()
    assert len(payload_1["items"]) == 2
    assert payload_1["items"][0]["type"] == "todo"
    assert payload_1["items"][1]["type"] == "risk"
    assert payload_1["next_cursor"] == payload_1["items"][-1]["id"]

    page_2 = client.get(
        "/v1/timeline",
        params={
            "project_id": project_id,
            "limit": 2,
            "cursor": payload_1["next_cursor"],
        },
    )
    assert page_2.status_code == 200

    payload_2 = page_2.json()
    assert len(payload_2["items"]) == 1
    assert payload_2["items"][0]["type"] == "decision"
    assert payload_2["next_cursor"] is None
