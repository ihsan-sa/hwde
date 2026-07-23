"""place_edit - apply an atomic footprint move/rotate/flip/lock op list (S9, SPEC P6.3).

The pipeline's ONLY writer for placement changes (SPEC section 4: op lists are
applied atomically; agents never raw-edit the board). Edit path decision (V4/V8,
recorded in PROGRESS S9): SWIG bundled python, headless - the spec's "IPC
headless" does not exist at the KiCad-10 pin (no api-server; kipy needs a GUI
pcbnew and the sandboxed-GUI probe now fails "KiCad is not ready to reply").
kipy/IPC is the KiCad-11 migration target.

Contract:
  place_edit.py --pcb B.kicad_pcb --ops ops.json [--out-report r.json]
  ops.json: {"version": 1, "ops": [...]}  (op shapes: see lib/place_swig.py)

Atomic + rollback: ops are validated first (schema + refs against the board);
the board is copied to a scratch dir INSIDE the board's directory; the SWIG
worker edits and saves the copy; the driver re-parses the copy and verifies
every op's target landed (position 1e-3 mm, angle 0.05 deg, side, locked);
only then does os.replace() swap it in (same volume -> atomic). Any failure
leaves the original board byte-identical. Re-applying the same op list is
idempotent (ops are absolute). exit 0 applied+verified / 2 error (rolled back).

Note: KiCad regenerates footprint/graphic UUIDs on every save, so two saves of
the same placement are NOT byte-identical - compare parsed positions, never
file hashes.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS / "lib"))

import checklib  # noqa: E402
import env  # noqa: E402
import placelib  # noqa: E402
from checklib import CheckError  # noqa: E402

WORKER = SCRIPTS / "lib" / "place_swig.py"

OP_FIELDS = {  # op -> (required, optional)
    "place": ({"ref", "x", "y"}, {"deg", "side"}),
    "move": ({"ref", "x", "y"}, set()),
    "rotate": ({"ref", "deg"}, set()),
    "flip": ({"ref", "side"}, set()),
    "lock": ({"ref", "locked"}, set()),
}
POS_TOL = 1e-3   # mm
ANG_TOL = 0.05   # deg


def validate_ops(doc: dict) -> list[dict]:
    if not isinstance(doc, dict) or doc.get("version") != 1:
        raise CheckError("ops file must be {'version': 1, 'ops': [...]}")
    ops = doc.get("ops")
    if not isinstance(ops, list) or not ops:
        raise CheckError("ops list is empty")
    for i, op in enumerate(ops):
        kind = op.get("op")
        if kind not in OP_FIELDS:
            raise CheckError(f"ops[{i}]: unknown op '{kind}'")
        req, opt = OP_FIELDS[kind]
        missing = req - op.keys()
        if missing:
            raise CheckError(f"ops[{i}] ({kind}): missing {sorted(missing)}")
        unknown = op.keys() - req - opt - {"op"}
        if unknown:
            raise CheckError(f"ops[{i}] ({kind}): unknown keys {sorted(unknown)}")
        for k in ("x", "y", "deg"):
            if k in op and not (isinstance(op[k], (int, float))
                                and math.isfinite(op[k])):
                raise CheckError(f"ops[{i}]: {k} must be a finite number")
        if "side" in op and op["side"] not in ("front", "back"):
            raise CheckError(f"ops[{i}]: side must be front|back")
        if "locked" in op and not isinstance(op["locked"], bool):
            raise CheckError(f"ops[{i}]: locked must be a boolean")
    return ops


def _expected_state(ops: list[dict]) -> dict[str, dict]:
    """Fold the op list into the final expected {ref: {x,y,deg,side,locked}}."""
    want: dict[str, dict] = {}
    for op in ops:
        w = want.setdefault(op["ref"], {})
        if op["op"] in ("place", "move"):
            w["x"], w["y"] = op["x"], op["y"]
        if op["op"] in ("place", "rotate") and op.get("deg") is not None:
            w["deg"] = op["deg"]
        if op["op"] in ("place", "flip") and op.get("side") is not None:
            w["side"] = op["side"]
        if op["op"] == "lock":
            w["locked"] = op["locked"]
    return want


def _verify(pcb: Path, ops: list[dict]) -> list[str]:
    model = placelib.PlaceModel(pcb)
    problems = []
    for ref, w in _expected_state(ops).items():
        fp = model.footprints.get(ref)
        if fp is None:
            problems.append(f"{ref}: vanished from saved board")
            continue
        if "x" in w and (abs(fp.pos[0] - w["x"]) > POS_TOL
                         or abs(fp.pos[1] - w["y"]) > POS_TOL):
            problems.append(f"{ref}: position {fp.pos} != ({w['x']}, {w['y']})")
        if "deg" in w and _angdiff(fp.angle, w["deg"]) > ANG_TOL:
            problems.append(f"{ref}: angle {fp.angle} != {w['deg']}")
        if "side" in w and fp.side != w["side"]:
            problems.append(f"{ref}: side {fp.side} != {w['side']}")
        if "locked" in w and fp.locked != w["locked"]:
            problems.append(f"{ref}: locked {fp.locked} != {w['locked']}")
    return problems


def _angdiff(a: float, b: float) -> float:
    d = abs(a - b) % 360.0
    return min(d, 360.0 - d)


def apply_ops(pcb: Path, ops: list[dict]) -> dict:
    """Validate refs, stage, run the SWIG worker, verify, atomically swap in.

    Returns the worker's per-op results. Raises CheckError (original board
    untouched) on any failure. Importable - place_seed --apply uses this.
    """
    pcb = Path(pcb).resolve()
    if not pcb.is_file():
        raise CheckError(f"board not found: {pcb}")
    model = placelib.PlaceModel(pcb)
    missing = sorted({op["ref"] for op in ops} - model.footprints.keys())
    if missing:
        raise CheckError(f"refs not on board: {', '.join(missing)}")

    cli = env.find_kicad_cli()
    bp = env.find_kicad_python(cli) if cli else None
    if bp is None:
        raise CheckError("KiCad bundled python not found (env.py)")

    stage = Path(tempfile.mkdtemp(prefix=".aiee_edit_", dir=pcb.parent))
    try:
        staged = stage / pcb.name
        shutil.copy2(pcb, staged)
        job = {"board": str(staged), "out": str(staged), "ops": ops}
        jf = stage / "job.json"
        jf.write_text(json.dumps(job), encoding="utf-8")
        cp = subprocess.run([str(bp), str(WORKER), str(jf)],
                            capture_output=True, text=True, encoding="utf-8",
                            errors="replace", timeout=180)
        out = (cp.stdout or "").strip().splitlines()
        try:
            result = json.loads(out[-1]) if out else {}
        except json.JSONDecodeError:
            result = {}
        if cp.returncode != 0 or not result.get("ok"):
            detail = result.get("error") or (cp.stderr or "").strip()[-300:] \
                or f"worker exit {cp.returncode}"
            idx = result.get("index")
            at = f" at ops[{idx}]" if idx is not None else ""
            raise CheckError(f"worker failed{at}: {detail} (rolled back)")
        problems = _verify(staged, ops)
        if problems:
            raise CheckError("post-apply verify failed (rolled back): "
                             + "; ".join(problems))
        os.replace(staged, pcb)
        return result["results"]
    finally:
        shutil.rmtree(stage, ignore_errors=True)


def run(argv: list[str] | None = None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--pcb", required=True)
    ap.add_argument("--ops", required=True)
    ap.add_argument("--out-report", default=None)
    args = ap.parse_args(argv)

    ops = validate_ops(checklib.load_json(args.ops, "ops file"))
    results = apply_ops(Path(args.pcb), ops)
    payload = {"script": "place_edit", "status": "pass", "board": args.pcb,
               "applied": len(ops), "verified": True, "results": results}
    return payload, args.out_report


def main(argv: list[str] | None = None) -> int:
    return checklib.cli_wrap("place_edit", lambda: run(argv))


if __name__ == "__main__":
    sys.exit(main())
