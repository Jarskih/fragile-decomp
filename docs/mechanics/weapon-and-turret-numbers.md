# Weapon and turret numbers: what is known, and what blocks the rest

Status: **behaviour confirmed; the fire delay is now VERIFIED (15 or 40
game ticks, see below); the remaining numeric values (damage, build costs,
power use, ranges) are NOT statically extractable from the reference flat —
this is now a proven negative result, not a gap in effort.** See "The
base-search campaign" below for the exhaustive search that closes the
question, and "Data files on the ISO" for the equally negative file-side
survey. **Update (2026-08-07): the GOG retail build ships the same stat
families as real data** — `make gog-constants` (stage 12) extracts the
ore/starting-value table, the cost-bearing stat records (ids 0x1e..0x27 +
0x37, costs 10000..30000) and the type-id list from
`build/flat/FRAGILE.EXE.gog.flat`; `make dump-constants` (stage 13)
cross-checks them at their runtime addresses. See
`docs/dataformats/gog-build-data.md`. The displacement reads listed below
still point at code in the GOG flat too, so the *exact* mapping of those
records onto weapon damage / HP / range fields remains open.

Source: reference-build flat `build/flat/FRAGILE.EXE.flat` (Interplay CD),
its raw disassembly, and the partial Ghidra export
`build/decomp/FRAGILE.EXE.flat/decompiled.c`. Addresses are image-relative
(base 0) unless stated.

## The short answer

- Every per-type stat the game uses (hit points, cost, power, range,
  weapon-mode byte, fire delay, accuracy, launcher offsets) is read by the
  code through a **DS-relative displacement** (e.g. `0xa6ba`, `0xa4ac`,
  `0xaade`, `0xb244`, `0x386d4`).
- At the flat offset equal to that displacement the bytes are **executable
  instructions** — the "tables in code" anomaly already documented in
  `asteroid-spawning.md` and `turrets-and-defence.md`.
- The tables therefore live either at `base + displacement` for some
  runtime data-segment base `base`, or are **built at runtime into the code
  region** (the way the proven direction tables at `0x5c800`/`0x5c900` are
  filled by the loop at `0x21414`).
- An exhaustive search over every candidate base (page-aligned and
  16-byte-aligned, in both possible directions `base ± displacement`) with a
  multi-anchor score function found **no consistent candidate**. So the
  values exist only in memory at runtime; static extraction from this flat
  is impossible. A runtime memory trace remains the only route — the
  snapshot tooling now exists (see resolution paths).

## What the numbers are and where the code reads them

All reads below are directly verified in the disassembly/export. The
"index" is the per-type byte (building type or weapon type as appropriate);
exact type→text-index mapping is only partially confirmed
(see `turrets-and-defence.md`).

| displacement | stride | field | verified read |
|---|---|---|---|
| `0xa6b8` | 6 | base HP bytes (creation) | `(&DAT_0000a6b8)[type*6]` |
| `0xa6ba` | **1 or 6** | build cost, u16 | live construction UI: `mov bx,[ecx+0xa6ba]` (0x8a87, stride 1, compared against the per-race fund); creation/validation path: `[type*6 + 0xa6ba]` (stride 6). Both patterns exist; which is live is unresolved. |
| `0xaade` | 1 | power/maintenance, signed byte | subtracted from the colony power value |
| `0xb244` | 0x14 | defence range, u16 | `FUN_0001c2f4`, stored at node `+0x0a` (`>> 2`) |
| `0xb247` | 0x14 | behaviour byte | re-armed into node `+0x52` |
| `0xb251` | 0x14 | building category byte | tested `== 7` in destruction |
| `0x386d4` | 0x14 | footprint width/height bytes | surface painter `FUN_0002fd34` |
| `0xa4ac` | 0xc | **ship/weapon table**: callback fn `+0`, race-mask u16 `+4`, mode byte `+8` (`-1` = disabled), **fire-delay byte `+9`**, flag u16 `+0xa` | weapon-slot code `FUN_00014384`: `call *0xa4ac(%edi)`; `[type*0xc + 0xa4b4]` mode check; `[type*0xc + 0xa4b5]` reload value; the 0xa4b5 read at 0xa4b5 is +9 from the table start |
| `0xc458` | 4 | per-race fund (credits), u32 | `[race*4 + 0xc458]`, compared against cost at 0x8a8e (live) |
| `0xcd8c` | — | player race, byte | `== *(byte*)(node+0xd0)` comparisons in the weapon code |
| `0x5bf70`..`0x5bf78` | — | build-queue state (live UI globals) | decremented at 0x8ab4, busy flag at `0x5bf78+0x21` |
| `0x7a5c8`/`0x7a5cc` | — | launch-position globals | written by `0x35874`, read by the fire wrapper |
| `0x5c800`/`0x5c900` | 4 | shared sin/cos direction tables, 256 dwords | **runtime-filled** by `0x21414` (320-entry window) — the model case for the anomaly |

