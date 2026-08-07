# The per-type weapon configuration table

Status: **confirmed** (both builds). The per-type table that the missile type
picker reads is **static initialized data** in the GOG build's flat image and
is filled with the same values at startup in the reference (Interplay CD)
build. Everything below was cross-checked against the flat images and the two
DOSBox savestate memory dumps (GOG run: image base 0x209084; reference run:
image base 0x20e084).

Companion to `weapons.md` (the firing pipeline) — this page is about the
table itself, its location, layout, and the sprite names it maps types to.

## Where the table lives

| build            | flat image              | runtime                  | nature                       |
|------------------|-------------------------|--------------------------|------------------------------|
| GOG              | `0xbb730`               | `0x2c37b4`               | static initialized data      |
| reference (CD)   | `.bss` zeros at `0xc8b90` | `0x2d2c14`             | written at startup, same values |

Address conventions observed at runtime (GOG): the code section maps at
`flat + 0x209084`, the config/string section at `flat + 0x208084` (one page
below the code base), a further data/BSS region at `flat + 0x28e000`. The
reference build: code at `flat + 0x20e084`, strings at `flat + 0x20d084`. The
weapon table belongs to the config/string section.

The table's internal pointer values use the original-image convention:
runtime pointer = stored value + 0x28e000 (GOG) — the stored values are not
usable as flat-file offsets directly.

## Record layout

One 20-byte record per type, stride 0x14 (the picker multiplies the type
index by 0x14; the GOG map symbol for the table is `g_weapon_twin_dword_table`).

| off | size | field |
|-----|------|-------|
| +0x00 | 8 | tag dword `0x6d6e6524` ("$nem") + 4 zero bytes — a 4-char code; same family as the "$ffm"/"$ohp" codes in the adjacent data stream |
| +0x08 | 4 | pointer to the type's sprite file name (below) |
| +0x0c | 8 | same tag dword + zeros |
| +0x0e | 1 | first byte of the pair the type picker tests (see below) |
| +0x0f | 1 | second byte of the pair |

Records 5+ in the GOG flat replace the tag with the flag dword 0x80000000,
and after the first six records the layout continues with byte tuples that
look like per-type numbers (flat `0xbb7c4` onwards):

```
24 50 88 40 11    26 50 40 40 13    21 50 24 24 13
16 63 32 60 10    20 63 32 90 11    19 63 80 80 10
```

six entries — matching the six late-game missile types (Virus, Anti-Virus,
Mega, Stasis, Bug Hunter, Meat-Eater). Interpreted as per-type stats
(damage/speed/radius?) but **not yet decoded**.

## The type picker (`type_pick`)

- GOG: `0x51948`; reference: `0x54864`.
- Takes a (min, max) range; rolls `rng(3)` for a type; the record bytes at
  +0x0e/+0x0f are the type's own (min, max) pair; it retries while
  `min < byte[+0x0e]` or `byte[+0x0f] >= max`; on success it copies the
  0x14-byte record out.
- The reference picker reads the same offsets (runtime `0x2d2c22`/`0x2d2c23`
  = table + 0x0e/+0x0f).
- Callers of the picker are not yet recovered (no direct `call` sites found —
  the spawn path likely reaches it through the handler table; see Open
  questions).

## The sprite names

The +8 pointer of each record points 6 bytes into a string of the form
`EK*_PHOTO\trmXX.256` (i.e. at `OTO\trmXX.256`) — the per-type turret
sprites, **14 entries**: `trm08.256` … `trm21.256`. The GOG build's game text
names 13 missile types (Explosive … Meat-Eater); the 14th entry is
unaccounted for (possibly the unarmed/default type).

The adjacent string pool in the same section holds the projectile sprites and
other resource names:

```
*_PHOTO\trm08.256 … *_PHOTO\trm21.256   per-type turret sprites
_P\laser.256, _P\shots.256              laser / generic shots
_P\XS00.256, _P\XS01.256, _P\XS02.256   Scatter shots
_P\XB00.256, _P\XB01.256, _P\XB02.256
_P\XMVI.256   (Virus)        _P\XMAV.256 (Anti-Virus)
_P\XMST.256   (Stasis)       _P\XMVA.256
_P\XMVB.256                   _P\FLAMES.256 (Napalm)
_P\VORTEX.256 (Vortex)
_MS\bigpage.256, _S\is0c.256, FX\LASER1.WAV, menu-video strings, "%s"/"%8d" formats
```

The XMV*/FLAMES/VORTEX names map 1:1 onto the missile types from the game
text (`_TEXT/AMERICAN.TXT`), which confirms this pool is the weapon-visual
registry. GOG strings live at flat `0x8a15c+`; reference strings at flat
`0x9232c+`; the "EK" prefixes and the exact pointer offset (+6) are not yet
explained.

## Open questions

- The concrete per-type **stats** (damage, speed, range, blast): the six
  byte-tuples at `0xbb7c4` and the per-type tables `weapons.md` lists as
  "tables in code" (e.g. the 0x386d4 family in the reference build) are not
  decoded. The picker's threshold pair at +0x0e/+0x0f coincides with the
  trailing ASCII of the tag dword, so its runtime meaning needs an in-game
  snapshot (the reference build writes the table at startup from a source
  that is not statically visible).
- Who calls `type_pick` and with what (min, max) ranges (the twin/Scatter
  spawn path).
- The meaning of the "$ffm"/"$nem"/"$ohp" tag codes and the entry stream that
  precedes the table in the GOG flat (`0xbb000`–`0xbb730`, 7-byte entries of
  `[value][nul][$tag][nul]`), and why the reference build keeps the table in
  BSS while the GOG build ships it as initialized data.
