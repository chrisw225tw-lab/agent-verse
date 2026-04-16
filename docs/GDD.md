# agent-verse — Game Design Document

## 1. Vision

A **horizontal tree-structured exploration game** designed for AI agents to play via CLI. Each section of the world is a 1D side-scrolling path (like Mario) with items, hazards, and NPCs. Sections connect at junction nodes forming a tree. The tree grows as agents/players create new sections, forming an emergent shared world.

**Core tension:** Simple enough for a 1B local model to play, rich enough for a frontier model to strategize.

**End-state vision:** Anyone joins with their own agent (OpenClaw, Claude Code, local Ollama, custom script) and coexists in a shared, ever-expanding tree world — exploring, trading, building, and encountering each other.

---

## 2. Staged Roadmap

| Stage | Scope | Networking | Status |
| :---- | :---- | :---- | :---- |
| **1 — Local Walking** | Single agent, CLI stdin/stdout, single Python file | None | NOW |
| **2 — Expand World** | Agent-created sections, persistence (JSON→SQLite), fog of war | None | TODO |
| **3 — Multiplayer Server** | FastAPI/WebSocket or Evennia, multi-agent simultaneous play | Server | TODO |
| **4 — Mobile** | React/web viewer for spectating, touch controls | Web | TODO |

Each stage is shippable independently. Stage 1 is the foundation — if the CLI game isn't fun for an agent, nothing else matters.

---

## 3. Data Model

As simple as possible. The entire world is a tree graph of nodes and edges.

```text
World = {
  nodes: {
    [node_id]: {
      exits: [edge_id, ...]    // connected sections
    }
  },
  edges: {
    [edge_id]: {
      id:     string,
      from:   node_id,          // left end
      to:     node_id,          // right end
      type:   "action" | "social" | "trade",
      length: int,              // tile count (8-40)
      tiles:  [{kind: string}]  // array of length tiles
    }
  },
  root: node_id
}

Entity = {
  edge:      edge_id,
  pos:       int,               // 0..length-1
  hp:        int,               // 0-100
  coins:     int,
  keys:      int,
  inventory: [string],
  alive:     bool
}
```

**Design rules:**

- No nested objects deeper than 2 levels
- All IDs are short strings: `n0`, `e3`
- Tile is just `{kind: string}` — nothing else
- Entity has no "class" or "stats" beyond hp/coins/keys — keep flat

---

## 4. Tile System

Tiles are the atoms of gameplay. Every tile has a **kind** and belongs to one of four **categories** that determine how the game engine processes it.

### 4.1 Categories

| Category | Behavior | Movement | Agent decision? |
| :---- | :---- | :---- | :---- |
| **PASSIVE** | Auto-pickup when stepped on | Pass through | No — automatic |
| **TRIGGER** | Auto-fire damage when stepped on | Pass through (with pain) | No — automatic |
| **BLOCKING** | Stops movement, forces choice | Cannot pass without resolving | **YES — forced** |
| **SOCIAL** | Optional interaction available | Pass through freely | Optional |
| **EMPTY** | Nothing | Pass through | No |

### 4.2 Tile Kinds

**Passive tiles (auto-pickup, consumed):**

| Kind | Char | Effect |
| :---- | :---- | :---- |
| coin | ○ | +1 coin |
| potion | ♥ | +25 hp (capped at 100) |
| key | ⚷ | +1 key (used for gates) |

**Trigger tiles (auto-fire on step):**

| Kind | Char | Effect | Consumed? |
| :---- | :---- | :---- | :---- |
| spike | ▲ | 8-15 damage | No (permanent hazard) |
| trap | ✖ | 12-20 damage | Yes (one-time) |

**Blocking tiles (STOP movement, force decision):**

| Kind | Char | Options presented |
| :---- | :---- | :---- |
| hole | ◌ | 1) jump (costs 10hp) 2) back |
| guard | ☻ | 1) pay (costs 5 coins) 2) fight (take 10-20dmg, 50% fail) 3) retreat |
| gate | ▯ | 1) unlock (costs 1 key) 2) back |
| boss | ☠ | 1) fight (take 15-30dmg, 40% fail, +10coin reward) 2) retreat |

**Social tiles (optional, pass-through):**

| Kind | Char | Interaction |
| :---- | :---- | :---- |
| npc | ☺ | Talk — returns a line of dialogue/lore |
| merchant | $ | Shop — buy potion(3coin), key(5coin) |
| sign | ⌂ | Read — directional hint or lore |
| portal | ◈ | Stage 2: user-created section entrance |

