---
title: Missiles and how they are fired
---

# Missiles and how they are fired

*Status: the firing behaviour below is read from the game's code; the
missile descriptions and prices are the game's own words. Figures that have
not been measured exactly are marked (?).*

## What a missile is

The game's weapons are **missiles**: warheads built on a colony and fired at
asteroids. In the game's own words there are thirteen kinds:

- **Explosive** — "A conventional (and cheap) warhead for general use."
- **Area Explosive** — "A standard warhead with a larger area of destruction."
- **Napalm** — "An advanced incendiary device using plasma gas to melt most
  structures."
- **Hellfire** — "A deadly substance capable of spreading across an entire
  asteroid. Effective on densely populated asteroids."
- **Scatter** — "Over the target asteroid this missile splits into several
  conventional explosive missiles for an improved hit ratio."
- **Vortex** — "Unleashes an electrical storm that will wander across the
  target asteroid, damaging everything it touches."
- **Nuclear** — "This multi-megaton device will destroy most structures on
  the target asteroid, as well as ships in orbit."
- **Virus** — "This volatile substance dissolves the very fabric of an
  asteroid, spreading swiftly."
- **Anti-Virus** — "Used to halt the spread of an asteroid virus. It will
  neutralize the virus and then itself."
- **Mega** — "The power unleashed by this warhead results in the destruction
  of an entire asteroid. Use with care!"
- **Stasis** — "New advances in temporal physics allow an entire asteroid to
  be frozen, incapable of action, for a period of time."
- **Bug Hunter** — a highly illegal anti-personnel-virus missile, effective
  only against the Artemia (50% fatalities).
- **Meat-Eater** — a highly illegal anti-personnel-virus missile, effective
  against the Achaeans, the Braccatia and Terrans (100% fatalities).

Each kind is built from specific ores, as the game's ore descriptions state:
Explosive and Scatter from Selenium, Area Explosive and Anti-Virus from
Barium, Vortex from Crystalite, Napalm and Hellfire from Quazinc, Nuclear
from Bytanium, Stasis from Korellium, Mega from Dragonium and Nexos, and
Virus from Traxium.

## Where missiles live

A colony's missiles are held in its **Missile Silos**, built on the
asteroid. New missiles are produced by **Missile Construction**, which uses
the **Vehicles fund** and the ores above, and each silo holds so many
missiles of each kind. The **Missile Control** screen is where the player
loads and fires them: you select missiles and a target, and the game refuses
with plain messages when there is nothing to fire at or no silos — "No
missiles have been selected", "No target has been selected", "Asteroid has
no missile silos".

Ships carry their own ammunition: the fleet panel shows **Missiles At** — how
many missiles each ship holds — and a ship's **Strike Rate**. Ships can be
ordered to **Attack** an asteroid or **Intercept** a hostile fleet, and a
fleet that is fighting is shown **In Combat**.

## How a firing ship behaves

A ship or fleet ordered to attack does the following, as read from the code:

- It **approaches its target** — the target asteroid, or the enemy fleet —
  turning as it flies, until it is within firing range.
- Firing happens **only while the target is genuinely hostile**: an enemy's
  asteroid, or any asteroid that is not yours. Ships will not open fire on a
  friendly or neutral target (?).
- Once in range it **fires repeatedly while approaching**: each tick there is
  a chance of a shot (the exact per-tick probability is not yet measured),
  and **each shot consumes one missile** from the ship's hold.
- Each shot is **aimed**: the missile's course is steered slightly toward the
  target every tick, so shots home in; a wayward shot can be re-aimed or
  dropped.
- A ship picks what to shoot at from the objects **around and on the target**:
  the defenders and ships in orbit. The targets are scored by distance and
  bearing — the nearest and most head-on gets shot at first.
- When the ship gets **very close to the target** it stops firing — the
  attack is over once the fleet is on top of the asteroid. The **retreat
  threshold** set on the fleet decides when it breaks off instead
  ([Vehicles](vehicles.md)).
- In-flight missiles are themselves shot at: defenders sweep a firing arc
  ahead of them, and anything in the arc — including incoming missiles — is
  hit and destroyed (?). This is why a defended asteroid is harder to bomb
  than an undefended one.

## What a hit does

A missile that reaches its target detonates and applies its warhead: the
explosive kinds blast the surface, the special kinds spread or freeze or
dissolve the asteroid as their descriptions say. Exactly how much damage each
warhead deals, how large its blast area is, and how fast each missile type
flies are not yet measured (?). The damage model for buildings and ships is
still being read from the game (?).

*Related: [Vehicles](vehicles.md) — the ships and fleets that carry and fire
missiles; [Asteroids](asteroids.md) — what the warheads are fired at.
[Ores and mining](ore-and-mining.md) — the ores each missile kind is built
from.*
