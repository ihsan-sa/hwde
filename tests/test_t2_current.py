"""T2 regression tests for check_current gate blind spots.

Derived from LEARNINGS.md:
 - 2026-07-28 [routing][check_current]: via-count rule is net-wide; overrides
   fed only track widths (a 1 A fuse tap on a 5 A net needed 10 vias).
 - 2026-07-29 [check_current][gates]: plane-fed rail = every via is a 1-via
   leaf cluster (27 unsatisfiable clusters on lumina-carrier +3V3).
 - 2026-07-29 [check_current][gates]: no bridge awareness - undersized_track
   could not say whether a parallel same-net path exists.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / ".claude" / "skills" / "ai-ee" / "scripts"
PYTHON = sys.executable
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(SCRIPTS / "lib"))
import check_current  # noqa: E402
import geom  # noqa: E402


# ---- synthetic boards (helper copied from tests/test_checks.py) ------------

def _board(tmp_path_factory, name: str, body: str) -> geom.BoardGeom:
    text = f"""(kicad_pcb
  (version 20260206) (generator "test")
  (general (thickness 1.6))
  (layers (0 "F.Cu" signal) (2 "B.Cu" signal) (25 "Edge.Cuts" user))
  (setup)
  (gr_rect (start 0 0) (end 20 10) (stroke (width 0.1)) (fill no)
    (layer "Edge.Cuts"))
{body})
"""
    p = tmp_path_factory.mktemp(name) / f"{name}.kicad_pcb"
    p.write_text(text, encoding="utf-8")
    return geom.load_board(p)


def _kinds(vs, kind):
    return [v for v in vs if v["kind"] == kind]


# ---- fixture A: plane-fed rail (LEARNINGS 2026-07-29 shape) ----------------
# Full B.Cu plane on +3V3; three 1-via leaf taps >2 mm apart, each with a
# short 0.3 mm F.Cu escape. At 1.0 A / 0.5 A-per-via every cluster needs 2.

PLANE_FED_BODY = """  (zone (net "+3V3") (layer "B.Cu")
    (polygon (pts (xy 0 0) (xy 20 0) (xy 20 10) (xy 0 10)))
    (filled_polygon (layer "B.Cu")
      (pts (xy 0 0) (xy 20 0) (xy 20 10) (xy 0 10))))
  (via (at 3 5) (size 0.6) (drill 0.3) (layers "F.Cu" "B.Cu") (net "+3V3"))
  (via (at 10 5) (size 0.6) (drill 0.3) (layers "F.Cu" "B.Cu") (net "+3V3"))
  (via (at 17 5) (size 0.6) (drill 0.3) (layers "F.Cu" "B.Cu") (net "+3V3"))
  (segment (start 3 5) (end 3.8 5) (width 0.3) (layer "F.Cu") (net "+3V3"))
  (segment (start 10 5) (end 10.8 5) (width 0.3) (layer "F.Cu") (net "+3V3"))
  (segment (start 17 5) (end 17.8 5) (width 0.3) (layer "F.Cu") (net "+3V3"))
