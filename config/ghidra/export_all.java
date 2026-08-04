// Export every function's decompiled C plus a symbol table for the current
// program. Java (GhidraScript), so it runs headless on any Ghidra without
// Jython or PyGhidra.
//
// Usage (via analyzeHeadless):
//   analyzeHeadless <proj> <name> -import <exe> \
//       -scriptPath config/ghidra -postScript export_all.java <outdir>
//
// Outputs into <outdir>/:
//   decompiled.c   concatenated per-function decompilations
//   functions.tsv  name / entry address / decompile status
//
// This is OUR script. The output it writes is derived game code and must stay
// under build/ (gitignored).
//@category Analysis
//@description Export decompiled C + function table to a directory

import java.io.File;
import java.io.FileWriter;
import java.io.PrintWriter;

import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionManager;
import ghidra.util.task.ConsoleTaskMonitor;

public class export_all extends GhidraScript {

	@Override
	public void run() throws Exception {
		String[] args = getScriptArgs();
		String outdir = (args.length > 0 && !args[0].isEmpty()) ? args[0] : ".";
		File dir = new File(outdir);
		if (!dir.isDirectory()) {
			dir.mkdirs();
		}

		DecompInterface ifc = new DecompInterface();
		ifc.openProgram(currentProgram);
		ConsoleTaskMonitor monitor = new ConsoleTaskMonitor();

		File outFile = new File(dir, "decompiled.c");
		File tsvFile = new File(dir, "functions.tsv");
		int count = 0;

		FunctionManager fm = currentProgram.getFunctionManager();
		StringBuilder tsv = new StringBuilder("name\taddress\tsize\tstatus\n");

		try (PrintWriter pw = new PrintWriter(new FileWriter(outFile))) {
			for (Function fn : fm.getFunctions(true)) {
				String name = fn.getName();
				String addr = fn.getEntryPoint().toString(false);
				String size = (fn.getBody() == null) ? "?"
						: String.valueOf(fn.getBody().getNumAddresses());
				DecompileResults res = ifc.decompileFunction(fn, 60, monitor);
				String status = "ok";
				pw.println("/* ===== " + name + " @ " + addr + " (size " + size
						+ ") ===== */");
				if (res != null && res.decompileCompleted()) {
					pw.println(res.getDecompiledFunction().getC());
				} else {
					status = "failed";
					pw.println("// decompile failed");
				}
				pw.println();
				pw.println();
				tsv.append(name).append('\t').append(addr).append('\t')
						.append(size).append('\t').append(status).append('\n');
				count++;
			}
		}

		try (PrintWriter pw = new PrintWriter(new FileWriter(tsvFile))) {
			pw.print(tsv);
		}

		println("[export_all] exported " + count + " function(s) to " + outdir);
	}
}
