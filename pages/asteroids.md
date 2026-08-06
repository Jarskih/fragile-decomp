---
title: Asteroids and how a galaxy is born
---

# Asteroids and how a galaxy is born

*Status: written from static analysis of the game's code. The general shape
below is solid; the parts that could not yet be recovered from the binary are
marked (?) and explained at the end. For the underlying dice streams, see
[Randomness and determinism](randomness.html).*

The game describes itself as set in "an ever-changing, randomly generated
universe", and it means it literally: the universe is made of **galaxies**, and
each galaxy is a cluster of **asteroids** — the worlds you prospect, mine,
colonise and defend. This page is about how a galaxy, and the asteroids inside
it, come to exist.

## A galaxy is a fixed cluster of asteroids

Every galaxy is generated to contain a fixed number of asteroids. The number is
always odd, and always between 25 and 31. It is decided by two things:

- the **size of the galaxy**, which narrows the range, and
- a **dice roll** at the moment the galaxy is created, which picks the exact
  number inside that range.

A larger galaxy is therefore packed with more asteroids, but two galaxies of
the same size will still differ from each other.

## Each asteroid is mostly poor, occasionally rich

Every asteroid carries a value for each of the ten kinds of ore the game
tracks. When the galaxy is born, each of those ten values is rolled for:

- Most of the time the asteroid is a **poor find**: the value comes out at
  roughly a twentieth of the most that kind of ore can ever be worth.
- Once in a while the roll falls in a **rich band**, and the asteroid is born
  holding a serious amount of that ore.
- Two of the ten kinds always start at nothing on any asteroid (?)

The game then looks at the ten results and quietly marks the single strongest
one — every asteroid ends up best known for one kind of ore, and that is the
kind the game leads you toward.

## The whole thing is reproducible

Nothing in the above depends on the clock or on player input. A galaxy is grown
from a single starting number taken from the universe's deterministic dice
stream, and every roll inside the growth is made against a private copy of that
stream. Given the same starting number, the same galaxy comes out, down to the
amounts of ore on every asteroid. (See [Randomness and
determinism](randomness.html) for how the streams work and how settings such as
**arena size** and **asteroid density** fit in.)

## Open questions

- The exact odds of the rich band and the exact amounts of ore it grants come
  from a value table that could not be recovered from the shipped binary — the
  table is not present in the game's data, and its contents are still a puzzle.
  Until that is solved, this page deliberately gives no exact numbers, only the
  shape of the roll (?)
- It is known *that* the settings change what gets generated, but the exact
  effect of **arena size** and **asteroid density** on the counts and values
  above is still being traced (?)
- Whether the asteroids of a galaxy are *placed* at specific positions by this
  generator — as opposed to being laid out by a later pass — is not yet
  established (?)
