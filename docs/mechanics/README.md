# mechanics — notes on the original game's exact mechanics

This directory collects **our own written analysis** of how the game works, so
that a faithful reimplementation can be built from the documentation alone.
This is the primary deliverable of the decompilation phase.

## What goes here

Precise, evidence-backed descriptions of gameplay mechanics:

- economy: ore values, prices, production rates, upkeep, taxes
- construction: build times, costs, placement rules
- blueprints / technology: the 36 priced Sci-Tek blueprints (38 catalogue entries), prerequisites, effects
- diplomacy: race dispositions, treaties, offers, consequences
- AI: race behaviour, thresholds, aggression scaling
- combat: weapon stats, ship stats, damage model, targeting
- world: asteroid generation, resource distribution, fog of war

Each claim should cite its evidence: a `build/reports/` artifact, a trace
(`build/traces/`), a function address in `build/decomp/`, or an observed
in-game test (cross-check with the online playable copy).

## Conventions

One file per topic, each with a status line:

```
Status: hypothesis | probing | confirmed
Source: disassembly | trace | in-game test | manual
```

Values that are still uncertain are marked `?` and revisited later. Nothing in
this directory is copied game data — it is our reconstruction, in our words.

## Index

Start with `main-loop.md` (dispatcher and cadence), then the topic notes.

- `main-loop.md` — the per-tick game-state dispatcher (states 0-0xf), the day
  cadence (32 ticks per day at default speed) and the subsystem
  functions/globals it drives; corrected 2026-10-18 for the day-count unit,
  supervisor/agent ticks, alien master tick and victory states.
- `life-support.md` — time base and calendar, the state driver, the daily
  colony update (population, air/food/water, power, radiation, workforce and
  unrest) and the random surplus-loss events.
- `economy-and-personnel.md` — the five money pools and the fund cascade,
  income (atmosphere-indexed stipend), Colony Supervisors, Agents and their
  mission prices, the Federal Transporter cycle.
- `alien-ai-trade-victory.md` — alien colonies and expansion, the hostility
  matrix, Non-Aggression Pacts and Joint Combat Treaties, game settings
  (arena, density, atmosphere, campaigns), win/lose rules (no time limit),
  trade, the black market and APVs; also lists the six alien race ids.
- `stat-tables-design-sheet.md` — consolidated designer view of the static
  stat tables: buildings (177), craft, hardpoint items, missiles, Sci-Tek
  prices, the agent mission table.
- `diplomacy.md` — reference-build relations analysis (partly overturned; read
  its correction box and `alien-ai-trade-victory.md` sections 6 and 10).
- `asteroid-spawning.md` — the new default game: home asteroid, creation,
  placement, daily drift, growth gate, custom size/density settings, with the
  static table values (ceilings, arena sizes, speed/direction tables).
- `asteroid-field-maintenance.md` — the population keeper, the "budding"
  respawn rule, movement and types (from savegame diffs).
- `ore-and-mining.md` — the ten ores, the three rarity tiers, mine buildings,
  ore generation at asteroid creation (with the static per-ore table),
  deposit placement, mining depletion.
- `scitek-blueprints.md` — the game's technology progression (there is no
  research mechanic): the 38-entry Sci-Tek brochure catalogue split into
  permanent upgrades / buildings / ships / missiles / hardpoints, what each
  item does, the ordering-and-delivery flow, and where the prices live.
- `vehicles.md` — the craft the player builds: the roster, construction
  (Ship Yards / Orbital Space Dock / blueprints), hardpoints, fleet rules and
  the 41-record craft stat table.
- `colony-surface-grid.md` — the colony building grid: record table,
  surface objects, crater/building cells, colony-view sprite building, the
  lazy "Create_Surface_Map" creator (unrecovered).
- `turrets-and-defence.md` — the defence buildings (Laser/Plasma/Photon
  Turrets, Anti-Missile Pods, alien equivalents) and what the game text and
  code say about them; there is no per-turret damage/range table.
- `building-stat-table.md` — the 177-row per-type structure stat table (armour,
  build days, cost, turret muzzle bytes) at GOG flat 0x8FFD4 (disp 0x9fd0),
  with the type-to-name mapping (type id = text index - 919).
- `weapons.md` — the firing pipeline and homing, and the missile warhead
  impact machine (the 0x200e4 family); part of its ship-weapon text is
  withdrawn (see its correction note).
- `ship-hit-formula.md` — missile impact and hit resolution: the per-tick
  strike roll, the blast/cone/scatter/walker warhead effects and the static
  per-launching-race numbers (GOG flat 0x91964).
- `weapon-and-turret-numbers.md` — where the combat/hardpoint tables really
  are (flat = displacement + 0x86004), the item price catalog, the colony
  event table, the overturned "fire delay 15/40" claim.
- `weapon-config-table.md` — the sprite descriptor table once mistaken for
  weapon stats.
- `asteroid-creation.md`, `rng.md` — reference-build notes (see
  `asteroid-spawning.md` for the GOG address table); their "tables in code"
  and "event scheduler" statements are superseded.

## Build-identity warning (read before citing addresses)

Two builds are analysed: the **GOG retail build** (`Fragile Allegiance/
FRAGILE.EXE`, flat `build/flat/FRAGILE.EXE.gog.flat`, the primary source for
numbers) and the **reference build** (archive.org / Interplay CD ISO, flat
`build/flat/FRAGILE.EXE.flat`). Their addresses are **not interchangeable**:
e.g. the dispatcher state byte is at 0x36b64 (reference) vs 0x34720 (GOG, where
`main` itself is the function at 0x14), `asteroid_create` is at 0x11a64 (reference) vs
0x117b4, the main RNG state at 0x4cd7c vs 0x6f854. Unless a note says
otherwise, addresses in these notes are GOG flat addresses.

**Data-table addressing (resolves the old "tables in code" anomaly).** Code
reads static tables through DS-relative *displacements* `D`. The bytes live at
**GOG flat `D + 0x86004`** (data object at flat 0x86000 plus the 4-byte image
header); the reference build uses `D + 0x8E004`. Reading `D` itself as a flat
offset lands in code, which is what the older notes reported as "code-like
bytes" / "runtime-only" tables. Code pointers stored in those tables are flat
- 4. Memdump offset = flat + 0x1C801C for flat >= 0x86000. The rename-map
keys for data tables are displacements; function keys are flat addresses. A
few tables really are runtime-filled (BSS, e.g. the sin/cos tables 0x7eaf0 and
the monthly ore prices 0xe808).
