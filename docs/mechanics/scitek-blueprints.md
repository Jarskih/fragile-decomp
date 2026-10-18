# Sci-Tek blueprints: the catalogue and what each item does

Status: confirmed — the catalogue contents, categories and per-item effects
from the game's own text resource; the ordering/delivery flow from the same;
the per-item prices are now fully mapped (rewritten 2026-10-18: the earlier
price-table section had the pair order swapped and mis-identified two of the
three tables; see "The price table").
Source: game text resource (`_TEXT/AMERICAN.TXT`, the same resource the game
displays) + the GOG build's static Sci-Tek grid table + the item-id anchors
read from the code (`stat-tables-design-sheet.md` section 5 holds the full
36-row table). Address convention: GOG flat = DS displacement + 0x86004.

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
  delivery delay is not located (Corrected 2026-10-18: the old "days columns"
  belong to the craft and agent tables, not to blueprints).
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
   blueprints have arrived:" (24195/24219). The delivery
   delay and the scheduling code are not yet located.
5. A hostile agent can steal a blueprint (40100/40124); the blueprint theft
   message names the colony and the lost blueprint.

## The price table (GOG build; rewritten 2026-10-18)

Corrected 2026-10-18: the previous version of this section (a "price pair"
table at 0xB72E4 read as `{price, type}`, a "10 x 20 B Ship Yards record" table
and a "12-record stat table") was wrong in three ways: the pair order was
swapped, 36 items are priced in the GOG build (there is no "ISO-only" subset;
the ISO build was not re-read), and the other two tables are not blueprint
data -- the 10-record decode is the start of the 41-record Ship Yards craft
table at flat 0x90B60 (`vehicles.md`, `stat-tables-design-sheet.md` 2.1), and
the 12-record table at 0x8F984 is the agent-mission fee list
(`stat-tables-design-sheet.md` 6.1; `economy-and-personnel.md`).

The real Sci-Tek table is the brochure grid at **flat 0xB7270**: 8-byte
records `{Sci-Tek id u32, price u32}` in display order (9 slots per section,
six sections; id -1 = empty slot). The Sci-Tek id is the alphabetical
catalogue index: **id = text index - 1530**, ids 0..35 (Mk2 Mine = 0 ...
Command Cruiser = 35). Anchors read from the code: Building Armour = 6,
Construction Droids = 7, Hi-Energy Power Stores = 11, Power Amplifier = 20 (the
byte offsets into the per-race blueprint-owned flag array, 38 bytes per race).
Scrambler (36) and Double Speed Engines (37) have no grid slot and no price.
The per-item prices (e.g. Mk2 Mine 75,000, Anti-Missile Pod 250,000, Mega
Missile 500,000, Shield x40 15,000, Shield x50 60,000 -- the last agrees with
the text) are tabulated in `stat-tables-design-sheet.md` section 5 together
with each item's grid section; they are not repeated here. The delivery delay
column of the old tables does not exist in this table: where the blueprint
delivery delay lives is not located (**?**).

- None of the catalogue text (names, descriptions) is stored in the EXE —
  it all lives in `_TEXT/AMERICAN.TXT` and is loaded at runtime (the same
  arrangement as the rest of the game's UI text). The loaded copy is a
  rebuilt string pool (base 0x6C7AB8 in the GOG memdump, file-ordered apart
  from single-byte drift); the Ship Yards help strings live in a separate
  512-byte-slot table (0x2903AA in the same dump).

## Open questions

- The effects of **Scrambler** and **Double Speed Engines**: both description
  slots are placeholders in the reference ISO's text resource. The full
  retail build may carry real text. (The brochure grid has 36 priced items
  -- the 36 blueprints of `README.md` -- and the catalogue carries 38 tokens;
  the two extras are exactly these placeholder items, which have no grid slot
  and no price in the GOG build, so they are leftovers.)
- The brochure's full section list (only "Mining" and "DefenSe" attested).
- Whether the 10 "blueprint ships" (Lazzaro Research … SkyMech, TXT
  120153–120280) are brochure items, ship classes, or variants — see
  `vehicles.md`.

## References

- `build/reports/strings/_TEXT__AMERICAN.TXT.strings.md` — the text resource;
  the token offsets quoted above are byte offsets into `_TEXT/AMERICAN.TXT`.
- `docs/mechanics/stat-tables-design-sheet.md` section 5 — the full Sci-Tek
  id / item / price / section table (flat 0xB7270).
- `docs/mechanics/weapon-and-turret-numbers.md` — the Ship Yards item price
  catalog (the always-available weapon/module family).
- `docs/dataformats/gog-build-data.md` — the GOG flat's stat-table region.
- `docs/mechanics/vehicles.md` — the craft roster, construction, hardpoints,
  and the other "blueprint" sense (ship design blueprints).
- `docs/mechanics/README.md` — the mechanics index (this document fills the
  "blueprints / technology" line).
