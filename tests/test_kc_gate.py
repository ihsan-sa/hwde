"""S2 acceptance tests: kicad-cli wrappers (kc.py) + gate infrastructure.

Plan S2 accept criteria:
  - wrappers produce normalized JSON for all three golden boards
  - a seeded DRC violation fails gate.py with exit 1 and correct coordinates

Pure tests (no toolchain) exercise the normalizer and gate logic on captured
kicad-cli JSON. `smoke`-marked tests drive the real kicad-cli (10.0.3 via
env.py) so `pytest -m "not smoke"` still runs the parser/logic checks.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / ".claude" / "skills" / "ai-ee" / "scripts"
GOLDEN = REPO / "tests" / "golden"
GATES_YAML = SCRIPTS.parent / "reference" / "gates.yaml"
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(SCRIPTS / "lib"))
import env  # noqa: E402
import kc  # noqa: E402
import gate  # noqa: E402

BOARDS = ["blinky2", "usbbuck4", "rf4"]


# ------------------------------------------------------------ captured JSON

# A representative raw kicad-cli DRC report exercising every section and the
# layer/net/refs parsing paths (shapes captured from real 10.0.3 output).
RAW_DRC = {
    "coordinate_units": "mm",
    "kicad_version": "10.0.3",
    "violations": [
        {"type": "track_width", "severity": "error",
         "description": "Track width (min width 0.1270 mm; actual 0.0500 mm)",
         "items": [{"description": "Track [+5V] on F.Cu, length 7.5000 mm",
                    "pos": {"x": 102.8, "y": 103.5}, "uuid": "u1"}]},
        {"type": "silk_over_copper", "severity": "warning",
         "description": "Silkscreen clipped by solder mask",
         "items": [{"description": "PCB text 'TP1' on F.Silkscreen",
                    "pos": {"x": 132.44, "y": 129.5}, "uuid": "u2"},
                   {"description": "Pad 1 [GND] of D1 on F.Cu",
                    "pos": {"x": 132.4375, "y": 129.5}, "uuid": "u3"}]},
    ],
    "unconnected_items": [
        {"type": "unconnected_items", "severity": "error",
         "description": "Missing connection",
         "items": [{"description": "Pad 2 [/MCO] of U1 on B.Cu",
                    "pos": {"x": 141.0, "y": 123.0}, "uuid": "u4"}]},
    ],
    "schematic_parity": [
        {"type": "footprint", "severity": "error",
         "description": "Footprint D1 pad nets differ from schematic",
         "items": [{"description": "Pad 1 [GND] of D1 on F.Cu",
                    "pos": {"x": 132.4, "y": 129.5}, "uuid": "u5"}]},
    ],
}

RAW_ERC = {
    "coordinate_units": "mm",
    "sheets": [{"path": "/", "uuid_path": "/",
                "violations": [
                    {"type": "pin_not_connected", "severity": "error",
                     "description": "Input pin not driven",
                     "items": [{"description": "Symbol U1 Pin 5 [PB0]",
                                "pos": {"x": 50.0, "y": 60.0}}]}]}],
}


# ---------------------------------------------------------- normalizer (pure)

def test_normalized_violation_has_schema_keys():
    for v in kc.parse_drc_data(RAW_DRC):
        for key in kc.SCHEMA_KEYS:
            assert key in v, f"missing {key} in {v}"
        assert v["source"] in ("drc", "unconnected", "parity")


def test_parse_drc_merges_all_sections():
    vs = kc.parse_drc_data(RAW_DRC)
    assert len(vs) == 4
    by_source = {}
    for v in vs:
        by_source.setdefault(v["source"], 0)
        by_source[v["source"]] += 1
    assert by_source == {"drc": 2, "unconnected": 1, "parity": 1}


def test_track_width_fields_parsed():
    tw = next(v for v in kc.parse_drc_data(RAW_DRC) if v["check"] == "track_width")
    assert tw["severity"] == "error"
    assert tw["pos"] == [102.8, 103.5]
    assert tw["layer"] == "F.Cu"
    assert tw["net"] == "+5V"
    assert tw["refs"] == []          # a bare track has no refdes
    assert "Track width" in tw["msg"]


def test_multi_item_aggregation():
    silk = next(v for v in kc.parse_drc_data(RAW_DRC)
                if v["check"] == "silk_over_copper")
    # net comes from the second item (first has none); refs union both items
    assert silk["net"] == "GND"
    assert silk["layer"] == "F.Silkscreen"
    assert silk["refs"] == ["D1", "TP1"]
    assert len(silk["items"]) == 2
    assert silk["pos"] == [132.44, 129.5]     # first item's position


def test_unconnected_net_and_refs():
    u = next(v for v in kc.parse_drc_data(RAW_DRC) if v["source"] == "unconnected")
    assert u["net"] == "/MCO"
    assert u["refs"] == ["U1"]
    assert u["layer"] == "B.Cu"


def test_parse_erc_nesting_and_source():
    vs = kc.parse_erc_data(RAW_ERC)
    assert len(vs) == 1
    v = vs[0]
    assert v["source"] == "erc"
    assert v["sheet"] == "/"
    assert v["refs"] == ["U1"]
    assert v["net"] == "PB0"


def test_summarize_counts():
    c = kc.summarize(kc.parse_drc_data(RAW_DRC))
    assert c["total"] == 4
    assert c["by_severity"] == {"error": 3, "warning": 1}


# ------------------------------------------------------------- gate logic (pure)

def _report(violations):
    return {"input": "x.kicad_pcb", "violations": violations,
            "counts": kc.summarize(violations)}


def test_gate_evaluate_fails_on_error():
    report = _report(kc.parse_drc_data(RAW_DRC))
    g = {"phase": "P6", "tool": "drc", "fail_severities": ["error"], "max_count": 0}
    res = gate.evaluate("drc", g, report)
    assert res["status"] == "fail"
    assert res["failing_count"] == 3          # three error-severity violations
    assert all(v["severity"] == "error" for v in res["failing"])


def test_gate_evaluate_clean_gate_counts_warnings():
    report = _report(kc.parse_drc_data(RAW_DRC))
    g = {"tool": "drc", "fail_severities": ["error", "warning"], "max_count": 0}
    res = gate.evaluate("clean", g, report)
    assert res["failing_count"] == 4          # warning now counts too


def test_gate_evaluate_passes_when_clean():
    res = gate.evaluate("drc", {"tool": "drc", "fail_severities": ["error"]},
                        _report([]))
    assert res["status"] == "pass"
    assert res["failing"] == []


def test_gate_evaluate_max_count_tolerance():
    report = _report(kc.parse_drc_data(RAW_DRC))
    g = {"tool": "drc", "fail_severities": ["error"], "max_count": 5}
    assert gate.evaluate("drc", g, report)["status"] == "pass"


# --------------------------------------------------------------- gates.yaml

def test_gates_yaml_valid():
    data = yaml.safe_load(GATES_YAML.read_text(encoding="utf-8"))
    gates = data["gates"]
    assert {"erc", "drc", "drc_routed"} <= set(gates)
    for name, g in gates.items():
        assert g["tool"] in ("erc", "drc"), f"{name}: bad tool {g['tool']}"
        for sev in g.get("fail_severities", ["error"]):
            assert sev in ("error", "warning", "exclusion")


# ------------------------------------------------------- git-commit helper

def test_git_commit_on_pass(tmp_path):
    repo = tmp_path / "r"
    repo.mkdir()

    def git(*a):
        return subprocess.run(["git", *a], cwd=repo, capture_output=True, text=True)
    assert git("init").returncode == 0
    git("config", "user.email", "t@t")
    git("config", "user.name", "t")
    (repo / "a.txt").write_text("hi", encoding="utf-8")
    res = gate.git_commit_on_pass("gate erc pass", repo)
    assert res["committed"] is True and res["commit"]
    # nothing left to commit -> clean skip, not an error
    res2 = gate.git_commit_on_pass("noop", repo)
    assert res2["committed"] is False and "nothing to commit" in res2["reason"]


# ------------------------------------------------------------------ fixtures

@pytest.fixture(scope="session")
def cli():
    c = env.find_kicad_cli()
    if c is None:
        pytest.skip("kicad-cli not installed")
    return c


SEG_RE = re.compile(
    r"\(segment\s+\(start (-?[\d.]+) (-?[\d.]+)\)\s+"
    r"\(end (-?[\d.]+) (-?[\d.]+)\)\s+\(width ([\d.]+)")


@pytest.fixture
def seeded_drc_board(tmp_path):
    """Copy golden blinky2, narrow its first track segment below the 0.127 mm
    floor -> a deterministic track_width DRC error. Returns (pcb_path, bbox)
    where bbox is the narrowed segment's extent for coordinate verification."""
    src = GOLDEN / "blinky2"
    pcb = tmp_path / "blinky2.kicad_pcb"
    shutil.copy(src / "blinky2.kicad_pcb", pcb)
    shutil.copy(src / "blinky2.kicad_pro", tmp_path / "blinky2.kicad_pro")
    text = pcb.read_text(encoding="utf-8")
    m = SEG_RE.search(text)
    assert m, "no track segment found in golden"
    sx, sy, ex, ey = (float(m.group(i)) for i in range(1, 5))
    patched = text[:m.start(5)] + "0.05" + text[m.end(5):]
    pcb.write_text(patched, encoding="utf-8")
    bbox = (min(sx, ex), min(sy, ey), max(sx, ex), max(sy, ey))
    return pcb, bbox


