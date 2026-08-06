# Galaxy creation

Status: creation routine and regeneration chain confirmed (static
disassembly), including the `galaxy_gen_start_values` → `galaxy_rank_start_values`
(+0x53) → `0x1e4dc` scale-row → `FUN_000319c4` tail of the chain. The
home-galaxy block at 0x11274 is confirmed but the values it copies are NOT in
the flat (see "Open question" below). The one indirect-call assumption (the
new-game path reaching the home-galaxy block) is flagged below and awaits
runtime confirmation.
Source: disassembly (`build/flat/FRAGILE.EXE.flat` + `build/named/.../decompiled.c`)

## Overview

A *galaxy* is one node of the game's master object list (sentinel
`g_obj_list_sentinel` @ 0xc3f4). The current galaxy is pointed to by the
global `g_galaxy_ptr` @ 0xc3c4. Galaxies are created by **`galaxy_create`
@ 0x11a64** and later filled in by a chain of deterministic generators driven
from the galaxy's 32-bit seed — see `docs/mechanics/rng.md` for the RNG
plumbing and the full `g_rng_state` write-site census.

## The creation routine `galaxy_create` @ 0x11a64

Verified asm flow:

1. **Allocate**: `obj_list_pop` pulls a node from the object list (sentinel
   0xc3f4, head `[0xc3e0]`); `FUN_00021274` initialises the node's sub-struct
   at +0x1ec and the planet/object area at +0x50.
2. If `DAT_00016d58 != 0` the node is flagged as "special": `[+0xa6] = 0xffff`.
3. **Type**: `[+0x50] = rng_next(5) + 4` → galaxy type in **4..8**.
4. **Planet count**: rolled as
   `count = 2 * (12 + ((type-4)*3)/5 + rng_next(2)) + 1`
   (asm: `idiv 5` on `(type-4)*3`, `+0xc`, plus a `rng_next(2)` roll, `*2`, `+1`)
   → an **odd** count of **25..31** planets depending on type and roll.
5. **Seed**: `[+0x98] = (rng_next(0x10000) << 16) | rng_next(0x10000)`
   (asm: two `call rng_next` with `eax = 0x10000`, first result `shl edx,0x10`
   then `add`). The seed is therefore just the next two high-scaled rolls of
   the live `g_rng_state` — **not** a name hash and never entered by the
   player.
6. `[+0xb4] = 0`, `[+0x14d] = 0xff`.
7. **List anchors**: the node's intrusive-list anchors at +0x8/+0xc, +0x10..+0x3c,
   +0xc0/+0xc4/+0xc8/+0xcc are made self-referential (empty lists).
