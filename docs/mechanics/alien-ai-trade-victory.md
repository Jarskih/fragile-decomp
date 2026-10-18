# Alien AI, diplomacy numbers, win/lose rules, game settings, trade and APVs

Status: probing. The settings, campaign, win/lose, time-cadence,
hostility-matrix, trade-market and APV sections are read from the GOG build's
code and static data and cross-checked against each other (confirmed unless a
line is tagged otherwise). The alien fleet launch / attack-volley decisions are
only partly decoded (section 6.4 and 11), and the Trade menu's availability
rules and the black-market legality consequences are incomplete (8.8). Every
claim carries an evidence tag (legend below).
Source: `build/flat/gog_disasm.txt` and `build/named/FRAGILE.EXE.gog.flat/
decompiled.c` (GOG build, addresses below are GOG flat addresses),
`build/flat/FRAGILE.EXE.gog.flat` static data (table values), the English game
text (`ENGLISH.TXT`, indices = our text catalogue), the retail manual (read
visually), `docs/mechanics/life-support.md` and `economy-and-personnel.md`
(time base, calendar, income, agents; they were written in parallel and agree
with this note).

Companion notes: `diplomacy.md` (written against the reference build; its
machinery is the same as here but several interpretations are overturned in
section 10), `main-loop.md`, `weapons.md`, `turrets-and-defence.md`,
`asteroid-spawning.md`.

## 0. Conventions

Evidence tags:

| tag | meaning |
|-----|---------|
| **C** | read from GOG code or static data and the interpretation is firmly supported |
| **C~** | code/data read exactly, but the *meaning* (name of the quantity) is inferred |
| **T** | game text (`ENGLISH.TXT`) only |
| **M** | manual only |
| **?** | unknown / not found |

Address conventions:

- **Code/flat addresses** (`0x15804`) are image-relative GOG flat addresses.
- **Data displacements** (`D 0x9e60`) are the operands the code uses for the
  data object; static initial values are at **flat = D + 0x86004**. This base
  is the one documented in `building-stat-table.md` ("Addressing (resolved)");
  it was re-verified here with the ore table (D 0x9cde -> flat 0x8fce2) and the
  arena table. Displacements beyond about D 0xbbfc are BSS (zero in the file,
  filled at run time) and cannot be read statically.
- A **day** is one calendar step (`life-support.md`: 4 x `[0xbd00]` outer-loop
  passes, 32 passes at the default). The variable named `g_tick_counter`
  (0xc6bc) counts *days*, so every "tick" threshold in the AI code below is a
  threshold in days. "Per day" in this note means "once per state cycle", i.e.
  once per calendar step.
- Race ids: 0 = unowned, 1..8 = player slots (human or network players; all
  human slots are treated as "Terran"), 9..14 = the six alien cultures.

### The six alien cultures (race ids) **C~/T**

The order of the AMERICAN text blocks for the six cultures (Representatives
2241-2246, names 2461-2466, "Asteroid" 2476-2481, "Fleet" 2491-2496) is
Rigellian, Braccatia, Mikotaj, Artemia, Mauna, Achaean. The code agrees with
this order in two independent places: race 13 is never chosen as a pact/treaty
partner or target (`0x6e05`, `0x6f07`, `0x6560` compare with 0xd; the manual
says the Mauna have no ambassador), and the per-culture campaign masks match
the campaign descriptions (section 3.4).

| id | culture | notes |
|----|---------|-------|
| 9 | Rigellian | peaceful baseline (Arms Unit text: "not a particularly aggressive species" **T**) |
| 10 | Braccatia | honour culture **T** |
| 11 | Mikotaj | |
| 12 | Artemia | |
| 13 | Mauna | never a diplomatic partner/target; highest starting hostility toward everyone |
| 14 | Achaean | never initiates pacts/treaties (period 999, section 6.5) |

## 1. Time and cadence table

Time base, calendar and speed are in `life-support.md` (default 32 passes per
day; start date 26 May 2496; day length = 4 x `D`, `D = 8 + 8*speed` when
`[0x1660f]` is set, `8 + 4*speed` otherwise; speed index 0..2 cycled mod 3 by
the options screen). The additions here are the cadences of the alien/relations
code, all in days:

| period | process | where |
|--------|---------|-------|
| every pass of the quarter driver, 4 per day | `ai_economy_tick` (player-side supervisor auto-management, **not** the aliens) | 0x4d655, 0x98b4 |
| 1 | `relations_matrix_tick` (hostility drift, treaty clocks) | main state 8, 0x55b4 |
| 1 | per alien race, per asteroid it owns: build/economy/fleet timers | `race_objects_tick` 0x15ce4, main states 9..14 (state = race id) |
| 1 | alien asteroid wealth counter `+0x1d8` decays 1 toward 0 | `race_master_tick` 0x15f64 (state 0xf) |
| 1 | slot timers of the six aliens (expansion, pact/treaty offer timers, raids) | 0x15f64 |
| 2 | defensive-response scan `race_attack_tick` | 0x17f34 (needs `[0x7e85c]`) |
| 8 | `ship_acquire_target` (alien learns the bearing of a player's scout) | 0x15b24 |
| 32 | `race_target_assign` (which asteroid builds the Transporter) | 0x156e4 |
| 32 (per race) | `race_raid_tick` | 0x15804 |
| 205/200/210/185/190/195 (+-10%) | alien expansion attempt, races 9..14 | 0x15204 |
| 300/400/500 (+0..30%) | alien Non-Aggression-Pact proposal, by atmosphere | 0x7444 |
| 600/400/200 (+0..30%) | alien Joint-Combat-Treaty proposal, by atmosphere | 0x74a4 |
| 150 | alien "slot event" (agent mission) per race with an agent | 0xed84 |
| 100..149 | agent spawn per race (all races 1..14) | 0xca04, timer 0xcb5f |
| 30 | monthly market update: all trade prices, stock refresh, Federation ore prices (section 8) | `0x47574` via the month call at 0x4e3fc |
| 150..239 / 150..199 | a Trade Merchant / a Trader is offered to each player race (section 8.2) | `event_scheduler` 0xf404, timers 0xcb61 / 0xcb60 |
| 4096 | each alien race's rally/home point is re-rolled inside the middle half of the arena (x in W/4 .. 3W/4, y in H/4 .. 3H/4) and bit 0x10 of its record is set **C~** | `race_master_tick` (flag 2), 0x14fe4 |

First-event times: raid tick on day 32; first expansion attempt on day
P(race) = 185..210 (no jitter on the first one); first pact proposal on day
300..650 depending on atmosphere (section 6.5).

## 2. Evidence for the subsystem enables **C**

`main` state dispatch (see `main-loop.md`) is confirmed. Corrections that
matter here:

- **State 0xf is not the end game.** It runs `race_master_tick` (0x15f64), the
  daily alien master tick. **States 9..14** call `race_objects_tick(state)`
  (0x15ce4): the per-asteroid tick of alien race `state`, one race per state,
  once per day. `colony_rating_update` and the tail work run on every tick as
  before.
- The four enables `[0xc6c4] [0xc6c8] [0xc6cc] [0xc6d0]` armed "at tick > 700"
  are **not alien-AI switches**. They gate the Colony Supervisor pool
  (0x8544), the Agent pool (0xcbd4) and the two halves of the **trade
  delegate scheduler** (0xf404, section 8.2: Traders `0xc6cc`, Trade Merchants
  `0xc6d0`). They are armed by the *player's own* claims: four byte
  counters per player race (`0xcb64..0xcb67`) are set at new-game time to
  `rng(3)+2`, `rng(2)+3`, `rng(2)+2`, `rng(2)+3` (2-4, 3-4, 2-3, 3-4) by
  0x7544 / 0xbc2e / 0xf084, decremented once per **successful claim by a human
  race** in `asteroid_claim_new` (0x23183..0x23209; whether the home colony
  goes through the same function is not established **?**), and the matching
  enable turns on when its counter hits 0 (supervisors `0xcb64`: 2-4 claims,
  agents `0xcb65`: 3-4, Traders `0xcb66`: 2-3, Merchants `0xcb67`: 3-4). At new
  game each enable starts at the configuration byte `[0x16600]`..`[0x16602]`
  (all 0 in the default configuration and forced to 0 in campaigns), or 1 when
  `[0x16618] != 0`. A backstop sets all four when the 200-day sweep finds the
  day count above 700 (first possible at day 800). **C**
- **The alien AI has no such delay.** Its timers start at day 0 (section 1).
- AI feature switches: `ai_features_setup` (0x14604, called from the scenario
  setup 0x22364) fills the per-feature flags `0x7e820..0x7e860` once. In the
  normal game (`[0x16618] == 0` and `[0x1660d] != 0`, the default; `[0x1660d]`
  is set to 1 by the new-game routine at 0x22340) **everything is on**. Two
  reduced sets exist:
  - `[0x1660d] == 0`: **off** are ore selling (`0x7e854`), colony capacity
    refresh (`0x7e840`), the defensive-response scan (`0x7e85c`), ship
    acquisition (`0x7e84c`), ship steering (`0x7e838`), the raid timers
    (`0x7e824`), the agent-mission tick (`0x7e828`), the fleet AI (`0x7e850`),
    the loiter-sector scan (`0x7e860`) and the target-marking step (`0x7e820`);
    **on** stay the expansion and pact/treaty timers, the periodic gate, the
    structure spawn/production/build ticks.
  - `[0x16618] != 0` (the "mode flag", which also halves the Federal
    Transporter cycle and disables the trade scheduler and the agent spawn): **off** are the expansion timers (`0x7e830`), the pact/treaty offer
    timers (`0x7e82c`), the defensive-response scan, the agent-mission tick and
    the pending-build tick; the rest stays on.
  What sets `[0x16618]` (multiplayer? tutorial?) is not known **?**.

## 3. Game settings -> numbers

### 3.1 The setting variables **C**

| byte | meaning | values |
|------|---------|--------|
| `[0x16610]` | **arena size** index | 0 Small, 1 Medium, 2 Large |
| `[0x16611]` | **asteroid density** index | 0 Low, 1 Standard, 2 High |
| `[0x16612]` | **atmosphere** index (the map calls it `g_race_cur_idx`) | 0 Peaceful, 1 Neutral, 2 Aggressive |
| `[0x1660e]` | game speed index | 0, 1, 2 (index 0 = Fast, ? text order only) |
| `[0x1660f]` | second option row of the options screen (Time On/Off in menus, ?) | 0/1 |
| `[0x16614]` | culture mask, bit n = race n present | bits 9..14 = aliens |

The defaults written by the new-game path (0x22780..0x2278c) are arena 0,
density 1, atmosphere 1 (Small / Standard / Neutral), speed 0; the retail
`CONFIG.INI` keys `ArenaSize`, `AsteroidDensity`, `ArenaAtmosphere`, `Aliens`,
`TimeRate`, `TimeOffInMenus` are the saved copies. `Aliens=0x0` (no alien
culture) is the "practice game" of the manual. **C/M**

Index meanings were fixed three ways: text order (Small/Medium/Large,
Low/Standard/High, Peaceful/Neutral/Aggressive), monotone numeric effects below,
and the campaign table (section 3.4) whose rows match the campaign blurbs.

### 3.2 Arena size and density **C**

Static data:

| item | D | values |
|------|---|--------|
| arena grid (cells, 1 cell = 32 units), index 0/1/2 | 0x1663c | 24x15, 29x18, 32x20 (768x480, 928x576, 1024x640 units) |
| asteroid ceiling (auto-spawn gate), row = `[0x16611] + 3*[0x16610]` | 0x9cb0 | small: **30 / 45 / 60**; medium: **40 / 60 / 80**; large: **50 / 75 / 100** (low / standard / high) |

The gate is checked every 8 days in state 8: `if ceiling > asteroid_count then
create+place another asteroid` (`main-loop.md`, `asteroid-spawning.md`). The
100-node pool is the hard cap, so Large/High is limited by the pool at 100.
The table values are now readable (they were "code-like bytes" before; the
empirical save counts 30/45/60 for small and 61 medium/medium agree). Other
sizes do not scale with the arena: the alien reach used by the target tracker
is a fixed 192 units (D 0x9db8), i.e. a quarter of the Small arena's width and
3/16 of the Large one.

### 3.3 Atmosphere: every effect found **C**

`[0x16612]` is read at only these places (all in the GOG code):

| effect | table | Peaceful / Neutral / Aggressive |
|--------|-------|---------------------------------|
| daily stipend credited to **every active player race's Money** (`race_income_tick`, state 2) | D 0x93b0 (words) | **100 / 250 / 400 Cr per day** |
| starting hostility shift of every alien (percentage points, section 6.2) | D 0x9504 and D 0x9531 | **-40 / 0 / +40** |
| rate multiplier applied to the per-shot hostility gain (percent) | D 0x94d4 | **-50 / 0 / +50 %** |
| rate multiplier applied to the hostility decay (percent) | D 0x94d7 | **-50 / 0 / +50 %** |
| alien NAP-proposal period (days, + rng up to 30 %) | D 0x95cc | 300 / 400 / 500 (races 9-13); race 14: 999 |
| alien Joint-Combat-Treaty proposal period (days, + rng up to 30 %) | D 0x9614 | 600 / 400 / 200 (races 9-13); race 14: 999 |
| alien expansion **lead** `adj[race][atm]` (colonies above the largest human colony count that an alien tries to reach) | D 0x9f36 | Rigellian 0/1/2; Braccatia 1/2/2; Mikotaj 1/2/2; Artemia 1/2/3; Mauna 1/2/3; Achaean 0/1/2 |

Nothing else reads the byte (0x14ff6 only checks `atmosphere <= 2`, which is
always true). In particular the atmosphere does **not** change
the starting Money (1,000,000 Cr in all three cases: D 0x16880, three dwords
of 0xf4240; the flag `[0x165fd]` instead gives **all five budget buckets**
1,000,000 Cr each),
the asteroid count, the day length, damage, or ore values.

The **stipend** is new information: the "fixed income table {100,250,400}" of
`economy-and-personnel.md` is indexed by the atmosphere (Neutral default =
250 Cr/day per player race, on top of 1 Cr per employee per day).

### 3.4 Campaign table **C**

`0xf7c4` (called from the scenario setup when a campaign number is chosen)
copies one 6-byte row of D 0x9c54 (index = campaign number 1..11, row 0 unused)
into the settings: byte 0 = arena, byte 1 = density, byte 2 = atmosphere,
word at +4 = culture mask (bits 9..14 replace the old alien bits). The rows:

| # | campaign (game text **T**) | arena | density | atmosphere | alien cultures (mask) |
|---|---------------------------|-------|---------|------------|------------------------|
| 1 | Beginner's Luck | Small | Standard | Peaceful | Rigellian (0x0200) |
| 2 | Encounters | Small | Standard | Peaceful | Braccatia, Mikotaj (0x0c00) |
| 3 | Getting Serious | Medium | Standard | Neutral | Rigellian, Mauna (0x2200) |
| 4 | Three's a Crowd | Medium | Standard | Neutral | Braccatia, Artemia, Achaean (0x5400) |
| 5 | Raising The Stakes | Large | High | Neutral | Rigellian, Braccatia, Artemia, Mauna (0x3600) |
| 6 | The Void | Large | High | Neutral | Rigellian, Braccatia, Mikotaj, Artemia, Achaean (0x5e00) |
| 7 | Crowded House | Large | High | Neutral | all six (0x7e00) |
| 8 | Knowledge is Power | Large | Standard | Aggressive | all six |
| 9 | Full On | Large | Low | Aggressive | all six |
| 10 | Getting Tight | Medium | Standard | Aggressive | all six |
| 11 | The Ultimate | Small | High | Aggressive | all six |

Notes: the campaign blurbs say "richly packed limited arena" for #1 (Small,
Standard here), "few asteroids" for #9 (Low) and "small arena" for #11 (Small);
all fit. In a campaign the per-feature flags `0x165fa..0x16607` are reset to
fixed defaults (0x225b4..0x226eb) and `[0x1660e]=0`, `[0x1660f]=1`
(`0x22800..0x22829`): campaigns always run at index-0 speed.

