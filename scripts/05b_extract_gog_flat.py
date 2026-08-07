#!/usr/bin/env python3
"""Stage 05b: slice the flat 32-bit image out of the GOG-build FRAGILE.EXE.

The GOG retail install (gitignored analysis input, `Fragile Allegiance/`) ships
a *different build* of FRAGILE.EXE than the reference ISO (1,612,039 B vs
1,525,267 B). It is a DOS/4G *bound* image of the same shape as the ISO build
(page table, offset table, relocation record stream, pre-linked flat image),
but with different anchors and 261 pages instead of 234.

This stage locates every structural anchor **dynamically** (no hardcoded
offsets): the "unbound" marker, the offset table, the record stream base and
the flat-image base are derived from the file itself, then the whole record
stream is parsed with the verified grammar (stage 05 / dos4gw-bound.md) and
every in-buffer field is cross-checked against the sliced image. The image is
pre-linked at base 0, so a correct slice verifies 100 %; any mismatch fails
loudly instead of producing a garbage slice.

Why a separate stage: the GOG tree is optional input (unlike the ISO), so the
stage is a standalone target (`make gog-flat`), not part of `make all`.

Outputs (derived, gitignored):
  build/flat/FRAGILE.EXE.gog.flat
  build/reports/flat_extract_gog.json / flat_extract_gog.md
"""
from __future__ import annotations

import json
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import fragile_decomp_lib as lib

# Record grammar (identical to stage 05; see docs/dataformats/dos4gw-bound.md):
#   07 <type:u8> <X:u16> <obj:u8> <Y>     type 0x10 -> Y is u32 (9 bytes),
#                                        type 0x00 -> Y is u16 (7 bytes)
#   02 <type:u8> <X:u16> <obj:u8>         (5 bytes, no Y)
# Stream g relocates into page (g-1): field = (g-1)*0x1000 + signed16(X) + 4.
GR = struct.Struct("<BBHB")

# Trap signature of the image start: four zero bytes then an int3/jmp trap.
IMAGE_TRAP = b"\x00\x00\x00\x00\xcc\xeb\xfd"

# The GOG build's flat image hash (verified 2026-08-07). Pin it so a swapped
# or re-downloaded GOG build fails loudly instead of silently changing results.
GOG_FLAT_SHA256 = "4e8d2d964e04197bba28dbd843a5bf334131aaf9c8244c57df9fc6187906a9d4"
GOG_FLAT_SIZE = 0x1041A7


def signed16(x: int) -> int:
    return x - 0x10000 if x >= 0x8000 else x


def find_anchors(f: bytes) -> dict:
    """Locate the bound-image anchors without hardcoded offsets."""
    ub = f.find(b"unbound")
    if ub < 0x30000:
        raise ValueError(f"DOS/4G 'unbound' marker not in loader region ({ub:#x})")
    # Offset table starts right after the NUL-terminated marker.
    ot = ub + 7
    # Read offset entries while they are monotonically non-decreasing.
    # Entry 0 is a 0 sentinel; stream g spans [off[g], off[g+1]); the last
    # entry is the one-past-end of the final stream. The raw run can run a few
    # entries past the real table when stream bytes happen to be monotonic, so
    # the true table length is chosen below by matching the zero padding
    # before the image.
    offs = []
    for i in range(512):
        v = struct.unpack_from("<I", f, ot + 4 * i)[0]
        if offs and v < offs[-1]:
            break
        offs.append(v)
    if len(offs) < 4 or offs[0] != 0:
        raise ValueError(f"offset table at {ot:#x} does not start with a "
                         f"0 sentinel ({offs[:4]})")
    # Image candidates: every trap signature after the offset table. For each
    # candidate N (entries in the table), the record stream must end exactly
    # at the image base with zero padding in between.
    trap = f.find(IMAGE_TRAP, ot + 4 * len(offs))
    while trap >= 0:
        for n in range(len(offs) - 1, 3, -1):
            end = ot + 4 * n + offs[n - 1]
            if end <= trap and f[end:trap] == b"\x00" * (trap - end):
                return {
                    "unbound": ub,
                    "page_table": _page_table_start(f, ub),
                    "offset_table": ot,
                    "offset_entries": n,
                    "streams": n - 2,
                    "stream_base": ot + 4 * n,
                    "last_stream_end": end,
                    "zero_pad_bytes": trap - end,
                    "image_base": trap,
                }
        trap = f.find(IMAGE_TRAP, trap + 1)
    raise ValueError("no offset-table length matches the zero padding before "
                     "a flat-image trap signature")


