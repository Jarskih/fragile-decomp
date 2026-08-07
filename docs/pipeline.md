# fragile-decomp pipeline

The pipeline turns the original CD image into documented, faithful
understanding of the game's mechanics. Every stage is a script under
`scripts/`; every artifact lands in `build/` (gitignored). All conclusions we
write ourselves go into `docs/mechanics/` and `docs/dataformats/` (committed).

```
iso/FragileAllegiance.iso        (gitignored, provided by you or `make download`)
        │  00_download_iso.py    resumable fetch from archive.org + hash check
        ▼
01_verify_iso.py                 hash vs iso.sha256, track table (data/audio)
        ▼
02_extract_iso.py                data session → build/iso/  (audio TOC only)
        ▼
03_inventory.py                  build/reports/inventory.* (name/size/hash/magic)
        ▼
04_binary_info.py                build/reports/binaries.*  (16-bit vs 32-bit)
        ▼
05_extract_flat.py               build/flat/FRAGILE.EXE.flat (DOS/4G slice)
        ▼
06_flat_analyze.py               build/reports/flat_analysis.* (entry/regions)
        ▼
build_runtime.py                 build/flat/FRAGILE.EXE.runtime.flat (loader view)
        ▼
07_ghidra_headless.sh            build/decomp/ (Ghidra projects + exported C/asm)
        ▼
08_strings.py                    build/reports/strings/    (per-file string dumps)
09_dat_survey.py                 build/reports/datsurvey.* (magic/entropy/probes)
        ▼
10_dosbox_trace.sh               build/traces/ (INT 21h/file-open log, disc check)
        ▼
11_apply_names.py                build/named/ (annotated copy of the decompiled C)
        ▼
docs/mechanics/, docs/dataformats/      OUR written conclusions (committed)
```

Optional stages (inputs other than the ISO):

```
05b_extract_gog_flat.py          build/flat/FRAGILE.EXE.gog.flat (GOG build)
12_gog_constants.py              build/reports/gog_constants.* (stat tables)
memdump.ps1  +  13_dump_constants.py   build/dumps/ -> build/reports/dump_constants.*
```

## Stage details

### 00 — download (optional)
Fetches the reference ISO from archive.org (default source
`Fragile_Allegiance_Interplay_Eng`, a 625 MB CD image incl. audio tracks).
Refuses to overwrite an existing image; verifies SHA-256 once a hash is
recorded in `iso.sha256`. If you already own the image, drop it in `iso/`
and skip this stage.

### 01 — verify
Identifies the container type (`.iso`, `.bin/.cue`, `.nrg`, `.img`),
computes SHA-256 of the image, and (when recorded) cross-checks `iso.sha256`.
Uses `cd-info`/`isoinfo` to write the track table (data track vs. Red Book
audio) to `build/reports/tracks.*`.

### 02 — extract
Extracts the ISO9660 data session (Joliet/Rock-Ridge aware) with `7z`,
falling back to `bsdtar`. Preserves names and case. Audio tracks are listed,
not extracted. If the input is already a plain directory (e.g. the contents of
an archive.org DOSBox zip), it is used as-is.

### 03 — inventory
Walks `build/iso` and records every file: relative path, size, SHA-256,
`file` magic, and a coarse category. Produces `inventory.json` (machine
readable) and `inventory.md`. This is the map of the disc and the input to
later stages.

### 04 — binary info
For every executable found, parses the DOS MZ header (`e_lfanew`, header
paras, entry point, overlay flag) and sniffs for DOS extenders (DOS/4GW,
DOS/32A, Watcom, DJGPP/CWSDPMI, PMODE). Classifies each as **16-bit real
mode** or **32-bit protected mode** — this decides how we configure Ghidra.

### 05 — extract flat (DOS/4G bound image)
FRAGILE.EXE is DOS/4G-bound: an MZ stub plus a relocation page/offset table and
record stream, then a flat 32-bit image. Stage 05 locates the structural
anchors (`unbound` signature, page table at 0x3B8BE, offset table at 0x3BC70,
record stream at 0x3C020), parses the record stream with the verified grammar
(all streams 1..234 — 37,311 records, every 07-record verified against the
flat image), and slices the image (file 0x8A760..EOF) into
`build/flat/FRAGILE.EXE.flat`. See `docs/dataformats/dos4gw-bound.md`.

### 06 — flat analysis
Maps the flat image's regions from printable-ASCII density (code
0x0..0x8D000, binary data 0x8D000..0x92000, resource-file table
0x92000..0x97000, relocated code-pointer tables 0x97000..0xE9000, last-page
tables 0xE9000..EOF), finds the entry candidates (0x04 int3-trap NOP slide,
0x14 push6 prologue), and counts pointer dwords into the string region.
Output: `build/reports/flat_analysis.*`.

