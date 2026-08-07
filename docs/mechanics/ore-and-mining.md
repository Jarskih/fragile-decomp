# Ore generation and mining

Status: ore **placement**, **reserves** and **extraction** confirmed by static
disassembly of the GOG flat plus savegame dumps; per-type ore **amounts**
read empirically from saves (the per-type tables at 0x9e78/0x9e90/0x9ea8/
0x9ede/0x9eb0, the ore-param tables 0x16644/0xa455, the reserve-roll tables
0x9cf8..0x9cfc and the per-unit value table 0x9cf8 hold code-like bytes in
the flat and are written at runtime — the statically unreadable values were
read from live saves instead). GOG image base 0x85760; addresses below are
image-relative.

## Correction history

Earlier drafts of this file misread several things; the corrected picture:

- The five counter fields `+0x1a4/+0x1af/+0x1b0/+0x1b2/+0x1b3` (and `+0x1b5`)
  are **not** ore amounts and mining does **not** decrement them. They are
  **deposit-respawn timers**: the per-type tick (0x15ce4) decrements each by
  one per tick, and when one hits zero the corresponding helper resets it
  from its per-class table and (re)places an ore-deposit cell.
- The "mining tick at 0x15dde" is not gated on mine buildings. It is part of
  the per-type tick 0x15ce4; the `cmpl 0x7e8xx, %ecx` checks are
  "if global flag [0x7e8xx] != 0" (%ecx is zeroed at 0x15cfa) — scenario-wide
  toggles, not building presence.
- `+0x1bc`/`+0x1c0` are not constants: they are **per-type handler function
  pointers** (loaded from the dword tables 0x9f48/0x9f60, called at
  0x15d3f/0x15d9d as `calll *444(%ebx)` / `calll *448(%ebx)`).
- The "ore amount" fields the earlier doc reported from saves are the
  initial values of those timers (level-1 column, see below).
- The real ore inventory is the **10-word reserve array at `+0x5c`**
  (one word per ore, in the game-text order Selenium, Asteros, Barium,
  Crystalite, Quazinc, Bytanium, Korellium, Dragonium, Traxium, Nexos),
  plus the 16-byte surface-deposit counter array at `+0xc8`.
- Type 0 (unowned) asteroids **do** carry ore reserves from creation (random
  per ore); the earlier "type 0/1 carry zero in all ore fields" observation
  referred only to the timer fields.
- The `+0x1a4` "15 → 18/19" save anomaly is not a regeneration re-roll: it is
  the colony-level byte `+0x19e` changing 1 → 2, which switches the table
  column the timers reset from.

## The ten ores and the three rarity tiers

The game's own text (ENGLISH.TXT) defines ten ores in three tiers:

| tier | ores |
|------|------|
| common | Selenium, Asteros, Barium, Crystalite |
| valuable | Quazinc, Bytanium, Korellium, Dragonium |
| rarest | Traxium, Nexos |

| mine building (Sci-Tek/Terran) | extracts | game text |
|---|---|---|
| Mine | common tier | "seeks out the most common ores - Selenium, Asteros, Barium and Crystalite" |
| Deep Bore Mine | valuable tier | "seeks out the more valuable ores - in this case Quazinc, Bytanium, Korellium and Dragonium" |
| Seismic Penetrator | rarest tier | "seeks out the rarest and most valuable ores (Traxium and Nexos)" — and as a blueprint "will double the output of all your deep-bore mines" |

Faction equivalents: Artemia Advanced Ore Extractor (≈ Deep Bore Mine) and
Rare Ore Extractor (rarest); Mauna Basic / Advanced / Superior Extraction
Units (Advanced ≈ Deep Bore Mine, Superior ≈ Seismic Penetrator); Achaean
Commonbore (common) and Deepbore (rarest).

## Ore reserves at creation — `+0x5c`, 10 words

Every asteroid node carries a **10-word ore-reserve array at `+0x5c`**, one
word per ore, in game-text order (index 0 = Selenium … 8 = Traxium, 9 =
Nexos). Indexing evidence: the reserve-roll generator 0x124f4 and the
extraction loop 0x16b04 index it 0..9; the amounts collapse into the tier
structure (common ores hundreds, valuable tens-to-hundreds, rarest ≤ 15);
and the reserve roll for indices 8/9 is the only one allowed to produce 0
(0x1254e–0x1256d: `if (i < 8) small-roll else 0`).

