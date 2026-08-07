"""Design-document generator acceptance tests (report_gen.py + env.find_pdflatex).

Criteria -> tests:
  - latex_escape is a total function: specials, backslash handled first,
    each mapped non-ASCII char, CJK fallback to '?', pure-ASCII invariant
                                     -> test_escape_* (hermetic)
  - markdown-lite ceiling: headings, nested bullets, inline marks, md tables
    and fences pass through as escaped tt blocks, snake_case never emphasized
                                     -> test_md_* (hermetic)
  - sections conditional on phase (pending stubs, exit 0)
                                     -> test_sections_pending_at_p4
  - due-but-absent core artifact -> missing[] + exit 1
                                     -> test_missing_core_exits_1
  - payload key contract             -> test_payload_keys
  - absent workspace / corrupt state.json -> exit 2
                                     -> test_absent_workspace_exit2,
                                        test_corrupt_state_exit2
  - --tex-only is full success (pdf null, ASCII .tex)
                                     -> test_tex_only_pass
  - pdflatex not installed -> auto tex-only, warning, exit 1
                                     -> test_no_pdflatex_degrades
  - set-but-invalid AIEE_PDFLATEX -> EnvError -> exit 2, .tex still written
                                     -> test_bad_pin_exit2
  - [ ] * brace-wrapped: a line-initial [ after the line-join is a fatal
    "Missing number", item labels swallow [x] content (adversarial F1/F2)
                                     -> test_escape_bracket_star_contexts,
                                        test_bracket_content_never_breaks_latex
  - compile failure/timeout explains itself in warnings (adversarial F5)
                                     -> test_compile_failure_adds_warning
  - env.find_pdflatex override ladder -> test_find_pdflatex_*
  - check_env pdflatex check (warn-level, loud on bad pin)
                                     -> test_check_env_pdflatex_unit
  - real boards produce a real PDF (both render conventions), >= 8 pages via
    pypdf, sections included, zero residue outside reports/design_doc/,
    second run overwrites cleanly    -> test_smoke_* (smoke marker)

Hermetic tests never invoke pdflatex (all synthetic runs are --tex-only or
have discovery monkeypatched/failed), so they pass on TeX-less machines.
"""
from __future__ import annotations

import json
import os
import struct
import subprocess
import sys
import zlib
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / ".claude" / "skills" / "ai-ee" / "scripts"
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(SCRIPTS / "lib"))

import check_env  # noqa: E402
import report_gen  # noqa: E402
from lib import env  # noqa: E402

TS = "2026-07-28T10:00:00"


# ------------------------------------------------------------------ helpers

def run_main(argv, tmp_path, capsys, name="out"):
    """Run report_gen.main() in-process; return (exit_code, payload_dict)."""
    out = tmp_path / f"{name}.json"
    code = report_gen.main([*argv, "--out", str(out)])
    cap = capsys.readouterr()
    if out.exists():
        payload = json.loads(out.read_text(encoding="utf-8"))
    else:
        payload = json.loads(cap.out) if cap.out.strip() else None
    return code, payload


def write_png(path: Path) -> None:
    """A minimal valid 1x1 RGB PNG (no imaging lib needed)."""
    def chunk(tag: bytes, data: bytes) -> bytes:
        return (struct.pack(">I", len(data)) + tag + data
                + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))
    ihdr = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
    idat = zlib.compress(b"\x00\xff\x00\x00")
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
                     + chunk(b"IDAT", idat) + chunk(b"IEND", b""))


def gate_entry(phase: str) -> dict:
    last = {"ts": TS, "status": "pass", "failing_count": 0, "total": 0}
    return {"phase": phase, "status": "pass", "attempts": 1,
            "last": dict(last), "history": [dict(last)]}


BRIEF_MD = """# Brief: synth

Overview paragraph with **bold**, *stars*, _under_, `code_span` and a
[link](https://example.com/x_y). Tolerance \u00b110%, load 4.7\u03a9, cap 1\u00b5F.

- top bullet, rated -40\u2103~+85\u2103
  - nested bullet \u0394T 10\u00b0
- second top bullet

| col_a | col_b |
|-------|-------|
| 1     | 2     |

```
raw & unparsed_stuff ~ ^ 100%
```
"""


