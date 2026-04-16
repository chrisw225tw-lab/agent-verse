"""CLI entry point. See GDD §5 and §11.

Usage:
    python -m agentverse.game          # text mode
    python -m agentverse.game --json   # JSON mode

Stage 1 scaffold: wires up the REPL, parser, and renderers. The actual
movement + encounter logic lives in engine.py (TODO).
"""

from __future__ import annotations

import argparse
import sys

from .engine import view
from .protocol import (
    parse_input,
    render_ascii_strip,
    render_state_json,
    render_state_text,
)
from .world import Entity, build_starter_world


def _valid_actions(world, entity) -> list[dict]:
    edge = world.edges[entity.edge]
    actions = []
    right_max = edge.length - 1 - entity.pos
    if right_max > 0:
        actions.append({"idx": len(actions) + 1, "cmd": "right",
                        "args": {"max": right_max}, "label": f"right({right_max}max)"})
    if entity.pos > 0:
        actions.append({"idx": len(actions) + 1, "cmd": "left", "label": "left"})
    actions.append({"idx": len(actions) + 1, "cmd": "map", "label": "map"})
    actions.append({"idx": len(actions) + 1, "cmd": "status", "label": "status"})
    return actions


def _emit_state(world, entity, path, valid, json_mode: bool, events=None, pending=None) -> None:
    kinds, offset = view(world, entity)
    if json_mode:
        line = render_state_json(world, entity, path, kinds, offset, valid,
                                 pending=pending, events=events)
    else:
        strip = render_ascii_strip(kinds, offset, entity.pos)
        line = render_state_text(world, entity, path, strip, valid,
                                 pending=pending, events=events)
    print(line, flush=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="agentverse")
    parser.add_argument("--json", action="store_true", help="JSON I/O mode")
    args = parser.parse_args(argv)

    world = build_starter_world()
    entity = Entity(id="player", edge="e0", pos=0)
    path = [world.root, entity.edge]

    while entity.alive:
        valid = _valid_actions(world, entity)
        _emit_state(world, entity, path, valid, json_mode=args.json)

        line = sys.stdin.readline()
        if not line:
            break
        action = parse_input(line)

        # TODO(stage-1): dispatch to engine.move / engine.resolve_pending.
        if action.cmd in ("quit", "exit"):
            break
        print(f"[stub] received action: cmd={action.cmd} args={action.args}",
              flush=True)
        # Without the engine, we don't advance state — just echo and loop.
        # This keeps the scaffold runnable while the engine is being built.
        break

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
