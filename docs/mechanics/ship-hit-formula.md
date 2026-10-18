# Missile impact and hit resolution (file name kept: "ship hit formula")

Status: **mechanics confirmed, per-type numbers now confirmed for the GOG
build** (static disassembly of `build/flat/FRAGILE.EXE.gog.flat` plus the
static data it reads; the Interplay CD reference build was analysed earlier and
is assumed identical — its flat is not in `build/` at the time of this
revision, so the ISO values are **not re-read**). The per-race bytes that
the earlier revision called "runtime-only" are **static initialised data** in
the GOG flat (see "Correction of 2026-10-18"). What remains open is listed at
the end.

Source: `build/flat/FRAGILE.EXE.gog.flat`, `build/flat/gog_disasm.txt`,
`build/named/FRAGILE.EXE.gog.flat/decompiled.c`. Provenance codes as in
`stat-tables-design-sheet.md`: **S@addr** static GOG flat address, **C@addr**
constant in code, **I** inferred.

## Correction of 2026-10-18 (read this first)

Three earlier statements of this note are overturned:

1. **"Tables in code / runtime-only" was a base error.** Every static table the
   GOG code reads through a DS-relative displacement `D` lives at GOG flat
   `D + 0x86004` (the data object starts at flat 0x86000, plus the 4-byte
   image header; see `stat-tables-design-sheet.md`). The per-race combat
   bytes (displacements `0xb960 … 0xb9d8`) therefore sit at flat
   `0x91964 … 0x919dc` and hold plausible, consistent data (values below).
   The same rule fixes the ISO build: ISO flat = `D + 0x8E004` (confirmed for
   the building table, `building-stat-table.md`); corresponding ISO
   displacements are the GOG ones `+ 0x6CC` for the combat block (ISO `0xc02c`
   ↔ GOG `0xb960`, `0xc095` ↔ `0xb9c9`, `0xba8a` ↔ `0xb3be`, `0xbfe4` ↔
   `0xb918`) and `+ 0x6E8` for the building/craft block (ISO `0xa6b8` ↔ GOG
   `0x9fd0`, `0xb244` ↔ `0xab5c`, `0xa4ac` ↔ `0x9dc4`). **I** — shift read off
   address pairs, not re-verified bytewise.
2. **Code pointers stored in data are `flat − 4`.** Every function pointer in
   the static tables (the handler lists; the 0x9dc4 table is the colony event table, not a weapon table) is the function's
   start minus 4 (functions are 16-byte aligned in the code object, the image
   adds a 4-byte header). Add 4 to get the flat start. Data-object pointers
   stored in tables (e.g. `0xba44`) are DS displacements (+0x86004 for flat).
3. **This machine is the missile *warhead* impact machine, not a ship/turret
   dogfight.** The "children" it sweeps are the **structures of the attacked
   asteroid** (the asteroid's `+0x8` list: child `+8` = building type, `+9` =
   hit points, `+0x14/+0x15` = surface-grid cell). The damage helper subtracts
   from the structure's hit points (`+9`) and removes the structure at ≤ 0. The
   handlers are chosen by the **missile type** (via the per-record id byte of
   the missile table, S@0x913C2 = record `+0xe`), not by ship or turret weapon.
   The earlier claim "hardpoint beam weapons (Laser, Photon, Plasma) and
   turrets resolve by radius/arc sweep" was wrong. The per-race index is the
   **launching race of the missile** (the missile node's `+9`, written when
   the missile node is created — e.g. the AI production tick `0x19984` stores
   the producing race there), not the attacked asteroid's owner.

Whether and how turrets and hardpoint weapons deal damage is **not** answered
by this machine; see `turrets-and-defence.md`.

## The three resolution models

| model | used by | roll? |
|---|---|---|
| **blast sweep** (circle or cone) | the Explosive, Area Explosive, Napalm, Hellfire, Nuclear and the Scatter bomblets and alien-special warheads | no roll — every structure inside the shape is hit once |
| **strike roll** | the rolled storm walker of the Vortex missile | per-tick roll vs a per-race byte |
| **direct hit** | two alien-special warheads | no roll — 120 damage |

The **missile targeting percentage** the player sees ("Strike chance: %d%%" /
the fleet panel "Strike Rate") is a separate, pure distance estimate (below).

## How the machine is keyed

