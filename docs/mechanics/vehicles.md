# Vehicles (ships): roster, construction and the stat tables

Status: probing — the roster, the construction rules and several concrete
stats are confirmed from the game's own text resource; the per-class numeric
stat table is **not** yet recoverable statically (see "the stat tables").
Source: game text resource (`_TEXT/AMERICAN.TXT`, the same resource the game
displays) + static disassembly of the current flat.

## Build identity — read this first

All addresses in this document are **image-relative offsets in the current
flat** (`build/flat/FRAGILE.EXE.flat`, extracted from the archive.org
reference ISO; image base 0x8A760 in the EXE, flat imported at base 0).

The current tree is the build the earlier docs call the **reference build**:
its `main` dispatcher is `DAT_00036b64` (named `g_game_state`), `asteroid_create`
is at 0x11a64 (sentinel 0xc3f4, seed field +0x98, count +0x9c, type +0x50),
the home block (seed 12345) is at 0x11274, and the main RNG state is at
0x4cd7c. The address tables in `main-loop.md`, `asteroid-spawning.md`,
`ore-and-mining.md` and `asteroid-field-maintenance.md` cite **different**
anchors for the same roles (0x34720 / 0x117b4 / 0xbd18 / 0x11084 / 0x6f854,
node fields +0xc0/+0x88/+0x8c) — those describe the GOG retail build, whose
EXE is not part of this repo. The two builds implement the same game; the
address tables are not interchangeable. **Reconciling the older docs' tables
with the current image is open work** (see the open questions).

The savegames under `build/iso/_SAVE` decode with the GOG build's node
offsets (type +0xc0, seed +0x88, count +0x8c — `docs/dataformats/
savegame-format.md`), so save-verified values from those documents must not be
assumed to map onto this build's offsets without re-checking.

## The vehicles and their names (from `_TEXT/AMERICAN.TXT`)

The game's own text resource names every craft. The singular/plural name
pairs (the plural is what messages like "X ships have been destroyed" use)
appear as consecutive tokens:

| index (TXT offset) | craft | plural |
|---|---|---|
| 120022 | Assault Fighter | Assault Fighters (120680) |
| 120038 | Combat Eagle | Combat Eagles (120697) |
| 120051 | Scoutship | Scoutships (120711) |
| 120061 | Destructor | Destructors (120722) |
| 120072 | Terminator | Terminators (120734) |
| 120083 | Transporter | Transporters (120746) |
| 120095 | Fleet Battleship | Fleet Battleships (120759) |
| 120112 | Space Dock | Space Docks (120777) |
| 120123 | Command Cruiser | Command Cruisers (120789) |
| 120139 | Spy Satellite | Spy Satellites (120806) |

The blueprint ships (names at 120153–120280): Lazzaro Research, Delphini
Assault, Messier-Lukannon, Transportation, Observatory, Rattlesnake,
WidowMaker, HeartsBlood, Morning Glory, SkyMech. The alien vessels (120288–
120663): Hiero, Ylikt-shan, Falari-Lourn, Ruth-Strivakh, Na-Xanth, Gerla-Kans
Explorer, All-Purpose Assault, Shielded Multi-Assault, Ultimate Mk II,
Hardcore, Geostationary Construction, Surveillance Craft Type 5, Combat Craft
Type 1.5, Max Combat Craft Type 6, Elite Command Craft, Transportation Craft
Type 3, Orbital Construction Area, Hunter/Prospector, Dedicated Fighter,
Dedicated Ore Transporter, Orbital Shipyard. The game gives the player no
further description of these; their exact roles are unconfirmed.

The weapon/shield hardpoint items (120957–121140): Ion Cannon, Disruptor,
Napalm Orb, Chaos Bomb, Vortex Mine, Laser, Photon Cannon, Plasma Cannon,
Static Inducer, Warp Generator, Deflector, Shield x10 … Shield x50.

## Confirmed stats from the game text

These numbers are stated by the game's own descriptions (blueprint long
descriptions and the blueprint "parts" screens in `_TEXT/AMERICAN.TXT`):

| craft | hardpoints | other confirmed figures |
|---|---|---|
| Fleet Battleship | **6** ("six weapon hardpoints", 122681; "six hardpoints", 128921) | 92 m long (122681); top speed **2 FN** (single rear thruster, 143977); wing-tip thrust engines, comms antenna + electric-field sensor probe, central gravitic reactor (144032/144150/144315); designed 2364 by R. Giggs, "a fraction of the size of the Federal Battleships", the primary warship of Sci-Tek and TetraCorp (128921) |
| Terminator | **4** ("four hardpoints for mounting weapons", 124684; "its four hardpoints", 137429) | "greater armor than existing ships" (124684); top speed **2 FN** (twin main engine thrusters, 151353); lateral maneuvering thrusters "unrivaled dog-fighting performance" (151259); integral short-range rotary cannon (151140); T-15 model in Federal Marine service, designed 2321 (137429) |
| Command Cruiser | **6** ("six hardpoints", 139568) | "strongly armed and armored"; carries up to **20 smaller fighters** in its hold; can **tow a number of medium craft**; long range (139568) |

