"""S12 acceptance tests: fab outputs, DFM, ordering.

Plan S12 accept criteria:
  - dfm_check.py catches the silk and rotation mutants
        -> test_dfm_catches_silk_over_pad, test_dfm_catches_cpl_rotation
           (the rotation catch is HERMETIC: the committed s7_regen netlist is
            the polarity oracle, so no toolchain is needed to pin V9)
  - zero false positives on the goldens
        -> test_dfm_goldens_clean, test_dfm_negative_control_mutants
  - golden board 2 package uploads clean to JLCPCB's web viewer
        -> package completeness/structure is machine-tested here
           (test_full_package_flow); the actual upload is a human step,
           recorded in PROGRESS.md, since JLC has no public viewer API.
  - CPL rotations spot-checked against JLC's rendered preview
        -> test_cpl_rotation_corrections pins the table-driven maths for the
           polarized packages; the visual preview is the same human step.

Pure tests need no toolchain (committed boards/netlists + synthetic gerbers
written by hand). Tests that export gerbers via kicad-cli are `smoke`.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / ".claude" / "skills" / "ai-ee" / "scripts"
REFERENCE = REPO / ".claude" / "skills" / "ai-ee" / "reference"
GOLDEN = REPO / "tests" / "golden"
PYTHON = sys.executable
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(SCRIPTS / "lib"))

import bom_cpl  # noqa: E402
import checklib  # noqa: E402
import dfm_check  # noqa: E402
import fab_export  # noqa: E402
import geom  # noqa: E402
import gerblib  # noqa: E402
import netlist_audit  # noqa: E402
import order_quote  # noqa: E402
import order_submit  # noqa: E402

MANIFEST = yaml.safe_load((GOLDEN / "manifest.yaml").read_text(encoding="utf-8"))
BOARDS = list(MANIFEST["golden_boards"])
GATES_YAML = REFERENCE / "gates.yaml"
BLINKY_NET = REPO / "tests" / "s7_regen" / "blinky2" / "golden.net"


def board_path(name: str) -> Path:
    return GOLDEN / name / f"{name}.kicad_pcb"


def mutant_path(name: str, board: str) -> Path:
    return GOLDEN / "mutants" / name / f"{board}.kicad_pcb"


# ------------------------------------------------------- synthetic gerbers

def _fmt(v: float) -> str:
    """mm -> 4.6 fixed-point gerber coordinate."""
    return str(int(round(v * 1e6)))


def write_gerber(path: Path, traces=(), flashes=()) -> None:
    """Minimal RS-274X. traces: [(w, x1, y1, x2, y2)]; flashes: [(dia, x, y)].
    Gerber Y points up, so callers pass gerber-space coordinates."""
    out = ["%FSLAX46Y46*%", "%MOMM*%"]
    ap = 10
    body = []
    for w, x1, y1, x2, y2 in traces:
        out.append(f"%ADD{ap}C,{w:.4f}*%")
        body += [f"D{ap}*", f"X{_fmt(x1)}Y{_fmt(y1)}D02*",
                 f"X{_fmt(x2)}Y{_fmt(y2)}D01*"]
        ap += 1
    for dia, x, y in flashes:
        out.append(f"%ADD{ap}C,{dia:.4f}*%")
        body += [f"D{ap}*", f"X{_fmt(x)}Y{_fmt(y)}D03*"]
        ap += 1
    out += body + ["M02*"]
    path.write_text("\n".join(out) + "\n", encoding="utf-8")


def write_drill(path: Path, holes=()) -> None:
    """Minimal Excellon. holes: [(dia, x, y)] in mm, gerber space."""
    lines = ["M48", "METRIC,TZ"]
    tools = sorted({d for d, _, _ in holes})
    for i, d in enumerate(tools, start=1):
        lines.append(f"T{i}C{d:.3f}")
    lines += ["%", "G90", "G05"]
    for i, d in enumerate(tools, start=1):
        lines.append(f"T{i}")
        for hd, x, y in holes:
            if hd == d:
                lines.append(f"X{x:.3f}Y{y:.3f}")
    lines.append("M30")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def synth_fab(tmp_path: Path, *, traces=(), flashes=(), holes=(),
              silk=(), mask=(), outline_mm=(0.0, 0.0, 20.0, 20.0)) -> object:
    """Build a minimal 2-layer fab dir and open it with gerblib."""
    d = tmp_path / "synth"
    d.mkdir(exist_ok=True)
    write_gerber(d / "synth-F_Cu.gtl", traces=traces, flashes=flashes)
    write_gerber(d / "synth-B_Cu.gbl")
    write_gerber(d / "synth-F_Silkscreen.gto", traces=silk)
    write_gerber(d / "synth-B_Silkscreen.gbo")
    write_gerber(d / "synth-F_Mask.gts", flashes=mask)
    write_gerber(d / "synth-B_Mask.gbs")
    x0, y0, x1, y1 = outline_mm
    write_gerber(d / "synth-Edge_Cuts.gm1", traces=[
        (0.1, x0, y0, x1, y0), (0.1, x1, y0, x1, y1),
        (0.1, x1, y1, x0, y1), (0.1, x0, y1, x0, y0)])
    write_drill(d / "synth.drl", holes=holes)
    return gerblib.open_fab(d)


RULES_2L = yaml.safe_load(
    (REFERENCE / "jlc_capabilities.yaml").read_text(encoding="utf-8")
)["design_rules"]["2layer_1oz"]


# =========================================================== pure: rotations

def test_rotations_table_loads_in_order():
    rules = bom_cpl.load_rotations(REFERENCE / "jlc_rotations.csv")
    assert len(rules) > 20
    pats = [p.pattern for p, _ in rules]
    # more specific SOT-323 must precede the broader SOT-23 family entry only
    # if both exist; the contract under test is that order is preserved.
    assert pats == [p.pattern for p, _ in
                    bom_cpl.load_rotations(REFERENCE / "jlc_rotations.csv")]


def test_cpl_rotation_corrections():
    """The table-driven maths for polarized/pin-1-sensitive packages."""
    rules = bom_cpl.load_rotations(REFERENCE / "jlc_rotations.csv")
    # (footprint, kicad rotation) -> (jlc rotation, correction)
    cases = [
        ("LED_0805_2012Metric", 180.0, 0.0, 180.0),
        ("LED_0805_2012Metric", 0.0, 180.0, 180.0),
        ("LQFP-48_7x7mm_P0.5mm", 0.0, 270.0, 270.0),
        ("SOT-23", 90.0, 270.0, 180.0),
        ("D_SOD-123", 0.0, 180.0, 180.0),
        ("C_0603_1608Metric", 90.0, 90.0, 0.0),      # unmatched -> unchanged
    ]
    for fp, base, want_final, want_corr in cases:
        final, corr, _ = bom_cpl.correct_rotation(fp, base, rules)
        assert final == pytest.approx(want_final), fp
        assert corr == pytest.approx(want_corr), fp


def test_correct_rotation_strips_library_prefix():
    rules = bom_cpl.load_rotations(REFERENCE / "jlc_rotations.csv")
    final, corr, pat = bom_cpl.correct_rotation(
        "LED_SMD:LED_0805_2012Metric", 0.0, rules)
    assert (final, corr) == (180.0, 180.0) and pat == "^LED_0805"


def test_rotation_wraps_mod_360():
    rules = [(__import__("re").compile("^X"), 270.0)]
    final, _, _ = bom_cpl.correct_rotation("XPART", 180.0, rules)
    assert final == pytest.approx(90.0)


# ============================================================ pure: BOM/CPL

POS_CSV = (
    "Ref,Val,Package,PosX,PosY,Rot,Side\n"
    '"C1","100nF","C_0603",1.0,-2.0,0.0,top\n'
    '"C2","100nF","C_0603",3.0,-4.0,90.0,top\n'
    '"D1","LED_red","LED_0805",5.0,-6.0,180.0,bottom\n'
)


def test_parse_pos_csv():
    rows = bom_cpl.parse_pos_csv(POS_CSV)
    assert [r["ref"] for r in rows] == ["C1", "C2", "D1"]
    assert rows[2]["side"] == "bottom" and rows[2]["rot"] == 180.0
    assert rows[0]["x"] == 1.0 and rows[0]["y"] == -2.0


def test_build_bom_groups_by_value_footprint_lcsc():
    rows = bom_cpl.parse_pos_csv(POS_CSV)
    bom = bom_cpl.build_bom(rows, {"C1": {"lcsc": "C1525"},
                                   "C2": {"lcsc": "C1525"}})
    caps = [r for r in bom if r["Comment"] == "100nF"]
    assert len(caps) == 1 and caps[0]["Designator"] == "C1,C2"
    assert caps[0]["LCSC"] == "C1525"
    led = [r for r in bom if r["Comment"] == "LED_red"][0]
    assert led["LCSC"] == ""          # no LCSC -> empty, reported separately


def test_build_bom_splits_when_lcsc_differs():
    rows = bom_cpl.parse_pos_csv(POS_CSV)
    bom = bom_cpl.build_bom(rows, {"C1": {"lcsc": "C1"}, "C2": {"lcsc": "C2"}})
    assert len([r for r in bom if r["Comment"] == "100nF"]) == 2


def test_build_cpl_layer_and_rotation():
    rows = bom_cpl.parse_pos_csv(POS_CSV)
    rules = bom_cpl.load_rotations(REFERENCE / "jlc_rotations.csv")
    cpl, audit = bom_cpl.build_cpl(rows, rules)
    by_ref = {r["Designator"]: r for r in cpl}
    assert by_ref["D1"]["Layer"] == "Bottom"
    assert by_ref["C1"]["Layer"] == "Top"
    # LED_0805 carries a 180 correction: 180 + 180 = 360 -> 0
    assert float(by_ref["D1"]["Rotation"]) == pytest.approx(0.0)
    assert by_ref["C1"]["Mid X"] == "1.0000"
    assert {a["ref"] for a in audit} == {"C1", "C2", "D1"}


@pytest.mark.parametrize("payload", [
    {"parts": [{"ref": "U1", "lcsc": "C123"}]},
    [{"refs": ["U1"], "lcsc": "C123"}],
    {"U1": "C123"},
    {"U1": {"lcsc": "C123"}},
])
def test_load_parts_map_shapes(tmp_path, payload):
    p = tmp_path / "parts.json"
    p.write_text(json.dumps(payload), encoding="utf-8")
    assert bom_cpl.load_parts_map(p)["U1"]["lcsc"] == "C123"


# ====================================================== pure: capabilities

def test_rule_key_and_pick():
    caps = dfm_check.load_capabilities(REFERENCE / "jlc_capabilities.yaml")
    assert dfm_check.rule_key(4, 1.0) == "4layer_1oz"
    key, rules = dfm_check.pick_rules(caps, 2, 1.0)
    assert key == "2layer_1oz" and rules["min_trace_width_mm"] == 0.127


def test_pick_rules_unknown_raises():
    caps = dfm_check.load_capabilities(REFERENCE / "jlc_capabilities.yaml")
    with pytest.raises(checklib.CheckError):
        dfm_check.pick_rules(caps, 8, 1.0)


def test_below_tolerance_absorbs_tessellation_but_not_defects():
    # a value exactly at the limit must pass despite micron-scale flattening
    assert not dfm_check._below(0.1498, 0.15)
    assert not dfm_check._below(0.15, 0.15)
    # a real shortfall still fails
    assert dfm_check._below(0.12, 0.15)
    assert dfm_check._below(0.1016, 0.127)


# ========================================================== pure: gerblib

def test_gerblib_classifies_layers(tmp_path):
    fab = synth_fab(tmp_path)
    assert fab.copper_layer_names() == ["F.Cu", "B.Cu"]
    assert set(fab.silk_files) == {"F", "B"}
    assert set(fab.mask_files) == {"F", "B"}
    assert fab.edge_file is not None and len(fab.drill_files) == 1


def test_gerblib_copper_layer_physical_order():
    names = {"B.Cu": 1, "In2.Cu": 2, "F.Cu": 3, "In1.Cu": 4}

    class Fake(gerblib.FabStack):
        def __init__(self):
            self.copper_files = names
    assert Fake().copper_layer_names() == ["F.Cu", "In1.Cu", "In2.Cu", "B.Cu"]


def test_gerblib_outline_and_board_space(tmp_path):
    fab = synth_fab(tmp_path, outline_mm=(0.0, -10.0, 20.0, 0.0))
    # gerber y in [-10, 0] -> board y in [0, 10] (gerblib negates y)
    assert fab.outline.bounds == pytest.approx((0.0, 0.0, 20.0, 10.0), abs=0.06)


def test_gerblib_reads_holes_in_board_space(tmp_path):
    fab = synth_fab(tmp_path, holes=[(0.3, 5.0, -5.0)])
    assert len(fab.holes) == 1
    h = fab.holes[0]
    assert (h.x, h.y) == pytest.approx((5.0, 5.0))
    assert h.diameter == pytest.approx(0.3)


def test_gerblib_tessellates_arcs_finely(tmp_path):
    """A round pad must not be read as a coarse polygon: the inscribed radius
    drives the annular-ring measurement (the bug that made blinky2's exactly-
    at-spec 0.6 mm vias look 0.025 mm short)."""
    fab = synth_fab(tmp_path, flashes=[(0.6, 5.0, -5.0)])
    pad = fab.copper("F.Cu").pads[0]
    from shapely.geometry import Point
    inscribed = pad.exterior.distance(Point(5.0, 5.0))
    assert inscribed == pytest.approx(0.3, abs=gerblib.ARC_MAX_ERROR_MM)


# =============================================== pure: seeded gerber defects

def test_dfm_flags_narrow_trace(tmp_path):
    fab = synth_fab(tmp_path, traces=[(0.08, 2.0, -2.0, 8.0, -2.0)])
    vios: list = []
    dfm_check.check_trace_width(fab, RULES_2L, vios)
    assert len(vios) == 1
    v = vios[0]
    assert v["kind"] == "dfm_trace_width" and v["severity"] == "error"
    assert v["width_mm"] == pytest.approx(0.08)
    assert v["pos"] == pytest.approx([5.0, 2.0], abs=1e-3)


def test_dfm_accepts_trace_at_the_limit(tmp_path):
    fab = synth_fab(tmp_path, traces=[(0.127, 2.0, -2.0, 8.0, -2.0)])
    vios: list = []
    dfm_check.check_trace_width(fab, RULES_2L, vios)
    assert vios == []


def test_dfm_flags_tight_clearance(tmp_path):
    # two parallel 0.2 mm traces whose copper edges are 0.05 mm apart
    fab = synth_fab(tmp_path, traces=[(0.2, 2.0, -2.0, 8.0, -2.0),
                                      (0.2, 2.0, -2.25, 8.0, -2.25)])
    vios: list = []
    dfm_check.check_clearance(fab, RULES_2L, vios)
    assert [v["kind"] for v in vios] == ["dfm_clearance"]
    assert vios[0]["clearance_mm"] == pytest.approx(0.05, abs=1e-3)


def test_dfm_ignores_touching_copper(tmp_path):
    """Connected copper is one conductor, not a zero-clearance violation."""
    fab = synth_fab(tmp_path, traces=[(0.3, 2.0, -2.0, 8.0, -2.0),
                                      (0.3, 8.0, -2.0, 8.0, -8.0)])
    vios: list = []
    dfm_check.check_clearance(fab, RULES_2L, vios)
    assert vios == []


def test_dfm_round_caps_join_overlapping_junctions(tmp_path):
    """S14: KiCad emits circular apertures, so trace ends are ROUND. Two
    same-net segments whose endpoints sit 0.05mm apart with 0.1mm cap radius
    OVERLAP - flat-capped buffering split them into phantom islands with a
    fake sub-minimum gap (two false dfm_clearance errors on a KiCad-clean
    board)."""
    fab = synth_fab(tmp_path, traces=[(0.2, 2.0, -2.0, 5.0, -2.0),
                                      (0.2, 5.05, -2.0, 8.0, -2.0)])
    vios: list = []
    dfm_check.check_clearance(fab, RULES_2L, vios)
    assert vios == []  # round caps overlap: one conductor, no phantom gap


def test_dfm_round_caps_expose_trace_end_at_edge(tmp_path):
    """S14 (false-negative direction): a trace END'S round cap reaches w/2
    closer to the board edge than the flat-capped model claimed."""
    # end at x=0.30 with w=0.3 -> round cap reaches x=0.15; JLC edge min 0.3
    fab = synth_fab(tmp_path, traces=[(0.3, 0.30, -5.0, 8.0, -5.0)],
                    outline_mm=(0.0, -20.0, 20.0, 0.0))
    vios: list = []
    dfm_check.check_copper_to_edge(fab, RULES_2L, vios)
    assert [v["kind"] for v in vios] == ["dfm_copper_to_edge"]


def test_dfm_flags_small_drill(tmp_path):
    fab = synth_fab(tmp_path, holes=[(0.15, 5.0, -5.0)])
    vios: list = []
    dfm_check.check_holes(fab, RULES_2L, vios)
    kinds = [v["kind"] for v in vios]
    assert "dfm_hole_size" in kinds
    v = [x for x in vios if x["kind"] == "dfm_hole_size"][0]
    assert v["diameter_mm"] == pytest.approx(0.15)


def test_dfm_flags_hole_to_hole(tmp_path):
    fab = synth_fab(tmp_path, holes=[(0.3, 5.0, -5.0), (0.3, 5.4, -5.0)])
    vios: list = []
    dfm_check.check_holes(fab, RULES_2L, vios)
    assert "dfm_hole_to_hole" in [v["kind"] for v in vios]


def test_dfm_flags_thin_annular_ring(tmp_path):
    # 0.4 mm pad on a 0.3 mm drill -> 0.05 mm ring (< 0.15 minimum)
    fab = synth_fab(tmp_path, flashes=[(0.4, 5.0, -5.0)],
                    holes=[(0.3, 5.0, -5.0)])
    vios: list = []
    dfm_check.check_annular_ring(fab, RULES_2L, vios)
    assert [v["kind"] for v in vios] == ["dfm_annular_ring"]
    assert vios[0]["ring_mm"] == pytest.approx(0.05, abs=5e-3)


def test_dfm_accepts_annular_ring_at_the_limit(tmp_path):
    fab = synth_fab(tmp_path, flashes=[(0.6, 5.0, -5.0)],
                    holes=[(0.3, 5.0, -5.0)])
    vios: list = []
    dfm_check.check_annular_ring(fab, RULES_2L, vios)
    assert vios == []


def test_dfm_flags_copper_over_board_edge(tmp_path):
    fab = synth_fab(tmp_path, traces=[(0.3, 0.05, -5.0, 8.0, -5.0)],
                    outline_mm=(0.0, -20.0, 20.0, 0.0))
    vios: list = []
    dfm_check.check_copper_to_edge(fab, RULES_2L, vios)
    assert [v["kind"] for v in vios] == ["dfm_copper_to_edge"]


def test_dfm_missing_layer_is_release_error(tmp_path):
    fab = synth_fab(tmp_path)
    (fab.dir / "synth-B_Mask.gbs").unlink()
    fab2 = gerblib.open_fab(fab.dir)
    vios: list = []
    dfm_check.check_release(fab2, 2, vios, None)
    assert "dfm_missing_layer" in [v["kind"] for v in vios]


def test_dfm_bom_incomplete_is_warning_only(tmp_path):
    fab = synth_fab(tmp_path)
    vios: list = []
    dfm_check.check_release(fab, 2, vios, {"missing_lcsc": ["U1", "C3"]})
    v = [x for x in vios if x["kind"] == "dfm_bom_incomplete"]
    assert len(v) == 1 and v[0]["severity"] == "warning"


def test_dfm_silk_sliver_is_warning_real_overlap_error(tmp_path):
    """S14: micron-sliver silk inside a mask opening (library body outlines)
    is a WARNING (fab auto-clips); substantial ink on solder surface stays an
    ERROR. Threshold SILK_OVERLAP_ERROR_MM2."""
    # sliver: 0.15mm silk stroke crossing a 1mm mask opening edge by ~0.02mm
    fab = synth_fab(tmp_path, silk=[(0.15, 3.0, -4.49, 7.0, -4.49)],
                    mask=[(1.0, 5.0, -5.0)])
    vios: list = []
    dfm_check.check_silk(fab, RULES_2L, vios)
    hits = [v for v in vios if v["kind"] == "dfm_silk_over_pad"]
    assert len(hits) == 1
    assert hits[0]["severity"] == "warning"
    assert hits[0]["overlap_mm2"] < dfm_check.SILK_OVERLAP_ERROR_MM2

    # substantial: the same stroke straight through the opening centre
    (tmp_path / "e").mkdir()
    fab2 = synth_fab(tmp_path / "e", silk=[(0.3, 3.0, -5.0, 7.0, -5.0)],
                     mask=[(1.0, 5.0, -5.0)])
    vios2: list = []
    dfm_check.check_silk(fab2, RULES_2L, vios2)
    hits2 = [v for v in vios2 if v["kind"] == "dfm_silk_over_pad"]
    assert len(hits2) == 1
    assert hits2[0]["severity"] == "error"
    assert hits2[0]["overlap_mm2"] >= dfm_check.SILK_OVERLAP_ERROR_MM2


def test_board_lcsc_map_from_footprint_fields(tmp_path):
    """S14: the board's own per-footprint LCSC fields are the primary
    ref->LCSC source for the BOM (board_init copies them from the symbols)."""
    pcb = tmp_path / "b.kicad_pcb"
    pcb.write_text(
        '(kicad_pcb (version 20260206) (generator "t")\n'
        '  (footprint "aiee:C0603" (at 10 10)\n'
        '    (property "Reference" "C1" (at 0 -4 0))\n'
        '    (property "Value" "100nF 50V X7R" (at 0 4 0))\n'
        '    (property "LCSC" "C14663" (at 0 0 0) (hide yes)))\n'
        '  (footprint "aiee:LQFP-48" (at 30 20)\n'
        '    (property "Reference" "U1" (at 0 -5 0))\n'
        '    (property "LCSC" "C8734" (at 0 0 0) (hide yes)))\n'
        '  (footprint "aiee:HDR" (at 40 20)\n'
        '    (property "Reference" "J1" (at 0 -5 0))))\n',
        encoding="utf-8")
    m = bom_cpl.board_lcsc_map(pcb)
    assert m["C1"]["lcsc"] == "C14663" and m["U1"]["lcsc"] == "C8734"
    assert "J1" not in m  # no LCSC field -> stays missing (honest)
    # per-ref parts.json overrides the board field
    merged = {**m, **{"C1": {"lcsc": "C99999", "mpn": None}}}
    assert merged["C1"]["lcsc"] == "C99999"


# ================================================ hermetic: CPL polarity (V9)

def test_polarity_clean_on_golden():
    """Zero false positives: the golden's pads match its schematic exactly."""
    nl = netlist_audit.parse_netlist(BLINKY_NET)
    bg = geom.load_board(board_path("blinky2"))
    vios: list = []
    facts = dfm_check.check_polarity(bg, nl, vios)
    assert vios == []
    assert facts["refs_checked"] == 17