# ----------------------------------------------------------- smoke: wrappers

@pytest.mark.smoke
@pytest.mark.parametrize("board", BOARDS)
def test_kc_erc_clean_on_goldens(cli, board):
    r = kc.run_erc(cli, GOLDEN / board / f"{board}.kicad_sch")
    assert r["status"] == "pass", r["violations"]
    assert r["counts"]["total"] == 0


@pytest.mark.smoke
@pytest.mark.parametrize("board", BOARDS)
def test_kc_drc_clean_on_goldens(cli, board):
    r = kc.run_drc(cli, GOLDEN / board / f"{board}.kicad_pcb", parity=True,
                   all_track_errors=True)
    assert r["status"] == "pass", r["violations"]
    assert r["counts"]["total"] == 0
    # normalized schema present even when empty
    assert r["units"] == "mm"


# --------------------------------------------------- smoke: gates on goldens

@pytest.mark.smoke
@pytest.mark.parametrize("board", BOARDS)
def test_gate_erc_passes_goldens(cli, board):
    gates = gate.load_gates(GATES_YAML)
    report = kc.run_erc(cli, GOLDEN / board / f"{board}.kicad_sch")
    assert gate.evaluate("erc", gates["erc"], report)["status"] == "pass"


@pytest.mark.smoke
@pytest.mark.parametrize("board", BOARDS)
def test_gate_drc_routed_passes_goldens(cli, board):
    gates = gate.load_gates(GATES_YAML)
    report = gate.run_report_for_gate(gates["drc_routed"],
                                      GOLDEN / board / f"{board}.kicad_pcb")
    assert gate.evaluate("drc_routed", gates["drc_routed"], report)["status"] == "pass"


