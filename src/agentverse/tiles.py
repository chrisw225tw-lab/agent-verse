"""Tile kinds and categories.

Every tile has a `kind` (string) and belongs to one of four categories that
determine how the engine processes it. See docs/GDD.md section 4.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Category(str, Enum):
    EMPTY = "empty"
    PASSIVE = "passive"    # auto-pickup when stepped on
    TRIGGER = "trigger"    # auto-fire damage when stepped on
    BLOCKING = "blocking"  # stops movement, forces a choice
    SOCIAL = "social"      # optional interaction, pass-through


# kind -> (category, ascii_char)
TILE_SPEC: dict[str, tuple[Category, str]] = {
    # Empty
    "empty":    (Category.EMPTY,    "·"),

    # Passive (auto-pickup, consumed on step)
    "coin":     (Category.PASSIVE,  "○"),
    "potion":   (Category.PASSIVE,  "♥"),
    "key":      (Category.PASSIVE,  "⚷"),

    # Trigger (auto-fire damage on step)
    "spike":    (Category.TRIGGER,  "▲"),   # permanent
    "trap":     (Category.TRIGGER,  "✖"),   # one-time

    # Blocking (stop, force choice)
    "hole":     (Category.BLOCKING, "◌"),
    "guard":    (Category.BLOCKING, "☻"),
    "gate":     (Category.BLOCKING, "▯"),
    "boss":     (Category.BLOCKING, "☠"),

    # Social (pass-through, optional talk/trade)
    "npc":      (Category.SOCIAL,   "☺"),
    "merchant": (Category.SOCIAL,   "$"),
    "sign":     (Category.SOCIAL,   "⌂"),
    "portal":   (Category.SOCIAL,   "◈"),
}


@dataclass
class Tile:
    kind: str

    @property
    def category(self) -> Category:
        return TILE_SPEC[self.kind][0]

    @property
    def char(self) -> str:
        return TILE_SPEC[self.kind][1]


def char_for(kind: str) -> str:
    return TILE_SPEC[kind][1]


def category_of(kind: str) -> Category:
    return TILE_SPEC[kind][0]
