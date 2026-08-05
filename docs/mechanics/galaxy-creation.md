# Galaxy creation

Status: confirmed (static disassembly); the one indirect-call assumption (the
new-game path reaching the home-galaxy block) is flagged below and awaits
runtime confirmation.
Source: disassembly (`build/flat/FRAGILE.EXE.flat` + `build/named/.../decompiled.c`)

## Overview

A *galaxy* is one node of the game's master object list (sentinel
`g_obj_list_sentinel` @ 0xc3f4). The current galaxy is pointed to by the
global `g_galaxy_ptr` @ 0xc3c4. Galaxies are created by **`FUN_00011a64`
@ 0x11a64** and later filled in by a chain of deterministic generators driven
from the galaxy's 32-bit seed — see `docs/mechanics/rng.md` for the RNG
plumbing and the full `g_rng_state` write-site census.

## The creation routine `FUN_00011a64` @ 0x11a64

Verified asm flow:

1. **Allocate**: `FUN_000212b4` pulls a node from the object list (sentinel
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
9. `FUN_00012994()`, `FUN_000127f4()` — post-creation hooks.

### Galaxy struct fields established so far

| offset | size | meaning |
|--------|------|---------|
| +0x50  | 1 | galaxy type, 4..8 (roll + 4) |
| +0x51  | 1 | flag byte (cleared for the home galaxy) |
| +0x54, +0x58 | 4×2 | position/scale pair (written by `FUN_00011ba4`) |
| +0x6c, +0x15e | 2×9 | home galaxy's 9 starting-planet slots (word pairs from tables 0xa384 / 0xa3c0) |
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

- **Home galaxy** — block at 0x11274 inside `FUN_000104c4`:
  `rng_seed(0x3039)` (== **12345**, the canonical LCG seed) immediately before
  `FUN_00011a64`; then `FUN_00011c24(0xb4)`, `FUN_00023054(1)`, `[+0x51]=0`,
  the 9 starting-planet word pairs copied from the static tables 0xa384/0xa3c0
  into +0x6c/+0x15e, `FUN_00031af4`, and finally `g_galaxy_ptr = galaxy`.
  The fixed seed makes the home galaxy's layout reproducible every new game.
- **Race galaxies** — `FUN_0000ff25` @ 0xff25 creates the per-race galaxies:
  each `FUN_00011a64` call is followed by `FUN_00011c24(<size code>)` (0xe4,
  0x130, 0x12f, 0x12e, 0x16e …) and `FUN_00023054(<name index>)` (0x9/0xa/0xb
  for the tagged races), with bits 0x2/0x4/0x8 OR-ed into the byte `DAT_00016d69`.
  **No direct callers** — reached only by indirect dispatch, so the new-game
  entry point is assumed here (confirm at runtime).
- **Main loop (state 8, in-game)** — `main` @ 0x14:
  - `FUN_0000f544` is called every tick while `g_mode_flag == 0` and creates
    7 more galaxies (via `FUN_00011a64`);
  - an **auto-spawn gate** at 0x3d3..0x422: if `[0x16d60]==0`, `[0xcd98]&7==0`,
    and `table[0xa398][ [0x16d65] + 3*[0x16d64] ] > [0xca20]`, it calls
    `FUN_00011a64` then `FUN_00011c24(0x3e8)` — new galaxies keep appearing as
    the game progresses (counter [0xca20] and the per-galaxy count live in the
    two byte counters [0x16d64]/[0x16d65] indexing the 3-wide table).
- Other creation callers in `FUN_00013844` (0x13941..0x13ad5) follow the same
  shape.

## Regeneration: `galaxy_regenerate` @ 0x320d4

Rebuilds a galaxy's content from its seed. Verified flow:

```
save g_rng_state
if (g_last_galaxy_seed != galaxy->+0x98 || FUN_0001e464 == 0 || iRam0001e470 == 0)
    galaxy_gen_surface(galaxy->+0x98)         # surface from seed
    FUN_00031fe4()                            # 6 moons (+0x140 spacing)
    DAT_00061964 = FUN_0005ce74()             # a generation count; 0 → fatal
    rng_seed(galaxy->+0x98)                   # reseed from galaxy seed
    FUN_00030af4, 0x310b4, 0x315d4, 0x31884,
    0x31b54, 0x31e64                          # content chain (continuous stream)
    g_last_galaxy_seed = galaxy->+0x98        # remember done state
    FUN_0001e464 = galaxy->+0x9c              # remember planet count
rng_seed(galaxy->+0x98)                       # home-planet placement
FUN_000319c4()
restore g_rng_state
```

Every generator is deterministic given the seed, and the pre-call `g_rng_state`
is restored, so regeneration neither depends on nor perturbs the live game
stream.

## Determinism conclusion

- A galaxy's entire layout (surface, moons, star fields, planets) is a pure
  function of its 32-bit seed at struct +0x98.
- The seed is produced by two `rng_next(0x10000)` rolls against the live
  `g_rng_state`, and the home-galaxy path seeds that state with the fixed
  constant **12345** first. So **the galaxy layout is a fixed universe on
  every new game**.
- The only clock-seeded stream is `g_rng_state2` (via `rng_seed_clock` in
  `FUN_0005bd24`), consumed solely by the encounter-placement generator
  `FUN_0002f114` — battles vary per run, the universe does not.
- Confirmed at runtime still pending: that the 0x11274 home-galaxy block (via
  `FUN_0000ff25`'s indirect dispatch) runs before any in-game galaxy creation.

## References

- `docs/mechanics/rng.md` — RNG internals, the seed formula, the exhaustive
  `g_rng_state` write-site census, the open cold-start-ordering question.
- `build/named/FRAGILE.EXE.flat/decompiled.c` — `FUN_00011a64` @ line 9626
  (seed write @ 9652), `FUN_000104c4` (0x11274 block), `FUN_0000ff25` @ 8786,
  `galaxy_regenerate` @ 25483.
