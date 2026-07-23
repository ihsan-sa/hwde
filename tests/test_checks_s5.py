"""S5 acceptance tests: verification suite part 2 + check orchestration.

Plan S5 accept criteria, arbitrated by tests/golden/manifest.yaml:
  - full mutant manifest coverage: every mutant caught by its designated check
        -> test_full_manifest_coverage (via verify_all), test_mutant_*
  - goldens clean under every S5 check and the merged runner
        -> test_golden_clean_*, test_verify_all_goldens_clean
  - verify_all.py summary schema stable and documented
        -> test_verify_all_schema

Pure tests exercise the algorithms on synthetic boards without any toolchain;
corpus tests are also toolchain-free (committed boards + pure-venv geometry).
Only the timing test carries the `smoke` marker.
"""
from __future__ import annotations

import json
import math
import subprocess
import sys
import time
from pathlib import Path

import pytest
import yaml
from shapely.geometry import box

REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / ".claude" / "skills" / "ai-ee" / "scripts"
GOLDEN = REPO / "tests" / "golden"
PYTHON = sys.executable
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(SCRIPTS / "lib"))
import check_creepage  # noqa: E402
import check_decoupling  # noqa: E402
import check_diffpair  # noqa: E402
import check_pdn  # noqa: E402
import check_silk  # noqa: E402
import check_thermal  # noqa: E402
import checklib  # noqa: E402
import cluster_violations  # noqa: E402
import geom  # noqa: E402
import verify_all  # noqa: E402

MANIFEST = yaml.safe_load((GOLDEN / "manifest.yaml").read_text(encoding="utf-8"))
BOARDS = list(MANIFEST["golden_boards"])
S5_CHECKS = ["check_diffpair", "check_silk", "check_creepage",
             "check_thermal", "check_pdn"]
# checks that exist by end of S5 (dfm_check is S12)
BUILT_CHECKS = {"check_return_path", "check_current", "check_decoupling",
                "check_diffpair", "check_silk"}


def board_path(name: str) -> Path:
    return GOLDEN / name / f"{name}.kicad_pcb"


def mutant_path(mutant: str) -> Path:
    board = MANIFEST["mutants"][mutant]["board"]
    return GOLDEN / "mutants" / mutant / f"{board}.kicad_pcb"


def golden_of(mutant: str) -> str:
    return MANIFEST["mutants"][mutant]["board"]


# ---- synthetic board helpers (mirror test_checks.py) ----------------------

def _board(tmp_path_factory, name: str, body: str) -> geom.BoardGeom:
    text = f"""(kicad_pcb
  (version 20260206) (generator "test")
  (general (thickness 1.6))
  (layers (0 "F.Cu" signal) (2 "B.Cu" signal) (25 "Edge.Cuts" user))
  (setup)
  (gr_rect (start -2 -2) (end 24 12) (stroke (width 0.1)) (fill no)
    (layer "Edge.Cuts"))
{body})
"""
    p = tmp_path_factory.mktemp(name) / f"{name}.kicad_pcb"
    p.write_text(text, encoding="utf-8")
    return geom.load_board(p)


# ============================================================ pure: creepage

def test_ipc2221_clearance_table():
    c = check_creepage.clearance_mm
    # external (outer): band boundaries
    assert c(15, True) == 0.10
    assert c(30, True) == 0.10
    assert c(31, True) == 0.60
    assert c(100, True) == 0.60
    assert c(150, True) == 0.60
    assert c(170, True) == 1.25
    assert c(300, True) == 1.25
    assert c(500, True) == 2.50
    # internal
    assert c(50, False) == 0.10
    assert c(150, False) == 0.20
    assert c(500, False) == 0.25
    # > 500 V linear
    assert c(1000, True) == pytest.approx(2.50 + 0.005 * 500)   # 5.0
    assert c(1000, False) == pytest.approx(0.25 + 0.0025 * 500)  # 1.5


def test_creepage_hv_pair_flagged(tmp_path_factory):
    body = ('  (segment (start 2 2) (end 18 2) (width 0.5) (layer "F.Cu") '
            '(net "HV"))\n'
            '  (segment (start 2 2.8) (end 18 2.8) (width 0.5) (layer "F.Cu") '
            '(net "GND"))\n')
    bg = _board(tmp_path_factory, "hv", body)
    vmap = {"HV": 100.0, "GND": 0.0}
    vs, facts = check_creepage.check_net(bg, "HV", 100.0, vmap)
    assert len(vs) == 1
    v = vs[0]
    assert v["net"] == "HV" and v["other_net"] == "GND"
    assert v["required_mm"] == 0.60 and v["spacing_mm"] == pytest.approx(0.30)


