# Economy and personnel: money, the four funds, supervisors, agents

Status: probing. The money pools, the fund cascade, the supervisor
(personnel) model and the agent price/duration model are read from the GOG
build's code and data tables (confirmed statically, section 1-6). Hiring
fees, the ore sale price, the loyalty model of agents and the endgame
scoring are not resolved (`?`, section 8). Game-text and manual claims are
kept in section 7 and are never used as evidence for a formula.
Source: `build/flat/gog_disasm.txt` and `build/named/FRAGILE.EXE.gog.flat/
decompiled.c` (GOG retail build, image-relative addresses, same convention
as `main-loop.md`); data tables read at "DS displacement + 0x86004" (see
`life-support.md`, "Addressing note"); savegame findings of the parallel
diff agent (credits, day counter); text from the build's `_TEXT` resources
(string index `i` has its pointer slot at `0x37974 + 4*i`; the loader at
0x25BD4 fills the array 0x37970..0x39FCC with the NUL-separated strings in
order, and the message posters take (title, body) from consecutive slots).

Cross-references (not repeated here): daily colony update, population and
the 1 Cr/day/employee income term: `life-support.md`. Blueprint prices and
ordering via the Federal Transporter: `scitek-blueprints.md`. Fines for
pacts and treaties: `diplomacy.md`. Ship/missile hardware prices:
`weapon-and-turret-numbers.md`, `building-stat-table.md`.

## 0. Corrections to existing notes (AGENTS rule 7)

These were found while reading the code below; the owning notes/rename-map
entries should be fixed in the same change that adopts this note.

- `main-loop.md` calls the 16-node pool at 0xBD10 and its tick 0x8544
  (`race_relations_tick`) a "relations" tick with thresholds in 0x967C.
  It is the **Colony Supervisor pool** and its daily payroll/stress tick
  (section 4). `colony_growth_tick` (0x8354) is the supervisor workload
  tick, not a colony growth routine.
- The 16-node pool at 0xBD14 (stride 0x40) and the "colony_*" functions
  0xBCE4..0xCF74 are the **Agent pool** (section 5), not colonies.
  `building_cost_calc` (0xC6C4) is the agent *mission price* function.
- `diplomacy.md` runtime-verification quotes the table at 0x967C as
  "400/0/1000/0/3000..." (a different base); the GOG flat holds the
  supervisor table at flat 0x8F680 (= displacement 0x967C), see 4.1.
- `g_race_production` (0xBDE8) is the **Missiles** fund and
  `g_race_reserves` (0xBDC4) is the **Personnel** fund (section 2).
- `g_cur_race` / `g_colony_pos_x/y` (0x16624/28/2C) are the calendar
  day/month/year (`life-support.md`); the supervisor pay-day compares
  against the calendar day.
- The rename-map has `0x9A1B` as the alien price-modifier table base; the
  rows begin at 0x9A24 (agent*6 + race 9..14 + 0x9A12), see 5.2.

## 1. Money pools (confirmed)

Five 32-bit pools per race, indexed by race id (stride 4; races 1..8 are the
"empire" slots including the human player; 9..14 aliens use a separate
treasury path, 0x16184/0x161E4):

| address | pool | evidence |
|---------|------|----------|
| 0xBD58 | **Money** (`g_race_treasury`, the "Credits" shown to the player) | 0x4314, 0x4C644, 0x28F4 |
| 0xBD7C | **Construction** fund | building placement cost taken from it (0x1A23D, 0x88A4); claim top-up 0x2308A |
| 0xBDA0 | **Vehicles** fund | ship-yard affordability test (`ui_calc_action_mask` 0x3D4C4 compares it with the item price at +0x50) |
| 0xBDE8 | **Missiles** fund (`g_race_production`) | per-tick production cost drained by 0xA04 |
| 0xBDC4 | **Personnel** fund (`g_race_reserves`) | supervisor payroll, guard cost, agent mission fees (sections 4, 5) |
| 0xBE0C | **Debt** (UI "Debt To Federation"; stored as a positive amount owed) | 0x4314 (adds), 0x3EA1 (repays) |

