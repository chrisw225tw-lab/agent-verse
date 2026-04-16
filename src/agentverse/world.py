"""World data model — tree of nodes and edges. See GDD §3."""

from __future__ import annotations

from dataclasses import dataclass, field

from .tiles import Tile


@dataclass
class Node:
    id: str
    exits: list[str] = field(default_factory=list)   # edge ids


@dataclass
class Edge:
    id: str
    from_node: str
    to_node: str
    type: str              # "action" | "social" | "trade"
    length: int            # 8..40
    tiles: list[Tile] = field(default_factory=list)
    cleared_by: set[str] = field(default_factory=set)


@dataclass
class World:
    root: str
    nodes: dict[str, Node] = field(default_factory=dict)
    edges: dict[str, Edge] = field(default_factory=dict)


@dataclass
class Entity:
    id: str
    edge: str
    pos: int = 0
    hp: int = 100
    coins: int = 0
    keys: int = 0
    inventory: list[str] = field(default_factory=list)
    alive: bool = True


def build_starter_world() -> World:
    """Stage 1 placeholder — a single empty corridor off the root.

    Replace with a real procedural generator once the engine lands.
    """
    w = World(root="n0")
    w.nodes["n0"] = Node(id="n0", exits=["e0"])
    w.nodes["n1"] = Node(id="n1", exits=["e0"])
    w.edges["e0"] = Edge(
        id="e0",
        from_node="n0",
        to_node="n1",
        type="action",
        length=10,
        tiles=[Tile(kind="empty") for _ in range(10)],
    )
    return w
