"""T4 - trigger-indexed remediation refs + the knowledge-ladder triage register.

Three contracts are pinned here:
  1. reference/remediations/<check_id>.md exists, is loadable, and is keyed to a
     REAL finding type (a wrong trigger key is the failure mode the design notes
     call out: "the rule was violated and its reference was never loaded").
  2. fix_dispatch.py attaches the matching ref to every work order that carries
     that kind - the fixer gets the knowledge without anyone remembering to
     paste it.
  3. design/ladder-triage.md carries one row per LEARNINGS.md entry, so new
     knowledge cannot silently skip triage; plus the SKILL.md health metric
     (the playbook must shrink, never grow - v2 plan Conventions).
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / ".claude" / "skills" / "hwde"
SCRIPTS = SKILL / "scripts"
REMED = SKILL / "reference" / "remediations"
TRIAGE = ROOT / "design" / "ladder-triage.md"
LEARNINGS = ROOT / "LEARNINGS.md"

sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(SCRIPTS / "lib"))

import cluster_violations  # noqa: E402
import fix_dispatch  # noqa: E402

# The check_ids that actually fired >=100 times across the six committed board
# workspaces (T4 tally, cumulative over every report JSON incl. fix-loop
# intermediates), PLUS (T6) every kind that fired on a SHIPPED board's final
# checks with no ref. Update from boards/*/reports/checks/*.json when a new
# kind fires on a shipped board - do not auto-derive from boards/ (workspaces
# are not stable test inputs).
TOP_FIRING = [
    "unconnected_items", "undersized_track", "clearance",
    "insufficient_transition_vias", "silk_overlap", "dfm_trace_width",
    "creepage", "track_width", "lib_footprint_issues", "silk_over_copper",
    "corridor_void", "silk_edge_clearance", "copper_edge_clearance",
    "track_dangling",
    # T6: fired on lumina-carrier's shipped P8 (check_current x2, x1, x1)
    "pour_neckdown", "decoupler_loop", "gnd_stub_long",
]

REQUIRED_SECTIONS = ["## Is it real?", "## Fix ladder", "## Do not",
                     "## Verify", "## Sources"]

MAX_LINES = 90  # a fixer reads this mid-run; refs stay skimmable

STATUSES = {"done", "open", "n/a"}
LEVELS = {"L0", "L1", "L2", "L3"}
ENTRY_RE = re.compile(r"^## (\d{4}-\d{2}-\d{2}) ((?:\[[^\]]+\])+) (.+)$")


def remediation_files() -> list[Path]:
    return sorted(p for p in REMED.glob("*.md") if p.name != "README.md")


def learnings_entries() -> list[tuple[int, str, str]]:
    """(line, date, title) for every dated LEARNINGS entry, in file order."""
    out = []
    for i, ln in enumerate(LEARNINGS.read_text(encoding="utf-8").splitlines(), 1):
        m = ENTRY_RE.match(ln)
        if m:
            out.append((i, m.group(1), m.group(3)))
    return out


def triage_rows() -> list[dict]:
    """Parse the pipe table in design/ladder-triage.md.

    Row shape: | n | learnings_line | entry | tags | now | target | owner |
                 status | note |
    """
    rows = []
    for ln in TRIAGE.read_text(encoding="utf-8").splitlines():
        if not ln.startswith("|"):
            continue
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        if len(cells) < 8 or not cells[0].isdigit():
            continue
        rows.append({"n": int(cells[0]), "line": int(cells[1]),
                     "entry": cells[2], "tags": cells[3], "now": cells[4],
                     "target": cells[5], "owner": cells[6],
                     "status": cells[7],
                     "note": cells[8] if len(cells) > 8 else ""})
    return rows


# ---------------------------------------------------------------------------
# 1. the refs themselves
# ---------------------------------------------------------------------------
def test_top_firing_check_ids_all_have_a_remediation_ref():
    missing = [k for k in TOP_FIRING if not (REMED / f"{k}.md").is_file()]
    assert not missing, f"no remediation ref for: {missing}"


@pytest.mark.parametrize("path", remediation_files(), ids=lambda p: p.stem)
def test_remediation_ref_shape(path: Path):
    text = path.read_text(encoding="utf-8")
    text.encode("ascii")  # ASCII-safe (SPEC 6 contract) - raises if not
    lines = text.splitlines()
    assert len(lines) <= MAX_LINES, f"{path.name}: {len(lines)} lines > {MAX_LINES}"
    assert lines[0].strip() == f"# {path.stem}", \
        f"{path.name}: title must be the check_id (trigger key, not a topic)"
    for section in REQUIRED_SECTIONS:
        assert any(ln.startswith(section) for ln in lines), \
            f"{path.name}: missing section {section}"


@pytest.mark.parametrize("path", remediation_files(), ids=lambda p: p.stem)
def test_remediation_trigger_key_is_a_real_finding_type(path: Path):
    """The filename IS the lookup key: it must be a kind the pipeline can
    actually emit, else the ref is unreachable at runtime."""
    assert path.stem in cluster_violations.FIXER_HINTS, (
        f"{path.name}: '{path.stem}' is not a known violation kind - "
        "fix_dispatch would never load it")


@pytest.mark.parametrize("path", remediation_files(), ids=lambda p: p.stem)
def test_remediation_sources_cite_real_learnings_entries(path: Path):
    """A drifted citation is a real defect: the fixer opens the wrong entry.

    Every parenthetical LEARNINGS line reference - "(1553)", "(line 231)",
    "(LEARNINGS 628-636)" - must land inside a real entry; a RANGE must stay
    within one entry; and when a date precedes it (within 130 chars) that
    entry must carry that date.
    """
    entries = learnings_entries()          # (line, date, title), file order
    total = len(LEARNINGS.read_text(encoding="utf-8").splitlines())

    def entry_of(n: int):
        prev = None
        for (ln, date, _t) in entries:
            if ln <= n:
                prev = (ln, date)
            else:
                break
        return prev

    assert "## Sources" in path.read_text(encoding="utf-8")
    flat = re.sub(r"\s+", " ", path.read_text(encoding="utf-8"))
    bad = []
    for m in re.finditer(r"\(([^)]{0,120})\)", flat):
        grp = m.group(1).strip()
        if not re.fullmatch(r"(?:LEARNINGS\s*)?(?:lines?\s*)?[\d,\s-]+", grp):
            continue
        nums = [int(x) for x in re.findall(r"\d+", grp)]
        if not nums:
            continue
        ctx = flat[max(0, m.start() - 130):m.start()]
        dates = re.findall(r"\d{4}-\d{2}-\d{2}", ctx)
        for n in nums:
            if not (9 <= n <= total):
                bad.append(f"({n}) out of LEARNINGS range")
            elif dates and entry_of(n)[1] != dates[-1]:
                bad.append(f"({n}) is {entry_of(n)}, cited as {dates[-1]}")
        # a hyphenated RANGE must stay inside one entry (a comma list may
        # legitimately cite several)
        for a, b in re.findall(r"(\d+)\s*-\s*(\d+)", grp):
            a, b = int(a), int(b)
            if 9 <= a <= total and 9 <= b <= total and \
                    entry_of(a)[0] != entry_of(b)[0]:
                bad.append(f"({a}-{b}) spans two entries "
                           f"({entry_of(a)[0]}, {entry_of(b)[0]})")
    assert not bad, f"{path.name}: stale LEARNINGS citations {bad}"


@pytest.mark.parametrize("path", remediation_files(), ids=lambda p: p.stem)
def test_remediation_ref_names_only_real_scripts(path: Path):
    """Guard against hallucinated tooling: a fixer will run what these say.

    Known = a .py that exists in the repo, or one our own scripts name (the
    vendored externals: KRT's route.py, easyeda2kicad's entry points).
    """
    real = {p.name for p in ROOT.rglob("*.py")
            if ".venv" not in p.parts and "tools" not in p.parts}
    for p in SCRIPTS.rglob("*.py"):
        real |= set(re.findall(r"\b([a-z_][a-z0-9_]*\.py)\b",
                               p.read_text(encoding="utf-8")))
    named = set(re.findall(r"\b([a-z_][a-z0-9_]*\.py)\b",
                           path.read_text(encoding="utf-8")))
    unknown = sorted(named - real)
    assert not unknown, f"{path.name}: names non-existent scripts {unknown}"


@pytest.mark.parametrize("path", remediation_files(), ids=lambda p: p.stem)
def test_remediation_ref_commands_use_real_flags(path: Path):
    """Every --flag handed to one of our scripts must exist in that script."""
    bad = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        ln = raw.replace("\\", "/")
        m = re.search(r"\b([a-z_][a-z0-9_]*)\.py\b", ln)
        if not m or "scripts/" not in ln:
            continue
        script = SCRIPTS / f"{m.group(1)}.py"
        if not script.is_file():
            continue
        src = script.read_text(encoding="utf-8")
        for flag in re.findall(r"(?<![\w-])(--[a-z][a-z0-9-]*)", ln):
            if flag not in src:
                bad.append(f"{m.group(1)}.py has no {flag}")
    assert not bad, f"{path.name}: {bad}"


# ---------------------------------------------------------------------------
# 2. fix_dispatch wiring
# ---------------------------------------------------------------------------
def _violation(check, kind=None, pos=(10.0, 10.0), net="+3V3", sev="error",
               source="drc"):
    v = {"check": check, "severity": sev, "pos": list(pos), "layer": "F.Cu",
         "net": net, "refs": [], "msg": f"{check} violation", "source": source,
         "items": [{"msg": "x", "pos": list(pos), "uuid": "u-1"}]}
    if kind:
        v["kind"] = kind
    return v


def test_remediation_paths_lookup_is_existence_based():
    assert fix_dispatch.remediation_paths(["undersized_track"]) == [
        str(REMED / "undersized_track.md").replace("\\", "/")]
    assert fix_dispatch.remediation_paths(["no_such_kind_at_all"]) == []
    assert fix_dispatch.remediation_paths([]) == []
    assert fix_dispatch.remediation_paths(None) == []
    # de-duplicated and sorted, unknown kinds dropped silently
    got = fix_dispatch.remediation_paths(
        ["silk_overlap", "silk_overlap", "no_such_kind_at_all", "creepage"])
    assert [Path(p).stem for p in got] == ["creepage", "silk_overlap"]


def test_work_orders_carry_the_matching_remediation(tmp_path):
    board = tmp_path / "b.kicad_pcb"
    board.write_text("(kicad_pcb)", encoding="utf-8")
    findings = {
        "gate": "verify", "phase": "P8",
        "violations": [
            _violation("check_current", kind="undersized_track", net="+5V",
                       source="check_current"),
            _violation("silk_overlap", pos=(60.0, 60.0), net=None),
            # T6: pour_neckdown now HAS a ref; same-domain singles merge, so
            # the two router kinds land in ONE order carrying BOTH refs
            _violation("pour_neckdown", kind="pour_neckdown", pos=(90.0, 90.0),
                       net="+12V", source="check_current"),
            # no ref for this kind -> order still valid, just no pointer
            _violation("check_current", kind="plane_missing", pos=(30.0, 30.0),
                       net="+12V", source="check_current"),
        ],
    }
    inp = tmp_path / "verify.json"
    inp.write_text(json.dumps(findings), encoding="utf-8")
    payload, _ = fix_dispatch.run(["--input", str(inp), "--board", str(board),
                                   "--out-dir", str(tmp_path / "wo")])

    assert payload["counts"]["orders"] == 3
    assert payload["counts"]["with_remediation"] == 2
    by_fixer = {o["fixer"]: o for o in payload["orders"]}
    assert set(by_fixer) == {"router", "silk", "plane"}

    router = by_fixer["router"]  # merged order carries the union of refs
    assert router["kinds"] == ["pour_neckdown", "undersized_track"]
    assert [Path(p).stem for p in router["remediations"]] == \
        ["pour_neckdown", "undersized_track"]
    silk = by_fixer["silk"]
    assert [Path(p).stem for p in silk["remediations"]] == ["silk_overlap"]
    for order in (router, silk):
        wo = json.loads(Path(order["work_order"]).read_text(encoding="utf-8"))
        assert wo["remediations"] == order["remediations"]
        assert all(Path(p).is_file() for p in wo["remediations"])
        # the fixer is told to read them, ahead of the domain guidance
        assert wo["guidance"][0] == fix_dispatch.REMEDIATION_GUIDANCE
        assert len(wo["guidance"]) == \
            len(fix_dispatch.DOMAINS[wo["fixer"]]["guidance"]) + 1
    plain = by_fixer["plane"]
    assert plain["remediations"] == []
    wo = json.loads(Path(plain["work_order"]).read_text(encoding="utf-8"))
    assert wo["guidance"] == fix_dispatch.DOMAINS[wo["fixer"]]["guidance"]


# ---------------------------------------------------------------------------
# 3. the triage register + the SKILL.md health metric
# ---------------------------------------------------------------------------
def test_every_learnings_entry_has_a_triage_row():
    """New knowledge cannot skip triage. Appending a LEARNINGS entry means
    appending its row - the message below is the row, ready to paste."""
    entries = learnings_entries()
    rows = {r["n"]: r for r in triage_rows()}
    src = LEARNINGS.read_text(encoding="utf-8").splitlines()
    missing = []
    for i, (ln, _date, title) in enumerate(entries, 1):
        if i in rows:
            continue
        tags = "".join(re.findall(r"\[[^\]]+\]", src[ln - 1]))
        missing.append(f"| {i} | {ln} | {title[:70]} | {tags} | L0 | L0 | "
                       f"UNTRIAGED | open | triage me: which artifact should "
                       f"own this? |")
    assert not missing, (
        f"{len(missing)} LEARNINGS entries have no row in design/"
        f"ladder-triage.md. Append these to its Register table (edit the "
        f"level/owner/status honestly - the rubric is in the file header):\n"
        + "\n".join(missing))
    phantom = [n for n in rows if n < 1 or n > len(entries)]
    assert not phantom, f"triage rows for non-existent entries: {phantom}"


def test_triage_rows_are_well_formed():
    rows = triage_rows()
    entries = learnings_entries()
    bad = []
    for r in rows:
        if r["now"] not in LEVELS or r["target"] not in LEVELS:
            bad.append(f"#{r['n']} level {r['now']}->{r['target']}")
        if not (r["status"] in STATUSES
                or re.fullmatch(r"planned-[TU]\d+", r["status"])):
            bad.append(f"#{r['n']} status {r['status']}")
        if not r["owner"]:
            bad.append(f"#{r['n']} no owner")
        if r["line"] != entries[r["n"] - 1][0]:
            bad.append(f"#{r['n']} line {r['line']} != {entries[r['n'] - 1][0]}")
    assert not bad, bad


def test_done_rows_are_actually_at_target():
    off = [f"#{r['n']} {r['now']}->{r['target']}" for r in triage_rows()
           if r["status"] == "done" and r["now"] != r["target"]]
    assert not off, f"status 'done' but not at target: {off}"


def test_skill_md_does_not_grow():
    """Health metric (design notes 6): knowledge climbs the ladder, so the
    always-loaded playbook shrinks. 286 = the T4 baseline."""
    skill = SKILL / "SKILL.md"
    n = len(skill.read_text(encoding="utf-8").splitlines())
    assert n <= 286, (
        f"SKILL.md is {n} lines (T4 baseline 286). New knowledge belongs in a "
        "script, a gate threshold, a template, or reference/remediations/ - "
        "not in the always-loaded prompt.")
