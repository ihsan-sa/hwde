"""knowledgelib - the class-indexed knowledge library (U4, v3 design decision 2).

One RECORD per file under reference/knowledge/records/<id>.yaml. A record is a
CLASS-level engineering fact (power-loop, EMI, thermal-via, ...) with the keys
that make retrieval DETERMINISTIC - the same trigger-not-judgment principle as
reference/remediations/ (T4): at runtime nobody decides they "need EMI
knowledge"; a board DECLARES a buck block / an SO-8-EP package, and the
matching records are injected by exact key lookup.

Record shape (schema-validated; the single source of truth is RECORD_SCHEMA):

  id: buck-input-hot-loop            # == filename stem, unique
  classes: [power-loop, emi]         # controlled vocab: CLASSES
  applies:                           # >= 1 non-empty list, else unreachable
    topologies: [buck]               # keyed by constraints.json blocks[]
    packages: [SO-8-EP]              # keyed by parts.json parts[].package
    interfaces: [usb]                # keyed by diff_pairs[].base / --interfaces
  rule:                              # machine-checkable fields, or null
    enforced_by: null                #   script[:--flag] that enforces it (must
    hf_bypass_nf: 100                #   exist), null = not yet enforced
  prose: >                           # the fact + why; <= PROSE_MAX chars -
    ...                              #   this text is PROMPT-INJECTED
  sources:                           # down to the page/section
    - {file: reference/knowledge/sources/x.pdf, page: 4}
  status: active                     # active | draft | superseded
  origin: migration:topologies/buck  # where the record came from

Sources PDFs live under reference/knowledge/sources/. Retrieval consumers:
scripts/knowledge.py (CLI), the orchestrator spawn step (SKILL.md), and
datasheet_extract.py --app-note (record-shaped extraction template).

Matching is normalized: topology/interface tokens casefold; package tokens
additionally drop non-alphanumerics ("SO-8-EP" == "SO8EP" == "so-8 ep") -
vendor package strings are not stable enough for exact string equality.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import yaml

LIB = Path(__file__).resolve().parent
SCRIPTS = LIB.parent
SKILL = SCRIPTS.parent
REPO = SKILL.parents[2]
RECORDS_DIR = SKILL / "reference" / "knowledge" / "records"
SOURCES_DIR = SKILL / "reference" / "knowledge" / "sources"

# Controlled class vocabulary (grow it here when a NEW class is real - same
# pattern as cluster_violations.FIXER_HINTS; tests pin committed records to it).
CLASSES = frozenset({
    "power-loop", "emi", "thermal", "thermal-via", "decoupling", "feedback",
    "selection", "sourcing", "inrush", "sequencing", "return-path",
    "constraints-emission", "esd", "creepage",
})
STATUSES = ("active", "draft", "superseded")
PROSE_MAX = 1500  # prompt-injected; a record is a focused fact, not an essay

RECORD_SCHEMA: dict = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "ai-ee knowledge record",
    "type": "object",
    "required": ["id", "classes", "applies", "rule", "prose", "sources",
                 "status", "origin"],
    "additionalProperties": False,
    "properties": {
        "id": {"type": "string", "pattern": "^[a-z0-9][a-z0-9-]*$"},
        "classes": {"type": "array", "minItems": 1,
                    "items": {"type": "string"}},
        "applies": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "topologies": {"type": "array", "items": {"type": "string"}},
                "packages": {"type": "array", "items": {"type": "string"}},
                "interfaces": {"type": "array", "items": {"type": "string"}},
            },
        },
        "rule": {
            "oneOf": [
                {"type": "null"},
                {"type": "object", "minProperties": 1,
                 "properties": {"enforced_by": {"type": ["string", "null"]}},
                 "additionalProperties": {
                     "type": ["string", "number", "boolean", "null"]}},
            ],
        },
        "prose": {"type": "string", "minLength": 1, "maxLength": PROSE_MAX},
        "sources": {
            "type": "array", "minItems": 1,
            "items": {
                "type": "object",
                "required": ["file"],
                "additionalProperties": False,
                "properties": {
                    "file": {"type": "string", "minLength": 1},
                    "page": {"type": "integer", "minimum": 1},
                    "section": {"type": "string"},
                    "note": {"type": "string"},
                },
            },
        },
        "status": {"type": "string", "enum": list(STATUSES)},
        "origin": {"type": "string", "minLength": 1},
    },
}


def blank_record() -> dict:
    """Schema-shaped skeleton (the --app-note extraction template)."""
    return {
        "id": "",
        "classes": [],
        "applies": {"topologies": [], "packages": [], "interfaces": []},
        "rule": None,
        "prose": "",
        "sources": [{"file": "reference/knowledge/sources/<pdf>", "page": 1}],
        "status": "active",
        "origin": "app-note:<pdf>",
    }


# ---------------------------------------------------------------------------
# normalization + loading
# ---------------------------------------------------------------------------
def norm_token(s: str) -> str:
    """Topology / interface / class key normalization."""
    return str(s).strip().casefold()


def norm_pkg(s: str) -> str:
    """Package key normalization: casefold + drop non-alphanumerics, so
    'SO-8-EP' == 'SO-8EP' == 'so8 ep' (vendor strings are not stable)."""
    return re.sub(r"[^a-z0-9]", "", str(s).casefold())


def record_files(records_dir: Path | str | None = None) -> list[Path]:
    d = Path(records_dir) if records_dir else RECORDS_DIR
    return sorted(d.glob("*.yaml"))


def load_records(records_dir: Path | str | None = None) -> list[dict]:
    """Parsed records, each with '_path' (skill-relative posix). Unparseable
    YAML raises - validate() reports it instead of raising."""
    out = []
    for p in record_files(records_dir):
        data = yaml.safe_load(p.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            try:
                data["_path"] = p.relative_to(SKILL).as_posix()
            except ValueError:
                data["_path"] = p.as_posix()
            out.append(data)
    return out


# ---------------------------------------------------------------------------
# validation (validate_registry-style: every named artifact must exist)
# ---------------------------------------------------------------------------
def _source_exists(file: str) -> bool:
    """Source files resolve skill-relative or repo-relative."""
    if not file or file != file.strip():
        return False
    return (SKILL / file).is_file() or (REPO / file).is_file()


def _script_flag_problems(where: str, text: str) -> list[str]:
    """T4 remediation rule, applied to record prose: every *.py named must
    exist in the repo, and every --flag on a line naming one of OUR scripts
    must appear in that script's source."""
    problems = []
    real = {p.name for p in SCRIPTS.rglob("*.py")} | \
           {p.name for p in (REPO / "tests").rglob("*.py")}
    for name in set(re.findall(r"\b([a-z_][a-z0-9_]*\.py)\b", text)):
        if name not in real:
            problems.append(f"{where}: names non-existent script {name}")
    for ln in text.splitlines():
        m = re.search(r"\b([a-z_][a-z0-9_]*)\.py\b", ln)
        if not m:
            continue
        script = SCRIPTS / f"{m.group(1)}.py"
        if not script.is_file():
            continue
        src = script.read_text(encoding="utf-8")
        for flag in re.findall(r"(?<![\w-])(--[a-z][a-z0-9-]*)", ln):
            if flag not in src:
                problems.append(
                    f"{where}: {m.group(1)}.py has no {flag}")
    return problems


