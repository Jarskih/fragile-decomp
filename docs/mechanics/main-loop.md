# Main loop and subsystem dispatch

Status: confirmed (static disassembly of the GOG retail build flat,
`build/flat/FRAGILE.EXE.flat` + `build/named/FRAGILE.EXE.flat/decompiled.c`).
Source: disassembly; runtime trace still deferred. Most subsystem roles here
are named from main's call graph and cross-read in the recovered bodies; the
entries flagged (TBD) are plausible-but-unconfirmed.

## The per-tick dispatcher: `g_game_state` (0x34720)

`main` reads one byte each tick and dispatches the game subsystems:

| state | work done in this tick |
|-------|------------------------|
| 0 | init scan: for every asteroid of types 1..8, walk the +0xc slot list and account the per-slot-type counters (0x7e1a8); `init_slot_scan` (0xe94) |
| 1 | object ticks: proximity scan (`object_proximity_scan` 0x11544), discovery (`object_discovery_tick` 0x115a4), terrain-buffer deallocation (`terrain_buffer_free` 0x23734), bud roll (`asteroid_bud_roll` 0x1b8d4) |
| 2 | colony economy: every colony pays its `+0xc2` income into `g_race_treasury` (0xbd58) and runs the per-colony economy chain (0x1d94 pop/morale calc, 0x1fd4, 0x20e4, 0x2224, 0x2494, 0x27e4, 0x3034); `colony_economy_tick` (0x28f4). `race_income_tick` (0x2994) then credits each active race a fixed amount from `g_race_income_table` (0x93b0) |
| 3 | structure behaviours: each asteroid's +8 list is updated through its +0xc callbacks; `structure_update_tick` (0x1414) |
| 5 | daily drift: `asteroid_daily_tick` (0x11364) per object; collision check 0x11104 for stationary objects |
| 6 | terrain generation: `slot_state_tick` (0xe04), then per asteroid with a pending terrain buffer: `terrain_gen_pass_a` (0x23894) and — after the pass counter at +0x139 bit 2 — `terrain_gen_pass_b` (0x24244); `structure_terrain_check` (0x1abe4) validates structure footprints against the buffer cells (bit 0x20/0x2) |
| 7 | world tick: `event_queue_tick` (0x48504), `race_ai_tick` (0x40b14), `race_elimination_check` (0x10004), `race_action_timer_tick` (0x3a44, every 12 ticks), `race_centroid_update` (0x5d04 for the race at `g_cur_race` 0x16624, every tick), a 200-tick sweep (decrement +0x95 counters, arm the relations/fleet/event enables at tick > 700), and `asteroid_destroy` (0x12044) for objects marked +0x4e&0x40 |
| 8 | relations/fleet/event ticks: `race_relations_tick` (0x8544, gated by 0xc6c4), `fleet_activity_tick` (0xcbd4, gated by 0xc6c8), `event_scheduler` (0xf404, when `g_mode_flag==0`), plus the auto-spawn gate → `asteroid_create`/`asteroid_place` while below the scenario ceiling |
| 9..0xe | `colony_rating_update` (0x6d4) per the rotating index (see below) |
| 0xf | end-game state (0x15f64) |

Every tick ends with: `colony_rating_update` for the asteroid at
`g_asteroid_update_index` (0xc340, 0..99, the rotating index into the 100-node
pool, stride 0x1dc), `asteroid_scan_sweep` (0x11644), the index wrap, and the
world object tick `object_world_tick` (0x1004) + fleet tick `fleet_update_tick`
(0x50624, ships at `g_ship_list_sentinel` 0xbd40).

## Subsystems (function → role, with the evidence)