"""

ENTRY_A = {"net": "+3V3", "current_a": 1.0, "via_amps": 0.5}


@pytest.fixture(scope="module")
def plane_fed_bg(tmp_path_factory):
    return _board(tmp_path_factory, "planefed", PLANE_FED_BODY)


def test_plane_fed_absent_keeps_old_errors(plane_fed_bg):
    """Control: without plane_fed the three 1-via taps are hard errors."""
    vs, facts = check_current.check_net(plane_fed_bg, dict(ENTRY_A))
    weak = _kinds(vs, "insufficient_transition_vias")
    assert len(weak) == 3
    assert all(v["severity"] == "error" for v in weak)
    assert all(v["required"] == 2 and v["vias"] == 1 for v in weak)
    assert {tuple(v["pos"]) for v in weak} == {(3.0, 5.0), (10.0, 5.0),
                                               (17.0, 5.0)}
    assert "advisory" not in weak[0]
    assert "plane_fed" not in facts


def test_plane_fed_downgrades_to_advisory(plane_fed_bg):
    vs, facts = check_current.check_net(
        plane_fed_bg, dict(ENTRY_A, plane_fed=True))
    weak = _kinds(vs, "insufficient_transition_vias")
    assert len(weak) == 3
    assert all(v["severity"] == "warning" for v in weak)
    assert all(v["advisory"] is True for v in weak)
    assert {tuple(v["pos"]) for v in weak} == {(3.0, 5.0), (10.0, 5.0),
                                               (17.0, 5.0)}
    # 0.3 mm escapes at the 1.0 A full-budget screen are advisory too
    thin = _kinds(vs, "undersized_track")
    assert thin and all(v["severity"] == "warning" and v["advisory"] is True
                        for v in thin)
    # violations reported, but nothing at error severity
    assert vs and not any(v["severity"] == "error" for v in vs)
    assert facts["plane_fed"] is True
    assert facts["advisory_violations"] == len(vs) == 6


def test_plane_fed_override_region_stays_error(plane_fed_bg):
    """The regulator-feed tap declared via an override stays enforceable."""
    entry = dict(ENTRY_A, plane_fed=True,
                 overrides=[{"near": [3, 5], "radius_mm": 1.0,
                             "current_a": 1.0}])
    vs, _ = check_current.check_net(plane_fed_bg, entry)
    weak = _kinds(vs, "insufficient_transition_vias")
    assert len(weak) == 3
    by_pos = {tuple(v["pos"]): v for v in weak}
    tap1 = by_pos[(3.0, 5.0)]
    assert tap1["severity"] == "error" and tap1["required"] == 2
    assert "advisory" not in tap1
    for pos in [(10.0, 5.0), (17.0, 5.0)]:
        assert by_pos[pos]["severity"] == "warning"
        assert by_pos[pos]["advisory"] is True


def test_plane_fed_clean_rail_passes(tmp_path_factory):
    """A plane-fed rail with adequate copper stays status pass."""
    body = """  (zone (net "+3V3") (layer "B.Cu")
    (polygon (pts (xy 0 0) (xy 20 0) (xy 20 10) (xy 0 10)))
    (filled_polygon (layer "B.Cu")
      (pts (xy 0 0) (xy 20 0) (xy 20 10) (xy 0 10))))
  (via (at 10 5) (size 0.6) (drill 0.3) (layers "F.Cu" "B.Cu") (net "+3V3"))
  (segment (start 10 5) (end 12 5) (width 0.5) (layer "F.Cu") (net "+3V3"))
"""
    bg = _board(tmp_path_factory, "planeok", body)
    entry = {"net": "+3V3", "current_a": 0.4, "via_amps": 0.5,
             "plane_fed": True}
    vs, facts = check_current.check_net(bg, entry)
    assert vs == []
    assert facts["plane_fed"] is True
    assert facts["advisory_violations"] == 0
    cons = bg.path.parent / "c.json"
    cons.write_text(json.dumps({"power": [entry]}), encoding="utf-8")
    payload, out = check_current.run(
        ["--pcb", str(bg.path), "--constraints", str(cons)])
    assert payload["status"] == "pass" and out is None


# ---- fixture B: declared plane-fed without a plane -------------------------

def test_plane_missing_is_error(tmp_path_factory):
    body = ('  (segment (start 1 5) (end 5 5) (width 1) (layer "F.Cu") '
            '(net "+3V3"))\n')
    bg = _board(tmp_path_factory, "noplane", body)
    vs, facts = check_current.check_net(
        bg, {"net": "+3V3", "current_a": 0.5, "plane_fed": True})
    assert [v["kind"] for v in vs] == ["plane_missing"]
    v = vs[0]
    assert v["severity"] == "error" and v["net"] == "+3V3"
    assert v["pos"] is not None and len(v["pos"]) == 2  # net-copper point
    assert facts["plane_fed"] is True
    assert facts["advisory_violations"] == 0


# ---- fixture C: overrides reach via clusters (LEARNINGS 2026-07-28) --------

def test_override_reaches_via_cluster(tmp_path_factory):
    """A 0.4 A branch tap on a 5 A net no longer needs 10 vias."""
    body = (
        '  (via (at 4 5) (size 0.6) (drill 0.3) (layers "F.Cu" "B.Cu") '
        '(net "VBUS"))\n'
        '  (via (at 16 5) (size 0.6) (drill 0.3) (layers "F.Cu" "B.Cu") '
        '(net "VBUS"))\n')
    bg = _board(tmp_path_factory, "viaover", body)
    entry = {"net": "VBUS", "current_a": 5.0, "via_amps": 0.5,
             "overrides": [{"near": [4, 5], "radius_mm": 1.0,
                            "current_a": 0.4}]}
    vs, _ = check_current.check_net(bg, entry)
    weak = _kinds(vs, "insufficient_transition_vias")
    assert len(weak) == 1          # tap cluster passes at 0.4 A (need 1 via)
    assert weak[0]["pos"] == [16.0, 5.0]
    assert weak[0]["severity"] == "error" and weak[0]["required"] == 10
    # control: without the override both clusters demand 10 vias (old rule)
    vs2, _ = check_current.check_net(
        bg, {"net": "VBUS", "current_a": 5.0, "via_amps": 0.5})
    assert len(_kinds(vs2, "insufficient_transition_vias")) == 2


# dumbbell pour (copied from tests/test_checks.py): two 5x5 lobes joined by
# a 0.2 mm strip; the neck fails a 0.5 A budget (req 0.25 mm)
DUMBBELL = """  (zone (net "PWR") (layer "B.Cu")
    (polygon (pts (xy 0 0) (xy 15 0) (xy 15 5) (xy 0 5)))
    (filled_polygon (layer "B.Cu")
      (pts (xy 0 0) (xy 5 0) (xy 5 2.4) (xy 10 2.4) (xy 10 0) (xy 15 0)
           (xy 15 5) (xy 10 5) (xy 10 2.6) (xy 5 2.6) (xy 5 5) (xy 0 5))))
  (via (at 2 2) (size 0.6) (drill 0.3) (layers "F.Cu" "B.Cu") (net "PWR"))
  (via (at 13 2) (size 0.6) (drill 0.3) (layers "F.Cu" "B.Cu") (net "PWR"))