A missile node stores its type at `+8` (index into the 16-byte missile table;
the record's `+0xe` field is the missile id, 0..17), the **launching race** at
`+9` (1 = TetraCorp, 2..8 = HumanCorp factions, 9..14 = the six alien races) and,
once it is on its way, the attacked asteroid at `+0x10`. All per-race bytes
below are indexed by `+9`, i.e. by who fired, so an alien race's missiles
behave differently from a human race's against the same victim. (Successor
walkers allocated by `obj_spawn_child` carry the *attacked asteroid's* owner
type in `+9` instead, but they never read the per-race bytes.)

Per-race table (S@0x91964…, nine 15-byte arrays indexed by launching race, index 0 unused = 0):

| launching race | blast damage | radius² A | radius² B | cone range² A | cone range² B | Scatter bomblets | Stasis base | strike % | lifetime base |
|---|---|---|---|---|---|---|---|---|---|
| displ. | 0xb960 | 0xb96f | 0xb97e | 0xb98d | 0xb99c | 0xb9ab | 0xb9ba | 0xb9c9 | 0xb9d8 |
| 1 – 8 (TetraCorp, HumanCorp) | 10 | 4 | 9 | 16 | 25 | 25 | 50 | 4 | 25 |
| 9 | 14 | 9 | 16 | 25 | 36 | 30 | 55 | 5 | 25 |
| 10 | 10 | 4 | 9 | 16 | 25 | 25 | 45 | 4 | 25 |
| 11 | 8 | 4 | 9 | 9 | 16 | 23 | 35 | 3 | 25 |
| 12 | 11 | 4 | 16 | 16 | 25 | 26 | 55 | 4 | 25 |
| 13 | 12 | 9 | 16 | 25 | 36 | 28 | 65 | 5 | 25 |
| 14 | 6 | 4 | 4 | 9 | 16 | 20 | 25 | 3 | 25 |

Reading (all **S**, roles **C**-confirmed from the handler code, see next
section): "radius²" and "range²" are squared distances in surface-grid cells (so
4 = 2 cells, 9 = 3, 16 = 4, 25 = 5, 36 = 6); damage is hit points removed from
each structure hit; strike % is the per-tick successor chance of the Vortex
walker; lifetime base feeds the walker lifetime. Races 1–8 are identical, so
every human or TetraCorp launcher uses the "typical" values; the six alien
races differ (races 9 and 13 are the strongest, 14 the weakest). The mapping of
races 9..14 onto the alien race names is now established (Corrected
2026-10-18, `alien-ai-trade-victory.md` section 0): 9 Rigellian, 10 Braccatia,
11 Mikotaj, 12 Artemia, 13 Mauna, 14 Achaean.

## Which missile uses which handler

The pointer table S@0x9191C (`0xb918`, one entry per missile id, ids 0-17)
points to a short list of handler pointers per id (lists at
`0xba44 …`); the shot node's `+0xc` walks the list one entry per state.

| id | Missile | handler (flat) | effect (launching race 1–8; alien values in the table above) |
|---|---|---|---|
| 0 | Explosive | 0x20094 | circle, radius² A: 10 damage to every structure within **2 cells** |
| 1 | Area Explosive | 0x200D4 | circle, radius² B: 10 damage within **3 cells** |
| 2 | Napalm | 0x20114 | cone sweep, range² A (4 cells), 5 damage, structure gets **burn state 5** |
| 3 | Hellfire | 0x20144 | cone sweep, range² B (5 cells), 5 damage, structure gets **burn state −10** |
| 4 | Scatter | 0x20174 | **25 bomblets** (races 1–8) dropped at random offsets 2–16 cells from the impact; each bomblet is a circle of radius² 4 (2 cells) with 10 damage (C@0x202B4) |
| 5 | Vortex | 0x20324 / 0x20354 | spawns a **rolled walker** (below) |
| 6 | Nuclear | 0x20534 | circle radius² 400 (**20 cells**) 7 damage, then a full-circle sweep of the same radius, 5 damage (C@0x20534); ships in orbit are moved (I); an asteroid counter `+0x95` += 4 |
| 7 | Virus | 0x205E4 | sets the asteroid's infection flag (`+0x139` bit 0), loads a timer `+0x9c` = 350 + rng(50), marks a random surface cell |
| 8 | Anti-Virus | 0x20684 | sets `+0x139` bit 1, `+0x95` += 1, clears bit 0 of `+0x19f` (I: cures the infection) |
| 9 | Mega | 0x206D4 | sets asteroid flag `+0x138` bit 5 (the destruction flag; I) |
| 10 | Stasis | 0x206F4 | sets the asteroid's hold timer `+0x11e` = S + rng(S/2) with S = Stasis base (**50–74** for types 1–8) |
| 11 | Bug Hunter | 0x20744 | posts event 4 on the target; 25 % → diplomatic record (see below) |
| 12 | Meat-Eater | 0x20794 | posts event 5 on the target; same 25 % gate |
| 13 | (alien special) | 0x207E4 | cone range² 196 (14 cells), 5 damage |
| 14 | (alien special) | 0x20814 / 0x20854 | a 180-tick random walker doing **120 damage** per tick (direct hit) |
| 15 | (alien special) | 0x209F4 | circle radius² 100 (10 cells), **120 damage** |
| 16 | (alien special) | 0x20A24 / 0x20B54 | drains the target's ore stocks (the loss per ore is a random value between the (min, max) pair of the ore starting-value table S@0x8FCF2, capped at the stock), then the same bomblet cloud as id 17 |
| 17 | (alien special) | 0x20B54 | the bomblet cloud alone (the second state of id 16): `b9ab` bomblets, each a cone sweep with cone range² A and 5 damage (C@0x202E4) |

