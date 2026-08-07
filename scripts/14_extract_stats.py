#!/usr/bin/env python3
"""Stage 14: extract the gameplay stat tables from a runtime memory dump.

`make memdump-all` snapshots the emulated RAM of the running game
(build/dumps/ram_*.bin). This stage decodes from those dumps the tables the
game actually uses:

1. The static stat tables (ore/start-values, stat records, type-id list and
   the auxiliary tables of the binary-data region) — verified byte-identical
   against the flat, at their runtime addresses (the stage-13 cross-check,
   repeated here as part of the stats report).

2. The per-type runtime tables the game materialises **at game start** into
   the code region (the "tables in code" family — displacement reads are
   relocated to absolute linear addresses `image_base + displacement`, and the
   startup code overwrites those code-region offsets with data):

   | runtime table | stride | content (from the read sites) |
   |---|---|---|
   | `0xab60` | 0x14 | per-type records: +0 count/limit byte, +9 count byte (== 8 test), +0x5 byte (`0xab65`) |
   | `0xab5e`/`0xab5f` | 4 | per-type bytes (overlapping views of the same region) |
   | `0x98a2` | 0x0e | per-type byte table (ore-ish, `type*0x0e`) |
   | `0xcb4e`/`0xcb5d` | 8 | per-type flag/counter words (`orb`/`andb`/`incb` sites) |
   | `0xbd58`..`0xbe0c` | 4 | per-race u32 finance pools (six pools) |
   | `0xc6b0` | — | global (node-type comparison value) |

   A dump taken at the **main menu does not contain these tables** — the code
   bytes are still in place (only relocations differ from the flat). The
   materialisation happens when a game is started. This stage detects that:
   if the table offsets still hold the flat's bytes, the report says so and
   the tables are left undecoded (a colony-view dump is required — start a
   game, then re-run `make memdump-all` + `make stats`).

3. The startup-materialised state that IS present in any dump (palette ramps,
   format strings, player names) — carried over from the stage-13 region diff.

Outputs (derived, gitignored):
  build/reports/stats.json / stats.md
"""
from __future__ import annotations

import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import fragile_decomp_lib as lib
import dump_constants as dc13  # stage 13 helpers: image locate, reloc bases, write diff

FLAT = "flat/FRAGILE.EXE.gog.flat"
FLAT_SHA = "4e8d2d964e04197bba28dbd843a5bf334131aaf9c8244c57df9fc6187906a9d4"

IMAGE_TRAP = b"\x00\x00\x00\x00\xcc\xeb\xfd"

# Static tables (flat offsets; runtime = flat - 0x1000 because the DOS/4G stub
# page is not mapped). Stage-12 shapes.
ORE_OFF = 0x8FCE2      # 11 rows x 14 B {p u8, pad u8, lo u16, hi u16, v1..v3 u16, tag u16}
ORE_ROWS = 11
ORE_STRIDE = 14
STATS_OFF = 0x8F680    # headless record + 15 records of 0x1C
STATS_STRIDE = 0x1C
STATS_RECORDS = 15
TYPE_IDS_OFF = 0x8F880
TYPE_IDS_LEN = 28

# Per-type runtime tables (flat offsets; the code reads them through
# relocations as absolute linear addresses image_base + offset). Not present
# in a main-menu dump — present only after a game has been started.
RUNTIME_TABLES = {
    "ab60": {"stride": 0x14, "rows": 40, "fields": {
        0x00: "count/limit byte",
        0x05: "byte",
        0x09: "count byte (== 8 test)",
    }},
    "98a2": {"stride": 0x0E, "rows": 40, "fields": {0x00: "per-type byte"}},
    "cb4e": {"stride": 0x08, "rows": 40, "fields": {
        0x00: "u16 flags (or/and bit ops)",
        0x0F: "byte flags (0xcb5d)",
        0x10: "byte counter (incb 0xcb5e)",
    }},
    "bd58": {"stride": 0x04, "rows": 9, "fields": {
        0x00: "per-race u32 finance pool (6 pools: 0xbd58, 0xbd7c, 0xbda0, "
              "0xbdc4, 0xbde8, 0xbe0c)",
    }},
}