### 4.3 Movement + Tile Resolution Sequence

When agent issues `move right N`:

```text
for each tile from current_pos+1 toward target:
    1. Check tile category
    2. If PASSIVE → apply effect, consume tile, continue
    3. If TRIGGER → apply damage, maybe consume, continue
       - If hp <= 0 → DEAD, stop
    4. If BLOCKING → STOP here (one tile before blocker)
       - Set pending forced choice
       - Return state + forced options
    5. If SOCIAL or EMPTY → continue
    6. Update position after each successful step
```

**Key rule: `move right 5` does NOT guarantee you move 5 tiles.** You might stop at tile 3 because a hole is at tile 4. This is what makes the game interesting — blind movement is risky, and agents must reason about what's ahead in their local view.

---

## 5. Agent Interface — Three Tiers

The game supports three input modes simultaneously. The server always outputs the same state format; only the input parsing differs.

### 5.1 Tier 0 — Index Pick (cheapest, 1B+ local model)

Agent sees numbered options, outputs a single number.

```text
[e0:action 5/19 path:n0→e0] @·○·▲·☺·◈ hp:100 coin:0 key:0
VALID: 1)right(4max) 2)left 3)status 4)map
> 3
```

**Token budget:** ~60-80 input tokens, 1-3 output tokens. **System prompt:** ~100 tokens explaining format. **Works with:** qwen2.5:7b, phi-3-mini, llama3.2:3b, any local model via Ollama.

### 5.2 Tier 1 — Keyword CLI (mid-tier, 7B+ or Haiku)

Agent outputs short keyword commands.

```text
[e0:action 5/19 path:n0→e0] @·○·▲·☺·◈ hp:100 coin:0 key:0
VALID: 1)right(4max) 2)left 3)status 4)map
> right 3
moved→6 +1coin moved→7 moved→8
[!] HOLE at 9 — must: 1)jump(-10hp) 2)back
> jump
```

**Token budget:** ~80-100 input tokens, 3-10 output tokens. **Commands:** `right [n]`, `left [n]`, `enter <eid>`, `map`, `status`, `talk`, `shop`, `read`, `jump`, `pay`, `fight`, `retreat`, `back`, `unlock`

### 5.3 Tier 2 — JSON Mode (API models, Sonnet/GPT-4o)

Launch with `--json` flag. State and actions are JSON.

```json
{"state": {"edge":"e0","type":"action","pos":5,"length":20,
  "path":["n0","e0"],"hp":100,"coins":0,"keys":0,
  "view":["empty","coin","empty","spike","empty","npc"],
  "view_offset":3},
 "valid":[
   {"idx":1,"cmd":"right","args":{"max":4}},
   {"idx":2,"cmd":"left"},
   {"idx":3,"cmd":"status"},
   {"idx":4,"cmd":"map"}],
 "pending":null}
```

Agent responds:

```json
{"action": 1, "args": {"n": 3}}
```

Or:

```json
{"action": "right", "n": 3}
```

**Token budget:** ~150-250 input, 10-30 output. **Advantage:** Machine-parseable, no ambiguity, supports tool-use function calling.

### 5.4 Input Parsing Priority

The game engine tries to parse input in this order:

1. **Pure integer** → Tier 0 index pick
2. **JSON object** → Tier 2 structured
3. **Keyword string** → Tier 1 command parse
4. **Fallback** → "Unknown command. Type help."

This means ANY agent can talk to the same game instance — no mode switching needed.

---

## 6. Information Hierarchy

How agents build a mental model of the world without flooding the context window.

### 6.1 Always Present — Breadcrumb (~10 tokens)

Every state line includes the path from root to current position:

```text
[e2:action 5/24 path:n0→e0→n1→e2]
```

**Cost:** Nearly zero. Agent always knows depth, which branches it took. **Purpose:** GPS — "where am I in the tree?"

### 6.2 Local View — Nearby Tiles (~20 tokens)

ASCII strip showing ±8 tiles around player:

```text
··○·@▲·☺··◌·
```

`@` = player. Agent can see hazards ahead and plan movement distance. **Purpose:** Tactical awareness — "what's immediately around me?"

### 6.3 On-Demand — Map Command (~50-80 tokens)

Agent spends one turn to see the explored tree structure:

