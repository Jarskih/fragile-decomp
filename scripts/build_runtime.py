#!/usr/bin/env python3
"""Replay the DOS/4G relocation stream over the flat image (loader view).

FRAGILE.EXE's flat slice is **pre-linked at base 0**: every relocated field
in the image already holds the exact value the DOS/4G loader would write, so
replaying the record stream must change nothing. Stage 05 slices the image and
cross-checks each field statically; this stage *applies* the stream the way the
loader would and fails loudly on any mismatch, turning "the image is
pre-linked" into a checkable invariant.

What is applied, per record (grammar verified for all streams 1..234):

    07 <type:u8> <X:u16> <obj:u8> <Y>   type 0x10 -> Y u32 (9 bytes),
                                        type 0x00 -> Y u16 (7 bytes)
    02 <type:u8> <X:u16> <obj:u8>       (5 bytes, no Y)

    field = (g-1)*0x1000 + signed16(X) + 4     ; stream g -> page (g-1)

The single non-verifiable field is stream 234's final record (X=0x0EAC,
Y=0x0881AC): its 4-byte field at flat 0xE9EB0 runs one byte past the end of
the image (0xE9EB3). It is reported, not treated as a mismatch.

The op=0x02 records are the exception to "no change": they patch the imm16 of
a `mov $imm16,%r16 ; mov %r16,%ds` DS data-selector setup, and the runtime
selector value is assigned by DOS/4G at load time — not statically recoverable.
They are inventoried (stream, field, instruction) and left at their static
0x0000 placeholder, so the emitted runtime image equals the static slice.

Outputs (derived, gitignored):
  build/flat/FRAGILE.EXE.runtime.flat     loader's view (== static slice)
  build/reports/runtime_build.json / .md
"""
from __future__ import annotations

import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import fragile_decomp_lib as lib

MAIN_EXE = "FRAGILE.EXE"
OFFSET_TABLE_OFF = 0x3BC70
RECORD_STREAM_OFF = 0x3C020
IMAGE_BASE_OFF = 0x8A760

# Grammar struct: op, type, X, obj (byte 4 is the target object id).
GR = struct.Struct("<BBHB")


def signed16(x: int) -> int:
    return x - 0x10000 if x >= 0x8000 else x


def field(g: int, x: int) -> int:
    return (g - 1) * 0x1000 + signed16(x) + 4


def parse_stream(seg: bytes) -> list[tuple]:
    p = 0
    recs = []
    while p < len(seg):
        b0 = seg[p]
        if b0 == 0x07:
            _, t, x, obj = GR.unpack_from(seg, p)
            if t == 0x10:
                y = struct.unpack_from("<I", seg, p + 5)[0]
                sz = 9
            elif t == 0x00:
                y = struct.unpack_from("<H", seg, p + 5)[0]
                sz = 7
            else:
                raise ValueError(f"07-record with type {t:#x} at offset {p:#x}")
            recs.append((0x07, t, x, obj, y, sz))
            p += sz
        elif b0 == 0x02:
            _, t, x, obj = GR.unpack_from(seg, p)
            recs.append((0x02, t, x, obj, None, 5))
            p += 5
        else:
            raise ValueError(f"unexpected record opcode {b0:#x} at offset {p:#x}")
    return recs