def test_dfm_catches_cpl_rotation():
    """S12's designated mutant (manifest: dfm_check owns cpl-rotation).

    kicad's --schematic-parity does NOT flag this board (V9 / LEARNINGS), so
    the per-pad-number comparison is the only thing standing between a
    backwards LED and the fab.
    """
    expect = MANIFEST["mutants"]["cpl-rotation"]["expect"]
    nl = netlist_audit.parse_netlist(BLINKY_NET)
    bg = geom.load_board(mutant_path("cpl-rotation", "blinky2"))
    vios: list = []
    dfm_check.check_polarity(bg, nl, vios)
    assert len(vios) == 1
    v = vios[0]
    assert v["kind"] == "cpl_polarity" and v["severity"] == "error"
    assert v["refs"] == [expect["ref"]]
    assert v["rotation_delta_deg"] == pytest.approx(
        expect["rotation_delta_deg"])
    # both pads reported, with board-vs-schematic nets named
    assert {m["pad"] for m in v["mismatches"]} == {"1", "2"}
    assert {m["board"] for m in v["mismatches"]} == {"/LED_A", "GND"}


def test_polarity_clean_on_non_rotation_mutants():
    """The other blinky2 mutants must not trip the polarity check."""
    nl = netlist_audit.parse_netlist(BLINKY_NET)
    for mut in ("silk-over-pad", "undersized-power-trace", "decoupler-moved"):
        bg = geom.load_board(mutant_path(mut, "blinky2"))
        vios: list = []
        dfm_check.check_polarity(bg, nl, vios)
        assert vios == [], f"{mut} falsely flagged by polarity"


