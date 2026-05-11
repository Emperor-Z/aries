"""Model aliases and global constants for Ares."""

from __future__ import annotations

OLLAMA_HOST = "http://localhost:11434"

# Model aliases — match existing Ollama pulls
SWIFT   = "qwen2.5-coder:3b"  # fast code, quick/fire-and-forget tasks
FORGE   = "qwen2.5-coder:7b"  # quality code, debugging, refactoring
SAGE    = "qwen3:4b"           # available; slower + verbose, not in active rotation
FLUX    = "qwen3.5:4b"         # MoE, 0.46s TTFT, 3× faster than qwen3:4b, 0 tool errors
RUNE    = "deepseek-r1:7b"     # chain-of-thought, deep research, planning
EMBED   = "nomic-embed-text"   # embeddings only — used by mem0/chromadb, not an agent

# Per-agent assignment rationale:
#   orchestrator → FLUX:  qwen3.5:4b MoE — fastest routing, native tool calling, direct responses
#   coder        → FORGE: qwen2.5-coder:7b — best code quality
#   thinker      → RUNE:  deepseek-r1:7b — native CoT for deep reasoning
#   runner       → SWIFT: qwen2.5-coder:3b — fastest, full GPU, simple tasks

AGENT_DEFAULTS = {
    "orchestrator": {"model": FLUX,  "temperature": 0.2, "max_tokens": 512,  "max_turns": 6},
    "coder":        {"model": FORGE, "temperature": 0.3, "max_tokens": 2048, "max_turns": 12},
    "thinker":      {"model": RUNE,  "temperature": 0.6, "max_tokens": 4096, "max_turns": 15},
    "runner":       {"model": SWIFT, "temperature": 0.4, "max_tokens": 1024, "max_turns": 8},
}

LOOP_GUARD = {
    "max_identical_calls": 3,
    "ping_pong_window": 6,
    "poll_tool_budget": 5,
    "max_context_messages": 80,
    "warn_before_block": True,
}