8. `iRam0000ca20++` — bumps the global galaxy counter (the same counter `[0xca20]`
   the main loop's auto-spawn gate compares against).
9. `FUN_00012994()`, `galaxy_gen_start_values()` — post-creation hooks.

### Galaxy struct fields established so far

| offset | size | meaning |
|--------|------|---------|
| +0x50  | 1 | galaxy type, 4..8 (roll + 4) |
| +0x51  | 1 | flag byte (cleared for the home galaxy) |
| +0x53  | 1 | ranked best-value slot index 0..9 (set by `galaxy_rank_start_values`; selects the 0x1e4dc scale row) |
| +0x54, +0x58 | 4×2 | position/scale pair (written by `FUN_00011ba4`) |
| +0x6c | 2×10 | starting-planet value set; written by the 0x11274 block (10 words) and by `galaxy_gen_start_values` / `galaxy_setup_start_values` |
| +0x15e | 2×10 | second starting-planet value set; written by the 0x11274 block only, at +0x15e+2·(i+1) for i=0..9 (lands at +0x160..+0x172) |
| +0x98  | 4 | **the galaxy seed** — everything else derives from it |
| +0x9c  | 2 | planet count (odd, 25..31) |
| +0xa5  | 1 | tick-down counter (decremented in main) |
| +0xa6  | 2 | 0xffff marker when `DAT_00016d58` set |
| +0xac  | 2 | word counter (decremented in main state 6) |
| +0xb4  | 4 | 0 at creation |
| +0xd0  | 1 | galaxy index (1..8) used to index the `[0xc458]` per-type table |
| +0x148 / +0x149 | 1/1 | flags bytes (0x148: race bit 0x2, scan bit 0x8, "owned" bit 0x40; 0x149: work bits 0x1/0x2) |
| +0x14d | 1 | 0xff at creation |
| +0x1b8 | 1 | byte written during main state-6 updates |
| +0x1ec | — | sub-struct initialised by `FUN_00021274` |

## Creation sites

- **Home galaxy** — a **standalone routine at 0x11274** (0x11274..0x112e9).
  Earlier notes attributed it to `FUN_000104c4`, but `functions.tsv` shows no
  function covering 0x11274 (it sits in a gap) and the disassembly is a
  self-contained routine; Ghidra never recovered it as a function. Verified
  flow:
  - `rng_seed(0x3039)` (== **12345**, the canonical LCG seed);
  - `galaxy_create` → galaxy created (deterministic, see above);
  - `galaxy_place(0xb4)` — position/rover placement;
  - `FUN_00023054(1)` — name/index assignment;
  - `[+0x51] = 0`;
  - copy loop i = 0..9 (ten iterations, `cmp eax,0x9; jle`): `[+0x6c+2i]` ←
    word `[i*2+0xa384]`, and `[+0x15e+2*(i+1)]` ← word `[i*2+0xa3c0]` (the
    second write uses `edx` already bumped past the +0x6c slot, so the +0x15e
    set lands at +0x160..+0x172);
  - `galaxy_rank_start_values` — rank the ten values;
  - `g_galaxy_ptr = galaxy` (`[0xc3c4]`).
  The fixed seed makes the home galaxy's layout reproducible every new game.
  **Caveat:** the two word tables at 0xa384 / 0xa3c0 that this loop reads do
  **not exist as data in the flat image** — those addresses hold executable
  code (Ghidra's `FUN_0000a3b4` @ 0xa3b4 starts inside the second table), and
  no relocation record targets them. See "Open question" below.
- **Race galaxies** — `FUN_0000ff25` @ 0xff25 creates galaxies in a loop (one
  per pass): the first pass (`esi==1`) makes a home-style galaxy with
  `galaxy_place(0xf1)`, `[+0x51]=0`, the +0x15e copy from 0xa384 (if
  `[0x16d5e]!=0`), and `g_galaxy_ptr` set; later passes place a
  caller-supplied size (`edi`). The
  loop runs until the pass counter reaches `[0x16d70]+1`, then the routine
  creates **eight** fixed galaxies, each `galaxy_create` then
  `galaxy_place(<size>)`: two untagged (`0x16e`, `0xe4`), then six tagged ones
  with sizes 0x130/0x12f/0x12e/0x12d/0x150/0xca, name indices
  0xa/0xb/0x9/0xc/0xd/0xe and bits 0x4/0x8/0x2/0x10/0x20/0x40 OR-ed into the
  byte `DAT_00016d69`; only the tagged ones call `FUN_00023054(<name index>)`.
  **No direct callers** — reached only by indirect dispatch, so the new-game
  entry point is assumed here (confirm at runtime).
- **Main loop (state 8, in-game)** — `main` @ 0x14:
  - `FUN_0000f544` is called every tick while `g_mode_flag == 0`; it is the
    event/encounter scheduler and **creates no galaxies itself**;
  - an **auto-spawn gate** at 0x3ca..0x422: if `[0x16d6c]==0` (i.e.
    `g_mode_flag==0`), `[0x16d60]==0`, `[0xcd98]&7==0`, and
    `table[0xa398][ [0x16d65] + 3*[0x16d64] ] > [0xca20]`, it calls
    `galaxy_create` then `galaxy_place(0x3e8)` — new galaxies keep appearing as
    the game progresses (counter [0xca20] and the per-galaxy count live in the
    two byte counters [0x16d64]/[0x16d65] indexing the 3-wide table).
    `galaxy_place(0x3e8)` is the "spawn near the player" placement: it searches
    the occupancy grid around the player's cell `[0xcdb0]/[0xcdb4]`.
- Other creation callers in `FUN_00013844` (0x13941..0x13ad5) follow the same
  shape.

## Regeneration: `galaxy_regenerate` @ 0x320d4

Rebuilds a galaxy's content from its seed. Verified flow:

```
save g_rng_state
if (g_last_galaxy_seed != galaxy->+0x98 || [0x1e468] == 0 || [0x1e470] == 0)
    free([0x1e468]); free([0x1e470])          # old buffers (0x5da51)
    galaxy_gen_surface(galaxy->+0x98)         # surface from seed
    FUN_00031fe4(galaxy, 0x24242424)          # one object, 12 slot-passes
                                              #   (two loops of 6; a word field
                                              #   +0xe advances +0x140 per pass,
                                              #   a 4-bit field +0x1c gets
                                              #   (i&3)+4; each pass calls the
                                              #   render dispatch 0x641f4).
                                              #   Identity unconfirmed.
    [0x61964] = malloc(0x20000)               # scratch workspace; 0 → fatal
    rng_seed(galaxy->+0x98)                   # reseed from galaxy seed
    FUN_00030af4(galaxy), 0x310b4,            # content chain; every step is
    0x315d4(galaxy), 0x31884, 0x31b54,        #   followed by hook call 0x601a4
    free([0x61964]), 0x31e64
    g_last_galaxy_seed = galaxy->+0x98        # remember done state
    [0x1e464] = galaxy->+0x9c                 # remember planet count
# always (also when the guard short-circuits to 0x32223):
[0x1e450] = alloc_child_object(0x5e6c4); [0x1e454] = alloc_child_object()
rng_seed(galaxy->+0x98)                       # reseed (placement stream)
idx = galaxy->+0x53                           # ranked best-value slot (0..9)
FUN_000319c4(row[idx] @ 0x1e4dc)              # a,b,c = the row's 3 bytes
restore g_rng_state
```

`FUN_00031fe4` @ 0x31fe4: saves `g_rng_state`, allocates one object from the
`0x51970` free list via `0x66547` (zeroed, `[+0x18]` = a fresh `[0x1e444]`
buffer, byte +0x1 |= 0x10), reseeds the RNG from `galaxy->+0x98`, then runs the
two 6-pass loops above (`or [obj],0x81` at the end) and **restores the saved
RNG state** — a third RNG-sandwich in the regeneration path (besides the guard
and the final `FUN_000319c4` step).

`galaxy_rank_start_values` @ 0x31af4 sets `galaxy->+0x53` to the slot index
(0..9) with the largest `(start_value << 8) / hi_slot` ratio (`hi_slot` =
`word [0xa3d8 + 0xe*i]`, the same table `galaxy_gen_start_values` reads; see
next section). `+0x53` is therefore the index of the galaxy's **best-value
asteroid slot** and is what selects the scale row at 0x1e4dc.

Every generator is deterministic given the seed, and the pre-call `g_rng_state`
is restored, so regeneration neither depends on nor perturbs the live game
stream.

## The 10-slot value table: `galaxy_gen_start_values` @ 0x127f4

Called from `galaxy_create` (its only call site, 0x11b98). For each slot
`i = 0..9` it reads a 14-byte row at `0xa3d4 + 0xe*i` (`p`@+0, `lo`@+2, `hi`@+4)
and rolls the slot's starting value at `galaxy->+0x6c + 2*i`:

```
roll = rng_next(100)
if roll < p:              value = lo + rng_next(hi - lo + 1)     # rich
elif i < 8:               value = 1 + rng_next(hi / 20)          # poor
else:                     value = 0
```

followed by `galaxy_rank_start_values` (see flow above). The same
10-row × 14-byte geometry at 0xa3d4 is read by **three more independent
routines** (`0x16754` accumulates `hi * [row+0xc]` over the ten rows;
`0x20ee4` reuses the (lo, hi) pair; `0x31af4` uses `hi`) — a consistent,
deliberate table, which is what makes the "table is code" anomaly below so
strange.

## `FUN_000319c4` @ 0x319c4 and the 0x7980c effect buffer

Called with the three bytes `a, b, c` of the `0x1e4dc` row selected by
`galaxy->+0x53` (see flow). It writes **32 slots × 3 bytes** at
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
the galaxy backdrop. Earlier "y-coordinate / position" notes on `0x7980c` are
**superseded**.

## Determinism conclusion

- A galaxy's entire content (surface, the 12-slot object, the backdrop/lighting
  effect data, planets) is a pure function of its 32-bit seed at struct +0x98.
- The seed is produced by two `rng_next(0x10000)` rolls against the live
  `g_rng_state`, and the home-galaxy path seeds that state with the fixed
  constant **12345** first. So **the galaxy layout is a fixed universe on
  every new game**.
- The only clock-seeded stream is `g_rng_state2` (via `rng_seed_clock` in
  `FUN_0005bd24`), consumed by the encounter-placement generator `FUN_0002f114`
  (13 of its 19 call sites; the other six sit in unrecovered gap code — see
  `docs/mechanics/rng.md`) — battles vary per run, the universe does not.
- Confirmed at runtime still pending: that the 0x11274 home-galaxy block (via
  `FUN_0000ff25`'s indirect dispatch) runs before any in-game galaxy creation.

## Open question: the 0xa3xx "static tables" do not exist in the flat

Several code paths read word tables from the 0xa3xx range, which the flat
image contains as **executable code**, not data:

| reference | used by | content at that flat address |
|-----------|---------|------------------------------|
| 0xa384 (10 words) | 0x11274 block → `+0x6c` | code (tail of the routine before `FUN_0000a3b4`) |
| 0xa3c0 (10 words) | 0x11274 block → `+0x15e` | **inside `FUN_0000a3b4` @ 0xa3b4** (verified function) |
| 0xa3d4, stride 0xe | `galaxy_gen_start_values` → `+0x6c` | **inside `FUN_0000a3b4` @ 0xa3b4** (code) |
| 0xa3d8, stride 0xe | `galaxy_rank_start_values` (ratio divisor) | code |
| 0xa3d6 / 0xa3d8, stride 0xe | `0x16754`, `0x20ee4` (independent readers) | code |
| 0xa3dc / 0xa3de, stride 0xe | `galaxy_setup_start_values` → `+0x6c` | code |
| 0xa398 (3-wide) | main-loop auto-spawn gate | code |
| 0xa460 | `FUN_00011ba4` | code |
| **0x1e4dc (10 rows × 3 bytes)** | `galaxy_regenerate` → `FUN_000319c4` scale params | **inside fn @ 0x1e4c6** (code) |

`0x1e4dc` joins the 0xa3xx family: the 10×3-byte scale table that
`galaxy_regenerate` indexes by `+0x53` is itself inside the body of a function
(`0x1e4c6..0x1e4f8`, no callers). So **both** the value table (0xa3d4) and the
scale table (0x1e4dc) of the galaxy-generation chain are code bytes in the
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
   path** and the real starting values come from `galaxy_setup_start_values`'s other branch
   (copy from an existing same-type galaxy). This would also make the 0x11274
   block effectively dead code. (The `galaxy_create` call site at 0x414 is
   reachable from startup, so this can only hold if the *value/scale reads*
   are the dead part.)
3. The code bytes genuinely serve double duty (least likely).

Until a DOSBox-X trace settles this, treat every "value copied from
table 0xa3xx" claim as **unverified**.

## References

- `docs/mechanics/rng.md` — RNG internals, the seed formula, the exhaustive
  `g_rng_state` write-site census, the open cold-start-ordering question.
- `build/named/FRAGILE.EXE.flat/decompiled.c` — `galaxy_create` @ line 9626
  (seed write @ 9652), the 0x11274 block (standalone routine; not in
  `functions.tsv`), `FUN_0000a3b4`, `FUN_0000ff25` @ 8786,
  `galaxy_regenerate` @ 25483.
