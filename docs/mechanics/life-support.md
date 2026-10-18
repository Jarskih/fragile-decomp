# Time base and colony life support

Status: probing. The time base, the daily colony update, the formulas and the
constants below are read directly from the GOG retail build's code and data
(confirmed statically); runtime values for a few inputs (game-speed index
mapping, the CPU decay callback, event magnitudes) are still hypotheses and
are marked `?`.
Source: static disassembly of the GOG flat (`build/flat/gog_disasm.txt`) and
its named decompilation (`build/named/FRAGILE.EXE.gog.flat/decompiled.c`);
data tables read from the flat at "DS displacement + 0x86004" (see
"Addressing note"); savegame diffs (parallel agent, `savediff/findings.md`:
day counter, tick counter, credits); game text and manual claims are kept in
a separate section and never used as evidence for a formula.

All addresses are image-relative in the GOG flat (same convention as
`main-loop.md`). Race ids used by the race masks and per-race tables: 1 =
TetraCorp (the player), 2..8 = HumanCorp factions, 9 Rigellian, 10 Braccatia,
11 Mikotaj, 12 Artemia, 13 Mauna, 14 Achaean (derivation in
`alien-ai-trade-victory.md`, section 0).

## Addressing note (how the tables were read)

Code and data use DS-relative displacements. For data tables this build puts
the byte at displacement `D` at flat offset `D + 0x86004` (verified: the
building priority table at displacement 0x9387 decodes as a permutation of
0..39, the month-length table at 0x34728 decodes as 31,28,31,30,..., the
death-chance table at 0x937C is monotone 0..100). Values quoted below as
"table @ D" were read this way. This is consistent with the offset note in
`building-stat-table.md`.

## 1. Time base

### Counters (all confirmed)

| address | role | evidence |
|---------|------|----------|
| 0x16630 | **global tick counter** (one increment per outer-loop pass, at 0x4E25A); saved at the end of the SAVEDATA block (save 0xA978) and copied into each asteroid node (+0xA4) | disasm; savegame diff |
| 0xBD00 | **day-length parameter D**: ticks per "quarter-day" step. Written at new-game setup (0x228C4) and re-stored by the state driver | disasm |
| 0xC6BC | **absolute day count** (0 at new game, +1 per calendar step). The existing name `g_tick_counter` is misleading: it counts days, not ticks | incremented at 0x4D737 by the calendar routine; savegame 0xA04 is its saved copy |
| 0x16624 / 0x16628 / 0x1662C | **calendar day (1..31), month (1..12), year**. Existing names `g_cur_race` / `g_colony_pos_x/y` are wrong (see Corrections) | read/written only by the calendar routine 0x4D6C4 and new-game setup 0x22756 |
| 0x16620 | scenario seed (fixed 0x7BA for scripted mode, else a 16-bit roll) | 0x2284D/0x22863 |
| 0x34720 | per-tick state selector (`g_game_state`), -1 on idle ticks | 0x4D5D4 |
| 0x34724..0x34727 | four enable flags set by the driver (see below) | 0x4D5D4 |
| save 0xA08 | fraction of day, 16.16 fixed, equals tick-in-day * 0x800 | savegame diff |

### The state driver 0x4D5D4 (`game_state_driver`)

Run once per outer-loop pass, right after the tick counter increments
(outer loop body 0x4E255..0x4E47D). With `T` = tick counter and `D` = 0xBD00:

1. All four enables and the state are cleared (state = -1).
2. If `(T-1) mod (D/4) == 0`: `g_game_state = (4*T / D) & 0xF`. So the 16 states
   each get one tick, spaced `D/4` ticks apart; the cycle repeats every `4*D`
   ticks.
3. If `T mod D == 0`: enable 0x34724 is set (`g_ai_economy_enable`), and the
   quarter `q = (T / D) & 3` selects a second flag through a 4-entry jump
   table: `q=0` sets 0x34726, `q=1` and `q=3` set 0x34725, `q=2` sets 0x34727.
4. After the driver the outer loop calls the **calendar routine 0x4D6C4**
   whenever 0x34726 is set.

