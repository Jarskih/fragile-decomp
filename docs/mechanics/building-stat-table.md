# The per-type building stat table (HP, state, cost)

Status: **confirmed**. The building stat table exists as real static data in
BOTH builds — GOG flat `0x8FFD4`, ISO flat `0x986BC` (byte-identical) — and
the GOG build's runtime copy was verified byte-identical in all four memory
dumps. The **row values are verified against the actual structure nodes in
the runtime dumps** (25 nodes across the four dumps; 14 anchor values match
uniquely). What remains open is the full type-byte → building-name mapping
(partially confirmed: type 9 = Satellite Silo, type 33 = Protected Storage
Tower — the type byte equals the AMERICAN.TXT text index for those).

Correction (2026-08-22): an earlier draft of this page read the table 0x20
bytes early (at GOG flat 0x8FFB4). The bytes there are the tail of the
preceding data; the table itself starts at 0x8FFD4. The corrected values
below are the ones the structure nodes in the dumps actually carry.

Source: GOG flat `build/flat/FRAGILE.EXE.gog.flat`, ISO flat
`build/flat/FRAGILE.EXE.flat`, their disassemblies, and the runtime dumps
`build/dumps/ram_*.bin` (image base 0x1C901C, code object base 0x24E000).

## The table

| build | flat offset | runtime (GOG, all 4 dumps) | rows | stride |
|---|---|---|---|---|
| GOG | 0x8FFD4 | 0x257FF0 (linear) | 40 | 6 |
| ISO | 0x986BC | materialised at 0xA6B8-family (the "tables in code" slot) | 40 | 6 |

Row layout (offsets relative to the row start): `{+0 base HP u8, +1 state
u8, +2 cost u16, +4 u16}`. The +4 u16 is zero for most rows; where non-zero
(types 3, 17, 18, 27, 31, 33) it is the overlapping tail of the preceding
data region, not an independent field — treat the row as `{HP, state,
cost}` with 2 pad bytes.

The earlier stage-12 report entries "0x90000 {u16,u16} pairs" and "0x8FFC4
mixed bytes" (`gog_constants.md`) are misaligned u16 re-reads of this same
table, not separate tables. The earlier draft's "0x8FFB4" reading covered
the tail of the preceding region plus the table's start at 0x8FFD4.

## Values (40 rows, type byte order)

```
 t:  HP st  cost    t:  HP st  cost     t:  HP st  cost
 0:   5 32  1000    14: 15 32  4300    28: 10 32  4000
 1:  34 32  1500    15: 20 36 30000    29: 10 48  3000
 2:  24 20  1500    16: 15 36  3500    30: 32 40  3000
 3:  16 36 15000    17: 20 30  5500    31: 20 32  7200
 4:   5  8   500    18: 20 52  7500    32: 40 30  8500
 5:  24 30  8000    19: 24 48 13000    33: 32 48  7500
 6:  10 10  1500    20: 36 40  8000    34: 15 30  5000
 7:  24 32  4400    21: 24 42 26500    35: 34 20  3200
 8:  20 32  4000    22: 28 64 45000    36: 10 32  5000
 9:  10 24  5000    23: 34 40 10000    37: 24 16  7000
10:  36 52 20000    24: 36 32  8000    38: 20 20  5000
11:  36 48 45000    25: 20 32  7500    39: 15 24  4500
12:  24 52 35000    26:  5 16   300
13:  20 36  5500    27: 16 25  3400
```

The state column (+1) is the initial state/range low byte read at creation
(`[type*6 + 0x9FD1]`, default path; the two special paths write 1 or 4).

## Verification against the runtime structure nodes

The runtime dumps contain real structure nodes (callback 0x1CABF0 =
relocated FUN_00001BF0; type at node +8, current HP at +9, grid position at
+0x14/+0x15). Their {type, HP} pairs match the table EXACTLY (undamaged):

