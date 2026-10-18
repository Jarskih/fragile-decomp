---
title: Ship-to-ship combat
---

# Ship-to-ship combat

*Status: **mostly unresolved.** The hardware a ship carries (hardpoint items,
armour, shields) is read from the game's data (**[code]**) and the retreat rule
is confirmed. How a hardpoint weapon actually damages another ship has **not**
been decoded: an earlier version of this page described "automatic hits inside a
forward arc" — that was taken from the missile warhead code, which sweeps
buildings, not ships, and has been withdrawn. Text-only claims are marked
**[text]**.*

## What is known

- Every craft has a number of **hardpoints**, each holding one weapon or defensive
  item (prices and stats on [Vehicles](vehicles.md)).
- The ship-to-ship weapons are the **Laser**, **Photon Cannon**, **Plasma Cannon**,
  **Ion Cannon**, **Disruptor**, **Napalm Orb**, **Chaos Bomb** and **Vortex
  Mine**. The defensive items are the **Deflector**, **Static Inducer**, **Warp
  Generator** and the **Shield** series.
- Every craft has **armour points**. A **Shield** fitted to a hardpoint adds its
  bonus (x10 to x50 = +10 to +50) to the craft's armour; the displayed armour is
  base plus bonuses. A craft whose armour reaches zero is destroyed
  **(inferred from the displayed stat; the damage application is not decoded)**.
- Item effects **[text]**: the Deflector deflects most energy attacks and works
  with shields; the Static Inducer's pulse leaves hostile craft unable to attack or
  move while it lasts, with friendly craft protected; the Warp Generator makes the
  ship briefly invulnerable at intervals.
- A fleet holds up to four ships and each day compares its damage with its
  **retreat threshold** (see [Vehicles](vehicles.md)).
- Fleets and ships identify themselves as hostile only toward other owners; the
  firing code does not shoot at its own side.

## What is not known

- **There is no per-weapon damage, range or rate-of-fire table.** The game's data
  has prices and armour bonuses for the hardpoint items and three internal rating
  figures per item used by the AI to value targets, but no damage number. Whether
  damage, range and reload are constants in the unrecovered ship-combat code, or
  implicit, is open.
- The ordering "Laser < Plasma < Photon" for turrets, the Photon Turret's longer
  "optimised range", and the Turret Optimizer blueprint doubling turret damage are
  stated only in the game's text **[text]**.
- Whether colony turrets damage ships with the same rules as hardpoint weapons.
- Weapon slot re-arm times: an earlier note quoted fire delays of 15, 40, 20, 30
  and 40 ticks; those belong to a message cooldown and to the colony-event table,
  not to weapons, and should not be used.

A remake that wants working ship-to-ship combat therefore has to choose its own
damage, range and rate-of-fire numbers; the only fixed anchors are the item
prices, armour bonuses, craft armour, speeds and hardpoint counts listed on the
[Vehicles](vehicles.md) page.

## Bombardment is a separate system

Attacks on an asteroid use missiles, not the weapons above. The targeting dialog
shows a **Strike chance** — the real probability that the missile reaches the
target, a function of distance only (with the Missile Guidance System extending
it). Once there, the warhead damages the buildings on the surface. See
[Missiles and how they are fired](missiles.md). The number the fleet panel calls
**Strike Rate** is this same distance estimate, not a per-shot die roll between
ships.

*Related: [Vehicles](vehicles.md) — hardpoints, fleets and the craft roster;
[Missiles and how they are fired](missiles.md) — ship-to-asteroid attack;
[Buildings](buildings.md) — turret rows.*
