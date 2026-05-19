# Ares Proprietary Independence Plan

## Status

### Done
- GitHub repo description updated — no longer mentions OpenJarvis.
- Hardcoded Langfuse keys removed from `start.sh`; secrets now loaded from
  `.env` via `source`.
- `.env.example` added with all configurable env vars documented.
- Model names and `OLLAMA_HOST` made overridable via environment variables.
- `check_required_models()` added to `engine.py`; `start.sh` warns on missing
  pulls at startup.
- Manual `sys.path` hacks removed from `engine.py`, `a2a_server.py`, `main.py`.
- `build_single_agent()` added so each A2A subprocess boots only its own agent.
- Conversation history window added to REPL and wired to all agent calls.
- `atexit`/`SIGTERM` shutdown handlers added to `main.py`.
- `tests/` suite added covering history, handoff, Serena tools, A2A endpoints,
  and config.
- This plan document added under `docs/`.

### Next
- Add `ares/runtime/` boundary modules (phase 1 facade).
- Move all `openjarvis.*` imports behind `ares/runtime/*`.
- Add static import boundary linter (fails CI if direct openjarvis imports
  appear outside `ares/runtime`).
- Add Ares proprietary license file + third-party Apache-2.0 attribution file.
- Rename any remaining comments/docstrings that describe Ares as an OpenJarvis
  wrapper.

---

## Summary

Make Ares a proprietary, Ares-owned system rather than a visible mix of
OpenJarvis components. The first step is to introduce Ares-owned runtime APIs
and move OpenJarvis behind a private compatibility layer. Later phases replace
that compatibility layer with Ares-native implementations.

OpenJarvis is Apache-2.0 in the local `ares-core` checkout, so Ares can be
proprietary while still using or adapting Apache-licensed code, provided the
license and attribution requirements are preserved for any derived portions.
This plan is technical planning, not legal advice.

Success criteria:

- No direct `openjarvis.*` imports outside Ares compatibility/runtime modules.
- User-facing names, docs, startup output, tests, and module boundaries present
  the product as Ares, not OpenJarvis.
- Current REPL, agents, A2A endpoints, Serena tools, memory, observability, and
  `/learn` continue working.
- Tests no longer need broad OpenJarvis stubs for normal Ares imports.

## Key Changes

- Add Ares-native runtime modules:
  - `ares/runtime/events.py`: expose `Event`, `EventBus`, `EventType`.
  - `ares/runtime/types.py`: expose `Message`, `Role`, `Conversation`,
    `AgentResult`, `ToolResult`, `ToolCall`.
  - `ares/runtime/tools.py`: expose `BaseTool`, `ToolSpec`, and later
    `ToolExecutor`.
  - `ares/runtime/engine.py`: expose Ares engine protocol and Ollama engine
    entrypoint.
  - `ares/runtime/tracing.py`: expose trace store/collector wrappers.
  - `ares/runtime/learning.py`: expose learning orchestrator wrapper.
  - `ares/runtime/a2a.py`: expose `AgentCard` and `A2AServer`.
  - `ares/runtime/agents.py`: expose `NativeReActAgent`, `NativeOpenHandsAgent`,
    `LoopGuard`, `LoopGuardConfig`.

- Move all OpenJarvis imports behind these modules:
  - Agents import Ares runtime types/tools/events instead of OpenJarvis.
  - `ares/engine.py` imports the Ares Ollama adapter.
  - `ares/memory.py`, `ares/observability.py`, `ares/learning.py`,
    `ares/a2a_server.py`, and Serena tools use Ares runtime APIs only.
  - Keep OpenJarvis delegation only inside `ares/runtime/*` for this phase.

- Make ownership and branding explicit:
  - Add an Ares project license/ownership file appropriate for proprietary
    distribution.
  - Add a third-party attribution file for OpenJarvis-derived or delegated code,
    preserving the Apache-2.0 license text.
  - Rename comments, docstrings, and tests that describe Ares as an OpenJarvis
    wrapper or OpenJarvis tool surface.

- Preserve external behavior:
  - REPL commands stay the same.
  - Agent model assignments stay the same.
  - A2A ports and endpoints stay the same.
  - Trace DB, Langfuse export, mem0 behavior, and Serena MCP behavior stay the
    same.
  - `start.sh` will still add `/home/z/ares-core/src` to `PYTHONPATH` during this
    phase.

## Implementation Notes

- Treat `ares/runtime/*` as the new public internal platform for Ares.
- Start with thin re-export/adapters to minimize behavior drift.
- Name the adapter layer as internal compatibility code, not as part of Ares'
  public identity.
- Update tests to stub or assert Ares runtime APIs, not OpenJarvis APIs.
- Add one regression test that imports every production Ares module with only
  `ares.runtime` as the dependency boundary.
- Add a static test or script check that fails if direct `openjarvis.` imports
  appear outside `ares/runtime`.
