# The per-type building stat table (armour, build time, cost, muzzle)

Status: **confirmed**. The building stat table exists as real static data in
the GOG build (flat `0x8FFD4`; the ISO flat `0x986BC` copy is reported
byte-identical for the Terran rows) and its **177 rows cover every building of
every race** (40 Terran + 137 alien). The GOG build's runtime copy was
verified byte-identical in all four memory dumps, and the row values were
verified against 25 live structure nodes. The type byte equals the game's text
index minus 919 for all 177 ids (see "Type to building mapping"); the
consolidated designer tables are in `stat-tables-design-sheet.md`.

Corrections (2026-10-18, this revision): (1) the table has 177 rows, not 40
(rows 40-176 are the alien buildings, ending exactly at `0x903FA`); (2) byte
+1 is the **build time in days**, not an "initial state"; (3) bytes +4/+5 are
real fields (turret muzzle offsets for the six armed buildings), not the
"overlapping tail" of the preceding data; (4) the full type-to-name mapping is
settled and the "open addressing question" is resolved (flat = displacement +
0x86004). Earlier correction (2026-08-22): an early draft read the table 0x20
bytes early (at `0x8FFB4`); the table starts at `0x8FFD4`.

Source: GOG flat `build/flat/FRAGILE.EXE.gog.flat`, its disassembly
`build/flat/gog_disasm.txt`, the named export
`build/named/FRAGILE.EXE.gog.flat/decompiled.c`, the text resource, and the
runtime dumps `build/dumps/ram_*.bin` (image base 0x1C901C, code object base
0x24E000; the dumps are not present in the current workspace, the dump-side
results below are from the earlier sessions).

## The table

| build | flat offset | runtime (GOG, all 4 dumps) | rows | stride |
|---|---|---|---|---|
| GOG | 0x8FFD4 | 0x257FF0 (linear) | 177 | 6 |
| ISO | 0x986BC | materialised at 0xA6B8-family (the "tables in code" slot) | 40 (Terran) verified | 6 |

Row layout (offsets relative to the row start):

| off | size | field | evidence |
|---|---|---|---|
| +0 | u8 | base armour (HP) | structure creation stores it in node +9 (GOG 0x1A324); matches the live nodes |
| +1 | u8 | build time in days | stored in node +0xA at placement; the structure callback (GOG 0x1BF4) decrements it once per game day and completes the building at 0 |
| +2 | u16 | cost (Terran rows); a small function code 0-8 for alien rows | deducted from the owner's fund at placement (GOG 0x1A243..0x1A259) |
| +4 | u8 | turret muzzle offset a (0 for unarmed buildings) | read by the sprite code (GOG 0x5131D) and by the completion code (GOG 0x1C2F: non-zero gives a random turret angle) |
| +5 | u8 | turret muzzle offset b | GOG 0x512C4 |

The earlier stage-12 report entries "0x90000 {u16,u16} pairs" and "0x8FFC4
mixed bytes" (`gog_constants.md`) are misaligned u16 re-reads of this same
table, not separate tables.

## Values (Terran rows 0-39)

```
 id: HP  days  cost   (mz)       id: HP  days  cost    (mz)
  0:  5   32    1000             20: 36   40    8000
  1: 34   32    1500             21: 24   42   26500
  2: 24   20    1500             22: 28   64   45000
  3: 16   36   15000  (20,13)    23: 34   40   10000
  4:  5    8     500             24: 36   32    8000
  5: 24   30    8000             25: 20   32    7500
  6: 10   10    1500             26:  5   16     300
  7: 24   32    4400             27: 16   25    3400  (16,12)
  8: 20   32    4000             28: 10   32    4000
  9: 10   24    5000             29: 10   48    3000
 10: 36   52   20000             30: 32   40    3000
 11: 36   48   45000             31: 20   32    7200  (57,6)
 12: 24   52   35000             32: 40   30    8500
 13: 20   36    5500             33: 32   48    7500  (52,5)
 14: 15   32    4300             34: 15   30    5000
 15: 20   36   30000             35: 34   20    3200
 16: 15   36    3500             36: 10   32    5000
 17: 20   30    5500  (27,13)    37: 24   16    7000
 18: 20   52    7500  (29,12)    38: 20   20    5000
 19: 24   48   13000             39: 15   24    4500
```

