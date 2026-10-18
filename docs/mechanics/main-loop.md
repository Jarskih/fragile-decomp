# Main loop and subsystem dispatch

Status: confirmed for the dispatcher and the cadence (static disassembly of
the GOG retail build flat, `build/flat/FRAGILE.EXE.gog.flat` +
`build/named/FRAGILE.EXE.gog.flat/decompiled.c`); subsystem roles are named
from main's call graph and cross-read in the recovered bodies, entries flagged
(TBD) are plausible-but-unconfirmed. Corrected 2026-10-18 (see the in-table
"Corrected" marks): the counter at 0xc6bc counts game DAYS, the 0x8544 and
0xcbd4 ticks are the supervisor and agent pools, state 0xf is the alien master
tick, states 9..14 are the per-alien tick, the victory states were re-read.
Source: disassembly; runtime trace still deferred.

Detailed analyses that supersede the short rows below: `life-support.md`
(calendar, state driver, colony life support), `economy-and-personnel.md`
(income, supervisors, agents), `alien-ai-trade-victory.md` (alien tick,
hostility/pacts, trade scheduler, win/lose), `stat-tables-design-sheet.md`
(static tables).

Addressing: all addresses are image-relative in the GOG flat. Code addresses
are flat addresses; DS-relative data displacements (the 0x9xxx / 0xbxxx /
0x16xxx globals) map to the flat bytes at `displacement + 0x86004` for the
*static* tables (see `life-support.md`, "Addressing note"). This resolves the
earlier "tables in code" anomaly for the GOG build.

## The per-tick dispatcher: `g_game_state` (0x34720)

`main` reads one byte each tick and dispatches the game subsystems:

| state | work done in this tick |
|-------|------------------------|
| 0 | init scan: for every asteroid of types 1..8, walk the +0xc slot list and account the per-slot-type counters (0x7e1a8); `init_slot_scan` (0xe94) |
| 1 | object ticks: proximity scan (`object_proximity_scan` 0x11544), discovery (`object_discovery_tick` 0x115a4), terrain-buffer deallocation (`terrain_buffer_free` 0x23734), bud roll (`asteroid_bud_roll` 0x1b8d4) |
| 2 | colony economy: every colony pays its `+0xc2` income into the race money (0xbd58, `g_race_money`) and runs the per-colony life-support chain (0x1d94 radiation, 0x1e44 population tick, 0x1fd4 air, 0x20e4 food, 0x2224 water, 0x2494 power, 0x27e4 staffing check, 0x3034 unrest; see `life-support.md`); `colony_economy_tick` (0x28f4). `race_income_tick` (0x2994) then credits each active race the daily stipend from the table at 0x93b0, indexed by the atmosphere byte 0x16612 (100/250/400 Cr, `economy-and-personnel.md`) |
| 3 | structure behaviours: each asteroid's +8 list is updated through its +0xc callbacks; `structure_update_tick` (0x1414) |
| 5 | daily drift: `asteroid_daily_tick` (0x11364) per object; collision check 0x11104 for stationary objects |
| 6 | terrain generation: `slot_state_tick` (0xe04), then per asteroid with a pending terrain buffer: `terrain_gen_pass_a` (0x23894) and — after the pass counter at +0x139 bit 2 — `terrain_gen_pass_b` (0x24244); `structure_terrain_check` (0x1abe4) validates structure footprints against the buffer cells (bit 0x20/0x2) |
| 7 | world tick: `event_queue_tick` (0x48504), `race_ai_tick` (0x40b14), `race_elimination_check` (0x10004), `race_action_timer_tick` (0x3a44), `contact_announce_tick` (every 12th DAY), `race_centroid_update` (0x5d04; `main` gates it on 0x16624 being 1..14, but 0x16624 is the CALENDAR day, not a race: Corrected 2026-10-18, see below), a 200-DAY sweep (decrement +0x95 counters; when the day count exceeds 700, i.e. first at day 800, force-arm the four supervisor/agent/trade enables), and `asteroid_destroy` (0x12044) for objects marked +0x4e&0x40 |
| 8 | `supervisor_daily_tick` (0x8544, Colony Supervisor pool, gated by 0xc6c4), `agent_pool_tick` (0xcbd4, Agent pool, gated by 0xc6c8), `trade_delegate_scheduler` (0xf404, Traders / Trade Merchants, when `g_mode_flag==0`, halves gated by 0xc6cc/0xc6d0), `relations_matrix_tick` (0x55b4, the hostility matrix), plus the auto-spawn gate (every 8th day) → `asteroid_create`/`asteroid_place` while below the scenario ceiling |
| 9..0xe | `race_objects_tick` (0x15ce4): the per-asteroid tick of alien race `state` (9 Rigellian .. 14 Achaean), once per day. Corrected 2026-10-18 (was: `colony_rating_update`; that runs in the tail on every tick) |
| 0xf | `race_master_tick` (0x15f64): the daily alien master tick (wealth counters, expansion / pact / raid timers). Corrected 2026-10-18: it is NOT an end-game state |

