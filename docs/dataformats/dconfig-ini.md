# DCONFIG.INI — the game's configuration / new-game scenario file

Status: probing (key names and value enums are known from the flat string
pool; the reader code that maps keys to variables has not been located in the
analysed flat image — see "Open question" below).
Source: disassembly (flat string pool) — `build/reports/strings/FRAGILE.EXE.strings.md`
for the raw offsets; offsets below are **flat-image** offsets (report offset
minus the 0x8a760 image base).

## What it is

`DCONFIG.INI` is the game's settings file. It does **not** ship on the disc
(the ISO inventory has no DCONFIG.INI), so the game writes it at runtime and
reads it back on startup. The string pool right before the "Reading
configuration file..." / "DCONFIG.INI" / "Can't find '%s'" message block holds
the complete list of accepted keys, plus the value enums the parser matches.

The keys that matter for the new-game **scenario** (these are the settings the
user observed changing between scenarios):

| key | meaning | value enum found in the pool |
|-----|---------|------------------------------|
| `ArenaSize` @ 0x8e414 | size of the arena / world | `small` (0x8e5cc), `medium` (0x8e5d3), `large` (0x8e5da) |
| `cAsteroidDensity` @ 0x8e41f | starting-asteroid density/count ("c" = count) | numeric (no enum strings) |
| `ArenaAtmosphere` @ 0x8e430 | hostility of the arena | `peaceful` (0x8e5f1), `neutral` (0x8e5fd), `aggressive` (0x8e608) |
| `Aliens` @ 0x8e440 | alien factions on/off | `none` (0x8e613) plus boolean values (`mYES` @ 0x8e4a7, `ON`) |

So the player-visible scenario differences map 1:1 onto these keys:
cAsteroidDensity varies the starting asteroid count, Aliens toggles the
factions, ArenaAtmosphere sets the hostility, ArenaSize sets the world size.

## Other keys in the same pool

`iTimeOffInMenus` (0x8e447), `pTimeRate` (0x8e457), `MouseSpeed` (0x8e464),
`mMouseDoubleClick` (0x8e46f), `FXVMenuAnimations` (0x8e481), `uFont`
(0x8e493), `ngaPlayerName` (0x8e499). Immediately before the scenario keys the
pool also holds the audio/network options (`MusicVolume`, `Network`,
`ComPort`, `ComBaud`, `ModemPort`, `ModemBaud`, `cModemInitString`,
`ModemDialNumber`, `ConnectionType`, `rModemType`, `RQMenuSFX`,
`MenuSFXVolume`, `olGameSFX`, `GameSFXVolume`, `orIngameMusic`,
`IngameMusicVolume`, `Speech`, `SpeechVolume`).

A three-value enum `low` (0x8e5da) / `standard` (0x8e5e0) / `high` (0x8e5ec)
sits just after the `large` value; its owning key is not yet pinned down
(candidate: `pTimeRate`).

## How established

- Stage 08 strings sweep over the whole MZ file lists every key in one
  contiguous block (report lines ~1149588..1150031), immediately followed by
  the reader's messages and the `DCONFIG.INI` filename, then the value enums.
- Values are stored as readable words, not numbers — consistent with an
  `fscanf`/`strcmp`-style parser rather than a binary one.

## Open question: the reader is not in the analysed flat

Not a single dword, EIP-relative, or base-register reference into the config
pool (0x8e350..0x8e540) exists anywhere in the flat image, and the Ghidra
export contains no `s_...` string labels at all. The messages ("Reading
configuration file...", "Can't find '%s'") are equally unreferenced. Same
anomaly family as the missing 0xa3xx static tables
(`docs/mechanics/asteroid-creation.md`, "Open question"): a class of static data
that the flat byte image does not connect to its code. So the key→variable
mapping for `cAsteroidDensity` and friends is unknown until the runtime trace
or a relocation decode resolves this.

## References

- `build/reports/strings/FRAGILE.EXE.strings.md` — raw string inventory
  (line ~5473 for the scenario keys, ~5488 for the reader messages).
- `build/reports/inventory.json` — ISO file list (no DCONFIG.INI shipped).
- `docs/mechanics/asteroid-creation.md` — the parallel "missing static data"
  anomaly.
- `docs/dataformats/gog-build-data.md` — the GOG build differs: it reads
  `CONFIG.INI` (not DCONFIG.INI) and its key set uses `AsteroidDensity`
  (no `c` prefix); the GOG install tree's written `CONFIG.INI`
  (`ArenaSize=0`, `AsteroidDensity=1`, `ArenaAtmosphere=1`, `Aliens=0x0`)
  confirms the 0-based value encoding.
