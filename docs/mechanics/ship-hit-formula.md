# Ship hit formula: what makes a shot hit

Status: **mechanics confirmed** by static disassembly of both builds (the
Interplay CD reference flat `build/flat/FRAGILE.EXE.flat` and the GOG retail
flat `build/flat/FRAGILE.EXE.gog.flat`). The per-race numeric stat bytes that
the rolls compare against remain runtime-only (see "What is still unknown").
This note overturns the earlier "the 0x200e4-family combat tick is
unreferenced/stale" conclusion in `weapons.md` and
`weapon-and-turret-numbers.md`: the family **is** the live combat machine —
it is dispatched through runtime-filled pointer tables, which is exactly why
no static callers exist. The GOG build proves it: the same machine is
present there, and it is reachable from the live event handler.

## The three hit models

There is no single "hit formula". Ship fire resolves in three different ways
depending on what is firing:

| model | used by | roll? |
|---|---|---|
| **arc/radius sweep** | hardpoint beam weapons (Laser, Photon, Plasma, …), turrets | no roll — everything in range & arc is hit |
| **strike roll** | the rolled sub-shots of the surface combat machine | per-tick roll vs a per-race byte |
| **direct hit** | heavy/direct shots of the same machine | no roll — damage every tick |

The **missile targeting percentage** the player sees ("Strike chance: %d%%"
/ the fleet panel "Strike Rate") is none of the above — it is a pure
distance estimate (confirmed earlier; restated below because it is the
number the player experiences).

## 1. The arc/radius sweep (hardpoint weapons, dogfight)

The per-tick weapon handlers sweep the target's child list (ships and
buildings on the asteroid surface) and mark everything inside the weapon's
reach:

- **radius sweep** `1f934` (GOG) / the ISO `1fd34` helper: a child is hit
  when `(dx² + dy²) ≤ range²`, where `dx`/`dy` are the child-centre offsets
  from the shot position in whole cells (child cell coords + half its
  footprint from the `0x36274`/`0x36275` — GOG — or `0x386d4`/`0x386d5` —
  ISO — per-type footprint tables).
- **cone sweep** `1f9e4` (GOG) / `1fde4` (ISO): same distance test, plus an
  arc test. The bearing from the launcher to the child must fall inside the
  window `[facing − 0xa0, facing + 0xa0]` (byte angles, full circle 256 →
  a 225°-wide window: only a 135° blind cone behind the firer misses).
  Children closer than the inner radius `(launcher +0x1f byte · range²) >> 6`
  are hit **without** the arc test.
- A hit sets the child's `+0xb` state byte to `5` (or `0xf6` for non-turret
  categories — the per-type category byte `0xb3be[type*16]` (GOG) /
  `0xba8a[type*16]` (ISO) decides) and applies the weapon's damage to the
  child's hit points via the damage helper (`1aa94` GOG / `1adb4` ISO).

**The ranges are per-race runtime bytes** — the sweep handlers index
`0xb960`/`0xb96f`/`0xb97e`/`0xb98d`/`0xb99c` (GOG; ISO `0xc02c`/`0xc03b`/
`0xc04a`/`0xc059`/`0xc068`) by the shot's `+9` field (the attacked object's
owner race). Values unknown statically (see below). The generic sweep damage
is **5** (`mov $5,%ebx` before the damage call at ISO `1ff3d`); the GOG
direct-hit handler uses **120**.

So a dogfight weapon either hits everything in its cone or nothing: there is
**no accuracy roll**. The player-side difficulty is positional (getting the
enemy inside range and in front).

## 2. The strike roll (surface combat machine)

The combat shot node (type byte `+8` = 5) is spawned by `combat_shot_spawn`
(ISO `1ffc4`) / `obj_spawn_child` (GOG `1fbc4`) — the two are verbatim the
same code. The node stores the attacked object at `+0x10`, the attacked
object's owner race at `+0x9`, the launch X/Y at `+0x18`/`+0x1a`, and a
**strike-roll flag** at `+0x14` (word):

- spawned with the 4th argument 0: `+0x14` = **0** — the shot **rolls**;
  its lifetime byte `+0xa` = `(rng_next(0xb9d8[race]) + 0xb9d8[race]) * 2`
  (GOG; ISO reads `0xc0a4` — a per-race speed base, doubled);
- spawned with the 4th argument ≠ 0: `+0x14` = **1** — the shot never
  rolls; lifetime = that byte + `rng_next(6)`.

The live chain: the event handler (ISO `0x52b74` event type 4, reachable
from the fleet order queue `0x51664`) spawns the first shot with
`(4 + rng_next(4))` — i.e. **no roll**, lifetime `4 + rng_next(4) +
rng_next(6)` = 4–12 ticks: the missile impact itself. The sub-shot spawner
handler (ISO `0x20774` / GOG `0x20324`) spawns follow-up shots with argument
0 — these are the **rolled** shots (the Scatter-missile-style
sub-munitions).