def test_creepage_below_30v_ignored(tmp_path_factory):
    body = ('  (segment (start 2 2) (end 18 2) (width 0.5) (layer "F.Cu") '
            '(net "A"))\n'
            '  (segment (start 2 2.8) (end 18 2.8) (width 0.5) (layer "F.Cu") '
            '(net "B"))\n')
    bg = _board(tmp_path_factory, "lv", body)
    vs, _ = check_creepage.check_net(bg, "A", 20.0, {"A": 20.0, "B": 0.0})
    assert vs == []          # 20 V difference is below the 30 V threshold


# ============================================================ pure: thermal

def test_theta_ja_monotonic_and_saturates():
    t = check_thermal.theta_ja
    assert t(0, False) == pytest.approx(174.0)             # bare footprint
    # area clamps at ~1 in^2 (A_SAT), so theta bottoms at theta(A_SAT) ~ 74 C/W
    # for 1 oz - which matches the LM3940 datasheet (74 C/W at 1 in^2)
    assert t(1e9, False) == pytest.approx(t(check_thermal.A_SAT_MM2, False))
    assert t(1e9, False) == pytest.approx(74.0, abs=1.0)
    assert 55.0 < t(1e9, False) < 174.0
    vals = [t(a, False) for a in range(0, 700, 20)]
    assert all(b <= a for a, b in zip(vals, vals[1:]))     # decreasing
    assert t(300, True) < t(300, False)                    # planes spread better


def test_thermal_area_and_via_flags(tmp_path_factory):
    # one dissipating part; GND copper is only a small pad island
    body = ('  (footprint "t:U" (at 10 6) (layer "F.Cu")\n'
            '    (property "Reference" "U9" (at 0 0 0) (layer "F.SilkS"))\n'
            '    (pad "1" smd rect (at 0 0) (size 2 2) (layers "F.Cu") '
            '(net "GND")))\n')
    bg = _board(tmp_path_factory, "hot", body)
    vs, facts = check_thermal.check_part(
        bg, {"ref": "U9", "net": "GND", "power_w": 1.5, "dt_c": 40})
    assert any(v["kind"] == "thermal_area" for v in vs)
    assert facts["rise_c"] > 40


def test_thermal_low_power_passes(tmp_path_factory):
    body = ('  (footprint "t:U" (at 10 6) (layer "F.Cu")\n'
            '    (property "Reference" "U9" (at 0 0 0) (layer "F.SilkS"))\n'
            '    (pad "1" smd rect (at 0 0) (size 2 2) (layers "F.Cu") '
            '(net "GND")))\n'
            '  (zone (net "GND") (layer "F.Cu")\n'
            '    (polygon (pts (xy 0 0) (xy 22 0) (xy 22 10) (xy 0 10)))\n'
            '    (filled_polygon (layer "F.Cu")\n'
            '      (pts (xy 0 0) (xy 22 0) (xy 22 10) (xy 0 10))))\n')
    bg = _board(tmp_path_factory, "cool", body)
    vs, facts = check_thermal.check_part(
        bg, {"ref": "U9", "net": "GND", "power_w": 0.2, "dt_c": 40})
    assert [v for v in vs if v["kind"] == "thermal_area"] == []


# ============================================================ pure: pdn

def test_pdn_no_bulk_and_undecoupled():
    bg = None  # check_rail only reads bg.nets for on_board; use a stub
    class _BG:
        nets = {"+3V3", "VDDA"}
    assocs = [{"cap": "C1", "rail": "+3V3", "value": "100nF"}]
    vs, facts = check_pdn.check_rail(_BG(), "+3V3", 0.4, assocs)
    assert vs[0]["kind"] == "pdn_no_bulk" and facts["bulk_count"] == 0
    vs2, facts2 = check_pdn.check_rail(_BG(), "VDDA", 0.1, assocs)
    assert vs2[0]["kind"] == "pdn_undecoupled" and facts2["cap_count"] == 0


def test_pdn_bulk_plus_ceramic_clean():
    class _BG:
        nets = {"+3V3"}
    assocs = [{"cap": "C1", "rail": "+3V3", "value": "100nF"},
              {"cap": "C2", "rail": "+3V3", "value": "10uF"}]
    vs, facts = check_pdn.check_rail(_BG(), "+3V3", 0.4, assocs)
    assert vs == []
    assert facts["bulk_count"] == 1 and facts["ceramic_count"] == 1


# ============================================================ pure: diffpair

