"""Tier 0 — Index-pick agent using a local Ollama model.

See GDD §5.1 and §12.1. Works with qwen2.5:7b, phi-3-mini, llama3.2:3b, etc.

Prereqs:
    pip install requests
    ollama pull qwen2.5:7b
    ollama serve
"""

from __future__ import annotations

import subprocess
import sys

import requests

SYSTEM = "You play a text game. Reply with ONLY a number from VALID options."


def main() -> int:
    game = subprocess.Popen(
        [sys.executable, "-m", "agentverse.game"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        text=True,
    )
    assert game.stdout and game.stdin

    while True:
        state = game.stdout.readline().strip()
        valid = game.stdout.readline().strip()
        if not state:
            break

        prompt = f"{state}\n{valid}\nChoose:"
        resp = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "qwen2.5:7b",
                "prompt": f"{SYSTEM}\n\n{prompt}",
                "stream": False,
            },
            timeout=60,
        )
        choice = resp.json()["response"].strip().split()[0]
        game.stdin.write(choice + "\n")
        game.stdin.flush()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
