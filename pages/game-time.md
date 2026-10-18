---
title: Game time
---

# Game time

*Status: the length of a day, the calendar and the daily/periodic cadences are
read from the game's code (**[code]**). The wall-clock speed of a tick, and
which of the three game-speed settings is which, are not settled (**?**). Where
a value is only stated in the game's text it is marked **[text]**.*

Everything in the game that "takes days" — construction, ship building,
supervisor pay, the Federal Transporter, alien expansion — is counted in the
unit described here. A remake should fix one definition of a **day** and
express every other timer in it.

## Ticks, days and the calendar

- The game runs in **ticks** (one pass of its main loop). At the default game
  speed **1 day = 32 ticks** **[code]**; this was also checked against saved
  games, which store the tick count as exactly `32 x day + tick-in-day`.
- A day is divided into **16 phases**, one phase every 2 ticks (a quarter of
  the day-length parameter, 8 at the default speed). Each phase does a different
  chunk of work (see below), so no single tick does everything. Work that is
  "daily" runs exactly once per 32-tick cycle.
- The calendar has **12 months** with the usual lengths (31, 28, 31, 30, 31,
  30, 31, 31, 30, 31, 30, 31) and a year counter **[code]**. A **new game starts
  on 26 May 2496** **[code]**.
- Quirk: the game picks the 28-day February table in leap years and the 29-day
  table in common years (the Gregorian leap rule is tested, but the two tables
  are the wrong way round). It only affects the date shown; every timer in the
  game counts days, not calendar months. A remake can ignore this.
- Several timers are phrased "every month" but are really **every 30 days**
  regardless of the calendar month: the monthly market update (see
  [Trade](trade.md)) and the periodic pass that follows it.
- The absolute **day count** (days since the start of the game) is a separate
  counter. Some one-off gates use it: relationships, supervisors and agents
  are unlocked by the player's colony claims (see [Personnel](personnel.md)) or,
  as a backstop, once the day count passes 700 (first checked at day 800); the
  end-of-game video differs before and after day 730 (see
  [Aliens and diplomacy](aliens-and-diplomacy.md)). Some small cadences use the
  day count modulo 4 (four-day cycles).

## Game speed

The options screen offers three speeds (shown as Fast, Average and Slow in the
game's text). The speed changes the number of **ticks per day**, not the number
of ticks the game logic runs per day of work:

| setting (assumed order) | ticks per day, default option | ticks per day, with the "time in menus" option cleared |
|---|---|---|
| Fast | 32 | 32 |
| Average | 64 | 48 |
| Slow | 96 | 64 |

- The day length is fixed when a new game is created. Whether changing the
  speed in the middle of a game takes effect is **not confirmed (?)**; the only
  place the code sets it is new-game setup.
- Which index is Fast (the table above assumes index 0 = Fast) is inferred
  from the order of the option strings **(?)**.
- Campaigns always start at the fastest setting with the default option.
- The code contains no timer wait: how long a tick lasts on screen depends on
  the machine. A rough observation under DOSBox is about 16 ms per tick, so a
  day is roughly half a second at Fast. Treat this as an estimate only.
- Every day count below is in these game days; multiply by the ticks-per-day
  for the chosen speed if you need ticks.

## What happens when

### Every day (once per 32-tick cycle) **[code]**

In the order the day's phases run:

1. **Colony economy** for every colony of every empire (all player slots):
   income, radiation, population, air, food, water, power, workforce, unrest and
   crime — in exactly that order (details on the
   [colony economy](colony-economy.md) page). The fixed per-race stipend is
   credited right after.
2. **Structure update**: building construction countdowns tick down (a
   building is ready when its countdown reaches zero), burning buildings lose
   hit points, and building behaviours run.
3. **Asteroid drift**: every moving asteroid advances (see
   [Asteroids](asteroids.md)).
4. **World pass**: elimination check (see [Aliens and diplomacy](aliens-and-diplomacy.md)),
   timed events, and each race's order/event queues.
5. **Relations pass**: the hostility matrix update, treaty and pact clocks,
   supervisor payroll and workload, agent missions, the trade-delegate
   scheduler, and the Federal Transporter countdown (see below).
6. **One alien race per phase**: each of the six alien cultures gets its own
   phase for its per-asteroid timers (building, ore, ship spawning and so on),
   and a further phase runs the alien master timers (expansion, pact offers,
   raids).

### Every tick

Fleet movement and firing, missiles in flight, the discovery countdown for new
asteroids, and the per-tick part of AI target tracking. These are the only
parts of the game that are not tied to the day.

### Periodic cadences (days unless stated)

| period | what happens | source |
|---|---|---|
| 1 | colony economy, hostility update, supervisors, alien asteroid timers | code |
| 2 | defensive-response scan of aliens whose asteroids are attacked | code |
| 4 | power plants burn one unit of Asteros ore per plant (every 4th day) | code |
| 8 | the asteroid-ceiling check (create another asteroid while below the setting's limit); an alien learns the bearing of a scout | code |
| 30 | monthly market update (all trade prices, stock, ore prices); colony power-critical message is throttled to once per 30 days | code |
| 32 | each alien runs a raid pass and assigns its Transporter | code |
| 60 | a working supervisor with no asteroids asks for some (player only) | code |
| 100 to 149 | a new agent becomes available for each race | code |
| 150 | an alien with an agent starts a mission | code |
| 185 to 210 | an alien tries to claim a new asteroid (per culture, +-10%) | code |
| 150 to 239 / 150 to 199 | a Trade Merchant / a Trader is offered to each player | code |
| 300 to 650 | first alien pact proposal; later proposals on the same period | code |

## The Federal Transporter cycle

The Federal Transporter is the supply ship that connects the player to the
outside: it delivers hired personnel, ordered Sci-Tek blueprints and queued
buildings and ships, and it carries away the ore you have loaded for sale. Each
empire has its own cycle **[code]**.

The cycle is a single countdown that runs once per day and goes below zero:

| countdown value | event |
|---|---|
| 30 | warning message: the Federal Transporter is in transit and will arrive at a named asteroid in 30 days |
| 10 to 9 | the same message again |
| 0 | **arrival** at the richest asteroid of the empire: delivery counters reset; hired supervisors and agents report for work; ordered blueprints and queued items are delivered |
| -40 | notice that it will depart in 10 days |
| -50 | **departure**: all ore shipped since arrival is valued at the month's Federation ore prices and credited, first against any Debt, the remainder to Money; the countdown restarts |

- The first countdown of a new game starts at **150**.
- After each departure the countdown restarts at **100 + a random 0..99**
  (normal game), so the arrival-to-arrival interval is roughly 150 to 250 days
  including the 50-day stay. A second game mode (the mode flag that also halves
  other cycles) uses 50 + a random 0..49.
- Hiring, ordering and ore sales all happen at these visits, which is why a
  save shows a nearly flat daily income that does not follow the mining rate.
  See [Colony economy](colony-economy.md) for the money rules and
  [Personnel](personnel.md) for what arrives.

## Open questions

- Which index of the speed option is Fast, and whether a speed change applies
  mid-game (the day length is only seen being set at new-game time).
- What the second option row (shown as "time on/off in menus") really means,
  and why it changes the day length.
- What switches the second game mode (the one that halves the transporter
  cycle and disables the trade scheduler).

*Related: [Colony economy](colony-economy.md); [Personnel](personnel.md);
[Aliens and diplomacy](aliens-and-diplomacy.md); [Trade](trade.md);
[Randomness and determinism](randomness.md).*
