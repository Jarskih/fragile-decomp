# Extraction roadmap — game-design numbers for the remake

Status: phases 0–3 largely done (2026-10-18); the remaining items are listed
below in design-impact order
Source: the open-question sections of every note in `docs/mechanics/` and
`docs/dataformats/`, the GOG build's `_TEXT/ENGLISH.TXT`, the manual, the
GOG savegames and the GOG flat image

This roadmap orders extraction work by **impact on game design**, not by
reverse-engineering convenience. The question behind every item: *does a
designer need this number or rule to make the remake play like the
original?* Bit-exact reproduction (RNG streams, generator call order,
sprite layout) is out of scope unless it changes how the game plays.

## The breakthrough: "tables in code" was a base error

Most per-type numbers looked runtime-only because the DS-relative table
reads were resolved against the wrong base. In the GOG build every static
gameplay table sits at **flat offset = DS displacement + 0x86004** (memdump
offset = flat + 0x1C801C); in the reference build the building table sits
at displacement + 0x8E004. The old exhaustive base search missed it because
the true base is 4 mod 16. With this rule, building, craft, missile,
warhead, settings, AI and trade tables all read as plain static data, and
most of the planned memdump capture session is no longer needed.

## Done

| item | result | technical note | designer page |
|---|---|---|---|
| Time base | 1 day = 32 ticks (default speed); calendar from 26 May 2496; game speed 0..2 lengthens the day; per-day and 30-day cadences | `main-loop.md`, `life-support.md` | `pages/game-time.md` |
| Life support | air/food/water demand = population (1 unit per employee per day), producer and storage values, power generation and brown-out priority, radiation deaths, workforce staffing, unrest and crime | `life-support.md` | `pages/colony-economy.md` |
| Money | Money pool plus four funds and debt; start 1,000,000 Cr; income 1 Cr per employee per day plus an atmosphere stipend; ore sold when the Federal Transporter departs; payment cascade and debt | `economy-and-personnel.md` | `pages/colony-economy.md` |
| Personnel | Colony Supervisor salary, workload, stress and death rolls; agent missions with base prices, durations and per-race price modifiers | `economy-and-personnel.md` | `pages/personnel.md` |
| Buildings | all 177 building rows (40 Terran + 137 alien): cost, HP, build days, footprint, MW, morale delta, capacities, staffing | `building-stat-table.md`, `stat-tables-design-sheet.md` | `pages/buildings.md` |
| Craft | 41 craft records: armour, speed, hardpoints, build days, ore costs, price; 16 hardpoint items | `vehicles.md`, `stat-tables-design-sheet.md` | `pages/vehicles.md` |
| Missiles and warheads | per-launching-race blast damage, radius, cone, Scatter count, Stasis/Virus timers, strike %; flight speed; the strike chance is the arrival probability | `ship-hit-formula.md`, `weapon-and-turret-numbers.md` | `pages/missiles.md` |
| Alien AI and diplomacy | hostility matrix (not friendship), pacts and treaties with quotas and fines, alien expansion and raid cadence, target choice | `alien-ai-trade-victory.md`, `diplomacy.md` | `pages/aliens-and-diplomacy.md` |
| Settings, campaigns, win/lose | arena and density tables, atmosphere effects, 11 campaigns; defeat = no colonies, victory = one race left; **no time limit** | `alien-ai-trade-victory.md` | `pages/aliens-and-diplomacy.md` |
| Trade | 101 goods, 32 parties, monthly price waves, buy/sell factors, delegate schedule, APVs and cures | `alien-ai-trade-victory.md` | `pages/trade.md` |
| Savegame fields | day/tick counters, Money pools, transporter timer, population, building counts | `savegame-format.md` | — |

Withdrawn along the way (fixed in every affected note): the "fire delay
15/40 VERIFIED" finding (message cooldowns), the "ship weapon-slot table"
(it is the colony event table: APVs and Terran colony events), "opinion"
matrices (they hold hostility), the `0x200e4` dogfight reading (it is the
missile warhead impact machine), and the 8-tick day.

## Remaining, by design impact

### High

1. **Ship-to-ship combat numbers.** No per-weapon damage, range or
   rate-of-fire table exists in the data; the hardpoint weapon callbacks sit
   in unrecovered gap code (GOG 0x13804..0x13d74 is the colony-event code;
   the weapon code still has to be located). Route: a Ghidra function pass
   over the gap code, then a memdump during a ship battle if the values are
   computed. Until then a remake must choose its own numbers
   (`pages/ship-combat.md`).
2. **Turret damage and Anti-Missile Pod interception.** Turrets differ only
   by their building row and muzzle bytes; how much damage a turret deals
   and how a pod stops a missile is not found. Same route as item 1.
3. **Alien fleet size and missile-volley choice.** Raid cadence and target
   choice are decoded; how many ships or missiles an attack commits is not.

### Medium

4. **Supervisor walk-out and sabotage thresholds**, the "blow up the
   colony" event, agent loyalty and capture chance.
5. **Unrest semantics**: whether the one-off morale delta at building
   placement and the daily unrest counter are the same quantity; the named
   sickness stages.
6. **Text-versus-code conflicts** a designer must pick a side on:
   Environment Control 3000/1000/1000 (code) vs 5000/600/600 (text);
   Solar Matrix 12 MW (code) vs 8 (long text). The code values are what the
   game actually does.
7. **Game speed mapping**: which speed index is "Fast", and whether a
   mid-game change is allowed.

### Low

8. Sci-Tek delivery delay location; the Trade menu availability rules and
   the delegate name table.
9. The 1,000,000 words at savegame 0xA8..0xC0; the CPU output decay link.
10. Re-reading the reference-build (ISO) copies of the tables with the
    +0x8E004 base (needs `iso/` restored and `make all`).

## Deliberately deprioritised

- RNG stream reproduction and exact generator call order
- Ring objects, sprite and terrain-record layout, colony-view rendering
- File container formats beyond what the save-diff route needs

## Definition of done for each item

1. The technical note has a `confirmed` status and cites a table address,
   a code address, a save diff or a dump.
2. A functional page in `pages/` states the rule in in-game language, with
   a numeric table a designer can paste into a spreadsheet, and tags each
   value as code-confirmed or text-only.
3. Any game-text claim the code contradicts is marked as such on the page.
