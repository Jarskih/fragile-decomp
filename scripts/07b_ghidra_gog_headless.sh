#!/usr/bin/env bash
# Stage 07b: Ghidra headless import/analyze/export for the GOG build's flat
# DOS/4G image.
#
# Analogue of the flat section of stage 07 (07_ghidra_headless.sh), but for the
# GOG retail build. Imports build/flat/FRAGILE.EXE.gog.flat as a raw 32-bit x86
# binary at base 0 and exports decompiled C into build/decomp/.
#
# The GOG flat image's entry point is image-relative 0x14 (same as the ISO
# build). The GOG rename entries in config/ghidra/rename-map.json live at addresses
# >= 0x80000 and do not collide with the ISO entries (< 0x80000), so `make names`
# applies the right set per program.
#
# Decompiled output is DERIVED WORK of the original binary and lives only under
# build/ (gitignored). Never commit it.
#
# Requires Ghidra: set GHIDRA_HOME or have analyzeHeadless on PATH
# (see docs/INSTALL.md).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
EXTRACT_JSON="$ROOT/build/reports/flat_extract_gog.json"
ANALYZE_JSON="$ROOT/build/reports/flat_analyze_gog.json"
GHIDRA_PROJ="$ROOT/build/decomp/ghidra_gog"
GHIDRA_OUT="$ROOT/build/decomp"
GHIDRA_SCRIPTS="$ROOT/config/ghidra"

# --- locate analyzeHeadless (same logic as 07_ghidra_headless.sh) ----------
GHIDRA_BIN=""
if [[ -n "${GHIDRA_HOME:-}" && -x "$GHIDRA_HOME/support/analyzeHeadless" ]]; then
  GHIDRA_BIN="$GHIDRA_HOME/support/analyzeHeadless"
elif command -v analyzeHeadless >/dev/null 2>&1; then
  GHIDRA_BIN="$(command -v analyzeHeadless)"
elif command -v ghidra >/dev/null 2>&1; then
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

# --- import the GOG flat image ---------------------------------------------
FLAT="$ROOT/build/flat/FRAGILE.EXE.gog.flat"
if [[ ! -f "$FLAT" || ! -f "$EXTRACT_JSON" ]]; then
  echo "error: $FLAT or $EXTRACT_JSON missing; run \`make gog-flat\` first." >&2
  exit 2
fi

# Entry point: image-relative 0x14 for the GOG build (matches the ISO build;
# the extract report's entry_hint defaults to the same value).
ENTRY="$(python3 -c "
import json,sys
d=json.load(open('$EXTRACT_JSON'))
print(hex(d.get('entry_hint',0x14)))" 2>/dev/null || echo "0x14")"
[[ "$ENTRY" == "0x0" || -z "$ENTRY" ]] && ENTRY="0x14"

# code_end is optional: only present if `make gog-flat-analyze` has run. When
# absent, set_entry.java simply omits the DATA_START label.
CODE_END=""
if [[ -f "$ANALYZE_JSON" ]]; then
  CODE_END="$(python3 -c "
import json,sys
d=json.load(open('$ANALYZE_JSON'))
print(hex(d.get('code_data',{}).get('code_end',0)))" 2>/dev/null || echo "")"
  [[ "$CODE_END" == "0x0" ]] && CODE_END=""
fi

mkdir -p "$GHIDRA_PROJ" "$GHIDRA_OUT"
echo "==> analyze GOG flat image $FLAT  project: fragile_decomp_FRAGILE_gog_flat"
PRE_ARGS=(-preScript set_entry.java "$ENTRY")
[[ -n "$CODE_END" ]] && PRE_ARGS+=("$CODE_END")
"$GHIDRA_BIN" "$GHIDRA_PROJ" "fragile_decomp_FRAGILE_gog_flat" \
    -import "$FLAT" \
    -overwrite \
    -processor x86:LE:32:default -loader BinaryLoader -loader-baseAddr 0x0 \
    -analysisTimeoutPerFile 600 \
    -scriptPath "$GHIDRA_SCRIPTS" \
    "${PRE_ARGS[@]}" \
    -postScript export_all.java "$GHIDRA_OUT/FRAGILE.EXE.gog.flat" \
    || echo "warning: analyzeHeadless failed for GOG flat image" >&2

echo "done: GOG flat analyzed; output in $GHIDRA_OUT/FRAGILE.EXE.gog.flat/"
