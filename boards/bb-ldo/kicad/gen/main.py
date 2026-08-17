"""Generator for the bb-ldo root schematic - ONE flat sheet (`main`).

The schematic SOURCE is this Python file; `../bb-ldo.kicad_sch`, the
`.kicad_pro` and `../decoupling.json` are BUILD OUTPUT. Rebuild:

    .venv/Scripts/python boards/bb-ldo/kicad/gen/lib_fixups.py   # once
    .venv/Scripts/python boards/bb-ldo/kicad/gen/main.py

(`lib_fixups.py` idempotently repairs two pulled symbols; re-run it after
any `lib_pull` refresh. It changes no connection point and no net.)

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

HOW THIS SHEET IS DRAWN
-----------------------
The board's whole lesson is that 5 V goes in one side and 3.3 V comes out
the other, so the SERIES PATH IS DRAWN AS WIRES, left to right in the order
current actually flows:

    J1.1 --> C1.1 --> U1.3 (VIN)      |      U1.4 (TAB) --> C2.1 --> J2.1

There is not one local label on this sheet. GND is a global POWER SYMBOL at
each pin, which is what architecture/sheets.md and constraints.json specify
(and what a return net wants - nobody draws a ground rail as a wire); the
two rails additionally carry a power symbol on their drawn run so the
exported net names are the bare `+5V` / `+3V3` / `GND` the constraints
declare. Wires are chained through explicit vertices: every part pin and
every power-symbol pin sits on a wire ENDPOINT, because KiCad connects at
endpoints only - a pin touching a wire mid-span does NOT connect.

Two geometry facts drive the U1 corner, both measured, not guessed:
KiCad's power symbols are exactly 2.54 mm tall, and U1's pins are on a
2.54 mm pitch. A power symbol on U1's pin 2 row therefore reaches exactly
into pin 1's row - so pin 1 (GND) is routed up and over to its symbol
instead of straight out, which is the only arrangement of the three
left-side pins with no wire crossing and no symbol/wire touch.

Canonical nets (architecture/sheets.md + architecture/constraints.json):
`+5V`, `+3V3`, `GND` - all three bare, no `/` root prefix, because every
one of them carries a power symbol.

THE LOAD-BEARING WIRE ON THIS BOARD - U1 PIN 4:
The SOT-223 symbol has FOUR pins and pin 4 is the TAB, which is
electrically VOUT (parts/C6186.json pinout[TAB] + exposed_pad.connect_to;
knowledge record `linear-regulator-live-tab-thermal-vias`). Pin 4 is wired
to `+3V3` EXPLICITLY, in addition to pin 2 - here it is the pin the drawn
output path leaves from, which is also the truth of the part: the tab IS
the output. That pad is the thermal interface to the ~1000 mm2 F.Cu `+3V3`
pour which is the ONLY heatsink holding this 1.0 W part under 115 C in
still air (theta_JA 65 C/W at 1000 mm2 -
`linear-regulator-tab-copper-area-theta-ja`). If pin 4 were left unwired
the pad would carry no net, the pour would never reach it, and the board
would pass ERC with no heatsink at all - a silent thermal failure no gate
before bring-up can see.

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

Both capacitors are POLARIZED solid tantalums; in both symbols pin 1 is the
`+` terminal, and both are wired pin 1 -> rail, pin 2 -> GND. A reversed
tantalum fails SHORT and can burn.
"""
from __future__ import annotations

import itertools
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
# The field is set HIDDEN: it is exported in the netlist (and copied onto
# footprints at P5) either way, and on the drawing it only collided with
# pin stubs and values.
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

# Decoupling associations (S4 / check_decoupling contract). Neither carries
# "role": "reg_input" - that role belongs to SWITCHING regulators. The notes
# ride along; check_decoupling and netlist_audit read the keys they know.
DECOUPLING = [
    {"cap": "C1", "ic": "U1", "pin": "3", "rail": "+5V", "value": V_C1,
     "note": "AMS1117 input capacitor (AMS1117 p5 / LM1117 9.2.2.1.1): 10uF "
             "tantalum at the VIN pin, short lead. Linear regulator - no "
             "switch node, so NOT role=reg_input and no HF ceramic partner "
             "(block-only scope: not datasheet-required)."},
    {"cap": "C2", "ic": "U1", "pin": "2", "rail": "+3V3", "value": V_C2,
     "note": "COMPENSATION element, NOT bypass: the AMS1117 output capacitor "
             "is part of the device frequency compensation and its ESR is "
             "the loop's stabilising zero (0.8 ohm @ 100 kHz, inside the "
             "0.3-22 ohm window). Do not substitute a ceramic or a polymer "
             "tantalum, and do not change the value."},
]

