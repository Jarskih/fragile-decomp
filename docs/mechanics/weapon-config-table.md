# The "weapon config table": a sprite descriptor table, not weapon stats

Status: **confirmed, and the earlier reading is overturned (2026-10-18).** The
per-type table the missile effect "type picker" reads is **static initialised
data** in the GOG build's flat image (the reference CD build fills the same
table at startup), and it is a table of **sprite descriptors for the
projectile / explosion animations** — name of the sprite file, native size and
animation parameters. It holds no damage, speed, range or blast figures. The
six five-byte tuples earlier "interpreted as per-type stats
(damage/speed/radius?)" are sprite sizes and frame counts. Cross-checked
against the flat image and the two DOSBox savestate memory dumps (GOG run: image
base 0x209084; reference run: image base 0x20e084).

Companion to `weapons.md` (the firing pipeline) and `ship-hit-formula.md` (the
impact machine, which holds the real per-missile numbers) — this page is about
the table itself, its location, layout and the sprite names.

## Where the table lives

The code addresses it as DS displacement `0x357b4`; **GOG flat = displacement +
0x86004 = 0xBB7B8** (the earlier statements "flat 0xbb730" and "the reference
table is BSS zeros at 0xc8b90" used a wrong base; the 0xbb730 figure was 0x88
bytes too low and the ISO flat equivalent has not been re-read).

| build | flat image | runtime | nature |
|---|---|---|---|
| GOG | `0xBB7B8` | `0x2c37b4` | static initialised data |
| reference (CD) | not re-read (expected at displacement + 0x8E004 or BSS filled at startup) | `0x2d2c14` | same values at startup |

The table sits at the end of a larger **file / asset table** that starts at
flat `0xBB000`: 162 twelve-byte rows `{name pointer, flag dword, size dword}`
(first the `*_MA\*.vid` video clips, then the `agm00..15` and `trm00..21` photo
sprites with the `$nem` flag, then `bigpage`, `is0c`, `laser`, `shots` with
flag `0x80000000`), then the 20-byte descriptor rows below. Name pointers are DS displacements (+0x86004 for flat); the strings
live at flat `0x8a15c+` (GOG).

## Record layout (20 bytes, displacement base 0x357b4)

Fields as the picker (GOG `0x51954`) and the projectile spawner (GOG `0x519f4`)
use them; offsets from the table base, so the name pointer of a row sits at
`+4`:

| off | size | field |
|-----|------|-------|
| +0x00 | 4 | zero (trailing dword of the previous row) |
| +0x04 | 4 | pointer to the sprite file name (e.g. `_P\XS00.256`) |
| +0x08 | 4 | flag `0x80000000` |
| +0x0c | 1 | animation parameter A (24, 26, 21, 16, 20, 19; 31 for the 8×8 sprites) — copied into the projectile slot |
| +0x0d | 1 | animation parameter B (50 or 63) — copied into the projectile slot |
| +0x0e | 1 | **native width** in pixels |
| +0x0f | 1 | **native height** in pixels |
| +0x10 | 4 | frame count (11, 13, 13, 10, 11, 10, 4 …) — **I** |

All fourteen rows (S@0xBB7BC… the row of the first sprite name; values are the
bytes A, B, width, height and the +0x10 dword):

| row | sprite file | A | B | width | height | +0x10 |
|---|---|---|---|---|---|---|
| 0 | `_P\XS00.256` | 24 | 50 | 88 | 40 | 11 |
| 1 | `_P\XS01.256` | 26 | 50 | 40 | 40 | 13 |
| 2 | `_P\XS02.256` | 21 | 50 | 24 | 24 | 13 |
| 3 | `_P\XB00.256` | 16 | 63 | 32 | 60 | 10 |
| 4 | `_P\XB01.256` | 20 | 63 | 32 | 90 | 11 |
| 5 | `_P\XB02.256` | 19 | 63 | 80 | 80 | 10 |
| 6 | `_P\XMVI.256` | 31 | 63 | 8 | 8 | 4 |
| 7 | `_P\XMAV.256` | 31 | 63 | 8 | 8 | 4 |
| 8 | `_P\XMST.256` | 31 | 63 | 8 | 8 | 4 |
| 9 | `_P\XMVI.256` (second entry) | 31 | 63 | 8 | 8 | 4 |
| 10 | `_P\XMVA.256` | 31 | 63 | 8 | 8 | 4 |
| 11 | `_P\XMVB.256` | 31 | 63 | 8 | 8 | 4 |
| 12 | `_P\FLAMES.256` | 0 | 0 | 0 | 0 | (loader fields) |