The fund selector used by `race_transfer_money` (0x4C644, selector in EBX)
is 1=Construction, 2=Vehicles, 3=Missiles, 4=Personnel, anything else =
Money; this is the same order as the UI labels. A transfer moves
`amount` out of Money into the chosen pool (clamped to the available Money;
a negative amount moves it back, clamped so the pool cannot go below 0).
The slider UI (`ui_update_resource_value` 0x399F4, five bars summed by
`ui_update_resource_graph` 0x39804) is a single bar of total width
Money+4 funds: dragging a boundary calls this transfer with the new
rounded value of the dragged pool, limited to (pool + Money). So the "four
budgets" are simply four sub-accounts; **income always lands in Money** and
only moves into a fund by player action (or the automatic claim top-up
below).

### 1.1 Start values (confirmed code; ? for which index the retail build uses)

New-game setup (0x22A58..0x22ADC): for races 1..8

- Money = `start_money[atmosphere]` where the table at displacement
  0x16880 (flat 0x9C884) is `{1,000,000, 1,000,000, 1,000,000}` indexed
  by the byte at 0x16612, which is the **atmosphere** index (0 Peaceful, 1
  Neutral, 2 Aggressive; `alien-ai-trade-victory.md` 3.1 -- it is not a
  "difficulty"; Corrected 2026-10-18; the word before the table is 0, which the
  earlier text counted as entry 0), so every setting starts with 1,000,000 Cr;
  all four funds and the debt start at 0.
  (A special-mode flag at 0x165FD instead sets *all five* pools of every
  race to 1,000,000.) Savegames start the human at 1,000,000 (plus a few
  hundred by day 0), matching index != 0; the seven words after the pool
  in the save are those other pools/the 1,000,000 filler.
- A new colony **claim** moves up to 8,000 Cr (`g_asteroid_claim_value`,
  displacement 0xA04A, value 8000) from Money into Construction so that the
  starting building (the CPU) can be placed; if Money cannot cover the
  shortfall the "no funds" message is posted instead (0x22F14).
- A debt of 10,000 is written by one command handler (0x5835D, in the
  0x58xxx runtime block); which action triggers it is not identified (?).

## 2. Income (confirmed)

Per game day (main state 2, `colony_economy_tick` 0x28F4 then
`race_income_tick` 0x2994):

1. for each own colony (owner 1..8, not in the "disabled" state): Money
   += population (+0xC2) of that colony (1 Cr per employee per day,
   `life-support.md`). A colony with population 0 is flagged for removal
   (+0x4E |= 0x40).
2. for each active race 1..8: Money += `income_table[atmosphere]`
   with `income_table` at displacement 0x93B0 = `{100, 250, 400}` (flat
   0x8F3B4), indexed by the atmosphere byte 0x16612 (Peaceful 100 /
   Neutral 250 / Aggressive 400 Cr per day per player race; confirmed by
   `alien-ai-trade-victory.md` 3.3, Corrected 2026-10-18: the earlier
   "g_difficulty" index was this atmosphere byte). The save diff suggests a
   larger constant (about 1018 per day) -- the 250 Cr stipend plus 1 Cr per
   employee per day does not by itself reproduce it (?, open question 1).

**Ore sales** are lump sums on the Federal Transporter cycle (4.4): ore
loaded since the transporter arrived is valued and credited when it
departs, first paying down the Debt, the surplus going to Money. This is
why the daily income of a save is nearly flat and "not proportional to ore
mined".

## 3. Payments, fines and the shortfall cascade (confirmed)

`race_credit_transfer` (0x4314; `diplomacy.md` calls it
`race_funds_transfer`): pay `amount` from race P to race Q.

- P an empire race (not 9..14): take as much as possible from, in order,
  **Money, Construction, Vehicles, Missiles, Personnel**; the amount
  actually collected is the return value. If Q != 0 and the five pools were
  not enough, the shortfall is *added to P's Debt* (0xBE0C). If Q == 0 the
  shortfall is not recorded here (?).
- Q (1..8) is credited the **full** `amount` into Money regardless of what P
  could pay; Q an alien race goes to the alien treasury path.
- P an alien: separate routine (0x16184).

The Debt is repaid by ore sales (4.4): the sale value reduces it; if it goes
negative the excess is paid into Money and Debt resets to 0. No daily
interest was found.

## 4. Colony Supervisors (confirmed from code unless marked)

### 4.1 Static table (16 supervisors)

