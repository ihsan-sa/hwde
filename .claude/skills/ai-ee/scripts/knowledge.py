#!/usr/bin/env python
"""knowledge.py - class-indexed knowledge library: validate / select / render (U4).

The retrieval half of v3 design decision 2. Records live in
reference/knowledge/records/*.yaml (shape: knowledgelib.RECORD_SCHEMA);
retrieval is TRIGGERED, never judged:

  --validate            lint every record (schema, id/filename, controlled
                        classes, source files exist, named scripts/flags
                        exist). exit 0 clean / 1 problems.
  --select              records matching a workspace's declared keys and/or
                        explicit --blocks/--packages/--interfaces. Emits
                        {keys, count, records, prompt_block}; prompt_block is
                        what the orchestrator pastes into a P3/P6/P7 spawn
                        prompt (empty = inject nothing). exit 0 even when
                        empty - no match is a fact, not a failure.
      --workspace WS    derive keys: constraints.json blocks[].topology
                        (P2's block list) + diff_pairs[].base, parts.json
                        parts[].package (P3's packages).
      --blocks a,b      explicit topology keys (union with workspace keys)
      --packages a,b    explicit package keys
      --interfaces a,b  explicit interface keys
  --list                every record: id, status, classes, applies.
  --render-topology T   regenerate reference/topologies/<T>.md from the
                        records (--out required); prints a JSON summary.
                        The committed view is test-pinned to this render.

Contract (SPEC section 6): argparse, JSON to stdout or --out, exit 0/1/2,
ASCII, no interactivity. --records-dir overrides the library root (tests).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(SCRIPTS / "lib"))

import knowledgelib  # noqa: E402
from checklib import utf8_stdout  # noqa: E402

SCRIPT = "knowledge"


def _csv(v: str | None) -> list[str]:
    return [x.strip() for x in (v or "").split(",") if x.strip()]


def do_validate(records_dir) -> tuple[dict, int]:
    problems = knowledgelib.validate(records_dir)
    n = len(knowledgelib.record_files(records_dir))
    payload = {"script": SCRIPT, "status": "pass" if not problems else "problems",
               "records": n, "problems": problems}
    return payload, 0 if not problems else 1


def do_select(args) -> tuple[dict, int]:
    keys = {"topologies": [], "packages": [], "interfaces": [], "sources": {}}
    if args.workspace:
        ws = Path(args.workspace)
        if not ws.is_dir():
            return {"script": SCRIPT, "status": "error",
                    "error": f"workspace not found: {ws}"}, 2
        keys = knowledgelib.workspace_keys(ws)
    keys["topologies"] = sorted(set(keys["topologies"]) | {
        knowledgelib.norm_token(t) for t in _csv(args.blocks)})
    keys["packages"] = sorted(set(keys["packages"]) | set(_csv(args.packages)))
    keys["interfaces"] = sorted(set(keys["interfaces"]) | {
        knowledgelib.norm_token(i) for i in _csv(args.interfaces)})

    records = knowledgelib.load_records(args.records_dir)
    hits = knowledgelib.select(records, keys["topologies"], keys["packages"],
                               keys["interfaces"])
    payload = {
        "script": SCRIPT, "status": "pass", "keys": keys, "count": len(hits),
        "records": [{k: r.get(k) for k in
                     ("id", "classes", "applies", "rule", "prose", "sources",
                      "origin", "_path")} for r in hits],
        "prompt_block": knowledgelib.prompt_block(hits, keys),
    }
    return payload, 0


def do_list(records_dir) -> tuple[dict, int]:
    records = knowledgelib.load_records(records_dir)
    payload = {"script": SCRIPT, "status": "pass", "count": len(records),
               "records": [{"id": r.get("id"), "status": r.get("status"),
                            "classes": r.get("classes"),
                            "applies": r.get("applies")} for r in records]}
    return payload, 0


def do_render(args) -> tuple[dict, int]:
    if not args.out:
        return {"script": SCRIPT, "status": "error",
                "error": "--render-topology requires --out (the view path)"}, 2
    records = knowledgelib.load_records(args.records_dir)
    text = knowledgelib.render_topology(records, args.render_topology)
    used = text.count("\n## ")
    if not used:
        return {"script": SCRIPT, "status": "error",
                "error": f"no active records apply to topology "
                         f"{args.render_topology!r} - refusing an empty view"}, 2
    Path(args.out).write_text(text, encoding="utf-8", newline="\n")
    return {"script": SCRIPT, "status": "pass", "written": args.out,
            "records_used": used}, 0


def main(argv: list[str] | None = None) -> int:
    utf8_stdout()
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--validate", action="store_true")
    mode.add_argument("--select", action="store_true")
    mode.add_argument("--list", action="store_true")
    mode.add_argument("--render-topology", metavar="TOPOLOGY")
    ap.add_argument("--workspace", help="--select: derive keys from this workspace")
    ap.add_argument("--blocks", help="--select: explicit topology keys, comma-sep")
    ap.add_argument("--packages", help="--select: explicit package keys, comma-sep")
    ap.add_argument("--interfaces", help="--select: explicit interface keys, comma-sep")
    ap.add_argument("--records-dir", help="override the records dir (tests)")
    ap.add_argument("--out", help="write JSON here (or the view for "
                                  "--render-topology; then the JSON summary "
                                  "goes to stdout)")
    args = ap.parse_args(argv)

    try:
        if args.validate:
            payload, code = do_validate(args.records_dir)
        elif args.select:
            payload, code = do_select(args)
        elif args.list:
            payload, code = do_list(args.records_dir)
        else:
            payload, code = do_render(args)
    except Exception as exc:  # noqa: BLE001 - contract: any error -> exit 2
        payload, code = {"script": SCRIPT, "status": "error",
                         "error": f"{type(exc).__name__}: {exc}"}, 2

    text = json.dumps(payload, indent=1, ensure_ascii=True)
    if args.out and not args.render_topology:
        Path(args.out).write_text(text, encoding="utf-8")
    else:
        print(text)
    return code


if __name__ == "__main__":
    sys.exit(main())
