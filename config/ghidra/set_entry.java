// Set the entry point and split the flat DOS/4G image into code/data.
//
// The flat image (build/flat/FRAGILE.EXE.flat) is imported as a raw 32-bit
// x86 binary at base 0. Addresses are image-relative, so a pointer dword in
// the file (e.g. 0x16d6c) resolves to the correct location without any
// relocation being applied.
//
// Usage (runs as a PRE script, before auto-analysis, so Ghidra disassembles
// from the entry):
//   analyzeHeadless <proj> <name> -import <flat> \
//       -processor x86:LE:32:default -loader BinaryLoader -loader-baseAddr 0x0 \
//       -scriptPath config/ghidra -preScript set_entry.java <entry> [<code_end>]
//
// <entry>    image-relative offset of the entry point (hex, e.g. 0x14)
// <code_end> image-relative end of the code region (hex); a DATA_START label
//            is created there for orientation.
//
// This is OUR script; the decompiled output it produces is derived game code
// and stays under build/ (gitignored).
//@category Analysis
//@description Set DOS/4G flat image entry point + code/data split

import ghidra.program.model.address.Address;
import ghidra.app.script.GhidraScript;

public class set_entry extends GhidraScript {

	private static long parseHex(String s) {
		s = s.trim().toLowerCase();
		if (s.startsWith("0x")) {
			s = s.substring(2);
		}
		return Long.parseLong(s, 16);
	}

	@Override
	public void run() throws Exception {
		String[] args = getScriptArgs();
		long entry = (args.length > 0 && !args[0].isEmpty()) ? parseHex(args[0]) : 0x14;
		long dataStart = (args.length > 1 && !args[1].isEmpty()) ? parseHex(args[1]) : -1;

		Address entryAddr = toAddr(entry);
		addEntryPoint(entryAddr);
		createFunction(entryAddr, "main");

		String info = "entry=" + entryAddr;
		if (dataStart >= 0) {
			createLabel(toAddr(dataStart), "DATA_START", true);
			info += " data_start=" + toAddr(dataStart);
		}
		println("[set_entry] " + info);
	}
}
