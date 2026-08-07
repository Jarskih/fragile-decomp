# Asteroid creation

Status: creation routine, regeneration chain and the **placement machinery**
all confirmed (static disassembly), including the `asteroid_gen_start_values` →
`asteroid_rank_start_values` (+0x53) → `0x1e4dc` scale-row → `FUN_000319c4` tail
of the regeneration chain, the `asteroid_place` modes (0x3e8 spiral near
player / 0x3e9 random-cell spiral / explicit cell), the budding placement
`asteroid_place_near_oldest` @ 0x12074 (40..110 units, ≥32-unit clearance,
near the oldest asteroid of the type), and the new-game field setup at 0xf994
(fill-to-ceiling + per-type budding). The home-asteroid block at 0x11274 is
confirmed but the values it copies are NOT in the flat (see "Open question"
below). The one indirect-call assumption (the new-game path reaching the
home-asteroid block) is flagged below and awaits runtime confirmation.

Terminology note: the game's own text (the `_TEXT/AMERICAN.TXT` resources)
names these objects **asteroids** and the arena's map regions **sectors**;
"galaxy" appears in the game only in drink descriptions. Earlier versions of
this note called the nodes galaxies; that label has been dropped as
misleading.

Source: disassembly (`build/flat/FRAGILE.EXE.flat` + `build/named/.../decompiled.c`)

## Overview

An *asteroid* is one node of the game's master object list (sentinel
`g_obj_list_sentinel` @ 0xc3f4). The current asteroid is pointed to by the
global `g_asteroid_ptr` @ 0xc3c4. Asteroids are created by **`asteroid_create`
@ 0x11a64** and later filled in by a chain of deterministic generators driven
from the asteroid's 32-bit seed — see `docs/mechanics/rng.md` for the RNG
plumbing and the full `g_rng_state` write-site census.

## The creation routine `asteroid_create` @ 0x11a64

Verified asm flow:

1. **Allocate**: `obj_list_pop` pulls a node from the object list (sentinel
   0xc3f4, head `[0xc3e0]`); `FUN_00021274` initialises the node's sub-struct
   at +0x1ec and the planet/object area at +0x50.
2. If `DAT_00016d58 != 0` the node is flagged as "special": `[+0xa6] = 0xffff`.
3. **Size class**: `[+0x50] = rng_next(5) + 4` → class in **4..8**.
4. **Surface width**: rolled as
   `width = 2 * (12 + ((class-4)*3)/5 + rng_next(2)) + 1`
   (asm: `idiv 5` on `(class-4)*3`, `+0xc`, plus a `rng_next(2)` roll, `*2`, `+1`)
   → an **odd** width of **25..31** cells depending on class and roll. The
   width sizes the asteroid's diamond-shaped surface grid: it is the row width
   used to index the surface bitplane at +0x134 (the /2 radius, the count²/2
   area, and the surface renderers all read +0x9c).
5. **Seed**: `[+0x98] = (rng_next(0x10000) << 16) | rng_next(0x10000)`
   (asm: two `call rng_next` with `eax = 0x10000`, first result `shl edx,0x10`
   then `add`). The seed is therefore just the next two high-scaled rolls of
   the live `g_rng_state` — **not** a name hash and never entered by the
   player.
6. `[+0xb4] = 0`, `[+0x14d] = 0xff`.
7. **List anchors**: the node's intrusive-list anchors at +0x8/+0xc, +0x10..+0x3c,
   +0xc0/+0xc4/+0xc8/+0xcc are made self-referential (empty lists).
