# The GOG build and its gameplay constant tables

Status: extraction confirmed; the gameplay stat tables exist as **real
static data** in the GOG build's flat image. Table *roles* beyond the
ore/start-values table and the cost records are still being pinned down.

Corrected 2026-10-18 (read this first): (1) the "tables in code" anomaly is a
**base error**, not a data problem: every DS displacement `D` of a static table
is at **GOG flat `D + 0x86004`** (data object at flat 0x86000 plus the 4-byte
image header); reading `D` itself as a flat offset hits code. Verified on the
building table (0x9fd0 -> 0x8FFD4), craft table (0xab5c -> 0x90B60), item
prices (0xaa08 -> 0x90A0C), missile table (0xb3b0 -> 0x913B4), morale
(0xa3f6 -> 0x903FA), ore table (0x9cec -> 0x9FCF0), the Sci-Tek grid and the
supervisor table (0x967c -> 0x8F680). The "Still open" paragraph at the end of
this note is therefore obsolete, and the memdump offset for a flat address
>= 0x86000 is `flat + 0x1C801C`. (2) The records at 0x8F680 are the **Colony
Supervisor table** (not an unidentified stat table) and the id list at 0x8F880
is the **starting build menu** (see the corrected sections below).

## Why a second build

The reference-ISO build of FRAGILE.EXE reads its gameplay stat tables
(ore starting values, building/ship costs, hit points, footprints …) through
DS-relative displacements. Read as flat offsets they land on **code** — the
former "tables in code" anomaly (`docs/mechanics/asteroid-creation.md`,
`docs/mechanics/weapon-and-turret-numbers.md`). Corrected 2026-10-18: the
anomaly was the missing +0x86004 (GOG) / +0x8E004 (ISO) data-object base, not
absent data; the base-search that found no candidate used 16-byte-aligned
bases only and so missed it.

The GOG retail install (gitignored analysis input, `Fragile Allegiance/`)
ships a **different build** of FRAGILE.EXE (1,612,039 B vs 1,525,267 B;
261 pages vs 234). Its flat image carries the same data families as real
static tables in a binary-data region (flat 0x8F000..0x9C000), which makes
the numbers extractable:

- `make gog-flat` (stage 05b) slices and verifies the GOG flat.
- `make gog-constants` (stage 12) decodes the tables into
  `build/reports/gog_constants.*`.
- `make memdump` + `make dump-constants` (stage 13) cross-check the tables
  at their runtime addresses against a read-only snapshot of the running
  game.

## Stage 05b: extraction (dynamic anchors)

The GOG build is a DOS/4G *bound* image of the same shape as the ISO build
(see `docs/dataformats/dos4gw-bound.md` for the grammar), but every anchor
differs. Stage 05b therefore locates all anchors dynamically:

| anchor | value (GOG) | how found |
|---|---|---|
| `unbound` marker | file 0x3BCD5 | signature scan |
| page table | file 0x3B8BE | longest backward run of sequential dwords |
| offset table | file 0x3BCDC | marker + 7; 263 entries |
| record stream | file 0x3C0F8 | end of the offset table |
| flat image | file 0x85760 | trap signature after the stream, zero-padded |
| flat size | 0x1041A7 (1,065,383 B) | sha256 `4e8d2d96…` (pinned in the script) |

The offset-table length is chosen as the largest N whose last stream ends in
zero padding right before the image (a monotonic garbage tail entry in the
raw scan is rejected this way). All 261 streams are parsed with the verified
grammar and every in-buffer field is cross-checked against the slice:
**34,921 verified, 0 mismatches, 1 off-buffer record** (the documented
last-record family). Record mix: 27,915 type-0x10 + 7,007 type-0x00 + 7
`02`-records; 81 empty streams.

## The gameplay constant tables (flat offsets, stage 12)

Region map of the GOG flat (image-relative):

```
0x00000..0x85000  code (incl. a DOS/4G 16-bit stub page at 0x85000..0x86000)
0x86000..0x8F000  string pool (config keys, messages, formats)
0x8F000..0x9C000  binary data: the gameplay constant tables
0x9C000..         catalog / pointer tables, then zero (BSS) regions
```

### Ore / starting-value table @ 0x8FCE2 (11 rows x 14 B)

| row | p (%) | lo | hi | v1 | v2 | v3 | tag |
|---|---|---|---|---|---|---|---|
| 0 | 5 | 8 | 20 | 0 | 65 | 1 | 2 |
| 1 | 80 | 500 | 1000 | 200 | 250 | 300 | 1 |
| 2 | 80 | 250 | 500 | 200 | 300 | 400 | 2 |
| 3 | 60 | 250 | 500 | 200 | 300 | 400 | 3 |
| 4 | 80 | 250 | 750 | 100 | 100 | 150 | 4 |
| 5 | 80 | 50 | 116 | 50 | 50 | 70 | 5 |
| 6 | 60 | 20 | 116 | 50 | 50 | 60 | 7 |
| 7 | 50 | 10 | 100 | 20 | 25 | 35 | 10 |
| 8 | 50 | 10 | 100 | 10 | 28 | 35 | 20 |
| 9 | 35 | 2 | 15 | 0 | 0 | 0 | 70 |
| 10 | 25 | 1 | 8 | 0 | 0 | 0 | 100 |

