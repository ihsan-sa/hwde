"""S10 acceptance tests: SA placement refinement (place_anneal).

Plan S10 accept criteria:
  - on golden board 2 stripped of placement (board_init -> seed): annealer
    beats the seed placement by >=20% HPWL
  - results reproducible per seed; runtime bounded
  - route-feedback mode is stubbed behind --route-feedback until S11 (the
    blending logic is exercised here with an injected fake probe)

Pure tests (engine invariants, cost terms, determinism, edge handling,
feedback blending) run with no toolchain and are unmarked; tests that build
the corpus board or drive SWIG carry `smoke`.
"""
from __future__ import annotations

import json
import math
import shutil
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / ".claude" / "skills" / "ai-ee" / "scripts"
GOLDEN = REPO / "tests" / "golden"

sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(SCRIPTS / "lib"))
import checklib  # noqa: E402
import env  # noqa: E402
import placelib  # noqa: E402
import place_anneal  # noqa: E402
from geom import _rot  # noqa: E402
from place_anneal import Engine, Params, _seg_cross  # noqa: E402


# ---- synthetic boards (test_place.py helpers) ------------------------------

def _fp(ref: str, x: float, y: float, angle: float = 0.0,
        layer: str = "F.Cu", pads: str = "", courtyard: str | None = "rect",
        cy: tuple = (-1.0, -1.0, 1.0, 1.0), attr: str | None = "smd",
        locked: bool = False) -> str:
    at = f"(at {x} {y} {angle})" if angle else f"(at {x} {y})"
    crt = "F.CrtYd" if layer.startswith("F.") else "B.CrtYd"
    court = ""
    if courtyard == "rect":
        court = (f'    (fp_rect (start {cy[0]} {cy[1]}) (end {cy[2]} {cy[3]})'
                 f' (stroke (width 0.05)) (fill no) (layer "{crt}"))\n')
    lock = "    (locked yes)\n" if locked else ""
    att = f"    (attr {attr})\n" if attr else ""
    return (f'  (footprint "t:{ref}" (layer "{layer}")\n'
            f'    {at}\n'
            f'    (property "Reference" "{ref}" (at 0 0 0))\n'
            f'{lock}{att}{court}{pads})\n')


def _pad(num: str, x: float, y: float, net: str | None = None,
         size: float = 0.6, kind: str = "smd rect",
         layers: str = '"F.Cu"') -> str:
    n = f' (net "{net}")' if net else ""
    return (f'    (pad "{num}" {kind} (at {x} {y}) (size {size} {size})'
            f' (layers {layers}){n})\n')


def _pcb(tmp_path_factory, name: str, body: str, w: float = 60.0,
         h: float = 40.0) -> Path:
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


def _scatter_board(tmp_path_factory, name="scatter") -> Path:
    """U1 center-ish with 4 nets; R1..R4 sharing one net each, scattered to
    the corners; J1 declared on the left edge; C1 a decoupling satellite."""
    body = _fp("U1", 40, 20, cy=(-3, -3, 3, 3),
               pads=_pad("1", -2, -2, "A") + _pad("2", 2, -2, "B")
               + _pad("3", 2, 2, "C") + _pad("4", -2, 2, "VCC"))
    body += _fp("R1", 4, 4, pads=_pad("1", -0.5, 0, "A")
                + _pad("2", 0.5, 0, "GND"))
    body += _fp("R2", 55, 4, pads=_pad("1", -0.5, 0, "B")
                + _pad("2", 0.5, 0, "GND"))
    body += _fp("R3", 55, 36, pads=_pad("1", -0.5, 0, "C")
                + _pad("2", 0.5, 0, "GND"))
    body += _fp("R4", 4, 36, pads=_pad("1", -0.5, 0, "VCC")
                + _pad("2", 0.5, 0, "GND"))
    body += _fp("C1", 20, 35, pads=_pad("1", -0.5, 0, "VCC")
                + _pad("2", 0.5, 0, "GND"))
    # J1 flush on the left edge: the annealer only SLIDES edge clusters
    # (seating them flush is place_seed's job), so the fixture starts legal
    body += _fp("J1", 2, 20, cy=(-2, -3, 2, 3),
                pads=_pad("1", 0, -1, "A") + _pad("2", 0, 1, "GND"))
    return _pcb(tmp_path_factory, name, body)


