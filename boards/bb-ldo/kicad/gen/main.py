"""Generator for the bb-ldo root schematic - ONE flat sheet (`main`).

The schematic SOURCE is this Python file; `../bb-ldo.kicad_sch`, the
`.kicad_pro` and `../decoupling.json` are BUILD OUTPUT. Rebuild:

    .venv/Scripts/python boards/bb-ldo/kicad/gen/lib_pin_angles.py   # once
    .venv/Scripts/python boards/bb-ldo/kicad/gen/main.py

(`lib_pin_angles.py` is an idempotent repair of one pulled symbol; re-run it
after any `lib_pull` refresh. It changes no connection point and no net.)

Topology (architecture/blocks.md B1-B3, architecture/sheets.md):

    J1 (+5V/GND screw terminal)
      -> C1 10uF tantalum across +5V/GND at U1's VIN pin
      -> U1 AMS1117-3.3 SOT-223 fixed 3.3 V linear regulator
      -> C2 22uF solid tantalum across +3V3/GND at U1's VOUT pin
      -> J2 (+3V3/GND screw terminal)

Five parts, three nets, no signal net, no hierarchy. There is deliberately
NO R1 minimum-load bleed (the 1117 minimum-load spec belongs to the
ADJUSTABLE variant, whose EXTERNAL divider draws it; the fixed part's
divider is internal and Kelvin-connected - knowledge record
`linear-regulator-fixed-variant-min-load`, verified). Scope tier is
`block-only`: no protection, no indicator, no test point, no enable strap.

Wiring facts come from parts/C6186.json (pinout ground truth), never from
memory; `expect=` pins the load-bearing pin NAMES against the library at
build time. Symbols are the pulled project lib lib/aiee.kicad_sym
(kicad/sym-lib-table nickname `aiee`).

Canonical nets (architecture/sheets.md + architecture/constraints.json):
`+5V`, `+3V3`, `GND` - all three are global POWER SYMBOLS, so the exported
net names are bare (no `/` root prefix) and no net acquires a sheet path.
Label text is always bare; a literal `/` would be escaped to `{slash}`.

THE LOAD-BEARING WIRE ON THIS BOARD - U1 PIN 4:
The SOT-223 symbol has FOUR pins and pin 4 is the TAB, which is
electrically VOUT (parts/C6186.json pinout[TAB] + exposed_pad.connect_to;
knowledge record `linear-regulator-live-tab-thermal-vias`). Pin 4 is wired
to `+3V3` EXPLICITLY, in addition to pin 2. That pad is the thermal
interface to the ~1000 mm2 F.Cu `+3V3` pour which is the ONLY heatsink
holding this 1.0 W part under 115 C in still air (theta_JA 65 C/W at
1000 mm2 - `linear-regulator-tab-copper-area-theta-ja`). If pin 4 were left
unwired the pad would carry no net, the pour would never reach it, and the
board would pass ERC with no heatsink at all - a silent thermal failure no
gate before bring-up can see.

Two idiom traps this block deliberately avoids (architecture/blocks.md s.3):
 1. This is a LINEAR regulator, not a switching one. C1 is NOT tagged
    `"role": "reg_input"` (that role is for a switching regulator's VIN and
    makes check_decoupling demand an HF ceramic within 7.5 mm) and NO 0.1 uF
    HF ceramic is fitted - that recommendation belongs to other datasheets,
    and an unrequested part is a scope violation at `block-only`.
 2. C2 is a COMPENSATION element, not bypass: its ESR is the zero that
    stabilises the loop (`linear-regulator-1117-output-cap-esr-window` /
    `linear-regulator-esr-zero-compensation`). Its value and part must not
    be substituted; the association carries that note into decoupling.json.

Both capacitors are POLARIZED solid tantalums; in BOTH pulled symbols pin 1
is the `+` terminal (the drawn "+" mark sits on the pin-1 side).
`place_ic_with_decoupling` wires cap pin 1 -> rail and pin 2 -> gnd, so
polarity lands anode -> rail, cathode -> GND. A reversed tantalum fails
SHORT and can burn.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
BOARD = HERE.parents[2]          # boards/bb-ldo
REPO = HERE.parents[4]           # repo root
sys.path.insert(0, str(REPO / ".claude" / "skills" / "ai-ee" / "scripts"))

import schlib  # noqa: E402
import kicad_sch_api as ksa  # noqa: E402

# kicad-sch-api resolves lib_ids through its GLOBAL cache, which never reads
# the project sym-lib-table - register the pulled lib explicitly.
ksa.get_symbol_cache().add_library_path(BOARD / "lib" / "aiee.kicad_sym")

FP = "aiee"  # footprint lib nickname (kicad/fp-lib-table)

# --- values: each string is BOTH the component Value and the decoupling
# metadata value, so netlist_audit's value-drift check is satisfied by
# construction. Kept ASCII (SPEC 6 output contract).
V_U1 = "AMS1117-3.3"
V_C1 = "10uF 16V solid tantalum"                    # parts/parts.json C7171
V_C2 = "22uF 16V solid tantalum ESR 0.8ohm"         # parts/parts.json C215872
V_J = "2P 5.08mm THT screw terminal"                # parts/parts.json C8465

# refdes -> LCSC code (parts/parts.json). bom_cpl.py keys on a field named
# exactly "LCSC"; the pulled symbols' own "LCSC Part" field does not match.
LCSC = {"U1": "C6186", "C1": "C7171", "C2": "C215872",
        "J1": "C8465", "J2": "C8465"}

# U1 pad -> net. Ground truth parts/C6186.json:
#   1 GND  - "Ground/Adjust"; AMS1117-3.3 is the FIXED part, so pin 1 = GND
#   2 VOUT - regulated 3.3 V output (the compensation node C2 sits on)
#   3 VIN  - unregulated input
#   4 TAB  - the SOT-223 tab, electrically the SAME NODE as pin 2 (VOUT).
#            Wired to +3V3 on purpose: see the module docstring.
# Every pin is wired; no input is left floating and there is no no-connect.
U1_PINS = {"1": "GND", "2": "+3V3", "3": "+5V", "4": "+3V3"}

# Notes carried into decoupling.json. check_decoupling / netlist_audit read
# the keys they know and ignore the rest; the note keeps the sidecar from
# reading as "two generic bypass caps" to a later agent or reviewer.
NOTES = {
    "C1": "AMS1117 input capacitor (AMS1117 p5 / LM1117 9.2.2.1.1): 10uF "
          "tantalum at the VIN pin, short lead. Linear regulator - no switch "
          "node, so NOT role=reg_input and no HF ceramic partner "
          "(block-only scope: not datasheet-required).",
    "C2": "COMPENSATION element, NOT bypass: the AMS1117 output capacitor is "
          "part of the device frequency compensation and its ESR is the "
          "loop's stabilising zero (0.8 ohm @ 100 kHz, inside the 0.3-22 ohm "
          "window). Do not substitute a ceramic or a polymer tantalum, and "
          "do not change the value.",
}


def build() -> schlib.Sheet:
    sh = schlib.Sheet("bb-ldo",
                      title="bb-ldo: AMS1117-3.3 1 W linear regulator block",
                      paper="A4", date="2026-08-16", company="ai-ee",
                      pwr_base=100)          # sheets.md: #PWR100-#PWR199

    # ---- B2: U1 + C1 (Cin at VIN pin 3) + C2 (Cout at VOUT pin 2) -------
    sh.place_ic_with_decoupling(
        "U1", "aiee:AMS1117-3.3", V_U1,
        at=(152.4, 88.9), pins=U1_PINS,
        footprint=f"{FP}:SOT-223-3_L6.5-W3.4-P2.30-LS7.0-BR",
        # pin-name insurance: a symbol change cannot slip the tab past us
        expect={"1": "GND", "2": "VOUT", "3": "VIN", "4": "VOUT"},
        decoupling=[
            {"cap": "C1", "pin": "3", "rail": "+5V", "value": V_C1,
             "lib_id": "aiee:TAJA106K016RNJ",
             "footprint": f"{FP}:CAP-SMD_L3.2-W1.6-RD-C7171"},
            {"cap": "C2", "pin": "2", "rail": "+3V3", "value": V_C2,
             "lib_id": "aiee:293D226X9016D2TE3",
             "footprint": f"{FP}:CAP-SMD_L7.3-W4.3"},
        ],
        caps_at=(88.9, 119.38), caps_dx=88.9)

    # ---- B1: J1 DC input (pin 1 = +5V, pin 2 = GND) ---------------------
    # A 2-position screw terminal has no vendor-assigned function per pin;
    # "pin 1 = the positive terminal" on BOTH connectors is this design's
    # convention, matching the capacitors' pin 1 = "+".
    sh.add_component("aiee:WJ500V-5.08-2P-14-00A", "J1", V_J,
                     at=(43.18, 88.9), rotation=90,
                     footprint=f"{FP}:CONN-TH_2P-P5.00_WJ500V-5.08-2P")
    sh.wire_pins("J1", {"1": "+5V", "2": "GND"})

    # ---- B3: J2 3V3 output (pin 1 = +3V3, pin 2 = GND) ------------------
    sh.add_component("aiee:WJ500V-5.08-2P-14-00A", "J2", V_J,
                     at=(241.3, 88.9), rotation=90,
                     footprint=f"{FP}:CONN-TH_2P-P5.00_WJ500V-5.08-2P")
    sh.wire_pins("J2", {"1": "+3V3", "2": "GND"})

    # ---- rails ----------------------------------------------------------
    # Power SYMBOLS force the bare global net names (+5V / +3V3 / GND) that
    # constraints.json declares; the symbol WINS over a coincident local
    # label, and its Value IS the exported net name.
    # +5V and GND are fed only by J1's PASSIVE connector pins -> both need a
    # PWR_FLAG or ERC reports an undriven power net (sheets.md ERC hint).
    # +3V3 is driven by U1 pin 2 (power_out): symbol, NO flag. All three sit
    # in their own column rather than on a pin stub, so no symbol body lands
    # on a neighbouring pin's label.
    sh.power_flag("+5V", at=(50.8, 152.4), sym="power:+5V", flag=True)
    sh.power_flag("+3V3", at=(50.8, 165.1), sym="power:+3V3", flag=False)
    sh.power_flag("GND", at=(50.8, 177.8), sym="power:GND", flag=True)

    # ---- decoupling metadata annotation ---------------------------------
    for assoc in sh.decoupling:
        assoc["note"] = NOTES[assoc["cap"]]

    # ---- LCSC part-number fields (downstream BOM keys on them) ----------
    for ref, code in LCSC.items():
        sh.sch.components.get(ref).set_property("LCSC", code)
    return sh


def main(argv=None) -> int:
    out_dir = Path(argv[0]) if argv else HERE.parents[1]   # .../kicad
    try:
        sh = build()
        sch = sh.save(out_dir, project=True)
        meta = sh.emit_decoupling(out_dir / "decoupling.json")
    except Exception as exc:  # noqa: BLE001  (SPEC 6: any error -> exit 2)
        print(json.dumps({"script": "gen.bb-ldo", "status": "error",
                          "error": f"{type(exc).__name__}: {exc}"}))
        return 2
    print(json.dumps({
        "script": "gen.bb-ldo", "status": "pass",
        "files": [str(sch), str(out_dir / "bb-ldo.kicad_pro"), str(meta)],
        "decoupling_associations": len(sh.decoupling),
        "place_report": sh.place_report,
    }, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
