"""lib_fixups.py - idempotent repair of pulled symbols in lib/aiee.kicad_sym.

Same pattern (and same reason) as `boards/stm32-blinky/kicad/gen/
lib_pin_types.py`: a defect in a PULLED easyeda2kicad symbol is fixed at the
SOURCE library, not worked around downstream. Re-run after any `lib_pull`
refresh, then re-run `main.py`.

Nothing here is electrical. Pin NUMBERS, NAMES, TYPES and CONNECTION POINTS
(`(at ...)`) are identical before and after every fixup, so footprint pad
mapping and the exported netlist are untouched - verified by
`netlist_audit --compare` against the pre-repair netlist (0 differences).

FIXUP 1 - pin ANGLES on aiee:293D226X9016D2TE3 (C2, 22 uF compensation Ta)
--------------------------------------------------------------------------
Its two pin angles came out of the pull backwards relative to its own
graphics. A KiCad pin is drawn FROM its connection point in the direction of
its angle, so a lead should point INWARD, toward the plates:

    pin 1 at x=-5.08, plates at x=-0.76 .. +1.02  -> angle 0   (+x, inward)
    pin 2 at x=+5.08                              -> angle 180 (-x, inward)

The pulled file had 180 and 0. Both leads were therefore drawn AWAY from the
plates, connecting to nothing, and `schlib.stub_dir` - which derives the
outward stub direction from the pin angle - emitted both auto-stubs INWARD,
landing the two net labels 5.08 mm apart ON the body ("+3V3GND", rail label
over the plate). `length` is trimmed to 3.81 mm so neither lead is drawn
through the plates.

FIXUP 2 - polarity GRAPHIC on aiee:TAJA106K016RNJ (C1, 10 uF input Ta)
----------------------------------------------------------------------
A solid tantalum drawn as a plain two-plate NON-polarized capacitor: two
straight plates, and the only anode cue a ~1 mm "+" placed above the axis
where KiCad renders pin 1's NUMBER, so the two collide and the cue is lost.
A reader cannot see the polarity, and a reversed tantalum fails SHORT and
can burn. Redrawn to the same convention the sibling 293D symbol already
uses: straight plate on the ANODE side (pin 1, +3.81), curved plate on the
cathode side, and the "+" moved BELOW the axis - clear of the pin number,
which KiCad renders above the lead.

Both fixups are whole-block rewrites of a symbol's graphics/pin headers, so
re-running is a no-op once applied (`--check` reports it without writing).

CLI: lib_fixups.py [--lib PATH] [--check]   exit 0/1/2 per SPEC 6.
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

SCRIPT = "lib_fixups"

# --- fixup 1: symbol unit -> {pin number: (angle_deg, length_mm)} ---------
PIN_ANGLES = {
    "293D226X9016D2TE3_0_1": {"1": (0.0, 3.81), "2": (180.0, 3.81)},
}

# --- fixup 2: symbol unit -> canonical graphics block --------------------
# Everything between the unit header and its first `(pin ` is replaced, so
# the rewrite is deterministic and idempotent. Pins are never touched.
_STROKE = "        (stroke (width 0) (type default))\n        (fill (type none))\n      )\n"


def _poly(*pts: tuple[float, float]) -> str:
    body = " ".join(f"(xy {x:g} {y:g})" for x, y in pts)
    return f"      (polyline\n        (pts\n          {body}\n        )\n{_STROKE}"


def _arc(start, mid, end) -> str:
    return (f"      (arc\n"
            f"        (start {start[0]:g} {start[1]:g})\n"
            f"        (mid {mid[0]:g} {mid[1]:g})\n"
            f"        (end {end[0]:g} {end[1]:g})\n{_STROKE}")


# TAJA106K016RNJ: pin 1 (anode, "+") sits at x=+3.81, pin 2 at x=-3.81.
# Anode = straight plate at +0.51 with its lead; cathode = curved plate on
# the left (the sibling 293D symbol's arc geometry, mirrored and scaled to
# this symbol's +/-2.03 plate height); "+" below the axis on the anode side.
GRAPHICS = {
    "TAJA106K016RNJ_0_1":
        _poly((0.51, -2.03), (0.51, 2.03))            # anode plate
        + _poly((1.27, 0), (0.51, 0))                 # anode lead to plate
        + _arc((-1.02, 2.03), (-0.42, 1.06), (-0.25, 0))    # cathode, upper
        + _arc((-0.25, 0), (-0.43, -1.06), (-1.02, -2.03))  # cathode, lower
        + _poly((1.02, -1.78), (2.03, -1.78))         # "+" horizontal
        + _poly((1.52, -1.27), (1.52, -2.29))         # "+" vertical
        + "      ",
}

# --- fixup 3: symbols whose PIN NAMES are meaningless numerals -----------
# easyeda names a 2-pin passive's pins "1" and "2" - the same strings as the
# pin NUMBERS. KiCad renders names inside the body, so on a small symbol the
# two names print on top of each other in the middle of the part (and on top
# of the numbers). Hide the names; the numbers stay, which is what tells a
# reader which end of a POLARIZED part is pin 1. Display-only: the netlist's
# libparts still carry the names (LEARNINGS 2026-08-09, the aiee:5602 case).
# The old bare-token form matches this file's own (version 20211014) style.
PIN_NAMES_HIDE = ("TAJA106K016RNJ", "293D226X9016D2TE3",
                  "WJ500V-5.08-2P-14-00A")
_PIN_NAMES_TOKEN = "    (pin_names hide)\n"

_PIN_RE = re.compile(
    r'\(pin\s+(?P<etype>\w+)\s+(?P<shape>\w+)\s*\n'
    r'(?P<at_ws>\s*)\(at\s+(?P<x>-?[\d.]+)\s+(?P<y>-?[\d.]+)\s+'
    r'(?P<ang>-?[\d.]+)\)\s*\n'
    r'(?P<len_ws>\s*)\(length\s+(?P<len>-?[\d.]+)\)\s*\n'
    r'(?P<rest>.*?\(number\s+"(?P<num>[^"]+)")',
    re.DOTALL)


def _unit_span(text: str, unit: str) -> tuple[int, int]:
    """Byte span of one `(symbol "<unit>" ...)` block, to the next symbol
    block or EOF (easyeda output never nests further)."""
    start = text.find(f'(symbol "{unit}"')
    if start < 0:
        raise ValueError(f"symbol unit '{unit}' not found")
    nxt = text.find('(symbol "', start + 1)
    return start, (nxt if nxt > 0 else len(text))


def _fix_pin_angles(text: str, changes: list[dict]) -> str:
    for unit, wants in PIN_ANGLES.items():
        s, e = _unit_span(text, unit)
        block = text[s:e]
        seen: set[str] = set()

        def fix(m: re.Match) -> str:
            num = m.group("num")
            seen.add(num)
            if num not in wants:
                return m.group(0)
            ang, ln = wants[num]
            was = (float(m.group("ang")), float(m.group("len")))
            if was == (ang, ln):
                return m.group(0)
            changes.append({"fixup": "pin_angles", "unit": unit, "pin": num,
                            "was": {"angle": was[0], "length": was[1]},
                            "now": {"angle": ang, "length": ln}})
            return (f'(pin {m.group("etype")} {m.group("shape")}\n'
                    f'{m.group("at_ws")}(at {m.group("x")} {m.group("y")} '
                    f'{ang:g})\n'
                    f'{m.group("len_ws")}(length {ln:g})\n'
                    f'{m.group("rest")}')

        block = _PIN_RE.sub(fix, block)
        missing = sorted(set(wants) - seen)
        if missing:
            raise ValueError(f"{unit}: pins {missing} not found in the symbol")
        text = text[:s] + block + text[e:]
    return text


def _fix_graphics(text: str, changes: list[dict]) -> str:
    for unit, want in GRAPHICS.items():
        s, e = _unit_span(text, unit)
        block = text[s:e]
        pin_i = block.find("(pin ")
        if pin_i < 0:
            raise ValueError(f"{unit}: no pins found - refusing to rewrite")
        head = f'(symbol "{unit}"\n'
        if not block.startswith(head):
            raise ValueError(f"{unit}: unexpected unit header")
        have = block[len(head):pin_i]
        if have == want:
            continue
        changes.append({"fixup": "graphics", "unit": unit,
                        "was_chars": len(have), "now_chars": len(want)})
        block = head + want + block[pin_i:]
        text = text[:s] + block + text[e:]
    return text


def _fix_pin_names(text: str, changes: list[dict]) -> str:
    for sym in PIN_NAMES_HIDE:
        s, e = _unit_span(text, sym)
        block = text[s:e]
        if "(pin_names" in block:
            continue
        anchor = "    (on_board yes)\n"
        i = block.find(anchor)
        if i < 0:
            raise ValueError(f"{sym}: no '(on_board yes)' anchor to insert at")
        j = i + len(anchor)
        changes.append({"fixup": "pin_names_hide", "unit": sym})
        text = text[:s] + block[:j] + _PIN_NAMES_TOKEN + block[j:] + text[e:]
    return text


def repair(lib: Path, write: bool = True) -> dict:
    text = original = lib.read_text(encoding="utf-8")
    changes: list[dict] = []
    text = _fix_pin_angles(text, changes)
    text = _fix_graphics(text, changes)
    text = _fix_pin_names(text, changes)
    if changes and write and text != original:
        lib.write_text(text, encoding="utf-8")
    return {"lib": str(lib), "changes": changes}


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
    print(json.dumps({"script": SCRIPT, "status": "pass", "lib": res["lib"],
                      "repaired": len(res["changes"]),
                      "changes": res["changes"],
                      "mode": "check" if args.check else "write"}, indent=1))
    return 1 if (args.check and res["changes"]) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
