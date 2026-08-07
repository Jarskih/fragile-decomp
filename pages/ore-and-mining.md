---
title: Ores and mining
---

# Ores and mining

*Status: written from the game's code and from saved-game data. The parts
marked (?) are inferred and not yet confirmed in a live run.*

## The ten ores

There are ten ores in three tiers, in the game's own words: the **most
common ores** — Selenium, Asteros, Barium and Crystalite; the **more
valuable ores** — Quazinc, Bytanium, Korellium and Dragonium; and the
**rarest and most valuable ores** — Traxium and Nexos.

## The three mines

Mining is done by three buildings, one per tier:

- the **Mine** seeks out the most common ores (Selenium, Asteros, Barium,
  Crystalite);
- the **Deep Bore Mine** seeks out the more valuable ores (Quazinc,
  Bytanium, Korellium, Dragonium);
- the **Seismic Penetrator** seeks out the rarest ores (Traxium and Nexos);
  as a blueprint it also doubles the output of all your deep-bore mines.

The other races have their own equivalents of the same three roles (for
example the Achaean Commonbore and Deepbore, the Mauna Superior Extraction
Unit, the Artemia Rare Ore Extractor).

A mine is a building placed on an asteroid's surface. Which tier of ore a
colony can extract is a property of the **mine**, not of the asteroid: the
mine simply draws on whatever ore the asteroid holds. There is no "this
asteroid contains Traxium, that one does not" marker — the rarest ores are
just much scarcer in the ground.

## How much ore an asteroid holds

Every asteroid has **ten ore reserves**, one per ore, in the order the ores
are listed above. They are fixed at the moment the asteroid is created —
nothing about the amounts is re-rolled later — and mining draws them down
over time.

What an asteroid starts with depends on who owns it:

- **The six alien asteroids** (the Rigellian, Braccatian, Mikotaj, Artemian,
  Maunid and Achaean asteroids) each hold exactly the same fixed reserves:
  300 Selenium, 400 Asteros, 400 Barium, 150 Crystalite, 70 Quazinc, 60
  Bytanium, 35 Korellium, 35 Dragonium — and **no Traxium and no Nexos**.
- **The player's home asteroid** (the TetraCorp Asteroid) is not rolled:
  its reserves are chosen by the same rules that generate the starting
  universe, and differ slightly from game to game. In the standard campaign
  it holds 277 Selenium, 327 Asteros, 360 Barium, 112 Crystalite, 53
  Quazinc, 55 Bytanium, 25 Korellium, 28 Dragonium — again **no Traxium and
  no Nexos**. Custom games give nearby values (for example 297/354/318/110/
  59/55/25/30 on a medium map), but the two rarest ores are always absent.
- **Every unowned asteroid** is rolled individually at creation, ore by
  ore. For the eight common and valuable ores each asteroid first rolls a
  presence chance; the result is either the ore's full window or a small
  residual: roughly — Selenium 500–1000 (else 1–50), Asteros and Barium
  250–500 (else 1–25), Crystalite 250–750 (else 1–37), Quazinc and Bytanium
  1–116, Korellium and Dragonium 1–100. The two rarest ores are scarcer in
  two ways: only about **one unowned asteroid in three has any Traxium**
  (2–15 units), and about **one in four has any Nexos** (1–8 units); the
  rest have none at all. No asteroid is ever generated with zero of a
  common or valuable ore. (The numbers are measured from saved games — see
  Open questions.)

So in a standard game of sixty asteroids, roughly twenty unowned asteroids
bear some Traxium and about sixteen bear some Nexos, in small amounts — and
the six alien asteroids and the home asteroid carry none of the two rarest
ores at the start.

**Asteroids that appear later in the game are rolled the same way.** Every
new asteroid (whether it buds off an existing one, is reported by a scout,
or is placed by a scenario) is generated with a fresh roll of its ten ore
reserves, using the same per-ore rules — so a later asteroid has the same
chances as an initial one. (The only exception is the six starting alien
asteroids, which use fixed amounts; a later-spawned alien asteroid rolls
its ore like any other.)

**What you see is not the reserves.** The two are different stores:

- **Reserves** — the ore *in the ground*: hidden, what mining draws on, and
  what a geosurvey reports. Always present (all eight common and valuable
  ores) and measured in hundreds of units.
- **Surface deposits** — the ore *shown* on the asteroid's surface: the
  lumps that have matured there. This display is usually almost empty: the
  home asteroid and freshly spawned asteroids typically show one or two
  ores (or none), while the same asteroid's reserves hold all eight common
  and valuable ores in quantity. Only long-lived alien asteroids build up a
  fuller surface.

This is why an asteroid can "have 0 of some ore" in the surface view even
though it was generated with all of them.

## What ore does over time

The reserves are not a static display, and an asteroid's ore is not a
permanent fact. The game's geosurvey events re-examine asteroids and
**correct the ore either way**:

- **More ore found** — "A recent geosurvey has revealed extra ore worth %d
  Credits on Colony Asteroid %s."
- **Less ore found** — "A recent geosurvey has revealed that ore valued at
  %d Credits never existed on Colony Asteroid %s."

So over a long game, any ore — even a common one — can be discovered in
larger amounts or drained down, and an asteroid that once showed a mineral
can end up without it. This is why "asteroids without some ore" appear in
play even though every asteroid is created with all eight common and
valuable ores.

Beyond the fluctuation, the mines convert units of ore into **ore value**
on the asteroid — each ore has its own per-unit value, so one unit of Nexos
is worth more than one unit of Selenium. The value accumulates on the
asteroid until the ore is shipped away (?).

Three observable consequences of this economy:

- The **colony level** of an asteroid (a grade from 1 to 3) is derived from
  its ore value: fresh asteroids start at grade 1 and step up as their value
  grows — the observed saves show the alien asteroids at grade 2 later in
  the game and the home asteroid at grade 3.
- The **colony value** displayed on the asteroid climbs toward a target
  built from the ore deposits sitting on its surface.
- Ore **deposits** appear on the asteroid's surface on their own schedule:
  a deposit matures and adds to the surface stock of its ore, and new
  deposits re-materialise on per-kind timers (?) — the schedule table is
  read from the game's runtime data, and the mapping of the individual
  schedules to the ten ores is not yet established.

## Open questions

- The per-ore amount tables, unit values and deposit schedules live in
  tables the game fills at runtime; the numbers above are measured from
  saved games, not read from those tables. A runtime trace would confirm
  them and the unit values exactly.
- How often the geosurvey re-evaluations run, and the effective rate at
  which ores are drained and discovered (the cadence of the events is not
  yet traced).
- Exactly which ores each mine tier draws (the tier lists above follow the
  game's own building descriptions).

*Related: [Randomness and determinism](randomness.md) — the reserves are
rolled from the deterministic universe stream, so the same settings always
produce the same ores in the same places.*
