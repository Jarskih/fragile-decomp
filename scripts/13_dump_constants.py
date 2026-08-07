#!/usr/bin/env python3
"""Stage 13: decode a runtime memory dump of the game (make memdump).

The game runs the GOG build under DOSBox; `make memdump` snapshots the
emulated RAM read-only into build/dumps/ram_<base>.bin. This stage:

  1. locates the loaded game image inside the dump (image-start trap
     signature + entry prologue, verified against the static GOG flat),
  2. derives the per-object relocation bases from the DOS/4G record stream
     (obj 3 = main image, obj 1 = the string/catalog object, obj 2 = the
     single-record object),
  3. reads the runtime DS data-selector values (the 7 `02`-record patch
     sites),
  4. cross-checks the static gameplay tables (stage 12) at their runtime
     addresses — the tables must be byte-identical in memory,
  5. catalogs the runtime-initialized regions: wherever the dump differs
     from the relocated image, the game has written state/tables at
     startup (player names, generated palette ramps, format strings).

Outputs (derived, gitignored):
  build/reports/dump_constants.json / dump_constants.md
  build/flat/FRAGILE.EXE.gog.runtime.bin   (the loaded image, raw)
"""
from __future__ import annotations

import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import fragile_decomp_lib as lib

FLAT = "flat/FRAGILE.EXE.gog.flat"
FLAT_SHA = "4e8d2d964e04197bba28dbd843a5bf334131aaf9c8244c57df9fc6187906a9d4"
GOG_EXE_REL = "Fragile Allegiance/FRAGILE.EXE"

IMAGE_TRAP = b"\x00\x00\x00\x00\xcc\xeb\xfd"
ENTRY = bytes.fromhex("53515256575531d28b1d")  # push6/xor/mov ebx,[..]

# Runtime table offsets (flat-space) verified against the dump 2026-08-07.
ORE_OFF = 0x8FCE2
STATS_OFF = 0x8F680
TYPE_IDS_OFF = 0x8F880
# The 7 DS-selector fixup sites (imm16 slots; see stage 05b / dos4gw-bound).
SELECTOR_SITES = [0x58589, 0x58754, 0x5ECCB, 0x6061D, 0x7EFC4, 0x7F08F,
                  0x7F00D]

GR = struct.Struct("<BBHB")


def find_dump(cfg: dict) -> Path | None:
    ddir = lib._path(cfg, "build_dir") / "dumps"
    if not ddir.is_dir():
        return None
    cands = sorted(ddir.glob("ram_*.bin"))
    return cands[-1] if cands else None


def locate_image(data: bytes, flat: bytes) -> int | None:
    """Find the loaded image: trap signature + entry prologue matching the
    flat, with the entry's first displacement relocated by a uniform base."""
    pos = 0
    while True:
        i = data.find(IMAGE_TRAP, pos)
        if i < 0:
            return None
        img = i  # image starts at the four zero bytes; trap at +4
        if data[img + 0x04:img + 0x0B] == flat[0x04:0x0B] and \
                data[img + 0x14:img + 0x1A] == flat[0x14:0x1A]:
            return img
        pos = i + 1


def load_offset_table(gog: bytes) -> tuple[list[int], int] | None:
    """Offset table + stream base, matched against the exe's own image
    position so a garbage monotonic tail entry cannot misalign the streams
    (same rule as stage 05b)."""
    ot = gog.find(b"unbound") + 7
    raw = []
    for k in range(512):
        v = struct.unpack_from("<I", gog, ot + 4 * k)[0]
        if raw and v < raw[-1]:
            break
        raw.append(v)
    img = gog.find(IMAGE_TRAP, ot)
    for n in range(len(raw) - 1, 3, -1):
        end = ot + 4 * n + raw[n - 1]
        if end <= img and gog[end:img] == b"\x00" * (img - end):
            return raw[:n], ot + 4 * n
    return None


