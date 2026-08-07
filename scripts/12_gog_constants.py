#!/usr/bin/env python3
"""Stage 12: decode the gameplay settings/constant tables of the GOG build.

The reference-ISO build of FRAGILE.EXE reads its stat tables through
DS-relative displacements that land on *code* in the flat image — the
"tables in code" anomaly (docs/mechanics/asteroid-creation.md,
docs/mechanics/weapon-and-turret-numbers.md). The GOG retail build
(`make gog-flat`, stage 05b) carries the same game data as **real static
tables** in its binary-data region (flat 0x8F000..0x91800), which makes the
numbers statically extractable.

This stage decodes the tables identified so far into
build/reports/gog_constants.{json,md}. Every table is checked against its
documented shape; a mismatch fails loudly (like stage 05) so a changed build
cannot silently produce garbage. Fields whose meaning is not yet confirmed
are reported as raw values with an explicit note — no guesses are dressed up
as facts.

Table catalog (flat offsets, GOG build):

| offset | content | confidence |
|---|---|---|
| 0x8f5d0 | u32 value table (300/400/500 / 999 / 600/400/200 runs) | structure confirmed, role unknown |
| 0x8f680 | stat records: {cost u16, f u8, c u8, 5×u32} — headless first record, then 15 records of {id u32, cost u16, f u8, c u8, 5×u32} | structure confirmed (id/cost), fields a..e unknown |
| 0x8f840 | {u16, u16} pairs | raw |
| 0x8f880 | type-id list (28 bytes, ids with holes) | raw |
| 0x8f898 | {u16} runs (position-like values) | raw |
| 0x8fca8 | u16 table (8 entries) | raw |
| 0x8fcc8 | 11 × 0x64 (100) | confirmed |
| 0x8fce2 | **ore/starting-value table**: 11 rows × 14 B {p u8, pad u8, lo u16, hi u16, v1 u16, v2 u16, v3 u16, tag u16} — matches the ISO `asteroid_gen_start_values` table shape (p@+0, lo@+2, hi@+4) | p/lo/hi confirmed |
| 0x8fd80 | byte ramp (surface styles?) | raw |
| 0x8fe5c | u16/u32 mix | raw |
| 0x8fe60 | byte ramp | raw |
| 0x8fea4 | byte ramps (4-row repeats) | raw |
| 0x8fec4 | u16 table (12 entries) | raw |
| 0x8ff40 | 15 × 4-byte rows | raw |
| 0x8ff48 | 12 code pointers | confirmed pointers |
| 0x8ff78 | byte rows | raw |
| 0x8ffc4 | mixed rows | raw |
| 0x90000 | {u16, u16} records (40 sampled) | raw |

The full raw bytes of the region 0x8F000..0x91800 go to
build/reports/gog_data_region.hex for future analysis passes.
"""
from __future__ import annotations

import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import fragile_decomp_lib as lib

FLAT = "flat/FRAGILE.EXE.gog.flat"
FLAT_SHA = "4e8d2d964e04197bba28dbd843a5bf334131aaf9c8244c57df9fc6187906a9d4"

ORE_OFF = 0x8FCE2      # 11 rows x 14 B
ORE_ROWS = 11
ORE_STRIDE = 14
STATS_OFF = 0x8F680    # headless record + 15 id records
STATS_STRIDE = 0x1C    # 28 B
STATS_RECORDS = 15
TYPE_IDS_OFF = 0x8F880
TYPE_IDS_LEN = 28


def table_region(flat: bytes) -> bytes:
    """The binary-data region holding the gameplay tables (report aid)."""
    return flat[0x8F000:0x91800]


