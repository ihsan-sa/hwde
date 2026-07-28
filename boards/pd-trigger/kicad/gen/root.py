"""Generator for the pd-trigger schematic - ONE FLAT root sheet.

The schematic SOURCE is this file; `kicad/pd-trigger.kicad_sch`,
`kicad/pd-trigger.kicad_pro` and `kicad/decoupling.json` are BUILD OUTPUT.
Full rebuild from scratch:

    .venv/Scripts/python boards/pd-trigger/kicad/gen/lib_pin_types.py
    .venv/Scripts/python boards/pd-trigger/kicad/gen/root.py

(lib_pin_types.py first after any library refresh - the pulled symbols'
electrical pin types are junk and ERC cannot pass on them. Do NOT re-run
lib_pull: symbol pulls are not idempotent and the hand edits in
lib/EDITS.md would be discarded.)

Flat, not hierarchical, per architecture/sheets.md s1: 28 BOM parts in one
functional chain, every block-crossing net is a rail or a two-part stub, and
the only multi-block signal (/HV_OK) lives inside the indication fan-out.
Consequence: all local labels are root-local, so they appear in the netlist
as `/NAME` - which is exactly what constraints.json declares for /VAUX,
/VIND and /VDD. VBUS and GND are power SYMBOLS, hence bare.

WIRING FACTS - ground truth, not memory
---------------------------------------
U1 CH224K (parts/C970725.json, WCH manual V2.1 tables 4-2 / 6.2 / 7.1 /
8.1.3 / 8.2.3; pad numbering re-confirmed in reports/lib_verify.json):
  pins 1 VDD, 2 CFG2, 3 CFG3, 4 DP, 5 DM, 6 CC2, 7 CC1, 8 VBUS(sense),
  9 CFG1, 10 PG, and GND = **pad 11** - the datasheet calls the exposed
  baseplate "pin 0" and it is the part's ONLY ground terminal; the pulled
  symbol AND footprint both number it 11 (V11 resolved: they agree).
  - VDD (1) is a shunt-regulated node (3.24/3.30/3.36 V, sinks 0-30 mA, abs
    max 3.6 V), fed by a ~1 k dropper from the bus and decoupled by 1 uF.
    It is NOT a regulator input - amendment A1 deleted the LDO for this.
  - VBUS sense (8) has a 13.5 V absolute maximum on a rail that reaches
    21 V: R1 = 10 k in series is mandatory (extract: "a series resistor to
    the external VBUS input is REQUIRED"), reference value 10 k.
  - CC1 (7) <- receptacle A5 and CC2 (6) <- B5, straight through, no
    crossover, no series R and NO external 5.1 k Rd: Rd is integrated on
    the K variant (the CH224D / CH221K reference schematics in the same
    manual DO show 5.1 k - the CH224K one deliberately does not).
  - DP (4) + DM (5) shorted TOGETHER at the chip on /BC12_DIS and NOT taken
    to the receptacle data contacts (architecture V12, resolved in favour of
    PD-only operation: blocks.md B2 / sheets.md s3 item 8). The datasheet's
    own reference schematic 6.2 wires them to the connector instead; the
    architecture overrides that, but they must not float either way.
  - PG (10) is left UNCONNECTED, matching reference schematic 6.2. No
    absolute maximum is published for this pin, so it may not be pulled to
    VBUS or /VIND; a /VDD-referenced pull-up would spend a large slice of
    the 1.7 mA the dropper delivers at the 5 V profile. NC-flagged below.
J1 USB4105-GF-A-120 (GCT drawing rev B3, verified in reports/lib_verify.json):
  the internally-bussed contacts carry COMPOUND pad names - VBUS is
  A4-B9 + B4-A9 (all four contacts), GND is A1-B12 + B1-A12 (all four).
  CC1 = A5, CC2 = B5. Data (A6/A7/B6/B7) and SBU (A8/B8) unused. The four
  THT shell stakes are pads 1-4, all named "EH", all bonded to GND.
D1 TVS2200DRVR (TI SLVSED5A s6): IN = pins 4,5,6; GND = pins 1,2,3 AND the
  exposed pad, which TI numbers 7. No cathode band - polarity is by pin.
D2 BZX84C6V2 (LGE datasheet): SOT-23 pin 1 = ANODE, pin 3 = cathode,
  pin 2 = no function (NC-flagged).
Q1 BC847BS (Nexperia BC847BS table 2, matches the pulled symbol exactly):
  1 E1, 2 B1, 3 C2, 4 E2, 5 B2, 6 C1. So TR1 ("Q1A", the window
  comparator) = pins 2/1/6 and TR2 ("Q1B", the inverter) = pins 5/4/3.
D3/D5/D6 LEDs: symbol pin 1 = K (cathode), pin 2 = A; both footprints put
  their cathode cue at pad 1 (lib/EDITS.md s2/s3).
SW1 2.54-3P: the pole pairing is 1-6, 2-5, 3-4 (footprint pad rows, verified
  in reports/lib_verify.json - neither symbol nor footprint states it, so it
  is hard-coded here). ON = contact closed = CFG line pulled to GND = 0.

Topology (blocks.md B1-B6, decisions.md D1-D7 + A1):
  VBUS is ONE copper object end to end - receptacle, TVS, bulk, both taps
  and the screw terminal. There is no VOUT and no series element in the 5 A
  path. /VIND is VBUS behind the 0 ohm link R14 and feeds ALL housekeeping
  (R1 sense, R2A/R2B dropper, the D2 window bias, R8, and the three LED
  legs) so check_current does not force 1.75 mm copper onto every stub.
  /VAUX is its own net behind the PPTC F1.

Deviations from the assignment brief, resolved in favour of the authorities
(architecture/blocks.md B2/B4/B5 + sheets.md s1 + parts/parts.json roles):
  - the dropper and the sense resistor hang off **/VIND**, not VBUS
    (sheets.md s1: "/VIND | R14 pin 2, R1, R2, R6, R8, R10, R12, R13").
  - the 10 k VBUS-sense resistor is **R1**; **R6** is the 6.8 k window base
    resistor. The brief swapped the two refdes.
  - the window detector is the full blocks.md B5 network: D2 + R6 into
    Q1A's base with R7 as the base-emitter leak shunt, R8 as Q1A's collector
    pull-up and R9 driving Q1B - not just D2/R12/R13.
Split refdes: parts.json ships the 1 k dropper as 2x 510 R 1206 in series
  (R2A, R2B) and the 22 uF bulk as 2x 10 uF 1206 (C1A, C1B). Both keep one
  BOM line each. constraints.json's R2 <-> U1 separation entry is updated to
  name R2A/R2B (sheets.md s2 requires constraints to track any refdes edit).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
BOARD = HERE.parents[2]          # boards/pd-trigger
REPO = HERE.parents[4]           # repo root
sys.path.insert(0, str(REPO / ".claude" / "skills" / "ai-ee" / "scripts"))

import kicad_sch_api as ksa  # noqa: E402

# kicad-sch-api resolves lib_ids through its GLOBAL cache, which never reads
# kicad/sym-lib-table (LEARNINGS 2026-07-27) - register the pulled lib.
ksa.get_symbol_cache().add_library_path(BOARD / "lib" / "aiee.kicad_sym")

import schlib  # noqa: E402

FP = "aiee"

# ---------------------------------------------------------------- symbols
S_U1 = "aiee:CH224K"
S_J1 = "aiee:USB4105-GF-A-120"
S_J2 = "aiee:KF128-5.08-2P"
S_J3 = "aiee:HXPZ2.54-1X2PZZ"
S_D1 = "aiee:TVS2200DRVR"
S_D2 = "aiee:BZX84C6V2_C841160"
S_LED_YG = "aiee:XL-1608SYGC-06"
S_LED_RD = "aiee:F.0603.00011_P2-0603R4TS2-06T-001"
S_Q1 = "aiee:BC847BS_C41375126"
S_SW1 = "aiee:2.54-3PTPGT"
S_F1 = "aiee:BSMD1206-100-30V"
S_C_10U = "aiee:CL31A106KBHNNNE"
S_C_100N = "aiee:CC0603KRX7R9BB104"
S_C_1U = "aiee:CL10A105KB8NNNC"
S_R_10K = "aiee:0603WAF1002T5E"
S_R_100K = "aiee:0603WAF1003T5E"
S_R_510 = "aiee:1206W4J0511T5E"
S_R_6K8 = "aiee:0603WAF6801T5E"
S_R_4K7 = "aiee:0603WAF4701T5E"
S_R_47K = "aiee:0603WAF4702T5E"
S_R_3K3 = "aiee:RC1206FR-073K3L"
S_R_1K5 = "aiee:0603WAF1501T5E"
S_R_4K7_0805 = "aiee:0805W8F4701T5E"
S_R_0R = "aiee:0603WAF0000T5E"

# ------------------------------------------------------------- footprints
F_R0603 = f"{FP}:R0603"
F_R0805 = f"{FP}:R0805"
F_R1206 = f"{FP}:R1206"
F_C0603 = f"{FP}:C0603"
F_C1206 = f"{FP}:C1206"
F_LED_YG = f"{FP}:LED0603-RD_GREEN"
F_LED_RD = f"{FP}:LED0603-RD"

# ------------------------------------------------------------------ values
V_10U = "10uF 50V X5R"
V_100N = "100nF 50V X7R"
V_1U = "1uF 50V X5R"

# LCSC codes, parts/parts.json (stamped on every component; KiCad 10 DRC
# raises footprint_symbol_field_mismatch without them - LEARNINGS 2026-07-27)
LCSC = {
    "U1": "C970725", "J1": "C5184243", "J2": "C474952", "J3": "C32713268",
    "D1": "C523793", "D2": "C841160", "D3": "C965805", "D6": "C965805",
    "D5": "C7496813", "Q1": "C41375126", "SW1": "C7421520", "F1": "C5358568",
    "C1A": "C13585", "C1B": "C13585", "C2": "C14663", "C5": "C15849",
    "R1": "C25804", "R8": "C25804",
    "R3": "C25803", "R4": "C25803", "R5": "C25803",
    "R2A": "C25386", "R2B": "C25386",
    "R6": "C23212", "R7": "C23162", "R9": "C25819", "R10": "C137292",
    "R12": "C22843", "R13": "C17673", "R14": "C21189",
}


def build() -> schlib.Sheet:
    sh = schlib.Sheet("pd-trigger",
                      title="pd-trigger: USB-C PD sink trigger, 5 A pass-through",
                      paper="A3", date="2026-07-28", company="ai-ee",
                      pwr_base=1)

    # ================================================== B1 input + protection
    # J1's four VBUS contacts and four GND contacts are ganged INSIDE the
    # part onto two compound pads each; all four of both must appear in the
    # netlist (the 5.00 A rating is collective across them - sheets.md s3
    # item 10). The four shell stakes go straight to GND: bench tool, no
    # chassis, so no 1 M / 4.7 nF hybrid tie (sheets.md s3 item 9).
    # Data + SBU contacts are NC-flagged: this is a power-only trigger, the
    # controller's DP/DM are shorted at the chip instead (see U1 below).
    # C1A/C1B/C2 are the connector-side bulk; they are declared here as VBUS
    # decoupling so check_pdn sees a reservoir on the rail (class "bulk":
    # they belong to the connector entry, not to an IC pin pair).
    sh.place_ic_with_decoupling(
        "J1", S_J1, "USB-C 16P 5A",
        at=(76.2, 88.9), footprint=f"{FP}:USB-C-SMD_MC-311D",
        pins={
            "A4-B9": "VBUS", "B4-A9": "VBUS",       # all four VBUS contacts
            "A1-B12": "GND", "B1-A12": "GND",       # all four GND contacts
            "A5": "CC1", "B5": "CC2",
            "A6": "NC", "A7": "NC",                 # Dp1/Dn1: PD-only board
            "B6": "NC", "B7": "NC",                 # Dp2/Dn2: PD-only board
            "A8": "NC", "B8": "NC",                 # SBU1/SBU2: unused
            "1": "GND", "2": "GND", "3": "GND", "4": "GND",   # shell stakes
        },
        expect={"A4-B9": "VBUS", "B4-A9": "VBUS", "A1-B12": "GND",
                "B1-A12": "GND", "A5": "CC1", "B5": "CC2", "A6": "Dp1",
                "A7": "Dn1", "B6": "Dp2", "B7": "Dn2", "A8": "SBU1",
                "B8": "SBU2", "1": "EH", "2": "EH", "3": "EH", "4": "EH"},
        decoupling=[
            {"cap": "C1A", "pin": "A4-B9", "rail": "VBUS", "value": V_10U,
             "lib_id": S_C_10U, "footprint": F_C1206, "class": "bulk"},
            {"cap": "C1B", "pin": "A4-B9", "rail": "VBUS", "value": V_10U,
             "lib_id": S_C_10U, "footprint": F_C1206, "class": "bulk"},
            {"cap": "C2", "pin": "A4-B9", "rail": "VBUS", "value": V_100N,
             "lib_id": S_C_100N, "footprint": F_C0603, "class": "bulk"},
        ],
        caps_at=(139.7, 152.4), caps_dx=25.4)

    # D1: unidirectional TVS, first element on VBUS at the connector.
    sh.add_component(S_D1, "D1", "TVS2200 22V", at=(139.7, 60.96),
                     footprint=f"{FP}:WSON-6_L2.0-W2.0-P0.65-BL-EP",
                     expect={"1": "GND", "2": "GND", "3": "GND", "4": "IN",
                             "5": "IN", "6": "IN", "7": "GND"})
    sh.wire_pins("D1", {"4": "VBUS", "5": "VBUS", "6": "VBUS",
                        "1": "GND", "2": "GND", "3": "GND", "7": "GND"})

    # ==================================================== B4 housekeeping stub
    # R14: the 0 ohm link that separates the 5 A net from everything else.
    # Fails safe - if it opens the controller loses its supply, no contract
    # is negotiated and the source stays at its 5 V default.
    sh.add_component(S_R_0R, "R14", "0R", at=(190.5, 60.96),
                     footprint=F_R0603)
    sh.wire_pins("R14", {"1": "VBUS", "2": "VIND"})

    # ======================================================== B6 output + aux
    sh.add_component(S_J2, "J2", "SCREW 5.08 2P", at=(241.3, 88.9),
                     footprint=f"{FP}:CONN-TH_P5.08_KF128-5.08-2P")
    sh.wire_pins("J2", {"1": "VBUS", "2": "GND"})
    sh.add_component(S_F1, "F1", "PPTC 1A 30V", at=(241.3, 60.96),
                     footprint=f"{FP}:F1206")
    sh.wire_pins("F1", {"1": "VBUS", "2": "VAUX"})
    sh.add_component(S_J3, "J3", "HDR 1x2 AUX", at=(292.1, 60.96),
                     footprint=f"{FP}:HDR-TH_2P-P2.54-V-M-3")
    sh.wire_pins("J3", {"1": "VAUX", "2": "GND"})

    # ============================================ B2 controller + its supply
    # C5 is the datasheet's ONLY specified capacitor for this part (table
    # 4-2: "VDD: operating supply input, external 1 uF capacitor to GND,
    # series resistor to VBUS"). rail_net pins the FINAL netlist name.
    sh.place_ic_with_decoupling(
        "U1", S_U1, "CH224K",
        at=(279.4, 114.3),
        footprint=f"{FP}:ESSOP-10_L4.9-W3.9-P1.0-LS6.0-TL-EP",
        pins={
            "1": "VDD",           # shunt node, fed by R2A+R2B from /VIND
            "2": "CFG2", "3": "CFG3", "9": "CFG1",
            "4": "BC12_DIS", "5": "BC12_DIS",   # DP+DM shorted at the chip
            "6": "CC2", "7": "CC1",             # straight to J1 B5 / A5
            "8": "VSENSE",        # behind R1 10 k: 13.5 V abs max on 21 V
            "10": "NC",           # PG: see module docstring / decisions D4
            "11": "GND",          # the "pin 0" baseplate, U1's only ground
        },
        expect={"1": "VDD", "2": "CFG2", "3": "CFG3", "4": "DP", "5": "DM",
                "6": "CC2", "7": "CC1", "8": "VBUS", "9": "CFG1",
                "10": "PG", "11": "GND"},
        decoupling=[
            # max_dist_mm 5 records the extract's own placement clause
            # ("VDD (pin 1) to GND, adjacent to the IC"); without it the
            # 1 uF value would auto-classify "bulk" and check_decoupling
            # would not complain until 20 mm.
            {"cap": "C5", "pin": "1", "rail": "VDD", "rail_net": "/VDD",
             "value": V_1U, "lib_id": S_C_1U, "footprint": F_C0603,
             "max_dist_mm": 5.0},
        ],
        caps_at=(215.9, 210.82))

    # R1: mandatory 10 k series into the VBUS-detect pin.
    sh.add_component(S_R_10K, "R1", "10k", at=(215.9, 165.1),
                     footprint=F_R0603)
    sh.wire_pins("R1", {"1": "VIND", "2": "VSENSE"})
    # R2A + R2B: the datasheet's dropper, shipped as 2x 510 R 1206 in series
    # (~1020 R) because no Basic-tier 1 k 2512 exists - 0.157 W each at 21 V
    # against 0.25 W parts. The single-package 1 k 2512 burning 0.31 W is the
    # architecture's primary; this is its pre-approved alternate (A1.3).
    sh.add_component(S_R_510, "R2A", "510R", at=(215.9, 180.34),
                     footprint=F_R1206)
    sh.wire_pins("R2A", {"1": "VIND", "2": "R2_MID"})
    sh.add_component(S_R_510, "R2B", "510R", at=(215.9, 195.58),
                     footprint=F_R1206)
    sh.wire_pins("R2B", {"1": "R2_MID", "2": "VDD"})

    # ======================================================= B3 profile select
    # 100 k (not 10 k) to /VDD: at the 5 V profile the whole /VDD node is fed
    # 1.7 mA through the dropper, and three 10 k pull-ups would eat 58 % of
    # it. Pull-UP polarity is the safety-relevant half - an open switch, an
    # unpopulated switch or a broken contact all read 1XX = 5 V.
    for ref, at, cfg in (("R3", (279.4, 165.1), "CFG1"),
                         ("R4", (279.4, 180.34), "CFG2"),
                         ("R5", (279.4, 195.58), "CFG3")):
        sh.add_component(S_R_100K, ref, "100k", at=at, footprint=F_R0603)
        sh.wire_pins(ref, {"1": "VDD", "2": cfg})
    # SW1 pole pairing 1-6 / 2-5 / 3-4 is HARD-CODED from the footprint pad
    # rows (reports/lib_verify.json): pads 1,2,3 sit at y=+4.30 and 6,5,4 at
    # y=-4.30, and neither the symbol nor the footprint declares the pairing.
    sh.add_component(S_SW1, "SW1", "DIP-3", at=(342.9, 180.34),
                     footprint=f"{FP}:SW-SMD_6P-L7.6-W6.0-P2.54-LS9.3-BL",
                     expect={"1": "A1", "2": "A2", "3": "A3", "4": "A4",
                             "5": "A5", "6": "A6"})
    sh.wire_pins("SW1", {"1": "CFG1", "6": "GND",     # pole 1
                         "2": "CFG2", "5": "GND",     # pole 2
                         "3": "CFG3", "4": "GND"})    # pole 3

    # ============================================================ B5 indication
    # D3 "PWR": the mandatory power-present LED, the only one that spans the
    # whole input range (0.76 mA at 4.4 V to 5.8 mA at 21 V; 0.11 W in R10,
    # hence 1206).
    sh.add_component(S_R_3K3, "R10", "3.3k", at=(76.2, 190.5),
                     footprint=F_R1206)
    sh.wire_pins("R10", {"1": "VIND", "2": "D3_A"})
    sh.add_component(S_LED_YG, "D3", "LED YG PWR", at=(114.3, 190.5),
                     footprint=F_LED_YG, expect={"1": "K", "2": "A"})
    sh.wire_pins("D3", {"2": "D3_A", "1": "GND"})

    # Window detector: D2 (6.2 V zener, cathode on /VIND) + R6 6k8 into
    # Q1A's base, R7 4k7 base-emitter shunt so zener knee leakage at 5.25 V
    # cannot forward-bias it. Trips at Vz + Vbe ~ 6.7 V: hard off at the 5 V
    # profile's 5.25 V ceiling, hard on at the 9 V profile's 8.55 V floor.
    sh.add_component(S_D2, "D2", "BZX84C6V2", at=(76.2, 228.6),
                     footprint=f"{FP}:SOT-23-3_L2.9-W1.3-P1.90-LS2.4-BR",
                     expect={"1": "A", "3": "K"})
    sh.wire_pins("D2", {"3": "VIND",    # cathode to the bus stub
                        "1": "ZBIAS",   # anode into the base chain
                        "2": "NC"})     # SOT-23 centre lead: no function
    sh.add_component(S_R_6K8, "R6", "6.8k", at=(114.3, 228.6),
                     footprint=F_R0603)
    sh.wire_pins("R6", {"1": "ZBIAS", "2": "HV_B"})
    sh.add_component(S_R_4K7, "R7", "4.7k", at=(114.3, 243.84),
                     footprint=F_R0603)
    sh.wire_pins("R7", {"1": "HV_B", "2": "GND"})

    # Q1A = TR1 (pins 2 B / 1 E / 6 C) is the comparator; Q1B = TR2
    # (5 B / 4 E / 3 C) inverts it, so exactly one of D5/D6 is ever lit.
    # An inverter rather than the cheaper single-transistor "current steal"
    # trick: the steal version depends on the two LEDs' forward voltages
    # being ordered correctly, which is a part-substitution trap (D4).
    sh.add_component(S_Q1, "Q1", "BC847BS", at=(165.1, 228.6),
                     footprint=f"{FP}:SOT-363-6_L2.2-W1.3-P0.65-LS2.1-BL",
                     expect={"1": "E", "2": "B", "3": "C",
                             "4": "E", "5": "B", "6": "C"})
    sh.wire_pins("Q1", {"2": "HV_B", "1": "GND", "6": "HV_OK",    # Q1A
                        "5": "FB_B", "4": "GND", "3": "FB_K"})    # Q1B
    sh.add_component(S_R_10K, "R8", "10k", at=(215.9, 228.6),
                     footprint=F_R0603)
    sh.wire_pins("R8", {"1": "VIND", "2": "HV_OK"})
    sh.add_component(S_R_47K, "R9", "47k", at=(215.9, 243.84),
                     footprint=F_R0603)
    sh.wire_pins("R9", {"1": "HV_OK", "2": "FB_B"})

    # D5 "5V ONLY" (red) conducts ONLY below the 6.7 V trip, through Q1B;
    # D6 "PROFILE OK" (green) only above it, into Q1A's collector node. Each
    # leg therefore has a fixed resistor sized for a single voltage regime,
    # which is why losing the regulated rail at amendment A1 did not damage
    # the scheme.
    sh.add_component(S_R_1K5, "R12", "1.5k", at=(76.2, 254.0),
                     footprint=F_R0603)
    sh.wire_pins("R12", {"1": "VIND", "2": "D5_A"})
    sh.add_component(S_LED_RD, "D5", "LED RED 5V ONLY", at=(114.3, 254.0),
                     footprint=F_LED_RD, expect={"1": "K", "2": "A"})
    sh.wire_pins("D5", {"2": "D5_A", "1": "FB_K"})
    sh.add_component(S_R_4K7_0805, "R13", "4.7k", at=(76.2, 269.24),
                     footprint=F_R0805)
    sh.wire_pins("R13", {"1": "VIND", "2": "D6_A"})
    sh.add_component(S_LED_YG, "D6", "LED YG PROFILE OK", at=(114.3, 269.24),
                     footprint=F_LED_YG, expect={"1": "K", "2": "A"})
    sh.wire_pins("D6", {"2": "D6_A", "1": "HV_OK"})

    # ================================================================== rails
    # VBUS and GND are power SYMBOLS (global, bare names). Every driver on
    # this board is a passive pin - the receptacle contacts, a resistor
    # dropper, an internal shunt - so each rail that feeds a power_in pin
    # needs a PWR_FLAG or ERC calls it undriven. /VDD is a root-LOCAL label
    # (netlist name /VDD) carrying U1's power_in pin 1, so it gets a bare
    # PWR_FLAG with no power symbol.
    sh.power_flag("VBUS", at=(330.2, 215.9), sym="power:VBUS", flag=True)
    sh.power_flag("GND", at=(330.2, 228.6), sym="power:GND", flag=True)
    sh.power_flag("VDD", at=(330.2, 241.3), sym=None, flag=True)

    for ref, code in LCSC.items():
        sh.sch.components.get(ref).set_property("LCSC", code)
    return sh


def main(argv=None) -> int:
    out_dir = Path(argv[0]) if argv else HERE.parents[1]  # .../kicad
    try:
        sh = build()
        sch = sh.save(out_dir, project=True)
        meta = sh.emit_decoupling(out_dir / "decoupling.json")
    except Exception as exc:  # noqa: BLE001  (SPEC 6: any error -> exit 2)
        print(json.dumps({"script": "gen.pd-trigger", "status": "error",
                          "error": f"{type(exc).__name__}: {exc}"}))
        return 2
    print(json.dumps({
        "script": "gen.pd-trigger", "status": "pass",
        "files": [str(sch), str(out_dir / "pd-trigger.kicad_pro"), str(meta)],
        "components": len(LCSC),
        "decoupling_associations": len(sh.decoupling),
    }, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
