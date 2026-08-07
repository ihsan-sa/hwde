"""state.py - state.json read/write helpers for the /ai-ee orchestrator (SPEC 4, S13).

state.json is the single source of truth for one design run. The orchestrator
NEVER carries pipeline state in its context: it reads the resume summary, acts,
and records every transition here. Every mutating subcommand appends a
timestamped event to `history`, so the file is both current state AND audit
trail (`a killed-and-resumed session continues from the last gate`).

Schema (version 1):
    {
      "version": 1, "board": str, "workspace": str, "created": ts, "updated": ts,
      "phase": "P0".."P10" | "done",
      "gates": {gate_name: {phase, status: pass|fail, attempts: int,
                            last: {ts, status, failing_count, total},
                            history: [same shape as last, oldest first]}},
      "human": {checkpoint_id: {status: approved|rejected|skipped, ts, note}},
      "artifacts": {name: workspace-relative path},
      "open_issues": [{id, gate, phase, fixer, net, kinds[], severity, count,
                       region, work_order, status: open|fixing|fixed|escalated|
                       waived, agent, attempts, opened, closed}],
      "next_issue_id": int,
      "budgets": {"fix_loops": {gate_name: remaining}, ...},
      "decisions": [{what, why, phase, ts}],
      "history": [{ts, event, ...detail}]
    }

CLI (spec 6 contract: argparse, JSON to stdout, exit 0 ok / 2 error; state.py
has no violation concept so exit 1 is unused):
    state.py init --workspace DIR --board NAME [--phase P0] [--force]
    state.py show|resume [--workspace DIR | --state FILE]
    state.py set-phase --phase P7 ...
    state.py record-gate --gate NAME --result gate_result.json [--phase PN] ...
    state.py artifact --name pcb --path kicad/b.kicad_pcb ...
    state.py decision --what W --why Y ...
    state.py human --checkpoint 2 --status approved [--note N] ...
    state.py issue --id 3 --status fixed [--agent fixer-1] [--bump-attempts] ...
    state.py budget --path fix_loops.drc_routed [--consume] ...
    state.py log --event TEXT [--data JSON] ...
    state.py snapshot --label L [--files F ...] / restore --label L ...

Writes are atomic (tmp file + os.replace, same directory). Single-writer by
design: the orchestrator serializes all state mutations (SPEC 4 concurrency).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "lib"))
import checklib  # noqa: E402
from checklib import CheckError  # noqa: E402

SCRIPT = "state"
PHASES = ["P0", "P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8", "P9", "P10",
          "done"]
# Machine-gate order along the pipeline (SPEC 3). The interim `drc` gate is a
# tool, not a pipeline edge, so it is not listed.
GATE_ORDER = [("P4", "erc"), ("P6", "place"), ("P7", "drc_routed"),
              ("P8", "verify"), ("P9", "dfm")]
# Human checkpoints (SPEC 7). 3 is optional-but-on-by-default.
CHECKPOINTS = {"1": "P2", "2": "P4", "3": "P6", "4": "P8", "5": "P10"}
DEFAULT_BUDGETS = {
    "fix_loops": {g: 3 for _, g in GATE_ORDER},
    "freerouting_retries": 2,
    "place_edit_iterations": 8,
}
SNAP_DIR = "state_snapshots"
# Standard workspace layout (T6 state-scaffold): init owns the scaffold so
# the orchestrator playbook does not transcribe a directory list every run.
SUBDIRS = ("brief", "architecture", "research", "parts", "lib", "kicad",
           "routing", "reports", "fab", "log")
# Digest discipline (T6 XC-4): SKILL says 5-10 lines per phase digest; the
# post-v1 runs drifted to 23-82. Warn (never fail) when the digest for the
# phase just left is missing or exceeds this cap (headroom for dense phases).
DIGEST_LINE_CAP = 15


def now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S")


def _atomic_write(path: Path, text: str) -> None:
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


class State:
    """In-memory view of one state.json. Mutators record history themselves;
    call save() (atomic) after a batch of mutations."""

    def __init__(self, path: Path, data: dict):
        self.path = Path(path)
        self.data = data

    # ---- lifecycle -------------------------------------------------------
    @classmethod
    def init(cls, workspace: Path, board: str, phase: str = "P0",
             force: bool = False) -> "State":
        workspace = Path(workspace)
        path = workspace / "state.json"
        if path.exists() and not force:
            raise CheckError(f"{path} already exists (use --force to recreate)")
        if phase not in PHASES:
            raise CheckError(f"unknown phase {phase!r}")
        workspace.mkdir(parents=True, exist_ok=True)
        for d in SUBDIRS:  # idempotent scaffold; pre-existing content survives
            (workspace / d).mkdir(exist_ok=True)
        ts = now()
        data = {
            "version": 1, "board": board,
            "workspace": str(workspace).replace("\\", "/"),
            "created": ts, "updated": ts, "phase": phase,
            "gates": {}, "human": {}, "artifacts": {}, "open_issues": [],
            "next_issue_id": 1,
            "budgets": json.loads(json.dumps(DEFAULT_BUDGETS)),
            "decisions": [],
            "history": [{"ts": ts, "event": "init", "board": board,
                         "phase": phase}],
        }
        st = cls(path, data)
        st.save()
        return st

    @classmethod
    def load(cls, path: Path) -> "State":
        path = Path(path)
        data = checklib.load_json(path, "state file")
        if data.get("version") != 1:
            raise CheckError(f"{path}: unsupported state version "
                             f"{data.get('version')!r}")
        return cls(path, data)

    def save(self) -> None:
        self.data["updated"] = now()
        _atomic_write(self.path, json.dumps(self.data, indent=1))

    def _log(self, event: str, **detail) -> None:
        self.data["history"].append({"ts": now(), "event": event, **detail})

    # ---- mutators --------------------------------------------------------
    def set_phase(self, phase: str) -> list[dict]:
        """Record the phase; return warn-only digest-discipline findings for
        the phase just left (T6 XC-4 - drift becomes recorded fact, exit 0)."""
        if phase not in PHASES:
            raise CheckError(f"unknown phase {phase!r}")
        prev = self.data["phase"]
        self.data["phase"] = phase
        self._log("phase", phase=phase, prev=prev)
        warnings: list[dict] = []
        if prev != phase and re.fullmatch(r"P\d+", prev or ""):
            digest = self.path.parent / "log" / f"{prev}-digest.md"
            if not digest.is_file():
                warnings.append({
                    "kind": "digest_discipline",
                    "msg": f"log/{prev}-digest.md missing for the phase just "
                           "left (SKILL: write 5-10 lines before set-phase)"})
            else:
                n = len(digest.read_text(encoding="utf-8",
                                         errors="replace").splitlines())
                if n > DIGEST_LINE_CAP:
                    warnings.append({
                        "kind": "digest_discipline",
                        "msg": f"log/{prev}-digest.md is {n} lines "
                               f"(cap {DIGEST_LINE_CAP}; SKILL says 5-10)"})
        return warnings

    def record_gate(self, gate: str, result: dict, phase: str | None = None) -> dict:
        status = result.get("status")
        if status not in ("pass", "fail"):
            raise CheckError(f"gate result status must be pass|fail, "
                             f"got {status!r}")
        entry = {"ts": now(), "status": status,
                 "failing_count": result.get("failing_count", 0),
                 "total": (result.get("counts") or {}).get("total", 0)}
        g = self.data["gates"].setdefault(
            gate, {"phase": phase or result.get("phase"), "status": None,
                   "attempts": 0, "last": None, "history": []})
        if phase:
            g["phase"] = phase
        g["attempts"] += 1
        g["status"] = status
        g["last"] = entry
        g["history"].append(entry)
        self._log("gate", gate=gate, status=status, attempt=g["attempts"],
                  failing_count=entry["failing_count"])
        return g

    def set_artifact(self, name: str, path: str) -> None:
        self.data["artifacts"][name] = str(path).replace("\\", "/")
        self._log("artifact", name=name, path=self.data["artifacts"][name])

    def add_decision(self, what: str, why: str, phase: str | None = None) -> None:
        self.data["decisions"].append(
            {"what": what, "why": why, "phase": phase or self.data["phase"],
             "ts": now()})
        self._log("decision", what=what)

    def record_human(self, checkpoint: str, status: str,
                     note: str | None = None) -> None:
        if checkpoint not in CHECKPOINTS:
            raise CheckError(f"unknown checkpoint {checkpoint!r} "
                             f"(known: {', '.join(CHECKPOINTS)})")
        if status not in ("approved", "rejected", "skipped"):
            raise CheckError("human status must be approved|rejected|skipped")
        self.data["human"][checkpoint] = {"status": status, "ts": now(),
                                          "note": note}
        self._log("human", checkpoint=checkpoint, status=status)

    def open_issue(self, issue: dict) -> dict:
        iid = self.data["next_issue_id"]
        self.data["next_issue_id"] = iid + 1
        rec = {"id": iid, "status": "open", "agent": None, "attempts": 0,
               "opened": now(), "closed": None, **issue}
        self.data["open_issues"].append(rec)
        self._log("issue_open", id=iid, gate=rec.get("gate"),
                  fixer=rec.get("fixer"), kinds=rec.get("kinds"))
        return rec

    def update_issue(self, iid: int, status: str | None = None,
                     agent: str | None = None, bump: bool = False) -> dict:
        for rec in self.data["open_issues"]:
            if rec["id"] == iid:
                if status:
                    if status not in ("open", "fixing", "fixed", "escalated",
                                      "waived"):
                        raise CheckError(f"bad issue status {status!r}")
                    rec["status"] = status
                    if status in ("fixed", "waived"):
                        rec["closed"] = now()
                if agent:
                    rec["agent"] = agent
                if bump:
                    rec["attempts"] += 1
                self._log("issue", id=iid, status=rec["status"],
                          agent=rec["agent"], attempts=rec["attempts"])
                return rec
        raise CheckError(f"no issue with id {iid}")

    def budget(self, dotted: str, consume: bool = False) -> int:
        node = self.data["budgets"]
        keys = dotted.split(".")
        for k in keys[:-1]:
            node = node.get(k)
            if not isinstance(node, dict):
                raise CheckError(f"unknown budget path {dotted!r}")
        leaf = keys[-1]
        if leaf not in node:
            raise CheckError(f"unknown budget path {dotted!r}")
        if consume:
            if node[leaf] <= 0:
                raise CheckError(f"budget {dotted} exhausted")
            node[leaf] -= 1
            self._log("budget", path=dotted, remaining=node[leaf])
        return node[leaf]

    # ---- snapshots (fix-loop safety net; SPEC 4 rollback) ----------------
    def _workspace(self) -> Path:
        return Path(self.data["workspace"])

    def snapshot(self, label: str, files: list[str] | None = None) -> dict:
        ws = self._workspace()
        dest = ws / SNAP_DIR / label
        if dest.exists():
            shutil.rmtree(dest)
        rels = files or [p for p in self.data["artifacts"].values()
                         if (ws / p).is_file()]
        manifest = []
        for rel in rels:
            src = ws / rel
            if not src.is_file():
                raise CheckError(f"snapshot source missing: {src}")
            out = dest / rel
            out.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, out)
            manifest.append({"path": str(rel).replace("\\", "/"),
                             "sha256": hashlib.sha256(
                                 src.read_bytes()).hexdigest()})
        (dest / "manifest.json").write_text(
            json.dumps({"label": label, "ts": now(), "files": manifest},
                       indent=1), encoding="utf-8")
        self._log("snapshot", label=label, files=len(manifest))
        return {"label": label, "files": manifest}

    def restore(self, label: str) -> dict:
        ws = self._workspace()
        dest = ws / SNAP_DIR / label
        man = checklib.load_json(dest / "manifest.json",
                                 f"snapshot {label} manifest")
        restored = []
        for f in man["files"]:
            src = dest / f["path"]
            if not src.is_file():
                raise CheckError(f"snapshot file missing: {src}")
            target = ws / f["path"]
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, target)
            if hashlib.sha256(target.read_bytes()).hexdigest() != f["sha256"]:
                raise CheckError(f"restore hash mismatch for {f['path']}")
            restored.append(f["path"])
        self._log("restore", label=label, files=len(restored))
        return {"label": label, "restored": restored}

    # ---- resume ----------------------------------------------------------
    def resume_summary(self) -> dict:
        gates = self.data["gates"]
        passed = [g for _, g in GATE_ORDER
                  if gates.get(g, {}).get("status") == "pass"]
        next_gate = None
        for ph, g in GATE_ORDER:
            if gates.get(g, {}).get("status") != "pass":
                next_gate = {"phase": ph, "gate": g}
                break
        open_issues = [i for i in self.data["open_issues"]
                       if i["status"] in ("open", "fixing")]
        pending_human = [cp for cp, ph in CHECKPOINTS.items()
                         if PHASES.index(self.data["phase"]) >
                         PHASES.index(ph) and cp not in self.data["human"]]
        last = self.data["history"][-1] if self.data["history"] else None
        return {
            "script": SCRIPT, "board": self.data["board"],
            "workspace": self.data["workspace"], "phase": self.data["phase"],
            "gates_passed": passed, "next_gate": next_gate,
            "open_issues": open_issues, "pending_human": sorted(pending_human),
            "budgets": self.data["budgets"],
            "artifacts": self.data["artifacts"], "last_event": last,
        }


# ---- CLI ----------------------------------------------------------------
def _find_state(args) -> Path:
    if getattr(args, "state", None):
        return Path(args.state)
    ws = getattr(args, "workspace", None)
    if ws:
        return Path(ws) / "state.json"
    p = Path("state.json")
    if p.exists():
        return p
    raise CheckError("give --state FILE or --workspace DIR (no ./state.json)")


def run(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)

    def common(p, state_required=True):
        p.add_argument("--state", help="path to state.json")
        p.add_argument("--workspace", help="workspace dir (state.json inside)")
        p.add_argument("--out", help="write result JSON here instead of stdout")

    p = sub.add_parser("init", help="create a new state.json")
    p.add_argument("--workspace", required=True)
    p.add_argument("--board", required=True)
    p.add_argument("--phase", default="P0")
    p.add_argument("--force", action="store_true")
    p.add_argument("--out")

    for name in ("show", "resume"):
        common(sub.add_parser(name))

    p = sub.add_parser("set-phase")
    common(p)
    p.add_argument("--phase", required=True)

    p = sub.add_parser("record-gate")
    common(p)
    p.add_argument("--gate", required=True)
    p.add_argument("--result", required=True,
                   help="gate.py result JSON (has status/failing_count)")
    p.add_argument("--phase")

    p = sub.add_parser("artifact")
    common(p)
    p.add_argument("--name", required=True)
    p.add_argument("--path", required=True)

    p = sub.add_parser("decision")
    common(p)
    p.add_argument("--what", required=True)
    p.add_argument("--why", required=True)
    p.add_argument("--phase")

    p = sub.add_parser("human")
    common(p)
    p.add_argument("--checkpoint", required=True)
    p.add_argument("--status", required=True)
    p.add_argument("--note")

    p = sub.add_parser("issue")
    common(p)
    p.add_argument("--id", type=int, required=True)
    p.add_argument("--status")
    p.add_argument("--agent")
    p.add_argument("--bump-attempts", action="store_true")

    p = sub.add_parser("budget")
    common(p)
    p.add_argument("--path", required=True, dest="bpath",
                   help="dotted path, e.g. fix_loops.drc_routed")
    p.add_argument("--consume", action="store_true")

    p = sub.add_parser("log")
    common(p)
    p.add_argument("--event", required=True)
    p.add_argument("--data", help="extra JSON object merged into the event")

    p = sub.add_parser("snapshot")
    common(p)
    p.add_argument("--label", required=True)
    p.add_argument("--files", nargs="*",
                   help="workspace-relative files (default: file artifacts)")

    p = sub.add_parser("restore")
    common(p)
    p.add_argument("--label", required=True)

    args = ap.parse_args(argv)

    if args.cmd == "init":
        st = State.init(Path(args.workspace), args.board, args.phase,
                        args.force)
        return {"script": SCRIPT, "cmd": "init", "state": str(st.path),
                "board": args.board, "phase": args.phase,
                "subdirs": list(SUBDIRS)}, args.out

    st = State.load(_find_state(args))
    result: dict = {"script": SCRIPT, "cmd": args.cmd}

    if args.cmd == "show":
        return {**result, **st.data}, args.out
    if args.cmd == "resume":
        return {**result, **st.resume_summary()}, args.out

    if args.cmd == "set-phase":
        warnings = st.set_phase(args.phase)
        result["phase"] = args.phase
        if warnings:
            result["warnings"] = warnings
    elif args.cmd == "record-gate":
        gres = checklib.load_json(args.result, "gate result")
        g = st.record_gate(args.gate, gres, args.phase)
        result.update(gate=args.gate, status=g["status"],
                      attempts=g["attempts"])
    elif args.cmd == "artifact":
        st.set_artifact(args.name, args.path)
        result.update(name=args.name, path=args.path)
    elif args.cmd == "decision":
        st.add_decision(args.what, args.why, args.phase)
        result.update(what=args.what)
    elif args.cmd == "human":
        st.record_human(args.checkpoint, args.status, args.note)
        result.update(checkpoint=args.checkpoint, status=args.status)
    elif args.cmd == "issue":
        rec = st.update_issue(args.id, args.status, args.agent,
                              args.bump_attempts)
        result.update(issue=rec)
    elif args.cmd == "budget":
        remaining = st.budget(args.bpath, args.consume)
        result.update(path=args.bpath, remaining=remaining)
    elif args.cmd == "log":
        extra = json.loads(args.data) if args.data else {}
        if not isinstance(extra, dict):
            raise CheckError("--data must be a JSON object")
        st._log(args.event, **extra)
        result.update(event=args.event)
    elif args.cmd == "snapshot":
        result.update(st.snapshot(args.label, args.files))
    elif args.cmd == "restore":
        result.update(st.restore(args.label))

    st.save()
    result["phase"] = st.data["phase"]
    return result, args.out


def main(argv=None) -> int:
    checklib.utf8_stdout()
    try:
        payload, out = run(argv)
    except SystemExit:
        raise
    except Exception as exc:  # noqa: BLE001  (spec 6: any error -> exit 2)
        print(json.dumps({"script": SCRIPT, "status": "error",
                          "error": f"{type(exc).__name__}: {exc}"}))
        return 2
    text = json.dumps(payload, indent=1)
    if out:
        Path(out).parent.mkdir(parents=True, exist_ok=True)
        Path(out).write_text(text, encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
