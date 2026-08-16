"""routelib - shared plumbing for the S11 routing pipeline (venv side).

Three concerns, used by route_edit.py / route_auto.py / planes_gen.py:

1. run_worker(): drive lib/route_swig.py in KiCad's BUNDLED python. The job
   and result travel via FILES in a caller-owned staging dir - worker stdout
   is noise by design (wx image-handler chatter, C-level "memory leak of type
   'PCB_TRACK *'" spray on bulk removals) and is never parsed.

2. Freerouting invocation: build_fr_cmd() with the S11-verified flag set
   (LEARNINGS [freerouting]): --gui.enabled=false, -de/-do, -mp, and the
   determinism/safety trio -mt 1 -is sequential -da (multithreaded optimizer
   has a known clearance bug AND is nondeterministic; -da is mandatory or FR
   phones home and can stall) + --logging.file.enabled=false (else a
   DEBUG-heavy freerouting.log lands in cwd). run_freerouting() enforces a
   PROCESS-level timeout - a wedged JVM is only cleared by a kill.

3. parse_fr_log(): the authoritative completion parse. FR's own success
   signal lies; unrouted-count priority is (a) session-completed line's
   "final score: S (N unrouted)", (b) the LAST pass line's "(N unrouted)"
   - a pass line WITHOUT the parenthetical means 0 unrouted at that pass -
   (c) None (unknown -> caller treats as failure). Gate on kicad-cli DRC,
   never on FR's numbers.
"""
from __future__ import annotations

import json
import re
import subprocess
import uuid
from pathlib import Path

from checklib import CheckError

WORKER = Path(__file__).resolve().parent / "route_swig.py"

# Deterministic / safe base flags (order: options first, then -de/-do).
FR_BASE_FLAGS = ["--gui.enabled=false", "-mt", "1", "-is", "sequential",
                 "-da", "--logging.file.enabled=false"]

# Escalation ladder for route_auto: each rung re-runs Freerouting on the same
# DSN with more effort. mp = max passes; oit = optimizer improvement threshold
# (percent; lower = keep optimizing longer); us = board update strategy.
DEFAULT_LADDER = [
    {"mp": 20},
    {"mp": 60, "oit": 0.05},
    {"mp": 100, "us": "global"},
]

# Score capture is `\d+(?:\.\d+)?`, NOT `[\d.]+`: when Freerouting finishes with
# nothing unrouted the line has no " (N unrouted)" suffix and ends in a full stop
# ("...score of 997.76."), which `[\d.]+` swallows -> float("997.76.") ValueError.
# The bug fired ONLY on success, because the suffix otherwise terminated the match
# at the space. Found on bb-buck P6 (route probe, completion 1.00).
_PASS_RE = re.compile(
    r"Auto-router pass #(\d+).*?score of (\d+(?:\.\d+)?)(?: \((\d+) unrouted\))?")
_SESSION_RE = re.compile(
    r"Auto-router session completed: started with (\d+) unrouted nets"
    r".*?final score: (\d+(?:\.\d+)?)(?: \((\d+) unrouted\))?")


WORK_MARKER = ".aiee_route_work"


def fresh_work_dir(work: Path) -> Path:
    """(Re)create a work dir SAFELY: only wipe a directory this pipeline
    created (marker file) or an empty one - a user-supplied --work-dir
    pointing at real data must never be rmtree'd (S11 review finding)."""
    import shutil

    work = Path(work)
    if work.exists():
        if not work.is_dir():
            raise CheckError(f"work dir is not a directory: {work}")
        if any(work.iterdir()) and not (work / WORK_MARKER).is_file():
            raise CheckError(
                f"refusing to wipe non-empty work dir {work} (no {WORK_MARKER}"
                " marker; pick a fresh --work-dir)")
        shutil.rmtree(work)
    work.mkdir(parents=True)
    (work / WORK_MARKER).write_text("", encoding="utf-8")
    return work


def swap_in(staged: Path, pcb: Path) -> None:
    """Atomic same-volume swap; degrade to copy for a cross-volume
    --work-dir (os.replace raises OSError across volumes on Windows)."""
    import os
    import shutil

    try:
        os.replace(staged, pcb)
    except OSError:
        shutil.copy2(staged, pcb)
        Path(staged).unlink(missing_ok=True)


