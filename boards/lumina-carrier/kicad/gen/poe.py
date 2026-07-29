"""LUM-CAR-A `poe` sheet: RJ45 PoE magjack -> TVS -> TPS2378 PD interface.

Refdes range (architecture/sheets.md s2.1): J1, U1-U9, R1-R19, C1-C19, D1-D9;
pwr_base 100 (#PWR100+/#FLG100+). EVERY refdes here is taken from
parts/parts.json, never from a symbol's Reference property - the EasyEDA pull
defaults J1's prefix to "RJ" and U1's is fine but the rule is uniform.

WHAT THIS SHEET IS
------------------
A NON-ISOLATED 802.3af PD front end. The magjack rectifies internally, so the
board sees one positive node `V48_RAW` (J1 P9) and one raw negative `V48_RTN`
(J1 P10). U1 switches the RETURN: its RTN pin (5) is board `GND`
(architecture/power_tree.md s1: "RTN = board GND"), and its VSS pin (4) plus
the exposed pad are `V48_RTN`, which sits up to 57 V BELOW GND while the
hot-swap FET is off. Nothing outside this sheet may touch `V48_RTN`.

GROUND TRUTH used for every connection (SPEC s5 - no wiring from memory)
-----------------------------------------------------------------------
parts/C337500.json (TPS2378, TI SLVSB99C) and parts/C91754.json (HanRun
HY931147C, datasheet schematic traced pin-by-pin), plus the library pin tables
printed by `schlib.py --pins aiee:<SYMBOL> --lib ../lib/aiee.kicad_sym`.

Load-bearing facts, with the trap each one avoids:
  * U1 exposed pad (9) is VSS, NOT RTN ("The PowerPAD is internally connected
    to VSS", sec 7.3.8/7.3.9). Padding it to RTN destroys the part.
  * U1 pin 8 APD is an INPUT and the datasheet says "If not used, connect APD
    to RTN". Its sink current is 1-3 uA, so a floating APD drifts above the
    1.5 V threshold and turns the pass MOSFET off. Tied through R9 (0 R) so a
    TPS2379 second source - whose pin 8 is GATE and must NOT see RTN - stays
    buildable by depopulating one link.
  * CDB (6) and T2P (7) are open-drain and referenced to RTN, not VSS. On this
    non-isolated board RTN IS board GND, so no optocoupler is needed; R4 pulls
    T2P up to +3V3 and R5 is the series limiter, so the node can never leave
    the 0-3.3 V window a GPIO can take.
  * RCLS (R3) = 90.9 R = Class 3 / 802.3af for build 1. 63.4 R = Class 4 /
    802.3at is the ENTIRE D-01 upgrade and is a VALUE SWAP on this same pad
    pair (parts.json C23223, qty_per_board 0) - deliberately NOT a second
    parallel footprint, because fitting both would give 37.4 R and an invalid
    class. Recorded in R3's fields so P6/P7 can put it on silk.
  * RDEN = R1 + R2 = 24.8 k with the tap out at /poe/DEN_TAP (grounding the
    tap to VSS spoils the signature = the clean hardware PD-disable). The
    magjack's internal bridge is in series with the detection path, but TI's
    own 24.9 k recommendation already assumes an input bridge (Figure 24), and
    the bridge's incremental resistance at the 200-400 uA detection current is
    ~0.35 k, so 24.8 k + bridge is ~25.1 k, inside IEEE's 23.7-26.3 k window.
    decisions.md D-A2's "may need trimming upward" therefore resolves to NO
    trim; the arithmetic is here so a later reader does not redo it.
  * CBULK is 4 x 10 uF / 100 V (C2/C4/C5/C6), not 2 x 22 uF: no 22 uF / 100 V
    MLCC exists on LCSC in any package. ~20-24 uF after DC-bias derating, well
    over the >= 5 uF AC-MPS floor (DS 7.4.7) and far under the ~180 uF port
    ceiling. Do not "fix" this back.
  * D1 SMBJ58A is unidirectional: pin 2 is the CATHODE (to V48_RAW).
  * J1 P7/P8 are absent from the HY931147C schematic (SKU-specific; the
    HR861153C alternate uses them) -> explicit no-connect.
  * J1 LEDs: 11 = yellow ANODE, 12 = yellow cathode, 13 = green ANODE,
    14 = green cathode. The W5500's LED outputs are ACTIVE LOW, so the anodes
    are fed from +3V3 through R7/R8 and the CATHODES carry /ETH_LED_ACT and
    /ETH_LED_LINK. Wired the other way round the LEDs simply never light.
  * NO Bob Smith network. TI SNLA079D 2.3: "Bob-Smith termination does not
    apply for Power Over Ethernet applications", and on a Mode A + Mode B PD
    there is no unpowered tap left to terminate. What survives is the AC half:
    R6 (1 M) || C3 (1 nF / 2 kV) from the shield tabs to GND.

Rebuild (writes ../poe.kicad_sch; the ROOT generator owns the project file):
    .venv/Scripts/python boards/lumina-carrier/kicad/gen/poe.py
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
# refdes -> LCSC, straight out of parts/parts.json (see module docstring).
LCSC = {
    "J1": "C91754",       # HY931147C PoE magjack
    "U1": "C337500",      # TPS2378DDAR PD interface
    "D1": "C2891331",     # SMBJ58A 58 V 600 W TVS
    "C1": "C28233",       # 100nF 100V X7R 0805 (VDD-VSS bypass)
    "C2": "C5156756", "C4": "C5156756",   # CBULK 10uF 100V X7R 1210
    "C5": "C5156756", "C6": "C5156756",
    "C3": "C9196",        # 1nF 2kV X7R 1206 (shield hybrid)
    "R1": "C30908", "R2": "C30908",       # 12.4k 1% 0805 (split RDEN)
    "R3": "C23130",       # 90.9R 1% 0603 (RCLS, the D-01 lever)
    "R4": "C17414", "R5": "C17414",       # 10k 1% 0805 (T2P network)
    "R6": "C22935",       # 1M 1% 0603 (shield bleed)
    "R7": "C23138", "R8": "C23138",       # 330R 1% 0603 (magjack LEDs)
    "R9": "C21189",       # 0R jumper 0603 (APD -> RTN link)
}

V_10U = "10uF 100V X7R 1210"
V_100N = "100nF 100V X7R 0805"
V_1N2K = "1nF 2kV X7R 1206"
V_12K4 = "12.4k 1% 0805"
V_10K = "10k 1% 0805"
V_1M = "1M 1% 0603"
V_330R = "330R 1% 0603"

R0603 = f"{FP}:R0603"
R0805 = f"{FP}:R0805"
C0805 = f"{FP}:C0805"
C1210 = f"{FP}:C1210"

SYM_R0805 = f"{FP}:0805W8F1242T5E"     # 12.4k body, value field carries the R
SYM_R10K = f"{FP}:0805W8F1002T5E"
SYM_R909 = f"{FP}:0603WAF909JT5E"
SYM_R1M = f"{FP}:0603WAF1004T5E"
SYM_R330 = f"{FP}:0603WAF3300T5E"
SYM_R0 = f"{FP}:0603WAF0000T5E"
SYM_C100N = f"{FP}:CL21B104KCFNNNE"
SYM_C10U = f"{FP}:FS32X106K101EGG"
SYM_C1N = f"{FP}:1206B102K202NT"


def _global_rail(sh: schlib.Sheet, net: str, at, sym: str,
                 flag: bool = True) -> None:
    """A rail cluster whose power SYMBOL is renamed to `net`.

    sheets.md P4 note 2: V48_RAW / V48_RTN must be GLOBAL bare nets, but KiCad
    ships no power symbol with those names. A local label alone would yield
    /poe/V48_RAW and `netlist_audit --constraints` would raise missing_net at
    ERROR severity (constraints.json.voltages + .power both name them bare).
    So place power:+48V and rewrite its Value, which is what KiCad 6+ derives
    a power symbol's net name from (verified for this build - see
    work/poe_harness.py, which exports a real hierarchical netlist).
    """
    sh.power_flag(net, at=at, sym=sym, flag=flag)
    ref = f"#PWR{sh._pwr_i:02d}"          # power_flag just allocated this one
    # NB: `.value = `, not set_property("Value", ...) - the latter is a silent
    # no-op for the Value field in kicad-sch-api 0.5.6 (measured this build).
    sh.sch.components.get(ref).value = net


def build() -> schlib.Sheet:
    sh = schlib.Sheet("poe", title="LUM-CAR-A: PoE PD front end (48 V domain)",
                      paper="A3", date="2026-07-28", company="ai-ee",
                      pwr_base=100)

    # ---------------------------------------------------------------- J1 -----
    # HY931147C: 6 chip-side signal pins, 2 SKU-NC pins, the internal
    # rectifier's V+/V-, 4 LED pins and 2 shield tabs.
    #
    # MDI mapping (parts/C91754.json layout_notes, traced from the datasheet
    # schematic): TX line side -> jack contacts J2 (upper, = P6) and J1 (lower,
    # = P5); RX line side -> J6 (upper, = P2) and J3 (lower, = P1). That is
    # standard T568B, where contact 1 is TX+, 2 is TX-, 3 is RX+, 6 is RX-.
    # The chip-side end of each winding therefore inherits the polarity of its
    # line-side counterpart: P5 -> TXP, P6 -> TXN, P1 -> RXP, P2 -> RXN.
    # ASSUMED: the datasheet prints no dot convention, so same-end == same
    # polarity is an inference. 100BASE-TX receivers auto-correct polarity, so
    # a swap costs nothing electrically; it is called out for P6 review.
    sh.add_component(f"{FP}:HY931147C", "J1", "HY931147C PoE RJ45 magjack",
                     at=(63.50, 101.60),
                     footprint=f"{FP}:RJ45-TH_HY931147C",
                     expect={"1": "1", "2": "2", "3": "3", "4": "4", "5": "5",
                             "6": "6", "7": "7", "8": "8", "9": "9",
                             "10": "10", "11": "11", "12": "12", "13": "13",
                             "14": "14", "GND1": "GND", "GND2": "GND"})
    sh.wire_pins("J1", {
        "1": "ETH_RXP",       # RX winding chip side, low end  <-> contact 3
        "2": "ETH_RXN",       # RX winding chip side, high end <-> contact 6
        # P3 = chip-side RX centre tap. NO-CONNECT: the W5500 datasheet
        # (5.5.5) specifies only "1:1, 350 uH" and gives NO centre-tap network,
        # the magjack datasheet gives none either, and no AC-termination part
        # is allocated to this sheet in parts.json. A floating receive CT is
        # the safe default (the W5500 biases RXP/RXN internally); a 0.1 uF
        # to GND can be added later if EMC asks. Raised for the orchestrator.
        "3": "NC",
        # P4 = chip-side TX centre tap -> +3V3. WIZnet's reference design biases
        # the transmit centre tap from the 3.3 V rail; leaving it open starves a
        # current-mode driver of its DC path, while a voltage-mode driver is
        # unharmed by the bias, so +3V3 is the safe choice under both readings.
        # ASSUMED (WIZnet design guide, not the W5500 datasheet) - see OPEN.
        "4": "+3V3",
        "5": "ETH_TXP",       # TX winding chip side, low end  <-> contact 1
        "6": "ETH_TXN",       # TX winding chip side, high end <-> contact 2
        # P7/P8: physically present in the mounting pattern but absent from the
        # HY931147C datasheet schematic - mechanical only on this SKU. (The
        # HR861153C alternate DOES use them, which is why this is flagged.)
        "7": "NC",
        "8": "NC",
        "9": "V48_RAW",       # V+ : common cathode of both internal bridges
        "10": "V48_RTN",      # V- : common anode of both internal bridges
        "11": "LED_Y_A",      # yellow anode  -> R7 -> +3V3
        "12": "ETH_LED_ACT",  # yellow cathode <- W5500 ACTLED (active low)
        "13": "LED_G_A",      # green anode   -> R8 -> +3V3
        "14": "ETH_LED_LINK",  # green cathode <- W5500 LINKLED (active low)
        "GND1": "SHIELD",     # shell tabs: hybrid to GND through R6 || C3,
        "GND2": "SHIELD",     # never a hard short (chassis/circuit moat)
    })

    # ---------------------------------------------------------------- D1 -----
    # TVS across the rectified input, physically first after the jack
    # (TI sec 8.2.2.2 makes a TVS mandatory). Unidirectional: K to the positive.
    sh.add_component(f"{FP}:SMBJ58A_C2891331", "D1", "SMBJ58A 58V 600W TVS",
                     at=(139.70, 152.40),
                     footprint=f"{FP}:SMB_L4.3-W3.6-LS5.4-R-RD",
                     expect={"1": "A", "2": "K"})
    sh.wire_pins("D1", {"1": "V48_RTN", "2": "V48_RAW"})

    # ------------------------------------------------------- LED resistors ---
    # Anode side from +3V3; ~4 mA at Vf 1.8-2.8 V, inside the W5500's IOL.
    sh.add_component(SYM_R330, "R7", V_330R, at=(127.00, 44.45),
                     footprint=R0603)
    sh.wire_pins("R7", {"1": "+3V3", "2": "LED_Y_A"})
    sh.add_component(SYM_R330, "R8", V_330R, at=(127.00, 69.85),
                     footprint=R0603)
    sh.wire_pins("R8", {"1": "+3V3", "2": "LED_G_A"})

    # ------------------------------------------------- detection signature ---
    # RDEN from VDD to DEN, split in two with the tap brought out.
    sh.add_component(SYM_R0805, "R1", V_12K4, at=(177.80, 50.80),
                     footprint=R0805)
    sh.wire_pins("R1", {"1": "V48_RAW", "2": "DEN_TAP"})
    sh.add_component(SYM_R0805, "R2", V_12K4, at=(177.80, 76.20),
                     footprint=R0805)
    sh.wire_pins("R2", {"1": "DEN_TAP", "2": "DEN"})

    # ------------------------------------------------------------ U1 --------
    # Pin 5 RTN is board GND; pin 4 VSS and the pad (9) are V48_RTN.
    # C1 is the IEEE 802.3 detection-window bypass (50-120 nF) across VDD-VSS,
    # so its return is V48_RTN, NOT GND - hence the gnd override.
    # C2/C4/C5/C6 are CBULK, which the datasheet places from VDD (1) to
    # RTN (5): it is charged through the hot-swap FET at the 140 mA inrush
    # limit, so it belongs on the GND side of the switch.
    sh.place_ic_with_decoupling(
        "U1", f"{FP}:TPS2378DDAR", "TPS2378DDAR",
        at=(241.30, 114.30),
        pins={"1": "V48_RAW",   # VDD
              "2": "DEN",       # detection signature
              "3": "CLS",       # classification, RCLS to VSS
              "4": "V48_RTN",   # VSS - local ground of the PD front end
              "5": "GND",       # RTN - drain of the pass MOSFET = board GND
              "6": "CDB",       # open-drain converter disable -> U20 EN
              "7": "T2P_OD",    # open-drain type-2 flag, pulled up by R4
              "8": "APD",       # -> R9 (0 R) -> RTN, per the datasheet
              "9": "V48_RTN"},  # PowerPAD is VSS. NOT RTN.
        footprint=f"{FP}:SOIC-8-1EP_3.9x4.9mm_P1.27mm_EP2.95x4.9mm_"
                  "Mask2.71x3.4mm",
        expect={"1": "VDD", "2": "DEN", "3": "CLS", "4": "VSS", "5": "RTN",
                "6": "CDB", "7": "T2P", "8": "APD", "9": "EP"},
        decoupling=[
            {"cap": "C1", "pin": "1", "rail": "V48_RAW", "gnd": "V48_RTN",
             "value": V_100N, "lib_id": SYM_C100N, "footprint": C0805},
            {"cap": "C2", "pin": "1", "rail": "V48_RAW", "value": V_10U,
             "lib_id": SYM_C10U, "footprint": C1210},
            {"cap": "C4", "pin": "1", "rail": "V48_RAW", "value": V_10U,
             "lib_id": SYM_C10U, "footprint": C1210},
            {"cap": "C5", "pin": "1", "rail": "V48_RAW", "value": V_10U,
             "lib_id": SYM_C10U, "footprint": C1210},
            {"cap": "C6", "pin": "1", "rail": "V48_RAW", "value": V_10U,
             "lib_id": SYM_C10U, "footprint": C1210},
        ],
        caps_at=(139.70, 215.90), caps_dx=25.40)

    # --------------------------------------------------- classification ------
    # THE D-01 LEVER. One resistor, standalone pad pair, silk-marked.
    # Dissipation: the part forces ~2.5 V across RCLS only inside the 11.9-23 V
    # classification window. af/90.9 R -> 27.9 mA typ (29.3 max) = 70-73 mW in
    # a 100 mW 0603, fine even continuously. The at/63.4 R upgrade draws
    # 39.9 mA typ (42 max) = 100-105 mW, i.e. AT or just over the 0603 rating -
    # acceptable only because classification is a sub-100 ms transient. Flagged
    # so the D-01 upgrade is not fitted assuming free thermal headroom.
    r3 = sh.add_component(SYM_R909, "R3", "90.9R 1% 0603",
                          at=(292.10, 165.10), footprint=R0603)
    sh.wire_pins("R3", {"1": "CLS", "2": "V48_RTN"})
    r3.set_property("Note", "D-01 LEVER  af=90R9 / at=63R4")
    r3.set_property("ALT_LCSC", "C23223")
    r3.set_property("ALT_VALUE", "63.4R 1% 0603 = Class 4 / 802.3at "
                                 "(NOT FITTED - value swap, not a 2nd part)")

    # ----------------------------------------------------------- APD ---------
    # Datasheet: "If not used, connect APD to RTN." R9 keeps it depopulatable
    # so a TPS2379 (pin 8 = GATE) can be stuffed on the same footprint.
    sh.add_component(SYM_R0, "R9", "0R jumper 0603", at=(292.10, 114.30),
                     footprint=R0603)
    sh.wire_pins("R9", {"1": "APD", "2": "GND"})

    # ------------------------------------------------------ T2P network ------
    # T2P is open drain to RTN, and RTN is board GND here, so the level shift
    # collapses to a pull-up plus a series limiter. R4 clamps the idle level to
    # +3V3 (the pin's own 57 V capability is never reached because nothing
    # pulls it up higher), R5 limits fault current into the ESP32-S3 GPIO.
    sh.add_component(SYM_R10K, "R4", V_10K, at=(317.50, 63.50),
                     footprint=R0805)
    sh.wire_pins("R4", {"1": "+3V3", "2": "T2P_OD"})
    sh.add_component(SYM_R10K, "R5", V_10K, at=(317.50, 88.90),
                     footprint=R0805)
    sh.wire_pins("R5", {"1": "T2P_OD", "2": "T2P"})

    # -------------------------------------------------------- shield hybrid --
    # 1 M bleed || 1 nF / 2 kV: DC-isolates the shell from board ground (which
    # floats at PoE potential on a non-isolated PD) while giving common-mode
    # energy an AC path. This is the PoE-legal remnant of Bob Smith.
    sh.add_component(SYM_R1M, "R6", V_1M, at=(50.80, 177.80), footprint=R0603)
    sh.wire_pins("R6", {"1": "SHIELD", "2": "GND"})
    sh.add_component(SYM_C1N, "C3", V_1N2K, at=(88.90, 177.80),
                     footprint=f"{FP}:C1206")
    sh.wire_pins("C3", {"1": "SHIELD", "2": "GND"})

    # ------------------------------------------------------------ rails ------
    # Every rail on this board is driven by a PASSIVE pin (a connector pin, an
    # inductor), so ERC needs a PWR_FLAG per rail. sheets.md s1.1 puts the
    # GND / V48_RAW / V48_RTN flags on THIS sheet (#FLG100+); +3V3's flag lives
    # on `pwr`, so +3V3 here is a consuming power symbol with flag=False.
    _global_rail(sh, "GND", (25.40, 228.60), "power:GND", flag=True)
    _global_rail(sh, "V48_RAW", (25.40, 241.30), "power:+48V", flag=True)
    _global_rail(sh, "V48_RTN", (25.40, 254.00), "power:+48V", flag=True)
    _global_rail(sh, "+3V3", (114.30, 254.00), "power:+3V3", flag=False)

    # ------------------------------------------------------ sheet interface --
    # Free-cluster variant (sheets.md s3 note 3): local label + hierarchical
    # label on one stub, so the hier label joins the net by wire geometry.
    # Shape is `passive` for everything the OTHER sheet drives, and `output`
    # only where THIS sheet is the driver - a sheet pin typed `input` on a net
    # whose members are all passive raises a false pin_not_driven at the root.
    for i, (net, shape) in enumerate([
            ("ETH_TXP", "passive"),
            ("ETH_TXN", "passive"),
            ("ETH_RXP", "passive"),
            ("ETH_RXN", "passive"),
            ("ETH_LED_LINK", "passive"),   # driven by U10 LINKLED, active low
            ("ETH_LED_ACT", "passive"),    # driven by U10 ACTLED, active low
            ("T2P", "output"),             # U1 type-2 flag -> U30 GPIO47
            # CDB is the 8th pin and is NOT in the brief's interface list.
            # sheets.md s1.3 files /poe/CDB as sheet-INTERNAL yet names U20's
            # EN (pwr sheet) as a member, which cannot both be true. Exposing
            # it is the only wiring that matches the architecture's PoE
            # start-up sequencing, so the root MUST carry "CDB" in poe's
            # add_sheet(nets=...) - see the OPEN note in the P4 report.
            ("CDB", "output")]):
        sh.hier_pin(net, shape=shape, at=(368.30, 25.40 + i * 12.70))

    for ref, code in LCSC.items():
        sh.sch.components.get(ref).set_property("LCSC", code)
    return sh


def main(argv=None) -> int:
    # Default out dir is kicad/, and project=False: the ROOT generator owns
    # <root>.kicad_pro, this sheet must never write one.
    out_dir = Path(argv[0]) if argv else BOARD / "kicad"
    try:
        sh = build()
        path = sh.save(out_dir, project=False)
    except Exception as exc:  # noqa: BLE001  (SPEC 6: any error -> exit 2)
        print(json.dumps({"script": "gen.poe", "status": "error",
                          "error": f"{type(exc).__name__}: {exc}"}))
        return 2
    print(json.dumps({
        "script": "gen.poe", "status": "pass",
        "sheet": str(path),
        "components": len(list(sh.sch.components)),
        "hier_pins": sorted(sh.hier_pins),
        "decoupling_associations": len(sh.decoupling),
    }, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
