#!/usr/bin/env python3
"""Shared helpers for the fragile-decomp reverse-engineering pipeline.

Committed code (ours). This module only manipulates paths, hashes, and tool
output; it never reads game content into anything that could be committed.

All derived artifacts are written under build/ (gitignored).
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
CONFIG_FILE = ROOT / "config" / "rules.yaml"


# ----------------------------------------------------------------------
# config
# ----------------------------------------------------------------------

def load_config() -> dict:
    with open(CONFIG_FILE, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def _path(cfg: dict, key: str) -> Path:
    p = cfg.get("paths", {}).get(key, key)
    return (ROOT / p) if not Path(p).is_absolute() else Path(p)


def iso_file(cfg: dict) -> Path:
    return _path(cfg, "iso_file")


def iso_dir(cfg: dict) -> Path:
    return _path(cfg, "iso_dir")


def build_dir(cfg: dict) -> Path:
    return _path(cfg, "build_dir")


def extracted_dir(cfg: dict) -> Path:
    return _path(cfg, "extracted_dir")


def decomp_dir(cfg: dict) -> Path:
    return _path(cfg, "decomp_dir")


def named_dir(cfg: dict) -> Path:
    return _path(cfg, "named_dir")


def traces_dir(cfg: dict) -> Path:
    return _path(cfg, "traces_dir")


def reports_dir(cfg: dict) -> Path:
    return _path(cfg, "reports_dir")


def strings_dir(cfg: dict) -> Path:
    return _path(cfg, "strings_dir")


def flat_dir(cfg: dict) -> Path:
    return _path(cfg, "flat_dir")


def hash_manifest(cfg: dict) -> Path:
    return ROOT / cfg.get("paths", {}).get("hash_manifest", "iso.sha256")


# ----------------------------------------------------------------------
# hashing
# ----------------------------------------------------------------------

def sha256_file(path: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        while True:
            block = fh.read(chunk)
            if not block:
                break
            h.update(block)
    return h.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# ----------------------------------------------------------------------
# filesystem
# ----------------------------------------------------------------------

def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def write_json(path: Path, data) -> None:
    ensure_dir(path.parent)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, sort_keys=True)
        fh.write("\n")


def write_md(path: Path, text: str) -> None:
    ensure_dir(path.parent)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


def write_tsv(path: Path, header: list[str], rows: list[list]) -> None:
    ensure_dir(path.parent)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\t".join(header) + "\n")
        for row in rows:
            fh.write("\t".join("" if c is None else str(c) for c in row) + "\n")


# ----------------------------------------------------------------------
# sha256 provenance manifest (iso.sha256)
# ----------------------------------------------------------------------

def parse_sha256_manifest(path: Path) -> list[tuple[str, str]]:
    """Parse a `sha256sum -c`-style manifest into [(hash, path), ...].

    Blank lines and `#` comments are ignored.
    """
    entries = []
    if not path.exists():
        return entries
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if len(line) >= 64 and line[63] == " ":
            entries.append((line[:64].lower(), line[65:].strip()))
        elif "  " in line:
            h, p = line.split("  ", 1)
            entries.append((h.strip().lower(), p.strip()))
    return entries


# ----------------------------------------------------------------------
# external tools
# ----------------------------------------------------------------------

def which(name: str) -> str | None:
    return shutil.which(name)


def run(cmd: list[str], check: bool = False, timeout: int | None = None,
        capture: bool = True) -> subprocess.CompletedProcess:
    """Run a command. Return CompletedProcess (stdout/stderr captured)."""
    return subprocess.run(
        cmd,
        check=check,
        timeout=timeout,
        text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.STDOUT if capture else None,
    )


def tool_version(cmd: list[str]) -> str:
    """Best-effort extraction of a dotted version string from a tool banner."""
    try:
        res = run(cmd)
        text = (res.stdout or "") + "\n" + (res.stderr or "")
        match = re.search(r"\d+(?:\.\d+)+", text)
        return match.group(0) if match else ""
    except (OSError, subprocess.SubprocessError):
        return ""


def find_ghidra() -> str | None:
    """Locate analyzeHeadless via PATH, GHIDRA_HOME, or `ghidra` on PATH.

    Order:
      1. analyzeHeadless on PATH
      2. $GHIDRA_HOME/support/analyzeHeadless
      3. `ghidra` on PATH: /usr/bin/ghidra -> /opt/ghidra/ghidraRun,
         infer the install dir from the launcher's resolved parent
    """
    found = shutil.which("analyzeHeadless")
    if found:
        return found
    home = os.environ.get("GHIDRA_HOME")
    if home:
        cand = Path(home) / "support" / "analyzeHeadless"
        if cand.is_file():
            return str(cand)
    launcher = shutil.which("ghidra")
    if launcher:
        resolved = Path(launcher).resolve()
        if resolved.name == "ghidraRun":
            cand = resolved.parent / "support" / "analyzeHeadless"
            if cand.is_file():
                return str(cand)
    return None


# DOSBox-X flatpak app id (exported launcher com.dosbox_x.DOSBox-X).
DOSBOX_FLATPAK_ID = "com.dosbox_x.DOSBox-X"


def find_dosbox() -> list[str] | None:
    """Return the argv for a usable DOSBox(-X), or None if not found.

    Candidates, first match wins:
      1. DOSBOX_BIN env override (a single command, or a full argv)
      2. dosbox-x / dosbox on PATH
      3. DOSBox-X flatpak export com.dosbox_x.DOSBox-X (PATH or the
         standard flatpak export directories)
    """
    override = os.environ.get("DOSBOX_BIN")
    if override:
        return override.split()
    for name in ("dosbox-x", "dosbox", DOSBOX_FLATPAK_ID):
        found = shutil.which(name)
        if found:
            return [found]
    for root in (Path("/var/lib/flatpak/exports/bin"),
                 Path.home() / ".local/share/flatpak/exports/bin"):
        cand = root / DOSBOX_FLATPAK_ID
        if cand.is_file():
            return [str(cand)]
    return None


# ----------------------------------------------------------------------
# file magic
# ----------------------------------------------------------------------

_MAGIC = None


def file_magic(path: Path) -> str:
    """Return the `file` magic description for a path.

    Uses python-magic when available, otherwise shells out to `file -b`.
    """
    global _MAGIC
    try:
        if _MAGIC is None:
            import magic  # type: ignore

            _MAGIC = "py"
        return _MAGIC and magic.from_file(str(path))
    except Exception:
        _MAGIC = None
    res = run(["file", "-b", str(path)])
    return (res.stdout or "").strip()


def classify_extension(name: str) -> str:
    """Coarse category from the file extension (pre-magic hint)."""
    ext = Path(name).suffix.lower().lstrip(".")
    if ext in ("exe", "com", "ovl", "bin", "drv"):
        return "executable"
    if ext in ("dat", "pak", "pck", "res", "idx", "lib", "arc", "cpt"):
        return "data"
    if ext in ("txt", "ini", "cfg", "log", "doc", "readme", "lst", "me"):
        return "text"
    if ext in ("bmp", "gif", "jpg", "jpeg", "png", "pcx", "pic", "lbm", "img"):
        return "image"
    if ext in ("wav", "voc", "mid", "rmi", "mus", "snd", "ogg"):
        return "audio"
    if ext in ("avi", "fli", "flc", "mov", "smk", "vqa"):
        return "video"
    if ext in ("hlp", "pif"):
        return "doc"
    return "other"


# ----------------------------------------------------------------------
# report helpers
# ----------------------------------------------------------------------

def report_pair(cfg: dict, stem: str, data) -> tuple[Path, Path]:
    """Write <stem>.json + <stem>.md and return (json_path, md_path)."""
    rdir = reports_dir(cfg)
    jpath = rdir / f"{stem}.json"
    write_json(jpath, data)
    mpath = rdir / f"{stem}.md"
    return jpath, mpath


def md_table(header: list[str], rows: list[list]) -> str:
    lines = ["| " + " | ".join(header) + " |", "|" + "|".join([" --- "] * len(header)) + "|"]
    for row in rows:
        cells = ["`%s`" % c if isinstance(c, str) and " " in c else str(c) for c in row]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


# ----------------------------------------------------------------------
# CLI boilerplate
# ----------------------------------------------------------------------

def make_parser(desc: str):
    import argparse

    p = argparse.ArgumentParser(description=desc)
    p.add_argument("--no-color", action="store_true", help="disable ANSI colors")
    return p


def note(msg: str, color: str = "") -> None:
    colors = {"red": "31", "green": "32", "yellow": "33", "cyan": "36"}
    if color and sys.stdout.isatty() and not os.environ.get("NO_COLOR"):
        msg = f"\033[{colors[color]}m{msg}\033[0m"
    print(msg)
