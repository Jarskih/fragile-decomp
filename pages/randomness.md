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

- The **universe stream** decides the asteroids — their surfaces and their
  ores — and the sector map they sit in. It is deliberately reproducible.
- The **chance stream** is seeded from the computer's clock each time the game
  is launched, so it is different on every run. It drives the events of play —
  the positioning and encounters that make a session feel alive.

The independence works both ways: the dice-rolls of play can never perturb the
layout of the universe, and generating a new asteroid can never affect the
chances of what happens next.

## An asteroid is its seed

Every asteroid is created from a single starting number drawn from the universe
stream — no asteroid name and no player input goes into it. When the game needs
an asteroid's content again, it rebuilds the asteroid's surface and its seeded
visual backdrop from that number, on a private copy of the stream that is put
back exactly where it was: **rebuilding** an asteroid neither consumes nor
disturbs the live stream, and given the same number the rebuild is identical.

Two things are deliberately *not* part of that rebuild, and are fixed once, at
creation, by draws against the live stream:

- the asteroid's **surface width** (how large its surface grid is), which is
  rolled before the seed is drawn, and
- the **amounts of ore** it is born with, which the generator rolls straight
  after the seed and never re-rolls.

This does not break reproducibility at the start of a new game: the stream is
reset to its fixed starting value first, so creation itself runs against a known
state, and the whole initial universe comes out the same on every new game.

## A new game

At the start of a new game the universe stream is wound to a fixed starting
value before the first asteroid is made. That first asteroid — the **home
world** — is therefore identical on every new game: same surface, same ore, and
its own 32-bit seed, which the game remembers. The stream keeps its known
position from there, so everything drawn later is also the same *given the same
sequence of draws* (?).

The settings change what gets generated, though. The options are **arena
size** (Small / Medium / Large), **asteroid density** (Standard / High) and
**atmosphere** (Peaceful / Neutral / Aggressive), so the above holds within
one choice of settings, not across different ones.

As play goes on, the field keeps changing — the game tops the number of
asteroids up toward a ceiling set by the arena-size and density settings by
spawning replacements along the map's outer frame (see [Asteroids and how they
are born](asteroids.md)). Those placements all draw from the same deterministic
stream, so a fully played-out run follows the same rules as the start.

## Saving never re-rolls

When you save, the game records where the universe stream currently stands,
and loading a saved game restores that position. A game resumed from a save
therefore continues its run of chance exactly where it left off — nothing is
re-rolled or scrambled.

## Reproducing the generator exactly

For a reimplementation that must produce the same universe from the same
starting number, the exact arithmetic matters. Combined with the private-copy
discipline described under "An asteroid is its seed", these details pin the
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
