---
title: Personnel
---

# Personnel: Colony Supervisors and Agents

*Status: salaries, thresholds, mission fees, durations and the daily rules are
read from the game's code (**[code]**). Hiring fees, the point at which a
stressed supervisor walks out, and an agent's per-day capture chance are not
resolved (**?**). Claims found only in the game's text or the manual are marked
**[text]**.*

The **Personnel fund** (one of the four budgets, see
[Colony economy](colony-economy.md)) pays two kinds of staff: **Colony
Supervisors**, who manage your asteroids, and **Agents**, who carry out spy and
sabotage missions. Both come from fixed pools of **16 people each**, one per
curriculum vitae shown in the game.

## Who arrives and when

- Neither kind is available at the start. Supervisors are unlocked by the
  player's own colony claims (after **2 to 4** claimed asteroids, decided at
  new-game time) and agents after **3 to 4** claims; a backstop unlocks both
  once the day count passes 700 (first noticed at day 800). **[code]**
- A new supervisor becomes available after a delay of **450 to 897 days**
  (three times a random 150 to 299 count). A new agent becomes available for
  every race (aliens included) every **100 to 149 days**, the first after 50 to
  149 days.
- Hired personnel travel with the next **Federal Transporter** arrival (see
  [Game time](game-time.md)) before they start work. They stay "on the way"
  until then.
- **No hiring fee** was found: the first cost is the first pay-day. (The
  manual says hiring is paid from the Personnel budget **[text]**.)

## Colony Supervisors

A supervisor is assigned to asteroids and keeps their colonies running; in the
game's text each asteroid with a supervisor reports low Construction,
Vehicle and Missile funds. In the code the observable mechanics are salary,
workload, stress and death.

### Pay

- Each supervisor has a fixed **monthly salary** from 10,000 to 30,000 Cr, due
  on a fixed **day of the month** (the day he arrived, minus 1, capped at the
  28th). On that day the whole salary plus any back pay is taken from the
  Personnel fund **[code]**.
