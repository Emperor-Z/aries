"""Tests for _AgentHandoffTool in orchestrator.py."""

import sys
import types
from unittest.mock import MagicMock

import pytest


def _make_stubs():
    """Inject minimal openjarvis stubs so we can import orchestrator without OJ installed."""
    stubs = {
        "openjarvis": types.ModuleType("openjarvis"),
        "openjarvis.agents": types.ModuleType("openjarvis.agents"),
        "openjarvis.agents.orchestrator": types.ModuleType("openjarvis.agents.orchestrator"),
        "openjarvis.agents.loop_guard": types.ModuleType("openjarvis.agents.loop_guard"),
        "openjarvis.agents._stubs": types.ModuleType("openjarvis.agents._stubs"),
        "openjarvis.core": types.ModuleType("openjarvis.core"),
        "openjarvis.core.events": types.ModuleType("openjarvis.core.events"),
        "openjarvis.tools": types.ModuleType("openjarvis.tools"),
        "openjarvis.tools._stubs": types.ModuleType("openjarvis.tools._stubs"),
    }

    class _AgentResult:
        def __init__(self, content, turns=1):
            self.content = content
            self.turns = turns

    class _BaseTool:
        pass

    class _ToolSpec:
        def __init__(self, **kw): pass

    class _ToolResult:
        def __init__(self, tool_name, content, success, metadata=None):
            self.tool_name = tool_name
            self.content = content
            self.success = success
            self.metadata = metadata or {}

    stubs["openjarvis.agents._stubs"].AgentResult = _AgentResult
    stubs["openjarvis.tools._stubs"].BaseTool = _BaseTool
    stubs["openjarvis.tools._stubs"].ToolSpec = _ToolSpec
    stubs["openjarvis.tools._stubs"].ToolResult = _ToolResult

    class _LoopGuardConfig:
        def __init__(self, **kw): pass

    class _LoopGuard:
        def __init__(self, cfg, bus=None): pass

    stubs["openjarvis.agents.loop_guard"].LoopGuard = _LoopGuard
    stubs["openjarvis.agents.loop_guard"].LoopGuardConfig = _LoopGuardConfig
    stubs["openjarvis.core.events"].EventBus = MagicMock

    for name, mod in stubs.items():
        sys.modules.setdefault(name, mod)

    return _AgentResult, _ToolResult


@pytest.fixture(autouse=True)
def _inject_stubs():
    _make_stubs()
    # Clean up ares.agents.orchestrator so it reimports with stubs
    sys.modules.pop("ares.agents.orchestrator", None)
    yield
    sys.modules.pop("ares.agents.orchestrator", None)


def _import_handoff_tool():
    # Also stub ares.config and ares.engine
    cfg_mod = types.ModuleType("ares.config")
    cfg_mod.AGENT_DEFAULTS = {
        "orchestrator": {"model": "x", "temperature": 0.2, "max_tokens": 2048, "max_turns": 6}
    }
    cfg_mod.LOOP_GUARD = {
        "max_identical_calls": 3, "ping_pong_window": 6,
        "poll_tool_budget": 5, "max_context_messages": 80, "warn_before_block": True,
    }
    sys.modules["ares.config"] = cfg_mod
    sys.modules["ares.engine"] = types.ModuleType("ares.engine")
    sys.modules["ares.engine"].get_engine = MagicMock()

    from ares.agents.orchestrator import _AgentHandoffTool
    return _AgentHandoffTool


def test_handoff_success():
    _AgentHandoffTool = _import_handoff_tool()
    AgentResult, ToolResult = _make_stubs()

    mock_agent = MagicMock()
    mock_agent.run.return_value = AgentResult(content="result text", turns=2)

    tool = _AgentHandoffTool("call_coder", "Coder agent", mock_agent)
    result = tool.execute(task="write a hello world script")

    assert result.success is True
    assert result.content == "result text"
    mock_agent.run.assert_called_once_with("write a hello world script")


def test_handoff_empty_task():
    _AgentHandoffTool = _import_handoff_tool()

    mock_agent = MagicMock()
    tool = _AgentHandoffTool("call_coder", "Coder agent", mock_agent)
    result = tool.execute(task="")

    assert result.success is False
    mock_agent.run.assert_not_called()


def test_handoff_agent_exception():
    _AgentHandoffTool = _import_handoff_tool()

    mock_agent = MagicMock()
    mock_agent.run.side_effect = RuntimeError("model timeout")

    tool = _AgentHandoffTool("call_coder", "Coder agent", mock_agent)
    result = tool.execute(task="do something")

    assert result.success is False
    assert "model timeout" in result.content


def test_tool_spec_shape():
    _AgentHandoffTool = _import_handoff_tool()
    tool = _AgentHandoffTool("call_thinker", "Thinker", MagicMock())
    spec = tool.spec
    assert spec.name == "call_thinker"
    params = spec.parameters
    assert "task" in params["properties"]
    assert "task" in params["required"]
