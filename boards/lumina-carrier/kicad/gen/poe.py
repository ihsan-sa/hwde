"""LUM-CAR-A `poe` sheet: RJ45 PoE magjack -> 2 bridges -> TVS -> TPS2378.

Refdes range (architecture/sheets.md s2.1): J1, U1-U9, R1-R19, C1-C19, D1-D9;
pwr_base 100 (#PWR100+/#FLG100+). EVERY refdes here is taken from
parts/parts.json, never from a symbol's Reference property - the EasyEDA pull
defaults J1's prefix to "RJ" and U1's is fine but the rule is uniform.

WHAT THIS SHEET IS
------------------
A NON-ISOLATED 802.3af PD front end (802.3at-capable; the class is one resistor
value - see R3). J1 is a **1000BASE-T PoE+ integrated connector module with NO
internal rectifier**: it brings out four RAW line-side centre taps, VC1/VC2 =
Alternative A (the data pairs) and VC3/VC4 = Alternative B (the spare pairs).
D2 and D3 are the two external full-wave bridges that turn those into the one
positive node `V48_RAW` and one raw negative `V48_RTN`. Both bridges are
mandatory: 802.3 requires a PD to accept power on EITHER Alternative and EITHER
polarity, and only one Alternative is ever energised at a time.

U1 switches the RETURN: its RTN pin (5) is board `GND`
(architecture/power_tree.md s1: "RTN = board GND"), and its VSS pin (4) plus
the exposed pad are `V48_RTN`, which sits up to 57 V BELOW GND while the
hot-swap FET is off. Nothing outside this sheet may touch `V48_RTN`.

Everything downstream of V48_RAW / V48_RTN (D1, U1, CBULK, RDEN, RCLS, T2P) is
unchanged from the superseded HY931147C build except RDEN, whose value depended
on that part's unspecified internal bridge - see "RDEN" below.

GROUND TRUTH used for every connection (SPEC s5 - no wiring from memory)
-----------------------------------------------------------------------
parts/C337500.json (TPS2378, TI SLVSB99C), parts/C22457393.json (LINK-PP
LPJG0926HENL, drawing LP18022610 rev A, schematic traced pin-by-pin from the
extractable p1 text AND the 300 dpi renders work/mj2/lpjg_sch_l.png +
lpjg_led2.png) and parts/C2892567.json (YONGYUTAI ABS210 bridge), plus the
library pin tables printed by
`schlib.py --pins aiee:<SYMBOL> --lib ../lib/aiee.kicad_sym`.

Load-bearing facts, with the trap each one avoids:
  * J1 PIN NUMBERING IS NOT THE HY931147C's. Chip side is 1 TD1+, 2 TD1-,
    3 TD2+, 6 TD2-, 7 TD3+, 8 TD3-, 9 TD4+, 10 TD4-, with the centre-tap bus
    on 4 AND 5; the four line-side taps are 11-14 and the LEDs moved to 15-18.
    The JACK end is unchanged standard T568B (contacts 1,2 = TX pair;
    3,6 = RX pair), so the MDI mapping did NOT move - only the chip-side pin
    numbers did. Wiring this from the old part's map flips the connector.
  * J1 pins 4 and 5 are ONE internal net - a single bus commons the chip-side
    centre taps of all four transformers and exits twice. BOTH must go to
    +3V3; leaving pin 5 open leaves an unconnected-pin ERC error, and driving
    it separately would short two supplies if a later part differs.
  * J1 pins 7-10 (TD3+/-, TD4+/-) are the chip-side ends of the two pairs the
    W5500 never drives. They are explicit no-connects, and pads 9/10 are
    deliberately kept as BARE copper: they are the closest chip-side pads to
    the 48 V taps, so a dead net there IS the isolation mitigation
    (lib/EDITS.md edit 7 - 1.401 mm to any energised net). Never net them.
  * J1 LEDs are COLOUR-SWAPPED relative to the HY931147C. 15 = GREEN anode,
    16 = green cathode (LEFT LED); 17 = YELLOW anode, 18 = yellow cathode
    (RIGHT LED). Odd = anode, as before. Green stays LINK and yellow stays
    ACT, so /ETH_LED_LINK and /ETH_LED_ACT swap physical sides - and R7
    (yellow, via LED_Y_A) and R8 (green, via LED_G_A) keep their nets.
    The W5500's LED outputs are ACTIVE LOW, so the anodes are fed from +3V3
    through R7/R8 and the CATHODES carry the signals. Wired the other way
    round the LEDs simply never light.
  * J1 pins 19/20 ("EH") are the shell board locks and are the ONLY path from
    the metal shield to the board - the two dia-3.20 mm mounting holes are
    non-plated. They carry /poe/SHIELD.
  * D2/D3 pin 3 is "+" and pin 4 is "-" (datasheet PINNING table); pins 1/2
    are the two AC inputs and sit on the same side of the body.
  * ONLY ONE BRIDGE CONDUCTS AT A TIME. A PSE energises Alternative A or B,
    never both, so the energised bridge carries the whole PD current - the
    dissipation is NOT shared between D2 and D3. Sizing therefore assumes one
    package takes it all (see "BRIDGE THERMAL" below).
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
    pair (parts.json C334927, qty_per_board 0) - deliberately NOT a second
    parallel footprint, because fitting both would give 37.4 R and an invalid
    class. Recorded in R3's fields so P6/P7 can put it on silk.
  * CBULK is 4 x 10 uF / 100 V (C2/C4/C5/C6), not 2 x 22 uF: no 22 uF / 100 V
    MLCC exists on LCSC in any package. ~20-24 uF after DC-bias derating, well
    over the >= 5 uF AC-MPS floor (DS 7.4.7) and far under the ~180 uF port
    ceiling. Do not "fix" this back.
  * D1 SMBJ58A is unidirectional: pin 2 is the CATHODE (to V48_RAW).

BRIDGE THERMAL - why ABS210 and not the obvious MB6S/MB10S
----------------------------------------------------------
Worst-case PD input current is the 802.3at ceiling, 0.600 A DC / 0.686 A peak
(connector-icd.md s6.1). Two junctions conduct in series, so the energised
bridge dissipates 2 x Vf(0.6 A) x 0.6 A. The board's ambient of record is the
sealed enclosure's internal air: 64 C worst case at a 40 C room
(connector-icd.md s7.7.3). Both parts below are 1000 V, both are cheap, and
the current ratings look adequate on both - the packages are what separate
them, which is why the current rating must NOT be read as a proxy for thermal
capability:

  MB10S / MB6S, MBS package (the default reflex, and the only JLC BASIC
    bridge on LCSC - C2488):
      datasheet mean rectifying current 0.5/0.8 A, NOT 1 A; Vf 1.0 V @ 0.5 A
      and 1.1 V @ 0.8 A -> ~1.03 V at 0.6 A -> P = 1.24 W
      RthJA = 90 C/W (Hottech MB05S-MB10S, p1)
      Tj = 64 + 90 x 1.24 = 176 C against a 150 C limit.  REJECTED, and by
      26 C, not by a rounding error.

  ABS210, ABS package (SELECTED, C2892567, 2 A / 1000 V):
      Vf ~0.88 V at 0.6 A from the typical forward curve (Fig.3), falling to
      ~0.70 V once hot (-2 mV/C) -> P = 0.83 W hot, 1.06 W if no thermal
      credit is taken at all
      RthJA = 65 C/W (p1, "mounted on glass epoxy PC board with 4 x (5 x 5 mm)
      copper pad")
      Tj = 64 + 65 x 1.06 = 133 C worst case, 118 C self-consistently.
      PASSES with 17-32 C of margin.

  Discrete PN or Schottky arrays were considered and rejected. Discretes are
  thermally better (only 2 of 4 conduct, so ~0.5 W per package) but cost 8
  parts and MORE board area than 2 x ABS, for margin that is already there.
  Schottkys are worse here for two reasons that are not about heat: 100 V
  parts have no margin over the SMBJ58A's 93.6 V clamp, and their reverse
  leakage distorts the detection signature (parts/C337500.json says so in as
  many words) and raises the 802.3 backfeed voltage on the unpowered pairs.

  P7 MUST give each of the 8 bridge pads its ~5 x 5 mm copper pour. The
  65 C/W above is quoted on that condition and is void without it.

RDEN - recomputed for REAL diodes
---------------------------------
IEEE wants an incremental resistance dV/dI of 23.7-26.3 k measured at the PI,
i.e. INCLUDING the input bridge. The old 24.8 k was justified against the
HY931147C's unspecified internal bridge with a guessed ~0.35 k adder. The
bridge is now a known part, so the adder is computable:

  ABS210 typical forward curve (Fig.3): 0.575 V at 10 mA, 0.700 V at 100 mA
  -> n.Vt = 0.125 / ln(10) = 54.3 mV, i.e. ideality n = 2.10 at 25 C, and
  Vf(100 uA) = 0.325 V extrapolated.
  Two junctions add 2.n.Vt.ln(I2/I1)/(I2-I1) to the chord the PSE measures.

  PSE probe pair              current pair        diode adder
  2.8 V / 3.8 V (worst)       89.4 / 129.0 uA     +1.00 k
  9.0 V / 10.0 V (best)       339.6 / 380.4 uA    +0.31 k

  with the old 24.8 k:  low probes, R at +1% -> 25.048 + 1.04 = 26.09 k,
      i.e. 0.8 % under the 26.3 k ceiling - and 0.2 % if the ideality is 2.4
      rather than 2.10.  4.5 % of slack at the floor, 0.8 % at the ceiling:
      the signature was not centred, it was leaning on the ceiling.
  with 24.2 k (R1 = R2 = 12.1 k 1%):
      low probes, R at +1% -> 24.442 + 1.00 = 25.44 k   (3.3 % under 26.3 k)
      high probes, R at -1% -> 23.958 + 0.31 = 24.27 k  (2.4 % over 23.7 k)
      -> 24.3-25.5 k over every legal probe pair and both tolerance corners.

  TI's generic 24.9 k recommendation (parts/C337500.json, sec 7.3.4) assumes
  "an input bridge" without naming one and lands in the same lean-on-the-
  ceiling place; knowing the bridge is what buys the re-centring. Dissipation
  is unchanged in character: the signature is only presented below ~10.9 V, so
  RDEN sees at most 10 V / 24.2 k = 413 uA = 4.1 mW, matching the datasheet's
  "about 5 mW". The tap stays out at /poe/DEN_TAP - grounding it to VSS spoils
  the signature, which IS the clean hardware PD-disable.

BOB SMITH - the old "we deliberately fit none" note is now WRONG
---------------------------------------------------------------
The superseded HY931147C carried no AC termination and this sheet cited TI
SNLA079D 2.3 ("Bob-Smith termination does not apply for Power Over Ethernet
applications") as the reason to fit none. **That rationale no longer applies
and must not be re-instated.** LPJG0926HENL contains a Bob Smith network that
cannot be removed or reached: 4 x 22 nF / 100 V, one from each VC node, each in
series with 75 R into a common node, and that node to SHIELD through
1000 pF / 2 kV.

Two consequences:
  * The board must NOT add its own 75 R terminations. They would parallel the
    internal ones and halve the common-mode termination to 37.5 R. None are
    fitted, which is now the right answer for a NEW reason.
  * R6 (1 M) || C3 (1 nF / 2 kV) from SHIELD to GND is RE-EXAMINED and KEPT.
    It is not a duplicate of the internal 1 nF: the internal cap runs from the
    termination node to SHIELD, C3 runs from SHIELD to GND, so the two are in
    SERIES and the termination node sees ~500 pF to board ground - halved, but
    still squarely inside the 100 pF - 10 nF that this function uses, and the
    2 kV rating is shared rather than stacked on one part. R6 is likewise
    still required: the internal network is purely capacitive, so without the
    1 M bleed the shell has no defined DC potential at all. Deleting either
    part on "the magjack already has one" would be a mistake.

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
    "J1": "C22457393",    # LPJG0926HENL 1000BASE-T PoE+ magjack, NO bridge
    "D2": "C2892567",     # ABS210 bridge - Alternative A (VC1/VC2)
    "D3": "C2892567",     # ABS210 bridge - Alternative B (VC3/VC4)
    "U1": "C337500",      # TPS2378DDAR PD interface
    "D1": "C2891331",     # SMBJ58A 58 V 600 W TVS
    "C1": "C28233",       # 100nF 100V X7R 0805 (VDD-VSS bypass)
    "C2": "C5156756", "C4": "C5156756",   # CBULK 10uF 100V X7R 1210
    "C5": "C5156756", "C6": "C5156756",
    "C3": "C9196",        # 1nF 2kV X7R 1206 (shield hybrid)
    "R1": "C17431", "R2": "C17431",       # 12.1k 1% 0805 (split RDEN)
    "R3": "C3000584",       # 90.9R 1% 0603 (RCLS, the D-01 lever)
    "R4": "C17414", "R5": "C17414",       # 10k 1% 0805 (T2P network)
    "R6": "C22935",       # 1M 1% 0603 (shield bleed)
    "R7": "C23138", "R8": "C23138",       # 330R 1% 0603 (magjack LEDs)
    "R9": "C21189",       # 0R jumper 0603 (APD -> RTN link)
}

V_10U = "10uF 100V X7R 1210"
V_100N = "100nF 100V X7R 0805"
V_1N2K = "1nF 2kV X7R 1206"
V_12K1 = "12.1k 1% 0805"
V_10K = "10k 1% 0805"
V_1M = "1M 1% 0603"
V_330R = "330R 1% 0603"

R0603 = f"{FP}:R0603"
R0805 = f"{FP}:R0805"
C0805 = f"{FP}:C0805"
C1210 = f"{FP}:C1210"

SYM_J1 = f"{FP}:LPJG0926HENL_C22457393"
SYM_BRIDGE = f"{FP}:ABS210_C2892567"
FP_J1 = f"{FP}:RJ45-TH_LPJG0926HENL_C22457393"
FP_BRIDGE = f"{FP}:ABF_L5.1-W4.4-P4.00-LS6.2-BL"

SYM_R0805 = f"{FP}:0805W8F1212T5E"      # 12.1k, the recomputed RDEN half
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
                      paper="A3", date="2026-07-29", company="ai-ee",
                      pwr_base=100)

    # ---------------------------------------------------------------- J1 -----
    # LPJG0926HENL: 10 chip-side winding ends, the doubled centre-tap bus
    # (4 + 5), four RAW line-side taps (11-14), 4 LED pins and 2 shell locks.
    #
    # MDI mapping (parts/C22457393.json, traced from the p1 schematic): the
    # datasheet names the jack contacts J1..J8 and pairs them
    # (J1,J2) (J3,J6) (J4,J5) (J7,J8) - standard T568B, where contact 1 is
    # TX+, 2 is TX-, 3 is RX+, 6 is RX-. The chip-side end of each winding
    # inherits the polarity of its line-side counterpart, so TD1+/- (pins 1/2)
    # <-> contacts 1/2 = the TX pair and TD2+/- (pins 3/6) <-> contacts 3/6 =
    # the RX pair. This is the SAME jack-end mapping as the HY931147C; only
    # the chip-side pin numbers moved.
    # ASSUMED: the datasheet prints no dot convention, so same-end == same
    # polarity is an inference. 100BASE-TX receivers auto-correct polarity, so
    # a swap costs nothing electrically; it is called out for P6 review.
    sh.add_component(SYM_J1, "J1", "LPJG0926HENL PoE+ RJ45 magjack",
                     at=(63.50, 101.60), footprint=FP_J1,
                     expect={"1": "TD1+", "2": "TD1-", "3": "TD2+",
                             "4": "CT", "5": "CT", "6": "TD2-",
                             "7": "TD3+", "8": "TD3-", "9": "TD4+",
                             "10": "TD4-", "11": "VC1", "12": "VC2",
                             "13": "VC3", "14": "VC4", "19": "EH",
                             "20": "EH"})
    sh.wire_pins("J1", {
        "1": "ETH_TXP",       # TD1+ , chip side of the pair on contacts 1/2
        "2": "ETH_TXN",       # TD1-
        "3": "ETH_RXP",       # TD2+ , chip side of the pair on contacts 3/6
        # P4/P5 = the ONE chip-side centre-tap bus, brought out twice. WIZnet's
        # reference design biases the transmit centre tap from the 3.3 V rail;
        # leaving it open starves a current-mode driver of its DC path, while a
        # voltage-mode driver is unharmed by the bias, so +3V3 is the safe
        # choice under both readings. On this part the same node also holds the
        # centre taps of the two unused pairs at +3V3, which is harmless
        # because both ends of those windings float.
        # NOTE: the HY931147C's separate, floating chip-side RX centre tap -
        # and the open item that went with it - no longer exists. There is no
        # RX-only tap on this part.
        # ASSUMED (WIZnet design guide, not the W5500 datasheet) - see OPEN.
        "4": "+3V3",
        "5": "+3V3",
        "6": "ETH_RXN",       # TD2-
        # P7-P10 = chip-side ends of the two pairs the W5500 never drives.
        # Explicit no-connects, and pads 9/10 are the isolation mitigation:
        # they are the closest chip-side copper to the 48 V taps, so they are
        # kept as BARE pads on a dead net (lib/EDITS.md edit 7). The line side
        # of those pairs is already terminated by the internal Bob Smith.
        "7": "NC",
        "8": "NC",
        "9": "NC",
        "10": "NC",
        # P11-P14 = the four RAW line-side centre taps. 720 mA max @ 57 VDC
        # continuous each (p1 item 7) = 1.20x the 802.3at 0.600 A DC ceiling
        # and 1.05x the 0.686 A peak. VC1+VC2 are Alternative A (data pairs),
        # VC3+VC4 Alternative B (spare pairs).
        "11": "POE_TAP_A1",
        "12": "POE_TAP_A2",
        "13": "POE_TAP_B1",
        "14": "POE_TAP_B2",
        "15": "LED_G_A",       # GREEN anode  -> R8 -> +3V3   (LEFT LED)
        "16": "ETH_LED_LINK",  # green cathode <- W5500 LINKLED (active low)
        "17": "LED_Y_A",       # YELLOW anode -> R7 -> +3V3   (RIGHT LED)
        "18": "ETH_LED_ACT",   # yellow cathode <- W5500 ACTLED (active low)
        "19": "SHIELD",       # shell board locks: hybrid to GND through
        "20": "SHIELD",       # R6 || C3, never a hard short (chassis moat)
    })

    # -------------------------------------------------- the two PD bridges ---
    # D2 rectifies Alternative A, D3 Alternative B, both onto the same
    # V48_RAW / V48_RTN. This restores exactly the topology the HY931147C had
    # inside it, and nothing downstream of those two nodes changes.
    # Each bridge blocks when its Alternative is unpowered: every diode points
    # INTO "+" and OUT OF "-", so with its AC inputs floating there is no path
    # from V48_RAW to V48_RTN through it. The idle bridge is therefore not a
    # load on detection, classification or the operating rail.
    for ref, at, taps, alt in (("D2", (190.50, 152.40),
                                ("POE_TAP_A1", "POE_TAP_A2"), "A"),
                               ("D3", (190.50, 190.50),
                                ("POE_TAP_B1", "POE_TAP_B2"), "B")):
        sh.add_component(SYM_BRIDGE, ref,
                         f"ABS210 2A 1000V bridge (Alt {alt})",
                         at=at, footprint=FP_BRIDGE,
                         expect={"1": "AC", "2": "AC", "3": "+", "4": "-"})
        sh.wire_pins(ref, {"1": taps[0], "2": taps[1],
                           "3": "V48_RAW", "4": "V48_RTN"})
        c = sh.sch.components.get(ref)
        c.set_property("Note", f"PD input bridge, Alternative {alt} "
                               "- 5x5 mm copper on all 4 pads (RthJA 65 C/W)")

    # ---------------------------------------------------------------- D1 -----
    # TVS across the rectified input, physically first after the bridges
    # (TI sec 8.2.2.2 makes a TVS mandatory). Unidirectional: K to the positive.
    sh.add_component(f"{FP}:SMBJ58A_C2891331", "D1", "SMBJ58A 58V 600W TVS",
                     at=(139.70, 152.40),
                     footprint=f"{FP}:SMB_L4.3-W3.6-LS5.4-R-RD",
                     expect={"1": "A", "2": "K"})
    sh.wire_pins("D1", {"1": "V48_RTN", "2": "V48_RAW"})

    # ------------------------------------------------------- LED resistors ---
    # Anode side from +3V3; ~4 mA at Vf 1.8-2.6 V, inside the W5500's IOL.
    # R7 is the YELLOW/ACT leg and R8 the GREEN/LINK leg, unchanged - it is the
    # magjack's LED PINS that swapped colour, not the drive network.
    sh.add_component(SYM_R330, "R7", V_330R, at=(127.00, 44.45),
                     footprint=R0603)
    sh.wire_pins("R7", {"1": "+3V3", "2": "LED_Y_A"})
    sh.add_component(SYM_R330, "R8", V_330R, at=(127.00, 69.85),
                     footprint=R0603)
    sh.wire_pins("R8", {"1": "+3V3", "2": "LED_G_A"})

    # ------------------------------------------------- detection signature ---
    # RDEN from VDD to DEN, split in two with the tap brought out.
    # 12.1 k + 12.1 k = 24.2 k; see the RDEN block in the module docstring for
    # why this moved down from 24.8 k now that the bridge diodes are known.
    sh.add_component(SYM_R0805, "R1", V_12K1, at=(177.80, 50.80),
                     footprint=R0805)
    sh.wire_pins("R1", {"1": "V48_RAW", "2": "DEN_TAP"})
    sh.add_component(SYM_R0805, "R2", V_12K1, at=(177.80, 76.20),
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
    r3 = sh.add_component(SYM_R909, "R3", "90.9R 1% 0805",
                          at=(292.10, 165.10), footprint=R0805)
    sh.wire_pins("R3", {"1": "CLS", "2": "V48_RTN"})
    r3.set_property("Note", "D-01 LEVER  af=90R9 / at=63R4")
    r3.set_property("ALT_LCSC", "C334927")
    r3.set_property("ALT_VALUE", "63.4R 1% 0805 = Class 4 / 802.3at "
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
    # energy an AC path. KEPT after re-examination against J1's internal Bob
    # Smith network - see the BOB SMITH block in the module docstring; C3 is in
    # SERIES with the magjack's internal 1 nF, not in parallel with it, and R6
    # is the only thing defining the shell's DC potential.
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
    # R3 borrows the 0603 90R9 symbol body but is fitted on an 0805 land with
    # an 0805 part (finding 16: the 63.4R at-upgrade alternate is ~105 mW
    # against a 100 mW 0603 rating, and D-01 promises a clean resistor swap).
    # Stamp the real identity so the sheet does not name the 0603 part.
    _r3 = sh.sch.components.get("R3")
    _r3.set_property("MPN", "FRC0805F90R9TS")
    _r3.set_property("Manufacturer", "FH (Guangdong Fenghua Advanced Tech)")
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