- If the fund cannot cover it, the fund is emptied, the shortfall is added to
  **back pay**, the supervisor's missed-pay count rises by 1, and his **stress**
  rises by 5 times his stress factor. Once the missed count reaches his own
  "warn after" value the player is told, in three tiers: back pay under one
  salary ("would like paying in full next month"), under three salaries ("wants
  back pay of N"), otherwise "demands full payment".
- A supervisor under **guard** (after a dismissal or disgruntled episode) costs
  **1,000 Cr per day** from Personnel; if less than that is available, the
  guard lapses with a "security under-funded" message.
- The text says an unpaid supervisor may quit, die or "blow up the entire
  colony" **[text]**; death from overwork is confirmed, the walk-out stress
  threshold and the sabotage are not found **(?)**.

### Workload, stress and death

Each working supervisor carries a **workload value W**, updated daily:

```
S  = sum of weights of the tasks enabled for him
W  = max(0, W + (number of asteroids assigned) x S - 20 x recovery_penalty)
workload shown = min(100, W x 100 / 12000) %
```

- The ten task switches in the supervisor panel have weights
  **2, 2, 2, 3, 3, 1, 1, 1, 2, 3**; all ten are on when he arrives. (Which task
  is which is not recorded here **(?)**.)
- Against his personal thresholds (table below):
  - if **W > T2**, his performance meter falls by 1 per day, otherwise it rises
    by 1 up to his cap (the meter starts at the cap);
  - if **W > T3**, stress rises by 2 per day (maximum 1000), otherwise it falls
    by 1;
  - if **W > T4** and he is not already disgruntled, a 4% daily chance makes him
    **disgruntled** (stress +80 x his stress factor);
  - if **W > T5**, a 4% daily chance that he **dies** (the message names one of
    three causes — heart attack, suicide from overwork, or unknown — chosen at
    random), and all his asteroids are unassigned.
- Dismissing or an unresolved disgruntled state moves him to "under guard" and
  adds stress 140 x his factor. Stress is capped at 1000.
- A working supervisor with no asteroids asks every 60 days (player only) for
  some to manage.

### The sixteen supervisors

Order follows the game's supervisor list. "Pay-day warn" is the number of
consecutive missed pay-days before the player is warned (99 = never). Thresholds
of 200,000 or 400,000 are effectively unreachable, matching the curriculum text
(stable, high-tolerance people).

| # | salary (Cr/month) | pay-day warn | T2 (meter falls) | T3 (stress rises) | T4 (disgruntled) | T5 (can die) | meter cap | recovery penalty | stress factor |
|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| 1 | 25,000 | 3 | 2,000 | 2,000 | 8,000 | 400,000 | 100 | 10 | 4 |
| 2 | 15,000 | 2 | 2,000 | 200,000 | 8,000 | 400,000 | 95 | 7 | 0 |
| 3 | 10,000 | 1 | 1,000 | 2,000 | 12,000 | 8,000 | 80 | 5 | 4 |
| 4 | 25,000 | 2 | 2,000 | 4,000 | 12,000 | 400,000 | 100 | 9 | 4 |
| 5 | 15,000 | 1 | 0 | 200,000 | 4,000 | 4,000 | 100 | 7 | 0 |
| 6 | 20,000 | 3 | 2,000 | 200,000 | 8,000 | 400,000 | 100 | 8 | 4 |
| 7 | 20,000 | 4 | 1,000 | 4,000 | 8,000 | 12,000 | 100 | 8 | 4 |
| 8 | 30,000 | 99 | 3,000 | 200,000 | 12,000 | 400,000 | 100 | 10 | 4 |
| 9 | 10,000 | 2 | 1,000 | 4,000 | 400,000 | 8,000 | 70 | 5 | 2 |
| 10 | 30,000 | 1 | 4,000 | 4,000 | 12,000 | 400,000 | 100 | 10 | 0 |
| 11 | 20,000 | 1 | 2,000 | 2,000 | 400,000 | 8,000 | 88 | 8 | 4 |
| 12 | 20,000 | 1 | 100,000 | 4,000 | 12,000 | 8,000 | 98 | 8 | 3 |
| 13 | 15,000 | 6 | 3,000 | 0 | 400,000 | 12,000 | 95 | 7 | 4 |
| 14 | 25,000 | 1 | 2,000 | 200,000 | 400,000 | 8,000 | 100 | 9 | 0 |
| 15 | 15,000 | 99 | 0 | 4,000 | 400,000 | 8,000 | 90 | 7 | 0 |
| 16 | 10,000 | 4 | 2,000 | 200,000 | 8,000 | 400,000 | 88 | 5 | 0 (?) |

Reading the table: cheap supervisors have a small T5 (they crack under
overload); expensive ones have a large T5 or a huge T3. The daily workload
change is `asteroids x S - 20 x penalty`. With S at most 20 and a penalty of 5
to 10, the recovery term is 100 to 200 per day, so a supervisor needs several
assigned asteroids with most tasks enabled before any workload builds up at all
(worked reading, not a code quote).

## Agents

An agent performs one or more **missions** against a target asteroid. Missions
take days to complete, cost a fee from the Personnel fund up front, and carry a
risk of the agent being caught.

### The thirteen missions

Order follows the game's mission list. "Impact" and "risk" are the points a
success adds to the agent's score and exposure. Fees are the base price before
the agent's own modifier.

| # | mission | days | base fee (Cr) | impact | risk |
|--:|---|--:|--:|--:|--:|
| 1 | sabotage a Ship Yard / Space Dock | 25 | 150,000 | 140 | 50 |
| 2 | collect satellite data-transfer frequencies | 12 | 60,000 | 30 | 20 |
| 3 | collect treaty information | 12 | 50,000 | 100 | 40 |
| 4 | collect asteroid location data | 12 | 75,000 | 40 | 30 |
| 5 | release the anti-population virus (APV) | 25 | 350,000 | 200 | 100 |
| 6 | destroy population centres and life support | 25 | 500,000 | 80 | 90 |
| 7 | destroy mining and ore storage | 20 | 130,000 | 50 | 50 |
| 8 | destroy power generation | 18 | 110,000 | 20 | 40 |
| 9 | destroy anti-missile defences and surface protection | 18 | 190,000 | 40 | 60 |
| 10 | destroy ship attack turrets | 20 | 200,000 | 50 | 50 |
| 11 | destroy ship and missile construction | 17 | 90,000 | 50 | 60 |
| 12 | destroy missiles in storage | 25 | 130,000 | 80 | 60 |
| 13 | destroy the Transporter | 20 | 145,000 | 140 | 50 |

The pairing of missions 7 and 10 to 12 with their effects follows the order of
the game's verb list only **(?)**.

### Price

A mission order is a *set* of up to 13 missions. The fee for each selected
mission is

```
fee = base + base x modifier / 100        (integer division)
```

where the **modifier** depends on the agent and the target's owner: one column
of 16 values for other human-slot empires, and a 16 x 6 table for the six alien
races. The newly selected missions are charged and deselected ones refunded in
the same step. If the target is lost before the agent arrives, the fee is
refunded. The game's "Mission Fees / Risk Factor Fees / Total Fee" lines are
this fee split into the base and the modifier **[code, text]**.

Modifier against another human empire (percent), agents 1 to 16:
`-20, 0, 25, 0, 0, 0, 50, 10, 0, 0, -30, 10, 0, 0, 0, -10`.

Modifier against an alien race (percent), columns Rigellian, Braccatia,
Mikotaj, Artemia, Mauna, Achaean:

| agent | Rig | Bra | Mik | Art | Mau | Ach |
|--:|--:|--:|--:|--:|--:|--:|
| 1 | 10 | 0 | 0 | -30 | 10 | 0 |
| 2 | 0 | 0 | -10 | 0 | 20 | 50 |
| 3 | -10 | 0 | 0 | 0 | -10 | -20 |
| 4 | 40 | -40 | 80 | 10 | 35 | 15 |
| 5 | 45 | 50 | 10 | 20 | 40 | 50 |
| 6 | -30 | 0 | 0 | 0 | 0 | 0 |
| 7 | 0 | -40 | 0 | 0 | 0 | 0 |
| 8 | 20 | -20 | -10 | -10 | -20 | -30 |
| 9 | -40 | -50 | -60 | -10 | 10 | -10 |
| 10 | 10 | 50 | -10 | 0 | 10 | 0 |
| 11 | 20 | 10 | 0 | -10 | 0 | -50 |
| 12 | 0 | 0 | 10 | 0 | 0 | 0 |
| 13 | 0 | 0 | 20 | 10 | 10 | 10 |
| 14 | 60 | 10 | 10 | 0 | -40 | 0 |
| 15 | 0 | 0 | 0 | 80 | 0 | 0 |
| 16 | 0 | 0 | 0 | 0 | 0 | 0 |

The agent's curriculum text ("pro-Terran bias", "friendship with the
Artemia") refers to these columns.

### Duration, cover and capture

- Each agent has a **duration modifier** in percent (agents 1 to 16: 60, 25, 80,
  -10, 35, 60, 20, 25, 45, 25, -20, 80, 50, 10, -30, 10), applied once to the
  mission's days: `days = base days - modifier x base days / 100` (a negative
  modifier lengthens the job).
