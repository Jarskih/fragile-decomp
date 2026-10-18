# Stat tables design sheet: buildings, craft, missiles

Status: **confirmed** for the table layouts, addresses and values quoted
(read from the GOG retail flat and cross-checked against the code that
consumes them and against the game's own text); individual columns whose
meaning is only inferred are marked **I** in the provenance legend and
listed again in "Open questions". Values that exist only at runtime are
collected in "Runtime-only values" with the address to read from a memdump.

Source: GOG flat `build/flat/FRAGILE.EXE.gog.flat`, its disassembly
`build/flat/gog_disasm.txt`, the named export
`build/named/FRAGILE.EXE.gog.flat/decompiled.c`, the text resource
(`_TEXT/ENGLISH.TXT` of the GOG install, same strings as AMERICAN.TXT apart
from small spelling differences), `build/reports/gog_constants.json`. The
tables below are our own re-tabulation of numbers read from those inputs;
nothing is copied from them verbatim.

This page is the consolidated, designer-facing view. The working analysis
behind it lives in `building-stat-table.md`, `vehicles.md`,
`scitek-blueprints.md` and `weapon-and-turret-numbers.md`.

## How to read this page

Provenance codes used in the tables and prose:

| code | meaning |
|---|---|
| **S@addr** | static table in the GOG flat at image-relative address `addr` |
| **C@addr** | constant compiled into code at `addr` (function or instruction) |
| **T** | claim in the game's own text (no number in the binary confirms it) |
| **I** | inferred: follows from S/C/T evidence but was not observed directly |
| **R** | runtime only: not in the static image, see "Runtime-only values" |

Address conventions (all verified):

- **Flat address = DS displacement + 0x86004** for every static table the GOG
  code reads (checked on the building table `0x9FD0 -> 0x8FFD4`, the
  Ship Yards craft table `0xAB5C -> 0x90B60`, the item prices
  `0xAA08 -> 0x90A0C`, the missile table `0xB3B0 -> 0x913B4` and the morale
  table `0xA3F6 -> 0x903FA`). The "tables in code" anomaly of the older
  notes is a base error, not a data problem, for the GOG build.
- **Memdump offset = flat + 0x1C801C** for flat addresses >= 0x86000 (image
  at dump offset 0x1C901C, minus the unmapped 0x1000 stub page).
- **Day** = 32 game ticks at the default game speed (`main-loop.md`).
  Structure and craft countdowns that are decremented once per game day are
  therefore given in days.
- Names are the game's own (`ENGLISH.TXT`). Ids are 0-based indexes into the
  name lists: building id = text index - 919, craft id = text index - 1462,
  Sci-Tek blueprint id = text index - 1530, missile id = text index - 1354.

## 1. Buildings

### 1.1 The id space: 177 buildings, one table

All races share one id space of **177 building ids** (S@0x8FFD4, 6 bytes per
id, ends exactly where the next table starts at 0x903FA):

- ids 0-39: the 40 Terran buildings (text 919-958). The Terran id is also the
  "type" used by the colony code (per-colony building counters sit at colony
  `+0xC8+id`).
- ids 40-176: the six alien races, in the order of the name lists in the text
  (Rigellian 40-62, Braccatian 63-85, Mikotaj 86-107, Artemian 108-129,
  Maunid 130-150, Achaean 151-176), so id = text index - 919 holds for all 177.
  (The race lists use the building-text spellings; the player-facing culture
  names are Rigellian, Braccatia, Mikotaj, Artemia, Mauna, Achaean = race ids
  9..14, `alien-ai-trade-victory.md` section 0.)
- Every alien building carries a **Terran role** (byte +3 of its class-table
  record, S@0xBC278), e.g. Subterranean Extractor -> Mine, Pithoi -> Storage
  Tower, Fire Power -> Plasma Turret. That role agreed with the building's
  name and text description in every one of the 137 cases, which is the
  strongest check of the id mapping; ids with role `(own)` or without a
  Terran counterpart (Science Labs, Databanks, Sports Hall, Dream, Resonance,
  Mask, Lanth, Nurseries, House of the Axe, Shell, The Cube, Gathering Ground,
  Market, Refining Forge, Destination Beam, Goods Yard, Ex-Fang) are the
  race-specific extras.

Record formats:

| table | address | record | fields |
|---|---|---|---|
| building stat table | S@0x8FFD4 | 6 B x 177 | +0 armour (HP) u8, +1 build time (days) u8, +2 cost u16, +4 / +5 turret muzzle offsets u8 |
| building class table | S@0xBC278 | 20 B x 177+ | +0 width, +1 height (cells), +2 u8 (unknown, 0-22), +3 Terran role id, +4 signed MW byte, +0xC..0x13 list-head words (pointer-like values in the file, rewritten at runtime) |
| morale delta | S@0x903FA | 1 B x 40 | signed byte, Terran ids only |
| power priority | S@0x8F38B | 1 B x 40 | building ids in priority order |

### 1.2 Terran buildings: core stats

Cost / armour / build time: **S@0x8FFD4** (+2 / +0 / +1). Footprint and MW
used: **S@0xBC278** (+0,+1 / +4). Morale delta: **S@0x903FA**. Muzzle offset:
S@0x8FFD4 +4/+5. Armour is the base value; a race that owns the Building
Armour blueprint (Sci-Tek id 6) gets **+10** on every new structure (C@0x1A31A).
Cost is deducted from the owner race's fund word (race table at displacement
0xBD7C, the Construction fund of the text; **I** for the label) when the
building is placed (C@0x1A243). Build time is the countdown loaded into the structure at
placement and decremented once per game day; the building works when it
reaches zero (C@0x1BF4). Two special start-up paths load 1 or 4 instead
(C@0x1A327 / 0x1A336, globals at displacements 0x165FA / 0x63F94, role
unconfirmed).

| id | Building | Cost (Cr) | Armour (HP) | Build time (days) | Footprint (cells) | MW used | Morale delta | Muzzle offset |
|---|---|---|---|---|---|---|---|---|
| 0 | Living Quarters | 1,000 | 5 | 32 | 2x2 | 0 | 10 | - |
| 1 | Power Store | 1,500 | 34 | 32 | 2x2 | 0 | 0 | - |
| 2 | Storage Facility | 1,500 | 24 | 20 | 2x2 | 1 | 0 | - |
| 3 | Anti-Missile Pod | 15,000 | 16 | 36 | 2x2 | 3 | 10 | 20,13 |
| 4 | Solar Panel | 500 | 5 | 8 | 1x1 | 0 | 0 | - |
| 5 | Radiation Filter | 8,000 | 24 | 30 | 2x2 | 3 | 10 | - |
| 6 | Solar Generator | 1,500 | 10 | 10 | 2x2 | 0 | 0 | - |
| 7 | Weapons Factory | 4,400 | 24 | 32 | 4x4 | 2 | 0 | - |
| 8 | Mine | 4,000 | 20 | 32 | 2x2 | 1 | 0 | - |
| 9 | Satellite Silo | 5,000 | 10 | 24 | 2x2 | 1 | 0 | - |
| 10 | Screen Generator | 20,000 | 36 | 52 | 2x2 | 7 | 20 | - |
| 11 | Ore Teleporter | 45,000 | 36 | 48 | 2x2 | 1 | 0 | - |
| 12 | Gravity Nullifier | 35,000 | 24 | 52 | 2x2 | 4 | 10 | - |
| 13 | Deep Bore Mine | 5,500 | 20 | 36 | 2x2 | 2 | 0 | - |
| 14 | Missile Silo | 4,300 | 15 | 32 | 2x2 | 0 | 0 | - |
| 15 | Repair Facility | 30,000 | 20 | 36 | 2x2 | 1 | 20 | - |
| 16 | Sensor Array | 3,500 | 15 | 36 | 1x1 | 2 | 5 | - |
| 17 | Plasma Turret | 5,500 | 20 | 30 | 2x2 | 3 | 8 | 27,13 |
| 18 | Photon Turret | 7,500 | 20 | 52 | 2x2 | 4 | 8 | 29,12 |
| 19 | Air Processor | 13,000 | 24 | 48 | 2x2 | 2 | 30 | - |
| 20 | C.P.U. | 8,000 | 36 | 40 | 4x4 | 0 | 50 | - |
| 21 | Seismic Penetrator | 26,500 | 24 | 42 | 3x3 | 3 | 0 | - |
| 22 | Asteroid Engine | 45,000 | 28 | 64 | 3x3 | 5 | 10 | - |
| 23 | Powerplant | 10,000 | 34 | 40 | 3x3 | 0 | 0 | - |
| 24 | Command Centre | 8,000 | 36 | 32 | 3x3 | 3 | 5 | - |
| 25 | Ship Yard | 7,500 | 20 | 32 | 3x3 | 2 | 0 | - |
| 26 | Landing Pad | 300 | 5 | 16 | 2x2 | 0 | 0 | - |
| 27 | Laser Turret | 3,400 | 16 | 25 | 2x2 | 2 | 5 | 16,12 |
| 28 | Solar Matrix | 4,000 | 10 | 32 | 2x2 | 0 | 0 | - |
| 29 | Resiblock | 3,000 | 10 | 48 | 2x2 | 0 | 20 | - |
| 30 | Storage Tower | 3,000 | 32 | 40 | 2x2 | 2 | 0 | - |
| 31 | P. Solar Matrix | 7,200 | 20 | 32 | 2x2 | 0 | 0 | 57,6 |
| 32 | Refuelling Depot | 8,500 | 40 | 30 | 2x2 | 0 | 5 | - |
| 33 | P. Storage Tower | 7,500 | 32 | 48 | 2x2 | 3 | 0 | 52,5 |
| 34 | Medical Centre | 5,000 | 15 | 30 | 3x3 | 1 | 30 | - |
| 35 | Environment Control | 3,200 | 34 | 20 | 2x2 | 0 | 40 | - |
| 36 | Pleasure Dome | 5,000 | 10 | 32 | 3x3 | 1 | 40 | - |
| 37 | Hydroponics Plant | 7,000 | 24 | 16 | 3x3 | 2 | 30 | - |
| 38 | Hydration Plant | 5,000 | 20 | 20 | 2x2 | 1 | 30 | - |
| 39 | Security Centre | 4,500 | 15 | 24 | 2x2 | 2 | -20 | - |