def test_discover_pairs():
    d = check_diffpair.discover_pairs
    assert d({"/USB_DP", "/USB_DM"}) == [("/USB_DP", "/USB_DM")]
    assert d({"/DIFF_P", "/DIFF_N"}) == [("/DIFF_P", "/DIFF_N")]
    assert d({"/CLK+", "/CLK-"}) == [("/CLK+", "/CLK-")]
    assert d({"+3V3", "GND", "/SCK", "/MISO", "/MOSI"}) == []
    # both ordered positive-first
    assert d({"/HS_N", "/HS_P"}) == [("/HS_P", "/HS_N")]


def _diffpair_body(n_track: str) -> str:
    return (
        '  (footprint "t:J" (at 0 5) (layer "F.Cu")\n'
        '    (property "Reference" "J1" (at 0 0 0) (layer "F.SilkS"))\n'
        '    (pad "1" smd rect (at 0 -0.15) (size 0.4 0.4) (layers "F.Cu") (net "/D_P"))\n'
        '    (pad "2" smd rect (at 0 0.15) (size 0.4 0.4) (layers "F.Cu") (net "/D_N")))\n'
        '  (footprint "t:U" (at 18 5) (layer "F.Cu")\n'
        '    (property "Reference" "U1" (at 0 0 0) (layer "F.SilkS"))\n'
        '    (pad "1" smd rect (at 0 -0.15) (size 0.4 0.4) (layers "F.Cu") (net "/D_P"))\n'
        '    (pad "2" smd rect (at 0 0.15) (size 0.4 0.4) (layers "F.Cu") (net "/D_N")))\n'
        '  (segment (start 0 4.85) (end 18 4.85) (width 0.25) (layer "F.Cu") (net "/D_P"))\n'
        + n_track)


PAIR_OK = _diffpair_body(
    '  (segment (start 0 5.15) (end 18 5.15) (width 0.25) (layer "F.Cu") (net "/D_N"))\n')
PAIR_MEANDER = _diffpair_body(
    '  (segment (start 0 5.15) (end 6 5.15) (width 0.25) (layer "F.Cu") (net "/D_N"))\n'
    '  (segment (start 6 5.15) (end 6 9) (width 0.25) (layer "F.Cu") (net "/D_N"))\n'
    '  (segment (start 6 9) (end 12 9) (width 0.25) (layer "F.Cu") (net "/D_N"))\n'
    '  (segment (start 12 9) (end 12 5.15) (width 0.25) (layer "F.Cu") (net "/D_N"))\n'
    '  (segment (start 12 5.15) (end 18 5.15) (width 0.25) (layer "F.Cu") (net "/D_N"))\n')


def test_diffpair_clean_pair(tmp_path_factory):
    bg = _board(tmp_path_factory, "pairok", PAIR_OK)
    vs, facts = check_diffpair.check_pair(bg, {"p": "/D_P", "n": "/D_N"})
    assert vs == []
    assert facts["skew_mm"] == pytest.approx(0.0, abs=1e-6)
    assert facts["branch_free"] is True
    assert facts["uncoupled_p_mm"] == pytest.approx(0.0, abs=0.2)


def test_diffpair_meander_uncoupled(tmp_path_factory):
    bg = _board(tmp_path_factory, "pairmeander", PAIR_MEANDER)
    vs, facts = check_diffpair.check_pair(bg, {"p": "/D_P", "n": "/D_N"})
    unc = [v for v in vs if v["kind"] == "diffpair_uncoupled"]
    assert len(unc) == 1 and unc[0]["severity"] == "error"
    assert facts["uncoupled_n_mm"] > 5.0


def test_diffpair_branch_free_excludes_stub(tmp_path_factory):
    """A series/pull stub on one net must not inflate its trunk length."""
    stub = ('  (segment (start 0 5.15) (end 18 5.15) (width 0.25) (layer "F.Cu") (net "/D_N"))\n'
            '  (segment (start 9 4.85) (end 9 1) (width 0.25) (layer "F.Cu") (net "/D_P"))\n')
    bg = _board(tmp_path_factory, "pairstub", _diffpair_body(stub))
    _, facts = check_diffpair.check_pair(bg, {"p": "/D_P", "n": "/D_N"})
    # D_P trunk is the 18 mm run, NOT 18 + 3.85 mm stub
    assert facts["length_p_mm"] == pytest.approx(18.0, abs=0.1)
    assert facts["branch_free"] is True


