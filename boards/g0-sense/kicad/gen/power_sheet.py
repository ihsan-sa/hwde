"""g0-sense `power` sheet: USB-C power-only sink -> VBUS protection -> AMS1117.

Blocks B1 (usb-input + protection) + B2 (ldo-3v3), architecture/blocks.md.
Refdes ranges (architecture/sheets.md s1): J1; U1; F1; D1-D9; R1-R9; C1-C9;
pwr_base=100. All four rails (VBUS / +5V / +3V3 / GND) are GLOBAL power
symbols with bare netlist names - this sheet has NO hierarchical pins.
Sheet-local labels: CC1, CC2 (-> /power/CC1, /power/CC2) plus the D2/R3
midpoint PWR_LED_K (-> /power/PWR_LED_K).

Pinouts are the P3 ground truth (lib pin tables read via schlib --pins),
not memory:
  J1  aiee:TYPE-C-31-M-12 (parts.json C165948): the pulled footprint merges
      the GND pad pairs and the VBUS pad pairs, so the symbol has compound
      pads A1B12/B1A12 = GND and A4B9/B4A9 = VBUS (all four contacts of each
      group landed+ganged per usbc-sink-receptacle-land-all-shell-bond);
      A5 = CC1, B5 = CC2; A6/A7/B6/B7 = DP1/DN1/DP2/DN2; A8/B8 = SBU1/SBU2;
      THT shield legs 1-4 all named "EH" -> GND (shell bonds to PCB GND).
  D1  aiee:SMF5.0A_C284108 has generic "1"/"2" pin names. Polarity settled
      TWO independent ways (LEARNINGS 2026-08-27 polarity rule): (a) the
      pulled symbol's diode graphic - cathode bar polyline at x=-1.27 on
      pin 1's side, triangle apex pointing at it; (b) the pulled footprint
      SOD-123_L2.8-W1.8-LS3.7-RD's silk cathode band (double stroke at
      x=-0.97/-0.83) on the pad-1 side. => pin 1 = CATHODE, pin 2 = ANODE.
  U1  parts/C6186.json: 1 GND, 2 VOUT, 3 VIN, 4 = SOT-223 TAB, and the
      pulled symbol names pin 4 VOUT (P3 digest decision: tab = VOUT) - the
      tab is wired to +3V3, never left floating (it is the thermal spreader
      connection for the F.Cu +3V3 pour at P7).
  C3  aiee:CA45-A010K226T is POLARIZED; the librarian renamed its pins to
      "+" (pin 1) / "-" (pin 2), established twice at P3 (manufacturer PDF
      marking convention + raw EasyEDA CAD "+" graphic). Pin 1 "+" -> +3V3,
      pin 2 "-" -> GND; a build-time assert below re-checks the names.
  D2  aiee:KT-0603R: pin 1 = A (anode), pin 2 = K (cathode).

Circuit decisions implemented here (all upstream, none re-derived):
- R1 on CC1 and R2 on CC2, 5.1k each, INDEPENDENTLY to GND - never one
  shared resistor (usbc-sink-cc-independent-rd-principle: shared Rd + an
  e-marked cable's Ra reads SRC.Ra on both pins and the source never
  enables VBUS; usbc-sink-rd-5k1-per-pin: nothing in series with CC).
- D1 TVS at the connector, cathode on VBUS, anode on GND, BEFORE the series
  PTC (usbc-sink-vbus-tvs-before-series-element).
- C1 100 nF is the ONLY capacitance ahead of the PTC: the Type-C sink
  attach-capacitance limit is <= 10 uF at the receptacle
  (usbc-sink-attach-capacitance-10uf); the 10 uF bulk (C2) lives AFTER F1.
- F1 PTC in series VBUS -> +5V.
- C2 10 uF X5R on +5V at U1 VIN (ldo-1117-input-cap-and-protection: the
  input cap's job is local source impedance, so it sits at the VIN pin,
  downstream of the PTC).
- C3 22 uF TANTALUM on +3V3 (ldo-1117-family-output-cap-esr: the 1117 loop
  needs the output cap's ESR inside 0.3-22 ohm; a bare ceramic is NOT a
  substitute). NOT substitutable, polarity as above.
- D2 (red) + R3 680R from +3V3 to GND: the LED indicates the 3V3 rail the
  logic runs on, not VBUS (architecture decision 11; R3 value is the P3
  BOM-of-record 680R Basic swap for the unavailable 620R).
- AMS1117 is a LINEAR regulator: no "role": "reg_input" on C2 and no HF
  input ceramic demanded - that rule is for switching regulators only.

PWR_FLAG placement: VBUS, +5V and GND have only passive/power_in pins, so
each carries the board's one PWR_FLAG here. +3V3 is DRIVEN by U1 pin 2
(power_out) - a flag there would be a power_out-vs-power_out ERC error.
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve()
BOARD = HERE.parents[2]          # boards/g0-sense
REPO = HERE.parents[4]           # repo root
sys.path.insert(0, str(REPO / ".claude" / "skills" / "ai-ee" / "scripts"))

import kicad_sch_api as ksa  # noqa: E402

import schlib  # noqa: E402

# kicad-sch-api resolves lib_ids through its global cache, which does NOT
# read kicad/sym-lib-table (LEARNINGS 2026-07-27) - register the pulled lib.
ksa.get_symbol_cache().add_library_path(BOARD / "lib" / "aiee.kicad_sym")

FP = "aiee"

LCSC = {
    "J1": "C165948", "R1": "C23186", "R2": "C23186", "D1": "C284108",
    "F1": "C976303", "C1": "C14663", "U1": "C6186", "C2": "C15850",
    "C3": "C122643", "D2": "C2286", "R3": "C23228",
}


def build() -> schlib.Sheet:
    sh = schlib.Sheet("power",
                      title="g0-sense: USB-C power entry + 3V3 LDO",
                      paper="A3", date="2026-08-27", company="ai-ee",
                      pwr_base=100)

    # ---- J1 USB-C receptacle, power-only sink -----------------------------
    sh.add_component("aiee:TYPE-C-31-M-12", "J1", "TYPE-C-31-M-12",
                     at=(63.50, 127.00),
                     footprint=f"{FP}:USB-C_SMD-TYPE-C-31-M-12_1",
                     expect={"A4B9": "VBUS", "B4A9": "VBUS",
                             "A1B12": "GND", "B1A12": "GND",
                             "A5": "CC1", "B5": "CC2",
                             "A6": "DP", "A7": "DN",
                             "B6": "DP", "B7": "DN",
                             "A8": "SBU1", "B8": "SBU2",
                             "1": "EH", "2": "EH", "3": "EH", "4": "EH"})
    sh.wire_pins("J1", {
        # all four VBUS contacts (footprint gangs them pairwise) and all
        # four GND contacts landed - collective current rating
        # (usbc-sink-receptacle-land-all-shell-bond).
        "A4B9": "VBUS", "B4A9": "VBUS",
        "A1B12": "GND", "B1A12": "GND",
        # shell/shield: all four THT legs bonded straight to GND.
        "1": "GND", "2": "GND", "3": "GND", "4": "GND",
        # CC pins to their OWN Rd resistors (sheet-local labels).
        "A5": "CC1", "B5": "CC2",
        # D+/D-: no-connect. Power-only sink - a PSD has no USB data
        # function, the pairs never become nets (blocks.md B1).
        "A6": "NC", "A7": "NC", "B6": "NC", "B7": "NC",
        # SBU1/SBU2: no-connect. No Alternate Mode on a power-only sink.
        "A8": "NC", "B8": "NC",
    })

    # ---- CC terminations: one INDEPENDENT 5.1k Rd per CC pin --------------
    # Two separate resistors, each its own pull to GND - NEVER shared
    # (usbc-sink-cc-independent-rd-principle), nothing in series
    # (usbc-sink-rd-5k1-per-pin).
    sh.add_component("aiee:0603WAF5101T5E", "R1", "5.1k 1%",
                     at=(114.30, 148.59), footprint=f"{FP}:R0603")
    sh.wire_pins("R1", {"1": "CC1", "2": "GND"})
    sh.add_component("aiee:0603WAF5101T5E", "R2", "5.1k 1%",
                     at=(114.30, 161.29), footprint=f"{FP}:R0603")
    sh.wire_pins("R2", {"1": "CC2", "2": "GND"})

    # ---- VBUS protection chain: J1 -> D1 (shunt) -> F1 (series) -> +5V ----
    # D1 pin 1 = CATHODE (settled two ways, see module docstring): cathode
    # to VBUS, anode to GND - TVS at the connector, ahead of the PTC
    # (usbc-sink-vbus-tvs-before-series-element).
    sh.add_component("aiee:SMF5.0A_C284108", "D1", "SMF5.0A TVS 5V",
                     at=(114.30, 96.52),
                     footprint=f"{FP}:SOD-123_L2.8-W1.8-LS3.7-RD")
    sh.wire_pins("D1", {"1": "VBUS", "2": "GND"})

    # C1 100 nF at the connector: the ONLY capacitance ahead of the PTC
    # (usbc-sink-attach-capacitance-10uf - receptacle-side bank must stay
    # under the 10 uF Type-C attach limit; bulk lives behind F1).
    sh.add_component("aiee:CC0603KRX7R9BB104", "C1", "100nF 50V X7R",
                     at=(139.70, 96.52), footprint=f"{FP}:C0603")
    sh.wire_pins("C1", {"1": "VBUS", "2": "GND"})

    # F1 PTC in series: VBUS -> +5V (750 mA hold / 1.5 A trip / 70 mOhm).
    sh.add_component("aiee:BSMD0805-075-16V", "F1", "PTC 750mA 16V",
                     at=(165.10, 96.52), footprint=f"{FP}:F0805")
    sh.wire_pins("F1", {"1": "VBUS", "2": "+5V"})

    # ---- U1 AMS1117-3.3 + C2 (VIN) / C3 (VOUT) ----------------------------
    # Pin 4 is the SOT-223 TAB = VOUT (pulled symbol + P3 decision): wired
    # to +3V3, not floating. C2 at VIN per ldo-1117-input-cap-and-protection;
    # C3 22 uF tantalum per ldo-1117-family-output-cap-esr. Linear regulator:
    # no reg_input role, no HF input ceramic demanded.
    sh.place_ic_with_decoupling(
        "U1", "aiee:AMS1117-3.3", "AMS1117-3.3",
        at=(215.90, 127.00),
        pins={"1": "GND", "2": "+3V3", "3": "+5V", "4": "+3V3"},
        footprint=f"{FP}:SOT-223-3_L6.5-W3.4-P2.30-LS7.0-BR",
        expect={"1": "GND", "2": "VOUT", "3": "VIN", "4": "VOUT"},
        decoupling=[
            {"cap": "C2", "pin": "3", "rail": "+5V",
             "value": "10uF 25V X5R",
             "lib_id": "aiee:CL21A106KAYNNNE", "footprint": f"{FP}:C0805"},
            {"cap": "C3", "pin": "2", "rail": "+3V3",
             "value": "22uF 10V tantalum",
             "lib_id": "aiee:CA45-A010K226T",
             "footprint": f"{FP}:CASE-A_3216"},
        ],
        caps_at=(203.20, 190.50), caps_dx=25.40)
    # C3 is POLARIZED - place_ic_with_decoupling wires cap pin 1 -> rail and
    # pin 2 -> GND, which for this part means "+" -> +3V3 and "-" -> GND.
    # Re-assert the librarian's pin renaming so a silent lib refresh can
    # never flip the tantalum (getting this backwards destroys hardware).
    c3_names = {p.number: p.name
                for p in sh.sch.components.get("C3").pins}
    if c3_names != {"1": "+", "2": "-"}:
        raise ValueError(f"C3 tantalum polarity pins changed: {c3_names}")

    # ---- D2 power LED (red) + R3 on the +3V3 rail -------------------------
    # Indicates the rail the logic runs on, not VBUS (decision 11).
    # +3V3 -> D2 anode (pin 1) -> cathode (pin 2) -> PWR_LED_K -> R3 -> GND.
    sh.add_component("aiee:KT-0603R", "D2", "Red LED",
                     at=(266.70, 96.52),
                     footprint=f"{FP}:LED-SMD_L1.6-W0.8-R-RD",
                     expect={"1": "A", "2": "K"})
    sh.wire_pins("D2", {"1": "+3V3", "2": "PWR_LED_K"})
    sh.add_component("aiee:0603WAF6800T5E", "R3", "680R 1%",
                     at=(266.70, 110.49), footprint=f"{FP}:R0603")
    sh.wire_pins("R3", {"1": "PWR_LED_K", "2": "GND"})

    # ---- rails: power symbols + the board's PWR_FLAGs ---------------------
    # VBUS / +5V / GND see only passive and power_in pins anywhere in the
    # hierarchy, so each carries its single board-wide PWR_FLAG here.
    # +3V3 is driven by U1 VOUT (power_out): symbol only, NO flag.
    sh.power_flag("VBUS", at=(63.50, 218.44), sym="power:VBUS", flag=True)
    sh.power_flag("+5V", at=(63.50, 231.14), sym="power:+5V", flag=True)
    sh.power_flag("GND", at=(63.50, 243.84), sym="power:GND", flag=True)
    sh.power_symbol_at_pin("U1", "1", "power:GND")
    sh.power_symbol_at_pin("U1", "2", "power:+3V3")

    for ref, code in LCSC.items():
        sh.sch.components.get(ref).set_property("LCSC", code)
    return sh


if __name__ == "__main__":
    path = build().save(BOARD / "kicad", project=False)
    print(f"wrote {path}")