(The XMV* / XMAV / XMST names are the Virus / Anti-Virus / Stasis style
8×8 marker sprites; `FLAMES` is the Napalm / burn animation. The row-9 duplicate
of `XMVI` is as stored.) **Reading the counts and parameter bytes A, B as
animation settings is inferred (I); the sizes were checked against the scale
computation below.**

## The type picker and the spawner

- **Picker** (GOG `0x51954`; the old note's `0x51948` is the function's
  alignment pad): called with a requested rectangle (width, height) and a seed.
  It draws a variant with the stateless positional mixer `rng_mix(3, x, y)`
  (`rng.md`; deterministic for a given position, up to three tries) among the
  first three rows (the `XS00/XS01/XS02` set) and accepts the first whose native width and height
  are **at least** the requested size (`byte[+0x0e] ≥ width` and `byte[+0x0f] ≥
  height`); if all three tries fail it falls back to row 0. This replaces the
  old "(min, max) range / retry while min < ..." description.
- **Spawner** (GOG `0x519f4`): takes a structure or blast object, requests the
  sprite for its footprint, then scales the sprite to fit: horizontal scale
  `(requested width << 8) / native width`, vertical `(requested height << 8) /
  native height`, takes the smaller and sets it to 0 if it exceeds 255 (so a
  fixed 256 = 1.0 scale). Position is the object's centre; the projectile slot
  table (GOG `0x8bc84`, 12-byte slots: object pointer, spawn tick, state,
  lifetime, angle, angle base) receives the A / B bytes.
- This is purely visual: the explosion sprite is picked and scaled to cover the
  blast rectangle. **The blast radius and damage are not read from this table.**

## The sprite names

The adjacent string pool holds the projectile sprites and other resource names:

```
*_PHOTO\agm00..agm15.256               16 more photo sprites (agm = ?)
*_PHOTO\trm00..trm21.256               22 photo sprites (trm00..trm21)
_MS\bigpage.256, *_S\is0c.256          misc
_P\laser.256, _P\shots.256             laser / generic shots
_P\XS00..XS02, XB00..XB02              Scatter-style blasts (descriptor rows above)
_P\XMVI, XMAV, XMST, XMVA, XMVB        small marker sprites
_P\FLAMES.256 (Napalm)   _P\VORTEX.256 (Vortex)
FX\LASER1.WAV, menu-video strings, "%s"/"%8d" formats
```

The earlier note counted 14 "turret" sprites `trm08` … `trm21` and was puzzled
by a 14th entry beside the 13 missile types; the file table in fact holds 22
`trm` rows (`trm00` … `trm21`) after 16 `agm` rows, so that count — and the
link between these photo rows and the missile types — was an artefact. What the
`trm` / `agm` photo images show is not established here. The `$nem` tag
(`0x6d6e6524` = the bytes `$nem`) is a flag word on the photo rows, the `$ffm` /
`$ohp` tags of the neighbouring stream are the same kind of flag. The "EK"
prefix and the "+6 pointer offset" of the earlier note came from reading
the pointers against the wrong base: with the correct base each pointer lands
exactly on the stored name (`*_PHOTO\trm08.256`, `_P\XS00.256`, …).

## Open questions

- The ISO flat re-read (does it hold identical rows, or the BSS-filled copy?).
- The exact meaning of parameters A / B (they feed the projectile slot's
  lifetime / angle fields) and of the +0x10 dword.
- Which game object calls the picker with which rectangle (the callers are
  reached through the handler lists of `ship-hit-formula.md`, not by direct
  call sites).
- The `$ffm` / `$nem` / `$ohp` flag codes of the 12-byte file rows at flat
  `0xbb000`–`0xbb7b8` (not a "7-byte entry stream" as the earlier note said)
  and what the loader does with them.
