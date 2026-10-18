---
title: Aliens and diplomacy
---

# Aliens and diplomacy

*Status: the settings, campaign table, win and lose rules, hostility model,
pact and treaty rules and alien timers are read from the game's code and data
(**[code]**). The alien fleet-launch and missile-volley decisions are only
partly decoded (**?**). Statements found only in the game's text or manual are
marked **[text]** / **[manual]**.*

## The races

Race numbers used throughout the game: **0** unowned, **1 to 8** the player
slots (the human, and the other empire slots; all are treated alike as
"Terran"), **9 to 14** the six alien cultures.

| id | culture | notes |
|--:|---|---|
| 9 | Rigellian | the peaceful baseline **[text]** |
| 10 | Braccatia | an honour culture **[text]** |
| 11 | Mikotaj | |
| 12 | Artemia | |
| 13 | Mauna (buildings: Maunid) | never a diplomatic partner or treaty target; starts the most hostile to everybody |
| 14 | Achaean | never proposes pacts or treaties |

Their buildings and craft are on [Buildings](buildings.md) and
[Vehicles](vehicles.md).

## Game settings and what they change

| setting | values | meaning |
|---|---|---|
| Arena size | Small / Medium / Large | grid of 24x15, 29x18 or 32x20 cells (32 units per cell) |
| Asteroid density | Low / Standard / High | with the size, sets the asteroid ceiling (below) |
| Atmosphere | Peaceful / Neutral / Aggressive | alien attitudes, pact rates, daily stipend, alien expansion |
| Game speed | three values | see [Game time](game-time.md) |
| Aliens present | any subset of the six | with none, it is the "practice game" |

Defaults: Small, Standard, Neutral, fastest speed. **[code]**

**Asteroid ceiling** (the field is topped up every 8 days while the count is
below it; the pool of 100 asteroids is a hard cap):

| | Low | Standard | High |
|---|--:|--:|--:|
| Small | 30 | 45 | 60 |
| Medium | 40 | 60 | 80 |
| Large | 50 | 75 | 100 |

**Atmosphere** is read in only these places; it does **not** change starting
Money (1,000,000 Cr), asteroid count, day length, damage or ore values:

| effect | Peaceful | Neutral | Aggressive |
|---|--:|--:|--:|
| daily stipend to every player's Money (Cr) | 100 | 250 | 400 |
| starting hostility shift of every alien (points) | -40 | 0 | +40 |
| change of the per-shot hostility gain | -50% | 0 | +50% |
| change of the hostility decay | -50% | 0 | +50% |
| alien Non-Aggression Pact proposal period (days, +0 to 30%) | 300 | 400 | 500 |
| alien Joint Combat Treaty proposal period (days, +0 to 30%) | 600 | 400 | 200 |
| alien expansion lead (colonies above the biggest player), Rigellian | 0 | 1 | 2 |
| Braccatia / Mikotaj | 1 | 2 | 2 |
| Artemia / Mauna | 1 | 2 | 3 |
| Achaean | 0 | 1 | 2 |

(The Achaean pact periods are 999 at every setting: they effectively never
propose.)

## Campaigns