- Add a documentation check that keeps public docs and startup text from
  presenting Ares as OpenJarvis-based, except in third-party attribution.

## Test Plan

- Run existing unit tests.
- Add tests for:
  - `AresSystem` history formatting still works.
  - `_AgentHandoffTool` still returns success, empty-task failure, and exception
    failure.
  - Serena tools still expose the same tool specs and return `ToolResult`.
  - A2A app factory still serves agent card, task endpoint, and health endpoint.
  - Static import boundary: only `ares/runtime/**` may import `openjarvis.*`.
  - Branding boundary: public docs and startup text use Ares naming; attribution
    files may mention OpenJarvis.

## Assumptions

- First phase is Ares facade first.
- This phase does not copy the full OpenJarvis source into Ares.
- OpenJarvis remains an implementation dependency temporarily.
- No behavior redesign yet: this is an ownership, branding, and architecture
  boundary refactor.
- Proprietary Ares licensing will be added separately from third-party
  Apache-2.0 attribution.
- A later phase will replace each runtime adapter with native Ares
  implementations, starting with the low-risk pieces: events, types, tools, and
  Ollama engine.

---

## Phase 2: Intelligence Layer (all local, Ollama-only)

All features below run entirely on-device. No cloud calls. Each technique is a
prompt-engineering or storage pattern layered on the existing Ollama engine.

### Hardware-aware model profiles

- Add `ares/runtime/hardware.py`: detect GPU VRAM (`nvidia-smi`/`rocm-smi`)
  and total system RAM at startup.
- Define three built-in profiles:

  | Profile | Condition                  | Models                                              |
  |---------|----------------------------|-----------------------------------------------------|
  | low     | ≤8 GB RAM, no GPU          | all agents: `qwen2.5-coder:1.5b`                   |
  | mid     | 16 GB RAM or 8 GB VRAM     | current defaults (FLUX, FORGE, RUNE, SWIFT)         |
  | high    | 32 GB+ RAM or 16 GB+ VRAM  | `qwen3:14b`, `qwen2.5-coder:32b`, `deepseek-r1:32b` |

- Auto-select profile at startup; print detected hardware and selected profile.
- Env var overrides (`ARES_*_MODEL`) always take precedence over auto-selection.
- Allow `ARES_HARDWARE_PROFILE=low|mid|high` to force a profile manually.

### SWE-agent ACI for coder and runner

- Replace raw shell/file tools with structured ACI commands:
  `open`, `goto <line>`, `scroll_down/up`, `search_file`, `search_dir`,
  `find_file`, `edit <start>:<end>`, `diff`, `run_tests`.
- Keeps the coder and runner agents from wasting tokens on repeated cat/grep
  cycles; each command returns a bounded, structured view.
- Implemented as Ares-native tools in `ares/tools/aci.py` — no OpenJarvis
  dependency.

### Reflexion — trace-to-reflection loop

- After each task completes (success or failure), run a short reflection prompt
  against the Langfuse trace summary.
- Store the reflection in mem0 tagged with task type and outcome.
- Before starting a new task, retrieve the top-k relevant reflections and
  prepend them to the agent's system prompt.
- Infrastructure already exists (Langfuse + mem0); new code is one
  post-task hook and one pre-task retrieval step.

### Voyager skill library

- After a successful coding, shell, or refactor workflow, extract the solution
  pattern as a named skill (description + code/command template).
- Store skills in a local SQLite table (`~/.ares/skills.db`).
- Before routing a task, retrieve top-k similar skills by embedding similarity
  and surface them to the orchestrator as hints.
- Pairs with and extends the existing `learning.py` / `/learn` command.

### ReWOO-style planning for expensive agents

- For thinker and orchestrator: emit a full tool-call plan first (one LLM
  call), then execute all tool calls sequentially without re-querying the model
  between steps.
- Reduces total Ollama inference calls per task from O(steps) to O(1) + tools.
- Only applies when the task is decomposable up front; falls back to standard
  ReAct loop for open-ended tasks.
- Requires `ares/runtime/engine.py` to be in place (do after phase 1).

### Self-RAG critique for memory and Serena results

- After any mem0 or Serena retrieval, run a one-shot critique prompt: "Is this
  retrieved context relevant and sufficient for the query?"
- If the critique scores weak, the agent signals the orchestrator to try a
  broader query or proceed without the context rather than hallucinate over it.
- Lightweight — one extra local inference call per retrieval, no new storage.

### Phase 2 ordering

1. Hardware-aware model profiles (unblocked, high user value)
2. SWE-agent ACI tools (unblocked, immediate coder improvement)
3. Reflexion hook (unblocked, infrastructure exists)
4. Voyager skill library (after Reflexion, shares mem0 plumbing)
5. ReWOO planning (after phase 1 runtime boundary)
6. Self-RAG critique (after ReWOO, lowest priority)
