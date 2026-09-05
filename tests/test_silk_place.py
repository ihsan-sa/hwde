"""T6 p1: silk_place - the refdes silk solver (LEARNINGS recipe promoted to L3).

Pure tests exercise the solver's own geometric model on synthetic boards
(candidate generation, collision scoring, crowded-first, skips, residuals,
determinism, ops schema). The smoke test applies the ops to a copy of the
blinky2 golden and holds the REAL DRC to zero silk findings - check_silk is
lenient and never the oracle (LEARNINGS 2026-07-27).
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / ".claude" / "skills" / "hwde" / "scripts"
GOLDEN = REPO / "tests" / "golden"
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(SCRIPTS / "lib"))
import env  # noqa: E402
import placelib  # noqa: E402
import place_edit  # noqa: E402
import silk_place  # noqa: E402
from checklib import CheckError  # noqa: E402


# ---- synthetic boards ------------------------------------------------------

def _fp(ref, x, y, pads="", cy=(-0.8, -0.5, 0.8, 0.5), refat="(at 0 -4 0)",
        attr="smd", hide=""):
    court = (f'    (fp_rect (start {cy[0]} {cy[1]}) (end {cy[2]} {cy[3]})'
             f' (stroke (width 0.05)) (fill no) (layer "F.CrtYd"))\n')
    return (f'  (footprint "t:{ref}" (layer "F.Cu")\n    (at {x} {y})\n'
            f'    (property "Reference" "{ref}" {refat} (layer "F.SilkS") '
            f'{hide}(effects (font (size 1 1) (thickness 0.15))))\n'
            f'    (attr {attr})\n{court}{pads})\n')


def _pad(num, x, y, net, w=0.9, h=0.95):
    return (f'    (pad "{num}" smd rect (at {x} {y}) (size {w} {h})'
            f' (layers "F.Cu") (net "{net}"))\n')


def _board(tmp_path_factory, name, body, w=30.0, h=20.0):
    text = f"""(kicad_pcb
  (version 20260206) (generator "test")
  (general (thickness 1.6))
  (layers (0 "F.Cu" signal) (2 "B.Cu" signal) (25 "Edge.Cuts" user))
  (setup)
  (gr_rect (start 0 0) (end {w} {h}) (stroke (width 0.1)) (fill no)
    (layer "Edge.Cuts"))
{body})
"""
    p = tmp_path_factory.mktemp(name) / f"{name}.kicad_pcb"
    p.write_text(text, encoding="utf-8")
    return p


def _crowded(tmp_path_factory, name="crowd"):
    """Three parts with library-style (0, -4) refdes offsets, packed so the
    naive offsets land labels on neighbours."""
    body = _fp("C1", 10, 10, _pad("1", -0.77, 0, "A") + _pad("2", 0.77, 0, "G"))
    body += _fp("C2", 10, 12.4, _pad("1", -0.77, 0, "B") + _pad("2", 0.77, 0, "G"))
    body += _fp("R1", 13, 10, _pad("1", -0.77, 0, "A") + _pad("2", 0.77, 0, "B"))
    body += _fp("H1", 3, 3, attr="board_only", refat="(at 0 -2 0)")
    body += _fp("D9", 25, 10, _pad("1", 0, 0, "A"), hide="(hide yes) ")
    return _board(tmp_path_factory, name, body)


# ============================================================ pure: solver

def test_solver_pulls_labels_in_and_clears_collisions(tmp_path_factory):
    pcb = _crowded(tmp_path_factory, "pull")
    payload, _ = silk_place.run(["--pcb", str(pcb)])
    assert payload["status"] == "pass"          # no residuals
    assert payload["targets"] == 3 and payload["moved"] == 3
    assert payload["median_beyond_extent_mm"] \
        < payload["median_beyond_extent_mm_before"]
    assert payload["median_beyond_extent_mm"] <= 1.5
    # verify with the solver's own box model: no label-label / label-pad hits
    ops = json.loads(Path(payload["ops_out"]).read_text("utf-8"))["ops"]
    place_edit.validate_ops({"version": 1, "ops": ops})
    model = placelib.PlaceModel(pcb)
    boxes = {o["ref"]: placelib.text_box(o["ref"], 1.0, 0.15,
                                         o["x"], o["y"], o.get("deg", 0.0))
             for o in ops}
    pads = [pp for ref in model.footprints
            for pp in silk_place._pad_polys_abs(model.footprints[ref])]
    refs = sorted(boxes)
    for i, a in enumerate(refs):
        for b in refs[i + 1:]:
            assert not boxes[a].intersects(boxes[b]), (a, b)
        for pp in pads:
            assert not boxes[a].intersects(pp), a


def test_solver_skips_hidden_and_board_only(tmp_path_factory):
    pcb = _crowded(tmp_path_factory, "skips")
    payload, _ = silk_place.run(["--pcb", str(pcb)])
    reasons = {s["ref"]: s["reason"] for s in payload["skipped"]}
    assert reasons["D9"] == "hidden"
    assert reasons["H1"] == "board_only"
    ops = json.loads(Path(payload["ops_out"]).read_text("utf-8"))["ops"]
    assert not any(o["ref"] in ("D9", "H1") for o in ops)


def test_solver_deterministic(tmp_path_factory):
    pcb = _crowded(tmp_path_factory, "det")
    outs = []
    for i in (1, 2):
        out = pcb.parent / f"ops{i}.json"
        silk_place.run(["--pcb", str(pcb), "--ops-out", str(out)])
        outs.append(out.read_text("utf-8"))
    assert outs[0] == outs[1]


def test_residual_reported_not_forced(tmp_path_factory):
    """A part walled in by oversized neighbour pads on all four sides within
    the push range must land in residual (exit 1), never overlap."""
    big = _pad("1", 0, 0, "X", w=6.0, h=6.0)
    body = _fp("C1", 10, 10, _pad("1", -0.77, 0, "A") + _pad("2", 0.77, 0, "G"))
    body += _fp("W1", 10, 5.2, big)
    body += _fp("W2", 10, 14.8, big)
    body += _fp("W3", 5.2, 10, big)
    body += _fp("W4", 14.8, 10, big)
    pcb = _board(tmp_path_factory, "walled", body)
    payload, _ = silk_place.run(["--pcb", str(pcb), "--refs", "C1"])
    assert payload["status"] == "violations"
    assert [r["ref"] for r in payload["residual"]] == ["C1"]
    kinds = {v["kind"] for v in payload["violations"]}
    assert kinds == {"silk_residual"}


def test_min_silk_clearance_read_from_pro(tmp_path_factory):
    pcb = _crowded(tmp_path_factory, "pro")
    assert silk_place.read_min_silk_clearance(pcb) == 0.0   # no sibling
    pcb.with_suffix(".kicad_pro").write_text(json.dumps(
        {"board": {"design_settings": {"rules": {"min_silk_clearance": 0.3}}}}),
        encoding="utf-8")
    assert silk_place.read_min_silk_clearance(pcb) == 0.3
    # the live value binds: candidates must clear obstacles by > 0.3
    payload, _ = silk_place.run(["--pcb", str(pcb)])
    for r in payload["results"]:
        assert r["clearance_mm"] > 0.3


def test_verify_drc_requires_apply(tmp_path_factory):
    pcb = _crowded(tmp_path_factory, "vguard")
    with pytest.raises(CheckError, match="--apply"):
        silk_place.run(["--pcb", str(pcb), "--verify-drc"])


def test_text_box_metrics():
    """Measured constants (LEARNINGS 2026-07-30): 3-char refdes at size 1.0 /
    t 0.15 inks ~2.64-2.69 x 1.16 mm; 90-deg text swaps the box axes."""
    b = placelib.text_box("R34", 1.0, 0.15, 0.0, 0.0, 0.0)
    x0, y0, x1, y1 = b.bounds
    assert 2.5 <= x1 - x0 <= 2.8
    assert y1 - y0 == pytest.approx(1.15)
    b90 = placelib.text_box("R34", 1.0, 0.15, 0.0, 0.0, 90.0)
    x0, y0, x1, y1 = b90.bounds
    assert y1 - y0 == pytest.approx(2.685, abs=0.2)
    assert x1 - x0 == pytest.approx(1.15, abs=1e-6)


# ============================================================ smoke: real DRC

@pytest.fixture(scope="session")
def cli():
    c = env.find_kicad_cli()
    if c is None:
        pytest.skip("kicad-cli not installed")
    return c


@pytest.mark.smoke
def test_blinky2_golden_apply_stays_drc_silk_clean(cli, tmp_path):
    """Acceptance (p1 verify plan): run the solver on a copy of the blinky2
    golden, apply, and hold the REAL DRC to zero silk findings."""
    import kc
    d = tmp_path / "b2"
    d.mkdir()
    for ext in (".kicad_pcb", ".kicad_pro", ".kicad_prl"):
        src = GOLDEN / "blinky2" / f"blinky2{ext}"
        if src.is_file():
            shutil.copy2(src, d / src.name)
    pcb = d / "blinky2.kicad_pcb"
    payload, _ = silk_place.run(["--pcb", str(pcb), "--apply", "--verify-drc"])
    assert payload["drc_silk_total"] == 0, payload["violations"]
    assert payload["residual"] == []
    assert payload["median_beyond_extent_mm"] is None \
        or payload["median_beyond_extent_mm"] <= 1.5
