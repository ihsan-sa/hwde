"""Toolchain discovery for ai-ee scripts.

Every ai-ee script resolves external tools through this module so that:

1. The whole pipeline agrees on ONE KiCad install. File formats are not
   forward-compatible (a KiCad-10-format board is unreadable by kicad-cli 9,
   exit 3), so mixing versions between steps silently breaks gates.
2. Tests and CI can redirect discovery with environment variables instead of
   mutating the machine.

Environment overrides (all optional; a set-but-invalid override is an error,
never silently ignored - a wrong pin must fail loudly):

  AIEE_KICAD_CLI        full path to kicad-cli executable (pins the install)
  AIEE_KICAD_ROOT       KiCad install root containing bin/
  AIEE_JAVA             full path to a java executable (for Freerouting)
  AIEE_FREEROUTING_JAR  full path to a freerouting jar
  AIEE_PDFLATEX         full path to a pdflatex executable (for report_gen)
  AIEE_NGSPICE_DLL      full path to a shared ngspice library (for sim_run)
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

# Minimum KiCad per SPEC.md section 1.
MIN_KICAD = (9, 0, 5)
# The pipeline authors all boards in KiCad 10 format (pinned 10.0.3) and
# formats are not forward-compatible: a 9.x kicad-cli exits 3 on them. An
# EXPLICIT pin (AIEE_KICAD_CLI / AIEE_KICAD_ROOT) below major 10 is therefore
# always a stale-pin mistake and is rejected loudly (ladder row 18). Plain
# discovery still accepts >= MIN_KICAD, so 9.0.5 stays reachable for manual
# experiments by NOT pinning.
PIN_MIN_MAJOR = 10
# Preference order among installed majors. 10.x preferred: it adds
# `pcb drc --refill-zones --save-board` (headless zone refill without SWIG)
# and `sch upgrade`. 9.0.5 is the verified fallback.
KICAD_PREFERENCE = ("10.", "9.")
# Freerouting 2.2.4 requires Java 25 (class file v69). Vendor docs saying
# "Java 21+" are stale for 2.2.x - verified on this machine (Java 24 fails
# with UnsupportedClassVersionError).
MIN_JAVA_FOR_FREEROUTING = 25

_TIMEOUT = 30


class EnvError(RuntimeError):
    """An explicit override (AIEE_*) points at something unusable."""


def repo_root() -> Path:
    """Repo root = nearest ancestor of this file containing SPEC.md or .git."""
    p = Path(__file__).resolve()
    for parent in p.parents:
        if (parent / "SPEC.md").exists() or (parent / ".git").exists():
            return parent
    # Fallback: fixed relative position .claude/skills/ai-ee/scripts/lib/env.py
    return p.parents[5]


def _run(cmd: list[str], timeout: int = _TIMEOUT) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd, capture_output=True, text=True, timeout=timeout,
        encoding="utf-8", errors="replace",
    )


def parse_version(text: str) -> tuple[int, ...]:
    """First dotted integer group in text -> tuple. '9.0.5-1' -> (9, 0, 5)."""
    m = re.search(r"(\d+(?:\.\d+)+)", text)
    if not m:
        return ()
    return tuple(int(x) for x in m.group(1).split("."))


# ---------------------------------------------------------------- KiCad

def kicad_installs() -> list[Path]:
    """Discover KiCad install roots (dirs containing bin/kicad-cli[.exe])."""
    roots: list[Path] = []
    if sys.platform == "win32":
        for pf in (os.environ.get("PROGRAMFILES", r"C:\Program Files"),):
            base = Path(pf) / "KiCad"
            if base.is_dir():
                roots += [d for d in base.iterdir()
                          if (d / "bin" / "kicad-cli.exe").exists()]
    elif sys.platform == "darwin":
        for app in Path("/Applications").glob("KiCad*/KiCad.app"):
            d = app / "Contents" / "MacOS"
            if (d / "kicad-cli").exists():
                roots.append(app / "Contents")
    else:
        w = shutil.which("kicad-cli")
        if w:
            roots.append(Path(w).parent.parent)
    return roots


def _cli_name() -> str:
    return "kicad-cli.exe" if sys.platform == "win32" else "kicad-cli"


def _cli_of_root(root: Path) -> Path:
    # Windows/Linux: <root>/bin/kicad-cli; macOS .app bundle: Contents/MacOS.
    for sub in ("bin", "MacOS"):
        c = root / sub / _cli_name()
        if c.exists():
            return c
    raise EnvError(f"AIEE_KICAD_ROOT has no bin/{_cli_name()}: {root}")


def _validate_pin(path: Path, var: str = "AIEE_KICAD_CLI",
                  ver: tuple[int, ...] | None = None) -> Path:
    """Reject an explicit KiCad pin whose major is below the pipeline format.

    ver is probed from the binary when not given (tests pass a stub tuple)."""
    if ver is None:
        ver = kicad_cli_version(path)
    if not ver:
        raise EnvError(
            f"{var} points at {path} but its version could not be determined "
            "(not a working kicad-cli?); unset the pin or point it at the "
            "10.0.3 install")
    if ver[0] < PIN_MIN_MAJOR:
        vs = ".".join(str(x) for x in ver)
        raise EnvError(
            f"{var} pins KiCad {vs}: pipeline file formats are 10.x "
            "(9.x cannot load them); unset the stale pin or point it at the "
            "10.0.3 install")
    return path


def find_kicad_cli() -> Path | None:
    """Resolve the pipeline's kicad-cli. Explicit pin > PATH > preferred install."""
    pin = os.environ.get("AIEE_KICAD_CLI")
    if pin:
        p = Path(pin)
        if not p.exists():
            raise EnvError(f"AIEE_KICAD_CLI does not exist: {pin}")
        return _validate_pin(p, "AIEE_KICAD_CLI")
    root_pin = os.environ.get("AIEE_KICAD_ROOT")
    if root_pin:
        return _validate_pin(_cli_of_root(Path(root_pin)), "AIEE_KICAD_ROOT")
    w = shutil.which("kicad-cli")
    if w:
        return Path(w)
    installs = kicad_installs()
    if not installs:
        return None
    scored: list[tuple[int, tuple[int, ...], Path]] = []
    for root in installs:
        cli = _cli_of_root(root)
        ver = kicad_cli_version(cli)
        if ver < MIN_KICAD:
            continue
        vs = ".".join(str(x) for x in ver)
        pref = next((len(KICAD_PREFERENCE) - i
                     for i, p in enumerate(KICAD_PREFERENCE) if vs.startswith(p)), 0)
        scored.append((pref, ver, cli))
    if not scored:
        return None
    scored.sort(key=lambda t: (t[0], t[1]))
    return scored[-1][2]