| address | name | evidence |
|---------|------|----------|
| 0x48f94 | `event_message_post` | posts an in-game event node (type byte, priority, text, two vararg groups into +0x20/+0x40); dedups identical messages within 25 ticks (param_1&0x40 path) |
| 0x48e64 | `event_message_post_b` | second entry of the same poster family (same signature at every call site) |
| 0xf404 | `event_scheduler` | per-race countdown slots 0xcb60/0xcb61 (stride 0x208) and 16 event records at 0xc206 (stride 0xc: flags, race byte, target, countdown); fires events (message types 10/0x28) on expiry; gated by 0xc6cc/0xc6d0, both armed at tick > 700 (rng.md's "event/encounter scheduler", internal addr 0xf544) |
| 0xf754 | `event_cancel` | clears an event record whose target matches EAX (or sets a 30-tick defer) |
| 0xcbd4 | `fleet_activity_tick` | 16 nodes at the 0xbd14 pool (stride 0x40): movement countdowns +0x38, arrival/deadline messages (type 7, race names from 0x39100), per-race fleet counts 0xcb5e, last-visit timestamps in the 0xca04 table (race*0x208 + type*4) |
| 0x8544 | `race_relations_tick` | 16 nodes at the 0xbd10 pool (stride 0x28): per-race counter 0xbdc4 vs thresholds 0x967c (stride 0x1c), attitude steps of 5 (0x983e table), three-tier escalation messages |
| 0x5744 | `relations_bitset_rebuild` | builds `g_relations_positive_bits` (0xc96e, 15 words) from `g_relations_target` (0xc9ac > 0) |
| 0x55b4 | `relations_matrix_tick` | 15×15 relation pair matrix at 0xc9c8 (words) with per-type caps 0xc98e, rates 0xc9e7, decay 0xc9f6, timers 0xca80, accumulators 0xca44/0xcab8; also ORs `g_slot_known_bits` (0xcb54) |
| 0x98b4 | `ai_economy_tick` | rotates the active race (slot bit 2), sums the five per-race counters (0xbd58+0xbd7c+0xbda0+0xbde8+0xbdc4), sets `g_race_wealth_tier` (0x7e264: <0x30d41 → poor, <2000000 → mid, else rich), then spends through the race's queue list 0xcb3c (many rng rolls per upkeep item) |
| 0x3b94 | `race_construction_tick` | per-race build timers 0xbf34, build queues 0xbf58 (9 types), calls `building_construct` (0x1b4c4) when a queue item's asteroid matches; gated by 0x34726 |
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
| 0x10004 | `race_elimination_check` | when a race's `g_slot_counters` hits 0 it respawns its asteroid via `race_asteroid_respawn` (0xff34) and sets `g_victory_state` (0x16864: 2 = only the player left, 3 = lone survivor with 0x1529c > 1) |
| 0x40b14 | `race_ai_tick` (TBD) | per-race deadline nodes at 0x16518/0x155f8: on expiry builds a fleet/offer via 0x61a4/0x6b54, then 0x41ee4/0x41f64, result handled by 0x4d0e4 — the offer/action cycle, exact payload unconfirmed |
| 0x48504 | `event_queue_tick` | walks the timed-event node list (pool near 0x86f3b) and fires items whose deadline tick passed via 0x48444 |
| 0x5d04 | `race_centroid_update` | shifts the 11-word history ring 0xcaf0, averages the race's asteroid positions into `g_race_centroid_x/y` (0xcb34/0xcb36) |
| 0x6d4 | `colony_rating_update` (TBD) | for the rotating asteroid: sums the ten start values weighted by `g_rank_divisor_table` (0x9cf0), scales by `g_rating_base` (0xbe30), and sets +0x19e to 0..3 against `g_rating_threshold_a/b/c` (0xbe34/0xbe38/0xbe3c); the meaning of the four states is unconfirmed |
| 0x5a4 | `world_pools_reset` | walks every object pool (asteroid 0xbd04, surface 0x168a0-family, 0xbd08/0xbd0c/0x16870, 1300×84 block) clearing each node via `wait_tick` (0x586b7) |
| 0xe94 / 0xe04 | `init_slot_scan` / `slot_state_tick` (TBD) | state-0 slot accounting vs the 0x7e1a8 counters; state-6 slot repair pass |
| 0x1d94 | `colony_population_update` (TBD) | computes +0x94 from +0x95/+0x6e/+0x5e/+0x6c with a 0x13 cap and a −3·(+0xcd) term |
| 0xc6c4 | `building_cost_calc` | base cost from 0x9980 (stride 0xc) plus a per-type percentage from 0x9a14/0x9a1b (types 1..8 vs wild) |

## Globals added with this pass

| address | name | notes |
|---------|------|-------|
| 0x34720 | `g_game_state` | the dispatcher byte (this build; the reference build's 0x36b64 entry never matches this image) |
| 0x34724 / 0x34725 / 0x34726 | `g_ai_economy_enable` / `g_fleets_enabled` / `g_race_ai_enable` | the three always-on subsystem gates around the state dispatcher |
| 0xc6c4 / 0xc6c8 / 0xc6cc / 0xc6d0 | relations / fleet / event enables | armed at tick > 700 in main; 0xc6c4 is read as the overlapping global `_FUN_0000c6c4` (not renamed — see below) |
| 0xc340 | `g_asteroid_update_index` | 0..99 rotation into the 100-node pool (stride 0x1dc) |
| 0x16624 | `g_cur_race` | the race currently processed (1..14); copied to the player's asteroid +0x84 on save |
| 0xbe30/0xbe34/0xbe38/0xbe3c | `g_rating_base` + three thresholds | colony-rating scales (TBD) |
| 0xbf10/0xbf34/0xbf58 | `g_race_node_ptr` / `g_race_timer` / `g_race_build_queue` | per-race current node, deadline timers, build queues (race*4) |
| 0xbd58/0xbdc4/0xbde8 | `g_race_treasury` / `g_race_reserves` / `g_race_production` | the three best-evidenced per-race counters of the five summed by the economy tick |
| 0xcb34/0xcb36/0xcaf0 | `g_race_centroid_x/y`, `g_race_history` | race position centroid and its 11-word ring |
| 0xc950/0xc96e/0xc9ac/0xc9c8/0xca44/0xcb54 | `g_type_known_bits` / `g_relations_positive_bits` / `g_relations_target` / `g_relations_matrix` / `g_relations_accum` / `g_slot_known_bits` | the relations/discovery arrays |
| 0xcb60/0xcb61 | `g_slot_event_timer_a/b` | per-type (stride 0x208) event countdown bytes |
| 0x16864/0x16865 | `g_victory_state` / `g_victory_flag` | end-of-game state bytes set by the elimination check |
| 0x7e264 | `g_race_wealth_tier` | −1 poor / 0 mid / 1 rich |
| 0xc33c | `g_terrain_buf_count` | active terrain height-field buffers |
| 0x93b0 | `g_race_income_table` | fixed per-day race income words (indexed by 0x16612) |

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
- State 4 is never dispatched in `main`; states 0xf and the elimination path
  (0x16864/0x16865) need a runtime trace to confirm the win/lose flow.
- Everything that touches a "table in code" (0x93b0, 0x9980, 0x9a14, 0x967c,
  0x983e, 0x7e1a8) inherits the GOG build's open question: the flat bytes at
  those addresses decode as instructions and the runtime values are
  unconfirmed (see `docs/mechanics/asteroid-spawning.md`, "tables in code").

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