### Fire delay semantics (from `FUN_00014384`)

- Each weapon slot node has a countdown `+0x10` and a state `+0x12`.
- When the slot's countdown expires, the weapon re-arms by reading the
  **per-type fire-delay byte** `[type*0xc + 0xa4b5]` into `+0x10`.
- The delay is a **tick count**: `+0x10` is decremented once per pass of the
  weapon handler, and one tick = one pass of `main` (see `main-loop.md`).
- After a successful shot the state is reset to `0x28` (**40 ticks**) before
  the per-type delay is loaded — a fixed rearm floor.
- The mode byte at `+8` (a.k.a. `0xa4b4`) checked `== -1` disables the
  weapon type.

## Live code confirmed this session

The construction-UI handler at `0x8a61`..`0x8ac0` is **live** (verified by
its behaviour, not assumed): it checks affordability
(`cost <= fund[race]`), sets/clears the busy flag, and decrements the
build-queue global. It reads:

- cost `u16` at `[type*2 + 0xa6ba]` (stride 1 — the affordability check the
  player actually sees);
- per-race fund at `[race*4 + 0xc458]`;
- globals at `0x5bf70`/`0x5bf74`/`0x5bf78`, `0x7a5c8`/`0x7a5cc`, `0x5c598`.

It also calls `FUN_0001a4b4` (placement validation, 49 call sites) — so
that function is reached at runtime.

Consequence: the earlier single-stride descriptions of the cost table
("stride 6" in `turrets-and-defence.md`) are incomplete — the live UI uses
stride 1. The two access patterns conflict; resolving which is the real
table layout requires the runtime tables (same blocker).

## The base-search campaign (the negative result)

Goal: find a base `B0` such that `B0 + displacement` (or `B0 −
displacement`) lands on real data for *all* tables simultaneously.

Anchors used per candidate: (a) rng state at `0x4cd7c` must be zero-initial
(BSS); (b) ten consecutive u16 costs in `[50, 60000]`; (c) six consecutive
weapon-table rows whose leading dword is a code-region pointer; plus manual
checks of HP bytes, power bytes, per-race funds, and the player-race byte.

Searches run, all **negative**:

1. `B0` page-aligned (`0x100` steps), `flat = B0 + displacement`.
2. `B0` page-aligned, `flat = displacement − B0`.
3. `B0` 16-byte-aligned (`0x10` steps), `flat = B0 + displacement`, full
   anchor set. The only two survivors (`0x8d3c0`, `0x8ddc0`) fail every
   content check on inspection (random costs, non-pointer weapon rows,
   garbage funds).

So the tables are **not present as data at any aligned base** in the flat.
Either the runtime DS base is unusual, or — consistent with the proven
direction-table precedent — the game materialises these tables at startup
in memory over what the flat shows as code. Either way the values are
runtime-only.

## Real data tables found in the flat (role unknown)

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
- Re-checking the table regions against the image (`0xa4ac..0xa520` weapon
  table, `0xc02c..0xc0a4` per-ship stats, `0xba8a`/`0xbfe4` dispatch,
  `0x9f88`/`0xa16c`/`0xa173`, the `0xf058` ammo pools, the `0xc458` funds,
  the `0xc3f4` list head): every one of these addresses decodes as
  instructions in the flat ("tables in code"), and no instruction anywhere
  in the image stores to any of them (exhaustive grep for absolute stores
  and `mov reg,$imm` base loads is empty). The known exception — the
  direction tables `0x5c800`/`0x5c900`, whose fill loop at `0x21414` is
  visible — shows the pattern the stat tables must follow: materialised in
  memory at startup from values that exist only in the program's runtime
  state, with no statically readable source.

So: **the numbers are not in any data file on the disc, and not in the
reference-ISO executable image as data.** They are installed into memory at
startup by the game itself (constants in the init path or derived), and the
only way to read them in the ISO build remains a runtime memory trace.
**Update (2026-08-07): the GOG build is the exception** — its flat ships the
same stat families as real static tables (stage 12 / `gog-build-data.md`),
so the numbers *are* statically readable from that build.

## The 0x20000-family "combat tick" is unreferenced