"""


def test_override_drops_pour_neck(tmp_path_factory):
    """A failing neck whose reported pos sits in an override region is
    re-tested at the override requirement and dropped when it passes."""
    bg = _board(tmp_path_factory, "neckover", DUMBBELL)
    base = {"net": "PWR", "current_a": 0.5}
    vs, _ = check_current.check_net(bg, dict(base))
    assert len(_kinds(vs, "pour_neckdown")) == 1     # control
    # region covers the whole pour (neck pos is a split-component sample)
    entry = dict(base, overrides=[{"near": [7.5, 2.5], "radius_mm": 10.0,
                                   "current_a": 0.05}])
    vs2, _ = check_current.check_net(bg, entry)
    assert _kinds(vs2, "pour_neckdown") == []


# ---- fixture D: bridge labeling (LEARNINGS 2026-07-29) ---------------------

_PADS_PWR = """  (footprint "t:U" (at 2 5)
    (layer "F.Cu")
    (property "Reference" "U1" (at 0 0 0))
    (pad "1" smd rect (at 0 0) (size 1 1) (layers "F.Cu") (net "PWR")))
  (footprint "t:U" (at 14 5)
    (layer "F.Cu")
    (property "Reference" "U2" (at 0 0 0))
    (pad "1" smd rect (at 0 0) (size 1 1) (layers "F.Cu") (net "PWR")))
"""

_DIRECT = '  (segment (start 2 5) (end 14 5) (width 0.2) (layer "F.Cu") (net "PWR"))\n'
_DETOUR = (
    '  (segment (start 2 5) (end 2 8) (width 0.2) (layer "F.Cu") (net "PWR"))\n'
    '  (segment (start 2 8) (end 14 8) (width 0.2) (layer "F.Cu") (net "PWR"))\n'
    '  (segment (start 14 8) (end 14 5) (width 0.2) (layer "F.Cu") (net "PWR"))\n')


def test_parallel_paths_labeled_not_bridge(tmp_path_factory):
    bg = _board(tmp_path_factory, "loop", _PADS_PWR + _DIRECT + _DETOUR)
    vs, facts = check_current.check_net(bg, {"net": "PWR", "current_a": 2.0})
    thin = _kinds(vs, "undersized_track")
    assert len(thin) == 4
    assert all(v["bridge"] is False for v in thin)
    assert all(v["severity"] == "error" for v in thin)  # label, not a waiver
    assert facts["bridge_labeled"] is True


def test_sole_path_labeled_bridge(tmp_path_factory):
    bg = _board(tmp_path_factory, "solepath", _PADS_PWR + _DIRECT)
    vs, facts = check_current.check_net(bg, {"net": "PWR", "current_a": 2.0})
    thin = _kinds(vs, "undersized_track")
    assert len(thin) == 1
    assert thin[0]["bridge"] is True
    assert facts["bridge_labeled"] is True


def test_zone_parallel_path_not_bridge(tmp_path_factory):
    """A segment paralleled by the net's own pour (via through-vias at both
    ends) is not a bridge when the graph includes zone fills."""
    body = _DIRECT + (
        '  (via (at 2 5) (size 0.6) (drill 0.3) (layers "F.Cu" "B.Cu") '
        '(net "PWR"))\n'
        '  (via (at 14 5) (size 0.6) (drill 0.3) (layers "F.Cu" "B.Cu") '
        '(net "PWR"))\n'
        """  (zone (net "PWR") (layer "B.Cu")
    (polygon (pts (xy 0 0) (xy 20 0) (xy 20 10) (xy 0 10)))
    (filled_polygon (layer "B.Cu")
      (pts (xy 0 0) (xy 20 0) (xy 20 10) (xy 0 10))))
