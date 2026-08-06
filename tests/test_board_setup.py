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
import fabfloors  # noqa: E402
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
        # the declared lamination total is exactly what the stack sums to,
        # and the ORDERED (nominal) thickness is within 5% of it - JLC's
        # real 1.6 mm laminations sum to 1.58-1.66 mm.
        total = sum(ly["thickness_mm"] for ly in s["stack"])
        assert abs(total - s["stack_total_mm"]) < 1e-6, f"{name}: sums to {total}"
        assert abs(total - s["thickness_mm"]) / s["thickness_mm"] < 0.05, \
            f"{name}: nominal {s['thickness_mm']} vs lamination {total}"
        for ci in s.get("controlled_impedance", []):
            assert ci["width_mm"] > 0
            if ci["kind"] == "diff":
                assert ci["gap_mm"] > 0
    # the 4-layer default has real copper layer names geom will match
    names = [ly["name"] for ly in st["stackups"][st["defaults"][4]]["stack"]
             if ly["type"] == "copper"]
    assert names == ["F.Cu", "In1.Cu", "In2.Cu", "B.Cu"]


def test_stackups_carry_verification_provenance():
    """T1: every entry says where its numbers came from, and no default
    points at a stackup JLC does not sell (the JLC04161H-3313 phantom sized
    a real 100R board; LEARNINGS 2026-07-30 [stackup][ordering])."""
    st = yaml.safe_load((REFERENCE / "stackups.yaml").read_text("utf-8"))
    for name, s in st["stackups"].items():
        assert "available" in s, f"{name}: no availability flag"
        prov = s.get("provenance")
        assert isinstance(prov, dict), f"{name}: no provenance block"
        assert prov.get("method") in {"jlc_open_api", "vendor_page", "none"}, \
            f"{name}: unknown provenance method {prov.get('method')!r}"
        assert prov.get("verified"), f"{name}: provenance has no date"
        if prov["method"] == "jlc_open_api":
            assert prov.get("template_code"), f"{name}: no JLC template code"
            assert prov.get("endpoint"), f"{name}: no endpoint recorded"
        if s["available"] is False:
            ret = s.get("retired") or {}
            assert ret.get("reason"), f"{name}: retired without a reason"
            assert ret.get("replacements"), f"{name}: retired with no successor"
    for layers, name in st["defaults"].items():
        assert st["stackups"][name]["available"] is True, \
            f"defaults[{layers}] = {name} is not available"
        assert st["stackups"][name]["layers"] == layers


def test_controlled_impedance_matches_stack():
    """The published width/gap are impedance.py's output for the stack's own
    outer dielectric - regenerate this table whenever the stack changes."""
    st = yaml.safe_load((REFERENCE / "stackups.yaml").read_text("utf-8"))
    for name, s in st["stackups"].items():
        rows = s.get("controlled_impedance") or []
        if not rows:
            continue
        h, er, oz = rules_gen.outer_microstrip_params(s)
        t = imp.CU_OZ_MM.get(oz, 0.035)
        for ci in rows:
            if ci["kind"] == "single":
                w = imp.solve_width(ci["impedance_ohm"], h, t, er)
                assert abs(w - ci["width_mm"]) < 5e-4, f"{name}/{ci['profile']}"
            else:
                w, g = imp.diff_pair(float(ci["impedance_ohm"]), h, t, er)
                assert abs(w - ci["width_mm"]) < 5e-4, f"{name}/{ci['profile']} width"
                assert abs(g - ci["gap_mm"]) < 5e-4, f"{name}/{ci['profile']} gap"


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


def _stackup(name="JLC04161H-1080B"):
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
    assert "Diff90" in cnames
    pats = {(p["netclass"], p["pattern"]) for p in report["patterns"]}
    assert ("Diff90", "/USB_DP") in pats
    # +3V3 (0.4 A -> 0.20 mm) needs nothing wider than the Default class;
    # VBUS (0.5 A -> 0.25 mm) gets its own class, at ITS width.
    assert ("Default", "+3V3") in pats
    assert ("Pwr_0p25mm", "VBUS") in pats
    assert {c["name"]: c["track_width"] for c in report["classes"]
            if c["name"].startswith("Pwr_")} == {"Pwr_0p25mm": 0.25}


