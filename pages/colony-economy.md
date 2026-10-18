---
title: Colony economy
---

# Colony economy

*Status: the formulas and constants below are read from the game's code
(**[code]**), from the GOG retail build; the reference build is assumed to be
the same. Statements that appear only in the game's text or manual are marked
**[text]** and are never used as evidence for a number. Items the analysis has
not resolved are marked **(?)** and listed at the end.*

This page describes what a colony does every day: how it houses and feeds its
people, how it powers its buildings, what makes people sick, unhappy or
criminal, and how money moves. All "per day" figures use the game day
described on [Game time](game-time.md) (32 ticks at the default speed). The
buildings referred to are listed, with cost and size, on
[Buildings](buildings.md).

## The daily colony update

Each day, every colony of every empire (a colony is an asteroid with a placed
CPU; its owner is one of the eight player slots) runs these steps **in this
order** **[code]**:

1. The owner's **Money** gains **1 Cr per employee** (the colony's population).
   A colony whose population is zero is flagged for abandonment instead. The
   fixed per-empire stipend is credited just after (see [Income](#income)).
2. **Radiation** is computed.
3. **Population** changes (growth, housing cap, sickness).
4. **Air**, **food** and **water** are balanced.
5. **Power** is recalculated. Because power runs *after* the three life-support
   steps, the brownout level they use is *yesterday's*.
6. **Workforce** check (are the workplaces staffed?).
7. **Unrest and crime** update, and a random event may fire.

## Population and housing

- **Housing capacity** = 100 per CPU + 50 per Living Quarters + 150 per
  Resiblock **[code]**.
- A new colony starts with **50 people**. A warning is posted to the owner when
  the population is below 30.
- Each day one die-roll decides the change: **+1 person with 60%** chance, **-1
  person with 10%**, nothing with 30%. The expected drift is about +0.5 per day
  up to the cap. (The -1 and the shortage/radiation losses are skipped if a
  hidden "no population loss" configuration byte is set; it is off in a normal
  game.)
- If population exceeds housing, it is cut back to the cap and the overshoot
  (when more than one) is added to **unrest**.
- Population never falls below zero. At zero the colony is removed ("colony
  death"). For the player, losing every colony is defeat (see
  [Aliens and diplomacy](aliens-and-diplomacy.md)).
- Every employee costs nothing to keep but consumes **1 unit/day** of each of
  air, food and water (below), and pays **1 Cr/day** into Money.

## Life support: Power, Air, Food, Water

The game's status display shows four resources, abbreviated PAFW. Air, food and
water share one unit: **"employees supported"**. Power is a different system
(per building, in MW).

### Air, food and water

Each resource has a **supply** (this day's production), a **demand** (the
population) and a **store** (surplus carried to the next day):

```
supply = free CPU output + per-building output * number of powered producers
net    = supply + store - population
net < 0 : store becomes 0 and people die (below)
net >= 0: store = min(net, store cap)
```

| resource | producer | output per building | still works while brownout level is below | store cap | deaths when the shortfall is S (people) |
|---|---|---|---|---|---|
| Air | Air Processor | 400 | 24 | 3000 per Environment Control + 1000 per CPU | S |
| Food | Hydroponics Plant | 300 | 22 | 1000 per Environment Control + 1000 per CPU | S/10 + 1 (integer division) |
| Water | Water (Hydration) Plant | 400 | 23 | 1000 per Environment Control + 1000 per CPU | S/5 + 1 |

- Deaths are added to **unrest** one for one **[code]**.
- The **CPU's free output** starts at **300 air, 250 food, 250 water** when the
  CPU is placed, and **falls by 1 per day** per resource until zero. (The data
  and decay routine are confirmed; the link to the CPU's own update is **(?)**.)
- Unused supply is wasted beyond the store cap; the store is purely a buffer of
  "employee-days".
- The Environment Control stores air 3000 / food 1000 / water 1000 in the code.
  **The game text says 5000 / 600 / 600** — the text is contradicted by the
  code in this build and the code values are used here.

### Power

Power is generated in MW, drawn per building, and shared by the whole colony:

```
generation = 2  x Solar Panel          + 8 x Solar Generator
           + 12 x Solar Matrix         + 12 x Protected Solar Matrix      (solar subtotal x2 with the Power Amplifier blueprint)
           + Powerplants: 32 each while the asteroid still holds Asteros ore, otherwise 8 each
           + 8 per CPU
available  = generation + stored power from yesterday
```

- The Power Amplifier doubles only the four solar types, not Powerplants or the
  CPU.
- A **Powerplant** burns Asteros from the asteroid's own reserve: every 4th day
  the reserve drops by the number of Powerplants (to zero at most). When the
  reserve is empty each plant gives only 8 MW.
- **Demand** is the sum of (number of buildings of a type x its MW draw). The
  Gravity Nullifier draws only while switched on; an Asteroid Engine draws its
  current power setting.
- **Stored power**: when everything is supplied, the surplus is stored up to
  **200 MW per Power Store** (400 with the Hi-Energy Power Stores blueprint)
  plus **50 per CPU**. If anything is cut, the store is empty.
- **Brownout order**: demand is added up along a fixed **priority list**. The
  first building type at which the running total exceeds the available power
  sets the colony's **brownout level** (0 = fully powered, up to 24). Types
  later in the list are cut first. The list, highest priority first:

  1 CPU, 2 Powerplant, 3 Living Quarters, 4 Resiblock, 5 Power Store,
  6 Storage Facility, 7 Solar Panel, 8 Solar Generator, 9 Solar Matrix,
  10 Protected Solar Matrix, 11 Storage Tower, 12 Environment Control,
  13 Pleasure Dome, 14 Landing Pad, 15 Refueling Depot, 16 Missile Silo,
  17 Air Processor, 18 Water Plant, 19 Hydroponics Plant, 20 Command Center,
  21 Screen Generator, 22 Radiation Filter, 23 Repair Facility, 24 Protected
  Storage Tower, 25 Medical Center, 26 Photon Turret, 27 Plasma Turret,
  28 Laser Turret, 29 Sensor Array, 30 Ship Yard, 31 Weapons Factory, 32 Mine,
  33 Deep Bore Mine, 34 Security Center, 35 Seismic Penetrator, 36 Anti-Missile
  Pod, 37 Satellite Silo, 38 Gravity Nullifier, 39 Ore Teleporter, 40 Asteroid
  Engine (cut first).

  The first 16 are never cut by the scheme. The cut-off points known from the
  code: **Medical Center stops at level 16 or more, Radiation Filter at 19 or
  more, Hydroponics at 22, Water Plant at 23, Air Processor at 24**. Other
  buildings are assumed to follow the same pattern (?). A "power critical"
  message is posted to the player at level 16 or higher, at most once per 30
  days per colony.
- A scenario switch forces the brownout level to zero (unlimited power); it is
  off in a normal game.

Power therefore degrades gracefully: engines, teleporters and weapons go dark
first, then security, medical care and radiation protection, and only then the
air, food and water plants — after which the shortages above start killing
people.

## Radiation and sickness

- Each day the colony's **radiation level R** is computed from the ore in the
  ground **[code]**:

  `R = extra term + Nexos reserve + Asteros reserve / 128 + Traxium reserve / 2`

  (Nexos and Traxium are the two radioactive high-grade ores; the "extra term"
  rises by 4 when a Nuclear missile hits and by 1 for an Anti-Virus missile, and
  decays over time.)
- While powered (brownout level below 19) each **Radiation Filter** lowers R by
  **3**; while powered (level below 16) each **Medical Center** lowers it by
  another **3**. R never goes below 0.
- **Sickness**: if R is above 10, one employee is lost every day (and unrest
  +1). Otherwise a loss happens with the probability below, indexed by R:

| R | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| daily chance of losing one employee (%) | 0 | 10 | 11 | 13 | 14 | 17 | 20 | 25 | 33 | 50 | 100 |

  Each loss reduces population by 1 and raises unrest by 1.
- The game's text describes staged disease outbreaks (reduced efficiency up to
  incapacitation) and Medical Center treatment; apart from the radiation loss
  above, only the six anti-population viruses and a handful of natural
  diseases are confirmed — see [Trade](trade.md#anti-personnel-viruses-apvs).

## Workforce

Six kinds of workplace each need **8 employees**: Mine, Deep Bore Mine,
Seismic Penetrator, Ship Yard, Missile Silo and Command Center **[code]**. Each
day the colony's population is allocated to them in this order, subtracting 8
per building: **Mines, then Deep Bore Mines and Seismic Penetrators, then Ship
Yards, then Missile Silos, then Command Centers**. The first group at which the
running balance goes negative, and every later group, is **understaffed** and
does not work (the colony shows "undermanned").

The remaining balance feeds unrest: balance between -20 and +20 reduces unrest
by 1; a balance above 59 adds balance/60 (an idle population breeds unrest). An
active **strike** (see below) switches every workplace off for its duration.

## Unrest and crime

Two numbers per colony. **Unrest** (range -80 to 400) rises with shortages,
overcrowding, sickness and unemployed workers; **crime** (range 0 to 310) rises
with unrest and falls with security. **[code]**

```
unrest = clamp(unrest - 2 x Pleasure Domes, -80, 400)          (each day)
if unrest < 31:  crime -= 2
crime += 1 + unrest x population / 56000 - Security Centers     (about)
crime  = clamp(crime, 0, 310)
```

- A single Security Center cancels the baseline +1 crime per day; each Pleasure
  Dome removes 2 unrest per day.
- Buildings also carry a one-off **morale value** applied when they are placed
  and reversed when they are removed (shown in the
  [Buildings](buildings.md) tables). Whether it is the same quantity as the
  daily unrest figure, and why Living Quarters (+10) and the Security Center
  (-20) have the signs they do, is unresolved **(?)**.
- From **crime 40** a countdown of 30 to 59 days runs; when it expires one
  random event is drawn from a list that depends on the crime tier (up to 100:
  4 kinds; up to 200: 6; up to 300 and above: 7). The decoded handlers:

| event | effect | size by tier (crime <=100 / <=200 / <=300 / >300) |
|---|---|---|
| strike | work stops for x/2 to x days | x = 20 / 80 / 120 / 140 |
| riot | lose about x% (+-5) of the population | x = 10 / 20 / 35 / 40 |
| theft | owner loses x/2 to 3x/2 Cr, with a message | x = 8,000 / 20,000 / 40,000 / 80,000 |
| sabotage | destroys or disables buildings (several handlers) | not fully decoded **(?)** |

- **Surplus-loss events**: four events can wipe a colony's entire stored surplus
  of air, water, power or food and post a "Surplus ... loss" message. The
  trigger probability is not extracted **(?)**; large Environment Control
  reserves are therefore at risk.
- The game text promises that Security Centers and Pleasure Domes act on
  specified numbers of personnel (150 and 300); the code instead applies a flat
  per-building effect with no employee cap **[text vs code]**.

## Money

Each empire holds **Money**, four **funds** and a **Debt**, all as whole Cr
**[code]**.

| pool | what draws on it |
|---|---|
| Money | the "Credits" shown; Sci-Tek blueprints and black-market goods are paid from here; income always lands here |
| Construction | placing a building (full cost at placement) |
| Vehicles | buying a craft (the Ship Yards check the fund holds at least the price) and building a Spy Satellite |
| Missiles | missile production, drained per production step; production stops when the fund is empty |
| Personnel | Colony Supervisor salaries and guards, agent mission fees |
| Debt | owed to the Federation; not a fund (shown as "Debt To Federation") |

- **Moving money**: the budget screen is one bar whose segments are Money and
  the four funds. Dragging a boundary moves Cr between Money and a fund; you can
  only draw on what Money holds, and a fund cannot go below zero when moved
  back. **Income never goes to a fund automatically** — except the claim below.
- **Start**: **1,000,000 Cr** Money for every atmosphere setting, all four
  funds and the Debt at zero. (A hidden test mode instead gives every pool
  1,000,000.)
- **New colony claim**: founding a colony moves up to **8,000 Cr** from Money
  into Construction so the CPU can be placed. If Money cannot cover it a "no
  funds" message appears instead.

### Income

Per day, per empire **[code]**:

| source | amount |
|---|---|
| each colony's employees | 1 Cr per employee |
| fixed stipend per empire, by the **atmosphere** setting | 100 (Peaceful) / 250 (Neutral) / 400 (Aggressive) Cr |
| ore sold to the Federation | lump sum at each Federal Transporter visit (see below) |

### Selling ore

You do not sell ore directly. The Federal Transporter (see
[Game time](game-time.md)) values all ore **shipped since it arrived** at its
departure, using the month's Federation ore prices (these equal the monthly
trade prices of the ten ores — see [Trade](trade.md)), and credits the total: first
to reduce your Debt, the remainder to Money. The Transporter visits roughly
every 150 to 250 days.

### Fines, payments and the shortfall cascade

When an empire must pay (a pact violation fine, a treaty penalty, a demanded
tribute) the amount is collected in this order: **Money, then Construction,
Vehicles, Missiles, Personnel**. Whatever the five pools cannot cover becomes
**Debt** (when the payee is another party). The payee is always credited the
full amount into Money, regardless of what the payer could afford. Debt is
repaid by ore sales; if a sale exceeds the Debt, the excess is paid into Money
and the Debt resets to zero. No interest was found. Fines can be as large as
the starting money (the manual shows a 1,000,000 Cr example).

### Other money rules

- **Buildings**: the full Cost is taken from Construction at placement; it is
  refunded only if the building cannot be created, never when demolished.
- **Ships**: price (hull plus fitted hardpoint items) from Vehicles. See
  [Vehicles](vehicles.md).
- **Missiles**: production cost drains Missiles per step. See
  [Missiles](missiles.md).
- **Alien races** do not use these pools; they pay for buildings from a
  production-point counter (see [Aliens and diplomacy](aliens-and-diplomacy.md)).
- **Final rating**: the "TetraCorp Rating" at the end is a weighted sum of what
  you built and still hold (100% of structures built, 50% of those remaining,
  smaller shares for ships and missiles) minus 70,000, the Debt and the start
  money, then scaled by the difficulty and the scenario. The exact term list is
  not reproduced **(?)**.

## Design summary (daily rules in one place)

| rule | value |
|---|---|
| day | 32 ticks (default) |
| income | 1 Cr per employee + stipend 100/250/400 |
| growth | +1 (60%), -1 (10%), capped by housing: CPU 100, Living Quarters 50, Resiblock 150 |
| consumption | 1 air, 1 food, 1 water per employee per day |
| producers | Air Processor 400, Hydroponics 300, Water Plant 400 |
| CPU free output | 300 / 250 / 250, falling 1 per day |
| shortage deaths | air S; water S/5+1; food S/10+1; also +unrest |
| radiation | R from Nexos, Asteros/128, Traxium/2; filters and medical -3 each; death chance table |
| workplace staffing | 8 per Mine, Deep Bore, Seismic, Ship Yard, Missile Silo, Command Center |
| power | priority-ordered brownout; stored 200 per Power Store (400 upgraded) |
| unrest events | countdown 30 to 59 days once crime is 40 or more |

## Text versus code

| claim in the game's text or manual | verdict |
|---|---|
| Living Quarters house 50, Resiblock 150 | confirmed |
| Air Processor 400, Hydroponics 300, Water Plant 400 | confirmed |
| Power Store 200 MW | confirmed (400 upgraded) |
| Solar Panel 2 MW, Solar Generator 8 MW | confirmed (doubled with Power Amplifier) |
| Powerplant 32 MW, 8 MW fallback, 1 Asteros per 4 days | confirmed |
| Solar Matrix 12 / 24 MW (tooltip) vs 8 MW (long text) | code gives 12; long text wrong |
| Protected Solar Matrix 8 MW (text) | code gives 12 |
| Environment Control 5000 / 600 / 600 | contradicted: code gives 3000 / 1000 / 1000 |
| CPU output falls 1 per day | confirmed in the data |
| each employee uses 1 unit of Power, Air, Food, Water | air/food/water confirmed; power is per building |
| Medical Center "up to 100 employees", Security Center "150", Pleasure Dome "300" | not found in code (flat per-building effect) |
| disease outbreaks with stages | only radiation sickness and the viruses found |
| an unpaid supervisor may blow up the colony | not found (see [Personnel](personnel.md)) |

## Open questions

- Whether the one-off morale values in the building table and the daily unrest
  figure are the same quantity.
- How surplus-loss events and the sabotage events are triggered and which
  buildings they hit.
- The staged outbreak mechanic and Medical Center treatment.
- The exact start-Money rule for the Peaceful atmosphere, and the full term list
  of the final rating.

*Related: [Game time](game-time.md); [Buildings](buildings.md);
[Personnel](personnel.md); [Trade](trade.md); [Ores and mining](ore-and-mining.md);
[Aliens and diplomacy](aliens-and-diplomacy.md).*