# #PWR/#FLG numbering: sheets.md assigns this sheet pwr_base = 100.
_PWR = itertools.count(100)
_FLG = itertools.count(100)


def _wire(sh: schlib.Sheet, *pts) -> None:
    """Draw a chain of wire segments through `pts`.

    schlib's public helpers only emit pin STUBS carrying a local label
    (`wire_pin`) - there is no pin-to-pin connect idiom - so this sheet,
    which is drawn with real wires and no labels at all, uses schlib's own
    segment primitive directly. Every interior point of the chain is a
    shared endpoint, which is how KiCad forms the connection.
    """
    for a, b in zip(pts, pts[1:]):
        schlib.assert_on_grid(a, "wire point")
        schlib.assert_on_grid(b, "wire point")
        sh._add_wire(tuple(a), tuple(b))


def _power(sh: schlib.Sheet, sym: str, net: str, at) -> None:
    """Place a power symbol with its PIN at `at` (no stub, no label).

    schlib's `power_symbol_at_pin` hardcodes a 2.54 mm stub and derives the
    net from a prior `wire_pin`, which would also emit a local label naming
    a net the symbol already names. Both are unwanted here, so this uses
    schlib's own single-pin placement primitive.
    """
    schlib.assert_on_grid(at, f"power symbol {net}")
    sh._place_pin1(sym, f"#PWR{next(_PWR)}", net, tuple(at))


def _flag(sh: schlib.Sheet, at) -> None:
    """Place a PWR_FLAG with its PIN at `at` (marks a rail as driven)."""
    schlib.assert_on_grid(at, "PWR_FLAG")
    sh._place_pin1("power:PWR_FLAG", f"#FLG{next(_FLG)}", "PWR_FLAG",
                   tuple(at))