# ================================================================= gates

def test_gates_yaml_has_dfm_gate():
    gates = yaml.safe_load(GATES_YAML.read_text(encoding="utf-8"))["gates"]
    assert "dfm" in gates
    g = gates["dfm"]
    assert g["tool"] == "dfm" and g["phase"] == "P9"
    assert g["fail_severities"] == ["error"]     # warnings must not fail


# ============================================================ pure: ordering

def test_quote_pcb_cost_scales_with_qty_and_layers():
    pricing = order_quote.load_pricing(REFERENCE / "jlc_pricing.yaml")
    c2 = order_quote.pcb_cost(pricing, 2, 5, 50, 40, "HASL", "green")
    c4 = order_quote.pcb_cost(pricing, 4, 5, 50, 40, "HASL", "green")
    assert c4["total"] > c2["total"]
    c2_30 = order_quote.pcb_cost(pricing, 2, 30, 50, 40, "HASL", "green")
    assert c2_30["total"] > c2["total"]


def test_quote_oversize_adds_cost():
    pricing = order_quote.load_pricing(REFERENCE / "jlc_pricing.yaml")
    small = order_quote.pcb_cost(pricing, 2, 5, 50, 40, "HASL", "green")
    big = order_quote.pcb_cost(pricing, 2, 5, 150, 140, "HASL", "green")
    assert small["oversize"] == 0.0 and big["oversize"] > 0.0