- Each agent has a **cover score** that starts at a negative number (e.g. -60,
  -40, -75, -10) and a **cover threshold** (e.g. 600, 200, 800, 300, 700). On
  every daily step on a target owned by someone else, the game compares cover
  with the threshold minus a per-agent modifier for the target's owner; if cover
  is below the need, the agent is at risk that day. When he is caught he is
  removed ("contact lost") and the mission lapses.
- The exact daily capture probability and the way spy satellites and a flag on
  the target change cover are not recovered **(?)**.
- When a mission completes, the success adds a share of its impact to the
  agent's cover score (100%, or 60% if the target has the relevant flag, plus 10
  per spy satellite) and its risk points to his exposure, and the outcome is
  reported to the player.
- A virus mission (APV delivery) needs an APV already in your stores; see
  [Trade](trade.md#anti-personnel-viruses-apvs).
- Alien races also hire agents. Every 150 days an alien with an agent picks the
  race it likes least and starts a mission: sabotage of missile defences if the
  target has more than four such buildings, sabotage of ship defences if more
  than four ship-defence buildings, otherwise a random one of the 13.

## Open questions

- Whether hiring has a one-time fee.
- The stress level at which a supervisor quits, and what causes the "blow up the
  colony" sabotage.
- The daily capture chance of an agent and the meaning of one unexplained byte
  in each mission record.
- Which of the ten supervisor task switches is which.

*Related: [Colony economy](colony-economy.md) (the Personnel fund and money
rules); [Game time](game-time.md) (the Federal Transporter);
[Aliens and diplomacy](aliens-and-diplomacy.md); [Trade](trade.md).*