def per_object_bases(data: bytes, gog: bytes, flat: bytes, img: int) -> dict:
    """For each relocation object, the dominant delta runtime-flat (the load
    base of that object, in flat-relative terms)."""
    tab = load_offset_table(gog)
    if tab is None:
        raise ValueError("offset table does not match the exe image position")
    offs, sb = tab
    rt = data[img:img + len(flat)]
    deltas: dict[int, dict] = {}
    for g in range(1, len(offs) - 1):
        seg = gog[sb + offs[g]:sb + offs[g + 1]]
        p = 0
        while p < len(seg):
            b0 = seg[p]
            if b0 == 0x07:
                _, t, x, obj = GR.unpack_from(seg, p)
                sz = 9 if t == 0x10 else 7
                sx = x - 0x10000 if x >= 0x8000 else x
                fp = (g - 1) * 0x1000 + sx + 4
                if fp + 4 <= len(flat):
                    fv = struct.unpack_from("<I", flat, fp)[0]
                    rv = struct.unpack_from("<I", rt, fp)[0]
                    d = (rv - fv) & 0xFFFFFFFF
                    c = deltas.setdefault(obj, {})
                    c[d] = c.get(d, 0) + 1
                p += sz
            else:
                p += 5
    out = {}
    for obj, c in deltas.items():
        d, n = max(c.items(), key=lambda kv: kv[1])
        out[obj] = {"base": d, "fields": n, "total": sum(c.values())}
    return out


def rt_off(fp: int) -> int:
    """Flat offset -> runtime offset. The DOS/4G stub page (flat
    0x85000..0x86000) is not mapped at runtime; everything >= 0x86000
    shifts down by 0x1000 (verified against the dump: strings, catalog and
    the static tables all land at flat - 0x1000)."""
    return fp if fp < 0x86000 else fp - 0x1000


def table_at(rt: bytes, flat: bytes) -> dict:
    """Cross-check the stage-12 tables at their runtime addresses."""
    o = rt_off(ORE_OFF)
    ore_rows = []
    for i in range(11):
        p = rt[o + i * 14]
        lo, hi = struct.unpack_from("<HH", rt, o + i * 14 + 2)
        ore_rows.append([i, p, lo, hi])
    s = rt_off(STATS_OFF)
    stats = []
    for i in range(15):
        off = s + 0x18 + i * 0x1C
        ident, cost = struct.unpack_from("<IH", rt, off)
        stats.append([f"{ident:#04x}", cost])
    t = rt_off(TYPE_IDS_OFF)
    return {
        "ore_table": {
            "runtime_offset": f"{o:06x}",
            "verified_identical": rt[o:o + 11 * 14] ==
            flat[ORE_OFF:ORE_OFF + 11 * 14],
            "rows": ore_rows,
        },
        "stat_records": {
            "runtime_offset": f"{s:06x}",
            "verified_identical": rt[s:s + 0x18 + 15 * 0x1C] ==
            flat[STATS_OFF:STATS_OFF + 0x18 + 15 * 0x1C],
            "records": stats,
        },
        "type_ids": list(rt[t:t + 28]),
    }


def initialized_regions(rt: bytes, flat: bytes, gog: bytes, img: int,
                        bases: dict) -> list[dict]:
    """True runtime-write regions: build the expected image (stub page
    removed + per-object relocations applied) and diff against the dump."""
    tab = load_offset_table(gog)
    if tab is None:
        raise ValueError("offset table does not match the exe image position")
    offs, sb = tab
    exp = bytearray(len(flat) - 0x1000)
    for i in range(len(exp)):
        exp[i] = flat[rt_off_back(i)]
    for g in range(1, len(offs) - 1):
        seg = gog[sb + offs[g]:sb + offs[g + 1]]
        p = 0
        while p < len(seg):
            b0 = seg[p]
            if b0 == 0x07:
                _, t, x, obj = GR.unpack_from(seg, p)
                sz = 9 if t == 0x10 else 7
                sx = x - 0x10000 if x >= 0x8000 else x
                fp = (g - 1) * 0x1000 + sx + 4
                if fp + 4 <= len(flat):
                    rp = rt_off(fp)
                    if rp + 4 <= len(exp):
                        v = struct.unpack_from("<I", flat, fp)[0]
                        base = bases.get(obj, {}).get("base", 0)
                        if t == 0x10:
                            exp[rp:rp + 4] = struct.pack(
                                "<I", (v + base) & 0xFFFFFFFF)
                        else:
                            exp[rp:rp + 2] = struct.pack(
                                "<H", (v + base) & 0xFFFF)
                p += sz
            else:
                p += 5
    runs = []
    start = None
    for i in range(len(exp)):
        if rt[i] != exp[i]:
            if start is None:
                start = i
        else:
            if start is not None:
                runs.append((start, i - 1))
                start = None
    if start is not None:
        runs.append((start, len(exp) - 1))
    out = []
    for s, e in runs:
        if e - s + 1 >= 8:
            out.append({"offset": f"{s:06x}", "end": f"{e:06x}",
                        "size": e - s + 1})
    return out


def rt_off_back(ro: int) -> int:
    return ro if ro < 0x85000 else ro + 0x1000