def test_diffpair_via_asymmetry(tmp_path_factory):
    body = PAIR_OK + \
        '  (via (at 9 4.85) (size 0.6) (drill 0.3) (layers "F.Cu" "B.Cu") (net "/D_P"))\n'
    bg = _board(tmp_path_factory, "pairvia", body)
    vs, _ = check_diffpair.check_pair(bg, {"p": "/D_P", "n": "/D_N"})
    assert any(v["kind"] == "diffpair_via_asymmetry" for v in vs)


# ============================================================ pure: silk

def test_silk_over_pad_center_rule(tmp_path_factory):
    body = ('  (footprint "t:D" (at 10 6) (layer "F.Cu")\n'
            '    (property "Reference" "D1" (at 0 -2 0) (layer "F.SilkS"))\n'
            '    (pad "1" smd roundrect (at 0 0) (size 1 1.4) '
            '(roundrect_rratio 0.25) (layers "F.Cu") (net "K")))\n'
            '  (gr_text "XX" (at 10 6 0) (layer "F.SilkS") '
            '(effects (font (size 1 1) (thickness 0.15))))\n')
    bg = _board(tmp_path_factory, "silkhit", body)
    root = __import__("sexpdata").loads(bg.path.read_text(encoding="utf-8"))
    vs = check_silk.run_checks(bg, check_silk.parse_silk(root))
    assert any(v["kind"] == "silk_over_pad" and "D1" in v["refs"] for v in vs)


def test_silk_beside_pad_clean(tmp_path_factory):
    body = ('  (footprint "t:D" (at 10 6) (layer "F.Cu")\n'
            '    (property "Reference" "D1" (at 0 -2 0) (layer "F.SilkS"))\n'
            '    (pad "1" smd rect (at 0 0) (size 1 1) (layers "F.Cu") (net "K")))\n'
            '  (gr_text "R1" (at 15 6 0) (layer "F.SilkS") '
            '(effects (font (size 1 1) (thickness 0.15))))\n')
    bg = _board(tmp_path_factory, "silkclear", body)
    root = __import__("sexpdata").loads(bg.path.read_text(encoding="utf-8"))
    vs = check_silk.run_checks(bg, check_silk.parse_silk(root))
    assert [v for v in vs if v["kind"] == "silk_over_pad"] == []


def test_silk_legibility(tmp_path_factory):
    body = ('  (gr_text "tiny" (at 10 6 0) (layer "F.SilkS") '
            '(effects (font (size 0.5 0.5) (thickness 0.15))))\n')
    bg = _board(tmp_path_factory, "silktiny", body)
    root = __import__("sexpdata").loads(bg.path.read_text(encoding="utf-8"))
    vs = check_silk.run_checks(bg, check_silk.parse_silk(root))
    assert any(v["kind"] == "silk_illegible" for v in vs)


def test_silk_rotated_refdes_no_false_positive(tmp_path_factory):
    """A vertical refdes tucked beside tiny pads (the rf4 C15 case) must be
    read with the absolute text angle so its box clears the pads."""
    # fp rotated -90: pad locals (+/-0.775, 0) become a vertical column at
    # x=fp_x; the ref local (0,-1.43,270) puts vertical text 1.43 mm to the
    # side. Reading the text angle as absolute (270) keeps its box off the pads;
    # (mis)adding the fp rotation would swing it horizontal, across them.
    body = ('  (footprint "t:C" (at 10 6 -90) (layer "F.Cu")\n'
            '    (property "Reference" "C15" (at 0 -1.43 270) (layer "F.SilkS") '
            '(effects (font (size 1 1) (thickness 0.15))))\n'
            '    (pad "1" smd roundrect (at -0.775 0) (size 0.9 0.95) '
            '(roundrect_rratio 0.25) (layers "F.Cu") (net "A"))\n'
            '    (pad "2" smd roundrect (at 0.775 0) (size 0.9 0.95) '
            '(roundrect_rratio 0.25) (layers "F.Cu") (net "B")))\n')
    bg = _board(tmp_path_factory, "c15", body)
    root = __import__("sexpdata").loads(bg.path.read_text(encoding="utf-8"))
    vs = check_silk.run_checks(bg, check_silk.parse_silk(root))
    assert [v for v in vs if v["kind"] == "silk_over_pad"] == []


# ============================================================ pure: cluster

