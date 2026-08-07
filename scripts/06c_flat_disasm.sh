#!/usr/bin/env bash
# Stage 06c: objdump the flat DOS/4G image (reference build) into
# build/flat/fragile.o + build/flat/full_disasm.txt.
#
# The flat image is raw 32-bit code at base 0; objdump cannot disassemble a
# bare binary, so objcopy wraps it into an ELF relocatable whose .text is the
# flat itself. The disassembly addresses are therefore image-relative and
# match the Ghidra flat import (stage 07) exactly.
#
# The output is a derived artifact and lives only under build/ (gitignored).
# Run `make flat-disasm` (part of `make all`).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
FLAT="$ROOT/build/flat/FRAGILE.EXE.flat"
OBJ="$ROOT/build/flat/fragile.o"
DISASM="$ROOT/build/flat/full_disasm.txt"

if [[ ! -f "$FLAT" ]]; then
  echo "error: $FLAT missing; run \`make extract-flat\` first" >&2
  exit 2
fi
if ! command -v objcopy >/dev/null 2>&1 || ! command -v objdump >/dev/null 2>&1; then
  echo "error: objcopy/objdump not found (binutils). Install it (docs/INSTALL.md)." >&2
  exit 2
fi

objcopy -I binary -O elf32-i386 -B i386 --rename-section .data=.text \
    "$FLAT" "$OBJ"
objdump -d "$OBJ" > "$DISASM"

echo "flat disassembly written to $DISASM"
