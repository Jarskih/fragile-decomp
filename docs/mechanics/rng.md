# Random-number generator

Status: confirmed (static disassembly); runtime trace still deferred.
Source: disassembly (`build/flat/FRAGILE.EXE.flat` + `build/named/.../decompiled.c`)

## Summary

The game has **two separate 32-bit LCGs** with the same multiplier, plus one
**stateless mixer** used where results must be deterministic:

| name | addr | state | seeded by | used for |
|------|------|-------|-----------|----------|
| `rng_next`  | 0x5bada | `g_rng_state`  (0x4cd7c) | `rng_seed` (0x5bb0e) | the general game RNG (448 call sites) |
| `rng_next2` | 0x5bac2 | `g_rng_state2` (0x4cd80) | `rng_seed_clock` (0x5ba58) | encounter / object-placement rolls — 19 call sites, 13 in FUN_0002f114, 6 in unrecovered gap code |
| `rng_mix`   | 0x5baf2 | none (stateless) | — | deterministic spawn positions, table lookups |

Both LCGs are the classic *Numerical Recipes* generator with multiplier
**69069 (0x10dcd)** mod 2³². Because 69069 ≡ 5 (mod 8) and the seed functions
force the state odd, each LCG has the full period **2³⁰** on the reachable
(odd) states and can never fall into the multiplicative LCG's absorbing zero
state.

## The core roll: `rng_next(range)` @ 0x5bada

Raw bytes:

```
52                push edx
89C2              mov edx,eax           ; edx = range
69057CCD0400CD0D  imul eax,[0x4cd7c],0x10dcd   ; state' = state * 69069 (mod 2^32)
A37CCD0400        mov [0x4cd7c],eax     ; state = state'
F7E2              mul edx               ; edx:eax = (u64)state' * range
89D0              mov eax,edx           ; result = high 32 bits
5A                pop edx
C3                ret
```

Formula, exactly:

```
state  = (state * 69069) mod 2^32
result = (state * range) >> 32          ; u64 multiply, take high word
```

Calling convention (verified at every call site): **range arrives in EAX**,
the result is returned in EAX; all other registers are preserved (EDX is
pushed/popped). `result ∈ [0, range)` for every `range ≥ 1`. This is the
standard multiply-high uniform reduction — slightly biased, but that is the
game's exact behaviour, so a reimplementation must reproduce it bit-for-bit if
it wants identical sequences.

The decompiled view models the ABI badly (`__fastcall(param_1=ECX,
param_2=EDX)` returning `CONCAT44(param_2, high32)`) because EAX is an implicit
input; trust the asm above, not the signature.

## Seeding the main RNG: `rng_seed(seed)` @ 0x5bb0e

```
C1C010            rol eax,0x10    ; swap 16-bit halves
66C1E002          shl ax,0x2      ; low word <<= 2
40                inc eax         ; +1 -> odd, never zero
A37CCD0400        mov [0x4cd7c],eax
C3                ret
```

So `g_rng_state = (ror16(seed) with low word << 2) + 1`. The `+1` (and the
`<<2` evenness before it) forces the state **odd**, which is exactly what the
LCG needs for full period; `rng_seed(0)` yields 1. The reseed value normally
comes from a caller argument (e.g. the galaxy seed) placed in EAX.

## The second LCG: `rng_seed_clock` @ 0x5ba58 + `rng_next2` @ 0x5bac2

`rng_seed_clock` runs **once**, in the main initialisation routine
`FUN_0005bd24` (0x5bd24), and seeds `g_rng_state2` from wall-clock entropy:

- two reads of the PIT timer channel 0 (port 0x40) as a 16-bit counter;
- DOS get-system-time (INT 21h AH=2Ch): `(hour*60+minute)*6000 + second*100 +
  hundredths`, added with carry to the PIT value;
- DOS get-date (INT 21h AH=2Ah): day-of-year added to the low word, year added
  to the high word (with carry);
