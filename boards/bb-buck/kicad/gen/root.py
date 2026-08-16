"""bb-buck root generator - THE WHOLE SCHEMATIC (one flat root sheet).

18-30 V -> 5.0 V / 2 A synchronous buck (TI LMR33630ADDAR, SOIC-8-EP).
Build mode ULTRA-BARE-BONES: one functional block plus only datasheet-
required support.  No protection, no indicator, no second rail, no UVLO
divider, no soft-start parts, no snubber - every part below is either in
`parts/parts.json` (a BOM line) or non-purchased geometry that
`architecture/constraints.json` names (TP1/TP2, H1-H4).

    Rebuild:  .venv\\Scripts\\python.exe boards/bb-buck/kicad/gen/root.py
    Outputs:  ../bb-buck.kicad_sch  ../bb-buck.kicad_pro  ../decoupling.json

The Python is the SOURCE; the .kicad_sch is build output.  Every pin number
and every wiring decision below comes from the datasheet extract
`parts/C841384.json` or from the project symbol library's own pin table,
never from memory.  `expect=` on U1 is pin-name insurance.

=====================================================================
1.  NET CONTRACT (architecture/sheets.md s2 - BINDING, do not "tidy")
=====================================================================
BARE global nets, made bare by a POWER SYMBOL whose Value names the net
(a power symbol's exported net name is its VALUE and the symbol WINS over
a coincident local label - LEARNINGS 2026-07-28):

    +VIN   +5V   GND

Root-sheet LOCAL labels, which KiCad exports with ONE leading slash:

    /SW  /FB  /BST      (declared or deliberately-undeclared, s4 of sheets.md)
    /VCC                (ADDED here - see s3 below)

*** The label TEXT written below is BARE ("SW", "FB", "BST", "VCC").  The
leading `/` is the ROOT SHEET PATH that KiCad prepends on export.  Typing
the slash into the label instead yields the escaped net `/{slash}SW` -
silently, with a clean build and a clean ERC - and every constraints.json
match then fails.  Measured on sbuck-5v3a before the fix (LEARNINGS
2026-08-09).  Verify with the exported net names, never by reading the
schematic. ***

`+VIN` has no stock power symbol; `power:VBUS` carries it with its Value
set to the net name, which is what schlib.power_flag does.

=====================================================================
2.  parts.json OVERRIDES architecture/sheets.md s3 IN THREE PLACES
=====================================================================
sheets.md s3 was written at P2 from the block diagram; P3 corrected it from
the datasheet and parts.json is the BOM of record.  The three deltas, all
implemented below:

  (1) C1, the HF input bypass, is 220 nF / 50 V / X7R, NOT 100 nF.
      Datasheet 9.2.2.6 is specific: "a small case size, 220-nF ceramic
      capacitor must be used at the input ... must also be rated at 50 V
      with an X7R dielectric."
  (2) C4/C5, the output bank, are 1210 / 22 uF / 25 V, NOT 1206.  No
      22 uF / 25 V / X7R part is stocked in 1206; 1210 is also the case the
      datasheet's own reference design uses (9.2.2.5).
  (3) C7 = C_VCC, 1 uF / 25 V X7R on the VCC pin, was MISSING from
      sheets.md entirely.  Datasheet 9.2.2.8: VCC "requires a 1-uF, 16-V
      ceramic capacitor connected from VCC to GND for proper operation."
      It is not optional and it is not decoration - it is the bypass for
      the internal LDO that supplies the gate drivers.

(3) is what forces the fourth local label, `/VCC`: the VCC pin needs a node
name and no canonical name exists for it.  It is an ADDITION, not a rename
- nothing in constraints.json refers to it, so no `missing_net` can arise -
and it cannot be mistaken for half of a differential pair (no _P/_N/DP/DM/
+/- suffix, and constraints.json.diff_pairs is an explicit empty list).

=====================================================================
3.  THE FOUR PIN-HANDLING JUDGMENTS, each resolved from C841384.json
=====================================================================
EN (pin 3) -> tied directly to `+VIN`, ZERO added parts.
    Table 6-1, EN pin function, verbatim: "Enable input to regulator.
    High = ON, low = OFF.  Can be connected directly to VIN.  Do not
    float."  Checked against the pin's OWN behaviour before adding any
    part, which is what knowledge record `buck-precision-en-fixed-softstart`
    demands: this is a PRECISION-threshold input (V_EN-H 1.2/1.231/1.26 V)
    with 0.2 nA of leakage - i.e. NOTHING internal defines the pin, so the
    library's usual "many parts auto-start, a divider is wasted parts" is
    the other case and floating is forbidden.  The direct VIN tie the
    datasheet names is therefore the fewest-parts always-on wiring.  No
    UVLO divider (mode-excluded, and decisions A2 removes the cable-droop
    motorboating case) and no soft-start parts (soft start is fixed
    internally at 4 ms typ with no SS pin; Cout inrush ~ Cout*Vout/tSS,
    about 55-65 mA on top of the load).
    Abs-max check: EN_to_AGND_max = VIN + 0.3 V, so EN at VIN is inside
    rating by construction at every input voltage.

PG (pin 4) -> explicit NO-CONNECT.
    Open-drain power-good output.  This board has no indicator and no
    consumer for it by mode (requirements.md s2: "no power-good").
    Table 6-1: "Can be left open when not used."  An output may float, but
    it is flagged no-connect rather than left dangling so the intent is in
    the file and ERC stays silent about it.  (Note the datasheet's other
    remark - the PG pull-up may be taken from VCC - is NOT taken up: there
    is nothing to pull up to and 9.2.2.8 forbids loading VCC otherwise.)

EP (pin 9) -> `GND`.
    The exposed pad is AGND, not a thermal-only pad: Table 6-1 states "All
    electrical parameters are measured with respect to this pin" and "This
    pad must be soldered to a ground plane."  AGND and PGND are the same
    net on this board (abs-max AGND-to-PGND is +/-0.3 V, i.e. they are
    meant to be tied).  The project symbol names pin 9 "EP" while the
    datasheet calls it AGND - a naming difference only; `expect` below
    asserts the symbol's own name so a library refresh cannot silently
    move the pad.  The >= 16-via 0.3 mm thermal array under it is a P6/P7
    review item (constraints.json _review_enforced (1)); nothing in the
    schematic can express it.

BOOT (pin 7) -> `/BST` with C6 100 nF to `/SW`, datasheet-required
    (9.2.2.7).  BOOT is typed `power_in` in the pulled library, and the
    bootstrap rail has no schematic-visible driver (the internal boot diode
    from VCC is inside the package), so ERC would raise
    `power_pin_not_driven` on a net that is correct.  Fixed at the SOURCE
    by `gen/lib_pin_types.py`, which retypes that one pin to `passive` -
    the same typing sbuck-5v3a's AP64350 BST pin carries.  Fixing it in the
    library rather than with a PWR_FLAG also keeps `/BST` out of
    netlist_audit's `power_undeclared` warning, which matters because
    sheets.md s4 deliberately leaves `/BST` undeclared.

=====================================================================
4.  DECOUPLING METADATA
=====================================================================
Every input cap on the VIN pin carries `role: "reg_input"`, INCLUDING the
220 nF HF ceramic.  Value-classing alone cannot see a MISSING cap: a
bulk-only buck input reads as "bulk cap, loose limits, fine" and ships the
lumina-carrier rework defect (LEARNINGS 2026-08-14).  The role turns on a
group check that demands an HF-capable member (<= 1 uF) within 7.5 mm of
the pin; C1 at 220 nF is that member.

C7 is recorded against pin 6 with `rail_net="/VCC"`: the wiring label is
the bare "VCC" but the association metadata must carry the FINAL netlist
name, and netlist_audit --decoupling checks it against the real netlist.

C6 is NOT an association (BOOT->SW is not a rail+gnd pair) and C4/C5 are
NOT (the output bank hangs off L1, not off an IC pin - constraints.json
already rules that `check_pdn`'s "+5V has no decoupling capacitors" is a
category error destined for reports/verify-waivers.json, not for a
synthetic association here).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
REPO = HERE.parents[4]                 # boards/<b>/kicad/gen/root.py -> repo
WORKSPACE = HERE.parents[2]            # boards/bb-buck
sys.path.insert(0, str(REPO / ".claude" / "skills" / "ai-ee" / "scripts"))
sys.path.insert(0, str(HERE.parent))

import kicad_sch_api as ksa            # noqa: E402
import schlib                          # noqa: E402

import lib_pin_types                   # noqa: E402  (sibling; see s3 BOOT)

# The ERC-blocking pin typing must be repaired BEFORE the symbol cache reads
# the library (idempotent; a no-op once applied).  Measured with it disabled:
# exactly one ERC finding, `power_pin_not_driven` on U1 pin 7 - and nothing
# else on the whole board.
lib_pin_types.main(verbose=False)

# kicad-sch-api's GLOBAL symbol cache never reads kicad/sym-lib-table, so the
# project library must be registered before any `aiee:` symbol is placed, and
# before save() re-serialises lib_symbols from that same cache
# (LEARNINGS 2026-07-28 and 2026-08-06).
PROJECT_LIB = WORKSPACE / "lib" / "aiee.kicad_sym"
ksa.get_symbol_cache().add_library_path(str(PROJECT_LIB))

# ------------------------------------------------------------------ symbols
S_U1 = "aiee:LMR33630ADDAR"
S_L1 = "aiee:SMDRI127-150MT"
S_C220N = "aiee:CC0603KRX7R9BB224"      # C1  220nF 50V X7R 0603
S_C10U = "aiee:CS3225X7R106K500NRL"     # C2, C3  10uF 50V X7R 1210
S_C100N = "aiee:CC0603KRX7R9BB104"      # C6  100nF 50V X7R 0603
S_C1U = "aiee:CC0603KRX7R8BB105"        # C7  1uF 25V X7R 0603
S_C22U = "aiee:CS3225X7R226K250NRL"     # C4, C5  22uF 25V X7R 1210
S_R100K = "aiee:RT0603BRD07100KL"       # R1  100k 0.1% 25ppm
S_R24K9 = "aiee:RT0603BRD0724K9L"       # R2  24.9k 0.1% 25ppm
S_J = "aiee:KF128-5.08-2P"              # J1, J2
S_TP = "Connector:TestPoint"
S_HOLE = "Mechanical:MountingHole"      # ZERO pins, unplated M3

# --------------------------------------------------------------- footprints
F_SO8EP = "aiee:ESOP-8_L4.9-W3.9-P1.27-LS6.0-TL-EP"
F_IND = "aiee:IND-SMD_L12.5-W12.5_RLF12545T"
F_C0603 = "aiee:C0603"
F_C1210 = "aiee:C1210"
F_R0603 = "aiee:R0603"
F_CONN = "aiee:CONN-TH_P5.08_KF128-5.08-2P"
F_TP = "TestPoint:TestPoint_Pad_D1.5mm"
F_HOLE = "MountingHole:MountingHole_3.2mm_M3"

# ref -> LCSC, straight from parts/parts.json.  parts.json is the S6
# per-DISTINCT-part shape (no `ref` keys), which `bom_cpl.load_parts_map`
# CANNOT map, so P9's only ref->LCSC source is the per-component `LCSC`
# field stamped here (bom_cpl.board_lcsc_map matches pname.upper()=="LCSC"
# only - the symbol's inherited "LCSC Part" property does NOT satisfy it).
LCSC = {
    "U1": "C841384",
    "L1": "C40000",
    "C1": "C107083",
    "C2": "C2918502", "C3": "C2918502",
    "C4": "C2918511", "C5": "C2918511",
    "C6": "C14663",
    "C7": "C106858",
    "R1": "C122538",
    "R2": "C136967",
    "J1": "C474952", "J2": "C474952",
}

# Fields KiCad should keep visible on the plot; everything else is hidden
# after save (the codes and notes must EXIST - P9 reads LCSC off them - but
# kicad-sch-api gives every generator-written field VISIBLE effects, which
# prints them on top of the parts they belong to).
VISIBLE_FIELDS = {"Reference", "Value"}

# ------------------------------------------------------------------ layout
# All anchors are multiples of 1.27 mm (schlib raises otherwise).  Rows are
# spaced so no stub label anchor can land on a foreign wire run (schlib's
# _assert_label_clear guard; LEARNINGS 2026-07-22 [erc]).
Y_MAIN = 76.20      # J1 -> U1 -> L1 -> J2, the power chain
Y_CAP = 114.30      # U1's decoupling row (C1, C2, C3, C7)
Y_AUX = 152.40      # C6 bootstrap, FB divider, output bank
Y_TP = 190.50       # test pads and mounting holes
Y_PWR = 228.60      # the three rail clusters


def build() -> schlib.Sheet:
    sh = schlib.Sheet(
        "bb-buck", paper="A3", rev="A", date="2026-08-15", company="ai-ee",
        title="bb-buck  18-30V -> 5.0V 2A synchronous buck (LMR33630A)")

    def add(lib_id, ref, value, at, footprint, pins, expect=None, note=None):
        """Place a purchased part, stamp its LCSC code, wire every pin.

        Every ref routed through here is a BOM line, so a missing code is a
        defect, not a default (see the LCSC map above).  Fail at build time.
        """
        code = LCSC.get(ref)
        if not code:
            raise KeyError(f"{ref}: no LCSC code in the parts map - a "
                           f"purchased part cannot ship unsourced")
        fields = {"LCSC": code}
        if note:
            fields["Note"] = note
        sh.add_component(lib_id, ref, value, at=at, footprint=footprint,
                         fields=fields, expect=expect)
        sh.wire_pins(ref, pins)

    # =============================================================== chain
    # J1 input terminal.  Pin 1 = +VIN, pin 2 = GND (sheets.md s3).  No
    # reverse-polarity protection exists by mode, so J1/J2 silk is the only
    # defence against a swap - a P6 silk item, not a schematic one.
    add(S_J, "J1", "KF128-5.08-2P", (38.10, Y_MAIN), F_CONN,
        {"1": "+VIN", "2": "GND"},
        note="DC INPUT 18-30V, LEFT edge, wire opening off-board")

    # U1 + the whole decoupling set.  Pin map and every wiring decision:
    # parts/C841384.json (see s3 of this file's header).
    #   1 PGND -> GND        5 FB   -> /FB
    #   2 VIN  -> +VIN       6 VCC  -> /VCC  (C7, datasheet 9.2.2.8)
    #   3 EN   -> +VIN       7 BOOT -> /BST  (C6 to /SW, 9.2.2.7)
    #   4 PG   -> no-connect 8 SW   -> /SW
    #   9 EP   -> GND
    # PG is the one deliberate no-connect: an open-drain power-good output
    # with no consumer on this board, "can be left open when not used"
    # (Table 6-1).  Flagged rather than dangling.
    sh.place_ic_with_decoupling(
        "U1", S_U1, "LMR33630ADDAR", at=(101.60, Y_MAIN), footprint=F_SO8EP,
        pins={"1": "GND", "2": "+VIN", "3": "+VIN", "4": "NC", "5": "FB",
              "6": "VCC", "7": "BST", "8": "SW", "9": "GND"},
        expect={"1": "PGND", "2": "VIN", "3": "EN", "4": "PG", "5": "FB",
                "6": "VCC", "7": "BOOT", "8": "SW", "9": "EP"},
        decoupling=[
            # role reg_input on ALL THREE input caps: the group check needs
            # to know the pin is a switching regulator's input, and C1 is
            # the HF member that satisfies it (220 nF <= 1 uF).
            {"cap": "C1", "pin": "2", "rail": "+VIN",
             "value": "220nF 50V X7R", "lib_id": S_C220N,
             "footprint": F_C0603, "role": "reg_input"},
            {"cap": "C2", "pin": "2", "rail": "+VIN",
             "value": "10uF 50V X7R", "lib_id": S_C10U,
             "footprint": F_C1210, "role": "reg_input"},
            {"cap": "C3", "pin": "2", "rail": "+VIN",
             "value": "10uF 50V X7R", "lib_id": S_C10U,
             "footprint": F_C1210, "role": "reg_input"},
            # C_VCC: rail_net carries the FINAL netlist name of the bare
            # "VCC" wiring label (root-local labels export with one slash).
            {"cap": "C7", "pin": "6", "rail": "VCC", "rail_net": "/VCC",
             "value": "1uF 25V X7R", "lib_id": S_C1U,
             "footprint": F_C0603},
        ],
        caps_at=(38.10, Y_CAP), caps_dx=25.40)
    for ref in ("U1", "C1", "C2", "C3", "C7"):
        sh.sch.components.get(ref).set_property("LCSC", LCSC[ref])

    # L1 15 uH shielded: /SW -> +5V.  Isat 8 A clears the 6.6 A floor
    # (1.3 x the part's 5.05 A max high-side current limit).
    add(S_L1, "L1", "15uH", (165.10, Y_MAIN), F_IND,
        {"1": "SW", "2": "+5V"})
    add(S_J, "J2", "KF128-5.08-2P", (215.90, Y_MAIN), F_CONN,
        {"1": "+5V", "2": "GND"},
        note="DC OUTPUT 5V 2A, BOTTOM edge, wire opening off-board")

    # ============================================================== support
    # C6 bootstrap, BOOT -> SW.  Datasheet 9.2.2.7: "a high-quality ceramic
    # capacitor of 100 nF and at least 10 V is required" - required, not
    # optional.  Spans /BST and /SW, so it is not a rail+GND decoupler and
    # cannot appear in decoupling.json.
    add(S_C100N, "C6", "100nF 50V X7R", (38.10, Y_AUX), F_C0603,
        {"1": "BST", "2": "SW"},
        note="bootstrap BOOT->SW, datasheet 9.2.2.7 (required)")

    # FB divider.  VREF is 1.000 V typ (7.5), so
    #   VOUT = 1.0 x (1 + 100k/24.9k) = 5.016 V, inside the 4.85-5.15 V
    # window with the whole +/-1.5% VREF spread (4.939-5.092 V) still inside.
    # BOTH resistors stay 0.1% / 25 ppm and from the same YAGEO RT0603BRD
    # family so their tempcos track - do not let a later phase substitute
    # 1% parts.  100k top is the datasheet's own recommendation (9.2.2.3).
    add(S_R100K, "R1", "100k 0.1% 25ppm", (76.20, Y_AUX), F_R0603,
        {"1": "+5V", "2": "FB"},
        note="FB top; sense point AFTER the output caps, away from /SW")
    add(S_R24K9, "R2", "24.9k 0.1% 25ppm", (114.30, Y_AUX), F_R0603,
        {"1": "FB", "2": "GND"},
        note="FB bottom; Vout=1.0*(1+100/24.9)=5.016V, divider 40uA")

    # Output bank: 2 x 22 uF 25 V X7R 1210 (>= 20 uF effective at 5 V bias).
    # 25 V rating, not the datasheet example's 16 V - the sourced part is
    # 25 V and more rating is never a defect here.
    for ref, x in (("C4", 152.40), ("C5", 190.50)):
        add(S_C22U, ref, "22uF 25V X7R", (x, Y_AUX), F_C1210,
            {"1": "+5V", "2": "GND"})

    # ======================================================== geometry-only
    # TP1/TP2 and H1-H4 are library land patterns, not BOM lines - P3's
    # part-sourcer deliberately gave them no parts.json entry.  Both stock
    # footprints declare `(attr exclude_from_pos_files exclude_from_bom)`,
    # so the symbol instances must agree or KiCad DRC raises "Footprint
    # attributes don't match symbol" once board_init pairs them.  `in_bom
    # no` is the whole fix: a KiCad 10 symbol has no exclude_from_pos_files
    # counterpart, so that bit cannot diverge.  `dnp` stays no - these parts
    # ARE fitted, they are simply not bought.
    #
    # Exactly ONE switch-node probe pad plus ONE adjacent ground pad (owner
    # answer A4); nothing else.  TP1 sits INSIDE the /SW copper at P6 (not
    # on a spur) and its pad counts against the 40 mm^2 /SW area ceiling;
    # TP2 returns straight down to the B.Cu pour - the pair exists to give a
    # scope probe a SHORT ground loop.
    for ref, net, x, why in (
            ("TP1", "SW", 38.10, "switch-node probe; INSIDE the /SW pour, "
                                 "counts against the 40mm2 area ceiling"),
            ("TP2", "GND", 63.50, "scope ground for TP1; short return to "
                                  "the B.Cu pour directly beneath")):
        sh.add_component(S_TP, ref, net, at=(x, Y_TP), footprint=F_TP,
                         fields={"Note": why})
        sh.wire_pin(ref, "1", net)

    # M3 clearance holes, 3.2 mm NPTH with a 6.5 mm keepout (constraints.json
    # placement.keepouts).  ZERO-pin symbol: unplated, no net.
    for i, ref in enumerate(("H1", "H2", "H3", "H4")):
        sh.add_component(S_HOLE, ref, "M3_3.2mm",
                         at=(round(101.60 + i * 19.05, 4), Y_TP),
                         footprint=F_HOLE)
    for ref in ("TP1", "TP2", "H1", "H2", "H3", "H4"):
        sh.sch.components.get(ref).in_bom = False

    # =========================================================== power rails
    # Power SYMBOLS make these three nets GLOBAL and BARE; a local label
    # would export "/+VIN" and silently break every constraints.json match
    # (sheets.md s2).  The symbol's VALUE names the net and schlib sets it
    # from the net argument, so `power:VBUS` with Value "+VIN" exports a
    # bare "+VIN" - there is no stock `power:+VIN`.
    #
    # PWR_FLAG on all three: a power symbol's own pin is power_in, so each
    # rail needs a driver ERC can see.  +VIN additionally carries U1 VIN and
    # EN, GND carries U1 PGND and the exposed pad (all power_in), and +5V's
    # only source is L1, a passive.
    sh.power_flag("GND", at=(38.10, Y_PWR), sym="power:GND", flag=True)
    sh.power_flag("+VIN", at=(88.90, Y_PWR), sym="power:VBUS", flag=True)
    sh.power_flag("+5V", at=(139.70, Y_PWR), sym="power:+5V", flag=True)
    return sh


# ------------------------------------------------------- field-visibility
def _match(text: str, open_idx: int) -> int:
    """Index just past the paren opened at `open_idx`, quote-aware."""
    depth, i, n = 0, open_idx, len(text)
    while i < n:
        ch = text[i]
        if ch == '"':
            i += 1
            while i < n:
                if text[i] == "\\":
                    i += 2
                    continue
                if text[i] == '"':
                    break
                i += 1
        elif ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    raise ValueError(f"unbalanced s-expression at {open_idx}")


def hide_aux_fields(path: Path) -> int:
    """`(hide yes)` on every non-VISIBLE property.  The fields must EXIST
    (P9 reads LCSC off them) but kicad-sch-api gives every generator-written
    field VISIBLE effects, which prints the codes and notes on top of the
    parts they belong to.  Hiding is a plot property only - exactly the form
    KiCad itself writes for Footprint and Datasheet.  Idempotent."""
    text = path.read_text(encoding="utf-8")
    out, pos, hidden = [], 0, 0
    needle = '(property "'
    while True:
        i = text.find(needle, pos)
        if i < 0:
            break
        j = text.index('"', i + len(needle))
        name = text[i + len(needle):j]
        end = _match(text, i)
        node = text[i:end]
        if name in VISIBLE_FIELDS or "(hide yes)" in node:
            out.append(text[pos:end])
            pos = end
            continue
        e = node.find("(effects")
        if e >= 0:
            e_end = _match(node, e)
            indent = " " * (len(node[:e]) - len(node[:e].rstrip(" \t")) - 1)
            node = (node[:e_end - 1] + f"\t{indent}(hide yes)\n{indent}"
                    + node[e_end - 1:])
        else:
            node = node[:-1] + "(effects (hide yes))"
        hidden += 1
        out.append(text[pos:i] + node)
        pos = end
    out.append(text[pos:])
    new = "".join(out)
    if new != text:
        path.write_text(new, encoding="utf-8")
    return hidden


def main(argv=None) -> int:
    args = [a for a in (argv or []) if not a.startswith("--")]
    out_dir = Path(args[0]) if args else HERE.parents[1]      # .../kicad
    try:
        sh = build()
        sch = sh.save(out_dir, project=True)
        hidden = hide_aux_fields(sch)
        meta = sh.emit_decoupling(out_dir / "decoupling.json")
    except Exception as exc:                # noqa: BLE001 (SPEC 6: error -> 2)
        print(json.dumps({"script": "gen.bb-buck", "status": "error",
                          "error": f"{type(exc).__name__}: {exc}"}))
        return 2
    print(json.dumps({
        "script": "gen.bb-buck", "status": "pass",
        "files": [str(sch), str(out_dir / "bb-buck.kicad_pro"), str(meta)],
        "components": len(sh.sch.components),
        "decoupling_associations": len(sh.decoupling),
        "fields_hidden": hidden,
        "field_placement": sh.place_report,
    }, indent=1, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
