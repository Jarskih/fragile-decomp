# Diplomacy: opinions, pacts, treaties and offers

Status: probing (reference-build static disassembly; runtime trace still
deferred — most roles here are read from the recovered bodies and are
cross-checked against the game's own text resources, which use the vocabulary
Non-Aggression Pact / Joint Combat Treaty / tribute / fines).
Source: `build/named/FRAGILE.EXE.flat/decompiled.c` (reference ISO build; the
GOG-build addresses in `main-loop.md` do **not** match this image).

This note documents how race-to-race diplomacy is implemented: the per-pair
opinion matrices, the pact/treaty node machinery, the incident/violation
counters, the alien offer decisions, and the tribute contracts. It is the
technical tier; a functional write-up belongs in `pages/` later.

## The big picture

The game tracks three separate things that are easy to conflate:

1. **Opinions** — a 15×15 (directed pair) matrix block at 0xd000-range, row
   stride 0x210 = 528 bytes, column stride 2. Two short values per directed
   pair (row race → column race) plus auxiliaries. Decays daily, rises on
   gifts/positive events, crashes on war.
2. **Pacts** — timed node objects: Non-Aggression Pacts (pair nodes on the
   0xc424 list) and Joint Combat Treaties (three-way nodes on the 0xc42c
   list, two signatories against a target race). Nodes carry opinion
   snapshots, a countdown, and a payment amount; they are created by
   `pact_node_create` (0x45a4) / `war_node_create` (0x48d4) and applied when
   their countdown expires.
3. **Incidents** — hostile acts (shots fired, asteroid collisions) are
   accumulated in the per-pair 0xd0a4 matrix (named `g_missile_count_table`
   in the map by the weapons pass); treaties drain this matrix into their
   shot-quota budgets; overshooting accrues fines.