### How reserves are rolled — reserve generator @ 0x124f4

Called on asteroid creation (hook of `asteroid_create`); also feeds
`asteroid_rank_start_values` (0x2ff04) at the end. For each ore i = 0..9
(14-byte stride in the per-ore table at 0x9cec, runtime-filled):

1. Presence roll: `if rng(100) < word [0x9cec + i*14]` →
   amount roll: `rng(word[0x9cf0 + i*14] - word[0x9cee + i*14] + 1) +
   word[0x9cee + i*14]` (uniform in the per-ore min..max window);
2. else if `i < 8`: `rng(word[0x9cf0 + i*14] / 20) + 1` (small residual);
3. else (i ≥ 8): `0` — the two rarest ores are simply absent.

Per-ore table layout (stride 14, at 0x9cec): word +0 = presence threshold,
word +2 = min amount, word +4 = max amount, word +6 = per-tick extraction
amount (used by the flux ticks 0x34f4/0x35d4), word +8 = faction base value
(used by 0x12594's jitter branch), word +10 = (unused), word +12 = per-unit
value (used by the value converter 0x16b04 and the value score at 0x7d4 —
address 0x9cf8).

Note: the six wild specials (types 9..14) show **identical fixed reserves**
in every save despite different asteroid seeds — they are copied from a fixed
per-class table, not rolled. The exact copy site is not yet identified (it is
not in `asteroid_assign_index`'s wild path, `asteroid_finalize` or the
`asteroid_create` hooks; candidate: a gap helper such as 0x7444/0x74a4 or a
per-type handler).

### Empirical reserve statistics (all unowned type-0 asteroids, 7 saves)

The observed distributions are **bimodal**, exactly matching the two
generator branches (window vs residual `rng(M/20)+1` — the residual maxima
observed, 50/25/25/37, confirm M/20 per ore):

| index | ore | window `[m, M]` | residual `1..M/20` | window share |
|---|---|---|---|---|
| 0 | Selenium | [500, 1000] | 1..50 | ~82% |
| 1 | Asteros | [250, 500] | 1..25 | ~81% |
| 2 | Barium | [250, 500] | 1..25 | ~64% |
| 3 | Crystalite | [250, 750] | 1..37 | ~75% |
| 4 | Quazinc | [1, 116] | — (never fires) | 100% |
| 5 | Bytanium | [1, 116] | — | 100% |
| 6 | Korellium | [1, 100] | — | 100% |
| 7 | Dragonium | [1, 100] | — | 100% |
| 8 | **Traxium** | [2, 15] | 0 (i ≥ 8 branch) | ~34% |
| 9 | **Nexos** | [1, 8] | 0 | ~28% |

So the presence thresholds T are < 100 for Selenium/Asteros/Barium/
Crystalite (the residual branch fires ~18–36% of the time, leaving a small
1..50 residual instead of the full window), ≥ 100 for Quazinc..Dragonium
(never fires), and ~34/~28 for Traxium/Nexos (the i ≥ 8 branch yields 0).
**No zero ever appears for indices 0..7** (both branches give ≥ 1;
0/380 sampled asteroids). This holds at creation only — the reserves
fluctuate afterwards (see "The ore flux" below), so an ore can later be
drained to zero. Earlier drafts of this table reported the mixed ranges
(e.g. "Selenium 3..1000"); the bimodal split above is the correct reading.

### Fixed reserves: the six wild specials and the home asteroid

- **Wild types 9..14 (the six alien-race asteroids)** all start with the
  **same fixed reserves** `[300, 400, 400, 150, 70, 60, 35, 35, 0, 0]`
  (identical across all six types in SAVEGAME.009): Selenium 300, Asteros
  400, Barium 400, Crystalite 150, Quazinc 70, Bytanium 60, Korellium 35,
  Dragonium 35, **Traxium 0, Nexos 0**.
- **Home asteroid (type 1)**: not rolled — the home block (0x11084) copies
  the runtime word table 0x9c9c into `+0x5c` (10 words). The table is filled
  per scenario, so the values vary between the standard campaign and custom
  games, but are fixed within one new game (identical across SAVEGAME.009
  and SAVEGAME.000):

  | game | reserves (Selenium…Nexos) |
  |---|---|
  | standard campaign | 277, 327, 360, 112, 53, 55, 25, 28, **0, 0** |
  | custom large/high | 285, 321, 336, 117, 57, 54, 26, 31, **0, 0** |
  | custom medium/medium | 297, 354, 318, 110, 59, 55, 25, 30, **0, 0** |
  | custom small/high | 267, 303, 300, 104, 56, 51, 28, 28, **0, 0** |
  | custom small/low | 272, 354, 348, 102, 56, 60, 27, 29, **0, 0** |
  | custom small/medium | 252, 330, 345, 107, 50, 52, 28, 30, **0, 0** |

  In every observed save the home asteroid carries **no Traxium and no
  Nexos** (indices 8/9 = 0). The home reserves sit in a much narrower band
  than the unowned rolls (Selenium always 252–297, Asteros 303–354,
  Barium 300–360, Crystalite 102–117, Quazinc 50–59, Bytanium 51–60,
  Korellium 25–28, Dragonium 28–31).
- Reserves are consumed by mining (compare SAVEGAME.009 → SAVEGAME.000:
  type 9 went `[300,400,400,150,70,60,35,35,0,0]` → `[292,388,390,145,67,58,
  35,34,0,0]` while its extraction state bytes turned on).

### Asteroids spawned during play

New asteroids created after game start (the main-loop auto-spawn gate at
0x472, the population keeper at 0xf884, the scenario spawner at 0x13604)
all go through `asteroid_create` (0x117b4), whose hook 0x124f4 rolls the
reserves exactly as at initial creation. The keeper additionally calls
0x12594, which **only re-rolls types 1..8** (faction base ± 20% jitter, or a
copy of an existing faction asteroid); for types 0 and 9..14 it does
nothing, so spawned asteroids of those types keep the 0x124f4 roll.
Empirical confirmation: the type-14 HCC-555, spawned during the
SAVEGAME.009→.000 window, holds `[885,279,10,27,5,5,58,3,0,0]` — rng-rolled,
unlike the fixed reserves of the six initial aliens. So the fixed
`[300,400,400,150,70,60,35,35,0,0]` belongs to the initial-special creation
path only; later wild-type spawns roll their ore like unowned asteroids.

## When ore is generated

At asteroid creation, in the wild path of `asteroid_assign_index` (0x22b94) —
the branch for types 9..14 (0x22ccf):

1. `call 0x18264` (`asteroid_init_by_type` — seam ring offsets).
2. `[0xc6b8] = type - 9` (class index `t`).
3. `asteroid_ore_setup` (0x185d4) + `object_create_on_cell` (0x181b4) run
   **twice**, with per-type parameters `dword [0x16644 + type*12]` (base
   resource) and `dword [0x16644 + type*12] + byte [0xa455 + type]`
   (one deposit per call).
4. `[+0x19e] = 1`, `[+0xc2] = 50`.
5. Timer fields are copied from per-class tables (level-1 column):

| node field | size | source table |
|-----------|------|--------------|
| `[+0x1a4]` | word | `byte [0x9e78 + t*4 + [+0x19e]]` |
| `[+0x1b0]` | byte | `byte [0x9e90 + t*4 + [+0x19e]]` |
| `[+0x1af]` | byte | `byte [0x9ea8 + t*4 + [+0x19e]]` |
| `[+0x1b2]` | byte | `byte [0x9ede + t]` |
| `[+0x1b3]` | byte | `byte [0x9eb0 + t]` |
| `[+0x1bc]` | dword | `dword [0x9f48 + t*4]` (handler pointer A) |
| `[+0x1c0]` | dword | `dword [0x9f60 + t*4]` (handler pointer B) |

The load-from-save path (0x22f14, type assigned to a type-0 node) reads the
same tables via `0x9e54/0x9e5c/0x9e64/0x9ed5/0x9e67/0x9f24/0x9f3c + type*4`
— algebraically the same addresses.

The counter values at creation (level 1, all saves):
`+0x1a4` = 15 (all t), `+0x1b0` = {19,14,15,13,11,17},
`+0x1af` = {62,42,50,35,46,58}, `+0x1b2` = 50 (all), `+0x1b3` =
{140,150,135,145,165,160} per t = 0..5.

## The colony level byte `+0x19e`

`+0x19e` is an **economic level 1..3** (observed 1 = fresh, 2 = colonised
wild, 3 = developed home / some spawned asteroids), written by the value
score function (~0x740): it sums `word [+0x5c + i*2]` weighted by the
per-ore table at 0x9cf8 and compares against the thresholds at 0xbe48/0xbe4c/
0xbe5c/0xbe48+8. It selects a **column** in the timer tables
(0x9e78/0x9e90/0x9ea8 are `[+0x19e]`-indexed; 0xa476/0xa477 are
`[+0x19e]*2`-indexed) and in the deposit-weight table 0xaf34
(`byte [0xaf34 + res*4 + [+0x19e]]`).

**This resolves the old "+0x1a4 anomaly":** between SAVEGAME.009 and
SAVEGAME.000 the wild asteroids' level byte went 1 → 2, so their `+0x1a4`
was reset from the level-2 column: `byte [0x9e78 + t*4 + 2]` = {18,19,19,18,
18,19}. Not a regeneration re-roll.

## Ore deposit placement — asteroid_ore_setup @ 0x185d4

Dispatches on the class byte `byte [0xa470 + t]` (jump table at 0x18598) and
computes one **ore cell (X,Y)** into the globals `g_cell_x/g_cell_y`
(0x9b554/0x9b558), then calls 0x2df44 (placement helper, same one the
faction path uses with size 0x14 = 20):

| class | cell source |
|---|---|
| 0 | from the size word `[+0x8c]`: `rng(size) - size/2` on each axis |
| 1 | seam record `[+0x1c4 + idx*2]` (idx from word table 0x9fd2) + `rng(3)-1` noise |
| 2 | fixed seam bytes, or **ring**: angle `rng(192) + [+0x1c8] + 32`, radius `size/2 + 6`, via sin/cos tables |
| 3 | `rng(4)` pick between fixed bytes `[+0x1c6]/[+0x1c7]` and a ring (radius `size/2 - 4`, angle `[+0x1d5] + rng(32) - 16`) |
| 4 | fixed seam byte pairs (+0x1c4/+0x1c5, +0x1c8/+0x1c9) or `rng(4)` pick |
| 5 | seam record from word table 0x9fd2 + noise |

The seam offsets `+0x1c4..+0x1c9` are written earlier by
`asteroid_init_by_type` (0x18264) from `(size/2 + k) * trig_table[rand]` —
the ring of ore deposits around the asteroid.

## The deposit objects — object_create_on_cell @ 0x181b4

Each ore cell becomes a 24-byte node from the per-cell pool (sentinel
0x168a0):

| field | content |
|-------|---------|
| `[+0x14]/[+0x15]` | cell X/Y from `g_cell_x/g_cell_y` |
| `[+0x8]` | resource type (the per-type parameter) |
| `[+0x9]` | subtype from `[param*6 + 0x9fd0]` |
| `[+0xa]` | 1 (or `[param*6 + 0x9fd1]`) — countdown to maturity |
| `[+0xc]` | behaviour pointer 0x17ff0 (called immediately) |

### Deposit behaviour @ 0x17ff0

On each tick decrements `[+0xa]`; at zero:

- clears the behaviour pointer;
- `byte [+0xc8 + res - base]++` — increments the asteroid's per-resource
  surface counter (base = `dword [0x16644 + type*12]`);
- if `res - base == byte [0xa41e + type]` and the counter is exactly 1:
  `call 0x1c2c4` (special-slot hook);
- if `word [0x9fd4 + res*6] != 0`: `[+0x16] = rng(2048)` (random orientation);
- dispatch on `byte [0x36277 + res*20]` (per-resource class: values 10/16/20
  observed) — 10 → `call 0x23554`, 16 → `call 0x1a914`, 20 → set
  `[+0x139] |= 0x10`.

So the **16-byte array at `+0xc8`** (indexed `res - base`, 0..15) counts the
matured deposits per resource of the asteroid's range `[dword 0x16644+type*12,
dword 0x1664c+type*12)`. It fills in over time (SAVEGAME.009: two 1s from the
initial deposits; SAVEGAME.000: 12–14 of 16 slots non-zero, values up to 3).

**How the surface count increases and decreases:**

- **Creation**: the wild path places two deposit cells (resources `base` and
  `base + byte[0xa455+type]`); the home gets its surface deposit via the
  faction path's placement helper (0x2df44/0x1a3a4).
- **Maturation**: each cell's countdown `[+0xa]` is decremented by its
  behaviour (0x17ff0); at zero the behaviour increments
  `byte[+0xc8 + res - base]` (and the cell becomes the visible lump —
  random orientation, per-resource class dispatch on 0x36277).
- **Re-spawn**: the per-type tick 0x15ce4 (types 9..14 only — this is why
  type 0 and the home never accumulate surface ore) counts down the
  deposit-respawn timers `+0x1a4/+0x1af/+0x1b0/+0x1b2/+0x1b3/+0x1b5`
  (level-1 values 15 / 62,42,50,35,46,58 / 19,14,15,13,11,17 / 50 /
  140,150,135,145,165,160). When one hits zero, the helper
  (0x18e14/0x199c4/0x19604/0x153a4/0x15664) picks a resource (via the
  availability scan 0x18c04 or the weighted table 0xaf34 — spending the
  ore-value budget `[+0x1a0]` for 0x19604) and places a new deposit cell on
  the seam ring; the timer resets from its per-class table (column
  `[+0x19e]`).
- **Consumption**: surface buildings with a running timer consume the
  surface ore — the surface-object tick 0x1a614 decrements
  `byte[+0xc8 + res - base]` when the object's countdown `[+0xa]` expires
  (0x1a6bf), then dispatches on the resource class byte `[+0x8]` (2 →
  "spend" of the `+0x150` store via 0x1a554; 12/20/22/24/25/30/33 → flag
  clears, per-type counter decrements at 0xc350, `+0x188`-word zeroing,
  object free, etc.).

**The `+0xc8` array is the *visible* surface ore, and it is nearly always
mostly zero.** The deposit timers only run for wild types 9..14, and only
matured deposits count. Empirically: the home asteroid (type 1) shows 0/16
and then 1/16 surface slots (SAVEGAME.009 → .000) while holding large
reserves; a freshly spawned type-14 shows 1/16; only long-lived alien
asteroids build up to 12–14/16. So the player's asteroid view shows mostly
"0 of most ores" even though the hidden `+0x5c` reserves are rich — the two
stores are distinct: reserves = in the ground (what mining drains, what the
geosurvey reports), `+0xc8` = lumps on the surface.

## The per-type tick @ 0x15ce4 — timers, not mining

Called from the main loop (0x497) once per loop for the current type 9..14
(16-step rotation). Walks the master list, and for each node of that type
(flags `[+0x139] & 0x10` set):

- calls the per-type handler `[+0x1bc]` (0x15d3f) and, while `word[+0x16c]
  < 23`, `[+0x1c0]` (0x15d9d);
- clamps `[+0xc2]`, then decrements each timer field by one, gated on the
  global flags 0x7e820/0x7e83c/0x7e840/0x7e844/0x7e848/0x7e854/0x7e858/
  0x7e860; at zero the matching helper fires:

| timer | helper | resets from |
|---|---|---|
| `[+0x1a4]` | 0x18e14 | `byte [0x9e78 + t*4 + [+0x19e]]`; then picks the resource with availability > 0 via 0x18c04 and places a deposit |
| `[+0x1b0]` | 0x199c4 | `byte [0x9e90 + t*4 + [+0x19e]]`; checks surface counters at `[+0xc8 + byte[0xa45a+t]]`/`[+0xc8 + byte[0xa452+t]]`, then the colonisation bookkeeping (0x13f/0x1a0 tables) |
| `[+0x1af]` | 0x19604 | `byte [0x9ea8 + t*4 + [+0x19e]]`; weighted-random deposit of resource via the 0xaf34 weight table, spending the value budget `[+0x1a0]` |
| `[+0x1b2]` | 0x153a4 | `byte [0x9ede + t]`; deposit + neighbour/angle bookkeeping (0x7e888) |
| `[+0x1b3]` | 0x15664 | `byte [0x9eb0 + t]` |
| `[+0x1b4]` | 0x17b74 | (colony-capacity related) |
| `[+0x1b5]` | 0x1a014 | (reset from table) |

The "availability" computation 0x18c04: per resource `res` in the type's
range, `avail[res] = byte [0xa476 + res*8 + 2*[+0x19e]]`, then for each
surface object (mine) of resource `res`: `avail[res] -= byte [0xa477 +
res*8 + 2*[+0x19e]]`; returns the first resource with positive availability.

## Mining — extraction of the reserves

Two extraction layers consume the `+0x5c` reserves:

1. **The daily ore tick @ 0x35d4** (per asteroid): for each ore i = 0..9:
   - presence gate: `if rng(100) >= word [0x9cec + i*14]` skip this ore
     (the same threshold table as the creation roll);
   - amount: `roll = rng(word [0x9cf2 + i*14])`, extract
     `min(roll, reserve[i])` units;
   - `reserve[i] -= extracted`; extracted units × dword value
     `[0xe808 + i*4]` accumulate into the tick's value total;
   - if the asteroid is the player's type, the total is reported as a
     message (0x48e64, type 5, priority 30 — the "ore mined" reports).
2. **The extractors** (0x16ba4/0x16bd4/0x16c04/0x16c34/0x16c94/0x16cf4),
   running every 4/8 ticks (`testb $3/$7, 50876`), call the converter
   0x16b04:
   - pick an ore index weighted by `word [+0x5c + idx*2]` (reserve amounts)
     within a per-mine range passed in ebx/ecx (observed ranges [0,10),
     [0,6), [6,10), [0,5), [5,10));
   - `word [+0x5c + idx*2] -= 1` (consume one unit of reserve);
   - `[+0x1a0] += word [0x9cf8 + idx*14]` (add the ore's per-unit value to
     the asteroid's ore-value budget).

The mine buildings are surface objects (84-byte nodes from the 0x168a8 pool,
created by 0x19804 from the 20-byte terrain records; records carry radius
`word [0xab5c + rec*20]`, requirement list at 0xaa4c, class byte at
0xab69). When mines exist on an asteroid they set per-mine state bytes on
the node (`+0xd9..+0xde`: ore-index/active bytes; e.g. the home asteroid in
SAVEGAME.000 has active byte `+0xdc` with ore index `+0xdb` = 0 → extracting
Selenium; the wild asteroids in SAVEGAME.000 show 1–3 active mines).

The budget `[+0x1a0]` (0 at creation, grows with mining) feeds the colony
value `[+0xc2]` (via the 0x1666c/0x16754 family: `+0xc2` moves toward
`50*c[+0xc8] + 200*c[+0xcb]`-style targets) and the level `[+0x19e]`.

**Shipping the budget.** When `[+0x1a0] != 0`, the loading tick 0x14989
walks the asteroid's surface-object lists (objects of the type at +0x18,
their sub-lists at +0xc), and for each class-5 record object
(`byte [0xab69 + res*20] == 5`) copies the budget into the object's
`[+0xc]` cargo field, sets the object's `[+0x4e] |= 0x20` flag, and
**zeroes `[+0x1a0]`** — the ore value leaves the asteroid as cargo
(transporter / ore transfer). The same tick then checks the surface
counter at `[+0xc8 + byte [0xa452 + t]]` and (0x19e24/0x20d34/0x19cd4
chain) launches ore-carrying ships that consume the per-resource counters
`[+0x13f + i]`.

**The set-2 store `+0x150` is capped.** 0x1a514 derives
`word[+0x164] = 300*byte[+0xca] + 600*byte[+0xe6] + 600*byte[+0xe9]`
(the surface-deposit-derived cap). The "spend" 0x1a554 sums `+0x150`, and
if the total exceeds the cap it trims ores back (per-ore steps
`byte [0xa9fe + i]`) until `total == cap`; with a zero cap it clears the
whole array. It is called from the class-2 branch of the surface-object
tick (0x1a762) — so the set-2 store (filled by the home/fixed-path copy of
0x9cd8 and the 0x18c4/0x1864 rare-ore reveal) is kept proportional to the
surface deposits.

## The ore flux — "More ore found" / "Less ore found"

The reserves are **not static** after creation. Two per-type ticks (reached
through the 0x58612 dispatch family; exact cadence untraced) re-roll chunks
of the reserves using the same per-ore tables as the creation roll:

- **0x34f4** (the "More ore found" event): picks a random active asteroid of
  the type (0x13344), then for each ore i = 0..9:
  `if rng(100) < word [0x9cec + i*14]`: `reserve[i] += rng(word [0x9cf2 + i*14])`
  and `value += added * dword [0xe808 + i*4]`. If the asteroid is the
  player's and value > 0, the message "More ore found — A recent geosurvey
  has revealed extra ore worth %d Credits on Colony Asteroid %s" is posted
  (0x48e64, type 5, priority 30). Two rare extras: `rng(100) < 3` →
  `word[+0x6c]++` and value += dword[0xe828]; `rng(100) < 1` →
  `word[+0x6e]++` and value += dword[0xe82c].
- **0x35d4** (the "Less ore found" event): same pick and per-ore gate, but
  **removes**: `roll = rng(word [0x9cf2 + i*14])`; if `roll >= reserve[i]`
  the reserve is **zeroed** (and the whole remaining amount valued), else
  `reserve[i] -= roll`. The removed value is posted as "Less ore found — A
  recent geosurvey has revealed that ore valued at %d Credits never existed
  on Colony Asteroid %s".

So over a long game an ore of any tier can be discovered, reduced, or
**drained to zero** ("never existed"), and new ore can appear. The observed
reserve drift over ~30 days (SAVEGAME.009 → .000, type 9:
`[300,400,400,150,70,60,35,35]` → `[292,388,390,145,67,58,35,34]`) is a mix
of this flux and the mine extractors (0x16b04).

Related: the rare-ore reveal pair 0x18c4/0x1864 — with a chance gate
(`rng(10) < 4`, or `rng(100) < byte[+0x13c]`), picks ore index 8 or 9
(whichever of `word[+0x6c]/[+0x6e]` is zero) and, while the total of the
`+0x150` array is below `word[+0x164]` (= `300*byte[+0xca] +
600*byte[+0xe6] + 600*byte[+0xe9]`), moves **one unit from the reserve to
the `+0x150` array** — the second 10-word store (set 2, from 0x9cd8), which
is otherwise zero in the observed saves.

## Open questions

- The exact runtime values of the runtime-filled tables (0x9c9c, 0x9cec,
  0x9e54..0x9eb3, 0xa41e, 0xa452..0xa45b, 0xa476/0xa477, 0xaf34, 0x16644,
  0x9f48/0x9f60, 0x36277, 0xe808) are not statically readable; the values
  above are empirical (saves) or structural (disasm).
- The copy site that gives the six wild specials their fixed reserves
  [300,400,400,150,70,60,35,35,0,0] is not yet identified (they do not go
  through the rng roll — values identical across different asteroid seeds).
- Where the home's starting-value table 0x9c9c is filled at runtime (per
  scenario), and why the home reserves vary between custom games while the
  alien reserves never do.
- The exact mapping of mine building → reserve-index range is inferred from
  the game text tier lists (0..3 / 4..7 / 8..9), not yet traced to the
  mine-placement code.
- The exact caller chain / cadence of the flux ticks 0x34f4 and 0x35d4
  (they sit in the 0x58612 dispatch family; a runtime trace would pin the
  per-day frequency and thus the effective drain rate).
- The meaning of the `+0x150` set-2 store and the `+0x164` cap (the
  0x18c4/0x1864 reveal moves rare-ore units from `+0x5c` to `+0x150`;
  the UI reads the `+0x5c` store for its hint groups).
- Meaning of the per-type handler pointers `[+0x1bc]/[+0x1c0]` beyond
  "called by the per-type tick" (their target code is in the flat at
  0x9b50..0x9f30, runtime base +0xfffe0000 — see `asteroid-spawning.md`).
- The +0xc8 slot ↔ ore mapping (the 16 slots cover the type's resource
  range, whose base `dword [0x16644 + type*12]` is runtime-filled).