def test_cluster_by_net_kind_region():
    violations = [
        {"source": "check_return_path", "severity": "error",
         "kind": "corridor_void", "net": "/MCO", "pos": [141.0, 123.0]},
        {"source": "check_return_path", "severity": "error",
         "kind": "corridor_void", "net": "/MCO", "pos": [141.3, 123.2]},
        {"source": "check_current", "severity": "error",
         "kind": "undersized_track", "net": "+3V3", "pos": [60.0, 40.0]},
        {"source": "check_pdn", "severity": "warning",
         "kind": "pdn_no_bulk", "net": "VDDA", "pos": None},
    ]
    clusters = cluster_violations.cluster(violations, radius=5.0)
    assert len(clusters) == 3          # two /MCO merge by region; others alone
    mco = next(c for c in clusters if c["net"] == "/MCO")
    assert mco["count"] == 2 and mco["fixer"] == "plane"
    assert mco["region"]["bbox"] is not None
    # errors sort before warnings
    assert clusters[0]["severity"] == "error"
    assert clusters[-1]["severity"] == "warning"


def test_cluster_far_apart_split():
    violations = [
        {"source": "c", "severity": "error", "kind": "corridor_void",
         "net": "GND", "pos": [10, 10]},
        {"source": "c", "severity": "error", "kind": "corridor_void",
         "net": "GND", "pos": [80, 80]},
    ]
    clusters = cluster_violations.cluster(violations, radius=5.0)
    assert len(clusters) == 2          # same net+kind, but far apart


# ============================================================ corpus: goldens

@pytest.mark.parametrize("board", BOARDS)
def test_golden_clean_diffpair(board):
    payload, _ = check_diffpair.run(["--pcb", str(board_path(board))])
    assert payload["status"] == "pass", json.dumps(payload["violations"])


@pytest.mark.parametrize("board", BOARDS)
def test_golden_clean_silk(board):
    payload, _ = check_silk.run(["--pcb", str(board_path(board))])
    assert payload["status"] == "pass", json.dumps(payload["violations"])


@pytest.mark.parametrize("board", BOARDS)
def test_golden_clean_creepage(board):
    payload, _ = check_creepage.run(
        ["--pcb", str(board_path(board)),
         "--constraints", str(GOLDEN / board / "constraints.json")])
    assert payload["status"] == "pass", json.dumps(payload["violations"])


@pytest.mark.parametrize("board", BOARDS)
def test_golden_clean_thermal(board):
    payload, _ = check_thermal.run(
        ["--pcb", str(board_path(board)),
         "--constraints", str(GOLDEN / board / "constraints.json")])
    assert payload["status"] == "pass", json.dumps(payload["violations"])


@pytest.mark.parametrize("board", BOARDS)
def test_golden_clean_pdn(board):
    payload, _ = check_pdn.run(
        ["--pcb", str(board_path(board)),
         "--constraints", str(GOLDEN / board / "constraints.json"),
         "--decoupling", str(GOLDEN / board / "decoupling.json")])
    assert payload["status"] == "pass", json.dumps(payload["violations"])


def test_verify_all_goldens_clean(tmp_path):
    for board in BOARDS:
        summary, _ = verify_all.run(
            ["--pcb", str(board_path(board)),
             "--constraints", str(GOLDEN / board / "constraints.json"),
             "--decoupling", str(GOLDEN / board / "decoupling.json"),
             "--reports-dir", str(tmp_path / board)])
        assert summary["status"] == "pass", json.dumps(summary["counts"])
        # every built check actually ran (not skipped) on a golden
        for name in ("check_return_path", "check_current", "check_decoupling",
                     *S5_CHECKS):
            assert summary["checks"][name]["status"] == "pass", name


# ============================================================ corpus: mutants

def test_mutant_diffpair_skew_caught():
    m = MANIFEST["mutants"]["diffpair-skew"]
    board = m["board"]
    payload, _ = check_diffpair.run(
        ["--pcb", str(mutant_path("diffpair-skew")),
         "--constraints", str(GOLDEN / board / "constraints.json")])
    assert payload["status"] == "violations"
    exp = m["expect"]
    hits = [v for v in payload["violations"]
            if v["kind"] == "diffpair_uncoupled"
            and set(v["pair"]) == set(exp["pair"])]
    assert len(hits) == 1, json.dumps(payload["violations"])
    assert hits[0]["uncoupled_mm"] >= exp["min_skew_mm"]
    assert hits[0]["severity"] == "error"


def test_mutant_silk_over_pad_caught():
    m = MANIFEST["mutants"]["silk-over-pad"]
    payload, _ = check_silk.run(["--pcb", str(mutant_path("silk-over-pad"))])
    assert payload["status"] == "violations"
    exp = m["expect"]
    hits = [v for v in payload["violations"]
            if v["kind"] == "silk_over_pad" and exp["ref"] in v["refs"]]
    assert len(hits) == 1, json.dumps(payload["violations"])
    v = hits[0]
    assert math.hypot(v["pos"][0] - exp["pos"][0],
                      v["pos"][1] - exp["pos"][1]) < 0.5


