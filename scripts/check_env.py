#!/usr/bin/env python3
"""Stage 0: verify the installed toolchain against config/rules.yaml.

Rule 5: this script NEVER installs anything. If a required tool is missing it
prints the fix (see docs/INSTALL.md) and exits non-zero.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import fragile_decomp_lib as lib


def main() -> int:
    cfg = lib.load_config()
    tools = cfg.get("tools", {})
    if not tools:
        lib.note("config/rules.yaml has no [tools] section", "red")
        return 2

    ap = lib.make_parser("verify the installed toolchain against config/rules.yaml")
    ap.add_argument("--for", dest="only_stage", default=None, metavar="STAGE",
                    help="only check tools needed by this pipeline stage")
    args = ap.parse_args()

    rows = []
    failures = 0
    warnings = 0

    for name, spec in sorted(tools.items()):
        required = spec.get("required", True)
        external = spec.get("external", False)
        minver = spec.get("min", "0")
        stages = spec.get("stages") or []

        if args.only_stage and args.only_stage not in stages:
            continue

        if external:
            if name == "ghidra":
                gpath = lib.find_ghidra()
                found = gpath is not None
                where = gpath or ""
            elif name == "dosbox-x":
                argv = lib.find_dosbox()
                found = argv is not None
                where = " ".join(argv) if argv else ""
            else:
                found = lib.which(name) is not None
                where = lib.which(name) or ""
            ver = ""
        else:
            found = lib.which(name) is not None
            ver = lib.tool_version([name] + ([] if not spec.get("version_flag")
                                              else [spec["version_flag"]]))
            where = lib.which(name) or ""

        ok = found and (not minver or _version_ge(ver, minver))
        status = "ok" if ok else ("missing" if not found else "version")
        if not found:
            status = "MISSING"
        elif not ok:
            status = f"TOO OLD (need {minver})"

        if not ok:
            if required:
                failures += 1
            else:
                warnings += 1

        rows.append([name, ver or "-", status, where or spec.get("note", "")])

    print()
    scope = f"  (scope: {args.only_stage})" if args.only_stage else ""
    print(f"fragile-decomp toolchain check{scope}")
    print("=" * 78)
    print(lib.md_table(["tool", "version", "status", "location/note"], rows))
    print()

    if failures:
        lib.note(f"{failures} required tool(s) missing or too old.", "red")
        lib.note("Install them manually — the pipeline never installs software.", "yellow")
        lib.note("See docs/INSTALL.md for per-tool instructions.", "yellow")
        return 1
    if warnings:
        lib.note(f"{warnings} optional tool(s) missing; some stages will degrade.", "yellow")
    lib.note("Toolchain OK.", "green")
    return 0


def _version_ge(a: str, b: str) -> bool:
    def parts(v: str) -> list[int]:
        return [int(m) for m in re.findall(r"\d+", v)] or [0]

    return parts(a) >= parts(b)


if __name__ == "__main__":
    sys.exit(main())
