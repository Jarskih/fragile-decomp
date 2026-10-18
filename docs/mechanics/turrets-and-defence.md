# Turrets and colony defence

Status: **behaviour confirmed** (the game's own text resources). The code
architecture notes below were written for the reference build and are
**partly corrected on 2026-10-18** after the table-base problem was solved
(GOG flat = DS displacement + 0x86004): the per-type tables the old text called
"turret range / behaviour / category" are the **craft table** (so the function
that reads them updates craft, not turrets), and the "colony weapon fire gate"
is the **Colony Supervisor performance gate**, not a weapon gate. The
per-type structure stats (hit points, cost, build days, power, footprint,
muzzle bytes) are readable static data: `building-stat-table.md` and
`stat-tables-design-sheet.md` section 1. **There is no per-turret damage /
range / fire-rate table in the game data** (see "The per-turret numbers" at the
end): the only things that tell a turret from any other building are its
text, its cost / power / hit-point row and its non-zero muzzle bytes.

Source: game text (`_TEXT/AMERICAN.TXT`) + disassembly of the reference ISO
flat (`build/flat/FRAGILE.EXE.flat`) and of the GOG flat
(`build/flat/FRAGILE.EXE.gog.flat`). Addresses are image-relative (base 0).

## The defence buildings

The game's own building name list (AMERICAN.TXT, pipe-delimited token table;
index is the 0-based position in that list) gives the Terran defensive
buildings:

| text index | building | role |
|-----------|----------|------|
| 3 | Anti-Missile Pod | "Defensive weapon that automatically targets incoming missiles." |
| 9 | Satellite Silo | spy-satellite launcher |
| 10 | Screen Generator | shield: "Generates a protective screen around several neighboring buildings" |
| 14 | Missile Silo | "Capable of launching any type of missile" |
| 17 | Plasma Turret | "A weapon of greater devastation than a laser turret. Efficient on power use too." |
| 18 | Photon Turret | "The best energy weapon available at this time. Fires photon packets capable of devastating armor." |
| 27 | Laser Turret | "A general purpose, auto tracking, defense turret." |
| 28 / 33 | Solar Matrix / Protected Storage Tower | carry an **integral Laser Turret** ("Protected by a weapon turret.") |

Alien equivalents (all named in the text):

| race | building | tier |
|------|----------|------|
| Braccatian | Fire Power | ≈ Plasma Turret, "slightly more efficient, both in terms of actual fire-power and in terms of accuracy... possibly the most accurate turret weapons in the universe" |
| Mikotaj | Merl / Na-Shrekn | ≈ Plasma / ≈ Photon |
| Artemian | Star Bars / Auto-deterrent / Super-deterrent | ≈ Anti-Missile Pod / turret "having the lowest range and firepower of all Artemian weapons" / ≈ Photon |
| Maunid | Stun Tower / Power Tower | ≈ Laser ("basic colony defense facility") / ≈ Photon "but more deadly" |
| Achaean | Asteroid Shield / Defense Battery | shielding / defensive battery (role details unconfirmed) |

The internal building type byte (structure node `+0x8`) **is** the text index
minus 919 for all 177 buildings of every race (`stat-tables-design-sheet.md`,
section 1.1) — the earlier doubt "do not assume text index == type byte" is
settled in favour of equality. The `type == 9` and `type == 8` tests of the
defence update `FUN_0001c2f4` are therefore *craft* ids (Spy Satellite and
Command Cruiser, see below), not building ids.

## How turrets fire (game text)

Quotes from AMERICAN.TXT; all three turret descriptions follow the same
template, differing only in the power/range/damage wording:

- **Auto-fire, motion detection**: "A standard motion-detection sensor
  automatically begins to track any hostile ships as soon as they fire on the
  colony. The turret will then return fire at standard range" (Laser, Plasma;
  Photon: "sophisticated motion-detection sensor... return fire at an
  optimized range").
- **Power requirement**: "assuming that it has sufficient power to do so" — a
  turret without power does not fire.
- **Weapons Factory requirement**: "Other defensive structures such as Laser
  Turrets will not function unless there is a Weapons Factory to maintain and
  supply them."
