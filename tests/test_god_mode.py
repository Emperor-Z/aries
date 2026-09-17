"""Tests for ares.god_mode — subprocess and mem0 are mocked."""

from __future__ import annotations

from unittest.mock import MagicMock, patch


def test_ascend_launches_aries_subprocess():
    with patch("subprocess.run") as mock_run, \
         patch("ares.god_mode._write_ares_battle_briefing"), \
         patch("builtins.print"):
        mock_run.return_value = MagicMock(returncode=0)
        from ares.god_mode import ascend
        rc = ascend()
    assert rc == 0
    cmd = mock_run.call_args[0][0]
    assert "aries" in cmd
    assert "--ascend" in cmd


def test_ascend_passes_workspace_to_aries():
    with patch("subprocess.run") as mock_run, \
         patch("ares.god_mode._write_ares_battle_briefing"), \
         patch("builtins.print"):
        mock_run.return_value = MagicMock(returncode=0)
        from ares.god_mode import ascend
        ascend(workspace="/home/z/myrepo")
    cmd = mock_run.call_args[0][0]
    assert "--workspace" in cmd
    assert "/home/z/myrepo" in cmd


def test_ascend_returns_127_when_aries_not_found():
    with patch("subprocess.run", side_effect=FileNotFoundError), \
         patch("ares.god_mode._write_ares_battle_briefing"), \
         patch("builtins.print"):
        from ares.god_mode import ascend
        rc = ascend()
    assert rc == 127


def test_write_ares_battle_briefing_includes_history():
    history = [
        {"role": "user", "content": "fix the login bug"},
        {"role": "assistant", "content": "I patched auth.py line 42"},
    ]
    with patch("ares.god_mode._mem_search", return_value=[]), \
         patch("mem0.Memory") as mock_mem_cls:
        mock_mem = MagicMock()
        mock_mem_cls.return_value = mock_mem
        from ares.god_mode import _write_ares_battle_briefing
        result = _write_ares_battle_briefing(history)
    assert "fix the login bug" in result
    assert "auth.py" in result
    mock_mem.add.assert_called_once()
    kw = mock_mem.add.call_args.kwargs
    assert kw["metadata"]["type"] == "battle_briefing"
    assert kw["metadata"]["from"] == "ares"
    assert kw["user_id"] == "arjun"
