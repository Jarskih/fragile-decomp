# OpenFA pipeline

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
05_ghidra_headless.sh            build/decomp/ (Ghidra projects + exported C/asm)
        ▼
06_strings.py                    build/reports/strings/    (per-file string dumps)
07_dat_survey.py                 build/reports/datsurvey.* (magic/entropy/probes)
        ▼
08_dosbox_trace.sh               build/traces/ (INT 21h file opens, disc check)
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

### 05 — Ghidra headless
Runs `analyzeHeadless` once per executable: import, auto-analysis, then the
Ghidra scripts in `config/ghidra/` export decompiled C, function lists, and
symbol tables into `build/decomp/`. Set `GHIDRA_HOME` if Ghidra is not on
`PATH`. **Decompiled output is never committed.**

### 06 — strings
Runs `strings` (ASCII + UTF-16LE) over the extracted files into
`build/reports/strings/`. String dumps reveal data-file names, error messages,
and table names — breadcrumbs for both data formats and later function naming.

### 07 — data-format survey
For candidate data blobs (large, non-executable, non-text), records first
bytes, per-block entropy (compression/encryption detection), and known-magic
hits. Output: `build/reports/datsurvey.*`. Follow-up format work is a human +
machine loop; conclusions go into `docs/dataformats/`.

### 08 — runtime trace
Generates a DOSBox-X config (template in `config/dosbox/`) that mounts
`build/iso` as the CD and the extracted/game dir as `C:`, then runs the game.
With the debugger build, captures file-open (`INT 21h`) activity and the
disc-check behavior into `build/traces/`.

## Reading the reports

Each stage writes both `.json` (for scripts) and `.md` (for humans) into
`build/reports/`. Start with `inventory.md` to see what the disc contains,
then `binaries.md` to know what we're disassembling.

## Reproducibility

- The pipeline is deterministic given the same image.
- `scripts/check_env.py` gates on tool versions from `config/rules.yaml`.
- `iso.sha256` pins the expected image so a substituted or corrupted file is
  caught before any analysis is wasted on it.