def make_workspace(tmp_path: Path, phase: str = "P10",
                   schematic: bool = True) -> Path:
    """Synthetic workspace matching the real state.json schema + artifact
    conventions closely enough to drive every section builder."""
    ws = tmp_path / "synth"
    board = "synth"
    gates = {"erc": gate_entry("P4")}
    if phase in ("P6", "P7", "P8", "P9", "P10", "done"):
        gates.update({"place": gate_entry("P6"), "drc_routed": gate_entry("P7"),
                      "verify": gate_entry("P8"), "dfm": gate_entry("P9")})
    state = {
        "version": 1, "board": board,
        "workspace": str(ws).replace("\\", "/"),
        "created": TS, "updated": TS, "phase": phase,
        "gates": gates,
        "human": {"1": {"status": "approved", "ts": TS,
                        "note": "note & ~caveat_with 100% margin"}},
        "artifacts": {"order": "fab/order.json"},
        "open_issues": [{
            "id": 1, "gate": None, "phase": "P8", "fixer": "review",
            "net": "GND", "kinds": ["current-return", "cu_neck"],
            "severity": "error", "count": 1, "region": None,
            "work_order": None, "status": "fixed", "agent": None,
            "attempts": 0, "opened": TS, "closed": TS}],
        "next_issue_id": 2,
        "budgets": {"fix_loops": {"erc": 3}},
        "decisions": [{"what": "2oz copper & pour_fanin for the 5A path",
                       "why": "IPC-2152 at dT=10; 1oz needs >3.5mm",
                       "phase": "P2", "ts": TS}],
        "history": [{"ts": TS, "event": "init", "board": board, "phase": "P0"}],
    }
    ws.mkdir()
    (ws / "state.json").write_text(json.dumps(state, indent=1), encoding="utf-8")

    (ws / "brief").mkdir()
    (ws / "brief" / "brief.md").write_text(BRIEF_MD, encoding="utf-8")
    (ws / "requirements.md").write_text(
        "# Requirements: synth\n\n## 1. Function\n\nDoes a thing at 5A "
        "\u00b110% with `check_current.required_width_mm` honored.\n",
        encoding="utf-8")
    arch = ws / "architecture"
    arch.mkdir()
    (arch / "stackup.md").write_text(
        "# synth - stackup\n\n## Chosen: `SYN2313_1.6_2oz` (2-layer, 2 oz)\n",
        encoding="utf-8")
    (arch / "sheets.md").write_text(
        "# synth - sheet plan\n\n| Sheet | File |\n|---|---|\n| root | x |\n",
        encoding="utf-8")
    for n in ("blocks.md", "decisions.md", "power_tree.md"):
        (arch / n).write_text(f"# {n}\n\ncontent\n", encoding="utf-8")

    log = ws / "log"
    log.mkdir()
    top = {"P4": 4, "P10": 10}.get(phase, 10)
    for i in range(0, top + 1):
        (log / f"P{i}-digest.md").write_text(
            f"# P{i} digest (synth)\nDid work with \u00b12% margins & "
            "100% coverage_of the plan.\n", encoding="utf-8")

    rep = ws / "reports"
    rep.mkdir()
    (rep / "erc-waivers.md").write_text(
        "# Schematic review waivers (synth)\n\nW1 range: -40\u2103~+85\u2103 "
        "accepted; see notes_x.\n", encoding="utf-8")
    if schematic:
        (rep / "schematic.pdf").write_bytes(b"%PDF-1.4\n%%EOF\n")
    rf = rep / "render_final"
    rf.mkdir()
    write_png(rf / "top.png")
    write_png(rf / "bottom.png")
    (rep / "review-board.md").write_text(
        "# Board review (synth)\n\nVerdict: fine.\n\n### E1 - a finding\n\n"
        "Detail with `check_current.required_width_mm` and 50% margin.\n",
        encoding="utf-8")
    (rep / "verify_all.json").write_text(json.dumps({
        "script": "verify_all", "board": "synth.kicad_pcb", "status": "pass",
        "counts": {"total": 0},
        "checks": {
            "check_silk": {"status": "pass", "counts": {"total": 0},
                           "report": None, "reason": None},
            "check_current": {"status": "skipped", "counts": {"total": 0},
                              "report": None, "reason": "no constraints"}},
        "violations": []}), encoding="utf-8")
    (rep / "bom_cpl.json").write_text(json.dumps({
        "script": "bom_cpl", "status": "pass", "bom_rows": [
            {"Comment": "10uF \u00b110%", "Designator": "C1A,C1B",
             "Footprint": "ESSOP-10_L4.9-W3.9-P1.0-LS6.0-TL-EP",
             "LCSC": "C13585"},
            {"Comment": "-40\u2103~+85\u2103 \u6df1\u5733",
             "Designator": "U1",
             "Footprint": "F.0603.00011/P2-0603R4TS2-06T-001",
             "LCSC": "C970725"}],
        "n_rotation_corrections": 2, "missing_lcsc": []}), encoding="utf-8")
    (rep / "fab_export.json").write_text(json.dumps({
        "script": "fab_export", "status": "pass",
        "layers_exported": ["F.Cu", "B.Cu", "Edge.Cuts"]}), encoding="utf-8")
    (rep / "gate-dfm.json").write_text(json.dumps({
        "script": "gate", "gate": "dfm", "status": "pass",
        "counts": {"total": 3, "by_severity": {"warning": 3}}}),
        encoding="utf-8")

    fab = ws / "fab"
    fab.mkdir()
    (fab / "order.json").write_text(json.dumps({
        "script": "order_submit", "status": "ready_for_human",
        "board": "synth.kicad_pcb",
        "spec_snapshot": {"layers": 2, "width_mm": 30.0, "height_mm": 20.0,
                          "qty": 10, "surface_finish": "HASL",
                          "solder_mask_color": "green", "assembly": True},
        "quote": {"selected": {"qty": 10, "total": 12.34, "unit_cost": 1.23},
                  "estimated": True,
                  "source": "boards\\synth\\fab\\quote.json"},
        "artifacts": {"gerber_zip": {
            "path": "boards\\synth\\fab\\synth_gerbers.zip",
            "sha256": "abcd" * 16, "bytes": 1}},
        "human_steps": [
            "Select 2oz copper ~ mandatory (\u00b10 tolerance on this)",
            "Upload boards\\synth\\fab\\synth_gerbers.zip to jlcdfm.com"]}),
        encoding="utf-8")
    return ws


