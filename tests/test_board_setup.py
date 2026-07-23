"""S8 acceptance tests: board setup + reference data.

Plan S8 accept criteria:
  - from golden board 2's netlist + a constraints.json: initialized board passes
    DRC setup checks (schematic parity 0, no courtyard/setup violations; the
    unrouted board's unconnected_items are expected and excluded)
  - generated rules demonstrably enforced: a violating test track fails DRC with
    the custom rule named

Pure tests (reference-data validation, rules_gen/impedance/board_init logic) run
with no toolchain and are unmarked; live-kicad-cli tests carry `smoke`.
"""
from __future__ import annotations

import csv
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[1]
SKILL = REPO / ".claude" / "skills" / "ai-ee"
SCRIPTS = SKILL / "scripts"
REFERENCE = SKILL / "reference"
GOLDEN = REPO / "tests" / "golden"

sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(SCRIPTS / "lib"))
import env  # noqa: E402
import impedance as imp  # noqa: E402
import rules_gen  # noqa: E402
import board_init  # noqa: E402
import kc  # noqa: E402


# ============================================================ reference data

def test_capabilities_yaml_valid():
    cap = yaml.safe_load((REFERENCE / "jlc_capabilities.yaml").read_text("utf-8"))
    dr = cap["design_rules"]
    for cls in ("2layer_1oz", "4layer_1oz", "4layer_2oz", "6layer_1oz"):
        assert cls in dr, f"missing capability class {cls}"
    required = {"min_trace_width_mm", "min_clearance_mm", "min_via_drill_mm",
                "min_via_diameter_mm", "min_annular_ring_mm", "min_hole_to_hole_mm",
                "min_copper_to_edge_mm", "min_silk_width_mm"}
    for cls, row in dr.items():
        assert required <= set(row), f"{cls} missing {required - set(row)}"
        assert 0 < row["min_trace_width_mm"] < 1
    # cited source present
    assert cap["meta"]["source_urls"]
    # 4-layer is finer than 2-layer (sanity vs JLC published tiers)
    assert dr["4layer_1oz"]["min_trace_width_mm"] < dr["2layer_1oz"]["min_trace_width_mm"]


def test_stackups_yaml_valid():
    st = yaml.safe_load((REFERENCE / "stackups.yaml").read_text("utf-8"))
    assert st["defaults"][2] in st["stackups"]
    assert st["defaults"][4] in st["stackups"]
    for name, s in st["stackups"].items():
        coppers = [ly for ly in s["stack"] if ly["type"] == "copper"]
        assert len(coppers) == s["layers"], f"{name}: copper count != layers"
        # physical stack sums near the nominal board thickness
        total = sum(ly["thickness_mm"] for ly in s["stack"])
        assert abs(total - s["thickness_mm"]) < 0.05, f"{name}: stack sums to {total}"
        for ci in s.get("controlled_impedance", []):
            assert ci["width_mm"] > 0
            if ci["kind"] == "diff":
                assert ci["gap_mm"] > 0
    # the 4-layer default has real copper layer names geom will match
    names = [ly["name"] for ly in st["stackups"][st["defaults"][4]]["stack"]
             if ly["type"] == "copper"]
    assert names == ["F.Cu", "In1.Cu", "In2.Cu", "B.Cu"]


