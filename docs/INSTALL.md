# fragile-decomp — Installation manual

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
4. Make sure the pipeline can find it — any of:
   - export `GHIDRA_HOME=/opt/ghidra` in your shell profile, or
   - set it per-invocation: `GHIDRA_HOME=/opt/ghidra make disassemble`, or
   - put `ghidraRun` on `PATH` (the pipeline then infers the install dir
     from the launcher; a symlink like `/usr/bin/ghidra -> /opt/ghidra/ghidraRun`
     works too).

The wrapper is `$GHIDRA_HOME/support/analyzeHeadless`; `scripts/check_env.py`
looks for it via `GHIDRA_HOME`, on `PATH`, and via the `ghidra` launcher.

## DOSBox-X

DOSBox-X for `make trace` (INT 21h / file-open logging works on any build):

```sh
sudo apt install dosbox-x            # Debian/Ubuntu ships it; check version
```

or grab a build from <https://dosbox-x.com/>. Plain `dosbox` also runs the
game; the pipeline auto-detects both. A custom `--enable-debug` (curses
debugger) build is NOT currently needed: the static decompilation route is
primary, and a runtime load-base trace is deferred (see
`docs/dataformats/dos4gw-bound.md`).

**Flatpak:** `flatpak install flathub com.dosbox_x.DOSBox-X`. The pipeline
auto-detects the exported launcher (`com.dosbox_x.DOSBox-X`), so no extra
setup is needed. Note the sandbox: `make trace` mounts `build/iso` and
`build/dosbox/cdrive`, so grant filesystem access if mounting fails:

```sh
flatpak override --user --filesystem=host com.dosbox_x.DOSBox-X
```

A custom binary or argv can always be forced with `DOSBOX_BIN=dosbox-x`.

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
