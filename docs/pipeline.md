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
record stream at 0x3C020), parses the record stream with the verified group
grammar (all groups 1..233 — every 07-record verified against the flat image),
and slices the image (file 0x8A760..EOF) into
`build/flat/FRAGILE.EXE.flat`. See `docs/dataformats/dos4gw-bound.md`.

### 06 — flat analysis
Maps the flat image's regions from printable-ASCII density (code
0x0..0x8D000, binary data 0x8D000..0x92000, resource-file table 0x92000..EOF),
finds the entry candidates (0x04 int3-trap NOP slide, 0x14 push6 prologue),
and counts pointer dwords into the string region. Output:
`build/reports/flat_analysis.*`.

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
curses build) that would validate the relocation records is deferred; the
static decompilation route is primary (see `docs/dataformats/dos4gw-bound.md`).

### 11 — apply names
Ghidra's export in `build/decomp/` is treated as read-only. This stage copies
each `decompiled.c` and `functions.tsv` to `build/named/`, applying curated
descriptive names from `config/ghidra/rename-map.json` with word-boundary
substitutions. Never edit `build/decomp/` by hand — renames live in the map
so the stage stays reproducible. `make names` is fast to iterate: editing the
map and re-running it re-applies the names without re-running Ghidra.

## Reading the reports

Each stage writes both `.json` (for scripts) and `.md` (for humans) into
`build/reports/`. Start with `inventory.md` to see what the disc contains,
then `binaries.md` to know what we're disassembling.

## Reproducibility

- The pipeline is deterministic given the same image.
- `scripts/check_env.py` gates on tool versions from `config/rules.yaml`.
- `iso.sha256` pins the expected image so a substituted or corrupted file is
  caught before any analysis is wasted on it.
