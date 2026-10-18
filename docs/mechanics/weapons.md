# Weapons: how ships fire at targets

Status: firing pipeline **confirmed** by static disassembly of the reference
build (Interplay CD flat, `build/flat/FRAGILE.EXE.flat`); the **impact side**
(flight, arrival roll, warhead effects and every per-type number) is
**confirmed for the GOG build** and lives in `ship-hit-formula.md`. **Revised
2026-10-18:** the "tables in code / runtime-only" statements of this note were
a base error — static tables read through a DS displacement `D` are at GOG flat
`D + 0x86004` (ISO flat `D + 0x8E004`); only displacements beyond the file size
(BSS, e.g. the direction tables) are runtime-filled. Remaining open: the
per-tick flight code in the ISO gap region and the exact choice of the impact
cell. Source: disassembly + `build/named/FRAGILE.EXE.flat/decompiled.c`.

Addresses are image-relative in the reference flat (the same layout the
pipeline currently produces; the GOG-build equivalents of these functions were
previously named in `config/ghidra/rename-map.json` under their GOG addresses).

## What the weapons are

The game's own vocabulary (US-English text resources) names the weapons
**missiles**. There are thirteen missile types:

Explosive, Area Explosive, Napalm, Hellfire, Scatter, Vortex, Nuclear, Virus,
Anti-Virus, Mega, Stasis, Bug Hunter, Meat-Eater.

Their warhead texts ("Explosive: A conventional (and cheap) warhead for
general use." … "Mega: The power unleashed by this warhead results in the
destruction of an entire asteroid.") describe surface effects, not ship
combat: **missiles are fired at asteroids** (from ships in orbit, or from the
asteroid's own silos), and their effects hit the surface (buildings, colony),
the orbiting ships, or the asteroid itself. Ships additionally carry an
armour stat ("Armor" in the ship panel) and "Hardpoints"; the fleet panel
shows "Strike Rate" and "Missiles At N" (how many missiles a ship carries).

Ore costs per type are fixed by the missile table (`stat-tables-design-sheet.md`
section 4): Selenium: Explosive, Scatter; Barium: Area Explosive, Anti-Virus;
Crystalite: Vortex; Quazinc: Napalm, Hellfire; Bytanium: Nuclear; Korellium:
Stasis; Traxium: Virus; Nexos: Mega (Dragonium is a craft ore, not a missile
ore; the earlier "Dragonium: Mega" was wrong).

## Object pools and the SHOT node

The in-flight missile is a **SHOT** node. The pool is created by the init at
`0x51584` ("shot" debug tag): **1024 nodes × 0x1c bytes**, pool base pointer
stored at BSS `0x16fc8`. Nodes are intrusive doubly-linked lists (links at
`+0`/`+4`); the allocator is the generic list-pop `0x212b4` (nothing to pop →
no shot), the unlink/recycle helper `0x21314`. The save routine dumps the
pool as the save's "SHOTS" section (tag 0xff700000, see
`docs/dataformats/savegame-format.md`).

Node data (after the two link dwords, i.e. at slot `+8`):

| off | size | field |
|-----|------|-------|
| +0x0 | byte | type |
| +0x1 | byte | subtype (copy of type) |
| +0x2 | byte | flags (0x40 set by the "scaled" spawn path) |
| +0x3 | byte | owner index (race) |
| +0x4 | word | X position (screen/world word) |
| +0x6 | word | Y position |
| +0x8 | word | Z position |
| +0xb | byte | launcher kind |
| +0xc | word | target X |
| +0xe | word | target Y |
| +0x10 | word | target Z |

Per-(race,type) missile counters live at `0xd0a4 + race*0x210 + type*2`
(incremented on spawn) — these feed the "Missiles At" fleet display.

## Direction tables (the shared trig)

All movement and aiming in the game uses two **256-entry dword tables** at
`0x5c800` and `0x5c900` indexed by a byte angle 0..255 (full circle). They are
the reference build's sin/cos pair: the daily drift tick `0x11624` moves an
asteroid by `speed * table[dir] / 12` (Y from `0x5c900`, X from `0x5c800`),
the fleet movement moves by `table[angle] * 3`, and the launch-position
helper `0x35874` offsets a moving launcher by `table[+0x1e]/table[+0x1f]`.

**The tables are written at runtime** (BSS: the GOG displacements `0x7eaf0` /
`0x7ebf0` lie beyond the end of the file image, so they cannot be static; this
is the one place where "runtime-filled" is right): the flat bytes at
0x5c800/0x5c900 of the reference build are dead code. The fill loop at `0x21414` computes
320 entries (`fildll(angle) × k1, fsin, × k2, round`) and stores them at
`0x5c7fc + i*4`, so the table the code reads at 0x5c800/0x5c900 is a
phase-shifted window of that 320-entry sine table. The constants `k1`/`k2`
(fldl operands at flat 0x192/0x19a) are likewise runtime-written; the exact
values are **unconfirmed statically** (open question, same as the asteroid
tables).

## The firing pipeline (per tick)

Entry points per tick:

- `main` (tail, every tick) walks the **0xc40c task list** and calls each
  node's handler at `+0xc`; the fleet/ship movement-and-fire tick is one of
  those handlers.
- `0x53474` — the **fleet update tick** (list sentinel `0xc41c`): per fleet,
  runs the order-queue tick `0x51664`, then per ship in the fleet's array
  (`+0x3d0`, count at `+0xf3`): message when owned, array-shift `0x52324`,
  gated tick `0x1e3c4`, and per-child `0x53354`.
- `0x53044` — per-fleet **target maintenance**: each fleet keeps two target
  slots (primary `+0x18`/score `+0x20`, secondary `+0x34`/score `+0x3c`);
  when a slot's target changes it fires via `0x52d24`; a per-slot countdown
  (`+4`) periodically re-acquires via `0x52f94`. Acquisition scores
  candidates with `0x52e64` (see Targeting).
- `0x51664` — the **pending-order queue**: nodes with a `+2`-byte countdown;
  on expiry, order kind (`+0x13`) 0 → `0x52a64` (+`0x515c4` on success),
  1 → `0x52b74`, 2 → `0x54904` + clear `+0x24` + `0x1fcc4`. The cleared
  fields (`+0x24`, `+0x34`, `+0x3c`, and the `0x40`-stride formation block at
  `+0x380`, see `0x515c4`) are the fleet's order/formation state.

**Approach and firing.** The movement/fire handler (`0x20234`-family, gap
code; key fragments verified):

1. If the fleet has a target (`+0x10`): decrement the approach counter
   `+0x14`; the fleet moves toward the target's position (`+0x54/+0x58` on
   the target, 16.16) by `direction-table[angle] * 3` per tick, and the
   heading `+0x1e` is steered toward the target (`atan2` via `0x5d464`,
   angle read via `0x5d4d4`).
