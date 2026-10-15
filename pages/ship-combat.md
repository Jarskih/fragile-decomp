---
title: Ship-to-ship combat
---

# Ship-to-ship combat

*Status: the hit resolution is now read out of the game's code in both
builds. What remains unknown (marked ?) are the per-race numbers — weapon
ranges, strike rates and shot speeds exist only in memory at runtime.*

## How a ship fights

A ship fires the weapons attached to its **hardpoints**. Each weapon on a
ship is controlled by its own fire-control slot:

- a weapon can only fire again after its **fire delay** has elapsed —
  each weapon type has its own delay between shots;
- every shot draws **ammunition** from the colony's stores: weapons are
  grouped into a few ammunition categories, and a weapon that belongs to a
  category with no stock left cannot fire;
- some weapon types are flagged as unavailable and never fire;
- a second firing mode is available to some slots and fires immediately,
  consuming ammunition in one go.

The ship-to-ship weapons are the **Laser**, **Photon Cannon**,
**Plasma Cannon**, **Ion Cannon**, **Disruptor**, **Napalm Orb**,
**Chaos Bomb** and **Vortex Mine**. The defensive hardpoints —
**Deflector**, **Static Inducer**, **Warp Generator** and the **Shield**
series — are covered on the [Vehicles](vehicles.md) page.

## What determines a hit

A hardpoint weapon hit is **not a random roll**. A firing ship simply
covers an area in front of it:

- every target within the weapon's **range** is hit automatically;
- for directional weapons the shot only reaches targets inside the firing
  ship's forward arc — a target that is not roughly in front of the ship
  cannot be hit;
- targets very close to the ship are hit no matter which way the weapon
  faces.

So for a dogfight the aim is positional: get the enemy ship inside the
weapon's range and in front of your ship, and the shot connects. The exact
range of each weapon and the size of the forward arc are per-race numbers
that exist only in memory at runtime (?), so they have not been read out
yet.

### What this means in practice

- **A ship held in front of you never gets lucky**: while the enemy stays
  inside the weapon's reach and in your forward arc, *every* shot that
  fires connects. There is no die roll that can turn a well-aimed shot into
  a miss.
- **The rear is a blind cone.** The forward arc covers everything except a
  sector directly behind the firing ship (about three eighths of the full
  circle). An enemy directly behind you cannot be hit at all, no matter how
  close or how weak — flying around behind an enemy ship is therefore a
  genuine and safe tactic, and being tailed by one is how you lose.
- **Getting too close removes the facing protection.** A target right on
  top of the firing ship is hit regardless of which way the weapon points —
  a ship that tries to hide by sitting inside the enemy's rear cone gives
  that protection up.
- **Dogfights are won by position, not by odds.** Two identical ships do
  not trade misses back and forth; the one that keeps the other in its arc
  and in range lands every shot, and the loser's escape is to *move* — fly
  behind the enemy or out of its range — rather than to hope a shot goes
  wide.
- **The arc sweep is also the anti-missile defence.** The same rule that
  puts ships in the line of fire puts incoming missiles there too:
  defenders cover their forward arc, and anything that enters it —
  including missiles on their way to the asteroid — is hit without a
  second roll, taking damage until its armor runs out (see
  [Missiles](missiles.md)).

The number the game calls **Strike Rate** is different: it is a distance
estimate shown for missile attacks, not a per-shot die roll. See
[Missiles and how they are fired](missiles.md).

## Armor and destruction

Every craft has a number of **armor points**. A hit subtracts the weapon's
damage from the target's armor; a craft whose armor reaches zero is
destroyed. Armor can be increased by fitting a **Shield** to a hardpoint —
a Shield x40 adds 40 armor points, a Shield x50 adds 50 — or by the larger
shield, which makes a ship "almost (but not quite) invulnerable to attack".

## Bombardment is a separate system

Attacks on an asteroid use missiles, not the weapons above. The targeting
dialog shows a **Strike chance** (a percentage) for the chosen target — a
distance-based estimate of the share of missiles that will reach it, not a
property of the missile type. See [Missiles and how they are
fired](missiles.md).

*Related: [Vehicles](vehicles.md) — hardpoints, fleets and the craft
roster; [Missiles and how they are fired](missiles.md) — ship-to-asteroid
attack.*
