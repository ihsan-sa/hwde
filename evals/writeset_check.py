"""writeset_check - an eval-loop fix row may not touch what judges it.

The rule (pipeline-arch design, "The eval loop"): "A fix row may not touch
scorers, checks, bounds, fixtures or waivers." A fix row is a branch named
track/eval-fix-<anything>; every other branch passes untouched. For a fix
row, every path changed between the merge base with --base and HEAD is
refused when it is one of:

  rule      this check itself (evals/writeset_check.py) and the workflow
            that runs it (.github/workflows/writeset.yml), new or changed
  scorers   the scoring code: SCORERS_FLOOR (bench.py, score_checks.py, the
            libs only they import, and lib/checklib.py, which every check
            reports through) plus whatever scoring_modules() derives from
            their imports; the grading data (reference/e2e-scoring.md,
            docs/check-scorecard.*); evals/; and any NEW path that would
            shadow one of those modules on import (a scripts/lib/e2elib/
            package, an e2elib.so, a tests/benchlib.py)
  checks    tests/ (a NEW test file is allowed when scan_test() finds
            nothing in it; changing, renaming or deleting an existing one
            is not), .github/, Makefile, check.cmd, any conftest.py, any
            pytest config file (pytest.ini, .pytest.ini, tox.ini,
            setup.cfg, pyproject.toml) and any interpreter hook (*.pth,
            sitecustomize.py, usercustomize.py), new or changed, at the
            root or below: each one can rewire or skip the suite
  bounds    any bounds.yaml, tests/fixtures/stages/baselines/
  fixtures  tests/fixtures/, tests/golden/
  waivers   any path with "waiver" in its name

Paths come from `git diff -z`, so a non-ASCII name is matched as itself,
not in git's quoted form. The workflow pipes main's copy of this file into
python, so --repo is where the branch's tree is read, never __file__.

CLI: writeset_check.py --branch B [--base origin/main] [--repo DIR]
     writeset_check.py --branch B --paths P...   (classify given A-added /
                                                  M-changed paths, no git)
Prints {"fix_row": bool, "refused": [{path, status, class[, why]}]} as JSON.
Exit 0 when nothing is refused, 1 when something is, 2 on a git error.
"""
from __future__ import annotations

import argparse
import ast
import json
import subprocess
import sys
from pathlib import Path

FIX_PREFIX = "track/eval-fix-"
SK = ".claude/skills/hwde/"
# the scripts that score, and the floor that holds whatever the derivation
# finds (paths under scripts/)
SCORER_ENTRY = ("bench.py", "score_checks.py")
SCORERS_FLOOR = {"bench.py", "score_checks.py", "lib/benchlib.py",
                 "lib/benchcorpus.py", "lib/e2elib.py", "lib/evalcard.py",
                 "lib/checklib.py"}
SCORING_DATA = {SK + "reference/e2e-scoring.md", "docs/check-scorecard.jsonl",
                "docs/check-scorecard.md"}
# the rule's own enforcement: refused first, whatever else changes
RULE_FILES = {"evals/writeset_check.py", ".github/workflows/writeset.yml"}
CHECK_FILES = {"Makefile", "check.cmd"}
# refused under any directory, added or changed: pytest or the interpreter
# loads each of them
PYTEST_FILES = {"conftest.py", "pytest.ini", ".pytest.ini", "tox.ini",
                "setup.cfg", "pyproject.toml", "sitecustomize.py",
                "usercustomize.py"}


# --- the scoring modules, from bench.py's imports --------------------------

