# Asteroid field maintenance: population keeper and "budding" respawn

Status: confirmed by static disassembly of the GOG flat
(`build/flat/FRAGILE.EXE.flat`) and cross-checked against savegame dumps
(asteroid name/position diffs between consecutive saves). GOG image base
0x85760; addresses below are image-relative.

## The wrong mental model first

Asteroids that "slip out of known space" are **destroyed, not relocated**:
the daily drift tick (0x11364) removes an object whose X/Y (>>16) leaves
`[0, [0xc6dc]/[0xc6e0])` and posts the "drifted out of known space" event.
Nothing on that path creates a replacement, and no code path ever spawns
asteroids **at the map border**.

The field is instead kept at its target population by a separate pass — the
population keeper — which **buds new asteroids off existing ones of the same
type**. Empirically (SAVEGAME.009 → SAVEGAME.000): 4 asteroids disappeared
and 4 appeared; the 4 new ones were 28–64 units from surviving asteroids, at
interior positions, never at the border.

**Losses are not only border drift.** The 4 replaced asteroids died at
*interior* positions (715,399 / 591,11 / 626,20 / 403,118) — destroyed by
collisions, mining or ships, not by drifting out. The keeper replaces *any*
loss, which is why the field count stays pinned at the density target.

## The population keeper

Entry at **0xf884** (reached from the world-creation dispatcher 0xf854 when
`g_mode_flag != 0`, the slot-filling / arena path). It iterates the object
types and keeps each type's population up.

```
for type in 0..14:
    if not flag bit 0 of [0xcb5d + type*520]: skip type     ; type enabled?
    walk master list (sentinel 0xbd18, next at +0):
        find FIRST node whose type byte [+0xc0] == type      ; the anchor
    if none: skip type
    n = [0x16610] + [0x16611] + 2                            ; spawn count
    for i in 0..n:
        obj = asteroid_create()                                ; 0x117b4
        place_near(obj, anchor, ...)                         ; 0x11da4
```

- The anchor is the **oldest surviving asteroid of that type** (the master
  list is in creation order, so "first match" = oldest).
- All `n` buds attach to that single anchor per keeper pass.
- The spawn count config is read from the same config bytes that drive the
  scenario gate (`[0x16610]` = size index, `[0x16611]` = density index).

## place_near @ 0x11da4 ("budding")

```
loop:
    ang  = rng_next(256)                     ; direction index
    dist = base + rng_next(range)            ; base/range per call site:
                                             ;   40..63  (type-11 fast path)
                                             ;   72..109 (normal path)
                                             ;   40..109 (alternate path)
    X = anchorX + dist * cos[ang] >> 16
    Y = anchorY + dist * sin[ang] >> 16
    for every other object o in master list:
        if (o.X - X)² + (o.Y - Y)² <= 1024:  ; 32 units clearance
            retry loop                        ; re-roll ang/dist, no cap
    set obj.X/Y
asteroid_finalize()                            ; 0x11904: roll speed+dir
```

The sin/cos tables are the same pair used by the movement tick: 0x7eb70 /
0x7eaf0 (256 entries × 4 bytes, indexed by the direction byte).

**The tables are generated at runtime.** 0x20fb4 fills 320 4-byte entries
starting at 0x7eb6c with `fsin` (a `fildll`/`fmul`/`fsin`/`fistpl` loop, two
`fldl` scale constants at image-relative 0x176 / 0x16e — zeroed in the flat,
written at runtime). Curious detail: cos (0x7ecf0) sits only 96 entries past
sin (0x7eb70), not a quarter-circle offset — either the offset is not a
quarter turn or the entry math is off; unresolved.

## Speed and direction rolls (asteroid_finalize @ 0x11904)

Speed and direction are rolled once, at placement, and never change:

```
[obj+0x41] = table[0x9d78 + rng_next(16)]                    ; speed (0..5)
[obj+0x42] = table[0x9da0 + rng_next(12)] - 5 + rng_next(10) ; direction
```

Both tables hold code-like bytes in the flat (see the anomaly note in
`docs/mechanics/asteroid-spawning.md`); the exact runtime values are
unconfirmed statically.

## Movement ("are they all moving?")

No. Speed is a signed byte at `[+0x41]`, rolled at placement by
`asteroid_finalize` (0x11904) from the 16-entry table at 0x9d78 (plus a
direction roll from the 12-entry table at 0x9da0). Speed 0 nodes are
stationary; speeds 1–5 move. Verified: in every save analysed, exactly the
speed-0 asteroids had identical coordinates across two saves.

Per-day drift (the tick 0x11364, run once per day per object):

```
X += (speed * cos[dir]) / 12        ; all fixed-point 16.16
Y += (speed * sin[dir]) / 12
```

Observed movement magnitudes (SAVEGAME.009 → .000, |Δ| per speed): speed 1
≈ 23, speed 2 ≈ 45–47, speed 3 ≈ 50–72, speed 4 ≈ 94–95 units over the
window — roughly linear in speed.

## Types ("what are the types?")

The type byte `[+0xc0]` is 0..14. The game's per-type data lives in a
15-entry table at 0xcb5c (stride 0x208 = 520 bytes per type): slot counters
at 0xcb5c, enable flags at 0xcb5d, slot words at 0xcb56/0xcb5a/0xcb74, name
bytes at 0xb0a4 (15 names). The drift tick and the collision check compare
the type against the player's index `[0xc6b0]` to decide whether to raise a
player-facing message — consistent with types being owner/faction indices:
0 = unowned, 1 = TetraCorp (the player's home asteroid), 2..8 = HumanCorp
factions, 9..14 = the six alien races. The observed saves contain exactly
one type-1 node (the home asteroid) plus the type-0 field.

**Type 255 marks a node mid-destruction** (observed on one node while its
siblings were 0/1) — useful for filtering dying objects out of save dumps.

## A separate special-object spawner @ 0x13604

Unrelated to the keeper: a function at 0x13604 creates objects of types
11, 10, 9, 10, 11, 12, 13, 14 at an exact (X, Y) passed in registers,
bounds-checked against the arena, each going through `asteroid_finalize` with
a type argument. It has no static callers — it is reached via jump-table
dispatch (0x58612 is the per-type dispatch/allocator). Used for scenario /
special placements (the six tagged specials 9..14 of the fixed path, see
`asteroid-spawning.md`), not for field maintenance.

## Asteroid names

Always `AST:XXX-NNN` (three letters + three digits), e.g. `AST:RTG-056`.
Names are unique per object and permanent across saves — a name-set diff
between two saves is a reliable change detector for destroyed vs. new
asteroids.

## Why budding, not border spawns

The game keeps a uniform-density field alive by topping up each type's
population next to the oldest member of that kin. New asteroids therefore
appear near survivors anywhere in the interior — verified: the 4 new
asteroids in the save pair sat 28–64 units from existing asteroids, in
interior sectors, never at the border.

## Empirical cluster check

| save | NN median | pairs < 40 u |
|------|-----------|--------------|
| SAVEGAME.000 | 49 | 18 / 60 |
| small-low | 50 | 10 / 30 |
| medium-medium | 44 | 21 / 61 |
| large-high | 50 | 27 / 91 |

The sub-40-unit pairs are the budding signature (min clearance 32, bud radius
40–110 ⇒ pairs land 32–50 units apart). The field is otherwise near-uniform
random (median ≈ uniform expectation).
