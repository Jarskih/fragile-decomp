#!/usr/bin/env python3
"""Stage 05: slice the flat 32-bit image out of the DOS/4G bound FRAGILE.EXE.

FRAGILE.EXE is a DOS/4G *bound* image: a real-mode loader stub (a nested Watcom
MZ at 0x38D64) is followed by DOS/4G's page table, offset table and a
relocation record stream, then by the flat 32-bit image that the loader maps
and runs in protected mode.

This stage:
  1. locates the bound-image structural markers (the "unbound" signature, page
     table, offset table, record stream) by scanning for their signatures and
     sanity-checks them,
  2. slices the flat image (everything after the record stream) into
     build/flat/FRAGILE.EXE.flat,
  3. parses the record stream with the verified grammar and cross-checks every
     in-buffer relocated field against the sliced flat image. The image is
     pre-linked at base 0: relocated fields already hold their final value,
     so the record stream is the *cross-check* that the slice is right, not a
     required post-pass (see `make runtime` / scripts/build_runtime.py).
and writes build/reports/flat_extract.{json,md}.

Outputs (derived, gitignored):
  build/flat/FRAGILE.EXE.flat
  build/reports/flat_extract.json / flat_extract.md
"""
from __future__ import annotations

import json
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import fragile_decomp_lib as lib

MAIN_EXE = "FRAGILE.EXE"

# --- structural anchors (file offsets), verified on the reference ISO ---------
# All values below were determined empirically from the reference image; the
# assertions in main() re-verify them on every run so a wrong ISO fails loudly
# instead of producing a garbage slice.
UNBOUND_MARKER = b"unbound"
PAGE_TABLE_OFF = 0x3B8BE      # 234 sequential dwords (0x0..0xE9 = pages 0..233)
OFFSET_TABLE_OFF = 0x3BC70    # 236 dwords (indices 0..235): stream start offsets
RECORD_STREAM_OFF = 0x3C020   # relocation record stream (streams 1..234)
IMAGE_BASE_OFF = 0x8A760      # first byte of the flat image (post-padding)
IMAGE_ENTRY_OFF = 0x14        # image-relative entry hint (Prologue_ push pattern)

# Record grammar (verified for ALL streams 1..234 against the flat image):
#   07 <type:u8> <X:u16> <obj:u8> <Y>     type 0x10 -> Y is u32 (9 bytes),
#                                        type 0x00 -> Y is u16 (7 bytes)
#   02 <type:u8> <X:u16> <obj:u8>         (5 bytes, no Y)
# The 4th byte is the *target object id*, not an opcode. Stream g maps to page
# (g-1); the relocated dword sits at
#   field = (g-1)*0x1000 + signed16(X) + 4          (uniform, g = 1..234)
# where signed16() treats X >= 0x8000 as negative. A 02-record patches the
# imm16 of a "66 B8..BF mov $imm16,%r16 ; 8E D8..DF mov %r16,%ds" DS data-
# selector setup; the loader writes the runtime selector for the target object.
GR = struct.Struct("<BBHB")   # op, type, X, obj


def signed16(x: int) -> int:
    return x - 0x10000 if x >= 0x8000 else x


def page_table(f: bytes) -> list[int]:
    """Page-table dwords. Sequential 0..N placeholders; entries beyond the
    clean run are not part of the table."""
    vals = []
    for i in range(240):
        off = PAGE_TABLE_OFF + 4 * i
        if off + 4 > len(f):
            break
        v = struct.unpack_from("<I", f, off)[0]
        if v != i:
            break
        vals.append(v)
    return vals


def offset_table(f: bytes) -> list[int]:
    """Stream start offsets (relative to the record stream region).

    236 entries (indices 0..235). off[0] is a 0 sentinel; stream g occupies
    [off[g], off[g+1]) for g = 1..234, so off[235] is the end of the last
    stream.
    """
    return [struct.unpack_from("<I", f, OFFSET_TABLE_OFF + 4 * i)[0]
            for i in range(236)]


def parse_stream(seg: bytes) -> list[tuple]:
    """Decode one stream's record sequence with the verified grammar.

    Returns [(op, type, X, obj, Y, size), ...]. Raises ValueError on the first
    byte that does not decode (a stream boundary misalignment or an unexpected
    opcode/type would otherwise silently corrupt the tallies).
    """
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


