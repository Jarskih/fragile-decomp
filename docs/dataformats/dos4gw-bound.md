# DOS/4G bound image in FRAGILE.EXE

Status: confirmed (static slice, all streams 1..234). Every in-buffer
relocated field is verified equal to its static value — the flat image is
**pre-linked at base 0** — so the record stream is the cross-check that the
slice is right, not a required post-pass. The only field that cannot be
verified in-buffer is the last stream's final record, which writes one byte
past the end of the image. The runtime values of the 7 selector fixups are
assigned by DOS/4G at load time and are not statically recoverable.

## Scope

`build/iso/FRAGILE.EXE` (1,525,267 B) is an MZ stub whose "unbound" marker
announces a **DOS/4G-bound 32-bit image**. It is NOT a single flat payload: a
bound image carries a *relocation page table + offset table + record stream*
followed by the flat image itself. Stage 05 locates the structural markers,
slices the flat image, and cross-checks its regions; `make runtime` replays the
record stream over the slice to confirm it is already pre-linked.

The flat image is **image-relative**: relocated dwords hold offsets from image
base 0, so it is imported into Ghidra at base 0 with no relocation applied.

## Structural anchors (file offsets, little-endian)

```
offset   size      field
0x00     …         MZ stub
0x3B8BE  4*234     page table: 234 sequential dwords 0x0..0xE9 (= page
                   indices 0..233)
0x3BC66  4         marker dword 0x750700ea (high byte 'u' begins the
                   signature)
0x3BC69  7         ASCII "unbound" (DOS/4G bound-image signature)
0x3BC70  4*236     offset table: 236 dwords (indices 0..235), stream start
                   offsets relative to the record-stream base 0x3C020
0x3C020  …         record stream: relocation records, streams 1..234
                   (42 streams zero-length, see below)
0x8A72F  49        zero padding (0x8A72F..0x8A760)
0x8A760  …..EOF    flat 32-bit image (958,131 B, sha256 c65fffb6…);
                   4 zero bytes + int3 trap at 0x00..0x05, entry at image
                   offset 0x14
```

The page-table extent 4*234 = 936 B lands the table at 0x3B8BE..0x3BC65; the
"unbound" signature is at **0x3BC69** (an earlier note said 0x3BBA9 — wrong:
0x3BBA9 is inside the page table).

The offset table is **236 entries**, not 234: `off[0]` is a 0 sentinel, stream
`g` occupies `[off[g], off[g+1])` for g = 1..234, and `off[235]` = 0x4E70F is
the one-past-end of the last stream. The two dwords at 0x3C018/0x3C01C —
0x4E5C3 and 0x4E70F, previously listed as "gap dwords (role unconfirmed)" — are
in fact `off[234]` (start of stream 234) and `off[235]` (its end).

`scripts/05_extract_flat.py` re-verifies every anchor on every run (the
assertions in `main()`) so a wrong ISO fails loudly instead of slicing garbage;
it slices `build/flat/FRAGILE.EXE.flat` = file offset 0x8A760..EOF.

## Record grammar (verified for all streams 1..234)

Every record decodes as one of two shapes:

```
07 <type:u8> <X:u16> <obj:u8> <Y>     ; relocation record
   type 0x10 -> Y is u32   (9 bytes)
   type 0x00 -> Y is u16   (7 bytes)
02 <type:u8> <X:u16> <obj:u8>         ; 5-byte, no Y
```

The 4th byte is the **target object id** (earlier notes mislabeled it "op").
Object tallies: obj 3 = 34,108, obj 1 = 3,202, obj 2 = 1 (the 7 `02`-records
all target obj 3).

The **Y size is chosen by `type`, not by `op`** — an earlier note claimed the
u32-vs-u16 split depended on the opcode and that streams ≥ 92 used a different
encoding; both were wrong. The grammar above decodes the **entire** stream
(streams 1..234), 37,311 records, with every stream boundary exact.

Full-stream tallies:

| opcode | (type, obj) | count |
|--------|------------|-------|
| 07 | 0x10/0x03 | 27,020 |
| 07 | 0x00/0x03 |  7,081 |
| 07 | 0x10/0x01 |  3,046 |
| 07 | 0x00/0x01 |    156 |
| 07 | 0x00/0x02 |      1 |
| 02 | 0x00/0x03 |      7 |
| **total** | | **37,311** |

(30,066 type-0x10 + 7,238 type-0x00 + 7 op-0x02; the old "op" column is the
target object byte.)

Relocation position rule — uniform, no special cases (verified 37,303/37,304
against the flat, see below):

```
base  = (stream-1) * 0x1000          ; stream g -> page (g-1)
field = base + signed16(X) + 4       ; where the relocated dword lands
```