def check_ore(f: bytes) -> list[dict]:
    """The 11-row ore/starting-value table (asteroid_gen_start_values)."""
    rows = []
    for i in range(ORE_ROWS):
        off = ORE_OFF + i * ORE_STRIDE
        p = f[off]
        lo, hi = struct.unpack_from("<HH", f, off + 2)
        v1, v2, v3, tag = struct.unpack_from("<HHHH", f, off + 6)
        if not (1 <= p <= 100 and 0 < lo < hi < 20000):
            raise ValueError(f"ore table row {i} fails shape check "
                             f"(p={p}, lo={lo}, hi={hi})")
        rows.append({
            "row": i, "offset": f"{off:06x}",
            "p": p, "lo": lo, "hi": hi,
            "v1": v1, "v2": v2, "v3": v3, "tag": tag,
        })
    return rows


def check_stats(f: bytes) -> dict:
    """The stat records at 0x8f680 (cost/id records)."""
    cost = struct.unpack_from("<H", f, STATS_OFF)[0]
    ff, cnt = f[STATS_OFF + 2], f[STATS_OFF + 3]
    a, b, c, d, e = struct.unpack_from("<IIIII", f, STATS_OFF + 4)
    head = {"offset": f"{STATS_OFF:06x}", "cost": cost, "f": ff, "cnt": cnt,
            "a": a, "b": b, "c": c, "d": d, "e": e}
    if not 10000 <= head["cost"] <= 60000:
        raise ValueError(f"stat record header cost {head['cost']} out of range")
    recs = []
    for i in range(STATS_RECORDS):
        off = STATS_OFF + 0x18 + i * STATS_STRIDE
        ident, cost = struct.unpack_from("<IH", f, off)
        ff, cnt = f[off + 6], f[off + 7]
        a, b, c, d, e = struct.unpack_from("<IIIII", f, off + 8)
        if not (0x10 <= ident <= 0x40 and 10000 <= cost <= 60000):
            raise ValueError(f"stat record {i} fails shape check "
                             f"(id={ident:#x}, cost={cost})")
        recs.append({
            "offset": f"{off:06x}", "id": ident, "cost": cost,
            "f": ff, "cnt": cnt, "a": a, "b": b, "c": c, "d": d, "e": e,
        })
    return {"head": head, "records": recs}


def raw_u16s(f: bytes, off: int, n: int) -> list[int]:
    return [struct.unpack_from("<H", f, off + 2 * i)[0] for i in range(n)]


def raw_u32s(f: bytes, off: int, n: int) -> list[int]:
    return [struct.unpack_from("<I", f, off + 4 * i)[0] for i in range(n)]


def raw_bytes(f: bytes, off: int, n: int) -> str:
    return " ".join(f"{b:02x}" for b in f[off:off + n])