def sections_by_name(payload: dict) -> dict:
    return {s["name"]: s["status"] for s in payload["sections"]}


# ------------------------------------------------------------------ latex_escape

def test_escape_specials():
    esc = report_gen.latex_escape
    assert esc("&") == r"\&" and esc("%") == r"\%" and esc("$") == r"\$"
    assert esc("#") == r"\#" and esc("_") == r"\_"
    assert esc("{") == r"\{" and esc("}") == r"\}"
    assert esc("~") == r"\textasciitilde{}"
    assert esc("^") == r"\textasciicircum{}"
    # OT1 text mode renders raw < > | as inverted punctuation / em-dash
    assert esc("->") == r"-\textgreater{}"
    assert esc("<") == r"\textless{}"
    assert esc("|") == r"\textbar{}"


def test_escape_backslash_first():
    esc = report_gen.latex_escape
    assert esc("\\") == r"\textbackslash{}"
    # the braces introduced FOR the backslash must not get re-escaped
    assert esc("a\\b") == r"a\textbackslash{}b"
    assert esc("\\&") == r"\textbackslash{}\&"
    assert esc("boards\\pd-trigger\\fab\\x.zip") == \
        r"boards\textbackslash{}pd-trigger\textbackslash{}fab\textbackslash{}x.zip"


def test_escape_unicode_map():
    esc = report_gen.latex_escape
    assert esc("\u00b1") == r"\(\pm\)"
    assert esc("\u03a9") == r"\(\Omega\)"
    assert esc("\u00b5") == r"\(\mu\)"      # micro sign U+00B5
    assert esc("\u03bc") == r"\(\mu\)"      # greek mu U+03BC
    assert esc("\u2103") == r"\(^{\circ}\)C"  # single-glyph degree C
    assert esc("\u00b0") == r"\(^{\circ}\)"
    assert esc("\u2022") == r"\textbullet{}"
    assert esc("\u0394") == r"\(\Delta\)"
    assert esc("\u00d8") == "dia. "