Notes on the columns:

- **MW used**: positive = power consumed by one building, drawn from the
  colony budget (C@0x2494 multiplies it by the building count). Generators and
  the CPU have 0 here; their output is a code constant (next table).
- **Morale delta**: subtracted from the colony morale/unrest accumulator
  (colony field +0x11A, fed to `colony_morale_tick` C@0x3034) once when the
  building is placed, and added back when it is removed (C@0x1A2C7 /
  C@0x1A683). Positive entries reduce the accumulator. Whether the
  accumulator reads as morale or as unrest, and why Living Quarters (text:
  "gives no morale") carries +10 and the Security Centre -20, is **I** /
  unresolved.
- **Muzzle offset**: non-zero only for the six armed buildings (Anti-Missile
  Pod, Plasma / Photon / Laser Turret, Protected Solar Matrix, Protected
  Storage Tower). The draw code scales each byte by about 2.44 and rotates it
  by the turret angle to place the shot origin (C@0x512C4..0x51350); the
  structure-completion code gives exactly these types a random initial turret
  angle (C@0x1C2F). **I** for the "muzzle" reading.
- Footprint is in colony surface-grid cells (`colony-surface-grid.md`).

### 1.3 Terran buildings: production, capacities, staffing, prerequisites

MW generated, capacities and staffing are **constants in code** (C@0x2494
power, C@0x1A514 ore storage, C@0x1E04 housing, C@0x1FD4..0x2224
air/food/water, C@0x27E4 staffing); the blueprint column is the Sci-Tek
catalogue (section 5) cross-checked against the starting build menu list
S@0x8F880; the notes column is game text (**T**).

| id | Building | MW generated | Capacity / output | Staff needed | Blueprint (Sci-Tek id, name, price) | Notes (text claims) |
|---|---|---|---|---|---|---|
| 0 | Living Quarters | - | houses 50 | - | none (starting menu) | cheap; weak vs attack |
| 1 | Power Store | - | stores 200 MW (400 with Hi-Energy Power Stores) | - | none (starting menu) |  |
| 2 | Storage Facility | - | stores 300 ore | - | none (starting menu) |  |
| 3 | Anti-Missile Pod | - | - | - | 2, Anti-Missile Pod, 250,000 | accuracy improves with more pods per asteroid |
| 4 | Solar Panel | 2 (x2 with Power Amplifier) | - | - | none (starting menu) |  |
| 5 | Radiation Filter | - | - | - | none (starting menu) |  |
| 6 | Solar Generator | 8 (x2) | - | - | none (starting menu) |  |
| 7 | Weapons Factory | - | - | - | none (starting menu) | needed for engines, warheads, hardpoints; laser turrets inoperative without one |
| 8 | Mine | - | - | 8 | none (starting menu) | ores Selenium, Asteros, Barium, Crystalite |
| 9 | Satellite Silo | - | - | - | none (starting menu) | builds and launches spy satellites |
| 10 | Screen Generator | - | - | - | 23, Screen Generator, 125,000 | protects neighbouring buildings |
| 11 | Ore Teleporter | - | - | - | 17, Ore Teleporter, 150,000 | needed on both ends |
| 12 | Gravity Nullifier | - | - | - | 10, Gravity Nullifier, 70,000 | must be off to run Asteroid Engines; collapses without power |
| 13 | Deep Bore Mine | - | - | 8 | none (starting menu) | ores Quazinc, Bytanium, Korellium, Dragonium |
| 14 | Missile Silo | - | 10 of each missile type (text) | 8 | none (starting menu) |  |
| 15 | Repair Facility | - | - | - | 22, Repair Facility, 150,000 | repairs buildings and hangared craft |
| 16 | Sensor Array | - | - | - | none (starting menu) | without one the asteroid has a very small sensor range |
| 17 | Plasma Turret | - | - | - | 19, Plasma Turret, 40,000 |  |
| 18 | Photon Turret | - | - | - | 18, Photon Turret, 100,000 |  |
| 19 | Air Processor | - | air for 400 | - | none (starting menu) |  |
| 20 | C.P.U. | 8 | houses 100; stores 50 MW; base output air 300 / food 250 / water 250; starts with 50 people | - | placed by Transporter | only buildable on an uninhabited asteroid via Transporter; outputs fall 1/day |
| 21 | Seismic Penetrator | - | - | 8 | 24, Seismic Penetrator, 120,000 | only mine for Traxium and Nexos |
| 22 | Asteroid Engine | - | - | - | 4, Asteroid Engines, 190,000 | speed falls to 0 without power |
| 23 | Powerplant | 32 with Asteros, else 8 | - | - | 21, Powerplant, 40,000 |  |
| 24 | Command Centre | - | - | 8 | none (starting menu) | needed to command fleets; builds the Space Dock |
| 25 | Ship Yard | - | - | 8 | none (starting menu) | builds Assault Fighter, Combat Eagle, Scoutship; needs Weapons Factory |
| 26 | Landing Pad | - | - | - | none (starting menu) | access to hangars |
| 27 | Laser Turret | - | - | - | none (starting menu) |  |
| 28 | Solar Matrix | 12 (x2) | - | - | 27, Solar Matrix, 50,000 |  |
| 29 | Resiblock | - | houses 150 | - | none (starting menu) |  |
| 30 | Storage Tower | - | stores 600 ore | - | none (starting menu) |  |
| 31 | P. Solar Matrix | 12 (x2) | - | - | with Solar Matrix (inferred) | protected: built-in laser turret |
| 32 | Refuelling Depot | - | - | - | none (starting menu) | ships/Transporters lose life and range without one |
| 33 | P. Storage Tower | - | stores 600 ore | - | none (starting menu) | built-in laser turret |
| 34 | Medical Centre | - | care for 100 (text) | - | none (starting menu) |  |
| 35 | Environment Control | - | surplus store (code: air 3000, food 1000, water 1000; text: 5000/600/600) | - | none (starting menu) |  |
| 36 | Pleasure Dome | - | 300 personnel (text) | - | none (starting menu) |  |
| 37 | Hydroponics Plant | - | food for 300 | - | none (starting menu) |  |
| 38 | Hydration Plant | - | water for 400 | - | none (starting menu) |  |
| 39 | Security Centre | - | - | - | none (starting menu) | handles troublemakers; not replaced by Resiblock |

Rules behind the numbers (all **C** unless marked):

- **Power supply per colony** = 2 x Solar Panels + 8 x Solar Generators +
  12 x Solar Matrices + 12 x Protected Solar Matrices (the whole solar
  subtotal doubles with the Power Amplifier blueprint, Sci-Tek id 20) + 8 per
  CPU + the Powerplant term. Powerplants give **32 MW each while the asteroid
  still holds Asteros ore, 8 MW each when it does not**; on every 4th pass
  (`tick & 3 == 3`) the asteroid's Asteros stock falls by the Powerplant count
  (text: one unit per 4 days; **I** for the unit). Surplus power carries over
  between passes, capped at 200 per Power Store (400 with the Hi-Energy
  Power Stores blueprint, id 11) plus 50 per CPU.
- **Text vs code**: the Solar Matrix tooltip says 12 MW / 24 MW and the code
  agrees; the long description says 8 MW, and the Protected Solar Matrix text
  says 8 MW while the code gives it 12. Treat the code as authoritative.
- **Demand**: sum of (count x MW used). Special cases: the Gravity Nullifier
  counts only while it is switched on, and an Asteroid Engine counts its
  current power setting instead of its table value.
- **Brown-out order**: demand is taken in the priority order of section 1.4;
  the first building type whose cumulative demand exceeds supply plus store
  sets the colony's shortfall position. Each producer shuts down when the
  shortfall position reaches its own place in the list: Air Processors work
  while the position is below 24, Hydration below 23, Hydroponics below 22
  (C@0x1FD4 / 0x2224 / 0x20E4); a "power critical" warning is raised at 16
  and above (C@0x2494).
