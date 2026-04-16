# agent-verse

A tree-structured exploration game designed for AI agents to play via CLI. Each section of the world is a 1D side-scrolling path with items, hazards, and NPCs. Sections connect at junction nodes forming a tree. The tree grows as agents create new sections — a shared, ever-expanding world.

> **Status: design stage.** No code yet. This repo is the spec.

## Read the spec

[**docs/GDD.md**](docs/GDD.md) — full Game Design Document, including:

- Stage 1 MVP scope — 3 agent classes, 10 classic-AI NPCs, 30 edges, 50 assets, 10 events
- Tile system, forced encounters, and scoring
- Three-tier agent interface (index pick / keyword / JSON)
- Information hierarchy (breadcrumb, local view, map, memory)
- Staged roadmap through multiplayer + mobile

## License

MIT — see [LICENSE](LICENSE).