2. While the approach counter `+0x14` is below `0x4000` the fire wrapper
   `0x35514` runs: it decrements `+0x14` by `0x100` per tick and calls the
   fire function `0x551f4` once the counter is below `0x4000`.
3. `0x551f4` (the **fire function**, called every tick while in range):
   - if `+0x14 < 0x800`: **stop firing** — clear the acquired target `+0x20`
     (arrival);
   - otherwise, only fire if the target (`+0x10`) is an **enemy**: the
     target's owner (`+0xd0`) differs from the shooter's owner (`+0x9`), and
     either the target's owner is an alien race (index > 8) or the target's
     stat at `+0x17c` is below 5;
   - acquire a fire-target if none held: `0x55104` walks the target's child
     list (children with per-type byte `0x386d7[type*0x14] == 3` and counter
     `+0x16` > 0x100) and keeps the child with the best rng roll (stored at
     `+0x20`);
   - compute the two positions: `0x35874` puts the fleet's own position
     (from its `+0x18/+0x1a/+0x1c` words or the moving-variant offsets) into
     `0x7a5c8/0x7a5cc/0x7a5d0`, then `0x52294` replaces them with the
     acquired child's world position (the child's `+0x14/+0x15` cell coords
     plus the per-type byte table `0x386d4` stride 0x14);
   - **homing steer**: the bearing from the child to the fleet (delta of the
     two positions, `0x5d4d4`) is compared against the child's `+0x16`
     angle; deviation > 8 steers `+0x16` by −4, deviation < −8 by +4,
     otherwise `+0x16` snaps to the bearing (each tick; the tick returns
     without firing while the deviation is outside ±8);
   - **fire gate**: `rng_next(100) < 30` — a **30% roll per tick**; then the
     bearing is recomputed and must fall in `[0x0c, 0x2b)` (byte-angle
     window ≈ 17°..60°): below 0x0c the aim is dropped (`0x36744` re-rolls
     the child's `+0x16` and `+0x20` is cleared), at/above 0x2b the tick
     skips firing;
   - on a successful fire: `0x54104` adds the launch velocity (per-type byte
     tables `0xa6bc/0xa6bd` stride 6 × 0x270/256, scaled by the direction
     tables) to the launch position, then the launch context is recorded
     (globals `0x36e64` target-child, `0x36e68` kind=1, `0x36e69` target
     owner, `0x36e6c/0x36e6e/0x36e70` X/Y/Z from the launch-position globals,
     `0x36e74` shooter, `0x36e78` flags=2), **one missile is consumed**
     (shooter `+0xa` -= 1) and the shot is spawned via `0x51724`.
4. `0x51724` — the **spawner** (also called directly by the target-change
   path `0x52d24`): pops a SHOT node, zeroes it, fills position from the
   launch globals and the per-type tables (`0x39811/0x39812` stride 0x10,
   dword tables at `0x5c800/0x5c900` — the latter are runtime-filled BSS, the
   former are an asset-descriptor table, see below), sets node type `+0x8` (either the constant 0x20 or
   `sqrt(distance)+1`, `0x5d4a4`), `+0x13` launcher kind, `+0xb` owner,
   `+0xa` flags, `+0x9` subtype, and bumps the per-(race,type) counter at
   `0xd0a4`. The spawner recurses (twin/Scatter-style multi-shot) and, for
   the scaled path, uses the launch-position helper `0x52294`.

**Missile type selection.** The shooter's missile cargo is a byte array at
`+0x48`. At fire time `0x52c24` (or `0x52ca4` for the second target slot)
rolls rng up to four times to pick a slot, retrying while the per-type table
`0xb1bc` (respectively the pointer table `0xb200`) says the picked type is
invalid; the fallback is type 9. The ISO displacements `0xb1bc` / `0xb200` map (shift 0x6E8) to GOG
`0xaad4` / `0xab18`, i.e. flat 0x90AD8 / 0x90B1C — inside the hardpoint-item
rating block (S@0x90AB4 rating A, 0x90AEC rating B, 0x90B1C rating C of
`stat-tables-design-sheet.md` section 3). So these are most probably
**hardpoint-item** validity / rating tables and the shooter's `+0x48` array is
the fitted-items array rather than a missile cargo (**I**; the "missile type"
wording of this paragraph is doubtful until the ISO bytes are re-read).

> **Corrected 2026-10-18 (overturned):** the table `0xa4ac` (GOG `0x9dc4`, flat 0x8FDC8) is the COLONY EVENT table (APV viruses and Terran colony events; mode byte = cure, byte +9 = stage length in days), not a ship weapon-slot table, so the paragraph below (fire-delay byte, "rearm floor") is withdrawn; see `weapon-and-turret-numbers.md`. The ammo-pool and `0x14384` observations were read from the same colony-event code and are unverified as weapon logic.

**Ship hardpoint weapons (ship-vs-ship / dogfight).** Ships also carry
hardpoint weapons (the Laser, Photon Cannon, Plasma Cannon, …): the per-type
table `0xa4ac` (stride 0xc — callback fn `+0`, race mask `+4`, mode byte
`+8` = 0xa4b4, −1 = disabled, fire-delay byte `+9` = 0xa4b5, flag `+0xa`)
drives the weapon slots (`call *0xa4ac(%edi)` at 0x1489a), with per-race
weapon slots at `0xcdd4` and the fire resolution `0x14384` (slot node `+0x8`
weapon type, `+0x10` fire countdown reloaded from 0xa4b5, `+0x12` state,
`+0x13` flags bit 2 = the intercept/secondary mode; shots consume ammo from
the per-race per-category pools at `0xf058` stride 0xf4).

The fire resolution `0x14384`:
- owner check: races 1..8 fire normally; owner 0 or >8 (aliens) roll
  `rng_next()` and return unless the roll hits;
- when the slot state (`+0x12`) reaches 0 the weapon re-arms: mode byte
  `0xa4b4[type] == -1` → weapon disabled; otherwise (bit 2 of `+0x13` clear)
  `weapon_ammo_check` (`0x4a374`: category must be < 5 and the per-race
  pool word at `0xf058[race*2 + (cat+0x44)*0xf4]` non-zero) gates the shot,
  and on success the slot countdown `+0x10` reloads from the fire-delay byte
  `0xa4b5[type]` after a fixed 0x28-tick rearm floor; with bit 2 set
  (`0x13`) `weapon_ammo_consume` (`0x4a3b4`) decrements the pool and
  `0x14114` fires immediately;
- the actual shot/beam behaviour is inside the per-type callbacks
  (`call *0xa4ac(%edi)` — see Open questions: the callback pointers are
  runtime values).

**The 0x200e4-family "combat tick" is the live combat machine (corrected).**
The per-subtype handlers at 0x200e4/0x2049c (dispatch via 0xba8a/0xbfe4)/
0x20564/0x2059e/0x207a4 (the `rng_next(100) < 0xc095[subtype]` strike roll)/
0x20b51/0x210a7 and the sweep helpers 0x1fd34/0x1fde4 have no static callers
because they are **dispatched through pointer tables** (static in the GOG
flat, which is why no static caller exists): the task-list walk calls the
handler at node `+0xc`, and `combat_shot_spawn` (`0x1ffc4`) loads that handler
from the pointer `0xbff8` (+4); the per-type dispatch reads
`0xbfe4[0xba8a[type*16]]` (GOG `0xb918[0xb3be[type*16]]`: the list for the
missile id). The stored code pointers are flat − 4. The earlier "probably
stale" conclusion was therefore wrong — the live chain runs
`0x51664` → `0x52b74` → `combat_shot_spawn` → the 0x200e4-family handlers.
The GOG retail build proves the same: its twin machine (handlers at
0x20094..0x20b54, spawned by `obj_spawn_child` 0x1fbc4) is present and live.
The full hit-resolution analysis — the blast sweeps (these are **missile
warhead** effects on the attacked asteroid's structures, not ship beam weapons
or turrets), the per-tick strike roll, the direct-hit path, the aim spread and
every per-type number — is in `ship-hit-formula.md`. The panel/dialog **percentages** are a different,
distance-based computation and are confirmed — see the next section.

## Strike chance: the missile accuracy formula (confirmed)

Status: **confirmed** by static disassembly in both builds — the ISO flat's
`FUN_00021104` (helper at `0x21104`, thunk `0x21184`; `math_angle_from_delta`
`0x5d464` is misnamed — it is a 2-D distance helper: `fildl` both deltas,
`0x66f58` = `sqrt(x²+y²)`, truncate to int) and the GOG build's `race_stat_percent`
at `0x20cb4` (`math_hypot` `0x5a214`). The two implementations are identical.

The game's "Strike chance: %d%%" — the missile targeting dialog's estimate
(TXT 34563) and the agent report's "Report of enemy missile launch" (TXT
34479) — is a pure distance function:

