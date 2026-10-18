---
title: Missiles and how they are fired
---

# Missiles and how they are fired

*Status: prices, ores, the arrival probability, the flight rules and every
warhead's blast numbers are read from the game's code and data (**[code]**,
GOG retail build). Missile descriptions are the game's own words (**[text]**).
Items not yet resolved are marked **(?)**. This page replaces an earlier model
in which defenders "swept" incoming missiles; no such mechanic was found.*

## What a missile is

The game's weapons against asteroids are **missiles**: warheads built on a colony
and fired at another asteroid. A missile has two independent stages:

1. **Flight** — does it arrive? Decided by the **strike chance**, a function of
   distance (below).
2. **Impact** — a warhead effect applied to the **buildings on the target
   asteroid**, using numbers that depend on **which race launched it**.

There are thirteen kinds:

| missile | price (Cr) | ore (1 unit) | blueprint | text |
|---|--:|---|--:|---|
| Explosive | 800 | Selenium | start | a cheap conventional warhead |
| Area Explosive | 6,400 | Barium | start | larger area of destruction |
| Napalm | 5,000 | Quazinc | start | incendiary; melts most structures |
| Hellfire | 16,000 | Quazinc | start | spreads across the whole asteroid |
| Scatter | 15,000 | Selenium | start | splits into several explosives over the target |
| Vortex | 8,000 | Crystalite | start | an electrical storm that wanders and damages |
| Nuclear | 50,000 | Bytanium | 300,000 | destroys most structures and ships in orbit |
| Virus | 30,000 | Traxium | 350,000 | dissolves the asteroid, spreading |
| Anti-Virus | 10,000 | Barium | 90,000 | neutralises a virus and itself |
| Mega | 100,000 | Nexos | 500,000 | destroys an entire asteroid |
| Stasis | 40,000 | Korellium | 150,000 | freezes an asteroid for a time |
| Bug Hunter | black market | - | none | illegal anti-personnel virus missile, effective against the Artemia |
| Meat-Eater | black market | - | none | illegal; effective against the Achaeans, Braccatia and Terrans |

Bug Hunter and Meat-Eater have no building-side price; they are Trader stock at
reference prices of 55,000 and 95,000 Cr (see [Trade](trade.md)). Each missile
also has a small ore-quantity number (1 to 5) that does two jobs: it is the
amount of its ore counted into the missile's trade price (price = cost + that
quantity x the ore's current price), and an alien colony keeps building that
missile only while its stock is below the same number. Alien races build their own arsenals and five special alien-only
warheads (below).

## Where missiles live

