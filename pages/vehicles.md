---
title: Vehicles
---

# Vehicles

*Status: the craft table (price, build time, armour, speed, hardpoints, ore) and
the hardpoint item prices are read from the game's data (**[code]**). Craft
descriptions, the fleet rules and the roles of the defensive items are the game's
own words (**[text]**). A few record fields are inferred (**?**), and the default
hardpoint loadouts and the attack/defence ratings the Ship Yards screen shows
exist only at run time.*

## What a vehicle is

All of the game's craft — the small fighters, the larger warships, the colony
ships, even the Spy Satellite and the Space Dock — are bought with the
**Vehicles** fund plus ore (see [Colony economy](colony-economy.md)). Two
buildings build them:

- the **Ship Yards** build the small craft: **Assault Fighter**, **Combat Eagle**
  and **Scoutship**;
- the **Orbital Space Dock** builds the larger craft — **Transporter**,
  **Destructor**, and the Sci-Tek blueprint ships. It is itself ordered through
  the Command Center, paid from the Vehicles fund like a craft, and only one may
  exist per asteroid.

A Weapons Factory and Ship Yards are required, plus the ores and money. The
blueprints for the Transporter and Destructor come from TetraCorp; the Terminator
(90,000), Fleet Battleship (150,000) and Command Cruiser (250,000) must be bought
from Sci-Tek. The Assault Fighter, Combat Eagle and Scoutship need no blueprint.
Finished craft appear beside the Dock and orbit until given orders.

Building takes the craft's **build days**, and an order can stall if the ore, the
Vehicles fund or the labour (Ship Yards need 8 staff) runs out. An order can be
cancelled only before construction has begun. A Ship Yard or Dock builds **3**
craft at a time; **Construction Droids** (80,000 Cr) raise it to **6** and cut the
build time by 25% (displayed time = days - floor(days/4)).

## The Terran craft

**[code]** Build time in days; speed in FN (the game's unit; what the letters mean
is not stated); range in map units; "ore" is the amount shown in the panel (the
ores match the game's ore-use text; whether the amounts are consumed per craft or
only gate the build is **(?)**).

| craft | price (Cr) | build days | armour | speed | hardpoints | range | ore |
|---|--:|--:|--:|--:|--:|--:|---|
| Assault Fighter | 6,000 | 20 | 20 | 4 | 1 | 160 | 2 Selenium, 2 Crystalite |
| Combat Eagle | 12,000 | 30 | 20 | 4 | 2 | 160 | 4 Selenium, 4 Crystalite |
| Scoutship | 3,000 | 20 | 5 | 3 | 1 | 192 | 4 Selenium, 2 Crystalite |
| Destructor | 15,000 | 48 | 40 | 2 | 3 | 160 | 8 Selenium, 6 Crystalite |
| Terminator | 34,000 | 60 | 50 | 2 | 4 | 160 | 8 Selenium, 2 Dragonium |
| Transporter | 24,000 | 100 | 40 | 2 | 2 | 192 | 6 Selenium, 1 Dragonium |
| Fleet Battleship | 60,000 | 80 | 70 | 2 | 6 | 160 | 8 Selenium, 6 Dragonium |
| Space Dock | 150,000 | 110 | 120 | 0 | 4 | 0 | 10 Bytanium, 15 Dragonium |
| Command Cruiser | 300,000 | 120 | 250 | 2 | 6 | 320 | 10 Barium, 18 Korellium |
| Spy Satellite | 10,000 | 16 | 1 | 4 | 0 | 320 | 2 Barium |

- The cost shown for a design is the hull price plus the prices of the fitted
  hardpoint items; the armour shown is the base armour plus the bonuses of fitted
  shields.
- The text agrees: the Terminator has four hardpoints and a top speed of 2 FN, the
  Fleet Battleship six and 2 FN, the Command Cruiser six.

## What the craft do **[text]**

- **Scoutship** — searches for new asteroids and performs a geosurvey
  ("prospect"). Its range is shown as a red circle when ordering; sent just beyond
  it, it can limp home on its Impulse Limp engines. It cannot report to home until
  it returns; the Long Range Transmitter (35,000 Cr) gives new small craft
  real-time contact.
- **Transporter** — colonises new asteroids, carries ore, and needs a Refueling
  Depot on the new colony to return home or start another.
- **Terminator** — four hardpoints, "greater armor than existing ships", an
  integral short-range rotary cannon, and a reputation for dog-fighting (T-15
  model, in Federal Marine service).
- **Fleet Battleship** — "the most powerful warship available", 92 m long, six
  hardpoints; the primary warship of Sci-Tek and TetraCorp.
- **Command Cruiser** — strongly armed and armoured, six hardpoints, carries up to
  twenty smaller fighters in its hold and can tow medium craft. Its long range
  extends a fleet's reach.
- **Spy Satellite** — orbits an asteroid and sends back video of its surface, which
  is how you see missile damage. Built in the Satellite Silo.

## Alien craft

31 alien craft use the same table; they cost nothing (the AI builds them). Each
parallels a Terran class; the race grouping is inferred from the order of the
names **(?)**.