```
dx = (target.X − launcher.X) >> 16     ; 16.16 world coords → whole units
dy = (target.Y − launcher.Y) >> 16
dist = floor(sqrt(dx² + dy²))          ; integer, 2-D only (Z ignored)
base = 0x20 (32)                       ; 0x40 (64) if the launcher's owner
       is a normal race (index < 9) and owns the Missile Guidance System
chance = dist ≤ base ? 100
       : max(0, 100 − (dist − base) · 100 / 160)   ; integer division
```

The guidance flag byte lives in the per-race research/blueprint array
(stride 0x26 = the 38-entry Sci-Tek catalogue; ISO base `0xcc34`, GOG base
`0xc558`): offset `+0xf` = catalogue index 15 = **Missile Guidance System**
(TXT 121394, "increase in strike accuracy of 25%"). The **Asteroid Tracker**
(offset `+0x5`, `0xcc39`) is *not* in the formula — per TXT 9148 it only
enables the display of the estimate.

Effect: 100% at ≤ 32 units (≤ 64 with guidance); then the chance falls by
an average of 1 percentage point per 1.6 units of distance, hitting 0% at
192 (224 with guidance) units. Integer division makes this a staircase:
distances 33/65 still return 100%; the first 99% values are 34/66. The
guidance blueprint therefore adds at most 20 percentage points, rather than
implementing the text's "+25%" as a multiplier. Units are whole world
units (16.16 fixed point shifted right 16); their player-facing scale is
not yet measured.