# ------------------------------------- smoke: THE acceptance - seeded failure

@pytest.mark.smoke
def test_seeded_drc_violation_fails_gate_with_coords(cli, seeded_drc_board):
    pcb, (x0, y0, x1, y1) = seeded_drc_board
    gates = gate.load_gates(GATES_YAML)
    report = gate.run_report_for_gate(gates["drc"], pcb)
    res = gate.evaluate("drc", gates["drc"], report)
    assert res["status"] == "fail"
    tw = [v for v in res["failing"] if v["check"] == "track_width"]
    assert len(tw) == 1, res["failing"]
    px, py = tw[0]["pos"]
    tol = 0.01
    assert x0 - tol <= px <= x1 + tol and y0 - tol <= py <= y1 + tol, (
        f"violation pos {px},{py} not on narrowed segment bbox {x0,y0,x1,y1}")


@pytest.mark.smoke
def test_gate_cli_exit_codes(cli, seeded_drc_board):
    """The literal acceptance: gate.py exits 1 on the seeded violation, 0 on
    the clean golden schematic."""
    pcb, _ = seeded_drc_board
    gate_py = SCRIPTS / "gate.py"

    fail = subprocess.run(
        [sys.executable, str(gate_py), "--gate", "drc", str(pcb)],
        capture_output=True, text=True, cwd=REPO)
    assert fail.returncode == 1, fail.stderr
    assert json.loads(fail.stdout)["status"] == "fail"

    ok = subprocess.run(
        [sys.executable, str(gate_py), "--gate", "erc",
         str(GOLDEN / "blinky2" / "blinky2.kicad_sch")],
        capture_output=True, text=True, cwd=REPO)
    assert ok.returncode == 0, ok.stderr


# ---------------------------------------------------- smoke: export wrappers

@pytest.mark.smoke
def test_kc_export_wrappers(cli, tmp_path):
    pcb = GOLDEN / "blinky2" / "blinky2.kicad_pcb"
    sch = GOLDEN / "blinky2" / "blinky2.kicad_sch"

    net = kc.export_netlist(cli, sch, tmp_path / "nl.net")
    assert net["status"] == "pass" and net["outputs"]

    pos = kc.export_pos(cli, pcb, tmp_path / "pos.csv", units="mm")
    assert pos["status"] == "pass"
    # confirm mm not inches: a board-space coordinate is tens of mm, ~1 in inches
    rows = (tmp_path / "pos.csv").read_text(encoding="utf-8").splitlines()[1:]
    xs = [abs(float(r.split(",")[3].strip('"'))) for r in rows if r]
    assert max(xs) > 25, "pos coordinates look like inches, not mm"


@pytest.mark.smoke
def test_render_wrapper_multiview(cli, tmp_path):
    import render
    pcb = GOLDEN / "blinky2" / "blinky2.kicad_pcb"
    r = render.render_views(pcb, ["top", "iso"], tmp_path, width=400,
                            height=300, quality="basic")
    assert r["status"] == "pass"
    assert {o["view"] for o in r["outputs"]} == {"top", "iso"}
    for o in r["outputs"]:
        assert Path(o["path"]).exists()