def validate(records_dir: Path | str | None = None) -> list[str]:
    """Structural problems across the records dir, as human-readable strings.
    Empty list = the library is internally consistent and every named
    artifact exists. Run by knowledge.py --validate and the test suite."""
    import jsonschema
    problems: list[str] = []
    seen_ids: dict[str, str] = {}
    validator = jsonschema.Draft202012Validator(RECORD_SCHEMA)

    for p in record_files(records_dir):
        where = p.name
        try:
            raw = p.read_text(encoding="utf-8")
        except OSError as exc:
            problems.append(f"{where}: unreadable ({exc})")
            continue
        try:
            raw.encode("ascii")
        except UnicodeEncodeError as exc:
            problems.append(f"{where}: not ASCII-safe ({exc})")
        try:
            data = yaml.safe_load(raw)
        except yaml.YAMLError as exc:
            problems.append(f"{where}: invalid YAML ({exc})")
            continue
        # YAML escapes can smuggle non-ASCII past the raw check, and record
        # text is prompt-injected verbatim - check the PARSED values too.
        try:
            json.dumps(data, ensure_ascii=False).encode("ascii")
        except UnicodeEncodeError:
            problems.append(f"{where}: not ASCII-safe (parsed values)")
        if not isinstance(data, dict):
            problems.append(f"{where}: not a mapping")
            continue

        for err in sorted(validator.iter_errors(data), key=lambda e: list(e.path)):
            path = "/".join(str(x) for x in err.path) or "(top)"
            problems.append(f"{where}: schema {path}: {err.message}")
        rid = data.get("id")
        if rid and rid != p.stem:
            problems.append(f"{where}: id {rid!r} != filename stem {p.stem!r}")
        if rid in seen_ids:
            problems.append(f"{where}: duplicate id {rid!r} (also {seen_ids[rid]})")
        elif rid:
            seen_ids[rid] = where

        for c in data.get("classes") or []:
            if norm_token(c) not in CLASSES:
                problems.append(
                    f"{where}: unknown class {c!r} (grow knowledgelib.CLASSES "
                    "if the class is real)")
        applies = data.get("applies") or {}
        if isinstance(applies, dict) and not any(
                applies.get(k) for k in ("topologies", "packages", "interfaces")):
            problems.append(
                f"{where}: applies has no keys at all - no board can ever "
                "retrieve this record (the T4 unreachable-trigger failure mode)")

        for i, src in enumerate(data.get("sources") or []):
            if isinstance(src, dict) and not _source_exists(src.get("file", "")):
                problems.append(
                    f"{where}: sources[{i}].file {src.get('file')!r} not found "
                    "(skill-relative or repo-relative)")
        rule = data.get("rule")
        if isinstance(rule, dict) and rule.get("enforced_by"):
            ref = str(rule["enforced_by"])
            script = ref.split(":", 1)[0]
            spath = SCRIPTS / script
            if not script.endswith(".py") or not spath.is_file():
                problems.append(
                    f"{where}: rule.enforced_by names non-existent script {ref!r}")
            elif ":" in ref:
                token = ref.split(":", 1)[1]
                if token not in spath.read_text(encoding="utf-8"):
                    problems.append(
                        f"{where}: rule.enforced_by {ref!r}: {token!r} not "
                        f"found in {script}")
        problems += _script_flag_problems(where, data.get("prose") or "")
    return problems


