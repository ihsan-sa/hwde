"""LUM-CAR-A `pwr` sheet: 48 -> 12 V buck, 12 -> 3.3 V buck, 48 V eFuse.

Refdes range (architecture/sheets.md s2.3): U20-U29, R60-R99, C50-C79,
D20-D29, L20-L29; pwr_base 300 (#PWR300+/#FLG300+). EVERY refdes here comes
from parts/parts.json, NEVER from a symbol's Reference property - three
symbols on this sheet would otherwise be annotated wrong:
  * C380359 TCC1206X5R226M250HT (22 uF 1206) has Reference "U"  -> C52/C53/
    C55/C56/C57 here.
  * C2297 KT-0805G (green LED)  has Reference "LED"             -> D21.
  * C2286 KT-0603R (red LED)    has Reference "LED"             -> D22.

WHAT THIS SHEET IS
------------------
The two most safety-critical circuits on the board:
  A. U20 SCT2A25 - ASYNCHRONOUS 100 V buck, V48_RAW -> +12V / 1.25 A.
  B. U22 TPS16630 - 60 V eFuse gating +48V_SW to the expansion connector.
     CAR-REQ-08 ("no daughter power without an explicit MCU enable") is
     implemented HERE, by R69, and by nothing else on the board.
  C. U21 TPS563201 - synchronous 12 -> 3.3 V, >= 0.5 A for the ESP32-S3.
  D. Hardware-only status LEDs off U22 PGOOD (D21) and FLT (D22).

GROUND TRUTH (SPEC s5 - no wiring, no threshold, no value from memory)
----------------------------------------------------------------------
parts/C5124114.json (SCT2A25, datasheet extract), parts/C1849461.json
(TPS16630, SLVSET9G Rev G), parts/C116592.json (TPS563201, ZHCSEL2), plus
the library pin tables printed by
`schlib.py --pins aiee:<SYMBOL> --lib ../lib/aiee.kicad_sym`.

Load-bearing facts, with the trap each one avoids:

  * U20 FB reference is **1.2 V, not 0.8 V**. R60/R61 = 270 k / 30 k gives
    1.2 x (1 + 270/30) = **12.000 V**. On an assumed 0.8 V reference the same
    part count would have produced 18 V - over the TPS563201's 17 V ceiling
    and over every 25 V output cap after derating.
  * C60 (150 pF NP0 across R60) is called NECESSARY for loop stability by the
    datasheet's own 48 -> 12 V example, not optional: a COT loop with a 300 k
    feedback string needs the zero.
  * U20 is ASYNCHRONOUS - D20 (SS510, 100 V) from SW to GND is REQUIRED. It
    dissipates more than U20 does.
  * U20 EN abs max is **6 V** and it is fed from U1's CDB on the 48 V side,
    so R62/R74 (100 k / 4.7 k) divide V48_RAW down before it ever reaches the
    pin, and double as the programmable input UVLO (see the block comment on
    the divider for the arithmetic and for the CDB-open behaviour).
  * U20 TM (6) is factory-test only - tied to GND, which the datasheet
    explicitly permits ("Connect TM to EN pin, to ground, or leave floating").
  * U22 has **no EN pin**. Its only control is SHDN (13), ACTIVE LOW, with an
    INTERNAL PULL-UP whose open-circuit voltage is 2.48-3.3 V against a 2.0 V
    enable threshold: left alone the eFuse powers up ON. **R69, the 10 k
    pull-down, is the CAR-REQ-08 fail-safe** and the only thing that makes the
    daughter rail default-off.
  * U22 MODE (12) is left OPEN (explicit no-connect, no resistor stuffed) =
    latch off after 162 ms of current limiting. Shorting it to GND would
    auto-retry into a browning-out daughter.
  * U22 IMON (14) carries R68 to GND and **no capacitor** - sec 8.3.6.
  * U22 OUT needs a Schottky to GND (D23, sec 9.4.1): V(OUT) abs max is
    **-0.3 V** and +48V_SW feeds an off-board inductive load, so the FET
    interrupting a short would drive OUT below its floor. Cathode on
    +48V_SW, anode on GND, physically adjacent to pins 18-20.
  * U22 UVLO/OVP is a THREE-resistor string IN->UVLO->OVP->GND (Figure 8-3).
    R66/R67/R73 were RE-DERIVED this session; see the block comment there.
  * SHDN and OVP are 5.5 V abs-max pins on a 57 V board. Neither may ever be
    exposed to the rail.

DEVIATIONS FROM parts/parts.json (the orchestrator must fold these back)
------------------------------------------------------------------------
  1. R66 1 M -> **620 k** (C185284), R67 12.4 k -> **10 k** (C17414, already
     on the BOM), R73 20 k -> **12 k** (C17444, JLC Basic). The BOM string
     gave UVLO rising 38.2 V (above the 37 V legal af minimum - a compliant
     PSE would have left the daughter dead) and OVP falling 57.9 V nominal,
     i.e. ~55.6 V worst case, below the 57 V legal PSE maximum. Arithmetic in
     the R66 block comment. C4328 (20 k 0805) leaves the BOM entirely.
  2. R71 330 R -> **10 k** (C25804, already on the BOM) and its top end moves
     from +3V3 to **+12V**. 330 R would have sunk 8.2 mA against a 10 mA ABS
     MAX; 1 k (the first repair) was still 10x below the datasheet's
     recommended 10-100 k R(PGOOD) window AND left D21's current set by the
     LED's 2.6-3.1 V Vf bin rather than by the resistor. See the block
     comment at R71 for the arithmetic.
  3. NEW refdes, all on LCSC lines the BOM already carries:
     R62 (100 k 0805, C149504) + R74 (4.7 k 0603, C23162) = the mandatory U20
     EN divider; C61/C62/C63 (100 nF 100 V 0805, C28233) = the local HF
     bypass the SCT2A25 and TPS16630 datasheets both require on a 48 V pin;
     D23 (SS510, C19229) = the sec 9.4.1 negative-transient Schottky on the
     eFuse output.

Rebuild (writes ../pwr.kicad_sch; the ROOT generator owns the project file):
    .venv/Scripts/python boards/lumina-carrier/kicad/gen/pwr.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import kicad_sch_api as ksa

HERE = Path(__file__).resolve()
BOARD = HERE.parents[2]
REPO = BOARD.parents[1]
sys.path.insert(0, str(REPO / ".claude" / "skills" / "ai-ee" / "scripts"))

import schlib  # noqa: E402

# kicad-sch-api resolves lib_ids through its GLOBAL cache, which never reads
# kicad/sym-lib-table (LEARNINGS 2026-07-27) - register the pulled library.
ksa.get_symbol_cache().add_library_path(BOARD / "lib" / "aiee.kicad_sym")

FP = "aiee"

# ---------------------------------------------------------------- part table
# refdes -> LCSC, from parts/parts.json except where the module docstring
# records a deviation.
LCSC = {
    "U20": "C5124114",    # SCT2A25STER 100 V asynchronous buck
    "L20": "C526032",     # 68uH 3A 140mohm
    "D20": "C19229",      # SS510C 100 V 5 A Schottky (catch diode)
    "C50": "C153036", "C51": "C153036",    # 2.2uF 100V X7R 1210 (VIN bulk)
    "C61": "C28233",      # 100nF 100V X7R 0805 (VIN HF bypass) - NEW REFDES
    "C54": "C14663",      # 100nF 50V X7R 0603 (BST-SW)
    "C52": "C380359", "C53": "C380359",    # 22uF 25V X5R 1206 (+12V out)
    "R60": "C22965",      # 270k 1% 0603 (FB top)
    "R61": "C22984",      # 30k 1% 0603 (FB bottom)
    "C60": "C107038",     # 150pF 50V NP0 0603 (feedforward across R60)
    "R62": "C149504",     # 100k 1% 0805 (EN divider top) - NEW REFDES
    "R74": "C23162",      # 4.7k 1% 0603 (EN divider bottom) - NEW REFDES

    "U21": "C116592",     # TPS563201DDCR 12 -> 3.3 V synchronous buck
    "L21": "C325964",     # 4.7uH 4A 46mohm
    "C55": "C380359",     # 22uF 25V X5R 1206 (VIN)
    "C58": "C14663",      # 100nF 50V X7R 0603 (VBST-SW)
    "C56": "C380359", "C57": "C380359",    # 22uF 25V X5R 1206 (+3V3 out)
    "R63": "C4216",       # 33k 1% 0603 (FB top)
    "R64": "C25804",      # 10k 1% 0603 (FB bottom)

    "U22": "C1849461",    # TPS16630PWPR 60 V eFuse
    "R66": "C865592",     # 620k 0.1% 25ppm 0805 thin-film (UVLO string R1)
    "R67": "C110775",     # 10k  0.1% 25ppm 0805 thin-film (UVLO string R2)
    "R73": "C865172",     # 12k  0.1% 25ppm 0805 thin-film (UVLO string R3)
    "R65": "C25810",      # 18k 1% 0603 (ILIM -> 1.0 A)
    "C59": "C57112",      # 10nF 50V X7R 0603 (dVdT)
    "R68": "C22984",      # 30k 1% 0603 (IMON scaling)
    "R69": "C25804",      # 10k 1% 0603 (SHDN pull-down) = CAR-REQ-08
    "R70": "C149504",     # 100k 1% 0805 (+48V_SW bleed)
    "C62": "C28233",      # 100nF 100V X7R 0805 (IN bypass)  - NEW REFDES
    "C63": "C28233",      # 100nF 100V X7R 0805 (OUT bypass) - NEW REFDES
    "D23": "C19229",      # SS510C 100 V 5 A Schottky OUT->GND - NEW REFDES
    "R71": "C25804",      # 10k 1% 0603 (PGOOD pull-up)     - VALUE CHANGED
    "D21": "C2297",       # KT-0805G green (power good)
    "R72": "C23138",      # 330R 1% 0603 (FLT LED series)
    "D22": "C2286",       # KT-0603R red (fault)
}

# ------------------------------------------------------------------- values
V_2U2 = "2.2uF 100V X7R 1210"
V_22U = "22uF 25V X5R 1206"
V_100N_100V = "100nF 100V X7R 0805"
V_100N = "100nF 50V X7R 0603"
V_10N = "10nF 50V X7R 0603"
V_150P = "150pF 50V NP0 0603"
V_270K = "270k 1% 0603"
V_30K = "30k 1% 0603"
V_33K = "33k 1% 0603"
V_10K = "10k 1% 0603"
V_18K = "18k 1% 0603"
V_4K7 = "4.7k 1% 0603"
V_330R = "330R 1% 0603"
V_100K = "100k 1% 0805"
V_620K = "620k 0.1% 0805"
V_10K_0805 = "10k 0.1% 0805"
V_12K = "12k 0.1% 0805"

# --------------------------------------------------------------- footprints
R0603 = f"{FP}:R0603"
R0805 = f"{FP}:R0805"
C0603 = f"{FP}:C0603"
C0805 = f"{FP}:C0805"
C1206 = f"{FP}:C1206"
C1210 = f"{FP}:C1210"

# ------------------------------------------------------------------ symbols
# Chip R/C bodies are interchangeable; the VALUE field carries the real value
# and the LCSC property carries the real part (poe.py established this).
SYM_R0603 = f"{FP}:0603WAF1802T5E"      # generic 0603 resistor body
SYM_R0805 = f"{FP}:0805W8F1242T5E"      # generic 0805 resistor body
SYM_R100K = f"{FP}:0805W8F1003T5E_C149504"
SYM_R4K7 = f"{FP}:0603WAF4701T5E"
SYM_R330 = f"{FP}:0603WAF3300T5E"
SYM_R10K = f"{FP}:0603WAF1002T5E"
SYM_R30K = f"{FP}:0603WAF3002T5E"
SYM_R33K = f"{FP}:0603WAF3302T5E"
SYM_R270K = f"{FP}:0603WAF2703T5E"
SYM_C2U2 = f"{FP}:FS32X225K101EGG"
SYM_C22U = f"{FP}:TCC1206X5R226M250HT"
SYM_C100N_100V = f"{FP}:CL21B104KCFNNNE"
SYM_C100N = f"{FP}:CC0603KRX7R9BB104"
SYM_C10N = f"{FP}:0603B103K500NT"
SYM_C150P = f"{FP}:CC0603JRNPO9BN151"


def _global_rail(sh: schlib.Sheet, net: str, at, sym: str,
                 flag: bool = True) -> None:
    """A rail cluster whose power SYMBOL is renamed to `net`.

    Same helper as poe.py: sheets.md P4 note 2 wants +48V_SW / V48_RAW as
    GLOBAL bare nets, but KiCad ships no power symbol with those names, and a
    local label alone would yield /pwr/+48V_SW - which constraints.json.power
    and .voltages both name bare, so netlist_audit would raise missing_net at
    ERROR severity. Place power:+48V and rewrite its Value, which is what
    KiCad 6+ derives a power symbol's net name from.
    """
    sh.power_flag(net, at=at, sym=sym, flag=flag)
    ref = f"#PWR{sh._pwr_i:02d}"          # power_flag just allocated this one
    # NB: `.value = `, not set_property("Value", ...) - the latter is a silent
    # no-op for the Value field in kicad-sch-api 0.5.6.
    sh.sch.components.get(ref).value = net


def build() -> schlib.Sheet:
    sh = schlib.Sheet("pwr", title="LUM-CAR-A: power (48->12, 12->3V3, eFuse)",
                      paper="A3", date="2026-07-28", company="ai-ee",
                      pwr_base=300)

    # =====================================================================
    # A.  U20 - SCT2A25 asynchronous buck, V48_RAW -> +12V @ 1.25 A
    # =====================================================================
    # Datasheet Table 2's own 48 V -> 12 V / 2 A design: L = 68 uH,
    # 2 x 22 uF out, 2 x 2.2 uF / 100 V in, 150 pF feedforward, SS510 catch
    # diode, 300 kHz fixed (no RT pin).
    #
    # PIN 6 (TM) -> GND: factory test only. The datasheet allows EN, GND or
    # floating; GND is the deterministic choice and cannot interact with the
    # EN network.
    # PIN 2 (NC) -> explicit no-connect: "Not Connection" in the pinout.
    # PIN 9 (thermal pad) -> GND: electrically bonded to pin 8 inside the
    # package; constraints.json.thermal already demands >= 9 vias on U20.
    sh.place_ic_with_decoupling(
        "U20", f"{FP}:SCT2A25STER", "SCT2A25STER",
        at=(101.60, 63.50),
        pins={"1": "FB48",       # FB, regulated to 1.2 V (NOT 0.8 V)
              "2": "NC",         # datasheet: "Not Connection"
              "3": "V48_RAW",    # VIN, 5.5-100 V rec / 110 V abs
              "4": "BST",        # bootstrap, C54 to SW
              "5": "SW",         # switch node, -1 V negative abs-max floor
              "6": "GND",        # TM: factory test, tied to GND
              "7": "CDB",        # EN, 6 V abs max - see the divider below
              "8": "GND",
              "9": "GND"},       # thermal pad == GND
        footprint=f"{FP}:SOIC-8-1EP_3.9x4.9mm_P1.27mm_EP2.41x3.3mm",
        expect={"1": "FB", "2": "NC", "3": "VIN", "4": "BST", "5": "SW",
                "6": "TM", "7": "EN", "8": "GND", "9": "PAD"},
        decoupling=[
            {"cap": "C50", "pin": "3", "rail": "V48_RAW", "value": V_2U2,
             "lib_id": SYM_C2U2, "footprint": C1210},
            {"cap": "C51", "pin": "3", "rail": "V48_RAW", "value": V_2U2,
             "lib_id": SYM_C2U2, "footprint": C1210},
            # NEW REFDES on an existing BOM line (C28233): the datasheet
            # "strongly recommends" a small 0.1 uF right at VIN/GND on top of
            # the bulk. 100 V part - a 50 V 0603 must never sit on this rail.
            {"cap": "C61", "pin": "3", "rail": "V48_RAW",
             "value": V_100N_100V, "lib_id": SYM_C100N_100V,
             "footprint": C0805},
        ],
        caps_at=(38.10, 114.30), caps_dx=38.10)

    # ------------------------------------------------- U20 EN / input UVLO --
    # U1's CDB (open drain, referenced to RTN == board GND on this
    # non-isolated PD) is pulled low only while the PD is in inrush current
    # limiting, and is high-Z otherwise. EN floats HIGH inside the SCT2A25,
    # so the pin cannot simply be tied to CDB: it would sit at the internal
    # pull-up voltage, and if CDB were ever driven from the rail it would
    # exceed the 6 V EN ABS MAX.
    #
    # R62/R74 = 100 k / 4.7 k, from V48_RAW to GND, with EN + CDB on the tap:
    #   EN(V48_RAW)      = V48_RAW x 4.7/104.7 = V48_RAW x 0.04489
    #   VIN_rise         = 1.25 x (R62+R74)/R74 = 1.25 x 22.277 = 27.8 V
    #   VIN_hys          = 2.1 uA x R62 = 0.21 V  ->  VIN_fall = 27.6 V
    #   EN at 57 V (max legal PoE)      = 2.56 V   (2.3x under the 6 V max)
    #   EN at 93.6 V (SMBJ58A clamp)    = 4.20 V   (still under 6 V)
    #   EN at 37 V (min legal af PD in) = 1.66 V   (> 1.25 V -> enabled)
    #   R62 dissipation at 57 V         = 29.6 mW  (0805, 125 mW)
    # 27.8 V sits BELOW the PD controller's ~30 V dropout on purpose: the
    # sequencing authority is U1, not this divider, so the buck must never be
    # the part that decides to drop out first.
    #
    # WITH CDB OPEN OR ABSENT the divider alone drives EN, so the converter
    # turns ON once V48_RAW passes 27.8 V. That is the intended fail state -
    # +12V/+3V3 are carrier-internal rails, and the DAUGHTER rail's default-off
    # requirement (CAR-REQ-08) is enforced by R69 on U22, not here.
    # CDB pulling low sinks V48_RAW/R62 = 0.57 mA max, inside U1's 2 mA
    # recommended (5 mA abs max) sink and far below its 0.5 V max VOL.
    sh.add_component(SYM_R100K, "R62", V_100K, at=(38.10, 38.10),
                     footprint=R0805)
    sh.wire_pins("R62", {"1": "V48_RAW", "2": "CDB"})
    sh.add_component(SYM_R4K7, "R74", V_4K7, at=(38.10, 63.50),
                     footprint=R0603)
    sh.wire_pins("R74", {"1": "CDB", "2": "GND"})

    # ------------------------------------------------ U20 power stage -------
    # BST-SW 0.1 uF, X5R or better, >= 10 V: mandatory ("must be connected").
    sh.add_component(SYM_C100N, "C54", V_100N, at=(165.10, 25.40),
                     footprint=C0603)
    sh.wire_pins("C54", {"1": "BST", "2": "SW"})
    sh.add_component(f"{FP}:FXL1360-680-M", "L20", "68uH 3A 140mohm inductor",
                     at=(165.10, 50.80),
                     footprint=f"{FP}:IND-SMD_L12.6-W13.5")
    sh.wire_pins("L20", {"1": "SW", "2": "+12V"})
    # ASYNCHRONOUS buck: the catch diode is not optional. SS510 = 100 V / 5 A
    # against a 57 V rail. Pin 1 = A (to GND), pin 2 = K (to SW).
    sh.add_component(f"{FP}:SS510", "D20", "SS510C 100V 5A Schottky SMC",
                     at=(165.10, 76.20),
                     footprint=f"{FP}:SMC_L7.1-W6.2-LS8.1-R-RD",
                     expect={"1": "A", "2": "K"})
    sh.wire_pins("D20", {"1": "GND", "2": "SW"})
    for ref, y in (("C52", 25.40), ("C53", 38.10)):
        sh.add_component(SYM_C22U, ref, V_22U, at=(203.20, y),
                         footprint=C1206)
        sh.wire_pins(ref, {"1": "+12V", "2": "GND"})

    # --------------------------------------------- U20 feedback divider -----
    # VOUT = VREF x (1 + R60/R61) with VREF = 1.2 V:
    #   270k / 30k -> 1.2 x 10.000 = 12.000 V exactly.
    # (The datasheet's own pair is 271k/30k = 12.04 V; 271 k is ZERO STOCK on
    # LCSC in every package, and 270 k is closer to nominal anyway.)
    # C60 is the loop-stability feedforward the datasheet ships with this
    # exact design - it belongs ACROSS R60, not from FB to GND.
    sh.add_component(SYM_R270K, "R60", V_270K, at=(203.20, 63.50),
                     footprint=R0603)
    sh.wire_pins("R60", {"1": "+12V", "2": "FB48"})
    sh.add_component(SYM_C150P, "C60", V_150P, at=(203.20, 76.20),
                     footprint=C0603)
    sh.wire_pins("C60", {"1": "+12V", "2": "FB48"})
    sh.add_component(SYM_R30K, "R61", V_30K, at=(203.20, 88.90),
                     footprint=R0603)
    sh.wire_pins("R61", {"1": "FB48", "2": "GND"})

    # =====================================================================
    # C.  U21 - TPS563201, +12V -> +3V3 @ >= 0.5 A
    # =====================================================================
    # EN (5) is tied straight to VIN: active high, VIH 1.6 V, abs max 19 V =
    # the same ceiling as VIN itself, so EN can never be the pin that fails
    # first. The internal 225-900 k pull-down makes a floating EN a dead rail,
    # and its 3x spread makes any resistor-programmed threshold meaningless -
    # the converter's own 4.5 V UVLO is the honest gate. The +3V3 rail must be
    # available whenever +12V is, because the ESP32-S3 module needs a supply
    # capable of >= 500 mA (355 mA Wi-Fi TX burst) with no enable handshake.
    sh.place_ic_with_decoupling(
        "U21", f"{FP}:TPS563201DDCR", "TPS563201DDCR",
        at=(317.50, 63.50),
        pins={"1": "GND",
              "2": "SW33",
              "3": "+12V",      # VIN, 4.5-17 V (12 V = 71 % of ceiling)
              "4": "FB33",      # VFB, 768 mV reference (this one was right)
              "5": "+12V",      # EN, active high
              "6": "BST33"},
        footprint=f"{FP}:SOT-23-6_L2.9-W1.6-P0.95-LS2.8-BR",
        expect={"1": "GND", "2": "SW", "3": "VIN", "4": "VFB", "5": "EN",
                "6": "VBST"},
        decoupling=[
            {"cap": "C55", "pin": "3", "rail": "+12V", "value": V_22U,
             "lib_id": SYM_C22U, "footprint": C1206},
        ],
        caps_at=(254.00, 25.40))
    # 0.1 uF VBST-SW: "must be connected ... for proper operation".
    sh.add_component(SYM_C100N, "C58", V_100N, at=(254.00, 50.80),
                     footprint=C0603)
    sh.wire_pins("C58", {"1": "BST33", "2": "SW33"})
    # L21 is the 4.7 uH end of the datasheet's 2.2 uH typ / 4.7 uH max window
    # for 3.3 V - legal, and deliberate: 46 mohm and 4.5 A saturation against a
    # 1.0 A design rail with 1.21 A ms-scale peaks. Higher L = lower ripple and
    # a slower load-step response; D-CAP2 needs no compensation change for it.
    sh.add_component(f"{FP}:SLO0530H4R7MTT", "L21",
                     "4.7uH 4A 46mohm inductor", at=(381.00, 38.10),
                     footprint=f"{FP}:IND-SMD_L5.4-W5.2")
    sh.wire_pins("L21", {"1": "SW33", "2": "+3V3"})
    # COUT 20-68 uF required; 2 x 22 uF = 44 uF nominal, ~25 uF after DC bias.
    for ref, y in (("C56", 76.20), ("C57", 101.60)):
        sh.add_component(SYM_C22U, ref, V_22U, at=(381.00, y),
                         footprint=C1206)
        sh.wire_pins(ref, {"1": "+3V3", "2": "GND"})
    # VOUT = 0.768 x (1 + R63/R64) = 0.768 x 4.3 = 3.302 V.
    # (Datasheet Table 2 lists 33.2k/10.0k = 3.318 V; 33 k is JLC Basic and
    # 3.302 V is closer to nominal, so the BOM pair is kept.)
    sh.add_component(SYM_R33K, "R63", V_33K, at=(254.00, 76.20),
                     footprint=R0603)
    sh.wire_pins("R63", {"1": "+3V3", "2": "FB33"})
    sh.add_component(SYM_R10K, "R64", V_10K, at=(254.00, 101.60),
                     footprint=R0603)
    sh.wire_pins("R64", {"1": "FB33", "2": "GND"})

    # =====================================================================
    # B.  U22 - TPS16630 eFuse, V48_RAW -> +48V_SW.  CAR-REQ-08 LIVES HERE.
    # =====================================================================
    # Pins 1/2/3 (IN) and 18/19/20 (OUT) are parallel power pins - "Do not
    # leave any of the IN and OUT pins un-connected" - and P_IN (6) must be
    # tied directly to IN. Pins 4/5/17 are N.C. Pin 21 is the PowerPAD: GND
    # for heat, but the datasheet insists it must NOT be the only GND
    # connection, which pin 9 satisfies.
    sh.place_ic_with_decoupling(
        "U22", f"{FP}:TPS16630PWPR", "TPS16630PWPR",
        at=(139.70, 203.20),
        pins={"1": "V48_RAW", "2": "V48_RAW", "3": "V48_RAW",
              "4": "NC", "5": "NC",
              "6": "V48_RAW",     # P_IN: "Always connect P_IN to IN directly"
              "7": "UVLO",
              "8": "OVP",         # 5.5 V ABS MAX - never sees the rail
              "9": "GND",
              "10": "DVDT",
              "11": "ILIM",
              # MODE OPEN = latch off after 162 ms of current limiting. An
              # explicit no-connect, NOT an unstuffed resistor footprint:
              # shorting MODE to GND would auto-retry every 648 ms into a
              # daughter that is browning out.
              "12": "NC",
              "13": "ENABLE",     # SHDN, ACTIVE LOW, 5.5 V abs max
              "14": "IMON",       # no bypass capacitor, ever
              "15": "FAULT",      # open drain, active low
              "16": "PGOOD",      # open drain, active high
              "17": "NC",
              "18": "+48V_SW", "19": "+48V_SW", "20": "+48V_SW",
              "21": "GND"},       # PowerPAD
        footprint=f"{FP}:HTSSOP-20-1EP_4.4x6.5mm_P0.65mm_EP3.4x6.5mm_"
                  "Mask2.96x2.96mm_ThermalVias",
        expect={"1": "IN", "2": "IN", "3": "IN", "4": "N.C", "5": "N.C",
                "6": "P_IN", "7": "UVLO", "8": "OVP", "9": "GND",
                "10": "dVdT", "11": "ILIM", "12": "MODE", "13": "SHDN",
                "14": "IMON", "15": "FLT", "16": "PGOOD", "17": "N.C",
                "18": "OUT", "19": "OUT", "20": "OUT", "21": "EP"},
        decoupling=[
            # Recommended Operating Conditions give 0.1 uF as the MINIMUM
            # external capacitance on IN/P_IN and on OUT. The >= 1 uF the
            # surge note asks for is already present upstream as poe's
            # 4 x 10 uF CBULK on the same V48_RAW node.
            {"cap": "C62", "pin": "1", "rail": "V48_RAW",
             "value": V_100N_100V, "lib_id": SYM_C100N_100V,
             "footprint": C0805},
            {"cap": "C63", "pin": "18", "rail": "+48V_SW",
             "value": V_100N_100V, "lib_id": SYM_C100N_100V,
             "footprint": C0805},
        ],
        caps_at=(76.20, 273.05), caps_dx=63.50)

    # ------------------------------------------------- UVLO / OVP string ----
    # THREE resistors in series, IN -> R66 -> UVLO -> R67 -> OVP -> R73 -> GND
    # (Figure 8-3).  Both comparators share the same reference:
    #   V(UVLOR) rising  = 1.200 x (R66+R67+R73)/(R67+R73)
    #   V(OVPR)  rising  = 1.200 x (R66+R67+R73)/R73
    #   falling  = the same expression with 1.122 V (fixed 0.935 ratio)
    #
    # WITH R66/R67/R73 = 620 k / 10 k / 12 k  (sum 642 k):
    #   UVLO rising  = 1.200 x 642/22   = 1.2 x 29.182 = 35.02 V
    #   UVLO falling = 1.122 x 29.182                  = 32.74 V
    #   OVP  rising  = 1.200 x 642/12   = 1.2 x 53.500 = 64.20 V
    #   OVP  falling = 1.122 x 53.500                  = 60.03 V
    #   divider current = 74.8 uA at 48 V (499x the 150 nA pin leakage, far
    #   over the datasheet's >= 20x rule); R66 burns 4.9 mW at 57 V.
    #
    # WORST CASE (+/-1 % resistors x the datasheet's own threshold limits -
    # rising 1.176/1.224 V, falling 1.09/1.15 V, NOT a symmetric +/-2 %):
    #   UVLO rising, worst HIGH = 1.224 x (1.01x620k + 0.99x22k)/(0.99x22k)
    #                           = 1.224 x 29.751 = 36.42 V
    #       -> still below 37 V, the minimum legal PD input voltage for the af
    #          build, so even a worst-case unit enables on a fully compliant
    #          PSE. The BOM's 1M/12.4k/20k gave 38.2 V NOMINAL and would have
    #          left the daughter dead on a legal supply.
    #   OVP falling, worst LOW   = 1.090 x (0.9802 x 52.5 + 1) = 57.18 V
    #       -> above 57 V, the maximum legal PSE output, so a legal rail always
    #          re-enables after an overvoltage event. The BOM string's 57.9 V
    #          nominal falling threshold landed near 55.6 V worst case and
    #          would have latched the daughter off against a LEGAL 57 V PSE.
    #   OVP rising, worst HIGH   = 1.224 x (1.0202 x 52.5 + 1) = 66.78 V
    #       -> under the 67 V IN/UVLO abs max, and backstopped anyway: D1
    #          (SMBJ58A) breaks down at 64.4 V minimum, so the TVS conducts
    #          before a worst-case unit could reach its own OVP threshold.
    # These two requirements pull in opposite directions (raising OVP falling
    # raises OVP rising by the same 0.935 ratio) and the feasible window for
    # (R66+R67)/R73 is only 52.33..52.68; 12 k puts it at 52.500, mid-window.
    #
    # UVLO must never float (sec 8.3.2) - it is fed by this string, always.
    # OVP is a 4 V rec / 5.5 V abs-max pin: it only ever sees ~1.2 V here, and
    # R67/R73 are 0805 so that an open R66 cannot expose them to the rail.
    sh.add_component(SYM_R0805, "R66", V_620K, at=(44.45, 165.10),
                     footprint=R0805)
    sh.wire_pins("R66", {"1": "V48_RAW", "2": "UVLO"})
    sh.add_component(SYM_R0805, "R67", V_10K_0805, at=(44.45, 177.80),
                     footprint=R0805)
    sh.wire_pins("R67", {"1": "UVLO", "2": "OVP"})
    sh.add_component(SYM_R0805, "R73", V_12K, at=(44.45, 190.50),
                     footprint=R0805)
    sh.wire_pins("R73", {"1": "OVP", "2": "GND"})

    # ------------------------------------------------------------- ILIM ----
    # R(ILIM) = 18 / I(OL) with R in kohm and I in A (Eq 6/10), so 18 k = a
    # 1.0 A overload limit - TI's own worked 1 A example. The ICD's sustained
    # +48V_SW rating is 0.50 A, so 1.0 A is 2x headroom; the 49.9 k the BOM
    # first carried would have limited at 0.36 A and tripped in normal use.
    # Recommended range 3-30 kohm, and UL 2367 needs >= 3 kohm.
    sh.add_component(SYM_R0603, "R65", V_18K, at=(44.45, 215.90),
                     footprint=R0603)
    sh.wire_pins("R65", {"1": "ILIM", "2": "GND"})

    # ------------------------------------------------------------- dVdT ----
    # 10 nF = the datasheet MINIMUM when the pin is used (the timing table is
    # only specified for C >= 10 nF; 1 nF would be out of spec).
    #   t(dVdT)   = 20.8e3 x 48 V x 10 nF   = 10.0 ms output ramp
    #   I(INRUSH) = C(OUT) x V(IN)/t(dVdT)  = 0.1 uF x 48 / 10 ms = 0.5 mA
    # i.e. the carrier contributes essentially no inrush of its own - the
    # daughter owns its inrush ramp, exactly as blocks.md requires.
    sh.add_component(SYM_C10N, "C59", V_10N, at=(44.45, 228.60),
                     footprint=C0603)
    sh.wire_pins("C59", {"1": "DVDT", "2": "GND"})

    # ------------------------------------------------------------- IMON ----
    # V(IMON) = I(OUT) x 27.9 uA/A x R68 -> 0.837 V at the 1.0 A limit and
    # 0.209 V at the af sustained 0.25 A, which lands the whole eFuse range
    # inside the ESP32-S3 ADC1 0 dB window where linearity is best.
    # NO CAPACITOR on this node (sec 8.3.6) - a bypass delays the reading.
    sh.add_component(SYM_R30K, "R68", V_30K, at=(44.45, 241.30),
                     footprint=R0603)
    sh.wire_pins("R68", {"1": "IMON", "2": "GND"})

    # ================= THE CAR-REQ-08 FAIL-SAFE - DO NOT REMOVE =============
    # SHDN is ACTIVE LOW with an INTERNAL PULL-UP: open-circuit 2.48 V min /
    # 2.7 V typ / 3.3 V max at 0.1 uA, against V(SHUTR) = 2.0 V rising. With
    # nothing fitted the eFuse therefore powers up ON and 48 V appears on the
    # expansion connector with no MCU present - the exact failure CAR-REQ-08
    # forbids. R69 holds SHDN at I(SHDN,leak) x 10 k = 10 uA x 10 k = 0.1 V,
    # 8x below the 0.8 V V(SHUTF) shutdown threshold, and sinks far more than
    # the 10 uA the datasheet demands of a pull-down.
    # To ENABLE, the ESP32-S3 GPIO drives /ENABLE high: 3.3 V >= the 2.0 V
    # threshold, 0.33 mA through R69, and 3.3 V is under the 5.5 V SHDN abs
    # max. SHDN must NEVER see the 48 V rail.
    r69 = sh.add_component(SYM_R10K, "R69", V_10K, at=(44.45, 254.00),
                           footprint=R0603)
    sh.wire_pins("R69", {"1": "ENABLE", "2": "GND"})
    r69.set_property("Note", "CAR-REQ-08 FAIL-SAFE - eFuse OFF with no MCU")
    # ========================================================================

    # ------------------------------------------------------------- bleed ----
    # ICD requirement: de-energise the connector's 48 V pins whenever ENABLE
    # is low. 100 k -> 0.475 mA / 22.6 mW at 47.5 V, 0805 because 0603 chip
    # resistors are only 75 V working parts.
    sh.add_component(SYM_R100K, "R70", V_100K, at=(215.90, 165.10),
                     footprint=R0805)
    sh.wire_pins("R70", {"1": "+48V_SW", "2": "GND"})

    # ------------------------------------------- negative-transient clamp ---
    # Sec 9.4.1: "TI recommends a Schottky diode from OUT to GND, placed
    # physically close to the OUT and GND pins, to absorb the negative spike
    # produced by output INDUCTANCE when the FET interrupts a short."
    # +48V_SW leaves the board through J3 pins 1/3/5 into a daughter that
    # holds a ~2800 uF bank behind its own harness - an unambiguously
    # inductive load - and V(OUT) abs max is only -0.3 V. Without this diode
    # a single downstream short recoils the OUT pins below their abs max.
    # SS510 (same 100 V / 5 A part as the buck's catch diode D20, already a
    # BOM line): CATHODE to +48V_SW, ANODE to GND, so it is reverse-biased
    # (57 V max against a 100 V rating) in every normal state and only
    # conducts when OUT swings negative.
    # PLACEMENT IS PART OF THE FIX - the loop OUT -> D23 -> GND must be
    # short, so P6 must keep D23 adjacent to U22 pins 18-20/9/21.
    d23 = sh.add_component(f"{FP}:SS510", "D23", "SS510C 100V 5A Schottky SMC",
                           at=(190.50, 152.40),
                           footprint=f"{FP}:SMC_L7.1-W6.2-LS8.1-R-RD",
                           expect={"1": "A", "2": "K"})
    sh.wire_pins("D23", {"1": "GND", "2": "+48V_SW"})
    d23.set_property("Note", "Neg-transient clamp - keep at U22 pins 18-20")

    # ---------------------------------------------------- status LEDs -------
    # D21, POWER GOOD (green). PGOOD is open drain but ACTIVE HIGH: it SINKS
    # when the FET is off and is high-Z when the rail is good, so the LED
    # cannot hang off it as a low-side load - it would light on FAILURE. The
    # only correct-polarity topology without an inverting transistor is
    # rail -> R71 -> PGOOD node -> D21 -> GND, in which the PULL-UP IS the
    # LED's current source. That is why the pull-up value and the LED current
    # cannot be separated by adding a second resistor: any ballast in that
    # string is simply in series with R71.
    #
    # They are decoupled by the RAIL instead. R71 = 10 k to **+12V**, not
    # 1 k to +3V3:
    #   * R(PGOOD) = 10 k is now inside the datasheet's recommended
    #     10-100 k window (sec 9.2.2.3.1); the old 1 k was 10x outside it.
    #   * PGOOD is rated 60 V and sec 8.3.8 explicitly allows pulling it to
    #     IN or OUT through a resistor, so a 12 V pull-up is in spec.
    #   * D21 (C2297 green) has Vf 2.6-3.1 V. Off 3.3 V the headroom is
    #     0.2-0.7 V, so the LED current was set by the Vf BIN, not by the
    #     resistor: 0.70 mA best bin down to 0.20 mA worst, a 3.5x spread on
    #     an indicator CAR-REQ-09 requires to be visible from outside the
    #     enclosure. Off 12 V the resistor dominates:
    #       I = (12 - Vf)/10k = 0.94 mA (Vf 2.6) .. 0.89 mA (Vf 3.1) = +/-3 %
    #     i.e. brighter than the old TYPICAL and no longer bin-dependent.
    #   rail good : PGOOD high-Z, 0.92 mA through D21, LIT
    #   rail off  : PGOOD sinks, node = 12 x 130/10130 = 0.15 V worst case
    #               (R(PGOOD,pd) 36-130 ohm), LED hard DARK, and the sink is
    #               1.18 mA - 8.5x under the 10 mA PGOOD ABS MAX.
    # Hardware-driven, no GPIO.
    sh.add_component(SYM_R10K, "R71", V_10K, at=(215.90, 190.50),
                     footprint=R0603)
    sh.wire_pins("R71", {"1": "+12V", "2": "PGOOD"})
    sh.add_component(f"{FP}:0805G", "D21", "Green LED 0805",
                     at=(215.90, 203.20), footprint=f"{FP}:LED0805-R-RD",
                     expect={"1": "A", "2": "K"})
    sh.wire_pins("D21", {"1": "PGOOD", "2": "GND"})

    # D22, FAULT (red). FLT is open drain ACTIVE LOW, so the natural low-side
    # topology has the right polarity: +3V3 -> R72 -> D22 -> FLT.
    #   fault : FLT sinks, 3.9 mA through the LED (+0.33 mA through the
    #           expansion sheet's R132 pull-up) = 4.2 mA, under the 10 mA max
    #   idle  : R132 holds /FAULT at +3V3, no voltage across the string, DARK
    # The /FAULT pull-up itself is R132 on the `expansion` sheet (sheets.md
    # s1.2); it is NOT duplicated here, and without it this LED string alone
    # would leave /FAULT floating around 1.7 V. Hardware-driven, no GPIO.
    sh.add_component(SYM_R330, "R72", V_330R, at=(215.90, 228.60),
                     footprint=R0603)
    sh.wire_pins("R72", {"1": "+3V3", "2": "FLT_LED"})
    sh.add_component(f"{FP}:KT-0603R", "D22", "Red LED 0603",
                     at=(215.90, 241.30),
                     footprint=f"{FP}:LED-SMD_L1.6-W0.8-R-RD",
                     expect={"1": "A", "2": "K"})
    sh.wire_pins("D22", {"1": "FLT_LED", "2": "FAULT"})

    # =====================================================================
    # rails
    # =====================================================================
    # sheets.md s1.1: this sheet OWNS the PWR_FLAGs for +48V_SW, +12V and
    # +3V3 (every one of them is formed by a passive pin - an eFuse output or
    # an inductor - so ERC would otherwise call all three undriven). GND and
    # V48_RAW are flagged on `poe`, so here they are consuming power symbols
    # with flag=False.
    _global_rail(sh, "GND", (266.70, 165.10), "power:GND", flag=False)
    _global_rail(sh, "V48_RAW", (266.70, 177.80), "power:+48V", flag=False)
    _global_rail(sh, "+48V_SW", (266.70, 190.50), "power:+48V", flag=True)
    _global_rail(sh, "+12V", (266.70, 203.20), "power:+12V", flag=True)
    _global_rail(sh, "+3V3", (266.70, 215.90), "power:+3V3", flag=True)

    # =====================================================================
    # sheet interface
    # =====================================================================
    # Free-cluster variant (sheets.md s3 note 3): local label + hierarchical
    # label on one stub, so the hier label joins the net by wire geometry.
    # Shape follows poe.py's rule - `passive` for nets another sheet drives,
    # `output` only where THIS sheet is the driver.
    #
    # CDB is the 4th pin and is NOT in this sheet's briefed interface list.
    # sheets.md s1.3 files /poe/CDB as poe-INTERNAL while naming U20's EN (on
    # THIS sheet) as a member, which cannot both be true; poe.py has already
    # resolved it the same way by exposing CDB as an output. The root MUST
    # therefore carry "CDB" in BOTH sheets' add_sheet(nets=...) and the final
    # net is /CDB, not /poe/CDB.
    for i, (net, shape) in enumerate([
            ("CDB", "passive"),      # driven by U1 (poe), consumed by U20 EN
            ("ENABLE", "passive"),   # driven by U30 GPIO36 (mcu)
            ("FAULT", "output"),     # driven HERE by U22 FLT (open drain)
            ("IMON", "output")]):    # driven HERE by U22 IMON
        sh.hier_pin(net, shape=shape, at=(330.20, 165.10 + i * 12.70))

    for ref, code in LCSC.items():
        sh.sch.components.get(ref).set_property("LCSC", code)
    # R66/R67/R73 are the only parts here mounted on a BORROWED symbol body
    # (the generic 0805 resistor, which carries 0805W8F1242T5E / C30908 in its
    # own fields). Overwrite the inherited identity fields so the schematic
    # does not name the wrong part - bom_cpl takes parts.json first, but a
    # human reading the sheet or the embedded lib_symbols would be misled.
    for ref, mpn, brand in (
            ("R66", "RT0805BRD07620KL", "YAGEO"),
            ("R67", "RT0805BRD0710KL", "YAGEO"),
            ("R73", "RT0805BRD0712KL", "YAGEO")):
        c = sh.sch.components.get(ref)
        c.set_property("LCSC Part", LCSC[ref])
        c.set_property("MPN", mpn)
        c.set_property("Manufacturer", brand)
    return sh


def main(argv=None) -> int:
    # Default out dir is kicad/, and project=False: the ROOT generator owns
    # <root>.kicad_pro, this sheet must never write one.
    out_dir = Path(argv[0]) if argv else BOARD / "kicad"
    try:
        sh = build()
        path = sh.save(out_dir, project=False)
    except Exception as exc:  # noqa: BLE001  (SPEC 6: any error -> exit 2)
        print(json.dumps({"script": "gen.pwr", "status": "error",
                          "error": f"{type(exc).__name__}: {exc}"}))
        return 2
    print(json.dumps({
        "script": "gen.pwr", "status": "pass",
        "sheet": str(path),
        "components": len(list(sh.sch.components)),
        "hier_pins": sorted(sh.hier_pins),
        "decoupling_associations": len(sh.decoupling),
    }, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