`signed16(X)` treats X >= 0x8000 as negative (X - 0x10000). The earlier
`base + ((X + 4) & 0xFFFF)` form equals this on the actual data only because
every X >= 0x8000 in the stream is >= 0xFFF4 (so X+4 wraps a full 0x10000 and
the discarded carry is a multiple of 0x1000 that base carries anyway); the
signed form is the correct general statement.

A `02`-record patches the imm16 of a **DS data-selector setup**, i.e. the
two-instruction sequence `66 B8..BF mov $imm16,%r16 ; 8E D8..DF mov %r16,%ds`,
at `base + signed16(X) + 4` — **not** at `base + X` (the earlier target list
0x5b6da/0x5b935/0x62c4d/0x64e59/0x84445/0x843c1/0x84378 was off by 4). All
seven imm16 slots are 0x0000 in the flat (placeholder) and the surrounding
bytes are the operand-size prefix + opcode:

| stream | X | patch site (base+X+4) | instruction |
|--------|-----|----------------------|-------------|
| 92 | 0x06d8 | 0x05b6dc | `66 B8` mov ax,imm16 / `8E D8` |
| 92 | 0x093d | 0x05b941 | `66 B8` |
| 99 | 0x0c4b | 0x062c4f | `66 B9` mov cx,imm16 / `8E D9` |
| 101 | 0x0e59 | 0x064e5d | `66 B8` |
| 133 | 0x0443 | 0x084447 | `66 BB` mov bx,imm16 / `8E DB` |
| 133 | 0x03c1 | 0x0843c5 | `66 B9` |
| 133 | 0x0378 | 0x08437c | `66 BB` |

