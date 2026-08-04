#!/usr/bin/env python3
"""Stage 06: analyse the flat 32-bit image sliced by stage 05.

Operates on build/flat/FRAGILE.EXE.flat (image-relative, base 0) and:
  1. estimates the code/data boundary (string density + pointer-heuristic scan),
  2. detects entry-point candidates (compiler prologue patterns),
  3. extracts ASCII strings from the data region and finds code references to
     them (a dword in code equal to the string's image offset),
  4. reports overall coherence statistics that sanity-check the slice.

Everything here is deterministic and derived (gitignored). Outputs:
  build/reports/flat_analysis.json / flat_analysis.md
"""
from __future__ import annotations

import re
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import openfa_lib as lib

MAIN_EXE = "FRAGILE.EXE"

PROLOGUES = [
    ("push6_xor", re.compile(rb"\x53\x51\x52\x56\x57\x55\x31\xd2")),
    ("std_ebp", re.compile(rb"\x55\x8b\xec")),
    ("std_ebp_push", re.compile(rb"\x55\x8b\xec\x83\xec")),
    ("subesp", re.compile(rb"\x81\xec....\x53")),
    ("int3_trap_nops", re.compile(rb"\xcc\xeb\xfd\x90\x90\x90\x90")),
]


def code_data_boundary(img: bytes) -> dict:
    """Estimate the code/data regions of the flat image.

    Code and binary data both show moderate printable-byte density and pointer-
    like aligned dwords, so no single threshold separates them reliably.
    Instead we locate two robust structural transitions:

      * code_end      -- first 4 KiB page where printable density drops below
                         0.10 for two consecutive pages (the code stream hands
                         off to a non-printable block), and
      * strings_start -- first page where printable density rises above 0.80
                         for three consecutive pages (the text/string region).

    The region [code_end, strings_start) is treated as binary data and is
    excluded from string extraction to avoid false positives.
    """
    n = len(img)
    page = 4096
    printable = []
    for off in range(0, n - page, page):
        block = img[off:off + page]
        printable.append(sum(1 for b in block if 0x20 <= b < 0x7F) / page)

    code_end = n
    run = 0
    for i, p in enumerate(printable):
        run = run + 1 if p < 0.10 else 0
        if run >= 2 and i * page >= 0x10000:
            code_end = i * page
            break

    strings_start = n
    run = 0
    for i, p in enumerate(printable):
        run = run + 1 if p > 0.80 else 0
        if run >= 3:
            strings_start = i * page
            break

    if strings_start < code_end:
        strings_start = code_end
    return {"size": n, "code_end": code_end,
            "strings_start": strings_start,
            "data_size": n - code_end,
            "string_region_size": n - strings_start}


def entry_candidates(img: bytes) -> list[dict]:
    """Detect plausible entry points within the first 64 KiB."""
    head = img[:0x10000]
    out = []
    for name, rx in PROLOGUES:
        for m in rx.finditer(head):
            out.append({"name": name, "offset": m.start(), "bytes": m.group()[:8].hex()})
    # sort by offset, dedupe adjacent (multiple prologues can share one start)
    out.sort(key=lambda d: d["offset"])
    dedup = []
    last = -10
    for d in out:
        if d["offset"] >= last + 4:
            dedup.append(d)
            last = d["offset"]
    return dedup[:20]


def extract_strings(img: bytes, start: int, min_len: int = 4) -> list[dict]:
    """Pull printable strings from the data region."""
    pat = re.compile(rb"[\x20-\x7E]{%d,}" % min_len)
    out = []
    for m in pat.finditer(img[start:]):
        if m.start() > 0 and img[start + m.start() - 1] in (0, 0xFF):
            continue
        out.append({"offset": start + m.start(), "text": m.group().decode("ascii", "replace")})
        if len(out) >= 50000:
            break
    return out


def region_pointers(img: bytes, code_end: int, sstart: int, send: int) -> dict:
    """Count aligned dwords whose value lands inside [sstart, send).

    String references in the game are image-relative dwords that may point at
    record-table fields inside the string region rather than at the start of a
    bare ASCII run, so we measure region membership instead of exact matches.
    """
    code = data = 0
    samples = []
    for i in range(0, len(img) - 4, 4):
        v = struct.unpack_from("<I", img, i)[0]
        if not (sstart <= v < send):
            continue
        if i < code_end:
            code += 1
        else:
            data += 1
        if len(samples) < 40:
            samples.append({"from": i, "to": v})
    return {"code": code, "data": data, "total": code + data,
            "sample": samples}


def main() -> int:
    cfg = lib.load_config()
    flat = lib.flat_dir(cfg) / f"{MAIN_EXE}.flat"
    if not flat.is_file():
        lib.note(f"{flat} not found (run `make extract-flat` first)", "red")
        return 2

    img = flat.read_bytes()
    bd = code_data_boundary(img)
    entries = entry_candidates(img)
    strings = extract_strings(img, bd["strings_start"])
    strings_end = min(bd["strings_start"] + 0x20000, bd["size"])
    ptrs = region_pointers(img, bd["code_end"], bd["strings_start"], strings_end)

    # sample strings (first ~60) for the report
    sample = [s["text"] for s in strings[:60]]

    data = {
        "source": f"flat/{MAIN_EXE}.flat",
        "size": bd["size"],
        "code_data": bd,
        "entry_candidates": entries,
        "strings": {
            "count": len(strings),
            "min_len": 4,
            "region_start": bd["strings_start"],
            "note": "file-table records (name + metadata trailer); see "
                    "docs/dataformats/dos4gw-bound.md",
            "sample": sample,
        },
        "string_region_pointers": {
            "region_end": strings_end,
            **ptrs,
        },
    }

    jpath, mpath = lib.report_pair(cfg, "flat_analysis", data)

    rows = [
        ["code", f"0x0 .. 0x{bd['code_end']:x}", bd["code_end"]],
        ["binary data", f"0x{bd['code_end']:x} .. 0x{bd['strings_start']:x}",
         bd["strings_start"] - bd["code_end"]],
        ["string data", f"0x{bd['strings_start']:x} .. 0x{bd['size']:x}",
         bd["string_region_size"]],
    ]
    md = (f"# Flat image analysis ({MAIN_EXE})\n\n"
          + lib.md_table(["region", "range", "size"], rows)
          + "\n\n## Entry candidates\n\n"
          + lib.md_table(["offset", "prologue", "bytes"],
                         [[f"0x{d['offset']:x}", d["name"], d["bytes"]] for d in entries])
          + "\n\n## Strings / pointer refs\n\n"
          + f"- {len(strings)} ASCII records in the string region (resource file "
          + f"table: name + metadata trailer).\n"
          + f"- {ptrs['code']} code dwords and {ptrs['data']} data dwords point "
          + f"into the string region (image-relative).\n")
    lib.write_md(mpath, md)
    lib.note(f"code 0x0..0x{bd['code_end']:x}, strings 0x{bd['strings_start']:x}+, "
             f"{len(entries)} entry candidates, {len(strings)} string records, "
             f"{ptrs['code']} code + {ptrs['data']} data string-region refs", "green")
    lib.note(f"report -> {jpath}", "green")
    return 0


if __name__ == "__main__":
    sys.exit(main())