Choosing a campaign sets the size, density, atmosphere and alien set together;
custom games set them independently. Campaigns always run at the fastest speed.
**[code]** (names from the game's text)

| # | campaign | arena | density | atmosphere | aliens |
|--:|---|---|---|---|---|
| 1 | Beginner's Luck | Small | Standard | Peaceful | Rigellian |
| 2 | Encounters | Small | Standard | Peaceful | Braccatia, Mikotaj |
| 3 | Getting Serious | Medium | Standard | Neutral | Rigellian, Mauna |
| 4 | Three's a Crowd | Medium | Standard | Neutral | Braccatia, Artemia, Achaean |
| 5 | Raising The Stakes | Large | High | Neutral | Rigellian, Braccatia, Artemia, Mauna |
| 6 | The Void | Large | High | Neutral | Rigellian, Braccatia, Mikotaj, Artemia, Achaean |
| 7 | Crowded House | Large | High | Neutral | all six |
| 8 | Knowledge is Power | Large | Standard | Aggressive | all six |
| 9 | Full On | Large | Low | Aggressive | all six |
| 10 | Getting Tight | Medium | Standard | Aggressive | all six |
| 11 | The Ultimate | Small | High | Aggressive | all six |

The manual's hardest recipe is Large, High, Aggressive, all six cultures
**[manual]**.

## Winning and losing

- **Victory**: every other configured race — aliens and other player slots —
  has lost all its asteroids. It need not be the player who destroyed them.
  Checked daily. **[code]**
- **Defeat**: the player owns no asteroids. A colony whose population reaches
  zero is destroyed and counts the same way. **[code]**
- With no alien culture configured (the practice game) victory can never fire;
  the game ends only by defeat or quitting.
- **There is no time limit.** The "out of time" end screen exists in the text
  but is never reached. **[code]**
- End videos: a defeat shows one of two videos depending on whether the day
  count is under or over 730; a victory shows one of two at random. A
  statistics screen with the "TetraCorp Rating" follows.

## What aliens do

Alien races have no Money; they run on production points and per-asteroid
timers, all counted in days. **[code]** (the descriptions of what each routine
does are inferred from the code it calls).

### Colony classes

Each alien asteroid has a class from 0 (richest) to 3, from its ore wealth rating
(about the 90th, 80th and 20th percentile of random asteroids: roughly 56, 51
and 31 on the rating scale) shifted by a wealth counter (positive after receiving
money, negative after paying fines, decaying by 1 per day). The class sets the
pace:

| class | structure cap | new-structure interval above the cap (days) |
|--:|--:|--:|
| 0 | 15 | 8 |
| 1 | 10 | 15 |
| 2 | 6 | 20 |
| 3 | 4 | 20 |

Below the cap an alien tries again in 1 to 2 days and places one building of a
random available type. Alien asteroids start with 50 people.

Other per-asteroid timers (days, by culture Rigellian, Braccatia, Mikotaj,
Artemia, Mauna, Achaean):

| timer | classes 0 / 1 / 2 / 3 or value |
|---|---|
| ore production interval | Rig 14/19/24/29, Bra 9/14/19/24, Mik 10/15/20/25, Art 8/13/18/23, Mau 6/11/16/21, Ach 12/17/22/27 |
| building interval | Rig 52/62/72/92, Bra 32/42/52/72, Mik 40/50/60/80, Art 25/35/45/65, Mau 36/46/56/76, Ach 48/58/68/88 |
| ore-selling base | Rig 64, Bra 52, Mik 72, Art 56, Mau 44, Ach 76 (scaled by stock) |
| ship-density scan | 50 for all |
| fleet-marking | Rig 140, Bra 150, Mik 135, Art 145, Mau 165, Ach 160 |
| capacity refresh | Rig 210, Bra 190, Mik 200, Art 170, Mau 150, Ach 230 |

### Expansion

Each culture tries to claim a new asteroid every **205 / 200 / 210 / 185 / 190 /
195 days** (Rigellian to Achaean, +-10%, first attempt on that exact day). It
needs a Transporter of its own and a free asteroid within range. It stops if
its colony count is at least **(the largest colony count among the human player
slots) + its lead** (table above). So aliens **rubber-band to the biggest human
empire**: at Neutral, with one human colony, a Rigellian aims for 2 and a Mauna
for 3. Every 32 days an alien without a Transporter tags asteroids to build one.
Every 32 days each alien also runs a **raid pass** that re-tasks its units on
foreign asteroids, colonises unowned ones when it has fewer than four colonies or
the asteroid is valuable, and sends ships toward the nearest foreign asteroid.

### Who an alien attacks

For each other race an alien computes an attractiveness: the average of its
current and baseline hostility toward that race (in %), plus how much weaker the
target is (the strength difference as a percentage), minus a distance penalty for
targets beyond 256 units. A race is a target only while this is positive.
Strength is dominated by colonies (600 each). Targets must be within **192 units**
of the attacking asteroid; up to three nearest per owner are considered. An
asteroid under attack is defended: if the defender is already hostile to the
attacker, it retaliates when the attacking fleet is within **60 units** (120 if
it owns a particular sensor-type building). Alien ships mass on the side from which
a human scout approached (the bearing is learned every 8 days).

The size and composition of alien attack fleets and when they fire missiles are
**not decoded (?)**.

## Hostility

The game keeps a **hostility** value from every race toward every other race
(never "friendship"). For each pair, there is a **baseline** the value decays
toward and a **current** value; range -100% (-1.0) to +100%.

### The daily update

```
if the pair had incidents today (weighted shots, collisions):
    current += gain x incident weight          (cap +100%)
    grace days += incident weight; days quiet = 0
else if grace days = 0:  current = max(baseline, current - decay)
else:                    grace days -= 1
```

- Each shot adds its weapon's weight (Explosive 1, Area Explosive 3, Napalm 5,
  Hellfire 7, Scatter 25, Vortex 20, Nuclear 100, Virus 100, Mega 255, Stasis 50,
  Bug Hunter and Meat-Eater 150); an asteroid collision adds a fixed weight to
  both directions.