def kicad_cli_version(cli: Path) -> tuple[int, ...]:
    try:
        return parse_version(_run([str(cli), "version"]).stdout)
    except (OSError, subprocess.TimeoutExpired):
        return ()


def find_kicad_python(cli: Path) -> Path | None:
    """KiCad's BUNDLED python (has the SWIG pcbnew module; the venv does not).

    Needed for Specctra DSN export / SES import and KiCad-9 zone refill.
    """
    name = "python.exe" if sys.platform == "win32" else "python3"
    for cand in (cli.parent / name, cli.parent.parent / "bin" / name):
        if cand.exists():
            return cand
    return None


# ---------------------------------------------------------------- Java / Freerouting

def java_major(java: Path) -> int:
    """Major version of a java executable, 0 if undeterminable."""
    try:
        cp = _run([str(java), "-version"])
    except (OSError, subprocess.TimeoutExpired):
        return 0
    ver = parse_version(cp.stderr or cp.stdout)
    if not ver:
        return 0
    return ver[1] if ver[0] == 1 and len(ver) > 1 else ver[0]  # "1.8" -> 8


def find_java() -> tuple[Path, int] | None:
    """Best java for Freerouting: AIEE_JAVA > repo tools/jre > PATH.

    Returns (path, major). Callers decide if major is sufficient.
    """
    pin = os.environ.get("AIEE_JAVA")
    if pin:
        p = Path(pin)
        if not p.exists():
            raise EnvError(f"AIEE_JAVA does not exist: {pin}")
        return p, java_major(p)
    name = "java.exe" if sys.platform == "win32" else "java"
    candidates = sorted(repo_root().glob(f"tools/jre/*/bin/{name}"))
    w = shutil.which("java")
    if w:
        candidates.append(Path(w))
    best: tuple[Path, int] | None = None
    for c in candidates:
        major = java_major(c)
        if best is None or major > best[1]:
            best = (c, major)
    return best


