# Weapon and turret numbers: where the tables really are

Status: **the "tables in code" problem is SOLVED for the GOG build** (it was a
base error, see below); the combat/hardpoint tables listed here are read as
static data from `build/flat/FRAGILE.EXE.gog.flat`. **The 12-record table
formerly read as weapon-slot fire delays is the colony event table** (see below); the earlier "fire delay VERIFIED at 15 / 40 ticks"
finding is **overturned** (those constants belong to a message cooldown, see
"The 15 and 40 constants"). A per-turret damage / range figure **does not
exist as a table** — see "Turrets and hardpoints". The ISO-side values were not
re-read in this revision (the ISO flat is not in `build/` now); the ISO tables
are expected to be byte-identical at ISO flat = displacement + 0x8E004.

Source: `build/flat/FRAGILE.EXE.gog.flat`, `build/flat/gog_disasm.txt`,
`build/named/FRAGILE.EXE.gog.flat/decompiled.c`; older notes of the reference
(Interplay CD) build kept where still valid. Addresses are image-relative (base
0) unless stated. Provenance codes **S** (static table), **C** (constant in
code), **I** (inferred) as in `stat-tables-design-sheet.md`.

## The short answer

- Every per-type stat the game reads through a **DS-relative displacement** `D`
  lives at **GOG flat `D + 0x86004`** (data object at flat 0x86000, plus the
  4-byte image header). For the reference build the base is `D + 0x8E004`.
  Verified on the building table (`0x9fd0 → 0x8FFD4`), the craft table
  (`0xab5c → 0x90B60`), item prices (`0xaa08 → 0x90A0C`), the missile table
  (`0xb3b0 → 0x913B4`), morale (`0xa3f6 → 0x903FA`), the combat block
  (`0xb960 → 0x91964`) and the colony event table (`0x9dc4 → 0x8FDC8`).
- The old "tables in code" anomaly came from reading the displacement as a flat
  offset (flat `D` is code). The old **base search** (below) could not find the
  base because it only tried 16-byte-aligned bases: the true bases `0x86004` /
  `0x8E004` are 4 mod 16.
- Displacements above the file size (GOG flat size 0x1040A7, i.e. `D >
  0x7E0A3`) are BSS and really are runtime-filled: the shared direction tables
  (GOG `0x7eaf0` / `0x7ebf0`, ISO `0x5c800` / `0x5c900`) are the model case.
- **Code pointers stored in data tables are flat − 4** (functions are 16-aligned
  in the code object; the image has a 4-byte header). Add 4 for the flat start.

## What the numbers are and where the code reads them

GOG column: displacement → flat address, with the verified meaning. The ISO
displacement is the GOG one plus 0x6E8 (building/craft block) or 0x6CC
(combat block) — read off address pairs, **I**.

| ISO displacement | GOG displacement → flat | stride | field | what it really is |
|---|---|---|---|---|
| `0xa6b8` | `0x9fd0 → 0x8FFD4` | 6 | byte | **building table +0: hit points** (Armour) |
| `0xa6ba` | `0x9fd2 → 0x8FFD6` | 6 | u16 | **building table +2: build cost**. The "stride 1 or 6" conflict is resolved: every access computes `type·3·2 = type·6` (the "stride 1" pattern is `3t` scaled by 2) |
| `0xa6bc` / `0xa6bd` | `0x9fd4` / `0x9fd5` | 6 | bytes | **building table +4/+5: turret muzzle offsets** (the launch-position helper scales them by 0x270/256) |
| `0xaade` | `0xa3f6 → 0x903FA` | 1 | s8 | **morale delta** (Terran ids), not a power contribution (the old "power/maintenance" reading is superseded; `stat-tables-design-sheet.md`) |
| `0xb244` | `0xab5c → 0x90B60` | 0x14 | u16 | **craft table +0: the craft's range** — *not* a turret range |
| `0xb247` | `0xab5f` | 0x14 | byte | **craft table +3: speed (FN)** — re-armed into the craft node (`+0x52`) |
| `0xb251` | `0xab69` | 0x14 | byte | **craft table +0xd: class id** (value 7 = Space Dock) — not a "building category" |
| `0x386d4` / `0x386d5` | `0x36274` / `0x36275` → 0xBC278 | 0x14 | bytes | **building class table +0/+1: footprint width / height in cells** |
| `0xa4ac` | `0x9dc4 → 0x8FDC8` | 0xc | 12 records | **colony event table** (Corrected 2026-10-18; not a weapon table) — see below |
| `0xba8a` | `0xb3be → 0x913C2` | 0x10 | u16 | **missile table +0xe: the missile id** (record index for ids 0–12) |
| `0xc02c … 0xc0a4` | `0xb960 … 0xb9d8 → 0x91964…` | 15 | bytes | **per-launching-race combat block** (damage, radius², Scatter count, Stasis base, strike %, lifetime base): `ship-hit-formula.md` |
| `0xbfe4` / `0xbff8` | `0xb918` / `0xb92c → 0x9191C…` | 4 | pointers | **per-missile-id handler lists** (static; GOG `0xb914 … 0xb958`) |
| `0xc100` / `0xc101` | `0xba34` / `0xba35 → 0x91A38` | 2 | s8 pairs | **8 neighbour steps of the walker** |
| `0xc458` | `0xbd7c` (runtime) | 4 | u32 | per-race fund; a runtime value, not static data |
| `0x39811` / `0x39812` | `0x373b1`-family (flat 0xBD3B5…) | 0x10 | bytes | **asset (sprite) descriptor table** — not a weapon table |
| `0x5c800` / `0x5c900` | `0x7eaf0` / `0x7ebf0` | 4 | dwords | shared sin/cos direction tables, **BSS, runtime-filled** (fill loop `0x21414` ISO) |