def test_power_netclasses_split_by_current():
    """A 20 mA rail must NOT inherit a 5 A trunk's width: one class per
    required width, thin rails on Default. Flattening them into one wide
    "Power" class is what fed Freerouting 1.75 mm traces for /VDD
    (LEARNINGS 2026-07-28 [routing][rules_gen][freerouting])."""
    cons = {"power": [{"net": "VBUS", "current_a": 5.0},
                      {"net": "/VDD", "current_a": 0.02},
                      {"net": "/VIND", "current_a": 0.05}]}
    cap = _cap("2layer_2oz")
    _, report = rules_gen.build(cons, cap, _stackup("JLC2313_1.6_2oz"),
                                baseline_only=False)
    by_net = {f["net"]: f for f in report["power"]}
    assert by_net["VBUS"]["class_width_mm"] > 1.0          # the 5 A trunk
    assert by_net["/VDD"]["netclass"] == "Default"
    assert by_net["/VIND"]["netclass"] == "Default"
    assert by_net["VBUS"]["netclass"] != by_net["/VDD"]["netclass"]
    widths = {c["name"]: c["track_width"] for c in report["classes"]}
    assert len(widths) == 1 and by_net["VBUS"]["netclass"] in widths
    # and the DRU still holds every net to its OWN minimum
    rules, _ = rules_gen.build(cons, cap, _stackup("JLC2313_1.6_2oz"), False)
    dru = {r.name: r.minv for r in rules}
    assert dru["aiee_pwr_width_VBUS"] > dru["aiee_pwr_width_VDD"]


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


def test_parse_netlist_custom_fields(tmp_path):
    """Custom symbol fields (LCSC...) are extracted; native ones excluded.

    S14 finding: symbols carrying an LCSC field made board_init's parity
    self-check fail (footprint_symbol_field_mismatch x N) because the fields
    never reached the footprints. parse_netlist must surface them.
    """
    with_fields = MINI_NET.replace(
        '(comp (ref "R1") (value "10k") '
        '(footprint "Resistor_SMD:R_0603_1608Metric"))',
        '(comp (ref "R1") (value "10k") '
        '(footprint "Resistor_SMD:R_0603_1608Metric")\n'
        '      (fields (field (name "LCSC") "C25804")\n'
        '              (field (name "Footprint") "Resistor_SMD:R_0603")\n'
        '              (field (name "Datasheet") "url")))')
    n = tmp_path / "f.net"
    n.write_text(with_fields, encoding="utf-8")
    comps, _ = board_init.parse_netlist(n)
    by_ref = {c["ref"]: c for c in comps}
    assert by_ref["R1"]["fields"] == {"LCSC": "C25804"}  # natives excluded
    assert by_ref["C1"]["fields"] == {}


def test_transient_silk_partition():
    """S14: cross-footprint silk at shelf positions is transient (placement
    re-positions); single-footprint silk (own silk over own pad) is a library
    defect and must still fail init."""
    cross = {"check": "silk_overlap", "refs": ["D2", "U1"]}
    cross2 = {"check": "silk_over_copper", "refs": ["C11", "C5"]}
    own = {"check": "silk_over_copper", "refs": ["D2"]}
    other = {"check": "courtyards_overlap", "refs": ["A", "B"]}
    edge = {"check": "silk_edge_clearance", "refs": ["SW1"]}
    suffixed = {"check": "silk_over_copper", "refs": ["R9", "R2B"]}
    assert board_init._is_transient_silk(cross)
    assert board_init._is_transient_silk(cross2)
    assert not board_init._is_transient_silk(own)
    assert not board_init._is_transient_silk(other)
    assert board_init._is_transient_silk(edge)      # edge = positional
    assert board_init._is_transient_silk(suffixed)  # R2B extracted (kc fix)


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


# ==================================================== T1: fab floors (one source)

