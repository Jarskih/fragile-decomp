#!/usr/bin/env python3
"""Stage 11: build a named-view mirror of the decompiled output.

Ghidra's exports under build/decomp/<prog>/ (decompiled.c + functions.tsv) are
treated as read-only derived artifacts: they are byte-identical to what stage 07
wrote and are never edited. This stage copies them into build/named/<prog>/ and
applies the curated name map config/ghidra/rename-map.json (word-boundary
substitutions), so the named view is a separate derived copy that `make clean`
regenerates like everything else.

The map keys are image-relative addresses for the flat image:
  globals   0x16d6c -> g_mode_flag      (renames DAT_00016d6c)
  functions 0x5bada -> rng_next         (renames FUN_0005bada)
  literals  0xc3f4  -> g_obj_list_sentinel  (renames the raw literal 0xc3f4)
  locals    0x31af4 -> { "iVar3": "slot", ... }  (function-scoped renames)
Global keys also rename RAM-pointer symbols: iRam0000c3c4 and uRam0000c3c4
are matched for globals such as 0xc3c4 -> g_asteroid_ptr.
Hex keys may be written with or without the 0x prefix, any case. Names must be
valid C identifiers (the script refuses to apply anything else).

The locals section is keyed by function address and maps the Ghidra register/
stack names inside that function (iVar3, sVar1, extraout_ECX, ...) to our names.
Each rename is applied only between that function's header comment and the next
one, so the same Ghidra name can mean different things in different functions.
Only renames whose meaning is established by analysis (and recorded in docs/)
should be added; when in doubt, leave the register name alone.

The named view is derived game code and lives only under build/ (gitignored).
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fragile_decomp_lib as lib  # noqa: E402

MAP_FILE = lib.ROOT / "config" / "ghidra" / "rename-map.json"

_IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_HEX = set("0123456789abcdef")


def load_map(path: Path) -> tuple[list[tuple[str, str]],
                                   dict[int, list[tuple[str, str]]], int]:
    """Return (global_table, function-addr -> local renames, total_name_count)."""
    if not path.exists():
        return [], {}, 0
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected a JSON object")

    tables: list[tuple[str, str]] = []

    def add_global(kind: str, prefix: str) -> None:
        for raw, name in (data.get(kind) or {}).items():
            addr = raw.strip().lower()
            if addr.startswith("0x"):
                addr = addr[2:]
            if not addr or not all(c in _HEX for c in addr):
                raise ValueError(f"invalid {kind} address {raw!r} in {path}")
            if not _IDENT.match(name):
                raise ValueError(f"not a valid C identifier {name!r} in {path}")
            token = f"{prefix}{int(addr, 16):08x}"
            # Ghidra prefixes overlapping globals with '_' (_DAT_0006bfb8).
            for t in (token, f"_{token}"):
                if t not in dict(tables):
                    tables.append((t, name))

    add_global("globals", "DAT_")
    # RAM-pointer globals get iRam/uRam symbols rather than DAT_.
    add_global("globals", "iRam")
    add_global("globals", "uRam")
    add_global("functions", "FUN_")

    for raw, name in (data.get("literals") or {}).items():
        addr = raw.strip().lower()
        if addr.startswith("0x"):
            addr = addr[2:]
        if not addr or not all(c in _HEX for c in addr):
            raise ValueError(f"invalid literal address {raw!r} in {path}")
        if not _IDENT.match(name):
            raise ValueError(f"not a valid C identifier {name!r} in {path}")
        tables.append((f"0x{int(addr, 16):x}", name))

    # longest first so a token is never a prefix of a longer one being replaced
    tables.sort(key=lambda kv: len(kv[0]), reverse=True)

    locals_map: dict[int, list[tuple[str, str]]] = {}
    for fraw, inner in (data.get("locals") or {}).items():
        addr = fraw.strip().lower()
        if addr.startswith("0x"):
            addr = addr[2:]
        if not addr or not all(c in _HEX for c in addr):
            raise ValueError(f"invalid function address {fraw!r} in {path}")
        if not isinstance(inner, dict):
            raise ValueError(f"locals for {fraw!r} in {path} must be a JSON object")
        table: list[tuple[str, str]] = []
        for old, new in inner.items():
            if not _IDENT.match(old):
                raise ValueError(f"not a valid local name {old!r} in {path}")
            if not _IDENT.match(new):
                raise ValueError(f"not a valid C identifier {new!r} in {path}")
            table.append((old, new))
        table.sort(key=lambda kv: len(kv[0]), reverse=True)
        locals_map[int(addr, 16)] = table

    local_count = sum(len(t) for t in locals_map.values())
    return tables, locals_map, len(data.get("globals", {})) \
        + len(data.get("functions", {})) + len(data.get("literals", {})) \
        + local_count


def _subst(text: str, tables: list[tuple[str, str]]) -> str:
    for old, new in tables:
        text = re.sub(rf"\b{re.escape(old)}\b", new, text)
    return text


_FUNC_HEADER = re.compile(
    r"^/\* ===== .*? @ ([0-9a-fA-F]{8}) \(size \d+\) ===== \*/$")


def apply_locals(text: str, locals_map: dict[int, list[tuple[str, str]]]
                 ) -> tuple[str, set[tuple[int, str]]]:
    """Rewrite local variables inside their own function's block only.

    The named view is line-structured: every function starts with a header line
    '/* ===== <name> @ <addr> (size N) ===== */'. Local renames keyed by that
    address are applied to each line between it and the next header, so the
    same Ghidra register name (iVar3, sVar1, ...) may mean different things in
    different functions.
    """
    out: list[str] = []
    hits: set[tuple[int, str]] = set()
    cur: int | None = None
    for line in text.splitlines(keepends=True):
        m = _FUNC_HEADER.match(line)
        if m:
            cur = int(m.group(1), 16)
            out.append(line)
            continue
        if cur is not None:
            table = locals_map.get(cur)
            if table:
                for old, new in table:
                    pattern = rf"\b{re.escape(old)}\b"
                    if re.search(pattern, line):
                        hits.add((cur, old))
                        line = re.sub(pattern, new, line)
        out.append(line)
    return "".join(out), hits


def header(program: str, applied: int, mapped: int,
           local_hits: set[tuple[int, str]],
           locals_map: dict[int, list[tuple[str, str]]]) -> str:
    n_locals = sum(len(t) for t in locals_map.values())
    return (
        f"/* Named view of build/decomp/{program}/decompiled.c.\n"
        f" * Generated by scripts/11_apply_names.py from\n"
        f" * config/ghidra/rename-map.json ({mapped} curated name(s), {applied}\n"
        f" * global token(s); {n_locals} local rename(s) across {len(locals_map)}\n"
        f" * function(s), {len(local_hits)} local token(s) matched here). The raw\n"
        f" * export in build/decomp/ is untouched.\n"
        f" * This is derived game code; it stays under build/ (gitignored). */\n\n"
    )


def process_program(prog_dir: Path, out_dir: Path, tables: list[tuple[str, str]],
                    locals_map: dict[int, list[tuple[str, str]]],
                    mapped: int) -> tuple[int, int]:
    src_c = prog_dir / "decompiled.c"
    if not src_c.exists():
        return 0, 0
    out_dir.mkdir(parents=True, exist_ok=True)

    text = src_c.read_text(encoding="utf-8")
    named = _subst(text, tables)
    named, local_hits = apply_locals(named, locals_map)
    applied = sum(old in text for old, _ in tables)
    (out_dir / "decompiled.c").write_text(
        header(prog_dir.name, applied, mapped, local_hits, locals_map)
        + named, encoding="utf-8")

    src_t = prog_dir / "functions.tsv"
    if src_t.exists():
        rows = src_t.read_text(encoding="utf-8").splitlines()
        named_rows = []
        for line in rows:
            name, sep, rest = line.partition("\t")
            named_rows.append(_subst(name, tables) + sep + rest if sep else line)
        (out_dir / "functions.tsv").write_text("\n".join(named_rows) + "\n",
                                               encoding="utf-8")
    return 1, len(local_hits)


def main() -> int:
    cfg = lib.load_config()
    decomp = lib.decomp_dir(cfg)
    outroot = lib.named_dir(cfg)
    tables, locals_map, mapped = load_map(MAP_FILE)

    programs = [p for p in sorted(decomp.iterdir())
                if p.is_dir() and (p / "decompiled.c").exists()]
    if not programs:
        lib.note(f"no decompiled output under {decomp}; run `make disassemble` "
                 "first", "yellow")
        return 0
    count = 0
    local_hits = 0
    for p in programs:
        prog_count, prog_hits = process_program(
            p, outroot / p.name, tables, locals_map, mapped)
        count += prog_count
        local_hits += prog_hits
    lib.note(f"[apply_names] {mapped} curated name(s) from {MAP_FILE} "
             f"({len(locals_map)} function(s) with local renames); {count} "
             f"program(s) mirrored to {outroot}; {local_hits} local token(s) "
             "matched", "green")
    return 0


if __name__ == "__main__":
    sys.exit(main())
