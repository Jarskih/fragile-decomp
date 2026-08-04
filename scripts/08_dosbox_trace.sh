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
#   DOSBOX_BIN   dosbox(-x) binary or full argv (default: auto-detect
#                dosbox-x / dosbox / DOSBox-X flatpak)
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

# --- locate DOSBox(-X) ---------------------------------------------------
read -r -a DOSBOX_CMD <<< "$(python3 - "$ROOT/scripts" <<'PY'
import sys
sys.path.insert(0, sys.argv[1])
import openfa_lib as lib
argv = lib.find_dosbox()
print(" ".join(argv) if argv else "")
PY
)"
if [[ ${#DOSBOX_CMD[@]} -eq 0 ]]; then
  echo "error: DOSBox(-X) not found (see docs/INSTALL.md), or set DOSBOX_BIN=." >&2
  exit 2
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
echo "==> running ${DOSBOX_CMD[*]}; executable: d:\\$EXE_REL"

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
  exec "${DOSBOX_CMD[@]}" -startdebugger -conf "$CFG_OUT" 2>&1 | tee "$TRACES/trace.log"
else
  "${DOSBOX_CMD[@]}" -conf "$CFG_OUT" 2>&1 | tee "$TRACES/run.log"
fi
