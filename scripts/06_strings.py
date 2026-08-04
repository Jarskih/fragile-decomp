#!/usr/bin/env python3
"""Stage 06: strings sweep over the extracted files.

Runs binutils `strings` (ASCII + UTF-16LE, with decimal offsets) per file into
build/reports/strings/. A small index summarizes counts per file.

String dumps are byte-level extracts of the original files and live only under
build/ (gitignored).
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import openfa_lib as lib


def safe_name(rel: str) -> str:
    return rel.replace("/", "__")


def run_strings(exe: str, file: Path, minlen: int, enc: str) -> str:
    res = lib.run(["strings", "-a", "-t", "d", f"-n", str(minlen), f"-e", enc, str(file)])
    return res.stdout or ""


def main() -> int:
    cfg = lib.load_config()
    root = lib.extracted_dir(cfg)
    outdir = lib.strings_dir(cfg)

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--minlen", type=int, default=4, help="minimum string length")
    ap.add_argument("--only-executables", action="store_true",
                    help="only sweep files classified as executables")
    ap.add_argument("--max-bytes", type=int, default=8 * 1024 * 1024,
                    help="skip files larger than this (0 = no limit)")
    args = ap.parse_args()

    if not root.is_dir():
        lib.note(f"nothing extracted yet: {root}", "red")
        return 2

    inv = lib.reports_dir(cfg) / "inventory.json"
    files = _targets(root, inv, args)
    lib.ensure_dir(outdir)

    summary = []
    for rel, abspath in files:
        if args.max_bytes and abspath.stat().st_size > args.max_bytes:
            continue
        ascii_s = run_strings("ascii", abspath, args.minlen, "s")
        utf16_s = run_strings("utf16le", abspath, args.minlen, "l")
        count = len(re.findall(r"^\s*\d+\s", ascii_s, flags=re.M)) if ascii_s else 0
        name = safe_name(rel)
        body = (f"# strings: {rel}  (ASCII)\n\n{ascii_s}\n\n"
                f"# strings: {rel}  (UTF-16LE)\n\n{utf16_s}\n")
        lib.write_md(outdir / f"{name}.strings.md", body)
        summary.append({"path": rel, "ascii_strings": count,
                        "ascii_file": f"{name}.strings.md"})

    summary.sort(key=lambda r: -r["ascii_strings"])
    jpath, mpath = lib.report_pair(cfg, "strings_index", summary)
    rows = [[s["path"], s["ascii_strings"], s["ascii_file"]] for s in summary]
    lib.write_md(mpath, "# Strings index\n\n" + lib.md_table(
        ["path", "ascii strings", "dump file"], rows) + "\n")
    lib.note(f"strings sweep complete ({len(summary)} files) -> {jpath}", "green")
    return 0


def _targets(root: Path, inv: Path, args) -> list[tuple[str, Path]]:
    if inv.exists():
        data = json_load(inv)
        out = []
        for e in data.get("files", []):
            rel = e["path"]
            if args.only_executables and e.get("category") != "executable":
                continue
            p = root / rel
            if p.is_file():
                out.append((rel, p))
        return out
    # fallback: walk the tree
    out = []
    for p in root.rglob("*"):
        if p.is_file():
            out.append((p.relative_to(root).as_posix(), p))
    return out


def json_load(path: Path) -> dict:
    import json
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


if __name__ == "__main__":
    sys.exit(main())
