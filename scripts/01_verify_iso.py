#!/usr/bin/env python3
"""Stage 01: verify the original image.

Detects the container type (.iso / .bin+.cue / .nrg / .img / directory),
computes SHA-256 of the image file(s), cross-checks iso.sha256 when a hash is
recorded, and records the track table (data vs. audio) into build/reports/.

Reports: build/reports/verify.{json,md}, build/reports/tracks.{json,md}
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import fragile_decomp_lib as lib


def detect_type(image: Path) -> str:
    if image.is_dir():
        return "directory"
    low = image.name.lower()
    if low.endswith(".cue"):
        return "cue"
    if low.endswith(".iso"):
        return "iso"
    if low.endswith(".nrg"):
        return "nrg"
    if low.endswith(".img") or low.endswith(".bin"):
        return "raw"
    if low.endswith(".mdf") or low.endswith(".mds"):
        return "alcohol"
    # sniff for the ISO9660 volume descriptor
    with open(image, "rb") as fh:
        head = fh.read(0x10000)
    if b"CD001" in head:
        return "iso"
    return "unknown"


def cue_bin_files(image: Path) -> list[Path]:
    """Resolve the .bin files referenced by a .cue sheet."""
    files = []
    for line in image.read_text(encoding="cp1252", errors="replace").splitlines():
        m = re.search(r"FILE\s+\"([^\"]+)\"", line)
        if m:
            cand = image.parent / m.group(1)
            if cand.exists() and cand not in files:
                files.append(cand)
    return files


def image_files(image: Path) -> list[Path]:
    t = detect_type(image)
    if t == "cue":
        bins = cue_bin_files(image)
        return bins or [image]
    return [image]


def track_table(image: Path) -> dict:
    """Parse cd-info (or isoinfo fallback) output into a track list."""
    result = {"tool": "", "raw": "", "tracks": [], "summary": ""}
    res = lib.run(["cd-info", str(image)])
    if res.returncode == 0 and res.stdout:
        result["tool"] = "cd-info"
        result["raw"] = res.stdout
    else:
        res2 = lib.run(["isoinfo", "-d", "-i", str(image)])
        if res2.returncode == 0:
            result["tool"] = "isoinfo"
            result["raw"] = res2.stdout
        else:
            result["summary"] = "no cd-info/isoinfo available; track table omitted"
            return result

    tracks = []
    for line in result["raw"].splitlines():
        m = re.search(r"Track\s+(\d+):\s+(\w+)", line)
        if m:
            kind = m.group(2).lower()
            if kind.startswith("data") or "mode" in line.lower():
                kind = "data"
            elif "audio" in kind:
                kind = "audio"
            tracks.append({"track": int(m.group(1)), "type": kind, "raw": line.strip()})
    audio = [t for t in tracks if t["type"] == "audio"]
    data = [t for t in tracks if t["type"] == "data"]
    result["tracks"] = tracks
    result["summary"] = (f"{len(data)} data track(s), {len(audio)} audio track(s)")
    return result


def main() -> int:
    cfg = lib.load_config()
    image = lib.iso_file(cfg)

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--record-hash", action="store_true",
                    help="pin the computed hash into iso.sha256")
    ap.add_argument("--image", default=str(image),
                    help=f"image path (default: {image})")
    args = ap.parse_args()

    image = Path(args.image)
    if not image.exists():
        lib.note(f"image not found: {image}", "red")
        lib.note("Place your own copy in iso/ or run `make download`.", "yellow")
        return 2

    files = image_files(image)
    kind = detect_type(image)
    lib.note(f"image type: {kind}  ({len(files)} file(s))", "cyan")

    statuses = []
    for f in files:
        h = lib.sha256_file(f)
        rec = _recorded_hash(cfg, f)
        if rec and h == rec:
            st = "recorded ✓"
        elif rec:
            st = "MISMATCH (recorded %s…)" % rec[:16]
        else:
            st = "not yet recorded"
        statuses.append({"file": str(f), "size": f.stat().st_size, "sha256": h,
                         "status": st})
        lib.note(f"  {f.name}: {f.stat().st_size} bytes  sha256 {h[:16]}…  [{st}]",
                 "green" if st.startswith("recorded") else "yellow")

    lib.ensure_dir(lib.reports_dir(cfg))
    data = {"image": str(image), "type": kind, "files": statuses}
    lib.write_json(lib.reports_dir(cfg) / "verify.json", data)
    rows = [[s["file"], s["size"], s["sha256"][:16] + "…", s["status"]] for s in statuses]
    lib.write_md(lib.reports_dir(cfg) / "verify.md",
                 "# Image verification\n\n" + lib.md_table(
                     ["file", "size", "sha256", "status"], rows) + "\n")

    tracks = track_table(image)
    lib.write_json(lib.reports_dir(cfg) / "tracks.json", tracks)
    lib.write_md(lib.reports_dir(cfg) / "tracks.md",
                 f"# Track table\n\n{tracks['summary']}\n\n```\n{tracks['raw']}\n```\n")

    if args.record_hash:
        for s in statuses:
            if not s["status"].startswith("recorded"):
                _record(cfg, Path(s["file"]), s["sha256"])
        lib.note("Recorded hashes in iso.sha256", "green")

    bad = [s for s in statuses if s["status"].startswith("MISMATCH")]
    if bad:
        lib.note("Image hash mismatch — do not analyze this file.", "red")
        return 2
    return 0


def _recorded_hash(cfg: dict, f: Path) -> str | None:
    man = lib.hash_manifest(cfg)
    for h, path in lib.parse_sha256_manifest(man):
        if path == str(f) or Path(path).name == f.name:
            return h
    return None


def _record(cfg: dict, f: Path, h: str) -> None:
    man = lib.hash_manifest(cfg)
    rel = str(f.relative_to(lib.ROOT)) if f.is_relative_to(lib.ROOT) else str(f)
    keep = [ln for ln in man.read_text(encoding="utf-8").splitlines()
            if ln.startswith("#") or (ln.strip() and not re.match(r"^[0-9a-f]{64}  ", ln))]
    keep.append(f"{h}  {rel}")
    man.write_text("\n".join(keep) + "\n", encoding="utf-8")
    lib.note(f"Recorded hash for {rel} in {man}", "green")


if __name__ == "__main__":
    sys.exit(main())