- **Damage ordering**: Photon > Plasma > Laser ("the greatest fire-power of
  the three turret types", "greater fire-power than the standard Laser
  Turret", "the most basic of colony defenses, this low-powered weapon").
- **Range ordering**: Laser/Plasma = "standard range"; Photon = "optimized
  range" (longer). The Artemian Auto-deterrent has "the lowest range and
  firepower".
- **Turret Optimizer** (Sci-Tek blueprint): "doubling the damage of all
  existing and future turrets... increasing the firepower of each shot by a
  factor of two" — applies to every turret type, retroactively and to future
  builds.
- **Anti-missile defence**: "This turret will attempt to knock out incoming
  warheads before they reach the asteroid." (Anti-Missile Pod; the Artemian
  Star Bars are the same building.)
- Turrets are immobile by definition ("a warship moves pretty damn fast,
  whereas a turret is by definition immobile").
- Fleets do not fight to the death: the player sets a "retreat level" — "the
  percentage of the fleet that must be destroyed in combat before that fleet
  will retreat".

## Code architecture (reference build)

### Which object the "defence update" updates (corrected)

The reference-build function `FUN_0001c2f4` (no direct callers, reached
indirectly) reads the per-type tables at displacements `0xb244`, `0xb247` and
`0xb251` (stride 0x14). At the correct base these are the **craft table**
(GOG `0xab5c` → flat 0x90B60): `+0` the craft's range, `+3` its speed, `+0xd`
its class id (7 = Space Dock). The type tests in the function fit the craft ids
too: `type == 9` is the **Spy Satellite** (stand-down: the satellite never
moves or attacks) and `type == 8` is the **Command Cruiser** (**I**: it re-places the
small craft it carries around itself with RNG-jittered positions clamped to the
map). So the function is the **craft / fleet-member update**, and the fields of
its node (`+0x18` target pointer, `+0x1c` / `+0x30` five-slot order arrays,
`+0x38` / `+0x3c` 16.16 position, `+0x4e` flags, `+0x52` speed behaviour byte,
`+0x0a` range loaded as `range >> 2`) are craft-node fields. It does not
describe colony turrets. The earlier reading as a "defensive-structure update"
is superseded.

### Structure (building) node — what is established

A building on the asteroid surface grid sits in the asteroid's `+0x8` list;
fields used by the structure code:

| offset | role |
|--------|------|
| +0x8 | building type byte = building id (indexes all per-building tables) |
| +0x9 | current hit points (initial value from building table +0, plus 10 with the Building Armour blueprint) |
| +0xb | burn state (5 or −10 after Napalm / Hellfire; `ship-hit-formula.md`) |
| +0xc | per-structure callback pointer (a `ret` stub for ordinary buildings; silos reuse it as the head of their missile-children list) |
| +0x14 / +0x15 | surface-grid cell (x, y), signed bytes |

### Per-type tables (corrected 2026-10-18)

| ISO displ. | GOG displ. → flat | stride | what it is |
|---------|--------|-------|------|
| 0xa6b8 | 0x9fd0 → 0x8FFD4 | 6 | building table +0: hit points (static, byte-identical in both builds, `building-stat-table.md`) |
| 0xa6ba | 0x9fd2 → 0x8FFD6 | 6 | building table +2: build cost u16. The earlier "stride 1 or 6" is settled: all accesses compute `type·3·2 = type·6` |
| 0xa6bc / 0xa6bd | 0x9fd4 / 0x9fd5 | 6 | building table +4/+5: **muzzle offsets** (non-zero only for Anti-Missile Pod, Plasma / Photon / Laser Turret, Protected Solar Matrix, Protected Storage Tower); they position the shot origin (scaled by 0x270/256 ≈ 2.44 and rotated by the turret angle) |
| 0xaade | 0xa3f6 → 0x903FA | 1 | morale delta of the building (not a power value) |
| 0xb244 | 0xab5c → 0x90B60 | 0x14 | **craft** range (u16) |
| 0xb247 | 0xab5f | 0x14 | **craft** speed (FN) |
| 0xb251 | 0xab69 | 0x14 | **craft** class id |
| 0x386d4 / 0x386d5 | 0x36274 / 0x36275 → 0xBC278 | 0x14 | building class table: footprint width / height in cells |
| 0xa4ac | 0x9dc4 → 0x8FDC8 | 0xc | colony event table (Corrected 2026-10-18; formerly misread as a ship weapon-slot table; see `weapon-and-turret-numbers.md`): handler `+0`, race mask `+4`, cure `+8`, stage length in days `+9`, flag `+0xa` |

### Craft update state machine (reference build, `FUN_0001c2f4` family)

- `FUN_00001404` (main state 3, "structure update") walks every asteroid's
  `+8` structure list and calls each structure's `+0xc` callback (and, via
  `0x1adb4`, applies the burn tick to burning structures).
