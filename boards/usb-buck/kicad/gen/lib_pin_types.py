"""Fix electrical pin types in lib/aiee.kicad_sym (one-shot, idempotent).

easyeda2kicad emits `unspecified` (and a few arbitrary `input`) electrical
types for every pin; KiCad 10 ERC then floods pin_to_pin warnings and raises
false pin_not_driven errors, so the P4 ERC gate (errors+warnings == 0,
--severity-all) cannot pass. Re-type pins from the datasheet-extract JSONs:

  supplies/grounds -> power_in,  regulator power output -> power_out,
  EVERYTHING else  -> passive.

"Everything else" deliberately includes the buck's FB/EN/BST: the datasheet
extract types FB `analog` and EN `input`, but an input-typed pin sitting on
a net whose only other members are passives raises a false pin_not_driven.

Re-run after any lib_pull refresh of the library (do NOT re-run lib_pull
itself - symbol pulls are not idempotent and the EasyEDA API 403s;
LEARNINGS 2026-07-28):

    .venv/Scripts/python boards/usb-buck/kicad/gen/lib_pin_types.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

LIB = Path(__file__).resolve().parents[2] / "lib" / "aiee.kicad_sym"

# (symbol, pin number) -> electrical type; "*" = symbol default.
# Sources: parts/C8734.json  (VBAT/VDDA/VDD_x power_in, VSSA/VSS_x ground ->
#                             KiCad power_in; every I/O passive)
#          parts/C5248536.json (VIN power_in, GND ground -> power_in,
#                             SW power_out; FB/EN/BST passive - see above)
#          parts/C2687116.json (GND ground -> power_in; VBUS is a clamp
#                             REFERENCE, not a die supply -> passive, as the
#                             extract itself types it; I/O pads passive)
# All other symbols (connectors, crystal, inductor, R/C/LED/switch) are
# passive throughout, which is the DEFAULT.
RULES: dict[str, dict[str, str]] = {
    "STM32F103C8T6": {
        "1": "power_in", "9": "power_in", "24": "power_in",
        "36": "power_in", "48": "power_in",       # VBAT, VDDA, VDD_1..3
        "8": "power_in", "23": "power_in", "35": "power_in",
        "47": "power_in",                         # VSSA, VSS_1..3
        "*": "passive",
    },
    "AP63203QWU-7": {
        "3": "power_in", "4": "power_in",         # VIN, GND
        "5": "power_out",                         # SW (switching output)
        "*": "passive",                           # FB, EN, BST
    },
    "USBLC6-2SC6_C2687116": {
        "2": "power_in",                          # GND (clamp return)
        "*": "passive",                           # I/O1 x2, I/O2 x2, VBUS
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
