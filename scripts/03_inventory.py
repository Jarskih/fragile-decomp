#!/usr/bin/env python3
"""Stage 03: inventory every extracted file (name/size/hash/magic).

Outputs build/reports/inventory.json (machine readable) and
build/reports/inventory.md (human). The JSON feeds later stages.

Rule 1: the manifest is written to build/ (gitignored); only aggregate stats
would ever be quoted in committed docs.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import fragile_decomp_lib as lib


def main() -> int:
    cfg = lib.load_config()
    root = lib.extracted_dir(cfg)

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default=str(root),
                    help=f"extracted tree (default: {root})")
    ap.add_argument("--no-hash", action="store_true", help="skip SHA-256 (faster)")
    args = ap.parse_args()

    root = Path(args.root)
    if not root.is_dir():
        lib.note(f"nothing extracted yet: {root} not a directory", "red")
        lib.note("Run `make extract` first.", "yellow")
        return 2

    entries = []
    nfiles = 0
    for p in sorted(root.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(root).as_posix()
        size = p.stat().st_size
        entry = {
            "path": rel,
            "size": size,
            "sha256": lib.sha256_file(p) if not args.no_hash else None,
            "magic": lib.file_magic(p),
            "category": lib.classify_extension(rel),
        }
        entries.append(entry)
        nfiles += 1

    by_cat: dict[str, int] = {}
    by_ext: dict[str, int] = {}
    for e in entries:
        by_cat[e["category"]] = by_cat.get(e["category"], 0) + 1
        ext = Path(e["path"]).suffix.lower().lstrip(".") or "(none)"
        by_ext[ext] = by_ext.get(ext, 0) + 1

    data = {
        "root": str(root),
        "file_count": nfiles,
        "total_size": sum(e["size"] for e in entries),
        "by_category": dict(sorted(by_cat.items(), key=lambda kv: -kv[1])),
        "by_extension": dict(sorted(by_ext.items(), key=lambda kv: -kv[1])),
        "files": entries,
    }
    jpath, mpath = lib.report_pair(cfg, "inventory", data)

    rows = [[e["path"], e["size"], (e["sha256"] or "-")[:16] + "…", e["magic"]]
            for e in entries]
    md = [
        "# File inventory",
        "",
        f"- **files:** {nfiles}",
        f"- **total size:** {data['total_size']} bytes",
        "",
        "## By category",
        "",
        lib.md_table(["category", "count"], [[k, v] for k, v in data["by_category"].items()]),
        "",
        "## Files",
        "",
        lib.md_table(["path", "size", "sha256", "magic"], rows),
        "",
    ]
    lib.write_md(mpath, "\n".join(md))
    lib.note(f"inventoried {nfiles} files -> {jpath}", "green")
    return 0


if __name__ == "__main__":
    sys.exit(main())
