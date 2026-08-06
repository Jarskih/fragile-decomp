#!/usr/bin/env python3
"""Stage 02: extract the ISO9660 data session into build/iso/.

Handles: plain directory (used as-is), .iso/.nrg/.img (via 7z, fallback
bsdtar), and .bin+.cue (data track extraction attempt). Audio tracks are
listed (see build/reports/tracks.*) but not extracted.

Rule 1: all extracted content lands under build/ (gitignored).
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import fragile_decomp_lib as lib


def main() -> int:
    cfg = lib.load_config()
    image = lib.iso_file(cfg)
    out = lib.extracted_dir(cfg)

    if not image.exists():
        lib.note(f"image not found: {image}", "red")
        lib.note("Run `make download` or place your image in iso/.", "yellow")
        return 2

    if image.is_dir():
        lib.note(f"input is a directory; using {image} as extracted tree", "cyan")
        lib.ensure_dir(out)
        for child in image.iterdir():
            dest = out / child.name
            if not dest.exists():
                if child.is_dir():
                    import shutil
                    shutil.copytree(child, dest)
                else:
                    shutil.copy2(child, dest)
        return 0

    low = image.name.lower()
    if low.endswith(".cue"):
        return _extract_cue(cfg, image, out)
    return _extract_iso(cfg, image, out)


def _extract_iso(cfg: dict, image: Path, out: Path) -> int:
    lib.ensure_dir(out)
    lib.note(f"extracting {image} -> {out}", "cyan")

    if lib.which("7z"):
        res = lib.run(["7z", "x", "-y", f"-o{out}", str(image)], capture=False)
        if res.returncode == 0:
            return 0
        lib.note("7z failed; trying bsdtar fallback.", "yellow")
    if lib.which("bsdtar"):
        res = lib.run(["bsdtar", "-xf", str(image), "-C", str(out)], capture=False)
        if res.returncode == 0:
            return 0
        lib.note("bsdtar also failed.", "red")
        return 1
    lib.note("no extractor available (need 7z or bsdtar)", "red")
    return 1


def _extract_cue(cfg: dict, image: Path, out: Path) -> int:
    lib.note("bin/cue images need track-aware extraction.", "yellow")
    # Try 7z on the data .bin directly; 7-Zip can sometimes read the ISO9660
    # session. This is best-effort.
    bins = [Path(f) for f in image_files(image)]
    data_bin = bins[0] if bins else None
    if data_bin is None:
        lib.note("no data file found in cue sheet", "red")
        return 1
    if lib.which("7z"):
        lib.note(f"attempting 7z on {data_bin}", "cyan")
        lib.ensure_dir(out)
        res = lib.run(["7z", "x", "-y", f"-o{out}", str(data_bin)], capture=False)
        if res.returncode == 0 and _nonempty(out):
            return 0
        lib.note("7z could not read the data session. Suggest converting with "
                 "`xorriso`/`bchunk` and re-running.", "yellow")
        return 1
    lib.note("7z required for bin/cue extraction", "red")
    return 1


def image_files(image: Path) -> list[Path]:
    import re
    files = []
    for line in image.read_text(encoding="cp1252", errors="replace").splitlines():
        m = re.search(r"FILE\s+\"([^\"]+)\"", line)
        if m:
            cand = image.parent / m.group(1)
            if cand.exists() and cand not in files:
                files.append(cand)
    return files


def _nonempty(d: Path) -> bool:
    return any(p.is_file() for p in d.rglob("*"))


if __name__ == "__main__":
    sys.exit(main())