def build() -> schlib.Sheet:
    sh = schlib.Sheet("bb-ldo",
                      title="bb-ldo: AMS1117-3.3 1 W linear regulator block",
                      paper="A4", date="2026-08-16", company="ai-ee",
                      pwr_base=100)

    # ---- parts ----------------------------------------------------------
    # U1: pins 1/2/3 on the LEFT (GND top, VOUT middle, VIN bottom), the tab
    # (pin 4) on the RIGHT - so the drawn output path leaves from the tab.
    sh.add_component("aiee:AMS1117-3.3", "U1", V_U1, at=(152.4, 88.9),
                     footprint=f"{FP}:SOT-223-3_L6.5-W3.4-P2.30-LS7.0-BR",
                     # pin-name insurance: a symbol change cannot slip the
                     # tab (pin 4) past us unnoticed
                     expect={"1": "GND", "2": "VOUT", "3": "VIN",
                             "4": "VOUT"})
    # Capacitors stay HORIZONTAL (rotation 0): KiCad rotates field TEXT with
    # the symbol while schem_refdes does not, so a rot-90 2-pin passive
    # overprints its own Reference/Value (LEARNINGS 2026-08-09). The drawn
    # rail drop plus the GND symbol carry the "this is a shunt" meaning.
    sh.add_component("aiee:TAJA106K016RNJ", "C1", V_C1, at=(109.22, 114.3),
                     footprint=f"{FP}:CAP-SMD_L3.2-W1.6-RD-C7171")
    sh.add_component("aiee:293D226X9016D2TE3", "C2", V_C2, at=(190.5, 114.3),
                     footprint=f"{FP}:CAP-SMD_L7.3-W4.3")
    # J1/J2 at rotation 0: both pins point DOWN, and the horizontal Value
    # text stays readable. Pin 1 = the positive terminal on both (a 2-pos
    # screw terminal has no vendor-assigned function per pin; this is the
    # design's convention, matching the capacitors' pin 1 = "+").
    sh.add_component("aiee:WJ500V-5.08-2P-14-00A", "J1", V_J,
                     at=(72.39, 88.9),
                     footprint=f"{FP}:CONN-TH_2P-P5.00_WJ500V-5.08-2P")
    sh.add_component("aiee:WJ500V-5.08-2P-14-00A", "J2", V_J,
                     at=(231.14, 80.01),
                     footprint=f"{FP}:CONN-TH_2P-P5.00_WJ500V-5.08-2P")

    # Pin positions, read back from the placed symbols (never assumed).
    j1_5v, j1_gnd = sh.pin_pos("J1", "1"), sh.pin_pos("J1", "2")
    j2_3v3, j2_gnd = sh.pin_pos("J2", "1"), sh.pin_pos("J2", "2")
    c1_pos, c1_neg = sh.pin_pos("C1", "1"), sh.pin_pos("C1", "2")
    c2_pos, c2_neg = sh.pin_pos("C2", "1"), sh.pin_pos("C2", "2")
    u1_gnd, u1_vout = sh.pin_pos("U1", "1"), sh.pin_pos("U1", "2")
    u1_vin, u1_tab = sh.pin_pos("U1", "3"), sh.pin_pos("U1", "4")

    # ---- +5V: J1.1 -> C1.1 -> U1.3, drawn left to right -----------------
    RUN5 = 109.22                    # the +5V run's y
    _wire(sh, j1_5v, (j1_5v[0], RUN5))                    # J1 down to run
    _wire(sh,                                             # the run itself
          (j1_5v[0], RUN5), (85.09, RUN5), (97.79, RUN5),
          (c1_pos[0], RUN5), (138.43, RUN5))
    _wire(sh, (c1_pos[0], RUN5), c1_pos)                  # tee down to C1 +
    _wire(sh, (138.43, RUN5), (138.43, u1_vin[1]), u1_vin)  # up into VIN
    # +5V is fed only by J1's PASSIVE pins -> PWR_FLAG, or ERC reports an
    # undriven power net. The power symbol names the net (bare "+5V").
    _wire(sh, (85.09, RUN5), (85.09, 104.14))
    _flag(sh, (85.09, 104.14))
    _wire(sh, (97.79, RUN5), (97.79, 104.14))
    _power(sh, "power:+5V", "+5V", (97.79, 104.14))

    # ---- +3V3: U1.4 (the TAB) -> C2.1 -> J2.1 ---------------------------
    RUN3 = u1_tab[1]                 # the tab's own row
    _wire(sh, u1_tab, (c2_pos[0], RUN3), (207.01, RUN3), (j2_3v3[0], RUN3))
    _wire(sh, (c2_pos[0], RUN3), c2_pos)                  # tee down to C2 +
    _wire(sh, (j2_3v3[0], RUN3), j2_3v3)                  # up into J2 pin 1
    # The tab run needs its OWN +3V3 symbol. Pin 2 and pin 4 are the same
    # node inside the package but two separate nodes on the sheet, and
    # routing pin 2 around the body would cross pin 1's or pin 3's wire -
    # so the rail's global power symbol is what joins them, which is the
    # mechanism sheets.md specifies. Omitting it silently split the rail
    # into an unnamed Net-(C2-Pad1); ERC stayed 0/0 and only
    # `netlist_audit --compare` caught it.
    _wire(sh, (207.01, RUN3), (207.01, 83.82))
    _power(sh, "power:+3V3", "+3V3", (207.01, 83.82))
    # U1 pin 2 is VOUT too (same node as the tab): short stub to a +3V3
    # symbol. This is the pin whose power_out type DRIVES the rail, so +3V3
    # takes no PWR_FLAG.
    _wire(sh, u1_vout, (133.35, u1_vout[1]))
    _power(sh, "power:+3V3", "+3V3", (133.35, u1_vout[1]))

    # ---- GND: a global power symbol at every return pin -----------------
    # U1 pin 1 goes up and over: a symbol on its own row would reach into
    # pin 2's row (symbols are 2.54 mm tall, the pin pitch), and descending
    # would cross pin 2's or pin 3's wire.
    _wire(sh, u1_gnd, (139.7, u1_gnd[1]), (139.7, 78.74),
          (119.38, 78.74), (119.38, 81.28))
    _power(sh, "power:GND", "GND", (119.38, 81.28))
    for pin, corner, drop in (
            (j1_gnd, None, (j1_gnd[0], 96.52)),           # J1 pin 2
            (j2_gnd, None, (j2_gnd[0], 87.63)),           # J2 pin 2
            (c1_neg, (102.87, c1_neg[1]), (102.87, 119.38)),
            (c2_neg, (198.12, c2_neg[1]), (198.12, 119.38))):
        pts = [pin] + ([corner] if corner else []) + [drop]
        _wire(sh, *pts)
        _power(sh, "power:GND", "GND", drop)
    # GND is fed only by passive pins and U1's power_in pin -> PWR_FLAG.
    # Its own little cluster: both wire endpoints carry a pin, so no label
    # is needed to terminate them.
    _wire(sh, (152.4, 137.16), (157.48, 137.16))
    _power(sh, "power:GND", "GND", (152.4, 137.16))
    _flag(sh, (157.48, 137.16))

    # ---- decoupling metadata (S4 contract) ------------------------------
    for ent in DECOUPLING:
        if U1_PINS[ent["pin"]] != ent["rail"]:
            raise ValueError(f"{ent['cap']}: U1 pin {ent['pin']} is wired to "
                             f"'{U1_PINS[ent['pin']]}', not '{ent['rail']}'")
        sh.decoupling.append(dict(ent))

    # ---- fields ---------------------------------------------------------
    for ref, code in LCSC.items():
        sh.sch.components.get(ref).add_property("LCSC", code, hidden=True)
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