Not table data (runtime globals): `0xcd8c` player race, `0x5bf70…0x5bf78`
build-queue state, `0x7a5c8` / `0x7a5cc` launch-position globals.

### The colony event table (S@0x8FDC8, 12 records of 12 bytes)

Corrected 2026-10-18: this 12-record table (GOG displacement 0x9dc4, flat 0x8FDC8) is the COLONY EVENT table (the six APV viruses and six Terran colony events), not a ship weapon-slot table: every reader is colony-event code (0x13e32..0x141d3, `colony_sickness_post` 0x13e74, handler call at 0x1459a); the race masks are the APV susceptibilities (`alien-ai-trade-victory.md` 8.6); byte +8 is the cure and byte +9 the stage length in days, not a fire delay. (Earlier revisions of this note read it as a
ship weapon-slot table with fire delays 20/30/40; that reading is withdrawn.)

Record: `{code pointer (flat-4), race mask u16 (+4), byte (+6), byte (+7), cure
s8 (+8, -1 = none), stage length u8 (+9, days), flag u16 (+0xa)}`. Race mask bit
`n` = race `n` (1 = TetraCorp; 9 Rigellian, 10 Braccatia, 11 Mikotaj, 12
Artemia, 13 Mauna, 14 Achaean). Records 0-5 are the six APVs (Shell Shock,
Phantom, Judgement Day, Silicon Death, Bug Hunter, Meat-Eater); records 6-11
(mask 0x2) are Terran-only colony events. The full decode of the first six
records (susceptibility, cure, stage length) is in `alien-ai-trade-victory.md`
8.6; the callbacks sit in gap code `0x13804 ... 0x13d74`. Raw values (cure
byte / stage-length byte): records 0-5 cure -1 or a cure id with lengths
30/30/20/30/30/20; records 6-11 lengths 40/40/40/40/30/40. No ship weapon
fire-delay table has been identified; the weapon re-arm time is unknown.

## Turrets and hardpoints: what is and is not in a table

- **There is no per-turret damage / range / fire-rate table.** The only static
  numbers per defence building are the building-table fields (cost, build
  days, hit points, muzzle bytes) and the class-table fields (footprint, MW
  used) — `stat-tables-design-sheet.md`, section 1. The turret and
  Anti-Missile Pod rows are told apart only by the **muzzle bytes** (non-zero
  = armed structure) and by the building type id in the code paths that test
  it.
- The earlier "defence range `0xb244` stride 0x14" is the **craft range**
  (160 for combat craft, 192 for scouts / transporters, 320 for the Command
  Cruiser and satellites, 0 for the Space Dock); the function that reads it
  (`FUN_0001c2f4` in the ISO numbering) is the craft update, not a turret
  update.
- The blast sweeps (`ship-hit-formula.md`) are **missile warhead** effects on
  the attacked asteroid's structures, not turret or hardpoint damage.
- Hardpoint item values that exist: prices, shield armour bonuses and the
  three rating tables A/B/C (below and in the design sheet). Their effect on
  combat is not traced.

## The 15 and 40 constants (overturned "fire delay")

