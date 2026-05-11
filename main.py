#!/usr/bin/env python3
"""Ares — terminal REPL entry point."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

# Ensure ares-core is on sys.path
_core = Path(__file__).parent.parent / "ares-core"
sys.path.insert(0, str(_core / "src"))
sys.path.insert(0, str(_core / ".venv" / "lib" / "python3.13" / "site-packages"))

logging.basicConfig(
    level=logging.WARNING,
    format="%(levelname)s %(name)s: %(message)s",
)

# Add ares package itself
sys.path.insert(0, str(Path(__file__).parent))

from ares.system import AresSystem

BANNER = """
╔══════════════════════════════════════╗
║  Ares  —  local AI  —  terminal     ║
║  /coder  /thinker  /runner          ║
║  /serena /learn    /quit            ║
╚══════════════════════════════════════╝
"""

COMMANDS = {
    "/coder":   "coder_run",
    "/thinker": "thinker_run",
    "/runner":  "runner_run",
    "/serena":  "serena_run",
}


def main() -> None:
    print(BANNER)
    print("Initialising...", flush=True)

    system = AresSystem()
    print("Ready.\n")

    while True:
        try:
            raw = input("ares> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye.")
            break

        if not raw:
            continue
        if raw in ("/quit", "/exit", "exit", "quit"):
            print("Bye.")
            break

        if raw == "/learn":
            print("Running rlm learning cycle...")
            summary = system.learn_now()
            print(f"Done: {summary}\n")
            continue

        # Check for direct agent override
        direct_method = None
        prompt = raw
        for cmd, method in COMMANDS.items():
            if raw.startswith(cmd + " "):
                direct_method = method
                prompt = raw[len(cmd):].strip()
                break

        try:
            if direct_method:
                response = getattr(system, direct_method)(prompt)
            else:
                response = system.run(prompt)
            print(f"\n{response}\n")
        except Exception as exc:
            print(f"\n[error] {exc}\n")


if __name__ == "__main__":
    main()
