"""U6 - workspace learnings, the promotion queue, and the promotion pass.

Four contracts are pinned here:
  1. Compile is deterministic and IDEMPOTENT: the same file gives the same
     ids, a re-compile never loses a ruling, and an entry that disappears is
     reported rather than silently dropped.
  2. A ruling is real: promoted means an artifact that EXISTS was written, and
     both promotion and decline carry a kind plus a reason. The queue is the
     record, so a resolution that cannot be read back is not a resolution.
  3. A root promotion moves the entry AND its triage row together - the two
     files the suite checks against each other are never hand-copied.
  4. rf-de-20m's 66-entry backlog is processed end to end (the U6 acceptance):
     every entry promoted or explicitly declined, and the queue lints clean.
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / ".claude" / "skills" / "hwde"
SCRIPTS = SKILL / "scripts"
RECIPES = SKILL / "reference" / "recipes"
RF_DE = ROOT / "boards" / "rf-de-20m"

sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(SCRIPTS / "lib"))

import learnings as cli  # noqa: E402
import learnlib  # noqa: E402

ENTRY_A = """## 2026-08-14 [P6][placement] Locking an anchor orphans its group

Measured on the fixture: scripts/place_seed.py reported 4 clusters of 6.
"""
ENTRY_B = """## 2026-08-14 [P8][check_current] pour_neck only samples where vias land

The bus bottleneck was never measured; scripts/check_current.py flagged a stub.
"""
ENTRY_C = """## 2026-08-15 [P9][fab] A tented via inside a pad opening is still bare

Nothing here names a script, so the target list stays empty.
"""


def _ws(tmp_path: Path, *entries: str, board: str = "golden") -> Path:
    ws = tmp_path / board
    ws.mkdir(parents=True, exist_ok=True)
    (ws / "LEARNINGS.md").write_text(
        f"# LEARNINGS - {board} (a golden workspace)\n\n"
        "## PROMOTION QUEUE\n\nPreamble sections are allowed up here.\n\n"
        + "\n".join(entries), encoding="utf-8", newline="\n")
    return ws


def _run(argv: list[str], capsys) -> tuple[int, dict]:
    code = cli.main(argv)
    return code, json.loads(capsys.readouterr().out)


# ---------------------------------------------------------------------------
# 1. compile: deterministic, idempotent, honest about drift
# ---------------------------------------------------------------------------
def test_compile_builds_a_queue_from_injected_entries(tmp_path, capsys):
    """The plan's golden-workspace dry run."""
    ws = _ws(tmp_path, ENTRY_A, ENTRY_B, ENTRY_C)
    code, payload = _run(["compile", "--workspace", str(ws)], capsys)
    assert code == 0, payload
    assert payload["entries"] == 3 and len(payload["added"]) == 3
    assert payload["counts"]["pending"] == 3

    queue = yaml.safe_load(
        (ws / "learnings" / "queue.yaml").read_text(encoding="utf-8"))
    rows = {r["entry"]: r for r in queue["entries"]}
    a = rows["2026-08-14-locking-an-anchor-orphans-its-group"]
    assert a["stage"] == "P6" and a["tags"] == ["P6", "placement"]
    assert a["targets"] == ["scripts/place_seed.py"]
    assert a["status"] == "pending" and a["proposed_level"] is None
    # a heading that names no artifact gets an empty target list, not a guess
    assert rows["2026-08-15-a-tented-via-inside-a-pad-opening"]["targets"] == []


def test_preamble_headings_are_allowed_but_later_ones_must_parse(tmp_path,
                                                                 capsys):
    ws = _ws(tmp_path, ENTRY_A, "## not a dated entry\n\nbody\n")
    code, payload = _run(["compile", "--workspace", str(ws)], capsys)
    assert code == 1
    assert any("not a dated entry" in m for m in payload["malformed"])
    # the preamble heading above the first entry did NOT count as malformed
    assert len(payload["malformed"]) == 1


def test_recompile_preserves_rulings_and_refreshes_drift(tmp_path, capsys):
    ws = _ws(tmp_path, ENTRY_A, ENTRY_B)
    _run(["compile", "--workspace", str(ws)], capsys)
    ruled_id = "2026-08-14-pour-neck-only-samples-where-vias-land"
    was = {r["entry"]: r["line"] for r in learnlib.load_queue(ws)["entries"]}
    code, _ = _run(["resolve", "--workspace", str(ws), "--entry", ruled_id,
                    "--status", "declined", "--kind", "board_local",
                    "--reason", "this fixture is not a real board"], capsys)
    assert code == 0

    # the file is edited where it hurts: a new entry BEFORE the ruled one, so
    # every later line number moves. Ids are what survive that, not lines.
    _ws(tmp_path, ENTRY_A, ENTRY_C, ENTRY_B)
    code, payload = _run(["compile", "--workspace", str(ws)], capsys)
    assert code == 0
    assert payload["counts"] == {"pending": 2, "promoted": 0, "declined": 1}
    assert payload["added"] == ["2026-08-15-a-tented-via-inside-a-pad-opening"]
    rows = {r["entry"]: r for r in learnlib.load_queue(ws)["entries"]}
    ruled = rows[ruled_id]
    assert ruled["status"] == "declined"
    assert ruled["resolution"]["reason"].startswith("this fixture")
    assert ruled["line"] > was[ruled_id]        # source drift was picked up