**Verification (2026-10-15).** Rechecked the instructions in
`build/flat/full_disasm.txt` and `build/flat/gog_disasm.txt`. The signed
`sar 16` is applied to each coordinate difference **before** the hypotenuse,
so negative fractional deltas round down, not toward zero. The hypotenuse
itself is truncated: ISO `0x5d488` calls `0x5ede2`, whose temporary x87
control-word high byte `0x1f` selects round-toward-zero before `frndint`;
GOG `0x5a238` calls the identical helper at `0x5bb52`. The previous
`round(sqrt(...))` description was wrong. For example, whole deltas (33, 8)
give distance 33 and 100%, not rounded distance 34 and 99%. At (34, 0) the
answer is 99%; at (191, 0) it is 1%; at (192, 0) it is 0%.

**What this verifies.** The targeting/report percentage is confirmed, and
the colony launch path also stores that value on each selected missile:
ISO `0x4e900` computes it once, `0x4e962..0x4e970` passes it in ECX to
`0x210e4`, and `0x210e7` writes CL to missile byte `+0x0a`. That establishes
a gameplay input, not just UI text. The consumer is the flight handler
(GOG `0x1fce4`, traced 2026-10-18): at the first approach tick it rolls
`rng_next(101)`; a roll at or below the byte gives the missile a 255-tick
timeout (it arrives), a roll above gives a 10-40-tick timeout (it expires en
route, see `ship-hit-formula.md`). So the percentage **is** the arrival
probability, (chance+1)/101 to be exact.

