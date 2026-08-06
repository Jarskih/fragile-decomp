---
title: Randomness and determinism
---

# Randomness and determinism

*Status: written from static analysis of the game's code. One conclusion is
not yet confirmed in a live run — it is marked (?) in "A new game" and
explained in the Open question at the end.*

The game describes itself as set in "an ever-changing, randomly generated
universe". The description splits neatly in two, and both halves are true of
different things: the *universe* is generated, reproducibly, from seeds, while
the *ever-changing* part is the chance stream described next.

## Two streams of chance

The game keeps two independent streams of random numbers and never lets them
mix:

- The **universe stream** decides the galaxies, their asteroids, their
  surfaces and their ores. It is deliberately reproducible.
- The **chance stream** is seeded from the computer's clock each time the game
  is launched, so it is different on every run. It drives the events of play —
  the positioning and encounters that make a session feel alive.

The independence works both ways: the dice-rolls of play can never perturb the
layout of the universe, and generating a new galaxy can never affect the
chances of what happens next.

## A galaxy is its seed

Every galaxy is grown from a single starting number. That number is simply the
next draw of the universe stream at the moment the galaxy is created — no
galaxy name and no player input goes into it. Given the same number, the game
produces the same galaxy, down to the last detail.

Generation works the random stream on a private copy and puts it back exactly
where it was. Growing a galaxy therefore neither consumes nor disturbs the
live stream that the rest of the game draws from.

## A new game

At the start of a new game the universe stream is wound to a fixed starting
value before the first galaxies are made, so the initial universe is expected
to be the same on every new game — the same galaxies in the same places (?).

The settings change what gets generated, though. The options are **arena
size** (Small / Medium / Large), **asteroid density** (Standard / High) and
**atmosphere** (Peaceful / Neutral / Aggressive), so the above holds within
one choice of settings, not across different ones.

As play goes on, more galaxies appear — scouts report new asteroids, new
discoveries happen. Those are drawn from the same deterministic stream, so the
growing universe follows the same rules as the start.

## Saving never re-rolls

When you save, the game records where the universe stream currently stands,
and loading a saved game restores that position. A game resumed from a save
therefore continues its run of chance exactly where it left off — nothing is
re-rolled or scrambled.

## Reproducing the generator exactly

For a reimplementation that must produce the same universe from the same
starting number, the exact arithmetic matters. Combined with the private-copy
discipline described under "A galaxy is its seed", these details pin the
sequence down completely:

- Each draw advances a 32-bit counter by multiplying it by **69069**
  (arithmetic modulo 2^32).
- A draw "in the range 0..N-1" is the upper part of the product of the counter
  and N.
- Seeding maps any input to an odd, non-zero counter value, which guarantees
  the sequence never gets stuck and does not repeat until it has cycled
  through its full length.
- The two streams are the same arithmetic on two separate counters.

## Open question

The fixed starting value at the start of a new game is inferred from the code,
not observed. Whether the path the game takes for **New Game** (as opposed to
**Custom Game** or a **Preset Game**) actually reaches it has not been
confirmed in a live run. Until that settles, treat the conclusion marked (?)
above as likely but unverified — the rest of this page does not depend on it.