Notes: the 25 % gate on Bug Hunter / Meat-Eater is a `rng_next(100) < 25` roll
that, on a pass, calls the bookkeeping routine `0x42114` — recorded only when
the attacker is the player and the target an alien race — i.e. it gates a
diplomatic record, not the effect (C@0x20762, C@0x207B2). The event numbers 4/5
are what the colony event queue (`0x13e74`) turns into the population-killing
effect. The Stasis timer `+0x11e` is decremented once per object-tick pass
(game state 1, C@0x123) and, while non-zero, blocks the asteroid's drift, AI
colony actions and fleet launches (multiple `cmpw $0,0x11e` guards): it is a
"frozen" timer. Its length in game days is not derived here.

The cone sweep (GOG `0x1f9e4`) hits a structure when its centre lies within the range² **and** either it is
closer than the inner radius `(node +0x1f · range²) >> 6` or its bearing from
the node lies within `[facing − 0xa0, facing + 0xa0]` (byte angles, a 225°
window; only a 135° sector is excluded). The facing byte `+0x1e` and inner
multiplier `+0x1f` come from the node; Nuclear sets `+0x1f` = 0x40 explicitly
(full radius). For Napalm and Hellfire the node's `+0x1e/+0x1f` are inherited
from the impact cell coordinates written by the spawner (`obj_spawn_child`), so
their cone orientation is effectively tied to the impact cell — **I**, not
traced further.

The circle sweep (GOG `0x1f934`) is the same distance test without an arc test.
Both tests use the structure's centre: its cell coordinates plus half its
footprint width/height (static footprint table S@0xBC278, `0x36274`/`0x36275`;
see `building-stat-table.md`).

### Damage, halving and burning

