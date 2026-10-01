"""docs/showcase/gallery.py: the showcase pictures every board the boards
repo's register lists with a routed layout, in both the PDF source and the
README, and a new board gets its words without anyone writing them."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
SHOWCASE = REPO / "docs" / "showcase"

_spec = importlib.util.spec_from_file_location("gallery", SHOWCASE / "gallery.py")
gallery = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gallery)

REG = """products:
  PCB-0001:
    title: tiny sensor node
    revs:
      A: {dir: PCB-0001-A_routed, date: 2026-09-01}
  PCB-0002:
    title: bench buck
    revs:
      A: {dir: PCB-0002-A_early, date: 2026-09-02}
"""

# A 2-layer board: a 30 x 20 outline whose right edge is a half circle of
# radius 10 bulging out to x = 40, and two footprints.
PCB = """(kicad_pcb
\t(version 20250114)
\t(layers
\t\t(0 "F.Cu" signal)
\t\t(2 "B.Cu" signal)
\t\t(25 "Edge.Cuts" user)
\t)
\t(footprint "R_0603"
\t\t(layer "F.Cu")
\t)
\t(footprint "C_0603"
\t\t(layer "F.Cu")
\t)
\t(gr_line (start 0 0) (end 30 0) (layer "Edge.Cuts"))
\t(gr_line (start 0 0) (end 0 20) (layer "Edge.Cuts"))
\t(gr_line (start 0 20) (end 30 20) (layer "Edge.Cuts"))
\t(gr_arc (start 30 0) (mid 40 10) (end 30 20) (layer "Edge.Cuts"))
)
"""


def make_root(tmp_path: Path) -> Path:
    root = tmp_path / "boards"
    root.mkdir()
    (root / "register.yaml").write_text(REG)
    routed = root / "PCB-0001-A_routed"
    (routed / "kicad").mkdir(parents=True)
    (routed / "kicad" / "PCB-0001-A_routed.kicad_pcb").write_text(PCB)
    (routed / "state.json").write_text(json.dumps({"phase": "P8", "gates": {}}))
    early = root / "PCB-0002-A_early"
    early.mkdir()
    (early / "state.json").write_text(json.dumps({"phase": "P3", "gates": {}}))
    return root


def test_finished_keeps_routed_and_drops_unrouted(tmp_path):
    root = make_root(tmp_path)
    assert gallery.finished(root) == ["routed"]


def test_pcb_facts_reads_layers_outline_and_footprints(tmp_path):
    root = make_root(tmp_path)
    f = gallery.pcb_facts(root / "PCB-0001-A_routed/kicad/PCB-0001-A_routed.kicad_pcb")
    assert f == {"layers": 2, "w": 40.0, "h": 20.0, "footprints": 2}


def test_blurb_comes_from_requirements_and_skips_run_bookkeeping(tmp_path):
    root = make_root(tmp_path)
    ws = root / "PCB-0001-A_routed"
    (ws / "requirements.md").write_text(
        "# req\n\n## 1. Function\n\nMode declaration: none. A small board that "
        "reads a sensor. It runs from USB.\n\n## 2. Interfaces\n- USB-C\n")
    assert gallery.requirements_blurb(ws) == \
        "A small board that reads a sensor. It runs from USB."


def test_board_without_words_gets_its_register_title(tmp_path):
    root = make_root(tmp_path)
    m = gallery.model(root, {"sections": []})
    assert m["new"] == ["routed"]
    plate = m["sections"][0]["blocks"][1]["plates"][0]
    assert plate["caption"] == "Tiny sensor node."
    assert plate["facts"] == "2 layers · 40 × 20 mm · 2 footprints"
    # The unrouted board is named in one line and never pictured.
    assert [b["name"] for b in m["unrouted"]] == ["early"]
    assert "early" not in m["shown"]


def test_shown_finds_pictured_boards_only():
    tex = "\\board{a}{alpha}%\n{2 layers}{}%\n{x}\n\\board{a-fcu}{alpha, top copper}%"
    assert gallery.shown_in_tex(tex) == ["alpha", "alpha, top copper"]
    md = "*__alpha__ · 2 layers · 1 × 1 mm*\n__beta__ named in prose only\n"
    assert gallery.shown_in_readme(md) == ["alpha"]


def test_every_finished_board_is_in_the_showcase():
    """Fails when the register lists a board with a routed layout that the
    committed showcase does not picture: run docs/showcase/sync.py."""
    from lib import env
    root = env.boards_root()
    if not (root / "register.yaml").is_file():
        pytest.skip(f"needs the boards repo ({root}; set HWDE_BOARDS_ROOT)")
    want = set(gallery.finished(root))
    assert want, "the boards repo lists no finished board"
    tex = (SHOWCASE / "hwde-showcase.tex").read_text(encoding="utf-8") + \
        (SHOWCASE / "gallery.tex").read_text(encoding="utf-8")
    readme = (REPO / "README.md").read_text(encoding="utf-8")
    missing_pdf = sorted(want - set(gallery.shown_in_tex(tex)))
    missing_md = sorted(want - set(gallery.shown_in_readme(readme)))
    assert not missing_pdf and not missing_md, (
        f"not in the showcase PDF source: {missing_pdf}; not in README.md: "
        f"{missing_md}. Run docs/showcase/sync.py.")