Consequences:

- **1 game day = 4 * D ticks** (one `q=0` event = one full state cycle = one
  calendar step). At the default `D = 8` that is **32 ticks per day**, matching
  the savegames exactly (tick = 32*day + tick-in-day in all 18 saves).
- Everything dispatched by state 2 (colony economy) and state 3 (structure
  behaviours) and state 5 (asteroid daily drift) therefore runs **once per
  day**. Per-tick work (state -1 tail, fleets, relations, AI) is not daily.
- The month cadence call at 0x4E3FC (`T mod (120*D) == 0`, 0x47574) is every
  30 days at any speed.

### Calendar routine 0x4D6C4 (`calendar_advance`)

Increments the day counter 0xC6BC, then the calendar day; if the day exceeds
the month length it resets to 1 and bumps the month, and past 12 the year.
Month lengths come from two 12-dword tables: displacement 0x34728 (Feb = 28)
and 0x34758 (Feb = 29). The leap test is the Gregorian rule (%4, %100, %400),
but the code picks the **28-day table for leap years and the 29-day table for
common years** (confirmed by reading the branch polarity at 0x4D6D6..0x4D712
and the table contents). A reimplementation that only needs relative time can
ignore this; it only affects the displayed date. A UI-dirty flag (0x35918) is
set each call.

**New-game start date**: 26 May 2496 (day 0x1A, month 5, year 0x9C0), set at
0x22756..0x22768 together with the player index 1.

### Game speed

`0x1660E` (0, 1, 2) is cycled by the options handler 0x26D04
(`(x+1) mod 3`) and rendered through a 3-string table at displacement 0x9D20.
The option strings are *Game Speed: Fast / Average / Slow* (text indices
2726-2730), so index 0 = Fast is the likely order (`?`, the string table was not
dumped). The day-length parameter is set at new-game time (0x228A1..0x228C4):

```
D = 8 + 8*speed   if 0x1660F != 0
D = 8 + 4*speed   if 0x1660F == 0
```

so ticks per day = `4*D`: with 0x1660F set (the default init value, toggled
by the "Time On/Off in Menus" option at 0x26CC4, text 2731-2734 `?`) Fast =
32, Average = 64, Slow = 96 ticks per day; with it clear 32 / 48 / 64. The
existing name `g_sfx_voice_enabled` for 0x1660F should be revisited.
Game-speed changes after setup do not obviously update 0xBD00 (it is only
written at 0x228C4); `?`.

Wall-clock rate per tick is not set by the code (no timer wait in the main
loop apart from the 0x74050 millisecond clock used for fixed pauses).

### Corrections to `main-loop.md`

- 0x16624 is the **calendar day**, not `g_cur_race`; 0x16628/0x1662C are month
  and year (the asteroid-destroy "save colony state" copies are a date stamp).
- 0xC6BC counts **days**: the "tick > 700 arms relations/fleet/event" gate
  (0x373, `cmpl $0x2bc`) is **day 700**, and the 0x2DA (730 day) tests at
  0x27B19/0x27B90 are also days. The "(0xC6BC & 3)" tests in other routines
  are 4-day cadences.
- The two readings of "day length" left open there are resolved: day = 4*D
  ticks (32 at default).

## 2. Per-colony data (asteroid node, stride 0x1DC)

Colony state lives in the asteroid node itself (confirmed by the code; note the
savegame diff found no separate "Power/Air/Food/Water" block because they are
fields of this node, mostly at +0x160..+0x18E).