def main() -> int:
    cfg = lib.load_config()
    exe = lib.extracted_dir(cfg) / MAIN_EXE
    flat_dir = lib.flat_dir(cfg)
    flat_in = flat_dir / f"{MAIN_EXE}.flat"
    if not exe.is_file() or not flat_in.is_file():
        lib.note(f"{exe} / {flat_in} missing (run `make extract-flat` first)",
                 "red")
        return 2

    src = exe.read_bytes()
    flat = bytearray(flat_in.read_bytes())
    ot = [struct.unpack_from("<I", src, OFFSET_TABLE_OFF + 4 * i)[0]
          for i in range(236)]

    by_type = {"0x10": 0, "0x00": 0}
    by_obj = {}
    total = 0
    written = 0
    mismatches: list[list] = []
    offbuf: list[list] = []
    selectors: list[list] = []
    empty = []
    reg_recs = 0
    reg_streams = set()
    for g in range(1, 235):
        seg = src[RECORD_STREAM_OFF + ot[g]:RECORD_STREAM_OFF + ot[g + 1]]
        if not seg:
            empty.append(g)
            continue
        try:
            recs = parse_stream(seg)
        except ValueError as exc:
            lib.note(f"stream {g}: {exc}", "red")
            return 2
        total += len(recs)
        for op, t, x, obj, y, sz in recs:
            by_obj[obj] = by_obj.get(obj, 0) + 1
            if op == 0x02:
                fp = field(g, x)
                # 16-bit selector slot; loader-assigned value, keep static.
                selectors.append([g, f"{x:#06x}", obj, f"{fp:#08x}",
                                  flat[fp - 2:fp + 4].hex()])
                continue
            by_type["0x10" if t == 0x10 else "0x00"] += 1
            fp = field(g, x)
            if 0x97000 <= fp < 0xE9000:
                reg_recs += 1
                reg_streams.add(g)
            if fp + 4 > len(flat):
                offbuf.append([g, f"{x:#06x}", f"{fp:#08x}", f"{y:#010x}"])
                continue
            st = struct.unpack_from("<I", flat, fp)[0]
            ok = (st == y) if t == 0x10 else ((st & 0xFFFF) == y)
            if not ok:
                mismatches.append([g, f"{x:#06x}", f"{fp:#08x}",
                                   f"{y:#010x}", f"{st:#010x}"])
                continue
            # Pre-linked: the loader's write equals the static byte value.
            flat[fp:fp + 4] = struct.pack("<I", y)
            written += 1

    runtime_flat = bytes(flat)
    identical = runtime_flat == flat_in.read_bytes()

    runtime_out = flat_dir / f"{MAIN_EXE}.runtime.flat"
    runtime_out.write_bytes(runtime_flat)

    data = {
        "source": MAIN_EXE,
        "records_total": total,
        "counts_by_type": by_type,
        "counts_by_obj": by_obj,
        "selector_fixups": selectors,
        "empty_streams": empty,
        "verification": {
            "fields_applied": written,
            "in_buffered_mismatches": mismatches,
            "off_buffer": offbuf,
            "image_identical_to_static": identical,
        },
        "region_0x97000_0xE9000": {
            "records": reg_recs,
            "streams": sorted(reg_streams),
        },
        "outputs": {
            "runtime_flat": f"flat/{MAIN_EXE}.runtime.flat",
            "size": len(runtime_flat),
        },
    }

    jpath, mpath = lib.report_pair(cfg, "runtime_build", data)

    bad = mismatches or len(offbuf) != 1 or not identical
    if bad:
        lib.note(f"runtime build FAILED: {len(mismatches)} mismatch(es), "
                 f"{len(offbuf)} off-buffer (expected 1), "
                 f"identical={identical}", "red")
        return 2

    rows = [
        ["records", "07 type 0x10", by_type["0x10"], "-"],
        ["records", "07 type 0x00", by_type["0x00"], "-"],
        ["records", "02 selector fixups", len(selectors),
         "runtime selector values not statically recoverable"],
        ["applied", "fields written", written, "all == static (pre-linked)"],
        ["verified", "off-buffer records", len(offbuf), "expected exactly 1"],
        ["runtime image", "output", f"{len(runtime_flat):#x} bytes",
         "identical to static slice" if identical else "DIFFERS"],
    ]
    md = (f"# Runtime image build ({MAIN_EXE})\n\n"
          + lib.md_table(["item", "kind", "value", "notes"], rows)
          + "\n\nOff-buffer records:\n\n"
          + lib.md_table(["stream", "X", "field", "Y"], offbuf)
          + "\n\nSelector fixups (DS data-selector loads, target obj):\n\n"
          + lib.md_table(["stream", "X", "obj", "field", "instruction"],
                         selectors)
          + "\n")
    lib.write_md(mpath, md)
    lib.note(f"runtime build: {written} fields applied (all no-ops), "
             f"{len(offbuf)} off-buffer, identical={identical}", "green")
    lib.note(f"runtime flat -> {runtime_out}", "green")
    lib.note(f"report -> {jpath}", "green")
    return 0


if __name__ == "__main__":
    sys.exit(main())