The per-tick strike handler (ISO `0x207a4` / GOG `0x20354`, gated by a
combat-enable global `0x36b69` ISO / `0x34725` GOG — the map names the GOG
byte `g_fleets_enabled`, semantics plausible-but-unconfirmed):

```
target.state = 10                       ; mark attacked object "under attack"
if --lifetime == 0: free the shot
if (shot.flags_roll == 0) {              ; +0x14 word
    if (rng_next(100) < strike_byte[shot.race]) {   ; shot.race = +0x9 = attacked race
        spawn the impact shot (lifetime byte from +0xa, no further rolls)
    }
}
cell = cell_scan(target, shot.x, shot.y) ; 1aea4 ISO / 1ab84 GOG
if (cell found) damage(cell, 2)          ; 2 HP to whatever occupies the cell
shot.x += offset_x[rng_next(8)]          ; random walk: 8 signed offset pairs
shot.y += offset_y[rng_next(8)]          ; (0xc100/0xc101 ISO, 0xba34/0xba35 GOG)
```

So the 2-HP cell damage happens **every tick** while the shot sits on an
occupied cell — the strike roll does not gate the damage. What it gates is
whether the shot **spawns a successor**: with probability `strike_byte /
100` per tick (`strike_byte` = the per-race byte at `0xc095` ISO / `0xb9c9`
GOG, indexed by the attacked object's owner race; `rng_next(100)` returns
0..99, see `rng.md`), the shot spawns a no-roll successor at its own
position with lifetime `parent + rng_next(6)`, so the attack chains on. The
effective "hit or miss" of the attack is therefore two-fold: spatial (the
shot's random walk must keep it over occupied cells — the `cell_scan` find
is the hit test) and temporal (the strike byte sets how likely the effect
is to persist past each tick). The chain ends when a shot's lifetime runs
out without a successful roll.

## 3. The direct-hit path

A sibling handler (GOG `0x20854`, gated by the global `0x34724`, map name
`g_ai_economy_enable` — unconfirmed) runs the same per-tick body **without
the roll** and with damage **120** (`mov $0x78,%ebx`). The same machine also
has a 25 % gate in **both** builds (ISO `0x20b94`/`0x20be4`, GOG `0x20794`):
the handler posts the attack event on the target (`0x14174` ISO /
`0x13e74` GOG, gated by the per-type race-mask word of the weapon table),
then rolls `rng_next(100) < 0x19` and only on a pass runs the bookkeeping
call (`0x44584` ISO / `0x42114` GOG, recorded only when the attacker is the
player and the target is an alien race) — i.e. the 25 % gates a diplomatic
record, not the hit itself.

## The aim-spread computation (flight handler)

The flight handler (ISO `0x200e4`/`0x20234`, GOG twins `0x1fce4`/`0x1fe34` —
verbatim the same code) computes the shot's random aim error from geometry
each time the approach-roll passes:

```
roll = rng_next(101)
if roll <= shot.lifetime:  → shot enters its end state
dx = (target.x − launcher.x) >> 16        ; whole units
dy = (target.y − launcher.y) >> 16
dist = round(sqrt(dx² + dy²))
s = dist − (launcher_speed_byte + target_speed_byte)    ; both +0x50 bytes
c = min(s, 160) − 32
x = c / 3                                  ; signed division
shot.lifetime = (rng_next(x) + rng_next(x) + rng_next(x) + 32) / 3
```

The lifetime byte doubles as the aim-spread parameter the strike handler
uses when spawning the impact. The exact flight/homing loop this feeds is
documented in `weapons.md` (homing steer ±8 byte-degrees per tick); the
spread-to-trajectory mapping is not fully pinned (see open questions).

## The missile targeting percentage (what the player sees)

Unchanged from `weapons.md` (confirmed): the targeting dialog's
"Strike chance" and the fleet panel's "Strike Rate" header value
(`ui_update_list_header`, GOG `0x392d4`, calls `race_stat_percent`
`0x20cb4` / ISO `0x21104`):

```
dist = 2-D distance between launcher and target (whole units, Z ignored)
base = 32  (64 if the launcher's race owns the Missile Guidance System
            blueprint — per-race blueprint byte, ISO 0xcc43 / GOG 0xc567)
chance = dist ≤ base ? 100
       : max(0, 100 − (dist − base) * 100 / 160)    ; integer division
```

Own asteroid → fixed 100 (the header special-case). 0 % at 192 units
(224 with guidance). This is an estimate of the missile's chance to arrive;
the impact itself always hits (see section 2: the first shot is spawned
without the roll flag).

## Worked examples

### The displayed strike chance

`chance = max(0, 100 − (dist − base)·100/160)` with `base` 32 (64 with the
Missile Guidance System), integer division:

