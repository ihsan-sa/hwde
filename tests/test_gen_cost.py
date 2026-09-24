"""gen_cost.py acceptance tests.

Criteria -> tests:
  - spend goes to the step hwde recorded: after a phase event to that phase,
    before a gate/checkpoint to the phase it closes, before the workspace to
    `setup`, after the last record to the furthest phase; naive history
    stamps read in the given zone  -> test_step_attribution
  - auto round = sessions that ran in the workspace's recorded span + the
    lead-in hour before it;
    a later session with no record is left out; a streamed message counts
    once (largest output); subagent messages count; the recorded total
    leads and the rest is an `unattributed` line; steps add up to the
    total; unpriced models reported, not priced -> test_design_run_round
  - a round with no hwde record inside is one `unsplit` line with a reason;
    a shared round is shown beside the total, not in it
                                     -> test_unsplit_and_shared_rounds
  - loop log: a timed-out iteration logs no cost and is counted
                                     -> test_loop_log_timeout
  - --out merges: a session whose transcript is gone keeps its figures
                                     -> test_merge_keeps_recorded_sessions
  - no session -> exit 1, --out untouched; no workspace -> exit 2
                                     -> test_exit_codes
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / ".claude" / "skills" / "hwde" / "scripts"
sys.path.insert(0, str(SCRIPTS))

import gen_cost  # noqa: E402

PRICES = """meta: {currency: USD, source: test table, verified: "2026-09-24"}
models:
  m-test: {input: 0, output: 10.0, cache_read: 0, cache_write_5m: 0,
           cache_write_1h: 0}
