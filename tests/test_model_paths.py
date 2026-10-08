"""3D model paths that survive a checkout move (check_model_paths.py, the
kc.py helpers it shares with render's relink, and lib_pull's rewrite).

Eleven boards named their models by absolute path into the track worktree
that built them; once the worktree went, the models were gone. Everything
here runs on small fixtures; one test repairs a /tmp copy of a real board and
skips without the boards repo.
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / ".claude" / "skills" / "hwde" / "scripts"
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(SCRIPTS / "lib"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import check_model_paths as cmp  # noqa: E402
import kc  # noqa: E402
import lib_pull  # noqa: E402
import verify_all  # noqa: E402

GONE = "/gone/worktrees/boards/t/ws/lib/aiee.3dshapes"
STOCK = "${KICAD10_3DMODEL_DIR}/Connector_PinHeader_2.54mm.3dshapes/H.step"


def _fp(ref: str, at: str, *models: str) -> str:
    ms = "".join(f'\t\t(model "{m}"\n\t\t\t(offset (xyz 0 0 0))\n\t\t)\n'
                 for m in models)
    return (f'\t(footprint "aiee:{ref}"\n\t\t(layer "F.Cu")\n'
            f'\t\t(at {at})\n\t\t(property "Reference" "{ref}"\n'
            f'\t\t\t(at 0 -2 0)\n\t\t)\n{ms}\t)\n')


def _ws(tmp_path: Path, *fps: str, state: bool = True) -> Path:
    """<ws>/kicad/b.kicad_pcb with <ws>/lib/aiee.3dshapes holding R.wrl and
    USBC.wrl, and <ws>/lib/aiee.pretty/R.kicad_mod naming R.wrl absolutely."""
    ws = tmp_path / "ws"
    shapes = ws / "lib" / "aiee.3dshapes"
    shapes.mkdir(parents=True)
    for n in ("R.wrl", "USBC.wrl"):
        (shapes / n).write_text("#VRML V2.0 utf8\n", encoding="utf-8")
    pretty = ws / "lib" / "aiee.pretty"
    pretty.mkdir()
    (pretty / "R.kicad_mod").write_text(
        f'(footprint "R"\n\t(model "{GONE}/R.wrl"\n\t)\n)\n', encoding="utf-8")
    (ws / "kicad").mkdir()
    if state:
        (ws / "state.json").write_text("{}", encoding="utf-8")
    pcb = ws / "kicad" / "b.kicad_pcb"
    pcb.write_text("(kicad_pcb\n\t(version 20241229)\n" + "".join(fps) + ")\n",
                   encoding="utf-8")
    return pcb


# ------------------------------------------------------------ kc helpers

@pytest.mark.parametrize("path,kind", [
    (STOCK, None),
    ("${KICAD9_3DMODEL_DIR}/X.3dshapes/Y.step", None),
    ("${KIPRJMOD}/../lib/aiee.3dshapes/R.wrl", None),
    ("${KIPRJMOD}/lib/aiee.3dshapes/R.wrl", None),
    (f"{GONE}/R.wrl", "absolute"),
    ("C:/dev/ai-ee3/boards/b/lib/aiee.3dshapes/R.wrl", "absolute"),
    ("C:\\\\dev\\\\b\\\\R.wrl", "absolute"),
    ("${KIPRJMOD}/../../../lib/aiee.3dshapes/R.wrl", "outside_workspace"),
    ("boards/b/lib/aiee.3dshapes/R.wrl", "unanchored"),
    ("${SOME_VAR}/R.wrl", "unanchored"),
])
def test_model_path_kind(tmp_path, path, kind):
    ws = tmp_path / "boards" / "ws"
    (ws / "kicad").mkdir(parents=True)
    assert kc.model_path_kind(path, ws / "kicad", ws) == kind


def test_model_paths_portable_rewrites_only_what_the_lib_holds(tmp_path):
    pcb = _ws(tmp_path)
    proj, ws = pcb.parent, pcb.parent.parent
    text = (f'(model "{GONE}/R.wrl")\n(model "{GONE}/R.wrl")\n'
            f'(model "/elsewhere/Missing.wrl")\n(model "{STOCK}")\n')
    new, done = kc.model_paths_portable(text, proj, ws, kc.model_libs(proj))
    rel = "${KIPRJMOD}/../lib/aiee.3dshapes/R.wrl"
    assert done == {f"{GONE}/R.wrl": rel}
    assert new.count(f'(model "{rel}")') == 2
    assert '(model "/elsewhere/Missing.wrl")' in new and STOCK in new
    # already portable: nothing to do
    assert kc.model_paths_portable(new, proj, ws, kc.model_libs(proj)) \
        == (new, {})


def test_portable_path_for_a_lib_beside_the_board(tmp_path):
    (tmp_path / "lib" / "x.3dshapes").mkdir(parents=True)
    f = tmp_path / "lib" / "x.3dshapes" / "A.wrl"
    f.write_text("", encoding="utf-8")
    assert kc.model_lib_file("/old/A.wrl", kc.model_libs(tmp_path)) == f
    assert kc.portable_model_path(f, tmp_path) == "${KIPRJMOD}/lib/x.3dshapes/A.wrl"


# ------------------------------------------------------------ the check

def test_check_flags_absolute_once_per_path_with_a_fix_line(tmp_path):
    pcb = _ws(tmp_path,
              _fp("R1", "10 20", f"{GONE}/R.wrl"),
              _fp("R2", "30 20", f"{GONE}/R.wrl"),
              _fp("J1", "50 20", STOCK),
              _fp("U1", "70 20", "/elsewhere/Missing.wrl"))
    payload, _ = cmp.run(["--pcb", str(pcb)])
    assert payload["status"] == "violations"
    by = {v["model_path"]: v for v in payload["violations"]}
    assert set(by) == {f"{GONE}/R.wrl", "/elsewhere/Missing.wrl"}
    r = by[f"{GONE}/R.wrl"]
    assert r["kind"] == "model_path_absolute" and r["severity"] == "error"
    assert r["refs"] == ["R1", "R2"] and r["pos"] == [10.0, 20.0]
    assert r["fixable"] and "--fix" in r["fix"]
    assert "${KIPRJMOD}/../lib/aiee.3dshapes/R.wrl" in r["msg"]
    u = by["/elsewhere/Missing.wrl"]
    assert not u["fixable"] and "lib_pull.py" in u["fix"]
    assert payload["workspace"] == str(pcb.parent.parent)


def test_check_flags_outside_workspace_and_unanchored(tmp_path):
    pcb = _ws(tmp_path,
              _fp("R1", "0 0", "${KIPRJMOD}/../../../lib/aiee.3dshapes/R.wrl"),
              _fp("R2", "1 0", "boards/b/lib/aiee.3dshapes/R.wrl"))
    kinds = sorted(v["kind"] for v in cmp.run(["--pcb", str(pcb)])[0]
                   ["violations"])
    assert kinds == ["model_path_outside_workspace", "model_path_unanchored"]


def test_clean_board_passes(tmp_path):
    pcb = _ws(tmp_path, _fp("R1", "0 0",
                            "${KIPRJMOD}/../lib/aiee.3dshapes/R.wrl"),
              _fp("J1", "1 0", STOCK))
    payload, _ = cmp.run(["--pcb", str(pcb)])
    assert payload["status"] == "pass" and "fixed" not in payload


def test_fix_rewrites_board_and_lib_footprints_and_is_idempotent(tmp_path):
    pcb = _ws(tmp_path,
              _fp("R1", "10 20", f"{GONE}/R.wrl"),
              _fp("J1", "50 20", f"{GONE}/USBC.wrl"),
              _fp("U1", "70 20", "/elsewhere/Missing.wrl"))
    # a CRLF board stays CRLF: only the path text changes
    pcb.write_bytes(pcb.read_bytes().replace(b"\n", b"\r\n"))
    before = pcb.read_bytes()
    payload, _ = cmp.run(["--pcb", str(pcb), "--fix"])
    fixed = payload["fixed"]
    assert fixed[str(pcb)] == {
        f"{GONE}/R.wrl": "${KIPRJMOD}/../lib/aiee.3dshapes/R.wrl",
        f"{GONE}/USBC.wrl": "${KIPRJMOD}/../lib/aiee.3dshapes/USBC.wrl"}
    mod = pcb.parent.parent / "lib" / "aiee.pretty" / "R.kicad_mod"
    assert str(mod) in fixed
    assert "${KIPRJMOD}/../lib/aiee.3dshapes/R.wrl" in mod.read_text("utf-8")
    after = pcb.read_bytes()
    assert after.count(b"\r\n") == before.count(b"\r\n")
    assert before.replace(GONE.encode(),
                          b"${KIPRJMOD}/../lib/aiee.3dshapes") == after
    # the unfixable path stays and is still reported
    assert [v["model_path"] for v in payload["violations"]] == \
        ["/elsewhere/Missing.wrl"]
    assert kc.model_audit(pcb)["missing"] == ["/elsewhere/Missing.wrl"]
    again, _ = cmp.run(["--pcb", str(pcb), "--fix"])
    assert again["fixed"] == {} and pcb.read_bytes() == after


def test_workspace_falls_back_to_the_dir_holding_lib(tmp_path):
    pcb = _ws(tmp_path, state=False)
    assert cmp.workspace_of(pcb) == pcb.parent.parent
    bare = tmp_path / "bare" / "b.kicad_pcb"
    bare.parent.mkdir()
    bare.write_text("(kicad_pcb)", encoding="utf-8")
    assert cmp.workspace_of(bare) == bare.parent.resolve()


def test_cli_exit_codes(tmp_path, capsys):
    pcb = _ws(tmp_path, _fp("R1", "0 0", f"{GONE}/R.wrl"))
    out = tmp_path / "r.json"
    assert cmp.main(["--pcb", str(pcb), "--out", str(out)]) == 1
    assert json.loads(out.read_text("utf-8"))["counts"]["total"] == 1
    assert cmp.main(["--pcb", str(pcb), "--fix", "--out", str(out)]) == 0
    assert cmp.main(["--pcb", str(tmp_path / "nope.kicad_pcb")]) == 2
    assert '"status": "error"' in capsys.readouterr().out


def test_registered_in_verify_suite():
    names = [c["name"] for c in verify_all.load_checks()]
    assert "check_model_paths" in names


# ------------------------------------------------------------ lib_pull

def test_lib_pull_writes_kiprjmod_relative_models(tmp_path):
    pcb = _ws(tmp_path)
    lib = pcb.parent.parent / "lib"
    r = lib_pull._portable_models(lib / "aiee.pretty", lib / "aiee.3dshapes",
                                  pcb.parent)
    assert r == {"rewritten": 1, "footprints": {
        "R.kicad_mod": ["${KIPRJMOD}/../lib/aiee.3dshapes/R.wrl"]}}
    assert lib_pull._portable_models(lib / "aiee.pretty",
                                     lib / "aiee.3dshapes",
                                     pcb.parent)["rewritten"] == 0


def test_lib_pull_rewrites_for_a_new_explicit_project(tmp_path):
    # --project <new>/kicad does not exist until _register_project runs
    pcb = _ws(tmp_path)
    lib = pcb.parent.parent / "lib"
    new = pcb.parent.parent / "kicad-new"
    r = lib_pull._portable_models(lib / "aiee.pretty", lib / "aiee.3dshapes",
                                  new, explicit=True)
    assert r == {"rewritten": 1, "footprints": {
        "R.kicad_mod": ["${KIPRJMOD}/../lib/aiee.3dshapes/R.wrl"]}}
    assert not new.exists()


def test_lib_pull_leaves_paths_without_a_project(tmp_path):
    pcb = _ws(tmp_path)
    lib = pcb.parent.parent / "lib"
    r = lib_pull._portable_models(lib / "aiee.pretty", lib / "aiee.3dshapes",
                                  tmp_path / "no-such-kicad")
    assert r["rewritten"] == 0 and "left absolute" in r["skipped"]
    r = lib_pull._portable_models(lib / "aiee.pretty", lib / "none.3dshapes",
                                  pcb.parent)
    assert r["rewritten"] == 0 and "--no-3d" in r["skipped"]
    assert GONE in (lib / "aiee.pretty" / "R.kicad_mod").read_text("utf-8")


# ------------------------------------------------------------ a real board

def test_fix_on_a_copy_of_a_real_board(tmp_path):
    import _boards
    src = _boards.real_board("esp32c3-node")
    pcbs = sorted((src / "kicad").glob("*.kicad_pcb"))
    if not pcbs or not (src / "lib").is_dir():
        pytest.skip(f"{src} has no kicad/*.kicad_pcb or lib/")
    ws = tmp_path / src.name
    (ws / "kicad").mkdir(parents=True)
    shutil.copytree(src / "lib", ws / "lib")
    shutil.copy2(pcbs[0], ws / "kicad" / pcbs[0].name)
    (ws / "state.json").write_text("{}", encoding="utf-8")
    pcb = ws / "kicad" / pcbs[0].name
    payload, _ = cmp.run(["--pcb", str(pcb), "--fix"])
    assert payload["status"] == "pass", payload["violations"][:3]
    missing = kc.model_audit(pcb)["missing"]
    assert all(m.startswith("${KICAD") for m in missing), missing