def test_quote_assembly_feeders_only_for_extended_parts():
    pricing = order_quote.load_pricing(REFERENCE / "jlc_pricing.yaml")
    basic = order_quote.assembly_cost(pricing, 5, 10, 40, 0)
    ext = order_quote.assembly_cost(pricing, 5, 10, 40, 3)
    assert basic["feeders"] == 0.0 and ext["feeders"] > 0.0
    assert ext["total"] > basic["total"]


def test_order_submit_reports_incomplete_package(tmp_path):
    man = order_submit.run(board_path("blinky2"), tmp_path)
    assert man["status"] == "incomplete"
    assert "gerber zip" in man["missing"]
    assert man["payment"].startswith("HUMAN")


def test_order_submit_hashes_and_human_steps(tmp_path):
    (tmp_path / "b_gerbers.zip").write_bytes(b"PK\x03\x04zip")
    (tmp_path / "BOM.csv").write_text("Comment\n", encoding="utf-8")
    (tmp_path / "CPL.csv").write_text("Designator\n", encoding="utf-8")
    man = order_submit.run(board_path("blinky2"), tmp_path)
    assert man["status"] == "ready_for_human"
    assert man["missing"] == []
    assert len(man["artifacts"]["gerber_zip"]["sha256"]) == 64
    # JLCDFM (V6) and the polarity preview must both be named for the human
    joined = " ".join(man["human_steps"]).lower()
    assert "jlcdfm" in joined and "polarized" in joined