def test_escape_cjk_fallback():
    assert report_gen.latex_escape("\u6df1\u5733\u5e02") == "???"


def test_escape_corpus_torture():
    esc = report_gen.latex_escape
    assert esc("unconnected-(U1-PC15-OSC32_OUT-Pad4)") == \
        r"unconnected-(U1-PC15-OSC32\_OUT-Pad4)"
    assert esc("ESSOP-10_L4.9-W3.9-P1.0-LS6.0-TL-EP") == \
        r"ESSOP-10\_L4.9-W3.9-P1.0-LS6.0-TL-EP"
    # non-ASCII glyph + active ~ in ONE attribute string
    assert esc("-40\u2103~+85\u2103") == \
        r"-40\(^{\circ}\)C\textasciitilde{}+85\(^{\circ}\)C"
    assert esc("F.0603.00011/P2-0603R4TS2-06T-001") == \
        "F.0603.00011/P2-0603R4TS2-06T-001"


def test_escape_bracket_star_contexts():
    """F1/F2: [ ] * are context-sensitive after \\\\ (optional arg / no-break
    star) and inside \\item (label); brace-wrapping is literal everywhere."""
    esc = report_gen.latex_escape
    assert esc("[ok] verified") == "{[}ok{]} verified"
    assert esc("[NRND] 22uF") == "{[}NRND{]} 22uF"
    assert esc("a[5mm]b") == "a{[}5mm{]}b"
    assert esc("*caveat*") == "{*}caveat{*}"


def test_escape_ascii_invariant():
    probe = ("".join(chr(i) for i in range(1, 0x300))
             + "\u2103\u2126\u6df1\u5733 mixed & _ ~ \\ text")
    out = report_gen.latex_escape(probe)
    assert all(ord(c) < 128 for c in out)
    assert report_gen.latex_escape(None) == ""
    assert report_gen.latex_escape(42) == "42"


# ------------------------------------------------------------------ markdown-lite

def test_md_headings():
    tex = report_gen.md_to_latex("# A\n\n## B\n\n### C\n")
    assert r"\subsection*{A}" in tex
    assert r"\subsubsection*{B}" in tex
    assert r"\paragraph*{C}" in tex


def test_md_bullets_nested():
    tex = report_gen.md_to_latex("- a\n  - b\n- c\n\npara\n")
    assert tex.count(r"\begin{itemize}") == 2
    assert tex.count(r"\end{itemize}") == 2
    assert tex.count(r"\item") == 3
    # lists closed before the trailing paragraph
    assert tex.rindex(r"\end{itemize}") < tex.rindex("para")


def test_md_inline():
    tex = report_gen.md_to_latex(
        "**bold** *star* _under_ `code_x` [txt](http://u/p_q)")
    assert r"\textbf{bold}" in tex
    assert r"\emph{star}" in tex
    assert r"\emph{under}" in tex
    assert r"\texttt{code\_x}" in tex
    assert r"txt (\texttt{http://u/p\_q})" in tex


def test_md_snake_case_not_emphasized():
    tex = report_gen.md_to_latex(
        "state_snapshots and check_current.required_width_mm stay plain")
    assert r"\emph" not in tex
    assert r"state\_snapshots" in tex


def test_md_table_passthrough():
    tex = report_gen.md_to_latex("| col_a | col_b |\n|---|---|\n| 1 | 2 |\n")
    assert r"\ttfamily" in tex          # rendered as tt block
    assert r"\begin{tabular}" not in tex  # never parsed into a table
    assert r"col\_a" in tex             # content escaped


def test_md_fence_passthrough():
    tex = report_gen.md_to_latex("```\nraw & stuff_here ~\n```\n")
    assert r"\ttfamily" in tex
    assert r"raw \& stuff\_here \textasciitilde{}" in tex


# ------------------------------------------------------------------ synthetic runs