Table at displacement 0x967C = flat 0x8F680, 16 rows of 28 bytes (the
first 16 of the "stat records" listed in `gog-build-data.md`, whose "id"
column is the portrait id in the next row's first 4 bytes). Row `i` goes
with the i-th name in the name table (pointer slot 0x39040) and the i-th
CV text pair. Fields:

| off | meaning |
|-----|---------|
| +0 u16 | **monthly salary** in Cr |
| +2 u8 | number of consecutive unpaid pay-days before the player gets the "wants salary" warning (99 = never) |
| +3 u8 | (unused by the tick; `thresh1`) |
| +4 u32 | T2: workload level above which the performance meter drops |
| +8 u32 | T3: workload level above which stress rises |
| +12 u32 | T4: workload level above which the "disgruntled" state can start |
| +16 u32 | T5: workload level above which the supervisor can die |
| +20 u8 | performance-meter cap (also its start value) |
| +21 u8 | **recovery penalty** `pen`: workload falls by 20*pen per day |
| +22 u8 | unidentified (2..6; `g_colony_ai_factor`, read at 0x9D77, ?) |
| +23 u8 | gender (0 male / 1 female; selects the "his/her back pay" text) |
| +24 u32 | portrait/CV id (first row 31, ...; of the form 30..39, 55) |

Values (salary / warn-after / T2 / T3 / T4 / T5 / meter cap / pen / stress
factor, the factor from the table at 0x983E, stride 4):

| row | salary | warn | T2 | T3 | T4 | T5 | cap | pen | stress factor |
|----:|-------:|-----:|---:|---:|---:|---:|----:|----:|--------------:|
| 0 | 25000 | 3 | 2000 | 2000 | 8000 | 400000 | 100 | 10 | 4 |
| 1 | 15000 | 2 | 2000 | 200000 | 8000 | 400000 | 95 | 7 | 0 |
| 2 | 10000 | 1 | 1000 | 2000 | 12000 | 8000 | 80 | 5 | 4 |
| 3 | 25000 | 2 | 2000 | 4000 | 12000 | 400000 | 100 | 9 | 4 |
| 4 | 15000 | 1 | 0 | 200000 | 4000 | 4000 | 100 | 7 | 0 |
| 5 | 20000 | 3 | 2000 | 200000 | 8000 | 400000 | 100 | 8 | 4 |
| 6 | 20000 | 4 | 1000 | 4000 | 8000 | 12000 | 100 | 8 | 4 |
| 7 | 30000 | 99 | 3000 | 200000 | 12000 | 400000 | 100 | 10 | 4 |
| 8 | 10000 | 2 | 1000 | 4000 | 400000 | 8000 | 70 | 5 | 2 |
| 9 | 30000 | 1 | 4000 | 4000 | 12000 | 400000 | 100 | 10 | 0 |
| 10 | 20000 | 1 | 2000 | 2000 | 400000 | 8000 | 88 | 8 | 4 |
| 11 | 20000 | 1 | 100000 | 4000 | 12000 | 8000 | 98 | 8 | 3 |
| 12 | 15000 | 6 | 3000 | 0 | 400000 | 12000 | 95 | 7 | 4 |
| 13 | 25000 | 1 | 2000 | 200000 | 400000 | 8000 | 100 | 9 | 0 |
| 14 | 15000 | 99 | 0 | 4000 | 400000 | 8000 | 90 | 7 | 0 |
| 15 | 10000 | 4 | 2000 | 200000 | 8000 | 400000 | 88 | 5 | 0? |

(Row 15's factor word reads 0 with a stray 0x100 in its neighbour word;
treated as 0, ?.) A value of 200000/400000 is effectively "never reached" and the
CV prose agrees (stable / high-tolerance supervisors have huge T3, small
salaries come with tiny T5, i.e. they die or crack under overload).

The 10 task flags (maintenance options: mining, power, radiation, security,
life support, ... in the CV panel) carry weights
`task_weight = {2,2,2,3,3,1,1,1,2,3}` (table at displacement 0x9670); the
assignment mask at node +0x14 starts as 0xFFFF (all on) when a supervisor
arrives (`supervisor_arrive`, 0x7D14).

### 4.2 Node (16 nodes, pool 0xBD10, stride 0x28, one per supervisor row)

| off | meaning |
|-----|---------|
| +8 | row index (0..15) |
| +9 | employer race (0 if free) |
| +0xC | back-pay owed (int) |
| +0x10 | pay-day: the calendar day-of-month on which the salary is due (hire/arrival day - 1, 28 if that is 0, capped 28) |
| +0x11 | consecutive missed pay-days |
| +0x12 u16 | state flags: 0x01 waiting to become available, 0x02 on the way (hired, awaiting the Transporter), 0x04 working, 0x08 sacked, 0x10 under guard, 0x20 dead/gone, 0x40 disgruntled, 0x80 guard paid today; 0x100/0x200 are used by the hire/arrival code |
| +0x14 u16 | enabled task mask |
| +0x16 | **number of asteroids assigned** (adjusted by `supervisor_assign_asteroid` 0x7714; asteroid byte +0x13D holds its supervisor row, -1 none) |
| +0x17 | workload % shown on the CV, = workload*100/12000, capped 100 |
| +0x18 int | **workload accumulator** W |
| +0x1C | performance meter (0..cap) |
| +0x1E s16 | **stress** (0..1000) |
| +0x21 / +0x22 | notice flags / 60-day nag countdown |
| +0x24 int | days until available / appearance countdown |

### 4.3 Daily rules (state 8 = once per game day)

`supervisor_daily_tick` (0x8544, per node, skipping dead and on-the-way):

- If not yet "available" (flag 1 clear): countdown +0x24 (via 0xB394) --
  when it was armed by the pool reset it is `3 * (150 + rng(150))` days
  (0x8234: 450..897 days). If flag 1 is set the countdown runs and when it
  reaches 0 the "new supervisor available" message is posted.
- Working supervisor with no asteroid assigned: every 60 days a "would like
  some asteroids to manage" request (player only).
- **Pay-day**: when `+0x10 == calendar day` the owner's Personnel fund is
  charged `salary + back_pay`.
  - If the fund covers it: fund -= (salary + back_pay), back-pay = 0,
    missed = 0.
  - Otherwise: back-pay += salary - fund (the whole fund is taken, fund = 0),
    missed += 1 and **stress += 5 * stress_factor**
    (`+0x1E += table[0x983E+4*row] * 5`). If the owner is the player and missed >= the row's warn-after value, a
    warning is posted: tier by back-pay: < 1 salary "would like paying in
    full next month"; < 3 salaries "wants back pay of N"; else "demands
    full payment".
- **Guard** (flag 0x10): each day 1,000 Cr is taken from Personnel; if less
  than 1,000 is available the guard lapses (flag 0x80 cleared, "security
  under-funded" posted once).
- `supervisor_workload_tick` (0x8354, working supervisors only), daily:
  1. `S = sum(task_weight[k] for each enabled task k)`
  2. `W += n * S - 20 * pen` (n = asteroids assigned), floor 0
  3. workload% = min(100, W * 100 / 12000)
  4. meter: if W > T2 the meter decrements (floor 0) else it increments up
     to the cap
  5. if W > T5: 4% chance (rng(100) < 4) the supervisor **dies**
     (`supervisor_die` 0x8194: state 0x20, all his asteroids are
     unassigned, message with one of three causes: heart attack / suicide
     from over-work / unknown, chosen by rng(3))
  6. else if W > T4 and not already flagged: 4% chance the state 0x40
     (disgruntled) is set and stress += 80 * factor
  7. if W > T3: stress += 2 per day (cap 1000), else stress -= 1 (floor 0)
- State 0x40 is consumed by 0x7BD4 (the "grumbling" outcome): clears the
  flag, stress += 140*factor twice and sets "under guard" handling.
  Sacking (0x7BD4 branch for state 8) moves the supervisor to "under guard"
  and adds stress 140*factor; the walk-out ("quit due to stress", "quit
  due to lack of pay") messages and the "blow up the colony" sabotage are
  produced by gap code reached through the same flags; the **stress
  threshold that triggers the walk-out is not recovered (?)**. Stress 1000
  is the cap written at arrival-by-transporter for a returning supervisor.
- Hiring/arrival (`supervisor_hire` 0x79C4, `supervisor_arrive` 0x7D14):
  hiring sets state "on the way" (flags 0x03), clears back-pay, stress and
  meter (= cap), employer = hirer; the supervisor starts working when the
  Federal Transporter arrives (4.4). **No hiring fee or immediate payment was
  found** -- the first salary is due on the pay-day (consistent with the
  save diff: hiring an agent did not change Credits).

### 4.4 Federal Transporter cycle (race timer 0xBF34, save offset 0x280)

`race_construction_tick` (0x3B94) runs once per game day for each race
1..8 and decrements a countdown (0xBF34 + 4*race; the save's field that
"starts at 150 and can go negative"). It is the **Federal Transporter
cycle**, not a review/quota timer:

| countdown value | event |
|-----------------|-------|
| 30 | message "Federal Transporter in transit / will arrive at <asteroid> in N days" (type 0x13) for the player |
| 10..9 | the same message (type 9) |
| 0 | **arrival**: the target asteroid (richest, `obj_find_richest`) is marked, the per-race delivery counters at 0xC09C are cleared, hired supervisors/agents change from "on the way" to working/available, ordered blueprints (8854) and queued buildings/ships (queue 0xBF58, 9 types) are delivered |
| -40 | "will depart in 10 days" notice for the player |
| -50 | **departure**: ore shipped since arrival is valued (`sum_k ore[k] * unit_value[k]`, `unit_value` at 0xE808+4k) and credited -- first against the Debt, any surplus into Money; the countdown restarts at `100 + rng(100)` (normal mode) or `50 + rng(50)` (mode flag 0x16618 != 0) |

So the transporter visits roughly every 100..199 days and stays 50. The
value per ore unit (`0xE808+4k`) is the monthly TRADE price of the ten ores
(Corrected 2026-10-18; `alien-ai-trade-victory.md` 8.3): `trade_monthly_update`
(0x47574, every 30 days) sets each ore price to its static reference price x
three sine waves (periods about 60/20/12 months, amplitudes 1 : 0.33 : 0.2, halved
for ores) x (1 + noise up to 9 %), and copies the ten ore prices into the
0xE808 table, so ore revenue at departure uses the price of the current
month. Hiring, ordering and ore sale all happen at these visits.

## 5. Agents (confirmed from code unless marked)

### 5.1 Pool and states

16 agents, pool 0xBD14, stride 0x40, one per CV (name table slot 0x39100,
3 texts each: motto and two bios). State byte +0xA: 0x01 available for
hire, 0x02 hired/on the way, 0x04 on a mission, 0x08 or 0x80 inactive, 0x10
travelling to the target. Key fields: +8 agent row, +9 employer, +0xD
chosen mission (0..12, -1 none), +0xE..+0x1A (13 bytes) the selected-orders
slots, +0x2C cover counter (s16), +0x2E (counts of missions done?), +0x30
exposure/score accumulator, +0x34 target asteroid pointer, +0x38 days
remaining.

### 5.2 Mission table and price (confirmed)

Table at displacement 0x9978, 13 rows of 12 bytes (flat 0x8F...; `+0` base
duration in days, `+1` unidentified byte, `+2` s16 info/impact points,
`+4` s16 exposure/risk points, `+8` s32 **base price in Cr**, function
pointer at displacement 0x9BB8+12*m):

| m | mission (order of the game's verb list) | days | price | impact | risk | `+1` |
|--:|-----------------------------------------|-----:|------:|------:|-----:|-----:|
| 0 | destroy the Ship Yard / SpaceDock | 25 | 150,000 | 140 | 50 | 50 |
| 1 | satellite data-transfer frequencies | 12 | 60,000 | 30 | 20 | 80 |
| 2 | collect treaty information | 12 | 50,000 | 100 | 40 | 65 |
| 3 | collect asteroid location data | 12 | 75,000 | 40 | 30 | 80 |
| 4 | set off the Anti Population Virus | 25 | 350,000 | 200 | 100 | 40 |
| 5 | destroy population centres and life support | 25 | 500,000 | 80 | 90 | 50 |
| 6 | destroy mining and ore storage | 20 | 130,000 | 50 | 50 | 55 |
| 7 | destroy power generation | 18 | 110,000 | 20 | 40 | 55 |
| 8 | destroy anti-missile defences and surface protection | 18 | 190,000 | 40 | 60 | 55 |
| 9 | destroy ship attack turrets | 20 | 200,000 | 50 | 50 | 55 |
| 10 | destroy ship and missile construction | 17 | 90,000 | 50 | 60 | 55 |
| 11 | destroy missiles in storage | 25 | 130,000 | 80 | 60 | 40 |
| 12 | destroy the Transporter | 20 | 145,000 | 140 | 50 | 55 |

The verb order is that of the pointer table at displacement 0x37E4C
(thirteen texts); the m <-> mission pairing follows that order and the
effect functions, but rows 6, 9, 10, 11 are paired by order only (?).
Price paid per mission:

```
price = base[m] + base[m] * mod / 100          (integer division)
mod   = price_mod_empire[agent]               if target owner is 1..8
        price_mod_alien[agent][race 9..14]    if target owner is an alien race
```

`price_mod_empire` (displacement 0x9A14, 16 signed bytes, flat 0x9A18...):
`-20,0,25,0,0,0,50,10,0,0,-30,10,0,0,0,-10`. `price_mod_alien` (0x9A24,
6 bytes per agent, columns = races 9..14, signed percent) rows 0..15:
`[10,0,0,-30,10,0] [0,0,-10,0,20,50] [-10,0,0,0,-10,-20] [40,-40,80,10,35,15]
[45,50,10,20,40,50] [-30,0,0,0,0,0] [0,-40,0,0,0,0] [20,-20,-10,-10,-20,-30]
[-40,-50,-60,-10,10,-10] [10,50,-10,0,10,0] [20,10,0,-10,0,-50]
[0,0,10,0,0,0] [0,0,20,10,10,10] [60,10,10,0,-40,0] [0,0,0,80,0,0]
[0,0,0,0,0,0]` (the CV prose "pro-Terran bias", "friendship with the
Artemia", ... refers to these columns).

A mission order is a *set* of up to 13 slots; `agent_orders_cost` (0xC7B4)
sums the price of newly selected slots minus the refund of deselected ones;
`agent_orders_apply` (0xC874) subtracts the net change from the owner's
**Personnel fund** (floor 0) and stores the orders. A destroyed or lost
target before arrival refunds the paid fee (messages); the game text
"Fee / Mission Fees / Risk Factor Fees / Total Fee" are this price split
(the base and the species modifier).

### 5.3 Per-agent table (displacement 0x9898, 16 rows of 14 bytes)

`b0` signed duration modifier in percent applied once: duration = base days
- b0 * base days / 100 (a negative b0 lengthens the job; rows use
60,25,80,-10,35,60,20,25,45,25,-20,80,50,10,-30,10 as signed); `b1,b2,b3`
unidentified; `+4` s16 starting value of the cover/score counter (-60,
-40, -75, -10, ...); `+6` s16 **cover threshold** (600,200,800,300,700,...)
used by the capture check; `+8..+10` bytes (75/95/80...) and `+11` flag;
`+12` age/field (21..31). Capture check (`agent_cover_check` 0xBCE4,
before every daily step of an agent on a target owned by someone else):

```
need = threshold[agent] - target_mod[agent][owner]     (second modifier table
        0x9A84 for empire owners, 0x9A94 + 6*agent for aliens)
if cover < need:   the agent is at risk; each day rng decides
else:              safe this day
```

If the check fails the agent is removed ("fled / contact lost"), the
mission lapses and (for the player) the contact-lost message is posted;
the exact success probability per day is in the unrecovered rng branch
(`rng_next` calls that Ghidra marked non-returning, ?). Daily the cover
counter rises by the target asteroid's +0xEF value (spy satellite
count, ?) and by the mission impact points on completion
(`g_colony_pct_val` = 100, or 60 when the agent is flagged in +0x98, plus
10 per satellite).

Mission completion: when the countdown reaches 0 the function at
0x9BB8+12*m is called; success adds `pct * impact / 100` to +0x2C and the
risk points to +0x30, and the outcome message (mission complete / successful
/ unable) is posted. "Double agent" and the freelance-enemy-agent reports
are other users of the same node pool.

## 6. Other money flows seen in code

- **Buildings**: cost from the 40-row table (`building-stat-table.md`) is
  taken from Construction at placement, refunded only if the node
  allocation fails; no refund on demolition (manual). `ai_economy_tick`
  (0x98B4) classifies an AI race by total wealth Money+4 funds:
  < 200,001 poor, < 2,000,000 middle, else rich.
- **Pacts/treaties**: fines move through section 3; the "amount of Credits
  paid/received" messages come from `race_add_money` (0x4D224) and
  `post_treasury_message` (0x4D364).
- **Ship purchases** require Vehicles >= price (+0x50 of the yard item,
  `weapon-and-turret-numbers.md`); **missile/ship production** drains the
  Missiles fund each tick by the item's cost-per-tick (0xA04) and stops
  ("production stopped") when the fund is empty.
- **Final rating** (`final_rating_calc`, 0x24D34): a weighted sum of what
  was built and held (counts times price: 100% of built structures, 50% of
  remaining ones, 30% / 20% terms for ships and missiles, 17% of ...)
  minus 70,000 minus Debt minus the start money, times
  `(0x16612 + 1)`, times the factor at 0xC34C, divided by
  `table[0x9CB0 + 3*scenario + sub]/2` (30,45,60,40,60,80,50,75,100,...).
  Shown as the "TetraCorp Rating" (exact term list not reproduced, ?).

## 7. Game text and manual claims (not evidence)

From the build's text resources and the manual extract:

- Four budgets named Construction, Vehicles, Missiles, Personnel plus
  Money; the Personnel fund "pays Colony Supervisors, Agents and Security".
  Low-fund warnings exist for Construction, Vehicle (ship) and Missile funds
  per asteroid supervisor, and "Not Enough Money In The Construction /
  Personnel Fund" on purchase; the code confirms the funds but the supervisor
  warning posting (`agent`-style funds check) was only traced for agents.
- Fines are deducted from Money, then the other budgets, then ore profits
  as a debt -- confirmed by section 3 and 4.4, with the caveat that the
  debt is recorded only when the payee id is nonzero.
- A supervisor not paid one month "may blow up the entire colony"; an
  overworked one may quit, die of heart attack or suicide (death is
  confirmed, 4.3; the blow-up is not found in the recovered code).
- The manual's example pact (10 years, fine 1,000,000 Cr) shows fines can
  be as large as the starting money.
- Manual: hiring costs come from the Personnel budget; the code shows a
  monthly salary (4.1) and no fee at hire.
- Intro text: "Act fast, think faster. TetraCorp expect results"; the end
  screens: out of time / colony destroyed (commission terminated) / all
  aliens destroyed (franchise offered). The time limit/victory conditions
  are in the end-state driver (`main-loop.md`, state 0xF) and were not
  analysed here.

## 8. Design-ready summary

Per race, five integers + a debt integer; income to Money only.

| quantity | value |
|----------|-------|
| start Money | 1,000,000 (all three atmospheres) |
| day length | 32 ticks (`life-support.md`) |
| pop income | 1 Cr per employee per day, colonies with pop > 0 |
| fixed income | {100,250,400} per day per player race, indexed by atmosphere (Peaceful/Neutral/Aggressive) |
| colony claim | up to 8,000 Cr moved Money -> Construction automatically |
| supervisor pay | 10,000..30,000 Cr/month, charged to Personnel on a fixed day-of-month, back-pay accumulates |
| guard (dismissal) | 1,000 Cr/day from Personnel while "under guard" |
| agent mission | 50,000..500,000 Cr + species modifier (-60%..+80%), 12..25 days, charged to Personnel |
| Transporter | arrival after 100..199 days (50..99 in the second mode), departs 50 days later; ore sold at departure |
| fine | via section 3 cascade, shortfall becomes Debt |

Supervisor workload recipe for a reimplementation: keep `W` per supervisor,
add `asteroids * sum(task_weight of enabled tasks) - 20*pen` daily (min 0);
use T2 for the performance meter, T3 for the stress slope (+2/-1 per day,
cap 1000), T4 for a 4%/day disgruntled flag, T5 for a 4%/day death roll.

## Open questions

1. Why does the saved daily income fit about 1018 Cr/day + population when
   the code shows `income_table = {100,250,400}`? Candidate: a second
   income term. (The index question is settled: the table is indexed by the
   atmosphere byte 0x16612.)
2. (Resolved 2026-10-18) Ore unit values (0xE808 + 4*k) are the monthly trade
   prices of the ores, updated every 30 days by the formula in
   `alien-ai-trade-victory.md` 8.3.
3. Supervisor stress thresholds that cause quitting/sabotage/colony
   explosion; the cause of "quit due to lack of pay" (missed-pay count?).
4. What the supervisor table byte +0x16 (2..6) and byte +3 do.
5. Supervisor hire: is there a one-time fee, and what decides which
   supervisors are offered when (appearance countdown 450..897 days)?
6. Agent loyalty model, the per-day capture probability, how `+0x98`
   and the satellite count enter, and the meaning of the mission-table
   `+1` byte.
7. Debt behaviour when the payee id is 0 (federation fines).
8. Which code path writes the 10,000 debt (0x5835D).
9. Time limit / dismissal rule ("out of time", "commission terminated"):
   resolved 2026-10-18: there is no time limit in the GOG build; state 4 is
   never written (`alien-ai-trade-victory.md` 4.1).