- The damage helper (`0x1aa94`) subtracts the damage byte from the structure's
  hit points; a structure at ≤ 0 is removed. If the asteroid has flag
  `+0x139` bit 5 set **and** the structure's footprint touches a cell carrying
  the screen flag (helper `0x1a9b4`), the damage is **halved, rounded up**
  (I: the Screen Generator's protection).
- Structure hit points are the Armour values of the building table
  (`building-stat-table.md`, 5–40 for the Terran set, +10 with the Building
  Armour blueprint). A typical 10-damage Explosive therefore removes any
  structure of 10 HP or less within 2 cells in one go and leaves a 40-HP
  structure at 30.
- **Burn state** (structure `+0xb`): the cone sweep writes `5` for Napalm and
  `−10` for every other cone sweep (Hellfire, Nuclear, the alien specials). The
  per-structure routine `0x1adb4`, called from the structure update pass
  (`0x1449`, game state 3 of the main loop — one pass per state cycle, not per
  main-loop tick), then removes **1 HP per pass**: state 5 counts down over 5
  passes; a negative state counts up from −10 and, each pass, has a
  **20 %** chance to ignite a neighbouring structure with the next state value —
  the game text's Hellfire "spreading across entire asteroid" (C@0x1ADB4).

## The strike roll (Vortex storm walker)

The Vortex missile's walker is the only user of the strike byte. A walker has a
lifetime and an attacked cell. Per tick (handler `0x20354`, gated by the global
at `0x34725`):

```
target "under attack" timer = 10
lifetime -= 1; if 0, free the walker
if the walker is a rolled one (flag +0x14 == 0)
    and rng_next(100) < strike_byte[launching race]:
        spawn a no-roll successor at this cell,
        lifetime = remaining lifetime + rng_next(6)
find the structure occupying the walker's cell (0x1ab84)
if found: structure loses 2 HP
move the walker one step in a random one of 8 neighbour directions
```

- **Rolled walker lifetime** at spawn: `(rng_next(L) + L) · 2` with `L` = the
  lifetime base (25 for every race) → an even number **50 … 98**, mean 74
  ticks (C@0x1FC22, S@0x919dc).
- **No-roll walker** (the missile impact node itself, and successors): lifetime
  `argument + rng_next(6)`; the impact node's argument is `4 + rng_next(4)`, so
  it lives 4 … 12 ticks.
- **Strike byte** (per tick successor chance): **4 %** for races 1–8; the
  alien values 5, 4, 3, 4, 5, 3 % (races 9…14).
- The 8 neighbour steps (S@0x91A38): (0,+1) (0,−1) (+1,+1) (+1,−1) (−1,+1)
  (−1,−1) (+1,0) (−1,0).
- Damage is **2 HP per tick** to whatever structure is on the walker's cell
  (also halved under a screen). The strike roll does not gate the damage; it
  gates whether the storm gets a successor.

Expectation for a rolled walker of lifetime `L` and `p = strike/100`: it makes
`p·L` successors on average; a successor spawned with `r` ticks left lives
`r + 2.5` on average, so the whole storm deals up to
`2L + p·(L² + 4L)` HP **if** the walker stays over structures. At `L = 74`,
`p = 0.04` that is 148 + 231 ≈ **380 HP** of potential damage per Vortex
walker (the real figure depends on how often the random walk sits over
structures) — the Vortex is a slow, widespread attrition weapon, as the game
text ("electrical storm across asteroid") suggests.

## The direct-hit walker

Handler `0x20854` (alien-special id 14) is the same per-tick body **without the
roll**: it lives 180 ticks (0xB4, set by `0x20814`), strikes the cell under it
for **120 HP** per tick (kills any structure) and random-walks; gated by the
global at `0x34724`. Alien-special id 15 is a single circle of 10 cells with the
same 120 damage. Both are one-shot annihilation weapons by comparison with
anything the Terran list has except Mega.

## Missile flight, strike chance and the aim spread

- **Flight speed is a constant for every missile type**: the flight handler
  (`0x1fe34`) advances the missile `3 · direction-table` per tick, i.e. **3
  world units per tick**, in whole 16.16 units (C@0x1FE6C…0x1FE9B), with no
  per-type factor. A launch from 192 units away takes about 64 ticks of flight
  (the lifetime byte is separate, see below).
- The missile arrives when its distance to the target's centre falls below the
  target asteroid's radius byte (`+0x40`, squared compare, C@0x1FEC0).
- At launch the colony code stores the strike percentage in the missile's
  `+0x0a` byte. At the first approach tick (`0x1fce4`) the flight handler rolls
  `rng_next(101)` and compares: a roll **at or below** the percentage (a hit,
  probability (chance+1)/101) sets the flight timeout `+0x0a` to **255**, long
  enough for any flight; a roll above it sets a **short timeout** from the aim
  spread below (about 10 – 40 ticks). The second-state handler (`0x1fe34`)
  decrements that byte every tick and frees the missile when it reaches 0, so
  a "missed" missile simply expires part-way to the target (its flight needs
  `distance / 3` ticks: 33 at 100 units, 64 at 192). The displayed "Strike
  chance" **is** the missile's arrival probability (C@0x1FD71…0x1FE03); a
  non-zero global byte at `0x1660a` forces 255 (a test switch; **I**).

### The aim spread

```
s = dist − (launcher speed byte + target speed byte)
x = (min(s, 160) − 32) / 3                      ; signed division
lifetime = (rng(x) + rng(x) + rng(x) + 32) / 3
```

(`rng(x)` = `rng_next(x)`, result in `[0, x)`; `s` subtracts both objects'
speed bytes `+0x50` from the distance.) This is the timeout of a **missed**
missile, not a position error: `s ≥ 192` gives `x = 42` and an expected 31
ticks; `s = 100` gives `x = 22`, ≈ 21 ticks — both shorter than the flight
time, so the missile expires before arriving; `s < 32` makes `x` negative and
the rolls degenerate (the close-range behaviour of a miss is unpredictable).

### The displayed strike percentage

```
dx = (target.X − launcher.X) >> 16 ; dy likewise ; dist = floor(sqrt(dx²+dy²))
base = 32 ; 64 if the launcher's race owns Missile Guidance System
chance = dist ≤ base ? 100 : max(0, 100 − (dist − base)·100/160)
```

(per-race blueprint byte stride 0x26, GOG `0xc558 + 0xf`; races ≥ 9 never
get the 64.) Own asteroid → fixed 100. The guidance blueprint therefore adds at
most 20 percentage points, not a multiplicative "+25 %".

| dist | base 32 | base 64 |
|---|---|---|
| ≤ base | 100% | 100% |
| 64 | 80% | 100% |
| 96 | 60% | 80% |
| 128 | 40% | 60% |
| 160 | 20% | 40% |
| 192 | 0% | 20% |
| ≥ 224 | 0% | 0% |

## The missile weight table (report "Total yield")

S@0x919EC (`0xb9e8`): 18 signed words indexed by missile id:

| id | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 | 16 | 17 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| weight | 1 | 3 | 5 | 7 | 25 | 20 | 100 | 100 | 0 | 255 | 50 | 150 | 150 | 20 | 50 | 100 | 50 | 30 |

Roles: each arrival adds the weight of the missile's id to a per-(attacked
owner type, attacking race) tally word (`0xc9c8 + owner·0x208 + race·2`; the
mirror "outgoing" array sits 30 bytes earlier, `0xc9aa`), and the sum over the
missiles in flight at an asteroid (`0x20d44`) feeds the launch report's "Total
yield" (**I**). When an alien race's outgoing tally against a human target
exceeds 24575, each of its arriving Vortex missiles has a 1-in-200 chance to be
turned into a type-12 (Meat-Eater) shot instead (C@0x1FEE6…0x1FF32). The weight table is the
best available yield scale: Explosive 1 … Mega 255, Bug Hunter / Meat-Eater
150; it is **not** a damage-in-HP value (the damage values are the table above).

