#!/usr/bin/env bash
# Stage 05: Ghidra headless import/analyze/export.
#
# Runs analyzeHeadless once per executable found by stage 04, then the
# config/ghidra/export_all.py post-script writes decompiled C and a symbol
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
fi
if [[ -z "$GHIDRA_BIN" ]]; then
  echo "error: analyzeHeadless not found." >&2
  echo "Install Ghidra and set GHIDRA_HOME (see docs/INSTALL.md)." >&2
  exit 2
fi

if [[ ! -f "$REPORTS_JSON" ]]; then
  echo "error: $REPORTS_JSON missing; run \`make binary-info\` first." >&2
  exit 2
fi

# --- enumerate executables from the stage-04 report ----------------------
python3 - "$REPORTS_JSON" <<'PY' > "$GHIDRA_OUT/exe_list.txt"
import json, sys
data = json.load(open(sys.argv[1]))
for e in data:
    if e.get("mz") and e["mz"].get("magic") == "MZ":
        print(e["path"])
PY

mkdir -p "$GHIDRA_PROJ" "$GHIDRA_OUT"
count=0
while IFS= read -r rel; do
  exe="$ROOT_FS/$rel"
  [[ -f "$exe" ]] || continue
  stem="$(basename "$exe")"
  proj="openfa_${stem%.*}"
  echo "==> analyze $rel  (project: $proj)"
  "$GHIDRA_BIN" "$GHIDRA_PROJ" "$proj" \
      -import "$exe" \
      -overwrite \
      -analysisTimeoutPerFile 600 \
      -scriptPath "$GHIDRA_SCRIPTS" \
      -postScript export_all.py "$GHIDRA_OUT/$stem" \
      || echo "warning: analyzeHeadless failed for $rel" >&2
  count=$((count+1))
done < "$GHIDRA_OUT/exe_list.txt"

echo "done: analyzed $count executable(s); output in $GHIDRA_OUT/"