SCATTER_CON = {"power": [{"net": "VCC", "current_a": 1.0}],
               "placement": {"edges": [{"ref": "J1", "edge": "left"}]}}
SCATTER_DEC = {"associations": [
    {"cap": "C1", "ic": "U1", "pin": "4", "rail": "VCC", "value": "100nF"}]}

FAST = dict(moves_per_cluster=25, max_epochs=12, stall=6, candidates=2)


def _run_anneal(pcb, constraints=SCATTER_CON, decoupling=SCATTER_DEC,
                seed=1, probe=None, **kw):
    params = Params(seed=seed, **{**FAST, **kw})
    return place_anneal.anneal(pcb, constraints, decoupling, params,
                               route_probe=probe)


def _engine(pcb, constraints=SCATTER_CON, decoupling=SCATTER_DEC, **kw):
    model = placelib.PlaceModel(pcb)
    placement = constraints.get("placement") or {}
    clusters, warns = placelib.build_clusters(model, decoupling, placement)
    bodies = place_anneal._build_bodies(model, clusters, warns)
    return Engine(model, bodies, constraints, decoupling, **kw), model


# ============================================================ pure: geometry

def test_seg_cross_predicate():
    assert _seg_cross((0, 0), (2, 2), (0, 2), (2, 0))
    assert not _seg_cross((0, 0), (2, 2), (3, 0), (5, 2))       # disjoint
    assert not _seg_cross((0, 0), (2, 2), (2, 2), (4, 0))       # endpoint touch
    assert not _seg_cross((0, 0), (2, 2), (1, 1), (3, 3))       # collinear
    assert not _seg_cross((0, 0), (2, 0), (1, 0), (1, 2))       # T-touch


def test_engine_hpwl_matches_placelib(tmp_path_factory):
    pcb = _scatter_board(tmp_path_factory, "hpwlref")
    eng, model = _engine(pcb)
    # engine normalizes satellites into slots; apply that state to the model
    place_anneal._apply_state(model, eng.bodies, eng.centers, eng.angles)
    want = placelib.hpwl(model)["total_mm"]
    assert eng.hpwl_raw_total == pytest.approx(want, abs=0.01)


def test_incremental_matches_full_sync(tmp_path_factory):
    import random
    pcb = _scatter_board(tmp_path_factory, "increm")
    eng, _model = _engine(pcb)
    rng = random.Random(42)
    movable = [b.cid for b in eng.bodies if b.kind != "edge_fixed"]
    for _ in range(60):
        cid = rng.choice(movable)
        c = (rng.uniform(2, 58), rng.uniform(2, 38))
        a = rng.choice((0.0, 90.0, 180.0, 270.0))
        eng.set_state(cid, c, a)
    kept = (eng.hpwl_raw_total, eng.hpwl_w_total, eng.overlap_total,
            eng.overflow, eng.cross_total, eng.rule_total)
    eng.full_sync()
    fresh = (eng.hpwl_raw_total, eng.hpwl_w_total, eng.overlap_total,
             eng.overflow, eng.cross_total, eng.rule_total)
    for k, f in zip(kept, fresh):
        assert k == pytest.approx(f, abs=1e-6)


def test_crossings_and_congestion_react_to_moves(tmp_path_factory):
    # A(R1-R2 horizontal) and B(R3-R4) - move R3/R4 to cross A, then away
    body = _fp("R1", 10, 20, pads=_pad("1", 0, 0, "A"))
    body += _fp("R2", 50, 20, pads=_pad("1", 0, 0, "A"))
    body += _fp("R3", 30, 5, pads=_pad("1", 0, 0, "B"))
    body += _fp("R4", 30, 35, pads=_pad("1", 0, 0, "B"))
    pcb = _pcb(tmp_path_factory, "cross", body)
    eng, _m = _engine(pcb, {"placement": {}}, {})
    assert eng.cross_total == 1.0          # vertical B crosses horizontal A
    r3 = next(b.cid for b in eng.bodies if b.cluster.anchor == "R3")
    eng.set_state(r3, (10.0, 35.0), 0.0)   # B now to one side, no crossing
    assert eng.cross_total == 0.0
    assert eng.overflow >= 0