# ================================================== smoke: live kicad-cli

@pytest.fixture(scope="module")
def fab_dirs(tmp_path_factory):
    """Export each golden's fab package once and reuse it."""
    out = {}
    base = tmp_path_factory.mktemp("fab")
    for name in BOARDS:
        d = base / name
        man = fab_export.run(board_path(name), d, make_zip=True)
        out[name] = (d, man)
    return out


@pytest.mark.smoke
def test_fab_export_layer_set_and_zip(fab_dirs):
    d, man = fab_dirs["blinky2"]
    assert man["status"] == "pass" and man["layer_count"] == 2
    names = {f["name"] for f in man["files"]}
    for want in ("blinky2-F_Cu.gtl", "blinky2-B_Cu.gbl", "blinky2-F_Mask.gts",
                 "blinky2-F_Silkscreen.gto", "blinky2-Edge_Cuts.gm1",
                 "blinky2.drl"):
        assert want in names, want
    assert Path(man["gerber_zip"]).exists()
    assert len(man["gerber_zip_sha256"]) == 64
    assert all(len(f["sha256"]) == 64 for f in man["files"])


@pytest.mark.smoke
def test_fab_export_four_layer_stackup_order(fab_dirs):
    _, man = fab_dirs["usbbuck4"]
    assert man["layer_count"] == 4
    assert man["copper_layers"] == ["F.Cu", "In1.Cu", "In2.Cu", "B.Cu"]
    names = {f["name"] for f in man["files"]}
    assert "usbbuck4-In1_Cu.g1" in names and "usbbuck4-In2_Cu.g2" in names


