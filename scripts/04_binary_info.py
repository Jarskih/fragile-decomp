#!/usr/bin/env python3
"""Stage 04: classify executables from the DOS MZ header.

Reads build/reports/inventory.json (or scans the extracted tree), parses the
MZ header of each executable, sniffs for DOS extenders (DOS/4GW, DOS/32A,
Watcom, DJGPP/CWSDPMI, PMODE, Causeway) and classifies each as 16-bit real
mode vs 32-bit protected mode. That choice drives the Ghidra setup.

Outputs build/reports/binaries.json + binaries.md.
"""
from __future__ import annotations

import json
import re
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import openfa_lib as lib

# Brand signatures commonly left by DOS extenders / compilers.
EXTENDER_MARKS = [
    ("DOS/4GW", re.compile(rb"DOS/4G[W ]", re.I)),
    ("DOS/4G", re.compile(rb"DOS/4G", re.I)),
    ("DOS/32A", re.compile(rb"DOS/32A", re.I)),
    ("DOSX", re.compile(rb"DOSX", re.I)),
    ("WATCOM", re.compile(rb"WATCOM|Watcom C/C\+\+|WATCOM C", re.I)),
    ("DJGPP", re.compile(rb"DJGPP", re.I)),
    ("CWSDPMI", re.compile(rb"CWSDP", re.I)),
    ("PMODE", re.compile(rb"PMODE", re.I)),
    ("CAUSEWAY", re.compile(rb"Causeway", re.I)),
    ("386MAX", re.compile(rb"386MAX", re.I)),
    ("HX/DPR", re.compile(rb"DOSC", re.I)),
    ("ZDLL", re.compile(rb"ZDLL", re.I)),
    ("CAUSEWAY", re.compile(rb"DMOS|Causeway", re.I)),
]


def find_executables(root: Path) -> list[Path]:
    out = []
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        if p.suffix.lower() in (".exe", ".com", ".ovl", ".drv"):
            out.append(p)
            continue
        # sniff for MZ in otherwise-unknown binaries
        with open(p, "rb") as fh:
            head = fh.read(2)
        if head == b"MZ":
            out.append(p)
    return sorted(out)


def parse_mz(data: bytes) -> dict | None:
    if data[:2] != b"MZ":
        return None
    (e_cblp, e_cp, e_crlc, e_cparhdr, e_minalloc, e_maxalloc,
     e_ss, e_sp, e_csum, e_ip, e_cs, e_lfarlc, e_ovno) = struct.unpack_from(
        "<HHHHHHHHHHHHH", data, 2)
    e_lfanew = struct.unpack_from("<I", data, 0x3C)[0] if len(data) >= 0x40 else 0
    info = {
        "magic": "MZ",
        "e_cblp": e_cblp,
        "e_cp": e_cp,
        "e_crlc": e_crlc,
        "e_cparhdr": e_cparhdr,
        "e_minalloc": e_minalloc,
        "e_maxalloc": e_maxalloc,
        "e_ss": e_ss,
        "e_sp": e_sp,
        "e_csum": e_csum,
        "e_ip": e_ip,
        "e_cs": e_cs,
        "e_lfarlc": e_lfarlc,
        "e_ovno": e_ovno,
        "e_lfanew": e_lfanew,
        "pe": data[e_lfanew:e_lfanew + 4] == b"PE\x00\x00",
        "headers_size": e_cparhdr * 16,
    }
    return info


def sniff_extenders(data: bytes) -> list[str]:
    hits = []
    # sample first 64 KiB (stub area) plus scan whole file cheaply
    for name, rx in EXTENDER_MARKS:
        if rx.search(data[:0x10000]) or rx.search(data):
            if name not in hits:
                hits.append(name)
    return hits


def classify(info: dict, extenders: list[str]) -> str:
    if info.get("pe"):
        return "PE/Win32 (not a DOS binary)"
    if info.get("e_ovno", 0) != 0:
        return "16-bit real-mode with overlays"
    if extenders:
        return "32-bit protected-mode DOS extender"
    # Small header + low maxalloc => typical 16-bit real-mode COM-ish EXE.
    if info.get("e_cparhdr", 0) <= 4:
        return "16-bit real-mode"
    return "16-bit real-mode (no extender detected)"


def main() -> int:
    cfg = lib.load_config()
    root = lib.extracted_dir(cfg)

    if not root.is_dir():
        lib.note(f"nothing extracted yet: {root} not a directory", "red")
        return 2

    exes = find_executables(root)
    if not exes:
        lib.note("no executables found in extracted tree", "yellow")
        return 0

    rows = []
    for exe in exes:
        data = exe.read_bytes()[:2 * 1024 * 1024]  # cap for scanning speed
        info = parse_mz(data)
        if info is None:
            rows.append({"path": exe.relative_to(root).as_posix(),
                         "size": exe.stat().st_size, "class": "not MZ",
                         "extenders": [], "magic": lib.file_magic(exe), "mz": None})
            continue
        extenders = sniff_extenders(data)
        cls = classify(info, extenders)
        entry = {
            "path": exe.relative_to(root).as_posix(),
            "size": exe.stat().st_size,
            "mz": info,
            "extenders": extenders,
            "class": cls,
        }
        rows.append(entry)

    jpath, mpath = lib.report_pair(cfg, "binaries", rows)
    md_rows = [
        [r["path"], r["size"], ",".join(r["extenders"]) or "-", r["class"]]
        for r in rows
    ]
    md = "# Executable classification\n\n" + lib.md_table(
        ["path", "size", "extender", "class"], md_rows) + "\n"
    lib.write_md(mpath, md)
    lib.note(f"classified {len(rows)} executables -> {jpath}", "green")
    return 0


if __name__ == "__main__":
    sys.exit(main())