The campaign numbers are the *only* place where size, density, atmosphere and
the alien set are coupled; a custom game chooses them independently
(maximum-difficulty recipe of the manual: Large, High, Aggressive, all six
cultures **M**).

## 4. Win and lose conditions

### 4.1 What the code can end the game with **C**

`g_victory_state` (0x16864) is written at four places only (every store was
enumerated in the disassembly):

| value | set by | meaning |
|-------|--------|---------|
| 1 | options screen quit (0x2859d) | player quit |
| **2** | `race_elimination_check` 0x10058 | **the player race's colony counter reached 0: the player lost** ("Your colony has been destroyed..." **T**) |
| **3** | `race_elimination_check` 0x100d1 | **exactly one race is still active while more than one was configured: victory** (the "all aliens destroyed" victory text **T**) |
| 5 | save-file validation failure (0x279b0) | bad saved game |

`race_elimination_check` (0x10004) runs every day in state 7 and only when
`[0x1660a]` (game-active/replay flag) and `[0x7f11c]` (the map's
`g_race_elimination_flag`, a debug switch cleared by the new-game routine at
0x22346; when set it also makes the alien expansion step ignore the colony-count
comparison, section 5.1) are clear. It loops over races 1..14: a race whose active bit (`0xcb5d`
bit 0) is set and whose colony counter (`0xcb5c`, number of asteroids it owns)
is 0 is eliminated by `race_asteroid_respawn` (0xff34: purge all its units,
fleets, orders and listed objects, clear the active bit, and for non-player
races post the "withdrawn from the sector" message and bump
`g_race_asteroid_respawn_count`). If the eliminated race is the player, state 2
is set. After the loop the active bits of races 1..14 are counted; if exactly
one remains **and `g_race_active_count` (the number of cultures configured at
start, 0x1529c) is greater than 1**, state 3 is set. Consequences:

- **Victory = every other configured race, aliens and other player slots, has
  lost all its asteroids.** Colonies need not be destroyed by the player: an
  alien that loses its last asteroid to anything (collision, an ally, a
  pandemic) counts.
- With no alien culture configured the count is 1, so victory can never fire:
  the **practice game** has no end except defeat or quitting. **C/M**
- The player's defeat is **only** "all asteroids gone". A colony that dies out
  (population 0) is destroyed in state 7 (message "Asteroid %s Colony Death"
  **T**) and counts the same way.
- **There is no time limit in the GOG build.** State 4 ("you have run out of
  time", text 2791/2792, selected in `0x280f4` from `0x39d88`) is never stored
  to `g_victory_state` anywhere in the executable; the text and the end-screen
  branch are leftovers. The campaign summaries and the manual do not mention a
  limit either (the manual states no win/lose rule at all). **C (absence)**

### 4.2 End screens **C**

After the main loop, `0x27ad5..0x27bad` picks one of four `.GDV` videos by
state:

| state | condition | video |
|-------|-----------|-------|
| 2 (lost) | day count < 730 | `_INTRO\OUT2.GDV` |
| 2 (lost) | day count >= 730 | `_INTRO\OUT4.GDV` |
| 3 (won) | `rng(2)` | `OUT1.GDV` or `OUT3.GDV` |
| 1 (quit) | wall-clock > 500 s | same random win pair; otherwise `OUT4` if day > 730, else none |

States 4/5 would instead show text screens via `0x280f4` (state 4 never occurs).
A statistics screen follows ("TetraCorp Rating", end-of-game stats **T/M**).
The meaning of the "TetraCorp rating" is not in this note **?**.

## 5. Alien colonies: what the aliens do every day

All of this is the per-asteroid tick `race_objects_tick` (0x15ce4) that runs
once per day for each alien race over every asteroid it owns that is ready
(`+0x11e == 0`) and active (`+0x139 & 0x10`), plus the race-wide tick
`race_master_tick` (0x15f64). The alien economy is simulated with per-asteroid
countdown bytes; each fires its action and reloads from a per-race table.

Colony class `c` in {0,1,2,3} (`+0x19e`), set by `colony_rating_update`
(0x6d4). `rating = 100 * (sum over the ten ore slots of reserve * weight +
production points `+0x1a0`) / base`, weights 1,2,3,4,5,7,10,20,70,100 (D 0x9cf8,
the "tag" column of the ore table, Selenium .. Nexos) and `base` = the sum of the
ore table's upper bounds times the weights (12,742). Three thresholds are
derived at game start by `0x16454` from 1000 random asteroid ore draws made
with the ore table (rich-roll chance `p`, bounds `lo..hi`; Monte-Carlo
re-run here: the 90th, 80th and 20th percentile of the rating, about **56, 51
and 31**, varying by a point or two per game): `T_a` (P90), `T_b` (P80),
`T_c` (P20). The class is:

| rating | wealth `+0x1d8 > 0` | `= 0` | `< 0` |
|--------|---------------------|-------|-------|
| `>= T_a` | 0 | 0 | 1 |
| `T_b .. T_a` | 0 | 1 | 2 |
| `T_c .. T_b` | 1 | 2 | 3 |
| `<= T_c` | 2 | 3 | 3 |

The alien wealth counter `+0x1d8` (positive after receiving money, negative
after paying fines; decays 1 per day toward 0) therefore shifts the class one
step in its favour or against it. Class 0 is the richest/largest colony.

The reload values are exact (**C**); the action descriptions are inferred
from the routines called (**C~**).

| timer (`+off`) | action | reload (days) |
|----------------|--------|---------------|
| `+0x1a4` (word) | `asteroid_spawn_object_tick` 0x18e14: count the structures on the asteroid; if `count <= cap[c]` and `+0xaa == 0` the next try is in `rng(2)+1` days, otherwise in `T_spawn[c]`; then place one building of a random available type | cap (D 0x9e60): **15 / 10 / 6 / 4** structures for class 0..3 (same for all six races); `T_spawn` (D 0x9e78): **8 / 15 / 20 / 20** days |
| `+0x1b0` | `planet_ore_production_tick` 0x199c4: produce one unit of the colony's chosen item if the stock is below the per-type limit and the production points (`+0x1a0`) pay for it | `T_prod[race][c]` (D 0x9e90): Rigellian 14/19/24/29, Braccatia 9/14/19/24, Mikotaj 10/15/20/25, Artemia 8/13/18/23, Mauna 6/11/16/21, Achaean 12/17/22/27 |
| `+0x1af` | `planet_pending_build_tick` 0x19604 + `structure_construction_tick` 0x19764: spawn the queued/requested building if the production points cover its cost (cost table at D 0x967c, 28-byte records) | `T_build[race][c]` (D 0x9ea8): Rig 52/62/72/92, Bra 32/42/52/72, Mik 40/50/60/80, Art 25/35/45/65, Mau 36/46/56/76, Ach 48/58/68/88 |
| `+0x1b5` | `planet_ore_sell_tick` 0x1a014: sell/haul ore to the nearest buyer; the next timer = `max(10, 100 - 100*(sum of ore stock)/30)` % of `K[race]` | `K` (D 0x9ee1+race): Rig 64, Bra 52, Mik 72, Art 56, Mau 44, Ach 76 |
| `+0x1b2` | `ship_density_scan` 0x153a4: pick the least crowded of 8 sectors around a building of class 2 in the type table (? which building) and move ships to loiter there; uses the bearing byte `+0x1b7` (section 6.4) | **50** for all six (D 0x9ede) |
| `+0x1b3` | `asteroid_ships_spawn` 0x15664: for each of N packages mark the most hostile known asteroid in range (`obj_find_best_relation` 0x13234) by setting this race's bit in its `+0x98` word (the same word the agent code reads as "cover"; likely spy-satellite coverage **C~**) | Rig 140, Bra 150, Mik 135, Art 145, Mau 165, Ach 160 (D 0x9ef0) |
| `+0x1b4` | `colony_capacity_refresh` 0x17b74 (population/capacity bookkeeping) | race table D 0x9edb: 210 / 190 / 200 / 170 / 150 / 230 |
| `race_fleet_ai_tick` 0x14874, whenever `+0x19f` bit 1 is set | send units/fleets to targets, see 6.4 | event driven |

The initial values of these timers are the table entries for the colony's class
at the moment it is claimed (`asteroid_claim_new`, 0x22f14/0x22dc2); the
colony starts with `+0xc2 = 50`.

Cost of a structure for an alien is the same cost table as for the player
(`building-stat-table.md`); aliens pay from the production-point counter
`+0x1a0` instead of Money, so their pace is set by the ore-sale timer above
and the stock-to-points conversion.

### 5.1 Expansion: how an alien claims new asteroids **C**

`slot_timer_reset` (0x15204) fires when a race's expansion timer (`0xcb56`,
first value `P` = 205/200/210/185/190/195 for races 9..14, D 0x9ec0) expires
(checked each day in `race_master_tick`). It re-arms the timer with
`P - P/10 + rng(P/5)` (0.9..1.1 P) and then:

