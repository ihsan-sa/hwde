"""LUM-CAR-A `eth` sheet: W5500 hardwired-TCP/IP Ethernet controller.

The schematic SOURCE is this file; `kicad/eth.kicad_sch` is BUILD OUTPUT.
Rebuild standalone:

    .venv/Scripts/python boards/lumina-carrier/kicad/gen/eth.py

The root generator imports `build()` and stitches this sheet with
`schlib.Project.add_sheet(eth.build(), ..., nets=[...])` - see INTERFACE
below for the exact `nets=` list and order.

Blocks (architecture/sheets.md s2.2): U10 W5500, Y10 25 MHz crystal group,
EXRES1 / TOCAP / 1V2O support, D10 MDI ESD array, SPI series + pull-ups.

REFDES: every reference comes from parts/parts.json, NEVER from the pulled
symbol's Reference property. Two of the symbols used here disagree with it:
`aiee:X322525MRB4SI` defaults to "X" (must be **Y10**) and
`aiee:TPD4E1U06DBVR_C19829453` defaults to "D" (correct here, D10).

WIRING FACTS - ground truth, not memory
---------------------------------------
U10 W5500 (parts/C32843.json, WIZnet DS v1.1.0, Table 2 + s5.3/5.5):
  - ONE 3.3 V supply, two on-die domains. AVDD = 4, 8, 11, 15, 17, 21;
    VDD = 28 (the only digital supply). Returns AGND = 3, 9, 14, 16, 19, 48
    and GND = 29. s5.3 gives ONE supply line, "Apply VDD, AVDD,
    2.97/3.3/3.63 V". There is NO 1.8 V core rail and no second supply.
  - 1V2O (22) is the on-chip 1.2 V regulator OUTPUT and "must be connected
    to a 10nF capacitor" - it is not a supply input. C33.
  - EXRES1 (10): 12.4 k 1 % to AGND (Figure 2 R21) sets the MDI drive
    current and hence the 950-1050 mV output amplitude. R30.
  - VBG (18) "must be left floating" - explicit no-connect, never loaded
    and never decoupled.
  - TOCAP (20): 4.7 uF, "trace length to capacitor should be short". C32.
  - RSVD ASYMMETRY: pin 23 "must be tied to GND"; pins 38-42 are NC
    (DS v1.0.2 changed 38-42 from "tie to GND" to "NC"). Pin 7 is DNC.
  - MDI: TXN=1, TXP=2, RXN=5, RXP=6. SPI: SCSn=32, SCLK=33, MISO=34,
    MOSI=35. INTn=36, RSTn=37.
  - LEDs SPDLED=24, LINKLED=25, DUPLED=26, ACTLED=27: push-pull ACTIVE LOW,
    IOL 8.6 mA min at VOL 0.4 V. LINK and ACT drive the J1 magjack LED
    CATHODES on the `poe` sheet (anodes to +3V3 through R7/R8 there).
  - PMODE[2:0] = 43/44/45 have internal pull-ups; floating = 111 =
    all-capable, auto-negotiation enabled. Left NC on purpose.
  - SCSn (32) and RSTn (37) have internal pull-ups (50/77/112 k); R33/R34
    are the external belt-and-braces pull-ups sheets.md s2.2 mandates.
  - SPI ceiling: 33.3 MHz is the BINDING guaranteed number (footnote 5 calls
    80 MHz "theoretical design speed"). The board runs 20 MHz = 1.7x margin.
    Mode 0/3, MSB first, Variable Length Data Mode (host drives SCSn).
  - LQFP-48, 7x7, 0.5 mm pitch, NO exposed pad.
  - The datasheet has NO layout chapter and NO decoupling requirement: the
    strings "decoupling", "bypass" and "layout" appear nowhere in its 67
    pages. Only TOCAP 4.7 uF and 1V2O 10 nF are mandated. The 100 nF per
    supply pin below is GOOD PRACTICE, explicitly NOT datasheet-mandated.

Y10 X322525MRB4SI (parts/parts.json + C32843.json s5.5.3): 25 MHz, CL 18 pF,
  +/-10 ppm initial and +/-20 ppm over -40..+85 C (= the DS's +/-30 ppm at
  25 C budget met with margin against IEEE 802.3 clause 25's +/-50 ppm),
  shunt <= 7 pF. Figure 3 reference schematic: crystal across XI (30) / XO
  (31), a 1 M feedback resistor across XI-XO, a 0 ohm series resistor in the
  XO leg, and a load capacitor from EACH crystal terminal to ground.
  Load caps are 27 pF NP0 = 2 x (CL 18 pF - ~4.5 pF stray); expect to trim
  on the first prototype. Most W5500 module schematics use 22 pF, which
  back-solves to CL 15 pF and is wrong for an 18 pF part.
  Symbol pins: 1 OSC1, 3 OSC2, 2 + 4 case GND (footprint pads 1/3 are the
  diagonal terminal pair - verified against aiee.pretty).

D10 TPD4E1U06DBVR (parts/C19829453.json): 1 = D2-, 2 = GND, 3 = D2+,
  4 = D1+, 5 = NC (a genuine no-connect), 6 = D1-. CJ 0.55 pF typ /
  0.9 pF max per line, safely inside the <= 1 pF/line budget, so it does not
  degrade the 100BASE-TX return-loss floor. Wired BY PIN NUMBER from that
  JSON - see the SYMBOL PIN NAMES note at D10 below (the pull had pins 1
  and 4 captioned backwards; the symbol has since been repaired).

MDI termination: NONE. Neither the W5500 nor the HY931147C magjack datasheet
  publishes any MDI termination value, and TI SNLA079D s2.3 states the 75
  ohm "Bob Smith" network does not apply to a PoE port (the centre taps feed
  the rectifier). No 75 ohm resistors and no centre-tap bias network here.

INTERFACE (root `nets=` list, order as declared in architecture/sheets.md
s1.2 / this sheet's row of the s0 table):
    ETH_TXP, ETH_TXN, ETH_RXP, ETH_RXN, ETH_LED_LINK, ETH_LED_ACT,
    ETH_SCLK, ETH_MOSI, ETH_MISO, ETH_CSn, ETH_INTn, ETH_RSTn
Rails (+3V3, GND) are power SYMBOLS: global, bare-named, NO sheet pin.
This sheet carries NO PWR_FLAG - sheets.md s1.1 puts all six on `poe`/`pwr`.

DEVIATIONS from architecture/sheets.md, and why
-----------------------------------------------
1. SPI series resistors split their nets. sheets.md s1.2 lists R31 as a
   MEMBER of `/ETH_SCLK` alongside both U10 SCLK and U30 GPIO12, but s2.2
   specifies R31/R32 as "22-33 ohm SERIES, at the driver pin" - a series
   element cannot leave one net. Resolved in favour of s2.2 (the more
   specific component-level statement): the hierarchical pin sits on the
   MCU-facing terminal, so `/ETH_SCLK` and `/ETH_MOSI` still cross the root
   exactly as constraints.json declares (`/ETH_SCLK` is a `high_speed`
   entry - if it stopped crossing, it would be renamed and
   check_return_path would raise CheckError -> exit 2). The PHY-side stubs
   become `/eth/SCLK_PHY` and `/eth/MOSI_PHY`, which no constraint names.
   Both resistors are intended for the DRIVER end: U30 drives SCLK and
   MOSI, so P6 must place R31/R32 next to U30, not next to U10
   (sheets.md s2.2: "placed at U30's end").
2. The crystal leg needs a third internal net. sheets.md s1.3 names only
   `/eth/XI` and `/eth/XO`, but the datasheet's 0 ohm series resistor in the
   XO leg splits XO into `/eth/XO` (U10 pin 31 side) and `/eth/XO_XTAL`
   (crystal + C31 side). Neither name is referenced by constraints.json.
3. R35 (1 M feedback) and R36 (0 R series) are NOT in parts/parts.json's
   refs lists. They re-use existing BOM lines - C22935 (1 M 1 % 0603, today
   qty 1 for R6) and C21189 (0 R 0603, today qty 1 for R9) - so P8 must bump
   both quantities from 1 to 2. No new part numbers are introduced.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
BOARD = HERE.parents[2]          # boards/lumina-carrier
REPO = HERE.parents[4]           # repo root
sys.path.insert(0, str(REPO / ".claude" / "skills" / "ai-ee" / "scripts"))

import kicad_sch_api as ksa  # noqa: E402

# kicad-sch-api resolves lib_ids through its GLOBAL cache, which never reads
# kicad/sym-lib-table (LEARNINGS 2026-07-28) - register the pulled lib.
ksa.get_symbol_cache().add_library_path(BOARD / "lib" / "aiee.kicad_sym")

import schlib  # noqa: E402

FP = "aiee"

# ---------------------------------------------------------------- symbols
S_U10 = "aiee:W5500"
S_Y10 = "aiee:X322525MRB4SI"
S_D10 = "aiee:TPD4E1U06DBVR_C19829453"
S_C_27P = "aiee:CC0603JRNPO9BN270"
S_C_100N = "aiee:CC0603KRX7R9BB104"
S_C_10N = "aiee:0603B103K500NT"
S_C_4U7 = "aiee:CL21A475KAQNNNE"
S_R_12K4 = "aiee:0805W8F1242T5E"
S_R_22R = "aiee:0603WAF220JT5E"
S_R_10K = "aiee:0603WAF1002T5E"
S_R_1M = "aiee:0603WAF1004T5E"
S_R_0R = "aiee:0603WAF0000T5E"

# ------------------------------------------------------------- footprints
F_R0603 = f"{FP}:R0603"
F_R0805 = f"{FP}:R0805"
F_C0603 = f"{FP}:C0603"
F_C0805 = f"{FP}:C0805"
F_U10 = f"{FP}:LQFP-48_L7.0-W7.0-P0.50-LS9.0-BL"
F_Y10 = f"{FP}:OSC-SMD_4P-L3.2-W2.5-BL_SIT8008BI"   # correct 4-pad 3225
F_D10 = f"{FP}:SOT-23-6_L2.9-W1.6-P0.95-LS2.8-BR"   # land, name is cosmetic

# ------------------------------------------------------------------ values
V_27P = "27pF 50V NP0 0603"
V_100N = "100nF 50V X7R 0603"
V_10N = "10nF 50V X7R 0603"
V_4U7 = "4.7uF 25V X5R 0805"

# LCSC codes, parts/parts.json (stamped on every component; KiCad 10 DRC
# raises footprint_symbol_field_mismatch without them - LEARNINGS 2026-07-27)
LCSC = {
    "U10": "C32843", "Y10": "C70593", "D10": "C19829453",
    "C30": "C107045", "C31": "C107045",
    "C32": "C1779", "C36": "C1779",
    "C33": "C57112",
    "C34": "C14663", "C35": "C14663", "C37": "C14663",
    "C38": "C14663", "C39": "C14663", "C40": "C14663",
    "C41": "C14663",       # AVDD pin 21 local HF cap - NEW REFDES
    "R30": "C30908",
    "R31": "C23345", "R32": "C23345",
    "R33": "C25804", "R34": "C25804",
    "R35": "C22935",       # 1 M feedback - BOM qty 1 -> 2 (see DEVIATIONS 3)
    "R36": "C21189",       # 0 R series   - BOM qty 1 -> 2 (see DEVIATIONS 3)
}

# Hierarchical interface, in the order the root must pass as `nets=`.
INTERFACE = [
    ("ETH_TXP", "output"), ("ETH_TXN", "output"),
    ("ETH_RXP", "input"), ("ETH_RXN", "input"),
    ("ETH_LED_LINK", "output"), ("ETH_LED_ACT", "output"),
    ("ETH_SCLK", "input"), ("ETH_MOSI", "input"), ("ETH_MISO", "output"),
    ("ETH_CSn", "input"), ("ETH_INTn", "output"), ("ETH_RSTn", "input"),
]


def build() -> schlib.Sheet:
    sh = schlib.Sheet("eth", title="LUM-CAR-A: eth - W5500 Ethernet controller",
                      paper="A3", date="2026-07-28", company="ai-ee",
                      pwr_base=200)

    # ==================================================== U10 W5500 + supply
    # Every one of the 48 pads is wired, pulled or explicitly no-connected.
    # The seven no-connect classes and their justifications:
    #   7  DNC     - Table 2 "Do Not Connect Pin".
    #   12/13/46/47 NC - Table 2 type NC, Figure 2 draws pin 12 crossed out.
    #   18 VBG     - "This pin will be measured as 1.2V at 25 deg C. It must
    #                 be left floating." Loading it shifts every analog bias.
    #   24 SPDLED  - the HY931147C has exactly TWO LED positions and s1.2
    #                assigns them to LINK and ACT; speed is unused.
    #   26 DUPLED  - same, duplex is unused.
    #   38-42 RSVD - DS v1.0.2 changed these five from "tie to GND" to "NC";
    #                they carry internal pull-downs. NOT pin 23 (see below).
    #   43/44/45 PMODE[2:0] - internal pull-ups, floating = 111 = all-capable
    #                with auto-negotiation, which is what this board wants.
    # AGND (3/9/14/16/19/48) and GND (29) both go to the single board GND:
    # this is a 4-layer board with one continuous In1.Cu GND plane
    # (architecture/stackup.md) and the W5500 datasheet publishes no split.
    sh.place_ic_with_decoupling(
        "U10", S_U10, "W5500", at=(177.8, 127.0), footprint=F_U10,
        pins={
            # MDI (analog, 100 ohm differential, root-crossed + constrained)
            "1": "ETH_TXN", "2": "ETH_TXP", "5": "ETH_RXN", "6": "ETH_RXP",
            # analog supply / return
            "4": "+3V3", "8": "+3V3", "11": "+3V3", "15": "+3V3",
            "17": "+3V3", "21": "+3V3",
            "3": "GND", "9": "GND", "14": "GND", "16": "GND", "19": "GND",
            "48": "GND",
            # digital supply / return (the ONLY pair)
            "28": "+3V3", "29": "GND",
            # analog support
            "10": "EXRES", "20": "TOCAP", "22": "1V2O",
            # RSVD ASYMMETRY - pin 23 is tied to GND, 38-42 are NOT
            "23": "GND",
            "38": "NC", "39": "NC", "40": "NC", "41": "NC", "42": "NC",
            # LEDs: active-low push-pull, drive the J1 LED cathodes on `poe`
            "24": "NC", "25": "ETH_LED_LINK", "26": "NC",
            "27": "ETH_LED_ACT",
            # 25 MHz crystal
            "30": "XI", "31": "XO",
            # SPI slave. SCLK/MOSI arrive through R31/R32 (DEVIATIONS 1).
            "32": "ETH_CSn", "33": "SCLK_PHY", "34": "ETH_MISO",
            "35": "MOSI_PHY", "36": "ETH_INTn", "37": "ETH_RSTn",
            # strap / reserved / do-not-connect
            "7": "NC", "12": "NC", "13": "NC", "18": "NC",
            "43": "NC", "44": "NC", "45": "NC", "46": "NC", "47": "NC",
        },
        expect={
            "1": "TXN", "2": "TXP", "3": "AGND", "4": "AVDD", "5": "RXN",
            "6": "RXP", "7": "DNC", "8": "AVDD", "9": "AGND", "10": "EXRES1",
            "11": "AVDD", "12": "NC", "13": "NC", "14": "AGND", "15": "AVDD",
            "16": "AGND", "17": "AVDD", "18": "VBG", "19": "AGND",
            "20": "TOCAP", "21": "AVDD", "22": "1V2O", "23": "RSVD",
            "24": "SPDLED", "25": "LINKLED", "26": "DUPLED", "27": "ACTLED",
            "28": "VDD", "29": "GND", "30": "XI", "31": "XO", "32": "SCSn",
            "33": "SCLK", "34": "MISO", "35": "MOSI", "36": "INTn",
            "37": "RSTn", "38": "RSVD", "39": "RSVD", "40": "RSVD",
            "41": "RSVD", "42": "RSVD", "43": "PMODE2", "44": "PMODE1",
            "45": "PMODE0", "46": "NC", "47": "NC", "48": "AGND",
        },
        decoupling=[
            # 100 nF per supply pin + one 4.7 uF local bulk: one dedicated
            # 100 nF on EVERY one of the seven supply pins (4/8/11/15/17/21
            # AVDD + 28 VDD) plus the shared bulk. NOT DATASHEET-MANDATED -
            # W5500 DS v1.1.0 has no decoupling table at all
            # (parts/C32843.json decoupling[]
            # entry: "NOT GROUNDED"). Standard practice for a 3.3 V mixed-
            # signal PHY drawing 132 mA typ while transmitting at 100M.
            # +3V3 / GND are power SYMBOLS -> bare global netlist names, so
            # no rail_net / gnd_net override is needed here.
            {"cap": "C34", "pin": "4", "rail": "+3V3", "value": V_100N,
             "lib_id": S_C_100N, "footprint": F_C0603},
            {"cap": "C35", "pin": "8", "rail": "+3V3", "value": V_100N,
             "lib_id": S_C_100N, "footprint": F_C0603},
            {"cap": "C37", "pin": "11", "rail": "+3V3", "value": V_100N,
             "lib_id": S_C_100N, "footprint": F_C0603},
            {"cap": "C38", "pin": "15", "rail": "+3V3", "value": V_100N,
             "lib_id": S_C_100N, "footprint": F_C0603},
            {"cap": "C39", "pin": "17", "rail": "+3V3", "value": V_100N,
             "lib_id": S_C_100N, "footprint": F_C0603},
            # C41: pin 21 is an AVDD pin like 4/8/11/15/17 and gets the same
            # dedicated 100 nF. Until this was added it was the ONE supply
            # pin served only by the shared 4.7 uF bulk (C36), which has
            # neither the self-resonance nor the placement proximity to be a
            # local HF return for an analog supply pin.
            {"cap": "C41", "pin": "21", "rail": "+3V3", "value": V_100N,
             "lib_id": S_C_100N, "footprint": F_C0603},
            {"cap": "C36", "pin": "21", "rail": "+3V3", "value": V_4U7,
             "lib_id": S_C_4U7, "footprint": F_C0805, "class": "bulk"},
            {"cap": "C40", "pin": "28", "rail": "+3V3", "value": V_100N,
             "lib_id": S_C_100N, "footprint": F_C0603},
            # The only two capacitors this datasheet actually REQUIRES.
            # C32 carries the Table 2 clause "The trace length to capacitor
            # should be short to stabilize the internal signals" as an
            # explicit 5 mm proximity warn threshold (the 4.7 uF value would
            # otherwise class as "bulk" and not complain until 20 mm).
            {"cap": "C32", "pin": "20", "rail": "TOCAP",
             "rail_net": "/eth/TOCAP", "value": V_4U7, "lib_id": S_C_4U7,
             "footprint": F_C0805, "max_dist_mm": 5.0},
            {"cap": "C33", "pin": "22", "rail": "1V2O",
             "rail_net": "/eth/1V2O", "value": V_10N, "lib_id": S_C_10N,
             "footprint": F_C0603},
        ],
        caps_at=(63.5, 241.3), caps_dx=25.4)

    # Rails are GLOBAL power symbols (bare netlist names, no sheet pin).
    # NO PWR_FLAG on this sheet: sheets.md s1.1 puts all six on poe/pwr,
    # and one flag per net drives it hierarchy-wide.
    sh.power_flag("+3V3", at=(63.5, 260.35), sym="power:+3V3", flag=False)
    sh.power_flag("GND", at=(88.9, 260.35), sym="power:GND", flag=False)

    # ============================================ EXRES1 bias (U10 pin 10)
    # 12.4 k 1 % to AGND, DS Figure 2 R21. Sets the internal analog bias and
    # therefore the 950-1050 mV MDI output amplitude - a 5 % part here moves
    # the transmit amplitude, so the 1 % tolerance is functional, not habit.
    sh.add_component(S_R_12K4, "R30", "12.4k 1% 0805", at=(114.3, 215.9),
                     footprint=F_R0805)
    sh.wire_pins("R30", {"1": "EXRES", "2": "GND"})

    # ================================================ 25 MHz crystal group
    # DS Figure 3: crystal across XI/XO, 1 M feedback across XI-XO, 0 R in
    # the XO leg, one load cap from each crystal terminal to ground.
    # Nets: /eth/XI (U10.30, Y10.1, C30, R35) - /eth/XO (U10.31, R35, R36)
    #       - /eth/XO_XTAL (R36, Y10.3, C31).   See DEVIATIONS 2.
    sh.add_component(S_R_1M, "R35", "1M 1% 0603", at=(228.6, 165.1),
                     footprint=F_R0603)
    sh.wire_pins("R35", {"1": "XI", "2": "XO"})
    sh.add_component(S_R_0R, "R36", "0R jumper 0603", at=(228.6, 177.8),
                     footprint=F_R0603)
    sh.wire_pins("R36", {"1": "XO", "2": "XO_XTAL"})
    # Y10: symbol Reference default is "X" - the refdes below is the one
    # parts/parts.json assigns, and constraints.json's eth_xtal group and
    # Y10<->J1 25 mm separation both key on it.
    sh.add_component(S_Y10, "Y10", "25MHz 18pF CL crystal",
                     at=(271.78, 177.8), footprint=F_Y10,
                     expect={"1": "OSC1", "2": "GND", "3": "OSC2",
                             "4": "GND"})
    sh.wire_pins("Y10", {"1": "XI", "3": "XO_XTAL", "2": "GND", "4": "GND"})
    # 27 pF NP0 = 2 x (CL 18 pF - ~4.5 pF stray). Expect to trim on proto 1.
    sh.add_component(S_C_27P, "C30", V_27P, at=(228.6, 190.5),
                     footprint=F_C0603)
    sh.wire_pins("C30", {"1": "XI", "2": "GND"})
    sh.add_component(S_C_27P, "C31", V_27P, at=(228.6, 203.2),
                     footprint=F_C0603)
    sh.wire_pins("C31", {"1": "XO_XTAL", "2": "GND"})

    # ======================================================= MDI ESD array
    # D10 TPD4E1U06, PHY side of the magnetics, at the J1 end of the pairs.
    # FITTED, not DNP (sheets.md s2.2).
    #
    # SYMBOL PIN NAMES - wired by PIN NUMBER from parts/C19829453.json
    # -------------------------------------------------------------------
    # The easyeda2kicad pull had pins 1 and 4 LABELLED backwards ("D1+" on
    # pin 1, "D2-" on pin 4) against the datasheet's 1 = D2-, 4 = D1+. The
    # netlist was always correct (wiring is by pin number), but the sheet
    # and the PDF showed ETH_TXP arriving on a pin captioned "D2-", which is
    # a trap for the layout and DFM readers. The symbol was repaired in
    # lib/aiee.kicad_sym (lib/EDITS.md edit 6); `expect` now asserts ALL SIX
    # names, so the mismatch cannot silently come back on a lib re-pull.
    # It never made an electrical difference - this is a uni-directional
    # steering array in which all four channels are identical and independent
    # (each I/O has a diode up to an internal rail and a diode down to GND;
    # the "pairs" are a drawing convention, there is no differential element
    # inside). Pairing follows the JSON's own layout note: pins 4/6 straddle
    # the NC pin (no ground stub between the two halves of a 100 ohm pair) so
    # they take TX, and pins 1/3 straddle GND and take RX.
    sh.add_component(S_D10, "D10", "TPD4E1U06 4ch 0.55pF ESD array",
                     at=(114.3, 107.95), footprint=F_D10,
                     expect={"1": "D2-", "2": "GND", "3": "D2+", "4": "D1+",
                             "5": "NC", "6": "D1-"})
    sh.wire_pins("D10", {
        "4": "ETH_TXP",     # datasheet D1+
        "6": "ETH_TXN",     # datasheet D1-
        "3": "ETH_RXP",     # datasheet D2+
        "1": "ETH_RXN",     # datasheet D2-
        "2": "GND",
        "5": "NC",          # genuine NC: "not a protected channel, not a GND"
    })

    # ================================================= SPI series + pull-ups
    # R31/R32: 22 ohm series damping. Fitted (not DNP) so the value can be
    # tuned if EMC bites. They belong at the DRIVER pin and U30 drives both
    # SCLK and MOSI, so P6 places them next to U30 even though they are
    # drawn on this sheet (sheets.md s2.2). See DEVIATIONS 1 for why the
    # hierarchical pin sits on the MCU-facing terminal.
    sh.add_component(S_R_22R, "R31", "22R 1% 0603", at=(241.3, 106.68),
                     footprint=F_R0603)
    sh.wire_pins("R31", {"1": "ETH_SCLK", "2": "SCLK_PHY"})
    sh.add_component(S_R_22R, "R32", "22R 1% 0603", at=(241.3, 119.38),
                     footprint=F_R0603)
    sh.wire_pins("R32", {"1": "ETH_MOSI", "2": "MOSI_PHY"})
    # R33 is MANDATORY, not hygiene: ESP32-S3 GPIO10 glitches low for ~60 us
    # at power-up and low = W5500 selected, so without it the PHY sees a
    # spurious frame before firmware runs. The W5500's own 50/77/112 k
    # internal pull-up is too weak to be relied on against that.
    sh.add_component(S_R_10K, "R33", "10k 1% 0603", at=(241.3, 132.08),
                     footprint=F_R0603)
    sh.wire_pins("R33", {"1": "+3V3", "2": "ETH_CSn"})
    # R34: belt and braces on RSTn (the W5500 has an internal pull-up too).
    sh.add_component(S_R_10K, "R34", "10k 1% 0603", at=(241.3, 144.78),
                     footprint=F_R0603)
    sh.wire_pins("R34", {"1": "+3V3", "2": "ETH_RSTn"})

    # ================================================== hierarchical exports
    # Free-cluster variant per sheets.md s3.3: a local label at one end and
    # the hierarchical label at the other, so the hier label joins the net by
    # WIRE GEOMETRY rather than by name merging. Column is in clear space -
    # no foreign wire runs under any of these label anchors (a label anchor
    # landing on a foreign wire silently merges the two nets, LEARNINGS
    # 2026-07-22).
    for i, (net, shape) in enumerate(INTERFACE):
        sh.hier_pin(net, shape=shape, at=(71.12, 88.9 + 7.62 * i))

    for ref, code in LCSC.items():
        sh.sch.components.get(ref).set_property("LCSC", code)
    return sh


def main(argv=None) -> int:
    out_dir = Path(argv[0]) if argv else HERE.parents[1]      # .../kicad
    try:
        sh = build()
        # project=False: the ROOT generator owns lumina-carrier.kicad_pro
        # and the merged decoupling.json (Project.save collects children).
        sch = sh.save(out_dir, project=False)
    except Exception as exc:  # noqa: BLE001  (SPEC 6: any error -> exit 2)
        print(json.dumps({"script": "gen.eth", "status": "error",
                          "error": f"{type(exc).__name__}: {exc}"}))
        return 2
    print(json.dumps({
        "script": "gen.eth", "status": "pass",
        "files": [str(sch)],
        "components": len(LCSC),
        "interface_nets": [n for n, _ in INTERFACE],
        "decoupling_associations": len(sh.decoupling),
    }, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