8. `iRam0000ca20++` — bumps the global asteroid counter (the same counter `[0xca20]`
   the main loop's auto-spawn gate compares against).
9. `FUN_00012994()`, `asteroid_gen_start_values()` — post-creation hooks.

### Asteroid struct fields established so far

| offset | size | meaning |
|--------|------|---------|
| +0x50  | 1 | size class, 4..8 (roll + 4); scales the map rendering |
| +0x51  | 1 | flag byte (cleared for the home asteroid) |
| +0x53  | 1 | ranked best-value slot index 0..9 (set by `asteroid_rank_start_values`; selects the 0x1e4dc scale row) |
| +0x54, +0x58 | 4×2 | position/scale pair (written by `FUN_00011ba4`) |
| +0x6c | 2×10 | starting-planet value set; written by the 0x11274 block (10 words) and by `asteroid_gen_start_values` / `asteroid_setup_start_values` |
| +0x15e | 2×10 | second starting-planet value set; written by the 0x11274 block only, at +0x15e+2·(i+1) for i=0..9 (lands at +0x160..+0x172) |
| +0x98  | 4 | **the asteroid seed** — everything else derives from it |
| +0x9c  | 2 | surface width (odd, 25..31 cells across the surface diamond) |
| +0xa5  | 1 | tick-down counter (decremented in main) |
| +0xa6  | 2 | 0xffff marker when `DAT_00016d58` set |
| +0xac  | 2 | word counter (decremented in main state 6) |
| +0xb4  | 4 | 0 at creation |
| +0xd0  | 1 | asteroid index (1..8) used to index the `[0xc458]` per-type table |
| +0x148 / +0x149 | 1/1 | flags bytes (0x148: race bit 0x2, scan bit 0x8, "owned" bit 0x40; 0x149: work bits 0x1/0x2) |
| +0x14d | 1 | 0xff at creation |
| +0x1b8 | 1 | byte written during main state-6 updates |
| +0x1ec | — | sub-struct initialised by `FUN_00021274` |

## Creation sites

- **Home asteroid** — a **standalone routine at 0x11274** (0x11274..0x112e9).
  Earlier notes attributed it to `FUN_000104c4`, but `functions.tsv` shows no
  function covering 0x11274 (it sits in a gap) and the disassembly is a
  self-contained routine; Ghidra never recovered it as a function. Verified
  flow:
  - `rng_seed(0x3039)` (== **12345**, the canonical LCG seed);
  - `asteroid_create` → asteroid created (deterministic, see above);
  - `asteroid_place(0xb4)` — position/slot placement;
  - `FUN_00023054(1)` — name/index assignment;
  - `[+0x51] = 0`;
  - copy loop i = 0..9 (ten iterations, `cmp eax,0x9; jle`): `[+0x6c+2i]` ←
    word `[i*2+0xa384]`, and `[+0x15e+2*(i+1)]` ← word `[i*2+0xa3c0]` (the
    second write uses `edx` already bumped past the +0x6c slot, so the +0x15e
    set lands at +0x160..+0x172);
  - `asteroid_rank_start_values` — rank the ten values;
  - `g_asteroid_ptr = asteroid` (`[0xc3c4]`).
  The fixed seed makes the home asteroid's layout reproducible every new game.
  **Caveat:** the two word tables at 0xa384 / 0xa3c0 that this loop reads do
  **not exist as data in the flat image** — those addresses hold executable
  code (Ghidra's `FUN_0000a3b4` @ 0xa3b4 starts inside the second table), and
  no relocation record targets them. See "Open question" below.
- **Race asteroids** — `FUN_0000ff25` @ 0xff25 creates asteroids in a loop (one
  per pass): the first pass (`esi==1`) makes a home-style asteroid with
  `asteroid_place(0xf1)`, `[+0x51]=0`, the +0x15e copy from 0xa384 (if
  `[0x16d5e]!=0`), and `g_asteroid_ptr` set; later passes place a
  caller-supplied size (`edi`). The
  loop runs until the pass counter reaches `[0x16d70]+1`, then the routine
  creates **eight** fixed asteroids, each `asteroid_create` then
  `asteroid_place(<size>)`: two untagged (`0x16e`, `0xe4`), then six tagged ones
  with sizes 0x130/0x12f/0x12e/0x12d/0x150/0xca, name indices
  0xa/0xb/0x9/0xc/0xd/0xe and bits 0x4/0x8/0x2/0x10/0x20/0x40 OR-ed into the
  byte `DAT_00016d69`; only the tagged ones call `FUN_00023054(<name index>)`.
  **No direct callers** — reached only by indirect dispatch, so the new-game
  entry point is assumed here (confirm at runtime).
- **Main loop (state 8, in-game)** — `main` @ 0x14:
  - `FUN_0000f544` is called every tick while `g_mode_flag == 0`; it is the
    event/encounter scheduler and **creates no asteroids itself**;
  - an **auto-spawn gate** at 0x3ca..0x422: if `[0x16d6c]==0` (i.e.
    `g_mode_flag==0`), `g_field_fill_gate==0` (the `[0x16d60]` byte, zeroed at
    new-game setup), `g_tick_count & 7 == 0` (every **8 ticks**), and
    `ceiling > g_asteroid_count`, it calls `asteroid_create` then
    `asteroid_place(0x3e8)` — the field keeps growing during play until the
    ceiling is met. The ceiling is the byte
    `g_density_ceiling_table[ g_map_density + 3*g_map_size ] @ 0xa398`, where
    `g_map_size` `[0x16d64]` and `g_map_density` `[0x16d65]` are the two
    scenario settings and `g_asteroid_count` is the live counter `[0xca20]`.
    `asteroid_place(0x3e8)` is the "spawn near the player" placement — a spiral
    search over the 32×32 occupancy grid from the player's cell (see
    "Placement" below). The 8-tick cadence and the `ceiling` read are the
    description's "every so often, check the density ceiling and top the field
    up".
- Other creation callers in `FUN_00013844` (0x13941..0x13ad5) follow the same
  shape.

## Placement: `asteroid_place` @ 0x11c24

Verified asm flow (969 bytes):

1. **Rebuild the occupancy grid**: zero `g_sector_occ_grid` @ 0x5bfa4 (a 32×32
   byte grid, 0x280 bytes, cleared via `FUN_0005bd04`), then walk the master
   object list and for every object write
   `grid[(x>>16)/0x20 + ((y>>16)/0x20)*0x20] = 1` where `+0x54`/`+0x58` are the
   16.16 position words. Cell size is **0x20 = 32 units**.
2. **Mode `param == 0x3e8` (1000)** — the in-game "near the player" spawn:
   - draw `x0` from `rng_next(0x100)`, fold it into an offset
     `iVar2 = max(0, (x0 - c)/2)` where `c` is `[0xcdb0]`-derived (cell columns
     `3*width/4`); draw a spiral direction `iVar3 = rng_next(4)`; start cell
     `(iVar7, iVar6) = (iVar2, c)`.
   - **spiral search**: while the current cell is occupied, advance through the
     four directional cases (up / right / down / left) exactly as the 0x3e9 mode
     does (see below); the search is bounded by `[0xcdb0]`/`[0xcdb4]` in the
     same way.
   - on success write `+0x54 = (rng_next(0x10) + iVar7*0x20 + 8) * 0x10000`
     and `+0x58 = (iVar4 + 0x1f) << 0x10` (iVar4 is the current row bound), or
     `(rng_next(0x10) + bound + 8) * 0x10000` on the y when at the left edge
     (iVar7 == 0).
   - if the spiral wraps and the wrap flag is already set, set
     `asteroid->+0xd0 = 0xff`, call `obj_list_move_front` (reinsert node) and
     return 0 (give up — no free cell).
   - afterwards, if `asteroid->+0x51 == 0`, set it to 1.
3. **Mode `param == 0x3e9` (1001)** — the new-game fill placement:
   - draw random cell column `ebx = rng_next([0xcdb0])` and row
     `ecx = rng_next([0xcdb4])`, remember both in stack slots; draw a spiral
     direction `eax = rng_next(4)`.
   - **spiral search**: `while grid[ebx + ecx*0x20] != 0`, move by case
     `eax`: 0 = right (wraps at `[0xcdb0]`), 1 = up (wrap at `[0xcdb4]`, tracks
     min/max), 2 = down, 3 = left (tracks min/max) — a classic expanding square
     spiral. `eax` cycles via `jmp dword [cs:eax*4+0x11c10]` (jump table).
   - on success: `+0x54 = (ebx*0x20 + 0x10) * 0x10000`,
     `+0x58 = (ecx*0x20 + 0x10) * 0x10000` (cell centre, 16.16).
   - **jitter**: if `[0x16d5e] == 0`, add `(rng_next(0x10) - 8) * 0x10000` to
     both +0x54 and +0x58 (random ±8-unit offset inside the cell).
4. **Mode `param < 1000`** — explicit cell:
   - `uVar5 = param % [0xcdb0]` (column); row = `param / [0xcdb0]` (+1 if the
     remainder is zero).
   - `+0x54 = (uVar5*0x20 - 0x10) * 0x10000`, `+0x58 = (row*0x20 - 0x10) * 0x10000`
     (cell centre, 16.16); jitter `(rng_next(0x10) - 4)` if `[0x16d5e]==0`.
5. Every mode ends with `asteroid_set_surface` (`FUN_00011bb4`), which rolls
   `+0x51` from `g_surface_style_table` @ 0xa460 (`rng_next(0x10)` index) and
   `+0x52` from `0xa488` (`rng_next(0xc)` index, `-5`, plus another
   `rng_next(0xa)`), the latter bounded by `[0xcdbc]` (map height).

`FUN_00011ba4` (16 bytes) is the raw position setter: `+0x54 = edx<<16`,
`+0x58 = ebx<<16`.

## The budding placement: `asteroid_place_near_oldest` @ 0x12074

Verified asm flow (216 bytes). **Callers: only the new-game field setup**
(`0xf994` region — see below). There is no in-play budding: a whole-flat scan
finds exactly three call sites (0xfd9f, 0xfdcd, 0xfe20), all inside that
setup routine.

```
do {
    angle = rng_next(0x100)                    # 0..255, indexes a 256-entry
                                               #   direction table at g_dir_cos_table (x) /
                                               #   g_dir_sin_table (y), 0x5c900/0x5c800
    distance = base + rng_next(range)          # base/range come from the caller
    x = ref->+0x54/0x10000 + table_x[angle] * distance / 0x10000
    y = ref->+0x58/0x10000 + table_y[angle] * distance / 0x10000
    new->+0x54 = x << 0x10;  new->+0x58 = y << 0x10
    too_close = false
    for other in object list:                  # skip new and ref
        dx = (other->+0x54 - new->+0x54) >> 0x10
        dy = (other->+0x58 - new->+0x58) >> 0x10
        if dx*dx + dy*dy <= 0x400:  too_close = true; break   # 0x400 = 32^2
} while (too_close)                            # re-roll until >32 units clear
asteroid_set_surface(); return new
```

- The reference asteroid `ref` is passed in EAX by the caller — the oldest
  surviving asteroid of the same type (the new-game setup walks the master list
  and picks the first node whose `+0xd0` type matches, starting from the list
  head, i.e. oldest first).
- The three call sites in the new-game setup use `(base, range)`:
  `(type + 0x1d, 0)` — fixed distance per type; `(0x48, 0x6e-0x48=0x26)` —
  72..110 units; `(0x28, 0x6e-0x28=0x46)` — **40..110 units**. The last is the
  description's "40-110 units out, re-rolling until 32 units clearance".
- Direction comes from the two 256-entry tables `g_dir_cos_table` @ 0x5c900
  (x) / `g_dir_sin_table` @ 0x5c800 (y) indexed by the angle draw — the game's
  cosine/sine lookup.
- This is the mechanism that keeps the field full without spawning at the map
  edge: each type's numbers are topped up around its oldest surviving member.

## New-game field setup @ 0xf994

A standalone routine (0xf994..0xfe74; called from the map-setup at 0x22846
after the cell/unit dimensions are loaded — see "Map dimensions" below). It
does **not** appear in `functions.tsv`/`decompiled.c` (it sits in a gap), so
the flow below is from raw disassembly:

1. If `[0x41474] != 0` → jump to the 0x11274 home-asteroid block.
2. If `g_mode_flag != 0` or `g_field_fill_gate != 0` → return (no field).
3. **Per-type presence**: for types 9..14, if bit `1<<type` of `g_race_flags`
   `[0x16d68]` is set, OR 1 into `[type*0x210 + 0xd239]` (the per-type flag
   byte at 0xd239, stride 0x210, base 0x1290..0x1ef0).
4. If `[0x16d53] != 0`, clear bit 0 of every type flag (`and 0xfe`).
5. Count the types with flag bit 0 set (ebp); `[0xca28] = 1`;
   draw `rng_next(0x100)` and `idiv ebp` to pick an initial type index.
6. **Fill to the ceiling** (0xfc90..0xfd0d):
   - count live objects in the master list (ebx);
   - `ceiling = byte[g_density_ceiling_table + 3*g_map_size + g_map_density]`
     (same table as the main-loop gate);
   - `need = ceiling - count`; if `ceiling == 0x64 (100)` then `need -= 10`
     (leave 10 slots free — the hard cap);
   - loop `need` times: `asteroid_create` + `asteroid_place(0x3e9)` — place
     each new asteroid near the player by the random-cell spiral.
7. `asteroid_prune_overlaps()` (`FUN_000137d4`, the only call site) — destroys
   asteroids (`+0xd0 == 0`, still-untyped) that sit within **90 units**
   (`0x1fa5 = 8101 ≈ 90²`) of a typed asteroid (`+0xd0 != 0`). A cleanup pass
   after the random-cell fill.
8. **Budding pass** (0xfd24..0xfe44): for each type flag with bit 0 set, find
   the first (oldest) master-list asteroid of that type, then:
   - if `g_mode_flag == 0`: create `(g_map_size + g_map_density + 1)` asteroids,
     each `asteroid_place_near_oldest` with base `0x28` (40), range `0x6e`
     (110) — i.e. **40..110 units** from the oldest asteroid of the type;
   - else: create one asteroid at fixed distance `type + 0x1d` from it, and a
     further loop creating more at 72..110 units (counts bounded by
     `g_map_size + g_map_density + 2`).
9. The whole loop advances the type pointer by 0x210 per type (0x1290..0x1ef0,
   i.e. up to 14 type rows) and runs `FUN_00013844` at the end.

This is the description's **"the rest of the field fills in — budding near the
oldest surviving asteroid of each type, 40-110 units out, ≥32-unit clearance,
never at the edge"**. Note the budding happens only here, at field creation:
during play the main-loop gate tops the field up near the player (0x3e8),
not by budding (see "Scenario settings" below).

## Map dimensions (cell grid)

`FUN_000227e4` (0x227e4..0x22850, part of the same unrecovered gap family; not
in `decompiled.c`) loads the arena size from the scenario settings:

```
[0xcdb0] = byte[0x16d90 + 2*g_map_size]    # width  in 32-unit cells
[0xcdb4] = byte[0x16d91 + 2*g_map_size]    # height in 32-unit cells
[0xcdb8] = [0xcdb0] << 5                    # width  in units (×32)
[0xcdbc] = [0xcdb4] << 5                    # height in units (×32)
```

then calls 0x228c4, 0x22db4, the new-game setup at 0xf994, 0x4124, 0x16754,
0x3ba04, 0x50044, and finally `[0xc3c4] = edx` (`g_asteroid_ptr`). The
0x16d90 table (2 bytes per map-size index) is **BSS in the flat** (bytes at
0x16d90 read `00 00 / 02 00 / eb 07` — uninitialised), so the actual
widths/heights are populated at runtime by the settings reader that is not
present in the flat; the flat cannot tell us e.g. "small = 30×30 cells".

## Scenario settings and the per-type tables

- `g_scenario_index` `[0x16fd0]` selects a **6-byte entry** in the table at
  **0xa33c** (stride 6). `FUN_0000f904` (gap routine, not in `decompiled.c`)
  reads it: `[0x16d64] = byte[0xa33c + 3*i]` (map size),
  `[0x16d65] = byte[0xa33d + 3*i]` (density),
  `[0x16d66] = byte[0xa33e + 3*i]`, and
  `[0x16d68] |= word[0xa340 + 2*i]` (the per-race presence bitmask, bits 9..14
  cleared first). `g_scenario_index` is written only at 0x2905c/0x29098/0x290b1/
  0x290fc.
- **Per-type tables**, all stride **0x210** and indexed by the asteroid's
  `+0xd0` type byte (base row 0x1290): list head at **0xd218**, live count at
  **0xd238**, flag byte at **0xd239** (bit 0 = type present, bit 1 = ?, bit 4 =
  "initialised", written `|0x10` by `FUN_000152e4`).
- `asteroid_set_type` (`FUN_000233e4`) assigns `+0xd0` on first creation and
  increments `[type*0x210 + 0xd238]`; `asteroid_destroy` (`FUN_00012154`)
  decrements `g_asteroid_count` and `[type*0x210 + 0xd238]` and unlinks the
  node from its `0xd218` list. So the per-type count is the game's own
  population bookkeeping.
- `g_type_rows` `[0x16d70]` (written from `[0x4e328]` at 0x27033) bounds the
  type-table loops (rows 0..g_type_rows, 14 max).
- `FUN_000152e4` (0x152e4, `asteroid_setup_type_cells`, called at 0x1636b)
  writes each type's initial cell offset to `[type*0x210 + 0xd214]/[+0xd216]`
  and sets the `0x10` flag. The
  function is reached from `FUN_00016264` (the per-tick scenario driver) when
  `iRam0005c550 != 0` and `g_tick_count & 0xfff == 0`, i.e. roughly every 4096
  ticks.
- `FUN_00015504` (0x15504) and `FUN_00015b04` (0x15b04) are **not** asteroid
  creators. They are colony/building-slot routines driven by `FUN_00016264`
  through the per-type countdowns `[type*0x210 + 0xd232]` and `[+0xd236]`
  (each decremented once per tick; when one hits 0 the routine runs and resets
  it from the 0xa596/0xa5b7 tables). `FUN_00015504` assigns a building slot
  (`FUN_0001d6d4`/`FUN_0001d774`) to a colony of the type when
  `[type*0x210 + 0xd238]` is below `max_count + byte[0xa61e + 3*(type-9) +
  0x16d66]`. Neither calls `asteroid_create`, `asteroid_place`, or
  `asteroid_place_near_oldest`.
- **In-game budding does not happen.** `asteroid_place_near_oldest` (0x12074)
  has exactly three call sites (0xfd9f, 0xfdcd, 0xfe20), all inside the
  new-game-setup gap routine — the budding pass is part of field creation, not
  of in-play population maintenance. During play the count is kept up by the
  main-loop gate alone: `asteroid_create` + `asteroid_place(0x3e8)` near the
  player every 8 ticks while below the ceiling. So the description's "budding
  keeps each kind's population up during play" is **not supported** by the
  code: budding is a one-time field-builder, and in-play top-ups appear near
  the player regardless of type.

## Regeneration: `asteroid_regenerate` @ 0x320d4

Rebuilds an asteroid's content from its seed. Verified flow:

```
save g_rng_state
if (g_last_asteroid_seed != asteroid->+0x98 || [0x1e468] == 0 || [0x1e470] == 0)
    free([0x1e468]); free([0x1e470])          # old buffers (0x5da51)
    asteroid_gen_surface(asteroid->+0x98)     # surface from seed
    FUN_00031fe4(asteroid, 0x24242424)        # one object, 12 slot-passes
                                              #   (two loops of 6; a word field
                                              #   +0xe advances +0x140 per pass,
                                              #   a 4-bit field +0x1c gets
                                              #   (i&3)+4; each pass calls the
                                              #   render dispatch 0x641f4).
                                              #   Identity unconfirmed.
    [0x61964] = malloc(0x20000)               # scratch workspace; 0 → fatal
    rng_seed(asteroid->+0x98)                 # reseed from asteroid seed
    FUN_00030af4(asteroid), 0x310b4,          # content chain; every step is
    0x315d4(asteroid), 0x31884, 0x31b54,      #   followed by hook call 0x601a4
    free([0x61964]), 0x31e64
    g_last_asteroid_seed = asteroid->+0x98    # remember done state
    [0x1e464] = asteroid->+0x9c               # remember surface width
# always (also when the guard short-circuits to 0x32223):
[0x1e450] = alloc_child_object(0x5e6c4); [0x1e454] = alloc_child_object()
rng_seed(asteroid->+0x98)                     # reseed (placement stream)
idx = asteroid->+0x53                         # ranked best-value slot (0..9)
FUN_000319c4(row[idx] @ 0x1e4dc)              # a,b,c = the row's 3 bytes
restore g_rng_state
```

`FUN_00031fe4` @ 0x31fe4: saves `g_rng_state`, allocates one object from the
`0x51970` free list via `0x66547` (zeroed, `[+0x18]` = a fresh `[0x1e444]`
buffer, byte +0x1 |= 0x10), reseeds the RNG from `asteroid->+0x98`, then runs the
two 6-pass loops above (`or [obj],0x81` at the end) and **restores the saved
RNG state** — a third RNG-sandwich in the regeneration path (besides the guard
and the final `FUN_000319c4` step).

`asteroid_rank_start_values` @ 0x31af4 sets `asteroid->+0x53` to the slot index
(0..9) with the largest `(start_value << 8) / hi_slot` ratio (`hi_slot` =
`word [0xa3d8 + 0xe*i]`, the same table `asteroid_gen_start_values` reads; see
next section). `+0x53` is therefore the index of the asteroid's **best-value
ore slot** and is what selects the scale row at 0x1e4dc.

Every generator is deterministic given the seed, and the pre-call `g_rng_state`
is restored, so regeneration neither depends on nor perturbs the live game
stream.

## The 10-slot value table: `asteroid_gen_start_values` @ 0x127f4

Called from `asteroid_create` (its only call site, 0x11b98). For each slot
`i = 0..9` it reads a 14-byte row at `0xa3d4 + 0xe*i` (`p`@+0, `lo`@+2, `hi`@+4)
and rolls the slot's starting value at `asteroid->+0x6c + 2*i`:

```
roll = rng_next(100)
if roll < p:              value = lo + rng_next(hi - lo + 1)     # rich
elif i < 8:               value = 1 + rng_next(hi / 20)          # poor
else:                     value = 0
```

followed by `asteroid_rank_start_values` (see flow above). The same
10-row × 14-byte geometry at 0xa3d4 is read by **three more independent
routines** (`0x16754` accumulates `hi * [row+0xc]` over the ten rows;
`0x20ee4` reuses the (lo, hi) pair; `0x31af4` uses `hi`) — a consistent,
deliberate table, which is what makes the "table is code" anomaly below so
strange.

## `FUN_000319c4` @ 0x319c4 and the 0x7980c effect buffer

Called with the three bytes `a, b, c` of the `0x1e4dc` row selected by
`asteroid->+0x53` (see flow). It writes **32 slots × 3 bytes** at
`0x7998c..0x799ee` (i.e. `0x7980c + 0x180`), slot `i`, byte `j`:

```
byte = ((rng_next(4) + 100 - rng_next(4)) * param_j * (9 + i)) / 0xee8
byte = min(byte, 0x3f)                 # clamp to a 6-bit value
```

`param_j` = the row byte for that slot-byte position (`a` for byte 0, `b` for
byte 1, `c` for byte 2); the scale factor starts at 9 and increments by 1 per
slot. After the loop it calls `0x642f5` (only if `[0x41474] != 0`) and
`0x64a34` on `0x7980c`.

The region `0x7980c` is an **animation / lighting buffer, not an asteroid
position table**: `0x64a6a` consumes up to 0x300 bytes from it as 6-bit ramp
values for a VGA-palette fade (reads DAC ports 0x3c7/0x3c9, builds a 768-entry
glow table at `0x50d14`), and `0x44f3b` memcpys 336 bytes of it into a
UI buffer. So `FUN_000319c4` generates per-slot 6-bit brightness/ramp data for
the asteroid backdrop. Earlier "y-coordinate / position" notes on `0x7980c` are
**superseded**.

## Determinism conclusion

- Everything the regeneration pass produces (surface, the 12-slot object, the
  backdrop/lighting effect data) is a pure function of the 32-bit seed at
  +0x98; the **size class, surface width and the ten ore amounts are set
  earlier, at creation**, by draws against the live stream —
  `asteroid_gen_start_values` has a single call site (0x11b98, inside
  `asteroid_create`) and is never re-run.
- The seed is produced by two `rng_next(0x10000)` rolls against the live
  `g_rng_state`, and the home-asteroid path seeds that state with the fixed
  constant **12345** first. Since only deterministic draws ever advance this
  stream, the whole universe — the home asteroid and every later spawn — is the
  same on every new game (for a fixed settings choice).
- The only clock-seeded stream is `g_rng_state2` (via `rng_seed_clock` in
  `FUN_0005bd24`), consumed by the encounter-placement generator `FUN_0002f114`
  (13 of its 19 call sites; the other six sit in unrecovered gap code — see
  `docs/mechanics/rng.md`) — battles vary per run, the universe does not.
- Confirmed at runtime still pending: that the 0x11274 home-asteroid block (via
  `FUN_0000ff25`'s indirect dispatch) runs before any in-game asteroid creation.

## Open question: the 0xa3xx "static tables" do not exist in the flat

Several code paths read word tables from the 0xa3xx range, which the flat
image contains as **executable code**, not data:

| reference | used by | content at that flat address |
|-----------|---------|------------------------------|
| 0xa384 (10 words) | 0x11274 block → `+0x6c` | code (tail of the routine before `FUN_0000a3b4`) |
| 0xa3c0 (10 words) | 0x11274 block → `+0x15e` | **inside `FUN_0000a3b4` @ 0xa3b4** (verified function) |
| 0xa3d4, stride 0xe | `asteroid_gen_start_values` → `+0x6c` | **inside `FUN_0000a3b4` @ 0xa3b4** (code) |
| 0xa3d8, stride 0xe | `asteroid_rank_start_values` (ratio divisor) | code |
| 0xa3d6 / 0xa3d8, stride 0xe | `0x16754`, `0x20ee4` (independent readers) | code |
| 0xa3dc / 0xa3de, stride 0xe | `asteroid_setup_start_values` → `+0x6c` | code |
| 0xa398 (3-wide) | density ceiling, main-loop auto-spawn gate + new-game fill | code |
| 0xa33c (stride 6) | per-scenario settings (size/density/relations/race-mask), read by gap routine 0xf904 | code |
| 0xa460 (16×1) | `asteroid_set_surface` → `+0x51` surface styles | code |
| **0x1e4dc (10 rows × 3 bytes)** | `asteroid_regenerate` → `FUN_000319c4` scale params | **inside fn @ 0x1e4c6** (code) |

`0x1e4dc` joins the 0xa3xx family: the 10×3-byte scale table that
`asteroid_regenerate` indexes by `+0x53` is itself inside the body of a function
(`0x1e4c6..0x1e4f8`, no callers). So **both** the value table (0xa3d4) and the
scale table (0x1e4dc) of the asteroid-generation chain are code bytes in the
flat.

Checks performed: **the relocation record stream is fully decoded and verified
against the flat (37,311 records, groups 1..233 — `docs/dataformats/
dos4gw-bound.md`)**; no record targets the 0xa000..0xa5000 range at all, and
none targets 0x1e4dc or the instruction dwords that embed it; a scan of the
whole code region finds **no writes** to any of these addresses (no `C7 05`,
`mov [disp],reg`, or similar); and Ghidra's own function list places
`FUN_0000a3b4` at 0xa3b4. So the values the routines would copy are
**not present in the flat as static data**. Working hypotheses, unresolved
without a runtime trace:

1. ~~**The bound-image fixups are not fully applied.**~~ **Resolved:** the
   grammar is fully decoded, so this no longer applies.
2. **The home block / these slots are never executed in the retail new-game
   path** and the real starting values come from `asteroid_setup_start_values`'s
   other branch (copy from an existing same-class asteroid). This would also
   make the 0x11274 block effectively dead code. (The `asteroid_create` call
   site at 0x414 is reachable from startup, so this can only hold if the
   *value/scale reads* are the dead part.)
3. The code bytes genuinely serve double duty (least likely).

Until a DOSBox-X trace settles this, treat every "value copied from
table 0xa3xx" claim as **unverified**.

## References

- `docs/mechanics/rng.md` — RNG internals, the seed formula, the exhaustive
  `g_rng_state` write-site census, the open cold-start-ordering question.
- `build/named/FRAGILE.EXE.flat/decompiled.c` — `asteroid_create` @ line 9626
  (seed write @ 9652), the 0x11274 block (standalone routine; not in
  `functions.tsv`), `FUN_0000a3b4`, `FUN_0000ff25` @ 8786,
  `asteroid_regenerate` @ 25483.
