"""One-shot helper: insert curated diplomacy names into config/ghidra/rename-map.json.

Keeps each section sorted by numeric address and preserves the file's
4-space JSON formatting. Run: python scripts/_diplomacy_names.py
"""
import json
import sys
from pathlib import Path

MAP = Path("config/ghidra/rename-map.json")

FUNCTIONS = {
    "0x42f4": "race_funds_transfer",
    "0x44e4": "relations_opinion_natural_boost",
    "0x45a4": "pact_node_create",
    "0x4724": "treaty_opinions_restore",
    "0x48d4": "war_node_create",
    "0x4b24": "pact_bits_clear",
    "0x4c14": "pact_violation_respond",
    "0x4ea4": "pact_node_apply_paid",
    "0x50f4": "relations_opinion_decay",
    "0x51b4": "relations_opinion_boost",
    "0x5274": "pact_list_tick",
    "0x52d4": "treaty_list_tick",
    "0x56c4": "relations_daily_tick",
    "0x5854": "relations_positive_bitset_rebuild",
    "0x5914": "relations_opinion_penalize",
    "0x5f04": "relations_pair_pct",
    "0x5f54": "race_approval_diff_pct",
    "0x5fa4": "race_military_diff_pct",
    "0x5ff4": "relations_table_fill",
    "0x6104": "approval_global_shift_pct",
    "0x61f4": "relations_value_distance_penalty",
    "0x62a4": "ai_pact_accept_test",
    "0x6544": "race_find_nearest",
    "0x6664": "ai_pact_offer_pick",
    "0x6944": "offer_attitude_tier_set",
    "0x6a54": "relations_value_distance_penalty_b",
    "0x6ae4": "military_pressure_value",
    "0x6bc4": "offer_amount_calc_a",
    "0x6c34": "offer_amount_calc_b",
    "0x6cc4": "ai_war_accept_test",
    "0x6ef4": "ai_war_offer_pick",
    "0x73c4": "pact_mutual_check",
    "0x7424": "pact_pair_node_check",
    "0x7474": "treaty_node_check",
    "0x74b4": "relations_elimination_cleanup",
    "0x86c4": "tribute_contract_tick",
    "0xf064": "agenda_defensive_set",
    "0xf114": "agenda_offensive_set",
    "0x15f14": "alien_war_timer_tick",
    "0x15f84": "alien_pact_timer_tick",
    "0x44454": "alien_response_schedule",
    "0x44484": "alien_offer_schedule",
    "0x444f4": "alien_fleet_schedule",
    "0x44584": "alien_response_schedule_b",
    "0x4f9a4": "ui_pact_create_cmd",
    "0x4f9f4": "ui_opinion_set_cmd",
    "0x4fae4": "ui_tribute_pay_cmd",
    "0x4fe24": "offer_cooldown_set",
}

GLOBALS = {
    "0xcd8c": "g_player_race",
    "0xcd90": "g_ai_race_cur",
    "0xcd94": "g_ai_race_index",
}


def key(addr: str) -> int:
    return int(addr, 16)


def merge(section: dict, additions: dict) -> dict:
    section = dict(section)
    for addr, name in additions.items():
        if addr in section:
            print(f"skip existing {addr} ({section[addr]})", file=sys.stderr)
            continue
        section[addr] = name
    return {k: section[k] for k in sorted(section, key=key)}


def main() -> None:
    data = json.loads(MAP.read_text(encoding="utf-8"))
    data["functions"] = merge(data["functions"], FUNCTIONS)
    data["globals"] = merge(data["globals"], GLOBALS)
    note = data["note"]
    if "diplomacy.md" not in note:
        data["note"] = note + (
            " The diplomacy pass (docs/mechanics/diplomacy.md, reference build):"
            " pact_node_*/war_node_*/treaty_* are the Non-Aggression-Pact /"
            " Joint-Combat-Treaty node machinery, relations_daily_tick 0x56c4 is the"
            " per-tick opinion matrix (decay + incident accumulation), ai_*_offer_pick"
            " / ai_*_accept_test are the alien offer decisions, tribute_contract_tick"
            " 0x86c4 is the per-day tribute income scheduler, and the 0xd000-range"
            " per-race-pair block holds the relation matrices."
        )
    MAP.write_text(json.dumps(data, indent=4, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"ok: {len(FUNCTIONS)} functions, {len(GLOBALS)} globals")


if __name__ == "__main__":
    main()