# ---------------------------------------------------------------------------
# retrieval
# ---------------------------------------------------------------------------
def select(records: list[dict], topologies=(), packages=(),
           interfaces=()) -> list[dict]:
    """ACTIVE records matching any key, sorted by id. Draft/superseded records
    are never injected."""
    tops = {norm_token(t) for t in topologies}
    pkgs = {norm_pkg(p) for p in packages}
    ifs = {norm_token(i) for i in interfaces}
    out = []
    for r in records:
        if r.get("status") != "active":
            continue
        ap = r.get("applies") or {}
        hit = (
            tops & {norm_token(t) for t in ap.get("topologies") or []}
            or pkgs & {norm_pkg(p) for p in ap.get("packages") or []}
            or ifs & {norm_token(i) for i in ap.get("interfaces") or []}
        )
        if hit:
            out.append(r)
    return sorted(out, key=lambda r: r.get("id") or "")


def workspace_keys(ws: Path | str) -> dict:
    """Deterministic retrieval keys for a workspace - NO agent judgment.

    topologies: constraints.json blocks[].topology (P2's block list; the
      board-side sidecar via statelib.kind_path, falling back to
      architecture/constraints.json before P5).
    packages:   parts.json parts[].package (P3's chosen packages; kind_path,
      falling back to parts/parts.json - the pre-P5 layout).
    interfaces: diff_pairs[].base from the same constraints file.
    """
    import statelib
    ws = Path(ws)
    state: dict = {}
    sp = ws / "state.json"
    if sp.is_file():
        state = json.loads(sp.read_text(encoding="utf-8"))
    board = state.get("board") or ws.name
    registry = state.get("artifacts") or {}
    imap = statelib.load_map()

    keys = {"topologies": [], "packages": [], "interfaces": [],
            "sources": {}}

    cpath = ws / statelib.kind_path("constraints", board, imap, registry)
    if not cpath.is_file():
        cpath = ws / "architecture" / "constraints.json"
    if cpath.is_file():
        data = json.loads(cpath.read_text(encoding="utf-8"))
        blocks = data.get("blocks") or []
        keys["topologies"] = sorted({
            norm_token(b["topology"]) for b in blocks
            if isinstance(b, dict) and b.get("topology")})
        keys["interfaces"] = sorted({
            norm_token(d["base"]) for d in data.get("diff_pairs") or []
            if isinstance(d, dict) and d.get("base")})
        keys["sources"]["constraints"] = cpath.as_posix()

    ppath = ws / statelib.kind_path("parts", board, imap, registry)
    if not ppath.is_file():
        ppath = ws / "parts" / "parts.json"
    if ppath.is_file():
        data = json.loads(ppath.read_text(encoding="utf-8"))
        keys["packages"] = sorted({
            str(p["package"]) for p in data.get("parts") or []
            if isinstance(p, dict) and p.get("package")})
        keys["sources"]["parts"] = ppath.as_posix()
    return keys