Race ids are bytes 0..14; 0 = unowned/neutral, 1..8 = the "empire" races,
9..14 = alien races, 0xd is special-cased (skipped) in the AI loops. The
player's race is `g_player_race` (0xcd8c). Many checks gate on `8 < race <
0xf` (aliens) vs `race < 9` (empires).

## The per-pair block (row stride 0x210, 15 rows; race row = race*0x210)

All offsets below are absolute addresses; `matrix[+off][i][j]` means
`off + i*0x210 + j*2` (short matrix), `+1` stride for byte matrices. "code
region" marks offsets whose flat bytes decode as instructions (the tables-
in-code anomaly, see `asteroid-spawning.md`): the **static initial values
are unconfirmed**; the matrix cells themselves are runtime data.

| address | stride | role | evidence |
|---------|--------|------|----------|
| 0xd04a | 2 (words) | symmetric 15-word bitset "opinion > 0", rebuilt by `relations_positive_bitset_rebuild` (0x5854) whenever `DAT_00036b68` is set (state scheduler, `FUN_000500a4`); the diplomacy-display matrix | 0x5854 |
| 0xd068 (`FUN_0000d064`+4, code region) | 2 | short matrix, second opinion component; read by `relations_pair_pct` (0x5f04) | 0x5f04, 0x4ea4, 0x48d4 |
| 0xd086 | 2 | short matrix, first opinion component; can be negative (clamped ±0x8000/0x7fff) | many |
| 0xd088 | 2 | short matrix, third component: the decaying/boosted value (`relations_daily_tick` decays it toward the 0xd06a floor; tribute adds `0xd0c3[col] * 0xd0a6`); the `>0` test drives 0xd04a | 0x56c4, 0x5854 |
| 0xd0a4 | 2 | **incident accumulator** `g_missile_count_table`: +1 per weapon fired at the column race (weapon-launch code ~0x519xx), += `sRam0000c0c6` per asteroid collision (0x112f4); drained to zero every tick into 0xd194; subtracted from treaty budgets by `treaty_list_tick` | 0x519xx, 0x112f4, 0x56c4, 0x52d4 |
| 0xd0a6 | 2 | per-pair "tribute amount" — read by 0x56c4 (while nonzero: set 0xd230 bit, `d15c += amount`, opinion += `0xd0c3[col]*amount`, reset 0xd120) but **no static writer found** in this build: dormant/dead path (?) | 0x56c4 |
| 0xd0c3 | 1 | per-column multiplier used only by the 0xd0a6 path (code region, unconfirmed) | 0x56c4 |
| 0xd0d2 | 1 | per-column daily decay amount for 0xd088 (code region, unconfirmed) | 0x56c4 |
| 0xd120 | 4 | per-pair int "ticks since last tribute" counter | 0x56c4 |
| 0xd15c | 4 | per-pair int: remaining tribute grace countdown (decremented when 0xd0a6==0) / extended by 0xd0a6 while paying | 0x56c4 |
| 0xd158 | 4 | per-pair int accumulator, += |opinion delta|/128 on positive opinion set (`ui_opinion_set_cmd`) | 0x4f9f4 |
| 0xd194 | 4 | per-pair int: accumulated 0xd0a4 (incidents), drained to zero by 0x56c4; readers unconfirmed | 0x56c4 |
| 0xd1cc / 0xd1d0 | 4 | per-race approval history ring (12 ints, shifted by `race_approval_pct` 0x5e14 and `FUN_00005ed4`); 0xd1d0 = newest; the per-race "approval score" | 0x5e14, 0x5ed4 |
| 0xd1fc | 4 | per-race int, second score (military?) read by `race_military_diff_pct` (0x5fa4); writer unconfirmed | 0x5fa4 |
| 0xd210 / 0xd212 | 2 | per-race averaged asteroid values written by 0x5e14 (position averages) | 0x5e14 |
| 0xd218 / 0xd220 | 4 | per-race intrusive lists: 0xd218 = structures/units list (walked by 0x9a34 fleet counting), 0xd220 = fleet/units list (walked by `military_pressure_value` 0x6ae4) | 0x9a34, 0x6ae4 |
| 0xd228 | 2-per-row bitset | "war/hostile" bits: set by `war_node_create` (flag&1), cleared by `pact_bits_clear` (0x4b24); blocks the natural opinion boost (0x44e4) | 0x48d4, 0x4b24, 0x44e4 |
| 0xd22a | 2-per-row bitset | "formal treaty/embargo" bits: set by `war_node_create` (flag&2), cleared by 0x4b24; gates the hostile-response path in `relations_opinion_penalize`/`race_count_units` | 0x48d4, 0x4b24, 0x5914, 0x59a4 |
| 0xd230 | 2-per-row bitset | "mutual pact active" (bit per column race, both directions required by `pact_mutual_check` 0x73c4): set by 0x56c4 when 0xd0a6 != 0, used by the AI candidate filters | 0x73c4, 0x56c4, 0x6544, 0x6664, 0x6ef4 |
| 0xd232 / 0xd236 / 0xd250 / 0xd252 / 0xd254 | 2 | per-race countdowns: 0xd232/0xd236 swept by the endgame driver 0x16264 (attack / other sweeps), 0xd250 agenda cooldown, 0xd252 war-decision timer, 0xd254 pact-decision timer | 0x16264, 0xf064, 0xf114, 0x15f14, 0x15f84 |
| 0xd238 | 1 | per-race byte gating the 12-tick "declared intent" message sweep (0x29e4): nonzero → one-shot message DAT_0003a198 for the player race; writer unconfirmed | 0x29e4 |
| 0xd239 | 1 | per-race flags: bit0 = race alive/active (checked everywhere), bit1 = "currently being AI-processed" (rotation in 0x9a34), bit2 = fixed military agenda set (0xf064/0xf114), bit3 = endgame processing rotation (0x16264) | 0x9a34, 0xf064, 0xf114, 0x16264 |
| 0xd244 / 0xd245 / 0xd248 / 0xd24c | 1/1/4/4 | fixed-agenda record: kind (8 defensive / 9 offensive), target race, tick set, target asteroid pointer | 0xf064, 0xf114 |
| 0xd258 / 0xd25c | 4 | per-race "last offer target" + expiry tick (cooldown). Set by `offer_cooldown_set` (0x4fe24) and the AI pickers; cleared when tick > 0xd25c (0x15f14) | 0x4fe24, 0x6664, 0x6ef4, 0x15f14 |
| 0xd200 | 1 | per-pair pact counters: +1 on `relations_opinion_sub`, −1 on `pact_node_apply_paid`; no other readers found (?) | 0x4fe4, 0x4ea4 |

## The daily tick: `relations_daily_tick` (0x56c4)

Called every tick from main state 8 (decompiled.c:181/310). Runs twice:

- `pact_list_tick` (0x5274) then `treaty_list_tick` (0x52d4) — see below.
- For every pair (i,j), i,j in 1..14:
  - if 0xd0a6[i][j] == 0: if 0xd15c[i][j] == 0 → decay 0xd088[i][j] by
    0xd0d2[j] toward the per-pair floor at 0xd06a; else 0xd15c-- (grace);
    0xd120++.
  - else (tribute active): set bit j of row i in 0xd230, 0xd15c += 0xd0a6,
    0xd088 += 0xd0c3[j] * 0xd0a6 (clamped 0x7fff), 0xd120 = 0.
- Then for every row: accumulate 0xd0a4 → 0xd194, zero 0xd0a4.

`relations_positive_bitset_rebuild` (0x5854) runs separately (not per tick):
when `DAT_00036b68` is set, it ORs row/column bits into the symmetric 0xd04a
words for every pair with 0xd088 > 0.

## Pact node machinery

Nodes are small objects on two intrusive lists: **0xc424** (pair pacts) and
**0xc42c** (three-way treaties). Both lists use the same field layout:

| off | meaning |
|-----|---------|
| +8 | race A |
| +9 | race B |
| +0xb | flags byte (bit0 = war/hostile bit in 0xd228, bit1 = treaty bit in 0xd22a; bit 0x80 = "declared"; 0x20/0x40 set by 0x52d4 as "A/B budget exhausted"; 0x8 = "rebalanced") |
| +0xc | ushort "who knows": 0xffff public, else bits of A,B |
| +0x10 | int countdown (per-tick decrement; 0 = apply). `war_node_create` seeds it from the caller; `pact_violation_respond` resets it to 5 |
| +0x14 | int payment/amount |
| +0x18/+0x19/+0x1a | creation date (day/month/year globals 0x16d78/0x16d7c/0x16d80) |
| +0x1c/+0x1e | stored short pair values (d068 / d086 for the A→C direction) |
| +0x20/+0x22 | stored short pair values (d068 / d086 for the B→C direction) |
| +0x24 / +0x28 | int budgets: seeded from table 0x9d44[flags&7] by `pact_node_create` (code region, unconfirmed value); consumed by `treaty_list_tick`; bytes +0x24/+0x25 select the apply path in `pact_list_tick` |
| +0x25 / +0x26 | byte counters: +0x26 is a 10-tick grace countdown (set by `war_node_create`); +0x25 is a second flag/counter byte |

Creation:

- **`pact_node_create` (0x45a4)** — the positive pact (Non-Aggression Pact /
  tribute): snapshots the current opinions A→C, B→C into the node, then
  forces those matrix cells to 0x7fff (max); the node carries the payment
  amount (param_1); `FUN_00004424` posts the announcement (DAT_0003a598) and
  sets +0xc.
- **`war_node_create` (0x48d4)** — the hostile pact (war): snapshots A→B,
  B→A opinions into the node, forces them to −0x8000, sets the 0xd228 (flag&1)
  and 0xd22a (flag&2) bits, arms the +0x26 = 10 grace countdown, and posts
  the announcement (DAT_0003a590); flag&2 → `FUN_0001bb44`, flag&1 →
  `FUN_00016544` (attack/fleet launches).
- **`pact_violation_respond` (0x4c14)** — called when the player race is on
  the receiving end of a hostile act against a formal treaty partner (see
  incidents): finds the pair node and resets its countdown to 5; posts one
  of five escalating message texts (DAT_0003a54c..574 for race A, a564..574
  for race B) selected by a reason code 1/2/4/8/0x10 passed in EBX.
- **`pact_bits_clear` (0x4b24)** — clears the 0xd228/0xd22a bits for the pair
  (treaty over).
- **`treaty_opinions_restore` (0x4724)** — writes the node's stored opinions
  back into the matrix at column C (used by 0x52d4 and 0x74b4).

Processing per tick:

- **`pact_list_tick` (0x5274)** — walks 0xc424: decrements +0x26 (floor 0)
  and +0x10; when +0x10 hits 0, applies the node: if bytes +0x24 and +0x25
  are both 0 → `relations_opinion_sub` (0x4fe4: write the stored opinions
  back, post DAT_0003a490, +1 to the 0xd200 counters, clear bits, then the
  negative decay 0x50f4 twice); else → `pact_node_apply_paid` (0x4ea4: write
  opinions, pay the +0x14 amount through `race_funds_transfer` 0x42f4, post
  DAT_0003a498, −1 to the 0xd200 counters, clear bits, positive boost 0x51b4).
- **`treaty_list_tick` (0x52d4)** — walks 0xc42c (the Joint Combat Treaty
  nodes: A and B are the signatories, C the target): every tick, budget
  [0x24] -= 0xd0a4[C][A] and [0x28] -= 0xd0a4[C][B] (shots fired by each
  signatory at C). When a budget drops below 1, flag 0x20 (A side) / 0x40
  (B side) is set and tier messages post (DAT_0003a468/46c and a470/474
  one-sided, a478/47c when both have finished; the final block
  DAT_0003a480/a484/a488/a48c reports the outcome, and the overshoot
  ×0x1e (=30) is accumulated into node +0x14 as the **fine**). When both
  flags are set, `treaty_opinions_restore` puts the pre-treaty opinions
  back. Fines flow through `race_funds_transfer`.

This matches the game's own vocabulary (AMERICAN.TXT, see the messages
catalog): "Joint Combat Treaty … shot quota … if %s forces fail to reach
their quota … you will pay the agreed fine", "Non Aggression Pact …
terminates in 5 days … fined %d Credits". The 5-day termination countdown
(0x3c = 60 ticks) is only confirmed for the tribute-contract list (0xc3ec);
the pact-node countdown units are unconfirmed.

## Incidents and violations

- Weapon fire at a race-owned target: d0a4[shooter][target] += 1 (weapon
  launch ~0x519xx, decompiled.c:39546).
- Asteroid collision (FUN_000112f4, decompiled.c:9415): d0a4 both directions
  += `sRam0000c0c6` (a short global; sign/static value unconfirmed), plus the
  "X and Y destroyed in collision" messages.
- `relations_opinion_penalize` (0x5914) / `race_count_units` (0x59a4) — the
  "we did a hostile thing to race X" penalty path (called from structure
  claims / attacks): if the 0xd22a bit (formal state) is set, escalate to
  `pact_violation_respond` when either race is an empire race (1..8), else
  post the tier messages; and add the per-race penalty table value
  (0x9c67 / 0x9c6d, code region, unconfirmed) to the d068 opinion.

## The AI offer decisions

Two parallel picker/test pairs run for alien races 9..14 (race 0xd skipped):

- **Peace/tribute**: `alien_pact_timer_tick` (0x15f84, per-race 0xd254
  countdown) → `ai_pact_offer_pick` (0x6664) → `ai_pact_accept_test` (0x62a4)
  → `pact_node_create`.
- **War**: `alien_war_timer_tick` (0x15f14, per-race 0xd252 countdown; also
  clears 0xd258/0xd25c cooldowns) → `ai_war_offer_pick` (0x6ef4) →
  `ai_war_accept_test` (0x6cc4) → `war_node_create`.

The pickers: build the per-race "best relations" table at 0x5bf4c via
`relations_table_fill` (0x5ff4), filter candidates by race-active (0xd239&1),
mutual pact bit (0xd230 via `pact_mutual_check` 0x73c4) and no pending node
(`pact_pair_node_check` 0x7424 / `treaty_node_check` 0x7474), score with
`relations_value_distance_penalty` (0x61f4: relations minus a distance-angle
penalty) or `relations_value_distance_penalty_b` (0x6a54) and
`military_pressure_value` (0x6ae4: −0x14 per enemy fleet in the 0xd220 list,
−10 per enemy asteroid flying the other's flag at +0x2a), and pick one
weighted by `rng_next`. If the picked race is an empire race (1..8) the
offer is instead scheduled via `alien_offer_schedule` (0x44484) /
`alien_fleet_schedule` (0x444f4) and the 0xd258/0xd25c cooldown is armed
(0x28 = 40 ticks).

The accept tests (0x62a4, 0x6cc4) return 1 accept / 2 counter-propose / 0
reject. Inputs: the current pair percentage (`relations_pair_pct` 0x5f04:
average of the two opinion components ×100/0x7fff), the approval-difference
percentages (`race_approval_diff_pct` 0x5f54, `race_military_diff_pct`
0x5fa4), the global approval shift (`approval_global_shift_pct` 0x6104,
clamped to 0/5), the per-race "opinion threshold" table (0x9ca3, code
region), the offer amounts (`offer_amount_calc_a` 0x6bc4: 900 −
20·(approval-diff − military-diff), clamped 90..1800; `offer_amount_calc_b`
0x6c34: approval·100 + 1000000 + relations%·(2000000/100), clamped
50000..10000000) and `offer_attitude_tier_set` (0x6944: relations% <10 → 1,
<50 → 2, ≥50 → 4; stored in the node flag byte). The counter-proposal logic
mutates the node's stored amounts/flags and retries once with the roles
swapped.

## Tribute contracts (economic side)

`tribute_contract_tick` (0x86c4) — runs in main state 8 gated by
`iRam0000cda0` (the same enable that gates `fleet_activity_tick` 0xcd34):
walks the per-race contract list at 0xc3ec and, once per day, credits each
race's treasury counter (0xc4a0) with the per-race daily tribute amount
(table 0x9d64, code region), posting "tribute" messages (DAT_0003a1d8/1dc)
and advancing a per-contract income counter (+0x1e += table 0x9f26·5). The
player-side commands are `ui_tribute_pay_cmd` (0x4fae4: pay amount to race
< 9, message DAT_0003a4f4/4fc) and `ui_opinion_set_cmd` (0x4f9f4: directly
set d086[row][col], accumulating 1/128 of the positive delta in 0xd158);
both live in the 0x4fxxx "command" block with the `cRam0003682c` assertion
pattern. Paying money to alien races reduces the payer's colony approval
(FUN_00016484: −amount/15000 per owned asteroid). `race_funds_transfer`
(0x42f4) is the shared treasury-transfer helper (also used by the pact
payment path).

## Race elimination

`relations_elimination_cleanup` (0x74b4) — called when a race is destroyed:
removes all 0xc424 nodes involving it (clearing their 0xd228/0xd22a bits via
`pact_bits_clear`), restores opinions for 0xc42c nodes involving it, and
posts the "pact with X is over" message (DAT_0003c70c) when the dead race
was the treaty target.

## Open questions

- The message texts behind DAT_0003a468..a5xx, a590, a598, a4f4, a1d8,
  a198, a41c, a338, 3a1c0 are all code-region constants (tables-in-code):
  ids unconfirmed; the game-text mapping (AMERICAN.TXT) is only inferred
  from the catalog.
- 0xd0a6 (the per-pair tribute amount that drives the 0x56c4 "tribute
  active" branch) has no static writer in this build; the branch may be
  dead here (or written through an indirect path not yet recovered).
- The static values of the per-race tables 0x9c58/0x9c67/0x9c6d/0x9c70/
  0x9ca3, 0x9d44, 0x9d64, 0x9f26, 0x9f86, 0xa16c/0xa173, 0xd0c3, 0xd0d2,
  0x9d7b and `sRam0000c0c6` are unconfirmed (code-region bytes).
- `offer_amount_calc_b` (0x6c34): approval·100 + 1000000 +
  relations%·(2000000/100), clamped 50000..10000000 (the relation unit is
  the percent value stored in the 0x5bf4c table).
- Whether the player's own diplomacy UI calls the same `ui_*` commands, and
  how 0xd158/0xd194/0xd1fc are consumed, is unconfirmed.
- The exact meaning of race 0xd being excluded from the AI loops, and of the
  races-1..8-vs-9..14 split (empire vs alien), needs a runtime trace or
  scenario-config reading.
- `FUN_000029e4` (the 12-tick sweep posting DAT_0003a198 when 0xd238 != 0)
  and the 0xd238 writer are unconfirmed.