### 06b — runtime image build
Replays the relocation record stream the way the DOS/4G loader would over the
stage-05 slice. Every in-buffer field is pre-linked (already equals its
runtime value), so the replay must be a no-op; the stage fails loudly on any
mismatch and emits `build/flat/FRAGILE.EXE.runtime.flat`, byte-identical to
the static slice. The 7 `02`-records (DS data-selector setup) are inventoried
and left at their static placeholder. Output:
`build/reports/runtime_build.*`. `make runtime`.

### 07 — Ghidra headless
Runs `analyzeHeadless` once per executable: import, auto-analysis, then the
Ghidra scripts in `config/ghidra/` export decompiled C, function lists, and
symbol tables into `build/decomp/`. After the DOS programs, the flat image
from stage 05 is imported as a raw 32-bit x86 binary at **base 0**
(`-loader BinaryLoader -loader-baseAddr 0x0`); `config/ghidra/set_entry.java`
(pre-script) creates `main` at the entry (0x14) and labels the code/data
boundary before auto-analysis. Set `GHIDRA_HOME` if Ghidra is not on `PATH`.
**Decompiled output is never committed.**

### 08 — strings
Runs `strings` (ASCII + UTF-16LE) over the extracted files into
`build/reports/strings/`. String dumps reveal data-file names, error messages,
and table names — breadcrumbs for both data formats and later function naming.

### 09 — data-format survey
For candidate data blobs (large, non-executable, non-text), records first
bytes, per-block entropy (compression/encryption detection), and known-magic
hits. Output: `build/reports/datsurvey.*`. Follow-up format work is a human +
machine loop; conclusions go into `docs/dataformats/`.

### 10 — runtime trace
Generates a DOSBox-X config (template in `config/dosbox/`) that mounts
`build/iso` as the CD and the extracted/game dir as `C:`, then runs the game.
With `--trace` it passes `-log-int21 -log-fileio`, capturing INT 21h and
file-open activity plus the disc-check behavior into `build/traces/` on any
DOSBox-X build. A runtime load-base trace (from a custom `--enable-debug`
curses build) that would observe the runtime selector values of the 7
`02`-records is deferred; the static decompilation route is primary (see
`docs/dataformats/dos4gw-bound.md`).

### 11 — apply names
Ghidra's export in `build/decomp/` is treated as read-only. This stage copies
each `decompiled.c` and `functions.tsv` to `build/named/`, applying curated
descriptive names from `config/ghidra/rename-map.json` with word-boundary
substitutions. The map's `globals`/`functions`/`literals` sections apply
everywhere; the `locals` section applies function-scoped renames (Ghidra
register names such as `iVar3` re-named per function, keyed by function
address), so the same register name can mean different things in different
functions. Never edit `build/decomp/` by hand — renames live in the map so the
stage stays reproducible. `make names` is fast to iterate: editing the map and
re-running it re-applies the names without re-running Ghidra.

### 05b — GOG build flat (optional, `make gog-flat`)
The GOG retail install tree (`Fragile Allegiance/`, gitignored analysis
input) ships a *different build* of FRAGILE.EXE whose gameplay stat tables
are real static data (the ISO build's are not — see `gog-build-data.md`).
Stage 05b locates every DOS/4G anchor dynamically (no hardcoded offsets),
slices the flat image, and cross-checks all 261 record streams (34,921
fields verified, 1 off-buffer). Output: `build/flat/FRAGILE.EXE.gog.flat`
+ `build/reports/flat_extract_gog.*`.

### 12 — GOG constants (optional, `make gog-constants`)
Decodes the gameplay constant tables from the GOG flat: the 11-row
ore/starting-value table (p/lo/hi), the cost-bearing stat records (ids
0x1e..0x27 + 0x37, costs 10000..30000), the type-id list and the remaining
table region (roles unidentified, raw). Every table is shape-checked and
fails loudly on mismatch; the flat sha256 is pinned. Output:
`build/reports/gog_constants.*` + `gog_data_region.hex`.

### 13 — dump constants (optional, `make memdump` + `make dump-constants`)
`memdump.ps1` snapshots the running game's emulated RAM read-only into
`build/dumps/`; stage 13 locates the loaded image, derives the per-object
relocation bases (obj 3 = 0x24E000, obj 1 = 0x1C9000, obj 2 = 0x14F000 for
the GOG build), reads the runtime DS data selectors (the 7 `02`-record
sites), cross-checks the static tables at their runtime addresses
(byte-identical), and catalogs the runtime-written regions (player names,
generated palette ramps). Output: `build/reports/dump_constants.*` +
`build/flat/FRAGILE.EXE.gog.runtime.bin`.

## Reading the reports

Each stage writes both `.json` (for scripts) and `.md` (for humans) into
`build/reports/`. Start with `inventory.md` to see what the disc contains,
then `binaries.md` to know what we're disassembling.

## Reproducibility

- The pipeline is deterministic given the same image.
- `scripts/check_env.py` gates on tool versions from `config/rules.yaml`.
- `iso.sha256` pins the expected image so a substituted or corrupted file is
  caught before any analysis is wasted on it.