def test_tex_only_pass(tmp_path, capsys):
    ws = make_workspace(tmp_path)
    code, payload = run_main(["--workspace", str(ws), "--tex-only"],
                             tmp_path, capsys)
    assert code == 0, payload
    assert payload["status"] == "pass"
    assert payload["pdf"] is None and payload["pages"] is None
    assert payload["compile"] is None
    assert payload["missing"] == []
    tex = ws / payload["tex"]
    assert tex.is_file()
    text = tex.read_text(encoding="utf-8")
    assert all(ord(c) < 128 for c in text)          # hard ASCII invariant
    assert r"\(\pm\)" in text                       # torture survived escaped
    assert "??" in text                             # CJK fell back
    assert "skipped - no constraints" in text       # honest skip reason
    assert r"ESSOP-10\_L4.9-W3.9-P1.0-LS6.0-TL-EP" in text
    assert r"\includepdf[pages=-]{reports/schematic.pdf}" in text
    assert "reports/render_final/top.png" in text
    assert "SYN2313" in text                        # stackup Chosen line
    assert sections_by_name(payload) == {
        s: "included" for s in ("title", "overview", "requirements",
                                "architecture", "schematic", "layout",
                                "verification", "dfm_fab", "run_record",
                                "artifact_index")}


def test_sections_pending_at_p4(tmp_path, capsys):
    ws = make_workspace(tmp_path, phase="P4", schematic=False)
    code, payload = run_main(["--workspace", str(ws), "--tex-only"],
                             tmp_path, capsys)
    assert code == 0, payload         # nothing hard-due yet -> pass
    assert payload["missing"] == []
    by_name = sections_by_name(payload)
    assert by_name["layout"] == "pending"
    assert by_name["verification"] == "pending"
    assert by_name["dfm_fab"] == "pending"
    assert by_name["requirements"] == "included"
    assert by_name["architecture"] == "included"
    text = (ws / payload["tex"]).read_text(encoding="utf-8")
    assert "Pending --- produced at P6" in text


def test_missing_core_exits_1(tmp_path, capsys):
    ws = make_workspace(tmp_path, phase="P10", schematic=False)
    code, payload = run_main(["--workspace", str(ws), "--tex-only"],
                             tmp_path, capsys)
    assert code == 1
    assert payload["status"] == "violations"
    assert "reports/schematic.pdf" in payload["missing"]
    assert sections_by_name(payload)["schematic"] == "missing"
    assert (ws / payload["tex"]).is_file()   # doc still produced


def test_payload_keys(tmp_path, capsys):
    ws = make_workspace(tmp_path)
    _, payload = run_main(["--workspace", str(ws), "--tex-only"],
                          tmp_path, capsys)
    assert list(payload) == ["script", "status", "board", "workspace", "tex",
                             "pdf", "pages", "sections", "missing", "warnings",
                             "compile"]
    assert payload["script"] == "report_gen"
    assert payload["board"] == "synth"
    assert all(set(s) == {"name", "status", "source"}
               for s in payload["sections"])


def test_absent_workspace_exit2(tmp_path, capsys):
    code, payload = run_main(["--workspace", str(tmp_path / "nope"),
                              "--tex-only"], tmp_path, capsys)
    assert code == 2
    assert payload["status"] == "error"
    assert "state.json" in payload["error"]


def test_corrupt_state_exit2(tmp_path, capsys):
    ws = tmp_path / "corrupt"
    ws.mkdir()
    (ws / "state.json").write_text("{not json", encoding="utf-8")
    code, payload = run_main(["--workspace", str(ws), "--tex-only"],
                             tmp_path, capsys)
    assert code == 2
    assert payload["status"] == "error"


def test_no_pdflatex_degrades(tmp_path, capsys, monkeypatch):
    ws = make_workspace(tmp_path)
    monkeypatch.setattr(report_gen.env, "find_pdflatex", lambda: None)
    code, payload = run_main(["--workspace", str(ws)], tmp_path, capsys)
    assert code == 1
    assert payload["status"] == "violations"
    assert payload["pdf"] is None and payload["compile"] is None
    assert any("pdflatex" in w for w in payload["warnings"])
    assert (ws / payload["tex"]).is_file()   # tex still written