1. does nothing unless the race owns at least one Transporter (`0xc300[race]`
   is the per-race count of ships of kind 5; it is incremented when a
   Transporter is built and decremented when it dies);
2. computes `M` = the largest colony count (`0xcb5c`) among the **player
   slots 1..8** (the loop at 0x15283..0x1529e runs over races 1..8 only; alien
   colonies are not counted);
3. if its own colony count is **>= M + adj[race][atmosphere]** (section 3.3),
   stops;
4. otherwise scans its asteroids for a Transporter whose range reaches an
   eligible free asteroid (`0x13174`: known to the race, unowned, not
   terrain-busy) and orders it to found a colony there (task 5).

So the aliens **rubber-band to the biggest human**: each alien tries to own
`M + adj` colonies, one new claim per attempt (185..230-day cadence), as long as
it has a Transporter and a free asteroid within range. With `M = 1` at the start
the target is `1 + adj`: Peaceful 1-2, Neutral 2-3, Aggressive 3-4 colonies
depending on the culture; a Rigellian or Achaean at Peaceful (`adj = 0`) only
expands when a human has more colonies than it. The debug flag `[0x7f11c]`, if
set, skips the comparison. This replaces the assumption in
`asteroid-spawning.md` / `main-loop.md` that alien growth is limited by a
generic day threshold. If the race has no Transporter,
`race_target_assign` (0x156e4, every 32 days) tags up to two of its
asteroids with the race's Transporter type (`g_race_target_table`, D 0xafcf:
types 13, 17, 23, 29, 35, 39 for races 9..14) so that its build queue makes
one. `race_raid_tick` (below) also sends an existing Transporter to an
unowned known asteroid when the race owns fewer than 4 colonies, when no
neighbour asteroid exists, or when the asteroid's rating is at least `T_c` (about the
20th percentile, so roughly four asteroids in five qualify).

## 6. Hostility, pacts, treaties and incidents

### 6.1 The matrix is a **hostility** matrix **C**

Per race row (stride 0x208, 15 rows) the code keeps these arrays, all indexed
by the column race 0..14 (the "known" and "declared" word bitsets too):

| array (base at row 0) | type | role | meaning |
|-----------------------|------|------|---------|
| `B`  0xc98c | s16 | baseline hostility of row toward column | the floor that `O` decays toward; also the stored long-term disposition |
| `O`  0xc9aa | s16 | current hostility of row toward column | -1.0 = 0x8000 ... +1.0 = 0x7fff |
| `X`  0xc9c8 | u16 | incidents today (shots/collision weight), column = target | drained once a day |
| `C`  0xc9e6 | u8 | per-incident gain of `O` (raw units per weighted incident) | |
| `D`  0xc9f5 | u8 | decay of `O` per day when quiet (raw units) | |
| `A`  0xca7c | s32 | grace days: sum of incidents, counted down by 1 per quiet day | |
| `T`  0xca40 | s32 | days since the last incident | |
| 0xcab8 | s32 | lifetime incident total | |

(The earlier names `g_relations_opinion_table` etc. suggest the opposite sign;
section 6.6 gives the evidence for the hostility reading.)

Daily update (`relations_matrix_tick`, state 8, 0x55b4), per ordered pair
(row `r`, column `c`):

```
if X[r][c] != 0:                     # an incident today (a "push")
    active[r] |= bit c               # r now "knows" c  (0xcb54)
    A[r][c]  += X[r][c]
    O[r][c]   = min(0x7fff, O[r][c] + C[r][c] * X[r][c])
    T[r][c]   = 0
else:
    if A[r][c] == 0:   O[r][c] = max(B[r][c], O[r][c] - D[r][c])
    else:              A[r][c] -= 1
    T[r][c] += 1
afterwards: total[r][c] += X[r][c]; X[r][c] = 0
```

`X[shooter][target]` receives the **weighted shot count**: a weapon class table
at D 0xb9e8 (shorts) indexed by the weapon's category byte `0xb3be + 16*type`
(missile table `stat-tables-design-sheet.md` section 4) gives the weight per
shot (values 1, 3, 5, 7, 25, 20, 100, 100, 0, 255, 50, ... for classes 0..10,
the same figures as the "B" column of that table), and asteroid collisions add
`[0xb9fa]` to both directions (0x1118e..0x111c0). The row of a player slot
(1..8) is never read by AI logic for anything but "is this target hostile to
me"; it stays zero, so a human is always an eligible target (6.4).

Conversion of the percent tables into raw values (section 6.2):
`O = scale_opinion(x) = clamp(x + shift[atm], -100, 100) * 32767 / 100`;
`C = clamp(c + c*att[atm]/100, 0, 100) * 182 / 100`;
`D = clamp(d + d*att2[atm]/100, 0, 100) * 45 / 100`. At Neutral a shot at the
player therefore moves the shooting alien's `O` by `C` raw units (0.2 %..0.5 %
of the full range) and `O` falls back toward `B` by only `D` = 4..36 units per
day (0.01..0.11 %) once the grace days `A` have run out. **A is a long
memory:** every incident adds its weight to `A`, so an alien that has fired
1000 weighted shots keeps its raised hostility for at least 1000 further quiet
days.

### 6.2 Starting values **C**

`0x3fa4` zeroes the whole block (0x1e78 bytes from 0xc98c) and `0x4144`
(called once from the scenario setup, skipped if `[0x165fe] != 0`) fills, for
each alien row r in 9..14: against every
player column (1..8) `O = scale(A0[r])`, `B = scale(B0[r])`, `C = ..(C0[r])`,
`D = ..(D0[r])`; against each alien column the same from the pair tables;
the diagonal is zero. Percent inputs (before the atmosphere shifts of
section 3.3):

Alien -> every player column:

| race | culture | A0 (start `O`) | B0 (baseline `B`) | C0 | D0 |
|------|---------|----------------|-------------------|----|----|
| 9 | Rigellian | 0 | -20 | 40 | 70 |
| 10 | Braccatia | 20 | -20 | 60 | 60 |
| 11 | Mikotaj | 40 | -15 | 60 | 60 |
| 12 | Artemia | 40 | -20 | 50 | 40 |
| 13 | Mauna | 90 | **+40** | 90 | 10 |
| 14 | Achaean | 0 | -30 | 30 | 80 |

(Tables at D 0x94da.. / 0x9507.. / 0x9534.. / 0x955e..; units: percent of full
range.) At Neutral the raw per-shot gain `C` is 72, 109, 109, 91, 163, 54 and
the raw daily decay `D` is 31, 27, 27, 18, 4, 36 for races 9..14.

Alien -> alien pairs (row = the hostile party, column = its target; Neutral
inputs):

`A0` (start O):

| | 9 | 10 | 11 | 12 | 13 | 14 |
|---|---|---|---|---|---|---|
| 9 | - | 50 | -60 | 35 | 70 | -40 |
| 10 | 10 | - | 60 | 80 | 70 | 0 |
| 11 | -50 | 70 | - | 80 | 0 | -30 |
| 12 | 0 | 30 | 80 | - | 95 | -50 |
| 13 | 70 | 80 | -10 | 95 | - | 10 |
| 14 | -80 | 30 | -20 | 20 | 90 | - |

`B0` (baseline):

| | 9 | 10 | 11 | 12 | 13 | 14 |
|---|---|---|---|---|---|---|
| 9 | - | -15 | -30 | -15 | -10 | -30 |
| 10 | -30 | - | -20 | 30 | 20 | -30 |
| 11 | -20 | -10 | - | -10 | -20 | -20 |
| 12 | -20 | -5 | -10 | - | 40 | -20 |
| 13 | 10 | 30 | -10 | 50 | - | -10 |
| 14 | -40 | -15 | -40 | -15 | -30 | - |

`C0` (gain) rows 9..14: 9: -,60,20,70,80,20 / 10: 50,-,60,90,90,50 /
11: 30,70,-,80,50,40 / 12: 50,80,70,-,100,40 / 13: 90,90,70,100,-,90 /
14: 20,40,20,40,50,-. `D0` (decay) rows: 9: -,30,90,30,10,80 /
10: 70,-,50,30,40,90 / 11: 80,50,-,40,50,70 / 12: 80,20,50,-,0,80 /
13: 10,5,30,0,-,20 / 14: 90,60,90,60,40,-. Only `O` and `B` are shifted by
the atmosphere table (+-40 points); `C` and `D` by the +-50 % tables.

Resulting starting state toward a human (percent of the full range, after the
atmosphere shift and clamping to +-100; gain and decay in raw units after the
+-50 % rate shift):