## Worked examples

**Explosive fired by a human race.** Blast damage 10, radius² 4: every
structure whose centre lies within 2 cells of the impact loses 10 HP. A
Solar Panel (5 HP) or Landing Pad (5 HP) is destroyed; a Mine (20 HP) drops to
10; a Weapons Factory (24 HP) to 14.

**Nuclear.** Damage 7 then 5 inside 20 cells: 12 HP total to everything in the
disc, plus the cone's burn mark (state −10: another ~10 HP over ten structure passes with
20 % per pass spread). Only structures with more than ~22 HP in total survive
(before halving by a screen).

**Vortex.** One no-roll walker (4–12 ticks, 2 HP/tick) and, through the
spawner state, a rolled walker (50–98 ticks, 4 % successor chance per tick).

**Strike chance.** As the table above; 32 units out is certain, 112 units out is
50 % for an unguided launcher.

## What is still unknown

- (Resolved 2026-10-18: race ids 9..14 are Rigellian, Braccatia, Mikotaj,
  Artemia, Mauna, Achaean.)
- The source of the cone facing / inner-radius bytes for Napalm and Hellfire
  (inherited from the node), and the exact impact-cell choice (made by the
  event stage, `0x14084`).
- The AMP (anti-missile pod) interception — the text says accuracy improves
  with more pods, but no table or code reading the pod count was found in
  this machine — and the unit of the Stasis / Virus timers in game days.
- Alien-special ids 13–17: the record id is certain, the text names
  (Detonator … Comms Killer) are not mapped to ids.
- The ISO build's values were not re-read (ISO flat absent); they are expected
  to be byte-identical (shifts above).

## References

- `docs/mechanics/weapons.md` — firing pipeline, homing, live chain.
- `docs/mechanics/weapon-and-turret-numbers.md` — the address-base campaign and
  the corrected tables list.
- `docs/mechanics/weapon-config-table.md` — the sprite descriptor table
  (not a stat table).
- `docs/mechanics/stat-tables-design-sheet.md` — section 4 (missiles) with the
  same values in designer form.
- `docs/mechanics/building-stat-table.md` — structure hit points and footprints.
- `docs/mechanics/rng.md` — `rng_next(range)` returns `[0, range)`.
- `build/flat/gog_disasm.txt`, `build/named/FRAGILE.EXE.gog.flat/decompiled.c`
  — `combat_radius_effect` 0x1f934, `combat_cone_effect` 0x1f9e4,
  `obj_spawn_child` 0x1fbc4, the handler family 0x20094…0x20b54,
  `race_stat_percent` 0x20cb4, `construction_timer_tick` 0x1adb4 (the burn
  tick, despite its name), `ui_update_list_header` 0x392d4.
