"""Castellated edge pads end to end: footprint, checks, DFM, quote, order, report.

The fixture tests/fixtures/castellated/castellated_edge.kicad_pcb is a 30 x 20
mm board with two rows of six castellated pads from castellated_fp.py (J1 on
the top edge, J2 on the bottom edge turned 180 deg); make_fixture.py rebuilds
it. Each mutant below is a text edit of that fixture into tmp_path, so every
case stands on its own board. rp2040-mini is read from the boards repo only
(skipped when absent) and must count 0 castellated pads today.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / ".claude" / "skills" / "hwde" / "scripts"
import sys  # noqa: E402

sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(SCRIPTS / "lib"))

import castellated_fp  # noqa: E402
import castellation  # noqa: E402
import geom  # noqa: E402
import order_quote  # noqa: E402
import order_submit  # noqa: E402
import report_gen  # noqa: E402
from _boards import real_board  # noqa: E402

FIX = REPO / "tests" / "fixtures" / "castellated" / "castellated_edge.kicad_pcb"
PLAIN = REPO / "tests" / "fixtures" / "rf_term_edge" / "rf_term_edge.kicad_pcb"
RULES = castellation.load_rules()


def _mutant(tmp_path: Path, edit) -> Path:
    out = tmp_path / "board.kicad_pcb"
    out.write_text(edit(FIX.read_text(encoding="utf-8")), encoding="utf-8")
    return out


def _kinds(pcb: Path) -> dict[str, int]:
    vios, _ = castellation.check(geom.load_board(pcb), RULES, 1.6)
    out: dict[str, int] = {}
    for v in vios:
        out[v["kind"]] = out.get(v["kind"], 0) + 1
    return out


def _move(text: str, ref: str, new_at: str) -> str:
    """Move footprint `ref` to `new_at` (the footprint's own (at ...))."""
    blocks = text.split("\n\t(footprint ")
    for i, b in enumerate(blocks):
        if f'"Reference" "{ref}"' in b:
            blocks[i] = re.sub(r"\(at [^)]*\)", f"(at {new_at})", b, count=1)
    return "\n\t(footprint ".join(blocks)


# ------------------------------------------------------------- footprint

def test_generator_marks_every_pad_castellated(tmp_path):
    out = tmp_path / "Cast.pretty" / "C6.kicad_mod"
    rep = castellated_fp.run(6, 2.54, out)
    text = out.read_text(encoding="utf-8")
    assert rep["status"] == "pass" and rep["drill_mm"] == RULES["rec_drill_mm"]
    assert text.count("(pad ") == 6
    assert text.count("(property pad_prop_castellated)") == 6
    # a board feature: nothing to buy or place
    assert "exclude_from_bom" in text and "exclude_from_pos_files" in text
    # hole centres on y = 0: pad centre + drill offset cancel
    assert "(at -6.35 0.275)" in text and "(offset 0 -0.275)" in text


@pytest.mark.parametrize("kw, words", [
    ({"pitch": 1.2}, "hole edge-to-edge"),
    ({"drill": 0.5}, "drill 0.5 mm < JLC minimum 0.6"),
    ({"ring": 0.1}, "ring 0.1 mm < JLC minimum 0.18"),
    ({"extension": 0.3}, "extension 0.3 mm < JLC minimum 0.5"),
])
def test_generator_refuses_below_jlc_minimums(tmp_path, kw, words):
    out = tmp_path / "x.kicad_mod"
    args = {"pitch": 2.54, **kw}
    pitch = args.pop("pitch")
    with pytest.raises(ValueError, match=re.escape(words)):
        castellated_fp.run(4, pitch, out, **args)
    assert not out.exists()
    # the same row at JLC's own minimums is accepted
    castellated_fp.run(4, 1.2 if "pitch" not in kw else 1.6, out,
                       drill=0.6, ring=0.18, extension=0.5)
    assert out.exists()


# ---------------------------------------------------------------- checks

def test_fixture_counts_and_passes():
    assert castellation.count(FIX) == 12
    vios, facts = castellation.check(geom.load_board(FIX), RULES, 1.6)
    assert vios == []
    assert facts == {"castellated_pads": 12, "castellated_refs": ["J1", "J2"]}


def test_board_without_castellation_counts_zero():
    vios, facts = castellation.check(geom.load_board(PLAIN), RULES, 1.6)
    assert facts["castellated_pads"] == 0 and vios == []


def test_unmarked_half_hole_is_an_error(tmp_path):
    pcb = _mutant(tmp_path, lambda t: t.replace(
        " (property pad_prop_castellated)", "").replace(
        "(property pad_prop_castellated)", ""))
    assert castellation.count(pcb) == 0
    assert _kinds(pcb) == {"castellated_unmarked": 12}


def test_castellated_pad_off_the_outline(tmp_path):
    # J1 moved 2 mm inside the board; J2 stays on its edge and stays clean
    pcb = _mutant(tmp_path, lambda t: _move(t, "J1", "15 2"))
    vios, _ = castellation.check(geom.load_board(pcb), RULES, 1.6)
    assert {v["kind"] for v in vios} == {"castellated_off_outline"}
    assert {v["refs"][0] for v in vios} == {"J1"} and len(vios) == 6


def test_castellated_hole_too_near_a_corner(tmp_path):
    # J1's row starts 0.15 mm from x = 0: the end hole is inside the corner
    # and the next edge; J2 untouched
    pcb = _mutant(tmp_path, lambda t: _move(t, "J1", "6.5 0"))
    vios, _ = castellation.check(geom.load_board(pcb), RULES, 1.6)
    near = {v["kind"] for v in vios if v["pad"] == "J1.1"}
    assert near == {"castellated_to_corner", "castellated_to_other_edge"}
    assert not [v for v in vios if v["refs"] == ["J2"]]


def test_castellated_drill_and_ring_and_extension(tmp_path):
    pcb = _mutant(tmp_path, lambda t: t.replace(
        "(drill 1\n", "(drill 0.5\n").replace("(drill 1)", "(drill 0.5)"))
    kinds = _kinds(pcb)
    assert kinds.get("castellated_drill") == 12
    # a 0.5 drill in a 1.5 x 2.05 pad leaves more ring/extension, not less
    assert "castellated_ring" not in kinds
    thin = _mutant(tmp_path, lambda t: re.sub(
        r"\(size 1\.5 2\.05\)", "(size 1.2 1.2)", t))
    kinds = _kinds(thin)
    assert kinds.get("castellated_ring") == 12
    assert kinds.get("castellated_pad_extension") == 12


def test_thickness_and_board_size(tmp_path):
    vios, _ = castellation.check(geom.load_board(FIX), RULES, 0.4)
    assert [v["kind"] for v in vios] == ["castellated_thickness"]
    vios, _ = castellation.check(geom.load_board(FIX), RULES, 0.6)
    assert vios == []


# ------------------------------------------------------------------- DFM

@pytest.mark.smoke
def test_dfm_exempts_castellated_and_checks_them(tmp_path):
    import dfm_check
    rep = dfm_check.run(FIX, polarity=False)
    assert rep["status"] == "pass", [v["msg"] for v in rep["violations"]]
    assert rep["castellated_pads"] == 12
    assert "castellation" in rep["coverage"]["ran"]
    # the same board without the property: ordinary edge rules fire
    plain = _mutant(tmp_path, lambda t: t.replace(
        " (property pad_prop_castellated)", "").replace(
        "(property pad_prop_castellated)", ""))
    rep = dfm_check.run(plain, polarity=False)
    kinds = {v["kind"] for v in rep["violations"]}
    assert {"castellated_unmarked", "dfm_hole_to_edge",
            "dfm_copper_to_edge"} <= kinds


# ------------------------------------------------------- quote and order

def test_quote_adds_the_castellated_surcharge():
    rep = order_quote.run(FIX, [5], ["HASL"], ["green"])
    row = rep["matrix"][0]
    assert rep["spec"]["castellated_pads"] == 12
    assert row["pcb"]["castellated"] == 36.0
    assert row["pcb"]["total"] == round(row["pcb"]["base"] + 36.0, 2)
    plain = order_quote.run(PLAIN, [5], ["HASL"], ["green"])
    assert "castellated_pads" not in plain["spec"]
    assert "castellated" not in plain["matrix"][0]["pcb"]


def test_pcb_param_castellated_holes_follows_the_board():
    spec = {"layers": 2, "qty": 5, "width_mm": 30, "height_mm": 20}
    assert order_submit.build_pcb_param(spec)["castellatedHoles"] == 0
    spec["castellated_pads"] = 12
    assert order_submit.build_pcb_param(spec)["castellatedHoles"] == 1


def test_order_manifest_counts_from_the_board(tmp_path):
    fab = tmp_path / "fab"
    fab.mkdir()
    man = order_submit.run(FIX, fab)
    assert man["spec_snapshot"]["castellated_pads"] == 12
    assert any(s.startswith("CASTELLATED:") for s in man["human_steps"])
    plain = order_submit.run(PLAIN, fab)
    assert plain["spec_snapshot"]["castellated_pads"] == 0
    assert not any("CASTELLATED" in s for s in plain["human_steps"])


# ----------------------------------------------------------------- report

def _doc(ws: Path) -> report_gen.DocBuilder:
    return report_gen.DocBuilder(ws, {"board": "x"}, "x")


def test_report_names_castellation_only_when_the_board_has_it(tmp_path):
    ws = tmp_path / "x"
    (ws / "brief").mkdir(parents=True)
    (ws / "brief" / "brief.md").write_text(
        "Pico-style castellated edge pins.\n", encoding="utf-8")
    doc = _doc(ws)
    doc.castellation_line({"castellated_pads": 12,
                           "castellated_refs": ["J1", "J2"]}, None)
    assert "12 castellated pad(s) on J1, J2" in doc.body[-1]
    assert doc.warnings == []

    doc = _doc(ws)
    doc.castellation_line({"castellated_pads": 0}, None)
    assert "none" in doc.body[-1]
    assert len(doc.warnings) == 1 and "brief/brief.md" in doc.warnings[0]

    # a brief that records the deviation is not a claim
    (ws / "brief" / "brief.md").write_text(
        "Edge pins ship as plain PTH, not castellated.\n", encoding="utf-8")
    doc = _doc(ws)
    doc.castellation_line(None, {"spec_snapshot": {"castellated_pads": 0}})
    assert doc.warnings == []


# ------------------------------------------------------------ rp2040-mini

def test_rp2040_mini_has_no_castellated_pads_today():
    ws = real_board("rp2040-mini")
    pcbs = sorted(p for p in ws.rglob("*.kicad_pcb")
                  if "state_snapshots" not in p.parts
                  and not p.name.startswith("_"))
    assert pcbs, f"no board file under {ws}"
    pcb = next((p for p in pcbs if p.parent.name == "route"), pcbs[-1])
    assert castellation.count(pcb) == 0


def test_count_and_refs_are_a_text_scan(tmp_path):
    """The order and BOM legs count a board geom cannot load."""
    assert castellation.refs(FIX) == ["J1", "J2"]
    stub = tmp_path / "stub.kicad_pcb"
    stub.write_text("(kicad_pcb)\n", encoding="utf-8")
    assert castellation.count(stub) == 0 and castellation.refs(stub) == []
