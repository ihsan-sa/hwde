"""LUM-PAR-A `led_if` sheet - B6: J5 LED harness header, TVS clamps, TC pads.

The SOURCE of this sheet is this file; `kicad/led_if.kicad_sch` is BUILD
OUTPUT. Standalone rebuild (writes the sheet only - the root generator owns
the .kicad_pro):

    .venv/Scripts/python boards/lumina-par/kicad/gen/led_if.py <out_dir>

The library pin types are ALREADY retyped (`reports/lib_pin_types.json`,
193 pins changed); do not re-run `lib_pin_types.py` here. Every pin this
sheet touches is `passive`, so the retype is what keeps the untouched
easyeda2kicad `unspecified` types from flooding ERC with `pin_to_pin`
warnings (LEARNINGS 2026-07-27).

The root generator imports `build()` and stitches this sheet with
`schlib.Project.add_sheet(led_if.build(), at=..., size=..., nets=HIER_NETS)`.
`HIER_NETS` below is the exact, ordered sheet-pin list the root must pass.

REFDES 500-599, `#PWR` base 500 (sheets.md s1). J5 is exempt by name - it is
this board's own harness header and follows the connector sequence after
J3/J4 (sheets.md s1 "Exception").

THE OPEN P4 ACTION, SETTLED: J5 IS SIDE ENTRY, AND THAT IS THE RIGHT PART
-------------------------------------------------------------------------
`p4-wiring-notes.md` s4 flags the entry direction as an open action because
`parts/C265014.json` calls S10B-PH-SM4-TB side entry while "the JST B-prefix
convention reads as top entry". Settled from the datasheet's own text layer
(`parts/C265014.pdf`, page 3, "SMT type shrouded header" table):

  * the Model No. column is split `Top entry type | Side entry type`;
  * the TOP-entry column lists B2B-PH-SM4-TB ... B16B-PH-SM4-TB;
  * the SIDE-entry column lists S2B-PH-SM4-TB ... S15B-PH-SM4-TB.
  * The same split appears twice more in the same PDF - page 2's through-hole
    table (B*B-PH-K-S top / S*B-PH-K-S side) and page 3's low-insertion-force
    table (B*B-PH-KL / S*B-PH-KL).

So the entry direction is the LEADING letter, not the "B" in "10B" (that B is
in every model number of the series, top and side alike). `S`10B-PH-SM4-TB is
SIDE ENTRY (right-angle): the mating wire bundle leaves PARALLEL to the PCB.
The extract was right and the ordered part is the right one - no swap-part.

Why side entry is also CORRECT for this board, not merely what was ordered:
  * The LED module does NOT mount to this board (stackup.md T-7 / ENC-10: a
    55 x 55 mm MCPCB on the enclosure wall with its own ~29-30 mm stack), so
    the harness has to leave the board laterally in every scenario.
  * `stackup.md` s1.1 puts J5 on **B.Cu**, and ICD s7.3 fixes the mated
    board-to-board height at **11.0 mm**. A top-entry header there would fire
    the mated PHR-10 housing plus its wire bend radius straight down into the
    carrier 11 mm below. The side-entry SMT wafer is 5.5 mm high and 6 mm
    deep, so it lives inside that gap and exits horizontally past the top
    edge.
  * `constraints.json.placement.edges` already puts J5 on the **top** edge at
    x ~ 56 mm, clear of the RJ45 notch (x 6-36) and the recovery-header
    keepout (x 76-98); 24.2 mm of land across x ~ 44-68 fits that span.

WHAT THIS LEAVES FOR P6 - a placement obligation, not a part change: the
side-entry land pattern is ASYMMETRIC front-to-back (extract layout_notes:
the two solder tabs sit 0.2 mm beyond the wafer's MATING end face, the 10
circuit pads sit 5.5-9.0 mm behind it, total land depth 9.2 mm). J5 must be
oriented with the wafer end face pointing OUT across the top edge and must
NOT be mirrored - "placing the footprint mirrored puts the connector opening
on the wrong side of the board edge". Check that in the MATED view, the same
way ICD s7.2 requires for J3/J4, not from the footprint.

J5 HARNESS PIN MAP - DEFINED HERE (no upstream document assigns it)
--------------------------------------------------------------------
`sheets.md` s1.5, `blocks.md` B6 and `power_tree.md` s157 all fix the
CONDUCTOR SET (4 anode + 4 per-channel return + /NTC_LED + a dedicated NTC
sense return) but no document assigns circuit numbers. This map is therefore
a NEW module-facing interface fact and has to reach the harness/module build
sheet:

    1  /LED0_A      2  GND (ch0 return)
    3  /LED1_A      4  GND (ch1 return)
    5  /LED2_A      6  GND (ch2 return)
    7  /LED3_A      8  GND (ch3 return)
    9  GND (NTC sense return)        10  /NTC_LED

  * Anode and its own return are ADJACENT so each channel is one crimp pair
    and the "twisted with its own return" rule (blocks.md B6: the harness
    sits inside the shunt-FET commutation loop) is achievable by construction.
  * The high-impedance NTC node is at the extreme end, pin 10, with TWO
    ground pins (8, 9) between it and the nearest switching anode (pin 7).
  * Pin 1 carries the datasheet's own "Circuit No.1" marking, which is on
    both the land-pattern drawing and the body figure.

THE DEDICATED NTC RETURN IS A SEPARATE PIN, NOT A SEPARATE NET
---------------------------------------------------------------
blocks.md B6 requires the NTC return to be "joined to GND only at the
comparator reference point; must not share a conductor with LED current".
The CONDUCTOR half is satisfied here and is netlist-visible: pin 9 is its own
J5 circuit, so no LED return current ever flows in the NTC sense wire.
The SINGLE-POINT-JOIN half is NOT expressible in the netlist - pins 2/4/6/8/9
are all `GND` (sheets.md s2 defines no separate return net, and inventing one
would be a net P5-P8 silently no-op on). It therefore becomes a P6/P7
obligation: pin 9's copper must reach GND at the analogue reference point
near U401, not be stitched into the plane at the connector. Flagged to the
orchestrator - there is no gate that enforces it.

J5 PINS 11/12 ARE MECHANICAL, AND ARE NO-CONNECTS
---------------------------------------------------
The symbol's 12 pins are 10 circuits + 2 solder tabs, and the pulled
footprint numbers them the same way (pads 11/12, 1.5 x 3.4 mm, on the mating
side). `parts/C265014.json` states the tabs are "PCB retention ... Not an
electrical circuit - the datasheet counts 10 circuits". The mating housing is
plastic PHR-10 with no shell, so the tabs carry no ESD path either. They are
flagged `~` no-connect: retention only, and off the GND plane so the two pads
that mechanically hold the harness down reflow with an even thermal profile.

TVS POLARITY IS NOT A COIN TOSS
--------------------------------
SMF15A is UNIDIRECTIONAL (a trailing "C" would be the bidirectional
SMF15CA). `parts/C435484.json`: page-4 pinning table "Pin1 cathode, Pin2
anode", cathode band at the pin-1 end. Cathode faces the positive harness
line (/LEDn_A), anode to GND - "a reversed SMF15A conducts as a forward diode
at ~1 V and shorts the harness". Incoming-reel check: marking code LM
(bidirectional SMF15CA is UM, and carries no cathode band at all).
15 V standoff is the BRANCH A value (33 V on branch B - same SOD-123 land, a
BOM value change). Branch A headroom: VRWM 15 V over a 12 V rail whose
open-circuit excursion is toward VIN, VBR(min) 16.7 V, VC 24.4 V at 8.2 A.

NO 48 V REACHES THIS SHEET, EVER (D-T13)
-----------------------------------------
That is what keeps the 0.635 mm clearance rule, the 100 V capacitor rule and
the 0805-minimum resistor rule off the harness and the module. Nothing here
wants `+48V_SW`; if a fix loop ever routes it to this sheet, stop.
Also from blocks.md B6, for whoever reviews this next: there is NO output
capacitor across an LED string anywhere on this board - a shunt FET dumps it
every PWM cycle - so a "missing bulk cap at the connector" finding is wrong.

NET NAMING (sheets.md s2 / p4-wiring-notes.md s6)
--------------------------------------------------
* `GND` is a bare GLOBAL power symbol, not a hierarchical pin. A local label
  alone on a child sheet would give `/led_if/GND` and `netlist_audit
  --constraints` would raise missing_net at ERROR severity.
* No PWR_FLAG here, and that is a cross-sheet contract, not a local style
  choice (confirmed by the `power` sheet agent). Every rail enters the board
  through J3's passive pins on `power`, so `power` owns ALL FOUR flags -
  GND, +12V, +3V3, +48V_SW - and flags each exactly once. This sheet places
  CONSUMING power symbols only (`flag=False`). A PWR_FLAG pin is `power_out`,
  so a second flag on GND would collide `power_out <-> power_out` at the
  project ERC and fail the gate - the same failure mode p4-wiring-notes.md s2
  warns about on the driver VCC nodes. GND is this sheet's only rail.

SHEET-ONLY ERC, MEASURED (kicad-cli 10.0.3, this file built standalone into a
scratch dir): 6 errors + 1 warning, ALL of them artefacts of building a CHILD
sheet with no parent, and all expected to clear in the stitched project:
  * 1x `power_pin_not_driven` on #PWR500 - the GND flag lives on `power`;
  * 5x `pin_not_connected` "Hierarchical label '<net>' in root sheet cannot be
    connected to non-existent parent sheet" - standalone, this file IS the
    root; the root stitch is what gives these labels a sheet pin;
  * 1x `isolated_pin_label` on NTC_LED - only J5 pin 10 sits on that net HERE;
    it gains the `thermal` sheet's pins through the sheet pin.
Netlist verified on the same build: /LED0_A..3_A = {J5 anode, TVS cathode}
each, /NTC_LED = {J5.10}, GND = 4 TVS anodes + J5.2/4/6/8/9 + both TC pads,
and pads 11/12 come out as `unconnected-(J5-Pad11/12)` singletons.
* The five nets in HIER_NETS cross the root and become `/NAME`. The root must
  place a root-sheet local label spelled exactly as in sheets.md s2 on each.
* This sheet has NO sheet-internal signal nets.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
BOARD = HERE.parents[2]          # boards/lumina-par
REPO = HERE.parents[4]           # repo root
sys.path.insert(0, str(REPO / ".claude" / "skills" / "ai-ee" / "scripts"))

import kicad_sch_api as ksa  # noqa: E402

# kicad-sch-api resolves lib_ids through its GLOBAL cache, which never reads
# kicad/sym-lib-table (LEARNINGS 2026-07-27) - register the pulled lib.
ksa.get_symbol_cache().add_library_path(BOARD / "lib" / "aiee.kicad_sym")

import schlib  # noqa: E402

# ---------------------------------------------------------------- symbols
S_J5 = "aiee:S10B-PH-SM4-TB"        # default Reference "U" -> forced to J5
S_TVS = "aiee:SMF15A_C435484"       # default Reference "D" -> D501..D504
S_TP = "Connector:TestPoint"        # stock KiCad, 1 passive pin

# ------------------------------------------------------------- footprints
# CONN-SMD_...: the SIDE-ENTRY recommended layout, 12 pads (10 circuits +
# 2 solder tabs), fp_verify_J5_C265014.json = pass.
F_J5 = "aiee:CONN-SMD_S10B-PH-SM4-TB-LF-SN"
F_SOD123 = "aiee:SOD-123_L2.7-W1.8-LS3.7-RD"
# Single SMD pad on F.Cu + F.Mask and NO paste = bare copper under a mask
# opening, which is exactly what a thermocouple pad is. 2.0 mm square takes a
# type-K bead and its adhesive; the footprint is already
# exclude_from_bom/exclude_from_pos_files.
F_TC_PAD = "TestPoint:TestPoint_Pad_2.0x2.0mm"

# ------------------------------------------------------------------ values
V_J5 = "S10B-PH-SM4-TB JST PH 10-way SMD header, 2.0 mm"
V_TVS = "SMF15A 15V unidirectional TVS, SOD-123"     # branch A; 33 V on B
V_TC = "thermocouple pad, bare Cu"

# LCSC codes, parts/parts.json. Stamped on every PURCHASED component: KiCad
# 10 DRC raises footprint_symbol_field_mismatch without them at the P5 gate
# (LEARNINGS 2026-07-27). TP501/TP502 are footprints, not parts.
LCSC = {
    "J5": "C265014",
    "D501": "C435484", "D502": "C435484",
    "D503": "C435484", "D504": "C435484",
}

# --------------------------------------------------- J5 harness pin map
# See the module docstring for the derivation. Pads 11/12 are the mechanical
# solder tabs, not circuits.
J5_PINS = {
    "1": "LED0_A",  "2": "GND",     # ch0 anode + its own return, twisted
    "3": "LED1_A",  "4": "GND",     # ch1
    "5": "LED2_A",  "6": "GND",     # ch2
    "7": "LED3_A",  "8": "GND",     # ch3
    # Pin 9 is the DEDICATED NTC sense return - electrically GND, physically
    # its own harness conductor so no LED current shares it (blocks.md B6).
    # Two ground pins (8, 9) sit between the switching anode on 7 and the
    # high-impedance sense node on 10.
    "9": "GND",     "10": "NTC_LED",
    # Solder tabs: PCB retention, not circuits (parts/C265014.json).
    "11": "NC",     "12": "NC",
}

# One TVS per CHANNEL at the header (blocks.md B6). Cathode (pin 1) to the
# positive harness line, anode (pin 2) to GND.
TVS = [("D501", "LED0_A"), ("D502", "LED1_A"),
       ("D503", "LED2_A"), ("D504", "LED3_A")]

# The ordered sheet-pin list the ROOT must pass as `nets=`. Shapes are THIS
# sheet's point of view (sheets.md s2): the four anodes arrive from `drivers`,
# the module NTC node leaves toward `thermal`. They land on the ROOT's sheet
# pins; the child's own hierarchical labels come out `input` regardless
# (kicad-sch-api 0.5.6 drops the shape argument) and KiCad checks no parity.
HIER_NETS = [
    ("LED0_A", "input"), ("LED1_A", "input"),
    ("LED2_A", "input"), ("LED3_A", "input"),
    ("NTC_LED", "output"),
]

# Bare-copper thermocouple pads for bring-up thermal verification next to the
# header (stackup.md T-6 / L-13). Both carry the ICD s9 bench-hazard
# silkscreen - a P6 silk task, recorded here so it is not lost.
TC_PADS = ["TP501", "TP502"]


def build() -> schlib.Sheet:
    sh = schlib.Sheet(
        "led_if",
        title="LUM-PAR-A: led_if - J5 LED harness, TVS clamps, TC pads (B6)",
        paper="A3", date="2026-08-07", company="ai-ee", pwr_base=500)

    # ======================================= J5 - LED harness header, 10-way
    # expect= is pin-name insurance: this symbol's pin NAMES are its pin
    # NUMBERS, so it also proves pad N exists for every N - including the two
    # solder-tab pads 11/12, which the extract numbers MP1/MP2.
    sh.add_component(S_J5, "J5", V_J5, at=(76.2, 88.9), footprint=F_J5,
                     expect={str(n): str(n) for n in range(1, 13)})
    # Pin 10 is wired further down by hier_pin's pin-stub variant, which
    # emits its own stub - wiring it here too would duplicate the wire.
    sh.wire_pins("J5", {p: n for p, n in J5_PINS.items() if p != "10"})

    # ============================================ GND - global power symbol
    # One symbol makes the net global and BARE across the hierarchy; every
    # other "GND" label on this sheet name-merges onto it. No PWR_FLAG (the
    # `power` sheet owns the source).
    sh.power_flag("GND", at=(25.4, 88.9), sym="power:GND", flag=False)

    # ==================================== D501-D504 - one TVS per channel
    # Cathode -> anode net, anode -> GND. Reversed, the part is a forward
    # diode at ~1 V and shorts the harness (parts/C435484.json).
    for i, (ref, net) in enumerate(TVS):
        sh.add_component(S_TVS, ref, V_TVS, at=(152.4, 55.88 + i * 20.32),
                         footprint=F_SOD123, expect={"1": "C", "2": "A"})
        sh.wire_pins(ref, {"1": net, "2": "GND"})

    # ================================== TP501/TP502 - thermocouple pads
    # Tied to GND ON PURPOSE (ASSUMED - no document names a net for them).
    # GND is the In1 solid plane, i.e. this board's thermal spreader, so a
    # GND-tied pad next to J5 reads real board temperature and corroborates
    # RT401 on the driver stage; an isolated pad would read only its own patch
    # of FR4. It is also why the ICD s9 bench-hazard silk applies at all -
    # board GND is the floating PoE return, so an earthed thermocouple here
    # breaks PD signature detection. One-line change if the orchestrator
    # would rather have them isolated.
    for i, ref in enumerate(TC_PADS):
        sh.add_component(S_TP, ref, V_TC, at=(266.7, 55.88 + i * 20.32),
                         footprint=F_TC_PAD, expect={"1": "1"})
        sh.wire_pin(ref, "1", "GND")

    # ============================================= hierarchical sheet pins x5
    # LEDn_A: free-cluster variant - local label at one end, hierarchical
    # label at the other, joined by wire GEOMETRY rather than by label
    # name-merging. Each of these nets carries 2+ components (J5 + its TVS).
    # NTC_LED: pin-stub variant. It touches exactly ONE component on this
    # sheet (J5 pin 10 - the module NTC and its divider top leg are off-sheet),
    # so hanging the hierarchical label straight off that pin's stub removes
    # the name-merge step entirely instead of adding a second label pair that
    # would have to find it.
    for i, (net, shape) in enumerate(HIER_NETS):
        if net == "NTC_LED":
            sh.hier_pin(net, shape=shape, ref="J5", pad="10")
        else:
            sh.hier_pin(net, shape=shape, at=(215.9, 55.88 + i * 10.16))

    for ref, code in LCSC.items():
        sh.sch.components.get(ref).set_property("LCSC", code)
    return sh


def main(argv=None) -> int:
    out_dir = Path(argv[0]) if argv else HERE.parents[1]   # .../kicad
    project = bool(argv[1:] and argv[1] == "--project")
    try:
        sh = build()
        sch = sh.save(out_dir, project=project)
    except Exception as exc:  # noqa: BLE001  (SPEC 6: any error -> exit 2)
        print(json.dumps({"script": "gen.led_if", "status": "error",
                          "error": f"{type(exc).__name__}: {exc}"}))
        return 2
    print(json.dumps({
        "script": "gen.led_if", "status": "pass",
        "sheet": "led_if",
        "files": [str(sch)],
        "components": len(LCSC) + len(TC_PADS),
        "hier_pins": [n for n, _ in HIER_NETS],
        "internal_nets": [],
        "j5_pin_map": J5_PINS,
        "no_connects": [p for p, n in J5_PINS.items() if n == "NC"],
        "decoupling_associations": len(sh.decoupling),
        "field_placement": sh.place_report,
    }, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
