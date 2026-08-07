# Asteroid spawning on the new default game

Status: confirmed (static disassembly of the GOG retail build,
`build/flat/FRAGILE.EXE.flat` + `build/named/FRAGILE.EXE.flat/decompiled.c`).
Source: disassembly; runtime trace still deferred.

## Terminology: "galaxy" is the game's "asteroid"

Draft notes and the reference-build docs call the master-list nodes
**galaxies** ("galaxy with 25..31 planets"); the game's own vocabulary calls
them **asteroids** — the colonisable bodies the text names "Unowned
Asteroid", "TetraCorp Asteroid", "Rigellian Asteroid", etc. This document and
the rename map use the game's term throughout (the map tokens were renamed
galaxy_* → asteroid_* when the terminology was corrected). Evidence:
`asteroid_assign_index` (0x22b94) sets `[+0xc0]` = owner type and the
per-type name fields; the game text lists exactly fifteen owner names — 0
Unowned, 1 TetraCorp (the player), 2..8 HumanCorp2..8, 9..14 the six alien
races — matching the fixed-asteroid creation loop (types 1..8, then the six
tagged specials 9..14); the drift tick moves these nodes ("Colony asteroid
... drifted out of known space") and the collision check names them ("Colony
asteroids %s and %s have collided"). What the reference notes called the
"planet count" (25..31 at +0x8c) is the asteroid's **size parameter**: it
drives the surface terrain radius (count²/4), the count×count surface grid
at [+0x90], the ore-seam ring placement (count/2 + 4), and the ore setup.
"Sector" (SK%07.3q) is a separate concept: a map-grid region of the asteroid
field used for navigation. The 25..31 rolls at creation are therefore
**asteroid sizes**, not a count of sub-bodies.

## Scope note: this document covers the GOG build

All addresses below are **image-relative offsets in the GOG retail flat**
(`FRAGILE.EXE`, image base 0x85760 in the EXE, flat imported at base 0).
The earlier `docs/mechanics/asteroid-creation.md` and `docs/mechanics/rng.md`
were written against the reference-ISO build, whose flat has a different
layout (different DOS/4G stub, different BSS). The mechanics are the same;
addresses and struct offsets are not. Notable GOG-side differences:

| thing | reference build | GOG build |
|-------|-----------------|-----------|
| main RNG state | 0x4cd7c | **0x6f854** |
| second RNG state | 0x4cd80 | **0x6f858** |
| `rng_seed` | 0x5bb0e | **0x5897e** |
| `rng_next` | 0x5bada | **0x5894a** |
| `rng_next2` | 0x5bac2 | **0x58932** |
| `rng_mix` | 0x5baf2 | **0x58962** |
| `asteroid_create` | 0x11a64 | **0x117b4** |
| `asteroid_place` | 0x11c24 | **0x11974** |
| `asteroid_regenerate` | 0x320d4 | **0x304e4** |
| home-asteroid block (seed 12345) | 0x11274 | **0x11084** |
| asteroid seed field | +0x98 | **+0x88** |
| asteroid count field | +0x9c | **+0x8c** |
| starting-value table pair | 0xa384 / 0xa3c0 | **0x9c9c / 0x9cd8** (real data) |
| `g_asteroid_ptr` | 0xc3c4 | **0xbcf8** |
| object-list sentinel | 0xc3f4 | **0xbd18** |

Important: the reference build's "missing static tables" problem
(`asteroid-creation.md` open question) exists in the GOG build **too** — the
10-word tables at 0x9c9c and 0x9cd8, the auto-spawn gate table 0x9cb0, the
speed table 0x9d78, the direction table 0x9da0 and the sin/cos tables
0x7eaf0/0x7eb70 all hold **code-like bytes in the flat** (verified: they
decode as executable instructions and no relocation record targets them).
The game reads those addresses as data at runtime; whether the flat bytes are
the actual values or the tables are written at runtime is unresolved without a
trace (same open question as the reference build).

## The new default game = single-player campaign

The campaign new-game start is a small routine at 0x279xx (in a gap; the
decompiled view has it as unrecovered code):

```
279cc:  mov ecx,1
        mov [0x1661c],ecx      ; g_num_fixed_asteroids = 1
        mov [0x63f94],ecx      ; g_campaign_flag = 1
279d3:  mov esi,0x2d1f0        ; (campaign resources pointer)
        ...
27a04:  call 0x22364          ; the new-game setup
```

The skirmish/multiplayer branch (0x279f2) leaves `g_campaign_flag == 0`.

## New-game setup @ 0x22364

1. Reads the arena-size index `[0x16610]` (`g_scenario_index`), looks up the
   size pair in the word table at **0x1663c** (small/medium/large), and sets:
   - `[0xc6d4]`/`[0xc6d8]` = grid dimensions (divisor used by `asteroid_place`),
   - `[0xc6ec]`/`[0xc6f0]` = pixel extents (size << 5),
   - `[0xc354] = 0`.
2. `call 0x22404` (unidentified setup), `call 0x228e4` — the latter does
   `rng_seed([0x16620])` (`g_scenario_seed`; **0x228f4** is an `rng_seed`
   call site) and fills per-asteroid scratch tables.
3. `call 0xf854` — the world-creation dispatcher (below).
4. Follow-up: `call 0x4144`, `call 0x16454`, `call 0x39bf4(-1)`,
   `call 0x4d574` (player start state, camera, resources).

## The dispatcher @ 0xf854

```
f854:  cmpl $0,[0x16618]        ; g_mode_flag (multiplayer?)
       jne  0xf884              ; -> slot-filling path (Path A)
f85d:  cmpl $0,[0x63f94]        ; g_campaign_flag
       jne  0x11084             ; -> HOME BLOCK (default campaign!)  (jump, not call)
f86a:  cmpb $0,[0x1660c]
       jne  0xfd14              ; -> fixed-asteroid path (Path B)
       fall through -> 0xf884
```

The home block is reached by a **direct conditional jump** (0xf864 `jne
0x11084`), which is why a byte search for call targets / pointer dwords finds
no references to it. It **returns** (0x110f9) — control comes back to the
caller of 0xf854 (0x223c5).

## Home block @ 0x11084 (the default campaign opening)

Verified flow (0x11084..0x110f9):

```
rng_seed(12345)                 ; canonical fixed seed
asteroid_create()                 ; 0x117b4, see below
test eax,eax; jz skip
asteroid_place(0xb4)              ; 180: fixed cell slot, see below
asteroid_assign_index(asteroid, 1)  ; 0x22b94: index/type 1, see below
[asteroid+0x51] = 0               ; clear flag
loop i=0..9:
    word [0x9c9c + 2i]      -> [asteroid + 0x5c + 2i]    ; starting-value set 1
    word [0x9cd8 + 2i]      -> [asteroid + 0x150 + 2i]   ; starting-value set 2
asteroid_rank_start_values()      ; 0x2ff04, see below
[0xbcf8] = asteroid               ; g_asteroid_ptr = home asteroid
ret
```

So the home asteroid is fully deterministic: seed 12345 -> type roll -> count
roll -> seed rolls -> fixed starting values -> ranked slot.

## asteroid_create @ 0x117b4 (GOG)

Same shape as the reference build, different offsets:

1. `obj_list_pop()` (0x20e64, sentinel 0xbd18); `FUN_00020e24()` initialises
   the node sub-structs at +0x1ec and +0x40.
2. If `[0x16604] != 0`: `[+0x96] = 0xffff` (special marker).
3. `[+0x40] = rng_next(5) + 4` — asteroid type 4..8.
4. Count: `(+0x8c) = 2 * (12 + ((type-4)*3)/5 + rng_next(2)) + 1` — odd,
   25..31.
5. `[+0x88] = (rng_next(0x10000) << 16) | rng_next(0x10000)` — the asteroid
   seed (two live-stream rolls; **not** a name hash).
6. `[+0xa4] = 0`, `[+0x13d] = 0xff`.
7. Self-referential list anchors at +0x8/+0xc, +0x10..+0x3c, +0xb0..+0xbc.
8. `[0xc344]++` — global asteroid counter (the same counter the main-loop
   auto-spawn gate compares against; 49988 == 0xc344).
9. Hooks: `call 0x12694`, `call 0x124f4` (start-value generation/setup).

## asteroid_place @ 0x11974 (GOG)

1. Marks the occupancy grid **0x7e298**: for every object in the 0xbd18 list,
   `grid[(y>>16)/0x20 * 0x20 + (x>>16)/0x20] = 1`.
2. `param == 0x3e8` (1000) and `0x3e9` special cases: rolls and returns
   without placing (these are the "spawn near player / extra" sizes used by
   the main-loop auto-spawn gate).
3. `param < 1000`: cell = `param / g_arena_size_x` style division; position
   `[+0x44] = (cell_x * 0x20 - 0x10) << 16`, `[+0x48] = (cell_y * 0x20 - 0x10) << 16`.
4. `asteroid_finalize()` (0x11904): `[+0x41] = table[0x9d78][rng_next(16)]`
   (16-entry sub-type table) plus further position finalization.

## asteroid_assign_index @ 0x22b94 (gap function, verified asm)

Called once per created asteroid/asteroid with (object, type). Assigns the
object's type index and slot bookkeeping:

1. `[+0xc0] = type`; `[+0x96] |= 1 << type` (type bit in the marker word).
2. Per-type slot counters: `[0xcb5c + type*520]++`,
   `[0xcb5d + type*520] |= 1` (0xcb5c/0xcb5d, stride 0x208).
3. `call 0x30714` — asteroid access-grid support (allocates `[asteroid+0x90]`
   bit-grid; calls 0x2f9e4 + 0x2fa44).
4. **Faction path** (`1 <= type <= 8`, incl. the home asteroid):
   - `call 0x2df44(0x14, obj, 0, 0)`; `call 0x1a3a4(0x14, g_cell_y, g_cell_x, obj)`
     (0x9b558/0x9b554 — the two helpers take size 0x14 = 20);
   - `[+0x9a] = 1 << type`; if `type == [0xc6b0]` (player's index): copies
     `[0x16624]/[0x16628]/[0x1662c]` into `[+0x84]/[+0x85]/[+0x86]`;
   - three `rng_next(40)` rolls -> slot fields 0xcb5f/0xcb60/0xcb61
     (stride 0x208);
   - `call 0x17db4` (colony capacity: `[+0x1b4] = clamp(100 - n*100/30, 10) * [type + 0x9edb]/100`),
     `call 0x1a064`, `call 0x14f64`, `call 0x7444`, `call 0x74a4`;
   - surface-object loop: for each 0x14-byte terrain record whose type byte is
     5, `call 0x19804(obj, record_index)` (creates the surface objects).
5. **Wild path** (types outside 1..8): `call 0x18264` (per-asteroid type
   initialiser); `[0xc6b8] = type - 9` (table index `t`); then:
   - `asteroid_ore_setup(0x185d4)` and `object_create_on_cell(0x181b4)` twice,
     with table values `[0x16644 + type*12]` (+`[0xa455 + type]`);
   - `[+0x19e] = 1` (colony level, see below); `[+0xc2] = 50`; deposit-respawn
     timer values (see `ore-and-mining.md` — these are timers, not ore
     amounts):
     `[+0x1a4] = [0x9e78 + [+0x19e] + t*4]`, `[+0x1b0] = [0x9e90 + [+0x19e] + t*4]`,
     `[+0x1af] = [0x9ea8 + [+0x19e] + t*4]`, `[+0x1b2] = [0x9ede + t]`,
     `[+0x1b3] = [0x9eb0 + t]`;
   - **handler pointers** (called by the per-type tick 0x15ce4 as
     `calll *444(%ebx)` / `calll *448(%ebx)`): `[+0x1bc] = dword [0x9f48 + t*4]`,
     `[+0x1c0] = dword [0x9f60 + t*4]`. In saves these read as 0xfffe9f30-ish
     values — the flat's image is loaded at runtime base ~0xfffe0000 and the
     per-type handlers live at flat offsets 0x9b50..0x9f30 (the
     "code-like" region between the ore tables).
   - `call 0x17db4`, `call 0x1a064`, `call 0x14f64`;
   - slot words: `[0xcb56 + type*520] = word [0x9eb0 + 2*type]`,
     `[0xcb5a + type*520] = [0x9ed8 + type]`, `[0xcb74 + type*520] = word [0x9ecc + 2*type]`;
   - `call 0x7444`, `call 0x74a4`.
6. Name: `[+0x18f..+0x19d]` = per-type name bytes from **0xb0a4** (`[+0x18e]`
   from `[0xb0a4 + type]`, the rest from `[0xb0b3 + type]`).
7. `rng_next(100) + 50` -> `[0xcb5f + type*520]`; `call 0x5dd4`;
   `[0xc6f4] = 0`; `call 0x1a914`.

**Ore reserves are set at creation too** (all types, not only wild): the
10-word reserve array `[+0x5c + i*2]` (one word per ore, game-text order
Selenium…Nexos) is rolled by the reserve generator 0x124f4 (per-ore presence
roll + amount roll, `rng < word[0x9cfc + i*14]` etc.); the home block instead
copies the fixed word table 0x9c9c, and the six wild types 9..14 start with
fixed reserves `[300,400,400,150,70,60,35,35,0,0]` (Selenium 300 … Dragonium
35, Traxium 0, Nexos 0). Unowned (type 0) asteroids get random reserves with
Traxium (2..15) present on ~34% and Nexos (1..8) on ~28% of asteroids. Full
analysis in `docs/mechanics/ore-and-mining.md`.

**`[+0x19e]` is the colony level (1..3),** not a constant: written by the
value-score function (~0x740) from the reserve-weighted sum against the
thresholds at 0xbe48/0xbe4c/0xbe5c; observed 1 (fresh), 2 (colonised wild),
3 (developed). It indexes a column of the timer tables and of the deposit
tables 0xa476/0xa477/0xaf34 — which is why the timer fields differ between
saves of the same asteroid (level 1 → 2 switches the column: `+0x1a4` 15 →
18/19).

## The fixed-asteroid path @ 0xfd14 (Path B)

Loop `esi = 1 .. [0x1661c]+1` (campaign: one pass, esi=1):
`asteroid_create`; `asteroid_place(0xf1)` for the first pass, `asteroid_place(0xf7)`
after; `asteroid_assign_index(obj, esi)`; `[+0x51] = 0`; `call 0x12594`;
if `[0x1660a] != 0` copy 10 words `0x9c9c -> [+0x150 + 2i]`;
**`[0xbcf8] = asteroid`**; `call 0x100e4`, `call 0x10354`, `call 0x10ad4`;
6x `call 0x1f824(obj, ebp, 0..5)`.

Then the eight fixed specials:
`asteroid_create` + `asteroid_place(0x16e)` (untagged),
`asteroid_create` + `asteroid_place(0xe4)` (untagged), and six tagged:
place sizes 0x130/0x12f/0x12e/0x12d/0x150/0xca with
`asteroid_assign_index` types **10/11/9/12/13/14** and bits
0x4/0x8/0x2/0x10/0x20/0x40 OR-ed into `[0x16615]` (`g_fixed_asteroid_flags`).

## asteroid_rank_start_values @ 0x2ff04 (gap function)

Loop i = 0..9: `score = (word [asteroid+0x5c+2i] << 8) / word [0x9cf0 + 14i]`
(10-entry divisor table, stride 14); keep the maximum score and its index;
store the index byte at `[asteroid+0x43]`.

## Content generation: asteroid_regenerate @ 0x304e4 (GOG)

Same skeleton as the reference build:

```
save g_rng_state
free two scratch list nodes
if (g_last_asteroid_seed != asteroid->+0x88 || [0x1c7f8] == 0 || [0x1c800] == 0):
    asteroid_gen_surface(asteroid->+0x88)      # 0x2ec84: terrain height field
    asteroid_gen_ring_objects()              # 0x303f4: 12 objects, 2 rings of 6
    g_terrain_buffer = alloc()             # 0x83854; 0 -> fatal (0x58f04)
    rng_seed(asteroid->+0x88)
    asteroid_gen_terrain_alloc()             # 0x2ef04 (also derives radius fields)
    asteroid_gen_terrain_spiral()            # 0x2f4c4 (height-field spiral fill)
    asteroid_gen_terrain_reseed()            # 0x2f9e4 (rng_seed(seed) + roll)
    asteroid_gen_terrain_spiral2()           # 0x2fc94
    asteroid_gen_terrain_grid()              # 0x2ff64 (grid fill, 0x400-stride)
    asteroid_gen_terrain_place()             # 0x30274 (cell extraction)
    g_last_asteroid_seed = asteroid->+0x88
    g_last_asteroid_count = asteroid->+0x8c
recreate two scratch list nodes
rng_seed(asteroid->+0x88)
asteroid_place_home_asteroid()               # 0x2fdd4: home-asteroid placement
restore g_rng_state
```

Callers: the per-asteroid regenerate entry `asteroid_tick_regen` (0x30bb4) and
the world-round driver at 0x30c00 (via the `asteroid_tick_loop` 0x30d94 /
0x3123f chain), each `mov [0xbcf8], eax` before the call — i.e. the current
asteroid is regenerated when the world round runs (entry into the asteroid).

## asteroid_gen_ring_objects @ 0x303f4 (the "12 objects")

Verified asm:

```
save g_rng_state
obj = alloc(); rng_seed([asteroid+0x88])
[obj+0x18] = [0x1c7d4]          ; sprite/object base
[obj+1] |= 0x10
x = -rng_next(1280) << 16       ; random angular offset
[obj+0x10] = 0x500000           ; ring radius A
[obj+0xc] = x
loop i=0..5:                    ; first ring
    [obj+0] |= 1                        ; activate
    [obj+0x1c] = 4 + (i & 3)            ; four images per ring
    call 0x5fcd4()                      ; link/register
    [obj+0xe] += 0x140                  ; 320 = angle step
x = -rng_next(1280) << 16
[obj+0x10] = 0x600000           ; ring radius B
loop i=0..5: same shape         ; second ring
[obj+0] |= 0x81
call 0x5a801(); restore g_rng_state
```

Both rings are rotated randomly but all angles come off the asteroid seed, so
the whole layout is deterministic.

**What the ring is.** The twelve objects are **pure visual decorations** —
the game's text gives them no name. Evidence: they are allocated by 0x62397,
which pops 128-byte nodes from a dedicated free list (sentinel 0x74350) and
links them into the render node list; they never enter the master object list
(0xbd18), so the movement tick, the collision check and the type assignment
never see them. They are drawn through the render pointer table at 0x81840
(8-byte entries, count 0x83870; toggled by 0x2d924/0x2d974 — show/hide in
the field view). Each node carries its own ring geometry: `[+0x10]` = radius
dword (0x500000 / 0x600000 = 80/96 px 16.16), `[+0xe]` = angle word,
`[+0xc]` = 16.16 angular offset, `[+0x1c]` = sprite image 4..7 (four images
per ring), `[+0x18]` = sprite base read from 0x1c7d4 (BSS; runtime value
unconfirmed). Their screen position is computed from the asteroid position at
draw time (they have no world position of their own), so they surround the
asteroid as a two-row ring of small rocks. Whether they
rotate over time is not verified; a runtime trace would settle it.

## Per-asteroid initialiser asteroid_init_by_type @ 0x18264 (gap)

Switch on the object's type byte `[+0xc0]` (six cases, jump table at 0x18244):
- rolls `rng_next(256)` -> `[+0x1d5]` (variation byte);
- each case writes the 4-byte offset field `[+0x1c4..+0x1c8]` from
  `(count/2 + k)` scaled by the sin/cos tables **0x7eaf0 / 0x7eb70**
  (k = 4 or 8 depending on case) — i.e. the asteroid sits on a ring whose
  radius is derived from the asteroid's size parameter;
- some cases also set `[+0x1c4]/[+0x1c5] = 0xfe` (unplaced marker) or roll
  further offsets.

The wild path of `asteroid_assign_index` calls this per asteroid; the cell
objects (`object_create_on_cell` 0x18104 / 0x181b4) are the small per-cell
field objects: `[+0x14]/[+0x15]` = cell coords from `g_cell_x/g_cell_y`
(0x9b554/0x9b558), `[+0x8]` = type, `[+0x9]` = subtype from
`[type*6 + 0x9fd0]`, `[+0xa]` = 1 or `[type*6 + 0x9fd1]`, behaviour pointer
`[+0xc] = 0x17ff0`.

## The home asteroid, exactly (seed 12345)

The home asteroid node in the saves (SAVEGAME.000/.009, node 0x03A21C) gives
ground truth: seed at [+0x88] = **0x50269FDC**, size parameter 27 at
[+0x8c]. An earlier hand simulation of the RNG produced a different seed
(0xa16c7d02) — that value is superseded by the save; the simulation's other
rolls (type/size) match the save. The type roll `rng_next(5)` = 2 → **surface
style 6** and size roll `rng_next(2)` = 0 → **size parameter 27**
(`2·(12 + 6/5 + 0) + 1`) stand; the seed itself is save-verified.

**27 is the size parameter, not an asteroid count.** The campaign start
creates exactly **one** master-list object — the player's home asteroid —
and the whole field layout (surface terrain, ore seams, ring rocks) is a pure
function of seed 12345 + these rolls.

## How many asteroids at the start

**One.** The campaign path (home block) creates exactly one master-list
object — the TetraCorp home asteroid. Nothing else on the start path calls
`asteroid_create` (verified caller census of 0x117b4: only the gate, the
creation loops, the specials, the savegame loader and the home block).
During the opening ticks, the main-loop gate then creates more asteroids
every 8 ticks while the scenario ceiling (gate table) is unmet, up to the
100-node pool cap — the scenario's asteroid density (Low/Standard/High) sets
how far the field fills.

## Custom game settings: size and density (empirical, save-verified)

The custom-game screen offers size (small/medium/large) and density
(low/standard/high). Savegame dumps (`docs/dataformats/savegame-format.md`)
verify what each one does:

| map | asteroids | X max | Y max | grid cells |
|-----|-----------|-------|-------|------------|
| small / low | 30 | 756 | 471 | 24 × 15 |
| small / medium | 45 | 686 | 437 | 24 × 15 |
| small / high | 60 | 758 | 471 | 24 × 15 |
| medium / medium | 61 | 919 | 563 | 29 × 18 |
| large / high | 91 | 1013 | 626 | 32 × 20 |
| standard (default) | 60 | 764 | 479 | 24 × 15 |

- **One cell = 32 units** on both axes (placement uses `cell*32 + jitter`,
  occupancy grid stride 0x20). Grid = size cells wide × tall:
  small 24×15 = 768×480, medium 29×18 = 928×576, large 32×20 = 1024×640.
- **Density scales the asteroid count**: small maps hold 30 / 45 / 60 for
  low / medium / high (ratio 1 : 1.5 : 2); large/high holds 91; the standard
  campaign holds 60 (≈ small/high).
- The spawn-count bytes `[0x16610]` (size index) and `[0x16611]` (density
  index) drive the keeper's per-type spawn count (`+2` in the keeper loop)
  and the gate-table row (`[0x16611] + 3*[0x16610]`), and `[0x16610]` selects
  the arena size pair from the word table at 0x1663c.

## Movement during the game: the daily drift tick @ 0x11364

Asteroids **do move**. `main` state 5 (0x1db..0x215) walks the master object
list and calls `FUN_00011364` once per object — the daily tick:

```
flags = [obj+0x138]
if flags & 1  -> skip movement, run collision check (0x11104)
if flags & 2 and not flags & 4 -> skip
if [0x16606] != 0 or [obj+0x11e] != 0 -> skip movement
speed = (signed byte)[obj+0x41]           ; +0x41: drift speed
dir   = (byte)[obj+0x42]                  ; +0x42: direction index
[obj+0x44] += (speed * cos_table[dir]) / 12    ; X
[obj+0x48] += (speed * sin_table[dir]) / 12    ; Y   (position is 16.16)
```

- The cos/sin tables are at 0x7eb70 / 0x7eaf0 (indexed ×4).
- **Boundary check**: if X or Y (>>16) leaves `[0, g_arena_extent_x/y)` the
  object is removed from the list (0x11e74); if its type `[+0xc0]` is the
  player's index `[0xc6b0]`, a message is posted via 0x48f94 (type 5,
  priority 30) — the in-game "Colony asteroid %s has drifted out of known
  space, all contact has been lost" event.
- The collision check (0x11104, called for stationary objects) sets
  proximity flags `[+0x4e] |= 8` / `[+0x13a] |= 1`, feeds the pairwise
  collision matrix at 0xc9c8, and reports "Asteroid collision imminent" for
  the player's asteroid.

**Speed/direction are rolled at placement**: `asteroid_finalize` (0x11904)
sets `[+0x41] = table[0x9d78 + rng_next(16)]` (speed; 16-entry table) and
`[+0x42] = table[0x9da0 + rng_next(12)] - 5 + rng_next(10)` (direction;
12-entry table). Both tables hold code-like bytes in the flat — the exact
runtime values are unconfirmed (see the anomaly note above). The drift step
is `speed/12` px per day.

**Movement verified from saves.** Speed `[+0x41]` is a discrete 0..5; speed-0
asteroids are genuinely stationary (identical coordinates across two saves),
speeds 1..5 move linearly with speed (~23 units per speed step over the save
window). New asteroids spawned by the population keeper get their speed from
`asteroid_finalize` on placement. See
`docs/mechanics/asteroid-field-maintenance.md` for the keeper, the "budding"
spawn rule (new asteroids appear near the oldest asteroid of their type —
**never at the map border**), and the measured cluster statistics.

## Where the home asteroid is placed

- **The home asteroid itself**: `asteroid_place(0xb4)` puts it at cell
  `(180 % size_x, 180/size_x + 1)` (180 = 0xb4; the same cell every new
  game — the formula does not depend on the seed), pixel position
  `((cell·0x20 - 0x10) << 16)` on both axes, `size_x` from the per-scenario
  byte-pair table at 0x1663c (index = `[0x16610]`), runtime-filled from the
  scenario/DCONFIG setup (reader unrecovered; values unconfirmed statically).
- **The ore seams on its surface**: the size parameter drives the seam ring
  positions — `asteroid_init_by_type` (0x18264) writes the 4-byte seam
  offset field `[+0x1c4..+0x1c8]` from `(size/2 + k) · trig_table[rand+36] >> 16`
  (k = 4 or 8 per type case; the per-asteroid roll `rng_next(256)` also
  lands at `[+0x1d5]`). The same trig tables are used by the movement tick,
  so placement and motion share one table pair.
- The 12 ring rocks sit at fixed radii 0x500000 / 0x600000 with angular
  spacing 0x140 (see `asteroid_gen_ring_objects` above).

## Object pools and the hard cap

The world-object pools are allocated in the new-game init at 0x22404:

| pool sentinel | nodes × size | role |
|---------------|--------------|------|
| [0xbd04] | 100 × 476 | **asteroids** (master list 0xbd18) |
| [0x168a0] | 8000 × 24 | per-cell field objects |
| [0x168a8] | 1300 × 84 | surface objects |
| [0xbd08] | 80 × 104 | (unidentified) |
| [0xbd0c] | 900 × 40 | (unidentified) |
| [0xbd10] | 16 × 40 | (unidentified) |
| [0xbd14] | 16 × 64 | (unidentified) |

`asteroid_create` pops from the 100-node pool via `obj_list_pop` (0x20e64) and
returns 0 (no creation) when it is exhausted — so **the total number of
asteroids in play is hard-capped at 100**. Each asteroid's size parameter
is 25..31, rolled once at creation and never changed.

## In-game growth: the main-loop auto-spawn gate

`main` state 8 (0x430..0x485): while `g_mode_flag == 0`, every 8 ticks
(`[0xc6bc] & 7 == 0`) and `[0x1660c] == 0`:

```
if table[0x9cb0][ [0x16611] + 3*[0x16610] ] > [0xc344]:   ; 3-wide spawn table
    asteroid_create()
    asteroid_place(0x3e8)     ; 1000: "spawn near player" (cell search)
```

`[0xc344]` is the running asteroid counter (bumped in `asteroid_create`), so the
gate table value per scenario row is effectively the **per-scenario asteroid
ceiling** (≤ the 100-node pool). The gate table sits at 0x9cb0 — code-like
bytes in the flat, values unconfirmed statically. The spawned asteroids get
their asteroid content on entry via the regeneration chain
(`asteroid_regenerate`), and the per-type slot bookkeeping (0xcb5c/0xcb5d,
stride 0x208) counts asteroids of each type 0..14.

## Open questions

- The exact caller chain of the round driver (0x3123f -> 0x30d94 -> 0x30bb4
  -> 0x304e4) back to `main` is by indirect dispatch; the concrete tick in
  which the home asteroid's surface objects first appear in the world view needs a
  DOSBox-X trace.
- `asteroid_place` sizes 1000/1001 and the "spawn near player" search (the
  reference build's `asteroid_place(0x3e8)` used the player cell
  `[0xcdb0]/[0xcdb4]`) were not re-derived for the GOG build; the special
  cases are confirmed but the exact cell-search code is in the surrounding
  gap.
- The 12 ring objects are decorative scenery (visual-only nodes, see
  `asteroid_gen_ring_objects`); the game names no such object.
- The runtime values of every "table in code" (0x9c9c, 0x9cd8, 0x9cb0,
  0x9d78, 0x9da0, 0x7eaf0, 0x7eb70) and of the arena-size table 0x1663c are
  unconfirmed until a runtime trace — the flat bytes at those addresses
  decode as instructions, not data. (The speed table 0x9d78 and direction
  table 0x9da0 feed `asteroid_finalize`; the sin/cos pair 0x7eaf0/0x7eb70 is
  generated at runtime at 0x20fb4 — a 320-entry `fsin` fill.) The ore
  tables (0x9cf8, 0x9e54..0x9eb3, 0x9f48/0x9f60, 0xa41e..0xa45b, 0xa476,
  0xaf34, 0x16644, 0x36277) are likewise runtime-filled; their values were
  recovered empirically from saves — see `docs/mechanics/ore-and-mining.md`.
- Whether the gate-table ceiling (per scenario) or the 100-node pool binds
  first in practice is a runtime question; the pool is the hard cap.
- The per-type keep-population loop (0xf884, `docs/mechanics/
  asteroid-field-maintenance.md`) runs on the arena/slot-filling path; which
  exact game states invoke it during campaign play needs a trace.
- Savegame internals (SAVEDATA/SIM_HEAP/BUILDING/SHIPS/SHOTS sections, header
  dwords) are partially decoded; see `docs/dataformats/savegame-format.md`.

## References

- `build/named/FRAGILE.EXE.flat/decompiled.c` — named view (functions that
  Ghidra recovered: `asteroid_create`, `asteroid_place`, `asteroid_finalize`,
  `asteroid_regenerate`, `asteroid_gen_surface`, `asteroid_gen_ring_objects`,
  `asteroid_gen_terrain_*`, `asteroid_ore_setup`, `object_create_on_cell`,
  `asteroid_colony_capacity`, `rng_seed`, `rng_next`, `rng_next2`, `rng_mix`).
- `build/flat/full_disasm.txt` — raw disassembly of the whole flat (gap
  functions: home block 0x11084, dispatcher 0xf854, fixed path 0xfd14,
  `asteroid_assign_index` 0x22b94, `asteroid_init_by_type` 0x18264,
  `asteroid_rank_start_values` 0x2ff04, keeper 0xf884, budding 0x11da4).
- `config/ghidra/rename-map.json` — the GOG addresses live alongside the
  reference-build names.
- `docs/dataformats/savegame-format.md` — savegame layout and the empirical
  per-map tables.
- `docs/mechanics/asteroid-field-maintenance.md` — the population keeper,
  budding rule, movement verification and cluster statistics.
- `docs/mechanics/ore-and-mining.md` — the ten ores, rarity tiers, ore
  generation at asteroid creation, deposit placement and mining depletion.
- `docs/mechanics/asteroid-creation.md`, `docs/mechanics/rng.md` — reference
  build; the GOG equivalents are tabulated above.