def test_rotations_csv_valid():
    rows = []
    with open(REFERENCE / "jlc_rotations.csv", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("regex,"):
                continue
            rx, rot = line.rsplit(",", 1)
            re.compile(rx)                     # each pattern must compile
            rows.append((rx, float(rot)))
    table = dict(rows)
    assert table["^SOT-23"] == 180.0
    assert table["^QFN-"] == 270.0
    assert table["^LQFP-"] == 270.0
    assert len(rows) >= 30


def test_dru_templates_exist_and_parse():
    for name in ("jlc_2layer_1oz", "jlc_4layer_1oz"):
        p = REFERENCE / "design_rules" / f"{name}.kicad_dru"
        text = p.read_text("utf-8")
        assert text.startswith("(version 1)")
        assert text.count("(rule ") == text.count(")\n(rule ") + 1  # each rule closes
        assert "track_width" in text and "clearance" in text


def test_dru_templates_match_generator(tmp_path):
    """Drift guard: committed templates == rules_gen --baseline-only output."""
    for name, layers in (("jlc_2layer_1oz", 2), ("jlc_4layer_1oz", 4)):
        out = tmp_path / f"{name}.kicad_dru"
        rc = rules_gen.main(["--layers", str(layers), "--copper-oz", "1.0",
                             "--baseline-only", "--out-dru", str(out),
                             "--out", str(tmp_path / "r.json")])
        assert rc == 0
        committed = (REFERENCE / "design_rules" / f"{name}.kicad_dru").read_text("utf-8")
        assert out.read_text("utf-8") == committed, f"{name} drifted from generator"


# ============================================================ impedance.py

def test_impedance_microstrip_reference():
    # classic: 50 ohm microstrip on 1.6 mm FR4 (er~4.2) ~ 2.9-3.1 mm
    w = imp.solve_width(50, 1.6, 0.035, 4.2)
    assert 2.8 < w < 3.2
    assert abs(imp.microstrip_z0(w, 1.6, 0.035, 4.2) - 50) < 0.1


def test_impedance_monotonic():
    z = [imp.microstrip_z0(w, 0.2104, 0.035, 4.05) for w in (0.1, 0.2, 0.4, 0.8)]
    assert z == sorted(z, reverse=True)   # Z0 falls as width grows


def test_impedance_diff_roundtrip():
    h, t, er = 0.2104, 0.035, 4.05
    for zt in (90, 100):
        w, s = imp.diff_pair(zt, h, t, er)
        assert 0.1 < w < 1.0 and 0.1 < s < 0.6
        assert abs(imp._zdiff(w, s, h, t, er) - zt) < 0.5


def test_impedance_geometry_for():
    g = imp.geometry_for({"impedance_ohm": 90, "kind": "diff"}, 0.2104, 4.05, 1.0)
    assert g["width_mm"] > 0 and g["gap_mm"] > 0


# ============================================================ rules_gen logic

def test_capability_class():
    assert rules_gen.capability_class(4, 1.0) == "4layer_1oz"
    assert rules_gen.capability_class(2, 2.0) == "2layer_2oz"


def _cap(cls="4layer_1oz"):
    return yaml.safe_load((REFERENCE / "jlc_capabilities.yaml").read_text("utf-8"))["design_rules"][cls]


def _stackup(name="JLC04161H-3313"):
    return yaml.safe_load((REFERENCE / "stackups.yaml").read_text("utf-8"))["stackups"][name]


def test_baseline_rules_shape():
    rules = rules_gen.baseline_rules(_cap())
    names = [r.name for r in rules]
    assert "aiee_track_width_floor" in names
    assert "aiee_clearance_floor" in names
    kinds = {r.constraint for r in rules}
    assert {"track_width", "clearance", "hole_size", "via_diameter",
            "annular_width", "edge_clearance", "hole_to_hole"} <= kinds


def test_power_rules_widths():
    cons = json.loads((GOLDEN / "usbbuck4" / "constraints.json").read_text("utf-8"))
    rules, facts = rules_gen.power_rules(cons, cu_mm=0.035)
    byn = {f["net"]: f for f in facts}
    assert byn["+3V3"]["min_width_mm"] == pytest.approx(0.20, abs=0.01)   # 0.4 A
    assert byn["VBUS"]["min_width_mm"] == pytest.approx(0.25, abs=0.01)   # 0.5 A
    r = {x.name: x for x in rules}["aiee_pwr_width_3V3"]
    assert "A.NetName == '+3V3'" in r.condition and r.constraint == "track_width"


def test_detect_diff_pairs():
    cons = json.loads((GOLDEN / "usbbuck4" / "constraints.json").read_text("utf-8"))
    pairs = rules_gen.detect_diff_pairs(cons)
    assert len(pairs) == 1
    dp = pairs[0]
    assert set([dp["p"], dp["n"]]) == {"/USB_DP", "/USB_DM"}
    assert dp["impedance_ohm"] == 90            # USB default
    # /MCO is single-ended, must NOT be paired
    assert all("MCO" not in p["p"] for p in pairs)


def test_rules_ordering_baseline_before_specific():
    cons = json.loads((GOLDEN / "usbbuck4" / "constraints.json").read_text("utf-8"))
    rules, _ = rules_gen.build(cons, _cap(), _stackup(), baseline_only=False)
    names = [r.name for r in rules]
    # every floor rule precedes every per-net rule (later rule wins -> specifics last)
    last_floor = max(i for i, n in enumerate(names) if n.endswith("_floor"))
    first_specific = min(i for i, n in enumerate(names)
                         if n.startswith("aiee_pwr_") or n.startswith("aiee_diff_"))
    assert last_floor < first_specific


def test_net_classes():
    cons = json.loads((GOLDEN / "usbbuck4" / "constraints.json").read_text("utf-8"))
    _, report = rules_gen.build(cons, _cap(), _stackup(), baseline_only=False)
    cnames = {c["name"] for c in report["classes"]}
    assert "Power" in cnames and "Diff90" in cnames
    pats = {(p["netclass"], p["pattern"]) for p in report["patterns"]}
    assert ("Power", "+3V3") in pats and ("Diff90", "/USB_DP") in pats


# ============================================================ board_init logic

MINI_NET = """(export (version "E")
  (components
    (comp (ref "R1") (value "10k") (footprint "Resistor_SMD:R_0603_1608Metric"))
    (comp (ref "C1") (value "100nF") (footprint "Capacitor_SMD:C_0603_1608Metric")))
  (nets
    (net (code "1") (name "+3V3") (node (ref "R1") (pin "1")) (node (ref "C1") (pin "1")))
    (net (code "2") (name "GND") (node (ref "R1") (pin "2")) (node (ref "C1") (pin "2")))))
"""


def test_parse_netlist(tmp_path):
    n = tmp_path / "m.net"
    n.write_text(MINI_NET, encoding="utf-8")
    comps, netmap = board_init.parse_netlist(n)
    assert {c["ref"] for c in comps} == {"R1", "C1"}
    assert comps[0]["fp"] == "Resistor_SMD:R_0603_1608Metric"
    assert netmap["R1.1"] == "+3V3" and netmap["C1.2"] == "GND"


def test_parse_netlist_missing_fp_raises(tmp_path):
    bad = MINI_NET.replace('(footprint "Resistor_SMD:R_0603_1608Metric")', "")
    n = tmp_path / "bad.net"
    n.write_text(bad, encoding="utf-8")
    with pytest.raises(ValueError):
        board_init.parse_netlist(n)


def test_build_stackup_block():
    block = board_init.build_stackup_block(_stackup())
    assert block.lstrip().startswith("(stackup")
    for cu in ("F.Cu", "In1.Cu", "In2.Cu", "B.Cu"):
        assert f'"{cu}"' in block
    assert "dielectric 1" in block and "epsilon_r" in block
    assert "copper_finish" in block


def test_last_json_helper():
    assert board_init._last_json('noise\n{"a": 1}\n')["a"] == 1
    assert board_init._last_json("nothing here") is None


# ============================================================ smoke: live kicad

@pytest.fixture(scope="session")
def cli() -> Path:
    c = env.find_kicad_cli()
    if c is None:
        pytest.skip("kicad-cli not installed")
    return c


def _drc(cli, pcb, parity=False):
    return kc.run_drc(cli, pcb, parity=parity)


def _rule_names(report):
    out = []
    for v in report["violations"]:
        m = re.search(r"rule '([^']+)'", v["msg"] or "")
        if m:
            out.append(m.group(1))
    return out


@pytest.fixture()
def usbbuck4_net(cli, tmp_path_factory):
    """Export golden board 2's netlist once (input to board_init)."""
    d = tmp_path_factory.mktemp("net")
    out = d / "usbbuck4.net"
    r = kc.export_netlist(cli, GOLDEN / "usbbuck4" / "usbbuck4.kicad_sch", out)
    assert r["status"] == "pass"
    return out


@pytest.mark.smoke
def test_board_init_end_to_end(cli, usbbuck4_net, tmp_path):
    """ACCEPTANCE: netlist -> initialized board, parity clean, no setup violations."""
    rep = tmp_path / "report.json"
    rc = board_init.main([
        "--netlist", str(usbbuck4_net), "--name", "usbbuck4",
        "--out", str(tmp_path / "kicad"), "--layers", "4", "--mounting-holes", "4",
        "--schematic", str(GOLDEN / "usbbuck4" / "usbbuck4.kicad_sch"),
        "--out-report", str(rep)])
    r = json.loads(rep.read_text("utf-8"))
    assert rc == 0 and r["status"] == "pass", r
    sc = r["self_check"]
    assert sc["parity_count"] == 0            # every part+net imported correctly
    assert sc["setup_violations"] == []        # no courtyard/short/mask/silk
    assert sc["unconnected_count"] > 0         # unrouted by design
    assert r["components"] == 23 and r["mounting_holes"] == 4

    # stackup was injected and geom reads it as authoritative (not FR4-assumed)
    sys.path.insert(0, str(SCRIPTS / "lib"))
    import geom
    bg = geom.load_board(tmp_path / "kicad" / "usbbuck4.kicad_pcb")
    assert bg.stackup.assumed is False
    assert bg.stackup.copper_layers == ["F.Cu", "In1.Cu", "In2.Cu", "B.Cu"]


def _prep_golden(tmp_path, board="usbbuck4"):
    """Copy a golden board + pro + sch into tmp for mutation."""
    d = tmp_path / board
    d.mkdir()
    for ext in (".kicad_pcb", ".kicad_pro", ".kicad_sch"):
        src = GOLDEN / board / f"{board}{ext}"
        if src.exists():
            shutil.copy(src, d / f"{board}{ext}")
    return d / f"{board}.kicad_pcb"


@pytest.mark.smoke
def test_rules_gen_clean_golden(cli, tmp_path):
    """Generated rules must NOT false-positive on the clean golden."""
    pcb = _prep_golden(tmp_path)
    rc = rules_gen.main([
        "--constraints", str(GOLDEN / "usbbuck4" / "constraints.json"),
        "--layers", "4", "--out-dru", str(pcb.with_suffix(".kicad_dru")),
        "--out", str(tmp_path / "r.json")])
    assert rc == 0
    rep = _drc(cli, pcb, parity=True)
    assert rep["counts"]["total"] == 0, rep["violations"]


@pytest.mark.smoke
def test_rules_gen_enforced(cli, tmp_path):
    """ACCEPTANCE: a violating test track fails DRC with the custom rule named.

    Narrow a +3V3 track to 0.15 mm - below the per-net power rule (0.20 mm) but
    ABOVE the fab floor (0.1016 mm) - so ONLY aiee_pwr_width_3V3 may fire, which
    also proves the specific rule overrides the generic floor (later rule wins).
    """
    pcb = _prep_golden(tmp_path)
    rules_gen.main(["--constraints", str(GOLDEN / "usbbuck4" / "constraints.json"),
                    "--layers", "4", "--out-dru", str(pcb.with_suffix(".kicad_dru")),
                    "--out", str(tmp_path / "r.json")])
    text = pcb.read_text("utf-8")
    pat = re.compile(r'(\(segment\s+\(start[^)]*\)\s+\(end[^)]*\)\s+)'
                     r'\(width [\d.]+\)(\s+\(layer[^)]*\)\s+\(net "\+3V3"\))', re.S)
    m = pat.search(text)
    assert m, "no +3V3 segment found to narrow"
    pcb.write_text(text[:m.start()] + m.group(1) + "(width 0.15)" + m.group(2)
                   + text[m.end():], encoding="utf-8")

    rep = _drc(cli, pcb)
    names = _rule_names(rep)
    assert "aiee_pwr_width_3V3" in names, rep["violations"]
    # the floor rule must NOT also fire (0.15 > 0.1016): specific rule won
    assert "aiee_track_width_floor" not in names
    # the offending violation is on +3V3, type track_width
    hit = [v for v in rep["violations"] if "aiee_pwr_width_3V3" in (v["msg"] or "")]
    assert hit and hit[0]["check"] == "track_width" and hit[0]["net"] == "+3V3"


@pytest.mark.smoke
@pytest.mark.parametrize("board,template,layers", [
    ("blinky2", "jlc_2layer_1oz", 2),
    ("usbbuck4", "jlc_4layer_1oz", 4),
])
def test_baseline_template_no_false_positive(cli, tmp_path, board, template, layers):
    pcb = _prep_golden(tmp_path, board)
    shutil.copy(REFERENCE / "design_rules" / f"{template}.kicad_dru",
                pcb.with_suffix(".kicad_dru"))
    rep = _drc(cli, pcb)
    assert rep["counts"]["total"] == 0, rep["violations"]


@pytest.mark.smoke
def test_rules_gen_pro_write_keeps_board_clean(cli, tmp_path):
    """Writing net_settings into the .kicad_pro must not break the board
    (LEARNINGS [kicad]: a bad pro blob silently disables overrides)."""
    pcb = _prep_golden(tmp_path)
    rc = rules_gen.main([
        "--constraints", str(GOLDEN / "usbbuck4" / "constraints.json"),
        "--layers", "4", "--out-dru", str(pcb.with_suffix(".kicad_dru")),
        "--pro", str(pcb.with_suffix(".kicad_pro")), "--out", str(tmp_path / "r.json")])
    assert rc == 0
    pro = json.loads(pcb.with_suffix(".kicad_pro").read_text("utf-8"))
    assert {c["name"] for c in pro["net_settings"]["classes"]} >= {"Default", "Power", "Diff90"}
    rep = _drc(cli, pcb, parity=True)
    assert rep["counts"]["total"] == 0, rep["violations"]
