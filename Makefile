# ======================================================================
# OpenFA pipeline orchestration
#
# Every stage writes to build/ (gitignored). None of the game's original
# content is ever touched by this file or placed outside iso/ + build/.
# ======================================================================

PY      := python3
SCRIPTS := scripts

.PHONY: all check download verify extract inventory binary-info disassemble \
        strings dat-survey trace clean help

help:
	@echo "OpenFA pipeline targets:"
	@echo "  make check          verify installed toolchain (never installs)"
	@echo "  make download       fetch the reference ISO from archive.org (optional)"
	@echo "  make verify         verify image + record track table"
	@echo "  make extract        extract the ISO9660 data session to build/iso"
	@echo "  make inventory      manifest every extracted file (name/size/hash/magic)"
	@echo "  make binary-info    classify executables (16-bit vs 32-bit extender)"
	@echo "  make disassemble    Ghidra headless import/analyze/export to build/decomp"
	@echo "  make strings        strings sweep over extracted files"
	@echo "  make dat-survey     data-file format survey (magic/entropy/probes)"
	@echo "  make trace          DOSBox(-X) runtime trace"
	@echo "  make all            full pipeline (download..trace)"
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

disassemble: check-disassemble binary-info
	./$(SCRIPTS)/05_ghidra_headless.sh

strings: check-strings inventory
	$(PY) $(SCRIPTS)/06_strings.py

dat-survey: check-dat-survey inventory
	$(PY) $(SCRIPTS)/07_dat_survey.py

trace: check-trace extract
	./$(SCRIPTS)/08_dosbox_trace.sh

all: download verify extract inventory binary-info disassemble strings dat-survey trace
	@echo "Pipeline finished. Reports in build/reports/, decompiled output in build/decomp/."

clean:
	rm -rf build
	@echo "Removed build/ (iso/ and original content untouched)."