def test_fabfloors_profile_and_rules():
    cls, cap = fabfloors.profile(4, 1.0)
    assert cls == "4layer_1oz"
    rules = fabfloors.pro_rules(cap)
    assert rules["min_track_width"] == cap["min_trace_width_mm"] == 0.1016
    assert rules["min_hole_to_hole"] == cap["min_hole_to_hole_mm"] == 0.5
    assert set(rules) == set(fabfloors.PRO_RULE_KEYS)
    with pytest.raises(fabfloors.FabFloorError, match="99layer_1oz"):
        fabfloors.profile(99, 1.0)


def test_fabfloors_check_pro_catches_the_shipped_defects():
    """The two defects that shipped on real boards: a floor BELOW the fab
    profile, and a floor at severity warning (LEARNINGS 2026-07-29 /
    2026-07-30 [board_init][rules_gen][dfm][gates])."""
    _, cap = fabfloors.profile(4, 1.0)
    good = board_init.build_pro("b.kicad_pro", cap)
    assert fabfloors.check_pro(good, cap) == []

    sub_fab = json.loads(json.dumps(good))
    sub_fab["board"]["design_settings"]["rules"]["min_track_width"] = 0.1
    msgs = fabfloors.check_pro(sub_fab, cap)
    assert any("min_track_width" in m and "BELOW" in m for m in msgs)

    warn = json.loads(json.dumps(good))
    warn["board"]["design_settings"]["rule_severities"]["hole_to_hole"] = "warning"
    assert any("hole_to_hole" in m for m in fabfloors.check_pro(warn, cap))

    empty = fabfloors.check_pro({}, cap)
    assert len(empty) == len(fabfloors.PRO_RULE_KEYS) + len(fabfloors.FLOOR_SEVERITIES)


@pytest.mark.parametrize("layers,oz", [(2, 1.0), (2, 2.0), (4, 1.0), (4, 2.0)])
def test_board_init_pro_floors_at_error(tmp_path, layers, oz):
    """board_init's project file must never ship a floor below the chosen
    JLC profile, and the checks that enforce them are ERROR, not warning."""
    _, cap = fabfloors.profile(layers, oz)
    pro_path = tmp_path / "b.kicad_pro"
    floors = board_init.write_pro(pro_path, cap)
    pro = json.loads(pro_path.read_text("utf-8"))
    assert fabfloors.check_pro(pro, cap) == []
    assert floors["min_track_width"] == cap["min_trace_width_mm"]
    sev = pro["board"]["design_settings"]["rule_severities"]
    assert sev["hole_to_hole"] == "error" and sev["track_width"] == "error"
    # the library-noise suppressions survive alongside the floors
    assert sev["lib_footprint_issues"] == "ignore"


def test_board_init_write_pro_refuses_sub_fab(tmp_path, monkeypatch):
    """A regression guard on build_pro itself: if it ever emits a floor
    below the profile again, write_pro raises instead of writing."""
    _, cap = fabfloors.profile(4, 1.0)
    # board_init imports the module as lib.fabfloors - patch ITS binding
    monkeypatch.setattr(board_init.fabfloors, "pro_rules",
                        lambda c: {**{k: float(c[v]) for k, v
                                      in fabfloors.PRO_RULE_KEYS.items()},
                                   "min_track_width": 0.1})
    with pytest.raises(RuntimeError, match="sub-fab floors"):
        board_init.write_pro(tmp_path / "b.kicad_pro", cap)
    assert not (tmp_path / "b.kicad_pro").exists()


def test_rules_gen_pro_writes_same_floors_and_severities(tmp_path):
    """rules_gen --pro and board_init must agree by construction: same
    single source, so a re-run of either cannot lower the floors."""
    _, cap = fabfloors.profile(4, 1.0)
    pro_path = tmp_path / "b.kicad_pro"
    board_init.write_pro(pro_path, cap)
    before = json.loads(pro_path.read_text("utf-8"))
    rules_gen.update_pro(pro_path, [], [], cap)
    after = json.loads(pro_path.read_text("utf-8"))
    ds_b = before["board"]["design_settings"]
    ds_a = after["board"]["design_settings"]
    assert ds_a["rules"] == ds_b["rules"]
    assert fabfloors.check_pro(after, cap) == []
    assert ds_a["rule_severities"]["lib_footprint_mismatch"] == "ignore"
    assert after["net_settings"]["classes"][0]["name"] == "Default"


