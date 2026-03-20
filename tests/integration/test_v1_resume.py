from fastapi.testclient import TestClient


def test_resume_returns_empty_state_for_unknown_project(client: TestClient) -> None:
    response = client.post("/v1/resume", json={"project_id": "proj_empty"})
    assert response.status_code == 200

    payload = response.json()
    assert "No conversation history" in payload["project_snapshot"]
    assert payload["recent_decisions"] == []
    assert payload["open_todos"] == []


def test_resume_reflects_recent_decisions_and_todos(client: TestClient) -> None:
    project_id = "proj_resume"
    session_id = "sess_resume_1"

    chat_1 = client.post(
        "/v1/chat",
        json={
            "project_id": project_id,
            "session_id": session_id,
            "message": "we will choose postgres as default storage",
            "options": {"max_output_tokens": 800, "stream": False},
        },
    )
    assert chat_1.status_code == 200

    chat_2 = client.post(
        "/v1/chat",
        json={
            "project_id": project_id,
            "session_id": session_id,
            "message": "next we need to add integration tests for resume",
            "options": {"max_output_tokens": 800, "stream": False},
        },
    )
    assert chat_2.status_code == 200

    resume = client.post("/v1/resume", json={"project_id": project_id})
    assert resume.status_code == 200
    payload = resume.json()

    assert "Captured 2 turns" in payload["project_snapshot"]
    assert len(payload["recent_decisions"]) >= 1
    assert len(payload["open_todos"]) >= 1