Callers (ISO): the targeting list header `FUN_0003b0e4` (the "100 if own
asteroid, else formula" path — the missile targeting screen's strike-chance
display) and the message builders `obj_spawn_subtyped`/`obj_spawn_bitmasked`
(the latter is the missile-launch report; its node `+0x58` carries the
chance). The same helper also scores ore buyers
(`FUN_0001a114`/`race_find_ore_buyer`, gated at > 25) — the helper is a
generic distance→percentage, not missile-specific.

**Targeting scores.** `0x52e64` scores a candidate from the shooter position:
distance must be in `[0x40, 0x4000]` and the bearing within ±0x10 of the
shooter's heading, else 0x7fffffff (rejected); otherwise the score is the
squared distance, or a fresh rng roll when the target is closer than 0x100
(and `+0x7` unset). The best score wins the slot.

**Cone sweep (confirmed live — see `ship-hit-formula.md`).** The child-list
sweep `0x1fde4` runs inside the live missile impact machine (its GOG twin is
`combat_cone_effect` `0x1f9e4`, reachable from the live event chain). A
warhead node (node `+0x8` type, `+0x1e` facing, `+0x1f*param_2` range) walks the
attacked asteroid's structure list; every child whose world position (`+0x14/+0x15` cell
offsets + per-type offsets from `0x386d4/0x386d5`) lies within the range²
and whose angle lies inside the facing arc (`+0x1e` ± 0xa0, byte angles — a
wide front cone) is marked hit (`+0xb = 5`, or 0xf6 for non-turret types)
and takes damage via `0x1adb4` (child `+0x9` HP −= damage, destroyed at
≤ 0). Children within the inner radius `(node+0x1f · range²) >> 6` skip the
arc test. The generic sweep damage is 5.

## Fleet structure facts

- Fleets are created by `0x528c4`: a node linked into the `0xc41c` list with
  ship array at `+0x3d0`, ship count `+0x3cc`, **max four ships per fleet**
  (a fifth is rejected, `0x1f354`), per-ship heading `+0x34` set at creation
  from the target angle, and a random fleet token at `+0x3c8`.