```text
> map
n0 ─e0:action(20)✓─ n1 ─e3:action(25)─ n4[dead end]
 │                    └─e4:social(14)─ n5[???]
 ├─e1:social(16)─ n2 ─e5:trade(20)─ n6[dead end]
 └─e2:trade(18)─ n3[2 unexplored]
★ You: e0 pos 5  ✓=cleared
```

**Fog of war:** Unexplored branches show `[???]` or `[N unexplored]`. Only sections the agent has entered reveal their type, length, and connections.

**Cost:** 1 turn. This is a strategic decision — "should I pause to plan or keep moving?"

**Purpose:** Strategic planning — "which branches have I explored? Where should I go next?"

### 6.4 Agent-Side — Memory (agent's responsibility)

The game does NOT provide memory. Smart agents build their own:

- Track visited edges and items found
- Remember which junctions have unexplored exits
- Plan backtrack routes
- Record NPC dialogue for clues

This is where the quality gap between a 1B model and a frontier model becomes apparent. The game provides structured, parseable output — what the agent does with it is its own problem.

**Reference:** LPLH framework's internal graph-based mapping is the gold standard for this.

---

## 7. Section Types

Three types that create variety in the tree and test different agent skills.

### 7.1 Action

**Challenge:** Survive hazards, manage HP. **Tile density:** High — lots of spikes, traps, holes, bosses. **Passive items:** Coins, potions (HP recovery crucial). **Agent skill tested:** Risk assessment, HP management, fight-or-flee decisions.

**Generation rules:**

- 15% chance passive tile
- 10% chance trigger tile
- 5% chance blocking tile
- Spikes are permanent, traps are one-time
- At least one potion per 15 tiles

### 7.2 Social

**Challenge:** Gather information, find hints. **Tile density:** Low hazards, many NPCs and signs. **NPC interactions:** Dialogue that may hint at other sections' contents. **Agent skill tested:** Information gathering, deciding what's relevant.

**Generation rules:**

- 10% chance passive tile
- 4% chance blocking tile (guard only)
- 16% chance social tile (npc, sign)
- Guards require conversation or payment, not combat

### 7.3 Trade

**Challenge:** Resource management, buy what you need. **Tile density:** Merchants, gates (need keys), moderate hazards. **Economy:** Coins are scarce, prices are fixed, keys unlock shortcuts. **Agent skill tested:** Resource allocation, planning purchases.

**Generation rules:**

- 12% chance passive tile
- 5% chance blocking tile (gate, guard)
- 11% chance social tile (merchant, npc, sign)
- At least one merchant per section

---

## 8. Forced Encounters — The Core Mechanic

This is what separates agent-verse from a trivial "move right until done" game.

### 8.1 Pending State

When agent hits a BLOCKING tile, the game enters **pending state**:

- Normal movement commands are disabled
- Only the forced options are available
- Agent MUST resolve before doing anything else

```text
moved→7 [!] GUARD blocks: "5 coins to pass"
must: 1)pay(5coin) 2)fight 3)retreat
>
```

The `pending` field in state is non-null, and `valid_actions` returns only the forced options.

### 8.2 Consequence Design

Every forced choice is a tradeoff — there's no free option:

| Encounter | Option A | Option B | Option C |
| :---- | :---- | :---- | :---- |
| Hole | jump: -10hp | back: lose progress | — |
| Guard | pay: -5coin | fight: risk hp + 50% chance blocked | retreat: lose progress |
| Gate | unlock: -1key | back: lose progress | — |
| Boss | fight: risk hp, +10coin if win, 40% fail | retreat: lose progress | — |

**"Fight fail" means:** You take full damage AND don't pass. You can try again (costs another turn + more damage risk) or retreat.

### 8.3 Death

HP reaches 0 → game over. Agent gets a summary:

```text
DEAD! Final: coins:12 keys:1 edges_explored:4/6 sections_cleared:2
```

In Stage 3 (multiplayer), death means respawn at root with inventory loss.

---

## 9. Section Creation (Stage 2+)

### 9.1 Create Command

At any junction node, an agent can create a new branch:

```text
> create action 20
✨ Created e7:action(20) from n3. New dead end: n7.
Costs: 10 coins (world building fee)
```

**Constraints:**

- Must be at a junction (pos 0 or pos length-1)
- Costs 10 coins
- Length: 8-40
- Type: action/social/trade
- Tiles are procedurally generated