- the low word is forced odd (`& 0xfffd | 1`).

`rng_next2` is byte-for-byte the same shape as `rng_next` but on
`g_rng_state2`. Its main consumer is `FUN_0002f114` (0x2f114, 859 B): the
encounter/object-placement generator, which rolls positions/offsets for a slot
counter `iRam0001e47c` — offsets of ±0x300/±0xa00, even-aligned fields
(`& 0xfffffffe`), and a 0x80000-space coordinate — writing into the tables at
0x5e5e4/0x5e60c/0x5e5bc/0x5e144/0x5e594/0x5e16c. 13 of the 19 `call rng_next2`
sites are inside `FUN_0002f114`; the other six (0x22d19, 0x369f6, 0x36a2d,
0x36ae4, 0x36b4c, 0x438b8) sit in code Ghidra did not recover as functions
(`functions.tsv` gaps), so the second stream's exact role is not fully closed.
So the game keeps a separate, clock-seeded stream for procedural placement so
it cannot perturb — or be perturbed by — the main gameplay stream.

## Deterministic mixer: `rng_mix` @ 0x5baf2

Stateless: it reads only registers and advances no state, so the same inputs
always give the same output. It folds three 32-bit values (EBX, ECX, EDX) by
rotate-xor-add, then multiply-high against EAX:

```
h = rotl(ebx^ecx^edx, 24) + rotl(ecx, 16) + rotl(edx, 8)
result = (u64)in_EAX * h >> 32
```

Used where placement must be repeatable regardless of RNG history:
- `FUN_0002d1c4` (0x2d1c4): spawn position — low nibble is the X cell and the
  next nibble the Y cell of a 16×16 grid scaled by 0x8000, offset from
  −0x3c000;
- `FUN_00054864` (0x54864): picks a table index whose `[min,max]` range
  (table at 0x37c22, 0x14-byte records) contains a mixed value, retrying up to
  3 times.
Only four call sites exist; one (0x521f0) is in unrecovered gap code.

## Deterministic galaxy generation (snapshot / reseed / restore)

The most important consequence of the design: **the galaxy is generated
deterministically from a seed without disturbing the live RNG.** Several
generators in 0x30800..0x32000 follow the same pattern — save `g_rng_state`,
`rng_seed(galaxy_seed)`, generate, restore:

- `galaxy_gen_surface` @ 0x30874: reseeds from its seed argument, runs world
  ticks (`FUN_0005bd04`) over a per-world-type pointer base
  (`DAT_00079b0c[type]`, stride `DAT_0004e77c`), writes a height field
  (values like `0x20000 / (round(f)+0x801)`) via a stream of `rng_next` rolls,
  then restores the state. Called from galaxy regeneration with the seed
  pushed on the stack.
- `galaxy_regenerate` @ 0x320d4: re-runs the whole pipeline only when the
  galaxy's seed field has changed. Verified asm flow:
  `esi = galaxy*; save g_rng_state;`
  `if ([0x1e460] == [esi+0x98] && flags set) skip;`
  `call 0x5da51 x2; call galaxy_gen_surface(seed=[esi+0x98]); call 0x601a4;`
  `call 0x31fe4(esi, 0x24242424); call 0x5ce74(0x20000); call 0x5bd04;`
  `eax=[esi+0x98]; call rng_seed; call 0x30af4/0x310b4/0x315d4/0x31884/`
  `0x31b54/0x31e64; [0x1e460]=[esi+0x98];`
  `restore g_rng_state.`
  So the whole galaxy depends only on the 32-bit seed at galaxy struct +0x98
  (named `g_last_galaxy_seed` @ 0x1e460 caches it for the changed-check).
  The seed is **not** a name hash — see "Where the galaxy seed comes from"
  below.
- `FUN_000315d4` @ 0x315d4: `rng_seed(param)`, then two `rng_next`-driven
  generation loops (`FUN_00031234`, `FUN_00031384`).
