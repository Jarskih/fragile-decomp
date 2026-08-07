---
title: Ship-to-ship combat
---

# Ship-to-ship combat

*Status: the firing machinery (hardpoint slots, ammunition, fire delays) is
confirmed from the binary. The accuracy calculation — what a hit depends on —
has **not** been read out of the game yet: the per-ship and per-weapon
numbers the game uses exist only in memory at runtime and are marked (?).*

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

A hit is not settled by one simple roll (?). The game reads a per-ship
**Strike Rate** (shown on each ship in the fleet panel) and applies it to
the firing ship's shots — a ship with a higher Strike Rate lands a higher
share of its shots. One blueprint promises a **25% increase in strike
accuracy**, which implies the rate is modified by equipment.

Two things about the hit calculation are known from the binary but not yet
confirmed against the running game (?):

- the ship's aim depends on its **heading relative to the target**: shots
  at targets off to the side miss more often than shots straight ahead;
- each fired shot carries a small random **spread**, so identical shots do
  not fly exactly the same.

For beam-style weapons the game is believed to resolve hits by **arc**:
everything within the weapon's range and inside the front arc of the firing
ship is hit, without a second roll. The exact range and arc of each weapon
are per-type numbers that have not been read out of the game yet (?).

## Armor and destruction

Every craft has a number of **armor points**. A hit subtracts the weapon's
damage from the target's armor; a craft whose armor reaches zero is
destroyed. Armor can be increased by fitting a **Shield** to a hardpoint —
a Shield x40 adds 40 armor points, a Shield x50 adds 50 — or by the larger
shield, which makes a ship "almost (but not quite) invulnerable to attack".

## Bombardment is a separate system

Attacks on an asteroid use missiles, not the weapons above. The targeting
dialog shows a **Strike chance** (a percentage) for the selected missile
type, and the expected share of missiles that will hit is part of the
planning display. See [Missiles and how they are fired](missiles.md).

*Related: [Vehicles](vehicles.md) — hardpoints, fleets and the craft
roster; [Missiles and how they are fired](missiles.md) — ship-to-asteroid
attack.*
