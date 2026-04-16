"""Sanity checks on the tile registry."""

from __future__ import annotations

from agentverse.tiles import TILE_SPEC, Category, category_of


def test_all_gdd_kinds_registered():
    expected = {
        "empty", "coin", "potion", "key",
        "spike", "trap",
        "hole", "guard", "gate", "boss",
        "npc", "merchant", "sign", "portal",
    }
    assert expected.issubset(TILE_SPEC.keys())


def test_categories_match_gdd():
    assert category_of("coin") is Category.PASSIVE
    assert category_of("spike") is Category.TRIGGER
    assert category_of("guard") is Category.BLOCKING
    assert category_of("npc") is Category.SOCIAL
    assert category_of("empty") is Category.EMPTY