| offset | size | meaning | evidence |
|--------|------|---------|----------|
| +0x5C.. | 10 x u16 | ore **reserve** per ore (index 0..9) | savegame diff; +0x5E = ore 1 is the Powerplant fuel read by 0x2494 |
| +0x94 | s8 | **radiation level** (see 4) | 0x1D94 |
| +0x95 | s8 | extra radiation term (decays in the 200-tick sweep) | 0x1D94, main-loop |
| +0xC0 | u8 | owner (1..8 factions/players, 9..14 wild) | colony loop test |
| +0xC1 | u8 | work-stoppage (strike) counter | 0x27E4, 0x2BA4 |
| +0xC2 | s16 | **population / employees** (the savegame diff's "output %") | all of section 3 |
| +0xC4 | s16 | workforce balance (population minus workplace demand) | 0x27E4 |
| +0xC8 + t | u8 x 40 | **count of buildings of type t** (t = 0..39, Terran text order) | 0x2494, 0x1E44 |
| +0x118 | s16 | **crime / tension** level, clamp 0..310 | 0x3034 |
| +0x11A | s16 | **unrest**, clamp -80..400 | 0x3034 |
| +0x11C | u8 | countdown to the next unrest event | 0x3034 |
| +0x138 | u8 | flags (bit0 gravity nullifier active, bit6 abandon, bit7 ?) | 0x2494, 0x28F4 |
| +0x139 | u8 | flags (bit4 = colony active / CPU placed) | 0x28F4, 0x1CBD |
| +0x13B | u8 | staffed-workplace bits (see 3.5) | 0x27E4 |
| +0x166 | u16 | power **generated** today | 0x2494 |
| +0x168 | u16 | power **demanded** today (buildings in priority order) | 0x2494 |
| +0x16A | u16 | **power stored** (carried to next day) | 0x2494 |
| +0x16C | u16 | **brownout level** L (0 = fully powered, 1..24) | 0x2494 |
| +0x16E | u8 | 30-day throttle for the power-critical message | 0x2494 |
| +0x170 / +0x172 / +0x174 | u16 | water / food / air **supply today** | 0x2224/20E4/1FD4 |
| +0x176 / +0x178 / +0x17A | u16 | water / food / air **demand today** (= population) | same |
| +0x17C / +0x180 / +0x184 | s32 | water / food / air **stored surplus** | same |
| +0x188 / +0x18A / +0x18C | u16 | **CPU base output** of air / food / water (decays) | 0x1CBD init, 0x1784 decay |
| +0x18E | u8 | bud countdown (unrelated) | main-loop |

The PAFW status display (0x3A6B8..) reads exactly these: per resource it
shows 0 = fine, 1 = supply below demand (living off the store), 2 = store
empty.

## 3. The daily colony update (state 2)

`colony_economy_tick` (0x28F4) walks every asteroid with owner 1..8, no
pending-construction delay (+0x11E == 0) and the colony-active bit
(+0x139 & 0x10). If population (+0xC2) is zero the asteroid is flagged for
abandonment (+0x138 |= 0x40). Otherwise, in this order:

1. **Income**: the owner's treasury (0xBD58 + owner*4) gains `population`
   credits (1 Cr per employee per day), then `race_income_tick` (0x2994)
   adds the fixed per-race stipend.
2. `0x1D94` radiation level (section 4).
3. `0x1E44` **population dynamics** (this function is currently named
   `thunk_rng_next` in the rename map; it is a full routine).
4. `0x1FD4` air, `0x20E4` food, `0x2224` water.
5. `0x2494` power recalculation (**runs after** the three life-support
   resources, so the brownout level L used by steps 2-4 is yesterday's).
6. `0x27E4` workforce check.
7. `0x3034` unrest / crime update and events.

### 3.1 Population dynamics (0x1E44)

Housing capacity: `cap = 100*CPU + 50*LivingQuarters + 150*Resiblock`
(counts at +0xDC, +0xC8, +0xE5).

Each day: roll 0..9; result 0..5 -> population +1 (60 %); result 9 -> population
-1 (10 %, only if config byte 0x165FB == 0); 6..8 nothing. Then the structure
threshold list (0x144A4) runs, then radiation losses (section 4), then
`population > cap` -> unrest += overshoot (if > 1) and population := cap.
Population is clamped to >= 0. A new CPU sets population to **50**
(0x1CBD). Below 30 colonists the owner is warned (message type 0x4D).
Expected drift with no losses is about +0.5 colonists/day up to the cap.

### 3.2 Air / food / water (0x1FD4, 0x20E4, 0x2224)

Same shape for each (supply S, demand = population P, store M):

```
S = cpuBase + perBuilding * count     (building term only if brownout L < limit)
net = S + M - P
net < 0 : M = 0 ; loss(net) people die and unrest rises by the same amount
net >= 0: M = min(net, cap)
```

| resource | node fields | producer (type, per building) | powered while L < | cap on store | loss when `net < 0` |
|----------|-------------|-------------------------------|-------------------|--------------|---------------------|
| air | base +0x188, store +0x184 | Air Processor (19): **400** | 24 (0x18) | 3000 per Environment Control + 1000 per CPU | `net` people (all of the shortfall) |
| food | base +0x18A, store +0x180 | Hydroponics Plant (37): **300** | 22 (0x16) | 1000 per EC + 1000 per CPU | `net/10 - 1` people (integer division) |
| water | base +0x18C, store +0x17C | Hydration Plant (38): **400** | 23 (0x17) | 1000 per EC + 1000 per CPU | `net/5 - 1` people |

So **each employee consumes exactly 1 unit/day of air, food and water**
(confirmed: demand field = population). All three resources use the same
unit as "employees supported". The loss line applies only when config byte
0x165FB is 0; the same amount is added to unrest (+0x11A). The store is
therefore a pure buffer measured in colonist-days.

The CPU provides a free base supply that is set when the CPU is placed
(air 300, food 250, water 250; 0x1CBD) and **decays by 1 per day** per
resource down to 0 (routine 0x1784; it is not called directly and is
presumably the CPU building's update callback `?`).

### 3.3 Power (0x2494)

```
gen   = 2*Solar Panel + 8*Solar Generator + 12*Solar Matrix + 12*P.Solar Matrix
        (all doubled if the race's Power-Amplifier flag, byte 0xC56C + race*0x26, > 0)
      + Powerplants: 32 each if the asteroid's Asteros reserve (+0x5E) > 0, else 8 each
      + 8 * CPU
avail = gen + stored(+0x16A)
```

- A Powerplant burns fuel from the asteroid's own Asteros **reserve**
  (+0x5E): every 4th day (`day & 3 == 3`) the reserve drops by the number of
  powerplants, to 0 if smaller. The amplifier does not affect powerplants or
  the CPU (they are added after the doubling).
- Demand is walked through a fixed **priority order** (table @ 0x9387, 40
  type ids; first = highest priority): CPU, Powerplant, Living Quarters,
  Resiblock, Power Store, Storage Facility, Solar Panel, Solar Generator,
  Solar Matrix, P.Solar Matrix, Storage Tower, Environment Control, Pleasure
  Dome, Landing Pad, Refuelling Depot, Missile Silo, **Air Processor,
  Hydration, Hydroponics**, Command Centre, Screen Generator, Radiation
  Filter, Repair Facility, P.Storage Tower, Medical Centre, Photon, Plasma,
  Laser, Sensor Array, Ship Yard, Weapons Factory, Mine, Deep Bore, Security
  Centre, Seismic Penetrator, Anti-Missile Pod, Satellite Silo, Gravity
  Nullifier, Ore Teleporter, Asteroid Engine (last = shed first).
- Each type's draw is `count * draw[t]` with `draw[t]` a signed byte at
  displacement `0x36278 + 0x14*t` (see the table in section 6). Special
  cases: Gravity Nullifier draws 4 only while the colony's nullifier flag
  (+0x138 bit0) is on (otherwise the loop appears to re-use the previous
  type's value, `?` probable decompiler/asm quirk); Asteroid Engine draws
  the signed engine setting at node +0x41 per engine.
- The **brownout level** L: the first priority position `p` at which
  cumulative demand exceeds `avail` gives `L = 40 - p`, capped at 24; 0 when
  everything is supplied. Higher L = more buildings cut. Buildings test L
  against a threshold (Air Processor works while L < 24, Hydroponics L < 22,
  Hydration L < 23, Radiation Filter L < 19, Medical Centre L < 16; others
  presumably the same scheme `?`). Priority positions 0..15 are never cut by
  this scheme.
- Stored power: if L == 0, `stored = min(avail - demand, cap)` with
  `cap = 200*PowerStore (400 with the "hi-energy power stores" flag byte
  0xC563 + race*0x26) + 50*CPU`; otherwise stored = 0.
- If L >= 16 (the Air Processor or anything cheaper-priority is cut) and the
  owner is the player, a "power critical" message is posted; a 30-day
  throttle counter (+0x16E) prevents repeats.
- If config byte 0x165FC is nonzero L is forced to 0 (unlimited power; a
  scenario/tutorial option `?`).

Power therefore degrades gracefully: low-priority weapons/engines go dark
first, then radiation protection and medical care, and only then the
air/food/water plants - which stop contributing, after which the section 3.2
shortages start killing people.

### 3.4 Order of failure (summary)

1. Power short: Asteroid Engine, Ore Teleporter, Gravity Nullifier, ...
   turrets, Security Centre, Medical Centre (L >= 16 loses it), Radiation
   Filter (L >= 19), Screen Generator/Command Centre (L >= 20-21).
2. Power very short: Hydroponics (L >= 22), Hydration (>= 23), Air Processor
   (>= 24) stop. Their contribution vanishes; the stored surplus buffers the
   loss until empty.
3. Store empty: air deaths = full shortfall per day, water = shortfall/5 + 1,
   food = shortfall/10 + 1; unrest rises one-for-one; with no population the
   asteroid is abandoned.

### 3.5 Workforce and unrest (0x27E4, 0x3034)

Workforce check: starting from population, subtract 8 per workplace in this
order: Mine; Seismic Penetrator + Deep Bore Mine; Ship Yard; Missile Silo;
Command Centre. The first stage where the running balance goes negative
clears that stage's bit (and all later bits) in +0x13B (bit0 Mine, bit1 Deep
Bore/Seismic, bit2 Ship Yard, bit3 Missile Silo, bit4 Command Centre) - an
understaffed workplace stops. The final balance goes into +0xC4. Then:

- balance in (-21, 21): unrest -1;
- balance > 59: unrest += balance / 60 (idle population breeds unrest);
- an active strike counter (+0xC1 != 0): all bits cleared, counter -1.

Unrest / crime (0x3034, daily):

```
unrest   = clamp(unrest - 2*PleasureDome, -80, 400)
if unrest < 31:  crime -= 2
crime   += (unrest*pop*100/56000 + 100)/100 - SecurityCentre   (about +1 + unrest*pop/56000)
crime    = clamp(crime, 0, 310)
```

(Pleasure Dome = type 36, Security Centre = type 39.) A single Security
Centre cancels the baseline +1/day; unrest feeds crime only through the small
`unrest*pop/56000` term.

At crime >= 40 a countdown (+0x11C, random 30-59 days) runs and, when it
expires, one random event is drawn by crime tier: <=100 (4 choices), <=200 (6),
<=300 (7), >300 (7). The handlers (names are hypotheses `?`):

| handler | role | magnitudes by tier |
|---------|------|--------------------|
| 0x2BA4 | **strike**: sets the work-stoppage counter +0xC1 to x/2 + rand(x/2) days | x = 20 / 80 / 120 / 140 |
| 0x2AF4 | **riot deaths**: lose about (x +/-5)% of the population | x = 10 / 20 / 35 / 40 |
| 0x2A84 | **theft**: owner loses x/2 + rand(x) credits (and a message) | x = 8000 / 20000 / 40000 / 80000 |
| 0x2F04 / 0x2DA4 / 0x2E44 / 0x2CE4 | building sabotage (destroys / disables buildings; 0x2CE4 picks from a per-race type table) | parameter 0..7, 1..11, 26 |

Only the first dispatch layers are decoded; the building types they hit are
not identified.

## 4. Radiation and disease

- **Radiation level** (+0x94, 0x1D94), computed each day before the
  population step:
  `R = (+0x95) + Nexos-slot reserve (+0x6E) + Asteros reserve (+0x5E)/128 + Traxium-slot reserve (+0x6C)/2`
  (ores 8 and 9 are the two high-grade ores; ore 1 is Asteros). If L < 19
  (Radiation Filter powered): `R -= 3 * RadiationFilter` (floor 0). If L < 16
  (Medical Centre powered) the population step subtracts a further
  `3 * MedicalCentre` from R (floor 0).
- **Daily sickness** (0x1E44): if `R > 10` one employee is lost every day
  (unrest +1). Otherwise a loss happens with probability from table @ 0x937C
  indexed by R: `R = 0..10 -> 0, 10, 11, 13, 14, 17, 20, 25, 33, 50, 100 %`.
  A loss reduces population by 1 and raises unrest by 1 (skipped if config
  byte 0x165FB != 0).
- The text catalogue's "outbreak" / "Colony Sickness Warning" stages
  (reduced efficiency ... total incapacitation) are *not* located in code
  yet; they probably key off R or an outbreak flag (`?`). The only confirmed
  disease effect is the population loss above.

## 5. Random surplus-loss events

Four event routines destroy a colony's whole stored surplus and post the
"Surplus Air/Water/Power/Food loss" messages (amount lost in the text):
0x36B4 air (+0x184), 0x3714 water (+0x17C), 0x3774 power (+0x16A), 0x37D4
food (+0x180). They are reached through the event scheduler's indirect calls
(`event_scheduler`, 0xF404); the trigger probability is not yet extracted
(`?`). The helper 0x13344 selects the affected colony of the race. Stores
therefore carry real risk: a large Environment Control reserve can vanish.

## 6. Design-ready summary (daily values, GOG build)

Type numbers are the order of the Terran building names in the text resource
(verified for 9 = Satellite Silo and 33 = Protected Storage Tower, and by
every code constant above). "Draw" is MW from the static record table;
population is the colony's employee count.

| type | building | produces / houses | stores | draw (MW) |
|------|----------|-------------------|--------|-----------|
| 0 | Living Quarters | houses 50 | | 0 |
| 1 | Power Store | | 200 MW (400 with hi-energy stores) | 0 |
| 2 | Storage Facility | | ore | 1 |
| 4 | Solar Panel | 2 MW (4 with amplifier) | | 0 |
| 5 | Radiation Filter | radiation -3 | | 3 |
| 6 | Solar Generator | 8 MW (16) | | 0 |
| 8 | Mine | needs 8 workers | | 1 |
| 13 | Deep Bore Mine | needs 8 workers | | 2 |
| 14 | Missile Silo | needs 8 workers | | 0 |
| 19 | Air Processor | air for 400 | | 2 |
| 20 | C.P.U. | houses 100, +8 MW, +50 MW store; free air 300 / food 250 / water 250, each -1/day; stores 1000 of each | | 0 |
| 21 | Seismic Penetrator | needs 8 workers | | 3 |
| 22 | Asteroid Engine | | | 5 (engine-setting based) |
| 23 | Powerplant | 32 MW with Asteros reserve (burns 1 per 4 days), else 8 MW | | 0 |
| 24 | Command Centre | needs 8 workers | | 3 |
| 25 | Ship Yard | needs 8 workers | | 2 |
| 28 | Solar Matrix | 12 MW (24) | | 0 |
| 29 | Resiblock | houses 150 | | 0 |
| 31 | P. Solar Matrix | 12 MW (24) | | 0 |
| 34 | Medical Centre | radiation -3 | | 1 |
| 35 | Environment Control | | air 3000, food 1000, water 1000 | 0 |
| 36 | Pleasure Dome | unrest -2/day | | 1 |
| 37 | Hydroponics Plant | food for 300 | | 2 |
| 38 | Hydration Plant | water for 400 | | 1 |
| 39 | Security Centre | crime -1/day | | 2 |

Remaining draws (MW) from the same table: Anti-Missile Pod 3, Weapons
Factory 2, Satellite Silo 1, Screen Generator 7, Ore Teleporter 1, Gravity
Nullifier 4 (while active), Repair Facility 1, Sensor Array 2, Plasma Turret
3, Photon Turret 4, Laser Turret 2, Storage Tower 2, P. Storage Tower 3,
Landing Pad / Refuelling Depot 0.

Daily rules in one place: employees pay 1 Cr/day each; each consumes 1
unit of air, food, water; population grows +1 with 60 % chance, -1 with 10 %
chance, capped by housing; shortages kill (air 1:1, water 1:5, food 1:10,
each +1); radiation kills with the table in section 4; unrest/crime as in
3.5; power is a priority-ordered brownout.

## 7. Text and manual claims vs the code

Text/manual statements (from `ENGLISH.TXT` / the manual; not evidence):

| claim | status vs code |
|-------|----------------|
| Living Quarters 50 people, Resiblock 150 | **confirmed** (0x1E44) |
| Air Processor 400, Hydroponics 300, Hydration 400 employees | **confirmed** (0x1FD4/20E4/2224) |
| Power Store 200 MW | **confirmed** (400 with the hi-energy stores flag) |
| Solar Panel 2 MW (4 amplified), Solar Generator 8 (16) | **confirmed** |
| Powerplant 32 MW from Asteros, 8 MW fallback, 1 Asteros / 4 days | **confirmed** (reserve-based) |
| Solar Matrix "12/24 MW" tooltip vs "max 8 MW" long text | code = **12** (24 amplified); the long text is wrong for this build |
| Environment Control stores 5000 air / 600 food / 600 water | **contradicted**: code gives 3000 / 1000 / 1000 (plus 1000 each per CPU) in the GOG build; the text may describe an earlier build |
| CPU output drops 1/day to zero | **confirmed in data** (init 300/250/250 and a decay routine); callback link unproven |
| each employee consumes 1 unit/day of Power, Air, Food, Water | air/food/water **confirmed**; power is *not* per employee, it is per building (table draws) |
| Medical Centre "up to 100 employees", Security Centre "150 employees", Pleasure Dome "300" | **not found**: the code uses Medical Centre as -3 radiation, Pleasure Dome -2 unrest/day, Security Centre -1 crime/day per building, with no employee caps |
| disease outbreaks with stages | only the radiation/sickness loss found; stages unresolved |

## Open questions

- Which of the three game-speed values maps to which index, and whether the
  speed option rewrites 0xBD00 mid-game (only the new-game write is known).
- Meaning of config bytes 0x165FB (no population loss) and 0x165FC (no
  brownout); they are probably scenario/difficulty/tutorial switches.
- The CPU decay routine 0x1784: confirm it is the CPU structure's update
  callback and that it runs once per day (state 3).
- The structure/threshold list at node +0x38 (0x144A4): it compares an item's
  population threshold (+0xA) with the current population, posts messages and
  sets unrest/crime from the item (+0x14/+0x16); likely the scenario event
  script, not yet decoded.
- The other-race variants of the population routine (0x16664, 0x16754, ...
  use different housing weights: 50 and 200 per slot 0xC8/0xCB). They are
  not called directly; find out whether they are per-race callbacks.
- Event triggers for surplus-loss events and the unrest event targets
  (0x2F04, 0x2DA4, 0x2E44, 0x2CE4).
- Exact "Colony Sickness" stages and Medical Centre treatment of outbreaks.
- What +0x95 holds (it feeds radiation and is decremented in the 200-tick
  sweep) and what writes it (nuclear weapons, explosions?).
- The unpowered type-12 (Gravity Nullifier) case in 0x2494 leaves the
  running draw register stale; check whether the original game really adds a
  neighbour's draw there.

## References

- GOG flat code: 0x4D5D4 (state driver), 0x4D6C4 (calendar), 0x4E204..0x4E47D
  (outer loop), 0x228A1 (day-length setup), 0x26D04 (speed option),
  0x28F4 (colony loop), 0x1D94, 0x1E44, 0x1FD4, 0x20E4, 0x2224, 0x2494,
  0x27E4, 0x3034, 0x1CBD, 0x1784, 0x3A6B8 (PAFW status).
- Data: priority table @ displacement 0x9387, death table @ 0x937C, draw
  table @ 0x36278 (stride 0x14), month tables @ 0x34728 / 0x34758.
- `docs/mechanics/main-loop.md`, `building-stat-table.md`,
  `docs/dataformats/savegame-format.md`; savegame diff notes (day counter at
  save 0xA04, tick counter 0xA978).