@pytest.mark.parametrize("mutant", sorted(MANIFEST["mutants"]))
def test_non_target_mutants_stay_clean(mutant):
    """Each S5 check must not fire on mutants it does not own (no cross-talk)."""
    target = MANIFEST["mutants"][mutant]["check"]
    board = golden_of(mutant)
    for script, mod in (("check_diffpair", check_diffpair),
                        ("check_silk", check_silk),
                        ("check_creepage", check_creepage),
                        ("check_thermal", check_thermal)):
        if script == target:
            continue
        argv = ["--pcb", str(mutant_path(mutant))]
        if script in ("check_creepage",):
            argv += ["--constraints", str(GOLDEN / board / "constraints.json")]
        elif script == "check_thermal":
            argv += ["--constraints", str(GOLDEN / board / "constraints.json")]
        payload, _ = mod.run(argv)
        assert payload["status"] == "pass", \
            f"{script} fired on {mutant}: {json.dumps(payload['violations'])}"


def test_full_manifest_coverage(tmp_path):
    """Every mutant whose designated check exists by S5 is caught by that check
    when the whole suite runs (cpl-rotation -> dfm_check is S12's to catch)."""
    for mutant, m in MANIFEST["mutants"].items():
        target = m["check"]
        if target not in BUILT_CHECKS:
            continue
        board = m["board"]
        summary, _ = verify_all.run(
            ["--pcb", str(mutant_path(mutant)),
             "--constraints", str(GOLDEN / board / "constraints.json"),
             "--decoupling", str(GOLDEN / board / "decoupling.json"),
             "--reports-dir", str(tmp_path / mutant)])
        assert summary["checks"][target]["status"] == "violations", \
            f"{mutant}: {target} did not catch it"
        assert any(v.get("source") == target for v in summary["violations"])


def test_cpl_rotation_deferred_to_dfm():
    """cpl-rotation is dfm_check's (S12); it must not be caught by any S5 check
    (documents the coverage gap so it is not silently 'passing')."""
    assert MANIFEST["mutants"]["cpl-rotation"]["check"] == "dfm_check"
    assert "dfm_check" not in BUILT_CHECKS


# ============================================================ verify_all schema

def test_verify_all_schema(tmp_path):
    summary, _ = verify_all.run(
        ["--pcb", str(board_path("usbbuck4")),
         "--constraints", str(GOLDEN / "usbbuck4" / "constraints.json"),
         "--decoupling", str(GOLDEN / "usbbuck4" / "decoupling.json"),
         "--reports-dir", str(tmp_path)])
    for key in ("script", "board", "status", "counts", "checks", "violations"):
        assert key in summary
    assert summary["script"] == "verify_all"
    assert set(summary["counts"]) >= {"total", "by_severity", "by_source",
                                      "by_check"}
    # every check has an entry with a stable shape
    for name in ("check_return_path", *S5_CHECKS):
        entry = summary["checks"][name]
        assert set(entry) >= {"status", "counts", "report"}
    # per-check report files were written
    assert (tmp_path / "summary.json").exists()
    assert (tmp_path / "check_silk.json").exists()


def test_verify_all_skips_missing_inputs(tmp_path):
    """Without decoupling/constraints, the checks needing them are SKIPPED, not
    errored; board-only checks still run."""
    summary, _ = verify_all.run(
        ["--pcb", str(board_path("blinky2")),
         "--reports-dir", str(tmp_path)])
    assert summary["checks"]["check_decoupling"]["status"] == "skipped"
    assert summary["checks"]["check_pdn"]["status"] == "skipped"
    assert summary["checks"]["check_silk"]["status"] == "pass"
    assert summary["checks"]["check_diffpair"]["status"] == "pass"


# ============================================================ CLI contract