def _local_imports(f: Path, scripts: Path) -> set[Path]:
    """The scripts/ and scripts/lib/ files f imports, at any depth in f."""
    try:
        tree = ast.parse(f.read_text(encoding="utf-8"))
    except (OSError, SyntaxError, ValueError):
        return set()
    out = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            names = [a.name for a in n.names]
        elif isinstance(n, ast.ImportFrom) and n.module and not n.level:
            names = [n.module] + [f"{n.module}.{a.name}" for a in n.names]
        else:
            continue
        for m in names:
            parts = m.split(".")
            roots = [scripts / "lib", scripts]
            if parts[0] == "lib":
                parts, roots = parts[1:], [scripts / "lib"]
            if not parts:
                continue
            for r in roots:
                for cand in (r.joinpath(*parts).with_suffix(".py"),
                             r.joinpath(*parts) / "__init__.py"):
                    if cand.is_file():
                        out.add(cand)
    return out


def _closure(starts, scripts: Path, stop=frozenset()) -> set[Path]:
    seen, todo = set(), list(starts)
    while todo:
        f = todo.pop()
        if f in seen or f in stop:
            continue
        seen.add(f)
        todo += _local_imports(f, scripts)
    return seen


def scoring_modules(repo: str) -> set[str]:
    """Repo paths of the scoring modules: SCORERS_FLOOR plus every module
    bench.py or score_checks.py imports, at any depth, that no other hwde
    script reaches. bench.py also imports the pipeline it scores (the
    checks, the gate, the router), which a fix row exists to fix, so the
    scorers are the modules only scoring uses."""
    scripts = Path(repo) / SK / "scripts"
    entry = {scripts / e for e in SCORER_ENTRY}
    scoring = _closure(entry, scripts)
    others = [p for p in scripts.glob("*.py") if p not in entry]
    pipeline = _closure(others, scripts, stop=frozenset(entry))
    derived = {p.relative_to(scripts).as_posix() for p in scoring - pipeline}
    return {SK + "scripts/" + rel for rel in SCORERS_FLOOR | derived}


def shadows(path: str, modules: set[str]) -> str | None:
    """The scoring module a NEW path would shadow on import: any path
    component named after it (a package dir e2elib/, e2elib.py, e2elib.so,
    e2elib.cpython-314.pyc), anywhere in the repo."""
    stems = {m.rsplit("/", 1)[-1][:-3] for m in modules if m.endswith(".py")}
    for comp in path.split("/"):
        if comp.split(".", 1)[0] in stems:
            return comp.split(".", 1)[0]
    return None


# --- what a new test file may not do ---------------------------------------

# names a test has no business touching: pytest's internals, the import
# system, the interpreter's namespaces and dynamic code
BANNED_NAMES = {"_pytest", "pluggy", "builtins", "__builtins__", "importlib",
                "ctypes", "gc", "runpy", "__import__", "exec", "eval",
                "compile", "setattr", "delattr", "globals", "vars",
                "pytest_plugins"}
# banned as any attribute (x.__dict__, pytest.hookimpl); builtins above are
# banned as bare names only, so monkeypatch.setattr and re.compile pass
BANNED_ATTR_NAMES = {"_pytest", "__builtins__", "pytest_plugins", "hookimpl",
                     "hookspec", "__dict__", "__globals__", "__code__",
                     "__subclasses__"}
BANNED_ATTRS = {("sys", "modules"), ("sys", "meta_path"),
                ("sys", "path_hooks"), ("sys", "path_importer_cache"),
                ("sys", "settrace"), ("sys", "setprofile"),
                ("sys", "addaudithook"), ("os", "putenv"),
                ("os", "unsetenv"), ("os", "chdir")}
MUTATORS = {"update", "pop", "popitem", "setdefault", "clear", "append",
            "extend", "insert", "remove", "discard", "add", "__setitem__",
            "__delitem__"}


def _root(node) -> str | None:
    while isinstance(node, (ast.Attribute, ast.Subscript, ast.Call)):
        node = node.func if isinstance(node, ast.Call) else node.value
    return node.id if isinstance(node, ast.Name) else None


def _mentions(node, names: set[str]) -> bool:
    return any(isinstance(n, ast.Name) and n.id in names
               for n in ast.walk(node))