@pytest.mark.smoke
def test_bom_cpl_on_golden(fab_dirs, tmp_path):
    rep = bom_cpl.run(board_path("blinky2"), tmp_path)
    assert rep["status"] == "pass" and rep["n_parts"] == 17
    assert Path(rep["bom"]).exists() and Path(rep["cpl"]).exists()
    d1 = [a for a in rep["rotation_audit"] if a["ref"] == "D1"][0]
    # golden D1 sits at 180 deg; the LED_0805 correction brings it to JLC 0
    assert d1["base_rot"] == pytest.approx(180.0)
    assert d1["final_rot"] == pytest.approx(0.0)
    assert rep["missing_lcsc"] and not rep["bom_complete"]  # no parts.json


@pytest.mark.smoke
@pytest.mark.parametrize("name", BOARDS)
def test_dfm_goldens_clean(fab_dirs, name):
    """Zero FALSE POSITIVES on every golden (warnings are advisory)."""
    d, _ = fab_dirs[name]
    rep = dfm_check.run(board_path(name), fab_dir=d,
                        schematic=GOLDEN / name / f"{name}.kicad_sch")
    errors = [v for v in rep["violations"] if v["severity"] == "error"]
    assert errors == [], errors
    assert rep["status"] == "pass"
    assert rep["polarity"]["status"] == "checked"


