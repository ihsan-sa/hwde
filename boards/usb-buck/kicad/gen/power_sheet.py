"""usb-buck `power` sheet: AP63203QWU-7 synchronous buck, VBUS -> +3V3.

Refdes range 100s (architecture/sheets.md s2); pwr_base 100.
NO sheet pins: all three of this sheet's nets are rails carried by power
SYMBOLS (global, bare VBUS / +3V3 / GND), and the switch node stays internal
(-> /power/SW, /power/BST). The three board PWR_FLAGs live here.

Pinout is parts/C5248536.json, not memory: 1 FB, 2 EN, 3 VIN, 4 GND, 5 SW,
6 BST.
  FB   ties DIRECTLY to the +3V3 output node - the AP63203Q is the FIXED
       3.3 V part ("tie the FB pin directly to VOUT ... no need for R1, R2 or
       C4", layout note 5). The resistive divider belongs to the ADJUSTABLE
       AP63200Q/AP63201Q and must not be fitted here.
  EN   tied to VIN (= VBUS). Float-to-enable is valid on this part (internal
       1.5 uA pull-up), and the datasheet's own wording is "connect to VIN or
       leave floating"; tying it removes a floating high-Z node at ERC and at
       the bench. decisions.md does not settle EN explicitly - sheets.md s2's
       power table does: "EN -> VBUS".
  SW   -> L1 -> +3V3 (there is no VOUT pin; the rail forms after the
       inductor, which is why +3V3 needs a PWR_FLAG).
  BST  100 nF to SW (C3) - required for the high-side gate driver.
"""
from __future__ import annotations

from pathlib import Path

import kicad_sch_api as ksa

import schlib

BOARD = Path(__file__).resolve().parents[2]
ksa.get_symbol_cache().add_library_path(BOARD / "lib" / "aiee.kicad_sym")

FP = "aiee"

V_10U = "10uF 25V X5R"
V_100N = "100nF 50V X7R"
V_22U = "22uF 25V X5R"

LCSC = {"U2": "C5248536", "L1": "C354587", "C1": "C15850", "C2": "C14663",
        "C3": "C14663", "C4": "C45783", "C5": "C45783"}


def build() -> schlib.Sheet:
    sh = schlib.Sheet("power", title="usb-buck: VBUS -> +3V3 buck", paper="A3",
                      date="2026-07-28", company="ai-ee", pwr_base=100)

    # ---- U2 buck + input capacitors C1/C2 ---------------------------------
    # C1 (10 uF) and C2 (100 nF) are the VIN pair the datasheet asks for
    # across pins 3/4; they are also the ONLY capacitance allowed on VBUS
    # (decisions.md item 7: USB inrush budget).
    sh.place_ic_with_decoupling(
        "U2", "aiee:AP63203QWU-7", "AP63203QWU-7",
        at=(152.40, 127.00),
        pins={"1": "+3V3",   # FB sense, straight to the output node
              "2": "VBUS",   # EN
              "3": "VBUS",   # VIN
              "4": "GND",
              "5": "SW",
              "6": "BST"},
        footprint=f"{FP}:TSOT-26_L2.9-W1.6-P0.95-LS2.8-BL",
        expect={"1": "FB", "2": "EN", "3": "VIN", "4": "GND", "5": "SW",
                "6": "BST"},
        decoupling=[
            {"cap": "C1", "pin": "3", "rail": "VBUS", "value": V_10U,
             "lib_id": "aiee:CL21A106KAYNNNE", "footprint": f"{FP}:C0805"},
            {"cap": "C2", "pin": "3", "rail": "VBUS", "value": V_100N,
             "lib_id": "aiee:CC0603KRX7R9BB104", "footprint": f"{FP}:C0603"},
        ],
        caps_at=(114.30, 190.50), caps_dx=30.48)

    # ---- bootstrap capacitor: BST -> SW ------------------------------------
    # Not a rail decoupler (it floats on the switch node), so it carries NO
    # decoupling metadata - sheets.md s2 lists only C1/C2/C12-C18 there.
    sh.add_component("aiee:CC0603KRX7R9BB104", "C3", V_100N,
                     at=(190.50, 101.60), footprint=f"{FP}:C0603")
    sh.wire_pins("C3", {"1": "BST", "2": "SW"})

    # ---- output filter: L1 4.7 uH + C4/C5 2 x 22 uF ------------------------
    sh.add_component("aiee:CKCS4030-4.7UH_M", "L1", "4.7uH",
                     at=(190.50, 127.00), footprint=f"{FP}:IND-SMD_L4.0-W4.0")
    sh.wire_pins("L1", {"1": "SW", "2": "+3V3"})
    sh.add_component("aiee:CL21A226MAQNNNE", "C4", V_22U,
                     at=(228.60, 152.40), footprint=f"{FP}:C0805")
    sh.wire_pins("C4", {"1": "+3V3", "2": "GND"})
    sh.add_component("aiee:CL21A226MAQNNNE", "C5", V_22U,
                     at=(228.60, 165.10), footprint=f"{FP}:C0805")
    sh.wire_pins("C5", {"1": "+3V3", "2": "GND"})

    # ---- rails + the board's three PWR_FLAGs -------------------------------
    # Every driver on this board is a passive pin (USB connector, inductor),
    # so without these ERC reports all three rails undriven. Power symbols
    # make the nets global, so one flag each covers the whole hierarchy.
    sh.power_flag("VBUS", at=(101.60, 215.90), sym="power:VBUS", flag=True)
    sh.power_flag("+3V3", at=(101.60, 228.60), sym="power:+3V3", flag=True)
    sh.power_flag("GND", at=(101.60, 241.30), sym="power:GND", flag=True)

    for ref, code in LCSC.items():
        sh.sch.components.get(ref).set_property("LCSC", code)
    return sh