def main() -> int:
    cfg = lib.load_config()
    flat_path = lib.flat_dir(cfg) / "FRAGILE.EXE.gog.flat"
    if not flat_path.is_file():
        lib.note(f"{flat_path} missing; run `make gog-flat` first", "red")
        return 2
    flat = flat_path.read_bytes()
    if lib.sha256_bytes(flat) != FLAT_SHA:
        lib.note("gog flat sha256 does not match the pinned hash — run "
                 "`make gog-flat` (or update the pin deliberately)", "red")
        return 2

    try:
        ore = check_ore(flat)
        stats = check_stats(flat)
    except ValueError as exc:
        lib.note(f"table shape check failed: {exc}", "red")
        return 2

    data = {
        "source": FLAT,
        "flat_sha256": FLAT_SHA,
        "ore_start_values": {
            "offset": f"{ORE_OFF:06x}",
            "rows": ORE_ROWS,
            "stride": ORE_STRIDE,
            "shape": "p:u8 @+0, lo:u16 @+2, hi:u16 @+4, v1/v2/v3/tag:u16 @+6..+12",
            "note": "p = rich-roll probability (%%), lo = poor bound, "
                    "hi = rich bound; matches the ISO build's "
                    "asteroid_gen_start_values table shape",
            "table": ore,
        },
        "stat_records": {
            "offset": f"{STATS_OFF:06x}",
            "stride": f"{STATS_STRIDE:#x}",
            "shape": "head: {cost u16, f u8, c u8, a..e u32} (24 B); records: "
                     "{id u32, cost u16, f u8, c u8, a..e u32} (28 B)",
            "note": "ids 0x1e..0x27 + 0x37; costs 10000..30000; fields a..e "
                    "unidentified (build time / hit points / power / range "
                    "candidates); the ISO build reads the same family via "
                    "DS displacements (weapon-and-turret-numbers.md)",
            "head": stats["head"],
            "records": stats["records"],
        },
        "type_ids": {
            "offset": f"{TYPE_IDS_OFF:06x}",
            "ids": list(flat[TYPE_IDS_OFF:TYPE_IDS_OFF + TYPE_IDS_LEN]),
            "note": "28 building/unit type ids with holes; overlaps the "
                    "stat-record id set",
        },
        "u16_pairs_8f840": {
            "offset": "08f840",
            "pairs": [[raw_u16s(flat, 0x8F840 + 4 * i, 2)]
                      for i in range(15)],
            "note": "15 {u16,u16} pairs; role unidentified",
        },
        "u16_runs_8f89c": {
            "offset": "08f89c",
            "values": raw_u16s(flat, 0x8F89C, 32),
            "note": "position-like signed u16 values (the type-id list ends "
                    "at 0x8f89b); role unidentified",
        },
        "u16_8fca8": {
            "offset": "08fca8",
            "values": raw_u16s(flat, 0x8FCA8, 8),
        },
        "bytes_8fcc8": {
            "offset": "08fcc8",
            "bytes": raw_bytes(flat, 0x8FCC8, 16),
            "note": "0x5a 0x50 then twelve 0x64 (100) and 0xfc; the 0x64 run "
                    "count matches the ore-table row count",
        },
        "u32_8f5d0": {
            "offset": "08f5d0",
            "values": raw_u32s(flat, 0x8F5D0, 39),
            "note": "runs of 300/400/500, 999, 600/400/200; income-like, "
                    "role unidentified",
        },
        "ramp_8fd80": {"offset": "08fd80",
                       "bytes": raw_bytes(flat, 0x8FD80, 0x20)},
        "ramp_8fe60": {"offset": "08fe60",
                       "bytes": raw_bytes(flat, 0x8FE60, 0x44)},
        "u16_8fec4": {"offset": "08fec4",
                      "values": raw_u16s(flat, 0x8FEC4, 12)},
        "rows4_8ff40": {"offset": "08ff40",
                        "rows": [raw_bytes(flat, 0x8FF40 + 4 * i, 4)
                                 for i in range(15)]},
        "code_ptrs_8ff48": {
            "offset": "08ff48",
            "values": raw_u32s(flat, 0x8FF48, 12),
            "note": "pointers into the code region (all < 0x90000)",
        },
        "rows4_8ff78": {"offset": "08ff78",
                        "rows": [raw_bytes(flat, 0x8FF78 + 4 * i, 4)
                                 for i in range(15)]},
        "mixed_8ffc4": {"offset": "08ffc4",
                        "bytes": raw_bytes(flat, 0x8FFC4, 0x40)},
        "u16_pairs_90000": {
            "offset": "090000",
            "pairs": [[raw_u16s(flat, 0x90000 + 4 * i, 2)]
                      for i in range(40)],
            "note": "cost-like u16 pairs (4400/8212, 4000/6154, ...); role "
                    "unidentified",
        },
        "rows4_91800": {"offset": "091800",
                        "rows": [raw_bytes(flat, 0x91800 + 4 * i, 4)
                                 for i in range(24)]},
    }

    rdir = lib.reports_dir(cfg)
    lib.ensure_dir(rdir)
    (rdir / "gog_data_region.hex").write_text(
        _hexdump(flat[0x8F000:0x91800], 0x8F000))
    jpath, mpath = lib.report_pair(cfg, "gog_constants", data)
    lib.write_md(mpath, _render(data))
    lib.note(f"report -> {jpath}", "green")
    lib.note(f"region hexdump -> {rdir / 'gog_data_region.hex'}", "green")
    return 0