| item | confirmed figures |
|---|---|
| Shield x40 | fills one hardpoint, +40 armor points (124168) |
| Shield x50 | fills one hardpoint, +50 armor points (124270); "renders a ship almost (but not quite) invulnerable", 60,000 Cr (135718) |
| Deflector | hardpoint; energizes the hull, deflects most energy attacks, stacks with shields (122575, 128548) |
| Static Inducer | hardpoint; EMP scrambles enemy electronics, "unable to attack or move" during the pulse (124481, 136499) |
| Warp Generator | hardpoint; periodic invulnerability via warp field (138654) |
| Construction Droids | Ship Yards / Orbital Space Docks construct up to **3** craft at once, **6** with droids; construction speed **+25%** (128030; the short description says "twice as many ships", 122475) |

Speed unit: the game displays ship speeds as **FN** (binary panel format
`%S: %d FN`, flat 0x8F21A). What "FN" abbreviates is not stated by the game.

The remaining per-class numbers — cost, build time in days, hull strength,
speed per class, and hardpoint counts for the ships the text does not
describe — are **not confirmed yet** (see below).

## How vehicles are made (game text)

- A Weapons Factory and Ship Yards are required to build ships, plus "supplies
  of the relevant ores and enough money in the Vehicles fund" (TXT 10).
- The Ship Yards build the small craft: Assault Fighters, Combat Eagles and
  Scoutships (TXT 262, 86814). Larger craft are built in the Orbital Space
  Dock, which is itself constructed through the Command Center; only one
  Orbital Dock per asteroid (TXT 1629, 1783).
- TetraCorp provides the blueprints for the Transporter and the Destructor;
  any other blueprints must be purchased from Sci-Tek (TXT 2299). Completed
  ships appear beside the Dock and orbit the colony until ordered or assigned
  to a fleet (TXT 2299).
- Spy Satellites are also paid from the Vehicles fund (TXT 3158).
- Build order management: orders show "time to construction", and can stall on
  missing ores, insufficient Vehicles funds, or insufficient labor; orders can
  be cancelled only before construction of that craft has begun (TXT 1020,
  1320).
- "All available ship types have a number of hardpoints" — points to which
  weapons and/or shielding are attached (TXT 459, 579, 693). The hardpoint UI
  toggles between offensive and defensive hardpoints (TXT 53587); a current
  hardpoint can be selected and placed onto the ship's blueprint, and
  re-clicking removes it (TXT 53653, 53789, 53877).

## Fleet rules (game text)

- Fleet speed = the slowest ship in the fleet (TXT 5698).
- Fleet range = that of the smallest craft in the fleet; it can be extended by
  loading small craft into a Command Cruiser (TXT 8169). The Command Cruiser's
  hold carries up to 20 small fighters (139568).
- Retreat: a per-fleet percentage setting — the fraction of the fleet that
  must be destroyed before the fleet retreats (100% = may never return,
  50% = loses half its ships first) (TXT 6272).
- Orders: proceed peacefully, attack, intercept (a hostile fleet) / merge
  (another own fleet), patrol a sector for a period, cancel the previous
  order, detach ships (TXT 6606–7474); up to five stacked commands per
  ship/fleet (TXT 7788).
- A scout's range circle shows whether it can make it back; out of range it
  may use its "Impulse Limp engines" to get back safely (TXT 10242, 10458).

## Binary anchors (current flat)

- Shipyard/panel format strings: "Cost" 0x8F27C, "Build time" 0x8F284,
  ".days" 0x8F28F, "Name" 0x8E4A2, "Description" 0x8EA04, "Title" 0x8EA1C,
  "%S: %d FN" 0x8F21A, "You Have No Transporters" 0x8F904, "On Order"
  0x9188C, "You Have The Following On Order..." 0x918D8, "iShip selector out
  of range" 0x91DBF, the fleet templates "Ships At" 0xADB08 and "SHIP NAME"
  0xB4FEC, and the save-section markers SAVEDATA/SIM_HEAP/BUILDING/SHIPS/
  SHOTS/SAVE_END at 0x9A2AC..0x9A360. None of these strings is referenced by
  a static code dword in the flat — the game builds its string-pointer tables
  at runtime, so string xrefs cannot be used to locate the UI code statically.