Missiles are held in **Missile Silos** (10 of each type per silo **[text]**;
doubled by the Missile Bay Extension, 60,000 Cr). New missiles are produced from
the **Missiles** fund and the ore in the table; each step drains the fund and
production stops when it is empty. The Missile Control screen loads and fires
them: it refuses with plain messages when nothing is selected or the asteroid has
no silos. Ships carry their own ammunition (the fleet panel's "Missiles At").

## Strike chance: does the missile arrive?

The "Strike chance" in the targeting dialog and in the enemy launch report is the
missile's **real arrival probability**. At launch the missile is rolled once
(0 to 100): a roll at or below the chance means it flies to the target; a roll
above means it **expires part-way** (after about 10 to 40 ticks, well short of the
target). So the probability is exactly (chance + 1) / 101.

Distance is the 2-D straight-line distance between the launching and target
asteroids, each coordinate difference rounded down to whole units, then the
distance rounded down.

```
allowance = 32 units, or 64 with the Missile Guidance System (player empires only)
chance    = 100                                   if distance <= allowance
          = max(0, 100 - (distance - allowance) x 100 / 160)   otherwise (integer division)
```

- Your own asteroid is fixed at 100%.
- It falls about 1 point per 1.6 units, reaching **0 at 192 units** (224 with
  guidance). Guidance adds at most 20 points; the brochure's "+25%" is not a
  multiplier.
- Every missile kind uses the same chance. The Asteroid Tracker blueprint only
  enables the display on the targeting screen.
- **Miss behaviour**: a missed missile's lifetime is about
  `(three random draws below x + 32) / 3` ticks, where `x = (min(distance minus both
  asteroids' speeds, 160) - 32) / 3`. At distance 192 that is about 31 ticks; the
  flight needs distance/3 ticks, so a miss always expires before arriving.
- **Flight speed** is the same for all types: **3 map units per tick** (33 ticks
  for 100 units; 64 for 192). A missile arrives when it is within the target
  asteroid's radius.

| distance (units) | chance | with guidance |
|---|--:|--:|
| up to 33 | 100% | 100% |
| 34 | 99% | 100% |
| 48 | 90% | 100% |
| 64 | 80% | 100% |
| 80 | 70% | 90% |
| 96 | 60% | 80% |
| 112 | 50% | 70% |
| 128 | 40% | 60% |
| 144 | 30% | 50% |
| 160 | 20% | 40% |
| 176 | 10% | 30% |
| 192 | 0% | 20% |
| 208 | 0% | 10% |
| 224 and beyond | 0% | 0% |

## What a hit does: the warhead

When a missile arrives it applies its warhead to the **buildings** of the target
asteroid. Damage reduces a building's hit points (the HP column on
[Buildings](buildings.md)); a building at 0 or below is destroyed. If the asteroid
has a Screen Generator effect and the building sits under it, the damage is halved
(rounded up) **(inferred)**. **There is no accuracy roll at impact**: every
building inside the blast shape is hit once.

Distances are surface-grid cells. A "circle" hits every building whose centre is
within the radius of the impact cell; a "cone" is a wide front sector (about 225
degrees) with a full-circle core. The numbers below are for missiles launched by
the **player empires (races 1 to 8, identical)**.

| missile | warhead | damage and size | extra |
|---|---|---|---|
| Explosive | circle | 10 damage within 2 cells | |
| Area Explosive | circle | 10 damage within 3 cells | |
| Napalm | cone | 5 damage within 4 cells | burn: 1 HP per structure pass for 5 passes |
| Hellfire | cone | 5 damage within 5 cells | burn: 1 HP for 10 passes; 20% chance each pass to ignite a neighbour |
| Scatter | 25 bomblets 2 to 16 cells around the impact | each: 10 damage within 2 cells | |
| Vortex | random-walk storm | 2 HP per tick to the building under it | one short walker (4 to 12 ticks) plus one long (50 to 98 ticks); each tick a 4% chance of a successor; roughly 380 HP potential in total |
| Nuclear | big circle | 7, then 5 damage within 20 cells | burn like Hellfire; ships in orbit moved; radiation +4 |
| Virus | infection flag | timer 350 + 0 to 49 | marks the asteroid infected |
| Anti-Virus | cure flag | - | clears the infection; radiation +1 |
| Mega | destruction flag | - | destroys the asteroid |
| Stasis | hold timer | 50 to 74 units | blocks the asteroid's drift, AI actions and fleet launches while it runs |
| Bug Hunter | virus event on the target | - | a 25% chance records an incident against the attacker |
| Meat-Eater | virus event on the target | - | same |

A burning building loses HP once per daily structure pass, not per tick. So a
typical 10-damage Explosive destroys any building of 10 HP or less within 2 cells
(Solar Panel, Landing Pad) and leaves a 20-HP Mine at 10. Nuclear totals about 12
HP directly plus burn, so only buildings above about 22 HP survive.

### Differences by launching race

The per-race values (a missile uses the launching race's, not the victim's):

