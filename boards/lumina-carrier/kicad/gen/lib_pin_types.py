"""Fix electrical pin types in lib/aiee.kicad_sym (idempotent).

easyeda2kicad emits `unspecified` on nearly every pin (plus a few arbitrary
`input`, e.g. chip resistors). KiCad 10 ERC --severity-all then floods
`pin_to_pin` warnings ("Unspecified and Unspecified are connected") and raises
FALSE `pin_not_driven` errors on the input-typed pins, so the P4 ERC gate
(errors + warnings == 0) cannot pass on an untouched pulled library.
See LEARNINGS 2026-07-27 [easyeda2kicad][erc].

Rules are DERIVED from the datasheet-extract JSONs rather than hand-listed:
a pin the extract types `ground` or `power_in` becomes KiCad `power_in`;
everything else becomes `passive`.

Deliberately no `power_out`: the rails are driven by PWR_FLAG symbols placed
per sheets.md s1.1, and typing a regulator output `power_out` as well would
raise power_out <-> power_out conflicts against those flags.

Re-run after any lib_pull refresh:

    .venv/Scripts/python.exe boards/lumina-carrier/kicad/gen/lib_pin_types.py
"""
from __future__ import annotations

import glob
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]          # boards/lumina-carrier
LIB = ROOT / "lib" / "aiee.kicad_sym"
PARTS = ROOT / "parts"

POWER_TYPES = {"ground", "power_in"}
DEFAULT = "passive"

# Explicit overrides that the datasheet extracts get wrong for ERC purposes.
# (symbol, pin) -> type. Applied AFTER the derived rules.
OVERRIDES: dict[tuple[str, str], str] = {
    # J1's GND1/GND2 are the magjack's shield/board-lock tabs, not a supply.
    # They sit on /poe/SHIELD, which has no power_out driver, so typing them
    # power_in raises a false power_pin_not_driven. (poe sheet agent, P4.)
    ("HY931147C", "GND1"): "passive",
    ("HY931147C", "GND2"): "passive",
}

SYM_RE = re.compile(r'\n  \(symbol "([^"]+)"')
PIN_RE = re.compile(r"\(pin\s+([a-z_]+)\s+line")
NUM_RE = re.compile(r'\(number\s+"([^"]+)"')


def norm(name: str) -> str:
    """Lib symbol name -> comparable key (strip _Cnnnn suffix, casefold)."""
    return re.sub(r"_C\d+$", "", name).casefold()


def build_rules() -> tuple[dict[str, dict[str, str]], list[str]]:
    """symbol -> {pin_number: type}, derived from the datasheet extracts."""
    parts = json.loads((PARTS / "parts.json").read_text(encoding="utf-8"))
    by_key: dict[str, str] = {}
    for p in parts["parts"]:
        if p.get("mpn") and p.get("lcsc"):
            by_key[norm(p["mpn"])] = p["lcsc"]

    rules: dict[str, dict[str, str]] = {}
    sourced: list[str] = []
    lib_text = LIB.read_text(encoding="utf-8")
    for sym in SYM_RE.findall(lib_text):
        lcsc = by_key.get(norm(sym))
        if not lcsc:
            continue
        ext = PARTS / f"{lcsc}.json"
        if not ext.exists():
            continue
        data = json.loads(ext.read_text(encoding="utf-8"))
        pins = data.get("pinout") or []
        if not pins:
            continue
        mapping = {
            str(pin["pin"]): ("power_in" if pin.get("type") in POWER_TYPES else DEFAULT)
            for pin in pins
            if pin.get("pin") is not None
        }
        n_pwr = sum(1 for v in mapping.values() if v == "power_in")
        rules[sym] = mapping
        sourced.append(f"{sym} <- {lcsc} ({len(mapping)} pins, {n_pwr} power_in)")
    return rules, sourced


def retype(text: str, rules: dict[str, dict[str, str]]) -> tuple[str, list[dict]]:
    changes: list[dict] = []
    out: list[str] = []
    pos = 0
    for m in PIN_RE.finditer(text):
        syms = SYM_RE.findall(text, 0, m.start())
        symbol = syms[-1] if syms else "?"
        num_m = NUM_RE.search(text, m.end())
        number = num_m.group(1) if num_m else "?"
        want = OVERRIDES.get((symbol, number),
                             rules.get(symbol, {}).get(number, DEFAULT))
        have = m.group(1)
        out.append(text[pos:m.start()])
        out.append(f"(pin {want} line")
        pos = m.end()
        if have != want:
            changes.append({"symbol": symbol, "pin": number, "from": have, "to": want})
    out.append(text[pos:])
    return "".join(out), changes


def main() -> int:
    try:
        rules, sourced = build_rules()
        text = LIB.read_text(encoding="utf-8")
        new, changes = retype(text, rules)
        if changes:
            LIB.write_text(new, encoding="utf-8")
        after = re.findall(PIN_RE, new)
        from collections import Counter
        print(json.dumps({
            "script": "lib_pin_types",
            "status": "pass",
            "lib": str(LIB),
            "symbols_with_datasheet_rules": len(rules),
            "sourced": sourced,
            "changed": len(changes),
            "pin_types_after": dict(Counter(after)),
        }, indent=1))
    except Exception as exc:  # noqa: BLE001
        print(json.dumps({"script": "lib_pin_types", "status": "error",
                          "error": f"{type(exc).__name__}: {exc}"}))
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
