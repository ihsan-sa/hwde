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

4. dsn_apply_net_rules(): KiCad's DSN export writes only netclass rules, so
   a per-net .kicad_dru floor (rules_gen's aiee_pwr_width_* track width and
   aiee_hv_* clearance) never reaches Freerouting, which then lays that net
   at the default 0.2 mm (rf-term's /RF: 4 track_width + 3 HV clearance DRC
   errors). Each such net is moved into its own DSN class carrying the
   floor.
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


def _sexp_end(text: str, i: int) -> int:
    """Index just past the s-expression opening at text[i] == '('."""
    depth, quoted = 0, False
    for j in range(i, len(text)):
        ch = text[j]
        if ch == '"':
            quoted = not quoted
        elif quoted:
            continue
        elif ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                return j + 1
    raise CheckError("unbalanced s-expression in DSN")


def _quote_mask(text: str) -> str:
    """`text` with every character inside double quotes blanked, so a paren
    in a quoted net name ("Net-(C1-Pad2)") is not read as structure."""
    out, quoted = [], False
    for ch in text:
        if ch == '"':
            quoted = not quoted
            out.append(ch)
        else:
            out.append(" " if quoted else ch)
    return "".join(out)


_DSN_TOKEN_RE = re.compile(r'"[^"]*"|[^\s()]+')


def dsn_apply_net_rules(dsn_text: str, widths: dict[str, float],
                        clearances: dict[str, float]) -> tuple[str, list]:
    """Give every net with a width or clearance floor (mm) above its DSN
    class's own its own class carrying max(class, floor). Returns (text,
    [net, ...] moved). Only a `(resolution um N)` DSN is handled - values are
    in um - anything else comes back unchanged."""
    if not re.search(r"\(resolution\s+um\s+\d+\)", dsn_text):
        return dsn_text, []
    nets = set(widths) | set(clearances)
    out, moved, pos = [], [], 0
    for m in re.finditer(r"\(class\s", dsn_text):
        if m.start() < pos:
            continue
        end = _sexp_end(dsn_text, m.start())
        block = dsn_text[m.start():end]
        head_end = next((j for j, t in enumerate(_quote_mask(block))
                         if j and t == "("), -1)
        head = block[:head_end] if head_end > 0 else block[:-1]
        body = block[head_end:-1] if head_end > 0 else ""
        toks = _DSN_TOKEN_RE.findall(head)[1:]     # drop "class"
        name, members = toks[0], toks[1:]
        cw = re.search(r"\(width\s+([\d.]+)\)", body)
        cc = re.search(r"\(clearance\s+([\d.]+)\)", body)
        cw = float(cw.group(1)) if cw else 0.0
        cc = float(cc.group(1)) if cc else 0.0
        keep, extra = [], []
        for tok in members:
            net = tok.strip('"')
            w = widths.get(net, 0.0) * 1000.0
            c = clearances.get(net, 0.0) * 1000.0
            if net not in nets or (w <= cw and c <= cc):
                keep.append(tok)
                continue
            nb = body
            if w > cw:
                nb = re.sub(r"\(width\s+[\d.]+\)", f"(width {w:g})", nb,
                            count=1)
            if c > cc:
                nb = re.sub(r"\(clearance\s+[\d.]+\)", f"(clearance {c:g})",
                            nb, count=1)
            cname = "aiee_" + re.sub(r"[^A-Za-z0-9_]", "_", net)
            extra.append(f"(class {cname} {tok}\n      {nb.strip()}\n    )")
            moved.append(net)
        out.append(dsn_text[pos:m.start()])
        if keep:
            out.append(f"(class {name} {' '.join(keep)}\n      "
                       f"{body.strip()}\n    )")
        for i, e in enumerate(extra):
            out.append(("\n    " if keep or i else "") + e)
        pos = end
    out.append(dsn_text[pos:])
    return "".join(out), moved