def test_bad_pin_exit2(tmp_path):
    ws = make_workspace(tmp_path)
    e = dict(os.environ)
    e["AIEE_PDFLATEX"] = r"C:\nonexistent\pdflatex.exe"
    r = subprocess.run(
        [sys.executable, str(SCRIPTS / "report_gen.py"),
         "--workspace", str(ws)],
        capture_output=True, text=True, env=e, timeout=120, cwd=str(REPO))
    assert r.returncode == 2, r.stdout + r.stderr
    payload = json.loads(r.stdout)
    assert payload["status"] == "error"
    assert "AIEE_PDFLATEX" in payload["error"]
    # F4: the loud exit must not discard the already-built document
    assert (ws / "reports" / "design_doc" / "synth-design-doc.tex").is_file()


def test_bracket_content_never_breaks_latex(tmp_path, capsys):
    """F1/F2 regression: [-initial digest lines, [NRND] BOM comments,
    task-list bullets and [optional] human_steps survive brace-wrapped."""
    ws = make_workspace(tmp_path)
    (ws / "log" / "P8-digest.md").write_text(
        "# P8 digest (synth)\n[ok] verified all rails\n*starred caveat*\n",
        encoding="utf-8")
    bom = json.loads((ws / "reports" / "bom_cpl.json")
                     .read_text(encoding="utf-8"))
    bom["bom_rows"][0]["Comment"] = "[NRND] 22uF low-ESR"
    (ws / "reports" / "bom_cpl.json").write_text(json.dumps(bom),
                                                 encoding="utf-8")
    order = json.loads((ws / "fab" / "order.json").read_text(encoding="utf-8"))
    order["human_steps"].insert(0, "[optional] flag the assembly side")
    (ws / "fab" / "order.json").write_text(json.dumps(order), encoding="utf-8")
    (ws / "brief" / "brief.md").write_text(
        "# Brief: synth\n\n- [x] shipped\n- [ ] pending\n", encoding="utf-8")
    code, payload = run_main(["--workspace", str(ws), "--tex-only"],
                             tmp_path, capsys)
    assert code == 0, payload
    text = (ws / payload["tex"]).read_text(encoding="utf-8")
    assert "{[}ok{]} verified all rails" in text
    assert "{[}NRND{]} 22uF low-ESR" in text
    assert r"\item {[}optional{]}" in text
    assert r"\item {[}x{]} shipped" in text
    # the fatal/swallowing raw forms must not exist anywhere
    assert "\\\\\n[" not in text and "\\\\\n*" not in text
    assert "\\item [" not in text


def test_requirements_fallback_architecture(tmp_path, capsys):
    """T6 reportgen-fallback: an off-root requirements.md (the shipped
    carrier escape) is included via the architecture/ fallback with a
    visible warning, never a 'not found' stub."""
    ws = make_workspace(tmp_path)
    body = (ws / "requirements.md").read_text(encoding="utf-8")
    (ws / "requirements.md").unlink()
    (ws / "architecture" / "requirements.md").write_text(body,
                                                         encoding="utf-8")
    code, payload = run_main(["--workspace", str(ws), "--tex-only"],
                             tmp_path, capsys)
    assert code == 0, payload
    by_name = {s["name"]: s for s in payload["sections"]}
    assert by_name["requirements"]["status"] == "included"
    assert by_name["requirements"]["source"] == "architecture/requirements.md"
    assert any("not workspace root" in w for w in payload["warnings"])
    text = (ws / payload["tex"]).read_text(encoding="utf-8")
    assert "Does a thing at 5A" in text          # the real body, not a stub
    assert "requirements.md not found" not in text