The previous revision reported that "a launcher fires every 15 or 40 game
ticks" because the countdown bytes `+0x1a8` / `+0x1a9` are re-armed to 15 or
40 and the next call is "the shot spawner 0x48e64". That reading is wrong:
`0x48e64` (`event_message_post_b`) is a **message poster**, and the enclosing
functions are the AI colony economy tick (`ai_economy_tick` 0x98b4) and the
colony advisor block (see `turrets-and-defence.md`, "The colony gate").
The 15 / 40 are message-cooldown counters, not weapon fire delays. The 12-record
table at 0x8FDC8 is NOT a weapon re-arm table (Corrected 2026-10-18); the
genuine weapon re-arm times are not identified.

## The base-search campaign (history; premise now known false)

An exhaustive search for a base `B0` with `B0 + displacement` landing on real
data (anchors: zero rng state, ten plausible u16 costs, six code-pointer weapon
rows) found no candidate, at 256-byte and 16-byte alignment, in both directions.
The method was sound but the grid was wrong: the true base is 4 mod 16
(`0x8E004` ISO, `0x86004` GOG). Kept so nobody repeats the search.

## Real data tables found in the ISO flat (role unknown)

Two genuine data structures exist in the flat (they read as data at their
positions, unlike the stat tables):

- `0x71dac`: 0xc-stride rows of **code pointers**, pattern `{a, b, b}`
  (e.g. `{0x7c268, 0x7c14c, 0x7c14c}`, `{0x7c846, 0x7c268, 0x7c268}`).
  A dispatch/jump table; target functions live in the gap code around
  `0x7c000`. Identity unconfirmed.
- `0x97f20`: 24-byte records with **consecutive ids 31..35** at the record
  end, and u16 pairs like `{25000, 1027}`, `{2000, 2000, 8000}` —
  plausibly a ship or weapon stat block (values like 25000/15000/8000
  recall costs/build times). Identity unconfirmed.

Both are worth a future Ghidra function pass on the gap regions.

## Data files on the ISO: checked, none hold stats

The "are the numbers in a data file?" question is now answered with a
survey of the image (stage 03 inventory + the strings index):

- The ISO's only files named `*.DAT` are `STUBBY.DAT` (89 bytes, the
  disc-check stub) and the Engage demo's `DATA.DAT` — neither is game data.
- The game's real data files are the extension-less containers `_B`, `_S`,
  `_M`, `_TRADE`, `_PHOTO`, `_MA`, `_SCITEK`. Their content is assets, not
  stats: the strings survey shows only embedded asset filenames
  (`AC01.256`, `TI001.256`, `*.VID`, `*.WAV`, …) and the formats match the
  graphics/sound loaders — no ship/weapon stat tables and no stat text.
- Re-checking the table regions: reading the displacements as flat offsets
  (`0xa4ac..0xa520`, `0xc02c..0xc0a4`, `0xba8a` / `0xbfe4`, ...) lands on
  instructions — that was the base error. At the correct base (ISO flat =
  displacement + 0x8E004, GOG flat = displacement + 0x86004) the same
  displacements read as plain data tables (see the table above). The only
  genuinely runtime-filled tables are the BSS ones, e.g. the direction tables
  `0x5c800` / `0x5c900` ISO (`0x7eaf0` / `0x7ebf0` GOG), whose fill loop at
  `0x21414` is visible.

So: the numbers are not in any data file on the disc; they are static tables
inside the executable image, readable once the base is right. (The ISO side was
confirmed for the building table; the rest is expected to match the GOG tables
and awaits a re-read of the ISO flat.)

## The combat machine, the 0x357b4 family and the memdump leads

- The 0x200e4-family handlers (ISO) / 0x20094…0x20b54 (GOG) are the **missile
  impact machine**; their dispatch lists are static data in the GOG flat
  (`0xb914…`), which is why they have no static callers (they are reached by
  function pointer). Full analysis and all numeric values:
  `ship-hit-formula.md`.
- The `0x357b4`-family (GOG flat 0xBB7B8, stride 0x14) is the **sprite
  descriptor table** of the type picker (`weapon-config-table.md`), static in
  the GOG build; the earlier "flat equivalent 0x957B4 is zeros" used the wrong
  base.
- `0x39040` (stride 4) is a per-type text-pointer table filled at load.

## Resolution paths (updated)

1. Memdump route: no longer needed for the tables above. Still needed for
   the runtime-written values `0xbd7c` (race funds), the structure list
   contents and anything above the file size (BSS).
