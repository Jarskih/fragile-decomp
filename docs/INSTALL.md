# OpenFA — Installation manual

> **Rule 5:** the pipeline scripts never install software. This manual exists
> so the *developer* can install the required tools. If `make check` reports a
> missing tool, come back here.

## What you need

| Tool | Why | How to get it (Linux) |
|------|-----|------------------------|
| Python ≥ 3.9 | all pipeline scripts | package `python3` |
| curl | ISO download (resumable) | package `curl` |
| 7-Zip (`7z`) | ISO 9660 + archive extraction | package `p7zip-full` |
| libarchive (`bsdtar`) | fallback extractor | package `libarchive-tools` |
| file | file-type detection | package `file` |
| binutils (`strings`, `objdump`) | strings sweep, disassembly helper | package `binutils` |
| NASM (`ndisasm`) | 16-bit disassembly helper | package `nasm` |
| GNU make | pipeline orchestration | package `make` |
| Ghidra | main disassembler/decompiler | <https://ghidra-sre.org/> (see below) |
| DOSBox-X | runtime tracing / game running | see below |

Optional (stages degrade gracefully):
- `xorriso` (ISO tools), `isoinfo`/`genisoimage`, `cd-info` (track tables)

## Installing on Debian/Ubuntu

```sh
sudo apt install python3 curl p7zip-full libarchive-tools file binutils nasm make \
                 xorriso genisoimage libcdio-utils
```

On Fedora: `sudo dnf install python3 curl p7zip libarchive file binutils nasm make \
xorriso genisoimage libcdio-tools` — names vary, use your package manager.

## Ghidra

Ghidra is not in most distro repos. Install it manually:

1. Requires a Java runtime (JDK 17+). `sudo apt install openjdk-17-jdk`
2. Download Ghidra from <https://ghidra-sre.org/> (or GitHub releases).
3. Unpack it somewhere permanent, e.g. `/opt/ghidra`.
4. Point the pipeline at it in one of two ways:
   - export `GHIDRA_HOME=/opt/ghidra` in your shell profile, or
   - set it per-invocation: `GHIDRA_HOME=/opt/ghidra make disassemble`

The wrapper is `$GHIDRA_HOME/support/analyzeHeadless`; `scripts/check_env.py`
looks for it there and on `PATH`.

## DOSBox-X

DOSBox-X (with the internal debugger, useful for `make trace`):

```sh
sudo apt install dosbox-x            # Debian/Ubuntu ships it; check version
```

or grab a build from <https://dosbox-x.com/>. Plain `dosbox` works for running
the game but the debugger build gives us INT 21h file-open tracing.

## Verifying the install

```sh
make check
```

This compares installed versions against `config/rules.yaml` and never changes
your system.

## First run

```sh
make download     # fetch the reference ISO (optional — or drop yours in iso/)
make check
make all
```
