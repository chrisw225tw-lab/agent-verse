"""Tier 2 — JSON-mode agent using the Anthropic API.

See GDD §5.3 and §12.2.

Prereqs:
    pip install anthropic
    export ANTHROPIC_API_KEY=sk-...
"""

from __future__ import annotations

import json
import subprocess
import sys

import anthropic

SYSTEM = """You are playing agent-verse. Each turn you receive JSON state with valid actions.
Respond with JSON: {"action": <index_or_command>}
Strategy: explore all branches, manage HP, collect coins, use map at junctions."""


def main() -> int:
    game = subprocess.Popen(
        [sys.executable, "-m", "agentverse.game", "--json"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        text=True,
    )
    assert game.stdout and game.stdin

    client = anthropic.Anthropic()
    history: list[dict] = []

    while True:
        line = game.stdout.readline().strip()
        if not line:
            break

        state = json.loads(line)
        if not state["state"]["alive"]:
            break

        history.append({"role": "user", "content": json.dumps(state)})
        # Context management — keep last 20 turns (40 messages)
        if len(history) > 40:
            history = history[-40:]

        resp = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=100,
            system=SYSTEM,
            messages=history,
        )
        answer = resp.content[0].text
        history.append({"role": "assistant", "content": answer})

        game.stdin.write(answer + "\n")
        game.stdin.flush()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