2. GOG flat route: done — see `docs/dataformats/gog-build-data.md` and the
   design sheet.
3. Open: the ISO re-read (needs the ISO flat re-extracted), (the twelve
   records at 0x8FDC8 are colony events, not weapon slots) and the behaviour behind the A/B/C hardpoint
   ratings.

## The item price catalog — CONFIRMED static data in both builds

**Update (2026-08-08).** The Ship Yards item-price tables are real static
data in **both** builds (the DS-displacement stat families are static as
well once the base is corrected, see the top of this note). Found
while mapping the weapons/modules prices from a shipyard-screen memdump
(`build/dumps/ram_1ce2a000.bin`, image at dump offset 0x1c901c; all tables
byte-identical flat vs runtime).

- **The 16 weapon/module prices** — GOG flat `0x90A0A`, ISO flat `0x990F4`.
  16 u32s `{price, 0}` pairs. Index 0..15 in the game's own order
  (`_TEXT/AMERICAN.TXT` 120957..121141): Ion Cannon 1000, Disruptor 6000,
  Napalm Orb 4000, Chaos Bomb 12000, Vortex Mine 5000, Laser 1000, Photon
  Cannon 4500, Plasma Cannon 9000, Static Inducer 4500, Warp Generator 9000,
  Deflector 12000, Shield x10 1500, x20 3000, x30 5000, x40 6500, x50 8000.
  Order + Ion Cannon's 1000 Cr verified against the live Ship Yards screen
  (DOSBox observation, 2026-08-08).
- **Shield armour values** — GOG `0x90A80`/`0x90AC0`: `{10, 20, 30, 40, 50}`
  (Shield x10..x50 armour points; matches the game text "Shield x40: +40
  armour points", "Shield x50: +50 armour points").
- **Per-item records** — GOG `0x90B60` / ISO `0x99248` (byte-identical),
  stride 0x14: `{u16 ×6, text-offset u16, days u16, price u32}`; the
  text-offset column (2, 260, 514, 774, 1026, …) points into the Ship Yards
  help-string table in the loaded TXT. The records' prices (6000, 12000,
  3000, 15000, 34000, 24000, 60000, 150000, 300000, …) are a second price
  family — the craft (ships) list, not yet mapped to names (the 60000
  record = 60 days matches the game text's Shield x50 mention only if read
  as a blueprint price; see below). Fully decoded (all 10 records) in
  `docs/mechanics/scitek-blueprints.md`, "The price tables".
- **Blueprint price pairs** — GOG `0xB72E4` / ISO `0xC1638`: `{price u32,
  type u32}` pairs, prices 15000..500000, type ids 0..35 (with -1
  sentinels; the GOG table = the ISO table's tail — ISO carries pairs for
  14 extra type ids). 60000 appears twice (type 15 and 28) — candidate
  blueprint prices for the Shield x40/x50 blueprints ("…all for a mere
  60,000 Cr too!" — TXT 135718, the Shield x50 blueprint description). The
  full type→price readout (both builds) is in
  `docs/mechanics/scitek-blueprints.md`, "The price tables". The 12-record
  table at GOG `0x8F984` / ISO `0x9806C` (`{price u32, 3 packed stat bytes,
  days u32}`) shares values (150000, 300000) with the per-item records and
  may be the same family in a different layout; role still open.
- The 0x90C20..0x91A00 region (decoded 2026-10-18): the missile table (16-byte
  records, S@0x913B4: 13 Terran types, then the alien arsenal lists from
  S@0x91488), the combat block of nine 15-byte per-race arrays (S@0x91964),
  the missile weight words (S@0x919EC), the handler-pointer lists (S@0x9191C,
  0x91A10…) and the 8 neighbour steps (S@0x91A38). See `ship-hit-formula.md`
  and `stat-tables-design-sheet.md` section 4.

Open: which Ship Yards items the 0x90B60 records are (list order from the
live screen would settle it), and the exact role of the 0xB72E4 pair table.

## References

- `build/flat/FRAGILE.EXE.gog.flat`, `build/flat/gog_disasm.txt` — source data.
- `docs/mechanics/ship-hit-formula.md` — missile impact machine with values.
- `docs/mechanics/weapon-config-table.md` — sprite descriptor table.
- `docs/mechanics/turrets-and-defence.md`, `docs/mechanics/weapons.md` —
  behaviour and firing pipeline.
- `docs/mechanics/stat-tables-design-sheet.md` — consolidated tables.
- `docs/mechanics/main-loop.md` — the tick dispatcher.