TYPE_NAMES = {
    0: "Unknown (type 0)",
    1: "?",
    2: "?",
    3: "Anti-Missile Pod",
    4: "?",
    5: "?",
    6: "?",
    7: "?",
    8: "Mine (deposit)",
    9: "Satellite Silo",
    10: "Screen Generator",
    14: "Missile Silo",
    17: "Plasma Turret",
    18: "Photon Turret",
    27: "Laser Turret",
    28: "Solar Matrix",
    33: "Protected Storage Tower",
}

# Text-index names come from _TEXT/AMERICAN.TXT via docs/mechanics; the
# type-byte -> text-index mapping is only partially confirmed (see
# turrets-and-defence.md), so names are hints, not facts.


def find_dump(cfg: dict, flat: bytes) -> Path | None:
    """The dump that actually contains the loaded game image.

    `make memdump-all` writes one file per region; the marker region (with
    the image) is not the alphabetically last one, so scan for the image
    trap signature directly.
    """
    ddir = lib._path(cfg, "build_dir") / "dumps"
    if not ddir.is_dir():
        return None
    for f in sorted(ddir.glob("ram_*.bin")):
        data = f.read_bytes()
        if locate_image(data, flat) is not None:
            return f
    return None


def locate_image(data: bytes, flat: bytes) -> int | None:
    pos = 0
    while True:
        i = data.find(IMAGE_TRAP, pos)
        if i < 0:
            return None
        img = i
        if data[img + 0x04:img + 0x0B] == flat[0x04:0x0B] and \
                data[img + 0x14:img + 0x1A] == flat[0x14:0x1A]:
            return img
        pos = i + 1


def rt_off(fp: int) -> int:
    return fp if fp < 0x86000 else fp - 0x1000


def static_tables(rt: bytes, flat: bytes) -> dict:
    """The binary-data-region tables at their runtime addresses, verified."""
    out = {}

    o = rt_off(ORE_OFF)
    rows = []
    ok = True
    for i in range(ORE_ROWS):
        p = rt[o + i * ORE_STRIDE]
        lo, hi = struct.unpack_from("<HH", rt, o + i * ORE_STRIDE + 2)
        v1, v2, v3, tag = struct.unpack_from("<HHHH", rt, o + i * ORE_STRIDE + 6)
        if rt[o + i * ORE_STRIDE:o + (i + 1) * ORE_STRIDE] != \
                flat[ORE_OFF + i * ORE_STRIDE:ORE_OFF + (i + 1) * ORE_STRIDE]:
            ok = False
        rows.append({"row": i, "p": p, "lo": lo, "hi": hi,
                     "v1": v1, "v2": v2, "v3": v3, "tag": tag})
    out["ore_start_values"] = {
        "runtime_offset": f"{o:06x}",
        "rows": rows,
        "verified_identical": ok,
    }

    s = rt_off(STATS_OFF)
    ok = rt[s:s + 0x18 + STATS_RECORDS * STATS_STRIDE] == \
        flat[STATS_OFF:STATS_OFF + 0x18 + STATS_RECORDS * STATS_STRIDE]
    cost = struct.unpack_from("<H", rt, s)[0]
    ff, cnt = rt[s + 2], rt[s + 3]
    a, b, c, d, e = struct.unpack_from("<IIIII", rt, s + 4)
    recs = []
    for i in range(STATS_RECORDS):
        off = s + 0x18 + i * STATS_STRIDE
        ident, rc = struct.unpack_from("<IH", rt, off)
        rf, rcnt = rt[off + 6], rt[off + 7]
        ra, rb, rc2, rd, re = struct.unpack_from("<IIIII", rt, off + 8)
        recs.append({"id": ident, "cost": rc, "f": rf, "cnt": rcnt,
                     "a": ra, "b": rb, "c": rc2, "d": rd, "e": re})
    out["stat_records"] = {
        "runtime_offset": f"{s:06x}",
        "verified_identical": ok,
        "head": {"cost": cost, "f": ff, "cnt": cnt, "a": a, "b": b,
                 "c": c, "d": d, "e": e},
        "records": recs,
    }

    t = rt_off(TYPE_IDS_OFF)
    out["type_ids"] = {
        "runtime_offset": f"{t:06x}",
        "ids": list(rt[t:t + TYPE_IDS_LEN]),
        "verified_identical":
            rt[t:t + TYPE_IDS_LEN] == flat[TYPE_IDS_OFF:TYPE_IDS_OFF + TYPE_IDS_LEN],
    }
    return out