def _page_table_start(f: bytes, ub: int) -> int:
    """Longest backward run of sequential dwords 0,1,2,… ending before the
    marker (report-only; the offset table is the authoritative structure).

    The table start is not 4-aligned (0x…BE in both builds), so all four
    dword residues near the marker are tried and the longest sequential run
    wins.
    """
    best_run = 0
    best_start = 0
    for r in range(4):
        a = ub - 0x20 - ((ub - 0x20 - r) % 4)
        v = struct.unpack_from("<I", f, a)[0]
        if v > 0x400:
            continue
        run = 0
        i = a
        while i - 4 >= 0x30000:
            prev = struct.unpack_from("<I", f, i - 4)[0]
            if prev != v - run - 1:
                break
            run += 1
            i -= 4
        if run > best_run:
            best_run = run
            best_start = i
    return best_start if best_run else 0


def parse_streams(f: bytes, a: dict) -> tuple[dict, bytes]:
    """Parse all streams and cross-check every 07-record against the image."""
    offs = [struct.unpack_from("<I", f, a["offset_table"] + 4 * i)[0]
            for i in range(a["offset_entries"])]
    img = a["image_base"]
    flat = f[img:]
    base = a["stream_base"]
    total = verified = bad = offbuf = n02 = 0
    empty = []
    by_type = {"0x10": 0, "0x00": 0}
    bad_list: list[list] = []
    for g in range(1, a["streams"] + 1):
        seg = f[base + offs[g]:base + offs[g + 1]]
        if not seg:
            empty.append(g)
            continue
        p = 0
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
                    raise ValueError(f"07-record with type {t:#x} at {p:#x}")
                fp = (g - 1) * 0x1000 + signed16(x) + 4
                total += 1
                by_type["0x10" if t == 0x10 else "0x00"] += 1
                if fp + 4 <= len(flat):
                    st = struct.unpack_from("<I", flat, fp)[0]
                    ok = (st == y) if t == 0x10 else ((st & 0xFFFF) == y)
                    if ok:
                        verified += 1
                    else:
                        bad += 1
                        bad_list.append([g, f"{x:#06x}", f"{fp:#08x}",
                                         f"{y:#010x}", f"{st:#010x}"])
                else:
                    offbuf += 1
                p += sz
            elif b0 == 0x02:
                n02 += 1
                p += 5
            else:
                raise ValueError(f"unexpected record opcode {b0:#x} at {p:#x}")
    return {
        "07_records": total,
        "02_records": n02,
        "verified": verified,
        "mismatches": bad_list,
        "off_buffer": offbuf,
        "empty_streams": empty,
        "by_type": by_type,
    }, flat


