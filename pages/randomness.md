---
title: Randomness and determinism
---

# Randomness and determinism

*Status: based on static analysis of the game's code. The conclusion that a
new game begins with the same universe is **unverified at runtime** — see the
open question at the end. Uncertain values are marked (?).*

The game describes itself as set in "an ever-changing, randomly generated
universe". That is true in a specific sense, and it is the key to how the
whole game behaves.

## Two separate streams of chance

The game keeps two independent streams of random numbers and never lets them
mix:

- One stream shapes the **universe**: it decides the galaxies, their
  asteroids, the surfaces, the moons and the ores. This stream is deliberately
  **reproducible**.
- The other stream drives **chance events during play** — the positioning and
  encounters that make each session feel alive. This stream is seeded from the
  computer's clock each time the game is launched, so it is different on every
  run.

Because the two are separate, the dice-rolls of combat and encounters can
never perturb the layout of the universe, and generating a new galaxy can
never affect the chances of what happens next in play.

## A galaxy is a seed

Every galaxy is grown from a single starting number. Given the same starting
number, the game produces the same galaxy — the same asteroids, surfaces,
ores and moons, down to the last detail. Nothing about the galaxy's name or
any player input goes into that number; it is simply the next roll of the
universe stream at the moment the galaxy is created.

This is what makes the universe *reproducible*: growing a galaxy runs the
random stream on a private copy, then puts it back exactly where it was.
Generating galaxies therefore neither consumes nor disturbs the live stream
that the rest of the game draws from.

## A new game

At the start of a new game the universe stream is wound to a fixed starting
value before the first galaxies are made. Current analysis therefore expects
the initial universe to be **the same on every new game** — the same galaxies
in the same places, with the same ores.

Two things qualify that statement:

- Whether the game always uses that fixed starting value (and not, say,
  something derived from the chosen game options) is still being confirmed in
  a live run. **This is currently unverified (?).**
- The new-game settings change what gets generated. The options include
  **universe size**, **arena size** (Small / Medium / Large), **asteroid
  density** (Low / Standard / High) and **atmosphere** (Peaceful / Neutral /
  Aggressive). Within the same settings the expectation is a fixed universe;
  across different settings, not.

As play goes on, more galaxies appear — scouts report new asteroids and new
discoveries happen. Those are rolled from the same deterministic stream, so
the universe continues to grow reproducibly.

## Chance is different every session

The in-game chance stream is seeded from the clock at launch, so the
encounters and placements that happen in one game will not repeat in the
next — even though the geography of the universe is (expected to be) fixed.
This is where the game's promise of an experience that "unfolds differently
with each new game" actually lives: the *events*, not the *places*.

## Saving never re-rolls

When you save, the game records where the universe stream currently stands,
and loading a saved game restores that position. A game resumed from a save
continues its run of chance exactly where it left off — nothing is re-rolled
and nothing is scrambled by saving or loading.

## Reproducing the generator exactly

For a reimplementation that must produce the same universe from the same
starting number, the exact arithmetic matters:

- Each draw advances a 32-bit counter by multiplying it by **69069**
  (arithmetic modulo 2^32).
- A draw "in the range 0..N-1" is the upper part of the product of the
  counter and N.
- Seeding maps any input to an odd, non-zero counter value, which guarantees
  the sequence can never get stuck and does not repeat until it has cycled
  through its full length.
- The universe stream is seeded and restored around galaxy generation, and is
  **never** seeded from the clock — only the chance stream is.

The two streams use the same arithmetic on two separate counters.

## Open question

The fixed starting value for a new game is inferred from the code; whether it
is actually on the path the game takes when you choose **New Game** (as
opposed to **Custom Game** or a **Preset Game**) has not yet been confirmed
in a live run. Until that is settled, treat "the initial universe is identical
on every new game" as **likely but unverified** — the rest of this page does
not depend on it.