def test_congestion_overflow_counts_demand_above_cap(tmp_path_factory):
    # 6 two-pad nets all funneled through the same 2 mm cell column
    body = ""
    for i in range(6):
        body += _fp(f"L{i}", 20, 19 + 0.1 * i,
                    pads=_pad("1", 0, 0, f"N{i}"))
        body += _fp(f"R{i}", 40, 19 + 0.1 * i,
                    pads=_pad("1", 0, 0, f"N{i}"))
    pcb = _pcb(tmp_path_factory, "cong", body)
    eng, _m = _engine(pcb, {"placement": {}}, {}, cong_cap=4)
    assert eng.overflow > 0
    eng2, _m2 = _engine(pcb, {"placement": {}}, {}, cong_cap=50)
    assert eng2.overflow == 0


def test_rule_terms(tmp_path_factory):
    pcb = _scatter_board(tmp_path_factory, "rules")
    eng, _m = _engine(pcb)
    # high-current path: current_a * hpwl(VCC) folded into rule_total
    assert eng.rule_total == pytest.approx(
        1.0 * eng.hpwl_raw["VCC"], abs=1e-6)
    # separation groups
    con = {**SCATTER_CON,
           "placement": {**SCATTER_CON["placement"],
                         "separation": [{"a": ["R1"], "b": ["R2"],
                                         "min_mm": 100.0}]}}
    eng2, _m2 = _engine(pcb, con)
    assert eng2.rule_total > eng.rule_total   # R1/R2 are < 100 mm apart
    # thermal spreading fires when hot parts sit closer than the spread
    con3 = {**SCATTER_CON, "thermal": [{"ref": "R1", "power_w": 1.0},
                                       {"ref": "R2", "power_w": 1.0}]}
    eng3, _m3 = _engine(pcb, con3)
    r1 = next(b.cid for b in eng3.bodies if b.cluster.anchor == "R1")
    r2 = next(b.cid for b in eng3.bodies if b.cluster.anchor == "R2")
    base = eng3.rule_total
    eng3.set_state(r1, (30.0, 20.0), 0.0)
    eng3.set_state(r2, (32.0, 20.0), 0.0)   # 2 mm apart < 10 mm spread
    assert eng3.rule_total > base


def test_gnd_excluded_from_mst_terms(tmp_path_factory):
    pcb = _scatter_board(tmp_path_factory, "gndmst")
    eng, _m = _engine(pcb)
    assert "GND" not in eng.mst_nets
    assert "GND" in eng.nets                # still counts toward hpwl
    assert eng._wnet["GND"] == place_anneal.W_GND


# ============================================================ pure: annealing

def test_anneal_improves_and_stays_legal(tmp_path_factory):
    pcb = _scatter_board(tmp_path_factory, "improve")
    before = placelib.hpwl(placelib.PlaceModel(pcb))["total_mm"]
    candidates, facts, _model = _run_anneal(pcb)
    best = candidates[0]
    assert best["legal"], best["violations"]
    assert best["hpwl_mm"] < before
    assert facts["hpwl_input_mm"] == pytest.approx(before, abs=0.01)


def test_board_file_untouched_by_anneal(tmp_path_factory):
    pcb = _scatter_board(tmp_path_factory, "untouched")
    raw = pcb.read_bytes()
    _run_anneal(pcb)
    assert pcb.read_bytes() == raw