Each sits in a function prologue that loads the DS data selector for object 3
(the image's own object). The runtime selector values are assigned by the
DOS/4G loader and are not statically recoverable; they are the one thing the
replay in `make runtime` must leave at its static placeholder.

**Stream 234 (last stream).** Its records relocate into the last flat page,
base (234-1)*0x1000 = 0xE9000 — no special-case base, the uniform rule simply
puts the last stream on the last page. 41 of its 42 records verify literally
against the flat bytes at that base; the 42nd (t=0x10, X=0x0eac, Y=0x0881ac)
targets position 0xE9EB0 and its 4-byte write would run one byte past the end
of the image (flat length 0xE9EB3) — so it can never be confirmed in-buffer.
Its Y is nonetheless a plausible code pointer (see "Last-page layout" below).

Empty (zero-length) offset-table streams — **42 total**: 142–151, 156–165,
201–203, 209–218, 222, 223, 226, 228–233. (`off[0]` is a sentinel, not a
stream.)

Empirical anchor for "offsets are image-relative": the entry prologue at
image offset 0x14 (`53 51 52 56 57 55 31 d2 8b 1d 6c 6d 01 00` =
push ebx/ecx/edx/esi/edi/ebp, xor edx,edx, `mov ebx,[0x16d6c]`) is exactly
what Ghidra decompiles from the base-0 flat import (`main` reads
`DAT_00016d6c`). A code dword `mov edx,[0xcd8c]` likewise matches a relocation
record with Y = 0xCD8C.

### Last-page layout (stream 234)

The stream-234 relocations describe a structured last page (flat
0xE9000..EOF):

- **Ascending dword table** at 0xE9000..: 0x983, 0xa14, 0xaad, 0xb50, 0xbfc,
  0xcb3, 0xd74, 0xe41, 0xf1a, 0x1000, … — each 12th entry doubles (0x1000,
  0x2000, 0x4000, 0x8000 at entries 9/21/33/45), i.e. a growing-offset table.
- **Code-pointer table** at 0xE9718..0xE9774: 23 dwords 0x92b4..0x931a
  (written by the 23 t=0x00 records) then a lone dword 0x11.
- **Selector-like dwords** at 0xE9794..0xE97A4: 0x80000000, 0xffff7fff,
  0xffffffff, 0xffff7fef, 0x00007f7f.
- **Code pointers** written by the remaining t=0x10 records — a cluster at
  0xE9A42..0xE9A68 plus 0xE99AC, 0xE9E9E, 0xE9EA4 (0x08b220, 0x05ba1f,
  0x05ba00, 0x08b499, 0x08b480, 0x08b47c, 0x08b49e, 0x08bfa2, 0x08c248), and
  ten more at 0xE9E6E..0xE9EB0 (0x066fff, 0x05eec2, 0x05eec7, 0x0672b9,
  0x0673e4, 0x088134, 0x0881ac, 0x08993b, 0x08a1b2, 0x088868). All verified
  against the flat.
- Flat 0x92b4..0x931a (the pointer table's targets) is 386 code: it calls
  `rng_next` @ 0x5bada and reads `[ecx+0x184]`/`[ecx+0x18a]`. The earlier
  "xrefs" from 0x45eb4/0x1a5dc were misread `call rel32` immediates, not real
  references.
- **Important:** an earlier note claimed the loader fills zeros at 0xE8718 —
  wrong base. 0xE8718..0xE8EB0 is an unrelated zero run on the second-to-last
  page; the stream-234 records never touch it.

### How the full-stream verification was done

Stage 05 now parses the whole stream (37,311 records) and cross-checks each
07-record against the sliced flat image; `make runtime` replays the stream and
fails on any difference. The relocation position rule was verified separately:
for each of the 37,304 `07`-records, the 4 (or 2) bytes at
`(stream-1)*0x1000 + signed16(X) + 4` in the flat equal Y. 37,303 match; the
single exception is stream 234's off-buffer record above. All 7 `02`-records
sit at `66 B8..BF` imm16 slots.

## Flat image regions

Stage 06 (`scripts/06_flat_analyze.py`) derives the layout from printable-
ASCII density (printable fraction < 0.10 across two pages → code ended;
> 0.80 across three pages → strings began):

```
0x00000..0x8D000   code (entry candidate 0x04 = int3-trap NOP slide;
                   0x14 = push6/xor prologue — confirmed entry)
0x8D000..0x92000   binary data (no relocation records target it)
0x92000..0x97000   strings / resource-file catalog (printable density 0.85..0.93;
                   no relocation records target it)
0x97000..0xE9000   relocated code-pointer tables (12,943 records, streams
                   152..227, all verified)
0xE9000..EOF       stream-234 last-page tables (see above)
```

The string/catalog area (0x92000..0x97000) is a **disc-wide resource catalog**,
one sub-table per ISO directory, of NUL-terminated `DIR\name` records (a `*`
prefix marks most of them), each followed by a short trailer (1-3 bytes, see
Open questions), then message/format strings (0x92000..0x92204, e.g. "Out of
memory making fleet combat list", "Too many menus"; format strings use
`\x07`/`\x08` directive bytes) and finally audio/palette binary data.
Sub-tables in order:

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

The region is **not** dead data: 12,943 relocation records (streams 152..227;
obj 3 × 11,346 + obj 1 × 1,597) land inside 0x97000..0xE9000 and every one
verifies against the flat, with 12,941 of the relocated values pointing into
the code region. An earlier note claimed "no decoded relocation target lies
above 0x92000 / the catalog is dead data"; that was an artifact of the old
incomplete grammar (only streams 0..91 decoded) and is withdrawn. The name
strings at 0x92000..0x96000 are not themselves relocation targets, but the
region 0x97000..0xE9000 holds large relocated code-pointer tables whose exact
role is not yet mapped (see Open questions).

## How established

- Stage 04 classified FRAGILE.EXE as a 16-bit MZ DOS executable with a 32-bit
  DOS/4G extender; the bound-image markers were located by scanning for the
  `unbound` signature and the sequential page-table run.
- Stage 05 (`make extract-flat`) verifies the anchors, parses the record
  stream (all 37,311 records) and cross-checks each field against the flat
  image. Stage 06 (`make flat-analyze`) finds the entry candidates and region
  boundaries. `make runtime` replays the stream and emits
  `build/flat/FRAGILE.EXE.runtime.flat`, byte-identical to the static slice
  (the image is pre-linked).
- Stage 07 imports `build/flat/FRAGILE.EXE.flat` into Ghidra as a raw x86 32-bit
  binary at base 0 (`-loader BinaryLoader -loader-baseAddr 0x0`), creates
  `main` at 0x14 (`config/ghidra/set_entry.java`), and exports 1,546 functions
  to `build/decomp/FRAGILE.EXE.flat/decompiled.c`. Addresses resolve
  image-relative (see the 0x16d6c anchor above).
- `make disassemble` is the end-to-end verification: all 9 MZ programs plus the
  flat image import cleanly (exit 0, no script errors).

## Open questions

- Runtime values of the 7 selector fixups (DS data-selectors for object 3) and
  the 16-bit vs zero-extended-32-bit write width for type-0x00 fields. Both are
  statically unobservable (all such fields' high words are 0), and would need a
  runtime load-base observation from a custom DOSBox-X `--enable-debug` build
  (deferred). What is certain is the Y-size rule (type), the position rule,
  and that all in-buffer records match the flat literally.
- Role of the 12,943 relocated code-pointer tables in 0x97000..0xE9000: which
  code reads them, and how they relate to the code pointers on the last page.
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
