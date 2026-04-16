# agent-verse

A **horizontal tree-structured exploration game** designed for AI agents to play via CLI. Each section of the world is a 1D side-scrolling path (like Mario) with items, hazards, and NPCs. Sections connect at junction nodes forming a tree. The tree grows as agents/players create new sections, forming an emergent shared world.

> **Core tension:** Simple enough for a 1B local model to play, rich enough for a frontier model to strategize.

**End-state vision:** Anyone joins with their own agent (OpenClaw, Claude Code, local Ollama, custom script) and coexists in a shared, ever-expanding tree world — exploring, trading, building, and encountering each other.

See [docs/GDD.md](docs/GDD.md) for the full game design document.

## Status

Stage 1 — Local Walking. Single agent, CLI stdin/stdout, single Python file. Scaffolded but not implemented.

| Stage | Scope | Networking | Status |
| :---- | :---- | :---- | :---- |
| **1 — Local Walking** | Single agent, CLI stdin/stdout | None | scaffold |
| **2 — Expand World** | Agent-created sections, persistence, fog of war | None | TODO |
| **3 — Multiplayer Server** | FastAPI/WebSocket, multi-agent simultaneous play | Server | TODO |
| **4 — Mobile** | React/web viewer for spectating, touch controls | Web | TODO |

## Quick start

```bash
# Human player
python -m agentverse.game

# JSON mode (for API-model agents)
python -m agentverse.game --json

# Tier 0 Ollama wrapper
python agents/tier0_ollama.py
```

## Repo layout

```
agent-verse/
├── docs/GDD.md              # Full game design document
├── src/agentverse/
│   ├── __init__.py
│   ├── game.py              # Main CLI entry point
│   ├── world.py             # Tree/node/edge data model
│   ├── tiles.py             # Tile kinds and resolution
│   ├── engine.py            # Move + encounter logic
│   └── protocol.py          # Text/JSON I/O
├── agents/                  # Example agent wrappers
│   ├── tier0_ollama.py      # Index-pick, 1B+ local models
│   └── tier2_claude.py      # JSON mode, frontier API models
├── tests/                   # pytest tests
├── requirements.txt
├── pyproject.toml
└── LICENSE
```

## Design principles

1. **Agent-first, human-watchable.** Every design decision optimizes for agent playability.
2. **Token budget is law.** State output stays under 150 tokens for Tier 0/1.
3. **Deterministic engine, intelligent agents.** No randomness in rules; seeded RNG at runtime.
4. **Forced decisions create intelligence signal.** Blocking tiles are where good agents shine.
5. **Enumerate, don't hallucinate.** Always provide a valid-action list.
6. **Simple data, emergent complexity.** ~14 tile kinds, a tree of nodes and edges. That's it.

## License

MIT — see [LICENSE](LICENSE).