def find_freerouting_jar() -> Path | None:
    pin = os.environ.get("AIEE_FREEROUTING_JAR")
    if pin:
        p = Path(pin)
        if not p.exists():
            raise EnvError(f"AIEE_FREEROUTING_JAR does not exist: {pin}")
        return p
    jars = sorted(repo_root().glob("tools/freerouting/freerouting-*.jar"))
    return jars[-1] if jars else None


def find_krt() -> Path | None:
    """KiCadRoutingTools plugins dir (vendored under tools/krt, S11).

    Returns the newest tools/krt/KiCadRoutingTools-*/plugins directory (the
    scripts sys.path-insert relative dirs, so callers must run them with
    cwd=plugins). Override with AIEE_KRT_DIR (points at the plugins dir).
    """
    pin = os.environ.get("AIEE_KRT_DIR")
    if pin:
        p = Path(pin)
        if not p.is_dir():
            raise EnvError(f"AIEE_KRT_DIR does not exist: {pin}")
        return p
    dirs = sorted(repo_root().glob("tools/krt/KiCadRoutingTools-*/plugins"))
    return dirs[-1] if dirs else None


# ---------------------------------------------------------------- ngspice (optional)

def find_ngspice_dll() -> Path | None:
    """Shared ngspice library for the SPICE sim gate (sim_run.py).

    Ladder: AIEE_NGSPICE_DLL pin > the DLL KiCad bundles beside kicad-cli
    (KiCad >= 9 ships ngspice for its own simulator) > None (sim gate cannot
    run). The pipeline loads it in-process via InSpice's shared-library
    binding - there is no ngspice.exe on this ladder on purpose: only the
    shared library exposes the ngGet_Vec_Info API the runner needs.
    """
    pin = os.environ.get("AIEE_NGSPICE_DLL")
    if pin:
        p = Path(pin)
        if not p.exists():
            raise EnvError(f"AIEE_NGSPICE_DLL does not exist: {pin}")
        return p
    cli = find_kicad_cli()  # EnvError from a bad AIEE_KICAD_* pin stays loud
    if cli is None:
        return None
    if sys.platform == "win32":
        name = "ngspice.dll"
    elif sys.platform == "darwin":
        name = "libngspice.dylib"
    else:
        name = "libngspice.so"
    cand = cli.parent / name
    return cand if cand.exists() else None


# ---------------------------------------------------------------- pdflatex (optional)

def find_pdflatex() -> Path | None:
    """pdflatex for report_gen's design document (optional toolchain member).

    Ladder: AIEE_PDFLATEX pin > PATH > the Windows per-user MiKTeX default
    install location. None = not installed (report_gen degrades to --tex-only).
    """
    pin = os.environ.get("AIEE_PDFLATEX")
    if pin:
        p = Path(pin)
        if not p.exists():
            raise EnvError(f"AIEE_PDFLATEX does not exist: {pin}")
        return p
    w = shutil.which("pdflatex")
    if w:
        return Path(w)
    if sys.platform == "win32":
        cand = (Path(os.environ.get("LOCALAPPDATA", ""))
                / "Programs" / "MiKTeX" / "miktex" / "bin" / "x64"
                / "pdflatex.exe")
        if cand.exists():
            return cand
    return None


# ---------------------------------------------------------------- Docker (optional)

def docker_state() -> str:
    """'up' (daemon reachable), 'down' (client only), or 'absent'."""
    if not shutil.which("docker"):
        return "absent"
    try:
        cp = _run(["docker", "info", "--format", "{{.ServerVersion}}"], timeout=10)
        return "up" if cp.returncode == 0 and cp.stdout.strip() else "down"
    except (OSError, subprocess.TimeoutExpired):
        return "down"
