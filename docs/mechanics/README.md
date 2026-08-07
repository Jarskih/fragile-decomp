# mechanics — notes on the original game's exact mechanics

This directory collects **our own written analysis** of how the game works, so
that a faithful reimplementation can be built from the documentation alone.
This is the primary deliverable of the decompilation phase.

## What goes here

Precise, evidence-backed descriptions of gameplay mechanics:

- economy: ore values, prices, production rates, upkeep, taxes
- construction: build times, costs, placement rules
- blueprints / technology: the 36 blueprints, prerequisites, effects
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

- `main-loop.md` — the per-tick game-state dispatcher and the subsystem
  functions/globals it drives (economy, relations, fleets, events, terrain,
  building, victory states).
- `diplomacy.md` — reference-build relations analysis: the per-pair opinion
  matrices (0xd000-range block), the Non-Aggression-Pact / Joint-Combat-
  Treaty node machinery, incident/violation counters and fines, the alien
  offer decisions, and the tribute contracts.
- `asteroid-spawning.md` — the new default game: home asteroid, creation,
  placement, daily drift, growth gate, custom size/density settings.
- `asteroid-field-maintenance.md` — the population keeper, the "budding"
  respawn rule, movement and types (from savegame diffs).
- `ore-and-mining.md` — the ten ores, the three rarity tiers, mine buildings,
  ore generation at asteroid creation, deposit placement, mining depletion.
- `vehicles.md` — the craft the player builds: the roster from the game's
  text resource, construction (Ship Yards / Orbital Space Dock / blueprints),
  hardpoints, fleet rules, and the status of the per-class stat tables.
- `colony-surface-grid.md` — the colony building grid: terrain-record table,
  surface objects, crater/building cells, colony-view sprite building, the
  lazy "Create_Surface_Map" creator (unrecovered).
- `turrets-and-defence.md` — the defence buildings (Laser/Plasma/Photon
  Turrets, Anti-Missile Pods, alien equivalents), the firing behaviour from
  the game text, and the reference-build defence state machine; per-turret
  damage/range numbers still open (tables-in-code anomaly, runtime trace
  deferred).
- `asteroid-creation.md`, `rng.md` — reference-build notes (see
  `asteroid-spawning.md` for the GOG address table).

## Build-identity warning (read before citing addresses)

The address tables in `main-loop.md`, `asteroid-spawning.md`,
`ore-and-mining.md` and `asteroid-field-maintenance.md` were written against
the **GOG retail build**, whose EXE is not part of this repository. The
current pipeline (`make all` against the archive.org reference ISO) produces
the **reference build**: its `main` dispatcher is at 0x36b64 (not 0x34720),
`asteroid_create` is at 0x11a64 (not 0x117b4), the object-list sentinel is
0xc3f4 (not 0xbd18), the home block is at 0x11274 (not 0x11084), and the
main RNG state is at 0x4cd7c (not 0x6f854). The savegames under
`build/iso/_SAVE` decode with the GOG build's offsets. The two builds
implement the same game, but **addresses and node offsets are not
interchangeable between them**; `docs/mechanics/vehicles.md` documents this
in detail. Re-baselining the older tables onto the current image is open
work.
