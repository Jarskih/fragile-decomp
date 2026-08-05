# DOS/4G bound image in FRAGILE.EXE

Status: confirmed (static slice); runtime relocation validation deferred.

## Scope

`build/iso/FRAGILE.EXE` (1,525,267 B) is an MZ stub whose "unbound" marker
announces a **DOS/4G-bound 32-bit image**. It is NOT a single flat payload: a
bound image carries a *relocation page table + delta-encoded relocation record
stream* followed by the flat image itself. Stages 09/10 locate the structural
markers, slice the flat image, and map its regions.

The flat image is internally **image-relative**: relocated dwords already hold
offsets from image base 0. So it can be imported into Ghidra at base 0 with no
relocation applied — the record stream becomes the *cross-check* that the
slice is right, not a required post-pass (the record encoding for groups ≥ 90
is still undecoded; it is not needed for base-0 static analysis).

## Structural anchors (file offsets, little-endian)

```
offset   size      field
0x00     …         MZ stub
0x3B8BE  4*235     page table: dwords 0..233 sequential (0x0,0x1,0x2,…) +
                   trailing marker tail (runtime-filled placeholders)
0x3BBA9  …         ASCII "unbound" (DOS/4G bound-image signature)
0x3BC70  4*234     offset table: group start offsets (relative to the record
                   stream region)
0x3C020  …         record stream: delta-encoded relocation records
0x8A760  …..EOF    flat 32-bit image (958,131 B, sha256
                   c65fffb6…); 4 zero bytes + int3 trap at 0x00..0x05,
                   entry at image offset 0x14
```

`scripts/05_extract_flat.py` re-verifies every anchor on every run (the
assertions in `main()`) so a wrong ISO fails loudly instead of slicing garbage;
it slices `build/flat/FRAGILE.EXE.flat` = file offset 0x8A760..EOF.

## Record grammar (groups 0..89)

Each record decodes as:

```
07 <type:u8> <X:u16> <op:u8> <Y>
type 0x10 -> Y is u32   ;  type 0x00/0x01 -> Y is u16
struct <BBHB>
```

16,105 records parse with this grammar (parse ratio 0.43 of the stream), then
parsing stops at file offset 0x5D693 exactly on **offset-table group 92**
(groups 0..91 decode; groups ≥ 92 use a different, undecoded encoding). The
first failure bytes are `02 00 d8 06 03 02 00 3d`.

Per (type, op) counts:

| type/op | count |
|---------|-------|
| 0x10/0x03 | 11,455 |
| 0x00/0x03 |  3,962 |
| 0x10/0x01 |    587 |
| 0x00/0x01 |    101 |

Empirical anchor for "offsets are image-relative": the entry prologue at
image offset 0x14 (`53 51 52 56 57 55 31 d2 8b 1d 6c 6d 01 00` =
push ebx/ecx/edx/esi/edi/ebp, xor edx,edx, `mov ebx,[0x16d6c]`) is exactly
what Ghidra decompiles from the base-0 flat import (`main` reads
`DAT_00016d6c`). A code dword `mov edx,[0xcd8c]` likewise matches a relocation
record with Y = 0xCD8C.

## Flat image regions

Stage 06 (`scripts/06_flat_analyze.py`) derives the layout from printable-
ASCII density (printable fraction < 0.10 across two pages → code ended;
> 0.80 across three pages → strings began):

```
0x00000..0x8D000   code (entry candidate 0x04 = int3-trap NOP slide;
                   0x14 = push6/xor prologue — confirmed entry)
0x8D000..0x92000   binary data
0x92000..EOF       strings / resource-file table (printable density 0.85..0.93)
```

The string region is a **disc-wide resource catalog**, one sub-table per ISO
directory, of NUL-terminated `DIR\name` records (a `*` prefix marks most of
them), each followed by a short trailer (1-3 bytes, see Open questions), then
message/format strings (0x92000..0x92204, e.g. "Out of memory making fleet
combat list", "Too many menus"; format strings use `\x07`/`\x08` directive
bytes) and finally audio/palette binary data. Sub-tables in order:

```
0x92204  _MS    menu sprites (font1/clock/edge/disc …)
0x9237c  _MA    intro/menu videos (pbNN/psNN/pmNN/phNN/stNN .vid)
0x92a04  _SCITEK scitek videos (st00..st37 .vid)
0x92cfc  _TRADE trade icons (tiNNN.256, ti001big.vid)
0x92d60  _PHOTO photo/mugshot sprites (cs/ag/csm/agm/trm NN.256)
0x93450  _S     ship sprites (PT/PU/PV/PW/PX/PY/PZ/PS/RI/BR/MK/AR/MN/AC …)
0x93740  _B     sprite sheets from the `_B/_B` container (PBS1..4, RIS, …)
0x94b00  _M     mini sprites (PM/RIM/BRM/MKM/ARM/MAM/ACM NN.256)
0x94f50  _SFX   sound effects (.WAV); 0x96000 _VO voice (.WAV)
```

`_MA\pb01.vid` ↔ `build/iso/_MA/PB01.VID`; the `_B` names match the 206-entry
directory inside the `_B/_B` container verbatim.

Despite the region's size, nothing in the flat image references it: the 179
"pointer dwords" stage 06 reports (67 code + 112 data) are all byte
coincidences — the four code-side samples are `cmp ax,0xb` / `mov dword
[reg+disp],0` instruction encodings, and of 262 aligned flat-portion dwords
landing inside the region, none points at a `*`/`_` name start. The 16,105
decoded relocation targets all lie below 0x92000, the message strings have zero
exact dword references, and no `GRAPHICS`/`Vide` payload magic is embedded in
the image. The catalog is dead data in the bound image: files are resolved at
runtime (by name from the CD), so this is not a pointer table into the flat
image.

## How established

- Stage 04 classified FRAGILE.EXE as a 16-bit MZ DOS executable with a 32-bit
  DOS/4G extender; the bound-image markers were located by scanning for the
  `unbound` signature and the sequential page-table run.
- Stage 05 (`make extract-flat`) verifies the anchors, parses the record
  stream, and slices the flat image. Stage 06 (`make flat-analyze`) finds the
  entry candidates and region boundaries.
- Stage 07 imports `build/flat/FRAGILE.EXE.flat` into Ghidra as a raw x86 32-bit
  binary at base 0 (`-loader BinaryLoader -loader-baseAddr 0x0`), creates
  `main` at 0x14 (`config/ghidra/set_entry.java`), and exports 1,546 functions
  to `build/decomp/FRAGILE.EXE.flat/decompiled.c`. Addresses resolve
  image-relative (see the 0x16d6c anchor above).
- `make disassemble` is the end-to-end verification: all 9 MZ programs plus the
  flat image import cleanly (exit 0, no script errors).

## Open questions

- Record encoding for offset-table groups ≥ 92 (change of scheme at 0x5D693);
  only needed for relocation *application*, not for base-0 static analysis.
- Exact meaning of the relocation types/ops (0x10 vs 0x00/0x01, op 0x01 vs
  0x03) — a runtime load-base trace would pin these down (deferred; would need
  a custom DOSBox-X `--enable-debug` build).
- What the 1-3 trailing bytes after each catalog name mean. **Resolved as NOT
  size, offset, hash, sector count, or container index** (checked against the
  `_B/_B` container directory offsets/sizes and ISO file sizes). They are
  deterministic per-record values that repeat by record position: `_B`/`_S`/`_M`
  share one 11-value cycle (`0a0000 000000 006100 000038 000000 040404 040400
  000098 000000 0a00f8 000000`) with a per-table starting phase (`_S` at slot 7,
  `_M` at slot 8, `_B` at slot 0); `_MA` uses its own 11-value cycle for the
  pb00-39 block (`000c c7fe 3536 6e79 695f 616e 726f 6677 0000 3600 3600`);
  `_SCITEK` uses a 12-value and `_PHOTO` a 9-value cycle; `_MS` repeats values
  (font1=clock `3c 80`, edge=disc `f4 c7 fe`, fontmb=arrow2 `0c`). The values
  are therefore a per-slot tag (sprite-bank / palette / type id) assigned by
  the build tool rather than geometry or pointer data; exact semantics
  unresolved.
