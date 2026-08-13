---
title: Buildings
---

# Buildings

*Status: every building's description is taken from the game's own text resource
(`_TEXT/AMERICAN.TXT`, the same resource the game displays). The effects below
are therefore the game's own words. The per-building Money cost, build time,
power use and numeric stats have **not** been read out of the game yet — they
are only known where the text gives a number (the megawatt figures, ore
capacities). A runtime memory trace of the GOG retail build is the route to the
rest; see [Open questions](#open-questions).*

The structures a colony is built from fall into three groups:

- **Always-available buildings** — you can build these on any colony without
  buying anything first. They are the bulk of the catalogue.
- **Brochure buildings** — these must be unlocked by ordering their blueprint
  from the Sci-Tek brochure (Money budget); until then they cannot be built.
  The brochure also sells permanent upgrades that improve whole families of
  buildings at once.
- **Alien equivalents** — every alien civilisation fields its own buildings that
  match the Terran ones. They are listed at the end.

A colony is laid out on the [asteroid surface grid](asteroid-spawning.md); each
building occupies cells on that grid and is built through the colony interface.
Most buildings need [power](#power-generation-and-storage) to function — a
building with no power simply does not work. Some buildings must exist before
others can be built (a Weapons Factory is required before any turret works; a
Weapons Factory is itself built only after a Landing Pad and the colony's first
CPU). Construction time is measured in days, and a build can stall
if the Money budget, the ores, or the workforce run out. Damaged buildings can
be repaired by the Repair Facility.

The tables below are grouped by role. The description column condenses the
game's own text to the mechanically relevant parts.

## Colony essentials

The first things a colony needs.

| building | source | cost | role |
|---|---|---|---|
| **CPU** (Colony Preservation Unit) | built automatically by the Transporter when founding a colony | — | Establishes a minimum survival colony. Produces air, food and water, but all three degrade by **1 unit per day** until they reach zero — the CPU is meant to be phased out once real buildings are up. Cannot be built manually. |
| **Landing Pad** | always available | — | The access point to the underground hangars. Idle ships should be kept in the hangars — they are safe there and are repaired if a Repair Facility exists. |
| **Command Center** | always available (large) | — | Houses the strategic computers that relay and collate sensor data; the only way to contact larger ships in transit between asteroids. **You cannot command any fleet without at least one Command Center.** One Command Center can oversee any number of colonies, so its location is unimportant. |
| **Weapons Factory** | always available (large) | — | Colony essential. Provides the engines for **all** spacecraft and enables the manufacture of every hardpoint weapon and missile warhead. **Turrets do not function without a Weapons Factory** to maintain and supply them. One suffices for a whole colony. |
| **Sensor Array** | always available | — | Extends the colony's sensor range (the CPU's built-in sensors are limited). Earlier and more accurate information on approaching asteroids and hostile fleets. |

## Power generation and storage

Every building that consumes power depends on these. The **Power Amplifier**
brochure blueprint doubles the output of all solar generators.

| building | source | cost | role |
|---|---|---|---|
| **Solar Panel** | always available | — | The cheapest, quickest array: **2 MW**, constant flow. Compatible with the Power Amplifier. |
| **Solar Generator** | always available | — | More efficient than the Solar Panel: **8 MW**, space-efficient. Compatible with the Power Amplifier. |
| **Solar Matrix** | brochure | — | Large solar array: **12 MW**, or **24 MW** with the Power Amplifier. Small footprint, useful on small asteroids. |
| **Powerplant** | brochure | — | Fusion plant. Burns Asteros: **32 MW** if ample Asteros is available (uses **1 unit of Asteros every 4 days**); without Asteros only **8 MW** from lesser ores. |
| **Power Store** | always available | — | Each holds **200 MW** of unused surplus for later use — a backup if generation is lost. Brings up a list of buildings that are without power. |
| **Refueling Depot** | always available | — | Generates the power to recharge the fuel crystals ships run on. Without it, ships' working life is shortened and Transporters cannot travel far enough to found new colonies. |

## Storage and transport

| building | source | cost | role |
|---|---|---|---|
| **Storage Facility** | always available | — | Stockpiles all ores for sale or use. Holds up to **300 units**. Conveyor belts move ore from mines to wherever it is needed. |
| **Protected Storage Tower** | always available | — | As the Storage Facility but holds up to **600 units** and carries an integral **Laser Turret** (prime target for attack — protect it). |
| **Ore Teleporter** | brochure | — | Instant ore transfer between asteroids. A Teleporter is needed on **both** ends; one on every asteroid gives best results. |

## Defence

Turrets use a motion-detection sensor that automatically tracks any hostile
ship as soon as it fires on the colony, then returns fire — assuming the
colony has [power](#power-generation-and-storage). They are maintained by the
Weapons Factory.

| building | source | cost | role |
|---|---|---|---|
| **Anti-Missile Pod** | brochure | — | Automated defence that tracks and shoots down incoming warheads. Compact but individually inaccurate — **several per asteroid** are advised. |
| **Screen Generator** | brochure | — | Projects a protective force field over **neighbouring** buildings, absorbing most energy from most weapons including inter-asteroid missiles. Several advised to cover important buildings. |
| **Laser Turret** | always available | — | General-purpose auto-tracking defence turret. |
| **Plasma Turret** | brochure | — | Greater fire-power than the Laser Turret, efficient on power. |
| **Photon Turret** | brochure | — | The best energy weapon. Fires photon packets "capable of devastating armor"; accuracy beyond compare. |
| **Missile Silo** | always available | — | Constructs and launches all missile types; also constructs and launches **spy satellites**. Each silo stores **10 of each missile type** (110 total). More silos raise the launch rate. |

## Mining

The three mines between them cover all [ten ores](ore-and-mining.md). The
**Seismic Penetrator** brochure blueprint unlocks the only mine that reaches the
two rarest ores.

| building | source | cost | role |
|---|---|---|---|
| **Mine** | always available | — | Extracts the four common ores (Selenium, Asteros, Barium, Crystalite). |
| **Deep Bore Mine** | brochure | — | Extracts the four valuable ores (Quazinc, Bytanium, Korellium, Dragonium). |
| **Seismic Penetrator** | brochure | — | Extracts the two rarest ores (Traxium, Nexos). |

(The **Mk2 Mine** and **Mk2 Deep Bore Mine** brochure blueprints double the
extraction rate of all existing and future Mines / Deep Bore Mines.)

## Construction and repair

| building | source | cost | role |
|---|---|---|---|
| **Ship Yards** | always available | — | Builds the small craft: Assault Fighter, Combat Eagle, Scoutship. Small craft landed in the hangars are repaired if a Repair Facility exists. (See [Vehicles](vehicles.md).) |
| **Orbital Space Dock** | built through the Command Center | — | Builds the larger craft (Transporter, Destructor, and any blueprinted warships). One per asteroid. (See [Vehicles](vehicles.md).) |
| **Repair Facility** | brochure | — | Constructs and directs maintenance robots that repair colony buildings. Also repairs small craft in the hangars, and large craft left to patrol from the Orbital Space Dock. |

(The **Construction Droids** brochure blueprint lets a Ship Yards or Space
Dock build **six** craft at once instead of three and speeds construction by
about **25%**.)

## Life support and workforce

The CPU degrades; these replace and expand its provisions. The
[Asteroids](asteroids.md) and [Ore and mining](ore-and-mining.md) pages explain
the economy they feed.

| building | source | cost | role |
|---|---|---|---|
| **Living Quarters** | always available | — | Basic housing. Quick to build but fragile and does little for morale; the Company recommends upgrading as soon as feasible to limit disorder and keep workers motivated. |
| **Radiation Filter** | brochure | — | Screens out the heavier radioactive particles; protects employees inside colony buildings from the sickness and lost production that high background radiation causes. |
| **Hydroponics** | always available | — | Grows food from high-protein algae; feeds up to **300** workers. |
| **Water Plant** | always available | — | Extracts water and oxygen from deep asteroid ice; provides for up to **400** workers. |
| **Medical Center** | brochure | — | Full hospital: routine and emergency care for up to **100** employees; handles rapid virus outbreaks and low-dose radiation. |
| **Environmental Control** | always available | — | Stores surplus air, food and water (up to **5 000** air, **600** food, **600** water) and monitors production to keep every section supplied. |
| **Pleasure Dome** | brochure | — | Entertainment (interactive, bars, sports) for up to **300** personnel at once — raises morale and reduces anti-social behaviour. |
| **Security Center** | brochure | — | Highly trained teams that step in when management and the workforce clash. Strongly advised to limit civil disorder and keep workers motivated. |

## Alien civilisations

Every alien race fields its own buildings that correspond to the Terran set.
The game names them all; the broad correspondences (the details differ per
race) are:

- **Rigellian** — Central Unit (CPU), Strategic Bunker (Command Center +
  information-gathering), Construction Unit (Ship Yards), Ground Deck
  (Landing Pad), Probe Launch (Missile Silo / satellites), Deep Space Probes
  (sensors), Gravitic Converter (Asteroid Engines + Gravity Nullifier),
  Energy Gatherer (Powerplant), Energy Globe (Power Store), Shield Generator
  (Screen Generator), Arms Unit (Weapons Factory), Missile Launchers (Missile
  Silo), a single **Extractor** for all mining, Storage Racks, Ex-Fang and
  Ultrathermal Lance (turrets), Anti-Battery (Anti-Missile Pod), Thermal Lance
  (basic turret).
- **Braccatian** — First Step (CPU), Clan Heart (Command Center + Council of
  Elders), TechMech (Ship Yards), Launch Site (Landing Pad), Eyes-in-the-Sky
  (satellite silo), Eyes-and-Ears (sensors), Anchor (Gravity Nullifier),
  Heart-of-the-Sun (fusion power), Aegis (Screen Generator), Forge (Weapons
  Factory), Battery (Missile Silo), Fire Power (≈ Plasma Turret, the most
  accurate), a single **Subterranean Extractor** for all mining, Pithoi
  (storage towers), Anti-Battery (Anti-Missile Pod).
- **Mikotaj** — Base Crystal (CPU), Structures Matrix (Ship Yards), Volition
  (Landing Pad), Visibility (satellite silo), Perception (sensors, the most
  sensitive in the Federation), Capacitors (store the mental energy that powers
  the colony), Sharir (Weapons Factory), Shrekn (Missile Silo), Merl (≈ Plasma
  Turret), Na-Shrekn (≈ Photon Turret), Lanth (cloaking device), a single
  **Ruth-feror** for all mining, Ruth-fett (storage).
- **Artemian** — Community (CPU), Healing Unit (Command Center), Resonance
  (power generation), Construction Yard (Ship Yards), Launch Pad, Perception
  (sensors), individual **Extractors** (mining), individual **Storage Towers**,
  Star Bars (basic turret), Auto-deterrent (shortest range), Super-deterrent (≈
  Photon Turret).
- **Maunid** — Temple (Command Center), Elite Block (Command Center + Sensor
  Array), individual **Extraction Units** (mining), Dome (Security Center),
  individual **Storage Buildings**, Stun Tower (basic defence), Power Tower (≈
  Photon Turret, "more deadly").
- **Achaean** — Communications Central (Command Center), Data Gatherer and
  Listening Device (sensors), individual **Commonbore / Deepbore** mines,
  Dockyard (Command Center + Construction Yard), individual **Storage
  Buildings**, Asteroid Shield / Defence Battery.

(The Terran building descriptions above are ground truth; the alien
correspondences are summarised from the same text resource.)

## Open questions

- The **Money cost, build time, power draw and numeric stats** (footprint,
  armour, turret damage / range) for each building are not yet extracted. They
  live in the game's per-type tables, which are written to memory only while the
  colony **building-placement** view is active. None of the currently captured
  runtime dumps were taken at that view (they are main-menu and Ship-Yards dumps),
  so the values are not present in any dump on hand. Capturing a fresh dump while
  the building-placement screen is open (the snapshot tooling already exists) is
  the route to read them. A separate static table of 16 stat records with costs
  exists, but its ids do not index the known building types, so it is a different
  table family and not the building stats.
- Whether morale / civil order is a numeric mechanic or purely flavour is not
  settled; the Security Center and Living Quarters texts imply one but the
  mechanics are not yet confirmed.
- Exact build prerequisites beyond the Weapons Factory / turret link described
  above; the per-building requirement lists are believed to live in the
  terrain-record table that has not yet been recovered.

*Related: [Vehicles](vehicles.md) — the craft built in the Ship Yards and
Orbital Space Dock; [Ores and mining](ore-and-mining.md) — the ores the mines
extract and the economy they feed; [Asteroids](asteroids.md) — the surface
grid buildings sit on; [Asteroid spawning](asteroid-spawning.md) — how the
field and its colonies are generated.*