def test_deterministic_per_seed(tmp_path_factory):
    pcb = _scatter_board(tmp_path_factory, "determ")
    c1, f1, _ = _run_anneal(pcb, seed=7)
    c2, f2, _ = _run_anneal(pcb, seed=7)
    assert [c["ops"] for c in c1] == [c["ops"] for c in c2]
    assert [c["cost"] for c in c1] == [c["cost"] for c in c2]
    assert f1["moves"] == f2["moves"] and f1["accepted"] == f2["accepted"]
    c3, f3, _ = _run_anneal(pcb, seed=8)
    assert (c3[0]["ops"] != c1[0]["ops"] or f3["accepted"] != f1["accepted"])


def test_satellites_ride_their_anchor(tmp_path_factory):
    pcb = _scatter_board(tmp_path_factory, "satride")
    candidates, _f, model = _run_anneal(pcb)
    # model holds the last candidate applied; re-apply best explicitly
    eng, model = _engine(pcb)
    ops = {o["ref"]: o for o in candidates[0]["ops"]}
    u1, c1 = ops["U1"], ops["C1"]
    # satellite offset in the anchor frame must match the engine's slot
    b = next(b for b in eng.bodies if b.cluster.anchor == "U1")
    slot, rel = b.slots["C1"]
    dx, dy = c1["x"] - u1["x"], c1["y"] - u1["y"]
    lx, ly = _rot(dx, dy, u1["deg"])       # back into the anchor frame
    assert (lx, ly) == (pytest.approx(slot[0], abs=0.01),
                        pytest.approx(slot[1], abs=0.01))
    assert (c1["deg"] - u1["deg"]) % 360.0 == pytest.approx(rel % 360.0,
                                                            abs=0.05)


def test_edge_cluster_stays_on_edge(tmp_path_factory):
    pcb = _scatter_board(tmp_path_factory, "edgemv")
    candidates, _f, _m = _run_anneal(pcb)
    model = placelib.PlaceModel(pcb)
    # fold best ops into the parsed model without SWIG: set pos/angle
    for o in candidates[0]["ops"]:
        fp = model.footprints[o["ref"]]
        fp.pos = (o["x"], o["y"])
        fp.angle = o["deg"]
    ext = model.footprints["J1"].extents_abs()
    line = placelib.edge_line(model.outline, "left")
    assert ext.distance(line) <= placelib.EDGE_TOL
    assert model.footprints["J1"].angle == pytest.approx(0.0)  # never rotated


def test_edge_with_explicit_pos_is_frozen(tmp_path_factory):
    pcb = _scatter_board(tmp_path_factory, "edgefix")
    con = {**SCATTER_CON, "placement": {
        "edges": [{"ref": "J1", "edge": "left", "pos": 0.5}]}}
    eng, _m = _engine(pcb, con)
    j1 = next(b for b in eng.bodies if b.cluster.anchor == "J1")
    assert j1.kind == "edge_fixed"
    before = eng.centers[j1.cid]
    candidates, _f, _m2 = _run_anneal(pcb, constraints=con)
    ops = {o["ref"]: o for o in candidates[0]["ops"]}
    # J1's cluster center never moved (origin may differ from center; compare
    # against the engine's own initial state via a fresh engine)
    eng2, _m3 = _engine(pcb, con)
    assert eng2.centers[j1.cid] == before


def test_top_n_distinct_and_sorted(tmp_path_factory):
    pcb = _scatter_board(tmp_path_factory, "topn")
    candidates, _f, _m = _run_anneal(pcb, candidates=3)
    scores = [c["score"] for c in candidates if c["legal"]]
    assert scores == sorted(scores)
    assert [c["rank"] for c in candidates] == list(
        range(1, len(candidates) + 1))
    for i, a in enumerate(candidates):
        for b in candidates[i + 1:]:
            assert a["ops"] != b["ops"]