### 9.2 Creator Attribution

Each edge stores `creator: entity_id`. Creators earn 1 coin each time another agent completes their section.

### 9.3 Portal System (Stage 2+)

Advanced creators can place portals that link non-adjacent nodes, breaking the tree into a graph. Portals require:

- Being at the destination node
- 20 coins
- A key

This creates shortcuts and loops, evolving the tree into a richer topology.

---

## 10. Multi-Agent Interactions (Stage 3+)

### 10.1 Encounters

When two agents occupy the same tile, both are notified:

```text
[!] Agent "TradeBot" is here.
extra: 1)talk 2)trade 3)ignore
```

This is NOT blocking — agents can ignore each other. But social/trade sections reward cooperation.

### 10.2 Trading

Agents on the same tile can propose trades:

```text
> trade TradeBot offer 3coin want 1key
TradeBot: ACCEPT
-3coin +1key
```

### 10.3 Communication

Agents can send short messages to nearby agents (same section):

```text
> say "boss ahead at pos 22, needs ~20hp"
```

Other agents in the section receive:

```text
[msg from Explorer] "boss ahead at pos 22, needs ~20hp"
```

---

## 11. CLI Protocol Specification

### 11.1 Text Mode (default)

**State output format:**

```text
[{edge_id}:{type} {pos}/{max_pos} path:{breadcrumb}] {ascii_strip} hp:{hp} coin:{coins} key:{keys}
VALID: 1){label} 2){label} ...
```

When pending (forced encounter):

```text
[!] {encounter_description}
must: 1){option} 2){option} ...
```

**Event output (between state lines):**

```text
moved→{pos} {events_space_separated}
```

Events: `+1coin`, `+25hp`, `-12hp(spike!)`, `+1key`, `DEAD!`

### 11.2 JSON Mode (`--json` flag)

Every output is a single JSON line:

```json
{
  "state": {
    "edge": "e0", "type": "action",
    "pos": 5, "length": 20,
    "path": ["n0", "e0"],
    "hp": 100, "coins": 3, "keys": 1,
    "view": ["empty","coin","empty","spike","empty"],
    "view_offset": 3,
    "alive": true
  },
  "valid": [
    {"idx": 1, "cmd": "right", "max": 4, "label": "right(4max)"},
    {"idx": 2, "cmd": "left", "label": "left"},
    {"idx": 3, "cmd": "map", "label": "map"},
    {"idx": 4, "cmd": "status", "label": "status"}
  ],
  "pending": null,
  "events": ["+1coin", "-12hp(spike!)"],
  "nearby_agents": []
}
```

**JSON input accepted:**

```json
{"action": 1}
{"action": "right", "n": 3}
```

### 11.3 Map Output Format (text mode)

```text
n0 ─e0:action(20)✓─ n1 ─e3:action(25)─ n4[dead end]
 │                    └─e4:social(14)─ n5[???]
 ├─e1:social(16)─ n2 ─e5:trade(20)─ n6[dead end]
 └─e2:trade(18)─ n3[2 unexplored]
★ You: e0 pos 5   ✓=cleared  ???=unexplored
```

### 11.4 Map Output Format (JSON mode)

```json
{
  "map": {
    "nodes": {
      "n0": {"explored": true, "exits": ["e0","e1","e2"]},
      "n1": {"explored": true, "exits": ["e0","e3","e4"]},
      "n5": {"explored": false}
    },
    "edges": {
      "e0": {"type":"action","length":20,"cleared":true,"from":"n0","to":"n1"},
      "e4": {"type":"social","length":14,"cleared":false,"from":"n1","to":"n5"}
    },
    "current": {"edge":"e0","pos":5}
  }
}
```

---

## 12. Agent Wrapper Examples (Stage 1)

### 12.1 Minimal Tier 0 Agent (Ollama)

```python
import subprocess, requests

game = subprocess.Popen(
    ["python", "-m", "agentverse.game"],
    stdin=subprocess.PIPE, stdout=subprocess.PIPE,
    text=True
)

SYSTEM = "You play a text game. Reply with ONLY a number from VALID options."

while True:
    state = game.stdout.readline().strip()
    valid = game.stdout.readline().strip()
    if not state:
        break

    prompt = f"{state}\n{valid}\nChoose:"
    resp = requests.post("http://localhost:11434/api/generate", json={
        "model": "qwen2.5:7b",
        "prompt": f"{SYSTEM}\n\n{prompt}",
        "stream": False
    })
    choice = resp.json()["response"].strip().split()[0]
    game.stdin.write(choice + "\n")
    game.stdin.flush()
```

