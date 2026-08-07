# ======================================================================
# fragile-decomp pipeline orchestration
#
# Every stage writes to build/ (gitignored). None of the game's original
# content is ever touched by this file or placed outside iso/ + build/.
# ======================================================================

PY      := python3
SCRIPTS := scripts

.PHONY: all check download verify extract inventory binary-info disassemble \
        strings dat-survey trace memdump memdump-all extract-flat flat-analyze flat-disasm runtime names \
        gog-flat gog-constants dump-constants messages clean help

help:
	@echo "fragile-decomp pipeline targets:"
	@echo "  make check          verify installed toolchain (never installs)"
	@echo "  make download       fetch the reference ISO from archive.org (optional)"
	@echo "  make verify         verify image + record track table"
	@echo "  make extract        extract the ISO9660 data session to build/iso"
	@echo "  make inventory      manifest every extracted file (name/size/hash/magic)"
	@echo "  make binary-info    classify executables (16-bit vs 32-bit extender)"
	@echo "  make extract-flat   slice the DOS/4G bound flat image from FRAGILE.EXE"
	@echo "  make flat-analyze   analyse the flat image (entry/code/data/strings)"
	@echo "  make runtime        replay the DOS/4G relocation stream over the flat"
	@echo "                      image; verifies the image is pre-linked at base 0"
	@echo "                      and emits build/flat/FRAGILE.EXE.runtime.flat"
	@echo "  make flat-disasm    objdump the flat image to build/flat/full_disasm.txt"
	@echo "                      (addresses are image-relative, same as stage 07)"
	@echo "  make disassemble    Ghidra headless import/analyze/export to build/decomp"
	@echo "                      (9 DOS programs + the flat DOS/4G image at base 0)"
	@echo "  make strings        strings sweep over extracted files"
	@echo "  make dat-survey     data-file format survey (magic/entropy/probes)"
	@echo "  make trace          DOSBox(-X) runtime trace (INT 21h/file-open log)"
	@echo "  make memdump        read-only memory snapshot of the game running under"
	@echo "                      DOSBox(-X) -> build/dumps (powershell, Windows side)"
	@echo "  make memdump-all    memdump + every committed region >= 64 KiB"
	@echo "                      (captures conventional/UMB memory; needed for the"
	@echo "                      DS data segment the stat tables live in)"
	@echo "  make gog-flat       slice + verify the GOG build's DOS/4G flat image"
	@echo "                      (build/flat/FRAGILE.EXE.gog.flat; needs the gitignored"
	@echo "                      'Fragile Allegiance/' retail install tree)"
	@echo "  make gog-constants  decode the gameplay stat tables of the GOG build"
	@echo "                      (ore values, costs, stat records) -> build/reports/"
	@echo "  make dump-constants decode a memdump: locate the image, derive the load"
	@echo "                      bases, cross-check the tables at their runtime addresses"
 	@echo "  make names          mirror decompiled.c to build/named/ with curated"
 	@echo "                      names from config/ghidra/rename-map.json"
 	@echo "  make messages       catalog of every message the player can receive"
 	@echo "                      (AMERICAN.TXT notifications + AMERICAN.SCR dialogue)"
 	@echo "                      -> build/reports/messages-catalog.md/.json"
 	@echo "  make all            full pipeline (download..names)"
	@echo "  make clean          wipe build/ (derived artifacts only; iso/ untouched)"

check:
	$(PY) $(SCRIPTS)/check_env.py

# Stage-scoped environment check (pattern rule). Each stage verifies only the
# tools it actually needs, so e.g. `make verify` works before Ghidra exists.
check-%:
	$(PY) $(SCRIPTS)/check_env.py --for $*

download: check-download
	$(PY) $(SCRIPTS)/00_download_iso.py

verify: check-verify
	$(PY) $(SCRIPTS)/01_verify_iso.py

extract: check-extract verify
	$(PY) $(SCRIPTS)/02_extract_iso.py

inventory: check-inventory extract
	$(PY) $(SCRIPTS)/03_inventory.py

binary-info: check-binary-info inventory
	$(PY) $(SCRIPTS)/04_binary_info.py

extract-flat: check-extract-flat inventory
	$(PY) $(SCRIPTS)/05_extract_flat.py

flat-analyze: check-flat-analyze extract-flat
	$(PY) $(SCRIPTS)/06_flat_analyze.py

runtime: check-runtime extract-flat
	$(PY) $(SCRIPTS)/build_runtime.py

flat-disasm: check-flat-disasm extract-flat
	./$(SCRIPTS)/06c_flat_disasm.sh

disassemble: check-disassemble binary-info flat-analyze
	./$(SCRIPTS)/07_ghidra_headless.sh

strings: check-strings inventory
	$(PY) $(SCRIPTS)/08_strings.py

dat-survey: check-dat-survey inventory
	$(PY) $(SCRIPTS)/09_dat_survey.py

trace: check-trace extract
	./$(SCRIPTS)/10_dosbox_trace.sh

# Windows-only: snapshots the emulated RAM of a running DOSBox(-X) via
# ReadProcessMemory (read-only observation). The game must be running first.
memdump:
	powershell.exe -NoProfile -ExecutionPolicy Bypass -File $(SCRIPTS)/memdump.ps1

# Windows-only: like memdump, but also captures every committed region >= 64 KiB
# (conventional/UMB memory, where the game's DS data segment lives).
memdump-all:
	powershell.exe -NoProfile -ExecutionPolicy Bypass -File $(SCRIPTS)/memdump.ps1 -AllSmall

gog-flat: check-gog-flat
	$(PY) $(SCRIPTS)/05b_extract_gog_flat.py

gog-constants: check-gog-constants gog-flat
	$(PY) $(SCRIPTS)/12_gog_constants.py

dump-constants: check-dump-constants gog-flat
	$(PY) $(SCRIPTS)/13_dump_constants.py

stats: check-dump-constants gog-flat
	$(PY) $(SCRIPTS)/14_extract_stats.py

names:
	$(PY) $(SCRIPTS)/11_apply_names.py

messages: check-strings extract
	$(PY) $(SCRIPTS)/15_messages_catalog.py

all: download verify extract inventory binary-info extract-flat flat-analyze runtime flat-disasm disassemble strings dat-survey trace names messages
	@echo "Pipeline finished. Reports in build/reports/, decompiled output in build/decomp/, named view in build/named/."

clean:
	rm -rf build
	@echo "Removed build/ (iso/ and original content untouched)."