""")
    bg = _board(tmp_path_factory, "zonepar", body)
    vs, _ = check_current.check_net(bg, {"net": "PWR", "current_a": 2.0})
    thin = _kinds(vs, "undersized_track")
    assert len(thin) == 1
    assert thin[0]["bridge"] is False


def test_no_undersized_no_bridge_fact(tmp_path_factory):
    """bridge_labeled only appears when labeling actually ran."""
    body = _PADS_PWR + \
        '  (segment (start 2 5) (end 14 5) (width 1.2) (layer "F.Cu") (net "PWR"))\n'
    bg = _board(tmp_path_factory, "wideok", body)
    vs, facts = check_current.check_net(bg, {"net": "PWR", "current_a": 2.0})
    assert _kinds(vs, "undersized_track") == []
    assert "bridge_labeled" not in facts


# ---- T6 (P8B-3): derived return-net coverage -------------------------------
# The pd-trigger 5A GND choke class: no board declares its return net, so
# return-path ampacity was unchecked. A >=3A rail synthesizes ONE plane-fed
# entry for the return net; ALL derived findings are advisory warnings.

_GND_RETURN_BODY = """  (segment (start 1 1) (end 19 1) (width 2.0) (layer "F.Cu") (net "VBUS"))
  (zone (net "GND") (layer "B.Cu")
    (polygon (pts (xy 0 0) (xy 15 0) (xy 15 5) (xy 0 5)))
    (filled_polygon (layer "B.Cu")
      (pts (xy 0 0) (xy 5 0) (xy 5 2.4) (xy 10 2.4) (xy 10 0) (xy 15 0)
           (xy 15 5) (xy 10 5) (xy 10 2.6) (xy 5 2.6) (xy 5 5) (xy 0 5))))
  (via (at 2 2) (size 0.6) (drill 0.3) (layers "F.Cu" "B.Cu") (net "GND"))
  (via (at 13 2) (size 0.6) (drill 0.3) (layers "F.Cu" "B.Cu") (net "GND"))
  (segment (start 2 2) (end 2.8 2) (width 0.3) (layer "F.Cu") (net "GND"))