- **Grace days are a long memory**: an alien that has fired 1,000 weighted shots
  keeps its raised hostility for at least 1,000 further quiet days.
- The human player's own row is never changed, so a human is always an eligible
  target.

### Starting hostility toward the player

Percentages of the full range, after the atmosphere shift (clamped to +-100);
gain per shot and decay per day are in raw units (the full range is about
32,767 units).

| culture | Peaceful current / baseline | Neutral | Aggressive | gain per shot P / N / A | decay per day P / N / A |
|---|---|---|---|---|---|
| Rigellian | -40 / -60 | 0 / -20 | 40 / 20 | 36 / 72 / 109 | 15 / 31 / 45 |
| Braccatia | -20 / -60 | 20 / -20 | 60 / 20 | 54 / 109 / 163 | 13 / 27 / 40 |
| Mikotaj | 0 / -55 | 40 / -15 | 80 / 25 | 54 / 109 / 163 | 13 / 27 / 40 |
| Artemia | 0 / -60 | 40 / -20 | 80 / 20 | 45 / 91 / 136 | 9 / 18 / 27 |
| Mauna | 50 / 0 | 90 / 40 | 100 / 80 | 81 / 163 / 182 | 2 / 4 / 6 |
| Achaean | -40 / -70 | 0 / -30 | 40 / 10 | 27 / 54 / 81 | 18 / 36 / 45 |

Reading it: at Peaceful only the Mauna are even neutral toward you; at Neutral
the Mauna sit at +40 and the others at -15 to -30, so they attack only a clearly
weaker colony; at Aggressive every culture has a positive baseline. A starting
value above the baseline decays slowly: Mikotaj at Neutral needs about 660 quiet
days.

### Alien toward alien

Starting (current) and baseline percentages at Neutral; row = the hostile party,
column = its target. The atmosphere shifts these by the same 40 points.

Current:

| | Rig | Bra | Mik | Art | Mau | Ach |
|---|--:|--:|--:|--:|--:|--:|
| Rig | - | 50 | -60 | 35 | 70 | -40 |
| Bra | 10 | - | 60 | 80 | 70 | 0 |
| Mik | -50 | 70 | - | 80 | 0 | -30 |
| Art | 0 | 30 | 80 | - | 95 | -50 |
| Mau | 70 | 80 | -10 | 95 | - | 10 |
| Ach | -80 | 30 | -20 | 20 | 90 | - |

Baseline:

| | Rig | Bra | Mik | Art | Mau | Ach |
|---|--:|--:|--:|--:|--:|--:|
| Rig | - | -15 | -30 | -15 | -10 | -30 |
| Bra | -30 | - | -20 | 30 | 20 | -30 |
| Mik | -20 | -10 | - | -10 | -20 | -20 |
| Art | -20 | -5 | -10 | - | 40 | -20 |
| Mau | 10 | 30 | -10 | 50 | - | -10 |
| Ach | -40 | -15 | -40 | -15 | -30 | - |

Gain and decay between aliens are also per pair (gain from 20 to 100, decay from
0 to 90); they are omitted here.

## Pacts and treaties

Two instruments, each between two parties. A pact value of -1.0 on a matrix cell
means a **pact in force**, not a war.

### Non-Aggression Pact (NAP)

- A clause set: no overt action, no covert action, or both. A violation is any
  prohibited action: shots, missiles, spy satellites, agents.
- Starts with a **10-day grace**; a violation then starts a **5-day countdown**
  to termination with penalties.
- Ending cleanly lowers both parties' hostility toward each other by **0.5**;
  ending by violation moves the **fine** from violator to victim and raises
  the victim's hostility toward the violator by 0.5.
- Creating a pact forces both aliens' hostility toward the partner to -1.0.

### Joint Combat Treaty (JCT)

- Two signatories agree to attack a **target** race. Each has a quota of
  weighted shots at the target: **Low 400, Medium 1,000, High 3,000**.
- Each daily weighted shot at the target reduces the quota; a side whose quota
  reaches zero is done; when both are done the treaty ends cleanly. A signatory
  that falls short owes a fine; with the overrun clause, the debt grows by
  **30 Cr per leftover shot** of the other side.
- Creating a JCT sets each alien signatory's hostility toward the target to
  +1.0; announcing it publicly adds +0.5 to the signatories' hostility toward
  an alien target.

### How aliens propose them

- Each culture has two timers (NAP and JCT) set at game start and re-armed on
  firing, at the periods in the atmosphere table. Achaeans never propose.
- **NAP**: the proposer picks a random other race (not itself, not Mauna) that
  it has met and has no NAP with, whose pact attractiveness is positive. If the
  partner is the human, the proposal goes to the player's communications screen.
- **JCT**: the partner needs positive pact attractiveness; the target is the
  **nearest** race (by colony centre) that is neither the proposer nor the
  partner nor Mauna.
- **Terms**: duration = 900 - 20 x (strength difference % minus attitude
  difference %), clamped to **90 to 1,800 days**; fine = 1,000,000 + 20,000 per
  point of approval + 100 per point of the proposer's strength, clamped to
  **50,000 to 10,000,000 Cr**. The clause level offered (Low, Medium, High) is
  set by the partner's attractiveness (under 10: Low; under 50: Medium; else
  High).
- **Acceptance** (when an alien evaluates a proposal): accept, counter or reject.
  A proposal is rejected if a NAP or JCT already exists between the same races.
  Otherwise it is accepted when the terms lie within a tolerance (2 x s %) of
  the AI's own preferred fine and duration, where `s` is 0 to 5 from the relative
  strength gap; else the AI sends a counter proposal.

### Gifts

Gifts are trade transfers at price zero and lower the receiving alien's
hostility; see [Trade](trade.md#gifts-and-hostility). Money paid to an alien
(tribute, fines) never changes hostility; it raises the alien's wealth counter
by amount/15,000 on each asteroid it owns.

## Open questions

- Alien fleet launches: composition, thresholds and when aliens fire missiles.
- Whether alien agents ever use the virus mission.
- How the diplomacy screen's wording maps onto hostility thresholds.
- What sets the game's second mode flag and the reduced-AI configuration.

*Related: [Game time](game-time.md); [Colony economy](colony-economy.md);
[Personnel](personnel.md); [Trade](trade.md); [Missiles](missiles.md);
[Ship-to-ship combat](ship-combat.md).*