(mz = muzzle offsets +4,+5; only the six armed buildings have them.) The
alien rows 40-176 (armour, build days, function code, muzzle) are tabulated in
`stat-tables-design-sheet.md`, section 1.5.

## Type to building mapping (confirmed)

The type byte (building id) is the index into the building-name block of the
text resource: **id = text index - 919** for all 177 buildings. The Terran
names, in id order:

| id | building | id | building | id | building | id | building |
|---|---|---|---|---|---|---|---|
| 0 | Living Quarters | 10 | Screen Generator | 20 | C.P.U. | 30 | Storage Tower |
| 1 | Power Store | 11 | Ore Teleporter | 21 | Seismic Penetrator | 31 | P. Solar Matrix |
| 2 | Storage Facility | 12 | Gravity Nullifier | 22 | Asteroid Engine | 32 | Refuelling Depot |
| 3 | Anti-Missile Pod | 13 | Deep Bore Mine | 23 | Powerplant | 33 | P. Storage Tower |
| 4 | Solar Panel | 14 | Missile Silo | 24 | Command Centre | 34 | Medical Centre |
| 5 | Radiation Filter | 15 | Repair Facility | 25 | Ship Yard | 35 | Environment Control |
| 6 | Solar Generator | 16 | Sensor Array | 26 | Landing Pad | 36 | Pleasure Dome |
| 7 | Weapons Factory | 17 | Plasma Turret | 27 | Laser Turret | 37 | Hydroponics Plant |
| 8 | Mine | 18 | Photon Turret | 28 | Solar Matrix | 38 | Hydration Plant |
| 9 | Satellite Silo | 19 | Air Processor | 29 | Resiblock | 39 | Security Centre |

Evidence, independent of the text order:

- **Effect code**: the colony code keeps a per-colony building counter at
  colony `+0xC8+id` and multiplies it by constants that match the text of
  each building: Solar Panel (id 4) x2 MW, Solar Generator (6) x8, Solar
  Matrix (28) and Protected Solar Matrix (31) x12, Powerplant (23) x32 / x8,
  CPU (20) x8 MW and 50 people at start, Air Processor (19) x400 air,
  Hydroponics (37) x300 food, Hydration (38) x400 water, Living Quarters (0)
  50 / Resiblock (29) 150 housing, Storage Facility (2) 300 / Storage Tower
  (30) and Protected Storage Tower (33) 600 ore, Pleasure Dome (36) and
  Security Centre (39) in the morale tick, Refuelling Depot (32) in the craft
  speed refresh (GOG 0x2494, 0x1A514, 0x1E04, 0x1FD4..0x2224, 0x3034,
  0x1C184).
- **Staffing**: ids 8, 13, 21, 25, 14, 24 (Mine, Deep Bore, Seismic, Ship
  Yard, Missile Silo, Command Centre) are the six buildings that each need 8
  people (GOG 0x27E4).
- **Alien equivalence**: each alien building's class record names a Terran
  role (`stat-tables-design-sheet.md` 1.1); in all 137 cases the role fits the
  building's name and description.
- **Starting menu**: the 27-id list at GOG `0x8F880` is exactly the set of
  Terran ids that are not blueprint-gated, apart from the CPU and the
  Protected Solar Matrix; the 11 missing ids are the 11 "Buildings" items of
  the Sci-Tek catalogue (`scitek-blueprints.md`).
- **Live nodes** (below): the node types 2, 4, 9, 16, 19, 26, 29, 30, 33, 34,
  35, 36, 37, 38 all carry the HP of the same-numbered row.

The earlier partial mapping (type 9 = Satellite Silo, 33 = Protected Storage
Tower) is a special case of this; the turrets (17 Plasma, 18 Photon, 27 Laser),
Anti-Missile Pod (3), Missile Silo (14), Screen Generator (10) and Solar
Matrix (28) rows that were "plausible" before are now confirmed.

## Verification against the runtime structure nodes

The runtime dumps contain real structure nodes (callback 0x1CABF0 =
relocated FUN_00001BF0; type at node +8, current HP at +9, countdown at +0xA,
grid position at +0x14/+0x15). Their {type, HP} pairs match the table EXACTLY
(undamaged):

