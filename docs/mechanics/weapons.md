# Weapons: how ships fire at targets

Status: firing pipeline **confirmed** by static disassembly of the reference
build (Interplay CD flat, `build/flat/FRAGILE.EXE.flat`); projectile **flight
and impact details** partially open (the per-tick movement/detonation code sits
in unrecovered gap code; see Open questions). Source: disassembly +
`build/named/FRAGILE.EXE.flat/decompiled.c`.

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

Ore costs per type are given by the game text (Selenium: Explosive, Scatter;
Barium: Area Explosive, Anti-Virus; Crystalite: Vortex; Quazinc: Napalm,
Hellfire; Bytanium: Nuclear; Korellium: Stasis; Dragonium: Mega; Traxium:
Virus; Nexos: Mega).

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

**The tables are written at runtime, like the asteroid tables** (same anomaly
as `docs/mechanics/asteroid-spawning.md` documents for 0x9c9c etc.): the flat
bytes at 0x5c800/0x5c900 are dead code. The fill loop at `0x21414` computes
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
   dword tables at `0x5c800/0x5c900` — all "tables in code", values
   runtime-only), sets node type `+0x8` (either the constant 0x20 or
   `sqrt(distance)+1`, `0x5d4a4`), `+0x13` launcher kind, `+0xb` owner,
   `+0xa` flags, `+0x9` subtype, and bumps the per-(race,type) counter at
   `0xd0a4`. The spawner recurses (twin/Scatter-style multi-shot) and, for
   the scaled path, uses the launch-position helper `0x52294`.

**Missile type selection.** The shooter's missile cargo is a byte array at
`+0x48`. At fire time `0x52c24` (or `0x52ca4` for the second target slot)
rolls rng up to four times to pick a slot, retrying while the per-type table
`0xb1bc` (respectively the pointer table `0xb200`) says the picked type is
invalid; the fallback is type 9. These per-type tables are the missile
validity/spawn tables (runtime values not statically readable, see Open
questions).

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

**The 0x200e4-family "combat tick" is unreferenced (stale).** The per-subtype
handlers at 0x200e4/0x2049c (dispatch via 0xba8a/0xbfe4)/0x20564/0x2059e/
0x20809 (the `rng_next(100) < 0xc095[subtype]` strike roll)/0x20b51/0x210a7,
and the sweep helpers 0x1fd34/0x1fde4, have **no static callers anywhere in
the image** (checked against the full disassembly). Their table reads
(`0xc02c..0xc0a4` per-subtype stats, strike byte `0xc095`, speed base
`0xc0a4`, `0xba8a`/`0xbfe4` dispatch) land on instruction bytes in the flat
(the "tables in code" anomaly, `weapon-and-turret-numbers.md`). The only
static chains into the combat machinery run through the live event handler
`0x52b74` (event types 0..2 → cell-hit scan `0x1aea4` + `+0xb` mark; type 4
→ `combat_shot_spawn` with an rng value) and the slot code above. So the
strike-roll/heading-roll accuracy mechanics found in that family must be
treated as **possibly stale** — whether the live game rolls a per-shot
"Strike Rate" is unconfirmed (a runtime trace is required; the fleet panel's
**Strike Rate** stat and the missile targeting dialog's "Strike chance: %d%%"
are the game's own labels, and one blueprint advertises "+25% strike
accuracy"). See `weapon-and-turret-numbers.md`.

**Targeting scores.** `0x52e64` scores a candidate from the shooter position:
distance must be in `[0x40, 0x4000]` and the bearing within ±0x10 of the
shooter's heading, else 0x7fffffff (rejected); otherwise the score is the
squared distance, or a fresh rng roll when the target is closer than 0x100
(and `+0x7` unset). The best score wins the slot.

**Arc sweep (stale, kept as reference).** The child-list sweep `0x1fde4` is
reachable only from the unreferenced 0x200e4-family (see above) and is
therefore not confirmed as live; it documents the firing model the stale
handlers used: a launcher (node `+0x8` type, `+0x1e` facing, `+0x1f*param_2`
range) walks the target's child list; every child whose world position
(`+0x14/+0x15` cell offsets + per-type offsets from `0x386d4/0x386d5`) lies
within the range² and whose angle lies inside the facing arc (`+0x1e` ± 0xa0,
byte angles — a wide front cone) is marked hit (`+0xb = 5`, or 0xf6 for
non-turret types) and takes damage via `0x1adb4` (child `+0x9` HP −= damage,
destroyed at ≤ 0). The live hit path in this build goes through the event
handler `0x52b74` (cell scan `0x1aea4`).

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

- **Dogfight accuracy**: the strike-roll/heading-roll mechanics found in the
  0x200e4-family are probably stale (no static callers — see the dogfight
  section). Whether the live game rolls a per-shot chance against the
  panel's "Strike Rate" (and how the +25%-accuracy blueprint applies) is
  unconfirmed; the answer lives in the runtime-filled weapon callbacks and
  needs a memory trace of a live fight.
- The per-tick **flight movement and detonation** of SHOT nodes: the
  movement uses the shared direction tables and the `+0x16` homing steer is
  confirmed, but the exact updater loop and the impact/crater application
  (the reference equivalent of the GOG `terrain_create_crater`/effect
  functions) sit in unrecovered gap code — next target for a Ghidra function
  pass or a DOSBox-X trace.
- The runtime values of every "table in code" used here: the direction
  tables 0x5c800/0x5c900 (fill loop 0x21414, constants at flat 0x192/0x19a),
  the per-type byte tables 0x386d4 (stride 0x14), 0x39811/0x39812 (stride
  0x10), 0xba8a (stride 0x10), the missile tables 0xb1bc/0xb200, and the
  handler table 0xbfe4. Same status as the asteroid tables in
  `docs/mechanics/asteroid-spawning.md` — unconfirmed until a runtime trace.
  One table is now **confirmed statically** (the type-picker's per-type
  table with the sprite-name pointers and the 14 turret sprites
  `*_PHOTO\trm08..21.256`): see `weapon-config-table.md`. The `type_pick`
  function is `0x54864` here (`0x51948` in the GOG build).
- The two fire-gate numbers (30% per-tick roll, bearing window 0x0c..0x2b)
  are observed as written; whether the 30% roll is a hit/miss roll or
  rate-of-fire gating, and the exact meaning of the bearing window (the
  below-0x0c branch drops the aim instead of firing), is not yet pinned
  down — a trace of a live attack would settle it.
- The target stat at `+0x17c` (compared against 5 in the enemy check) is
  plausibly the target's armour/defence but is not yet identified.

## References

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