- The state-8 fleet-activity tick `fleet_activity_tick` (0xcd34, 804 bytes,
  gated by `g_fleet_enable` 0xcda4, one of the four subsystem enables armed
  at tick > 700 in main): walks the 16 activity records at `[0xc3f0] + 8 +
  i*0x40` (the 16×40 pool from `asteroid-spawning.md`), posting message
  type 7 (arrival/deadline) via 0x4b6b4. Record fields: +8 type, +9
  race/owner, +0xa flags (bit1 = in transit, bit2 = at destination, bit4 =
  order active, bit0x10 = message pending), +0x34 asteroid pointer, +0x38
  tick countdown (0x32 = 50 in `FUN_0000d0d4`'s reset), +0x2c word from the
  per-type table `word[0x9f84 + type*14]`. The per-type slot counters live
  at 0xd22c+0x210*i (stride 0x210, indices 1..14).
- The fleet tick `fleet_update_tick` (0x53474, 727 bytes, called from main's
  tail every tick and from the state-8 branch): walks the **ship fleet
  list** at sentinel **g_ship_list_sentinel 0xc41c**. Fleet node (stride
  0x3f4): ship count at +0x3cc (short), per-ship slots — ship pointer at
  +0x3d0+4·i, offset words at +0x3e2/+0x3ea; per-ship sub-node: +8 type, +9
  race, +0xc weapon-list head, +0x36 fleet retreat percentage, +0x58 a
  second type byte (< 0xf), position at +0x50/+0x54 (16.16). The tick
  refreshes the per-race ship-presence bitmaps at 0xd02c, runs the retreat
  roll (damage % vs the fleet's retreat threshold at ship+0x36), and
  accounts weapon slots via `g_weapon_slot_table` (0xcdd4, `[race*0x28 +
  type*4]`, 10 slots per race — the same table the defence doc's attack flow
  uses). Ship weapons use the hardpoint weapon table at **g_ship_weapon_table
  0xa4ac** (stride 0xc: callback fn, race mask, fire timer, mode byte, flag —
  see `turrets-and-defence.md`).
- Savegame: the SHIPS section (marker 0x9A318) dumps a linked pool of 0x54-
  byte nodes (the doc's 1300×84 pool); in the provided saves it contains only
  free-list nodes, so no ship instances are available for field verification.

## The stat tables — open question

The per-class numeric records (cost, build time, hull, speed, hardpoint
counts) are read by the ship code from addresses in the code/data region that
hold **instruction-like bytes in the flat** ("tables in code", same anomaly
as the asteroid tables documented in `asteroid-spawning.md`): e.g.
`word[0x9f84 + type*14]` in the fleet-activity path, the hardpoint weapon
table at 0xa4ac (which sits inside a real function's byte stream), and the
per-type slot words. No code writes these addresses statically; their
runtime values are therefore not recoverable from the flat. This is exactly
the documented "runtime trace required" situation:

- No ship instances exist in the provided saves (the SHIPS section is a free
  list), so the save-diff technique cannot recover per-ship stats either.
- The in-game Ship Yards screen is the authoritative display, but reading it
  requires a runtime session (DOSBox debug build with a memory dump — the
  repo's deferred item from `docs/INSTALL.md` / `scripts/10_dosbox_trace.sh`).
- Until then, treat every unverified number in the table above as
  `?`. What is confirmed: the roster, the construction pipeline, the
  hardpoint system, the confirmed per-ship figures listed above, and the
  fleet rules.

## Open questions

- The per-class numeric stat table (costs, build times, hull, speed,
  hardpoints) — needs a runtime trace; the flat bytes at the table addresses
  are code-like.
- Which TXT tokens the Ship Yards displays for the base ships' descriptions,
  and whether the 10 "blueprint ships" (Lazzaro Research … SkyMech) map 1:1
  onto ship classes or onto variants of them.
- The exact meanings of "FN" and of the fleet-node flag bits (+0xa).
- The GOG-vs-reference build identity of the older docs' address tables (see
  "Build identity"); the repo should eventually re-baseline those tables onto
  the current image or record which artifacts were made from the GOG build.

## References

- `build/reports/strings/_TEXT__AMERICAN.TXT.strings.md` — the text resource
  (token offsets quoted above are byte offsets into `_TEXT/AMERICAN.TXT`).
- `build/flat/full_disasm.txt` + `build/flat/fragile.o` — the current flat,
  disassembled (the `_binary_..._FRAGILE_EXE_flat` blob; objdump -d, whole
  image).
- `build/named/FRAGILE.EXE.flat/decompiled.c` — `main` state 8,
  `fleet_activity_tick` (0xcd34), `fleet_update_tick` (0x53474) and
  `FUN_0000d0d4` at the addresses above.
- `docs/mechanics/main-loop.md`, `asteroid-spawning.md` — the same subsystems
  at GOG-build addresses; see the build-identity note.
- `docs/dataformats/savegame-format.md` — SHIPS section layout.