| dump | nodes (type:HP) |
|---|---|
| ram_1cd67000.bin | 26:5, 16:15, 29:10, 37:24, 29:10, 2:24 |
| ram_1cdfd000.bin | 9:10, 34:15, 38:20, 37:24, 36:10, 4:5, 30:32, 29:10, 4:5 x4, 38:20 |
| ram_1ce2a000.bin | 19:24, 29:10 |
| ram_20459000.bin | 33:32, 26:5, 2:24, 35:34 |

A 14-anchor scan (types 2, 4, 9, 16, 19, 26, 29, 30, 33, 34, 35, 36, 37, 38)
finds the table at runtime 0x257FF0 uniquely in all four dumps; the
phase-0x20 offset (0x8FFB4-based) reads do NOT match the nodes.

## The +10 armour bonus

The structure-creation paths (`structure_place` GOG 0x1A1C4 and the second
creator 0x1A3DB..0x1A49C) apply the table value as-is when the per-race byte
at `race*0x26 + 0xC55E` is **<= 0** (signed), and **+10** when **> 0**. That
byte is the Sci-Tek **Building Armour** blueprint flag (catalogue id 6; the
per-race flag array is 0x26 = 38 bytes, one per catalogue item, starting at
`+0xC558`):

```
GOG 1A310: test %dl,%dl          ; dl = byte[race*0x26 + 0xc55e]
GOG 1A312: jle   1A31E           ; <= 0: no bonus
GOG 1A314: mov   0x9FD0(%eax),%al ; eax = 6*type
GOG 1A31A: add   $0xA,%al        ; +10
GOG 1A324: mov   %al,0x9(%ebx)   ; structure node +9 = current HP
```

The observed nodes carry the base values (no bonus) because those colonies'
race bytes were <= 0 at creation (the dumps' sessions had no player colony).
The damage helper (GOG 0x1AA94-family) decrements node +9; a structure is
destroyed at 0.

## Addressing (resolved)

The code reads the table through displacement `0x9FD0`. The data segment
base is such that **flat = displacement + 0x86004** (the table's first row at
flat 0x8FFD4 is displacement 0x9FD0). The same base places the Ship Yards
craft table (displacement 0xAB5C at flat 0x90B60), the item prices (0xAA08 at
0x90A0C), the missile table (0xB3B0 at 0x913B4) and the morale table (0xA3F6
at 0x903FA), so it is a property of the data object, not of this table. The
earlier "0x20 trap-prefix" explanation is superseded; the values are
unaffected. In the dumps the runtime address is flat + 0x1C801C (0x257FF0 for
this table).

## Neighbouring per-building tables

All indexed by the same building id; details and values in
`stat-tables-design-sheet.md`:

| flat | stride | content |
|---|---|---|
| 0x903FA | 1 | morale/unrest delta applied at placement (signed), Terran ids 0-39 |
| 0xBC278 | 20 | class record per id: footprint (+0 width, +1 height), +3 Terran role, +4 signed MW |
| 0x8F38B | 1 | power priority order (40 building ids) |
| 0x8F880 | 1 | the 27 ids available without a blueprint |

## Savegames

The savegame `BUILDING`/`SHIPS` sections are the 8000 x 24-byte pool dumps;
all free in every observed save (no building instances). No structure nodes
were found in the SAVEDATA section either. The savegames do not currently
carry building data to cross-check.

## References

- GOG flat 0x8FFD4 / ISO flat 0x986BC (the table, byte-identical for the
  Terran rows).
- `build/flat/gog_disasm.txt` 0x1A1C4..0x1A49C (the two creators), 0x1BF4
  (structure callback), 0x1C2F, 0x2494 (power), 0x3034 (morale), 0x512C4,
  0x5168C, 0x88A4..0x8952 (build queue).
- `build/dumps/ram_1cd67000.bin` etc. - structure nodes at ~0x58xxxx, the
  table at 0x257FF0.
- `build/reports/gog_constants.md` - the 0x90000 / 0x8FFC4 entries are
  misaligned views of this table.
- `docs/mechanics/stat-tables-design-sheet.md` - all 177 rows, power /
  capacity / staffing rules and provenance.
- `docs/mechanics/turrets-and-defence.md`, `weapon-and-turret-numbers.md` -
  the earlier "tables in code" analysis this page resolves for the
  armour/build-time/cost family.
