#!/usr/bin/env bash
# Stage 07: Ghidra headless import/analyze/export.
#
# Runs analyzeHeadless once per executable found by stage 04, then the
# config/ghidra/export_all.java post-script writes decompiled C and a symbol
# table into build/decomp/.
#
# Decompiled output is DERIVED WORK of the original binary and lives only
# under build/ (gitignored). Never commit it.
#
# Requires Ghidra: set GHIDRA_HOME or have analyzeHeadless on PATH
# (see docs/INSTALL.md).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REPORTS_JSON="$ROOT/build/reports/binaries.json"
ROOT_FS="$ROOT/build/iso"
GHIDRA_PROJ="$ROOT/build/decomp/ghidra"
GHIDRA_OUT="$ROOT/build/decomp"
GHIDRA_SCRIPTS="$ROOT/config/ghidra"

# --- locate analyzeHeadless ---------------------------------------------
GHIDRA_BIN=""
if [[ -n "${GHIDRA_HOME:-}" && -x "$GHIDRA_HOME/support/analyzeHeadless" ]]; then
  GHIDRA_BIN="$GHIDRA_HOME/support/analyzeHeadless"
elif command -v analyzeHeadless >/dev/null 2>&1; then
  GHIDRA_BIN="$(command -v analyzeHeadless)"
elif command -v ghidra >/dev/null 2>&1; then
  # infer the install dir from the `ghidra` launcher:
  #   /usr/bin/ghidra -> /opt/ghidra/ghidraRun -> /opt/ghidra/support/analyzeHeadless
  GHIDRA_HOME_GUESS="$(dirname "$(readlink -f "$(command -v ghidra)")")"
  if [[ -x "$GHIDRA_HOME_GUESS/support/analyzeHeadless" ]]; then
    GHIDRA_BIN="$GHIDRA_HOME_GUESS/support/analyzeHeadless"
  fi
fi
if [[ -z "$GHIDRA_BIN" ]]; then
  echo "error: analyzeHeadless not found." >&2
  echo "Install Ghidra, set GHIDRA_HOME, or put \`ghidra\` on PATH (docs/INSTALL.md)." >&2
  exit 2
fi

if [[ ! -f "$REPORTS_JSON" ]]; then
  echo "error: $REPORTS_JSON missing; run \`make binary-info\` first." >&2
  exit 2
fi

# --- enumerate executables from the stage-04 report ----------------------
# Default: the game's own DOS executables (config game.executables).
# ANALYZE_ALL=1 overrides to every DOS (non-PE) MZ executable.
# PE/Win32 files (demo DirectX DLLs) are always skipped.
python3 - "$REPORTS_JSON" "$ROOT/config/rules.yaml" > "$GHIDRA_OUT/exe_list.txt" <<'PY'
import json, os, sys
import yaml
rows = json.load(open(sys.argv[1]))
cfg = yaml.safe_load(open(sys.argv[2])) or {}
game = cfg.get("game") or {}
allow_all = os.environ.get("ANALYZE_ALL") == "1"
allowlist = [p.replace("\\", "/").lower()
             for p in (game.get("executables") or [])]
seen = set()
for e in sorted(rows, key=lambda r: r.get("path", "")):
    mz = e.get("mz")
    if not mz or mz.get("magic") != "MZ" or mz.get("pe"):
        continue
    path = e.get("path", "")
    if not allow_all and path.lower() not in allowlist:
        continue
    if path in seen:
        continue
    seen.add(path)
    print(path)
PY

mkdir -p "$GHIDRA_PROJ" "$GHIDRA_OUT"
count=0
while IFS= read -r rel; do
  exe="$ROOT_FS/$rel"
  [[ -f "$exe" ]] || continue
  stem="$(basename "$exe")"
  proj="fragile_decomp_${stem%.*}"
  echo "==> analyze $rel  (project: $proj)"
  "$GHIDRA_BIN" "$GHIDRA_PROJ" "$proj" \
      -import "$exe" \
      -overwrite \
      -analysisTimeoutPerFile 600 \
      -scriptPath "$GHIDRA_SCRIPTS" \
      -postScript export_all.java "$GHIDRA_OUT/$stem" \
      || echo "warning: analyzeHeadless failed for $rel" >&2
  count=$((count+1))
done < "$GHIDRA_OUT/exe_list.txt"

# --- flat DOS/4G image (stage 05) --------------------------------------
# Import the sliced flat 32-bit image as a raw x86 binary at base 0. Addresses
# are image-relative so relocations are not applied. set_entry.java (preScript)
# sets the entry before auto-analysis so Ghidra disassembles from it.
FLAT="$ROOT/build/flat/FRAGILE.EXE.flat"
if [[ -f "$FLAT" && -f "$ROOT/build/reports/flat_extract.json" ]]; then
  ENTRY="$(python3 -c "
import json,sys
d=json.load(open('$ROOT/build/reports/flat_extract.json'))
print(hex(d.get('entry_hint',0x14)))")"
  CODE_END="$(python3 -c "
import json,sys
d=json.load(open('$ROOT/build/reports/flat_analysis.json'))
print(hex(d.get('code_data',{}).get('code_end',0)))")"
  echo "==> analyze flat image $FLAT  (project: fragile_decomp_FRAGILE_flat)"
  "$GHIDRA_BIN" "$GHIDRA_PROJ" "fragile_decomp_FRAGILE_flat" \
      -import "$FLAT" \
      -overwrite \
      -processor x86:LE:32:default -loader BinaryLoader -loader-baseAddr 0x0 \
      -analysisTimeoutPerFile 600 \
      -scriptPath "$GHIDRA_SCRIPTS" \
      -preScript set_entry.java "$ENTRY" "$CODE_END" \
      -postScript export_all.java "$GHIDRA_OUT/FRAGILE.EXE.flat" \
      || echo "warning: analyzeHeadless failed for flat image" >&2
  count=$((count+1))
else
  echo "note: flat image not present; run \`make extract-flat flat-analyze\` to import it" >&2
fi

echo "done: analyzed $count program(s); output in $GHIDRA_OUT/"