The per-subtype combat handlers at `0x200e4`/`0x2049c`/`0x20564`/`0x2059e`/
`0x20809` (the `rng_next(100) < 0xc095[subtype]` strike roll)/`0x20b51`/
`0x210a7` and the sweep helpers `0x1fd34`/`0x1fde4` have **no static
callers** in the full disassembly (checked line-by-line). Their stat reads
land on instruction bytes (above), and no chain of pointer tables reaches
them (the known dispatch table at `0x71dac` points into `0x7c000` code,
not `0x20000`). They are therefore **probably stale code** from an earlier
layout. Consequence for analysis: the strike-roll / heading-roll accuracy
mechanics found in that family are **not confirmed live**; the live combat
path is the slot machinery (`0x14384`/`0x14114`/`0x4a374`/`0x4a3b4`) plus
the event handler `0x52b74` (event types 0..2 → cell scan `0x1aea4`, type 4
→ shot spawn `0x1ffc4`), and its accuracy mechanics sit inside the
runtime-only callback table `0xa4ac` — unreachable statically.

## Resolution paths

1. **Runtime memory trace — tooling in place and executed.** `make memdump`
   (read-only snapshot) has been run; `make dump-constants` (stage 13)
   locates the loaded image, derives the per-object relocation bases
   (obj 3 = 0x24E000, obj 1 = 0x1C9000, obj 2 = 0x14F000 for the GOG
   build), reads the runtime DS data selectors (0xD88E/0xD98E/0xDB8E), and
   cross-checks the static tables in memory — byte-identical
   (`build/reports/dump_constants.md`). The ISO build's own runtime layout
   would be decoded the same way if the ISO build is run instead.
2. **GOG flat — DONE.** The GOG binary is in the workspace
   (`Fragile Allegiance/`, gitignored analysis input). `make gog-flat` +
   `make gog-constants` extract and verify its flat and decode the tables
   (see `docs/dataformats/gog-build-data.md`). The rename map's GOG-side
   names can now be cross-checked against these values.

## Fire delay — VERIFIED (GOG build, second dump 2026-08-07)

A second memdump (`build/dumps/ram_1cdfd000.bin`, game in the colony view)
plus a disassembly pass of the GOG fire code settles the original question:

- The per-node **fire countdown** is the byte at node `+0x1a9`,
  decremented once per tick (`0x9b99..0x9ba3`), and the weapon fires when
  it reaches zero.
- On firing, the countdown is reloaded with a **constant**:
  - **40 ticks** — the main node-fire tick at 0x115a4 (the same 40-tick
    rearm floor as the reference build's `slot+0x12 = 0x28`);
  - **15 ticks** — the second fire path at 0x9bc9/0x9c16.
- Both paths then call the shot spawner 0x48e64 with
  `(node, 0x8d, 0x1e, <race global>, 0, <race global>, node+0x4c, 0)` —
  the 0x37b30/0x37b34 vs 0x37e20/0x37e24 pairs are the two launcher
  contexts (missile silo vs turret / ship).
- Per-node fire gating: only nodes whose owner (`+0xc0`) equals the player
  race (0xc6b0) call the spawner.

So: **a launcher fires every 15 or 40 game ticks** (path-dependent), one
tick = one pass of `main` (see `docs/mechanics/main-loop.md`).

### Leads chased and eliminated (same session)

The two per-type table families that looked like weapon stats are NOT:

- `0x357b4`-family (stride 0x14; the map's g_weapon_twin_dword/field_a/
  thresh_a+b names) — at runtime (0x2837B4) this is the game's
  **asset/file table**: 8 file slots (`type byte @0x2db7b4`, `dword
  @0x2db7fc`, `dword @0x2db7dc`) and 12-byte rows `{file-name ptr,
  0x80000000, size}` with pointers into the string pool (`_P\laser.256`,
  `_P\XB00.256`, … — the weapon-sprite file names; flat equivalent 0x957B4
  is zeros, so the table is built at startup). The 0x51954..0x51cc0
  functions that read it are the **asset loader / type selector**, not the
  weapons. Its per-type byte fields read all-zero in the dumps (no combat
  state materialises them here).
- `0x39040` (stride 4) — a per-type **text-pointer table** into the loaded
  AMERICAN.TXT buffer (runtime 0x6edxxx = the description strings; read at
  0x9be8 with `0x39040(,%type,4)`).

## References

- `build/flat/FRAGILE.EXE.flat`, `build/flat/full_disasm.txt` — source
  data (regenerated 2026-08-07).
- `build/decomp/FRAGILE.EXE.flat/decompiled.c` — `FUN_00014384`,
  `FUN_0001a4b4`, `FUN_0001c2f4`, `FUN_0001ddc4`, `FUN_0001e934`.
- `docs/mechanics/turrets-and-defence.md`, `docs/mechanics/weapons.md` —
  behaviour and firing pipeline.
- `docs/mechanics/asteroid-spawning.md` — the "tables in code" anomaly and
  the runtime fill precedent.
- `docs/mechanics/main-loop.md` — the tick dispatcher (one tick = one pass
  of main).
