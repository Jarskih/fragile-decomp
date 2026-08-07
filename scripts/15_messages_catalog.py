#!/usr/bin/env python3
"""Stage 15: catalog of every message the player can receive.

Input: the game's US-English text resources under build/iso/_TEXT/
(AMERICAN.TXT, AMERICAN.SCR), which are plain NUL-separated ASCII token
tables.

Output: build/reports/messages-catalog.md + messages-catalog.json, a full
verbatim list of
  * the message-window notification block of AMERICAN.TXT (headline/body
    tokens in file order, byte offsets included), and
  * the whole AMERICAN.SCR diplomatic dialogue bank, split at the six
    ambassador greeting strings (speaker sections), with the trailing
    player-option/interface tokens in an appendix.

Token text is quoted verbatim; control characters are escaped for the
markdown report (the JSON keeps raw text). Neither output is committed; both
live under build/ (gitignored).
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import fragile_decomp_lib as lib

TXT_MSG_START = "Federal Transporter has arrived"
TXT_MSG_END_PREFIX = "REPORT SUMMARY"

SCR_SECTIONS = [
    ("Rigellian - Ancyra LaMarr, Rigellian Ambassador for the Fragmented Sectors "
     "and Federal Minister for Culture",
     "My name is Ancyra LaMarr", ""),
    ("Braccatian - Lord Solon Valtravers, Braccatian Ambassador for the "
     "Fragmented Sectors",
     "Greetings to you. My name translates into your tongue as Lord Solon Valtravers",
     ""),
    ("Mikotaj - Ge Tra Xi, Mikotaj Ambassador for the Fragmented Sectors",
     "I am Ge Tra Xi", ""),
    ("Artemian - SabrisSan Lars, Artemian Ambassador for the Fragmented Sectors "
     "and Federal Minister for Law Enforcement",
     "Greetings. I am SabrisSan Lars",
     "The tail of this bank (from offset 36428) is the intercession dialogue: "
     "the player asks the ambassadors to intercede with each other's races."),
    ("Terran - Jane Fong, Federal Minister for Trade Relations and Terran "
     "Ambassador for the Fragmented Sectors",
     "I am Jane Fong",
     "Only the greeting stands at this offset; Jane Fong's replies appear in "
     "the intercession dialogue web of the final bank."),
    ("Achaean - Valtimar map Gryar Shirran, Achaean Ambassador for the Fragmented "
     "Sectors, member of the Achaean Trading Union",
     "I am Valtimar map Gryar Shirran",
     "The final bank holds the Achaean dialogue plus the intercession dialogue "
     "web between the player and every ambassador (attacks, agents, Mauna "
     "trading, fines, treaties)."),
]

SCR_APPENDIX_START = "[ Propose Non Aggression Pact ]"


def tokens(path: Path) -> list[tuple[int, str]]:
    data = path.read_bytes()
    out: list[tuple[int, str]] = []
    off = 0
    for raw in data.split(b"\x00"):
        out.append((off, raw.decode("ascii", errors="replace")))
        off += len(raw) + 1
    return out


def esc(s: str) -> str:
    return (s.replace("\\", "\\\\").replace("|", "\\|")
            .replace("\n", "\\n").replace("\t", "\\t")
            .replace("\v", "\\v").replace("\r", "\\r"))


def dump_table(entries: list[tuple[int, str]]) -> str:
    lines = ["| offset | text |", "| --- | --- |"]
    for off, text in entries:
        lines.append(f"| {off} | {esc(text)} |")
    return "\n".join(lines)


def find_tok(toks: list[tuple[int, str]], start: int, pred) -> int:
    for i in range(start, len(toks)):
        if pred(toks[i][1]):
            return i
    return -1


def main() -> int:
    cfg = lib.load_config()
    root = lib.extracted_dir(cfg)
    txt_path = root / "_TEXT" / "AMERICAN.TXT"
    scr_path = root / "_TEXT" / "AMERICAN.SCR"
    for p in (txt_path, scr_path):
        if not p.is_file():
            lib.note(f"missing text resource: {p} (run `make extract`)", "red")
            return 2

    txt_toks = tokens(txt_path)
    scr_toks = tokens(scr_path)

    i_start = find_tok(txt_toks, 0, lambda s: s == TXT_MSG_START)
    i_end = find_tok(txt_toks, i_start, lambda s: s.startswith(TXT_MSG_END_PREFIX))
    if i_start < 0 or i_end < 0:
        lib.note("could not locate the message block in AMERICAN.TXT", "red")
        return 2
    txt_block = [(o, t) for o, t in txt_toks[i_start:i_end] if t != ""]

    sections = []
    appendix = []
    cursor = 0
    for name, greeting, note in SCR_SECTIONS:
        j = find_tok(scr_toks, cursor, lambda s, g=greeting: s.startswith(g))
        if j < 0:
            lib.note(f"greeting not found in AMERICAN.SCR: {greeting!r}", "red")
            return 2
        sections.append({"name": name, "greeting": greeting, "note": note, "i": j})
        cursor = j + 1
    k = find_tok(scr_toks, cursor, lambda s: s.startswith(SCR_APPENDIX_START))
    if k < 0:
        lib.note("appendix marker not found in AMERICAN.SCR", "red")
        return 2
    sections.append({"name": "Player dialogue options and interface tokens",
                     "greeting": SCR_APPENDIX_START, "note": "", "i": k})

    data = {
        "source_files": ["_TEXT/AMERICAN.TXT", "_TEXT/AMERICAN.SCR"],
        "txt_message_block": {
            "first_offset": txt_block[0][0],
            "last_offset": txt_block[-1][0],
            "tokens": [{"offset": o, "text": t} for o, t in txt_block],
        },
        "scr_sections": [],
    }

    md = [
        "# Messages the player can receive (from the _TEXT resources)",
        "",
        "Status: confirmed extract; speaker attribution within each dialogue",
        "bank is not yet mapped (see below).",
        "",
        "The game's US-English text resources are NUL-separated ASCII token",
        "tables. AMERICAN.TXT holds the message-window notification block",
        "(`make messages` reports the whole block; the rest of the file is",
        "help text and UI labels). AMERICAN.SCR is the diplomatic dialogue",
        "bank: every line anyone can say to the player during negotiations.",
        "AMERICAN.CDB is the Colony Database encyclopedia and carries no",
        "messages; it is not part of this catalog.",
        "",
        "Offsets are byte offsets into the extracted file. `%s`/`%d` are",
        "format placeholders; `%tNNN` references another token of the table.",
        "Tokens may appear more than once; repetitions are kept as the file",
        "contains them.",
        "",
        "Speaker attribution: a section starts where a new ambassador's",
        "greeting string stands in the file. The bank that follows is that",
        "ambassador's dialogue tree, but it also holds the player's reply",
        "options, and the later banks additionally hold intercession",
        "conversations between the player and several ambassadors. Which line",
        "belongs to whom is therefore not yet resolved line-by-line; the",
        "section notes flag the mixed regions.",
        "",
        f"## Part 1 - AMERICAN.TXT message-window notifications",
        f"({txt_block[0][0]}..{txt_block[-1][0]}, {len(txt_block)} tokens)",
        "",
        "Headline/body pairs appear consecutively (title token, then the",
        "detail token(s), often with format placeholders).",
        "",
        dump_table(txt_block),
        "",
        "## Part 2 - AMERICAN.SCR diplomatic dialogue",
        "",
    ]

    for idx, sec in enumerate(sections, start=1):
        start_off = scr_toks[sec["i"]][0]
        if idx < len(sections):
            end_off = scr_toks[sections[idx]["i"]][0]
        else:
            end_off = scr_toks[-1][0]
        block = [t for t in scr_toks if start_off <= t[0] < end_off and t[1] != ""]
        data["scr_sections"].append({
            "name": sec["name"], "greeting": sec["greeting"],
            "first_offset": start_off, "last_offset": block[-1][0],
            "tokens": [{"offset": o, "text": t} for o, t in block],
        })
        md += [
            f"### 2.{idx} {sec['name']}",
            f"offsets {start_off}..{block[-1][0]}; {len(block)} tokens.",
            "",
        ]
        if sec["note"]:
            md += [f"Note: {sec['note']}", ""]
        md += [dump_table(block), ""]

    lib.write_md(lib.reports_dir(cfg) / "messages-catalog.md", "\n".join(md))
    jpath = lib.reports_dir(cfg) / "messages-catalog.json"
    lib.write_json(jpath, data)
    lib.note(f"messages catalog: {len(txt_block)} TXT notifications, "
             f"{len(scr_toks)} SCR dialogue tokens -> messages-catalog.md/.json",
             "green")
    return 0


if __name__ == "__main__":
    sys.exit(main())
