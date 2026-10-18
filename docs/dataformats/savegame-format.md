# Savegame file format (.000–.009, GOG build)

Status: confirmed by direct binary analysis of saves produced by the GOG
retail build. All offsets are file offsets.

## File size

Every observed save is exactly **548472 bytes (0x85E78)**.

## Top-level layout

| offset | content |
|--------|---------|
| 0x00000 | `"SAVEGAME"` magic block |
| 0x00020 | `"SAVEDATA"` block header |
| 0x00030 | SAVEDATA data (43344 bytes = 0xA950, ends at 0xA980) |
| 0x0A980 | `"SIM_HEAP"` — the sim-object heap dump |
| ~0x2EF9C … 0x3AA4C | master object pool (476-byte nodes) — **offset varies** |
| 0x3A990 | `"BUILDING"` section |
| 0x697A8 | `"SHIPS"` section |
| 0x84250 | `"SHOTS"` section |
| 0x85E68 | `"SAVE_END"` marker |

The section markers (`SIM_HEAP`, `BUILDING`, `SHIPS`, `SHOTS`, `SAVE_END`) are
also present in the EXE's data segment (flat offsets 0x91C04/0x91C28/0x91C4C/
0x91C70/0x91C94) — they are the format templates the save routine writes.

## Headers

```
0x00  "SAVEGAME\0\0\0\0"   magic
0x0C  dword 0x00085E58      file size minus 32 (observed, role unconfirmed)
0x10  dword 0x00002717      constant (10007) across all observed saves
0x20  "SAVEDATA\0\0\0\0"   magic
0x28  dword 0x0000A950      SAVEDATA section size (43344)
0x34  dword                 varies per save — likely the saved RNG state
                            (e.g. 0xD7B76CA1 in SAVEGAME.008, 0xD5435D83 in
                            small-low, 0x5DCC018B in medium-medium,
                            0x3D2FE517 in large-high)
```

## The master object pool

A contiguous array of **476-byte (0x1DC) nodes**. The pool base **moves between
saves** (e.g. 0x2EF9C in SAVEGAME.008, 0x339FC in SAVEGAME.009/.000) because
the heap layout depends on allocation history. Locate it by scanning for the
name field instead of using a fixed offset.

Asteroid nodes are found by scanning for `"AST:"` (node start = match − 0x4C)
and walking forward in 0x1DC steps while the name at +0x4C still starts with
`"AST:"`.

### Node layout (shared with the runtime master-list nodes)

| offset | size | field |
|--------|------|-------|
| 0x00 | dword | master-list next link (sentinel 0xBD18) |
| 0x04 | dword | second list link |
| 0x41 | byte | drift speed, 0..5 (0 = stationary) |
| 0x42 | byte | direction index, 0..255 (into sin/cos tables) |
| 0x44 | dword | X position, 16.16 fixed point |
| 0x48 | dword | Y position, 16.16 fixed point |
| 0x4C | 16 B | name, e.g. `"AST:RTG-056"` |
| 0xC0 | byte | **type**: 0 unowned, 1 TetraCorp (home), 9..14 alien/special; 255 = node mid-destruction |
| 0x138 | byte | flags (bit 0 set = skip drift movement) |

Names are unique per object and persist across saves — a name set diff between
two saves identifies which asteroids were destroyed and which appeared.

### Further asteroid-node fields (save diffs)

Established by diffing a chain of saves from one session (day 1504 → 1509 →
1527 → 1542) plus the other GOG saves:

| offset | size | field | confidence |
|--------|------|-------|------------|
| 0x5C | 10 × u16 | ore reserve per ore; falls as the ore is mined | high |
| 0xA4 | dword | copy of the global tick counter | high |
| 0xC2 | word | colony **population** (employees); copied into the daily air/food/water demand fields 0x176/0x178/0x17A. Settled colonies sit near 100–150, a new colony grows from its starting staff. Confirmed by code: see `docs/mechanics/life-support.md` | confirmed |
| 0xC8 | 40 × byte | building count per building type (Terran text order) | confirmed (code) |
| 0x150 | 10 × u16 | the player's mined-ore stock; rises 1:1 with the fall of 0x5C, on player-owned (type 1) nodes only | high |
| 0x18E | word | budding countdown, −1 per day on every owned asteroid | high |

The life-support state is also in the node (stored surpluses, radiation,
unrest, crime); the code-side field list is in
`docs/mechanics/life-support.md`. A first pass over the saves missed these
because their values barely move on a settled colony.

## SAVEDATA globals (save diffs)

| file offset | size | field | confidence |
|-------------|------|-------|------------|
| 0x0A4 | i32 × 6, stride 0x24 | per-race Money pools (runtime 0xBD58; the four funds and the debt are separate pools): 0xA4 is the human player, 0xC8/0xEC/0x110/0x134 the AI races, 0x158 always 0 | high (0xA4), medium (others) |
| 0x0A8..0x0C0 | 7 × dword | always 1,000,000 in every save; role unknown | — |
| 0x280 | dword | the player's Federal Transporter timer (runtime 0xBF34): −1 per day, arrival at 0, departure (ore sale) at −50, then restarts; see `docs/mechanics/economy-and-personnel.md` | confirmed (code) |
| 0xA04 | u32 | day counter, 0 in a new game | confirmed |
| 0xA08 | u32 | fraction of the day, 16.16 fixed point = tick_in_day × 0x800 | confirmed |
| 0xA978 | u32 | global tick counter (last dword of SAVEDATA) | confirmed |

**One game day is 32 ticks**: `[0xA978] = 32 × [0xA04] + [0xA08] / 0x800`
holds exactly in all 18 saves tested.

New games show 1,000,300 and 1,000,450 credits at day 0, i.e. a 1,000,000
starting balance plus the first ticks of income. Across a 38-day stretch of
one game the player's balance rose by a near-constant ≈1,470–1,490 Cr per
day, independent of how much ore was mined in the interval.

A hired spy agent occupies a small record around 0x594..0x5F0: 0x59C counts
down the days until it reaches the target, 0x5F0 the days of spying left
(the UI offers spy time in 5-day steps). Hiring did not change the credit
balance in these saves.

## Observed data points

| save | asteroids | X max | Y max | map (cells) |
|------|-----------|-------|-------|-------------|
| SAVEGAME.000 (standard) | 60 | 764 | 479 | 24 × 15 |
| custom-small-low-density | 30 | 756 | 471 | 24 × 15 |
| custom-small-medium-density | 45 | 686 | 437 | 24 × 15 |
| custom-small-highdensity | 60 | 758 | 471 | 24 × 15 |
| custom-medium-medium-density | 61 | 919 | 563 | 29 × 18 |
| custom-large-high-density | 91 | 1013 | 626 | 32 × 20 |

Cell size is 32 units on both axes (see `docs/mechanics/asteroid-field-maintenance.md`).

Note the medium map is 29×18 cells — a non-round number, suggesting the
size table at 0x1663c holds {24, 29, 32} × {15, 18, 20} rather than a single
scale factor applied to a base map.

## Open questions

- Meaning of the header dwords at 0x0C / 0x10 / 0x34 (0x34 is likely the
  saved RNG state but not yet verified against the RNG algorithm).
- Internal layout of the SIM_HEAP / BUILDING / SHIPS / SHOTS sections, and
  the rest of SAVEDATA (the master pool, the time fields and the credit pools
  are decoded).
- Cross-checking the life-support fields of `life-support.md` against the
  saves (a save, build one building, save pair would do it).
- The role of the 1,000,000 words at 0xA8..0xC0.