Row shape `{p u8, pad u8, lo u16, hi u16, v1 u16, v2 u16, v3 u16, tag u16}`
matches the ISO build's `asteroid_gen_start_values` reader exactly
(p @ +0, lo @ +2, hi @ +4, stride 0xE): `roll < p` gives a "rich" value in
`[lo, hi]`, otherwise a poor value derives from `hi`. The v1/v2/v3/tag
columns are not yet mapped to code (open question).

### Stat records @ 0x8F680 — the Colony Supervisor table

Corrected 2026-10-18: these 16 rows are the Colony Supervisor table
(displacement 0x967C): `cost` is the monthly salary, `cnt`/`f` the warn-after
and unused bytes, `a..e` the workload thresholds, and the trailing `id` the
portrait / CV id of the next row's supervisor, not a building type id. The
full decode is in `docs/mechanics/economy-and-personnel.md` section 4.1. The
raw dump follows as originally recorded (columns `id`/`cost`/`f`/`cnt`/`a..e`
are the old labels).

A headless first record `{cost u16, f u8, cnt u8, a..e u32}` (24 B) followed
by 15 records of `{id u32, cost u16, f u8, cnt u8, a..e u32}` (28 B, stride
0x1C):

| id | cost | f | cnt | a | b | c | d | e |
|---|---|---|---|---|---|---|---|---|
| 0x1F (31) | 15000 | 2 | 4 | 2000 | 200000 | 8000 | 400000 | … |
| 0x20 (32) | 10000 | 1 | 2 | 1000 | 2000 | 12000 | 8000 | … |
| 0x21 (33) | 25000 | 2 | 12 | 2000 | 4000 | 12000 | 400000 | … |
| 0x22 (34) | 15000 | 1 | 4 | 0 | 200000 | 4000 | 4000 | … |
| 0x23 (35) | 20000 | 3 | 6 | 2000 | 200000 | 8000 | 400000 | … |
| 0x24 (36) | 20000 | 4 | 8 | 1000 | 4000 | 8000 | 12000 | … |
| 0x25 (37) | 30000 | 0x63 | 1 | 3000 | 200000 | 12000 | 400000 | … |
| 0x26 (38) | 10000 | 2 | 3 | 1000 | 4000 | 400000 | 8000 | … |
| 0x27 (39) | 30000 | 1 | 6 | 4000 | 4000 | 12000 | 400000 | … |
| 0x1E (30) | 20000 | 1 | 12 | 2000 | 2000 | 400000 | 8000 | … |
| 0x1F (31) | 20000 | 1 | 6 | 100000 | 4000 | 12000 | 8000 | … |
| 0x20 (32) | 15000 | 6 | 8 | 3000 | 0 | 400000 | 12000 | … |
| 0x21 (33) | 25000 | 1 | 6 | 2000 | 200000 | 400000 | 8000 | … |
| 0x37 (55) | 15000 | 0x63 | 6 | 0 | 4000 | 400000 | 8000 | … |
| 0x23 (35) | 10000 | 4 | 5 | 2000 | 200000 | 8000 | 400000 | … |

Full table incl. the `e` column: `build/reports/gog_constants.md`. The ids
resemble the id list @ 0x8F880 (28 ids with holes: 0,1,2,4,5,6,7,8,9,0xD,
0xE,0x10,0x13,0x18,0x19,0x1A,0x1B,0x1D,0x1E,0x20..0x27) only by coincidence:
Corrected 2026-10-18, the list at 0x8F880 (displacement 0x987c) is the
**starting build menu** (the building ids offered at game start), not a
type-id list for these records. The first record's
`{cost=25000, f=3, cnt=4}` equals the ISO doc's observed `{25000, 1027}`
(u16 0x0403) — same table family, now readable. Fields `a..e` are
the supervisor workload thresholds T2..T5 (see the correction above).

### Other tables in the region (raw, roles unidentified)

