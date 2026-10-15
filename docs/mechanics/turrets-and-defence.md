# Turrets and colony defence

Status: **behaviour confirmed** (the game's own text resources) and the
reference-build code architecture for the defence state machine **confirmed**
(static disassembly + the partial decompiled export of the reference ISO flat,
`build/decomp/FRAGILE.EXE.flat/decompiled.c`). The colony weapon **fire gate
("hit" formula) is now CONFIRMED in both builds** (see "The colony weapon
fire gate" below). The per-type **HP / state / cost table is now READABLE
static data in both builds** (see `docs/mechanics/building-stat-table.md`).
The per-turret **numeric stats — damage, exact range, fire rate, power use —
are NOT yet extractable**: the per-type stat tables hold code-like bytes in
the flat (the "tables in code" anomaly already documented for the GOG build in
`asteroid-spawning.md`/`ore-and-mining.md`) and are written at runtime, so a
runtime memory trace is still required. See "Open question" below.

Source: game text (`_TEXT/AMERICAN.TXT`) + disassembly of the reference ISO
flat (`build/flat/FRAGILE.EXE.flat`). Addresses are image-relative (base 0).

## The defence buildings

The game's own building name list (AMERICAN.TXT, pipe-delimited token table;
index is the 0-based position in that list) gives the Terran defensive
buildings:

| text index | building | role |
|-----------|----------|------|
| 3 | Anti-Missile Pod | "Defensive weapon that automatically targets incoming missiles." |
| 9 | Satellite Silo | spy-satellite launcher (the code tests this type for the anti-missile/silo path, see below) |
| 10 | Screen Generator | shield: "Generates a protective screen around several neighboring buildings" |
| 14 | Missile Silo | "Capable of launching any type of missile" |
| 17 | Plasma Turret | "A weapon of greater devastation than a laser turret. Efficient on power use too." |
| 18 | Photon Turret | "The best energy weapon available at this time. Fires photon packets capable of devastating armor." |
| 27 | Laser Turret | "A general purpose, auto tracking, defense turret." |
| 28 / 33 | Solar Matrix / Protected Storage Tower | carry an **integral Laser Turret** ("Protected by a weapon turret.") |

Alien equivalents (all named in the text):

| race | building | tier |
|------|----------|------|
| Braccatian | Fire Power | ≈ Plasma Turret, "slightly more efficient, both in terms of actual fire-power and in terms of accuracy... possibly the most accurate turret weapons in the universe" |
| Mikotaj | Merl / Na-Shrekn | ≈ Plasma / ≈ Photon |
| Artemian | Star Bars / Auto-deterrent / Super-deterrent | ≈ Anti-Missile Pod / turret "having the lowest range and firepower of all Artemian weapons" / ≈ Photon |
| Maunid | Stun Tower / Power Tower | ≈ Laser ("basic colony defense facility") / ≈ Photon "but more deadly" |
| Achaean | Asteroid Shield / Defense Battery | shielding / defensive battery (role details unconfirmed) |

The internal building type byte (structure node `+0x8`) indexes the per-type
tables below. Its mapping onto the text index is **partially confirmed only**:
the code tests `type == 9` for the satellite-silo path (matches the text
index) and `type == 8` for a child-launching path (text index 8 is the Mine —
either the mapping is not the text order, or the type-8 path is mine-deposit
placement; unresolved). Do not assume text index == type byte.

## How turrets fire (game text)

Quotes from AMERICAN.TXT; all three turret descriptions follow the same
template, differing only in the power/range/damage wording:

- **Auto-fire, motion detection**: "A standard motion-detection sensor
  automatically begins to track any hostile ships as soon as they fire on the
  colony. The turret will then return fire at standard range" (Laser, Plasma;
  Photon: "sophisticated motion-detection sensor... return fire at an
  optimized range").
- **Power requirement**: "assuming that it has sufficient power to do so" — a
  turret without power does not fire.
- **Weapons Factory requirement**: "Other defensive structures such as Laser
  Turrets will not function unless there is a Weapons Factory to maintain and
  supply them."
- **Damage ordering**: Photon > Plasma > Laser ("the greatest fire-power of
  the three turret types", "greater fire-power than the standard Laser
  Turret", "the most basic of colony defenses, this low-powered weapon").
- **Range ordering**: Laser/Plasma = "standard range"; Photon = "optimized
  range" (longer). The Artemian Auto-deterrent has "the lowest range and
  firepower".
- **Turret Optimizer** (Sci-Tek blueprint): "doubling the damage of all
  existing and future turrets... increasing the firepower of each shot by a
  factor of two" — applies to every turret type, retroactively and to future
  builds.
- **Anti-missile defence**: "This turret will attempt to knock out incoming
  warheads before they reach the asteroid." (Anti-Missile Pod; the Artemian
  Star Bars are the same building.)
- Turrets are immobile by definition ("a warship moves pretty damn fast,
  whereas a turret is by definition immobile").
- Fleets do not fight to the death: the player sets a "retreat level" — "the
  percentage of the fleet that must be destroyed in combat before that fleet
  will retreat".

## Code architecture (reference build)

### Structure (building) node

A building on the asteroid surface grid; every structure sits in the
asteroid's `+0x8` list and has a field at `+0xc` (set to `FUN_0001be0`, a
`ret` stub, at creation, 0x1a650 — so the per-structure callback in
`FUN_00001404` is a no-op for regular buildings; silos reuse `+0xc` as the
head of their missile-children list). The specialised defence paths are
dispatched elsewhere — the defence update `FUN_0001c2f4` has **no direct
callers** and is reached indirectly. Fields used by the defence code (offsets
relative to the node):

| offset | role |
|--------|------|
| +0x8 | building type byte (indexes the per-type tables) |
| +0x9 | current hit points (base from table `0xa6b8`, `+10` in one creation path) |
| +0xa | state byte at creation (0/1/4/table `0xa6b9`); the defence code loads the **u16 range** here from table `0xb244` — same field, low byte |
| +0xc | callback pointer (stub `0x1be0`) / silo child-list head |
| +0x14 / +0x15 | surface-grid position (x, y) |
| +0x18 | current target pointer |
| +0x1c / +0x30 | 5-slot order arrays (cleared by the stand-down) |
| +0x38 / +0x3c | object X/Y position, 16.16 fixed point (used by the range gate) |
| +0x4e | flags word (`>>8` bit 4 = the armed/combat flag used by the defence paths) |
| +0x4f / +0x52 | behaviour state bytes (the latter re-armed from table `0xb247`) |

### Per-type tables (all "tables in code" — see open question)

| address | stride | field | role |
|---------|--------|-------|------|
| 0xa6b8 | 6 | byte | base hit points at creation (with the `+10` bonus when the race byte at `race*0x26+0xcc3a` is positive); the table is **static data** in both builds — see `building-stat-table.md` (GOG flat 0x8FFD4 / ISO flat 0x986BC, byte-identical) |
| 0xa6ba | 1 or 6 | u16 | build cost in credits (paid from the per-race fund at `0xc458`); the **live** construction-UI check reads `[type*2 + 0xa6ba]` (0x8a87), the creation path reads `[type*6 + 0xa6ba]` — conflicting strides, unresolved (see `weapon-and-turret-numbers.md`) |
| 0xaade | 1 | signed byte | per-type power/maintenance contribution (subtracted from the colony power value `+0x12a`) |
| 0xb244 | 0x14 | u16 | defence range; stored at node `+0x0a` (`>> 2` in the arming path of `FUN_0001c2f4`) |
| 0xb247 | 0x14 | byte | behaviour state byte re-armed into node `+0x52` |
| 0xb251 | 0x14 | byte | building category byte (tested `== 7` in the destruction path) |
| 0x386d4 | 0x14 | bytes | footprint width/height (surface-bitmap painter `FUN_0002fd34`: `(1<<w)-1` bits per row, `h` rows) |
| 0xa4ac | 0xc | 6 fields | **ship** hardpoint weapon table: callback fn `+0`, race-mask `+4`, mode byte `+8` (`-1` = disabled), fire-delay byte `+9` (reloads the slot countdown), flag `+0xa` |

### Defence state machine

- `FUN_00001404` (main state 3, "structure update") walks every asteroid's
  `+8` structure list and calls each structure's `+0xc` callback.
- `FUN_0001c2f4` — the defensive-structure update (indirectly dispatched):
  - type-8 path: (re)places the structure's child objects on the surface
    with RNG-jittered positions clamped to the map bounds (silo-launch or
    mine-deposit placement — which one is unresolved);
  - type-9 (satellite/anti-missile) and armed-flag paths: stand-down via
    `FUN_0001bdd4`;
  - default path: arms the structure (`+0x52 = 1`), loads its range from
    table `0xb244` (`>> 2`) into `+0x0a`, then checks the target pointer
    `+0x18`: no target, or distance-squared beyond range squared → stand down
    (`FUN_0001ddc4` clears target and orders); in range → the firing
    resolution continues in the (unrecovered) caller.
- `FUN_0001ddc4` — stand-down: clears the 5-slot order arrays, the target
  pointer and the range value.
- `FUN_0001e934` / `FUN_0001c494` — re-arm/refresh: reload node `+0x0a`
  (range) and `+0x52` (behaviour) from the tables; the type-8 case also
  refreshes the children.

### The attack flow

- Fleets attack through the race-attack functions (`race_attack_launch`,
  `race_attack_tick`; GOG addresses 0x17e24/0x17f34 — the reference build's
  equivalents sit in the same region) and the combat cluster 0x14000..0x15000:
  order lists at `+0x38` with per-order type/timer fields, weapon slots per
  race at `0xcdd4` (stride 0x28, 10 slots), targeting
  (`FUN_0004a374`/`FUN_0004a3b4`), and the fire resolution `FUN_00014384`
  (reloads the slot countdown from weapon-table `0xa4b5`, i.e. `+9`).
- Ship weapons use the `0xa4ac` table (stride 0xc; see above).
- The fleet tick `FUN_00053474` (0x53474) runs every tick from main's tail:
  ship list at `0xc41c`, per-ship data at `+0x3d0`, combat-flag gates, and
  the missile/weapon slot accounting. `rng.md` already flags the
  0x49000..0x54000 block ("combat/damage rolls") as the next candidate for a
  dedicated mechanics doc.

## The colony weapon fire gate — the "hit" formula (2026-08-13)

Every colony defence weapon — the turret and missile-silo shot paths — shares
one **per-tick fire gate** that runs before the weapon's countdown is even
touched. It is identical in both builds (ISO fire tick 0x9b3e, gate rolls at
0x9c03/0x9c8e/0x9f78/0x9fcf/0xa000; GOG fire tick 0x99c4, gate rolls at
0x9a89/0x9b14/0x9dfe/…; GOG `rng_next` = 0x5894a):

```
accuracy = colony_record[+0x1c]                ; signed byte
if (rng_next(100) >= accuracy) {               ; the gate
    countdown = 0;                             ; failed gate: primed for a snap shot
    return;
}
countdown -= 1;
if (countdown == 0) { fire shot; countdown = 15; }
```

- **The accuracy byte** (`+0x1c`) lives on the **colony record** (the
  per-race colony slot; pointer cached in `g_cur_colony` 0x5bf78, written at
  0x9bbd), *not* on the structure/turret node. The fire tick walks the
  asteroid object list (0xc3f4) for that race's colony object, looks the
  colony record up by kind (`+0x14d` vs record `+8`) and reads the byte from
  there.
- **Initial value** = the per-colony-kind maximum, loaded from byte table
  `0x9d78` (ISO) / `0x9690` (GOG), stride 0x1c (init at ISO 0x7c51; GOG init
  0x7ac1, per-kind record init loop at GOG 0x7543 creates 16 records of
  stride 0x28 with `+0x1c` = accuracy).
- **Drift** (once per colony tick, inside the growth tick — ISO 0x856e / GOG
  0x83ee): if the colony's growth value `+0x18` is **above** the per-kind
  threshold dword table `0x9d68` (ISO) / `0x9680` (GOG) the byte falls by 1
  (floor 0); otherwise it rises by 1 (ceiling = the max table). The growth
  percentage kept at `+0x17` is `min(100, growth*100/12000)`. So a colony
  under growth pressure loses weapon accuracy; a relaxed one regains it.
- **Countdowns**: three slots — `+0x1b8`/`+0x1b9`/`+0x1bb` (ISO; GOG
  `+0x1a8`/`+0x1a9`/`+0x1ab`), each re-armed to **15** (0xf) ticks after
  firing (ISO 0x9c2f/0x9d43/0x9d90/0xa02c); another path re-arms 40 (ISO
  0x118b8, GOG 0x115a4). The shot spawner is 0x4b584 (ISO) / 0x48e64 (GOG),
  called with the per-path launcher-context globals (0x3a250/0x3a254,
  0x3a290/0x3a294, 0x3a588/0x3a58c); the owner-must-be-player check precedes
  the spawn.
- **Failed-gate semantics**: a failed roll zeroes the countdown, and the
  fire test is `countdown == 0` *before* the decrement — so after any
  failed gate the next passed roll fires immediately (a "snap shot" after
  the tracking lock is regained), while a steady lock fires every **16**
  ticks (15 charge ticks, then the fire tick). Net effect: fire interval
  ≈ 16 ticks at accuracy ≥ 100; at mid accuracy (~50) the snap-shot path
  dominates and the weapon fires roughly every few ticks; at accuracy → 0
  it nearly stops. An accuracy byte of 255 (signed −1) disables the gate
  entirely (never fires).
- **Fire rate in game time**: the steady 16-tick cycle at full accuracy is
  **half a game day** at the default game speed — one game day ≈ 32
  main-pass ticks (see `main-loop.md`, "State cadence and the game day"; the
  day length scales with the game-speed index, unconfirmed). So a fully
  accurate colony defence weapon fires about **twice per game day**. The
  tick→seconds rate is host-dependent, not a code constant: roughly
  0.2–0.3 s per 16 ticks on a standard DOSBox VGA setup (≈60–70 passes/s,
  estimate).
- **Rare event**: when the accuracy byte is below 5, a second roll
  (`rng_next(100) < 5`) each tick triggers a 27-way table pick
  (`rng_next(27)` → byte table 0x9f64 ISO / 0x987c GOG) into an
  effect/message call (0x8a24 ISO / 0x88a4 GOG).
- **Still runtime-only — and the "flat addresses" are obj-relative, not
  flat offsets (correction 2026-08-29).** The reader instructions' displacements
  (`0x9d68`/`0x9d78`/`0x9d7a`/`0x9d7c` ISO, `0x9680`/`0x9690`/`0x9692`/
  `0x9694` GOG) are **per-object offsets**, not image offsets: the loader
  relocates them onto the DOS/4G data object, and the flat bytes at those
  offsets are live code (the fire-tick / colony-tick functions), so reading
  the flat there yields opcode bytes, not table values. The **GOG runtime
  addresses** are pinned from the relocated loaded image
  (`build/flat/FRAGILE.EXE.gog.runtime.bin`) and verified against the live
  memdump (image at dump offset 0x1c901c): data object `obj3` base
  `0x24E000`, so the per-kind stride-0x1c record block sits at guest
  `0x257680` (`obj3 + 0x9680`): threshold dword `+0x00`, a second dword
  `+0x0c`, max-accuracy byte `+0x10` (`0x257690`), ai-factor byte `+0x12`
  (`0x257692`), and another byte `+0x14` (`0x257694`). The ISO build uses the
  same scheme but its data-object base is not yet known (no ISO memdump).
  The values are still runtime-written: no captured dump (all "main-menu
  status", even the colony-view / Ship-Yards dumps) has the block
  materialised — the flat's obj3 content there is a table of relocated code
  pointers. A fresh dump from a **running game** (colony view after a new
  game is started) read at guest `0x257680` + kind·0x1c decodes the real
  per-kind thresholds and max accuracies. The mapping colony-kind ↔ game
  name is also still open.

### Worked examples

The gate and countdown for one weapon slot, tick by tick (`r` = the
`rng_next(100)` roll, `C` = the slot countdown; the weapon fires when the
roll passes and `C` was 0 before the decrement):

**Accuracy ≥ 100 (full lock).** Every roll passes (r < 100 always). After a
shot the countdown is 15, so the weapon charges for 15 ticks and fires on
the 16th — one shot per 16 ticks, forever. At spawn the countdown starts at
0, so the first shot comes on the very first active tick.

```
tick:  1   2   3   …  15  16      (after shot C=15)
roll:  <A  <A  <A  …  <A  <A
C:     15  14  13  …  1   0→fire, C=15
```

**Accuracy 255 (signed −1).** `r ≥ −1` holds for every roll, so the gate
always fails: the countdown is repeatedly zeroed but the weapon never
fires. A colony kind whose table maximum is 0xff has its weapon effectively
switched off.

**Accuracy 50 (erratic).** Half the rolls pass. After a shot, the first
failing roll (expected after ~2 ticks) zeroes the countdown, and the next
passing roll (expected ~2 ticks later) fires immediately — a snap shot.
Expected interval ≈ 4 ticks, *faster* than full accuracy, because the
weapon discharges on every re-lock:

```
tick:  1     2     3     4
roll:  pass  fail  pass  —
C:     15→14   →0   0→fire, C=15     (fire 3 ticks after the previous
                                      shot; on average ≈ 4)
```

**Accuracy 5 (near-blind).** 95% of rolls fail. After a shot the countdown
is zeroed almost immediately; the weapon then waits ~20 ticks for a passing
roll to fire (expected interval ≈ 21 ticks). While the byte sits below 5,
every tick also rolls the 5% rare event, which picks one of 27 effects via
`rng_next(27)` — roughly one extra event per 20 ticks of combat.

**Accuracy 0.** The gate never passes; the weapon never fires.

**Drift scenario (placeholder numbers — the real tables are runtime-only).**
Suppose a colony kind's tables read max accuracy 104 and growth threshold
5000. With growth at 3000 the byte climbs 1 per tick to its 104 cap: the
gate always passes and the weapon fires on the steady 16-tick cycle. An
attack pushes growth to 7000: the byte now falls 1 per tick, and the
weapon slides from steady fire (≥100) through the erratic snap-shot regime
(~50, a shot every few ticks) down toward near-silence (≤5, a shot every
~21 ticks plus rare events). The transition is gradual — one accuracy point
per colony tick in either direction.

## Open question: the per-turret numbers

The **damage values (and exact range/fire-rate/power numbers) per turret are
not yet known**. Why:

- The per-type stat tables (`0xa6b8`, `0xa6ba`, `0xaade`, `0xb244`, `0xb247`,
  `0xb251`, `0x386d4`) sit in regions of the flat that decode as instructions
  — the "tables in code" anomaly — and **no code writes them**, so the flat
  bytes are not the runtime values and static extraction fails. This is the
  same situation `ore-and-mining.md`/`asteroid-spawning.md` describe for the
  GOG build; it applies to the reference build as well.
- The current build artifacts are additionally degraded: `build/decomp/…/
  decompiled.c` is a partial export (1,546 functions; even
  `structure_update_tick` from `main-loop.md` is missing). `build/flat/
  full_disasm.txt` (regenerated 2026-08-07 alongside `fragile.o`) now matches
  the current flat byte-for-byte and covers the whole image including gap
  code, but the full GOG export the rename map was built on is no longer in
  `build/`, and the GOG binary is not in this workspace.

Resolution paths (both deferred):

1. **Runtime memory trace** (the repo's deferred plan): run the game under a
   DOSBox-X debug build until an enemy attack fires on a colony, then read the
   in-memory tables at the addresses above — the values are written at
   startup/load. This also settles the type-8 path and the type-number
   mapping.
2. **Re-import the GOG flat** into Ghidra (the rename map already names the
   GOG-side combat functions) and read the weapon/structure code there.

## References

- `_TEXT/AMERICAN.TXT` (the pipe-delimited token table: building names and
  descriptions — the Terran building name list starts at 0x1107F with
  "Living Quarters", "Laser Turret" at 0x111FD; the Anti-Missile Pod
  description at 0xDE81).
- `build/named/FRAGILE.EXE.flat/decompiled.c` — named view of the partial
  export; `FUN_00001404`, `FUN_0001c2f4`, `FUN_0001ddc4`, `FUN_0001e934`,
  `FUN_0001c494`, `FUN_00014384`, `FUN_0001a4b4` (structure creation),
  `FUN_00053474` (fleet tick).
- `config/ghidra/rename-map.json` — GOG-side combat names (`race_attack_*`,
  `weapon_*`, `combat_*`) whose reference-build addresses are not yet mapped.
- `docs/mechanics/main-loop.md`, `docs/mechanics/rng.md` — the tick
  dispatcher and the RNG call-site census (combat block 0x49000..0x54000).
- The fire gate: ISO `build/flat/full_disasm.txt` 0x9b3e..0xa071 (rolls at
  0x9c03/0x9c8e/0x9f78/0x9fcf/0xa000, growth drift at 0x856e, init at
  0x7c51, tables 0x9d68/0x9d74/0x9d78, 40-tick re-arm 0x118b8); GOG
  `build/flat/gog_disasm.txt` 0x99c4..0xa0c8 (rolls at 0x9a89/0x9b14,
  drift at 0x83ee, init at 0x7adc, tables 0x9680/0x9690).
