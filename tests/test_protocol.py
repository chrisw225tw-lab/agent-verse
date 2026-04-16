"""Smoke tests for the input parser. Expand as the engine lands."""

from __future__ import annotations

from agentverse.protocol import parse_input


def test_integer_is_pick():
    a = parse_input("3")
    assert a.cmd == "pick" and a.args == {"idx": 3}


def test_json_is_structured():
    a = parse_input('{"action": 1}')
    assert a.cmd == "json" and a.args == {"action": 1}


def test_keyword_right_with_count():
    a = parse_input("right 4")
    assert a.cmd == "right" and a.args == {"n": 4}


def test_keyword_bare():
    a = parse_input("map")
    assert a.cmd == "map"


def test_empty_is_noop():
    a = parse_input("   \n")
    assert a.cmd == "noop"


def test_bad_json_falls_through():
    a = parse_input("{not json}")
    # falls through to keyword parsing
    assert a.cmd == "{not"