- `FUN_0001c2f4` — the craft update: type-8 (Command Cruiser) path places the
  carried craft; type-9 (Spy Satellite) and armed-flag paths stand down via
  `FUN_0001bdd4`; the default path arms the craft (`+0x52 = 1`), loads its range
  from the craft table (`>> 2`) into `+0x0a`, then checks the target pointer
  `+0x18`: no target, or distance-squared beyond range squared → stand down
  (`FUN_0001ddc4` clears target and orders); in range → the firing resolution
  continues in the (unrecovered) caller.
- `FUN_0001ddc4` — stand-down: clears the 5-slot order arrays, the target
  pointer and the range value.
- `FUN_0001e934` / `FUN_0001c494` — re-arm/refresh: reload node `+0x0a`
  (range) and `+0x52` (speed) from the craft table; the type-8 case also
  refreshes the carried craft.

### The attack flow

- Fleets attack through the race-attack functions (`race_attack_launch`,
  `race_attack_tick`; GOG addresses 0x17e24/0x17f34 — the reference build's
  equivalents sit in the same region) and the combat cluster 0x14000..0x15000:
  order lists at `+0x38` with per-order type/timer fields, weapon slots per
  race at `0xcdd4` (stride 0x28, 10 slots), targeting
  (`FUN_0004a374`/`FUN_0004a3b4`), and the fire resolution `FUN_00014384`
  (reloads the slot countdown from weapon-table `0xa4b5`, i.e. `+9`).
- Ship weapons use the `0xa4ac` table (stride 0xc; see above).
- The fleet tick `FUN_00053474` (0x53474) runs every tick from main's tail:
  ship list at `0xc41c`, per-ship data at `+0x3d0`, combat-flag gates, and
  the missile/weapon slot accounting. `rng.md` already flags the
  0x49000..0x54000 block ("combat/damage rolls") as the next candidate for a
  dedicated mechanics doc.

## The colony gate (formerly "colony weapon fire gate") — corrected 2026-10-18

The block previously documented here (ISO fire tick 0x9b3e, GOG 0x99c4…0xa0c8,
rolls at GOG 0x9a89 / 0x9b14) was read as the "hit formula" of colony turrets
and silos. It is **not a weapon gate**:

- It lives inside the AI / colony economy tick (`ai_economy_tick` 0x98b4 and its
  neighbours) and walks the asteroids of one race that are ordinary colonies
  (colony flag `+0x139` bit 4, not frozen: hold timer `+0x11e` = 0).
- The "shot spawner" it calls (GOG `0x48e64`, `event_message_post_b`) is a
  **message poster**: arguments are message type 0x8d, a duration of 30 and the
  text pointers `0x37b00`/`0x37b04` (or `0x37b30`/`0x37b34`) plus the name text
  from the pointer table at `0x39040` indexed by the record's `+8`.