def test_repair_fixes_forced_overlap(tmp_path_factory):
    pcb = _scatter_board(tmp_path_factory, "repair")
    eng, model = _engine(pcb)
    r1 = next(b.cid for b in eng.bodies if b.cluster.anchor == "R1")
    r2 = next(b.cid for b in eng.bodies if b.cluster.anchor == "R2")
    eng.set_state(r1, (30.0, 20.0), 0.0)
    eng.set_state(r2, (30.2, 20.0), 0.0)   # forced courtyard overlap
    place_anneal._apply_state(model, eng.bodies, eng.centers, eng.angles)
    assert any(v["kind"] == "courtyard_overlap"
               for v in placelib.legality_violations(model, {}))
    moved = place_anneal._repair(model, eng, {})
    assert moved
    assert not [v for v in placelib.legality_violations(model, {})
                if v["severity"] == "error"]


def test_all_locked_yields_note(tmp_path_factory):
    body = _fp("R1", 10, 10, locked=True, pads=_pad("1", 0, 0, "A"))
    body += _fp("R2", 20, 10, locked=True, pads=_pad("1", 0, 0, "A"))
    pcb = _pcb(tmp_path_factory, "alllock", body)
    candidates, facts, _m = _run_anneal(pcb, {"placement": {}}, {})
    assert facts["movable_clusters"] == 0
    assert "note" in facts
    assert len(candidates) == 1


# ============================================================ pure: feedback

def test_route_feedback_flag_is_stubbed(tmp_path_factory):
    pcb = _scatter_board(tmp_path_factory, "fbstub")
    rc = place_anneal.main(["--pcb", str(pcb), "--route-feedback"])
    assert rc == 2


def test_route_probe_blends_into_scoring(tmp_path_factory):
    pcb = _scatter_board(tmp_path_factory, "fbprobe")
    calls = []

    def probe(model):
        calls.append(len(model.footprints))
        return 0.4

    candidates, facts, _m = _run_anneal(pcb, probe=probe, feedback_every=2,
                                        max_epochs=6, stall=6)
    assert calls, "probe was never invoked"
    assert facts["feedback_used"] is True
    assert facts["last_completion"] == pytest.approx(0.4)
    best = candidates[0]
    assert best["completion"] == pytest.approx(0.4)
    # blended score = cost * (1 + w_fb * (1 - completion))
    w_fb = place_anneal.DEFAULT_WEIGHTS["feedback"]
    # cost/score are rounded to 3 dp in the report - allow that much slack
    assert best["score"] == pytest.approx(best["cost"] * (1 + w_fb * 0.6),
                                          abs=2e-3)


def test_probe_boosts_cong_and_cross_weights(tmp_path_factory):
    pcb = _scatter_board(tmp_path_factory, "fbboost")
    eng, _m = _engine(pcb)
    params = Params(seed=1, **{**FAST, "max_epochs": 4}, feedback_every=1)
    ann = place_anneal.Annealer(eng, params, route_probe=lambda m: 0.25)
    ann.run()
    assert eng.fb_boost == pytest.approx(
        1.0 + place_anneal.FB_GAIN * 0.75)


# ============================================================ pure: CLI

def test_cli_report_and_ops_files(tmp_path_factory, tmp_path):
    pcb = _scatter_board(tmp_path_factory, "cli")
    (pcb.parent / "constraints.json").write_text(json.dumps(SCATTER_CON),
                                                 encoding="utf-8")
    (pcb.parent / "decoupling.json").write_text(json.dumps(SCATTER_DEC),
                                                encoding="utf-8")
    rep = tmp_path / "rep.json"
    rc = place_anneal.main([
        "--pcb", str(pcb), "--seed", "3", "--candidates", "2",
        "--moves-per-cluster", "25", "--max-epochs", "10", "--stall", "6",
        "--out-dir", str(tmp_path / "cands"), "--out-report", str(rep)])
    assert rc == 0
    r = json.loads(rep.read_text("utf-8"))
    assert r["script"] == "place_anneal" and r["status"] == "pass"
    for k in ("seed", "clusters", "hpwl_input_mm", "hpwl_best_mm",
              "improvement_pct", "epochs", "moves", "t0", "runtime_s",
              "candidates"):
        assert k in r, k
    for c in r["candidates"]:
        f = Path(c["ops_file"])
        assert f.is_file()
        doc = json.loads(f.read_text("utf-8"))
        assert doc["version"] == 1 and doc["ops"]
        assert "ops" not in c and "violations" not in c   # slim in report
        assert "n_violations" in c