def runtime_tables(rt: bytes, flat: bytes, written_runs: list[tuple[int, int]]
                   ) -> dict:
    """The per-type tables the game materialises at game start.

    Materialisation is detected precisely: the game's startup writes are the
    regions where the dump differs from the *relocated* image (stage-13 diff).
    In a main-menu dump no table region is written and the offsets still hold
    code bytes; in a colony-view dump the game has overwritten them.
    """
    out = {}
    for name, spec in RUNTIME_TABLES.items():
        off = int(name, 16)
        stride = spec["stride"]
        rows = spec["rows"]
        region = range(off, off + rows * stride)
        written = any(r0 <= off < r1 or off < r1 <= off + rows * stride
                      for r0, r1 in written_runs)
        got = rt[off:off + rows * stride]
        out[name] = {
            "offset": f"{off:06x}",
            "stride": f"{stride:#x}",
            "rows": rows,
            "fields": spec["fields"],
            "materialised": written,
            "note": ("game-start runtime table; present in a colony-view dump"
                     if written else
                     "main-menu dump: still holds code bytes; start a game and "
                     "re-run make memdump-all + make stats to decode"),
        }
        if written:
            out[name]["values"] = _decode_rows(got, stride, rows)
    return out


def _decode_rows(got: bytes, stride: int, rows: int) -> list:
    return [got[r * stride:(r + 1) * stride].hex(" ")
            for r in range(rows)]