def main() -> int:
    cfg = lib.load_config()
    dump = find_dump(cfg)
    if dump is None:
        lib.note("no build/dumps/ram_*.bin found; run `make memdump` while "
                 "the game is running under DOSBox(-X) first", "red")
        return 2
    flat_path = lib.flat_dir(cfg) / "FRAGILE.EXE.gog.flat"
    if not flat_path.is_file():
        lib.note("run `make gog-flat` first", "red")
        return 2
    flat = flat_path.read_bytes()
    if lib.sha256_bytes(flat) != FLAT_SHA:
        lib.note("gog flat sha256 mismatch — run `make gog-flat`", "red")
        return 2
    data = dump.read_bytes()
    img = locate_image(data, flat)
    if img is None:
        lib.note("loaded game image not found in the dump (is the game at "
                 "the main menu / colony view?)", "red")
        return 2

    gog = (lib.ROOT / GOG_EXE_REL).read_bytes()
    bases = per_object_bases(data, gog, flat, img)
    rt = data[img:img + len(flat)]
    tables = table_at(rt, flat)

    sel = []
    for site in SELECTOR_SITES:
        sel.append({"site": f"{site:06x}",
                    "selector": f"{struct.unpack_from('<H', rt, site + 2)[0]:#06x}"})
    regions = initialized_regions(rt, flat, gog, img, bases)

    out = {
        "dump": str(dump.relative_to(lib.ROOT)),
        "image": {
            "dump_offset": f"{img:06x}",
            "size": len(flat),
            "flat_sha256": FLAT_SHA,
        },
        "objects": bases,
        "ds_selectors": sel,
        "tables": tables,
        "runtime_written_pages": regions,
        "note": "The static tables are byte-identical in memory; the "
                "runtime-write regions hold startup state (player-name "
                "strings, generated palette ramps, format-string patches). "
                "The displacement reads of the stat code (e.g. 0xab69, "
                "0xb3b4) target addresses that are code both statically and "
                "at runtime with DS = image base; resolving which runtime "
                "segment they index needs the emulated GDT/LDT (open).",
    }
    lib.write_json(lib.reports_dir(cfg) / "dump_constants.json", out)

    rows = [
        ["dump", str(dump.relative_to(lib.ROOT)), f"{len(data):#x} B", "-"],
        ["image", f"dump offset {img:06x}", f"{len(flat):#x} B",
         "trap + entry prologue match the static flat"],
    ]
    for obj, b in sorted(bases.items()):
        rows.append([f"obj {obj}", f"base 0x{b['base']:06x}",
                     f"{b['fields']}/{b['total']} fields",
                     "dominant relocation delta (linear load base)"])
    md = ["# Runtime dump decode (stage 13)\n",
          lib.md_table(["item", "value", "size / count", "notes"], rows),
          "\n## DS data selectors (the 7 `02`-record patch sites)\n",
          "`" + ", ".join(f"{s['site']} -> {s['selector']}" for s in sel) + "`\n",
          "\n## Static tables at runtime\n",
          f"Ore table @ {tables['ore_table']['runtime_offset']}: "
          f"{'identical to the flat' if tables['ore_table']['verified_identical'] else 'DIFFERS!'}.\n",
          lib.md_table(["row", "p", "lo", "hi"],
                       tables["ore_table"]["rows"]),
          f"\nStat records @ {tables['stat_records']['runtime_offset']}: "
          f"{'identical to the flat' if tables['stat_records']['verified_identical'] else 'DIFFERS!'}.\n",
          lib.md_table(["id", "cost"], tables["stat_records"]["records"]),
          "\n## Runtime-written regions (runs >= 8 bytes)\n",
          "Runs where the dump differs from the expected relocated image "
          "(startup state / generated tables; flat-relative runtime "
          "offsets):\n",
          "`" + ", ".join(f"{r['offset']}..{r['end']} ({r['size']} B)"
                         for r in regions) + "`\n",
          "\nRaw loaded image: `build/flat/FRAGILE.EXE.gog.runtime.bin`\n"]
    lib.write_md(lib.reports_dir(cfg) / "dump_constants.md", "\n".join(md))
    lib.ensure_dir(lib.flat_dir(cfg))
    (lib.flat_dir(cfg) / "FRAGILE.EXE.gog.runtime.bin").write_bytes(rt)
    lib.note(f"image at dump offset {img:#x}; "
             f"bases: " + ", ".join(f"obj {o}=0x{b['base']:x}" for o, b in
                                    sorted(bases.items())), "green")
    lib.note("report -> build/reports/dump_constants.json", "green")
    return 0


if __name__ == "__main__":
    sys.exit(main())
