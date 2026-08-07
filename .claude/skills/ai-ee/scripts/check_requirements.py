#!/usr/bin/env python
"""check_requirements.py - deterministic exit lint for the P0 artifact.

The requirements doc is agent prose by design, but three properties are
checkable and one escape shipped for lack of a check (lumina-carrier's
design-doc PDF said 'requirements.md not found' while the file sat under
architecture/): location, the 9-section schema, and the open-question format.

Checks (T6 req-lint):
  (a) <workspace>/requirements.md exists at the workspace ROOT. On a miss,
      strays under architecture/ and brief/ are named (kind req_misplaced,
      error); when no file exists anywhere the kind is req_missing (error).
  (b) '## <n>' headings must cover sections 1..9 (any title wording; extra
      sections 0, 10+, Answers, Traceability are fine). One req_sections
      error per missing number.
  (c) section 9 must contain numbered open questions (plain '1.' or bold
      '**1.' style) or the literal 'none' - req_oq_format, warning.

Script contract (SPEC.md section 6): argparse, JSON to stdout or --out,
ASCII. Exit 0 = artifact conforms (warnings allowed - they are advisory at
P0, mirroring check_env), 1 = errors (orchestrator loops the analyst once),
2 = cannot run.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "lib"))
import checklib  # noqa: E402
from checklib import CheckError  # noqa: E402

SCRIPT = "check_requirements"
SECTION_NAMES = {
    1: "Function", 2: "Interfaces", 3: "Power", 4: "Environment",
    5: "Size & mounting", 6: "Quantity & budget", 7: "Assembly",
    8: "Compliance/safety flags", 9: "Open questions",
}
STRAY_DIRS = ("architecture", "brief")
_HEADING = re.compile(r"^##\s+(\d+)")
# numbered open question: '1.' / '2)' with optional markdown bold/underline
_NUMBERED = re.compile(r"^\s*(?:\*\*|__)?\s*\d+[.)]")

MISPLACED_REMEDIATION = ("move to workspace root - report_gen.py and all "
                         "later phases resolve it there")


def _vio(severity: str, kind: str, msg: str, **extras) -> dict:
    return checklib.violation("requirements", severity, None, None, None, [],
                              msg, SCRIPT, kind=kind, **extras)


def lint(ws: Path) -> tuple[list[dict], dict]:
    violations: list[dict] = []
    req = ws / "requirements.md"
    facts: dict = {"workspace": str(ws).replace("\\", "/"),
                   "path": None, "sections_found": []}
    if not req.is_file():
        strays = [p for d in STRAY_DIRS if (ws / d).is_dir()
                  for p in sorted((ws / d).rglob("requirements.md"))]
        if strays:
            for s in strays:
                rel = s.relative_to(ws).as_posix()
                violations.append(_vio(
                    "error", "req_misplaced",
                    f"requirements.md found at {rel}, not the workspace "
                    f"root: {MISPLACED_REMEDIATION}",
                    stray_path=rel, remediation=MISPLACED_REMEDIATION))
        else:
            violations.append(_vio(
                "error", "req_missing",
                "requirements.md not found at the workspace root (or under "
                "architecture/ or brief/) - P0 has not produced its artifact"))
        return violations, facts

    facts["path"] = "requirements.md"
    lines = req.read_text(encoding="utf-8", errors="replace").splitlines()
    # (b) section coverage by number, wording-tolerant ('&' vs 'and' vs '/')
    found: dict[int, int] = {}
    for i, ln in enumerate(lines):
        m = _HEADING.match(ln)
        if m and int(m.group(1)) not in found:
            found[int(m.group(1))] = i
    facts["sections_found"] = sorted(found)
    for n, name in SECTION_NAMES.items():
        if n not in found:
            violations.append(_vio(
                "error", "req_sections",
                f"section '## {n}. {name}' missing", section=n))
    # (c) open-question format: numbered lines or the literal 'none'
    if 9 in found:
        start = found[9] + 1
        end = next((i for i in range(start, len(lines))
                    if lines[i].startswith("## ")), len(lines))
        body = lines[start:end]
        has_q = any(_NUMBERED.match(ln) for ln in body)
        has_none = any(re.search(r"\bnone\b", ln, re.IGNORECASE)
                       for ln in body)
        if not (has_q or has_none):
            violations.append(_vio(
                "warning", "req_oq_format",
                "section 9 has neither numbered open questions "
                "(e.g. '1. ...') nor the literal 'none'", section=9))
    return violations, facts


def run(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--workspace", required=True,
                    help="board workspace dir (requirements.md at its root)")
    ap.add_argument("--out", help="write result JSON here instead of stdout")
    args = ap.parse_args(argv)
    ws = Path(args.workspace)
    if not ws.is_dir():
        raise CheckError(f"workspace does not exist: {ws}")
    violations, facts = lint(ws)
    payload = checklib.report(SCRIPT, None, violations, **facts)
    if not any(v["severity"] == "error" for v in violations):
        payload["status"] = "pass"  # warnings are advisory at P0
    return payload, args.out


def main(argv=None) -> int:
    return checklib.cli_wrap(SCRIPT, lambda: run(argv))


if __name__ == "__main__":
    raise SystemExit(main())
