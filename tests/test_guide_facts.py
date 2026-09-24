"""guide_facts.py acceptance tests.

Criteria -> tests:
  - complete fab package -> exit 0 / pass, BOM rows + paths populated
                                     -> test_complete_package_pass
  - missing zip/BOM/CPL -> exit 1, `missing` names it; a complete sibling
    workspace built in the same test is unaffected -> test_missing_fab_files
  - missing quote/schematic pdf -> `todo`, not a violation
                                     -> test_missing_quote_and_schematic_is_todo
  - no workspace / unreadable state.json -> exit 2
                                     -> test_no_workspace_exit2,
                                        test_unreadable_state_exit2
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / ".claude" / "skills" / "hwde" / "scripts"
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(SCRIPTS / "lib"))

import guide_facts  # noqa: E402

TS = "2026-07-28T10:00:00"

BOM_HEADER = "Designator,Comment,Footprint,LCSC,Qty Per Board,MPN,Assembly Class\n"


def bom_row(designator="R1", comment="10k", footprint="0402", lcsc="C1000",
           qty="1", mpn="", assy="smt_placed") -> str:
    return f"{designator},{comment},{footprint},{lcsc},{qty},{mpn},{assy}\n"


def make_workspace(tmp_path: Path, name: str = "synth", board: str = "synth",
                   with_fab: bool = True, with_quote: bool = True,
                   with_schematic: bool = True) -> Path:
    """Synthetic workspace covering the state.json + kicad/ + fab/ facts
    guide_facts.collect reads, per the artifact_kinds paths in
    reference/invalidation.yaml (kicad/{board}.kicad_sch,
    kicad/{board}.kicad_pcb, kicad/parts.json, fab/{board}_gerbers.zip,
    fab/BOM.csv, fab/BOM-full.csv, fab/CPL.csv)."""
    ws = tmp_path / name
    state = {
        "version": 1, "board": board, "phase": "P10", "mode": "default",
        "gates": {"dfm": {"status": "pass"}},
        "artifacts": {},
        "decisions": [{"text": "used 2oz copper", "phase": "P2", "ts": TS}],
    }
    ws.mkdir()
    (ws / "state.json").write_text(json.dumps(state, indent=1), encoding="utf-8")

    kicad = ws / "kicad"
    kicad.mkdir()
    (kicad / f"{board}.kicad_sch").write_text("(kicad_sch)", encoding="utf-8")
    (kicad / f"{board}.kicad_pcb").write_text("(kicad_pcb)", encoding="utf-8")
    (kicad / "parts.json").write_text(json.dumps({"parts": [
        {"lcsc": "C1000", "mpn": "RC0402", "basic": True, "price": 0.01,
         "description": "10k resistor"}]}), encoding="utf-8")

    if with_fab:
        fab = ws / "fab"
        fab.mkdir()
        (fab / f"{board}_gerbers.zip").write_bytes(b"PK\x03\x04")
        (fab / "BOM.csv").write_text(BOM_HEADER + bom_row(), encoding="utf-8")
        (fab / "BOM-full.csv").write_text(BOM_HEADER + bom_row(),
                                          encoding="utf-8")
        (fab / "CPL.csv").write_text(
            "Designator,Mid X,Mid Y,Layer,Rotation\nR1,1,1,top,0\n",
            encoding="utf-8")
        if with_quote:
            (fab / "quote.json").write_text(json.dumps({
                "estimated": True, "currency": "USD",
                "matrix": [{"qty": 10, "surface_finish": "HASL",
                           "total": 12.3, "unit_cost": 1.23,
                           "assembly": {"total": 5.0}}]}), encoding="utf-8")

    if with_schematic:
        reports = ws / "reports"
        reports.mkdir()
        (reports / "schematic.pdf").write_bytes(b"%PDF-1.4\n%%EOF\n")

    return ws


def run_main(ws: Path, tmp_path: Path, capsys, name="out"):
    out = tmp_path / f"{name}.json"
    code = guide_facts.main(["--workspace", str(ws), "--out", str(out)])
    if out.exists():
        payload = json.loads(out.read_text(encoding="utf-8"))
    else:
        payload = json.loads(capsys.readouterr().out)
    return code, payload


# ------------------------------------------------------------------ pass

def test_complete_package_pass(tmp_path, capsys):
    ws = make_workspace(tmp_path)
    code, payload = run_main(ws, tmp_path, capsys)
    assert code == 0, payload
    assert payload["status"] == "pass"
    assert payload["missing"] == []
    assert payload["board"] == "synth"
    assert len(payload["bom"]) == 1
    row = payload["bom"][0]
    assert row["lcsc"] == "C1000"
    assert row["jlc_status"] == "basic"
    assert row["unit_price"] == 0.01
    assert payload["paths"]["gerber_zip"] == "fab/synth_gerbers.zip"
    assert payload["paths"]["bom"] == "fab/BOM.csv"
    assert payload["paths"]["cpl"] == "fab/CPL.csv"
    assert payload["paths"]["schematic_pdf"] == "reports/schematic.pdf"
    assert payload["paths"]["quote"] == "fab/quote.json"
    assert payload["todo"] == []
    assert payload["parts_cost_per_board"] == 0.01


def test_upload_bom_with_jlc_header_is_read(tmp_path, capsys):
    """No BOM-full.csv: the fallback reads bom_cpl's JLC upload header,
    whose part column is "LCSC Part #", not "LCSC"."""
    ws = make_workspace(tmp_path)
    (ws / "fab" / "BOM-full.csv").unlink()
    (ws / "fab" / "BOM.csv").write_text(
        "Comment,Designator,Footprint,LCSC Part #\n10k,R1,0402,C1000\n",
        encoding="utf-8")
    code, payload = run_main(ws, tmp_path, capsys)
    assert code == 0, payload
    assert payload["bom"][0]["lcsc"] == "C1000"
    assert payload["bom"][0]["jlc_status"] == "basic"


# ------------------------------------------------------------------ missing fab files

def test_missing_fab_files(tmp_path, capsys):
    broken = make_workspace(tmp_path, name="broken", board="broken",
                            with_fab=False)
    code, payload = run_main(broken, tmp_path, capsys, name="broken_out")
    assert code == 1
    assert payload["status"] == "violations"
    assert any("gerber zip" in m for m in payload["missing"])
    assert any("BOM.csv" in m for m in payload["missing"])
    assert any("CPL.csv" in m for m in payload["missing"])

    # a complete sibling workspace built in the same test is unaffected
    complete = make_workspace(tmp_path, name="complete")
    code2, payload2 = run_main(complete, tmp_path, capsys, name="complete_out")
    assert code2 == 0
    assert payload2["status"] == "pass"
    assert payload2["missing"] == []


# ------------------------------------------------------------------ todo, not a violation

def test_missing_quote_and_schematic_is_todo(tmp_path, capsys):
    ws = make_workspace(tmp_path, with_quote=False, with_schematic=False)
    code, payload = run_main(ws, tmp_path, capsys)
    assert code == 0, payload
    assert payload["status"] == "pass"
    assert payload["missing"] == []
    facts = {t["fact"] for t in payload["todo"]}
    assert "cost estimate" in facts
    assert "schematic export" in facts
    assert payload["paths"]["quote"] is None
    assert payload["paths"]["schematic_pdf"] is None


# ------------------------------------------------------------------ error (exit 2)

def test_no_workspace_exit2(tmp_path, capsys):
    code, payload = run_main(tmp_path / "nope", tmp_path, capsys)
    assert code == 2
    assert payload["status"] == "error"
    assert "state.json" in payload["error"]


def test_unreadable_state_exit2(tmp_path, capsys):
    ws = tmp_path / "corrupt"
    ws.mkdir()
    (ws / "state.json").write_text("{not json", encoding="utf-8")
    code, payload = run_main(ws, tmp_path, capsys)
    assert code == 2
    assert payload["status"] == "error"
