#!/usr/bin/env python3
"""Stage 00: (optional) download the reference ISO from archive.org.

Resumable via curl; refuses to clobber an existing image; verifies SHA-256
when a hash is recorded in iso.sha256; can record the hash (--record-hash)
for reproducibility.

Rule 1: the ISO is written only under iso/ (gitignored).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import fragile_decomp_lib as lib


def main() -> int:
    cfg = lib.load_config()
    sources = cfg.get("iso", {}).get("sources", [])
    default_id = cfg.get("iso", {}).get("default_identifier", "")

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source", default=default_id,
                    help="archive.org source identifier (default: %(default)s)")
    ap.add_argument("--force", action="store_true",
                    help="re-download even if the image exists")
    ap.add_argument("--record-hash", action="store_true",
                    help="write the verified hash into iso.sha256")
    args = ap.parse_args()

    src = next((s for s in sources if s.get("identifier") == args.source), None)
    if src is None:
        lib.note(f"unknown source identifier '{args.source}'. Known: "
                 + ", ".join(s["identifier"] for s in sources), "red")
        return 2

    target = lib.iso_dir(cfg) / src["filename"]
    recorded = _recorded_hash(cfg, target)

    if target.exists() and not args.force:
        actual = lib.sha256_file(target)
        if recorded and actual == recorded:
            lib.note(f"{target} already present and hash matches.", "green")
            return 0
        if recorded:
            lib.note(f"{target} already present but hash MISMATCH "
                     f"(expected {recorded[:16]}…, got {actual[:16]}…). "
                     "Use --force to re-download.", "red")
            return 2
        lib.note(f"{target} already present (hash not yet recorded).", "yellow")
        if args.record_hash:
            _record(cfg, target, actual, src)
        return 0

    part = target.with_suffix(target.suffix + ".part")
    urls = _mirror_urls(src)
    lib.note(f"Downloading {src['identifier']} ({len(urls)} mirror(s))", "cyan")
    ok = False
    for url in urls:
        lib.note(f"  -> {url}", "cyan")
        res = lib.run([
            "curl", "-L", "-C", "-", "--fail",
            "--retry", "15", "--retry-all-errors", "--retry-delay", "3",
            "--retry-connrefused",
            "--speed-limit", "2048", "--speed-time", "60",
            "-w", "\n[http] code=%{http_code} bytes=%{size_download}\n",
            "--output", str(part), url,
        ], capture=False)
        if res.returncode == 0:
            ok = True
            break
        lib.note(f"  mirror failed (curl exit {res.returncode}); trying next…", "yellow")
    if not ok:
        lib.note("all mirrors failed. archive.org CDN may be overloaded; wait a "
                 "while and run `make download` again — a .part file is kept, so "
                 "the download resumes.", "red")
        lib.note("Alternative: download manually to iso/FragileAllegiance.iso, "
                 "then run `python3 scripts/01_verify_iso.py --record-hash`.", "yellow")
        return 1
    if not part.exists() or part.stat().st_size == 0:
        lib.note("download produced no data", "red")
        return 1
    part.replace(target)

    expected_size = src.get("size")
    actual_size = target.stat().st_size
    if expected_size and actual_size != expected_size:
        lib.note(f"size mismatch: expected {expected_size}, got {actual_size}. "
                 "The remote file may have changed.", "red")
        return 1

    actual = lib.sha256_file(target)
    if recorded and actual != recorded:
        lib.note(f"downloaded file hash MISMATCH: expected {recorded[:16]}…, "
                 f"got {actual[:16]}…", "red")
        return 2
    if recorded:
        lib.note(f"downloaded {target} ({actual_size} bytes), hash verified.", "green")
    else:
        lib.note(f"downloaded {target} ({actual_size} bytes).", "green")

    if args.record_hash:
        _record(cfg, target, actual, src)
    else:
        lib.note(f"sha256: {actual}", "cyan")
        lib.note("Tip: run with --record-hash to pin this hash in iso.sha256 "
                 "(keeps the pipeline reproducible).", "yellow")
    return 0


def _mirror_urls(src: dict) -> list[str]:
    """Candidate download URLs, most preferred first.

    1. the canonical archive.org/download/... endpoint (redirects to a live
       CDN node, rotated per request),
    2. the item's direct storage node derived from the metadata API
       (https://<server><dir>/<filename>).

    archive.org's CDN nodes intermittently return HTTP 500; trying both
    sources and retrying within curl makes the download resilient to that.
    """
    urls = [src["url"]]
    try:
        meta = lib.run(["curl", "-s", "--max-time", "30", "--fail",
                        f"https://archive.org/metadata/{src['identifier']}"])
        if meta.returncode == 0 and meta.stdout:
            d = json.loads(meta.stdout)
            server, dire = d.get("server"), d.get("dir")
            if server and dire:
                node = f"https://{server}{dire}/{src['filename']}"
                if node != src["url"]:
                    urls.append(node)
    except (json.JSONDecodeError, OSError):
        pass
    return urls


def _recorded_hash(cfg: dict, target: Path) -> str | None:
    man = lib.hash_manifest(cfg)
    if not man.exists():
        return None
    want = str(target.relative_to(lib.ROOT))
    for entry in lib.parse_sha256_manifest(man):
        h, path = entry
        if path == want or Path(path).name == target.name:
            return h
    return None


def _record(cfg: dict, target: Path, h: str, src: dict) -> None:
    man = lib.hash_manifest(cfg)
    rel = str(target.relative_to(lib.ROOT))
    header = (
        "# fragile-decomp ISO provenance manifest (committed for reproducibility)\n"
        "# Contains hashes and file names only — never any game content.\n"
        f"# source: {src['url']}\n"
    )
    # Keep any unrelated (already-committed) lines, drop stale entries for rel.
    lines = []
    if man.exists():
        for line in man.read_text(encoding="utf-8").splitlines():
            if line.startswith("#") or line.startswith("sha256 "):
                continue
            lines.append(line)
    lines.append(f"{h}  {rel}")
    man.write_text(header + "\n" + "\n".join(lines) + "\n", encoding="utf-8")
    lib.note(f"Recorded hash for {rel} in {man}", "green")


if __name__ == "__main__":
    sys.exit(main())