def _anchored(tree) -> set[str]:
    """Module-level names built from __file__ (REPO, SCRIPTS, ...)."""
    names = {"__file__"}
    for st in tree.body:
        value = getattr(st, "value", None)
        if isinstance(st, (ast.Assign, ast.AnnAssign)) and value is not None \
                and _mentions(value, names):
            for t in (st.targets if isinstance(st, ast.Assign)
                      else [st.target]):
                names |= {n.id for n in ast.walk(t)
                          if isinstance(n, ast.Name)}
    return names


def _sys_path_ok(call: ast.Call, anchored: set[str]) -> bool:
    """sys.path.insert/append of a path built from __file__ only."""
    fn = call.func
    return (fn.attr in ("insert", "append") and bool(call.args)
            and _mentions(call.args[-1], anchored)
            and all(_mentions(a, anchored) or isinstance(a, ast.Constant)
                    for a in call.args))


def scan_test(src: str) -> str | None:
    """Why a new test file could change how OTHER tests run, else None.

    An ordinary test imports, builds paths from __file__ and puts them on
    sys.path, defines tests and fixtures, and patches through pytest's
    monkeypatch, which is undone after each test. Refused: a pytest hook
    (def pytest_*); a name in BANNED_NAMES, an attribute in
    BANNED_ATTR_NAMES or BANNED_ATTRS; "_pytest" in a string; getattr with
    a computed name; assigning or deleting an attribute or item of an
    imported module (bench.score = ..., os.environ["X"] = ...); a mutating
    call on one (checklib.REGISTRY.clear(), os.environ.update());
    aliasing os.environ, sys.path or sys.modules; a sys.path change whose
    path is not built from __file__; and a file that does not parse.
    Reading os.environ is fine; monkeypatch.setenv is how a test sets it."""
    try:
        tree = ast.parse(src)
    except (SyntaxError, ValueError) as e:
        return f"does not parse: {e}"
    imported = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.ImportFrom) and \
                (n.module or "").split(".")[0] in BANNED_NAMES:
            return f"imports from {n.module}"
        if isinstance(n, (ast.Import, ast.ImportFrom)):
            for a in n.names:
                if a.name.split(".")[0] in BANNED_NAMES:
                    return f"imports {a.name}"
                imported.add((a.asname or a.name).split(".")[0])
    anchored = _anchored(tree)
    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and \
                n.name.startswith("pytest_"):
            return f"defines the pytest hook {n.name}"
        if isinstance(n, ast.Name) and n.id in BANNED_NAMES:
            return f"uses {n.id}"
        if isinstance(n, ast.Attribute):
            if n.attr in BANNED_ATTR_NAMES:
                return f"uses .{n.attr}"
            if isinstance(n.value, ast.Name) and \
                    (n.value.id, n.attr) in BANNED_ATTRS:
                return f"uses {n.value.id}.{n.attr}"
        if isinstance(n, ast.Constant) and isinstance(n.value, str) and \
                "_pytest" in n.value:
            return "names _pytest in a string"
        if isinstance(n, ast.Assign) and isinstance(n.value, ast.Attribute) \
                and _root(n.value) in imported and n.value.attr in (
                    "environ", "path", "modules"):
            return f"aliases {_root(n.value)}.{n.value.attr}"
        if isinstance(n, (ast.Assign, ast.AugAssign, ast.AnnAssign,
                          ast.Delete)):
            targets = (n.targets if isinstance(n, (ast.Assign, ast.Delete))
                       else [n.target])
            for t in targets:
                for sub in ast.walk(t):
                    if isinstance(sub, (ast.Attribute, ast.Subscript)) and \
                            _root(sub) in imported:
                        return f"assigns into the imported {_root(sub)}"
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and \
                n.func.id == "getattr" and not (
                    len(n.args) > 1 and isinstance(n.args[1], ast.Constant)):
            return "calls getattr with a computed name"
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and \
                n.func.attr in MUTATORS and _root(n.func) in imported and \
                isinstance(n.func.value, (ast.Attribute, ast.Subscript)):
            v = n.func.value
            if isinstance(v, ast.Attribute) and v.attr == "path" and \
                    isinstance(v.value, ast.Name) and v.value.id == "sys":
                if _sys_path_ok(n, anchored):
                    continue
                return "changes sys.path to a path not built from __file__"
            return f"mutates the imported {_root(n.func)} (.{n.func.attr})"
    return None


