"""LUM-PAR-A `power` sheet (block B1): rail entry, bulk, test points, H5,
branch-B front end (DNP).

Refdes range (architecture/sheets.md s1.1): 100-199, `#PWR`/`#FLG` base 100.
J3 and H5 are the ICD-named exceptions to the hundreds block (sheets.md s1).
EVERY refdes here comes from parts/parts.json and is passed explicitly to
add_component - NEVER taken from a symbol's own Reference property. On this
sheet one symbol would otherwise annotate wrong: **C113344
`DS1023-2*7SF11` carries Reference "H"**, not "J".

WHAT THIS SHEET IS
------------------
Everything the board's three supply rails touch before they fan out, plus the
one thing that is neither a rail nor a signal:

  A. J3 - the 2x7 POWER socket. Three rails arrive; on branch A only two are
     loaded (`+12V` and `+3V3`). `+48V_SW` is LANDED, NOT TAPPED.
  B. Bulk / HF decoupling of the two loaded rails (C101-C105).
  C. TP101-TP103 - bench test pads on all three rails.
  D. H5 - the CAR-REQ-15 M3 support hole between J3 and J4. Mechanical only.
  E. The branch-B hot-swap front end (Q101/Q102/R101-R104/C106-C108), fitted
     as DNP footprints so branch B stays a populate change, not a respin.
  F. The PWR_FLAGs for all four rails - see "WHO OWNS THE PWR_FLAGS" below.

GROUND TRUTH (SPEC s5 - no pin number, no value, no net from memory)
--------------------------------------------------------------------
architecture/p4-wiring-notes.md (BINDING - supersedes sheets.md),
architecture/sheets.md s1.1/s2/s4, architecture/blocks.md B1,
brief/06-connector-icd.md s3.1/s5.4/s7.3/s7.5/s9, parts/parts.json,
parts/C113344.json, parts/C115989.json, parts/C427379.json, plus the library
pin tables printed by
`schlib.py --pins "aiee:<SYMBOL>" --lib lib/aiee.kicad_sym`.

Load-bearing facts, with the trap each one avoids:

  * **J3'S PIN NUMBERS COME FROM ICD-01 s3.1 AND NOWHERE ELSE.** The CONNFLY
    DS1023 datasheet publishes NO pin numbering at all (parts/C113344.json,
    p4-wiring-notes s4). J3_PINS below is a transcription of the ICD table -
    if that table is re-issued, this map moves with it.
  * **J3 is reverse-mounted on the BOTTOM side, facing down** (ICD s7.3).
    That is a placement/side property, and it is set at P6 with a `place_edit`
    flip op - but **it is NOT schematic-neutral, and the original claim here
    that "the netlist is side-agnostic and correct either way" was WRONG and
    is the direct cause of a 48 V-to-GND short found at P6.** Flipping a 2-row
    connector to the back swaps its ROWS, so a literal transcription of the
    ICD table on both boards crosses 12 of 14 contacts. `J3_PINS` below is
    therefore the ICD table with rows A/B EXCHANGED - see the block comment
    above it. Pin 1 is checked in the MATED view, against the carrier's own
    netlist, not from the footprint.
  * **`+48V_SW` is LANDED, NOT TAPPED** (blocks.md B1). Its three pins reach
    TP103 and the DNP bleed R104 and stop. Landing it rather than floating
    the pads is what makes the net visible to `check_creepage` at P8, so the
    ICD s5.4 0.635 mm clearance is enforced by the tool instead of by hope.
  * **CAR-REQ-17's bleed obligation is NOT triggered on branch A** - no
    energy is stored on `+48V_SW` (no bulk, no series element). R104 is
    fitted DNP so the obligation is met the instant any 48 V bulk is added.
  * **Every 48 V-domain resistor is 0805 and every 48 V-domain capacitor is
    100 V** (ICD s5.4). 0603 chip resistors are 75 V working parts and 63 V
    caps do not survive 57 V after ceramic DC-bias derating. R101-R104 are
    0805; C106-C108 are 100 V. This is why branch B needs no footprint
    change: R104 is ALREADY 0805 on branch A (sheets.md s1.1).
  * **The bulk is ceramic, not aluminium.** ICD s7.6's DC-DC hot-zone keepout
    bans electrolytics and this board fits none at all: ~40 uF nameplate /
    ~25 uF effective on `+12V` is decoupling, not storage (power_tree s8).
  * **Q101 is a P-channel part and its pinout is NOT the usual SOT-23 order:**
    C115989 pinout = 1 G / 2 D (the TAB, and the trimmed centre lead - same
    node) / 3 S. Q102 (BSS123, C427379) = 1 G / 2 S / 3 D. Both are checked
    with `expect=` at placement.
  * **No decoupling associations are emitted from this sheet.** C101-C105 are
    RAIL bulk/HF; there is no IC here whose supply pin they decouple, and the
    S4 association contract names an IC + pin. Recording a fake one would put
    a lie into `check_decoupling` at P6.

WHO OWNS THE PWR_FLAGS  (read before adding one on another sheet)
------------------------------------------------------------------
**All four rails are flagged HERE and nowhere else.** Every rail on this
board enters through J3, whose 14 pins are all typed `passive`
(reports/lib_pin_types.json), and every stock power symbol contributes a
`power_in` pin - so without a flag each rail raises `pin_not_driven` at ERC.
A SECOND flag on the same net is not harmless: PWR_FLAG's pin is `power_out`
and two of them collide as `power_out <-> power_out`, which is the same
failure p4-wiring-notes s2 warns about on the driver VCC nodes. Other sheets
must place consuming power SYMBOLS only (`flag=False`).

`+48V_SW` has no stock power symbol. `power:+48V` is placed and schlib's
`power_flag` sets its VALUE to the net name, which is what KiCad 6+ derives a
power symbol's net from - so the net comes out global and BARE, exactly as
sheets.md s2 and constraints.json require. A local label alone would have
produced `/power/+48V_SW` and `netlist_audit --constraints` would raise
missing_net at ERROR severity.

DNP MARKING - AND THE GAP IT SITS IN
-------------------------------------
The nine branch-B parts carry a **`Variant` = `DNP`** field (sheets.md s4
rule 1: "Mark them DNP in the BOM variant field"). They are otherwise fully
present - in the netlist, on the board, with pads - because their clearance
and area must be accounted for at P6/P7.

Two things a later phase must know:
  1. `kicad-sch-api` 0.5.5 has no `dnp` field on `SchematicSymbol` at all and
     its writer hard-codes `(dnp no)`, so KiCad's NATIVE do-not-populate flag
     is unreachable from a generator. `Variant` is the only marking available
     inside `build()`.
  2. **Nothing in the skill currently reads any DNP marking** (grep-verified
     across `scripts/`: the single hit is a comment in bom_cpl.py). P9's
     `bom_cpl` derives its part list from the board's pos export, which will
     include these nine unless the orchestrator adds a filter keyed on
     parts.json `dnp: true` or on this field. Flagged, not worked around.

NET NAMING (sheets.md s2, p4-wiring-notes s5.6)
-----------------------------------------------
* `GND` / `+12V` / `+3V3` / `+48V_SW` are POWER SYMBOLS -> global, BARE.
* `EN_OK` is this sheet's ONLY hierarchical pin (in, from `control`). It
  crosses the root and becomes `/EN_OK`; the leading slash is KiCad's root
  path, not label text, so the label here is bare.
* Three nets are sheet-internal and become `/power/<NAME>`:
      V48_B    branch-B switched 48 V node (Q101 drain -> C106/C107 bulk)
      Q101_G   branch-B P-FET gate node
      Q102_D   branch-B pull-down FET drain / Q102_G its gate
  All four exist only on the DNP option and no constraint references them.

NOT ON THIS SHEET
-----------------
* No `+12V` inrush limiter. The rail comes off the carrier's always-on 100 V
  buck and is OCP-limited at 2.0 A; the ENABLE gate on `control` is what
  bounds the step (blocks.md B1).
* No output capacitor anywhere near an LED string - that rule is `drivers`'
  but it is restated because a fix loop reaches for a cap on any sheet.
* No 48 V bulk on branch A. C106/C107 are DNP and sit BEHIND Q101, on the
  drain, which is the only place a hot-swap FET can limit their inrush.

Rebuild (writes <out>/power.kicad_sch; the ROOT generator owns the project):
    .venv/Scripts/python boards/lumina-par/kicad/gen/power.py [OUT_DIR]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
BOARD = HERE.parents[2]          # boards/lumina-par
REPO = BOARD.parents[1]          # repo root
sys.path.insert(0, str(REPO / ".claude" / "skills" / "ai-ee" / "scripts"))

import schlib  # noqa: E402

# kicad-sch-api resolves lib_ids through its GLOBAL cache, which never reads
# kicad/sym-lib-table (LEARNINGS 2026-07-27) - register the pulled library.
# schlib already imported the module under a stdout redirect (it prints
# library-scan noise); reuse THAT object rather than importing it again bare,
# which would put the noise on our JSON stdout.
ksa = schlib.ksa
ksa.get_symbol_cache().add_library_path(str(BOARD / "lib" / "aiee.kicad_sym"))

# ------------------------------------------------------------------- nets
GND = "GND"
V12 = "+12V"
V3V3 = "+3V3"
V48 = "+48V_SW"
EN_OK = "EN_OK"          # hier, in from `control`; final net /EN_OK
V48_B = "V48_B"          # sheet-local, DNP only -> /power/V48_B
Q101_G = "Q101_G"        # sheet-local, DNP only
Q102_G = "Q102_G"
Q102_D = "Q102_D"

# ------------------------------------------------------------------ symbols
S_J3 = "aiee:DS1023-2*7SF11"              # default Reference "H" -> J3
S_C22U_25V = "aiee:CS3225X7R226K250NRL"   # 22uF 25V X7R 1210, horizontal
S_C10U_16V = "aiee:TCC0805X7R106K160FT"   # 10uF 16V X7R 0805, VERTICAL
S_C100N = "aiee:CC0603KRX7R9BB104"        # 100nF 50V X7R 0603, horizontal
S_C10U_100V = "aiee:FS32X106K101EGG"      # 10uF 100V X7R 1210, horizontal
S_C33N_100V = "aiee:CC0805KKX7R0BB333"    # 33nF 100V X7R 0805, VERTICAL
S_R100K = "aiee:0805W8F1003T5E_C149504"   # 100k 1% 0805
S_R10K = "aiee:0805W8F1002T5E"            # 10k 1% 0805
S_QP = "aiee:NCE01P13K"                   # P-channel, 1 G / 2 D(tab) / 3 S
S_QN = "aiee:BSS123_C427379"              # N-channel, 1 G / 2 S / 3 D
S_TP = "Connector:TestPoint"              # stock, single passive pin
S_HOLE = "Mechanical:MountingHole"        # stock, ZERO pins

# --------------------------------------------------------------- footprints
F_J3 = "aiee:HDR-TH_14P-P2.54-V-F-R2-C7-S2.54-1"   # 1.70 mm annulus (EDITS 1)
F_C1210 = "aiee:C1210"
F_C0805 = "aiee:C0805"
F_C0603 = "aiee:C0603"
F_R0805 = "aiee:R0805"
F_TO252 = "aiee:TO-252-2_L6.6-W6.1-P4.57-LS10.1-TL-CW"
F_SOT23 = "aiee:SOT-23-3_L2.9-W1.5-P1.90-LS2.6-BR"
F_TP = "TestPoint:TestPoint_Pad_D1.5mm"            # stock, bare 1.5 mm SMD pad
F_HOLE = "MountingHole:MountingHole_3.2mm_M3"      # stock, ICD s7.5

# ------------------------------------------------------------------- values
# parts/parts.json `value` verbatim for the passives; the three long
# catalogue strings (J3, Q101, Q102) are trimmed to what belongs in a
# schematic field - the LCSC code carries the exact identity.
V_J3 = "DS1023-2*7SF11 2x7 socket 2.54mm 600V"
V_22U_25V = "22uF 25V X7R 1210"
V_10U_16V = "10uF 16V X7R 0805"
V_100N = "100nF 50V X7R 0603"
V_10U_100V = "10uF 100V X7R 1210"
V_33N_100V = "33nF 100V X7R 0805"
V_100K = "100k 0805 1%"
V_10K = "10k 0805 1%"
V_QP = "NCE01P13K -100V P-MOSFET TO-252"
V_QN = "BSS123 100V N-MOSFET SOT-23"
V_TP = "TestPoint"
V_HOLE = "MountingHole_3.2mm_M3"

# LCSC codes, parts/parts.json. Stamped on every PURCHASED component: KiCad 10
# DRC raises footprint_symbol_field_mismatch without them at the P5 gate
# (LEARNINGS 2026-07-27). TP101-TP103 and H5 are bare copper / a hole and
# carry none.
LCSC = {
    "J3": "C113344",
    "C101": "C2918511", "C102": "C2918511",
    "C103": "C380347", "C104": "C380347",
    "C105": "C14663",
    "Q101": "C115989", "Q102": "C427379",
    "C106": "C5156756", "C107": "C5156756", "C108": "C327114",
    "R101": "C149504", "R104": "C149504",
    "R102": "C17414", "R103": "C17414",
}

# The branch-B option set. sheets.md s4 rule 1: these MUST be in the netlist -
# a DNP part still has pads, so its clearance and area are accounted for at
# P6/P7 and branch B stays a populate change rather than a respin.
DNP_REFS = ("Q101", "Q102", "R101", "R102", "R103", "R104",
            "C106", "C107", "C108")

# ------------------------------------------- ICD-01 rev A3 s3.1 - J3 POWER
# ***** THE DS1023 DATASHEET PUBLISHES NO PIN NUMBERS. THIS TABLE IS THE
# ***** ONLY SOURCE (p4-wiring-notes s4). Odd = row A, even = row B; the
# ***** carrier's mating J3 (boards/lumina-carrier/kicad/gen/expansion.py)
# ***** transcribes the SAME table, which is what makes the pair mate.
# Design properties, each checkable by eye against the ICD:
#   * the 48 V group is at ONE end, bounded by GND on every side (2/4/6
#     across-row, 7 along-row);
#   * column 4 (pins 7/8) is an all-GND guard column;
#   * rail order along the connector is 48 -> GND -> 12 -> 3.3, so no
#     single-position mis-seat can put a higher rail on a lower rail's pin.
# ===================== MATED-VIEW ROW SWAP - READ BEFORE EDITING ============
# This map is the ICD s3.1 table with **row A and row B EXCHANGED**, and that
# is deliberate. It is NOT a transcription error.
#
# J3 is reverse-mounted on B.Cu facing down (ICD s7.3). Flipping a 2-row
# connector to the back permutes its pin map: the two ROWS swap while the
# columns stay put. Measured on the real boards at P6 - with this board's J3
# at the carrier's anchor, all 14 pad positions coincide EXACTLY (so the pair
# mates mechanically) but carrier pin 2k+1 physically contacts daughter pin
# 2k+2.
#
# ICD s3.1 gives ONE table, pin number -> net, with no mirroring instruction,
# and LUM-CAR-A transcribed it literally on its top-side male header. If this
# board also transcribed it literally, the mated pair would join:
#     carrier 1/3/5 +48V_SW  ->  daughter 2/4/6 GND      <-- 48 V SHORTED TO GND
#     carrier 2/4/6 GND      ->  daughter 1/3/5 +48V_SW  <-- at SIX contacts
#     carrier 9 +12V -> daughter 10 GND, carrier 12 +3V3 -> daughter 11 +12V
# i.e. 12 of 14 contacts crossed, and the board destroys itself (and probably
# the carrier's eFuse) on first power-up.
#
# NO GATE IN THIS PIPELINE CAN SEE THAT: erc, netlist_audit, DRC and verify all
# compare a board against ITSELF. The defect exists only BETWEEN two boards.
# The ICD and sheets.md both flagged "check pin 1 in the MATED view, not from
# the footprint" as an open designer's-call item; this map is that check's
# answer, verified pin-by-pin against boards/lumina-carrier's own netlist.
#
# CONSEQUENCE: if J3 is ever moved to the TOP side, or the ICD re-issues s3.1,
# this swap must be re-derived - do not carry it forward blindly.
# ===========================================================================
J3_PINS = {
    "1": GND,   "2": V48,
    "3": GND,   "4": V48,
    "5": GND,   "6": V48,
    "7": GND,   "8": GND,      # column 4: the all-GND guard column (swap is a no-op)
    "9": GND,   "10": V12,
    "11": V3V3, "12": V12,
    "13": V3V3, "14": GND,
}

# Rails: (net, stock symbol, cluster origin). schlib.power_flag draws
# symbol -> label -> PWR_FLAG along one wire; `power:+48V` is re-VALUEd to
# "+48V_SW" by _place_pin1 (see the module docstring).
RAILS = [
    (GND, "power:GND", (127.0, 55.88)),
    (V12, "power:+12V", (127.0, 68.58)),
    (V3V3, "power:+3V3", (127.0, 81.28)),
    (V48, "power:+48V", (127.0, 93.98)),
]

# Bench-hazard wording. ICD s9: the whole fixture floats at PoE potential and
# an earthed probe BREAKS PD signature detection outright (detection currents
# are a few hundred microamps), so every test point carries the warning.
TP_HAZARD = "ICD s9 BENCH HAZARD silk - floating at PoE potential"


def _add(sh, ref, lib_id, value, at, footprint=None, expect=None,
         dnp=False, note=None, in_bom=True):
    """add_component + the three identity fields this board stamps.

    `in_bom=False` for the non-purchasable parts (H5's hole, the bare-copper
    test pads).  KiCad's stock MountingHole/TestPoint FOOTPRINTS already carry
    "exclude from BOM"; if the SYMBOL does not agree, kicad-cli DRC raises
    `footprint_symbol_mismatch` ("'Exclude from bill of materials' settings
    differ") once per part.  That is a WARNING, so it clears the P5/P6 gates -
    but `drc_routed` at P7 fails on warnings too, and by then the fix is a
    schematic change behind a placed and routed board.  Set it here.
    """
    fields = {}
    code = LCSC.get(ref)
    if code:
        fields["LCSC"] = code
    if dnp:
        # sheets.md s4 rule 1. See the module docstring for why this is a
        # property and not KiCad's native dnp flag.
        fields["Variant"] = "DNP"
    if note:
        fields["Note"] = note
    c = sh.add_component(lib_id, ref, value, at, footprint=footprint,
                         fields=fields or None, expect=expect)
    if not in_bom:
        c.in_bom = False
    return c


def _note(sh, at, lines, dy=5.08):
    """A block of sheet text, ONE add_text per line - an embedded newline in
    a quoted s-expression is not a form kicad-sch-api is known to round-trip,
    and a note is not worth risking the file over."""
    x, y = at
    for i, line in enumerate(lines):
        sh.sch.add_text(line, position=(x, round(y + i * dy, 4)))


def build() -> schlib.Sheet:
    sh = schlib.Sheet("power",
                      title="LUM-PAR-A: power - J3 rail entry, bulk, "
                            "test points, branch-B front end (DNP)",
                      paper="A3", date="2026-08-07", company="ai-ee",
                      pwr_base=100)

    # =====================================================================
    # A.  J3 - the 2x7 POWER socket (ICD-01 s3.1)
    # =====================================================================
    # expect= is pin-name insurance: this symbol's pin NAMES are its pin
    # NUMBERS, so it also proves pad N exists for every N in 1..14.
    _add(sh, "J3", S_J3, V_J3, (63.5, 76.2), footprint=F_J3,
         expect={str(n): str(n) for n in range(1, 15)},
         note="Bottom side, reverse-mounted, facing down - ICD s7.3")
    sh.wire_pins("J3", J3_PINS)

    # =====================================================================
    # F.  Rails - the ONLY PWR_FLAGs on this board (see module docstring)
    # =====================================================================
    for net, sym, at in RAILS:
        sh.power_flag(net, at=at, sym=sym, flag=True)

    # =====================================================================
    # C.  TP101-TP103 - bench test pads, one per rail
    # =====================================================================
    # Bare 1.5 mm SMD pads. TP103 sits on +48V_SW and is half the reason the
    # rail is landed at all: the rail becomes measurable at bring-up without
    # a probe on a bare connector pad (blocks.md B1).
    for ref, net, x in (("TP101", V12, 177.8),
                        ("TP102", V3V3, 203.2),
                        ("TP103", V48, 228.6)):
        _add(sh, ref, S_TP, V_TP, (x, 55.88), footprint=F_TP,
             expect={"1": "1"}, note=TP_HAZARD, in_bom=False)
        sh.wire_pin(ref, "1", net)

    # =====================================================================
    # D.  H5 - CAR-REQ-15 board-to-board support hole
    # =====================================================================
    # ICD s7.5: `board_init --mounting-holes` generates the four CORNER holes
    # only, so the 5th is added here to carry a refdes and a deterministic
    # placement (constraints.json placement.fixed keys on H5 at (46, 74),
    # board-local - and stackup.md TRAP 2's translation applies to it).
    # ZERO pins, so it joins no net; it is on the schematic purely to own an
    # identity that P6 can address.
    _add(sh, "H5", S_HOLE, V_HOLE, (279.4, 55.88), footprint=F_HOLE,
         note="ICD s7.5 - place_edit to (46,74) board-local at P6",
         in_bom=False)

    # =====================================================================
    # B.  Bulk and HF decoupling of the two LOADED rails
    # =====================================================================
    # +12V: 2 x 22 uF / 25 V. 25 V on a 12 V rail is 2x BEFORE DC-bias
    # derating; the rail carries 0.717 A worst case (power_tree s3 rev B).
    # Horizontal symbol: pin 1 left, pin 2 right.
    for ref, y in (("C101", 127.0), ("C102", 152.4)):
        _add(sh, ref, S_C22U_25V, V_22U_25V, (63.5, y), footprint=F_C1210,
             expect={"1": "1", "2": "2"})
        sh.wire_pins(ref, {"1": V12, "2": GND})

    # +3V3: 2 x 10 uF / 16 V + 1 x 100 nF. That rail carries <= 5 mA of logic
    # and sense only and NEVER LED current (D-02, power_tree s4).
    # VERTICAL symbol: pin 2 on top, pin 1 below - rail on top.
    for ref, y in (("C103", 127.0), ("C104", 152.4)):
        _add(sh, ref, S_C10U_16V, V_10U_16V, (127.0, y), footprint=F_C0805,
             expect={"1": "1", "2": "2"})
        sh.wire_pins(ref, {"2": V3V3, "1": GND})
    _add(sh, "C105", S_C100N, V_100N, (190.5, 127.0), footprint=F_C0603,
         expect={"1": "1", "2": "2"})
    sh.wire_pins("C105", {"1": V3V3, "2": GND})

    # =====================================================================
    # E.  BRANCH-B FRONT END - DNP ON BRANCH A.  Do not delete.
    # =====================================================================
    # Topology (blocks.md B1): a high-side 100 V P-FET whose gate is pulled
    # UP to the raw 48 V and pulled DOWN through a series resistor from
    # /EN_OK, with a gate-to-drain capacitor setting dV/dt.
    #
    #   +48V_SW --+--------------------- S  Q101  D ----+---- V48_B
    #             |                      |              |
    #            R101 (100k, 0805)       +--- C108 -----+   (Cgd, 33nF/100V)
    #             |                                      |
    #             +---------- Q101_G ---------+        C106 || C107
    #                            |            |         (2 x 10uF/100V)
    #                          R102 (10k)     |            |
    #                            |           GND ---------+
    #                        Q102_D
    #                            |
    #             /EN_OK --R103-- G Q102 (BSS123)  S --> GND
    #
    # Why each element is what it is (parts/parts.json role text, P2/P3):
    #   * Q101 is TO-252 and not SOT-23 on purpose - the sizing target is
    #     <= 0.30 A inrush at ~15 V/ms, a ~3.2 ms ramp and ~23 mJ of SOA
    #     energy that must be checked at 56-72 C AMBIENT, not the datasheet's
    #     25 C case (E-5, L-14).
    #   * The inrush target is set against the TPS2378's 0.85 A MINIMUM
    #     current limit (E-6) - not its 1.0 A typical, and emphatically not
    #     the connector's 5.4 A.
    #   * R101 100 k from the rail sources ~0.48 mA into the gate node, so
    #     with C108 = 33 nF the ramp is ~14.5 V/ms and the inrush is
    #     20 uF x 14.5 V/ms = 0.29 A, inside the 0.30 A target.
    #   * Q102 is 100 V and NOT 60 V: a 2N7002 at 60 V leaves 5 % margin on a
    #     57 V worst-case rail. Vgs(th) 1.8 V, so 3.3 V /EN_OK drives it.
    #   * C106/C107 sit on the DRAIN, behind Q101. That is the only place a
    #     hot-swap FET can limit their inrush; on the raw side the connector
    #     would charge them directly and the FET would do nothing.
    #   * ICD s5.4 mandates 0805 resistors and 100 V capacitors across the
    #     48 V domain. Both hold here, which is exactly why branch B needs no
    #     footprint change (sheets.md s1.1).
    #
    # Q101 pin geometry: G stubs LEFT, D stubs UP, S stubs DOWN.
    _add(sh, "R101", S_R100K, V_100K, (63.5, 203.2), footprint=F_R0805,
         expect={"1": "1", "2": "2"}, dnp=True)
    sh.wire_pins("R101", {"1": V48, "2": Q101_G})
    _add(sh, "Q101", S_QP, V_QP, (127.0, 203.2), footprint=F_TO252,
         expect={"1": "G", "2": "D", "3": "S"}, dnp=True,
         note="P-channel: 1=G, 2=D(tab), 3=S - C115989 pinout")
    sh.wire_pins("Q101", {"1": Q101_G, "2": V48_B, "3": V48})
    # Cgd: gate-to-drain, NOT gate-to-ground. Vertical symbol, pin 2 on top.
    _add(sh, "C108", S_C33N_100V, V_33N_100V, (190.5, 203.2),
         footprint=F_C0805, expect={"1": "1", "2": "2"}, dnp=True)
    sh.wire_pins("C108", {"2": V48_B, "1": Q101_G})
    for ref, y in (("C106", 203.2), ("C107", 228.6)):
        _add(sh, ref, S_C10U_100V, V_10U_100V, (254.0, y), footprint=F_C1210,
             expect={"1": "1", "2": "2"}, dnp=True)
        sh.wire_pins(ref, {"1": V48_B, "2": GND})

    # The /EN_OK half of the gate network.
    _add(sh, "R103", S_R10K, V_10K, (63.5, 241.3), footprint=F_R0805,
         expect={"1": "1", "2": "2"}, dnp=True)
    sh.wire_pins("R103", {"1": EN_OK, "2": Q102_G})
    _add(sh, "R102", S_R10K, V_10K, (127.0, 241.3), footprint=F_R0805,
         expect={"1": "1", "2": "2"}, dnp=True)
    sh.wire_pins("R102", {"1": Q101_G, "2": Q102_D})
    _add(sh, "Q102", S_QN, V_QN, (190.5, 241.3), footprint=F_SOT23,
         expect={"1": "G", "2": "S", "3": "D"}, dnp=True,
         note="N-channel: 1=G, 2=S, 3=D - C427379 pinout")
    sh.wire_pins("Q102", {"1": Q102_G, "2": GND, "3": Q102_D})

    # R104 - the CAR-REQ-17 bleed, +48V_SW to GND, 0805 per ICD s5.4.
    # NOTE FOR WHOEVER POPULATES BRANCH B: this bleed is on the RAW rail,
    # UPSTREAM of Q101, which is where parts.json's role text puts it and
    # where it belongs on branch A (the only 48 V node that exists). On
    # branch B the stored energy is on V48_B, BEHIND Q101, so this resistor
    # alone does not discharge C106/C107 - a second bleed across the bank, or
    # moving this one to V48_B, is part of that populate change.
    _add(sh, "R104", S_R100K, V_100K, (63.5, 266.7), footprint=F_R0805,
         expect={"1": "1", "2": "2"}, dnp=True)
    sh.wire_pins("R104", {"1": V48, "2": GND})

    # =====================================================================
    # sheet interface - ONE hierarchical pin
    # =====================================================================
    # Free-cluster variant (schlib.hier_pin `at=`): local label at one end,
    # hierarchical label at the other, joined by wire GEOMETRY rather than by
    # label name-merging. `input` because `control` (U201) drives it; the
    # child-side label comes out `input` regardless of what is asked for
    # (kicad-sch-api 0.5.5 drops the shape), and KiCad does not check
    # sheet-pin/label shape parity - the ROOT side is the one that lands.
    sh.hier_pin(EN_OK, shape="input", at=(25.4, 190.5))

    # =====================================================================
    # sheet notes - what a human opening the .kicad_sch has to be told
    # =====================================================================
    # The notes column lives at x = 330.2, clear of every symbol (H5 at
    # 279.4 is the right-most) and ABOVE the A3 title block, whose top edge
    # sits near y = 246 - the first pass ran the last block to y = 256.5 and
    # printed over it.
    _note(sh, (330.2, 63.5), [
        "J3 PIN NUMBERS: ICD-01 s3.1 ONLY.",
        "The DS1023 datasheet publishes none.",
        "Bottom side, reverse-mounted, facing down",
        "(ICD s7.3) - side is set at P6, and pin 1",
        "must be checked in the MATED view, not",
        "from the footprint.",
    ])
    _note(sh, (330.2, 101.6), [
        "+48V_SW IS LANDED, NOT TAPPED (branch A).",
        "J3 1/3/5 -> TP103 + DNP bleed R104, and",
        "stops. No 48 V bulk is stored, so",
        "CAR-REQ-17 is not triggered; R104 exists",
        "so it is met the instant any is added.",
        "0.635 mm outer clearance, board-wide, on",
        "every 48 V net (ICD s5.4).",
    ])
    _note(sh, (330.2, 144.78), [
        "TEST POINTS CARRY THE ICD s9 BENCH-HAZARD",
        "SILKSCREEN. The fixture floats at PoE",
        "potential; an earthed probe breaks PD",
        "signature detection outright. Silk text is",
        "a P6/P7 place_edit add_text op.",
    ])
    _note(sh, (330.2, 177.8), [
        "THIS SHEET OWNS THE PWR_FLAGS for GND,",
        "+12V, +3V3 and +48V_SW. Every rail enters",
        "through J3's passive pins. Do NOT add a",
        "second flag on another sheet: PWR_FLAG is",
        "a power_out pin and two of them collide.",
    ])
    _note(sh, (330.2, 210.82), [
        "BRANCH-B FRONT END (Q101/Q102/R101-R104/",
        "C106-C108) IS DNP ON BRANCH A, and is in",
        "the netlist on purpose - a DNP part still",
        "has pads, so its clearance and area are",
        "accounted for at P6/P7 and branch B stays",
        "a populate change, not a respin.",
    ])
    return sh


def main(argv=None) -> int:
    # Default out dir is kicad/, and project=False: the ROOT generator owns
    # <root>.kicad_pro, this sheet must never write one.
    out_dir = Path(argv[0]) if argv else BOARD / "kicad"
    try:
        sh = build()
        path = sh.save(out_dir, project=False)
    except Exception as exc:  # noqa: BLE001  (SPEC 6: any error -> exit 2)
        print(json.dumps({"script": "gen.power", "status": "error",
                          "error": f"{type(exc).__name__}: {exc}"}))
        return 2
    print(json.dumps({
        "script": "gen.power", "status": "pass",
        "sheet": str(path),
        "components": len(list(sh.sch.components)),
        "hier_pins": sorted(sh.hier_pins),
        "rails_flagged": [net for net, _, _ in RAILS],
        "internal_nets": sorted({V48_B, Q101_G, Q102_G, Q102_D}),
        "dnp": sorted(DNP_REFS),
        "decoupling_associations": len(sh.decoupling),
        "field_placement": sh.place_report,
    }, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
