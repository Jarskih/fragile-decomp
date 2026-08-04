# AGENTS.md — Standing instructions for every session working on OpenFA

This file is the authoritative list of rules for this repository. Read it before
doing anything. It is load-bearing: future sessions (human or agent) must follow
it exactly.

## Project goal

Recreate the 1996 DOS game **Fragile Allegiance** (Gremlin Interactive / Cajji
Software). The rebuilt game will use a modern framework but the original art.
The long first phase is **decompilation**: we reverse-engineer the original
game's exact mechanics to be as faithful as possible.

The original game binary is copyright-protected. Everything we commit must be
unambiguously our own work: scripts, configuration, and written analysis notes.
Nothing derived from the game's copyrighted files may ever be committed.

## The rules

1. **Never commit original game files.**
   No ISO, no extracted files, no executables, no data files, no artwork, no
   audio. The gitignored `iso/` and `build/` trees are the only places original
   content may exist, and they are never `git add`ed.

2. **Never commit decompiled files.**
   Disassembly, decompiled C, Ghidra projects, symbol dumps, string dumps, and
   byte-level extracts of original files all count. They live under `build/`
   only (gitignored).

3. **Everything is scripted.**
   The path from ISO → decompilation runs through scripts under `scripts/`.
   Do not run ad-hoc manual pipelines; add or fix a script instead.

4. **Reproducible.**
   Given the same ISO, the pipeline must produce the same derived result.
   Scripts are deterministic, write to `build/`, and verify the ISO against the
   committed `iso.sha256` provenance manifest.

5. **The agent never installs software.**
   Missing tools are detected by `scripts/check_env.py`, which points the user
   to `docs/INSTALL.md`. The developer performs all installations. Agents must
   not `apt install`, `pip install`, download toolchains, or otherwise mutate
   the system.

6. **Only our work gets committed.**
   Committed content is limited to: scripts (`scripts/`), configuration
   (`config/`), documentation we write (`docs/`, `README.md`), the provenance
   manifest (`iso.sha256`: hashes and file names only — no contents), and
   `Makefile`/`.gitignore`/etc.

## What is committed vs. what is not

| Committed (ours)                        | Never committed (theirs/derived)                |
|-----------------------------------------|-------------------------------------------------|
| `scripts/*` pipeline scripts            | `iso/**` the game image(s)                      |
| `config/**` templates & Ghidra scripts  | `build/**` extracted files, decompiled C/asm,   |
| `docs/**` written analysis + manuals    |   symbol/string dumps, Ghidra projects, traces, |
| `iso.sha256` hashes + file names        |   reports                                       |
| `Makefile`, `.gitignore`, `README`      | any stray copies of game files elsewhere        |

## Commands

- `make check` — verify installed toolchain against `config/rules.yaml`
- `make all` — run the full pipeline (download → verify → extract → inventory
  → binary-info → extract-flat → flat-analyze → disassemble → strings →
  dat-survey → trace)
- `make clean` — wipe `build/` (derived artifacts only; never touches `iso/`)
- Individual stages: `make download verify extract inventory binary-info
  extract-flat flat-analyze disassemble strings dat-survey trace`

## Pipeline overview

See `docs/pipeline.md` for detail. Outputs (reports) land in `build/reports/`;
decompiled output in `build/decomp/`; traces in `build/traces/`.

Stage numbering in `scripts/`:
- `00` download the ISO from archive.org (optional)
- `01` verify the image + record track table
- `02` extract the ISO9660 data session
- `03` inventory files (name/size/hash/magic)
- `04` classify executables (16-bit vs 32-bit DOS extender)
- `05` extract the DOS/4G-bound flat image from FRAGILE.EXE
- `06` analyse the flat image (entry candidates, code/data/string regions)
- `07` Ghidra headless import/analyze/export
- `08` strings sweep
- `09` data-file format survey (magic/entropy/header probes)
- `10` DOSBox(-X) runtime tracing (INT 21h/file-open log, disc check)

Analysis conclusions are written by us into `docs/dataformats/` and
`docs/mechanics/`; raw decompiled output stays in `build/`.
