#!/usr/bin/env python3
"""Stage 09: data-file format survey.

For candidate data blobs (large, non-executable, non-text) records:
  - first bytes (hex) and printable glimpse
  - whole-file entropy + per-block entropy (flags compression/encryption)
  - known-magic hits
  - a few little/big-endian header integers

Outputs build/reports/datsurvey.{json,md}. This is a *probe*; the real format
work is the human+machine loop whose conclusions go to docs/dataformats/.
"""
from __future__ import annotations

import argparse
import json
import math
import struct
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import openfa_lib as lib

MAGICS = [
    ("gzip", b"\x1f\x8b"), ("zlib", b"\x78\x9c"), ("bzip2", b"BZh"),
    ("zip", b"PK\x03\x04"), ("7z", b"7z\xbc\xaf\x27\x1c"), ("rar", b"Rar!"),
    ("pcx", b"\x0a\x05\x01\x08"), ("bmp", b"BM"), ("png", b"\x89PNG"),
    ("jpeg", b"\xff\xd8\xff"), ("gif", b"GIF8"), ("tga", b"\x00\x02\x00\x00"),
    ("riff/avi-wav", b"RIFF"), ("iff/ilbm", b"FORM"), ("fli", b"\x11\xaf\x11\xaf"),
    ("flc", b"\x00\x00\x0c\xfc"), ("smk", b"SMS"), ("voc", b"Creative Voice File"),
    ("lzo", b"\x89LZO"), ("lzss", b"LZSS"), ("lz4", b"\x04\x22\x4d\x18"),
    ("zlx", b"\x1b\x33\xfa"), ("lzma", b"\x5d\x00\x00"),
]

SCAN_CAP = 4 * 1024 * 1024   # bytes of a file we actually read for entropy


def entropy(data: bytes) -> float:
    if not data:
        return 0.0
    c = Counter(data)
    n = len(data)
    return -sum((k / n) * math.log2(k / n) for k in c.values())


def per_block_entropy(data: bytes, block: int = 256, max_blocks: int = 256) -> list[float]:
    vals = []
    for i in range(0, min(len(data), block * max_blocks), block):
        vals.append(entropy(data[i:i + block]))
    return vals


def is_compressed_like(evals: list[float]) -> bool:
    if not evals:
        return False
    high = sum(1 for v in evals if v > 7.2)
    low = sum(1 for v in evals if v < 5.0)
    return high / len(evals) > 0.5 and low / len(evals) < 0.15


def survey(path: Path, full: bytes) -> dict:
    head = full[:64]
    blocks = per_block_entropy(full)
    hdr_ints = []
    if len(full) >= 16:
        hdr_ints = {
            "le": [struct.unpack_from("<I", full, 0)[0],
                   struct.unpack_from("<I", full, 4)[0]],
            "be": [struct.unpack_from(">I", full, 0)[0],
                   struct.unpack_from(">I", full, 4)[0]],
        }
    magic_hits = [name for name, sig in MAGICS if full.startswith(sig)]
    glimpse = "".join(chr(b) if 32 <= b < 127 else "." for b in head[:40])
    return {
        "hex": head.hex(),
        "glimpse": glimpse,
        "entropy_whole": round(entropy(full), 4),
        "entropy_blocks": [round(v, 3) for v in blocks[:24]],
        "compressed_like": is_compressed_like(blocks),
        "magic": magic_hits,
        "header_u32_le": hdr_ints.get("le") if hdr_ints else None,
        "header_u32_be": hdr_ints.get("be") if hdr_ints else None,
        "size": path.stat().st_size,
    }


def main() -> int:
    cfg = lib.load_config()
    root = lib.extracted_dir(cfg)

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--limit", type=int, default=200,
                    help="max candidate files to probe (largest first)")
    ap.add_argument("--min-size", type=int, default=1024)
    ap.add_argument("--only-category", default="data,image,audio,other")
    args = ap.parse_args()

    inv = lib.reports_dir(cfg) / "inventory.json"
    if not inv.exists():
        lib.note("inventory.json missing; run `make inventory` first", "red")
        return 2

    data = json.loads(inv.read_text(encoding="utf-8"))
    want = set(args.only_category.split(","))
    cands = [e for e in data["files"]
             if e["size"] >= args.min_size and e["category"] in want
             and e["category"] != "text"]
    cands.sort(key=lambda e: -e["size"])
    cands = cands[: args.limit]

    results = []
    for e in cands:
        p = root / e["path"]
        try:
            with open(p, "rb") as fh:
                full = fh.read(SCAN_CAP)
        except OSError as exc:
            results.append({"path": e["path"], "error": str(exc)})
            continue
        s = survey(p, full)
        s["path"] = e["path"]
        results.append(s)

    jpath, mpath = lib.report_pair(cfg, "datsurvey", results)
    rows = [[r["path"], r["size"], r["magic"] or "-",
             "y" if r.get("compressed_like") else "-",
             f"{r['entropy_whole']:.2f}", r["glimpse"]]
            for r in results if "error" not in r]
    md = "# Data-file survey\n\n" + lib.md_table(
        ["path", "size", "magic", "c/enc", "entropy", "head"], rows) + "\n"
    lib.write_md(mpath, md)
    lib.note(f"surveyed {len(results)} candidate files -> {jpath}", "green")
    return 0


if __name__ == "__main__":
    sys.exit(main())