| dump | nodes (type:HP) |
|---|---|
| ram_1cd67000.bin | 26:5, 16:15, 29:10, 37:24, 29:10, 2:24 |
| ram_1cdfd000.bin | 9:10, 34:15, 38:20, 37:24, 36:10, 4:5, 30:32, 29:10, 4:5 ×4, 38:20 |
| ram_1ce2a000.bin | 19:24, 29:10 |
| ram_20459000.bin | 33:32, 26:5, 2:24, 35:34 |

A 14-anchor scan (types 2,4,9,16,19,26,29,30,33,34,35,36,37,38) finds the
table at runtime 0x257FF0 uniquely in all four dumps; the phase-0x20 offset
(0x8FFB4-based) reads do NOT match the nodes.

## The +10 HP bonus

The structure-creation paths (`structure_place` GOG 0x1A1C4 and the second
creator 0x1A3DB..0x1A49C) apply the table value as-is when the per-race byte
at `race*0x26 + 0xC55E` is **≤ 0** (signed), and **+10** when **> 0**:

```
GOG 1A310: test %dl,%dl          ; dl = byte[race*0x26 + 0xc55e]
GOG 1A312: jle   1A31E           ; <= 0: no bonus
GOG 1A314: mov   0x9FD0(%eax),%al ; eax = 6*type
GOG 1A31A: add   $0xA,%al        ; +10
GOG 1A324: mov   %al,0x9(%ebx)   ; structure node +9 = current HP
```

The observed nodes carry the base values (no bonus) — those colonies' race
bytes were ≤ 0 at creation (the dumps' sessions had no player colony). The
damage helper (GOG 0x1AA94-family) decrements node +9; a structure is
destroyed at 0.

## Open addressing question

The relocated read sites use displacement 0x9FD0 (`0x24E000 + 0x9FD0 =
0x257FD0`), but the table matching the nodes sits 0x20 bytes later (0x257FF0
= flat 0x8FFD4). The 0x20 = the image's trap prefix (4 zero bytes + 3-byte
trap + 0x19 nops = 0x20 bytes), suggesting the displaced reads resolve
relative to the image start minus the trap prefix — i.e. the runtime data
segment base is the image base + 0x20. This is consistent with the
"DS data selectors" note in `gog-build-data.md` (the bases were never
resolved). The values are unaffected: the nodes prove which bytes the game
uses.

## Type → building mapping (partial)

The type byte equals the AMERICAN.TXT text index for the verified cases:

| type | building | HP | cost |
|---|---|---|---|
| 9 | Satellite Silo (code-verified) | 10 | 5000 |
| 33 | Protected Storage Tower (text index 33) | 32 | 7500 |

The turrets (text 17 Plasma, 18 Photon, 27 Laser), the missile and
anti-missile buildings (3, 14), the Screen Generator (10) and Solar Matrix
(28) sit at the text-index rows of this table with plausible HP/cost
(16/15000, 15/4300, 20/5500, 20/7500, 16/3400, 36/20000, 10/4000) — but the
exact mapping for those still needs the live colony-view confirmation (see
`turrets-and-defence.md`). The dumps' node types (2, 4, 9, 16, 19, 26, 29,
30, 33, 34, 35, 36, 37, 38) are all members of the type-id list at 0x8F880.

## Savegames

The savegame `BUILDING`/`SHIPS` sections are the 8000 × 24-byte pool dumps;
all free in every observed save (no building instances). No structure nodes
were found in the SAVEDATA section either. The savegames do not currently
carry building data to cross-check.

## References

- GOG flat 0x8FFD4 / ISO flat 0x986BC (the table, byte-identical).
- `build/flat/gog_disasm.txt` 0x1A1C4..0x1A49C (the two creators), 0x88A4..
  0x8952 (build queue), 0x1C2F, 0x512C4, 0x5168C.
- `build/dumps/ram_1cd67000.bin` etc. — structure nodes at ~0x58xxxx,
  the table at 0x257FF0.
- `build/reports/gog_constants.md` — the 0x90000 / 0x8FFC4 entries are
  misaligned views of this table.
- `docs/mechanics/turrets-and-defence.md`, `weapon-and-turret-numbers.md` —
  the earlier "tables in code" analysis this page resolves for the
  HP/state/cost family.