| craft | race | Terran counterpart | armour | speed (FN) | hardpoints | build days | range |
|---|---|---|---|---|---|---|---|
| Lazzaro Research | Rigellian | Scoutship | 16 | 6 | 2 | 24 | 192 |
| Delphini Assault | Rigellian | Destructor | 35 | 4 | 3 | 40 | 160 |
| Messier-Lukannon | Rigellian | Terminator | 48 | 4 | 4 | 75 | 160 |
| Transportation | Rigellian | Transporter | 25 | 4 | 2 | 90 | 160 |
| Observatory | Rigellian | Space Dock | 130 | 0 | 4 | 90 | 0 |
| Rattlesnake | Braccatian | Scoutship | 20 | 5 | 2 | 28 | 192 |
| WidowMaker | Braccatian | Fleet Battleship | 50 | 3 | 4 | 75 | 160 |
| HeartsBlood | Braccatian | Transporter | 65 | 2 | 6 | 120 | 160 |
| Morning Glory | Braccatian | Combat Eagle | 15 | 5 | 4 | 50 | 160 |
| SkyMech | Braccatian | Space Dock | 100 | 0 | 5 | 110 | 0 |
| Hiero | Mikotaj | Scoutship | 15 | 5 | 2 | 15 | 192 |
| Ylikt-shan | Mikotaj | Combat Eagle | 30 | 5 | 2 | 30 | 160 |
| Falari-Lourn | Mikotaj | Fleet Battleship | 70 | 2 | 5 | 80 | 160 |
| Ruth-Strivakh | Mikotaj | Transporter | 40 | 2 | 2 | 112 | 160 |
| Na-Xanth | Mikotaj | Space Dock | 140 | 0 | 4 | 80 | 0 |
| Gerla-Kans Explorer | Artemian | Scoutship | 32 | 5 | 2 | 30 | 192 |
| All-Purpose Assault | Artemian | Combat Eagle | 36 | 5 | 3 | 33 | 160 |
| Shielded Multi-Assault | Artemian | Destructor | 50 | 3 | 4 | 60 | 160 |
| Ultimate Mk II | Artemian | Fleet Battleship | 80 | 2 | 6 | 115 | 160 |
| Hardcore | Artemian | Transporter | 90 | 2 | 5 | 220 | 160 |
| Geostationary Construction | Artemian | Space Dock | 130 | 0 | 5 | 86 | 0 |
| Surveillance Craft Type 5 | Maunid | Scoutship | 5 | 4 | 2 | 24 | 192 |
| Combat Craft Type 1.5 | Maunid | Combat Eagle | 50 | 3 | 4 | 52 | 160 |
| Max Combat Craft Type 6 | Maunid | Terminator | 70 | 2 | 6 | 122 | 160 |
| Elite Command Craft | Maunid | Fleet Battleship | 80 | 2 | 6 | 100 | 160 |
| Transportation Craft Type 3 | Maunid | Transporter | 35 | 2 | 4 | 122 | 160 |
| Orbital Construction Area | Maunid | Space Dock | 130 | 0 | 5 | 96 | 0 |
| Hunter/Prospector | Achaean | Scoutship | 25 | 5 | 2 | 25 | 192 |
| Dedicated Fighter | Achaean | Terminator | 50 | 3 | 4 | 70 | 160 |
| Dedicated Ore Transporter | Achaean | Transporter | 40 | 3 | 4 | 90 | 160 |
| Orbital Shipyard | Achaean | Space Dock | 100 | 0 | 3 | 80 | 0 |

## Hardpoints and items

Every craft has a number of **hardpoints** to which weapons and shields are
attached; they can be swapped by clicking again and are split into offensive and
defensive. The items and their prices **[code]**:

| item | type | price (Cr) | armour bonus | blueprint |
|---|---|--:|--:|---|
| Ion Cannon | weapon | 1,000 | - | start |
| Disruptor | weapon | 6,000 | - | start |
| Napalm Orb | weapon | 4,000 | - | start |
| Chaos Bomb | weapon | 12,000 | - | start |
| Vortex Mine | weapon | 5,000 | - | start |
| Laser | weapon | 1,000 | - | start |
| Photon Cannon | weapon | 4,500 | - | start |
| Plasma Cannon | weapon | 9,000 | - | start |
| Static Inducer | defence | 4,500 | - | 80,000 |
| Warp Generator | defence | 9,000 | - | 75,000 |
| Deflector | defence | 12,000 | - | 115,000 |
| Shield x10 | defence | 1,500 | 10 | start |
| Shield x20 | defence | 3,000 | 20 | start |
| Shield x30 | defence | 5,000 | 30 | start |
| Shield x40 | defence | 6,500 | 40 | 15,000 |
| Shield x50 | defence | 8,000 | 50 | 60,000 |

Roles **[text]**: the **Deflector** deflects most energy attacks and works
alongside shields; the **Static Inducer** emits an electromagnetic pulse that
leaves hostile craft unable to attack or move during it; the **Warp Generator**
periodically phases the ship out of space, making it briefly invulnerable; a
**Shield** fills one hardpoint and adds its armour; the Shield x50 makes a ship
"almost (but not quite) invulnerable". How the offensive items deal damage is not
decoded (see [Ship-to-ship combat](ship-combat.md)); the game also keeps three
rating figures per item that the AI uses to value targets **(?)**.

## Fleets

- A fleet holds up to **four ships** (a fifth is rejected) **[code]**.
- It moves at the speed of its **slowest** ship and has the range of its
  **smallest** craft, so loading fighters into a Command Cruiser extends it.
- It has a **retreat threshold**: the share of the fleet that may be destroyed
  before it withdraws; each day the fleet compares its damage with this threshold.
  At 100% it never turns back; at 50% it leaves after losing half.
- Orders: proceed peacefully, attack an asteroid, intercept a hostile fleet (or
  merge with your own), patrol a sector for a time, cancel the previous order,
  detach ships, show cargo. Up to five orders stack and can be changed in space.
  Fleets show on the scanner as coloured triangles.

## Open questions

- The default hardpoint loadouts and the attack/defence ratings (run-time only).
- The meaning of the craft record's range and "alternate days" fields.
- Whether the ore amounts are consumed per craft or only checked.

*Related: [Buildings](buildings.md); [Missiles](missiles.md);
[Ship-to-ship combat](ship-combat.md); [Ores and mining](ore-and-mining.md);
[Asteroids](asteroids.md).*