def test_rules_gen_pro_repairs_a_sub_fab_project(tmp_path):
    """The lumina-carrier shape: a project file already carrying KiCad's
    0.25 mm hole floor at warning is REPAIRED, not merged around."""
    _, cap = fabfloors.profile(4, 1.0)
    pro_path = tmp_path / "b.kicad_pro"
    pro_path.write_text(json.dumps({"board": {"design_settings": {
        "rules": {"min_track_width": 0.1, "min_hole_to_hole": 0.25},
        "rule_severities": {"hole_to_hole": "warning"}}}}), encoding="utf-8")
    rules_gen.update_pro(pro_path, [], [], cap)
    pro = json.loads(pro_path.read_text("utf-8"))
    assert pro["board"]["design_settings"]["rules"]["min_hole_to_hole"] == 0.5
    assert fabfloors.check_pro(pro, cap) == []


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


@pytest.mark.smoke
def test_board_init_writes_profile_floors(cli, usbbuck4_net, tmp_path):
    """ACCEPTANCE (T1): the project file board_init ships satisfies the
    chosen JLC profile at ERROR severity - and the board it just built is
    still DRC-clean under those (stricter) floors."""
    rep = tmp_path / "report.json"
    rc = board_init.main([
        "--netlist", str(usbbuck4_net), "--name", "usbbuck4",
        "--out", str(tmp_path / "kicad"), "--layers", "4",
        "--schematic", str(GOLDEN / "usbbuck4" / "usbbuck4.kicad_sch"),
        "--out-report", str(rep)])
    r = json.loads(rep.read_text("utf-8"))
    assert rc == 0 and r["status"] == "pass", r
    assert r["fab_profile"] == "4layer_1oz" and r["copper_oz"] == 1.0
    _, cap = fabfloors.profile(4, 1.0)
    pro = json.loads((tmp_path / "kicad" / "usbbuck4.kicad_pro").read_text("utf-8"))
    assert fabfloors.check_pro(pro, cap) == []
    # the two values that shipped wrong on real boards
    rules = pro["board"]["design_settings"]["rules"]
    assert rules["min_track_width"] == 0.1016 and rules["min_hole_to_hole"] == 0.5
    assert r["self_check"]["setup_violations"] == []


@pytest.mark.smoke
def test_board_init_refuses_unavailable_stackup(cli, usbbuck4_net, tmp_path):
    """A stackup JLC does not sell must fail LOUDLY by name, with its
    replacement - never silently size a board (JLC04161H-3313 phantom)."""
    rep = tmp_path / "report.json"
    rc = board_init.main([
        "--netlist", str(usbbuck4_net), "--name", "usbbuck4",
        "--out", str(tmp_path / "kicad"), "--layers", "4",
        "--stackup", "JLC04161H-3313", "--out-report", str(rep)])
    r = json.loads(rep.read_text("utf-8"))
    assert rc == 2 and r["status"] == "error"
    assert "available: false" in r["error"]
    assert "JLC04161H-1080B" in r["error"]          # names the replacement


def test_rules_gen_refuses_unavailable_stackup(tmp_path, capsys):
    rc = rules_gen.main(["--layers", "4", "--stackup", "JLC04161H-3313",
                         "--out-dru", str(tmp_path / "b.kicad_dru")])
    assert rc == 2
    out = json.loads(capsys.readouterr().out)
    assert out["status"] == "error" and "JLC04161H-1080B" in out["error"]


def _edge_shapes(pcb: Path, kind: str) -> int:
    """Count `kind` primitives that sit on Edge.Cuts."""
    txt = pcb.read_text(encoding="utf-8")
    return sum(1 for m in re.finditer(r"\(%s\b" % kind, txt)
               if "Edge.Cuts" in txt[m.start():m.start() + 400])


