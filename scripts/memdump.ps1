# scripts/memdump.ps1 — read-only memory snapshot of the game running under
# DOSBox(-X). Part of the "runtime memory trace" resolution path (see
# docs/mechanics/weapon-and-turret-numbers.md).
#
# What it does:
#   1. attaches READ-ONLY to the running DOSBox/DOSBox-X process
#      (PROCESS_VM_READ | PROCESS_QUERY_INFORMATION — nothing is written);
#   2. walks the process address space with VirtualQueryEx;
#   3. finds the emulated RAM block by locating the DOS/4G extender stub
#      marker ("DOS/4G", the standard extender copyright string — not game
#      content) inside it;
#   4. dumps the whole block to build/dumps/ram_<base>.bin with a sidecar
#      JSON (process, bitness, marker linear address, estimated image base).
#
# The game itself is never modified, patched, or automated — this is
# observation only, and the dumps are derived artifacts that stay under
# build/ (gitignored).
#
# Usage (from the repo root, after the game is running at the main menu):
#   powershell -NoProfile -ExecutionPolicy Bypass -File scripts\memdump.ps1
#   make memdump
#
# Parameters:
#   -ProcId   specific process id (default: the single DOSBox/DOSBox-X process)
#   -Name     process name prefix to match (default "DOSBox")
#   -Marker   ASCII marker identifying the DOS/4G stub (default "DOS/4G")
#   -StubMarkerOffset  file offset of the marker in the DOS/4G stub
#             (default 0x25c) — used to estimate the image base
#   -All      also dump every committed readable private region >= 4 MiB
#   -AllSmall also dump every committed readable private region >= 64 KiB
#             (captures conventional/UMB memory, which is a separate DOSBox
#             region from the marker region)
#   -Force    overwrite existing dump files
#
# Exit codes: 0 = at least one dump written; 2 = no DOSBox process found;
# 3 = process found but no marker (and not -All); 4 = usage error.