"""


def _run_cli(bg, power):
    cons = bg.path.parent / "cons.json"
    cons.write_text(json.dumps({"power": power}), encoding="utf-8")
    return check_current.run(["--pcb", str(bg.path),
                              "--constraints", str(cons)])[0]


def test_derived_return_fires_at_5a(tmp_path_factory):
    bg = _board(tmp_path_factory, "gndret", _GND_RETURN_BODY)
    payload = _run_cli(bg, [{"net": "VBUS", "current_a": 5.0}])
    derived = [e for e in payload["checked"] if e.get("derived")]
    assert len(derived) == 1 and derived[0]["net"] == "GND"
    gnd_vs = [v for v in payload["violations"] if v["net"] == "GND"]
    assert gnd_vs, "derived GND coverage produced no findings"
    # the choke class is visible: pour neck between the via attachments
    necks = [v for v in gnd_vs if v["kind"] == "pour_neckdown"]
    assert len(necks) == 1
    # ...and EVERY derived finding is an advisory warning, never an error
    assert all(v["severity"] == "warning" for v in gnd_vs)
    assert all(v["derived"] is True for v in gnd_vs)
    assert necks[0]["advisory"] is True
    assert "derived return-net coverage" in necks[0]["msg"]


def test_derived_return_below_threshold_skipped(tmp_path_factory):
    bg = _board(tmp_path_factory, "gndlow", _GND_RETURN_BODY)
    payload = _run_cli(bg, [{"net": "VBUS", "current_a": 2.0}])
    assert not any(e.get("derived") for e in payload["checked"])
    assert not any(v["net"] == "GND" for v in payload["violations"])


def test_derived_return_skipped_when_declared(tmp_path_factory):
    """An explicitly declared return net is the owner's judgment - no
    synthesis on top of it."""
    bg = _board(tmp_path_factory, "gnddecl", _GND_RETURN_BODY)
    payload = _run_cli(bg, [{"net": "VBUS", "current_a": 5.0},
                            {"net": "GND", "current_a": 5.0,
                             "plane_fed": True}])
    assert not any(e.get("derived") for e in payload["checked"])
    # the declared entry still runs (pour neck at ERROR: declared plane_fed)
    necks = [v for v in payload["violations"] if v["kind"] == "pour_neckdown"]
    assert necks and all(v["severity"] == "error" for v in necks)


def test_derived_return_needs_a_zone(tmp_path_factory):
    """Routed-only return (no zone fill) is not judgeable at plane-fed
    semantics - no synthesis, no noise."""
    body = ('  (segment (start 1 1) (end 19 1) (width 2.0) (layer "F.Cu") '
            '(net "VBUS"))\n'
            '  (segment (start 1 5) (end 19 5) (width 0.3) (layer "F.Cu") '
            '(net "GND"))\n')
    bg = _board(tmp_path_factory, "gndtrk", body)
    payload = _run_cli(bg, [{"net": "VBUS", "current_a": 5.0}])
    assert not any(e.get("derived") for e in payload["checked"])
    assert not any(v["net"] == "GND" for v in payload["violations"])


def test_derived_return_net_field_overrides_default(tmp_path_factory):
    body = _GND_RETURN_BODY.replace('"GND"', '"AGND"')
    bg = _board(tmp_path_factory, "agnd", body)
    payload = _run_cli(bg, [{"net": "VBUS", "current_a": 5.0,
                             "return_net": "AGND"}])
    derived = [e for e in payload["checked"] if e.get("derived")]
    assert len(derived) == 1 and derived[0]["net"] == "AGND"


# ---- T6 (P8A-4): plane_fed_candidate hint (facts only) ---------------------

def test_plane_fed_candidate_hint(plane_fed_bg):
    """The plane-fed shape without the key gets the facts hint; severities
    are untouched (still the old errors - the hint is machine-visible only)."""
    vs, facts = check_current.check_net(plane_fed_bg, dict(ENTRY_A))
    assert facts["plane_fed_candidate"] is True
    assert any(v["severity"] == "error" for v in vs)  # unchanged behavior


def test_no_hint_when_plane_fed_declared(plane_fed_bg):
    _, facts = check_current.check_net(
        plane_fed_bg, dict(ENTRY_A, plane_fed=True))
    assert "plane_fed_candidate" not in facts


def test_no_hint_without_zone(tmp_path_factory):
    body = _PADS_PWR + _DIRECT + (
        '  (via (at 2 5) (size 0.6) (drill 0.3) (layers "F.Cu" "B.Cu") '
        '(net "PWR"))\n')
    bg = _board(tmp_path_factory, "nohint", body)
    _, facts = check_current.check_net(bg, {"net": "PWR", "current_a": 2.0})
    assert "plane_fed_candidate" not in facts


# ---- exit codes / run() CLI contract ---------------------------------------

def test_cli_exit_codes(tmp_path_factory, plane_fed_bg):
    script = SCRIPTS / "check_current.py"
    # violations (advisory-only still exits 1: status is "violations")
    cons = plane_fed_bg.path.parent / "pf.json"
    cons.write_text(json.dumps(
        {"power": [dict(ENTRY_A, plane_fed=True)]}), encoding="utf-8")
    proc = subprocess.run(
        [PYTHON, str(script), "--pcb", str(plane_fed_bg.path),
         "--constraints", str(cons)], capture_output=True, text=True)
    assert proc.returncode == 1
    payload = json.loads(proc.stdout)
    assert payload["status"] == "violations"
    assert payload["counts"]["by_severity"] == {"warning": 6}
    assert payload["checked"][0]["plane_fed"] is True
    # error: net not on board -> exit 2
    cons2 = plane_fed_bg.path.parent / "ghost.json"
    cons2.write_text(json.dumps(
        {"power": [{"net": "/GHOST", "current_a": 1.0}]}), encoding="utf-8")
    proc2 = subprocess.run(
        [PYTHON, str(script), "--pcb", str(plane_fed_bg.path),
         "--constraints", str(cons2)], capture_output=True, text=True)
    assert proc2.returncode == 2
    assert json.loads(proc2.stdout)["status"] == "error"
