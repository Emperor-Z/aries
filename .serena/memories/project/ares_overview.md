# Ares project overview

Ares is a local terminal AI system in `/home/z/ares`. It is described by the initial commit as a "100% local multi-agent AI system".

Key files:
- `main.py`: terminal REPL entry point. Loads `.env`, initializes `AresSystem`, supports `/coder`, `/thinker`, `/runner`, `/serena`, `/learn`, `/quit`.
- `ares/system.py`: top-level wiring for EventBus, memory, observability, agents, orchestrator, Serena, and RLM learning. Contains `AresSystem` and `build_single_agent` for lightweight A2A subprocesses.
- `ares/engine.py`: shared OllamaEngine singleton; validates Ollama health and checks required models from config.
- `ares/config.py`: configuration for Ollama/models and related runtime settings.
- `ares/a2a_server.py`: A2A server surface.
- `ares/observability.py`, `ares/memory.py`, `ares/learning.py`, `ares/serena_client.py`: shared infrastructure.

Runtime shape:
- Local Ollama backend via OpenJarvis `OllamaEngine`.
- Agents include coder, thinker, runner, serena, and orchestrator.
- Conversation history is injected into agent prompts with a 10-message window.
- Learning cycle can run via `/learn` or automatically every 20 interactions.
- Serena MCP subprocess is closed during `AresSystem.shutdown()`.

Current repository note as of 2026-05-19:
- Single commit: `724a5d7 feat: initial Ares commit — 100% local multi-agent AI system`.
- Worktree had uncommitted local changes in `.serena/project.yml`, `ares/a2a_server.py`, `ares/config.py`, `ares/engine.py`, `ares/observability.py`, `ares/system.py`, `main.py`, `start.sh`, plus new `.env.example`, `.serena/.gitignore`, and `tests/`.
- Do not revert user changes unless explicitly requested.

Strategic direction:
- Ares should become its own proprietary, Ares-owned system rather than a visible mix of OpenJarvis components.
- Near-term migration approach: Ares facade first. Add Ares-owned runtime APIs, move OpenJarvis imports behind private compatibility modules, then replace adapters with native Ares implementations over time.
- Preserve Apache-2.0 license/attribution requirements for any OpenJarvis-derived code while making public docs, startup text, tests, and module boundaries present the product as Ares.

Development style:
- Prefer existing Ares patterns and introduce Ares-owned interfaces before replacing internals.
- Use `rg`/symbol tools for exploration.
- Keep changes scoped and verify with focused tests where possible.