def verify_records(recs: list[tuple], g: int, flat: bytes) -> dict:
    """Cross-check every 07-record of stream g against the flat image.

    The flat is pre-linked at base 0, so each in-buffer field must already
    equal Y (full u32 for type 0x10, low u16 for type 0x00). Records whose
    4-byte field would run past the end of the image are counted as off-buffer
    (exactly one is expected: stream 234's final record, see the report).
    """
    base = (g - 1) * 0x1000
    verified = 0
    bad: list[list] = []
    offbuf: list[list] = []
    for op, t, x, obj, y, sz in recs:
        if op != 0x07:
            continue
        fp = base + signed16(x) + 4
        if fp + 4 > len(flat):
            offbuf.append([g, f"{x:#06x}", f"{fp:#08x}", f"{y:#010x}"])
            continue
        st = struct.unpack_from("<I", flat, fp)[0]
        ok = (st == y) if t == 0x10 else ((st & 0xFFFF) == y)
        if ok:
            verified += 1
        else:
            bad.append([g, f"{x:#06x}", f"{fp:#08x}", f"{y:#010x}",
                        f"{st:#010x}"])
    return {"verified": verified, "mismatches": bad, "off_buffer": offbuf}


def main() -> int:
    cfg = lib.load_config()
    exe = lib.extracted_dir(cfg) / MAIN_EXE
    if not exe.is_file():
        lib.note(f"{exe} not found (run `make extract` first)", "red")
        return 2

    f = exe.read_bytes()
    problems = []
    if f[:2] != b"MZ":
        problems.append("not an MZ executable")
    ub = f.find(UNBOUND_MARKER)
    if not (0x3B000 <= ub < RECORD_STREAM_OFF):
        problems.append(f"DOS/4G \"unbound\" marker not in loader region ({ub:#x})")
    if not (0x80000 <= IMAGE_BASE_OFF < len(f)):
        problems.append("image base offset out of range")
    if not (f[IMAGE_BASE_OFF:IMAGE_BASE_OFF + 4] == b"\x00\x00\x00\x00"
            and f[IMAGE_BASE_OFF + 4:IMAGE_BASE_OFF + 7] == b"\xcc\xeb\xfd"):
        problems.append("image base start signature mismatch "
                        "(expected zero-pad + int3/jmp trap)")
    if not (f[IMAGE_BASE_OFF - 0x30:IMAGE_BASE_OFF - 0x8] == b"\x00" * 0x28):
        problems.append("padding before image base is not zeros")
    if problems:
        for p in problems:
            lib.note(f"validation failed: {p}", "red")
        return 2

    flat = f[IMAGE_BASE_OFF:]
    size = len(flat)
    image_end = IMAGE_BASE_OFF + size

    pt = page_table(f)
    ot = offset_table(f)

    # 236 offset-table entries must span [0 .. one-past-last-stream], and the
    # remaining gap to the image base is the documented 49 zero bytes.
    last_end = RECORD_STREAM_OFF + ot[235]
    tail_zeros = IMAGE_BASE_OFF - last_end
    if tail_zeros < 0:
        lib.note("offset table runs past the image base", "red")
        return 2

    # Parse every stream and cross-check its records against the flat slice.
    counts = {}
    by_type = {"0x10": 0, "0x00": 0}
    by_opcode = {}
    by_obj = {}
    total = 0
    empty_streams = []
    verify = {"verified": 0, "mismatches": [], "off_buffer": []}
    for g in range(1, 235):
        seg = f[RECORD_STREAM_OFF + ot[g]:RECORD_STREAM_OFF + ot[g + 1]]
        if not seg:
            empty_streams.append(g)
            continue
        try:
            recs = parse_stream(seg)
        except ValueError as exc:
            lib.note(f"stream {g}: {exc}", "red")
            return 2
        total += len(recs)
        for op, t, x, obj, y, sz in recs:
            by_opcode[f"{op:#04x}"] = by_opcode.get(f"{op:#04x}", 0) + 1
            by_obj[obj] = by_obj.get(obj, 0) + 1
            if op == 0x02:
                continue
            by_type["0x10" if t == 0x10 else "0x00"] += 1
            key = f"{t:#04x}/{op:#04x}"
            counts[key] = counts.get(key, 0) + 1
        v = verify_records(recs, g, flat)
        verify["verified"] += v["verified"]
        verify["mismatches"].extend(v["mismatches"])
        verify["off_buffer"].extend(v["off_buffer"])

    data = {
        "source": MAIN_EXE,
        "source_size": len(f),
        "image_base_offset": IMAGE_BASE_OFF,
        "image_end_offset": image_end,
        "image_size": size,
        "image_sha256": lib.sha256_bytes(flat),
        "entry_hint": IMAGE_ENTRY_OFF,
        "markers": {
            "unbound": ub,
            "page_table": PAGE_TABLE_OFF,
            "offset_table": OFFSET_TABLE_OFF,
            "record_stream": RECORD_STREAM_OFF,
        },
        "page_table": {
            "start": PAGE_TABLE_OFF,
            "clean_sequential_entries": len(pt),
            "note": "placeholder dwords 0..N; runtime-filled; entry beyond the "
                    "clean run is the trailing marker tail",
        },
        "offset_table": {
            "start": OFFSET_TABLE_OFF,
            "entries": len(ot),
            "first_entries": ot[:8],
            "last_entries": ot[232:],
            "note": "236 dwords; off[0] sentinel; stream g = [off[g], off[g+1]) "
                    "for g = 1..234; off[235] = end of the last stream",
        },
        "record_stream": {
            "start": RECORD_STREAM_OFF,
            "end": last_end,
            "parsed_total": total,
            "tail_zero_bytes": tail_zeros,
            "empty_streams": empty_streams,
            "counts_by_type": by_type,
            "counts_by_type_obj": counts,
            "counts_by_opcode": by_opcode,
            "counts_by_obj": by_obj,
            "verification": {
                "in_buffered_verified": verify["verified"],
                "in_buffered_mismatches": verify["mismatches"],
                "off_buffer": verify["off_buffer"],
            },
            "note": "07-records relocate to (g-1)*0x1000 + signed16(X) + 4 "
                    "(uniform for all streams 1..234); 02-records patch the "
                    "imm16 of a DS data-selector load for the target object",
        },
        "outputs": {
            "flat": f"flat/{MAIN_EXE}.flat",
            "size": size,
        },
    }

    flat_dir = lib.flat_dir(cfg)
    flat_out = flat_dir / f"{MAIN_EXE}.flat"
    lib.ensure_dir(flat_dir)
    flat_out.write_bytes(flat)

    if verify["mismatches"] or len(verify["off_buffer"]) != 1:
        lib.note(f"record cross-check FAILED: "
                 f"{len(verify['mismatches'])} in-buffer mismatch(es), "
                 f"{len(verify['off_buffer'])} off-buffer record(s) "
                 f"(expected 1)", "red")
        return 2

    jpath, mpath = lib.report_pair(cfg, "flat_extract", data)

    rows = [
        ["image", f"0x{IMAGE_BASE_OFF:06x}..0x{image_end:06x}",
         f"{size} ({size:#x})", data["image_sha256"][:16] + "..."],
        ["record stream", f"0x{RECORD_STREAM_OFF:06x}..0x{last_end:06x}",
         total, f"{tail_zeros} zero pad bytes before the image"],
        ["cross-check", "all streams 1..234",
         f"{verify['verified']} fields match",
         f"{len(verify['off_buffer'])} off-buffer (expected 1)"],
        ["entry hint", f"0x{IMAGE_ENTRY_OFF:x} (image-relative)", "-", "Prologue_"],
    ]
    md = (f"# Flat image extraction ({MAIN_EXE})\n\n"
          + lib.md_table(["region", "range", "size / records", "notes"], rows)
          + "\n\nRecord counts by (type, op):\n\n"
          + lib.md_table(["type/op", "count"],
                         [[k, v] for k, v in sorted(counts.items())])
          + "\n\nObject id tallies: "
          + ", ".join(f"obj {k} = {v}" for k, v in sorted(by_obj.items()))
          + "\n\nEmpty streams: "
          + ", ".join(str(g) for g in empty_streams)
          + f"\n\nOff-buffer records: {verify['off_buffer']}\n")
    lib.write_md(mpath, md)
    lib.note(f"sliced {size} bytes ({size:#x}) -> {flat_out}", "green")
    lib.note(f"record cross-check: {verify['verified']} verified, "
             f"{len(verify['off_buffer'])} off-buffer", "green")
    lib.note(f"report -> {jpath}", "green")
    return 0


if __name__ == "__main__":
    sys.exit(main())
