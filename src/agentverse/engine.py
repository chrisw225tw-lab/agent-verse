"""Game engine: movement + encounter resolution.

Stage 1 scaffold. The core loop (GDD §4.3) is intentionally left as TODO so
the first real PR has an obvious, bounded target.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .tiles import Category, category_of
from .world import Entity, World


@dataclass
class StepResult:
    events: list[str] = field(default_factory=list)
    pending: Optional[dict] = None   # set when a BLOCKING tile is reached


def view(world: World, entity: Entity, radius: int = 8) -> tuple[list[str], int]:
    """Return (kinds[], view_offset) — a ±radius window around the entity."""
    edge = world.edges[entity.edge]
    lo = max(0, entity.pos - radius)
    hi = min(edge.length, entity.pos + radius + 1)
    kinds = [edge.tiles[i].kind for i in range(lo, hi)]
    return kinds, lo


def move(world: World, entity: Entity, direction: int, n: int) -> StepResult:
    """Move `n` tiles in `direction` (+1 right, -1 left) with tile resolution.

    TODO(stage-1): implement per GDD §4.3.
      - iterate tile-by-tile
      - PASSIVE: apply effect, consume tile
      - TRIGGER: apply damage, consume if one-time (trap), check death
      - BLOCKING: stop, return pending forced options
      - SOCIAL/EMPTY: pass through
    """
    raise NotImplementedError("engine.move — see GDD §4.3")


def resolve_pending(world: World, entity: Entity, choice: str) -> StepResult:
    """Resolve a pending blocking encounter (hole/guard/gate/boss).

    TODO(stage-1): implement per GDD §8.
    """
    raise NotImplementedError("engine.resolve_pending — see GDD §8")


__all__ = ["StepResult", "view", "move", "resolve_pending", "Category", "category_of"]
