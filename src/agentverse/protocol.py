"""Text and JSON I/O protocol. See GDD §5 and §11.

Input parsing priority (GDD §5.4):
  1. Pure integer      -> Tier 0 index pick
  2. JSON object       -> Tier 2 structured
  3. Keyword string    -> Tier 1 command parse
  4. Fallback          -> "Unknown command."
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from .tiles import char_for
from .world import Entity, World


@dataclass
class ParsedAction:
    cmd: str              # e.g. "right", "left", "map", "status", "pick"
    args: dict[str, Any]
    raw: str              # the original input line


def parse_input(line: str) -> ParsedAction:
    s = line.strip()
    if not s:
        return ParsedAction(cmd="noop", args={}, raw=s)

    # 1) pure integer -> index pick
    if s.lstrip("-").isdigit():
        return ParsedAction(cmd="pick", args={"idx": int(s)}, raw=s)

    # 2) JSON
    if s.startswith("{"):
        try:
            obj = json.loads(s)
            return ParsedAction(cmd="json", args=obj, raw=s)
        except json.JSONDecodeError:
            pass

    # 3) Keyword
    parts = s.split()
    cmd = parts[0].lower()
    args: dict[str, Any] = {}
    if cmd in ("right", "left") and len(parts) > 1 and parts[1].isdigit():
        args["n"] = int(parts[1])
    return ParsedAction(cmd=cmd, args=args, raw=s)


# ---------- Text mode rendering ----------

def render_ascii_strip(kinds: list[str], view_offset: int, entity_pos: int) -> str:
    """Render the ±8 local view with @ marking the player position."""
    chars: list[str] = []
    for i, k in enumerate(kinds):
        if view_offset + i == entity_pos:
            chars.append("@")
        else:
            chars.append(char_for(k))
    return "·".join(chars)


def render_state_text(
    world: World,
    entity: Entity,
    path: list[str],
    ascii_strip: str,
    valid: list[dict],
    pending: dict | None = None,
    events: list[str] | None = None,
) -> str:
    edge = world.edges[entity.edge]
    breadcrumb = "→".join(path)
    header = (
        f"[{edge.id}:{edge.type} {entity.pos}/{edge.length - 1} path:{breadcrumb}] "
        f"{ascii_strip} hp:{entity.hp} coin:{entity.coins} key:{entity.keys}"
    )
    lines = []
    if events:
        lines.append(" ".join(events))
    lines.append(header)
    if pending:
        lines.append(f"[!] {pending['desc']}")
        opts = " ".join(f"{i + 1}){o}" for i, o in enumerate(pending["options"]))
        lines.append(f"must: {opts}")
    else:
        opts = " ".join(f"{v['idx']}){v['label']}" for v in valid)
        lines.append(f"VALID: {opts}")
    return "\n".join(lines)


# ---------- JSON mode rendering ----------

def render_state_json(
    world: World,
    entity: Entity,
    path: list[str],
    view_kinds: list[str],
    view_offset: int,
    valid: list[dict],
    pending: dict | None = None,
    events: list[str] | None = None,
) -> str:
    edge = world.edges[entity.edge]
    payload = {
        "state": {
            "edge": edge.id,
            "type": edge.type,
            "pos": entity.pos,
            "length": edge.length,
            "path": path,
            "hp": entity.hp,
            "coins": entity.coins,
            "keys": entity.keys,
            "view": view_kinds,
            "view_offset": view_offset,
            "alive": entity.alive,
        },
        "valid": valid,
        "pending": pending,
        "events": events or [],
        "nearby_agents": [],
    }
    return json.dumps(payload, ensure_ascii=False)