# --- classifying a diff -----------------------------------------------------

def classify(path: str, status: str, scorers: set[str] | None = None
             ) -> str | None:
    """The protected class a changed path falls in, or None when allowed.
    status is git's letter: A added, anything else changes what was there.
    scorers: scoring_modules() of the repo (default: the floor)."""
    if scorers is None:
        scorers = {SK + "scripts/" + rel for rel in SCORERS_FLOOR}
    name = path.rsplit("/", 1)[-1]
    if path in RULE_FILES:
        return "rule"
    if "waiver" in path.lower():
        return "waivers"
    if name == "bounds.yaml" or path.startswith("tests/fixtures/stages/baselines/"):
        return "bounds"
    if path.startswith(("tests/fixtures/", "tests/golden/")):
        return "fixtures"
    if path in scorers or path in SCORING_DATA or path.startswith("evals/"):
        return "scorers"
    if (path.startswith(".github/") or path in CHECK_FILES
            or name in PYTEST_FILES or name.endswith(".pth")):
        return "checks"
    if path.startswith("tests/") and status != "A":
        return "checks"
    return None


def _path(b: bytes) -> str:
    return b.decode("utf-8", "surrogateescape")


def parse_z(out: bytes) -> list[tuple[str, str]]:
    """(status, path) from `git diff -z --name-status`. NUL-separated, so a
    path is its raw bytes, never git's quoted "tests/sub_\\303\\251" form. A
    rename (R100 old new) yields a D for its source and an A for its
    destination; a copy (C) an A for its destination."""
    f = out.split(b"\0")
    entries, i = [], 0
    while i < len(f) and f[i]:
        st = f[i].decode("ascii")
        if st[0] in "RC":
            if st[0] == "R":
                entries.append(("D", _path(f[i + 1])))
            entries.append(("A", _path(f[i + 2])))
            i += 3
        else:
            entries.append((st[0], _path(f[i + 1])))
            i += 2
    return entries


def changed(repo: str, base: str) -> list[tuple[str, str]]:
    """(status, path) for every path the branch changed since its merge
    base; --no-renames already splits a rename into its two ends."""
    r = subprocess.run(["git", "-C", repo, "diff", "-z", "--name-status",
                        "--no-renames", f"{base}...HEAD"],
                       capture_output=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.decode(errors="replace").strip())
    return parse_z(r.stdout)


def _disk(repo: str):
    def read(path: str) -> str | None:
        try:
            return (Path(repo) / path).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            return None
    return read


def check(branch: str, entries: list[tuple[str, str]], repo: str = ".",
          read=None) -> dict:
    """read(path) gives an added file's text (default: repo's tree); an
    added test file that can't be read is refused."""
    if not branch.startswith(FIX_PREFIX):
        return {"fix_row": False, "refused": []}
    scorers = scoring_modules(repo)
    read = read or _disk(repo)
    refused = []
    for status, path in entries:
        cls, why = classify(path, status, scorers), None
        if cls is None and status == "A":
            stem = shadows(path, scorers)
            if stem:
                cls, why = "scorers", f"shadows the scoring module {stem}"
        if cls is None and status == "A" and path.startswith("tests/") \
                and path.endswith(".py"):
            src = read(path)
            why = "unreadable" if src is None else scan_test(src)
            cls = "checks" if why else None
        if cls:
            r = {"path": path, "status": status, "class": cls}
            if why:
                r["why"] = why
            refused.append(r)
    return {"fix_row": True, "refused": refused}


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
    res = check(args.branch, entries, args.repo)
    print(json.dumps(res, indent=1))
    return 1 if res["refused"] else 0


if __name__ == "__main__":
    sys.exit(main())
