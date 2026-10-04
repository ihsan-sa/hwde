"""writeset_check - an eval-loop fix row may not touch what judges it.

The rule (pipeline-arch design, "The eval loop"): "A fix row may not touch
scorers, checks, bounds, fixtures or waivers." A fix row is a branch named
track/eval-fix-<anything>; every other branch passes untouched. For a fix
row, every path changed between the merge base with --base and HEAD is
refused when it is one of:

  scorers   bench.py, score_checks.py, lib/benchlib.py, lib/benchcorpus.py,
            lib/e2elib.py, reference/e2e-scoring.md, evals/
  checks    tests/ (adding a NEW test file is allowed; changing, renaming
            or deleting an existing one is not), .github/, Makefile,
            check.cmd, any conftest.py, and any pytest config file
            (pytest.ini, .pytest.ini, tox.ini, setup.cfg, pyproject.toml),
            new or changed, at the root or below: each one can rewire or
            skip the suite
  bounds    any bounds.yaml, tests/fixtures/stages/baselines/
  fixtures  tests/fixtures/, tests/golden/
  waivers   any path with "waiver" in its name

CLI: writeset_check.py --branch B [--base origin/main] [--repo DIR]
     writeset_check.py --branch B --paths P...   (classify given A-added /
                                                  M-changed paths, no git)
Prints {"fix_row": bool, "refused": [{path, status, class}]} as JSON.
Exit 0 when nothing is refused, 1 when something is, 2 on a git error.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys

FIX_PREFIX = "track/eval-fix-"
SK = ".claude/skills/hwde/"
SCORERS = {SK + "scripts/bench.py", SK + "scripts/score_checks.py",
           SK + "scripts/lib/benchlib.py", SK + "scripts/lib/benchcorpus.py",
           SK + "scripts/lib/e2elib.py", SK + "reference/e2e-scoring.md"}
CHECK_FILES = {"Makefile", "check.cmd"}
# refused under any directory, added or changed: pytest loads each of them
PYTEST_FILES = {"conftest.py", "pytest.ini", ".pytest.ini", "tox.ini",
                "setup.cfg", "pyproject.toml"}


def classify(path: str, status: str) -> str | None:
    """The protected class a changed path falls in, or None when allowed.
    status is git's letter: A added, anything else changes what was there."""
    name = path.rsplit("/", 1)[-1]
    if "waiver" in path.lower():
        return "waivers"
    if name == "bounds.yaml" or path.startswith("tests/fixtures/stages/baselines/"):
        return "bounds"
    if path.startswith(("tests/fixtures/", "tests/golden/")):
        return "fixtures"
    if path in SCORERS or path.startswith("evals/"):
        return "scorers"
    if (path.startswith(".github/") or path in CHECK_FILES
            or name in PYTEST_FILES):
        return "checks"
    if path.startswith("tests/") and status != "A":
        return "checks"
    return None


def changed(repo: str, base: str) -> list[tuple[str, str]]:
    """(status, path) for every path the branch changed since its merge base;
    a rename counts as a delete of the old path plus an add of the new."""
    r = subprocess.run(["git", "-C", repo, "diff", "--name-status",
                        "--no-renames", f"{base}...HEAD"],
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip())
    return [(ln.split("\t", 1)[0][0], ln.split("\t", 1)[1])
            for ln in r.stdout.splitlines() if "\t" in ln]


def check(branch: str, entries: list[tuple[str, str]]) -> dict:
    fix = branch.startswith(FIX_PREFIX)
    refused = []
    if fix:
        for status, path in entries:
            cls = classify(path, status)
            if cls:
                refused.append({"path": path, "status": status, "class": cls})
    return {"fix_row": fix, "refused": refused}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--branch", required=True)
    ap.add_argument("--base", default="origin/main")
    ap.add_argument("--repo", default=".")
    ap.add_argument("--paths", nargs="+",
                    help="STATUS:PATH entries instead of a git diff")
    args = ap.parse_args(argv)
    if args.paths:
        entries = [tuple(p.split(":", 1)) for p in args.paths]
    elif not args.branch.startswith(FIX_PREFIX):
        entries = []
    else:
        try:
            entries = changed(args.repo, args.base)
        except RuntimeError as e:
            print(f"writeset_check: {e}", file=sys.stderr)
            return 2
    res = check(args.branch, entries)
    print(json.dumps(res, indent=1))
    return 1 if res["refused"] else 0


if __name__ == "__main__":
    sys.exit(main())
