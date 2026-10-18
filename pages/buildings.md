---
title: Buildings
---

# Buildings

*Status: cost, hit points, build time, footprint, power draw, power output,
capacities and staffing are read from the game's code and data tables
(**[code]**, GOG retail build; the Terran rows are reported identical in the
reference build). The descriptions in the "role" columns are the game's own
text (**[text]**), condensed. Where code and text disagree, the code value is
used and the conflict is stated. Items still open are marked **(?)**.*

The structures a colony is built from fall into three groups:

- **Always-available buildings** — 27 types you can build on any colony without
  buying anything first.
- **Brochure buildings** — 11 types (plus one variant) unlocked by ordering the
  blueprint from the Sci-Tek brochure (Money). Their blueprint prices are in the
  tables below. The brochure also sells permanent upgrades (see
  [Upgrades](#brochure-upgrades-that-change-building-numbers)).
- **Alien equivalents** — every alien culture fields its own buildings that
  match the Terran ones; their numbers are listed at the end.

A colony is laid out on the [asteroid surface grid](asteroid-spawning.md); each
building occupies a square of cells. The CPU is placed by the Transporter when a
colony is founded and cannot be built by hand. Construction takes the building's
**build days** (counted down once per game day, see [Game time](game-time.md));
the building works when the count reaches zero. The cost is taken in full from the
**Construction** fund at placement and is not refunded on demolition. Most
buildings draw power; a building that loses power stops working (see
[Colony economy](colony-economy.md) for the brownout order). A Weapons Factory is
required for turrets to work and, with Ship Yards, to build ships. Damaged
buildings are repaired by the Repair Facility. A race that owns the
**Building Armour** blueprint gets **+10 hit points** on every new building.

## How to read the tables

- **Cost** in Cr; **HP** = hit points (the game calls it armour); **days** =
  build time; **size** = footprint in cells; **MW** = power drawn by one
  building (0 for generators, whose output is shown separately).
- **Morale** is a one-off value applied to the colony when the building is
  placed and reversed when it is removed. A positive value *reduces* the colony's
  unrest accumulator. Its exact reading is unresolved **(?)**; the daily unrest
  effects that are confirmed are on [Colony economy](colony-economy.md).
- **Blueprint** = Sci-Tek blueprint price in Cr, or "start" if available from the
  beginning.

## Colony essentials

| building | cost | HP | days | size | MW | morale | blueprint | role [text] |
|---|--:|--:|--:|---|--:|--:|---|---|
| **CPU** (Colony Preservation Unit) | 8,000 | 36 | 40 | 4x4 | 0 (makes 8) | 50 | placed by the Transporter | The minimum survival colony: houses 100, stores 50 MW, gives free air 300 / food 250 / water 250 that each fall by 1 per day, starts with 50 people. Only on an uninhabited asteroid. |
| **Landing Pad** | 300 | 5 | 16 | 2x2 | 0 | 0 | start | Access to the underground hangars; idle ships are safe and repaired there. |
| **Command Center** | 8,000 | 36 | 32 | 3x3 | 3 | 5 | start | Needed to command any fleet. One serves any number of colonies; also builds the Space Dock. Needs 8 staff. |
| **Weapons Factory** | 4,400 | 24 | 32 | 4x4 | 2 | 0 | start | Engines for all craft, manufacture of hardpoint weapons and warheads; turrets do not function without one. |
| **Sensor Array** | 3,500 | 15 | 36 | 1x1 | 2 | 5 | start | Extends sensor range; without one an asteroid has a very small range. (The Improved Sensors upgrade makes it unnecessary.) |

## Power generation and storage

Output is a constant in the code (see [Colony economy](colony-economy.md)). The
**Power Amplifier** doubles the four solar types.

| building | cost | HP | days | size | MW made | MW used | blueprint | role [text] |
|---|--:|--:|--:|---|--:|--:|---|---|
| **Solar Panel** | 500 | 5 | 8 | 1x1 | 2 (4 amplified) | 0 | start | Cheapest and quickest. |
| **Solar Generator** | 1,500 | 10 | 10 | 2x2 | 8 (16) | 0 | start | More efficient than the panel. |
| **Solar Matrix** | 4,000 | 10 | 32 | 2x2 | 12 (24) | 0 | 50,000 | Large array; small footprint. The long text says 8 MW, but the code gives 12 (the tooltip says 12/24). |
| **Protected Solar Matrix** | 7,200 | 20 | 32 | 2x2 | 12 (24) | 0 | with the Solar Matrix (?) | A Solar Matrix with a built-in laser turret. The text says 8 MW; the code gives 12. |
| **Powerplant** | 10,000 | 34 | 40 | 3x3 | 32 while the asteroid holds Asteros ore, else 8 | 0 | 40,000 | Fusion; burns 1 Asteros per plant every 4 days from the asteroid's reserve. |
| **Power Store** | 1,500 | 34 | 32 | 2x2 | - | 0 | start | Holds 200 MW of surplus (400 with Hi-Energy Power Stores). |
| **Refueling Depot** | 8,500 | 40 | 30 | 2x2 | - | 0 | start | Recharges ship fuel; without one ship life is shortened and Transporters cannot reach new colonies. |

## Storage and transport

| building | cost | HP | days | size | MW | morale | blueprint | role |
|---|--:|--:|--:|---|--:|--:|---|---|
| **Storage Facility** | 1,500 | 24 | 20 | 2x2 | 1 | 0 | start | Holds **300** ore units. |
| **Storage Tower** | 3,000 | 32 | 40 | 2x2 | 2 | 0 | start | Holds **600** ore units. |
| **Protected Storage Tower** | 7,500 | 32 | 48 | 2x2 | 3 | 0 | start | Holds **600**; has a built-in Laser Turret. |
| **Ore Teleporter** | 45,000 | 36 | 48 | 2x2 | 1 | 0 | 150,000 | Instant ore transfer; needed on both ends. |

## Defence

There is **no per-turret table for damage, range or rate of fire** in the game's
data. What the data holds for each defence building is its row below. The text
claims that damage rises Laser, Plasma, Photon, that the Photon Turret has a
longer ("optimised") range, and that the Turret Optimizer blueprint (240,000 Cr)
doubles the damage of every turret; none of these has a number in the code
**[text only]**. Turrets begin to track a hostile ship as soon as it fires on the
colony, fire back if powered, and need a Weapons Factory.

| building | cost | HP | days | size | MW | morale | blueprint | role [text] |
|---|--:|--:|--:|---|--:|--:|---|---|
| **Laser Turret** | 3,400 | 16 | 25 | 2x2 | 2 | 5 | start | General-purpose auto-tracking turret. |
| **Plasma Turret** | 5,500 | 20 | 30 | 2x2 | 3 | 8 | 40,000 | More firepower than the laser; efficient on power. |
| **Photon Turret** | 7,500 | 20 | 52 | 2x2 | 4 | 8 | 100,000 | The best energy weapon. |
| **Anti-Missile Pod** | 15,000 | 16 | 36 | 2x2 | 3 | 10 | 250,000 | Tracks and shoots down incoming warheads; individually inaccurate, so several per asteroid. Its actual effect on missiles is not found in the code **(?)**. |
| **Screen Generator** | 20,000 | 36 | 52 | 2x2 | 7 | 20 | 125,000 | Force field over neighbouring buildings; cuts damage to buildings under it (halved, rounded up, in the missile code). |
| **Missile Silo** | 4,300 | 15 | 32 | 2x2 | 0 | 0 | start | Builds and launches all missiles; stores 10 of each type [text] (doubled by the Missile Bay Extension). Needs 8 staff. |
| **Satellite Silo** | 5,000 | 10 | 24 | 2x2 | 1 | 0 | start | Builds and launches spy satellites. |

## Mining

Each mine needs **8 staff**. The three mines between them cover all
[ten ores](ore-and-mining.md).

| building | cost | HP | days | size | MW | blueprint | ores |
|---|--:|--:|--:|---|--:|---|---|
| **Mine** | 4,000 | 20 | 32 | 2x2 | 1 | start | Selenium, Asteros, Barium, Crystalite |
| **Deep Bore Mine** | 5,500 | 20 | 36 | 2x2 | 2 | start | Quazinc, Bytanium, Korellium, Dragonium |
| **Seismic Penetrator** | 26,500 | 24 | 42 | 3x3 | 3 | 120,000 | Traxium, Nexos |

## Construction and repair

| building | cost | HP | days | size | MW | morale | blueprint | role |
|---|--:|--:|--:|---|--:|--:|---|---|
| **Ship Yard** | 7,500 | 20 | 32 | 3x3 | 2 | 0 | start | Builds Assault Fighter, Combat Eagle, Scoutship (see [Vehicles](vehicles.md)). Needs 8 staff. |
| **Repair Facility** | 30,000 | 20 | 36 | 2x2 | 1 | 20 | 150,000 | Repair robots for buildings and hangared craft. |
| **Asteroid Engine** | 45,000 | 28 | 64 | 3x3 | 5 (engine setting) | 10 | 190,000 | Lets you steer the asteroid; stops without power. |
| **Gravity Nullifier** | 35,000 | 24 | 52 | 2x2 | 4 while on | 10 | 70,000 | Holds neighbouring asteroids still; must be off while engines run. |

The **Orbital Space Dock** is a craft, not a building: it is ordered through the
Command Center (see [Vehicles](vehicles.md)).

## Life support and workforce

| building | cost | HP | days | size | MW | morale | blueprint | what it does |
|---|--:|--:|--:|---|--:|--:|---|---|
| **Living Quarters** | 1,000 | 5 | 32 | 2x2 | 0 | 10 | start | Houses 50. |
| **Resiblock** | 3,000 | 10 | 48 | 2x2 | 0 | 20 | start | Houses 150. |
| **Air Processor** | 13,000 | 24 | 48 | 2x2 | 2 | 30 | start | Air for 400 employees. |
| **Hydroponics Plant** | 7,000 | 24 | 16 | 3x3 | 2 | 30 | start | Food for 300. |
| **Water (Hydration) Plant** | 5,000 | 20 | 20 | 2x2 | 1 | 30 | start | Water for 400. |
| **Environment Control** | 3,200 | 34 | 20 | 2x2 | 0 | 40 | start | Stores surplus: code **air 3,000 / food 1,000 / water 1,000** (text says 5,000 / 600 / 600). |
| **Radiation Filter** | 8,000 | 24 | 30 | 2x2 | 3 | 10 | start | Radiation level -3 each. |
| **Medical Center** | 5,000 | 15 | 30 | 3x3 | 1 | 30 | start | Radiation level -3 each; the text says care for 100 employees (not in the code). |
| **Pleasure Dome** | 5,000 | 10 | 32 | 3x3 | 1 | 40 | start | Unrest -2 per day each (text: 300 personnel). |
| **Security Center** | 4,500 | 15 | 24 | 2x2 | 2 | -20 | start | Crime -1 per day each (text: 150 employees). |

Population, supply, brownout and unrest formulas: [Colony economy](colony-economy.md).

## Staffing

**Mine, Deep Bore Mine, Seismic Penetrator, Ship Yard, Missile Silo and Command
Center each need 8 people**, filled from the colony population in that order. An
understaffed group does not work. **[code]**

## Brochure upgrades that change building numbers

| blueprint | price | effect |
|---|--:|---|
| Power Amplifier | 100,000 | solar types give double |
| Hi-Energy Power Stores | 30,000 | Power Store holds 400 |
| Building Armour | 110,000 | +10 HP on new buildings |
| Mk2 Mine / Mk2 Deep Bore Mine | 75,000 / 95,000 | extraction rate doubled |
| Construction Droids | 80,000 | 6 craft at once instead of 3; about 25% faster |
| Missile Bay Extension | 60,000 | silo storage doubled |
| Improved Sensors | 44,000 | sensors in all colonies; Sensor Arrays unnecessary |

Others (turret doubling, Asteroid Tracker, Missile Guidance) are on the
[Missiles](missiles.md) and [Ship-to-ship combat](ship-combat.md) pages.

## Power priority

When power is short, the lowest-priority buildings go dark first. Order from
safest to first cut is given on [Colony economy](colony-economy.md).

## Alien civilisations

Alien buildings are in the same table in the game's data. Their HP and build
days are plain values; **their cost field is only a function code (0 to 8), not a
price** — aliens build with production points (see
[Aliens and diplomacy](aliens-and-diplomacy.md)). The power column uses the
opposite sign for generators (positive = makes power, negative = uses it) **(sign
convention inferred)**. "Terran role" is the building's Terran counterpart; race
specific buildings have no counterpart. Every one of the 137 roles matched the
building's name and description.


### Rigellian buildings

| building | Terran role | HP | build days | footprint | power (+makes / -uses) |
|---|---|---|---|---|---|
| Central Unit | C.P.U. | 30 | 36 | 3x3 | 8 |
| Filtration Plant | Hydration Plant | 20 | 20 | 2x2 | -1 |
| Nourishment Bank | Hydroponics Plant | 10 | 20 | 2x2 | -1 |
| Community | Living Quarters | 20 | 48 | 2x2 | 0 |
| Health Unit | Medical Centre | 30 | 36 | 2x2 | -1 |
| Strategic Bunker | Command Centre | 45 | 34 | 3x3 | -3 |
| Science Labs | race-specific | 50 | 58 | 3x3 | -1 |
| Databanks | race-specific | 50 | 44 | 2x2 | -1 |
| Construction Unit | Ship Yard | 30 | 30 | 4x4 | -2 |
| Ground Deck | Landing Pad | 20 | 18 | 3x3 | 0 |
| Probe Launch | Satellite Silo | 30 | 24 | 2x2 | -1 |
| Deep Space Probes | Sensor Array | 30 | 36 | 2x2 | -1 |
| Gravitic Converter | Asteroid Engine | 10 | 46 | 2x2 | -4 |
| Energy Gatherer | Solar Matrix | 30 | 46 | 2x2 | 32 |
| Energy Globe | Power Store | 30 | 52 | 2x2 | 0 |
| Shield Generator | Screen Generator | 45 | 46 | 2x2 | -6 |
| Arms Unit | Weapons Factory | 40 | 30 | 3x3 | -3 |
| Missile Launcher | Missile Silo | 25 | 30 | 3x3 | 0 |
| Thermal Lance | Plasma Turret | 25 | 28 | 3x3 | -3 |
| Extractor | Mine | 35 | 42 | 2x2 | -2 |
| Storage racks | Storage Tower | 40 | 48 | 3x3 | -2 |
| Ex-Fang | race-specific | 45 | 48 | 4x4 | -4 |
| Ultrathermal Lance | Photon Turret | 45 | 57 | 3x3 | -3 |

### Braccatian buildings

| building | Terran role | HP | build days | footprint | power (+makes / -uses) |
|---|---|---|---|---|---|
| First Step | C.P.U. | 45 | 45 | 3x3 | 10 |
| Clan Heart | Command Centre | 55 | 73 | 3x3 | -2 |
| Radiation Shield | Radiation Filter | 16 | 30 | 3x3 | -1 |
| Source | Hydroponics Plant | 45 | 40 | 2x2 | -2 |
| Aesir's Hall | Air Processor | 30 | 50 | 2x2 | -1 |
| Longhouse | Living Quarters | 25 | 35 | 3x3 | 0 |
| Sports Hall | race-specific | 25 | 58 | 3x3 | 0 |
| Field Hospital | Medical Centre | 15 | 26 | 3x3 | -1 |
| Glasshouse | Security Centre | 15 | 22 | 2x2 | -2 |
| TechMech | Ship Yard | 40 | 45 | 3x3 | -3 |
| Launch Site | Landing Pad | 20 | 12 | 3x3 | 0 |
| Eyes-in-the-Sky | Satellite Silo | 25 | 24 | 2x2 | 0 |
| Eyes-and-Ears | Sensor Array | 25 | 35 | 2x2 | -1 |
| Anchor | Asteroid Engine | 30 | 65 | 2x2 | -5 |
| Heart-of-the-Sun | Solar Matrix | 35 | 50 | 2x2 | 40 |
| Aegis | Screen Generator | 35 | 50 | 2x2 | -5 |
| Forge | Weapons Factory | 60 | 57 | 3x3 | -3 |
| Anti-Battery | Anti-Missile Pod | 35 | 30 | 2x2 | -2 |
| Battery | Missile Silo | 35 | 30 | 3x3 | 0 |
| Turret | Photon Turret | 30 | 42 | 2x2 | -3 |
| Subterranean Extractor | Mine | 30 | 48 | 2x2 | -2 |
| Pithoi | Storage Tower | 30 | 56 | 2x2 | -1 |
| Fire Power | Plasma Turret | 30 | 32 | 2x2 | -4 |

### Mikotaj buildings

| building | Terran role | HP | build days | footprint | power (+makes / -uses) |
|---|---|---|---|---|---|
| Base Crystal | C.P.U. | 50 | 50 | 3x3 | 10 |
| Stability | Command Centre | 40 | 78 | 3x3 | -1 |
| Purity | Radiation Filter | 35 | 52 | 2x2 | -1 |
| Fulfilment | Hydroponics Plant | 30 | 50 | 2x2 | -1 |
| Internal | Living Quarters | 12 | 56 | 3x3 | -1 |
| Dream | race-specific | 40 | 38 | 3x3 | 0 |
| Resonance | race-specific | 50 | 66 | 3x3 | -5 |
| Fa-lanth | Screen Generator | 45 | 50 | 2x2 | -6 |
| Mask | race-specific | 30 | 80 | 2x2 | -2 |
| Structures Matrix | Ship Yard | 25 | 35 | 3x3 | -2 |
| Volition | Landing Pad | 10 | 18 | 2x2 | 0 |
| Visibility | Satellite Silo | 20 | 24 | 2x2 | -1 |
| Perception | Sensor Array | 20 | 36 | 2x2 | -2 |
| Capacitors | Solar Matrix | 35 | 40 | 2x2 | 38 |
| Lanth | race-specific | 50 | 55 | 2x2 | -3 |
| Sharir | Weapons Factory | 20 | 34 | 3x3 | -3 |
| Shrekn | Missile Silo | 10 | 32 | 2x2 | 0 |
| Ruth-feror | Mine | 15 | 48 | 3x3 | -2 |
| Ruth-fett | Storage Tower | 10 | 40 | 2x2 | -2 |
| Merl | Plasma Turret | 15 | 35 | 2x2 | -3 |
| Na-Shrekn | Photon Turret | 20 | 57 | 2x2 | -3 |
| SoftCore | C.P.U. | 25 | 40 | 4x4 | 12 |

### Artemian buildings

| building | Terran role | HP | build days | footprint | power (+makes / -uses) |
|---|---|---|---|---|---|
| Environmental Stabiliser | Environment Control | 50 | 26 | 3x3 | -1 |
| Filtration Tanks | Hydroponics Plant | 50 | 30 | 3x3 | -2 |
| Canisters | Living Quarters | 20 | 46 | 2x2 | 0 |
| Nurseries | race-specific | 60 | 30 | 2x2 | 0 |
| Healing Quarters | Medical Centre | 15 | 26 | 2x2 | -1 |
| House of the Axe | race-specific | 35 | 48 | 3x3 | -1 |
| Naval Dockyard | Ship Yard | 45 | 56 | 3x3 | -3 |
| Launch Pads | Landing Pad | 20 | 18 | 2x2 | -1 |
| Deep Probes | Sensor Array | 25 | 34 | 2x2 | -1 |
| Gravitic Converter | Asteroid Engine | 20 | 50 | 3x3 | -6 |
| Shielded Solars | Solar Matrix | 35 | 46 | 2x2 | 26 |
| Shell | race-specific | 40 | 44 | 2x2 | -3 |
| Arms Forge | Weapons Factory | 50 | 36 | 3x3 | -4 |
| Star Bars | Anti-Missile Pod | 23 | 34 | 2x2 | -2 |
| Missile Launcher | Missile Silo | 35 | 30 | 2x2 | 0 |
| Auto-deterrent | Plasma Turret | 40 | 28 | 2x2 | -2 |
| Super-deterrent | Photon Turret | 40 | 48 | 3x3 | -1 |
| Force Fields | Screen Generator | 30 | 30 | 2x2 | -4 |
| Advanced Ore Extractor | Deep Bore Mine | 30 | 34 | 3x3 | -1 |
| Rare Ore Extractor | Seismic Penetrator | 35 | 40 | 3x3 | -2 |
| Ore Depot | Storage Tower | 25 | 24 | 2x2 | -1 |
| Refining Forge | race-specific | 35 | 38 | 3x3 | -1 |

### Maunid (Mauna) buildings

| building | Terran role | HP | build days | footprint | power (+makes / -uses) |
|---|---|---|---|---|---|
| Base Block | C.P.U. | 50 | 35 | 3x3 | 22 |
| Shielding Block | Radiation Filter | 20 | 30 | 3x3 | -1 |
| Nutrition Block | Hydroponics Plant | 20 | 26 | 3x3 | -1 |
| Off-duty Block | Living Quarters | 20 | 24 | 2x2 | 0 |
| Health Block | Medical Centre | 10 | 16 | 2x2 | 0 |
| The Cube | race-specific | 30 | 30 | 3x3 | 0 |
| Elite Block | Sensor Array | 60 | 56 | 3x3 | -4 |
| Construction Area | Ship Yard | 50 | 32 | 4x4 | -3 |
| Launch Area | Landing Pad | 40 | 18 | 2x2 | 0 |
| Satellite Pad | Satellite Silo | 45 | 24 | 3x3 | -1 |
| Fast Breeder Reactor | Solar Matrix | 35 | 52 | 2x2 | 50 |
| Arms Block | Weapons Factory | 50 | 36 | 4x4 | -5 |
| Defence Pods | Anti-Missile Pod | 40 | 34 | 2x2 | -3 |
| Attack Pods | Missile Silo | 40 | 34 | 2x2 | -1 |
| Pulse Tower | Plasma Turret | 40 | 32 | 2x2 | -4 |
| Screening Pods | Screen Generator | 30 | 34 | 2x2 | -8 |
| Advanced Extraction Unit | Deep Bore Mine | 30 | 38 | 3x3 | -2 |
| Superior Extraction Unit | Seismic Penetrator | 40 | 44 | 3x3 | -3 |
| Ores Block | Storage Tower | 50 | 32 | 2x2 | -2 |
| Motion Units | Asteroid Engine | 60 | 66 | 2x2 | -5 |
| Laser Boost | Photon Turret | 45 | 28 | 2x2 | -4 |

### Achaean buildings

| building | Terran role | HP | build days | footprint | power (+makes / -uses) |
|---|---|---|---|---|---|
| Footprint | C.P.U. | 38 | 50 | 3x3 | 2 |
| Anti-Rad Screen | Radiation Filter | 15 | 32 | 2x2 | -1 |
| Environmental Control | Environment Control | 15 | 36 | 2x2 | -1 |
| Filtration Vats | Hydration Plant | 30 | 38 | 2x2 | -1 |
| Nutrient Vats | Hydroponics Plant | 30 | 40 | 2x2 | -1 |
| Habitat | Living Quarters | 25 | 56 | 2x2 | 0 |
| Pharmacopeion | Medical Centre | 15 | 30 | 3x3 | -1 |
| Gathering Ground | race-specific | 45 | 68 | 3x3 | 0 |
| Market | race-specific | 45 | 76 | 3x3 | 0 |
| Communications Central | Command Centre | 50 | 36 | 3x3 | -2 |
| Shipyard | Ship Yard | 30 | 45 | 3x3 | -4 |
| Landing Pad | Landing Pad | 10 | 18 | 2x2 | 0 |
| Missile Launcher | Missile Silo | 40 | 34 | 2x2 | 0 |
| Data Gatherer | Satellite Silo | 15 | 28 | 3x3 | -1 |
| Listening Device | Sensor Array | 20 | 40 | 2x2 | -2 |
| Manoeuvring Device | Asteroid Engine | 35 | 68 | 2x2 | -6 |
| Destination Beam | race-specific | 50 | 100 | 2x2 | -3 |
| Reactor Cores | Solar Matrix | 25 | 40 | 2x2 | 66 |
| Asteroid Shield | Screen Generator | 26 | 46 | 2x2 | -6 |
| Defence Battery | Anti-Missile Pod | 30 | 36 | 2x2 | -2 |
| Commonbore | Mine | 16 | 44 | 3x3 | -1 |
| Deepbore | Seismic Penetrator | 25 | 42 | 3x3 | -3 |
| Ore Yard | Storage Tower | 35 | 44 | 2x2 | -1 |
| Goods Yard | race-specific | 45 | 40 | 2x2 | 0 |
| Stun Tower | Laser Turret | 18 | 26 | 2x2 | -2 |
| Power Tower | Photon Turret | 20 | 50 | 2x2 | -3 |

Descriptive names for the race-specific extras (text): the Rigellian Science Labs,
Databanks and Ex-Fang; Braccatian Sports Hall; Mikotaj Dream, Resonance, Mask and
Lanth (a cloaking device); Artemian Nurseries, House of the Axe, Shell and
Refining Forge; Maunid The Cube; Achaean Gathering Ground, Market, Destination
Beam and Goods Yard. The Braccatian "Fire Power" (Plasma-class) is described as
possibly the most accurate turret weapon in the game; the Maunid "Power Tower" as
more deadly than the Photon Turret.

## Open questions

- The reading of the one-off morale values and the Living Quarters (+10) and
  Security Center (-20) signs.
- The Anti-Missile Pod's interception effect (no code found).
- Per-turret damage, range and rate of fire (no table; may be a code constant
  in unrecovered ship-combat code).
- What the Protected Solar Matrix needs as a blueprint.

*Related: [Colony economy](colony-economy.md); [Vehicles](vehicles.md);
[Ores and mining](ore-and-mining.md); [Asteroids](asteroids.md);
[Asteroid spawning](asteroid-spawning.md); [Missiles](missiles.md).*