- 0x8F5D0: u32 runs 300/400/500 x4, 999x3, 600/400/200 — Corrected 2026-10-18: the alien Non-Aggression-Pact / Joint-Combat-Treaty proposal periods by atmosphere (`docs/mechanics/alien-ai-trade-victory.md` 6.5), not income. The race income table (100/250/400 Cr per day, indexed by atmosphere) is the separate word array at 0x8F3B4 (displacement 0x93B0).
- 0x8F840: 15 {u16,u16} pairs (100,4), (5000,0), (150,4), … .
- 0x8F898: signed u16 runs (position-like).
- 0x8FCA8/0x8FCC8: u16 table; `0x5a 0x50` + twelve 0x64 (100) + 0xFC.
- 0x8FD80/0x8FE60/0x8FEA4: byte ramps (surface/palette candidates).
- 0x8FEC4: u16s 205,200,210,185,190,195,150x6 — the alien expansion-attempt periods for races 9..14 (`alien-ai-trade-victory.md` section 1) and the 150-day alien agent slot-event periods.
- 0x8FF40/0x8FF78: 4-byte rows; 0x8FF48: 12 code pointers.
- 0x90000: {u16,u16} pairs (4400,8212), (4000,6154), … — **resolved: a
  misaligned u16 re-read (phase +0x4C) of the building stat table** (Corrected
  2026-10-18: it starts at 0x8FFD4 (displacement 0x9fd0) and has 177 rows of
  6 B, not 40 -- the 40 Terran buildings are only ids 0-39; rows were
  {HP u8, build days u8, cost u16, muzzle byte, muzzle byte}; see
  `docs/mechanics/building-stat-table.md`), not a separate table.
- 0x90A0A / 0x90B60 / 0x90C20: **the Ship Yards item catalog** — 16
  weapon/module prices (1000..12000 Cr; verified against the live Ship
  Yards screen), the Shield x10..x50 armour values {10,20,30,40,50}, and
  the **41-record craft table at 0x90B60** (Corrected 2026-10-18: not "per-item
  `{u16 x6, text-offset, days, price}` records" with a resolved text offset;
  the fields are in `docs/mechanics/stat-tables-design-sheet.md` 2.1 and
  `vehicles.md`; see also `weapon-and-turret-numbers.md`, "The item price catalog").
  The ISO build ships the same tables at 0x990F4 / 0x99164.
- 0x91800: 4-byte rows of small values.
- 0x8F2C0/0x8F2D0: two 16-row permutation tables over 0..3.

The full hexdump lives in `build/reports/gog_data_region.hex` (stage 12).

## Stage 13: runtime dump decode (make memdump + make dump-constants)

`scripts/memdump.ps1` snapshots the emulated RAM of the running DOSBox
read-only (`build/dumps/ram_<base>.bin`); stage 13 locates the loaded image
inside it and reports:

- **Image**: dump offset 0x1C901C (trap + entry prologue match the static
  flat); the relocation base is derived per object from the record stream —
  **obj 3 = 0x24E000** (21,419 fields), **obj 1 = 0x1C9000** (1,394
  fields), **obj 2 = 0x14F000** (1 field).
- **Layout quirk**: the DOS/4G 16-bit stub page (flat 0x85000..0x86000) is
  **not mapped** at runtime; every flat offset >= 0x86000 shifts down by
  0x1000. Verified for the string pool, the resource catalog and the stat
  tables (ore table @ runtime 0x8ECE2, stat records @ 0x8E680).
- **DS data selectors** (the 7 `02`-record sites): 0xD88E / 0xD98E /
  0xDB8E at runtime.
- **Static tables at runtime**: byte-identical to the flat (the tables are
  not materialised at startup — they ship as data).
- **Runtime-written regions**: startup state and generated tables — the
  multiplayer player names ("Fragile Allegiance 1".."9" @ 0x90B1D),
  version/date format strings, and VGA palette-ramp tables (0x999A0..,
  6-bit ramp values — the lighting-fade family documented in
  `docs/mechanics/asteroid-creation.md`).

### What this settles and what it does not

- **Settled**: the GOG build ships the stat tables as data; the values in
  stage 12's report are the values the running game uses (verified in
  memory). The ISO build's "tables in code" anomaly is *not* a linker
  quirk of the tables themselves — the same tables exist in the GOG build
  as plain data.
- **Resolved 2026-10-18** (was "still open"): the ISO and GOG builds both
  reach their tables through DS displacements; the data object sits at
  flat `D + 0x86004` (GOG) / `D + 0x8E004` (ISO). There is no runtime
  materialisation and no need for the GDT/LDT: the displacement reads (0xab69,
  0xb3b4, ...) hit static craft / missile table fields. The ISO side was
  verified for the building table only.

## Reproducibility

- The GOG flat sha256 is pinned in both stage scripts; a changed/replaced
  GOG install fails loudly.
- `make gog-flat` / `make gog-constants` / `make dump-constants` are
  standalone targets (the GOG tree is optional input, unlike the ISO).
- Nothing from `Fragile Allegiance/` or `build/dumps/` is ever committed.

## References

- `build/reports/flat_extract_gog.md`, `build/reports/gog_constants.md`,
  `build/reports/dump_constants.md` (derived).
- `docs/dataformats/dos4gw-bound.md` — the record grammar both builds share.
- `docs/mechanics/weapon-and-turret-numbers.md` — the ISO-side negative
  result this work supersedes for the GOG build.
- `docs/mechanics/asteroid-creation.md` — the 0xa3xx "tables in code"
  anomaly (resolved: +0x86004/+0x8E004 base).
- `docs/mechanics/stat-tables-design-sheet.md` — the consolidated table view.
