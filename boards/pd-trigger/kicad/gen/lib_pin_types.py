"""Fix electrical pin types in lib/aiee.kicad_sym (one-shot, idempotent).

easyeda2kicad emits `unspecified` (and a few arbitrary `input`) electrical
types for every pin; KiCad 10 ERC then floods pin_to_pin warnings and raises
false pin_not_driven errors on the input-typed ones (this pull: 51
`unspecified` + 34 `input`), so the P4 ERC gate (errors + warnings == 0,
--severity-all) cannot pass on an untouched pulled library. Fix at the
SOURCE, not via .kicad_pro severities.

Rule, from the datasheet extract (parts/C970725.json `pinout[].type`):

  supply / ground pins -> power_in,  EVERYTHING else -> passive.

Only ONE part on this board has supply pins: U1 CH224K, whose extract types
pin 1 (VDD) `power_in` and pin 0/11 (GND) `ground`. Both become power_in and
both nets carry a PWR_FLAG in root.py.

Deliberately NOT power_in / not typed from the extract's own labels:

  U1 pin 8 (VBUS, extract type `input`)  - a voltage-DETECT input sitting on
      /VSENSE behind R1; its only net-mate is a resistor, so an input type
      would raise a false pin_not_driven (same trap as usb-buck's FB/EN).
  U1 pins 2/3/9 (CFG1..3, `input`) - same: pulled up through R3..R5 and
      shorted to GND by SW1, both passives.
  U1 pins 4/5/6/7/10 (`bidirectional` / `open_collector`) - passive.
  D1 TVS2200 GND pins, LED cathodes, F1, the connectors - two-terminal or
      contact parts that consume nothing; power_in would be semantically
      wrong and buys nothing (their nets are already flagged or passive).

There is no power_out anywhere: this board has no regulator (the LDO was
dropped at amendment A1) - VBUS is driven by the receptacle and /VDD by a
resistor dropper into an internal shunt, so both are PWR_FLAG rails.

Re-run after any lib_pull refresh of the library (do NOT re-run lib_pull
itself - symbol pulls are not idempotent and the EasyEDA API 403s;
LEARNINGS 2026-07-28), BEFORE root.py:

    .venv/Scripts/python boards/pd-trigger/kicad/gen/lib_pin_types.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

LIB = Path(__file__).resolve().parents[2] / "lib" / "aiee.kicad_sym"

# (symbol, pin number) -> electrical type; "*" = symbol default.
RULES: dict[str, dict[str, str]] = {
    "CH224K": {
        "1": "power_in",    # VDD, internal 3.3 V shunt node (extract 8.2.3)
        "11": "power_in",   # GND = the "pin 0" baseplate, U1's ONLY ground
        "*": "passive",
    },
}
DEFAULT = "passive"

PIN_RE = re.compile(r"\(pin\s+([a-z_]+)\s+line")
SYM_RE = re.compile(r'\(symbol\s+"([^"]+)"')
NUM_RE = re.compile(r'\(number\s+"([^"]+)"')


def retype(text: str) -> tuple[str, list[dict]]:
    changes: list[dict] = []
    out: list[str] = []
    pos = 0
    for m in PIN_RE.finditer(text):
        sym_matches = SYM_RE.findall(text, 0, m.start())
        symbol = re.sub(r"_\d+_\d+$", "", sym_matches[-1]) if sym_matches else "?"
        num_m = NUM_RE.search(text, m.end())
        number = num_m.group(1) if num_m else "?"
        rules = RULES.get(symbol, {})
        want = rules.get(number, rules.get("*", DEFAULT))
        have = m.group(1)
        out.append(text[pos:m.start()])
        out.append(f"(pin {want} line")
        pos = m.end()
        if have != want:
            changes.append({"symbol": symbol, "pin": number,
                            "from": have, "to": want})
    out.append(text[pos:])
    return "".join(out), changes


def main() -> int:
    try:
        text = LIB.read_text(encoding="utf-8")
        new, changes = retype(text)
        if changes:
            LIB.write_text(new, encoding="utf-8")
    except Exception as exc:  # noqa: BLE001  (SPEC 6: any error -> exit 2)
        print(json.dumps({"script": "lib_pin_types", "status": "error",
                          "error": f"{type(exc).__name__}: {exc}"}))
        return 2
    print(json.dumps({"script": "lib_pin_types", "status": "pass",
                      "lib": str(LIB), "changed": len(changes),
                      "changes": changes}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