@pytest.mark.smoke
def test_dfm_catches_silk_over_pad(tmp_path):
    """The other mutant dfm_check must catch, at manifest coordinates."""
    expect = MANIFEST["mutants"]["silk-over-pad"]["expect"]
    pcb = mutant_path("silk-over-pad", "blinky2")
    rep = dfm_check.run(pcb, netlist=BLINKY_NET)
    hits = [v for v in rep["violations"] if v["kind"] == "dfm_silk_over_pad"]
    assert hits, "silk-over-pad not caught"
    v = hits[0]
    assert v["severity"] == "error" and v["refs"] == [expect["ref"]]
    assert v["pos"][0] == pytest.approx(expect["pos"][0], abs=0.1)
    assert v["pos"][1] == pytest.approx(expect["pos"][1], abs=0.1)
    assert rep["status"] == "violations"


@pytest.mark.smoke
def test_dfm_end_to_end_catches_rotation_mutant():
    """The hermetic polarity unit test, re-proven through the full CLI path."""
    rep = dfm_check.run(mutant_path("cpl-rotation", "blinky2"),
                        netlist=BLINKY_NET)
    hits = [v for v in rep["violations"] if v["kind"] == "cpl_polarity"]
    assert len(hits) == 1 and hits[0]["refs"] == ["D1"]
    assert rep["status"] == "violations"


