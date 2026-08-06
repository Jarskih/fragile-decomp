---
title: fragile-decomp
---

# fragile-decomp

**Decompilation &amp; analysis of *Fragile Allegiance***
(Gremlin Interactive / Cajji Software, 1996) — **work in progress**.

A scripted, reproducible reverse-engineering pipeline whose goal is to
understand how the game works — technically *and* functionally — well enough
that the documented knowledge alone could support a faithful reimplementation.
The reimplementation itself is out of scope here.

## Status

- Pipeline stages 00–11 run against the original CD image (extract, inventory,
  Ghidra disassembly, runtime traces).
- Data-format work underway: DOS/4G flat image, container formats, string dumps.
- Functional descriptions are being written from the technical analysis and
  published on this site as they mature.
- Notes are corrected whenever a claim is overturned — nothing here outlives
  an overturned finding.

## Functional documentation

This site publishes only the functional descriptions — the game's mechanics
written in plain, in-game language. They are the primary deliverable of the
project.

- [Randomness and determinism](randomness.md) — the two streams of chance,
  how the universe is generated, and what a reimplementation must reproduce.

The technical analysis (addresses, disassembly references, open questions) is
intentionally **not** published here; it stays in the repository for
developers and agents.

## Legal note

*Fragile Allegiance* is copyright-protected, and its copyright is not ours.
This project contains **no original game files** and no decompiled output; you
must own a copy of the game to run the pipeline locally. Our own work (scripts,
config, docs) is MIT-licensed.

## Links

- Source repository: <https://github.com/Jarige/fragile-decomp>
- License (our work only): [MIT](https://github.com/Jarige/fragile-decomp/blob/master/LICENSE.md)