def test_requirements_registry_path_wins(tmp_path, capsys):
    """The artifacts registry outranks the path ladder; a registry entry at
    the root stays warning-free."""
    ws = make_workspace(tmp_path)
    (ws / "docs").mkdir()
    (ws / "requirements.md").rename(ws / "docs" / "req.md")
    state = json.loads((ws / "state.json").read_text(encoding="utf-8"))
    state["artifacts"]["requirements"] = "docs/req.md"
    (ws / "state.json").write_text(json.dumps(state, indent=1),
                                   encoding="utf-8")
    code, payload = run_main(["--workspace", str(ws), "--tex-only"],
                             tmp_path, capsys)
    assert code == 0, payload
    by_name = {s["name"]: s for s in payload["sections"]}
    assert by_name["requirements"]["source"] == "docs/req.md"
    assert any("not workspace root" in w for w in payload["warnings"])
    # registry pointing at the root -> no warning (root is the contract)
    state["artifacts"]["requirements"] = "requirements.md"
    (ws / "state.json").write_text(json.dumps(state, indent=1),
                                   encoding="utf-8")
    (ws / "docs" / "req.md").rename(ws / "requirements.md")
    code, payload = run_main(["--workspace", str(ws), "--tex-only"],
                             tmp_path, capsys, name="out2")
    assert code == 0, payload
    assert not any("not workspace root" in w for w in payload["warnings"])


def test_compile_failure_adds_warning(tmp_path, capsys, monkeypatch):
    """F5: a failed or timed-out compile must explain itself in warnings."""
    ws = make_workspace(tmp_path)
    fake = tmp_path / "pdflatex.exe"
    fake.write_bytes(b"x")
    monkeypatch.setattr(report_gen.env, "find_pdflatex", lambda: fake)
    monkeypatch.setattr(
        report_gen, "compile_pdf",
        lambda p, w, n: ({"engine": str(p), "rc": 1, "passes": 1,
                          "seconds": 0.1, "latex_log_tail": "boom"}, None))
    code, payload = run_main(["--workspace", str(ws)], tmp_path, capsys)
    assert code == 1 and payload["status"] == "violations"
    assert any("pdflatex failed" in w for w in payload["warnings"])

    monkeypatch.setattr(
        report_gen, "compile_pdf",
        lambda p, w, n: ({"engine": str(p), "rc": 124, "passes": 1,
                          "seconds": 0.1, "timed_out": True}, None))
    code2, payload2 = run_main(["--workspace", str(ws)], tmp_path, capsys,
                               name="out2")
    assert code2 == 1
    assert any("timed out" in w for w in payload2["warnings"])


# ------------------------------------------------------------------ find_pdflatex

def test_find_pdflatex_pin(monkeypatch, tmp_path):
    exe = tmp_path / "pdflatex.exe"
    exe.write_bytes(b"x")
    monkeypatch.setenv("AIEE_PDFLATEX", str(exe))
    assert env.find_pdflatex() == exe


def test_find_pdflatex_pin_invalid(monkeypatch):
    monkeypatch.setenv("AIEE_PDFLATEX", r"C:\nonexistent\pdflatex.exe")
    with pytest.raises(env.EnvError, match="AIEE_PDFLATEX does not exist"):
        env.find_pdflatex()


def test_find_pdflatex_path(monkeypatch, tmp_path):
    exe = tmp_path / "pdflatex.EXE"        # PATH hits may be uppercase
    exe.write_bytes(b"x")
    monkeypatch.delenv("AIEE_PDFLATEX", raising=False)
    monkeypatch.setattr(env.shutil, "which", lambda name: str(exe))
    assert env.find_pdflatex() == exe


def test_find_pdflatex_none(monkeypatch, tmp_path):
    monkeypatch.delenv("AIEE_PDFLATEX", raising=False)
    monkeypatch.setattr(env.shutil, "which", lambda name: None)
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))   # no MiKTeX inside
    assert env.find_pdflatex() is None


@pytest.mark.skipif(sys.platform != "win32", reason="windows default location")
def test_find_pdflatex_miktex_default(monkeypatch, tmp_path):
    exe = tmp_path / "Programs" / "MiKTeX" / "miktex" / "bin" / "x64" / "pdflatex.exe"
    exe.parent.mkdir(parents=True)
    exe.write_bytes(b"x")
    monkeypatch.delenv("AIEE_PDFLATEX", raising=False)
    monkeypatch.setattr(env.shutil, "which", lambda name: None)
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    assert env.find_pdflatex() == exe