"""


def utc(hhmm: str) -> datetime:
    h, m = hhmm.split(":")
    return datetime(2026, 9, 24, int(h), int(m), tzinfo=timezone.utc)


def msg(hhmm: str, mid: str, out: int, model: str = "m-test") -> str:
    """One assistant line; `out` output tokens = out * $10/M."""
    return json.dumps({"type": "assistant",
                       "timestamp": f"2026-09-24T{hhmm}:00.000Z",
                       "message": {"id": mid, "model": model,
                                   "usage": {"input_tokens": 0,
                                             "output_tokens": out}}})


def session(pdir: Path, sid: str, lines: list[str], recorded: float | None = None,
            sub: list[str] | None = None) -> Path:
    pdir.mkdir(parents=True, exist_ok=True)
    body = list(lines)
    if recorded is not None:
        body.append(json.dumps({"type": "cost-state", "totalCostUSD": recorded}))
    p = pdir / f"{sid}.jsonl"
    p.write_text("\n".join(body) + "\n", encoding="utf-8")
    if sub:
        d = pdir / sid / "subagents"
        d.mkdir(parents=True)
        (d / "agent-1.jsonl").write_text("\n".join(sub) + "\n", encoding="utf-8")
    return p


def workspace(tmp: Path, history: list[dict]) -> Path:
    ws = tmp / "ws"
    ws.mkdir()
    (ws / "state.json").write_text(json.dumps(
        {"board": "synth", "history": history}), encoding="utf-8")
    (tmp / "prices.yaml").write_text(PRICES, encoding="utf-8")
    return ws


HISTORY = [  # naive stamps, read as UTC via --history-tz +00:00
    {"ts": "2026-09-24T10:00:00", "event": "init", "phase": "P0"},
    {"ts": "2026-09-24T10:10:00", "event": "phase", "phase": "P3"},
    {"ts": "2026-09-24T10:20:00", "event": "gate", "gate": "erc"},
    {"ts": "2026-09-24T10:30:00", "event": "phase", "phase": "P5"},
    {"ts": "2026-09-24T10:40:00", "event": "gate", "gate": "dfm"},
    {"ts": "2026-09-24T10:41:00", "event": "decision", "what": "x"},
]


def run(tmp: Path, ws: Path, *extra: str) -> int:
    return gen_cost.main(["--workspace", str(ws), "--history-tz", "+00:00",
                          "--prices", str(tmp / "prices.yaml"), *extra])


def test_step_attribution():
    ms = gen_cost.milestones(HISTORY, timezone.utc)
    assert [m[2] for m in ms] == ["enter", "enter", "exit", "enter", "exit"]
    want = {"09:50": "setup", "10:05": "P0", "10:15": "P4", "10:25": "P4",
            "10:35": "P9", "10:50": "P9"}
    assert {t: gen_cost.step_of(utc(t), ms) for t in want} == want
    # A naive stamp is read in the zone given: 06:00 at -04:00 is 10:00 UTC.
    from datetime import timedelta
    edt = timezone(timedelta(hours=-4))
    assert gen_cost.parse_ts("2026-09-24T06:00:00", edt) == utc("10:00")


def test_design_run_round(tmp_path):
    ws = workspace(tmp_path, HISTORY)
    pdir = tmp_path / "proj"
    # Lead-in: ended 30 min before init -> counted, as `setup`.
    session(pdir, "a-lead", [msg("09:20", "m1", 100000),
                             msg("09:30", "m2", 100000)], recorded=0.5)
    # The run: m3 streamed twice (8 then 100000 tokens) counts once, a
    # subagent message counts, an unknown model is reported unpriced, and the
    # recorded total is 0.3 above the priced sum.
    session(pdir, "b-run", [msg("10:05", "m3", 8), msg("10:05", "m3", 100000),
                            msg("10:35", "m4", 200000),
                            msg("10:36", "m5", 5000, model="m-other")],
            recorded=4.3, sub=[msg("10:15", "s1", 100000)])
    # Hours later, no hwde record in its span -> not this round.
    session(pdir, "c-later", [msg("15:00", "m6", 900000)], recorded=9.0)
    out = ws / "reports" / "cost.json"
    assert run(tmp_path, ws, "--project-dir", str(pdir), "--out", str(out)) == 0
    doc = json.loads(out.read_text())
    (rnd,) = doc["rounds"]
    assert [s["id"] for s in rnd["sessions"]] == ["a-lead", "b-run"]
    b = rnd["sessions"][1]
    assert b["priced_usd"] == 4.0 and b["recorded_usd"] == 4.3 and b["usd"] == 4.3
    assert b["by_step"] == {"P0": 1.0, "P4": 1.0, "P9": 2.0}
    assert b["unpriced_tokens"] == {"m-other": 5000}
    steps = {s["step"]: s["usd"] for s in doc["by_step"]}
    assert steps == {"setup": 2.0, "P0": 1.0, "P4": 1.0, "P9": 2.0,
                     "unattributed": 0.3}
    assert doc["total_usd"] == 6.3 == round(sum(steps.values()), 4)
    assert doc["breakdown"] == "full" and doc["breakdown_reason"] is None
    assert doc["recorded_usd"] == 4.8  # a-lead's 0.5 is below its priced 2.0
    assert doc["unpriced_tokens"] == {"m-other": 5000}


def test_unsplit_and_shared_rounds(tmp_path):
    ws = workspace(tmp_path, HISTORY)
    pdir = tmp_path / "proj"
    run_s = session(pdir, "run", [msg("10:05", "m1", 50000),
                                  msg("10:15", "m0", 50000)], recorded=1.0)
    fix = session(pdir, "fix", [msg("12:00", "m2", 200000)], recorded=2.0)
    both = session(pdir, "both", [msg("13:00", "m3", 400000)], recorded=4.0)
    out = ws / "reports" / "cost.json"
    assert run(tmp_path, ws, "--session", str(run_s), "--label", "design run",
               "--out", str(out)) == 0
    assert run(tmp_path, ws, "--session", str(fix), "--label", "fix round",
               "--out", str(out)) == 0
    assert run(tmp_path, ws, "--session", str(both), "--label", "shared round",
               "--shared-with", "another board", "--out", str(out)) == 0
    doc = json.loads(out.read_text())
    assert doc["total_usd"] == 3.0  # the shared 4.0 is not in it
    assert doc["shared"] == [{"label": "shared round",
                              "shared_with": "another board", "usd": 4.0}]
    unsplit = [s for s in doc["by_step"] if s["step"] == "unsplit"]
    assert unsplit == [{"step": "unsplit", "label": "fix round", "usd": 2.0,
                        "reason": "hwde recorded no step in the workspace "
                                  "while this round ran"}]
    assert {s["step"] for s in doc["by_step"]} == {"P0", "P4", "unsplit"}
    assert doc["breakdown"] == "partial"
    assert "fix round:" in doc["breakdown_reason"]


def test_loop_log_timeout(tmp_path):
    ws = workspace(tmp_path, HISTORY)
    pdir = tmp_path / "proj"
    session(pdir, "run", [msg("10:05", "m1", 100000),
                          msg("10:35", "m2", 100000)], recorded=2.0)
    log = tmp_path / "loop.log"
    log.write_text(
        "2026-09-24T10:00:00Z iter 1/2 start (budget $8)\n"
        "2026-09-24T10:20:00Z iter 1 end rc=0 err=false/success turns=3 "
        "cost=$1.0 total=$1.0 commits=yes\n"
        "2026-09-24T10:21:00Z iter 2/2 start (budget $8)\n"
        "2026-09-24T11:21:00Z iter 2 end rc=124 err=/ turns= cost=$ "
        "total=$1.0 commits=yes\n"
        # a loop of another day: outside the round, not reconciled
        "2026-09-20T10:00:00Z iter 1/1 start (budget $8)\n"
        "2026-09-20T10:30:00Z iter 1 end rc=0 err=false/success turns=3 "
        "cost=$7.0 total=$7.0 commits=yes\n", encoding="utf-8")
    out = ws / "reports" / "cost.json"
    assert run(tmp_path, ws, "--project-dir", str(pdir), "--loop-log",
               str(log), "--out", str(out)) == 0
    doc = json.loads(out.read_text())
    loop = doc["rounds"][0]["loop"]
    assert [i["rc"] for i in loop["iterations"]] == [0, 124]
    assert loop["logged_usd"] == 1.0 and loop["unlogged_iterations"] == 1
    assert doc["loop_logged_usd"] == 1.0 and doc["total_usd"] == 2.0


def test_merge_keeps_recorded_sessions(tmp_path):
    ws = workspace(tmp_path, HISTORY)
    pdir = tmp_path / "proj"
    old = session(pdir, "old", [msg("10:05", "m1", 100000)], recorded=1.0)
    out = ws / "reports" / "cost.json"
    assert run(tmp_path, ws, "--project-dir", str(pdir), "--note", "n1",
               "--out", str(out)) == 0
    old.unlink()  # the transcript is gone; its figures must stay
    session(pdir, "new", [msg("10:35", "m2", 200000)], recorded=2.0)
    assert run(tmp_path, ws, "--project-dir", str(pdir), "--note", "n1",
               "--out", str(out)) == 0
    doc = json.loads(out.read_text())
    assert [s["id"] for s in doc["rounds"][0]["sessions"]] == ["old", "new"]
    assert doc["total_usd"] == 3.0 and doc["notes"] == ["n1"]


def test_exit_codes(tmp_path, capsys):
    ws = workspace(tmp_path, HISTORY)
    out = ws / "reports" / "cost.json"
    out.parent.mkdir()
    out.write_text('{"keep": true}', encoding="utf-8")
    empty = tmp_path / "empty"
    empty.mkdir()
    assert run(tmp_path, ws, "--project-dir", str(empty), "--out", str(out)) == 1
    assert json.loads(out.read_text()) == {"keep": True}
    assert "ran while the workspace recorded its steps" in capsys.readouterr().out
    assert run(tmp_path, tmp_path / "nope") == 2