When the always-on gates are set, the tail first runs `relations_bitset_rebuild` + `ai_economy_tick` (player-side supervisor auto-management, not the aliens) and the entity-list ticks. Every tick ends with: `colony_rating_update` for the asteroid at
`g_asteroid_update_index` (0xc340, 0..99, the rotating index into the 100-node
pool, stride 0x1dc), `asteroid_scan_sweep` (0x11644), the index wrap, and the
world object tick `object_world_tick` (0x1004) + fleet tick `fleet_update_tick`
(0x50624, ships at `g_ship_list_sentinel` 0xbd40).

## State cadence and the game day

`g_game_state` is not advanced inside `main` — the outer loop's state driver
(GOG 0x4d5d4, called every main pass) recomputes it each tick:

```
ebx = [0xbd00]                          ; the day-length global
if ((tick-1) % (ebx/4) == 0)            ; only every ebx/4 ticks
    g_game_state = (tick*4 / ebx) & 0xf ; pick the next state
else
    g_game_state = -1                   ; empty tick: main runs only its tail
```

So each state value lasts `[0xbd00]/4` ticks and the full 0..0xf cycle is
`4*[0xbd00]` ticks; on the ticks in between, `g_game_state` is −1 and `main`
only runs the tail above. State 5 — the per-day drift, `asteroid_daily_tick`
0x11364 — therefore fires once per full cycle.

- **`0xbd00`** — the day-length global (GOG runtime guest address 0x259d00),
  written at scenario init (GOG 0x228c4) as `[0x1660e]*8+8` when
  `[0x1660f]` is nonzero, else `[0x1660e]*4+8`. The default init sets
  `[0x1660e]=0` (and `[0x1660f]` on), so `[0xbd00]=8`. `0x1660e` is the game
  speed index (0..2, cycled by the options handler 0x26d04); the derivation is
  in `life-support.md` section 1. The old name `g_sfx_voice_enabled` for
  0x1660f is doubtful (`life-support.md` reads it as a "time runs in menus"
  option, hypothesis).
- **Game-day length — confirmed 32 ticks.** With the default `[0xbd00]=8` a
  full state cycle is 32 ticks, and the savegames prove that this cycle is the
  game day: every GOG save stores a day counter (SAVEDATA file offset 0xA04),
  a 16.16 day fraction (0xA08, always `tick_in_day * 0x800`, tick_in_day
  0..31) and the global tick counter (0xA978), and in all 18 saves tested
  `tick = 32 * day + tick_in_day` holds exactly (see
  `docs/dataformats/savegame-format.md`). The earlier alternative reading (an
  8-tick day) is overturned. Several SAVEDATA countdowns fall by exactly 1 per
  day, as this reading predicts.
- **A longer cadence**: the outer loop also calls 0x47574 every `[0xbd00]*120`
  ticks (GOG 0x4e3fc) = 960 ticks at default = 30 days. 0x47574 is
  `trade_monthly_update` (all trade prices, stock refresh, ore unit values;
  `alien-ai-trade-victory.md` section 8.3). The calendar routine 0x4d6c4
  advances the day / month / year (0x16624 / 0x16628 / 0x1662c) and the
  absolute day count 0xc6bc once per game day.