def main() -> int:
    cfg = lib.load_config()
    flat_path = lib.flat_dir(cfg) / "FRAGILE.EXE.gog.flat"
    if not flat_path.is_file():
        lib.note("run `make gog-flat` first", "red")
        return 2
    flat = flat_path.read_bytes()
    if lib.sha256_bytes(flat) != FLAT_SHA:
        lib.note("gog flat sha256 mismatch — run `make gog-flat`", "red")
        return 2
    dump = find_dump(cfg, flat)
    if dump is None:
        lib.note("no dump contains the loaded game image; run `make memdump-all` "
                 "while the game is running under DOSBox(-X)", "red")
        return 2
    data = dump.read_bytes()
    img = dc13.locate_image(data, flat)
    if img is None:
        lib.note("loaded game image not found in the dump (is the game at the "
                 "main menu / colony view?)", "red")
        return 2
    rt = data[img:img + len(flat)]

    gog = (lib.ROOT / dc13.GOG_EXE_REL).read_bytes()
    bases = dc13.per_object_bases(data, gog, flat, img)
    runs = dc13.initialized_regions(rt, flat, gog, img, bases)
    written_runs = [(int(r["offset"], 16), int(r["end"], 16) + 1)
                    for r in runs]

    stats = static_tables(rt, flat)
    rts = runtime_tables(rt, flat, written_runs)

    any_materialised = any(t["materialised"] for t in rts.values())
    out = {
        "dump": str(dump.relative_to(lib.ROOT)),
        "image_dump_offset": f"{img:06x}",
        "static_tables": stats,
        "runtime_tables": rts,
        "gameplay_dump": any_materialised,
        "note": ("Per-type stat values (costs, HP, power, range, fire delay) "
                 "are materialised into the code region at game start; a "
                 "main-menu dump cannot contain them. " +
                 ("Colony-view dump detected; per-type rows decoded."
                  if any_materialised else
                  "Start a game (colony view) in DOSBox and re-run "
                  "`make memdump-all` then `make stats` to decode them.")),
    }
    lib.write_json(lib.reports_dir(cfg) / "stats.json", out)

    md = ["# Gameplay stats from the runtime dump (stage 14)\n",
          f"Dump: `{out['dump']}` (image at dump offset {img:#x}).\n"]

    st = stats
    md.append("## Static tables (verified in memory)\n")
    md.append("Ore / starting-value table @ runtime "
              f"{st['ore_start_values']['runtime_offset']}: "
              f"{'identical to the flat' if st['ore_start_values']['verified_identical'] else 'DIFFERS!'}.\n")
    rows = [["row", "p (%)", "lo", "hi", "v1", "v2", "v3", "tag"]]
    for r in st["ore_start_values"]["rows"]:
        rows.append([r["row"], r["p"], r["lo"], r["hi"], r["v1"], r["v2"],
                     r["v3"], f"{r['tag']:04x}"])
    md.append(lib.md_table(rows[0], rows[1:]) + "\n")

    sr = st["stat_records"]
    md.append(f"Stat records @ {sr['runtime_offset']}: "
              f"{'identical to the flat' if sr['verified_identical'] else 'DIFFERS!'}.\n")
    md.append(f"Headless first record: {sr['head']}\n")
    rows = [["id", "cost", "f", "cnt", "a", "b", "c", "d", "e"]]
    for r in sr["records"]:
        rows.append([f"{r['id']:#04x}", r["cost"], f"{r['f']:02x}",
                     f"{r['cnt']:02x}", r["a"], r["b"], r["c"], r["d"],
                     f"{r['e']:#010x}"])
    md.append(lib.md_table(rows[0], rows[1:]) + "\n")
    md.append("ids overlap the type-id list; the exact field mapping onto "
              "build time / hit points / power / range is still open "
              "(docs/mechanics/weapon-and-turret-numbers.md).\n")

    ti = st["type_ids"]
    md.append(f"Type-id list @ {ti['runtime_offset']}: "
              f"{'identical to the flat' if ti['verified_identical'] else 'DIFFERS!'}\n")
    md.append("`" + ", ".join(f"{x:#x}" for x in ti["ids"]) + "`\n")

    md.append("## Per-type runtime tables (game-start materialisation)\n")
    if any_materialised:
        md.append("A colony-view dump was captured — the per-type tables are "
                  "materialised and decoded below.\n")
    else:
        md.append("This dump was taken at the **main menu**: the per-type "
                  "tables are not yet materialised (the offsets still hold "
                  "code bytes). To decode the per-type stats, start a game "
                  "(colony view) in DOSBox and re-run:\n\n"
                  "    make memdump-all\n    make stats\n\n"
                  "The table layouts below are already pinned by the code's "
                  "read sites.\n")
    for name, t in rts.items():
        md.append(f"### 0x{name} (stride {t['stride']}, {t['rows']} rows)\n")
        md.append(f"{t['note']}\n")
        if "values" in t:
            for i, v in enumerate(t["values"]):
                md.append(f"- row {i}: `{v}`")
            md.append("")
    lib.write_md(lib.reports_dir(cfg) / "stats.md", "\n".join(md))
    lib.note(f"report -> build/reports/stats.md "
             f"({'gameplay dump decoded' if any_materialised else 'main-menu dump: per-type stats need a colony-view dump'})",
             "green" if any_materialised else "yellow")
    return 0


if __name__ == "__main__":
    sys.exit(main())
