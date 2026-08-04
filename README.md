# OpenFA — Open Fragile Allegiance

A faithful, from-scratch recreation of the 1996 DOS game **Fragile Allegiance**
(Gremlin Interactive / Cajji Software). The rebuilt game will run on a modern
framework while reusing the original art. To get the mechanics exactly right, we
first **decompile the original game** and document its behavior.

> **Legal note.** The original game is copyright-protected. This repository
> contains **only our own work**: pipeline scripts, configuration, and written
> analysis notes. No original game files and no decompiled output are ever
> committed. You must own a copy of the game (or its image) to run this
> pipeline locally; it stays in the gitignored `iso/` and `build/` trees.

## How the project works

The long first phase is a scripted, reproducible **reverse-engineering
pipeline**. Starting from the original CD image, the pipeline extracts,
inventories, disassembles, and traces the game, producing:

- machine-readable reports under `build/reports/` (gitignored),
- decompiled output under `build/decomp/` (gitignored),
- **written analysis notes** under `docs/mechanics/` and `docs/dataformats/`
  (committed — these are our conclusions, written by us).

The notes are the deliverable: they describe the game's exact mechanics
(economy, diplomacy, AI, blueprints, combat) so the modern rebuild can match
them.

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

## Repository layout

```
AGENTS.md            standing rules for every session
Makefile             pipeline orchestration
iso.sha256           provenance manifest (hashes of the expected image)
scripts/             00..08 pipeline stages + check_env.py
config/              rules.yaml, Ghidra scripts, DOSBox config template
docs/                INSTALL.md, pipeline.md, mechanics/, dataformats/
iso/                 (gitignored) your copy of the original image
build/               (gitignored) all derived artifacts
```

## License

Our committed work (scripts, configs, docs) is MIT — see `LICENSE.md`.
This license does **not** cover the original game in any way.