def test_a_queue_id_with_no_entry_behind_it_is_reported_not_deleted(tmp_path,
                                                                    capsys):
    ws = _ws(tmp_path, ENTRY_A, ENTRY_B)
    _run(["compile", "--workspace", str(ws)], capsys)
    (ws / "LEARNINGS.md").write_text(
        f"# LEARNINGS - golden\n\n{ENTRY_A}", encoding="utf-8", newline="\n")
    code, payload = _run(["compile", "--workspace", str(ws)], capsys)
    assert code == 1
    assert payload["orphans"] == [
        "2026-08-14-pour-neck-only-samples-where-vias-land"]


# ---------------------------------------------------------------------------
# 2. rulings are real
# ---------------------------------------------------------------------------
def test_a_ruling_needs_a_reason_and_a_kind_that_matches_the_status(tmp_path,
                                                                    capsys):
    ws = _ws(tmp_path, ENTRY_A)
    _run(["compile", "--workspace", str(ws)], capsys)
    eid = "2026-08-14-locking-an-anchor-orphans-its-group"
    queue = learnlib.load_queue(ws)

    short = learnlib.apply_ruling(queue, {"entry": eid, "status": "declined",
                                          "kind": "board_local",
                                          "reason": "no"}, ws)
    assert not short["applied"] and "reason" in short["why"]
    crossed = learnlib.apply_ruling(queue, {"entry": eid, "status": "declined",
                                            "kind": "script_check",
                                            "reason": "a promotion kind on a "
                                                      "decline"}, ws)
    assert not crossed["applied"]
    assert queue["entries"][0]["status"] == "pending"


def test_a_second_ruling_on_a_resolved_entry_is_refused(tmp_path, capsys):
    ws = _ws(tmp_path, ENTRY_A)
    _run(["compile", "--workspace", str(ws)], capsys)
    eid = "2026-08-14-locking-an-anchor-orphans-its-group"
    queue = learnlib.load_queue(ws)
    first = learnlib.apply_ruling(queue, {"entry": eid, "status": "declined",
                                          "kind": "board_local",
                                          "reason": "fixture, not a board"}, ws)
    again = learnlib.apply_ruling(queue, {"entry": eid, "status": "promoted",
                                          "kind": "prompt_line",
                                          "artifacts": ["agents/router.md"],
                                          "level": "L0",
                                          "reason": "changing my mind"}, ws)
    assert first["applied"] and not again["applied"]
    assert "already declined" in again["why"]


@pytest.mark.parametrize("mutate,expected", [
    (lambda r: r.update(status="promoted", resolution={
        "kind": "script_check", "artifacts": [], "reason": "wrote it somewhere",
        "date": "2026-08-14"}), "no artifacts"),
    (lambda r: r.update(status="promoted", resolution={
        "kind": "script_check", "artifacts": ["scripts/no_such_script.py"],
        "reason": "wrote it somewhere", "date": "2026-08-14"}),
     "does not exist"),
    (lambda r: r.update(status="pending", resolution={
        "kind": "board_local", "reason": "ruled but pending",
        "date": "2026-08-14"}), "pending but carries"),
    (lambda r: r.update(status="declined"), "no resolution"),
    (lambda r: r.update(targets=["scripts/not_here.py"]), "does not exist"),
])
def test_validate_catches_a_queue_that_claims_more_than_it_did(
        tmp_path, capsys, mutate, expected):
    ws = _ws(tmp_path, ENTRY_A)
    _run(["compile", "--workspace", str(ws)], capsys)
    queue = learnlib.load_queue(ws)
    row = queue["entries"][0]
    mutate(row)
    if row["status"] == "promoted":
        row["proposed_level"] = "L2"      # isolate the defect under test
    learnlib.save_queue(ws, queue)
    problems, _ = learnlib.validate_queue(ws)
    assert any(expected in p for p in problems), problems


def test_validate_is_clean_on_a_freshly_compiled_queue(tmp_path, capsys):
    ws = _ws(tmp_path, ENTRY_A, ENTRY_B, ENTRY_C)
    _run(["compile", "--workspace", str(ws)], capsys)
    code, payload = _run(["validate", "--workspace", str(ws)], capsys)
    assert code == 0 and payload["problems"] == []