| dist | base 32 | base 64 |
|---|---|---|
| ≤ base | 100% | 100% |
| 48 | 90% | 100% |
| 64 | 80% | 100% |
| 80 | 70% | 90% |
| 96 | 60% | 80% |
| 112 | 50% | 70% |
| 128 | 40% | 60% |
| 144 | 30% | 50% |
| 160 | 20% | 40% |
| 176 | 10% | 30% |
| 192 | 0% | 20% |
| 208 | 0% | 10% |
| ≥ 224 | 0% | 0% |

Practical reading: attacking a near neighbour is effectively free of
misses; from ~112 units out every second missile is expected to fail; past
192 units (without guidance) no missile is expected to arrive at all.
Own-asteroid targets force 100 regardless of distance.

### The arc window and the blind cone

`[facing − 0xa0, facing + 0xa0]` in byte angles (256 = full circle) = a
**225° window**; the uncovered 135° sector is directly behind the firer.
So a beam weapon can never hit anything behind its ship, and the facing
test is dropped entirely inside the inner radius
`(launcher +0x1f · range²) >> 6` — a ship sitting on top of the firer is
hit no matter which way it points.

### The fire gate

`rng_next(100) < 30` → on average one launch per 100/30 ≈ 3.3 eligible
ticks (the bearing window `[0x0c, 0x2b)` can push the interval out). A ship
carrying 30 missiles and staying in firing range for ~100 ticks therefore
empties its hold — the "Missiles At" counter ticks down at the same rate.

### The strike roll and chaining

A rolled shot damages its cell 2 HP **every tick** (spatial test
permitting) and, per tick, with probability `p = strike_byte/100`, spawns a
no-roll successor with lifetime `parent + rng_next(6)`. A shot with
lifetime `L` therefore deals `2L` HP itself and an expected
`2·L·p·(L+3)` HP through its successors (each of the L ticks can trigger a
successor worth 2·(L+3) HP on average, spatial test permitting). The strike
byte is runtime-only, so `p` is illustrative: at `p = 0.5` and `L = 20` the
shot itself deals 40 HP and the expected successor damage is
`2·20·0.5·23 = 460` HP — the roll is what turns a short-lived shot into a
sustained attack. (With `p = 0` the attack always ends with the first
shot's lifetime.)

### The aim spread

`x = (min(dist − speeds, 160) − 32)/3`, then
`lifetime = (rng_next(x) + rng_next(x) + rng_next(x) + 32)/3`:

- `dist − speeds ≥ 192`: clamped — `x = 42`, each roll 0..41, expected
  lifetime `(3·20.5 + 32)/3 ≈ 31` ticks.
- `dist − speeds = 100`: `x = 22`, expected lifetime `(3·11 + 32)/3 ≈ 21`
  ticks.
- `dist − speeds < 32`: `x` goes negative and the three rolls return
  degenerate values — the close-range behaviour of the spread byte is
  garbage/unpredictable (matches the drop-the-aim branches in the fire
  wrapper; see open questions).

## What is still unknown

- **The per-race stat bytes** (strike byte `0xc095` ISO / `0xb9c9` GOG;
  range bytes `0xc02c`… ISO / `0xb960`… GOG; speed base `0xc0a4`/`0xb9d8`;
  scatter count `0xc077`/`0xb9ab`): materialised at runtime only. Neither
  flat shows them as data, no writer with immediate constants was found in
  either build, and none of the captured memdumps (all taken outside combat)
  has them — the earlier "tables in code" negative result stands for the
  values. A dump taken **during** a surface battle is the remaining route.
- The runtime handler-pointer values (`0xbfe4`/`0xbff8` ISO, `0xb918`/
  `0xb92c`/`0xb914` GOG) that fix the state sequence and the per-type
  callback pointers (ISO `0xa4ac`, GOG `0x9dc4`).
- The exact mapping of the flight-handler spread value onto the impact
  position (the random walk already covers the shot position; how much of
  the spread survives into the walk is unconfirmed).
- The precise role of the 25 % gate (`0x20b94`/`0x20be4` ISO, `0x20794` GOG;
  believed to gate a diplomatic bookkeeping record, not a hit — see
  section 3).

## References

- `docs/mechanics/weapons.md` — firing pipeline, homing, the (corrected)
  live chain.
- `docs/mechanics/weapon-and-turret-numbers.md` — the "tables in code"
  campaign and the runtime-table blocker.
- `docs/mechanics/rng.md` — `rng_next(range)` returns `[0, range)`.
- `build/flat/full_disasm.txt`, `build/flat/gog_disasm.txt` — the raw
  disassemblies both regions of this note are read from.
- `build/named/FRAGILE.EXE.gog.flat/decompiled.c` — `combat_cone_effect`
  (0x1f9e4), `combat_radius_effect` (0x1f934), `obj_spawn_child` (0x1fbc4),
  `race_stat_percent` (0x20cb4), `ui_update_list_header` (0x392d4),
  `event_entry_fire` (0x14084), `ship_steering_tick` (0x14a94).
