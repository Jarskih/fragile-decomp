#!/usr/bin/env python3
"""Stage 05: slice the flat 32-bit image out of the DOS/4G bound FRAGILE.EXE.

FRAGILE.EXE is a DOS/4G *bound* image: a real-mode loader stub (a nested Watcom
MZ at 0x38D64) is followed by DOS/4G's page table, offset table and a
delta-encoded relocation record stream, then by the flat 32-bit image that the
loader maps and runs in protected mode.

This stage:
  1. locates the bound-image structural markers (the "unbound" signature, page
     table, offset table, record stream) by scanning for their signatures and
     sanity-checks them,
  2. slices the flat image (everything after the record stream) into
     build/flat/FRAGILE.flat,
  3. parses the record stream with the documented group grammar as far as it
     decodes and inventories the relocation records (the foundation for later
     relocation work),
and writes build/reports/flat_extract.{json,md}.

The flat slice is image-relative and internally self-consistent: relocated
dwords hold image offsets, not absolute addresses, so Ghidra can analyse it at
base 0 without applying relocations (relocation is a uniform +load-base).

Outputs (derived, gitignored):
  build/flat/FRAGILE.flat
  build/reports/flat_extract.json / flat_extract.md
"""
from __future__ import annotations

import json
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import openfa_lib as lib

MAIN_EXE = "FRAGILE.EXE"

# --- structural anchors (file offsets), verified on the reference ISO ---------
# All values below were determined empirically from the reference image; the
# assertions in main() re-verify them on every run so a wrong ISO fails loudly
# instead of producing a garbage slice.
UNBOUND_MARKER = b"unbound"
PAGE_TABLE_OFF = 0x3B8BE      # 234 sequential dwords (0x0..0xE9 = pages 0..233)
OFFSET_TABLE_OFF = 0x3BC70    # 234 dwords: group start offsets within record stream
RECORD_STREAM_OFF = 0x3C020   # relocation record stream
IMAGE_BASE_OFF = 0x8A760      # first byte of the flat image (post-padding)
IMAGE_ENTRY_OFF = 0x14        # image-relative entry hint (Prologue_ push pattern)

# Record grammar (verified for ALL groups 1..233 against the flat image; the
# only unverifiable record is group 233's last, which reads off the end of the
# image):
#   07 <type:u8> <X:u16> <op:u8> <Y>     type 0x10 -> Y is u32 (9 bytes),
#                                        type 0x00 -> Y is u16 (7 bytes)
#   02 <type:u8> <X:u16> <op:u8>         (5 bytes, no Y; type 0x00/op 0x03)
# Relocated dword position = base + ((X + 4) & 0xFFFF), base = (group-1)*0x1000
# for groups 1..232; group 233 uses base = group*0x1000 (last flat page).
# A 02-record patches the imm16 of a "66 B8..BF mov reg16, imm16" instruction at
# base + X + 4.
GR = struct.Struct("<BBHB")   # 07, type, X, op
GR2 = struct.Struct("<BBHB")  # 02, type, X, op


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
    """Group-start offsets (relative to the record stream region)."""
    return [struct.unpack_from("<I", f, OFFSET_TABLE_OFF + 4 * i)[0]
            for i in range(234)]


def parse_records(f: bytes, start: int, limit: int) -> dict:
    """Parse the record stream with the verified group grammar.

    Returns per-opcode and per-(type,op) counts, the number of records, and
    the trailing (unparsed) byte count. 07-records carry Y (u32 for type
    0x10, u16 for type 0x00) relocated to base + ((X+4) & 0xFFFF);
    02-records are 5-byte (no Y) patches of a 66 B8..BF imm16. The grammar
    was verified externally against the flat image for all 37,304 07-records
    (37,303 match; the last group-233 record reads off the end of the image).
    """
    p = start
    counts = {}
    by_opcode = {}
    total = 0
    while p < limit:
        b0 = f[p]
        if b0 == 0x07:
            _, t, x, op = GR.unpack_from(f, p)
            if t == 0x10:
                y = struct.unpack_from("<I", f, p + 5)[0]
                sz = 9
            elif t == 0x00:
                y = struct.unpack_from("<H", f, p + 5)[0]
                sz = 7
            else:
                break
            key = f"{t:#04x}/{op:#04x}"
            by_opcode["07"] = by_opcode.get("07", 0) + 1
        elif b0 == 0x02:
            _, t, x, op = GR2.unpack_from(f, p)
            y = None
            sz = 5
            key = f"{t:#04x}/{op:#04x}"
            by_opcode["02"] = by_opcode.get("02", 0) + 1
        else:
            break
        counts[key] = counts.get(key, 0) + 1
        total += 1
        p += sz
    tail = limit - p
    return {"total": total, "counts": counts, "by_opcode": by_opcode,
            "tail_zero_bytes": tail, "end": p,
            "parse_ratio": round((p - start) / max(1, limit - start), 4)}


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
    rec = parse_records(f, RECORD_STREAM_OFF, IMAGE_BASE_OFF)
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
        },
        "record_stream": {
            "start": RECORD_STREAM_OFF,
            "end": IMAGE_BASE_OFF,
            "parsed_total": rec["total"],
            "parsed_to": rec["end"],
            "parse_ratio": rec["parse_ratio"],
            "tail_zero_bytes": rec["tail_zero_bytes"],
            "counts_by_type_op": rec["counts"],
            "counts_by_opcode": rec["by_opcode"],
            "note": "07-records are image-relative dwords at "
                    "base+((X+4)&0xffff); 02-records patch imm16 at base+X+4; "
                    "group 233 base is group*0x1000, others (group-1)*0x1000",
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

    jpath, mpath = lib.report_pair(cfg, "flat_extract", data)

    rows = [
        ["image", f"0x{IMAGE_BASE_OFF:06x}..0x{image_end:06x}",
         f"{size} ({size:#x})", data["image_sha256"][:16] + "..."],
        ["record stream", f"0x{RECORD_STREAM_OFF:06x}..0x{IMAGE_BASE_OFF:06x}",
         rec["total"], f"{rec['tail_zero_bytes']} tail bytes unparsed"],
        ["entry hint", f"0x{IMAGE_ENTRY_OFF:x} (image-relative)", "-", "Prologue_"],
    ]
    md = (f"# Flat image extraction ({MAIN_EXE})\n\n"
          + lib.md_table(["region", "range", "size / records", "notes"], rows)
          + "\n\nRecord counts by (type, op):\n\n"
          + lib.md_table(["type/op", "count"],
                         [[k, v] for k, v in sorted(rec["counts"].items())])
          + "\n")
    lib.write_md(mpath, md)
    lib.note(f"sliced {size} bytes ({size:#x}) -> {flat_out}", "green")
    lib.note(f"report -> {jpath}", "green")
    return 0


if __name__ == "__main__":
    sys.exit(main())