def main() -> int:
    cfg = lib.load_config()
    exe = lib._path(cfg, "gog_exe") if cfg.get("paths", {}).get("gog_exe") \
        else None
    if exe is None or not exe.is_file():
        lib.note(f"GOG build not found ({exe}); expected the gitignored "
                 f"'Fragile Allegiance/' retail install tree", "red")
        return 2

    f = exe.read_bytes()
    if f[:2] != b"MZ":
        lib.note(f"{exe} is not an MZ executable", "red")
        return 2

    try:
        anchors = find_anchors(f)
        stats, flat = parse_streams(f, anchors)
    except ValueError as exc:
        lib.note(f"anchor/stream validation failed: {exc}", "red")
        return 2

    sha = lib.sha256_bytes(flat)
    problems = []
    if len(flat) != GOG_FLAT_SIZE:
        problems.append(f"image size {len(flat):#x} != expected {GOG_FLAT_SIZE:#x}")
    if sha != GOG_FLAT_SHA256:
        problems.append(f"image sha256 {sha[:16]}… != pinned {GOG_FLAT_SHA256[:16]}…")
    if stats["mismatches"] or stats["off_buffer"] != 1:
        problems.append(f"record cross-check: {len(stats['mismatches'])} "
                        f"mismatch(es), {stats['off_buffer']} off-buffer "
                        f"(expected 1)")
    if problems:
        for p in problems:
            lib.note(f"validation failed: {p}", "red")
        return 2

    flat_dir = lib.flat_dir(cfg)
    lib.ensure_dir(flat_dir)
    flat_out = flat_dir / "FRAGILE.EXE.gog.flat"
    flat_out.write_bytes(flat)

    data = {
        "source": str(exe.relative_to(lib.ROOT)),
        "source_size": len(f),
        "anchors": {k: (f"{v:#x}" if isinstance(v, int) else v)
                    for k, v in anchors.items()},
        "image": {
            "size": len(flat),
            "sha256": sha,
        },
        "streams": {
            "records_07": stats["07_records"],
            "records_02": stats["02_records"],
            "verified": stats["verified"],
            "off_buffer": stats["off_buffer"],
            "empty_streams": len(stats["empty_streams"]),
            "empty_stream_list": stats["empty_streams"],
            "by_type": stats["by_type"],
        },
        "outputs": {"flat": "flat/FRAGILE.EXE.gog.flat"},
        "note": "The GOG build's stat tables are real data in the flat "
                "(see stage 12 / docs/dataformats/gog-build-data.md); the ISO "
                "build materialises them at runtime instead.",
    }

    jpath, mpath = lib.report_pair(cfg, "flat_extract_gog", data)
    rows = [
        ["source", str(exe.relative_to(lib.ROOT)), f"{len(f)} B", "GOG retail build"],
        ["unbound marker", f"0x{anchors['unbound']:06x}", "-", "DOS/4G bound signature"],
        ["page table", f"0x{anchors['page_table']:06x}", "-", "sequential dwords"],
        ["offset table", f"0x{anchors['offset_table']:06x}",
         f"{anchors['offset_entries']} entries", f"{anchors['streams']} streams"],
        ["record stream", f"0x{anchors['stream_base']:06x}.."
         f"0x{anchors['last_stream_end']:06x}",
         f"{stats['07_records']} + {stats['02_records']} records",
         f"{anchors['zero_pad_bytes']} zero pad bytes before the image"],
        ["flat image", f"0x{anchors['image_base']:06x}..EOF",
         f"{len(flat):#x} B", sha[:16] + "…"],
        ["cross-check", f"streams 1..{anchors['streams']}",
         f"{stats['verified']} fields match",
         f"{stats['off_buffer']} off-buffer (expected 1)"],
    ]
    md = (f"# Flat image extraction (GOG build, FRAGILE.EXE)\n\n"
          + lib.md_table(["region", "range", "size / records", "notes"], rows)
          + f"\n\nRecord counts by relocation type: {stats['by_type']}.\n"
          + f"\nEmpty streams: {len(stats['empty_streams'])}"
          + (f" ({', '.join(str(g) for g in stats['empty_streams'])})" if
             stats["empty_streams"] else "")
          + "\n")
    lib.write_md(mpath, md)
    lib.note(f"sliced {len(flat)} bytes ({len(flat):#x}) -> {flat_out}", "green")
    lib.note(f"record cross-check: {stats['verified']} verified, "
             f"{stats['off_buffer']} off-buffer", "green")
    lib.note(f"report -> {jpath}", "green")
    return 0


if __name__ == "__main__":
    sys.exit(main())