- **Housing**: Living Quarters 50, Resiblock 150, CPU 100 (summed by
  C@0x1E04, shown as the colony's population maximum; **I** for the label).
- **Life support**: each Air Processor adds 400 air, each Hydroponics Plant
  300 food, each Hydration Plant 400 water on top of the CPU base output
  (300 / 250 / 250). Every person uses 1 of each per pass; a deficit removes
  population and raises unrest (C@0x1FD4..0x2224).
- **Ore storage**: Storage Facility 300, Storage Tower 600, Protected
  Storage Tower 600 (C@0x1A514; text agrees).
- **Staffing**: each Mine, Deep Bore Mine, Seismic Penetrator, Ship Yard,
  Missile Silo and Command Centre needs **8 people**; the colony population is
  consumed in the order Mines -> Deep Bore + Seismic -> Ship Yards -> Missile
  Silos -> Command Centres, and a category with too few people is flagged
  "undermanned" (C@0x27E4).
- **Morale terms outside the table**: every Pleasure Dome lowers the morale
  accumulator by a further 2 per pass; every Security Centre lowers the
  unrest value by 1 per pass (C@0x3034).
- **Starting build menu**: the 27 ids in S@0x8F880 are the buildings
  available without a blueprint. The 11 blueprint buildings (Anti-Missile
  Pod, Screen Generator, Ore Teleporter, Gravity Nullifier, Repair Facility,
  Plasma Turret, Photon Turret, Seismic Penetrator, Asteroid Engine,
  Powerplant, Solar Matrix) are exactly the ids missing from it, apart from
  the CPU (placed by a Transporter) and the Protected Solar Matrix.

### 1.4 Power priority order

S@0x8F38B, first = last to lose power (**I** for the "first/last" reading; the
loop semantics above are C):

20 C.P.U., 23 Powerplant, 0 Living Quarters, 29 Resiblock, 1 Power Store, 2 Storage Facility, 4 Solar Panel, 6 Solar Generator, 28 Solar Matrix, 31 P. Solar Matrix, 30 Storage Tower, 35 Environment Control, 36 Pleasure Dome, 26 Landing Pad, 32 Refuelling Depot, 14 Missile Silo, 19 Air Processor, 38 Hydration Plant, 37 Hydroponics Plant, 24 Command Centre, 10 Screen Generator, 5 Radiation Filter, 15 Repair Facility, 33 P. Storage Tower, 34 Medical Centre, 18 Photon Turret, 17 Plasma Turret, 27 Laser Turret, 16 Sensor Array, 25 Ship Yard, 7 Weapons Factory, 8 Mine, 13 Deep Bore Mine, 39 Security Centre, 21 Seismic Penetrator, 3 Anti-Missile Pod, 9 Satellite Silo, 12 Gravity Nullifier, 11 Ore Teleporter, 22 Asteroid Engine

### 1.5 Alien buildings

Same record formats as 1.2, for ids 40-176. Differences:

- **Cost**: the u16 at +2 of an alien record holds a small code (0-8), not a
  price; it groups the buildings by function (0 power, 1 mining/storage,
  2 life support, 3 production, 4 sensors, 5 command, 6 launch/satellite/
  missile, 7 turrets, 8 screens), so only armour and build days are
  gameplay numbers here. **I**
- **MW (raw)**: the signed byte at +4 of the class record. For ids 0-39 a
  positive value is consumption (C@0x2494). The alien records use the opposite
  sign for generators: the CPU equivalents show +8..+22 and the power
  buildings +26..+66, while ordinary consumers are negative. The Terran
  power loop never reads ids >= 40, so this sign convention is **I**.
- Armour and build days are plain values (S@0x8FFD4).
- Alien structures were not seen being placed by the player; the AI colonies
  create them (the structure-place code accepts any id).

| id | Building | Race | Terran role | Armour | Build days | AI cat. | Footprint | MW (raw) | Muzzle |
|---|---|---|---|---|---|---|---|---|---|
| 40 | Central Unit | Rigellian | C.P.U. | 30 | 36 | 5 | 3x3 | 8 | - |
| 41 | Filtration Plant | Rigellian | Hydration Plant | 20 | 20 | 2 | 2x2 | -1 | - |
| 42 | Nourishment Bank | Rigellian | Hydroponics Plant | 10 | 20 | 2 | 2x2 | -1 | - |
| 43 | Community | Rigellian | Living Quarters | 20 | 48 | 2 | 2x2 | 0 | - |
| 44 | Health Unit | Rigellian | Medical Centre | 30 | 36 | 2 | 2x2 | -1 | - |
| 45 | Strategic Bunker | Rigellian | Command Centre | 45 | 34 | 5 | 3x3 | -3 | - |
| 46 | Science Labs | Rigellian | (own) | 50 | 58 | 5 | 3x3 | -1 | - |
| 47 | Databanks | Rigellian | (own) | 50 | 44 | 5 | 2x2 | -1 | - |
| 48 | Construction Unit | Rigellian | Ship Yard | 30 | 30 | 3 | 4x4 | -2 | - |
| 49 | Ground Deck | Rigellian | Landing Pad | 20 | 18 | 6 | 3x3 | 0 | - |
| 50 | Probe Launch | Rigellian | Satellite Silo | 30 | 24 | 6 | 2x2 | -1 | - |
| 51 | Deep Space Probes | Rigellian | Sensor Array | 30 | 36 | 4 | 2x2 | -1 | - |
| 52 | Gravitic Converter | Rigellian | Asteroid Engine | 10 | 46 | 4 | 2x2 | -4 | - |
| 53 | Energy Gatherer | Rigellian | Solar Matrix | 30 | 46 | 0 | 2x2 | 32 | - |
| 54 | Energy Globe | Rigellian | Power Store | 30 | 52 | 0 | 2x2 | 0 | - |
| 55 | Shield Generator | Rigellian | Screen Generator | 45 | 46 | 8 | 2x2 | -6 | - |
| 56 | Arms Unit | Rigellian | Weapons Factory | 40 | 30 | 3 | 3x3 | -3 | - |
| 57 | Missile Launcher | Rigellian | Missile Silo | 25 | 30 | 6 | 3x3 | 0 | - |
| 58 | Thermal Lance | Rigellian | Plasma Turret | 25 | 28 | 7 | 3x3 | -3 | 27,15 |
| 59 | Extractor | Rigellian | Mine | 35 | 42 | 1 | 2x2 | -2 | - |
| 60 | Storage racks | Rigellian | Storage Tower | 40 | 48 | 1 | 3x3 | -2 | - |
| 61 | Ex-Fang | Rigellian | (own) | 45 | 48 | 7 | 4x4 | -4 | 31,20 |
| 62 | Ultrathermal Lance | Rigellian | Photon Turret | 45 | 57 | 7 | 3x3 | -3 | 30,16 |
| 63 | First Step | Braccatian | C.P.U. | 45 | 45 | 5 | 3x3 | 10 | - |
| 64 | Clan Heart | Braccatian | Command Centre | 55 | 73 | 5 | 3x3 | -2 | - |
| 65 | Radiation Shield | Braccatian | Radiation Filter | 16 | 30 | 2 | 3x3 | -1 | - |
| 66 | Source | Braccatian | Hydroponics Plant | 45 | 40 | 2 | 2x2 | -2 | - |
| 67 | Aesir's Hall | Braccatian | Air Processor | 30 | 50 | 2 | 2x2 | -1 | - |
| 68 | Longhouse | Braccatian | Living Quarters | 25 | 35 | 2 | 3x3 | 0 | - |
| 69 | Sports Hall | Braccatian | (own) | 25 | 58 | 5 | 3x3 | 0 | - |
| 70 | Field Hospital | Braccatian | Medical Centre | 15 | 26 | 2 | 3x3 | -1 | - |
| 71 | Glasshouse | Braccatian | Security Centre | 15 | 22 | 5 | 2x2 | -2 | - |
| 72 | TechMech | Braccatian | Ship Yard | 40 | 45 | 3 | 3x3 | -3 | - |
| 73 | Launch Site | Braccatian | Landing Pad | 20 | 12 | 6 | 3x3 | 0 | - |
| 74 | Eyes-in-the-Sky | Braccatian | Satellite Silo | 25 | 24 | 6 | 2x2 | 0 | - |
| 75 | Eyes-and-Ears | Braccatian | Sensor Array | 25 | 35 | 4 | 2x2 | -1 | - |
| 76 | Anchor | Braccatian | Asteroid Engine | 30 | 65 | 4 | 2x2 | -5 | - |
| 77 | Heart-of-the-Sun | Braccatian | Solar Matrix | 35 | 50 | 0 | 2x2 | 40 | - |
| 78 | Aegis | Braccatian | Screen Generator | 35 | 50 | 8 | 2x2 | -5 | - |
| 79 | Forge | Braccatian | Weapons Factory | 60 | 57 | 3 | 3x3 | -3 | - |
| 80 | Anti-Battery | Braccatian | Anti-Missile Pod | 35 | 30 | 7 | 2x2 | -2 | 32,14 |
| 81 | Battery | Braccatian | Missile Silo | 35 | 30 | 6 | 3x3 | 0 | - |
| 82 | Turret | Braccatian | Photon Turret | 30 | 42 | 7 | 2x2 | -3 | 37,20 |
| 83 | Subterranean Extractor | Braccatian | Mine | 30 | 48 | 1 | 2x2 | -2 | - |
| 84 | Pithoi | Braccatian | Storage Tower | 30 | 56 | 1 | 2x2 | -1 | - |
| 85 | Fire Power | Braccatian | Plasma Turret | 30 | 32 | 7 | 2x2 | -4 | 40,24 |
| 86 | Base Crystal | Mikotaj | C.P.U. | 50 | 50 | 5 | 3x3 | 10 | - |
| 87 | Stability | Mikotaj | Command Centre | 40 | 78 | 5 | 3x3 | -1 | - |
| 88 | Purity | Mikotaj | Radiation Filter | 35 | 52 | 2 | 2x2 | -1 | - |
| 89 | Fulfilment | Mikotaj | Hydroponics Plant | 30 | 50 | 2 | 2x2 | -1 | - |
| 90 | Internal | Mikotaj | Living Quarters | 12 | 56 | 2 | 3x3 | -1 | - |
| 91 | Dream | Mikotaj | (own) | 40 | 38 | 2 | 3x3 | 0 | - |
| 92 | Resonance | Mikotaj | (own) | 50 | 66 | 0 | 3x3 | -5 | - |
| 93 | Fa-lanth | Mikotaj | Screen Generator | 45 | 50 | 8 | 2x2 | -6 | - |
| 94 | Mask | Mikotaj | (own) | 30 | 80 | 3 | 2x2 | -2 | - |
| 95 | Structures Matrix | Mikotaj | Ship Yard | 25 | 35 | 3 | 3x3 | -2 | - |
| 96 | Volition | Mikotaj | Landing Pad | 10 | 18 | 6 | 2x2 | 0 | - |
| 97 | Visibility | Mikotaj | Satellite Silo | 20 | 24 | 6 | 2x2 | -1 | - |
| 98 | Perception | Mikotaj | Sensor Array | 20 | 36 | 4 | 2x2 | -2 | - |
| 99 | Capacitors | Mikotaj | Solar Matrix | 35 | 40 | 0 | 2x2 | 38 | - |
| 100 | Lanth | Mikotaj | (own) | 50 | 55 | 4 | 2x2 | -3 | - |
| 101 | Sharir | Mikotaj | Weapons Factory | 20 | 34 | 3 | 3x3 | -3 | - |
| 102 | Shrekn | Mikotaj | Missile Silo | 10 | 32 | 6 | 2x2 | 0 | - |
| 103 | Ruth-feror | Mikotaj | Mine | 15 | 48 | 1 | 3x3 | -2 | - |
| 104 | Ruth-fett | Mikotaj | Storage Tower | 10 | 40 | 1 | 2x2 | -2 | - |
| 105 | Merl | Mikotaj | Plasma Turret | 15 | 35 | 7 | 2x2 | -3 | 29,0 |
| 106 | Na-Shrekn | Mikotaj | Photon Turret | 20 | 57 | 7 | 2x2 | -3 | 30,0 |
| 107 | SoftCore | Mikotaj | C.P.U. | 25 | 40 | 5 | 4x4 | 12 | - |
| 108 | Environmental Stabiliser | Artemian | Environment Control | 50 | 26 | 2 | 3x3 | -1 | - |
| 109 | Filtration Tanks | Artemian | Hydroponics Plant | 50 | 30 | 2 | 3x3 | -2 | - |
| 110 | Canisters | Artemian | Living Quarters | 20 | 46 | 2 | 2x2 | 0 | - |
| 111 | Nurseries | Artemian | (own) | 60 | 30 | 5 | 2x2 | 0 | - |
| 112 | Healing Quarters | Artemian | Medical Centre | 15 | 26 | 2 | 2x2 | -1 | - |
| 113 | House of the Axe | Artemian | (own) | 35 | 48 | 5 | 3x3 | -1 | - |
| 114 | Naval Dockyard | Artemian | Ship Yard | 45 | 56 | 3 | 3x3 | -3 | - |
| 115 | Launch Pads | Artemian | Landing Pad | 20 | 18 | 6 | 2x2 | -1 | - |
| 116 | Deep Probes | Artemian | Sensor Array | 25 | 34 | 4 | 2x2 | -1 | - |
| 117 | Gravitic Converter | Artemian | Asteroid Engine | 20 | 50 | 4 | 3x3 | -6 | - |
| 118 | Shielded Solars | Artemian | Solar Matrix | 35 | 46 | 0 | 2x2 | 26 | - |
| 119 | Shell | Artemian | (own) | 40 | 44 | 4 | 2x2 | -3 | - |
| 120 | Arms Forge | Artemian | Weapons Factory | 50 | 36 | 3 | 3x3 | -4 | - |
| 121 | Star Bars | Artemian | Anti-Missile Pod | 23 | 34 | 7 | 2x2 | -2 | 27,26 |
| 122 | Missile Launcher | Artemian | Missile Silo | 35 | 30 | 6 | 2x2 | 0 | - |
| 123 | Auto-deterrent | Artemian | Plasma Turret | 40 | 28 | 7 | 2x2 | -2 | 27,22 |
| 124 | Super-deterrent | Artemian | Photon Turret | 40 | 48 | 7 | 3x3 | -1 | 28,32 |
| 125 | Force Fields | Artemian | Screen Generator | 30 | 30 | 8 | 2x2 | -4 | - |
| 126 | Advanced Ore Extractor | Artemian | Deep Bore Mine | 30 | 34 | 1 | 3x3 | -1 | - |
| 127 | Rare Ore Extractor | Artemian | Seismic Penetrator | 35 | 40 | 1 | 3x3 | -2 | - |
| 128 | Ore Depot | Artemian | Storage Tower | 25 | 24 | 1 | 2x2 | -1 | - |
| 129 | Refining Forge | Artemian | (own) | 35 | 38 | 4 | 3x3 | -1 | - |
| 130 | Base Block | Maunid | C.P.U. | 50 | 35 | 5 | 3x3 | 22 | - |
| 131 | Shielding Block | Maunid | Radiation Filter | 20 | 30 | 2 | 3x3 | -1 | - |
| 132 | Nutrition Block | Maunid | Hydroponics Plant | 20 | 26 | 2 | 3x3 | -1 | - |
| 133 | Off-duty Block | Maunid | Living Quarters | 20 | 24 | 2 | 2x2 | 0 | - |
| 134 | Health Block | Maunid | Medical Centre | 10 | 16 | 2 | 2x2 | 0 | - |
| 135 | The Cube | Maunid | (own) | 30 | 30 | 5 | 3x3 | 0 | - |
| 136 | Elite Block | Maunid | Sensor Array | 60 | 56 | 5 | 3x3 | -4 | - |
| 137 | Construction Area | Maunid | Ship Yard | 50 | 32 | 3 | 4x4 | -3 | - |
| 138 | Launch Area | Maunid | Landing Pad | 40 | 18 | 6 | 2x2 | 0 | - |
| 139 | Satellite Pad | Maunid | Satellite Silo | 45 | 24 | 6 | 3x3 | -1 | - |
| 140 | Fast Breeder Reactor | Maunid | Solar Matrix | 35 | 52 | 0 | 2x2 | 50 | - |
| 141 | Arms Block | Maunid | Weapons Factory | 50 | 36 | 3 | 4x4 | -5 | - |
| 142 | Defence Pods | Maunid | Anti-Missile Pod | 40 | 34 | 7 | 2x2 | -3 | 32,26 |
| 143 | Attack Pods | Maunid | Missile Silo | 40 | 34 | 6 | 2x2 | -1 | - |
| 144 | Pulse Tower | Maunid | Plasma Turret | 40 | 32 | 7 | 2x2 | -4 | 26,18 |
| 145 | Screening Pods | Maunid | Screen Generator | 30 | 34 | 8 | 2x2 | -8 | - |
| 146 | Advanced Extraction Unit | Maunid | Deep Bore Mine | 30 | 38 | 1 | 3x3 | -2 | - |
| 147 | Superior Extraction Unit | Maunid | Seismic Penetrator | 40 | 44 | 1 | 3x3 | -3 | - |
| 148 | Ores Block | Maunid | Storage Tower | 50 | 32 | 1 | 2x2 | -2 | - |
| 149 | Motion Units | Maunid | Asteroid Engine | 60 | 66 | 4 | 2x2 | -5 | - |
| 150 | Laser Boost | Maunid | Photon Turret | 45 | 28 | 7 | 2x2 | -4 | 32,26 |
| 151 | Footprint | Achaean | C.P.U. | 38 | 50 | 5 | 3x3 | 2 | - |
| 152 | Anti-Rad Screen | Achaean | Radiation Filter | 15 | 32 | 2 | 2x2 | -1 | - |
| 153 | Environmental Control | Achaean | Environment Control | 15 | 36 | 2 | 2x2 | -1 | - |
| 154 | Filtration Vats | Achaean | Hydration Plant | 30 | 38 | 2 | 2x2 | -1 | - |
| 155 | Nutrient Vats | Achaean | Hydroponics Plant | 30 | 40 | 2 | 2x2 | -1 | - |
| 156 | Habitat | Achaean | Living Quarters | 25 | 56 | 2 | 2x2 | 0 | - |
| 157 | Pharmacopeion | Achaean | Medical Centre | 15 | 30 | 2 | 3x3 | -1 | - |
| 158 | Gathering Ground | Achaean | (own) | 45 | 68 | 5 | 3x3 | 0 | - |
| 159 | Market | Achaean | (own) | 45 | 76 | 5 | 3x3 | 0 | - |
| 160 | Communications Central | Achaean | Command Centre | 50 | 36 | 5 | 3x3 | -2 | - |
| 161 | Shipyard | Achaean | Ship Yard | 30 | 45 | 3 | 3x3 | -4 | - |
| 162 | Landing Pad | Achaean | Landing Pad | 10 | 18 | 6 | 2x2 | 0 | - |
| 163 | Missile Launcher | Achaean | Missile Silo | 40 | 34 | 6 | 2x2 | 0 | - |
| 164 | Data Gatherer | Achaean | Satellite Silo | 15 | 28 | 6 | 3x3 | -1 | - |
| 165 | Listening Device | Achaean | Sensor Array | 20 | 40 | 4 | 2x2 | -2 | - |
| 166 | Manoeuvring Device | Achaean | Asteroid Engine | 35 | 68 | 4 | 2x2 | -6 | - |
| 167 | Destination Beam | Achaean | (own) | 50 | 100 | 4 | 2x2 | -3 | - |
| 168 | Reactor Cores | Achaean | Solar Matrix | 25 | 40 | 0 | 2x2 | 66 | - |
| 169 | Asteroid Shield | Achaean | Screen Generator | 26 | 46 | 8 | 2x2 | -6 | - |
| 170 | Defence Battery | Achaean | Anti-Missile Pod | 30 | 36 | 7 | 2x2 | -2 | 38,12 |
| 171 | Commonbore | Achaean | Mine | 16 | 44 | 1 | 3x3 | -1 | - |
| 172 | Deepbore | Achaean | Seismic Penetrator | 25 | 42 | 1 | 3x3 | -3 | - |
| 173 | Ore Yard | Achaean | Storage Tower | 35 | 44 | 1 | 2x2 | -1 | - |
| 174 | Goods Yard | Achaean | (own) | 45 | 40 | 5 | 2x2 | 0 | - |
| 175 | Stun Tower | Achaean | Laser Turret | 18 | 26 | 7 | 2x2 | -2 | 32,16 |
| 176 | Power Tower | Achaean | Photon Turret | 20 | 50 | 7 | 2x2 | -3 | 40,28 |

## 2. Craft (Ship Yards)

### 2.1 The ten Terran craft

One 20-byte record per craft, S@0x90B60 (ids = craft text index - 1462). The
Ship Yards panel code (C@0x3B6C4) reads exactly these fields, which fixes
their meaning: price, armour and ore pairs are the UI "Cost", "Armour" and
"Ore needed"; build time is "Build time"; hardpoints is "Hardpoints"; speed is
the FN number.

| record offset | field | provenance |
|---|---|---|
| +0 u16 | range (initial value of the craft's range field, 0 for the Space Dock; feeds the target-search radius, C@0x1DA94) | I |
| +2 u8 | base armour (shields add the item bonus of section 3) | C@0x3B6C4, C@0x35AD4 |
| +3 u8 | speed in FN (loaded into the craft after construction; restored by a Refuelling Depot, C@0x1C184) | C@0x1C184 |
| +4 u8 | hardpoint count | C@0x19354 |
| +5 u8 | build time in days (construction countdown); the UI shows it minus 25% (T - floor(T/4)) once Construction Droids (Sci-Tek id 7) are owned | C@0x3B6C4 |
| +6 / +7 | ore 1: type (0 Selenium .. 9 Nexos), amount shown in the panel | S, checked against the ore text for all ten craft |
| +8 / +0xC | ore 2: type, amount | S, same check |
| +0xD u8 | class id (equals the craft id for Terran craft; alien craft point at their Terran counterpart) | S |
| +0xE u16 | alternate days (only read by the AI spawn roll, C@0x4FED4) | I |
| +0x10 u32 | price in Cr | C@0x3B6C4 |

| type | Craft | Price (Cr) | Build time (days) | Armour | Speed (FN) | Hardpoints | Range | Ore 1 | Ore 2 | Alt days |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | Assault Fighter | 6,000 | 20 | 20 | 4 | 1 | 160 | 2 Selenium | 2 Crystalite | 25 |
| 1 | Combat Eagle | 12,000 | 30 | 20 | 4 | 2 | 160 | 4 Selenium | 4 Crystalite | 30 |
| 2 | Scoutship | 3,000 | 20 | 5 | 3 | 1 | 192 | 4 Selenium | 2 Crystalite | 20 |
| 3 | Destructor | 15,000 | 48 | 40 | 2 | 3 | 160 | 8 Selenium | 6 Crystalite | 50 |
| 4 | Terminator | 34,000 | 60 | 50 | 2 | 4 | 160 | 8 Selenium | 2 Dragonium | 50 |
| 5 | Transporter | 24,000 | 100 | 40 | 2 | 2 | 192 | 6 Selenium | 1 Dragonium | 30 |
| 6 | Fleet Battleship | 60,000 | 80 | 70 | 2 | 6 | 160 | 8 Selenium | 6 Dragonium | 60 |
| 7 | Space Dock | 150,000 | 110 | 120 | 0 | 4 | 0 | 10 Bytanium | 15 Dragonium | 70 |
| 8 | Command Cruiser | 300,000 | 120 | 250 | 2 | 6 | 320 | 10 Barium | 18 Korellium | 70 |
| 9 | Spy Satellite | 10,000 | 16 | 1 | 4 | 0 | 320 | 2 Barium | - | 0 |

Derived rules:

- **Ship cost** shown in the panel = hull price + the prices of the fitted
  hardpoint items (section 3); **armour** = base armour + the armour bonus of
  fitted shields (C@0x3B6C4).
- **Speed check**: Terminator 2 and Fleet Battleship 2 agree with the game
  text ("top speed of 2 FN" for both). Hardpoint check: Terminator 4,
  Fleet Battleship 6, Command Cruiser 6 agree with the text.
- **Ore check**: every craft's two ore types match the game's ore-use text
  (small craft Selenium + Crystalite; Destructor Selenium + Crystalite;
  Terminator, Transporter, Fleet Battleship Selenium + Dragonium; Space Dock
  Bytanium + Dragonium; Command Cruiser Barium + Korellium; Spy Satellite
  Barium). Whether the amounts are consumed per craft in full or only
  gate the build is **I**.
- **Build capacity**: 3 craft at once, 6 with Construction Droids, build
  speed +25% (T, consistent with the -25% in the panel code).
- **Blueprints**: Terminator (id 30), Fleet Battleship (9) and Command
  Cruiser (35) are Sci-Tek items; Transporter and Destructor are provided by
  TetraCorp; the Space Dock is built from the Command Centre, one per asteroid
  (T). Assault Fighter, Combat Eagle and Scoutship need no blueprint.

### 2.2 Alien craft

The same table continues with 31 more records (ids 10-40, text index
1472-1502) of the same layout, price 0 (AI-built). The race groups are
inferred from the order of the name lists and the name vocabulary (**I**).
Records +6/+7/+8 hold different data for these craft (255 = none, 127 etc.)
and are not decoded; the Terran counterpart in "Terran role" comes from
byte +0xD.

| type | Craft | Race group | Armour | Speed | Hardpoints | Build time | Range | Terran role | Alt days |
|---|---|---|---|---|---|---|---|---|---|
| 10 | Lazzaro Research | Rigellian | 16 | 6 | 2 | 24 | 192 | Scoutship | 20 |
| 11 | Delphini Assault | Rigellian | 35 | 4 | 3 | 40 | 160 | Destructor | 50 |
| 12 | Messier-Lukannon | Rigellian | 48 | 4 | 4 | 75 | 160 | Terminator | 50 |
| 13 | Transportation | Rigellian | 25 | 4 | 2 | 90 | 160 | Transporter | 30 |
| 14 | Observatory | Rigellian | 130 | 0 | 4 | 90 | 0 | Space Dock | 70 |
| 15 | Rattlesnake | Braccatian | 20 | 5 | 2 | 28 | 192 | Scoutship | 20 |
| 16 | WidowMaker | Braccatian | 50 | 3 | 4 | 75 | 160 | Fleet Battleship | 60 |
| 17 | HeartsBlood | Braccatian | 65 | 2 | 6 | 120 | 160 | Transporter | 30 |
| 18 | Morning Glory | Braccatian | 15 | 5 | 4 | 50 | 160 | Combat Eagle | 30 |
| 19 | SkyMech | Braccatian | 100 | 0 | 5 | 110 | 0 | Space Dock | 70 |
| 20 | Hiero | Mikotaj | 15 | 5 | 2 | 15 | 192 | Scoutship | 20 |
| 21 | Ylikt-shan | Mikotaj | 30 | 5 | 2 | 30 | 160 | Combat Eagle | 30 |
| 22 | Falari-Lourn | Mikotaj | 70 | 2 | 5 | 80 | 160 | Fleet Battleship | 60 |
| 23 | Ruth-Strivakh | Mikotaj | 40 | 2 | 2 | 112 | 160 | Transporter | 30 |
| 24 | Na-Xanth | Mikotaj | 140 | 0 | 4 | 80 | 0 | Space Dock | 70 |
| 25 | Gerla-Kans Explorer | Artemian | 32 | 5 | 2 | 30 | 192 | Scoutship | 20 |
| 26 | All-Purpose Assault | Artemian | 36 | 5 | 3 | 33 | 160 | Combat Eagle | 30 |
| 27 | Shielded Multi-Assault | Artemian | 50 | 3 | 4 | 60 | 160 | Destructor | 50 |
| 28 | Ultimate Mk II | Artemian | 80 | 2 | 6 | 115 | 160 | Fleet Battleship | 60 |
| 29 | Hardcore | Artemian | 90 | 2 | 5 | 220 | 160 | Transporter | 30 |
| 30 | Geostationary Construction | Artemian | 130 | 0 | 5 | 86 | 0 | Space Dock | 70 |
| 31 | Surveillance Craft Type 5 | Maunid | 5 | 4 | 2 | 24 | 192 | Scoutship | 20 |
| 32 | Combat Craft Type 1.5 | Maunid | 50 | 3 | 4 | 52 | 160 | Combat Eagle | 30 |
| 33 | Max Combat Craft Type 6 | Maunid | 70 | 2 | 6 | 122 | 160 | Terminator | 50 |
| 34 | Elite Command Craft | Maunid | 80 | 2 | 6 | 100 | 160 | Fleet Battleship | 60 |
| 35 | Transportation Craft Type 3 | Maunid | 35 | 2 | 4 | 122 | 160 | Transporter | 30 |
| 36 | Orbital Construction Area | Maunid | 130 | 0 | 5 | 96 | 0 | Space Dock | 70 |
| 37 | Hunter/Prospector | Achaean | 25 | 5 | 2 | 25 | 192 | Scoutship | 20 |
| 38 | Dedicated Fighter | Achaean | 50 | 3 | 4 | 70 | 160 | Terminator | 50 |
| 39 | Dedicated Ore Transporter | Achaean | 40 | 3 | 4 | 90 | 160 | Transporter | 30 |
| 40 | Orbital Shipyard | Achaean | 100 | 0 | 3 | 80 | 0 | Space Dock | 70 |

## 3. Hardpoint items

16 items, S@0x90A0C (price, u32 x 16), S@0x90A50 (armour bonus), in the
order of the text list 1514-1529. The three rating tables are read only by
the AI target-valuation code (`colony_value_sum` C@0x16DA4 and the raid
pickers) and by the Ship Yards panel; their precise meaning (attack /
defence rating) is **I**.

| item | Name | Price (Cr) | Armour bonus | Rating A | Rating B | Rating C | Blueprint |
|---|---|---|---|---|---|---|---|
| 0 | Ion Cannon | 1,000 | - | - | - | 2 | none |
| 1 | Disruptor | 6,000 | - | - | - | 6 | none |
| 2 | Napalm Orb | 4,000 | - | - | - | 4 | none |
| 3 | Chaos Bomb | 12,000 | - | - | - | 12 | none |
| 4 | Vortex Mine | 5,000 | - | - | - | 5 | none |
| 5 | Laser | 1,000 | - | - | 2 | 1 | none |
| 6 | Photon Cannon | 4,500 | - | - | 5 | 1 | none |
| 7 | Plasma Cannon | 9,000 | - | - | 9 | 1 | none |
| 8 | Static Inducer | 4,500 | - | 30 | - | - | 28, Static Inducer, 80,000 |
| 9 | Warp Generator | 9,000 | - | 50 | - | - | 33, Warp Generator, 75,000 |
| 10 | Deflector | 12,000 | - | 60 | - | - | 8, Deflector, 115,000 |
| 11 | Shield x10 | 1,500 | 10 | 10 | - | - | none |
| 12 | Shield x20 | 3,000 | 20 | 20 | - | - | none |
| 13 | Shield x30 | 5,000 | 30 | 30 | - | - | none |
| 14 | Shield x40 | 6,500 | 40 | 40 | - | - | 25, Shield x40, 15,000 |
| 15 | Shield x50 | 8,000 | 50 | 50 | - | - | 26, Shield x50, 60,000 |

Blueprint gating of the items is S@0xAA014 (item -> Sci-Tek id, -1 = free);
the five gated entries agree with the Sci-Tek catalogue list.

The ship attack and defence numbers shown by the UI come from the runtime
value table at flat 0xBEC30 (**R**).

## 4. Missiles

13 Terran missile types, 16-byte records at S@0x913B4 (ids = text index -
1354). Fields:

- price: +8 u32 (**I**: the field matches the missile Cost, ascending with
  the destructive power: Explosive 800 ... Mega 100,000);
- ore: +4 u8 type (0 Selenium .. 9 Nexos; matches the ore text for all 11
  buyable types); the production code takes one unit of that ore from the
  colony stock per missile (`building_construction_tick`, C@0xA04);
- N: +5 u8, read in TWO places (Corrected 2026-10-18; the two analyses each saw
  one): (a) the **ore quantity** in the monthly trade price, `price(87+id) = cost
  + N * ore unit price` (C@0x47B14..0x47B3F, `alien-ai-trade-victory.md` 8.1), and
  the Missiles screen shows it next to the ore name (C@0x3B31D); (b) the
  **per-colony stock cap** of the AI production tick (C@0x19ADF/0x19AE5: builds
  a missile only while the colony's stock counter `0x13f + id` is below N).
  Both reads are verified in the disassembly, so N is one byte with both
  effects; whether the cap is deliberately equal to the ore quantity is
  unknown. For the Terran table N is the ore units per missile;
- W: +0 u32, the **production-point cost** of one missile in the AI production
  tick (C@0x19AF3..0x19B16: needs colony production points `+0x1A0 >= W`, then
  subtracts W). Terran/HumanCorp records: 8 for most types, 15 for Nuclear and
  Virus, 30 for Mega; alien records use a different scale (below);
- flag: +0xC u16: 400 for Scatter and Nuclear, 1 for Virus, Mega and
  Meat-Eater, 255 for Anti-Virus, Stasis and Bug Hunter, 0 otherwise. It is
  copied into the `+0x1C` word of a visual debris / marker node (C@0x33777); no
  damage role was found. Role otherwise unresolved (**I**: a visual class);
- id: +0xE u16: the missile id used by every effect lookup (equals the record
  index for the 13 Terran records; the alien records repeat ids 0-17).
- B (weight word): table S@0x919EC, see 4.2.

| id | Missile | Price (Cr) | Ore (1 unit) | Field N (ore units / stock cap) | Field W (prod. pts) | Flag | Weight (S@0x919EC) | Blueprint |
|---|---|---|---|---|---|---|---|---|
| 0 | Explosive | 800 | Selenium | 1 | 8 | 0 | 1 | none |
| 1 | Area Explosive | 6,400 | Barium | 2 | 8 | 0 | 3 | none |
| 2 | Napalm | 5,000 | Quazinc | 1 | 8 | 0 | 5 | none |
| 3 | Hellfire | 16,000 | Quazinc | 3 | 8 | 0 | 7 | none |
| 4 | Scatter | 15,000 | Selenium | 3 | 8 | 400 | 25 | none |
| 5 | Vortex | 8,000 | Crystalite | 3 | 8 | 0 | 20 | none |
| 6 | Nuclear | 50,000 | Bytanium | 5 | 15 | 400 | 100 | 16, Nuclear Missile, 300,000 |
| 7 | Virus | 30,000 | Traxium | 1 | 15 | 1 | 100 | 32, Virus Missile, 350,000 |
| 8 | Anti-Virus | 10,000 | Barium | 4 | 8 | 255 | 0 | 3, Anti-Virus Missile, 90,000 |
| 9 | Mega | 100,000 | Nexos | 1 | 30 | 1 | 255 | 13, Mega Missile, 500,000 |
| 10 | Stasis | 40,000 | Korellium | 2 | 8 | 255 | 50 | 29, Stasis Missile, 150,000 |
| 11 | Bug Hunter | - | - | - | 0 | 255 | 150 | none |
| 12 | Meat-Eater | - | - | - | 0 | 1 | 150 | none |

The Bug Hunter and Meat-Eater APV missiles have no price or ore here: they
are black-market goods (T). Blueprint prices are in section 5; missile silo
capacity is 10 per type per silo (T; no constant 10 was looked for in the
production code, so this stays a text claim).

### 4.1 Warhead effects and numbers (GOG, S/C)

The per-missile effect machine is documented in `ship-hit-formula.md`; the
designer-facing numbers are collected here. All effects hit the **structures of
the attacked asteroid** (hit points = the Armour column of section 1.2). The
per-race bytes are indexed by the **launching race** (1 = TetraCorp, 2-8
HumanCorp, 9-14 aliens). Distances are surface-grid cells; "r2" is the squared
radius.

| id | Missile | Effect | Numbers (races 1-8) | Provenance |
|---|---|---|---|---|
| 0 | Explosive | circle sweep | 10 damage, r2 4 (2 cells) | S@0x91964 / 0x91973, C@0x20094 |
| 1 | Area Explosive | circle sweep | 10 damage, r2 9 (3 cells) | S@0x91964 / 0x91982, C@0x200D4 |
| 2 | Napalm | cone sweep + burn | 5 damage, r2 16 (4 cells), burn state 5 (5 structure passes x 1 HP) | S@0x91991, C@0x20114 |
| 3 | Hellfire | cone sweep + burn | 5 damage, r2 25 (5 cells), burn state -10 (10 passes x 1 HP, 20 % spread per pass) | S@0x919A0, C@0x20144 |
| 4 | Scatter | 25 bomblets 2-16 cells around the impact | each bomblet: circle r2 4, 10 damage | S@0x919AF, C@0x20174 / 0x202B4 |
| 5 | Vortex | random-walk storm walker | 2 HP per tick on the occupied cell; rolled walker 50-98 ticks, 4 % successor chance per tick | S@0x919CD / 0x919DC, C@0x20354 |
| 6 | Nuclear | big circle + full cone | 7 + 5 damage within r2 400 (20 cells), burn state -10 | C@0x20534 |
| 7 | Virus | infection flag | timer 350 + rng(50) | C@0x205E4 |
| 8 | Anti-Virus | cure flag | - | C@0x20684 (I) |
| 9 | Mega | destruction flag | - | C@0x206D4 (I) |
| 10 | Stasis | hold timer | 50 + rng(25) = 50-74 (units of the object-tick pass) | S@0x919BE, C@0x206F4 |
| 11 | Bug Hunter | event 4 on the target | 25 % gate to a diplomatic record | C@0x20744 |
| 12 | Meat-Eater | event 5 on the target | 25 % gate to a diplomatic record | C@0x20794 |

Alien races differ in the same bytes (table in `ship-hit-formula.md`): damage
14/10/8/11/12/6, r2 A 9/4/4/4/9/4, r2 B 16/9/9/16/16/4, cone A 25/16/9/16/25/9,
cone B 36/25/16/25/36/16, Scatter bombs 30/25/23/26/28/20, Stasis base
55/45/35/55/65/25, strike % 5/4/3/4/5/3 for races 9..14.

**Missile speed**: the same for every type, 3 world units per tick (C@0x1FE7E).
**Strike value**: not per type: the arrival probability is (chance+1)/101
with chance the distance formula of `weapons.md` (base 32 units, 64 with
Missile Guidance), applied by the flight handler. **Blast radius / damage**
are the numbers above.

### 4.2 The weight words and the alien arsenals

S@0x919EC, 18 signed words indexed by missile id:
1, 3, 5, 7, 25, 20, 100, 100, 0, 255, 50, 150, 150, 20, 50, 100, 50, 30 (ids
0-17). This is the "destructive scale" used for the report's total yield
(**I**) and the incident tally; ids 11 and 12 (Bug Hunter, Meat-Eater) are 150.

Each alien race builds from its own roster: the per-race list table S@0x9C7B0 (12
bytes per race: first record, count, end) points races 1-8 at records 0-12 and
races 9-14 (9 Rigellian, 10 Braccatia, 11 Mikotaj, 12 Artemia, 13 Mauna, 14 Achaean) at records 13-19, 20-29, 30-38, 39-50, 51-60, 61-68 of the same
16-byte missile table. Their W (production points) / N (ore units, also the AI stock cap) by missile id
(races 9, 10, 11, 12, 13, 14; `-` = not built):

| id | R9 | R10 | R11 | R12 | R13 | R14 |
|---|---|---|---|---|---|---|
| 0 Explosive | 2/18 | - | 2/18 | 2/12 | 2/35 | 2/18 |
| 1 Area Explosive | 3/12 | 3/20 | 3/14 | 3/12 | 3/25 | 3/15 |
| 2 Napalm | 5/12 | 5/15 | 5/10 | 5/12 | 5/18 | 5/8 |
| 3 Hellfire | - | 7/15 | - | 7/10 | 7/16 | - |
| 4 Scatter | 9/8 | 9/9 | 9/8 | 9/8 | 9/12 | - |
| 5 Vortex | 11/8 | 11/10 | 11/8 | 11/10 | 11/10 | 11/8 |
| 6 Nuclear | - | 25/2 | - | 25/1 | 25/2 | - |
| 7 Virus | - | 25/1 | 25/1 | 25/1 | 25/1 | 25/1 |
| 8 Anti-Virus | 25/1 | 25/2 | 25/1 | 25/1 | 25/2 | 25/2 |
| 9 Mega | - | - | - | 50/1 | - | - |
| 10 Stasis | 25/1 | 25/2 | 25/2 | 25/1 | - | 25/2 |
| 13 (special) | - | 25/1 | - | - | - | - |
| 14 (special) | - | - | 35/2 | - | - | - |
| 15 (special) | - | - | - | 35/1 | - | - |
| 16 (special) | - | - | - | - | 65/1 | - |
| 17 (special) | - | - | - | - | - | 35/2 |

The special ids 13-17 are one alien-only missile per race (races 10-14; race 9
has none): 13 = cone r2 196, 5 damage; 14 = 180-tick walker with 120 damage per
tick; 15 = circle r2 100 with 120 damage; 16 = ore-stock drain plus a bomblet
cloud; 17 = the bomblet cloud alone (cone sweeps, 5 damage). The text names (Detonator, Multi-det,
Flamejell, Maxi-det, Flare, Viral Repair, Temporal Stasis, ...) are not mapped
to these ids.

### 4.3 Defence buildings (turrets and the Anti-Missile Pod)

There is **no turret damage / range / fire-rate table**. The static data per
defence building is the building-table row (cost, armour, build days, power,
footprint, muzzle) of section 1.2:

| building | cost | armour | build days | MW | footprint | muzzle bytes | provenance |
|---|---|---|---|---|---|---|---|
| Anti-Missile Pod | 15,000 | 16 | 36 | 3 | 2x2 | 20,13 | S@0x8FFD4, S@0xBC278 |
| Laser Turret | 3,400 | 16 | 25 | 2 | 2x2 | 16,12 | same |
| Plasma Turret | 5,500 | 20 | 30 | 3 | 2x2 | 27,13 | same |
| Photon Turret | 7,500 | 20 | 52 | 4 | 2x2 | 29,12 | same |

Damage ordering (Laser < Plasma < Photon), "standard" vs "optimized" range and
the Turret Optimizer doubling are **T** only. The craft range column (160 / 192
/ 320) is the **ships'** range, not a turret range. The missile blast machine
does not model turrets.

## 5. Sci-Tek blueprints (36 purchasable items)

S@0xB7270: the brochure grid, 8-byte records `{Sci-Tek id, price}` in
display order (9 slots per section, id -1 = empty slot; six sections). The
Sci-Tek id is the alphabetical catalogue index (text 1530 + id): the
anchors Building Armour = 6, Construction Droids = 7, Hi-Energy Power Stores
= 11 and Power Amplifier = 20 are the byte offsets the game code tests in the
per-race blueprint flag array (race record + 0xC558 + id, 38 bytes per race).
Scrambler (36) and Double Speed Engines (37) have no grid slot. The Shield
x50 price of 60,000 agrees with the item text.

| Sci-Tek id | Item | Price (Cr) | Brochure section (grid slot) |
|---|---|---|---|
| 0 | Mk2 Mine | 75,000 | Mining (slot 28) |
| 1 | Mk2 Deep Bore Mine | 95,000 | Mining (slot 29) |
| 2 | Anti-Missile Pod | 250,000 | Defence (slot 0) |
| 3 | Anti-Virus Missile | 90,000 | Missiles (slot 22) |
| 4 | Asteroid Engines | 190,000 | Other (slot 46) |
| 5 | Asteroid Tracker | 40,000 | Other (slot 48) |
| 6 | Building Armour | 110,000 | Defence (slot 4) |
| 7 | Construction Droids | 80,000 | Other (slot 49) |
| 8 | Deflector | 115,000 | Ships and hardpoints (slot 12) |
| 9 | Fleet Battleship | 150,000 | Ships and hardpoints (slot 10) |
| 10 | Gravity Nullifier | 70,000 | Other (slot 45) |
| 11 | Hi-Energy Power Stores | 30,000 | Power (slot 36) |
| 12 | Improved Sensors | 44,000 | Other (slot 47) |
| 13 | Mega Missile | 500,000 | Missiles (slot 18) |
| 14 | Missile Bay Extension | 60,000 | Missiles (slot 23) |
| 15 | Missile Guidance System | 80,000 | Missiles (slot 24) |
| 16 | Nuclear Missile | 300,000 | Missiles (slot 19) |
| 17 | Ore Teleporter | 150,000 | Mining (slot 30) |
| 18 | Photon Turret | 100,000 | Defence (slot 1) |
| 19 | Plasma Turret | 40,000 | Defence (slot 2) |
| 20 | Power Amplifier | 100,000 | Power (slot 39) |
| 21 | Powerplant | 40,000 | Power (slot 37) |
| 22 | Repair Facility | 150,000 | Other (slot 50) |
| 23 | Screen Generator | 125,000 | Defence (slot 5) |
| 24 | Seismic Penetrator | 120,000 | Mining (slot 27) |
| 25 | Shield x40 | 15,000 | Ships and hardpoints (slot 14) |
| 26 | Shield x50 | 60,000 | Ships and hardpoints (slot 15) |
| 27 | Solar Matrix | 50,000 | Power (slot 38) |
| 28 | Static Inducer | 80,000 | Ships and hardpoints (slot 16) |
| 29 | Stasis Missile | 150,000 | Missiles (slot 20) |
| 30 | Terminator | 90,000 | Ships and hardpoints (slot 9) |
| 31 | Turret Optimiser | 240,000 | Defence (slot 3) |
| 32 | Virus Missile | 350,000 | Missiles (slot 21) |
| 33 | Warp Generator | 75,000 | Ships and hardpoints (slot 13) |
| 34 | Long Range Transmitter | 35,000 | Other (slot 51) |
| 35 | Command Cruiser | 250,000 | Ships and hardpoints (slot 11) |

Section names in the grid: only "Mining" (Seismic Penetrator) and "Defence"
(Anti-Missile Pod) are attested by the help text; the other section names
above are descriptive.

Blueprint effect flags the code reads (race flag array at record +0xC558):
id 6 Building Armour (+10 armour on new structures, C@0x1A31A), id 7
Construction Droids (-25% craft build time in the panel, C@0x3B6C4), id 11
Hi-Energy Power Stores (store size 400, C@0x2669), id 20 Power Amplifier
(solar x2, C@0x2503), id 2 / 4 / ... gate the menu items listed in 1.3.

## 6. Other numeric tables found nearby

### 6.1 Agent mission table

13 records at S@0x8F97C, 12 bytes: `{a u8, b u8, c u16, d u16, 0, fee u32}`;
read by `agent_daily_tick` (C@0xC0D4) and `agent_mission_price` (C@0xC6C4,
fee scaled by per-race modifier tables). The 13 records match the 13 agent
mission names of the text in order and the fees look right for them (treaty
information cheapest, fatal building sabotage dearest), so this is the
agent mission price list (**I**). Earlier notes called it a "12-record stat
table"; it is not a craft or building table.

| rec | Agent mission (inferred) | Fee (Cr) | a | b | c | d |
|---|---|---|---|---|---|---|
| 0 | SpaceDock Sabotage. | 150,000 | 25 | 50 | 140 | 50 |
| 1 | Satellite signal recon. | 60,000 | 12 | 80 | 30 | 20 |
| 2 | Treaty information. | 50,000 | 12 | 65 | 100 | 40 |
| 3 | Asteroid location. | 75,000 | 12 | 80 | 40 | 30 |
| 4 | APV delivery. | 350,000 | 25 | 40 | 200 | 100 |
| 5 | Fatal building sabotage. | 500,000 | 25 | 50 | 80 | 90 |
| 6 | Mining/Ore sabotage. | 130,000 | 20 | 55 | 50 | 50 |
| 7 | Power generation sabotage. | 110,000 | 18 | 55 | 20 | 40 |
| 8 | Missile defences sabotage. | 190,000 | 18 | 55 | 40 | 60 |
| 9 | Ship defence sabotage. | 200,000 | 20 | 55 | 50 | 50 |
| 10 | Construction facilities sabotage. | 90,000 | 17 | 55 | 50 | 60 |
| 11 | Missile sabotage. | 130,000 | 25 | 40 | 80 | 60 |
| 12 | Transporter Sabotage. | 145,000 | 20 | 55 | 140 | 50 |

### 6.2 Colony event table (not weapon slots)

Corrected 2026-10-18: this 12-record table (GOG displacement 0x9dc4, flat 0x8FDC8) is the COLONY EVENT table (the six APV viruses and six Terran colony events), not a ship weapon-slot table: every reader is colony-event code (0x13e32..0x141d3, `colony_sickness_post` 0x13e74, handler call at 0x1459a); the race masks are the APV susceptibilities (`alien-ai-trade-victory.md` 8.6); byte +8 is the cure and byte +9 the stage length in days, not a fire delay.

12 records of 12 bytes at S@0x8FDC8, `{code pointer (flat - 4), race mask u16,
two bytes, cure s8, stage length u8 (days), flag u16}`. Race mask bit n = race n.
The callbacks sit in unrecovered gap code. The "Mode" and "Fire delay" column
headers below are the old (withdrawn) reading: read them as cure and stage
length in days.

| slot | Callback (flat) | Race mask | Mode | Fire delay (ticks) | Flag |
|---|---|---|---|---|---|
| 0 | 0x138A4 | 0x1000 | 3 | 30 | 1 |
| 1 | 0x138F4 | 0x800 | -1 | 30 | 1 |
| 2 | 0x13A44 | 0x4402 | -1 | 20 | 1 |
| 3 | 0x13B34 | 0x6400 | 0 | 30 | 1 |
| 4 | 0x13804 | 0x1000 | 1 | 30 | 1 |
| 5 | 0x139A4 | 0x4402 | 1 | 20 | 1 |
| 6 | 0x13B84 | 0x2 | 4 | 40 | 0 |
| 7 | 0x13C04 | 0x2 | 1 | 40 | 0 |
| 8 | 0x13CA4 | 0x2 | 1 | 40 | 0 |
| 9 | 0x13CF4 | 0x2 | 1 | 40 | 0 |
| 10 | 0x13D44 | 0x2 | 1 | 30 | 1 |
| 11 | 0x13D74 | 0x2 | 0 | 40 | 0 |

### 6.3 Records that are not building or craft stats

- S@0x8F680 (28-byte records; the id at the end of each record is the
  supervisor portrait / CV id): the **Colony Supervisor table** (16 rows),
  read by `supervisor_workload_tick` (C@0x8354) and `supervisor_daily_tick`
  (C@0x8544); full decode in `economy-and-personnel.md` section 4.1
  (Corrected 2026-10-18: earlier "AI colony / diplomacy ticks" was wrong).
- S@0x8F5D0-0x8F670 (300/400/500 triples, 999s): the alien pact / treaty
  offer periods (`alien-ai-trade-victory.md` 6.5), not income (Corrected
  2026-10-18). The race income table is the separate array at flat 0x8F3B4
  (disp 0x93B0), indexed by atmosphere.

## 7. Runtime-only values

These are not in the static image (zero or pointer slots in the file); read
them from a memdump at the dump offset given (flat + 0x1C801C).

| value | flat | dump offset | note |
|---|---|---|---|
| default hardpoint loadout per craft class (6 item ids per class, 0x10 = empty) | 0x9B2EC | 0x263308 | filled when the Ship Yards screen opens |
| Ship Yards panel caption string pointers (ore / stat names) | 0xBF600 | 0x28761C | built from the loaded text |
| per-type name pointers (building / craft names) | 0xBF104 | 0x287120 | text pointers |
| UI value table for items (attack / defence display) | 0xBEC30 | 0x286C4C | |
| structure completion handler pointers, one per building id | 0x8F2E0 | 0x2572FC | assigned at startup |
| per-colony building counts | colony +0xC8+id | per node | live game state |
| missile arrival probability | n/a | n/a | computed: distance formula of `weapons.md` (guidance blueprint raises the 32-unit base to 64); applied by the flight handler |
| missile flight time | n/a | n/a | computed: 3 units per tick over the distance; timeout rules in `ship-hit-formula.md` |
| missile blast radius / damage | S@0x91964... | n/a | static, section 4.1 (not runtime) |
| turret damage and range per turret type | n/a | n/a | **does not exist as a table** (section 4.3); Turret Optimiser doubling is text only (T) |

## 8. Corrections to earlier notes

- `building-stat-table.md`: the table is 177 rows, not 40; byte +1 is the
  **build time in days**, and bytes +4/+5 are real fields (turret muzzle
  offsets), not "overlapping tail" bytes. Fixed in that note.
- `vehicles.md`: the craft stat table is statically readable (S@0x90B60) and
  all ten craft are mapped. Fixed in that note.
- `scitek-blueprints.md` (not edited here): section "The price tables":
  the price-pair table at 0xB72E4 was read with the pair order swapped; the
  real records are `{Sci-Tek id, price}` starting at 0xB7270, all 36 items
  are priced in the GOG build (no "ISO-only" types), the id is the catalogue
  index, and the "12-record stat table" is the agent mission list (6.1). The
  Ship Yards record decode there ("textoff", "days") should use the field
  list of section 2.1.
- `weapon-and-turret-numbers.md` (now corrected, 2026-10-18) and `docs/dataformats/gog-build-data.md`
  (not edited here): for the GOG build the displacement reads are static
  data at disp + 0x86004; the 0x8F880 id list is the starting build menu,
  and the 0x8F680 records are the Colony Supervisor table (`economy-and-personnel.md` section 4).

- Combat notes (`ship-hit-formula.md`, `weapons.md`, `weapon-and-turret-numbers.md`,
  `turrets-and-defence.md`, `weapon-config-table.md`) rewritten 2026-10-18: the
  per-race combat bytes are static (S@0x91964), the "colony fire gate" is the
  supervisor performance gate, the 0xB244-family "turret" tables are the craft
  table, the "weapon config table" is a sprite descriptor table, the 12-record
  table at 0x8FDC8 is the colony event table (not weapon slots), and field W of
  the missile table is the AI production-point cost; field N is both the ore
  quantity in the trade price and the AI stock cap (section 4).

## Open questions

- Meaning of the morale/unrest accumulator sign and of the Living Quarters
  +10 / Security Centre -20 entries.
- The class-table byte +2 of every building (values 0-22).
- Missile flag field (+0xC) role; the unit of the Stasis / Virus timers in
  game days; the AMP interception effect; the text names of the alien special
  missiles (ids 13-17) and the text names of the alien special missiles (alien race ids are now known: 9 Rigellian .. 14 Achaean).
- Hardpoint item rating tables A / B / C.
- Craft: range field +0, the two unknown bytes +6/+7 meaning for alien craft,
  alt-days +0xE.
- Whether the ISO build carries the same alien building rows (the Terran
  rows are reported byte-identical in `building-stat-table.md`).
