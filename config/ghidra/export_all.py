# Ghidra post-script (Jython): export every function's decompiled C plus a
# symbol table for the current program.
#
# Usage (via analyzeHeadless):
#   analyzeHeadless <proj> <name> -import <exe> \
#       -scriptPath config/ghidra -postScript export_all.py <outdir>
#
# Outputs into <outdir>/:
#   decompiled.c   concatenated per-function decompilations
#   functions.tsv  name / entry address / decompile status
#
# This is OUR script. The output it writes is derived game code and must stay
# under build/ (gitignored).
#
# Requires Ghidra's Jython environment; run only through analyzeHeadless.
from __future__ import print_function

import os

from ghidra.app.decompiler import DecompInterface
from ghidra.util.task import ConsoleTaskMonitor

args = getScriptArgs()
outdir = args[0] if args and args[0] else "."
if not os.path.isdir(outdir):
    os.makedirs(outdir)

ifc = DecompInterface()
ifc.openProgram(currentProgram)
monitor = ConsoleTaskMonitor()

listing = currentProgram.getListing()
fm = currentProgram.getFunctionManager()

out_path = os.path.join(outdir, "decompiled.c")
tsv_path = os.path.join(outdir, "functions.tsv")

count = 0
rows = []
with open(out_path, "w") as out:
    for fn in fm.getFunctions(True):
        name = fn.getName()
        addr = fn.getEntryPoint().toString(False)
        body = fn.getBody()
        size = "?" if body is None else str(body.getNumAddresses())
        res = ifc.decompileFunction(fn, 60, monitor)
        status = "ok"
        out.write("/* ===== %s @ %s (size %s) ===== */\n" % (name, addr, size))
        if res is not None and res.decompileCompleted():
            out.write(res.getDecompiledFunction().getC())
        else:
            status = "failed"
            out.write("// decompile failed\n")
        out.write("\n\n")
        rows.append((name, addr, size, status))
        count += 1

with open(tsv_path, "w") as out:
    out.write("name\taddress\tsize\tstatus\n")
    for name, addr, size, status in rows:
        out.write("%s\t%s\t%s\t%s\n" % (name, addr, size, status))

print("[export_all] exported %d function(s) to %s" % (count, outdir))
