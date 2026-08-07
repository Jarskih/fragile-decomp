---
title: Asteroid spawning — implementation instructions
---

# Asteroid spawning — implementation instructions

*Status: written from the technical analysis (`docs/mechanics/asteroid-spawning.md`,
`docs/mechanics/asteroid-field-maintenance.md`, `docs/mechanics/colony-surface-grid.md`).
Items marked (?) are inferred or unverified and flagged in "Things to verify".*

This page is the build brief for implementing the asteroid-field system in a
reimplementation. It describes **what the game does** in implementable terms.
The random-number arithmetic is in [Randomness and determinism](randomness.md)
and must be implemented exactly as described there; this page builds on it.

The system has five moving parts, implemented in this order: **universe
creation**, **content generation**, **movement**, **population maintenance**
and **the colony surface**.

## 1. Universe creation

### A new game

1. Initialise the **universe stream** with the fixed starting value **12345**
   (the same value every new game).
2. Create the player's home asteroid:
   - roll its **surface style** — a value 4..8 from the universe stream;
   - roll its **size parameter** — `2 * (12 + (style-4)*3/5 + roll(2)) + 1`,
     which lands on an odd number in 25..31;
   - roll its **seed** — two consecutive 16-bit draws of the universe stream
     combined into one 32-bit number (not derived from the name);
   - **place** it at the fixed cell that depends only on the arena size
     (same cell every new game, not random);
   - assign it **type 1** (TetraCorp, the player's own colony) and the
     player's name.
3. Nothing else spawns at start. The home asteroid is the only object until
   the growth gate (section 4) begins topping the field up.

### Arena settings

- **Arena size** (Small/Medium/Large) fixes the playfield: Small is 24×15
  cells, Medium 29×18, Large 32×20. **One cell = 32 units** on both axes.
- **Asteroid density** (Low/Medium/High) fixes the per-scenario **ceiling** —
  the target field population: Small holds 30/45/60 respectively, the standard
  campaign 60, Large/High 91.
- The absolute hard cap is **100 asteroids** at any one time. Creation simply
  fails when the cap is reached.

## 2. Content generation (per asteroid, from its seed)

Every asteroid's entire contents — surface terrain, ore seams, decorative
rocks — are a **pure function of its seed**. Implement one function
`generate_content(seed, size)` and call it whenever an asteroid's contents are
needed:

1. Work on a **private copy** of the universe stream (save the counter,
   generate, restore). Generation must never perturb live play rolls.
2. Generate the terrain as a size×size height field: build the height grid
   (spiral fill), then extract the surface cells inside the radius
   `size²/4`.
3. Lay the ore seams on a ring derived from the size.
4. Place 12 decorative rocks around the asteroid in two rings of 6, at fixed
   radii with random angular offset — pure decoration, no gameplay effect.

Determinism rule: the same seed must always produce the same asteroid. This is
the contract for save/load and for multiplayer (see [Randomness](randomness.md)).

## 3. Movement

- Every asteroid rolls **two values once, at placement**: a **speed** 0..5 and
  a **direction** index 0..255 into a 256-entry sine/cosine table.
- Each in-game day, a moving asteroid (speed ≥ 1) drifts:
  `x += speed * cos(dir) / 12`, `y += speed * sin(dir) / 12` (fixed point,
  16.16 — keep the fractional part).
- **Speed 0 asteroids never move.** This is observable and must be preserved.
- **Leaving the map**: if an asteroid's integer position leaves the arena,
  remove it and post the "drifted out of known space" event for the player's
  asteroid (for the player's own, the "Colony asteroid … drifted out" message).
- **Collisions**: asteroids whose circles overlap flag proximity; when the
  player's asteroid is involved, announce "Asteroid collision imminent".

## 4. Population maintenance

The field never spawns asteroids at the map border. Two mechanisms keep the
population up:

### The growth gate (during play)

Every **8 ticks**, while the field is below the scenario ceiling (section 1),
create one asteroid and place it **near the player** (search outward from the
player's cell for a free cell). This is how the field reaches its density
target early in the game.

### The population keeper (replacement)

When an asteroid is destroyed (drift-out, collision, mining, combat), the
keeper replaces it:

1. For each **owner type** in 0..14, if the type is enabled and at least one
   asteroid of that type survives:
   - find the **oldest surviving asteroid of that type** (creation order);
   - spawn the replacement **next to it**: random angle, distance 40..110
     units, re-rolling until the spot is at least **32 units** from every
     other asteroid (no limit on retries);
   - roll speed/direction for the new asteroid.
2. If a type has gone extinct (no survivor), that type is simply skipped.

Notes:

- "Types" are **owners**, not rock kinds: 0 unowned, 1 player (TetraCorp),
  2..8 the seven human corporations, 9..14 the six alien races.
- The keeper keeps the field pinned to the density target, so the count stays
  constant even under sustained losses.
- Consequence to preserve: **new asteroids appear in the interior, near
  survivors of their own type, never at the border** — the observed signature
  is pairs of asteroids 32..50 units apart (bud radius 40..110 minus the
  32-unit clearance).

## 5. The colony surface (what you build on)

The colony view of an asteroid is built **lazily** when the asteroid is
entered:

1. The surface is the size×size terrain grid from section 2.
2. The surface is populated from **records**: each record type carries a
   subtype, and each subtype yields a fixed number of **surface cells**
   (1, 6 or 30 per record, per the subtype). Cells carry **grid coordinates**
   on the 0..31 grid.
3. Cells come in two kinds used by the view: **craters** (the surface
   features) and **building cells** (where buildings stand). The view shows
   at most **8 craters** at a time.
4. Buildings are placed near the **Sky Hook** and are positioned using the
   cell grid coordinates. Building construction proceeds through stages
   (scaffolding), which the building cells encode.
5. Rendering detail: buildings and craters are drawn as sprites whose screen
   positions are computed from the cell grid values via the view's scale
   table; keep this conversion a separate, testable function.

## Things to verify (?) — keep these configurable

- The fixed starting value **12345** for a new game: inferred from code, not
  yet confirmed in a live run (see the open question in
  [Randomness](randomness.md)).
- The exact record table (which subtype yields 1/6/30 cells) is read from a
  table whose static contents are **not confirmed** — implement it from the
  structure, with the counts as data the agent must fill from a live trace.
- The seed of the home asteroid is known from a save (0x50269FDC in the
  analysed build) — useful as a regression test for the RNG chain, not as a
  constant to hard-code.
- Whether the per-scenario ceiling or the 100-asteroid cap binds first in
  practice: the cap is the hard limit.

## Acceptance tests

1. **Determinism**: two new games with the same settings produce the same
   home asteroid (same size, same seed, same terrain), and the same field
   over the first N days.
2. **Density**: with standard settings the field settles at 60 asteroids
   (standard campaign) and stays pinned there across several hundred days of
   simulated play with losses enabled.
3. **No border spawns**: over a long simulated game, no new asteroid ever
   appears within 32 units of the map edge (initial layout excepted).
4. **Budding signature**: with losses enabled, pairs of asteroids 32..50
   units apart appear, and replacements cluster near surviving same-type
   asteroids.
5. **Speed 0**: a speed-0 asteroid's coordinates never change.
6. **Drift-out**: an asteroid leaving the map is removed and the event fires;
   a drift-out is never "relocated".
7. **Seed invariance of content**: `generate_content(seed, size)` returns
   identical output for the same seed and does not disturb the live random
   stream.
