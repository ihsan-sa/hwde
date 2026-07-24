#!/usr/bin/env python
"""check_env.py - validate the ai-ee toolchain on this machine.

Script contract (SPEC.md section 6): argparse, JSON to stdout (or --out FILE),
exit 0 = environment OK (warnings allowed), 1 = one or more checks failed,
2 = internal error. Human-readable remediation goes to stderr so stdout stays
machine-parseable.

Run it with the repo venv interpreter - package checks inspect the running
interpreter:  .venv/Scripts/python .claude/skills/ai-ee/scripts/check_env.py

Fast mode (default) checks presence/versions only. --full adds live probes:
SWIG pcbnew roundtrip via KiCad's bundled python (needed for Specctra DSN/SES
and KiCad-9 zone refill) and an IPC headless-connect attempt (kipy). Probe
failures are recorded as warnings with the working fallback named, because
each has a sanctioned alternative path in SPEC.md.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata
import json
import subprocess
import sys
import tempfile
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import env  # noqa: E402

MIN_PYTHON = (3, 11)

# import name -> pip distribution name
REQUIRED_PACKAGES = {
    "kipy": "kicad-python",
    "kiutils": "kiutils",
    "kicad_sch_api": "kicad-sch-api",
    "skidl": "skidl",
    "shapely": "shapely",
    "numpy": "numpy",
    "gerbonara": "gerbonara",
    "sexpdata": "sexpdata",
    "yaml": "PyYAML",
    "easyeda2kicad": "easyeda2kicad",
    "pypdf": "pypdf",
    "jsonschema": "jsonschema",
    "scipy": "scipy",
    "pytest": "pytest",
}

KICAD_INSTALL_HELP = (
    "Install KiCad >= 9.0.5: direct installer from "
    "https://kicad-downloads.s3.cern.ch/windows/stable/ or "
    "'winget install -e --id KiCad.KiCad' (on this host winget may need its "
    "full path: %LOCALAPPDATA%/Microsoft/WindowsApps/winget.exe). "
    "Or point AIEE_KICAD_CLI at an existing kicad-cli."
)
JAVA_HELP = (
    "Freerouting 2.2.4 needs Java >= 25 (the 'Java 21+' docs are stale; "
    "verified: Java 24 fails with UnsupportedClassVersionError). Unzip a "
    "portable Temurin 25 JRE into tools/jre/ "
    "(https://adoptium.net/temurin/releases/?version=25 - no system install "
    "needed), or set AIEE_JAVA, or start Docker Desktop and use the "
    "ghcr.io/freerouting/freerouting image."
)
JAR_HELP = (
    "Download freerouting-2.2.4.jar from "
    "https://github.com/freerouting/freerouting/releases into "
    "tools/freerouting/, or set AIEE_FREEROUTING_JAR."
)

SWIG_PROBE = """\
import sys
import pcbnew
out = sys.argv[1]
b = pcbnew.CreateEmptyBoard()
b.Save(out)
b2 = pcbnew.LoadBoard(out)
assert b2 is not None
print("build=" + pcbnew.GetBuildVersion())
"""


def check(name: str, ok: bool, detail: str, remediation: str = "",
          warn: bool = False) -> dict:
    status = "pass" if ok else ("warn" if warn else "fail")
    c = {"name": name, "status": status, "detail": detail}
    if not ok and remediation:
        c["remediation"] = remediation
    return c


def check_python() -> dict:
    v = sys.version_info
    return check(
        "python-version", (v.major, v.minor) >= MIN_PYTHON,
        f"{v.major}.{v.minor}.{v.micro} at {sys.executable}",
        f"Recreate the venv with Python >= {'.'.join(map(str, MIN_PYTHON))}: "
        "py -3.13 -m venv .venv && .venv/Scripts/python -m pip install -r requirements.txt",
    )


def check_packages() -> list[dict]:
    import contextlib
    import io
    out = []
    # skidl prints env-var warnings on import AND drops <script>.log/.erc
    # files in the CWD; sandbox both so stdout stays pure JSON and the repo
    # stays clean.
    scratch = tempfile.mkdtemp(prefix="aiee_imports_")
    for mod, dist in REQUIRED_PACKAGES.items():
        try:
            sink = io.StringIO()
            with contextlib.chdir(scratch), \
                 contextlib.redirect_stdout(sink), contextlib.redirect_stderr(sink):
                importlib.import_module(mod)
            try:
                ver = importlib.metadata.version(dist)
            except importlib.metadata.PackageNotFoundError:
                ver = "unknown"
            out.append(check(f"package:{dist}", True, f"import {mod} ok, {ver}"))
        except Exception as e:  # import errors vary wildly across packages
            out.append(check(
                f"package:{dist}", False,
                f"import {mod} failed: {type(e).__name__}: {e}",
                f"{Path(sys.executable)} -m pip install {dist}   "
                "(or: pip install -r requirements.txt)",
            ))
    return out


def check_kicad(resolved: dict, full: bool) -> list[dict]:
    out = []
    try:
        cli = env.find_kicad_cli()
    except env.EnvError as e:
        return [check("kicad-cli", False, str(e), KICAD_INSTALL_HELP)]
    if cli is None:
        return [check("kicad-cli", False, "no KiCad >= 9.0.5 found", KICAD_INSTALL_HELP)]

    ver = env.kicad_cli_version(cli)
    vs = ".".join(map(str, ver))
    resolved["kicad_cli"] = str(cli)
    resolved["kicad_version"] = vs
    out.append(check(
        "kicad-cli", ver >= env.MIN_KICAD, f"{cli} ({vs})", KICAD_INSTALL_HELP))
    if ver < env.MIN_KICAD:
        return out

    r = subprocess.run([str(cli), "pcb", "render", "--help"],
                       capture_output=True, text=True, timeout=60)
    out.append(check(
        "kicad-cli-render", r.returncode == 0,
        "pcb render subcommand available" if r.returncode == 0
        else "pcb render missing (KiCad too old?)",
        KICAD_INSTALL_HELP))

    d = subprocess.run([str(cli), "pcb", "drc", "--help"],
                       capture_output=True, text=True, timeout=60)
    has_refill = "--refill-zones" in (d.stdout + d.stderr)
    resolved["drc_refill_zones"] = has_refill
    out.append(check(
        "kicad-cli-refill-zones", has_refill,
        "drc --refill-zones supported" if has_refill else
        "drc lacks --refill-zones (KiCad 9): zone refill must go through the "
        "bundled-python SWIG fallback",
        "Prefer KiCad 10.x for headless zone refill.", warn=True))

    kpy = env.find_kicad_python(cli)
    resolved["kicad_python"] = str(kpy) if kpy else None
    out.append(check(
        "kicad-bundled-python", kpy is not None,
        f"{kpy}" if kpy else "bundled python.exe not found next to kicad-cli",
        "SWIG pcbnew (Specctra DSN/SES, KiCad-9 zone refill) needs KiCad's own "
        "python. Reinstall KiCad with the Python component."))

    if full and kpy is not None:
        out.append(probe_swig(kpy))
    return out


def probe_swig(kpy: Path) -> dict:
    with tempfile.TemporaryDirectory() as td:
        board = str(Path(td) / "trivial.kicad_pcb")
        try:
            r = subprocess.run([str(kpy), "-c", SWIG_PROBE, board],
                               capture_output=True, text=True, timeout=180)
        except subprocess.TimeoutExpired:
            return check("swig-pcbnew-roundtrip", False,
                         "timed out after 180 s (wx assert dialog wedge?)",
                         "See LEARNINGS.md [kicad][swig]; fallback: vendored "
                         "Python DSN writer per SPEC.md P7.", warn=True)
    ok = r.returncode == 0 and "build=" in r.stdout
    detail = r.stdout.strip() if ok else (r.stderr.strip() or r.stdout.strip())[-400:]
    return check("swig-pcbnew-roundtrip", ok,
                 f"CreateEmptyBoard/Save/LoadBoard ok ({detail})" if ok
                 else f"probe failed: {detail}",
                 "Fallback: vendored Python DSN writer per SPEC.md P7.",
                 warn=True)


def probe_ipc() -> dict:
    smoke = Path(__file__).resolve().parent / "smoke_ipc.py"
    try:
        r = subprocess.run([sys.executable, str(smoke)],
                           capture_output=True, text=True, timeout=300)
        data = json.loads(r.stdout) if r.stdout.strip() else {}
    except Exception as e:
        return check("ipc-headless", False, f"probe crashed: {e}", warn=True)
    verdict = data.get("verdict", "no-verdict")
    ok = verdict == "headless-ok"
    return check(
        "ipc-headless", ok,
        json.dumps(data)[:600],
        "IPC edits fall back to SWIG bundled python (verified working); "
        "see PROGRESS.md S0 smoke results.",
        warn=True)


def check_java(resolved: dict) -> list[dict]:
    out = []
    try:
        j = env.find_java()
    except env.EnvError as e:
        return [check("java-for-freerouting", False, str(e), JAVA_HELP)]
    docker = env.docker_state()
    resolved["docker"] = docker
    if j:
        resolved["java"] = str(j[0])
        resolved["java_major"] = j[1]
    if j and j[1] >= env.MIN_JAVA_FOR_FREEROUTING:
        out.append(check("java-for-freerouting", True, f"{j[0]} (major {j[1]})"))
    elif docker == "up":
        out.append(check(
            "java-for-freerouting", True,
            f"java {'major %d' % j[1] if j else 'absent'} is insufficient, but "
            "Docker daemon is up (freerouting container path)"))
    else:
        have = f"best java found: {j[0]} (major {j[1]})" if j else "no java found"
        out.append(check("java-for-freerouting", False,
                         f"{have}; docker: {docker}", JAVA_HELP))

    jar = None
    try:
        jar = env.find_freerouting_jar()
    except env.EnvError as e:
        out.append(check("freerouting-jar", False, str(e), JAR_HELP))
        return out
    resolved["freerouting_jar"] = str(jar) if jar else None
    out.append(check("freerouting-jar", jar is not None,
                     str(jar) if jar else "no jar in tools/freerouting/",
                     JAR_HELP))
    return out


def check_git() -> dict:
    import shutil
    g = shutil.which("git")
    return check("git", g is not None, g or "git not on PATH",
                 "Install git: https://git-scm.com/download/win")


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):  # cp1252 console guard
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", help="write JSON report to this file instead of stdout")
    ap.add_argument("--full", action="store_true",
                    help="also run live probes (SWIG roundtrip, IPC headless)")
    ap.add_argument("--quiet", action="store_true", help="suppress stderr summary")
    args = ap.parse_args(argv)

    resolved: dict = {"platform": sys.platform, "repo_root": str(env.repo_root())}
    checks: list[dict] = []
    try:
        checks.append(check_python())
        checks.extend(check_packages())
        checks.extend(check_kicad(resolved, args.full))
        checks.extend(check_java(resolved))
        checks.append(check_git())
        if args.full:
            checks.append(probe_ipc())
    except Exception:
        print(json.dumps({"script": "check_env", "status": "error",
                          "error": traceback.format_exc()}))
        return 2

    failed = [c for c in checks if c["status"] == "fail"]
    warned = [c for c in checks if c["status"] == "warn"]
    report = {
        "script": "check_env",
        "status": "fail" if failed else "pass",
        "resolved": resolved,
        "checks": checks,
    }
    text = json.dumps(report, indent=2)
    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
    else:
        print(text)

    if not args.quiet:
        for c in failed:
            print(f"FAIL {c['name']}: {c['detail']}", file=sys.stderr)
            if c.get("remediation"):
                print(f"  fix: {c['remediation']}", file=sys.stderr)
        for c in warned:
            print(f"warn {c['name']}: {c['detail']}", file=sys.stderr)
        print(f"check_env: {len(failed)} failed, {len(warned)} warnings, "
              f"{len(checks)} checks", file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        print(json.dumps({"script": "check_env", "status": "error",
                          "error": traceback.format_exc()}))
        sys.exit(2)
