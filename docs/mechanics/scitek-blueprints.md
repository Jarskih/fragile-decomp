# Sci-Tek blueprints: the catalogue and what each item does

Status: confirmed — the catalogue contents, categories and per-item effects
from the game's own text resource; the ordering/delivery flow from the same;
the three price tables fully decoded as static data in both builds (per-item
name mapping still open).
Source: game text resource (`_TEXT/AMERICAN.TXT`, the same resource the game
displays) + the static price tables in both builds' flats + the GOG runtime
memdump (`build/dumps/ram_1ce2a000.bin`).

This is the game's technology progression. There is **no research mechanic** —
no research centres, no research topics, nothing called research in the UI.
(The word "research" appears only in lore: Rigellian Science Labs/Databanks
flavour and the Mega Missile's back-story.) Instead, technology advances by
**ordering blueprints from the Sci-Tek brochure**; each blueprint either
permanently upgrades everything of one kind, or unlocks one new construction
option. The predecessor game MAX (demo on the same CD) does have research
centres, but that is a different game.

## What the system is

- The Sci-Tek Brochure is the ordering screen ("Accesses the Sci-Tek brochure
  where you can order the blueprints for new items, e.g. special ships and
  buildings", TXT 44582). The brochure is organised into **sections**; the
  help text attests a "Mining section" (where the Seismic Penetrator lives)
  and a "DefenSe section" (Anti-Missile Pods) (TXT 56856). The other
  sections' names are not attested in this resource (?).
- Blueprints are bought with the Money budget ("When you buy items from
  Sci-Tek or from black market traders, the cost will be deducted from the
  Money budget", TXT 2912).
- The ordering UI: an "ORDER BLUEPRINT" button (TXT 56693/56755); an item
  already owned shows faded, an item on order shows "ON ORDER" (TXT 57342).
- Delivery: the order is announced by the message "Blueprints have arrived"
  (TXT 24195), "The following blueprints have arrived:" (TXT 24219). The
  delivery delay (in days) is carried by the days columns of the price
  tables (see below).
- Spy counterplay: agents of hostile races can steal blueprints — the
  "Sci-Tek blueprint theft" event: "Thieves on Colony Asteroid %s have stolen
  the %s blueprint." (TXT 40100/40124).
- TetraCorp already provides the Transporter and Destructor blueprints free;
  "any other blueprints must be purchased from Sci-Tek" (TXT 2299).
- In the demo on the reference ISO, only the Seismic Penetrator and the
  Anti-Missile Pods can actually be ordered (TXT 56856) — the full catalogue
  text is still present in the resource.

Two different things are both called "blueprint" in the game text: (a) the
Sci-Tek brochure items described here, and (b) the **ship design blueprints**
shown on the Ship Yards hardpoint screen ("PREVIOUS BLUEPRINT"/"NEXT
BLUEPRINT", "To place a hardpoint onto the ship; click the red boxes on the
blueprint", TXT 53248/53789) — that is the hardpoint-editing view of a ship
class, not a purchasable item (see `vehicles.md`).

## The catalogue — all 38 entries (TXT 121141–121727)

The brochure list in the game's own order, with the short description
(121748–125384) and long description (125384–140084) token offsets. Effects
below are summarised from those texts.

### Permanent upgrades (14)

| item | TXT (name / short / long) | effect (from game text) |
|---|---|---|
| Mk2 Mine | 121141 / 121748 / 125384 | Doubles the extraction rate of all Mines, existing and future. |
| Mk2 Deep Bore Mine | 121150 / 121844 / 125625 | Doubles the extraction rate of all Deep Bore Mines, existing and future. |
| Asteroid Tracker | 121222 / 122252 / 127442 | Installs tracking on all colonies; the asteroid-field screen can display the path and speed of every known asteroid. Also adds a strike-accuracy estimate to the missile targeting screen (TXT 9148). |
| Building Armor | 121239 / 122375 / 127688 | Strengthens all buildings against meteor strikes and enemy attacks; the armour material is a by-product of the hydroponics process. |
| Construction Droids | 121254 / 122475 / 128030 | Ship Yards and Orbital Space Docks can build **6** craft at once instead of 3, and construct **25%** faster. |
| Hi-Energy Power Stores | 121319 / 122898 / 129917 | Doubles the capacity of all Power Stores, existing and future. |
| Improved Sensors | 121342 / 122985 / 130094 | Sensors are installed on all existing colonies and built into future CPUs; Sensor Arrays become unnecessary. |
| Missile Bay Extension | 121372 / 123185 / 131163 | Doubles missile storage on each asteroid (the silo loading-rack system; per-silo storage doubles). |
| Missile Guidance System | 121394 / 123273 / 131513 | Missile strike accuracy +25%. |
| Power Amplifier | 121477 / 123713 / 133153 | Doubles the output of all solar-power generators, existing and future (Solar Panels, Solar Generators, Solar Matrices). |
| Turret Optimizer | 121632 / 124793 / 137924 | Doubles the damage of all turrets, existing and future. |
| Long Range Transmitter | 121678 / 125135 / 139112 | Long-range two-way contact for small craft (Scoutships); automatically installed in all **new** craft — cannot be retrofitted. |
| Scrambler | 121717 / 125353 / 140053 | **No description in this resource** — both the short and long slots hold placeholders ("Scrambler", "Long description for Scrambler"). Effect unknown (?). |
| Double Speed Engines | 121727 / 125363 / 140084 | **No description in this resource** — both slots hold placeholders. The name suggests doubling Asteroid Engine performance, but this is inference, not confirmed (?). |

### Buildings (11) — unlocks the building for construction

| item | TXT (name / short / long) | effect (from game text) |
|---|---|---|
| Anti-Missile Pod | 121169 / 121950 / 125868 | Automated defence pod that tracks and shoots down incoming warheads before they reach the asteroid; compact but individually inaccurate — several per asteroid advised. |
| Asteroid Engines | 121205 / 122130 / 126957 | Gives the asteroid an engine: exact direction and speed can be specified; without power the asteroid stops. |
| Gravity Nullifier | 121301 / 122808 / 129375 | Creates a gravity field holding this and neighbouring asteroids stationary; must be off while Asteroid Engines operate; field collapses without power. |
| Ore Teleporter | 121434 / 123469 / 132171 | Instant ore transfer between asteroids — an Ore Teleporter is needed on **both** ends. |
| Photon Turret | 121449 / 123533 / 132396 | The best energy weapon; fires photon packets "capable of devastating armor". |
| Plasma Turret | 121463 / 123631 / 132863 | Greater fire-power than the Laser Turret, efficient on power. |
| Powerplant | 121493 / 123808 / 133442 | Fusion power plant, up to 32 MW from Asteros ore (1 unit of ore per 4 days); without Asteros, only 8 MW from lesser ores. |
| Repair Facility | 121504 / 123901 / 133991 | Constructs and directs maintenance robots that repair colony buildings (and craft in hangars); shows building armour/damage status. |
| Screen Generator | 121520 / 123957 / 134450 | Projects a force field over neighbouring buildings, absorbing a high percentage of energy from most weapons including inter-asteroid missiles. |
| Seismic Penetrator | 121537 / 124048 / 134911 | The only mine able to extract Traxium and Nexos. |
| Solar Matrix | 121578 / 124372 / 136012 | Large solar array: 12 MW, or 24 MW with a Power Amplifier. |

### Ships (3) — unlocks the craft for construction

| item | TXT (name / short / long) | effect (from game text) |
|---|---|---|
| Fleet Battleship | 121284 / 122681 / 128921 | The most powerful warship available; 92 m, **6** weapon hardpoints; designed 2364 by R. Giggs; the primary warship of Sci-Tek and TetraCorp. |
| Terminator | 121621 / 124684 / 137429 | Very effective warship, greater armour than existing ships, **4** hardpoints; T-15 model in Federal Marine service, designed 2321. |
| Command Cruiser | 121701 / 125238 / 139568 | The largest ship: strongly armed and armoured, **6** hardpoints, carries up to 20 smaller fighters, tows a number of medium craft, long range (extends fleet range). |

### Missiles (5) — unlocks the warhead for construction

| item | TXT (name / short / long) | effect (from game text) |
|---|---|---|
| Anti-Virus Missile | 121186 / 122038 / 126401 | Halts the spread of an asteroid virus, neutralises it, and slowly reverses the mutated areas; "then itself" (the missile is consumed); leaves increased radiation. |
| Mega Missile | 121359 / 123084 / 130588 | Destroys an entire asteroid (reduces it to rubble). "Use with care!" |
| Nuclear Missile | 121418 / 123363 / 131841 | Multi-megaton warhead: destroys most structures on the target and damages ships in orbit; radiation renders the asteroid uninhabitable for many years. |
| Stasis Missile | 121606 / 124569 / 136939 | Temporal physics warhead: freezes the target asteroid — nothing can happen inside the field, no arrivals/departures — until the field decays. |
| Virus Missile | 121649 / 124885 / 138353 | Deposits a volatile radioactive substance that spreads across the asteroid, destabilising the rock; buildings cannot stand on it and are destroyed as it spreads. |

### Hardpoints (5) — unlocks the ship module

| item | TXT (name / short / long) | effect (from game text) |
|---|---|---|
| Deflector | 121274 / 122575 / 128548 | Energises the hull, deflecting most energy attacks; can be used with existing shields. |
| Static Inducer | 121591 / 124481 / 136499 | Emits a periodic EMP beam scrambling enemy ships' electronics — during the pulse hostile craft cannot attack or move; friendly craft are protected by an attunement burst. |
| Warp Generator | 121663 / 124999 / 138654 | Periodically phases the ship out of space, rendering it temporarily invulnerable; pulsed on and off (cannot be maintained permanently). |
| Shield x40 | 121556 / 124168 / 135412 | Fills one hardpoint; +40 armour points. |
| Shield x50 | 121567 / 124270 / 135718 | Fills one hardpoint; +50 armour points; "renders a ship almost (but not quite) invulnerable"; the blueprint costs 60,000 Cr. |

Not in the brochure (always available at the Ship Yards): the basic
ship-yard weapon/module family — Ion Cannon, Disruptor, Napalm Orb, Chaos
Bomb, Vortex Mine, Laser, Photon Cannon, Plasma Cannon, Shield x10/x20/x30
(TXT 120957–121141; prices 1000–12000 Cr — see
`weapon-and-turret-numbers.md`, "The item price catalog").

## The ordering/delivery flow (game text)

1. Open the brochure (icon help, TXT 44582), browse the sections, pick an
   item, press ORDER BLUEPRINT (56693/56755).
2. The price is deducted from the Money budget (2912).
3. Owned items are shown faded; items on order show "ON ORDER" (57342).
4. Delivery is announced: "Blueprints have arrived" / "The following
   blueprints have arrived:" (24195/24219). The delivery delay (in days)
   is carried by the days columns of the price tables (see below; the
   exact delivery scheduling code is not yet located).
5. A hostile agent can steal a blueprint (40100/40124); the blueprint theft
   message names the colony and the lost blueprint.

## The price tables — full decode (both builds)

Three tables carry the catalogue's money/days numbers. All three are **static
data, byte-identical between the ISO build and the GOG build** (verified by
direct comparison, 2026-08-10) — the earlier "tables in code" anomaly does
not affect them. What the numbers mean per item is still partly open, but the
tables themselves are now fully read out.

### 1. Blueprint price pairs `{price u32, type u32}` — ISO 0xC1638 / GOG 0xB72E4

The GOG table is the ISO table's tail: the ISO build carries 14 extra
front entries (marked *I* — present in the ISO build only; the GOG build
lacks those 11 types). Prices are the **Money-budget cost of the
blueprint**; the type column is the item's internal type id (the game's
string/description tables are keyed by the same ids). The two 60,000-Cr
entries (type 15 and 28) match the text "…all for a mere 60,000 Cr too!"
(TXT 135718, the Shield x50 blueprint) — the Shield x40/x50 blueprints.

| type | price | | type | price | | type | price |
|---|---|---|---|---|---|---|
| 0 | 120,000 | | 13 | 0 | | 26 | 15,000 |
| 1 | 75,000 | | 14 | 90,000 | | 27 | 40,000 |
| 2 | — (no entry) | | 15 | 60,000 | | 28 | 60,000 |
| 3 | 350,000 | | 16 | 500,000 | | 29 | 300,000 |
| 4 | 70,000 | | 17 | 95,000 | | 30 | 0 *I* |
| 5 | 44,000 | | 18 | 250,000 *I* | | 31 | 40,000 *I* |
| 6 | 240,000 *I* | | 19 | 100,000 *I* | | 32 | 150,000 |
| 7 | 40,000 | | 20 | 50,000 | | 33 | 115,000 *I* |
| 8 | 250,000 *I* | | 21 | 30,000 | | 34 | 150,000 |
| 9 | 90,000 *I* | | 22 | 80,000 | | 35 | 150,000 *I* |
| 10 | 0 | | 23 | 110,000 *I* | | | |
| 11 | 0 | | 24 | 0 | | | |
| 12 | 190,000 | | 25 | 75,000 *I* | | | |

35 of the 36 types 0..35 are present (type 2 absent); five carry price 0
(types 10, 11, 13, 24, 30 — free/sentinel, role open). The 36-entry span
matches the "36 blueprints" figure in `docs/mechanics/README.md`; the
catalogue carries 38 text tokens — the two extra are Scrambler and Double
Speed Engines, whose descriptions are placeholders (see open questions).
Which type id names which catalogue item is **not yet confirmed** — the type
ids are shared with the per-type description/stat tables, whose keying the
code builds at runtime.

### 2. Ship Yards per-item records — ISO 0x99248 / GOG 0x90B60 (10 × 20 B)

`{u16 ×6, text-offset u16, days u16, price u32}`. The text-offset column
resolves against the runtime **Ship Yards help-string table** — a rebuilt
string pool at runtime 0x2903AA (GOG memdump `build/dumps/ram_1ce2a000.bin`)
holding the Ship Yards tutorial paragraphs in 512-byte slots, with strings
longer than 100 characters split into 100-char chunks at +0x65. The even
records' offsets resolve to the first five Ship Yards help paragraphs ("A
Weapons Factory and Ship Yards are required…", "Click on the building to
access the Ship Yards.", "Click on the Build icon…", "Small craft can be
constructed in the Ship Yards…", "All available ship types have a number of
hardpoints…") — records 0/2/4 hit the string starts, records 6/8 land a few
bytes in. The odd records' offsets land on padding — unresolved (?).

| rec | u16 fields (a..f) | textoff | days | price |
|---|---|---|---|---|
| 0 | 160, 1044, 5121, 512, 3, 0 | 2 | 25 | 6,000 |
| 1 | 160, 1044, 7682, 1024, 3, 0 | 260 | 30 | 12,000 |
| 2 | 192, 773, 5121, 1024, 3, 0 | 514 | 20 | 3,000 |
| 3 | 160, 552, 12291, 2048, 3, 0 | 774 | 50 | 15,000 |
| 4 | 160, 562, 15364, 2048, 7, 0 | 1026 | 50 | 34,000 |
| 5 | 192, 552, 25602, 1536, 7, 0 | 1281 | 30 | 24,000 |
| 6 | 160, 582, 20486, 2048, 7, 0 | 1542 | 60 | 60,000 |
| 7 | 0, 120, 28164, 2565, 7, 0 | 1807 | 70 | 150,000 |
| 8 | 320, 762, 30726, 2562, 6, 0 | 2066 | 70 | 300,000 |
| 9 | 320, 1025, 4096, 514, 0, 0 | 2304 | 0 | 10,000 |

Interpretation: the Ship Yards **craft roster** — 10 records, prices
6,000–300,000 Cr, days 0–70 (build time or delivery; the last record's 0
days suggests the "instant" Spy Satellite or similar). Which record maps to
which craft is **not yet confirmed** (a runtime look at the live Ship Yards
screen settles it; deferred).

### 3. The 12-record stat table — ISO 0x9806C / GOG 0x8F984 (12 × 12 B)

`{price u32, 3 packed stat bytes, days u32}`:

| rec | price | stat bytes (a,b,c) | days |
|---|---|---|---|
| 0 | 150,000 | 0x0C, 0x50, 0x1E | 20 |
| 1 | 60,000 | 0x0C, 0x41, 0x64 | 40 |
| 2 | 50,000 | 0x0C, 0x50, 0x28 | 30 |
| 3 | 75,000 | 0x19, 0x28, 0xC8 | 100 |
| 4 | 350,000 | 0x19, 0x32, 0x50 | 90 |
| 5 | 500,000 | 0x14, 0x37, 0x32 | 50 |
| 6 | 130,000 | 0x12, 0x37, 0x14 | 40 |
| 7 | 110,000 | 0x12, 0x37, 0x28 | 60 |
| 8 | 190,000 | 0x14, 0x37, 0x32 | 50 |
| 9 | 200,000 | 0x11, 0x37, 0x32 | 60 |
| 10 | 90,000 | 0x19, 0x28, 0x50 | 60 |
| 11 | 130,000 | 0x14, 0x37, 0x8C | 50 |

The prices (90,000–500,000) are the same family as the pair table's; the
days (20–100) look like construction build times. The three stat bytes are
small numbers (12–25, 40–80, 20–200) — stat candidates, role open.

- None of the catalogue text (names, descriptions) is stored in the EXE —
  it all lives in `_TEXT/AMERICAN.TXT` and is loaded at runtime (the same
  arrangement as the rest of the game's UI text). The loaded copy is a
  rebuilt string pool (base 0x6C7AB8 in the GOG memdump, file-ordered apart
  from single-byte drift); the Ship Yards help strings live in a separate
  512-byte-slot table (0x2903AA in the same dump).

## Open questions

- The effects of **Scrambler** and **Double Speed Engines**: both description
  slots are placeholders in the reference ISO's text resource. The full
  retail build (GOG, not in this repo) may carry real text — checking it
  would settle both items. (Note: `docs/mechanics/README.md` speaks of "the
  36 blueprints"; the catalogue carries 38 tokens — exactly the two
  placeholder items, and the price-pair table spans 36 types. Whether the
  full game ships 36 or 38 is part of the same question.)
- Attaching the type ids (pair table) and record numbers (per-item table)
  to the 38 catalogue items: needs a runtime trace with the brochure/Ship
  Yards open, or a code-level pass on the runtime-built pointer tables
  (deferred runtime item).
- The five 0-price types (10, 11, 13, 24, 30) and the absent type 2.
- The brochure's full section list (only "Mining" and "DefenSe" attested).
- Whether the 10 "blueprint ships" (Lazzaro Research … SkyMech, TXT
  120153–120280) are brochure items, ship classes, or variants — see
  `vehicles.md`.

## References

- `build/reports/strings/_TEXT__AMERICAN.TXT.strings.md` — the text resource;
  the token offsets quoted above are byte offsets into `_TEXT/AMERICAN.TXT`.
- `docs/mechanics/weapon-and-turret-numbers.md` — the Ship Yards item price
  catalog (the always-available weapon/module family) and the blueprint
  price-pair table discovery.
- `docs/mechanics/gog-build-data.md` — the GOG flat's stat-table region
  (0x8F000..0x9C000), the per-item records and the runtime verification.
- `build/dumps/ram_1ce2a000.bin` — the GOG Ship-Yards-screen memdump: the
  loaded TXT string pool (base 0x6C7AB8) and the 512-byte-slot Ship Yards
  help-string table (0x2903AA) used to resolve the per-item text-offset
  column.
- `docs/mechanics/vehicles.md` — the craft roster, construction, hardpoints,
  and the other "blueprint" sense (ship design blueprints).
- `docs/mechanics/README.md` — the mechanics index (this document fills the
  "blueprints / technology" line).