# ---------------------------------------------------------------------------
# 3. root promotion moves the entry and its triage row together
# ---------------------------------------------------------------------------
@pytest.fixture()
def root_pair(tmp_path):
    """Copies of the two files a root promotion writes, so the test never
    appends to the repo's own LEARNINGS.md."""
    root = tmp_path / "LEARNINGS.md"
    tri = tmp_path / "ladder-triage.md"
    shutil.copy2(ROOT / "LEARNINGS.md", root)
    shutil.copy2(ROOT / "design" / "ladder-triage.md", tri)
    return root, tri


def _triage_rows(path: Path) -> list[list[str]]:
    rows = []
    for ln in path.read_text(encoding="utf-8").splitlines():
        if not ln.startswith("|"):
            continue
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        if len(cells) >= 8 and cells[0].isdigit():
            rows.append(cells)
    return rows


def test_root_promotion_appends_the_entry_and_a_matching_row(tmp_path,
                                                             root_pair, capsys):
    root, tri = root_pair
    ws = _ws(tmp_path, ENTRY_A)
    _run(["compile", "--workspace", str(ws)], capsys)
    eid = "2026-08-14-locking-an-anchor-orphans-its-group"
    before = len(_triage_rows(tri))

    moved = learnlib.promote_to_root(
        ws, eid, {"now": "L0", "target": "L2",
                  "owner": "scripts/lib/placelib.py", "status": "open",
                  "note": "build_clusters drops the group"},
        root=root, triage_file=tri)

    text = root.read_text(encoding="utf-8")
    assert "Locking an anchor orphans its group" in text
    assert f"Promoted from {ws.as_posix()}/LEARNINGS.md" in text
    assert "scripts/place_seed.py reported 4 clusters" in text  # body verbatim

    rows = _triage_rows(tri)
    assert len(rows) == before + 1
    last = rows[-1]
    assert int(last[0]) == moved["n"] == len(rows)
    # the row's line number must be where the entry actually starts
    entries = learnlib._root_entries(text)
    assert int(last[1]) == entries[moved["n"] - 1][0] == moved["line"]
    assert last[4] == "L0" and last[5] == "L2"
    assert last[6] == "scripts/lib/placelib.py" and last[7] == "open"


def test_root_promotion_refuses_a_duplicate_and_a_bad_row(tmp_path, root_pair,
                                                          capsys):
    root, tri = root_pair
    ws = _ws(tmp_path, ENTRY_A)
    _run(["compile", "--workspace", str(ws)], capsys)
    eid = "2026-08-14-locking-an-anchor-orphans-its-group"
    good = {"now": "L0", "target": "L2", "owner": "scripts/lib/placelib.py",
            "status": "open", "note": ""}
    learnlib.promote_to_root(ws, eid, good, root=root, triage_file=tri)

    with pytest.raises(ValueError, match="already carries"):
        learnlib.promote_to_root(ws, eid, good, root=root, triage_file=tri)
    with pytest.raises(ValueError, match="does not exist"):
        learnlib.promote_to_root(ws, eid, {**good, "owner": "scripts/nope.py"},
                                 root=tmp_path / "other.md", triage_file=tri)
    with pytest.raises(ValueError, match="levels"):
        learnlib.promote_to_root(ws, eid, {**good, "target": "L9"},
                                 root=tmp_path / "other.md", triage_file=tri)
    with pytest.raises(ValueError, match="triage.status"):
        learnlib.promote_to_root(ws, eid, {**good, "status": ""},
                                 root=tmp_path / "other.md", triage_file=tri)


def test_a_failed_root_promotion_does_not_strand_the_rest_of_the_pass(
        tmp_path, capsys):
    """A batch is a whole pass; one bad ruling reports and the rest proceed."""
    ws = _ws(tmp_path, ENTRY_A, ENTRY_B)
    _run(["compile", "--workspace", str(ws)], capsys)
    queue = learnlib.load_queue(ws)
    bad = learnlib.apply_ruling(queue, {
        "entry": "2026-08-14-locking-an-anchor-orphans-its-group",
        "status": "promoted", "kind": "root_learnings", "level": "L2",
        "reason": "this one has no triage block at all"}, ws)
    ok = learnlib.apply_ruling(queue, {
        "entry": "2026-08-14-pour-neck-only-samples-where-vias-land",
        "status": "declined", "kind": "board_local",
        "reason": "fixture, not a real board"}, ws)
    assert not bad["applied"] and "triage" in bad["why"]
    assert ok["applied"]