- The byte read at record `+0x1c` ("accuracy") is the **Colony Supervisor's
  performance meter** (`economy-and-personnel.md` section 4: the record is the
  supervisor node, meter cap = table byte +0x14 of the 28-byte supervisor
  rows at flat 0x8F680, i.e. 100, 95, 80, 100, 100, 100, 100, 100, 70, 100, 88,
  98, 95, 100, 90, 88 for supervisors 0..15; the drift threshold dword is the
  row's T2 workload level).

What the code does, per colony and per tick, stays as described: roll
`rng_next(100)` against the meter (a roll at or above it fails and zeroes the
cooldown byte), count the cooldown byte (`+0x1a8` / `+0x1a9` / `+0x1ab`) down
and, when it reaches 0, reload **15** and post the supervisor's notice to the
player (only for the player's own race); another path re-arms **40** (GOG
0x115a4). A meter byte of 255 (signed −1) never passes; below 5, a second
`rng_next(100) < 5` roll triggers a 27-way pick (byte table GOG 0x987c; Corrected 2026-10-18: that table is the starting build-menu id list, so this "event pick" reading is doubtful) of an
event / message effect. The meter drifts by 1 per colony tick: falls when the
supervisor's workload exceeds the row's T2 level, otherwise rises to its cap.

The 15 and 40 are therefore **message cooldowns**, the probabilistic gate is
the supervisor doing (or reporting) his work, and nothing here fires a weapon.
The earlier derived statements "about twice per game day", "snap shots" and the
worked examples (accuracy 100 / 50 / 5 / 255 / 0, drift scenario) described the
same arithmetic and remain valid only as a description of that
supervisor-notice gate; they are not turret fire-rate data and have been
removed from this note. Detailed supervisor behaviour: `economy-and-personnel.md`.

## The per-turret numbers (answer, 2026-10-18)

**There is no per-turret damage, range, fire-rate or power-use table.** What
the game data holds for the defence buildings (all static, GOG flat):

| building | cost (Cr) | HP | build days | MW used | muzzle |
|---|---|---|---|---|---|
| Anti-Missile Pod | 15,000 | 16 | 36 | 3 | 20,13 |
| Laser Turret | 3,400 | 16 | 25 | 2 | 16,12 |
| Plasma Turret | 5,500 | 20 | 30 | 3 | 27,13 |
| Photon Turret | 7,500 | 20 | 52 | 4 | 29,12 |
| Protected Solar Matrix (built-in turret) | 7,200 | 20 | 32 | 0 | 57,6 |
| Protected Storage Tower (built-in turret) | 7,500 | 32 | 48 | 3 | 52,5 |

(S@0x8FFD4 and S@0xBC278, see `stat-tables-design-sheet.md`; muzzle values are
the two raw bytes.) The damage ordering Laser < Plasma < Photon, the "standard
range" / "optimized range" wording and the Turret Optimizer doubling are
**text-only claims**; no byte in any table found encodes turret damage, range
or fire interval, and the missile blast machine (`ship-hit-formula.md`) is not a
turret model. The craft range (160 / 192 / 320) belongs to ships. How a turret
shot is resolved against ships may therefore be a code constant in the
unrecovered ship-combat code (`0x13800…0x13d80`, the weapon callbacks of the
slot table) or implicit; it is the next thing to trace. Resolution paths 1 and 2
of the old note (runtime trace, GOG re-import) are no longer needed for the
tables: both builds' tables are readable statically.

## References

- `_TEXT/AMERICAN.TXT` (the pipe-delimited token table: building names and
  descriptions — the Terran building name list starts at 0x1107F with
  "Living Quarters", "Laser Turret" at 0x111FD; the Anti-Missile Pod
  description at 0xDE81).
- `build/named/FRAGILE.EXE.flat/decompiled.c` — named view of the partial
  export; `FUN_00001404`, `FUN_0001c2f4`, `FUN_0001ddc4`, `FUN_0001e934`,
  `FUN_0001c494`, `FUN_00014384`, `FUN_0001a4b4` (structure creation),
  `FUN_00053474` (fleet tick).
- `config/ghidra/rename-map.json` — GOG-side combat names (`race_attack_*`,
  `weapon_*`, `combat_*`) whose reference-build addresses are not yet mapped.
- `docs/mechanics/main-loop.md`, `docs/mechanics/rng.md` — the tick
  dispatcher and the RNG call-site census (combat block 0x49000..0x54000).
- The supervisor / colony gate: ISO `build/flat/full_disasm.txt` 0x9b3e..0xa071
  (rolls at 0x9c03/0x9c8e/0x9f78/0x9fcf/0xa000, growth drift at 0x856e); GOG
  `build/flat/gog_disasm.txt` 0x99c4..0xa0c8 (rolls at 0x9a89/0x9b14, drift at
  0x83ee) — inside `ai_economy_tick` 0x98b4.
- `docs/mechanics/economy-and-personnel.md` — the supervisor table and meter.
- `docs/mechanics/ship-hit-formula.md` — missile blast machine and values.
