#!/usr/bin/env bash
# Stage 08: run the game under DOSBox(-X) and capture a trace.
#
# Generates a DOSBox config from config/dosbox/dosbox-x.conf.template that
# mounts build/iso as the CD and a scratch dir as C:, then runs the game.
# With --trace (needs the DOSBox-X debugger build) it starts the debugger and
# logs console output; file-open (INT 21h) activity appears in build/traces/.
#
# Env overrides:
#   GAME_EXE     relative path to the game executable inside the CD tree
#                (default: auto-discover FRAGILE.EXE)
#   DOSBOX_BIN   dosbox(-x) binary (default: dosbox-x, fallback dosbox)
#
# Traces are derived runtime behavior and live only under build/ (gitignored).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CDROOT="$ROOT/build/iso"
CFG_OUT="$ROOT/build/dosbox/dosbox-x.conf"
SCRATCH="$ROOT/build/dosbox/cdrive"
TRACES="$ROOT/build/traces"

if [[ ! -d "$CDROOT" ]]; then
  echo "error: $CDROOT missing; run \`make extract\` first." >&2
  exit 2
fi

if [[ -z "${DOSBOX_BIN:-}" ]]; then
  if command -v dosbox-x >/dev/null 2>&1; then
    DOSBOX_BIN="dosbox-x"
  elif command -v dosbox >/dev/null 2>&1; then
    DOSBOX_BIN="dosbox"
  else
    echo "error: neither dosbox-x nor dosbox found (docs/INSTALL.md)." >&2
    exit 2
  fi
fi

# --- locate the game executable -----------------------------------------
if [[ -n "${GAME_EXE:-}" ]]; then
  EXE_REL="$GAME_EXE"
else
  EXE_REL="$(python3 - "$CDROOT" <<'PY'
import pathlib, sys
root = pathlib.Path(sys.argv[1])
for cand in ("FRAGILE.EXE", "fragile.exe", "Fragile.exe", "FRAGILE"):
    hits = sorted(root.rglob(cand))
    if hits:
        print(hits[0].relative_to(root).as_posix()); sys.exit(0)
# fall back to any *.exe at the top two levels
for p in sorted(root.rglob("*.exe")):
    parts = p.relative_to(root).parts
    if len(parts) <= 3:
        print(p.relative_to(root).as_posix()); sys.exit(0)
print("")
PY
)"
fi

if [[ -z "$EXE_REL" ]]; then
  echo "warning: could not auto-discover the game executable." >&2
  echo "Set GAME_EXE=path/on/cd e.g. GAME_EXE=fragalle/FRAGILE.EXE" >&2
  EXE_REL="FRAGILE.EXE"
fi
EXE_DIR="$(dirname "$EXE_REL")"
[[ "$EXE_DIR" == "." ]] && EXE_DIR="\\"
EXE_NAME="$(basename "$EXE_REL")"
echo "==> running $DOSBOX_BIN; executable: d:\\$EXE_REL"

# --- substitute placeholders into the config template ---------------------
mkdir -p "$SCRATCH" "$TRACES"
python3 - "$ROOT/config/dosbox/dosbox-x.conf.template" "$CFG_OUT" \
    "$SCRATCH" "$CDROOT" "$EXE_DIR" "$EXE_NAME" <<'PY'
import sys
tmpl, out, scratch, cdroot, exedir, exe = sys.argv[1:]
text = open(tmpl, encoding="utf-8").read()
text = text.replace("__SCRATCH__", scratch.replace("\\", "\\\\"))
text = text.replace("__ISO_DIR__", cdroot.replace("\\", "\\\\"))
text = text.replace("__EXE_DIR__", exedir.replace("\\", "\\\\"))
text = text.replace("__EXE__", exe)
open(out, "w", encoding="utf-8").write(text)
print("config written:", out)
PY

# --- run -------------------------------------------------------------------
if [[ "${1:-}" == "--trace" ]]; then
  echo "==> starting with debugger (DOSBox-X). Console trace in build/traces/."
  exec "$DOSBOX_BIN" -startdebugger -conf "$CFG_OUT" 2>&1 | tee "$TRACES/trace.log"
else
  "$DOSBOX_BIN" -conf "$CFG_OUT" 2>&1 | tee "$TRACES/run.log"
fi