- The save routine (`0x218b4`) persists the fleets as the "SHIPS" section;
  the ships themselves are surface objects (the 0x54-byte pool, tag
  0xffc00000) — a ship in the fleet panel is one of the asteroid's surface
  objects whose list the save follows.

## Open questions

- **Hit resolution — answered**: see `ship-hit-formula.md`. Missile warheads
  resolve by circle / cone sweeps over the attacked asteroid's structures with
  no accuracy roll; the strike roll (`rng_next(100) < per-race byte`) exists
  only in the Vortex storm walker, and the displayed "Strike Rate" / "Strike
  chance" is the distance formula that also decides whether a missile arrives
  (a roll at or below it gives the missile a 255-tick timeout, a roll above it a
  10-40-tick one). The per-race bytes are **static** and listed there.
  Whether ship hardpoint weapons and turrets have a resolution model of their
  own is unanswered (no table; the weapon callbacks sit in gap code
  `0x13800…0x13d80`).
- The per-tick **flight movement and detonation** of SHOT nodes: the
  movement uses the shared direction tables and the `+0x16` homing steer is
  confirmed, but the exact updater loop and the impact/crater application
  (the reference equivalent of the GOG `terrain_create_crater`/effect
  functions) sit in unrecovered gap code — next target for a Ghidra function
  pass or a DOSBox-X trace.
- The "tables in code" used here, resolved on 2026-10-18 (GOG flat = displ. +
  0x86004): `0x386d4` (stride 0x14) is the building class table (footprints,
  GOG `0x36274`); `0xba8a` (stride 0x10) is the missile table's id field (GOG
  `0xb3be`); `0xbfe4` is the static per-missile handler-list table (GOG
  `0xb918…`); `0xa6bc/0xa6bd` are the building muzzle bytes; `0x39811/0x39812`
  (stride 0x10) belong to the asset (sprite) descriptor table; `0xb1bc/0xb200`
  most probably fall in the hardpoint rating block. Still runtime: the direction
  tables 0x5c800/0x5c900 (fill loop 0x21414, constants at flat 0x192/0x19a;
  GOG `0x7eaf0/0x7ebf0` are BSS). The type-picker's table with the sprite-name
  pointers and the 14 turret-sprite names is statically readable and is a
  **sprite descriptor table**: see `weapon-config-table.md`. The `type_pick`
  function is `0x54864` here (`0x51948` in the GOG build).
- The two fire-gate numbers (30% per-tick roll, bearing window 0x0c..0x2b)
  are observed as written; the 30% roll is a **rate-of-fire gate** on the
  missile firing pipeline (it decides whether a tick fires a missile at
  all), not a hit/miss roll — the hit resolution is in
  `ship-hit-formula.md`. The bearing window (the below-0x0c branch drops
  the aim instead of firing) is still not fully pinned — a trace of a live
  attack would settle it.
- The target stat at `+0x17c` (compared against 5 in the enemy check) is
  plausibly the target's armour/defence but is not yet identified.

## References

- `docs/mechanics/ship-hit-formula.md` — the hit models (arc/radius sweep,
  strike roll, direct hit), the aim-spread computation and the displayed
  strike percentage (this session's analysis).
- `docs/mechanics/weapon-config-table.md` — the per-type weapon table,
  sprite-name pool and type picker (confirmed statically).
- `build/named/FRAGILE.EXE.flat/decompiled.c` — named view (this build).
- `build/flat/full_disasm.txt` — raw disassembly of the reference flat
  (regenerated by `make flat-disasm`).
- `build/iso/_SAVE/*.000` — sample saves; SHOTS/SHIPS section layout in
  `docs/dataformats/savegame-format.md` (GOG build; layouts match).
- Game text: `_TEXT/AMERICAN.TXT` (missile names, warhead texts, ship/fleet
  panel labels).
- GOG-build weapon names (the `weapon_*`/`projectile_*` entries of
  `config/ghidra/rename-map.json`) were the semantic map for this pass; the
  GOG and reference builds differ in layout, so the addresses do not match.