@pytest.mark.smoke
@pytest.mark.parametrize("mut,board", [
    ("undersized-power-trace", "blinky2"),
    ("decoupler-moved", "blinky2"),
    ("diffpair-skew", "usbbuck4"),
    ("missing-return-via", "usbbuck4"),
])
def test_dfm_negative_control_mutants(mut, board):
    """Mutants owned by OTHER checks must not raise dfm errors."""
    rep = dfm_check.run(mutant_path(mut, board),
                        schematic=GOLDEN / board / f"{board}.kicad_sch")
    errors = [v for v in rep["violations"] if v["severity"] == "error"]
    assert errors == [], f"{mut}: {errors}"


@pytest.mark.smoke
def test_dfm_gate_passes_golden_and_fails_mutant(tmp_path):
    import gate
    gates = yaml.safe_load(GATES_YAML.read_text(encoding="utf-8"))["gates"]
    ok = gate.evaluate("dfm", gates["dfm"],
                       gate.run_report_for_gate(gates["dfm"],
                                                board_path("blinky2")))
    assert ok["status"] == "pass" and ok["failing_count"] == 0

    # stage the mutant beside blinky2's schematic so the gate finds its oracle
    staged = tmp_path / "mut"
    staged.mkdir()
    src = mutant_path("cpl-rotation", "blinky2")
    (staged / "blinky2.kicad_pcb").write_bytes(src.read_bytes())
    (staged / "blinky2.kicad_sch").write_bytes(
        (GOLDEN / "blinky2" / "blinky2.kicad_sch").read_bytes())
    bad = gate.evaluate("dfm", gates["dfm"],
                        gate.run_report_for_gate(gates["dfm"],
                                                 staged / "blinky2.kicad_pcb"))
    assert bad["status"] == "fail"
    assert any(f["kind"] == "cpl_polarity" for f in bad["failing"])


@pytest.mark.smoke
def test_full_package_flow(tmp_path):
    """P9 -> P10: export, BOM/CPL, quote, order manifest. This is the machine-
    checkable half of 'the package uploads clean'; the upload itself is the
    documented human step."""
    pcb = board_path("usbbuck4")
    fab = tmp_path / "fab"
    man = fab_export.run(pcb, fab, make_zip=True)
    assert man["status"] == "pass"
    bc = bom_cpl.run(pcb, fab)
    assert bc["status"] == "pass"
    q = order_quote.run(pcb, [5, 30], ["HASL"], ["green"], assembly=True)
    assert q["estimated"] is True and q["spec"]["layers"] == 4
    assert q["matrix"] and q["cheapest"]["qty"] == 5
    sub = order_submit.run(pcb, fab, quote=None, qty=5)
    assert sub["status"] == "ready_for_human"
    assert sub["artifacts"]["gerber_zip"]["sha256"] == man["gerber_zip_sha256"]
    assert sub["api"]["available"] is False        # no credentials configured


@pytest.mark.smoke
def test_dfm_runtime_budget(fab_dirs):
    """The whole DFM pass stays well inside a gate's patience on the densest
    golden (rf4 carries ~90 vias and a coplanar pour)."""
    d, _ = fab_dirs["rf4"]
    t0 = time.time()
    dfm_check.run(board_path("rf4"), fab_dir=d,
                  schematic=GOLDEN / "rf4" / "rf4.kicad_sch")
    assert time.time() - t0 < 30.0
