"""S1 acceptance tests: golden-board corpus.

Plan S1 accept criteria:
  - golden boards pass `kicad-cli sch erc` / `pcb drc` clean
  - mutation scripts run deterministically
  - manifest complete

Everything here drives the REAL kicad-cli (10.0.3 pin via env.py); tests
are marked `smoke` where they need the live toolchain so `pytest -m "not
smoke"` still runs the pure-file checks.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[1]
GOLDEN = REPO / "tests" / "golden"
sys.path.insert(0, str(REPO / ".claude" / "skills" / "hwde" / "scripts" / "lib"))
import env  # noqa: E402

BOARDS = ["blinky2", "usbbuck4", "rf4"]
MUTATIONS = {
    "plane-split-under-clock": "plane_split_under_clock.py",
    "missing-return-via": "missing_return_via.py",
    "undersized-power-trace": "undersized_power_trace.py",
    "decoupler-moved": "decoupler_moved.py",
    "diffpair-skew": "diffpair_skew.py",
    "silk-over-pad": "silk_over_pad.py",
    "cpl-rotation": "cpl_rotation.py",
}


@pytest.fixture(scope="session")
def kicad_cli() -> Path:
    cli = env.find_kicad_cli()
    if cli is None:
        pytest.skip("kicad-cli not installed")
    return cli


@pytest.fixture(scope="session")
def manifest() -> dict:
    return yaml.safe_load((GOLDEN / "manifest.yaml").read_text(encoding="utf-8"))


def run_cli(cli: Path, args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run([str(cli), *args], capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=300)


def erc_violations(cli: Path, sch: Path, tmp: Path) -> list[dict]:
    rep = tmp / "erc.json"
    run_cli(cli, ["sch", "erc", "--format", "json", "--severity-all",
                  "-o", str(rep), str(sch)])
    data = json.loads(rep.read_text(encoding="utf-8"))
    return [v for s in data.get("sheets", []) for v in s.get("violations", [])]


def drc_violations(cli: Path, pcb: Path, tmp: Path, parity: bool) -> list[dict]:
    rep = tmp / "drc.json"
    args = ["pcb", "drc", "--format", "json", "--severity-all"]
    if parity:
        args.append("--schematic-parity")
    run_cli(cli, [*args, "-o", str(rep), str(pcb)])
    data = json.loads(rep.read_text(encoding="utf-8"))
    return (data.get("violations", []) + data.get("unconnected_items", [])
            + data.get("schematic_parity", []))


# ------------------------------------------------------------------ goldens

@pytest.mark.smoke
@pytest.mark.parametrize("board", BOARDS)
def test_golden_erc_clean(kicad_cli, board, tmp_path):
    sch = GOLDEN / board / f"{board}.kicad_sch"
    assert sch.exists(), f"golden schematic missing: {sch}"
    violations = erc_violations(kicad_cli, sch, tmp_path)
    assert violations == [], (
        f"{board} ERC not clean: "
        f"{[(v['type'], v['severity']) for v in violations]}")


@pytest.mark.smoke
@pytest.mark.parametrize("board", BOARDS)
def test_golden_drc_clean_with_parity(kicad_cli, board, tmp_path):
    pcb = GOLDEN / board / f"{board}.kicad_pcb"
    assert pcb.exists(), f"golden board missing: {pcb}"
    violations = drc_violations(kicad_cli, pcb, tmp_path, parity=True)
    assert violations == [], (
        f"{board} DRC/parity not clean: "
        f"{[(v['type'], v['severity']) for v in violations]}")


@pytest.mark.smoke
@pytest.mark.parametrize("board", BOARDS)
def test_golden_zones_filled(board):
    """Committed goldens must carry saved zone fills (S3 relies on them)."""
    pcb = GOLDEN / board / f"{board}.kicad_pcb"
    assert "filled_polygon" in pcb.read_text(encoding="utf-8"), (
        f"{board}: no saved zone fill - regenerate via gen.py")


# ----------------------------------------------------------------- mutants

@pytest.mark.smoke
@pytest.mark.parametrize("name", list(MUTATIONS))
def test_mutation_deterministic_and_effective(name, tmp_path):
    """Two runs -> byte-identical output; output differs from the golden."""
    script = GOLDEN / "mutations" / MUTATIONS[name]
    digests = []
    boards = []
    for i in range(2):
        out = tmp_path / f"run{i}"
        cp = subprocess.run(
            [sys.executable, str(script), "--out", str(out)],
            capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=300)
        assert cp.returncode == 0, f"{name} run {i} failed: {cp.stdout}"
        summary = json.loads(cp.stdout.strip().splitlines()[-1])
        pcb = Path(summary["out"])
        boards.append(pcb)
        digests.append(hashlib.sha256(pcb.read_bytes()).hexdigest())
    assert digests[0] == digests[1], f"{name} is not deterministic"
    golden = GOLDEN / boards[0].stem / boards[0].name
    assert boards[0].read_bytes() != golden.read_bytes(), (
        f"{name} did not change the board")


@pytest.mark.parametrize("name", list(MUTATIONS))
def test_mutant_committed(name, manifest):
    """The committed mutants directory matches the manifest."""
    board = manifest["mutants"][name]["board"]
    pcb = GOLDEN / "mutants" / name / f"{board}.kicad_pcb"
    assert pcb.exists(), (
        f"committed mutant missing: {pcb} (run mutations/{MUTATIONS[name]})")


# ---------------------------------------------------------------- manifest

def test_manifest_complete(manifest):
    assert set(manifest["golden_boards"]) == set(BOARDS)
    assert set(manifest["mutants"]) == set(MUTATIONS)
    known_checks = {"check_return_path", "check_decoupling", "check_current",
                    "check_diffpair", "check_creepage", "check_thermal",
                    "check_silk", "check_pdn", "dfm_check"}
    for name, m in manifest["mutants"].items():
        assert m["board"] in BOARDS, f"{name}: unknown board {m['board']}"
        assert m["check"] in known_checks, f"{name}: unknown check {m['check']}"
        script = GOLDEN / m["script"]
        assert script.exists(), f"{name}: script missing {script}"
        assert "expect" in m and m["expect"], f"{name}: no expectation"


def test_manifest_boards_exist(manifest):
    for name, g in manifest["golden_boards"].items():
        d = GOLDEN / g["dir"]
        for ext in (".kicad_sch", ".kicad_pcb", ".kicad_pro"):
            assert (d / f"{name}{ext}").exists(), f"{name}{ext} missing"
