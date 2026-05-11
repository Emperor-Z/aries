"""AresSystem — top-level object that wires all components together."""

from __future__ import annotations

import logging

from openjarvis.core.events import EventBus

from ares.agents import coder as _coder_mod
from ares.agents import thinker as _thinker_mod
from ares.agents import runner as _runner_mod
from ares.agents import orchestrator as _orch_mod
from ares.agents import serena_agent as _serena_mod
from ares.memory import wire_memory_to_bus
from ares.observability import wire_observability, wrap_with_collector
from ares.learning import build_learning_orchestrator, run_cycle

logger = logging.getLogger(__name__)


class AresSystem:
    """Initialise and hold all Ares agents + shared infrastructure."""

    def __init__(self) -> None:
        self.bus = EventBus()

        # Memory (mem0 → EventBus)
        wire_memory_to_bus(self.bus)

        # Observability (Langfuse exporter → EventBus)
        wire_observability(self.bus)

        # Build agents
        logger.info("Building agents...")
        _coder   = _coder_mod.build(self.bus)
        _thinker = _thinker_mod.build(self.bus)
        _runner  = _runner_mod.build(self.bus)
        _serena  = _serena_mod.build(self.bus)
        _orch    = _orch_mod.build(self.bus, _coder, _thinker, _runner, _serena)

        # Wrap each agent in a TraceCollector (records every run to SQLite)
        self.coder        = wrap_with_collector(_coder,   self.bus)
        self.thinker      = wrap_with_collector(_thinker, self.bus)
        self.runner       = wrap_with_collector(_runner,  self.bus)
        self.serena       = wrap_with_collector(_serena,  self.bus)
        self.orchestrator = wrap_with_collector(_orch,    self.bus)

        # rlm learning orchestrator
        self.learner = build_learning_orchestrator()

        self._interaction_count = 0
        self._learn_every = 20  # trigger a learning cycle every N interactions

        logger.info("Ares ready.")

    def run(self, prompt: str) -> str:
        """Route a user prompt through the orchestrator and return the response."""
        result = self.orchestrator.run(prompt)
        self._maybe_learn()
        return result.content or "(no output)"

    def coder_run(self, prompt: str) -> str:
        result = self.coder.run(prompt)
        self._maybe_learn()
        return result.content or "(no output)"

    def thinker_run(self, prompt: str) -> str:
        result = self.thinker.run(prompt)
        self._maybe_learn()
        return result.content or "(no output)"

    def runner_run(self, prompt: str) -> str:
        result = self.runner.run(prompt)
        self._maybe_learn()
        return result.content or "(no output)"

    def serena_run(self, prompt: str) -> str:
        result = self.serena.run(prompt)
        self._maybe_learn()
        return result.content or "(no output)"

    def learn_now(self) -> dict:
        """Manually trigger a learning cycle and return the summary."""
        return run_cycle(self.learner)

    def _maybe_learn(self) -> None:
        self._interaction_count += 1
        if self._interaction_count % self._learn_every == 0:
            try:
                run_cycle(self.learner)
            except Exception as exc:
                logger.warning("rlm learning cycle failed: %s", exc)
