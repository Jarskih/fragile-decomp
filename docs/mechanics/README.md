# mechanics — notes on the original game's exact mechanics

This directory collects **our own written analysis** of how the game works, so
that a faithful reimplementation can be built from the documentation alone.
This is the primary deliverable of the decompilation phase.

## What goes here

Precise, evidence-backed descriptions of gameplay mechanics:

- economy: ore values, prices, production rates, upkeep, taxes
- construction: build times, costs, placement rules
- blueprints / technology: the 36 blueprints, prerequisites, effects
- diplomacy: race dispositions, treaties, offers, consequences
- AI: race behaviour, thresholds, aggression scaling
- combat: weapon stats, ship stats, damage model, targeting
- world: asteroid generation, resource distribution, fog of war

Each claim should cite its evidence: a `build/reports/` artifact, a trace
(`build/traces/`), a function address in `build/decomp/`, or an observed
in-game test (cross-check with the online playable copy).

## Conventions

One file per topic, each with a status line:

```
Status: hypothesis | probing | confirmed
Source: disassembly | trace | in-game test | manual
```

Values that are still uncertain are marked `?` and revisited later. Nothing in
this directory is copied game data — it is our reconstruction, in our words.
