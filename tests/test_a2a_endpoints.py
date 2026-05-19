"""Tests for A2A HTTP endpoint shape (health + agent card)."""

import sys
import types
from unittest.mock import MagicMock

import pytest

# ── stubs ─────────────────────────────────────────────────────────────────────

def _stub_openjarvis():
    for mod_name in [
        "openjarvis", "openjarvis.a2a", "openjarvis.a2a.protocol",
        "openjarvis.a2a.server",
    ]:
        sys.modules.setdefault(mod_name, types.ModuleType(mod_name))

    class _AgentCard:
        def __init__(self, **kw):
            self.__dict__.update(kw)
        def to_dict(self):
            return {k: v for k, v in self.__dict__.items()}

    class _A2AServer:
        def __init__(self, agent_card, handler, bus=None):
            self.card = agent_card
            self.handler = handler
        def handle_request(self, req):
            prompt = req.get("params", {}).get("message", {}).get("parts", [{}])[0].get("text", "")
            return {"result": {"parts": [{"text": self.handler(prompt)}]}}

    sys.modules["openjarvis.a2a.protocol"].AgentCard = _AgentCard
    sys.modules["openjarvis.a2a.server"].A2AServer = _A2AServer
    return _AgentCard


@pytest.fixture(autouse=True)
def _inject():
    _stub_openjarvis()
    sys.modules.pop("ares.a2a_server", None)
    yield
    sys.modules.pop("ares.a2a_server", None)


def _make_app(agent_name: str, handler=None):
    from ares.a2a_server import make_app
    if handler is None:
        handler = lambda prompt: f"echo: {prompt}"
    return make_app(agent_name, handler)


# ── tests ─────────────────────────────────────────────────────────────────────

def test_health_endpoint():
    from fastapi.testclient import TestClient
    app = _make_app("coder")
    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["agent"] == "coder"


def test_agent_card_endpoint():
    from fastapi.testclient import TestClient
    app = _make_app("thinker")
    client = TestClient(app)
    resp = client.get("/.well-known/agent.json")
    assert resp.status_code == 200
    card = resp.json()
    assert "name" in card
    assert "thinker" in card["name"].lower() or "thinker" in str(card).lower()


def test_all_agent_names_have_cards():
    from ares.a2a_server import CARDS, PORTS
    assert set(CARDS.keys()) == set(PORTS.keys())
    for name, card in CARDS.items():
        assert card.name  # not empty
        assert card.url


def test_task_endpoint_delegates_to_handler():
    from fastapi.testclient import TestClient
    responses = []

    def handler(prompt):
        responses.append(prompt)
        return "handled"

    app = _make_app("runner", handler)
    client = TestClient(app)
    payload = {
        "params": {
            "message": {"parts": [{"text": "do something"}]}
        }
    }
    resp = client.post("/a2a/tasks", json=payload)
    assert resp.status_code == 200
