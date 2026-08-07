# Turrets and colony defence

Status: **behaviour confirmed** (the game's own text resources) and the
reference-build code architecture for the defence state machine **confirmed**
(static disassembly + the partial decompiled export of the reference ISO flat,
`build/decomp/FRAGILE.EXE.flat/decompiled.c`). The per-turret **numeric
stats — damage, exact range, fire rate, power use — are NOT yet extractable**:
the per-type stat tables hold code-like bytes in the flat (the "tables in
code" anomaly already documented for the GOG build in
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
| 0xa6b8 | 3 | byte | base hit points at creation (with the `+0xa` modifier) |
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
