"""mem0 + chromadb memory backend wired into OJ EventBus.

Subscribes to MEMORY_STORE and MEMORY_RETRIEVE events so any agent that
emits those events gets persistent cross-session memory automatically.
"""

from __future__ import annotations

import logging
from typing import Any

from openjarvis.core.events import EventBus, EventType

logger = logging.getLogger(__name__)

_mem0_client = None


def _get_mem0():
    global _mem0_client
    if _mem0_client is None:
        try:
            from mem0 import Memory
            _mem0_client = Memory()
            logger.info("mem0 memory backend initialised")
        except ImportError:
            logger.warning("mem0 not installed — memory persistence disabled")
    return _mem0_client


def _on_memory_store(payload: dict[str, Any]) -> None:
    mem = _get_mem0()
    if mem is None:
        return
    content = payload.get("content") or payload.get("data")
    user_id = payload.get("user_id", "ares")
    agent_id = payload.get("agent_id")
    if content:
        try:
            mem.add(content, user_id=user_id, agent_id=agent_id)
        except Exception as exc:
            logger.warning("mem0 store failed: %s", exc)


def _on_memory_retrieve(payload: dict[str, Any]) -> None:
    mem = _get_mem0()
    if mem is None:
        return
    query = payload.get("query", "")
    user_id = payload.get("user_id", "ares")
    if query:
        try:
            results = mem.search(query, user_id=user_id)
            payload["results"] = results  # mutate so callers can read back
        except Exception as exc:
            logger.warning("mem0 retrieve failed: %s", exc)


def wire_memory_to_bus(bus: EventBus) -> None:
    """Subscribe mem0 handlers to the shared EventBus."""
    bus.subscribe(EventType.MEMORY_STORE, _on_memory_store)
    bus.subscribe(EventType.MEMORY_RETRIEVE, _on_memory_retrieve)
    logger.info("mem0 wired to EventBus")


def search(query: str, user_id: str = "ares", limit: int = 5) -> list[dict]:
    """Direct memory search — usable from orchestrator routing logic."""
    mem = _get_mem0()
    if mem is None:
        return []
    try:
        return mem.search(query, user_id=user_id, limit=limit)
    except Exception as exc:
        logger.warning("mem0 search failed: %s", exc)
        return []
