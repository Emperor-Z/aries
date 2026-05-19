"""Shared OllamaEngine singleton for all Ares agents."""

from __future__ import annotations

import logging

from openjarvis.engine.ollama import OllamaEngine
from ares.config import OLLAMA_HOST, REQUIRED_MODELS

logger = logging.getLogger(__name__)

_engine: OllamaEngine | None = None


def get_engine() -> OllamaEngine:
    global _engine
    if _engine is None:
        _engine = OllamaEngine(host=OLLAMA_HOST)
        if not _engine.health():
            raise RuntimeError(f"Ollama not reachable at {OLLAMA_HOST}")
    return _engine


def check_required_models() -> list[str]:
    """Return a list of required models that are not yet pulled in Ollama.

    Logs a warning for each missing model. Does not raise — callers decide
    whether missing models are fatal.
    """
    try:
        engine = get_engine()
        available = {m.get("name", m) if isinstance(m, dict) else str(m)
                     for m in (engine.list_models() or [])}
        missing = [m for m in REQUIRED_MODELS if m not in available]
        for m in missing:
            logger.warning("Model not pulled: %s  (run: ollama pull %s)", m, m)
        return missing
    except Exception as exc:
        logger.warning("Could not check model availability: %s", exc)
        return []
