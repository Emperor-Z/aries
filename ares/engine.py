"""Shared OllamaEngine singleton for all Ares agents."""

from __future__ import annotations

import sys
from pathlib import Path

# Make sure ares-core src is importable
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "ares-core" / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "ares-core" / ".venv" / "lib" / "python3.13" / "site-packages"))

from openjarvis.engine.ollama import OllamaEngine
from ares.config import OLLAMA_HOST

_engine: OllamaEngine | None = None


def get_engine() -> OllamaEngine:
    global _engine
    if _engine is None:
        _engine = OllamaEngine(host=OLLAMA_HOST)
        if not _engine.health():
            raise RuntimeError(f"Ollama not reachable at {OLLAMA_HOST}")
    return _engine
