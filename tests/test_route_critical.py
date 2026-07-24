"""S11 acceptance tests: critical-net routing via KRT (route_critical).

Pure tests (constraint parsing, S5 pair-discovery reuse, IPC width numbers,
plan ordering, JSON_SUMMARY parsing, grading floors, stub-pad detach/restore,
missing-tool errors) run with no toolchain and are unmarked. The `smoke` test
builds the placed-unrouted usbbuck4 corpus board (board_init -> place_seed,
the test_place_anneal pattern) and drives KRT + kicad-cli live:
/USB_DP + /USB_DM routed as a coupled pair passing check_diffpair, +3V3/VBUS
at IPC-2152 width, no new DRC errors.

Determinism note: KRT stamps fresh uuid4s, so assertions compare routed nets
and DRC outcomes, never board bytes.
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / ".claude" / "skills" / "ai-ee" / "scripts"
GOLDEN = REPO / "tests" / "golden"

sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(SCRIPTS / "lib"))
import check_diffpair  # noqa: E402
import env  # noqa: E402
import geom  # noqa: E402
import route_critical as rc  # noqa: E402
from checklib import CheckError  # noqa: E402


# ---- synthetic board helpers (test_place_anneal pattern) --------------------

def _fp(ref: str, x: float, y: float, pads: str = "") -> str:
    return (f'  (footprint "t:{ref}" (layer "F.Cu")\n'
            f'    (at {x} {y})\n'
            f'    (property "Reference" "{ref}" (at 0 0 0))\n'
            f'{pads}  )\n')


def _pad(num: str, x: float, y: float, net: str | None = None,
         size: float = 0.6) -> str:
    n = f'\n      (net "{net}")' if net else ""
    return (f'    (pad "{num}" smd rect\n      (at {x} {y})\n'
            f'      (size {size} {size})\n      (layers "F.Cu"){n}\n'
            f'      (uuid "uu-{num}-{net or "x"}")\n    )\n')


def _pcb(tmp_path, name: str, body: str, w: float = 60.0, h: float = 40.0) -> Path:
    text = f"""(kicad_pcb
  (version 20260206) (generator "test")
  (general (thickness 1.6))
  (layers (0 "F.Cu" signal) (2 "B.Cu" signal) (25 "Edge.Cuts" user))
  (setup)
  (gr_rect (start 0 0) (end {w} {h}) (stroke (width 0.1)) (fill no)
    (layer "Edge.Cuts"))
{body})
"""
    p = tmp_path / f"{name}.kicad_pcb"
    p.write_text(text, encoding="utf-8")
    return p


def _pair_board(tmp_path) -> Path:
    """U1 P/N pads adjacent, J2 P/N pads adjacent, R9 pull-up stub on P."""
    body = _fp("U1", 40, 20,
               pads=_pad("1", 0, 0, "/USB_DP") + _pad("2", 0, 0.5, "/USB_DM"))
    body += _fp("J2", 10, 20,
                pads=_pad("1", 0, 0, "/USB_DP") + _pad("2", 0, 0.65, "/USB_DM"))
    body += _fp("R9", 45, 30,
                pads=_pad("1", -0.5, 0, "/USB_DP") + _pad("2", 0.5, 0, "+3V3"))
    return _pcb(tmp_path, "pairboard", body)


# ============================================================ pure: widths

def test_power_width_numbers():
    # IPC-2152 minimum (check_current.required_width_mm) * 1.5, floor 0.3
    assert rc.power_width_mm(0.4) == 0.3          # 0.2 * 1.5 = 0.3
    assert rc.power_width_mm(0.5) == 0.375        # 0.25 * 1.5
    assert rc.power_width_mm(2.0) == 1.65         # 1.10 * 1.5
    assert rc.power_width_mm(3.0) == 2.7          # 1.80 * 1.5
    assert rc.power_width_mm(0.05) == 0.3         # clamped to the floor
    # hotter allowance -> narrower requirement, still floored
    assert rc.power_width_mm(0.4, dt_c=20.0) == 0.3
    # thicker copper -> narrower
    assert rc.power_width_mm(2.0, cu_mm=0.070) == pytest.approx(0.825)


def test_power_specs_from_constraints():
    cons = {"power": [{"net": "+3V3", "current_a": 0.4},
                      {"net": "VBUS", "current_a": 0.5, "dt_c": 10},
                      {"net": None, "current_a": 1.0},       # ignored
                      {"net": "/X"}]}                        # no current: ignored
    specs = rc.power_specs(cons)
    assert [(s["net"], s["width_mm"]) for s in specs] == \
        [("+3V3", 0.3), ("VBUS", 0.375)]


# ============================================================ pure: pairing

def test_diff_specs_discovery_reuses_s5_checker():
    cons = {"high_speed": [{"net": "/MCO", "reference": "GND"},
                           {"net": "/USB_DP"}, {"net": "/USB_DM"}]}
    specs = rc.diff_specs(cons, [])
    assert specs == [{"p": "/USB_DP", "n": "/USB_DM", "impedance_ohm": 90}]
    # byte-for-byte the S5 checker's pairing on the same names
    hs = [e["net"] for e in cons["high_speed"]]
    assert [(s["p"], s["n"]) for s in specs] == check_diffpair.discover_pairs(hs)


def test_diff_specs_non_usb_defaults_100_ohm():
    cons = {"high_speed": [{"net": "/LVDS_P"}, {"net": "/LVDS_N"}]}
    specs = rc.diff_specs(cons, [])
    assert specs == [{"p": "/LVDS_P", "n": "/LVDS_N", "impedance_ohm": 100}]


def test_diff_specs_explicit_wins_over_discovery():
    cons = {"diff_pairs": [{"p": "/USB_DP", "n": "/USB_DM", "gap_mm": 0.4,
                            "impedance_ohm": 85}],
            "high_speed": [{"net": "/USB_DP"}, {"net": "/USB_DM"}]}
    specs = rc.diff_specs(cons, [])
    assert len(specs) == 1
    assert specs[0]["impedance_ohm"] == 85 and specs[0]["gap_mm"] == 0.4


def test_rf_specs_excludes_pair_halves():
    cons = {"rf": [{"net": "/ANT", "impedance_ohm": 50}],
            "high_speed": [{"net": "/CLK", "impedance_ohm": 50},
                           {"net": "/USB_DP", "impedance_ohm": 90}]}
    specs = rc.rf_specs(cons, {"/USB_DP", "/USB_DM"})
    assert [(s["net"], s["impedance_ohm"]) for s in specs] == \
        [("/ANT", 50), ("/CLK", 50)]


# ============================================================ pure: plan

def test_plan_order_default_only_and_override():
    assert rc.plan_order(None, None) == ["diff", "rf", "power"]
    assert rc.plan_order("power", None) == ["power"]
    assert rc.plan_order(None, {"order": ["power", "diff"]}) == ["power", "diff"]
    assert rc.plan_order("diff", {"order": ["power", "diff"]}) == ["diff"]
    with pytest.raises(CheckError):
        rc.plan_order(None, {"order": ["bogus"]})
    with pytest.raises(CheckError):
        rc.plan_order(None, {"order": []})


# ============================================================ pure: summary

def test_parse_summary_takes_last_line():
    out = ('noise\nJSON_SUMMARY: {"successful": 1}\nmore\n'
           'JSON_SUMMARY: {"successful": 2, "failed_single": []}\n')
    assert rc.parse_summary(out) == {"successful": 2, "failed_single": []}


def test_parse_summary_absent_or_bad():
    assert rc.parse_summary("no summary here\n") is None
    assert rc.parse_summary("JSON_SUMMARY: not-json\n") is None


def test_pair_outcome_and_net_failed():
    summary = {"routed_diff_pairs": ["/USB_D"],
               "pair_reports": [{"pair": "/USB_D", "p_net": "/USB_DP",
                                 "n_net": "/USB_DM", "outcome": "coupled"}]}
    assert rc._pair_outcome(summary, "/USB_DP", "/USB_DM") == (True, "coupled")
    deferred = {"routed_diff_pairs": [],
                "pair_reports": [{"pair": "/USB_D", "p_net": "/USB_DP",
                                  "n_net": "/USB_DM", "outcome": "deferred",
                                  "failure_reason": "no-escape-path"}]}
    ok, reason = rc._pair_outcome(deferred, "/USB_DP", "/USB_DM")
    assert not ok and reason == "no-escape-path"
    assert rc._pair_outcome({}, "/A_P", "/A_N") == (False, "pair-not-detected")

    assert rc._net_failed({"failed_single": ["VBUS"]}, "VBUS")
    assert rc._net_failed(
        {"failed_multipoint": [{"net_name": "+3V3", "failed_pads": [{}]}]},
        "+3V3") == "multipoint: 1 pad(s) unconnected"
    assert rc._net_failed({"failed_single": [], "failed_multipoint": []},
                          "+3V3") is None


# ============================================================ pure: floors

def test_grading_floors_defaults_and_pro(tmp_path):
    assert rc.grading_floors(None) == rc.KICAD_DEFAULTS
    pro = tmp_path / "b.kicad_pro"
    pro.write_text(json.dumps({
        "board": {"design_settings": {"rules": {
            "min_track_width": 0.1, "min_copper_to_edge": 0.3,
            "min_via_diameter": 0.45, "min_through_hole_diameter": 0.2}}},
        "net_settings": {"classes": [
            {"name": "Default", "clearance": 0.127},
            {"name": "Power", "clearance": 0.2}]},
    }), encoding="utf-8")
    floors = rc.grading_floors(pro)
    assert floors == {"clearance": 0.2, "track_width": 0.1,
                      "via_diameter": 0.45, "via_drill": 0.2,
                      "edge_clearance": 0.3}
    # a project without those keys keeps every stock default
    pro2 = tmp_path / "c.kicad_pro"
    pro2.write_text(json.dumps({"board": {"design_settings": {"rules": {
        "min_track_width": 0.1}}}}), encoding="utf-8")
    f2 = rc.grading_floors(pro2)
    assert f2["track_width"] == 0.1 and f2["clearance"] == 0.2
    assert f2["via_diameter"] == 0.5 and f2["edge_clearance"] == 0.5


# ============================================================ pure: geometry

class _FakeStackup:
    dielectrics = [object()]
    copper_thickness = {"F.Cu": 0.035}

    def adjacent(self, layer):
        return None, "In1.Cu"

    def height_between(self, a, b):
        return 0.2104

    def epsilon_between(self, a, b):
        return 4.05


class _FakeBG:
    copper_layers = ["F.Cu", "In1.Cu", "In2.Cu", "B.Cu"]
    stackup = _FakeStackup()


def test_pair_geometry_matches_rules_gen_math():
    # same numbers as rules_gen/impedance on the S8 4-layer JLC stackup
    w, g = rc.pair_geometry(_FakeBG(), 90)
    assert (w, g) == (0.314, 0.2104)
    assert rc.rf_width(_FakeBG(), 50) == pytest.approx(0.3669, abs=1e-4)


def test_pair_geometry_fallback_without_stackup():
    class Bare:
        copper_layers = ["F.Cu"]

        class stackup:
            dielectrics = []
            copper_thickness = {}

            @staticmethod
            def adjacent(layer):
                return None, None
    assert rc.pair_geometry(Bare(), 90) == (rc.FALLBACK_PAIR_WIDTH, 0.2)
    assert rc.rf_width(Bare(), 50) == rc.BASE_TRACK_WIDTH


def test_pair_geometry_pinned_pitch():
    # constraints gap_mm is CENTER-to-center; width + edge gap ~= pitch
    w, g = rc.pair_geometry(_FakeBG(), 90, gap_c2c_mm=0.5)
    assert w + g == pytest.approx(0.5, abs=0.02)


# ============================================================ pure: stub pads

def test_unmatched_stub_pads_finds_pullup(tmp_path):
    bg = geom.BoardGeom.from_file(_pair_board(tmp_path))
    assert rc.unmatched_stub_pads(bg, "/USB_DP", "/USB_DM") == \
        [("R9", "/USB_DP")]


def test_detach_restore_roundtrip(tmp_path):
    original = _pair_board(tmp_path).read_text(encoding="utf-8")
    detached, restores = rc.detach_stub_pads(original, [("R9", "/USB_DP")])
    assert detached != original
    s, e = rc._footprint_block(detached, "R9")
    assert '(net "/USB_DP")' not in detached[s:e]
    assert '(net "+3V3")' in detached[s:e]          # partner pad untouched
    assert rc.restore_stub_pads(detached, restores) == original


def test_detach_handles_numbered_net_nodes(tmp_path):
    text = _pair_board(tmp_path).read_text(encoding="utf-8") \
        .replace('(net "/USB_DP")', '(net 14 "/USB_DP")')
    detached, restores = rc.detach_stub_pads(text, [("R9", "/USB_DP")])
    s, e = rc._footprint_block(detached, "R9")
    assert '"/USB_DP"' not in detached[s:e]
    assert rc.restore_stub_pads(detached, restores) == text


def test_detach_missing_pad_or_ref_raises(tmp_path):
    text = _pair_board(tmp_path).read_text(encoding="utf-8")
    with pytest.raises(CheckError):
        rc.detach_stub_pads(text, [("R9", "/NOPE")])
    with pytest.raises(CheckError):
        rc.detach_stub_pads(text, [("R99", "/USB_DP")])
    with pytest.raises(CheckError):
        rc.restore_stub_pads("unrelated text", [("gone", "orig")])


# ============================================================ pure: CLI/tools

def test_missing_krt_is_a_check_error(monkeypatch):
    monkeypatch.setattr(rc.env, "find_kicad_cli", lambda: Path("kicad-cli"))
    monkeypatch.setattr(rc.env, "find_krt", lambda: None)
    with pytest.raises(CheckError, match="KiCadRoutingTools"):
        rc._tools()


def test_cli_missing_board_exits_2():
    assert rc.main(["--pcb", "no/such/board.kicad_pcb"]) == 2


def test_no_critical_items_is_a_pass(tmp_path):
    # a board with no constraints sidecar has nothing critical: exit 0,
    # board untouched, and no toolchain is required to say so
    pcb = _pair_board(tmp_path)
    raw = pcb.read_bytes()
    rep = tmp_path / "r.json"
    assert rc.main(["--pcb", str(pcb), "--out-report", str(rep)]) == 0
    r = json.loads(rep.read_text(encoding="utf-8"))
    assert r["status"] == "pass"
    assert r["facts"]["routed"] == [] and r["facts"]["board_updated"] is False
    assert pcb.read_bytes() == raw


def test_only_filter_skips_other_kinds(tmp_path):
    # --only power on a diff-only constraints file -> nothing to do, skipped
    # reported; no KRT needed
    pcb = _pair_board(tmp_path)
    (tmp_path / "constraints.json").write_text(json.dumps(
        {"high_speed": [{"net": "/USB_DP"}, {"net": "/USB_DM"}]}),
        encoding="utf-8")
    rep = tmp_path / "r.json"
    assert rc.main(["--pcb", str(pcb), "--only", "power",
                    "--out-report", str(rep)]) == 0
    r = json.loads(rep.read_text(encoding="utf-8"))
    assert r["facts"]["skipped"] == [
        {"kind": "diff", "count": 1, "why": "not in --only/plan"}]


# ============================================================ smoke: corpus

@pytest.fixture(scope="session")
def cli() -> Path:
    c = env.find_kicad_cli()
    if c is None:
        pytest.skip("kicad-cli not installed")
    return c


@pytest.fixture(scope="session")
def krt_dir() -> Path:
    k = env.find_krt()
    if k is None:
        pytest.skip("KiCadRoutingTools not vendored (tools/krt)")
    return k


@pytest.fixture(scope="session")
def placed_board(cli, tmp_path_factory) -> Path:
    """usbbuck4 netlist -> board_init (4 layer) -> place_seed --apply: the
    placed-unrouted S11 input (test_place_anneal's seeded_board pattern)."""
    import board_init
    import kc
    import place_seed
    d = tmp_path_factory.mktemp("critical")
    net = d / "usbbuck4.net"
    kc.export_netlist(cli, GOLDEN / "usbbuck4" / "usbbuck4.kicad_sch", net)
    rc_init = board_init.main([
        "--netlist", str(net), "--name", "usbbuck4",
        "--out", str(d / "kicad"), "--layers", "4", "--mounting-holes", "4"])
    assert rc_init == 0
    pcb = d / "kicad" / "usbbuck4.kicad_pcb"
    for name in ("constraints.json", "decoupling.json"):
        shutil.copy2(GOLDEN / "usbbuck4" / name, pcb.parent / name)
    payload, _ = place_seed.run([
        "--pcb", str(pcb), "--ops-out", str(d / "seed_ops.json"), "--apply"])
    assert payload["status"] == "pass"
    return pcb


@pytest.mark.smoke
def test_critical_routing_acceptance_usbbuck4(placed_board, krt_dir, tmp_path):
    """Plan S11 acceptance: the USB pair routes as a COUPLED pair passing the
    S5 check, power nets route at IPC width, and DRC gains no new errors."""
    rep = tmp_path / "report.json"
    assert rc.main(["--pcb", str(placed_board),
                    "--out-report", str(rep)]) == 0
    r = json.loads(rep.read_text(encoding="utf-8"))
    assert r["status"] == "pass"
    facts = r["facts"]

    kinds = {(f["kind"], tuple(f["nets"])) for f in facts["routed"]}
    assert ("diff", ("/USB_DP", "/USB_DM")) in kinds
    assert ("power", ("+3V3",)) in kinds and ("power", ("VBUS",)) in kinds

    # DRC gained nothing; unconnected only dropped
    assert facts["drc_delta"]["new"] == {}
    assert facts["drc_delta"]["after"].get("unconnected_items", 0) < \
        facts["drc_delta"]["before"].get("unconnected_items", 0)

    # S5 diff-pair check passed on the routed pair (uncoupled <= 5 mm)
    assert facts["diffpair_check"] == "pass"
    dp = facts["diffpair_facts"][0]
    assert max(dp["uncoupled_p_mm"], dp["uncoupled_n_mm"]) <= 5.0
    assert dp["skew_mm"] <= 5.0

    # board really carries the copper, on the preferred outer layer
    bg = geom.BoardGeom.from_file(placed_board)
    for net in ("/USB_DP", "/USB_DM"):
        tks = bg.tracks_of(net=net)
        assert tks, f"{net} has no copper"
        assert {t.layer for t in tks} == {"F.Cu"}
    for f in facts["routed"]:
        if f["kind"] != "power":
            continue
        net, want = f["nets"][0], f["width_mm"]
        tks = bg.tracks_of(net=net)
        assert tks, f"{net} has no copper"
        # trunk at IPC width (taps may legitimately neck down at fine pads)
        assert max(t.width for t in tks) == pytest.approx(want, abs=1e-3)

    # the pull-up stub pad the KRT workaround detached is back on its net
    assert [list(s) for s in
            [tuple(x) for f in facts["routed"] if f["kind"] == "diff"
             for x in f["stub_pads_detached"]]] == [["R3", "/USB_DP"]]
    assert len(bg.pads_of(net="/USB_DP")) == 3
