"""check_model_paths.py - every 3D model path in a board survives a checkout
move (P8 verify suite).

The hit: eleven boards in the boards repo name their footprints' models by
absolute path into the track worktree that built them
(`/.../worktrees/boards/<track>/<ws>/lib/aiee.3dshapes/X.wrl`). Once that
worktree is removed the path is dead, STEP export drops the part and a doc's
render shows the USB-C wrong or missing. lib_pull.py now writes
${KIPRJMOD}-relative paths; this check catches every board made before that,
and anything else that bakes a path in.

A model path passes when it is
  ${KICAD<n>_3DMODEL_DIR}/...   the stock KiCad library, or
  ${KIPRJMOD}/...               relative to the board's dir and staying inside
                                the board's workspace (state.json above it;
                                without one, the dir holding lib/).
Anything else is an error, one finding per distinct path (refs = every
footprint that uses it, pos = the first one), kind:
  model_path_absolute           /home/.., C:/.., \\\\host\\..
  model_path_outside_workspace  ${KIPRJMOD}/ climbing out of the workspace
  model_path_unanchored         a bare relative path, or any other ${VAR}
Whether the file exists today does not matter: a path into a live worktree
resolves until the day that worktree goes. A path whose file is missing is
render's concern (kc.model_audit), not this check's.

--fix rewrites each failing path whose file the workspace's own
lib/*.3dshapes holds, by name, to ${KIPRJMOD}/<rel>/lib/<x>.3dshapes/<name>,
in the board and in the workspace's lib/*.pretty footprints (so the next
footprint update does not bring the old path back). It uses the name lookup
render's relink uses (kc.model_libs / kc.model_lib_file). The report is then
taken on the rewritten board; `fixed` lists what changed. A path with no file
in the lib stays and is still reported.

CLI: --pcb board.kicad_pcb [--fix] [--out report.json]
     exit 0 pass / 1 violations / 2 error, per SPEC section 6.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import sexpdata

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "lib"))
import checklib  # noqa: E402
import kc  # noqa: E402
import statelib  # noqa: E402

SCRIPT = "check_model_paths"
KINDS = {"absolute": "model_path_absolute",
         "outside_workspace": "model_path_outside_workspace",
         "unanchored": "model_path_unanchored"}


def _head(node) -> str | None:
    if isinstance(node, list) and node and isinstance(node[0], sexpdata.Symbol):
        return node[0].value()
    return None


def _sval(x) -> str:
    return x.value() if isinstance(x, sexpdata.Symbol) else str(x)


def board_models(pcb: Path) -> list[tuple[str, tuple, str]]:
    """(ref, (x, y), model path) for every model of every footprint, in
    board order."""
    data = sexpdata.loads(_read(pcb))
    out = []
    for node in data[1:]:
        if _head(node) != "footprint":
            continue
        ref, pos, models = None, None, []
        for sub in node[1:]:
            h = _head(sub)
            if h == "property" and len(sub) >= 3 \
                    and _sval(sub[1]) == "Reference":
                ref = _sval(sub[2])
            elif h == "at" and len(sub) >= 3:
                pos = (float(sub[1]), float(sub[2]))
            elif h == "model" and len(sub) >= 2:
                models.append(_sval(sub[1]))
        out += [(ref or "?", pos, m) for m in models]
    return out


def workspace_of(pcb: Path) -> Path:
    """The board's workspace: the dir holding state.json above it, else the
    dir holding lib/ (the board's own or its parent), else the board's dir."""
    ws = statelib.find_workspace(pcb)
    if ws:
        return ws
    base = pcb.resolve().parent
    return next((r for r in (base, base.parent) if (r / "lib").is_dir()), base)


def _read(p: Path) -> str:
    # newline="" keeps a CRLF board byte-identical outside the rewritten paths
    with open(p, encoding="utf-8", newline="") as fh:
        return fh.read()


def _write(p: Path, text: str) -> None:
    with open(p, "w", encoding="utf-8", newline="") as fh:
        fh.write(text)


def fix(pcb: Path, ws: Path) -> dict:
    """Rewrite the board's and the workspace lib footprints' failing model
    paths that the workspace lib holds by name. Returns {file: {old: new}}."""
    project = pcb.resolve().parent
    libs = kc.model_libs(project)
    files = [pcb] + sorted({f for d in libs
                            for f in d.parent.glob("*.pretty/*.kicad_mod")})
    done: dict[str, dict[str, str]] = {}
    for f in files:
        text = _read(f)
        new, changed = kc.model_paths_portable(text, project, ws, libs)
        if changed:
            _write(f, new)
            done[str(f)] = changed
    return done


def check(pcb: Path, ws: Path) -> list[dict]:
    project = pcb.resolve().parent
    libs = kc.model_libs(project)
    by_path: dict[str, dict] = {}
    for ref, pos, path in board_models(pcb):
        why = kc.model_path_kind(path, project, ws)
        if why is None:
            continue
        hit = by_path.setdefault(path, {"why": why, "refs": [], "pos": pos})
        if ref not in hit["refs"]:
            hit["refs"].append(ref)
    viols = []
    for path, h in by_path.items():
        name = path.replace("\\", "/").rsplit("/", 1)[-1]
        lib_file = kc.model_lib_file(path, libs)
        if lib_file:
            new = kc.portable_model_path(lib_file, project)
            fix_line = (f"check_model_paths.py --pcb {pcb} --fix rewrites it "
                        f"to {new}")
        else:
            fix_line = (f"put {name} in {ws / 'lib'}/<lib>.3dshapes/ (re-pull "
                        f"the part with lib_pull.py, or copy it in), then run "
                        f"check_model_paths.py --pcb {pcb} --fix; a stock "
                        f"KiCad model takes ${{KICAD10_3DMODEL_DIR}}/...")
        kind = KINDS[h["why"]]
        refs = h["refs"]
        msg = (f"{', '.join(refs[:6])}{' ...' if len(refs) > 6 else ''}: "
               f"3D model path {path} is {h['why'].replace('_', ' ')} - it "
               f"breaks once that checkout moves. Fix: {fix_line}")
        viols.append(checklib.violation(
            SCRIPT, "error", h["pos"], None, None, refs, msg, SCRIPT,
            kind=kind, model_path=path, fixable=bool(lib_file),
            fix=fix_line))
    return viols


def run(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--pcb", required=True)
    ap.add_argument("--fix", action="store_true",
                    help="rewrite failing paths the workspace lib holds by "
                         "name, in the board and its lib footprints")
    ap.add_argument("--out", help="write the JSON report here")
    args = ap.parse_args(argv)
    pcb = Path(args.pcb)
    if not pcb.is_file():
        raise checklib.CheckError(f"board not found: {pcb}")
    ws = workspace_of(pcb)
    fixed = fix(pcb, ws) if args.fix else None
    viols = check(pcb, ws)
    facts = {"workspace": str(ws),
             "model_libs": [str(d) for d in kc.model_libs(pcb.resolve().parent)]}
    if fixed is not None:
        facts["fixed"] = fixed
    return checklib.report(SCRIPT, pcb, viols, **facts), args.out


def main(argv=None) -> int:
    return checklib.cli_wrap(SCRIPT, lambda: run(argv))


if __name__ == "__main__":
    sys.exit(main())