- `FUN_00031fe4` @ 0x31fe4: `rng_seed()`, spawns six objects in a row
  (`+0x140` spacing, flags `|1`, per-object rolls), then restores.
- `FUN_000320d4`-adjacent callers, and `FUN_000220d4` @ 0x220d4 which stores
  the *current* `g_rng_state` into the planet record field 0xc3b8 before
  ticking — a per-planet seed snapshot, meaning is TBD.

## Neighbouring helper cluster (NOT RNG)

Right after `rng_seed` sit four arithmetic helpers used all over the code for
fixed-point scaling; they take no state:

- `FUN_0005bb1c` — `(i64)(a*b)/c` truncating
- `FUN_0005bb21` — `(a*b)/c` rounded to nearest
- `FUN_0005bb2f` — `(a*b)/c` rounded away from zero
- `FUN_0005bb42` — `(u64)(a*b) rol (bl&31)`

Don't mistake them for PRNGs (they are pure functions of their inputs).

## Call-site census

A byte scan of the code region finds **448 `call rng_next` instructions**; the
named view exposes ~300 of them as source lines across **~110 distinct caller
functions**. Distribution of the immediate range values (42 distinct; the rest
are register/computed ranges, e.g. a player stat or map dimension):

| range | rolls | notes |
|-------|-------|-------|
| 0x64 (100) | 39 | dominant — classic percentage roll (`roll < threshold`) |
| 0x2 / 0x3 / 0x4 | 25/25/19 | small choice / variant counts |
| 0xa (10) | 17 | d10-style rolls |
| 0x8 / 0x6 / 0x5 | 13/10/10 | small pools |
| 0x100 (256) | 10 | byte/8-bit rolls |
| 0xc8 (200), 0x32 (50), 0x3c (60), 0x28 (40) | 5/4/4/3 | economy/combat thresholds |
| 0x4000–0x10000, 0x800, 0x1000 | ~14 | coordinate / screen-space offsets |
| 0x9c40 (40000), 0xc350 (50000) | 2 | large distance rolls |

Clustering by address region (call sites per 64 KiB block):

| region | functions | rolls | reading |
|--------|-----------|-------|---------|
| 0x00000..0x10000 | 38 | 96 | main loop, AI, entity update (incl. `FUN_0000c234`, `FUN_00009a34`) |
| 0x10000..0x20000 | 39 | 97 | combat/weapons/terrain helpers, `FUN_0002d1c4` placement |
| 0x20000..0x40000 | 17 | 68 | galaxy generation, `FUN_0002f114` encounter placement (state2) |
| 0x40000..0x60000 | 17 | 46 | combat/damage rolls (0x49000..0x54000), init `FUN_0005bd24` |

## Where the galaxy seed comes from (closed)

The galaxy seed is a pure live-RNG output, taken at the moment the galaxy
struct is created. There is no name hash, and the player never enters it.

- The seed field is written in exactly one place, `galaxy_create` @ 0x11a64
  (galaxy creation, decompiled line 9652):
  `*(int *)(galaxy + 0x98) = (rng_next(0x10000) << 16) | rng_next(0x10000);`
  Verified in asm: two `call rng_next` with `eax = 0x10000` (0x11af2,
  0x11afe), first result `shl edx,0x10` (0x11b0d) then `add` with the second
  (0x11b17).
  So the seed is simply the next two 16-bit-scaled rolls of `g_rng_state`.
- `galaxy_regenerate` reseeds from that field (`rng_seed([esi+0x98])`) before
  re-running the generator chain, then restores the pre-call state, so every
  galaxy is fully determined by its 32-bit seed.
