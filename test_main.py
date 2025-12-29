from fastapi.testclient import TestClient
from unittest.mock import patch

from main import app
from agent import UpstreamLLMTimeoutError

client = TestClient(app)


def test_root():
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.json()["message"].lower().startswith("welcome")


def test_agent_endpoint_happy_path():
    with patch("main.run_weekend_planner", return_value={"output": "Hello plan"}):
        resp = client.post("/agent", json={"query": "Plan my weekend in Seattle"})
    assert resp.status_code == 200
    assert resp.json() == {"output": "Hello plan", "raw": None}


def test_agent_endpoint_empty_query():
    resp = client.post("/agent", json={"query": ""})
    assert resp.status_code in (422,)


def test_agent_endpoint_strips_followup_questions():
    # Simulate the model ending with a follow-up question.
    with patch(
        "main.run_weekend_planner",
        return_value={
            "output": "Here is your plan.\n\nWould you like me to tailor it further?",
        },
    ):
        resp = client.post("/agent", json={"query": "Plan my weekend in Seattle"})

    assert resp.status_code == 200
    assert resp.json()["raw"] is None
    # main.py returns output from run_weekend_planner; the one-shot enforcement is in agent.py.
    # This test only ensures the API shape + that we don't echo a question back.
    assert "?" not in resp.json()["output"]


def test_agent_endpoint_timeout_returns_504():
    with patch("main.run_weekend_planner", side_effect=UpstreamLLMTimeoutError("timeout")):
        resp = client.post("/agent", json={"query": "Plan my weekend in Seattle"})
    assert resp.status_code == 504
    assert "timed out" in resp.json()["detail"].lower()
