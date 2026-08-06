---
title: Asteroids and how they are born
---

# Asteroids and how they are born

*Status: written from static analysis of the game's generator. Everything in
this page is read directly from the code except the per-ore numbers, which come
from a value table that could not be recovered from the shipped binary — those
claims are marked (?) and no concrete numbers are given for them. For the
arithmetic of the two dice streams (draws in a range, seeding, the private-copy
discipline), see [Randomness and determinism](randomness.md).*

The game sets its action in "an ever-changing, randomly generated universe".
That universe is a map of **sectors** — the "Fragmented Sectors" the game's
fiction names — and sitting in those sectors are the **asteroids**: the worlds
you prospect, mine and colonise. The game calls no level of this hierarchy a
galaxy; that word appears only in the description of a drink. This page gives
the exact rules by which an asteroid comes into being, in the order the game
performs them.

## Creation: size, surface, seed

Creating an asteroid performs the following draws, in this order, all from the
live deterministic stream:

1. **Size class.** One draw in 0..4, mapped to class **4..8** — five classes,
   small to large. The class sets how large the asteroid is drawn on the
   sector map.
2. **Surface width.** One draw of a coin, uniformly 0 or 1, combined as

   ```
   width = 2 * (12 + floor((class - 4) * 3 / 5) + coin) + 1
   ```

   The width is therefore always **odd**, and each class permits exactly two
   values, differing by 2, each with probability 1/2:

   | class | width |
   |-------|-------|
   | 4, 5  | 25 or 27 |
   | 6, 7  | 27 or 29 |
   | 8     | 29 or 31 |

   Classes 4 and 5 share a range, as do 6 and 7; moving up two classes shifts
   both possible widths by 2. The width is the asteroid's surface size: the
   number of cells across the middle of its diamond-shaped surface grid
   (roughly half of width² buildable cells). Size class and surface are
   therefore linked — a larger class draws a larger blob on the sector map
   *and* a wider surface. Note the width is drawn **before** the seed, so it
   is never a function of the seed.
3. **Seed.** Two draws in 0..65535 packed into one 32-bit number. This is the
   number the game later rebuilds the asteroid's content from. Nothing
   player-entered ever goes into it.

All three steps consume the live stream and none of them reads the clock. The
home asteroid is created immediately after the stream has been reset to its
fixed starting value, so its class, width and seed — and the ore rolls below —
are identical on every new game. Asteroids created later draw from wherever the
stream has reached; those too are deterministic, since only deterministic
draws ever advance this stream.

## Ore: what an asteroid is born with

The game tracks **ten kinds of ore**. Its own text names exactly ten (Barium,
Bytanium, Crystalite, Dragonium, Asteros, Korellium, Nexos, Quazinc, Selenium,
Traxium), which is the count the generator uses, though the pairing of names to
the generator's ten slots is not yet confirmed (?).

At creation, every asteroid receives an amount for each kind *k*, rolled as:

```
u  = draw in 0..99
if u < T_k:      amount = L_k + draw in 0..(H_k - L_k)     # rich: uniform in [L_k, H_k]
else:            amount = 1 + draw in 0..(floor(H_k / 20) - 1)   # poor: uniform in 1..floor(H_k / 20)
```

where *T_k*, *L_k*, *H_k* are per-kind constants. The distribution shape:

- **Rich vs poor** is a single Bernoulli test: the rich branch fires with
  probability *T_k*/100, clamped to the unit interval. The threshold is a
  signed 16-bit value and is not restricted to 0..100, so the structure
  deliberately allows a kind to be **always rich** (T_k ≥ 100) or **never
  rich** (T_k ≤ 0).
- **Rich amounts** are uniform over the kind's full band [L_k, H_k]
  (H_k − L_k + 1 equally likely values).
- **Poor amounts** are uniform over 1..⌊H_k/20⌋ — at most one twentieth of the
  kind's ceiling, never 0.
- **Two of the ten kinds are exempt**: their amount is always exactly 0. No
  freshly generated asteroid ever holds them (?).

The concrete per-kind values of T_k, L_k, H_k live in a table whose contents
could not be recovered from the binary (?); this page therefore gives the shape
of the roll exactly, but withholds numbers rather than inventing them.

## The asteroid's dominant ore

After the ten amounts are rolled, the generator marks the asteroid's single
dominant kind: the one maximising

```
amount_k * 256 / H_k      (integer division; ties go to the earlier kind)
```

i.e. the amount **relative to that kind's ceiling**, not the raw amount. An
asteroid holding a modest quantity of a low-ceiling ore can be "best at" that
ore while another kind sits higher in absolute units. Ties are resolved to the
kind with the lower slot.

This is a creation-time decision. The ten amounts and the dominant kind are
fixed when the asteroid is created.

## Rebuilding an asteroid from its seed

When the game needs an asteroid's content again, it rebuilds it from the
asteroid's 32-bit seed. The rebuild runs all of its draws against a **private
copy** of the deterministic stream and hands the stream back where it was, so
it never consumes or perturbs live play. Given the same seed, the rebuild is
identical.

The rebuild covers the asteroid's **surface** and its **seeded visual
backdrop**. It does **not** re-run the ore roll: that routine has a single call
site, at creation, and the rebuild never reaches it. Ore amounts and the
dominant kind therefore stay as fixed at creation, while the surface and
backdrop are pure functions of the seed.

## Placing an asteroid in a sector

Creation and the ore roll give each asteroid its nature; a later, separate step
assigns its position. The asteroid is placed in a free slot of the sector
grid — one asteroid per slot — and asteroids already placed are skipped, so no
two asteroids ever share a slot. Placement for newly discovered asteroids is
biased towards the player's own position on the map.

## What the settings change

Arena size and asteroid density are the two knobs that alter what gets
generated: the game's own text describes a small arena as "limited" and packed.
The exact mapping of the settings onto the sector map's extent, the surface
classes above, the ore rolls or the seeded content has not yet been traced, so
nothing concrete is claimed here (?).

## Open questions

- The per-kind threshold and band (T_k, L_k, H_k) could not be recovered from
  the binary; no numeric instantiation of the rolls above is possible until it
  is (?).
- Which two kinds are the always-zero pair, and which kind a given asteroid is
  "best at", follow from that table and are likewise pending (?).
- How arena size and asteroid density steer the sector map's extent, the
  surface classes, ore rolls and seeded content (?).
- Whether the slot grid of the placement step is the same as the map of
  sectors the game draws and names (the two are the same size in the code, but
  the identity is not yet confirmed) (?).