def prompt_block(records: list[dict], keys: dict | None = None) -> str:
    """The ASCII block the orchestrator pastes into a spawn prompt. Empty
    string when nothing matched (the caller then injects nothing)."""
    if not records:
        return ""
    keys = keys or {}
    shown = {k: keys.get(k) for k in ("topologies", "packages", "interfaces")
             if keys.get(k)}
    lines = ["KNOWLEDGE RECORDS (deterministic retrieval"
             + (f"; keys: {json.dumps(shown, sort_keys=True)}" if shown else "")
             + "). Treat rules as constraints; cite the record id when you "
             "apply or overrule one:"]
    for r in records:
        lines.append(f"- {r['id']} [{', '.join(r.get('classes') or [])}]")
        prose = " ".join((r.get("prose") or "").split())
        lines.append(f"  {prose}")
        rule = r.get("rule")
        if isinstance(rule, dict):
            fields = {k: v for k, v in rule.items() if k != "enforced_by"}
            if fields:
                lines.append("  rule: " + " ".join(
                    f"{k}={v}" for k, v in sorted(fields.items())))
        srcs = []
        for s in r.get("sources") or []:
            loc = s.get("file", "")
            if s.get("page"):
                loc += f" p.{s['page']}"
            if s.get("section"):
                loc += f" {s['section']}"
            srcs.append(loc)
        if srcs:
            lines.append("  source: " + "; ".join(srcs))
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# topology view rendering (reference/topologies/<t>.md stays as a view)
# ---------------------------------------------------------------------------
def render_topology(records: list[dict], topology: str) -> str:
    """Markdown view of every record applying to a topology - the generated
    replacement for the hand-written reference/topologies/<t>.md. Deterministic
    (sorted by id); a test pins the committed view to this render."""
    t = norm_token(topology)
    hits = [r for r in sorted(records, key=lambda r: r.get("id") or "")
            if t in {norm_token(x) for x in
                     (r.get("applies") or {}).get("topologies") or []}
            and r.get("status") == "active"]
    lines = [
        f"# Topology reference: {topology} (GENERATED VIEW - do not hand-edit)",
        "",
        "Source of truth: reference/knowledge/records/ (U4). Regenerate with",
        f"`scripts/knowledge.py --render-topology {topology} --out "
        f"reference/topologies/{topology}.md`; a test pins this file to the",
        "records, so hand-edits fail the suite - edit the record, re-render.",
        "",
        "HOW TO USE (research-reference-design agents): read this FIRST, then",
        "research only the part-specific delta (exact external-component",
        "table, errata, the family's FB flavor). Cite deltas against the",
        "record ids. Retrieval into P6/P7 spawn prompts is automatic",
        "(knowledge.py --select) once constraints.json declares the block.",
    ]
    for r in hits:
        lines += ["", f"## {r['id']} [{', '.join(r.get('classes') or [])}]", ""]
        lines.append((r.get("prose") or "").rstrip())
        rule = r.get("rule")
        if isinstance(rule, dict):
            fields = {k: v for k, v in rule.items() if k != "enforced_by"}
            if fields:
                lines += ["", "Rule: " + " ".join(
                    f"{k}={v}" for k, v in sorted(fields.items()))]
        srcs = []
        for s in r.get("sources") or []:
            loc = s.get("file", "")
            if s.get("page"):
                loc += f" p.{s['page']}"
            if s.get("section"):
                loc += f" {s['section']}"
            srcs.append(loc)
        if srcs:
            lines += ["", "Sources: " + "; ".join(srcs)]
    lines.append("")
    return "\n".join(lines)
