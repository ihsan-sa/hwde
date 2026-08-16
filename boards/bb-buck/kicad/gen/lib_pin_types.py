"""Fix electrical pin types in lib/aiee.kicad_sym (idempotent, in place).

The pulled library already carries a sane typing pass for U1 - supplies and
grounds `power_in`, SW and VCC `power_out`, signals `passive` - with ONE
ERC-blocking exception: BOOT (pin 7) is typed `power_in`.

`/BST` has no schematic-visible driver: the bootstrap rail is refreshed by
a diode INSIDE the package (VCC -> BOOT) and its only other member is C6,
a passive.  kicad-cli 10.0.3 ERC --severity-all therefore raises
`power_pin_not_driven` on a net that is electrically correct, and the P4
gate wants errors + warnings == 0.  Retyping the pin is the source fix
(LEARNINGS 2026-07-27: fix the library, not the .kicad_pro severities); the
alternative - a PWR_FLAG on /BST - would also pull `/BST` into
netlist_audit's `power_undeclared` warning, and architecture/sheets.md s4
deliberately leaves that net undeclared.

`passive` is the same typing sbuck-5v3a's AP64350 BST pin carries, and it
is what the retype rule prescribes: supplies/grounds power_in, regulator
output power_out, everything else passive.  A bootstrap node is not the
part's supply.

Re-run after any lib_pull refresh of the library:

    .venv/Scripts/python boards/bb-buck/kicad/gen/lib_pin_types.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

LIB = Path(__file__).resolve().parents[2] / "lib" / "aiee.kicad_sym"

# (symbol, pin number) -> electrical type.  Only DEVIATIONS from what the
# pulled library already has are listed; every other pin is left untouched,
# so this file cannot silently re-type a symbol a later lib_pull adds.
# Source: parts/C841384.json Table 6-1 pin functions.
RULES: dict[str, dict[str, str]] = {
    "LMR33630ADDAR": {"7": "passive"},      # BOOT - see the module docstring
}

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
        want = RULES.get(symbol, {}).get(number)
        have = m.group(1)
        if want is None or want == have:
            continue
        out.append(text[pos:m.start()])
        out.append(f"(pin {want} line")
        pos = m.end()
        changes.append({"symbol": symbol, "pin": number,
                        "from": have, "to": want})
    out.append(text[pos:])
    return "".join(out), changes


def main(verbose: bool = True) -> int:
    try:
        text = LIB.read_text(encoding="utf-8")
        new, changes = retype(text)
        if changes:
            LIB.write_text(new, encoding="utf-8")
    except Exception as exc:                # noqa: BLE001 (SPEC 6: error -> 2)
        if verbose:
            print(json.dumps({"script": "gen.lib_pin_types",
                              "status": "error",
                              "error": f"{type(exc).__name__}: {exc}"}))
        return 2
    if verbose:
        print(json.dumps({"script": "gen.lib_pin_types", "status": "pass",
                          "lib": str(LIB), "changed": len(changes),
                          "changes": changes}, indent=1, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