- **Unit of 0xc6bc (Corrected 2026-10-18).** The counter named
  `g_tick_counter` in the older map is a DAY count (+1 per game day); the
  per-pass tick counter is 0x16630. Every comparison of 0xc6bc in states 7 and
  8 (the `%12`, `%8`, `%200` and `>700` tests, previously read as ticks) is
  therefore in days.
- **Tick rate in wall-clock seconds is not fixed in the code**: the main loop
  has no constant wait; it runs at the host DOSBox pace. On a standard VGA
  DOSBox setup that is roughly 60–70 passes/s (estimate), i.e. ≈16 ms/tick —
  making the ~16-tick colony defence cycle ≈ 0.2–0.3 s. Do not treat this as
  a code fact.

## Subsystems (function → role, with the evidence)

| address | name | evidence |
|---------|------|----------|
| 0x48f94 | `event_message_post` | posts an in-game event node (type byte, priority, text, two vararg groups into +0x20/+0x40); dedups identical messages within 25 ticks (param_1&0x40 path) |
| 0x48e64 | `event_message_post_b` | second entry of the same poster family (same signature at every call site) |
| 0xf404 | `trade_delegate_scheduler` | per-race countdown slots 0xcb60/0xcb61 (stride 0x208) and 16 event records at 0xc206 (stride 0xc: flags, race byte, target, countdown); offers a Trader (0xc6cc) or a Trade Merchant (0xc6d0) to each player race (`alien-ai-trade-victory.md` 8.2). Corrected 2026-10-18: not a random-event scheduler (rng.md's "event/encounter scheduler" label is wrong); the enables are armed by the player's own claims, backstopped by day > 700 |
| 0xf754 | `event_cancel` | clears an event record whose target matches EAX (or sets a 30-tick defer) |
| 0xcbd4 | `agent_pool_tick` | Corrected 2026-10-18: the 0xbd14 pool (16 nodes, stride 0x40) is the AGENT pool (spies / couriers), not fleets: mission countdowns +0x38, arrival/deadline messages (type 7, race names from 0x39100), per-race agent counts 0xcb5e, availability timestamps in the 0xca04 table (race*0x208 + type*4). See `economy-and-personnel.md` |
| 0x8544 | `supervisor_daily_tick` | Corrected 2026-10-18: the 0xbd10 pool (16 nodes, stride 0x28) is the Colony Supervisor pool; per-race personnel fund 0xbdc4 (`g_race_fund_personnel`, formerly "reserves") vs the supervisor table at 0x967c (stride 0x1c), stress steps from the 0x983e table, three-tier grumble / sack messages. Not diplomatic relations; see `economy-and-personnel.md` |
| 0x5744 | `relations_bitset_rebuild` | builds `g_relations_positive_bits` (0xc96e, 15 words) from `g_relations_target` (0xc9ac > 0) |
| 0x55b4 | `relations_matrix_tick` (`hostility_daily_tick`) | 15 rows (stride 0x208) of per-column arrays. Corrected 2026-10-18: the cells are HOSTILITY, not friendliness (`alien-ai-trade-victory.md` section 6; baseline 0xc98c, current 0xc9aa, incident 0xc9c8, gain 0xc9e6, decay 0xc9f5, replacing the earlier cap/rate/decay labels);  timers 0xca80, accumulators 0xca44/0xcab8; also ORs `g_slot_known_bits` (0xcb54) |
| 0x98b4 | `ai_economy_tick` | player-side supervisor auto-management (not the aliens): rotates the active race (slot bit 2), sums the five per-race funds (0xbd58 money + 0xbd7c construction + 0xbda0 vehicles + 0xbde8 missiles + 0xbdc4 personnel), sets `g_race_wealth_tier` (0x7e264: <0x30d41 → poor, <2000000 → mid, else rich), then spends through the race's queue list 0xcb3c (many rng rolls per upkeep item) |
| 0x3b94 | `race_construction_tick` (`transporter_cycle_tick`) | per-race Federal Transporter cycle timer 0xbf34 / target 0xbf10 (formerly "build timer" / "node ptr"), build queues 0xbf58 (9 types), calls `building_construct` (0x1b4c4) when a queue item's asteroid matches; gated by 0x34726 |
| 0x1004 | `object_world_tick` | the master-list per-asteroid update: faction bits, sub-lists at +0x10/+0x18/+0x20 dispatched through their callback pointers, discovery bits 0xc950/0xc96e, destruction (+0x4e&0x20) |
| 0x11644 | `asteroid_scan_sweep` | the rotating asteroid's +0x120 radius marks `g_type_known_bits` (0xcb54) and +0x96 for objects inside it |
| 0x11544 | `object_proximity_scan` | marks all master-list objects within radius as near (+0x4e&2) |
| 0x115a4 | `object_discovery_tick` | pending-discovery countdown +0x1a9 (40 ticks); on expiry posts the discovery message via 0x48e64 for the player's asteroid |
| 0x12044 | `asteroid_destroy` | full teardown: decrements `g_slot_counters`, cancels events, drains the +0x38 queue, saves the player's colony state (0x16624/0x16628/0x1662c → +0x84/+0x85/+0x86), frees the terrain buffer |
| 0x23794 / 0x23734 | `terrain_buffer_alloc` / `terrain_buffer_free` | height-field buffer at +0x124 (allocated via 0x20e04, freed after the +0x121 countdown); `g_terrain_buf_count` (0xc33c) tracks the active count |
| 0x23894 / 0x24244 | `terrain_gen_pass_a` / `terrain_gen_pass_b` | state-6 time-sliced terrain passes over the buffer, switch on buffer[0] (pass counter 0..3), per-cell bit tests (0x20/0x2) with rng rolls |
| 0x1abe4 | `structure_terrain_check` | per structure in the +8 list (dims from the 0x36274 table, stride 0x14), checks the footprint cells against the terrain buffer; failure → retry via 0x1aa94 |
| 0x1b4c4 | `building_construct` | creates the building node (per-type records 0xab5c, stride 0x14; resource list +0x48; player counters 0xc414/0xc43c/0xc4cc); also called from the race builder |
| 0x1b3e4 | `extractor_create` | creates the type-9 mine/extractor node on an asteroid (speed from 0xac15/0xac17/0xac20) |
| 0x1b8d4 | `asteroid_bud_roll` | the budding spawn roll (main state 1, gated on +0x139&0x10 and the +0x18e countdown) |
| 0x10004 | `race_elimination_check` | when a race's `g_slot_counters` hits 0 it respawns its asteroid via `race_asteroid_respawn` (0xff34) and sets `g_victory_state` (0x16864). Corrected 2026-10-18: 2 = the PLAYER lost (its colony counter is 0), 3 = victory (exactly one race left while more than one was configured, 0x1529c > 1); 1 = quit, 5 = bad save; state 4 ("out of time") is never written: there is no time limit (`alien-ai-trade-victory.md` section 4) |
| 0x40b14 | `race_ai_tick` (TBD) | per-race deadline nodes at 0x16518/0x155f8: on expiry builds a fleet/offer via 0x61a4/0x6b54, then 0x41ee4/0x41f64, result handled by 0x4d0e4 — the offer/action cycle, exact payload unconfirmed |
| 0x48504 | `event_queue_tick` | walks the timed-event node list (pool near 0x86f3b) and fires items whose deadline tick passed via 0x48444 |
| 0x5d04 | `race_centroid_update` | (race index arrives in EAX; the `0x16624` gate in `main` tests the calendar day, so the call happens only on days 1..14 of each month: a mis-named global, argument source still to be traced **?**) shifts the 11-word history ring 0xcaf0, averages the race's asteroid positions into `g_race_centroid_x/y` (0xcb34/0xcb36) |
| 0x6d4 | `colony_rating_update` (TBD) | for the rotating asteroid: sums the ten start values weighted by `g_rank_divisor_table` (0x9cf0), scales by `g_rating_base` (0xbe30), and sets +0x19e to 0..3 against `g_rating_threshold_a/b/c` (0xbe34/0xbe38/0xbe3c); the meaning of the four states is unconfirmed |
| 0x5a4 | `world_pools_reset` | walks every object pool (asteroid 0xbd04, surface 0x168a0-family, 0xbd08/0xbd0c/0x16870, 1300×84 block) clearing each node via `wait_tick` (0x586b7) |
| 0xe94 / 0xe04 | `init_slot_scan` / `slot_state_tick` (TBD) | state-0 slot accounting vs the 0x7e1a8 counters; state-6 slot repair pass |
| 0x1d94 | `colony_radiation_update` | Corrected 2026-10-18: radiation step of the per-colony chain; population is 0x1e44 `colony_population_tick` (`life-support.md`) |
| 0xc6c4 | `agent_mission_price` | Corrected 2026-10-18: mission fee from the agent-mission table at 0x9978 (+8 = price column; the old 0x9980 "building cost" is the same table) times a per-mission percentage from 0x9a14 (empire) / 0x9a24 (alien) (`economy-and-personnel.md`). The byte at 0xc6c4 is also the supervisor enable (overlapping global) |

## Globals added with this pass

| address | name | notes |
|---------|------|-------|
| 0x34720 | `g_game_state` | the dispatcher byte (this build; the reference build's 0x36b64 entry never matches this image) |
| 0x34724 / 0x34725 / 0x34726 | `g_ai_economy_enable` / `g_fleets_enabled` / `g_race_ai_enable` | the three always-on subsystem gates around the state dispatcher |
| 0xc6c4 / 0xc6c8 / 0xc6cc / 0xc6d0 | supervisor / agent / Trader / Trade-Merchant enables (were: relations / fleet / event) | Corrected 2026-10-18: armed by the player's own successful claims (2-4, 3-4, 2-3, 3-4 claims) with a backstop in the 200-day sweep when the day count exceeds 700 (`alien-ai-trade-victory.md` section 2); 0xc6c4 is read as the overlapping global `_FUN_0000c6c4` (not renamed — see below) |
| 0xc340 | `g_asteroid_update_index` | 0..99 rotation into the 100-node pool (stride 0x1dc) |
| 0x16624 / 0x16628 / 0x1662c | `g_cal_day` / `g_cal_month` / `g_cal_year` (formerly misnamed `g_cur_race` / `g_colony_pos_x/y`) | Corrected 2026-10-18: calendar day (1..31), month, year (new game 26 May 2496), written only by setup and `calendar_advance` 0x4d6c4; the copies into an asteroid's +0x84/+0x85/+0x86 are date stamps. The older reading "race currently processed" was wrong (`life-support.md`) |
| 0xc6bc | `g_tick_counter` (wrong) | absolute game-day count (0 at new game), saved at SAVEDATA 0xA04; the per-pass tick counter is 0x16630 |
| 0xbe30/0xbe34/0xbe38/0xbe3c | `g_rating_base` + three thresholds | colony-rating scales (TBD) |
| 0xbf10/0xbf34/0xbf58 | `g_race_transporter_target` / `g_race_transporter_timer` / `g_race_build_queue` | per-race Federal Transporter target and cycle timer (old names `g_race_node_ptr` / `g_race_timer`), build queues (race*4) |
| 0xbd00 | day-length global | ticks per state-quadrant; drives the state cadence and the month cadence (see "State cadence and the game day"); GOG runtime guest 0x259d00 |
| 0xbd58/0xbd7c/0xbda0/0xbdc4/0xbde8 | `g_race_money` / `g_race_fund_construction` / `g_race_fund_vehicles` / `g_race_fund_personnel` / `g_race_fund_missiles` | the five per-race funds summed by the economy tick (old names treasury / reserves / production for three of them; `economy-and-personnel.md`) |
| 0xcb34/0xcb36/0xcaf0 | `g_race_centroid_x/y`, `g_race_history` | race position centroid and its 11-word ring |
| 0xc950/0xc96e/0xc9ac/0xc9c8/0xca44/0xcb54 | `g_type_known_bits` / `g_relations_positive_bits` / `g_relations_target` / `g_relations_matrix` / `g_relations_accum` / `g_slot_known_bits` | the relations/discovery arrays |
| 0xcb60/0xcb61 | `g_slot_event_timer_a/b` | per-type (stride 0x208) event countdown bytes |
| 0x16864/0x16865 | `g_victory_state` / `g_victory_flag` | end-of-game state bytes set by the elimination check |
| 0x7e264 | `g_race_wealth_tier` | −1 poor / 0 mid / 1 rich |
| 0xc33c | `g_terrain_buf_count` | active terrain height-field buffers |
| 0x93b0 | `g_race_income_table` | per-day race income words, indexed by the atmosphere byte 0x16612 (100/250/400 Cr; flat 0x93b0+0x86004) |

## Open questions

- `_FUN_0000c6c4` (the overlapping global at 0xc6c4) is not renamed: the map
  engine matches `FUN_`/`DAT_`/`iRam`/`uRam` tokens and the underscore-prefixed
  function token falls outside those patterns. Consider extending
  `scripts/11_apply_names.py` if renaming it becomes important.
- `g_slot_consume_table` (0x16648), `g_race_action_timer` (0xc534) and the
  five per-race counters (0xbd58..0xbde8) are named from single call sites;
  their exact arithmetic is unconfirmed (TBD).
- The 0xbd20/0xbd28/0xbd30 master lists (`g_entity_list_a/b/c_sentinel`) are
  dispatched through callback pointers; their game-side identity (fleet
  orders? treaties? convoys?) is unconfirmed.
- State 4 is never dispatched in `main` and never stored to `g_victory_state`;
  the win/lose flow is settled statically in `alien-ai-trade-victory.md`
  section 4 (runtime trace would only confirm it).
- The former "table in code" anomaly (0x93b0, 0x9980, 0x9a14, 0x967c, 0x983e,
  0x7e1a8) is resolved for the GOG build: static tables are read at flat
  `displacement + 0x86004` (the old reads used the displacement itself and so
  hit code). The 0x7e1a8-range entries are runtime counters, not static data.

## References

- `build/named/FRAGILE.EXE.flat/decompiled.c` — named view; `main` at line 10,
  the subsystem bodies at the addresses above.
- `config/ghidra/rename-map.json` — the machine-readable name map. As of the
  full-coverage passes it carries 3156 curated entries: every recovered
  function and every global variable of the GOG flat is named (game logic in
  the 0x00000–0x4xxxx range; the statically-linked runtime — heap, DOS/4G/DPMI,
  VGA/SVGA, MIDI/SFX, printf/soft-float, libc — in the 0x6xxxx–0x8xxxx range
  with `d4g_`/`dos_`/`gfx_`/`sfx_`/`libc_`/`math_`/`fmt_` prefixes). Globals
  follow `g_<domain>_<role>` naming (`g_ui_*`, `g_race_*`, `g_slot_*`,
  `g_msg_*` message-text pointers, `g_gfx_*`, `g_timer_*`, `g_file_*`, …);
  the 28 string constants are in a `strings` section (`str_*`). Ghidra's own
  `thunk_FUN_*` labels are kept; gap code (functions Ghidra never recovered,
  e.g. the home-asteroid block 0x11084) has no token in the export and cannot be
  mapped here. Function-local variables (`iVar1`, `local_20`, …) are
  Ghidra-generated per-function names and are not mappable through the rename
  map.
- `docs/mechanics/rng.md`, `asteroid-creation.md`, `asteroid-spawning.md`,
  `asteroid-field-maintenance.md`, `ore-and-mining.md` — the mechanic docs
  whose address tables these names build on.