@pytest.mark.smoke
def test_board_init_rounded_corners(cli, usbbuck4_net, tmp_path):
    """MECH-01: --corner-radius draws the outline as 4 lines + 4 corner arcs
    (pcbnew has no filleted-rect primitive) and geom must still read one closed
    outline polygon from it. Mounting holes move out of the rounded quadrant."""
    rep = tmp_path / "report.json"
    rc = board_init.main([
        "--netlist", str(usbbuck4_net), "--name", "usbbuck4",
        "--out", str(tmp_path / "kicad"), "--layers", "4", "--margin", "10",
        "--mounting-holes", "4", "--corner-radius", "4",
        "--schematic", str(GOLDEN / "usbbuck4" / "usbbuck4.kicad_sch"),
        "--out-report", str(rep)])
    r = json.loads(rep.read_text("utf-8"))
    assert rc == 0 and r["status"] == "pass", r
    assert r["self_check"]["setup_violations"] == []
    assert r["self_check"]["parity_count"] == 0
    assert r["corner_radius"] == 4.0            # inset 5.0 > 4.0, no clamp

    pcb = tmp_path / "kicad" / "usbbuck4.kicad_pcb"
    assert (_edge_shapes(pcb, "gr_line"), _edge_shapes(pcb, "gr_arc"),
            _edge_shapes(pcb, "gr_rect")) == (4, 4, 0)

    # the arc/line loop must remain a valid closed outline downstream
    sys.path.insert(0, str(SCRIPTS / "lib"))
    import geom
    bg = geom.load_board(pcb)
    assert bg.outline is not None and bg.outline.area > 0


def _init_board(tmp_path, netlist, *extra):
    rep = tmp_path / "report.json"
    rc = board_init.main([
        "--netlist", str(netlist), "--name", "usbbuck4",
        "--out", str(tmp_path / "kicad"), "--layers", "4",
        "--outline", "100x80", "--corner-radius", "3", "--mounting-holes", "4",
        "--schematic", str(GOLDEN / "usbbuck4" / "usbbuck4.kicad_sch"),
        "--out-report", str(rep), *extra])
    return rc, json.loads(rep.read_text("utf-8"))


@pytest.mark.smoke
def test_board_init_edge_notch(cli, usbbuck4_net, tmp_path):
    """MECH: a --cutout touching an outline edge reshapes the perimeter into a
    notch (the LUMINA daughter boards' RJ45 relief). geom must read the notched
    polygon, not the bounding rectangle."""
    import math
    from shapely.geometry import Point
    rc, r = _init_board(tmp_path, usbbuck4_net, "--cutout", "6,0,30,26")
    assert rc == 0 and r["status"] == "pass", r
    assert r["self_check"]["setup_violations"] == []
    assert len(r["cutouts"]) == 1 and r["outline_origin"] is not None

    sys.path.insert(0, str(SCRIPTS / "lib"))
    import geom
    o = geom.load_board(tmp_path / "kicad" / "usbbuck4.kicad_pcb").outline
    # 100x80, less the 30x26 notch, less four r=3 corners
    assert o.area == pytest.approx(8000 - 780 - (4 - math.pi) * 9, abs=0.5)
    ox, oy = o.bounds[0], o.bounds[1]
    assert not o.contains(Point(ox + 21, oy + 10))   # inside the notch
    assert o.contains(Point(ox + 21, oy + 40))       # below the notch


@pytest.mark.smoke
def test_board_init_cutout_over_corner_is_rejected(cli, usbbuck4_net, tmp_path):
    """A notch running into a rounded corner would self-intersect the outline
    and fail polygonize downstream. It must be skipped loudly at the source."""
    import math
    rc, r = _init_board(tmp_path, usbbuck4_net, "--cutout", "0,0,10,10")
    assert rc == 0 and r["status"] == "pass", r
    assert any("corner radius" in n for n in r["worker_notes"]), r["worker_notes"]

    sys.path.insert(0, str(SCRIPTS / "lib"))
    import geom
    o = geom.load_board(tmp_path / "kicad" / "usbbuck4.kicad_pcb").outline
    # untouched rounded rectangle - the cutout was not drawn
    assert o.area == pytest.approx(8000 - (4 - math.pi) * 9, abs=0.5)