- The player's **home galaxy is deliberately deterministic**: a standalone
  routine at 0x11274 (earlier notes said "inside `FUN_000104c4`" — wrong; no
  `functions.tsv` entry covers 0x11274) runs `rng_seed(0x3039)` (== **12345**,
  the canonical LCG seed) immediately before calling `galaxy_create`, then
  copies ten words into `+0x6c`/`+0x15e` and stores the galaxy pointer in
  `g_galaxy_ptr` (0xc3c4). **Caveat:** the source "tables" at 0xa384/0xa3c0
  are executable code in the flat (see `docs/mechanics/galaxy-creation.md`,
  "Open question"), so the copied values are unverified until a runtime trace.
  The race/extra galaxies created by `FUN_0000ff25` @ 0xff25 then roll from
  the same deterministic stream. Net effect: **the galaxy layout is a fixed
  universe on every new game**; only the clock-seeded `g_rng_state2` encounter
  stream varies per run.
  (Assumption to confirm at runtime: that the 0x11274 block is on the
  new-game path; it is reached only by indirect call through `FUN_0000ff25`.)
  Note the main loop can also create galaxies directly: in state 8, `main`
  calls `FUN_0000f544` every tick while `g_mode_flag == 0` — that function is
  the event/encounter scheduler and creates no galaxies itself — and an
  auto-spawn gate (`table[0xa398][[0x16d65]+3*[0x16d64]] > [0xca20]` →
  `galaxy_create` then `galaxy_place(0x3e8)`); those run after the new-game
  seed, so they stay deterministic. (Same caveat applies to the 0xa398 gate
  table: also code in the flat.)

## The complete `g_rng_state` write-site census

Scanning the whole flat image for every dword write (`A3`, `89 /r` for all
eight registers, `C7 /0`) to 0x4cd7c yields **exactly eight sites**, all
identified:

| addr | instruction | what it is |
|------|-------------|------------|
| 0x5bae7 | `mov [0x4cd7c],eax` | `rng_next` — the LCG advance |
| 0x5bb16 | `mov [0x4cd7c],eax` | `rng_seed` — the only seeding site |
| 0x322eb | `mov [0x4cd7c],edi` | `galaxy_regenerate` — final restore (uVar5) |
| 0x320bf | `mov [0x4cd7c],esi` | `FUN_00031fe4` moon generator — restore |
| 0x3238b | `mov [0x4cd7c],esi` | `FUN_00032304` — restore |
| 0x3091a | `mov [0x4cd7c],eax` | unlabeled surface generator after `galaxy_gen_surface` (uses stride `[0x4e77c]`) — restore |
| 0x24b0a | `mov [0x4cd7c],edi` | unlabeled noise/map generator (0x800-byte fill at 0x150f0 + 0x100 rolls) — restore |
| 0x223f0 | `mov [0x4cd7c],eax` | savegame-load (0x222b4): restores the snapshot `FUN_000220d4` took into 0xc3b8, so a load does not perturb the live stream |

Consequence: the ONLY way `g_rng_state` ever changes is via `rng_next`'s LCG
advance or an explicit `rng_seed`. There is no clock-derived seeding of the
main stream (the clock only feeds `g_rng_state2`).

## Open questions

- Initial value of `g_rng_state` before the first `rng_seed` at runtime:
  with BSS zero-initialised it would be 0 (and, since `rng_next` from state 0
  returns 0 forever, anything that rolls before the new-game `rng_seed(12345)`
  is degenerate but harmless — menu/title animation). The remaining unknown is
  the ordering on the startup path (indirect dispatch): does the title/menu
  roll the main RNG before `g_game_state` reaches 8, and does anything call
  `rng_seed` with a non-fixed value first? The two other
  reachable-but-unlabelled `rng_seed` callers (0x22dc3, 0x24a15) have no
  direct callers and are candidates.
- Precise subsystem roles for the heavy users `FUN_0000c234`, `FUN_00009a34`,
  and the 0x49000..0x54000 combat block — next candidates for their own
  mechanics docs.
- The `rng_mix` input registers at each call site (what the caller leaves in
  EAX/EBX/ECX/EDX), to pin down exactly what makes each placement
  deterministic.
