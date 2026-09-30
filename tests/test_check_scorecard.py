"""Per-check scorecard (score_checks.py): the feedback gate plus its pieces.

  - test_no_check_regressed: the gate. Scores the golden + mutant corpora and
    fails when any check's false positives or misses rose above the last
    line of docs/check-scorecard.jsonl (the committed baseline).
  - test_every_check_has_recall: every verify check owns a planted fault.
  - the rest pin the matching, triage, comparison and recording rules on
    fixtures of their own. The boards corpus is never needed here.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / ".claude" / "skills" / "hwde" / "scripts"
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(SCRIPTS / "lib"))
import checklib  # noqa: E402
import score_checks as sc  # noqa: E402


@pytest.fixture(scope="module")
def scored(tmp_path_factory):
    out = tmp_path_factory.mktemp("score") / "score.json"
    rc = sc.main(["--corpora", "golden,mutants", "--compare",
                  "--out", str(out)])
    return rc, json.loads(out.read_text(encoding="utf-8"))


# ------------------------------------------------------------ the gate

def test_no_check_regressed(scored):
    rc, payload = scored
    assert payload["baseline"], "docs/check-scorecard.jsonl has no baseline"
    assert payload["regressions"] == [], json.dumps(
        {"regressions": payload["regressions"],
         "findings": payload["findings"]}, indent=1)
    assert rc == 0


def test_every_check_has_recall(scored):
    _, payload = scored
    missing = [n for n, c in payload["checks"].items() if c["recall"] is None]
    assert missing == [], f"no planted fault exercises {missing}"


def test_scored_every_verify_check(scored):
    _, payload = scored
    assert list(payload["checks"]) == sc.CHECK_NAMES
    assert payload["corpora"]["boards"]["status"] == "skipped"


# ------------------------------------------------------------ matching

def test_catches_needs_every_expect_key():
    v = {"kind": "silk_over_pad", "net": None, "refs": ["D1"],
         "pos": [132.4, 129.5], "layer": "F.SilkS"}
    assert sc.catches({"ref": "D1", "pos": [132.44, 129.5]}, v)
    assert sc.catches({"kind": "silk_over_pad", "ref": "D1"}, v)
    assert not sc.catches({"ref": "D2"}, v)
    assert not sc.catches({"ref": "D1", "pos": [140.0, 129.5]}, v)
    assert not sc.catches({"kind": "silk_misattributed", "ref": "D1"}, v)
    assert sc.catches({"pair": ["/B", "/A"]}, {"pair": ["/A", "/B"]})
    assert not sc.catches({"pair": ["/A", "/C"]}, {"pair": ["/A", "/B"]})


def test_triage_entry_scoping():
    t = {"board": "b", "check": "check_pdn", "kind": "pdn_undecoupled",
         "net": "GND", "verdict": "fp", "reason": "r"}
    hit = {"kind": "pdn_undecoupled", "net": "GND", "refs": []}
    assert sc.triage_matches(t, "check_pdn", hit)
    assert not sc.triage_matches(t, "check_silk", hit)
    assert not sc.triage_matches(t, "check_pdn", {**hit, "net": "+3V3"})
    scoped = {**t, "refs": ["C1"]}
    assert sc.triage_matches(scoped, "check_pdn", {**hit, "refs": ["C1"]})
    # a refs-scoped entry never matches a refs-less finding
    assert not sc.triage_matches(scoped, "check_pdn", hit)


def test_triage_file_validated(tmp_path):
    p = tmp_path / "t.yaml"
    p.write_text("entries:\n  - {board: b, check: c, kind: k, verdict: fp}\n",
                 encoding="utf-8")
    with pytest.raises(checklib.CheckError):
        sc.load_triage(p)
    p.write_text("entries:\n  - {board: b, check: c, kind: k, verdict: fp,"
                 " reason: why}\n", encoding="utf-8")
    assert len(sc.load_triage(p)) == 1


def test_committed_triage_loads():
    assert sc.load_triage(sc.TRIAGE)


# ------------------------------------------------------------ comparison

def _line(fp: int, misses: int, boards: str = "scored") -> dict:
    cell = {"fp": fp, "misses": misses, "untriaged": 0}
    return {"date": "2026-09-29",
            "corpora": {"golden": "scored", "mutants": "scored",
                        "boards": boards},
            "checks": {"check_x": {"fp": fp, "tp": 1, "caught": 1,
                                   "misses": misses, "precision": None,
                                   "recall": None,
                                   "by_corpus": {"golden": cell,
                                                 "mutants": cell,
                                                 "boards": cell}}}}


def test_regressions_rise_only():
    assert sc.regressions(_line(1, 1), _line(1, 1)) == []
    assert sc.regressions(_line(0, 0), _line(1, 1)) == []    # better
    regs = sc.regressions(_line(2, 1), _line(1, 1))
    assert {(r["corpus"], r["metric"]) for r in regs} == \
        {("golden", "fp"), ("mutants", "fp"), ("boards", "fp")}
    assert sc.regressions(_line(5, 5), None) == []            # no baseline


def test_regressions_skip_a_corpus_either_run_skipped():
    regs = sc.regressions(_line(2, 1, boards="skipped"), _line(1, 1))
    assert "boards" not in {r["corpus"] for r in regs}
    assert regs                                  # golden/mutants still count


def test_regressions_ignore_a_check_new_to_the_baseline():
    now = _line(3, 3)
    now["checks"]["check_new"] = now["checks"].pop("check_x")
    assert sc.regressions(now, _line(0, 0)) == []


def test_record_appends_and_rewrites_doc(tmp_path):
    hist, doc = tmp_path / "h.jsonl", tmp_path / "d.md"
    doc.write_text(f"intro\n{sc.DOC_BEGIN}\nSTALE\n{sc.DOC_END}\n## Open\nkept\n",
                   encoding="utf-8")
    for line in (_line(1, 1), _line(0, 1)):
        with hist.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(line) + "\n")
    sc.write_doc(doc, hist)
    text = doc.read_text(encoding="utf-8")
    assert "STALE" not in text and text.endswith("## Open\nkept\n")
    assert "| check_x | 0 | 1 | 1 | - | - | fp 1->0 |" in text
    assert sc.last_record(hist)["checks"]["check_x"]["fp"] == 0


def test_cli_error_is_exit_2(capsys):
    assert sc.main(["--corpora", "nonsense"]) == 2
    assert json.loads(capsys.readouterr().out)["status"] == "error"


# ------------------------------------------------------------ regression
# fixtures for false positives the scorecard found (docs/check-scorecard.md)

def test_pdn_skips_a_return_net_but_not_a_bare_rail(tmp_path):
    """check_pdn flagged GND, listed under power for its return current, as
    an undecoupled rail on three finished boards. A ground net is skipped;
    a real rail with no caps is still an error."""
    import check_pdn
    golden = REPO / "tests" / "golden" / "blinky2"
    cons = tmp_path / "constraints.json"
    cons.write_text(json.dumps({"power": [
        {"net": "GND", "current_a": 1.0},
        {"net": "+5V", "current_a": 0.5}]}), encoding="utf-8")
    dec = tmp_path / "decoupling.json"
    dec.write_text(json.dumps({"associations": []}), encoding="utf-8")
    payload, _ = check_pdn.run(["--pcb", str(golden / "blinky2.kicad_pcb"),
                                "--constraints", str(cons),
                                "--decoupling", str(dec)])
    flagged = {v["net"] for v in payload["violations"]
               if v["kind"] == "pdn_undecoupled"}
    assert flagged == {"+5V"}
    assert {"rail": "GND", "current_a": 1.0,
            "skipped": "return net: decoupled to, not on"} in payload["checked"]