@pytest.mark.smoke
def test_board_init_corner_radius_clamped_to_hole_inset(cli, usbbuck4_net,
                                                        tmp_path):
    """A radius past the mounting-hole inset must shrink the RADIUS, not move
    the hole: parts are packed around the holes at that inset, so relocating a
    hole inward lands it in a neighbour's courtyard (H1 vs C1)."""
    rep = tmp_path / "report.json"
    rc = board_init.main([                       # default margin 6 -> inset 3.0
        "--netlist", str(usbbuck4_net), "--name", "usbbuck4",
        "--out", str(tmp_path / "kicad"), "--layers", "4",
        "--mounting-holes", "4", "--corner-radius", "4",
        "--schematic", str(GOLDEN / "usbbuck4" / "usbbuck4.kicad_sch"),
        "--out-report", str(rep)])
    r = json.loads(rep.read_text("utf-8"))
    assert rc == 0 and r["status"] == "pass", r
    assert r["self_check"]["setup_violations"] == []
    assert r["corner_radius"] == 3.0
    assert any("clamped to the mounting-hole inset" in n
               for n in r["worker_notes"])


@pytest.mark.smoke
def test_board_init_square_corners_by_default(cli, usbbuck4_net, tmp_path):
    """Backward compat: without --corner-radius the outline stays one rect."""
    rep = tmp_path / "report.json"
    rc = board_init.main([
        "--netlist", str(usbbuck4_net), "--name", "usbbuck4",
        "--out", str(tmp_path / "kicad"), "--layers", "4",
        "--out-report", str(rep)])
    r = json.loads(rep.read_text("utf-8"))
    assert rc == 0 and r["corner_radius"] == 0.0
    pcb = tmp_path / "kicad" / "usbbuck4.kicad_pcb"
    assert _edge_shapes(pcb, "gr_rect") == 1
    assert _edge_shapes(pcb, "gr_arc") == 0


@pytest.mark.smoke
def test_board_init_lcsc_fields_and_inplace_schematic(cli, usbbuck4_net, tmp_path):
    """S14 regressions: (a) symbols with custom LCSC fields must init to a
    parity-CLEAN board (fields copied onto footprints, hidden); (b) --schematic
    pointing at the file already in the out dir must not SameFileError."""
    # inject an LCSC field into every comp's existing (fields ...) block
    txt = usbbuck4_net.read_text(encoding="utf-8")
    txt = txt.replace("(fields\n",
                      '(fields\n\t\t\t\t(field\n\t\t\t\t\t(name "LCSC") "C999")\n')
    net2 = tmp_path / "with_lcsc.net"
    net2.write_text(txt, encoding="utf-8")

    out_dir = tmp_path / "kicad"
    out_dir.mkdir()
    # schematic already IN the out dir under the board's name (the P4 layout)
    sch_dst = out_dir / "usbbuck4.kicad_sch"
    shutil.copy(GOLDEN / "usbbuck4" / "usbbuck4.kicad_sch", sch_dst)

    rep = tmp_path / "report.json"
    rc = board_init.main([
        "--netlist", str(net2), "--name", "usbbuck4",
        "--out", str(out_dir), "--layers", "4", "--mounting-holes", "0",
        "--schematic", str(sch_dst),          # samefile as the copy target
        "--out-report", str(rep)])
    r = json.loads(rep.read_text("utf-8"))
    assert rc == 0 and r["status"] == "pass", r
    assert r["self_check"]["parity_count"] == 0   # LCSC fields no longer trip it

    board_text = (out_dir / "usbbuck4.kicad_pcb").read_text(encoding="utf-8")
    assert '"LCSC"' in board_text and '"C999"' in board_text
    # fields default visible-on-silk in pcbnew; the worker must hide them
    import re as _re
    for m in _re.finditer(r'\(property "LCSC"[\s\S]{0,400}?\(hide yes\)',
                          board_text):
        break
    else:
        pytest.fail("LCSC footprint fields are not hidden")


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
    names = {c["name"] for c in pro["net_settings"]["classes"]}
    assert names >= {"Default", "Pwr_0p25mm", "Diff90"}
    # ... and the written floors still satisfy the fab profile
    assert fabfloors.check_pro(pro, _cap()) == []
    rep = _drc(cli, pcb, parity=True)
    assert rep["counts"]["total"] == 0, rep["violations"]
