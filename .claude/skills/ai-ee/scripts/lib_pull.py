#!/usr/bin/env python
"""lib_pull.py - pull a part's KiCad symbol/footprint/3D via easyeda2kicad and
register it in the project library tables (SPEC.md P3, 6.1).

Wraps `easyeda2kicad --full --lcsc_id=Cxxxx --output <base>`, which writes
  <base>.kicad_sym            (symbol library)
  <base>.pretty/<fp>.kicad_mod (footprints, LEGACY (module ...) format)
  <base>.3dshapes/<name>.{wrl,step}
then appends the libraries to <project>/fp-lib-table + sym-lib-table (idempotent).
Footprints load in KiCad 10 despite the legacy format (LEARNINGS 2026-07-22
[easyeda2kicad]); --verify-load confirms it with `kicad-cli fp export svg`.

Contract (SPEC section 6): argparse, JSON to stdout or --out, exit 0/1/2.
  0 = every requested part pulled (or already present)
  1 = one or more parts failed to pull
  2 = internal error / bad arguments

Examples:
  lib_pull.py --lcsc C1525
  lib_pull.py --lcsc C8734 C25804 --out-dir board/lib --project board/kicad --verify-load
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "lib"))
import fplib  # noqa: E402
from lib import env  # noqa: E402


def _run_easyeda(lcsc: str, base: Path, no_3d: bool, overwrite: bool) -> subprocess.CompletedProcess:
    cmd = [sys.executable, "-m", "easyeda2kicad",
           f"--lcsc_id={lcsc}", "--output", str(base)]
    cmd += ["--symbol", "--footprint"] if no_3d else ["--full"]
    if overwrite:
        cmd.append("--overwrite")
    return subprocess.run(cmd, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=120)


def _footprints_for_lcsc(pretty_dir: Path, lcsc: str) -> list[Path]:
    """Footprint files carrying this LCSC id (via the (property "LCSC Part" ..))."""
    hits = []
    for fp in fplib.footprint_files(pretty_dir):
        try:
            if lcsc in fp.read_text(encoding="utf-8", errors="replace"):
                hits.append(fp)
        except OSError:
            continue
    return hits


def _pull_one(lcsc: str, base: Path, no_3d: bool, overwrite: bool) -> dict:
    sym_lib = base.with_suffix(".kicad_sym")
    pretty = Path(str(base) + ".pretty")
    try:
        cp = _run_easyeda(lcsc, base, no_3d, overwrite)
    except subprocess.TimeoutExpired:
        return {"lcsc": lcsc, "status": "error", "detail": "easyeda2kicad timed out (network?)"}
    log = (cp.stdout or "") + (cp.stderr or "")

    fps = _footprints_for_lcsc(pretty, lcsc)
    already = "already exists" in log
    created = "Created Kicad footprint" in log or "Created Kicad symbol" in log
    if not fps and not sym_lib.exists():
        return {"lcsc": lcsc, "status": "error",
                "detail": (log.strip()[-400:] or f"easyeda2kicad rc={cp.returncode}, "
                           "no library files produced")}

    warnings = []
    fp_reports = []
    for fp in fps:
        try:
            f = fplib.parse_footprint(fp)
        except Exception as exc:  # noqa: BLE001
            warnings.append(f"could not parse {fp.name}: {exc}")
            continue
        if not f.has_courtyard:
            warnings.append(f"{f.name}: no courtyard layer (easyeda2kicad "
                            "footprints sometimes omit it; DRC courtyard checks degrade)")
        fp_reports.append({
            "name": f.name,
            "file": str(fp),
            "copper_pads": len(f.copper_pads),
            "courtyard": f.has_courtyard,
            "silk": f.has_layer_kind("SilkS"),
        })
    return {
        "lcsc": lcsc,
        "status": "exists" if (already and not created) else "pulled",
        "symbol_lib": str(sym_lib) if sym_lib.exists() else None,
        "footprint_lib": str(pretty) if pretty.is_dir() else None,
        "footprints": fp_reports,
        "warnings": warnings,
    }


# ---------------------------------------------------------- lib-table registration

def _uri_for(target: Path, project: Path | None) -> str:
    """A KiCad lib-table URI: ${KIPRJMOD}-relative (portable) when possible.

    Uses os.path.relpath so a lib SIBLING of the project dir resolves to
    ${KIPRJMOD}/../lib/... (KiCad expands the .. fine). Falls back to an absolute
    path only across drives (relpath raises ValueError on win32).
    """
    import os
    t = target.resolve()
    if project is not None:
        try:
            rel = os.path.relpath(t, project.resolve())
            return "${KIPRJMOD}/" + Path(rel).as_posix()
        except ValueError:
            pass
    return t.as_posix()


def _register(table_path: Path, table_head: str, nickname: str, uri: str) -> str:
    """Append a lib entry to an fp-/sym-lib-table (create if absent, idempotent).

    Returns "added" | "present" | "created".
    """
    line = (f'  (lib (name "{nickname}")(type "KiCad")(uri "{uri}")'
            f'(options "")(descr ""))')
    if not table_path.exists():
        table_path.parent.mkdir(parents=True, exist_ok=True)
        table_path.write_text(f"({table_head}\n  (version 7)\n{line}\n)\n",
                              encoding="utf-8")
        return "created"
    text = table_path.read_text(encoding="utf-8", errors="replace")
    if f'(name "{nickname}")' in text:
        return "present"
    idx = text.rstrip().rfind(")")
    if idx < 0:  # malformed - rewrite fresh
        table_path.write_text(f"({table_head}\n  (version 7)\n{line}\n)\n",
                              encoding="utf-8")
        return "created"
    new = text[:idx].rstrip("\n") + "\n" + line + "\n" + text[idx:]
    table_path.write_text(new, encoding="utf-8")
    return "added"


def _register_project(project: Path, nickname: str, sym_lib: Path | None,
                      pretty: Path | None) -> dict:
    project.mkdir(parents=True, exist_ok=True)
    out: dict = {}
    if pretty is not None and pretty.is_dir():
        out["fp"] = _register(project / "fp-lib-table", "fp_lib_table",
                              nickname, _uri_for(pretty, project))
    if sym_lib is not None and sym_lib.exists():
        out["sym"] = _register(project / "sym-lib-table", "sym_lib_table",
                               nickname, _uri_for(sym_lib, project))
    return out


# ---------------------------------------------------------- optional load check

def _verify_load(pretty: Path) -> dict:
    """Confirm KiCad itself parses the pulled footprints (fp export svg)."""
    try:
        cli = env.find_kicad_cli()
    except env.EnvError as exc:
        return {"ok": False, "detail": str(exc)}
    if cli is None:
        return {"ok": False, "detail": "no kicad-cli found"}
    with tempfile.TemporaryDirectory() as td:
        outdir = Path(td) / "svg"
        outdir.mkdir(parents=True, exist_ok=True)  # dir must pre-exist (LEARNINGS)
        try:
            cp = subprocess.run([str(cli), "fp", "export", "svg", str(pretty),
                                 "--output", str(outdir)],
                                capture_output=True, text=True,
                                encoding="utf-8", errors="replace", timeout=120)
        except subprocess.TimeoutExpired:
            return {"ok": False, "detail": "kicad-cli fp export svg timed out"}
        svgs = list(outdir.glob("*.svg"))
        err = "Error creating svg" in (cp.stdout + cp.stderr)
        return {"ok": bool(svgs) and not err,
                "svgs": len(svgs),
                "detail": (cp.stdout + cp.stderr).strip()[-300:] if not svgs else "ok"}


def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--lcsc", nargs="+", required=True, help="LCSC id(s), e.g. C1525")
    ap.add_argument("--out-dir", default=None,
                    help="library directory. Default: <project>/../lib when "
                         "--project is given, else ./lib")
    ap.add_argument("--lib-name", default="aiee", help="library nickname/base (default aiee)")
    ap.add_argument("--project", help="project dir to register the libs into")
    ap.add_argument("--no-3d", action="store_true", help="skip 3D models (faster)")
    ap.add_argument("--overwrite", action="store_true", help="re-pull existing parts")
    ap.add_argument("--verify-load", action="store_true",
                    help="confirm footprints load via kicad-cli fp export svg")
    ap.add_argument("--out", help="write JSON here instead of stdout")
    args = ap.parse_args(argv)

    try:
        # A bare relative default resolves against the CWD, and orchestrators run
        # from the repo root - so "lib" silently became <repo>/lib, shared by
        # every concurrent board run, while the board's own lib/ stayed empty
        # and the script still reported pass (LEARNINGS, lumina-strobe
        # BLOCKING-06). Derive from --project instead, and refuse the repo root.
        if args.out_dir:
            out_dir = Path(args.out_dir)
        elif args.project:
            out_dir = Path(args.project).resolve().parent / "lib"
        else:
            out_dir = Path("lib")
        try:
            if out_dir.resolve() == (env.repo_root() / "lib").resolve():
                raise RuntimeError(
                    f"refusing to use the repo-root library {out_dir.resolve()} - "
                    f"it is shared by every board run. Pass --out-dir "
                    f"boards/<board>/lib, or pass --project so the default "
                    f"derives from it.")
        except (OSError, ValueError):
            pass
        out_dir.mkdir(parents=True, exist_ok=True)
        base = out_dir / args.lib_name
        results = [_pull_one(l, base, args.no_3d, args.overwrite) for l in args.lcsc]

        sym_lib = base.with_suffix(".kicad_sym")
        pretty = Path(str(base) + ".pretty")
        registered = None
        if args.project:
            registered = _register_project(
                Path(args.project), args.lib_name,
                sym_lib if sym_lib.exists() else None,
                pretty if pretty.is_dir() else None)

        load = _verify_load(pretty) if (args.verify_load and pretty.is_dir()) else None

        failed = [r for r in results if r["status"] == "error"]
        payload = {
            "script": "lib_pull",
            "status": "fail" if failed else "pass",
            "lib_name": args.lib_name,
            "symbol_lib": str(sym_lib) if sym_lib.exists() else None,
            "footprint_lib": str(pretty) if pretty.is_dir() else None,
            "results": results,
            "registered": registered,
            "load_check": load,
        }
    except Exception as exc:  # noqa: BLE001 - contract: any error -> exit 2
        print(json.dumps({"script": "lib_pull", "status": "error",
                          "error": f"{type(exc).__name__}: {exc}"}))
        return 2

    text = json.dumps(payload, indent=1, ensure_ascii=True)
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
    else:
        print(text)
    return 1 if payload["status"] == "fail" else 0


if __name__ == "__main__":
    sys.exit(main())
