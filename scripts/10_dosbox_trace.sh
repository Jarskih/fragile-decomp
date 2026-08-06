#!/usr/bin/env bash
# Stage 10: run the game under DOSBox(-X) and capture a trace.
#
# Generates a DOSBox config from config/dosbox/dosbox-x.conf.template that
# mounts build/iso as the CD and a scratch dir as C:, then runs the game.
#
# Runtime memory tracing (load-base dump) would need a custom DOSBox-X
# --enable-debug build; that plan is deferred. With --trace this stage passes
# -log-int21 -log-fileio, which any DOSBox-X build honors (the flag handlers
# live in the always-compiled debug lib) and records INT 21h / file-open
# activity in build/traces/. The static decompilation route (stages 05-07)
# is primary; this stage only records file-open + runtime logs.
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
import fragile_decomp_lib as lib
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
LOGFILE="$TRACES/dosbox-x.log"
python3 - "$ROOT/config/dosbox/dosbox-x.conf.template" "$CFG_OUT" \
    "$SCRATCH" "$CDROOT" "$EXE_DIR" "$EXE_NAME" "$LOGFILE" <<'PY'
import sys
tmpl, out, scratch, cdroot, exedir, exe, logfile = sys.argv[1:]
text = open(tmpl, encoding="utf-8").read()
text = text.replace("__SCRATCH__", scratch.replace("\\", "\\\\"))
text = text.replace("__ISO_DIR__", cdroot.replace("\\", "\\\\"))
text = text.replace("__EXE_DIR__", exedir.replace("\\", "\\\\"))
text = text.replace("__EXE__", exe)
text = text.replace("__LOGFILE__", logfile.replace("\\", "\\\\"))
open(out, "w", encoding="utf-8").write(text)
print("config written:", out)
print("dosbox-x log file:", logfile)
PY

# --- run -------------------------------------------------------------------
# -log-int21/-log-fileio enable INT 21h + file-open logging on any DOSBox-X
# build (the flag handlers live in the always-compiled debug lib). A custom
# --enable-debug (curses debugger) build is deferred; see docs/INSTALL.md.
if [[ "${1:-}" == "--trace" ]]; then
  echo "==> tracing INT 21h/file-open to $TRACES/trace.log"
  exec "${DOSBOX_CMD[@]}" -log-int21 -log-fileio -conf "$CFG_OUT" 2>&1 | tee "$TRACES/trace.log"
else
  "${DOSBOX_CMD[@]}" -conf "$CFG_OUT" 2>&1 | tee "$TRACES/run.log"
fi
