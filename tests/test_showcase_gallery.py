"""docs/showcase/gallery.py: the showcase pictures every board the boards
repo's register lists with a routed layout, in both the PDF source and the
README, and a new board gets its words without anyone writing them."""
from __future__ import annotations

import importlib.util
import json
import warnings
from pathlib import Path

import pytest
from _boards import SHIPPED_CHECKS

REPO = Path(__file__).resolve().parents[1]
SHOWCASE = REPO / "docs" / "showcase"

_spec = importlib.util.spec_from_file_location("gallery", SHOWCASE / "gallery.py")
gallery = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gallery)


class ShowcaseBehind(UserWarning):
    """A finished board the committed showcase does not picture yet."""


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


def report_not_shown(root: Path, strict: bool, **texts) -> dict:
    """Name the finished boards the committed showcase does not picture. The
    boards repo finishes boards on its own clock, so by default this only
    warns: it never turns hwde's landing check red. strict
    (HWDE_LINT_SHIPPED=1) fails instead; `gallery.py --check` exits 1 on it."""
    gone = gallery.not_shown(root, **texts)
    if gone["pdf"] or gone["readme"]:
        msg = (f"the showcase is behind the boards repo: not in the PDF source: "
               f"{gone['pdf']}; not in README.md: {gone['readme']}. "
               f"Run docs/showcase/sync.py.")
        if strict:
            pytest.fail(msg)
        warnings.warn(ShowcaseBehind(msg))
    return gone


def test_a_finished_board_missing_from_the_showcase_warns_and_is_reported(tmp_path):
    root = make_root(tmp_path)
    texts = {"tex": "\\board{a}{other}%\n", "readme": "*__other__ · 2 layers*\n"}
    with pytest.warns(ShowcaseBehind, match=r"\['routed'\]"):
        gone = report_not_shown(root, strict=False, **texts)
    assert gone == {"pdf": ["routed"], "readme": ["routed"]}
    with pytest.raises(pytest.fail.Exception, match="routed"):
        report_not_shown(root, strict=True, **texts)
    shown = {"tex": "\\board{a}{routed}%\n", "readme": "*__routed__ · 2 layers*\n"}
    assert report_not_shown(root, strict=True, **shown) == {"pdf": [], "readme": []}


def test_gallery_check_names_a_finished_board_the_showcase_lacks(tmp_path, monkeypatch, capsys):
    root = make_root(tmp_path)
    monkeypatch.setattr(gallery, "generate", lambda *a, **k: {
        "tex_changed": False, "readme_changed": False})
    assert gallery.main(["--boards-root", str(root), "--check"]) == 1
    out = json.loads(capsys.readouterr().out)
    assert out["not_shown"] == {"pdf": ["routed"], "readme": ["routed"]}


def test_every_finished_board_is_in_the_showcase():
    """Warns (fails with HWDE_LINT_SHIPPED=1) when the register lists a board
    with a routed layout that the committed showcase does not picture: run
    docs/showcase/sync.py."""
    from lib import env
    root = env.boards_root()
    if not (root / "register.yaml").is_file():
        pytest.skip(f"needs the boards repo ({root}; set HWDE_BOARDS_ROOT)")
    assert gallery.finished(root), "the boards repo lists no finished board"
    report_not_shown(root, strict=SHIPPED_CHECKS)