| culture | Peaceful O0 / B0 | Neutral O0 / B0 | Aggressive O0 / B0 | gain C per shot (raw) P/N/A | decay D per day (raw) P/N/A |
|---|---|---|---|---|---|
| Rigellian | -40 / -60 | 0 / -20 | 40 / 20 | 36 / 72 / 109 | 15 / 31 / 45 |
| Braccatia | -20 / -60 | 20 / -20 | 60 / 20 | 54 / 109 / 163 | 13 / 27 / 40 |
| Mikotaj | 0 / -55 | 40 / -15 | 80 / 25 | 54 / 109 / 163 | 13 / 27 / 40 |
| Artemia | 0 / -60 | 40 / -20 | 80 / 20 | 45 / 91 / 136 | 9 / 18 / 27 |
| Mauna | 50 / 0 | 90 / 40 | 100 / 80 | 81 / 163 / 182 | 2 / 4 / 6 |
| Achaean | -40 / -70 | 0 / -30 | 40 / 10 | 27 / 54 / 81 | 18 / 36 / 45 |

Because an alien only treats a target as attractive when `avg(O,B)% +
strength advantage` is positive (6.4), the settled (`O = B`) attitudes decide
who threatens a freshly founded human colony: at **Peaceful** only the Mauna
(baseline 0 after the shift) are even neutral and every other culture is
solidly negative; at **Neutral** the Mauna sit at +40 and the rest at -15..-30
(so only a clear strength advantage makes them attack); at **Aggressive**
*every* culture has a positive baseline (+10 Achaean .. +80 Mauna) and is
eligible from day 1. The starting `O` above the baseline (Mikotaj and Artemia at
+40, Mauna at +90 at Neutral) makes those cultures eligible until `O` has
decayed, which takes `(O - B) * 32767 / (100 * D)` quiet days (for example
Mikotaj at Neutral: 55 points at 27 raw/day = about 660 days) because the
grace counter `A` starts at 0.

Reading: Mauna start the most hostile (90 / +40 toward the player); at
Aggressive every alien's baseline is 40 points higher, so even the Rigellians
(-20 -> +20) have positive baseline hostility toward the player, at Peaceful
it is 40 lower (Mauna +40 -> 0). **C for the numbers; C~ for the "hostility"
sign, section 6.6.**

### 6.3 Event effects (all in units of 0x3fff = half the range) **C**

Constants: D 0x9570 + 4*race (step for `B`) and D 0x9588 + 4*race (step for `O`)
hold `0x3fff` for races 9..14.

- Pact completed without violation (`relations_treaty_resolve`, 0x4ed4):
  stored pre-pact values are restored, then both aliens' `O` and `B` toward
  each other are **lowered by 0x3fff (0.5)**, floored at 0x8000.
- Pact ended by a violation (`relations_conflict_resolve`, 0x4d84): values
  restored, the fine is paid violator -> victim, and the **victim's `O` and `B`
  toward the violator are raised by 0x3fff** (cap 0x7fff). Only alien rows are
  edited (the human row stays zero).
- Joint Combat Treaty creation (`combat_event_create`, 0x45c4): for each
  signatory that is an alien, `O` and `B` toward the **target** are forced to
  **+1.0 (0x7fff)**; announcing the treaty publicly also adds `+0x3fff` via
  `relations_opinion_add_guarded` (0x4504) to the signatories' hostility toward
  the target when the target is an alien.
- Non-Aggression Pact creation (`relations_declare_create`, 0x4844): for each
  alien party `O` and `B` toward the partner are forced to **-1.0 (0x8000)**.
- **Gifts** (a trade transfer at unit price 0, section 8.5) lower the
  receiving alien's `O` toward the giver by `value/1000` raw units (floor `B`),
  times 25 / 10 for a culture's own sacred artefact or remedy.
- Paying money to an alien (`race_credit_transfer` 0x4314, also used for fines)
  does not touch the matrix: it adds `amount/15000` to the wealth counter `+0x1d8` of
  every asteroid the alien owns (positive = money received; fines subtract), which decays
  by 1 per day and shifts colony classes (section 5). A 150,000 Cr gift is
  therefore worth +10 for about 10 days. **C**

### 6.4 Who an alien treats as an enemy **C/C~**

- `race_approvals_recalc` (0x5ef4) computes for the acting alien `r`, for every
  other active race `x`: `approval[x] = avg(O[r][x]%, B[r][x]%) + econ_diff%`
  where `O%`/`B%` = `value*100/0x7fff` and `econ_diff% = (S_r - S_x)*100 /
  max(S_r, S_x)` with `S` the **strength score** (below). So approval (despite
  the name) is "how attractive a target x is": high hostility, or a much
  weaker x, makes it positive.
- Strength score `S(race)` (`race_score_calc` 0x5c34, refreshed every day for
  one race in rotation): `600 * (#asteroids ... the value in ECX) + 4 * sum(
  asteroid +0x128 shorts) + 5 * (sum(+0x12a shorts) + units counted
  by race_count_units) + race_strength_total`. Colonies dominate (600 each).
  The exact meaning of the `+0x128/+0x12a` fields and the unit counts is **C~**
  (structure/unit values).
- Distance weighting: `race_approval_adj` (0x60f4) subtracts `(d - 256)/8`
  from the approval when the centroid distance `d > 256` (`race_approval_adj2`
  0x68c4 uses 320 for pact partners). The weight used inside the strength
  share is `100` for `d <= 96`, falling linearly to 0 at `d = 480`
  (`race_weight_pct` 0x5f84).
- Target tracking (`obj_approach_track_update` 0x126f4) for an alien asteroid
  `A`: weights `w[x] = approval[x]` (0 for itself and inactive races); the
  candidates are asteroids known to the race (`+0x96` bit) within **192 units**
  (D 0x9db8) of `A` (excluding `A` and the previous target `+0x1b8`); up to
  **three nearest per owner race** are kept. `combat_weighted_pick` (0x174b4)
  then chooses among races with `w[x] > 0` the tracked asteroid maximising
  `(w[x] + 128*|v|) * 0x10000 / S_unit` where `v` is the candidate's
  per-viewer value (`+0x128`) and the candidate's score (squared distance) must
  not exceed the unit's reach `S_unit`. (`combat_attack_pick` 0x14754 returns
  a nearby own tracked asteroid first if one exists.) The exact formula
  constants are **C~**.
- "Non-hostile" selection: the helpers at 0x12d64/0x12e44 pick the nearest
  known asteroid whose owner has `O[owner][me] <= 0` (not hostile to me); they
  are used to choose where an idle unit goes. A *human* owner always satisfies
  this (row zero). `obj_find_best_relation` (0x13234) is the opposite: it picks
  the asteroid with the **largest positive** `O[me][owner]` that is not a
  declared pact partner (`0xcb4e` bitset).
- **Defensive response** (`race_attack_tick`, 0x17f34, every 2 days): for every
  fleet in flight whose order is 2 or 3 (attack asteroid / intercept) and whose
  target asteroid belongs to an alien `D`, if **`O[D][fleet owner] > 0`** (the
  defender is already hostile to the attacker) then `race_attack_launch`
  (0x17e24) tells the defender to retaliate: it only acts if the fleet is
  within **60 units** (squared 0xe10) of the target, or **120 units** (0x3840)
  when the defender owns a particular building of its race (table D 0xa443,
  ? the sensor/command building), and it then re-tasks a defensive structure
  (state 0x46 = 70) at the attacker. An alien that is *not* hostile to the
  attacker does not launch this response (its turrets still shoot). **C~**
- The dogfight special case: while a human fires at an alien whose `O` toward
  that human exceeds 0x5fff (0.75), each shot has a 1/200 chance to be turned
  into the stronger shot type 0xc (0x1ff1d..0x1ff32). **C~**
- `ship_acquire_target` (0x15b24, every 8 days): for each player scout (kind 2
  craft in state 4) inside the sensor radius (`+0x120`, signed byte) of an alien
  asteroid that does not yet know the scout's home asteroid, the alien stores
  the bearing (byte angle*8/256 -> `+0x1b7`) which `ship_density_scan` later
  uses to choose a loiter sector: aliens start massing toward the side a scout
  came from. **C~**

What I did **not** resolve (section 11): the alien fleet size/composition per
attack (ship loadouts are chosen by `obj_fill_component_slots` 0x19094 from the
tables at D 0x9f78..0x9fc3 with per-race probabilities 60/50/55/40/60/50/50/
40/50/30/60/65; the alien missile "arsenal lists" at flat 0x91488 are present
but their consumer was not traced) and the missile-volley decision (when and
how many missiles an alien fires).

### 6.5 Pacts and treaties: the AI **C**

Constants from the code/data:

| item | value |
|------|-------|
| NAP node | list 0xbd48; fields: A +8, B +9, flags +0xb (bit0 "known", bit1 "declared", 0x80 secret), days left +0x10, fine +0x14, snapshots +0x1c..0x22, A/B violation bytes +0x24/+0x25, grace +0x26 |
| NAP clause (`flags & 3`/UI) | 1 No overt action, 2 No covert action, 4 No overt-or-covert (UI text) **C/T** |
| NAP creation grace | **10 days** (`+0x26 = 10`): violations in the first 10 days do not count |
| NAP violation (`relations_event_append` 0x4b64) | countdown reset to **5 days**; reason bits 1 shots, 2 missiles, 4 spy satellites, 8 agents; the violation message announces termination in 5 days with penalties **T** |
| NAP expiry | clean: restore, both lower hostility by 0.5; violated: fine moves violator -> victim, victim +0.5 hostility |
| JCT node | list 0xbd50; A, B signatories +8/+9, target +0xa, flags +0xb (1/2/4 = Low/Medium/High, 8 = overrun penalties, 0x20/0x40 = A/B budget exhausted, 0x80 secret), days left +0x10, fine +0x14, budgets +0x24/+0x28 |
| JCT combat quotas (D 0x965c) | **Low 400, Medium 1000, High 3000** weighted shots per signatory |
| JCT daily rule (`combat_daily_tick` 0x51c4) | each signatory's budget falls by `X[signatory][target]` that day; when a budget reaches 0 the side is "done"; when both are done the treaty ends clean |
| JCT fine | at expiry, the signatory that fell short owes the other; with the overrun flag the debt grows by `|overshoot| * 30` Cr (`0x1e`), where the overshoot is the *other* side's leftover budget |
| JCT creation | forces `O,B` signatories -> target to +1.0; public announcement adds +0.5 |
| max pact duration offered by the AI | **1800 days**; min 90 |
| offer terms | duration `= clamp(900 - 20*(econ_diff% - attr_diff%), 90, 1800)` days (`colony_pop_target` 0x6a34); fine `= clamp(1,000,000 + approval%*20,000 + 100*S_proposer, 50,000, 10,000,000)` Cr (`colony_treasury_target` 0x6ab4; ECX: `approval*2,000,000/100`) |
| clause/target level offered | by approval of the partner: `<10` -> level 1 (Low), `<50` -> 2 (Medium), `>=50` -> 4 (High) (`colony_init_state` 0x67b4) |

These replace `diplomacy.md`'s "amount" for `offer_amount_calc_a` (it is the
**duration in days**, which also explains the 1800 cap vs the manual's 10-year
example) and confirm its fine formula.

**Who proposes, and when.** Each alien keeps two countdowns (`0xcb76`, NAP;
`0xcb78`, JCT), set at game start to `base + rng(0.3 base)` (0x7444 / 0x74a4)
and re-armed the same way when they fire. Bases by atmosphere
(section 3.3): NAP 300/400/500 and JCT 600/400/200 days for races 9..13; race
14 (Achaean) uses 999/999 so it effectively never initiates. At 0x15c24/0x15c84:

- **NAP proposal** (`0x6d64`): candidates are active races other than itself
  and race 13, mutually "known" (bit in `0xcb54` both ways) and not already
  paired by a NAP (`relations_pair_find`); a candidate qualifies if its score
  `race_approval_adj2` > 0, otherwise if `race_penalty_count` > 0; one is chosen
  at random. The clause bits offered: bit0 if `adj2 > 0`, bit1 if
  `penalty_count > 0`, 0x80 secret if `colony_econ_table[...] > 0`. If the chosen
  partner is the human the proposal is posted to the player's comms
  (`0x42014`); if it is another alien the counterpart evaluates it at once
  (`colony_econ_tick2` 0x6b54) and, on accept or an accepted counter, the NAP is
  created.
- **JCT proposal** (`0x6514`): partner candidates have `race_approval_adj` > 0;
  the treaty target is `race_pick_lowest` (0x63e4): the **nearest** (centroid
  distance) active, mutually-known race that is neither the proposer, the
  partner nor race 13. Evaluated by `colony_econ_tick` 0x61a4.

`race_penalty_count` (0x6954) = `21 - 20*(units of the candidate in the
proposer's penalty list) - 10*(asteroids of the candidate whose `+0x4c` word has
the proposer's bit)`: it falls for every grievance recorded against the candidate.

