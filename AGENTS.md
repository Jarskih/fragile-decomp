# AGENTS.md — Standing instructions for every session working on fragile-decomp

This file is the authoritative list of rules for this repository. Read it before
doing anything. It is load-bearing: future sessions (human or agent) must follow
it exactly.

## Project goal

This repository's scope is the **decompilation and analysis** of the 1996 DOS
game **Fragile Allegiance** (Gremlin Interactive / Cajji Software). Our aim is
to understand the game's mechanics — **technically and, most importantly,
functionally** — well enough that the documented knowledge alone is sufficient
to build a faithful reimplementation of the game. The reimplementation itself
is out of scope here and belongs in a separate repository; this repository
serves as its input. No game code is written or designed in this repository.

The original game binary is copyright-protected. Everything we commit must be
unambiguously our own work: scripts, configuration, and written analysis notes.
Nothing derived from the game's copyrighted files may ever be committed.

## The rules

1. **Never commit original game files.**
   No ISO, no extracted files, no executables, no data files, no artwork, no
   audio, no manual. The gitignored `iso/` and `build/` trees are the
   only places original content may exist, and they are never `git add`ed.

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

7. **Record mistakes immediately.**
   When analysis finds that an earlier conclusion was wrong or incomplete,
   correct the affected documentation right away, in the same session, instead
   of deferring the fix. Never let a stale note survive an overturned finding.

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
  dat-survey → trace → names)
- `make clean` — wipe `build/` (derived artifacts only; never touches `iso/`)
- Individual stages: `make download verify extract inventory binary-info
  extract-flat flat-analyze disassemble strings dat-survey trace names`

## Pipeline overview

See `docs/pipeline.md` for detail. Outputs (reports) land in `build/reports/`;
decompiled output in `build/decomp/`; named view in `build/named/`; traces in
`build/traces/`.

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
- `11` apply curated names from `config/ghidra/rename-map.json` to a copy of
  the decompiled C in `build/named/`

Analysis conclusions are written by us into `docs/dataformats/` and
`docs/mechanics/`; raw decompiled output stays in `build/`. Never edit the
Ghidra exports in `build/decomp/` in place — treat them as read-only and
encode any renaming in `config/ghidra/rename-map.json` via stage `11`.

## Documentation strategy: two tiers

Our documentation is written in two distinct tiers, because the audience for
it is twofold:

1. **Technical descriptions** — the working analysis used for further reverse
   engineering. These are the existing notes in `docs/mechanics/` and
   `docs/dataformats/`. They are allowed to (and expected to) reference
   addresses, variable names, register conventions, asm-level facts, and open
   questions. They are the source of truth; they are primarily for the agent
   and the developer to consult while decompiling.

2. **Functional descriptions** — explanations of how the game works, written
   in the language of the game, not of the binary: no variable names, no
   pointer/hex addresses, no Ghidra or disassembly references. They describe
   behaviour and mechanics ("how fast do ships accelerate", "what determines
   planet yields") completely enough that someone reading them alone could
   reimplement that mechanic faithfully. **These are the primary deliverable
   of this repository** — the functional knowledge is what the reimplementation
   repository will be built from.

Rules that follow from this:

- When we document a mechanic, the technical analysis lands in
  `docs/mechanics/` (or `docs/dataformats/`) first; a functional write-up for
  the same mechanic is a separate, later step, written from that analysis.
- Functional docs live in `pages/`, which is published to GitHub Pages (via
  `.github/workflows/pages.yml`). `docs/` is internal and never published —
  this is a structural guarantee, not a publishing discipline.
- Functional docs must be self-contained prose: no `FUN_0000…`, no `0x…`,
  no struct offsets, no register names. Sanitise away any internal detail
  that only makes sense inside the decompilation project.
- Nothing from `build/` is ever published; functional docs are plain prose and
  contain no derived game content.
- Functional docs use the game's own vocabulary, mined from the game's US-English
  text resources (the `_TEXT/AMERICAN.TXT`/`.SCR`/`.CDB` files under `build/iso/`).
  That is the authority for UI labels and terminology. Other language packs
  (e.g. `FRANCAIS.*`) are ignored — our content is English only. No OCR of a
  game manual is needed or performed.
- If a technical and a functional doc describe the same mechanic, they live in
  different files (or different sections) so that the technical detail never
  leaks into the functional text.
- A mechanic is not "done" until it has a functional description that stands
  on its own.