| launching race | blast damage | circle radii (cells) A / B | cone ranges (cells) A / B | Scatter bomblets | Stasis base | vortex successor % |
|---|--:|---|---|--:|--:|--:|
| 1 to 8 (players) | 10 | 2 / 3 | 4 / 5 | 25 | 50 | 4 |
| 9 Rigellian | 14 | 3 / 4 | 5 / 6 | 30 | 55 | 5 |
| 10 Braccatia | 10 | 2 / 3 | 4 / 5 | 25 | 45 | 4 |
| 11 Mikotaj | 8 | 2 / 3 | 3 / 4 | 23 | 35 | 3 |
| 12 Artemia | 11 | 2 / 4 | 4 / 5 | 26 | 55 | 4 |
| 13 Mauna | 12 | 3 / 4 | 5 / 6 | 28 | 65 | 5 |
| 14 Achaean | 6 | 2 / 2 | 3 / 4 | 20 | 25 | 3 |

(A applies to Explosive and Napalm, B to Area Explosive and Hellfire. The race
mapping of ids 9 to 14 follows the order of the alien building lists and is
plausible, not proven.) The Stasis timer is the base plus 0 to half of the base.

### Alien-only warheads

Each race from 10 to 14 has one special missile: a cone of 14 cells with 5 damage;
a 180-tick walker doing **120 damage** per tick; a circle of 10 cells with **120
damage**; an ore-stock drain plus a bomblet cloud; or the bomblet cloud alone
(cone sweeps of 5 damage). 120 damage kills any building. Their in-game names
(for example Detonator, Maxi-det, Flare, Viral Repair, Temporal Stasis) are not
mapped to these ids **(?)**.

## How a firing ship behaves

A ship or fleet ordered to attack:

- **Approaches** the target asteroid or fleet, turning as it flies, until within
  firing range.
- Fires only at a genuinely hostile target (not at its own owner; friendly or
  neutral targets are not attacked **(?)**).
- Once in range it **fires repeatedly while approaching**: each tick has a **30%
  chance** of launching, and each launch consumes **one missile** from the ship's
  hold. A shot is taken only when the target lies within an angular window ahead
  of the ship; outside it the tick is skipped, and a target that is too far off
  the nose drops the current aim.
- **Aims** at one object of the target asteroid and steers the shot slightly toward
  it every tick (homing).
- **Stops firing** when the fleet is very close to the target. The fleet's retreat
  threshold decides when it breaks off earlier (see [Vehicles](vehicles.md)).
- The 30% is a rate-of-fire gate, not a hit chance. (An earlier claim of a
  "15 or 40 tick" fire delay was a message cooldown and has been dropped.)

## Defence against missiles

- A **Screen Generator** reduces building damage (above).
- The **Anti-Missile Pod** is described by the text as knocking out incoming
  warheads and getting better with more pods per asteroid. **No code reading the
  pod count was found**, so its actual effect is unknown **(?)**. A remake
  designer should treat pods as a design decision rather than a measured rule.
- Distance is the only thing that lowers arrival; the target's defences do not
  change the displayed or real strike chance.

## Hostility cost

Each shot also adds a **weight** to the hostility between the races (Explosive 1,
Area Explosive 3, Napalm 5, Hellfire 7, Scatter 25, Vortex 20, Nuclear 100, Virus
100, Anti-Virus 0, Mega 255, Stasis 50, Bug Hunter and Meat-Eater 150): see
[Aliens and diplomacy](aliens-and-diplomacy.md). When an alien's accumulated
outgoing weight against a human exceeds a threshold, each arriving Vortex has a
1-in-200 chance to become a Meat-Eater **(inferred)**.

## Open questions

- The Anti-Missile Pod effect; the unit (days?) of the Virus and Stasis timers.
- The impact-cell choice and the cone orientation of Napalm and Hellfire.
- The names of the alien special warheads.

*Related: [Vehicles](vehicles.md) — the ships that carry and fire missiles;
[Ship-to-ship combat](ship-combat.md); [Buildings](buildings.md) — hit points;
[Trade](trade.md); [Ores and mining](ore-and-mining.md).*
