# fragile-decomp — Fragile Allegiance decompilation

The **decompilation and analysis** of the 1996 DOS game **Fragile Allegiance**
(Gremlin Interactive / Cajji Software). The goal is to understand the game's
mechanics — technically and, most importantly, functionally — well enough that
the documented knowledge alone is sufficient to build a faithful
reimplementation of the game. The reimplementation itself is out of scope
here; this repository serves as its input.

> **Legal note.** The original game is copyright-protected. This repository
> contains **only our own work**: pipeline scripts, configuration, and written
> analysis notes. No original game files and no decompiled output are ever
> committed. You must own a copy of the game (or its image) to run this
> pipeline locally; it stays in the gitignored `iso/` and `build/` trees.

## How the project works

This repository runs a scripted, reproducible **reverse-engineering pipeline**.
Starting from the original CD image, the pipeline extracts, inventories,
disassembles, and traces the game, producing:

- machine-readable reports under `build/reports/` (gitignored),
- decompiled output under `build/decomp/` (gitignored),
- a curated named view of the decompiled code under `build/named/`
  (gitignored), produced from `config/ghidra/rename-map.json`,
- **written analysis notes** under `docs/mechanics/` and `docs/dataformats/`
  (committed — these are our conclusions, written by us).

The notes are the deliverable, in two tiers. Technical notes (`docs/mechanics/`,
`docs/dataformats/`) record the working analysis used for further reverse
engineering. **Functional write-ups describe the game's mechanics in plain
language** — how the economy, diplomacy, AI, blueprints, and combat behave —
completely enough that someone could reimplement them faithfully from the
documentation alone.

## Getting started

1. **Install the toolchain** — see `docs/INSTALL.md`. The pipeline scripts never
   install anything; the developer installs the required tools.
2. **Get the ISO** — either place your own image in `iso/`, or run
   `make download` to fetch the archive.org copy
   (identifier `Fragile_Allegiance_Interplay_Eng`).
3. **Check the environment** — `make check`.
4. **Run the pipeline** — `make all`.

## Rules of the road

These are enforced structurally (`.gitignore`) and persisted in `AGENTS.md`:

1. Never commit original game files.
2. Never commit decompiled files.
3. Everything is scripted (`scripts/`).
4. The pipeline is reproducible (verified against `iso.sha256`).
5. Agents never install software; developers do (see `docs/INSTALL.md`).
6. Only our work gets committed.
7. Record mistakes immediately (never let a stale note outlive an overturned finding).

## Repository layout

```
AGENTS.md            standing rules for every session
Makefile             pipeline orchestration
iso.sha256           provenance manifest (hashes of the expected image)
scripts/             00..11 pipeline stages + check_env.py
config/              rules.yaml, Ghidra scripts, DOSBox config template
docs/                INSTALL.md, pipeline.md, mechanics/, dataformats/
iso/                 (gitignored) your copy of the original image
build/               (gitignored) all derived artifacts
```

## License

Our committed work (scripts, configs, docs) is MIT — see `LICENSE.md`.
This license does **not** cover the original game in any way.
