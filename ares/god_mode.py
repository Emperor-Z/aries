"""Ares → Aries God Mode ascend bridge.

Writes an Ares-side battle briefing to mem0, then launches the
`aries --ascend` process. Ares exits cleanly after ascend() returns.

The dependency arrow is one-way: this module knows about `aries`.
Aries knows nothing about Ares.
"""

from __future__ import annotations

import logging
import subprocess
import sys

from ares.memory import search as _mem_search

logger = logging.getLogger(__name__)


def _write_ares_battle_briefing(
    history: list[dict],
    workspace: str | None = None,
) -> str | None:
    """Write a structured battle briefing to mem0 from Ares session state.

    Composed from recent REPL history + mem0 entries. Written directly to
    mem0 (bypassing the EventBus) so metadata can be set.
    """
    recent = history[-20:] if history else []
    lines = []
    for msg in recent:
        label = "You" if msg["role"] == "user" else "Ares"
        lines.append(f"{label}: {msg['content'][:300]}")

    recent_memories = _mem_search("current objective files decisions", limit=10)
    mem_lines = [e.get("memory") or e.get("data", "") for e in recent_memories if e]

    briefing = (
        "# Battle Briefing — Ares Standing Down\n\n"
        "## Recent Conversation\n"
        + ("\n".join(lines) or "(no history)") + "\n\n"
        "## Recent Memory Entries\n"
        + ("\n".join(f"- {m}" for m in mem_lines if m) or "(none)") + "\n\n"
        "## Recommended Next Action\n"
        "Review the conversation above and continue in Aries God Mode.\n"
    )

    try:
        from mem0 import Memory
        mem = Memory()
        mem.add(
            briefing,
            user_id="arjun",
            agent_id="ares",
            metadata={"type": "battle_briefing", "from": "ares"},
        )
        logger.info("Ares battle briefing written to mem0 (len=%d)", len(briefing))
    except Exception as exc:
        logger.warning("Ares battle briefing write failed: %s", exc)

    return briefing


def ascend(
    workspace: str | None = None,
    history: list[dict] | None = None,
    aries_bin: str = "aries",
    extra_args: list[str] | None = None,
) -> int:
    """Stand Ares down and ascend to Aries God Mode.

    1. Writes an Ares-side battle briefing to mem0.
    2. Launches `aries --ascend [--workspace <workspace>]` as a subprocess.
    3. Returns the exit code of the aries process.

    Blocks until the aries process exits — the war god is in one place at a time.
    The Ares REPL loop should break immediately after this returns.
    """
    logger.info("Ares standing down — ascending to Aries God Mode")
    print("\nStanding down. Preparing battle briefing...", flush=True)

    _write_ares_battle_briefing(history or [], workspace=workspace)
    print("Battle briefing written. Ascending to Aries God Mode...\n", flush=True)

    cmd = [aries_bin, "--ascend"]
    if workspace:
        cmd += ["--workspace", workspace]
    if extra_args:
        cmd += extra_args

    try:
        proc = subprocess.run(cmd, check=False)
        return proc.returncode
    except FileNotFoundError:
        print(
            f"[war god] aries binary not found at {aries_bin!r}. "
            "Install aries-god-mode and ensure `aries` is on PATH.",
            file=sys.stderr,
        )
        return 127