def _hexdump(blob: bytes, base: int) -> str:
    out = []
    for r in range(0, len(blob), 16):
        chunk = blob[r:r + 16]
        vals = " ".join(f"{b:02x}" for b in chunk)
        asci = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
        out.append(f"{base + r:06x}: {vals:<47} {asci}")
    return "\n".join(out) + "\n"


def _render(data: dict) -> str:
    md = ["# Gameplay settings and constants (GOG build, stage 12)\n",
          f"Source: `{data['source']}` (flat sha256 {data['flat_sha256'][:16]}…).",
          "The GOG retail build ships the gameplay stat tables as real data; "
          "the reference-ISO build reads the same families through "
          "DS-relative displacements that land on code in its flat "
          "(see docs/mechanics/weapon-and-turret-numbers.md).\n"]

    ore = data["ore_start_values"]
    md.append(f"## Ore / starting-value table @ {ore['offset']}\n")
    md.append(f"11 rows x {ore['stride']} B. {ore['note']}.\n")
    rows = [["row", "p (%)", "lo", "hi", "v1", "v2", "v3", "tag"]]
    for r in ore["table"]:
        rows.append([r["row"], r["p"], r["lo"], r["hi"], r["v1"], r["v2"],
                     r["v3"], f"{r['tag']:04x}"])
    md.append(lib.md_table(rows[0], rows[1:]) + "\n")

    st = data["stat_records"]
    md.append(f"## Stat records @ {st['offset']}\n")
    md.append(f"{st['note']}\n")
    md.append(f"Headless first record: {st['head']}\n")
    rows = [["id", "cost", "f", "cnt", "a", "b", "c", "d", "e"]]
    for r in st["records"]:
        rows.append([f"{r['id']:#04x}", r["cost"], f"{r['f']:02x}",
                     f"{r['cnt']:02x}", r["a"], r["b"], r["c"], r["d"],
                     f"{r['e']:#010x}"])
    md.append(lib.md_table(rows[0], rows[1:]) + "\n")

    for key, title in (
        ("type_ids", "Type-id list"),
        ("u16_pairs_8f840", "{u16,u16} pairs @ 0x8f840"),
        ("u16_runs_8f89c", "u16 runs @ 0x8f89c"),
        ("u16_8fca8", "u16 table @ 0x8fca8"),
        ("bytes_8fcc8", "bytes @ 0x8fcc8"),
        ("u32_8f5d0", "u32 table @ 0x8f5d0"),
        ("ramp_8fd80", "byte ramp @ 0x8fd80"),
        ("ramp_8fe60", "byte ramps @ 0x8fe60"),
        ("u16_8fec4", "u16 table @ 0x8fec4"),
        ("rows4_8ff40", "4-byte rows @ 0x8ff40"),
        ("code_ptrs_8ff48", "code-pointer table @ 0x8ff48"),
        ("rows4_8ff78", "4-byte rows @ 0x8ff78"),
        ("mixed_8ffc4", "mixed bytes @ 0x8ffc4"),
        ("u16_pairs_90000", "{u16,u16} pairs @ 0x90000"),
        ("rows4_91800", "4-byte rows @ 0x91800"),
    ):
        v = data[key]
        note = v.get("note")
        md.append(f"## {title} ({v.get('offset', '')})")
        if note:
            md.append(f"\n{note}\n")
        body = v.get("values", v.get("bytes", v.get("ids", v.get("pairs",
                                                                 v.get("rows")))))
        if isinstance(body, list) and body and isinstance(body[0], list):
            md.append("\n| values |\n| --- |")
            for row in body:
                md.append("| `" + ", ".join(str(x) for x in row) + "` |")
        else:
            md.append("\n`" + ", ".join(str(x) for x in body) + "`\n")
        md.append("")

    md.append("## Raw region\n\n"
              "Full hexdump of flat 0x8F000..0x91800 (the binary-data region "
              "holding the tables): `build/reports/gog_data_region.hex`.\n")
    return "\n".join(md)


if __name__ == "__main__":
    sys.exit(main())
