from fastapi.testclient import TestClient
from unittest.mock import patch

from main import app

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