def test_check_env_pdflatex_unit(monkeypatch):
    # F3: hermetic against an ambient AIEE_PDFLATEX pin in the caller's env
    monkeypatch.delenv("AIEE_PDFLATEX", raising=False)
    resolved: dict = {}
    c = check_env.check_pdflatex(resolved)
    assert c["name"] == "pdflatex"
    assert c["status"] in ("pass", "warn")     # never a hard fail when absent

    monkeypatch.setattr(check_env.env, "find_pdflatex", lambda: None)
    c_absent = check_env.check_pdflatex({})
    assert c_absent["status"] == "warn"        # absent branch, deterministic
    assert "AIEE_PDFLATEX" in c_absent["remediation"]

    def raiser():
        raise env.EnvError("AIEE_PDFLATEX does not exist: bad")
    monkeypatch.setattr(check_env.env, "find_pdflatex", raiser)
    c2 = check_env.check_pdflatex({})
    assert c2["status"] == "fail"              # bad pin fails loudly
    assert "AIEE_PDFLATEX" in c2["detail"]


# ------------------------------------------------------------------ smoke

@pytest.fixture(scope="session")
def pdflatex_bin():
    try:
        p = env.find_pdflatex()
    except env.EnvError:
        p = None
    if p is None:
        pytest.skip("pdflatex not installed")
    return p


def git_status_lines(scope: str) -> set[str]:
    """Porcelain lines SCOPED to the workspace under test (ladder row 92 /
    LEARNINGS 2026-07-28 [testing][windows]): a global diff makes any
    concurrent session's dirty file - or a stray repo-root file - fail the
    litter assertion falsely. The assertion keeps full power within scope."""
    r = subprocess.run(["git", "-C", str(REPO), "status", "--porcelain",
                        "--", scope],
                       capture_output=True, text=True, timeout=60)
    return {ln for ln in r.stdout.splitlines() if ln.strip()}


def run_cli(workspace_rel: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPTS / "report_gen.py"),
         "--workspace", workspace_rel],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        timeout=280, cwd=str(REPO))


def assert_real_run(r: subprocess.CompletedProcess, board: str) -> dict:
    assert r.returncode == 0, (r.stdout or "")[-2500:] + (r.stderr or "")[-500:]
    payload = json.loads(r.stdout)
    assert payload["status"] == "pass"
    assert payload["compile"]["rc"] == 0 and payload["compile"]["passes"] == 2
    pdf = REPO / "boards" / board / payload["pdf"]
    assert pdf.is_file() and pdf.stat().st_size > 0
    assert payload["pages"] >= 8
    from pypdf import PdfReader                      # independent recount
    assert len(PdfReader(str(pdf)).pages) == payload["pages"]
    by_name = {s["name"]: s for s in payload["sections"]}
    for sec in ("schematic", "layout", "verification", "dfm_fab"):
        assert by_name[sec]["status"] == "included", by_name[sec]
    return payload


@pytest.mark.smoke
def test_smoke_pd_trigger_with_residue_and_rerun(pdflatex_bin):
    """render_final/{top,bottom}.png convention + full pipeline data."""
    before = git_status_lines("boards/pd-trigger")
    payload = assert_real_run(run_cli("boards/pd-trigger"), "pd-trigger")
    assert "render_final/top.png" in json.dumps(payload["sections"])
    # second run must overwrite cleanly
    assert_real_run(run_cli("boards/pd-trigger"), "pd-trigger")
    # residue: nothing new outside reports/design_doc/, no tracked file touched
    new = git_status_lines("boards/pd-trigger") - before
    assert all(ln.startswith("?? ") and "/reports/design_doc/" in ln
               for ln in new), sorted(new)


@pytest.mark.smoke
def test_smoke_stm32_blinky(pdflatex_bin):
    """renders/<board>_{top,bottom,iso}.png convention + labeled + layers."""
    before = git_status_lines("boards/stm32-blinky")
    payload = assert_real_run(run_cli("boards/stm32-blinky"), "stm32-blinky")
    src = json.dumps(payload["sections"])
    assert "renders/stm32-blinky_top.png" in src
    assert "render_labeled/stm32-blinky_top.png" in src
    new = git_status_lines("boards/stm32-blinky") - before
    assert all(ln.startswith("?? ") and "/reports/design_doc/" in ln
               for ln in new), sorted(new)