[CmdletBinding()]
param(
    [int]$ProcId = 0,
    [string]$Name = "DOSBox",
    [string]$Marker = "DOS/4G",
    [long]$StubMarkerOffset = 0x25c,
    [switch]$All,
    [switch]$AllSmall,
    [switch]$Force
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
$OutDir = Join-Path $RepoRoot "build\dumps"

$MEM_COMMIT = 0x1000
$PROCESS_VM_READ = 0x0010
$PROCESS_QUERY_INFORMATION = 0x0400
$PAGE_NOACCESS = 0x01
$PAGE_GUARD = 0x100
$MinDumpSize = 1MB
$AllMinSize = 4MB
$ChunkSize = 131072

Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;

public static class MemDump {
    [DllImport("kernel32.dll")]
    public static extern IntPtr OpenProcess(uint access, bool inherit, uint pid);

    [DllImport("kernel32.dll")]
    public static extern bool CloseHandle(IntPtr h);

    [DllImport("kernel32.dll")]
    public static extern uint VirtualQueryEx(IntPtr h, IntPtr addr, IntPtr buf, uint len);

    [DllImport("kernel32.dll")]
    public static extern bool ReadProcessMemory(IntPtr h, IntPtr addr,
        byte[] buf, uint size, out IntPtr read);
}
"@

function Parse-Mbi([byte[]]$buf, [bool]$is64, [ref]$baseAddr, [ref]$size, [ref]$state) {
    if ($is64) {
        $baseAddr.Value = [BitConverter]::ToInt64($buf, 0)
        $size.Value    = [BitConverter]::ToInt64($buf, 24)
        $state.Value   = [BitConverter]::ToInt32($buf, 32)
    } else {
        $baseAddr.Value = [BitConverter]::ToInt32($buf, 0) -band 0xFFFFFFFFL
        $size.Value    = [BitConverter]::ToInt32($buf, 12) -band 0xFFFFFFFFL
        $state.Value   = [BitConverter]::ToInt32($buf, 16)
    }
}

function Read-Region([IntPtr]$h, [long]$base, [long]$size) {
    $out = New-Object System.IO.MemoryStream
    $buf = New-Object byte[] $ChunkSize
    $off = 0L
    while ($off -lt $size) {
        $len = [Math]::Min($ChunkSize, $size - $off)
        $read = [IntPtr]::Zero
        if (-not [MemDump]::ReadProcessMemory($h, [IntPtr]($base + $off), $buf, $len, [ref]$read)) {
            return $null
        }
        $out.Write($buf, 0, [int]$read.ToInt64())
        $off += $read.ToInt64()
        if ($read.ToInt64() -eq 0) { break }
    }
    return $out.ToArray()
}

function Find-Marker([byte[]]$data, [string]$marker) {
    $needle = [System.Text.Encoding]::ASCII.GetBytes($marker)
    $limit = $data.Length - $needle.Length
    for ($i = 0; $i -le $limit; $i++) {
        $hit = $true
        for ($j = 0; $j -lt $needle.Length; $j++) {
            if ($data[$i + $j] -ne $needle[$j]) { $hit = $false; break }
        }
        if ($hit) { return $i }
    }
    return -1
}

# --- locate the process -------------------------------------------------
$proc = $null
if ($ProcId -ne 0) {
    $proc = Get-Process -Id $ProcId -ErrorAction SilentlyContinue
    if (-not $proc) { Write-Output "no process with pid $ProcId"; exit 4 }
} else {
    $cands = @(Get-Process -Name "$Name*" -ErrorAction SilentlyContinue)
    if ($cands.Count -eq 0) {
        Write-Output "no process matching '$Name*' is running. Start the game first (get it to the main menu or colony view)."
        exit 2
    }
    if ($cands.Count -gt 1) {
        Write-Output ("multiple processes match '{0}*': {1} - rerun with -ProcId" -f $Name, (($cands | ForEach-Object { "$($_.Id):$($_.ProcessName)" }) -join ', '))
        exit 4
    }
    $proc = $cands[0]
}

$h = [MemDump]::OpenProcess($PROCESS_VM_READ -bor $PROCESS_QUERY_INFORMATION, $false, [uint32]$proc.Id)
if ($h -eq [IntPtr]::Zero) {
    Write-Output "OpenProcess failed (error $([Runtime.InteropServices.Marshal]::GetLastWin32Error())). The game must be running under the same user account."
    exit 4
}

# --- walk the address space ---------------------------------------------
$mbi = [Runtime.InteropServices.Marshal]::AllocHGlobal(48)
try {
    $cursor = 0L
    $is64 = $true
    $hits = @()
    $allRegions = @()
    $tried32 = $false
    $summary = @()
    New-Item -ItemType Directory -Path $OutDir -Force | Out-Null
    while ($true) {
        $ret = [MemDump]::VirtualQueryEx($h, [IntPtr]$cursor, $mbi, 48)
        if ($ret -eq 0) { break }
        if ($ret -eq 28 -and -not $tried32) { $is64 = $false; $tried32 = $true }  # 32-bit target
        $buf = New-Object byte[] $ret
        [Runtime.InteropServices.Marshal]::Copy($mbi, $buf, 0, $ret)
        $b = 0L; $s = 0L; $st = 0
        Parse-Mbi $buf $is64 ([ref]$b) ([ref]$s) ([ref]$st)
        if ($s -le 0) { break }
        $next = $b + $s
        if ($next -le $b) { break }

        if ($st -eq $MEM_COMMIT -and $s -ge 0x10000) {
            $data = Read-Region $h $b $s
            if ($data) {
                $allRegions += [PSCustomObject]@{ Base = $b; Size = $s }
                if ($s -ge $MinDumpSize) {
                    $idx = Find-Marker $data $Marker
                    if ($idx -ge 0) {
                        $hits += 1
                        $fname = "ram_{0:x}.bin" -f $b
                        $path = Join-Path $OutDir $fname
                        if (-not (Test-Path $path) -or $Force) {
                            [System.IO.File]::WriteAllBytes($path, $data)
                            $summary += [PSCustomObject]@{
                                File = $path
                                Base = ('0x{0:x}' -f $b)
                                Size = $s
                                MarkerLinear = ('0x{0:x}' -f ($b + $idx))
                                EstImageBase = ('0x{0:x}' -f ($b + $idx - $StubMarkerOffset))
                            }
                            Write-Output ("dumped {0} ({1} bytes, {2} MiB)" -f $fname, $s, [Math]::Round($s / 1MB, 1))
                        } else {
                            Write-Output "skip $path (exists; -Force to overwrite)"
                        }
                    }
                }
            }
        }
        $cursor = $next
    }

Write-Output ("process: {0} (pid {1}, {2}-bit target)" -f $proc.ProcessName, $proc.Id, $(if ($is64) { '64' } else { '32' }))
Write-Output "committed readable regions >= 64 KiB: $($allRegions.Count); largest:"
$allRegions | Sort-Object Size -Descending | Select-Object -First 5 | ForEach-Object {
    Write-Output ("  0x{0:x}: {1} MiB" -f $_.Base, [Math]::Round($_.Size / 1MB, 1))
}

if ($summary.Count -eq 0) {
    if (-not $All -and -not $AllSmall) {
        Write-Output "marker '$Marker' not found in any region >= 1 MiB."
        Write-Output "Is the game running (main menu or colony view), not DOS?"
        Write-Output "Re-run with -All to dump every large region for inspection, or check the process name (-Name)."
        exit 3
    }
    Write-Output "marker not found; dumping every region >= $($AllMinSize / 1MB) MiB (re-read, failures skipped)"
    foreach ($t in $allRegions | Where-Object { $_.Size -ge $AllMinSize }) {
        $name = "ram_{0:x}.bin" -f $t.Base
        $path = Join-Path $OutDir $name
        if ((Test-Path $path) -and -not $Force) {
            Write-Output "skip $path (exists; -Force to overwrite)"
            continue
        }
        $data = Read-Region $h $t.Base $t.Size
        if (-not $data) {
            Write-Output ("read failed for 0x{0:x}; skipped" -f $t.Base)
            continue
        }
        [System.IO.File]::WriteAllBytes($path, $data)
        $summary += [PSCustomObject]@{ File = $path; Base = ('0x{0:x}' -f $t.Base); Size = $t.Size }
        Write-Output ("dumped {0} ({1} bytes, {2} MiB)" -f $name, $t.Size, [Math]::Round($t.Size / 1MB, 1))
    }
}

# Small-region mode: capture conventional/UMB memory (the game's data segment
# lives there and holds the DS-relative stat tables; see
# docs/mechanics/weapon-and-turret-numbers.md).
if ($AllSmall) {
    $Min = 0x10000
    $picked = @($allRegions | Where-Object { $_.Size -ge $Min -and $_.Size -lt $AllMinSize })
    Write-Output ""
    Write-Output "-AllSmall: dumping every committed region >= 64 KiB (conventional/UMB captured): $($picked.Count) regions"
    foreach ($t in $picked) {
        $name = "ram_{0:x}.bin" -f $t.Base
        $path = Join-Path $OutDir $name
        if ((Test-Path $path) -and -not $Force) {
            Write-Output "skip $path (exists; -Force to overwrite)"
            continue
        }
        $data = Read-Region $h $t.Base $t.Size
        if (-not $data) {
            Write-Output ("read failed for 0x{0:x}; skipped" -f $t.Base)
            continue
        }
        [System.IO.File]::WriteAllBytes($path, $data)
        $summary += [PSCustomObject]@{ File = $path; Base = ('0x{0:x}' -f $t.Base); Size = $t.Size }
        Write-Output ("dumped {0} ({1} bytes, {2} KiB)" -f $name, $t.Size, [Math]::Round($t.Size / 1KB, 1))
    }
}
[MemDump]::CloseHandle($h) | Out-Null

if ($summary.Count -eq 0) { Write-Output "nothing dumped."; exit 3 }
$info = [PSCustomObject]@{
    Process = $proc.ProcessName
    Pid = $proc.Id
    Target = $(if ($is64) { '64-bit' } else { '32-bit' })
    Marker = $Marker
    AllRegions = @($allRegions | ForEach-Object {
        [PSCustomObject]@{ Base = ('0x{0:x}' -f $_.Base); Size = $_.Size }
    })
    Dumps = $summary
}
$info | ConvertTo-Json -Depth 4 | Set-Content -Path (Join-Path $OutDir "dump_info.json")
Write-Output ""
Write-Output "Dumps written to build\dumps\. The sidecar records every region and the estimated image base."
Write-Output "Next: decode the runtime tables from the dump (weapon delay, costs, HP, power)."
exit 0
}
finally {
    [Runtime.InteropServices.Marshal]::FreeHGlobal($mbi)
    if ($h -ne [IntPtr]::Zero) { [MemDump]::CloseHandle($h) | Out-Null }
}