**Acceptance** (both evaluators, return 1 accept / 2 counter / 0 reject): let
`s = |clamp(share_diff%)|` with `share_diff` = relative strength difference of
the proposer versus a distance-weighted sum of the others: `s = 0` if the
difference is >= 20 %, `s = 5` for 5..19 %, else the absolute value (0..4). A
JCT is rejected when `approval_adj + s < 0`; accepted when no pact or treaty
between the two races exists and the terms are within `+-2*s %` of the AI's own
preferred fine and duration (`s` also scales the secret/overrun/level tolerance), else
the AI answers with its own terms ("however I have sent you a counter
proposal" **T**). A NAP clause bit is accepted when `adj2 > s` (overt) or
`penalty_count > s` (covert). The proposal is always rejected when a NAP or JCT
between the same races already exists.

### 6.6 Why O is hostility, not friendship **C~**

All of these have the sign of "aggression/hostility", none fits a "friendliness"
reading:

1. A Non-Aggression Pact drives both parties' value to -1.0; a Joint Combat
   Treaty drives each signatory's value toward the *target* to +1.0.
2. Shots fired at a race raise the shooter's value toward the victim
   (`X` push), and the value then decays back to a baseline.
3. A clean pact completion lowers it by 0.5; a violation raises the victim's
   value toward the violator by 0.5.
4. The attack-target weight is `avg(O,B)% + strength advantage`, required to be
   positive; `obj_find_best_relation` picks the *largest positive* value
   for a target; the defensive response needs `O[defender][attacker] > 0`.
5. Campaign text: the peaceful cultures (Rigellian, Achaean) have negative
   baselines (-20, -30) and the cultures the campaigns call hard (Mauna) a
   +40 baseline.

Consequently the **-1.0 cells in the 2026-08-07 runtime dump (pairs 9-11, 9-12,
10-12, 11-12, 14-11 and 11 toward player slot 1) are Non-Aggression Pacts in
force, not wars.** (The aliens had signed them among themselves by then.)

## 7. How aggression toward the player is produced (summary)

1. Starting hostility toward the player is the table in 6.2; atmosphere shifts
   it by +-40 points (Peaceful/Aggressive). Race 13 (Mauna) starts at 0.9 and
   has the highest baseline.
2. The human player's row is never updated by incidents *against* him, but
   every shot or collision the alien causes raises the alien's own value toward
   the target (6.1), and a violated pact raises the victim's. So an alien that
   keeps fighting the player stays hostile for as many days as it has fired
   weighted shots.
3. An alien chooses targets whose hostility-plus-strength approval is positive
   and within 192 units; the player is eligible whenever `avg(O,B)% +
   econ_diff% - distance penalty > 0`. A player that is much weaker than the
   alien (colony count dominates the score at 600 per colony) is attractive
   even at negative hostility; a player stronger than the alien by more than
   the baseline magnitude (e.g. 20 %-30 % for the peaceful cultures) is not.
4. Raids: every 32 days each alien runs `race_raid_tick`: it re-tasks the
   units standing on each known foreign asteroid, colonises unowned ones when it
   is small (<4 colonies) or the asteroid is valuable, and orders ships that can
   reach the nearest foreign asteroid to move there (task 2).
5. Joint Combat Treaties among aliens (proposal period 200..600 days) name the
   *nearest* rival as the target; at Aggressive atmosphere they are proposed
   three times as often as at Peaceful.
6. Agents: each race 1..14 receives a new available agent every 100..149 days
   (first one after 50..149); an alien agent that has "arrived" executes its
   mission at once. Every 150 days an alien with an agent picks the race with the
   highest approval (else highest `O`) and starts an agent mission: if the
   target owns more than 4 missile-defence buildings the mission is Missile
   defence sabotage, if more than 4 ship-defence buildings, Ship defence
   sabotage, else a random mission of the 13 (`slot_event_tick` 0xed84,
   `slot_event_queue_a/b` 0xef14/0xefc4, `slot_event_resolve` 0xecb4 calling
   the mission table at D 0x9bb8). **C~** (agent text in `economy-and-
   personnel.md`).
7. What actually *damages* the player (fleet launches, missile volleys) follows
   from the unit tasks of 5 and 6.4; the decision constants are not decoded.

Design-level reading for a remake: aggression = hostility value + relative
strength + distance, modulated by atmosphere only through the *starting
hostility*, the *pact/treaty offer rates*, the *expansion lead* and the *rates*
of change; there is no other difficulty variable in the alien code.

## 8. Trade, black market and APVs

The trade engine was found late; everything in 8.1-8.6 is read from code and
static data (**C**) unless tagged. The names `fleet_transfer_units`,
`asteroid_calc_*`, `asteroid_check_system_event`, `asteroid_ship_count_table`
etc. in the rename map belong to this subsystem and are wrong (section 10).

### 8.1 Parties and items **C**

Every trade quantity is kept per **party** (word counts at D 0xe904, cost
basis in Cr at D 0xe944, stride 0xf4 bytes per item, 32 parties per item):

| party | who |
|-------|-----|
| 0 | the **market pool** (unowned stock) |
| 1..8 | player slots |
| 9..14 | the six alien cultures (they also hold stock lines) |
| 15..22 | **Trade Merchants**, 8 delegate slots (record index 0..7) |
| 23..30 | **Traders**, 8 colony-visiting slots (record index 8..15) |

Item ids (101 items; text indices 2030 + id, the order of the trade list):

| ids | group | who trades it in the UI |
|-----|-------|--------------------------|
| 0..67 | 68 luxury goods | cultures and Trade Merchants |
| 68..72 | 5 pharmaceuticals (Biofort, Vir-Attack, Supa-Shellac, Swat, Star Balm) | cultures and Trade Merchants |
| 73..76 | 4 APVs (Shell Shock, Phantom, Judgement Day, Silicon Death) | **Traders only** |
| 77..86 | 10 ores | Traders: only ids **81..86** (Quazinc .. Nexos); Selenium..Crystalite are never listed |
| 87..99 | 13 missiles | Traders: only ids **90..99** (Hellfire, Scatter, Vortex, Nuclear, Virus, Anti-Virus, Mega, Stasis, Bug Hunter, Meat-Eater); Explosive, Area Explosive, Napalm are never listed |
| 100 | Information | Traders |

(The "which items a party can show" rule is the list-building loops of
`0x45a54`: parties 23..30 scan ids 0x49..0x4c, 0x51..0x56, 0x5a..0x63 and the
Information flag; every other party scans ids 0..0x48. A line is shown when
either the player or the party holds a non-zero count.)

Reference prices and global supplies (static tables D 0x32ed8 and D 0x3306c;
"-" = 0 / not applicable):

**Luxuries**

| id | item | ref price (Cr) | global supply |
|----|------|----------------|---------------|
| 0 | Beers | 4000 | 200 |
| 1 | Wines | 6000 | 200 |
| 2 | Altarian Panther Sweat | 70000 | 50 |
| 3 | St.Etienne's Real Cream & Honey Liqueur | 50000 | 100 |
| 4 | Muet & Champignon vintage champagne | 64000 | 100 |
| 5 | Fizzimo Lumiere | 75000 | 30 |
| 6 | Bristol glass | 6000 | 45 |
| 7 | Crystal Cantata Inc. products | 24000 | 25 |
| 8 | Deep pile velvet | 20000 | 50 |
| 9 | Silk | 10000 | 100 |
| 10 | Watered silk | 12000 | 80 |
| 11 | Raw silk | 10000 | 80 |
| 12 | Satin taffeta | 15000 | 60 |
| 13 | Egyptian sea-cotton | 1000 | 200 |
| 14 | Achaean angora | 20000 | 100 |
| 15 | Tiara & Bracelet set | 115000 | 5 |
| 16 | Choker | 123000 | 2 |
| 17 | Solitaire emerald | 250000 | 6 |
| 18 | Brooch | 150000 | 8 |
| 19 | Necklace | 65000 | 6 |
| 20 | Eternity ring | 125000 | 5 |
| 21 | Pectoral | 250000 | 2 |
| 22 | Collar | 75000 | 3 |
| 23 | 3-strand bracelet | 55000 | 10 |
| 24 | Diamond | 35000 | 15 |
| 25 | Emerald | 45000 | 5 |
| 26 | Sapphire | 28000 | 12 |
| 27 | Ruby | 30000 | 6 |
| 28 | Ultropaz | 17000 | 8 |
| 29 | Alexandrite | 17000 | 10 |
| 30 | Metachrome | 18000 | 10 |
| 31 | Opal | 11000 | 10 |
| 32 | Pearl | 13000 | 10 |
| 33 | Moonstone | 7000 | 17 |
| 34 | Astramarine | 16000 | 8 |
| 35 | Peridot | 5000 | 15 |
| 36 | Amethyst | 8000 | 12 |
| 37 | Abstract Sculpture | 20000 | 40 |
| 38 | Domestic interior units | 10000 | 60 |
| 39 | Decorative drinking horns | 10000 | 45 |
| 40 | Worked leather | 5000 | 65 |
| 41 | Ornamental archaic weaponry | 20000 | 20 |
| 42 | Fizzimo Liqueurs | 1000 | 500 |
| 43 | Rigellian ant eggs | 500 | 1000 |
| 44 | Pearls dissolved in brandy | 1100 | 350 |
| 45 | Goat's ear mushrooms | 600 | 250 |
| 46 | Organic corn on the cob | 450 | 1000 |
| 47 | Braccatian kulos cheese | 850 | 800 |
| 48 | Grains | 100 | 15000 |
| 49 | Seaweed | 150 | 15000 |
| 50 | Krill | 100 | 15000 |
| 51 | Water | 200 | 10000 |
| 52 | Ortok's Mansions | 100000 | 3 |
| 53 | Shades of Brutos | 850000 | 1 |
| 54 | Huskar Cigars | 4000 | 20 |
| 55 | Maunik's Cube | 110000 | 5 |
| 56 | Gong of Death Song | 1000000 | 1 |
| 57 | Holostar globes | 85000 | 5 |
| 58 | Besthelda's Apothecary | 150000 | 3 |
| 59 | Photoplasmic Cocoon | 1250000 | 2 |
| 60 | Steam Racers | 700000 | 5 |
| 61 | KKZ Quad | 550000 | 5 |
| 62 | Kraagil Oil | 500000 | 3 |
| 63 | Sacrificial Axe | 75000 | 1 |
| 64 | Horn of Plenty | 70000 | 1 |
| 65 | Dionne's Lightwork | 2500000 | 1 |
| 66 | Loving Cup | 30000 | 1 |
| 67 | Law of the Cube | 1250000 | 1 |
**Pharmaceuticals**

| id | item | ref price (Cr) | global supply |
|----|------|----------------|---------------|
| 68 | Biofort | 20000 | 50 |
| 69 | Vir-Attack | 15000 | 50 |
| 70 | Supa-Shellac | 13000 | 50 |
| 71 | Swat | 18000 | 50 |
| 72 | Star Balm | 13000 | 50 |
**APVs**

| id | item | ref price (Cr) | global supply |
|----|------|----------------|---------------|
| 73 | Shell Shock | 56000 | 30 |
| 74 | Phantom | 64000 | 30 |
| 75 | Judgement Day | 85000 | 25 |
| 76 | Silicon Death | 83000 | 25 |
**Ores**

| id | item | ref price (Cr) | global supply |
|----|------|----------------|---------------|
| 77 | Selenium Ore | 50 | - |
| 78 | Asteros Ore | 80 | - |
| 79 | Barium Ore | 150 | - |
| 80 | Crystalite Ore | 400 | - |
| 81 | Quazinc Ore | 1200 | 500 |
| 82 | Bytanium Ore | 1300 | 500 |
| 83 | Korellium Ore | 2300 | 500 |
| 84 | Dragonium Ore | 3500 | 500 |
| 85 | Traxium Ore | 50000 | 20 |
| 86 | Nexos Ore | 150000 | 20 |
**Missiles**

| id | item | ref price (Cr) | global supply |
|----|------|----------------|---------------|
| 87 | Explosive Missile | - | - |
| 88 | Area Explosive Missile | - | - |
| 89 | Napalm Missile | - | - |
| 90 | Hellfire Missile | - | - |
| 91 | Scatter Missile | - | - |
| 92 | Vortex Missile | - | - |
| 93 | Nuclear Missile | - | - |
| 94 | Virus Missile | - | - |
| 95 | Anti-Virus Missile | - | - |
| 96 | Mega Missile | - | - |
| 97 | Stasis Missile | - | - |
| 98 | Bug Hunter Missile | 55000 | - |
| 99 | Meat-Eater Missile | 95000 | - |
**Information**

| id | item | ref price (Cr) | global supply |
|----|------|----------------|---------------|
| 100 | Information | 15000 | - |

The missile prices are not in the reference table: the monthly update (8.3)
sets `price(87+t) = cost(t) + N(t) * oreprice(ore(t))` from the missile table
(D 0xb3b0: +8 cost, +4 ore type, +5 `N`): Explosive 800 + 1 x Selenium, Area
Explosive 6,400 + 2 x Barium, Napalm 5,000 + 1 x Quazinc, Hellfire 16,000 +
3 x Quazinc, Scatter 15,000 + 3 x Selenium, Vortex 8,000 + 3 x Crystalite,
Nuclear 50,000 + 5 x Bytanium, Virus 30,000 + 1 x Traxium, Anti-Virus 10,000
+ 4 x Barium, Mega 100,000 + 1 x Nexos, Stasis 40,000 + 2 x Korellium. So `N`
is an ore quantity of the missile; the same byte is also the AI per-colony stock
cap (verified C@0x19ADF); `stat-tables-design-sheet.md` section 4 now records
both roles (Corrected 2026-10-18).

### 8.2 Who appears and when **C**

The scheduler is `event_scheduler` (0xf404). It is the **trade delegate
scheduler**, not a colony random-event scheduler. Two independent mechanisms,
each enabled by its own flag (section 2: Traders `0xc6cc` after the player's
2nd-3rd claim, Merchants `0xc6d0` after the 3rd-4th claim; the whole scheduler
is off when `[0x16618] != 0`):

| | Trade Merchants (records 0..7) | Traders (records 8..15) |
|---|---|---|
| per player race timer | `0xcb61`, re-armed **150 + rng(90)** days (150..239) | `0xcb60`, re-armed **150 + rng(50)** days (150..199) |
| when it fires | picks a free record at random, excluding the one that last left for this race (`0xcb63`); if none is free it retries in **20 days** | same, excluding `0xcb62` |
| the record | owner = the race, active; visit length **150 + rng(50)** days | owner = the race, flagged "needs target" (bit 4); request window **30 days** |
| player messages | "Trade Merchant %s available" (type 10); at 10 days left a 10-day "leaving your sector" warning; the record then frees and remembers itself as last-left | a "Trader %s requesting target" message (available in %d days, select a colony to visit); reminder at 10 days; if the player picks one of his own asteroids before the window ends (`0xf3b4` stores the asteroid pointer) the trader becomes a normal visit at that asteroid with a 10-day leave warning; if no colony is chosen the trader leaves silently |
| initial timer value | 0 in the file, so the first offer comes after about 256 days once the flag is on (**C~**) | same |

The names shown come from the 8-entry table at 0x395a4 (record index to
name). A Trade Merchant is reachable from the Trade menu without choosing a
colony; a Trader's goods (ores, missiles, APVs, Information) are delivered to
and taken from the visited asteroid's stores and silos (ore: `+0x150 + 2*ore`
on the asteroid node; missiles: objects created in or removed from the
asteroid's missile list, `0x1f824` / `0x1f8c4`). The Trader visit length after
the target is chosen is set in a path the decompiler lost (an `rng` call,
**?**).

### 8.3 Price model **C**

Prices are global, **not per trader**: the buy and sell price functions do not
depend on the party. They are recomputed by the monthly market update
`0x47574` (called every 30 days, `[0xbd00]*120` outer passes, plus 12 warm-up
steps at new game by `0x470b4`):

```
for every item k with a reference price R[k] (ids 0..86, 98, 99):
    w   = (0x100*sin(a) + 0x55*sin(b) + 0x33*sin(c)) >> 8        # sin in 16.16
    w  /= 2                                      if k is an ore (77..86)
    P   = R[k] * (0x20000 + w) >> 17             # 1 + w/131072
    P   = P * (0x100 + rng(25)) >> 8             # +0 .. +9.4 % noise
where a = ((phase1 >> 8) + item_byte1) & 0xff, b and c likewise with phase2/3,
phase1 += 0x444, phase2 += 0xccc, phase3 += 0x1555 per month,
item_byte1..3 = three random bytes per item chosen at new game.
```

So each item follows three sine cycles of about **60, 20 and 12 months**
(amplitudes 1.0 : 0.33 : 0.20 of +-0.5), i.e. the price swings between about
0.23 and 1.77 times the reference (ores half as far: 0.62..1.38) plus a 0..9 %
upward noise term. The previous monthly prices of every item are kept in a ring
(the "price per unit over the past year" graph). The ten ore prices are copied
to the **Federation ore price** table (0xe808 + 4k) each month, so Federation
ore revenue and trade ore prices are the same number (this answers open
question 2 of `economy-and-personnel.md`: the unit values change monthly by
this formula). Missile prices use the ore prices of the same month (8.1).

What the player pays and receives (`P` = this month's price):

| item class | player **buys** at | player **sells** at |
|------------|--------------------|---------------------|
| luxury goods, pharmaceuticals (0..72) | `P` | `0.85 P` |
| APVs (73..76) | `P` | `0.50 P` |
| ores (77..86) | `max(P, 1.4 * (P + 0.2*(P - R)))` | `P + 0.2*(P - R)` |
| missiles (87..99) | `1.40 P` | `1.03 P` |
| Information (100) | one price `I = 7,500 + 100*floor(rng(30000)/100)` per month (7,500..37,400) | not sellable |

(`R` is the static reference of the ore.) Money moves only for player parties;
alien parties have no treasury. The player's **average price paid** is the cost
basis per unit (`value/count`); a sale removes cost basis proportionally. The
transfer routine (`0x45d84`) moves the count, adds `price*count` to the
buyer's basis and subtracts the proportional basis from the seller's, and
updates the Money bucket of any party < 9. The UI totals are computed by
`0x462a4`: positive selected quantity (player sells) at the sell price,
negative (player buys) at the buy price.

### 8.4 Stock **C**

- The pool (party 0) starts with the global supply `S` of each item. Each
  month the pool of **pharmaceuticals (68..72), APVs, ores and missiles** is
  reset to `S - (sum of counts held by the other parties)`; for ids >= 77 the
  sum starts at party 9 (player holdings do not reduce it), for ids <= 76 it
  includes the players, so player purchases of pharmaceuticals and APVs shrink
  the supply. Luxury goods (0..67) are never re-stocked: the pool only changes
  through trades and returned stock lines.
- Stock lines of a party (`0x46f14` adds a line, `0x472b4` trims/adds,
  `0x47574` refreshes every culture party 9..14 and every inactive
  merchant/trader once a month):
  - merchants and cultures hold **5..12** lines; each added line is: with 40 %
    (merchants; 20 % for cultures, with an Artemian special case of
    Biofort/Vir-Attack/Star Balm) a pharmaceutical, otherwise a random luxury
    id 0..67; quantity `(S/(n+8) + 1 + rng(S/(n+8))) / 2` capped by the pool,
    `n` = number of configured races;
  - Traders hold **4..8** lines; each added line is: 50 % one of the six
    higher ores (ids 81..86), 40 % one of the ten missiles 90..99, 10 % one of
    the four APVs; quantity `(S/8 + rng(S/8))/2 + 1` capped by the pool
    (about 32..63 units of a 500-supply ore, 2..3 Traxium/Nexos units or APV
    doses, 1 missile, because missiles have no supply value);
  - when a party exceeds its minimum (merchants 5, traders 4) a random line is
    returned to the pool, with an extra 50 % chance of a second trim, and a
    50 % chance of one more added line below the maximum;
  - a Trader also carries up to three **asteroid ids** for the Information
    item (first always, second always if different, third 50 %); buying
    Information marks those asteroids as known to the buyer.
- The player can sell any listed item back; the pool grows accordingly.

### 8.5 Gifts and relations **C**

A transfer with unit price 0 is a **gift**. `relations_adjust_value` (0x47f24)
lowers the receiving alien's hostility toward the giver:
`O := max(B, O - value/1000)` where `value = P(item) * count * m` in Cr and the
multiplier `m` is 1 except for culture-specific artefacts and remedies (item
ids by text): **Braccatia** receiving the Gong of Death Song (id 56) `m = 25`,
the Horn of Plenty (id 64) `m = 10`; **Artemia** receiving the Sacrificial Axe
(id 63), Supa-Shellac (id 70) or Swat (id 71) `m = 10`. One raw unit of `O` is
1/32767 of the range, so an ordinary 100,000 Cr gift is worth 100 units
(0.3 %); only the Gong (1,000,000 x 25 / 1000 = 25,000 units = 76 %) really
moves a culture.

A hidden **Braccatian grudge** exists: the command at 0x47e54 (called with
second argument 10) stamps a per-player day (`0xcb8c`); 90 days later
(`relations_tick_boost`, 0x47e84, called from `race_ai_tick`) the stamp is
cleared and Braccatia's `O` toward that player rises by 0x1000 (12.5 %) and `B`
by 0x400 (3 %); returning the Gong resets `O := B` and lowers `B` by 0x800, and
any gift worth more than 100,000 (after `m`) clears the stamp. This matches the
game text on the Gong (keeping it without meaning to return it invites
trouble from the Braccatia once they find out) and suggests, but does not
prove, that acquiring the Gong (or trading with Braccatia) arms the stamp
(**C~**). Paying money (tribute or fine, not a trade) never changes `O`; it
changes the wealth counter of section 5.

### 8.6 APV mechanics **C**

The six anti-personnel viruses are **colony events** `0..5` in the table at D
0x9dc4 (12-byte records `{handler, race mask word, byte, byte cure, byte period,
word}`; handler pointers in the table are 4 low, e.g. 0x138a0 means 0x138a4):

| id | virus | susceptible (mask bits) | cure | stage length |
|----|-------|-------------------------|------|--------------|
| 0 | Shell Shock (APV) | Artemia (0x1000) | Swat | 30 |
| 1 | Phantom | Mikotaj (0x0800) | none | 30 |
| 2 | Judgement Day | Terran + Braccatia + Achaean (0x4402) | none | 20 |
| 3 | Silicon Death | Braccatia + Mauna + Achaean (0x6400) | Biofort | 30 |
| 4 | Bug Hunter | Artemia (0x1000) | Vir-Attack | 30 |
| 5 | Meat-Eater | Terran + Braccatia + Achaean (0x4402) | Vir-Attack | 20 |

(Terran = bit 1, which every human player slot uses; aliens use their own bits
9..14: 0x0400 Braccatia, 0x0800 Mikotaj, 0x1000 Artemia, 0x2000 Mauna, 0x4000
Achaean.) An event is created by `event_queue_post` (0x13e74) on an asteroid of
a susceptible owner; no two events of the same APV type coexist on one
asteroid, and a natural disease (types 6..11) additionally blocks a second
disease. The cure column matches the game text exactly (Swat cures Shell
Shock, Biofort cures Silicon Death, Vir-Attack cures Meat-Eater and Bug
Hunter).

Population effects (`+0xc2` of the asteroid; one handler call per day while the
event is active; the event ends only when a handler writes 0x7fff into the
node's threshold `+0xa` or the Chief Medical Officer's cure is authorised
(text 295-297); a handler that never writes it keeps draining until the
colony is dead):

| APV | acute phase | afterwards (every day until cured) |
|-----|-------------|-------------------------------------|
| Shell Shock | none: -(2 + rng(5)) = **2..6 per day** | same, never ends: 100 % |
| Phantom | incubation 0, then a budget of `0.8 * population` spread evenly over `8 + rng(3)` = 8..10 days (**80 %**) | -(1 + rng(2)) = 1..2 per day |
| Judgement Day | incubation `10 + rng(10)` = 10..19 days (**"about a fortnight"**), then one blow of `70 + rng(10)` % (**70-79 %**); 5 % chance the event ends there | 95 %: -(1 + rng(5)) = 1..5 per day |
| Silicon Death | -(3 + rng(2)) = **3..4 per day** | same, never ends (the "85 %" of the text is not enforced by code) |
| Bug Hunter | budget `0.5 * population` over `3 + rng(4)` = 3..6 days (**50 %**) | -(1 + rng(4)) = 1..4 per day |
| Meat-Eater | -(2 + rng(3)) = **2..4 per day** | same, never ends: 100 % |

Consequence: **Phantom and Judgement Day have no cure** (cure column "none"),
so against a susceptible colony they end only by extinction (Judgement Day
has a 5 % chance to stop after its blow); the other four are stopped by the
matching pharmaceutical. The messages "Colony Sickness Warning", "%s Detected",
"%s Emergency", "%s Contained" are the stage texts **T**.

Delivery: the agent mission **APV delivery** (mission 4, 350,000 Cr, mission
table in `stat-tables-design-sheet.md` 6.1, executor 0xde04) posts the chosen
virus (index 0..5 in the order byte `+0xb`) on the target asteroid when the
agent arrives; "You Do Not Have Any APVs To Use" is the refusal, so the virus
must have been bought first. The inventory routine is `0x47dce` (consume one
dose: `count -= 1`, cost basis reduced proportionally; the UI bitmask of owned
APVs is `0x47d94`). The two APV *missiles* Bug Hunter and Meat-Eater use the
same event path from the warhead impact (**C~**). The six natural diseases
(types 6..11: Astrophobia, Rigellian Flu, Deep Space Debilitation, Korsakov's
Syndrome, Belt Fever, Spacer's Salmonella; cures Star Balm, Vir-Attack x4,
Biofort) affect Terrans only and come from the random colony-event system of
the player slots; durations 21..28 days (Astrophobia), 28..41 days with 5..10
deaths per day up to 40 % of the population (Flu), 120..179 and 90..149 days of
reduced efficiency without deaths (Debilitation, Korsakov's).

Risk summary for the player: a human colony is susceptible to exactly two APVs,
Judgement Day (no cure: 70-79 % in one blow after 10-19 days, then a slow
bleed) and Meat-Eater (cure Vir-Attack, kills 2..4 per day, never ends by
itself); Vir-Attack (15,000 Cr reference, supply 50, sold by merchants) is the
Terran defence against Meat-Eater, and there is none against Judgement Day. The dangerous sellers are the **Traders** (10 % of their lines are
APVs, 2..3 doses each, 56,000..85,000 Cr reference). Whether *aliens* use APVs
against the player is **?**: alien agents pick their mission with the
defence-count rule or at random (section 7, item 6) and the code path that
would carry an APV index for an alien agent was not found.

### 8.7 Legality and the black market **T**

The game text marks items by legality: Fizzimo Lumiere (export from Achaean
space illegal), Shades of Brutos and Law of the Cube and all trade with the
Mauna or in Maunid items (illegal under Federal law), Huskar Cigars (illegal,
black market), Besthelda's Apothecary (outlawed), Photoplasmic Cocoon (banned),
Steam Racers (illegal), KKZ Quad (banned), Kraagil Oil (black market only,
endangered species), goat's-ear mushrooms (probably illegally harvested); sacred artefacts (Gong, Horn of Plenty, Loving Cup, Law of the
Cube) must not be sold back to their owners without risk. None of these flags
exists as a field in the price or stock tables: the legality is flavour text
plus the unit values (the sacred and banned items are the 500,000..2,500,000 Cr
entries). The code-level consequences found are the Gong grudge (8.5) and the
Mikotaj/Achaean-trade-with-Mauna accusations (text 242/243; the posting code
was not located **?**). Agent sabotage side channels (ships sold on the black
market, ore, missiles, blueprint theft) are in `economy-and-personnel.md` /
`scitek-blueprints.md` **T**.

### 8.8 Unresolved

- How the Trade menu decides which of the six cultures are "available" (the
  culture parties 9..14 hold stock, but their availability gate was not found).
- The 8-name table (0x395a4): which indices are the six cultures' delegates and
  which are black-market dealers.
- The Trader visit length after a target is chosen; the true initial values of
  the two timers.
- Whether aliens ever buy from or sell to the pool beyond the stock refresh.

## 9. Design-ready quick reference

All numbers GOG build, days unless stated.

| quantity | value |
|----------|-------|
| game day | 4 x D outer passes, D = 8 (+8 or +4 per speed step) |
| victory | all other configured races have 0 asteroids (needs >= 2 configured races) |
| defeat | player owns 0 asteroids |
| time limit | none |
| alien races | 9 Rig, 10 Bra, 11 Mik, 12 Art, 13 Mauna, 14 Ach |
| arena cells | 24x15 / 29x18 / 32x20 |
| asteroid ceiling | 30/45/60, 40/60/80, 50/75/100 |
| start Money | 1,000,000 Cr, all atmospheres |
| daily stipend per player | 100 / 250 / 400 Cr (atmosphere) |
| initial hostility shift | -40 / 0 / +40 points |
| hostility rate shift | -50 / 0 / +50 % |
| NAP proposal period | 300 / 400 / 500 (+0..30 %) |
| JCT proposal period | 600 / 400 / 200 (+0..30 %) |
| race 14 offer period | 999 |
| expansion period | 205 / 200 / 210 / 185 / 190 / 195 (+-10 %) |
| alien colony target | (largest human colony count) + adj, adj by culture/atmosphere in 3.3 (0..3) |
| alien raid period | 32 |
| alien structure caps | 15 / 10 / 6 / 4 by class |
| alien build pace | 8 / 15 / 20 / 20 days (above cap), 1-2 days (below) |
| reach for target tracking | 192 units |
| retaliation radius | 60 units (120 with the special building) |
| NAP | grace 10 days, violation -> 5 days to end, +-0.5 hostility on end |
| JCT quotas | 400 / 1000 / 3000 shots; overrun fine 30 Cr per shot |
| pact duration offered | 90..1800 days |
| pact fine offered | 50,000..10,000,000 Cr (base 1,000,000) |
| agents | new available agent per race every 100..149 days |
| alien agent mission | every 150 days per race with an agent |
| APV losses | see 8.6 (Judgement Day and Phantom have no cure) |
| market update | every 30 days; price = ref x (1 + w) x (1 + rng(25)/256), w = three sines (60/20/12 months), halved for ores |
| player sells / buys (goods) | 0.85 P / P (APV 0.50 P / P; ores P + 0.2(P-R) / max(P, 1.4x); missiles 1.03 P / 1.40 P) |
| Trade Merchant offered | every 150-239 days per player race, stays 150-199 days |
| Trader offered | every 150-199 days, 30-day target window, 10-day leave warning |
| stock lines | merchants/cultures 5-12 (goods, 40 % pharma), traders 4-8 (50 % ores 81-86, 40 % missiles 90-99, 10 % APVs) |
| gift effect | -value/1000 raw hostility units (Gong x25, own artefact/remedy x10) |
| Gong grudge | 90 days after the stamp: Braccatia O +0.125, B +0.03 |

## 10. Corrections to existing notes

- `diplomacy.md`: (a) the opinion cells are **hostility**, not friendliness
  (6.6); (b) cells at 0x8000 are Non-Aggression Pacts in force, not wars (the
  runtime dump section is re-read accordingly: the pairs 9-11, 9-12, 10-12,
  11-12, 14-11, 11-player are pacts); (c) the GOG function `relations_declare_create`
  (0x4844) is the NAP creator (the reference `war_node_create`) and
  `combat_event_create` (0x45c4) the JCT creator (`pact_node_create`); the
  "formal treaty / embargo" and "mutual pact" bit descriptions are the
  `0xcb4c/0xcb4e/0xcb54` bitsets (known, declared, contacted); (d)
  `offer_amount_calc_a` is the offer **duration in days** (90..1800); (e) the
  "tribute amount" branch of the daily tick (reference `0xd0a6`) is in the GOG
  build the normal incident-push path fed by the incident matrix `X`
  (probably the same matrix as the reference `0xd0a4`, addressed with a
  one-column offset): it is not a dead tribute path; (f) the player's own row is zero, so the "scenario's starting
  dispositions" of rows 1..8 are not data; (g) all per-race tables the reference
  note called "code region, unconfirmed" are readable in the GOG build (6.2,
  section 3).
- `main-loop.md`: state 0xf is `race_master_tick` (alien master tick), not the
  end-game state; states 9..14 are the per-alien `race_objects_tick`;
  `g_victory_state` 2 = player lost, 3 = lone survivor/victory (not "2 = only
  the player left"); the "tick > 700" enables are supervisor/agent/event
  enables armed by the player's claims (section 2) and day counts, not alien
  switches; `0x16612` is the atmosphere, `0x16610` arena, `0x16611` density.
- `asteroid-spawning.md`: the gate table at D 0x9cb0 is readable and equals
  30,45,60 / 40,60,80 / 50,75,100; the arena table D 0x1663c equals 24,15 /
  29,18 / 32,20.
- `economy-and-personnel.md`: open question 1 resolved: income table index is
  the atmosphere (100/250/400 per day per player race). Open question 2
  resolved: the ore unit values `0xE808 + 4k` are the monthly trade prices of the
  ten ores (section 8.3: reference x sine waves x noise, copied every 30 days).
  The "ore found/lost" and Federation price discussion should use that formula.
- `main-loop.md` and the map: `event_scheduler` (0xf404) with the 16 records at
  0xc205/0xc206 is the **Trade Merchant / Trader scheduler**; `slot_timer_a/b_arm`
  (0xf264 / 0xf124) arm Traders / Merchants; `asteroid_check_system_event`
  (0x472b4), `rng_extra_roll` (0x46f14), `fleet_transfer_units` (0x45d84),
  `asteroid_calc_display_value` / `asteroid_calc_stat_value` (0x45c04 /
  0x45cc4), `asteroid_sync_display_data` (0x45944) are the trade stock, transfer
  and price routines; `g_asteroid_ship_count_table` (0xe904) and
  `g_asteroid_ship_value_table` (0xe944) are the per-party trade counts and
  cost basis; `g_asteroid_stat_value_table` (0x32ed8) is the static item price
  table. The "colony random events" of the text (explosions, thefts) are not in
  this scheduler.
- `stat-tables-design-sheet.md` 4: the missile record's `+5` byte `N` is the
  ore quantity used in the market price (8.1) and also the AI stock cap (both reads verified, reconciled in the sheet); the Bug Hunter / Meat-Eater
  entries do have prices (55,000 / 95,000 reference) and are Trader stock.
- `stat-tables-design-sheet.md` 6.3: the 28-byte records at flat 0x8f680 are
  the per-structure cost/threshold table of the alien build code
  (`planet_pending_build_tick` reads costs from D 0x967c); `0x8f5d0` triples are
  the alien pact/treaty offer periods (section 6.5), not income.

## 11. Open questions

1. Alien fleet launches: composition, strength thresholds and the missile-volley
   decision (tables D 0x9f78..0x9fc3 and the arsenal lists at flat 0x91488 are
   present; the consumers `obj_fill_component_slots`, the build-queue spawner
   0x19284 and the alien task executor were not traced). **?**
2. Trade: which cultures the Trade menu lists as available, the 8-name table
   at 0x395a4, the Trader visit length, the initial delegate timers and any
   relation consequences of illegal goods other than the Gong grudge (8.8).
   The `g_msg_*` id-to-variable mapping is piecewise (linear in two
   segments) and was not needed. **?**
3. Whether alien agents can choose mission 4 (APV delivery) and with which virus.
4. Exact `combat_weighted_pick` constants and the `+0x128/+0x12a/+0x12c` fields.
5. What sets `[0x16618]` (mode flag) and `[0x1660d]`; whether the options
   screen row `[0x1660f]` really is "Time On/Off in menus" and why it changes
   the day length (`life-support.md`).
6. Meaning of the "TetraCorp rating" on the statistics screen.
7. `ship_acquire_target` bearing (`+0x1b7`) consumer details, and what the
   `+0x98` marks of `asteroid_ships_spawn` do beyond agent cover.
8. Per-weapon-class incident weights: the order of classes 0..17 in D 0xb9e8
   versus weapon names (classes 0..10 follow the missile table).
9. Hostility cannot be seen by the player directly in the code paths read; the
   diplomacy screen's wording of levels (messages around text 2798-2830) was not
   mapped to thresholds.

## Appendix: proposed rename-map entries (not applied)

Globals (GOG): 0x16610 `g_arena_size_index`; 0x16611 `g_asteroid_density_index`;
0x16612 `g_atmosphere`; 0x1660e `g_game_speed_index`; 0x16614 `g_culture_mask`;
0x1529c `g_configured_race_count`; 0x1687c `g_campaign_number`; 0xc6bc
`g_day_count`; 0x16630 `g_outer_tick`; 0x16624/28/2c `g_cal_day/month/year`;
0x16864 `g_victory_state` (values 2 = lost, 3 = won); 0xc98c `g_hostility_baseline`
(B); 0xc9aa `g_hostility_current` (O); 0xc9c8 `g_hostility_incident` (X);
0xc9e6 `g_hostility_gain` (C); 0xc9f5 `g_hostility_decay` (D); 0xca7c
`g_hostility_grace_days` (A); 0xcb4c/0xcb4e/0xcb54 `g_nap_known_bits` /
`g_nap_declared_bits` / `g_contact_bits`; 0xcb56 `g_alien_expand_timer`; 0xcb5a
`g_alien_raid_timer`; 0xcb5e `g_agent_count`; 0xcb5f `g_agent_spawn_timer`;
0xcb74 `g_alien_slot_event_timer`; 0xcb76 `g_alien_nap_timer`; 0xcb78
`g_alien_jct_timer`; 0xc300 `g_transporter_count`; 0xbd48 `g_nap_list`; 0xbd50
`g_jct_list`; 0x1d8 asteroid field `+wealth`.

Trade (GOG): 0xf404 `event_scheduler` -> `trade_delegate_scheduler`; 0xf124
`slot_timer_b_arm` -> `trade_merchant_arm`; 0xf264 `slot_timer_a_arm` ->
`trader_arm`; 0xf3b4 (unnamed) -> `trader_set_target`; 0x45d84
`fleet_transfer_units` -> `trade_transfer`; 0x46244 `ui_refresh_stats_table` ->
`trade_refresh_prices`; 0x45c04 `asteroid_calc_display_value` ->
`trade_sell_price`; 0x45cc4 `asteroid_calc_stat_value` -> `trade_buy_price`;
0x462a4 `asteroid_calc_total_assets` -> `trade_net_total`; 0x45a54
`asteroid_build_visible_systems` -> `trade_build_item_list`; 0x45944
`asteroid_sync_display_data` -> `trade_sync_player_stock`; 0x46f14
`rng_extra_roll` -> `trade_add_stock_line`; 0x472b4
`asteroid_check_system_event` -> `trade_party_refresh`; 0x470b4 (unnamed) ->
`trade_market_init`; 0x47574 (unnamed) -> `trade_monthly_update`; 0x47dce
(unnamed) -> `apv_consume`; 0x47d94 `asteroid_ships_present_mask` ->
`apv_owned_mask`; 0x47e84 `relations_tick_boost` -> `braccatia_grudge_tick`;
0x47f24 `relations_adjust_value` -> `gift_adjust_hostility`. Globals/tables:
0xe904 `g_trade_count` (stride 0xf4 per item, word per party); 0xe944
`g_trade_basis`; 0xe8cc `g_trade_price` (same stride); 0xe808
`g_federation_ore_price`; 0x32ed8 `g_trade_ref_price`; 0x3306c
`g_trade_supply`; 0xc205 `g_trade_delegate_records` (16 x 12 bytes);
0xcb60 / 0xcb61 `g_trader_timer` / `g_merchant_timer`; 0xcb62 / 0xcb63
`g_trader_last` / `g_merchant_last`; 0xcb8c `g_braccatia_grudge_stamp`;
0x14910..0x14918 `g_market_phase`; 0x395a4 `g_trade_delegate_names`; 0x1481c
`g_information_price`; 0xb9e8 `g_incident_weight_by_category`; 0xb3b0
`g_missile_table` (stride 16).

Data tables (displacements): 0x93b0 `g_atmosphere_stipend`; 0x9504 / 0x9531
`g_atm_shift_O` / `g_atm_shift_B`; 0x94d4 / 0x94d7 `g_atm_rate_gain` /
`g_atm_rate_decay`; 0x95cc `g_alien_nap_period`; 0x9614 `g_alien_jct_period`;
0x9f36 `g_alien_expand_lead`; 0x9ec0 `g_alien_expand_period`; 0x9ecf
`g_alien_raid_period`; 0x9e60 `g_alien_struct_cap`; 0x9e78 `g_alien_spawn_period`;
0x9e90 `g_alien_prod_period`; 0x9ea8 `g_alien_build_period`; 0x9c54
`g_campaign_table`; 0x9cb0 `g_asteroid_ceiling`; 0x965c `g_jct_quota`; 0x9db8
`g_alien_reach`; 0xafcf `g_alien_transporter_type`; 0x9dc4 `g_sickness_table`.

Functions: 0x15f64 `race_master_tick` (keep) with comment "alien master tick";
0x15ce4 `race_objects_tick` -> `alien_asteroid_tick`; 0x15204 `slot_timer_reset`
-> `alien_expand_attempt`; 0x7444 `rng_discard` -> `alien_nap_timer_arm`; 0x74a4
`rng_discard2` -> `alien_jct_timer_arm`; 0x6d64 `race_pressure_tables` ->
`alien_nap_propose`; 0x6514 `race_approvals_table_fill` -> `alien_jct_propose`;
0x6b54 `colony_econ_tick2` -> `nap_evaluate`; 0x61a4 `colony_econ_tick` ->
`jct_evaluate`; 0x4844 `relations_declare_create` -> `nap_create`; 0x45c4
`combat_event_create` -> `jct_create`; 0x5164 `relations_event_tick` ->
`nap_daily_tick`; 0x51c4 `combat_daily_tick` -> `jct_daily_tick`; 0x4ed4
`relations_treaty_resolve` -> `nap_end_clean`; 0x4d84 `relations_conflict_resolve`
-> `nap_end_violated`; 0x4b64 `relations_event_append` -> `nap_violation`; 0x55b4
`relations_matrix_tick` -> `hostility_daily_tick`; 0x4144 (unnamed) ->
`hostility_init`; 0x5c34 `race_score_calc` -> `race_strength_score`; 0x60f4
`race_approval_adj` -> `target_score`; 0x126f4 `obj_approach_track_update` ->
`alien_target_track`; 0x174b4 `combat_weighted_pick` -> `alien_target_pick`;
0x17f34 `race_attack_tick` -> `alien_defence_scan`; 0x17e24 `race_attack_launch`
-> `alien_defence_launch`; 0x14604 (unnamed) -> `ai_features_setup`; 0x13e74
`event_queue_post` -> `colony_sickness_post`; 0xed84 `slot_event_tick` ->
`alien_agent_mission_tick`; 0x10004 `race_elimination_check` (keep) and 0xff34
`race_asteroid_respawn` -> `race_eliminate`.
