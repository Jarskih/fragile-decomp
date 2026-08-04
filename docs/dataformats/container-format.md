# Extensionless data archives (the `_*` container format)

Status: confirmed

## Scope

The following extensionless files in the disc root, one per content area,
all share a single container format:

| File           | Magic    | Entries | Unpacked bytes |
|----------------|----------|---------|----------------|
| `_B/_B`        | `_B`     | 205     | 800,912        |
| `_MA/_MA`      | `_MA`    | 91      | 717,824        |
| `_PHOTO/_PHOTO`| `_PHOTO` | 88      | 959,856        |
| `_S/_S`        | `_S`     | 98      | 1,855,656      |
| `_SCITEK/_SCITEK` | `_SCITEK` | 36   | 305,976        |
| `_TRADE/_TRADE`| `_TRADE` | 202     | 1,652,024      |
| `_ZOOM/_ZOOM`  | `_ZOOM`  | 137     | 3,053,400      |

Each archive unpacks `.256` images (256-colour bitmaps + palette) for one
visual subsystem: starfield (`_S`), planet zoom-in frames (`_ZOOM`),
trade/political portraits (`_TRADE`), science-fiction (SciTek) screens
(`_SCITEK`), space station views (`_MA`), and background plates (`_B`,
`_PHOTO`).

## Structure (little-endian)

```
offset  size  field
0x00    8     magic tag, ASCII, NUL-padded ("_S", "_TRADE", …)
0x08    12    reserved, all zero
0x14    4     data section offset; also implicitly ends the directory
0x18    24*n  directory of n entries
data    …     payloads, one per entry, contiguous, in directory order
```

Directory entry (24 bytes):

```
offset  size  field
0x00    8     file name, ASCII, NUL-padded ("ST00.256", "AC01.256", …)
0x08    8     reserved, all zero
0x10    4     payload offset, absolute within the container file
0x14    4     payload size in bytes
```

Entry count is not stored directly; it is derived from the data offset:

```
n = (data_offset - 0x18) / 24
```

For `_SCITEK/_SCITEK`: data_offset = 0x378 = 0x18 + 36×24, i.e. 36 entries
(ST00.256 … ST35.256); ST35.256 ends exactly at EOF.

## How established

- `make inventory` (03) + `make dat-survey` (07) flagged the extensionless
  root files as `data` with no magic — the only large non-media files on the
  disc, and the obvious place for the game's artwork sets.
- Reading the first 0x40 bytes of each archive showed a common layout: magic
  tag at 0x00, a small LE value at 0x14, then a directory of ASCII names.
- Cross-checks that confirm the layout for every archive:
  - the first payload starts exactly at the 0x14 value;
  - every `offset[i] == offset[i-1] + size[i-1]` (strictly contiguous);
  - the final payload ends exactly at EOF;
  - all directory names are printable ASCII.
- Verified with an ad-hoc parser over `build/iso/` (results above). The
  parser is intentionally not committed: it only touches derived data, so it
  lives with the raw output in `build/`, not in `scripts/`.

## Open questions

- What the 12 reserved bytes (0x08..0x13) are for (version? creation time?).
- Whether the `0x14` value is best read as "data offset" or "directory size
  in bytes including the 24-byte header" — they are numerically identical.
- Exact `.256` pixel format (size = 640×480 + 848 for the intro plates; the
  palette and dimensions must be confirmed from FRAGILE.EXE).
- Whether `FRAGILE.EXE` opens these with a single open+seek helper (one
  pattern) or per-subsystem readers — to be confirmed once Ghidra is
  available (`make disassemble`).