def run_worker(bundled_python: Path, job: dict, stage: Path,
               timeout: int = 300, worker: Path | None = None) -> dict:
    """Run one SWIG-worker verb; job/result via files under `stage`.

    Default worker is route_swig; board_update passes lib/update_swig.py
    (same job/result-file protocol - bulk Remove sprays stdout, results
    must travel by file)."""
    tag = uuid.uuid4().hex[:8]
    job_file = stage / f"job_{tag}.json"
    result_file = stage / f"result_{tag}.json"
    job = dict(job)
    job["result"] = str(result_file)
    job_file.write_text(json.dumps(job), encoding="utf-8")
    try:
        cp = subprocess.run(
            [str(bundled_python), str(worker or WORKER), str(job_file)],
            capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        raise CheckError(
            f"{(worker or WORKER).stem} {job.get('verb')} timed out after "
            f"{timeout}s (wedged SWIG/wx call - board untouched)") from exc
    if not result_file.is_file():
        tail = (cp.stderr or cp.stdout or "").strip()[-300:]
        raise CheckError(
            f"{(worker or WORKER).stem} {job.get('verb')} wrote no result "
            f"(exit {cp.returncode}): {tail}")
    result = json.loads(result_file.read_text(encoding="utf-8"))
    if not result.get("ok"):
        raise CheckError(
            f"{(worker or WORKER).stem} {job.get('verb')} failed: "
            f"{result.get('error')}")
    return result


def build_fr_cmd(java: Path, jar: Path, dsn: Path, ses: Path,
                 rung: dict | None = None) -> list[str]:
    rung = rung or {}
    cmd = [str(java), "-jar", str(jar)] + FR_BASE_FLAGS
    cmd += ["-mp", str(rung.get("mp", 20))]
    if rung.get("oit") is not None:
        cmd += ["-oit", str(rung["oit"])]
    if rung.get("us"):
        cmd += ["-us", str(rung["us"])]
    if rung.get("inc"):
        cmd += ["-inc", str(rung["inc"])]
    cmd += ["-de", str(dsn), "-do", str(ses)]
    return cmd


def run_freerouting(java: Path, jar: Path, dsn: Path, ses: Path, *,
                    rung: dict | None = None, timeout: int = 600,
                    log_file: Path | None = None) -> dict:
    """One Freerouting run. Returns parse_fr_log() facts + process info."""
    cmd = build_fr_cmd(java, jar, dsn, ses, rung)
    try:
        cp = subprocess.run(cmd, capture_output=True, text=True,
                            encoding="utf-8", errors="replace",
                            timeout=timeout, cwd=str(dsn.parent))
        out = (cp.stdout or "") + "\n" + (cp.stderr or "")
        timed_out = False
        rc = cp.returncode
    except subprocess.TimeoutExpired as exc:
        out = ((exc.stdout or b"").decode("utf-8", "replace")
               if isinstance(exc.stdout, bytes) else (exc.stdout or ""))
        timed_out = True
        rc = 124
    if log_file is not None:
        log_file.write_text(out, encoding="utf-8")
    facts = parse_fr_log(out)
    facts.update({"rc": rc, "timed_out": timed_out,
                  "ses_written": ses.is_file(), "cmd": cmd})
    return facts


def parse_fr_log(text: str) -> dict:
    passes = []
    for m in _PASS_RE.finditer(text):
        passes.append({"pass": int(m.group(1)), "score": float(m.group(2)),
                       "unrouted": int(m.group(3)) if m.group(3) else 0})
    session = _SESSION_RE.search(text)
    unrouted = None
    started = None
    score = None
    if session:
        started = int(session.group(1))
        score = float(session.group(2))
        unrouted = int(session.group(3)) if session.group(3) else None
    if unrouted is None and passes:
        unrouted = passes[-1]["unrouted"]
    if unrouted is None and session:
        unrouted = 0  # session completed, no pass lines captured
    return {"passes": passes, "unrouted": unrouted,
            "started_unrouted": started, "final_score": score,
            "session_completed": bool(session)}


def completion_fraction(facts: dict) -> float | None:
    """Fraction of FR's starting workload that got routed (0..1)."""
    started, left = facts.get("started_unrouted"), facts.get("unrouted")
    if started in (None, 0):
        return 1.0 if facts.get("session_completed") and left in (0, None) \
            else None
    if left is None:
        return None
    return max(0.0, min(1.0, 1.0 - left / started))