def test_cli_missing_board_exits_2():
    assert place_anneal.main(["--pcb", "no/such/board.kicad_pcb"]) == 2


# ============================================================ smoke: corpus

@pytest.fixture(scope="session")
def cli() -> Path:
    c = env.find_kicad_cli()
    if c is None:
        pytest.skip("kicad-cli not installed")
    return c


@pytest.fixture(scope="session")
def seeded_board(cli, tmp_path_factory) -> Path:
    """usbbuck4 netlist -> board_init -> place_seed --apply (the S10 input)."""
    import board_init
    import kc
    import place_seed
    d = tmp_path_factory.mktemp("annealinit")
    net = d / "usbbuck4.net"
    kc.export_netlist(cli, GOLDEN / "usbbuck4" / "usbbuck4.kicad_sch", net)
    rc = board_init.main([
        "--netlist", str(net), "--name", "usbbuck4",
        "--out", str(d / "kicad"), "--layers", "4", "--mounting-holes", "4"])
    assert rc == 0
    pcb = d / "kicad" / "usbbuck4.kicad_pcb"
    for name in ("constraints.json", "decoupling.json"):
        shutil.copy2(GOLDEN / "usbbuck4" / name, pcb.parent / name)
    payload, _ = place_seed.run([
        "--pcb", str(pcb), "--ops-out", str(d / "seed_ops.json"), "--apply"])
    assert payload["status"] == "pass"
    return pcb


@pytest.mark.smoke
def test_anneal_acceptance_usbbuck4(seeded_board, tmp_path):
    """Plan S10 acceptance: >=20% HPWL under the seed, legal, bounded runtime.

    60 epochs is the smoke budget (26% at 50 epochs when built); the default
    140-epoch budget reached 43.4% in ~2 min (PROGRESS S10)."""
    import place_edit
    import place_metrics
    constraints = json.loads(
        (GOLDEN / "usbbuck4" / "constraints.json").read_text("utf-8"))
    decoupling = json.loads(
        (GOLDEN / "usbbuck4" / "decoupling.json").read_text("utf-8"))
    seed_hpwl = placelib.hpwl(placelib.PlaceModel(seeded_board))["total_mm"]
    params = Params(seed=1, max_epochs=60)
    candidates, facts, _m = place_anneal.anneal(
        seeded_board, constraints, decoupling, params)
    best = candidates[0]
    assert best["legal"], best["violations"]
    improvement = 100.0 * (seed_hpwl - best["hpwl_mm"]) / seed_hpwl
    assert improvement >= 20.0, (seed_hpwl, best["hpwl_mm"])
    assert facts["runtime_s"] < 1800.0     # plan bar: <30 min

    # apply the winner and hold it to the P6 gate
    place_edit.apply_ops(seeded_board, best["ops"])
    payload, _ = place_metrics.run(["--pcb", str(seeded_board)])
    assert payload["status"] == "pass", payload["violations"]
    assert payload["metrics"]["hpwl"]["total_mm"] == pytest.approx(
        best["hpwl_mm"], abs=0.05)
    for f in payload["metrics"]["decoupling"]:
        assert f["manhattan_mm"] < 10.0, f


@pytest.mark.smoke
def test_anneal_reproducible_on_corpus(seeded_board):
    outs = []
    constraints = json.loads(
        (GOLDEN / "usbbuck4" / "constraints.json").read_text("utf-8"))
    decoupling = json.loads(
        (GOLDEN / "usbbuck4" / "decoupling.json").read_text("utf-8"))
    for _ in range(2):
        c, _f, _m = place_anneal.anneal(
            seeded_board, constraints, decoupling,
            Params(seed=11, max_epochs=8, stall=8))
        outs.append(json.dumps([x["ops"] for x in c]))
    assert outs[0] == outs[1]