# ---------------------------------------------------------------------------
# 4. the rf-de-20m acceptance + the wiring
# ---------------------------------------------------------------------------
def test_rf_de_backlog_is_processed_end_to_end():
    """U6 acceptance: 66 entries, each promoted or explicitly declined."""
    queue = learnlib.load_queue(RF_DE)
    assert queue is not None, "rf-de-20m has no compiled queue"
    rows = queue["entries"]
    assert len(rows) == 66
    pending = [r["entry"] for r in rows if r["status"] == "pending"]
    assert not pending, f"{len(pending)} entries never ruled on: {pending[:3]}"
    for r in rows:
        res = r["resolution"]
        assert len(res["reason"]) >= 40, r["entry"]   # a reason, not a shrug
        if r["status"] == "promoted":
            assert res["kind"] in learnlib.PROMOTE_KINDS
            assert res["artifacts"] and r["proposed_level"]
        else:
            assert res["kind"] in learnlib.DECLINE_KINDS


def test_rf_de_queue_lints_clean():
    problems, _ = learnlib.validate_queue(RF_DE)
    assert problems == [], problems


def test_rf_de_root_promotions_are_in_the_register():
    """Every root_learnings ruling points at a row that is really there."""
    rows = [r for r in learnlib.load_queue(RF_DE)["entries"]
            if (r.get("resolution") or {}).get("kind") == "root_learnings"]
    assert len(rows) >= 30
    register = {int(c[0]) for c in _triage_rows(ROOT / "design" / "ladder-triage.md")}
    entries = learnlib._root_entries(
        (ROOT / "LEARNINGS.md").read_text(encoding="utf-8"))
    for r in rows:
        n = int(r["resolution"]["artifacts"][0].split("#")[1])
        assert n in register and n <= len(entries), r["entry"]


def test_every_run_recipe_ends_with_the_compile_step():
    """Run close is not optional: a run that captures nothing promotes
    nothing, and the queue is the only durable trace."""
    for name in ("full-run", "review", "fix-finding"):
        text = (RECIPES / f"{name}.md").read_text(encoding="utf-8")
        assert "learnings.py compile --workspace" in text, name
        assert "## Run close" in text, name


def test_sweep_reports_every_workspace_that_captures_learnings(capsys):
    code, payload = _run(["sweep", "--boards-dir", str(ROOT / "boards")],
                         capsys)
    assert code == 0
    boards = {b["board"]: b for b in payload["boards"]}
    assert "rf-de-20m" in boards
    assert boards["rf-de-20m"]["entries"] == boards["rf-de-20m"]["queued"] == 66
    assert boards["rf-de-20m"]["uncompiled"] == 0


def test_queue_filters_by_stage_for_the_learner_operator_mode(tmp_path, capsys):
    """U7 pulls one stage's entries; the counts still describe the whole queue
    so a filtered read never reads as an empty backlog."""
    ws = _ws(tmp_path, ENTRY_A, ENTRY_B, ENTRY_C)
    _run(["compile", "--workspace", str(ws)], capsys)
    code, payload = _run(["queue", "--workspace", str(ws), "--stage", "P8",
                          "--status", "pending"], capsys)
    assert code == 0
    assert payload["shown"] == 1 and payload["counts"]["pending"] == 3
    assert payload["entries"][0]["stage"] == "P8"


def test_queue_without_a_compile_is_an_error_not_an_empty_answer(tmp_path,
                                                                 capsys):
    ws = _ws(tmp_path, ENTRY_A)
    code, payload = _run(["queue", "--workspace", str(ws)], capsys)
    assert code == 2 and "compile" in payload["error"]


def test_init_writes_the_standard_shape_and_never_overwrites(tmp_path, capsys):
    ws = tmp_path / "newboard"
    code, payload = _run(["init", "--workspace", str(ws), "--what", "a fixture"],
                         capsys)
    assert code == 0 and payload["written"]
    entries, malformed = learnlib.parse_entries(
        (ws / "LEARNINGS.md").read_text(encoding="utf-8"))
    assert not malformed and len(entries) == 1 and entries[0]["stage"] == "P0"
    (ws / "LEARNINGS.md").write_text("# mine\n", encoding="utf-8")
    code, payload = _run(["init", "--workspace", str(ws)], capsys)
    assert code == 0 and payload["written"] is None
    assert (ws / "LEARNINGS.md").read_text(encoding="utf-8") == "# mine\n"


def test_triage_summary_is_recomputed_from_the_table():
    summary = learnlib.triage_summary()
    assert summary["rows"] == summary["learnings_entries"]
    header = (ROOT / "design" / "ladder-triage.md").read_text(encoding="utf-8")
    assert f"all {summary['rows']} rows" in header, (
        "the register header's counts are stale - run `learnings.py triage`")