def test_cli_exit_codes_and_out(tmp_path):
    # clean board -> exit 0
    proc = subprocess.run(
        [PYTHON, str(SCRIPTS / "check_diffpair.py"),
         "--pcb", str(board_path("usbbuck4")), "--out", str(tmp_path / "d.json")],
        capture_output=True, text=True)
    assert proc.returncode == 0
    payload = json.loads((tmp_path / "d.json").read_text(encoding="utf-8"))
    assert payload["script"] == "check_diffpair" and payload["status"] == "pass"
    # mutant -> exit 1 with normalized schema
    proc = subprocess.run(
        [PYTHON, str(SCRIPTS / "check_silk.py"),
         "--pcb", str(mutant_path("silk-over-pad"))],
        capture_output=True, text=True)
    assert proc.returncode == 1
    v = json.loads(proc.stdout)["violations"][0]
    for key in ("check", "severity", "pos", "layer", "net", "refs", "msg",
                "source", "items"):
        assert key in v
    # cluster_violations exits 1 when clusters present
    summ = tmp_path / "s.json"
    summ.write_text(json.dumps({"violations": [
        {"source": "c", "severity": "error", "kind": "x", "net": "N",
         "pos": [1, 1]}]}), encoding="utf-8")
    proc = subprocess.run(
        [PYTHON, str(SCRIPTS / "cluster_violations.py"), "--input", str(summ)],
        capture_output=True, text=True)
    assert proc.returncode == 1
    # bad input -> exit 2
    proc = subprocess.run(
        [PYTHON, str(SCRIPTS / "check_creepage.py"),
         "--pcb", str(board_path("rf4")), "--constraints", str(tmp_path / "no.json")],
        capture_output=True, text=True)
    assert proc.returncode == 2


# ============================================================ regressions
# (bugs found by the S5 adversarial review; each test locks a fix)

def test_discover_pairs_conservative():
    """H/L and lone single-letter suffixes are NOT differential pairs."""
    d = check_diffpair.discover_pairs
    assert d({"/VREFH", "/VREFL"}) == []
    assert d({"/ADDR_H", "/ADDR_L"}) == []
    assert d({"/USB_DP", "/USB_DM"}) == [("/USB_DP", "/USB_DM")]   # still works
    assert d({"/LVDS_P", "/LVDS_N"}) == [("/LVDS_P", "/LVDS_N")]


def test_diffpair_unrouted_half_no_nan(tmp_path_factory):
    """One net pad-only (unrouted) -> reported not-routed, no NaN in the JSON."""
    bg = _board(tmp_path_factory, "unrouted", _diffpair_body(""))  # no D_N track
    vs, facts = check_diffpair.check_pair(bg, {"p": "/D_P", "n": "/D_N"})
    assert vs == [] and facts["routed"] is False
    json.dumps(facts, allow_nan=False)          # would raise on NaN tokens


def test_diffpair_absent_pair_warns_not_aborts(tmp_path):
    cons = tmp_path / "c.json"
    cons.write_text(json.dumps({"diff_pairs": [
        {"p": "/USB_DP", "n": "/USB_DM"},
        {"p": "/GHOST_P", "n": "/GHOST_N"}]}), encoding="utf-8")
    payload, _ = check_diffpair.run(
        ["--pcb", str(board_path("usbbuck4")), "--constraints", str(cons)])
    assert payload["status"] == "violations"     # warning, not exit-2 error
    kinds = {v["kind"] for v in payload["violations"]}
    assert "diffpair_missing_net" in kinds
    assert payload["checked"], "the valid pair was still evaluated"


def test_diffpair_empty_pairs_no_autodiscovery(tmp_path):
    cons = tmp_path / "c.json"
    cons.write_text(json.dumps({"diff_pairs": []}), encoding="utf-8")
    payload, _ = check_diffpair.run(
        ["--pcb", str(board_path("usbbuck4")), "--constraints", str(cons)])
    assert payload["status"] == "pass" and payload["checked"] == []


def test_diffpair_single_layer_no_crash(tmp_path_factory):
    text = """(kicad_pcb (version 20260206) (generator "test")
  (general (thickness 1.6))
  (layers (0 "F.Cu" signal) (25 "Edge.Cuts" user)) (setup)
  (gr_rect (start -2 -2) (end 24 12) (stroke (width 0.1)) (fill no)
    (layer "Edge.Cuts"))
""" + _diffpair_body(
        '  (segment (start 0 5.15) (end 18 5.15) (width 0.25) (layer "F.Cu") (net "/D_N"))\n') + ")\n"
    p = tmp_path_factory.mktemp("single") / "s.kicad_pcb"
    p.write_text(text, encoding="utf-8")
    bg = geom.load_board(p)
    vs, facts = check_diffpair.check_pair(bg, {"p": "/D_P", "n": "/D_N"})
    assert facts["skew_ps"] is not None          # eps fell back to FR4, no crash


def test_creepage_absent_voltage_net_skipped(tmp_path):
    cons = tmp_path / "c.json"
    cons.write_text(json.dumps({"voltages": [{"net": "/GHOST", "voltage": 400}]}),
                    encoding="utf-8")
    payload, _ = check_creepage.run(
        ["--pcb", str(board_path("blinky2")), "--constraints", str(cons)])
    assert payload["status"] == "pass"           # skipped, not exit-2
    assert "/GHOST" in payload["skipped_absent_nets"]


