"""Generator for the pd-trigger-lite schematic - ONE FLAT root sheet.

Source of truth for kicad/pd-trigger-lite.kicad_sch (+ .kicad_pro,
decoupling.json). Rebuild:

    .venv/bin/python boards/pd-trigger-lite/kicad/gen/root.py

Wiring facts (parts/C42459160.json, CH224 manual V2.1 tables 4-1/5-1, 6.1.1):
  U1 CH224A: 1 VHV (supply, 32 V abs max, 1 uF to GND), 8 VBUS sense (short
  to VHV), 6 CC2, 7 CC1 (direct, Rd internal), 9 CFG1 (Rset to GND),
  2/3 CFG2/CFG3 float (internal pull-ups, single-resistor mode), 4/5 DP/DM
  unused (6-pin receptacle has no data contacts), 10 PG unused, 11 = GND pad.
  Rset table 5-1: 6.8k 9 V, 24k 12 V, 56k 15 V, 120k 20 V.
J1 TYPE-C-6M-001 (C2798175): A9/B9 VBUS, A12/B12 GND, A5 CC1, B5 CC2,
  shell stakes 1-4 to GND.
D1 KT-0603R: pin 1 = A, pin 2 = K.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
BOARD = HERE.parents[2]
REPO = HERE.parents[4]
sys.path.insert(0, str(REPO / ".claude" / "skills" / "hwde" / "scripts"))

import kicad_sch_api as ksa  # noqa: E402

ksa.get_symbol_cache().add_library_path(BOARD / "lib" / "aiee.kicad_sym")

import schlib  # noqa: E402

FP = "aiee"
R0603 = f"{FP}:R0603"
LCSC = {
    "U1": "C42459160", "J1": "C2798175", "C1": "C15849",
    "R1": "C23212", "R2": "C23352", "R3": "C23206", "R4": "C25808",
    "R5": "C21189", "R6": "C25804", "D1": "C2286", "R7": "C21189",
}


def build() -> schlib.Sheet:
    sh = schlib.Sheet("pd-trigger-lite",
                      title="pd-trigger-lite: USB-C PD trigger, 9/12/15/20 V, 3 A",
                      paper="A4", date="2026-09-24", company="hwde", pwr_base=1)

    # ---- B1 input: USB-C 6P, power only
    sh.add_component("aiee:TYPE-C-6M-001", "J1", "USB-C 6P", at=(50.8, 76.2),
                     footprint=f"{FP}:USB-C-SMD_918-418K2023S40006",
                     expect={"A9": "VBUS", "B9": "VBUS", "A12": "GND",
                             "B12": "GND", "A5": "CC1", "B5": "CC2"})
    sh.wire_pins("J1", {"A9": "VBUS", "B9": "VBUS", "A12": "GND",
                        "B12": "GND", "A5": "CC1", "B5": "CC2",
                        "1": "GND", "2": "GND", "3": "GND", "4": "GND"})

    # ---- B2 controller
    sh.place_ic_with_decoupling(
        "U1", "aiee:CH224A", "CH224A", at=(114.3, 76.2),
        footprint=f"{FP}:ESSOP-10_L4.9-W3.9-P1.0-LS6.0-TL-EP",
        pins={"1": "VHV", "8": "VHV",          # VHV + sense tied (table 4-1)
              "7": "CC1", "6": "CC2",
              "9": "CFG1",
              "2": "NC", "3": "NC",            # CFG2/3 float in Rset mode
              "4": "NC", "5": "NC",            # DP/DM: no data contacts
              "10": "NC",                      # PG unused
              "11": "GND"},
        expect={"1": "VHV", "2": "CFG2", "3": "CFG3", "4": "DP", "5": "DM",
                "6": "CC2", "7": "CC1", "8": "VBUS", "9": "CFG1",
                "10": "PG", "11": "GND"},
        decoupling=[{"cap": "C1", "pin": "1", "rail": "VHV", "rail_net": "/VHV",
                     "value": "1uF 50V X5R", "lib_id": "aiee:CL10A105KB8NNNC",
                     "footprint": f"{FP}:C0603", "max_dist_mm": 5.0}],
        caps_at=(114.3, 111.76))

    # ---- B3 voltage select: Rset + one link per voltage, 12 V fitted (R5 0R)
    rows = [("R1", "aiee:0603WAF6801T5E", "6.8k", "SEL9", "JP1", "9V"),
            ("R2", "aiee:0603WAF2402T5E", "24k", "SEL12", "R5", "12V"),
            ("R3", "aiee:0603WAF5602T5E", "56k", "SEL15", "JP2", "15V"),
            ("R4", "aiee:0603WAF1203T5E", "120k", "SEL20", "JP3", "20V")]
    for i, (r, lib, val, mid, link, volts) in enumerate(rows):
        y = 60.96 + i * 15.24
        sh.add_component(lib, r, val, at=(165.1, y), footprint=R0603)
        sh.wire_pins(r, {"1": "CFG1", "2": mid})
        if link == "R5":
            sh.add_component("aiee:0603WAF0000T5E", "R5", "0R (12V fitted)",
                             at=(203.2, y), footprint=R0603)
        else:
            # open link = an EMPTY 0603 land (DNP): bridge it with solder
            # or move R5's 0R onto it. Same land as R5, so the owner can
            # simply relocate the one fitted 0R to pick a voltage.
            sh.add_component("Jumper:SolderJumper_2_Open", link,
                             f"{volts} link (open)", at=(203.2, y),
                             footprint=R0603, fields={"LCSC": ""})
            sh.mark_dnp(link)
        sh.wire_pins(link, {"1": mid, "2": "GND"})

    # ---- B4 indicator
    sh.add_component("aiee:0603WAF1002T5E", "R6", "10k", at=(50.8, 127.0),
                     footprint=R0603)
    sh.wire_pins("R6", {"1": "VHV", "2": "LED_A"})

    # R7 0R: splits the 3 A VBUS net (1.25 mm width rule) from the
    # milliamp /VHV stub, so U1's 1 mm-pitch pins and the LED leg can be
    # reached with thin copper. Fails safe: open R7 = no PD request, 5 V.
    sh.add_component("aiee:0603WAF0000T5E", "R7", "0R", at=(76.2, 111.76),
                     footprint=R0603)
    sh.wire_pins("R7", {"1": "VBUS", "2": "VHV"})
    sh.add_component("aiee:KT-0603R", "D1", "LED red", at=(76.2, 127.0),
                     footprint=f"{FP}:LED-SMD_L1.6-W0.8-R-RD",
                     expect={"1": "A", "2": "K"})
    sh.wire_pins("D1", {"1": "LED_A", "2": "GND"})

    # ---- output pads (board feature, not assembled)
    sh.add_component("Connector_Generic:Conn_01x02", "J2", "OUT VBUS/GND",
                     at=(114.3, 139.7), footprint=f"{FP}:OUT_2P_P2.54_D1.1")
    sh.wire_pins("J2", {"1": "VBUS", "2": "GND"})

    # ---- rails: every driver is passive (receptacle contacts) -> PWR_FLAGs
    sh.power_flag("VBUS", at=(165.1, 132.08), sym="power:VBUS", flag=True)
    sh.power_flag("GND", at=(165.1, 144.78), sym="power:GND", flag=True)
    sh.power_flag("VHV", at=(165.1, 157.48), sym=None, flag=True)

    for ref, code in LCSC.items():
        sh.sch.components.get(ref).set_property("LCSC", code)
    # board features (bare copper): nothing to buy; matches the footprints'
    # exclude_from_bom attr so DRC parity stays clean
    for ref in ("J2",):
        sh.sch.components.get(ref).in_bom = False
    return sh


def hide_lcsc_fields(path: Path) -> None:
    """Hide the LCSC property text (it is BOM data, and ksa draws it on top
    of pin labels). Pure text edit on the saved file, electrically inert."""
    import re
    txt = path.read_text(encoding="utf-8")
    txt = re.sub(r'(\(property "LCSC" "[^"]*"\n\s*\(at [^)]*\)\n\s*\(effects\n)',
                 r'\1\t\t\t\t(hide yes)\n', txt)
    path.write_text(txt, encoding="utf-8")


def main(argv=None) -> int:
    out_dir = Path(argv[0]) if argv else HERE.parents[1]
    try:
        sh = build()
        sch = sh.save(out_dir, project=True)
        hide_lcsc_fields(sch)
        meta = sh.emit_decoupling(out_dir / "decoupling.json")
    except Exception as exc:  # noqa: BLE001
        print(json.dumps({"script": "gen.pd-trigger-lite", "status": "error",
                          "error": f"{type(exc).__name__}: {exc}"}))
        return 2
    print(json.dumps({"script": "gen.pd-trigger-lite", "status": "pass",
                      "files": [str(sch), str(meta)],
                      "components": len(LCSC) + 4}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