### 12.2 Tier 2 Agent (Claude API)

```python
import subprocess, json, anthropic

game = subprocess.Popen(
    ["python", "-m", "agentverse.game", "--json"],
    stdin=subprocess.PIPE, stdout=subprocess.PIPE,
    text=True
)

client = anthropic.Anthropic()
history = []

SYSTEM = """You are playing agent-verse. Each turn you receive JSON state with valid actions.
Respond with JSON: {"action": <index_or_command>}
Strategy: explore all branches, manage HP, collect coins, use map at junctions."""

while True:
    line = game.stdout.readline().strip()
    if not line:
        break
    state = json.loads(line)
    if not state["state"]["alive"]:
        break
    history.append({"role": "user", "content": json.dumps(state)})
    # Trim history to last 20 turns (context management)
    if len(history) > 40:
        history = history[-40:]

    resp = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=100,
        system=SYSTEM,
        messages=history
    )
    answer = resp.content[0].text
    history.append({"role": "assistant", "content": answer})
    game.stdin.write(answer + "\n")
    game.stdin.flush()
```

### 12.3 Human Player

```bash
python -m agentverse.game
# Just type commands or numbers. No wrapper needed.
```

---

## 13. Scoring & Win Conditions

### 13.1 Section Completion

An agent "clears" a section by reaching the far end (pos = length-1). This is tracked per-agent.

### 13.2 Run Score

```text
score = (coins × 1) + (sections_cleared × 10) + (unique_nodes_visited × 5) - (turns_taken × 0.1)
```

### 13.3 No Global Win

There is no "beat the game" state. The tree can grow infinitely. Value comes from:

- Exploration coverage (% of tree visited)
- Wealth accumulation
- Sections created (Stage 2+)
- Agent encounters and trades (Stage 3+)

This is an **open-ended sandbox**, not a linear campaign.

---

## 14. Reference Repositories

| Repo | Why relevant | Key takeaway |
| :---- | :---- | :---- |
| [Evennia](https://github.com/evennia/evennia) | Production Python MUD engine | Stage 3 backbone candidate — handles networking, DB, multi-user |
| [DennisMUD](https://github.com/seisatsu/DennisMUD) | Player-created world via in-game commands | `create` command pattern, telnet+websocket dual access |
| [TextArena](https://github.com/LeonGuertler/TextArena) | 74+ text game envs, multi-agent, TrueSkill | Agent wrapper protocol, competitive ranking |
| [TALES](https://github.com/microsoft/tale-suite) | LLM text game benchmark | Agent scaffolding patterns, vLLM local model support |
| [GamingAgent](https://github.com/lmgame-org/GamingAgent) | ICLR 2026, harness for LLM game agents | Config-driven harness, observation/action separation |
| [MUDGPT/Holodeck](https://github.com/darvin/Holodeck) | LLM-generated MUD world | Auto-generated locations and quests |
| [OpenClaw](https://github.com/openclaw/openclaw) | Config-first agent framework | SOUL.md + skills pattern, Ollama support, natural agent entry point |

---

## 15. Design Principles

1. **Agent-first, human-watchable.** Every design decision optimizes for agent playability. The frontend is a spectator tool, not the primary interface.
2. **Token budget is law.** State output must stay under 150 tokens for Tier 0/1. Every field earns its place.
3. **Deterministic engine, intelligent agents.** The game engine is pure logic — no randomness in rules, only in world generation. All runtime randomness (fight outcomes, damage rolls) uses seeded RNG for reproducibility.
4. **Forced decisions create intelligence signal.** The difference between a good and bad agent is how they handle blocking encounters, not how fast they type "move right."
5. **Enumerate, don't hallucinate.** Always provide valid action list. Never require the agent to guess command syntax.
6. **Simple data, emergent complexity.** The tile system has ~14 kinds. The tree has nodes and edges. That's it. Complexity comes from their combinations and the agent's planning.
7. **Layered information.** Local view is free (tactical). Map costs a turn (strategic). Memory is the agent's job (intelligence). This creates a natural skill gradient.
8. **Grow, don't ship.** The world starts small and grows through play. Stage 2+ lets agents expand it. There's no "content update" — the players ARE the content.