def test_thermal_distant_pour_not_counted(tmp_path_factory):
    """A big same-net pour far from the part is not its heatsink (local reach)."""
    text = """(kicad_pcb (version 20260206) (generator "test")
  (general (thickness 1.6))
  (layers (0 "F.Cu" signal) (2 "B.Cu" signal) (25 "Edge.Cuts" user)) (setup)
  (gr_rect (start -2 -2) (end 62 12) (stroke (width 0.1)) (fill no)
    (layer "Edge.Cuts"))
  (footprint "t:U" (at 10 6) (layer "F.Cu")
    (property "Reference" "U9" (at 0 0 0) (layer "F.SilkS"))
    (pad "1" smd rect (at 0 0) (size 1 1) (layers "F.Cu") (net "GND")))
  (zone (net "GND") (layer "F.Cu")
    (polygon (pts (xy 40 0) (xy 58 0) (xy 58 10) (xy 40 10)))
    (filled_polygon (layer "F.Cu")
      (pts (xy 40 0) (xy 58 0) (xy 58 10) (xy 40 10)))))
"""
    p = tmp_path_factory.mktemp("distant") / "d.kicad_pcb"
    p.write_text(text, encoding="utf-8")
    bg = geom.load_board(p)
    vs, facts = check_thermal.check_part(
        bg, {"ref": "U9", "net": "GND", "power_w": 1.0, "dt_c": 40})
    # the 180 mm^2 pour is >25 mm away -> excluded; only the 1 mm^2 pad counts
    assert facts["area_mm2"] < 10
    assert any(v["kind"] == "thermal_area" for v in vs)


def test_pdn_micro_sign_parsed():
    p = check_decoupling.parse_farads
    assert p("10µF") == pytest.approx(1e-5)   # micro sign
    assert p("10μF") == pytest.approx(1e-5)   # Greek mu

    class _BG:
        nets = {"+3V3"}
    vs, facts = check_pdn.check_rail(
        _BG(), "+3V3", 0.4, [{"cap": "C1", "rail": "+3V3", "value": "10µF"}])
    assert facts["bulk_count"] == 1 and vs == []   # not mis-read as no-bulk


def test_cluster_missing_source_no_crash():
    clusters = cluster_violations.cluster(
        [{"severity": "error", "kind": "x", "net": "N", "pos": [1, 1]}], 5.0)
    assert len(clusters) == 1 and clusters[0]["checks"] == []


def test_verify_all_no_stale_report(tmp_path):
    """A check that ERRORS this run must not be reported as pass from a stale
    report file left by a previous run."""
    # board with an unfilled zone -> the zone-reading checks exit 2
    board = tmp_path / "stale.kicad_pcb"
    board.write_text("""(kicad_pcb (version 20260206) (generator "test")
  (general (thickness 1.6))
  (layers (0 "F.Cu" signal) (2 "B.Cu" signal) (25 "Edge.Cuts" user)) (setup)
  (gr_rect (start 0 0) (end 20 10) (stroke (width 0.1)) (fill no)
    (layer "Edge.Cuts"))
  (segment (start 1 1) (end 9 1) (width 0.25) (layer "F.Cu") (net "+3V3"))
  (zone (net "GND") (layer "B.Cu")
    (polygon (pts (xy 0 0) (xy 20 0) (xy 20 10) (xy 0 10)))))
""", encoding="utf-8")
    cons = tmp_path / "constraints.json"
    cons.write_text(json.dumps({"power": [{"net": "+3V3", "current_a": 0.4}]}),
                    encoding="utf-8")
    reports = tmp_path / "reports"
    reports.mkdir()
    (reports / "check_current.json").write_text(
        json.dumps({"script": "check_current", "status": "pass",
                    "counts": {"total": 0}, "violations": []}), encoding="utf-8")
    summary, _ = verify_all.run(
        ["--pcb", str(board), "--constraints", str(cons),
         "--reports-dir", str(reports)])
    assert summary["checks"]["check_current"]["status"] == "error"


# ============================================================ smoke: timing

@pytest.mark.smoke
def test_verify_all_rf4_under_30s(tmp_path):
    t0 = time.perf_counter()
    geom._CACHE.clear()
    verify_all.run(
        ["--pcb", str(board_path("rf4")),
         "--constraints", str(GOLDEN / "rf4" / "constraints.json"),
         "--decoupling", str(GOLDEN / "rf4" / "decoupling.json"),
         "--reports-dir", str(tmp_path)])
    elapsed = time.perf_counter() - t0
    assert elapsed < 30.0, f"verify_all took {elapsed:.1f}s on rf4"
