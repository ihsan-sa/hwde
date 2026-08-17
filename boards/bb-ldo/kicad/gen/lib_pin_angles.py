"""lib_pin_angles.py - idempotent repair of pin ANGLES in lib/aiee.kicad_sym.

Same pattern (and same reason) as `boards/stm32-blinky/kicad/gen/
lib_pin_types.py`: a defect in a PULLED easyeda2kicad symbol is fixed at the
SOURCE library, not worked around downstream. Re-run after any `lib_pull`
refresh, then re-run `main.py`.

THE DEFECT (aiee:293D226X9016D2TE3, C2's 22 uF tantalum)
--------------------------------------------------------
Its two pin angles are reversed relative to its own graphics. A KiCad pin is
drawn FROM its `(at ...)` connection point in the direction of its angle, so
the lead should point INWARD, toward the plates:

    pin 1 at x=-5.08, plates at x=-0.76 .. +1.02  -> angle 0   (+x, inward)
    pin 2 at x=+5.08                              -> angle 180 (-x, inward)

The pulled file has 180 and 0 - exactly backwards. Two consequences:
 1. both leads are drawn AWAY from the plates and connect to nothing, while
    a 3.5 mm gap sits between each connection point and its plate;
 2. schlib derives the outward auto-stub direction from the pin angle
    (`stub_dir`), so both wire stubs and both net labels are emitted INWARD,
    landing 5.08 mm apart ON the body - the rail and ground labels render
    as a single run-together string ("+3V3GND") with the rail label over
    the plate. On a human-reviewed schematic (H2) that is not readable.

Rotating the cap to a vertical shunt is NOT the fix: KiCad rotates field
TEXT with the symbol while schem_refdes does not, so a rot-90/270 2-pin
passive overprints its own Reference/Value (LEARNINGS 2026-08-09).

Nothing electrical changes. A pin's connection point is its `(at ...)`,
which is untouched; only the drawn lead direction (and the stub direction
schlib derives from it) changes. Pin numbers, names, types and positions are
identical before and after, so footprint pad mapping and the netlist are
unaffected. `length` is trimmed to 3.81 mm on both pins so neither lead is
drawn through the plates.

CLI: lib_pin_angles.py [--lib PATH] [--check]   exit 0/1/2 per SPEC 6.
     --check reports without writing (exit 1 if a repair is still needed).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
BOARD = HERE.parents[2]                      # boards/bb-ldo
DEFAULT_LIB = BOARD / "lib" / "aiee.kicad_sym"

SCRIPT = "lib_pin_angles"

# symbol unit -> {pin number: (angle_deg, length_mm)}
WANT = {
    "293D226X9016D2TE3_0_1": {"1": (0.0, 3.81), "2": (180.0, 3.81)},
}

_PIN_RE = re.compile(
    r'\(pin\s+\w+\s+\w+\s*\n'
    r'(?P<at_ws>\s*)\(at\s+(?P<x>-?[\d.]+)\s+(?P<y>-?[\d.]+)\s+'
    r'(?P<ang>-?[\d.]+)\)\s*\n'
    r'(?P<len_ws>\s*)\(length\s+(?P<len>-?[\d.]+)\)\s*\n'
    r'(?P<rest>.*?\(number\s+"(?P<num>[^"]+)")',
    re.DOTALL)


def _unit_span(text: str, unit: str) -> tuple[int, int]:
    """Byte span of one `(symbol "<unit>" ...)` block (to the next symbol
    block or the end of file - pins never appear after it in easyeda output)."""
    start = text.find(f'(symbol "{unit}"')
    if start < 0:
        raise ValueError(f"symbol unit '{unit}' not found")
    nxt = text.find('(symbol "', start + 1)
    return start, (nxt if nxt > 0 else len(text))


def repair(lib: Path, write: bool = True) -> dict:
    text = lib.read_text(encoding="utf-8")
    changes: list[dict] = []
    for unit, wants in WANT.items():
        s, e = _unit_span(text, unit)
        block = text[s:e]
        seen = set()

        def fix(m: re.Match) -> str:
            num = m.group("num")
            seen.add(num)
            if num not in wants:
                return m.group(0)
            ang, ln = wants[num]
            was = (float(m.group("ang")), float(m.group("len")))
            if was == (ang, ln):
                return m.group(0)
            changes.append({"unit": unit, "pin": num,
                            "was": {"angle": was[0], "length": was[1]},
                            "now": {"angle": ang, "length": ln}})
            return (f'(pin {m.group(0).split()[1]} {m.group(0).split()[2]}\n'
                    f'{m.group("at_ws")}(at {m.group("x")} {m.group("y")} '
                    f'{ang:g})\n'
                    f'{m.group("len_ws")}(length {ln:g})\n'
                    f'{m.group("rest")}')

        block = _PIN_RE.sub(fix, block)
        missing = sorted(set(wants) - seen)
        if missing:
            raise ValueError(f"{unit}: pins {missing} not found in the symbol")
        text = text[:s] + block + text[e:]
    if changes and write:
        lib.write_text(text, encoding="utf-8")
    return {"lib": str(lib), "changes": changes,
            "status": "pass" if (write or not changes) else "fail"}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--lib", default=str(DEFAULT_LIB),
                    help="symbol library to repair")
    ap.add_argument("--check", action="store_true",
                    help="report only; exit 1 if a repair is still needed")
    args = ap.parse_args(argv)
    try:
        res = repair(Path(args.lib), write=not args.check)
    except Exception as exc:  # noqa: BLE001  (SPEC 6: any error -> exit 2)
        print(json.dumps({"script": SCRIPT, "status": "error",
                          "error": f"{type(exc).__name__}: {exc}"}))
        return 2
    payload = {"script": SCRIPT, "status": res["status"],
               "lib": res["lib"], "repaired": len(res["changes"]),
               "changes": res["changes"],
               "mode": "check" if args.check else "write"}
    print(json.dumps(payload, indent=1))
    return 1 if (args.check and res["changes"]) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
