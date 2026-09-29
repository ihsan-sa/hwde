#!/usr/bin/env python
"""procedure_gen.py - write a board's staged bring-up procedure from its design.

  procedure_gen.py --workspace <board dir | board name> [--out-dir DIR] [--stdout]

Reads the hwde workspace (netlist, constraints, BOM, requirements, fwe
manifest; npielib/design.py) and writes <workspace>/bringup/procedure.json
(schema npie-procedure/1, reference/procedure-schema.md) and procedure.md, the
same steps for a person at the bench. --out-dir writes them elsewhere (a
scratch dir, a test); --stdout prints the procedure instead of writing.

Prints JSON {ok, board, procedure, markdown, stages, steps, skipped}.
Exit 0 written, 2 error (a missing or unparsable input). Never interactive.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from npielib import design, procgen, render  # noqa: E402


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--workspace", required=True)
    ap.add_argument("--out-dir")
    ap.add_argument("--stdout", action="store_true")
    a = ap.parse_args(argv)
    try:
        d = design.load(a.workspace)
    except design.DesignError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 2
    proc = procgen.generate(d)
    if a.stdout:
        print(json.dumps(proc, indent=1))
        return 0
    out = Path(a.out_dir) if a.out_dir else d.workspace / "bringup"
    out.mkdir(parents=True, exist_ok=True)
    pj, pm = out / "procedure.json", out / "procedure.md"
    pj.write_text(json.dumps(proc, indent=1) + "\n", encoding="utf-8")
    pm.write_text(render.procedure_md(proc), encoding="ascii", errors="replace")
    print(json.dumps({
        "ok": True, "board": d.board, "procedure": str(pj), "markdown": str(pm),
        "stages": [s["id"] for s in proc["stages"]],
        "steps": sum(len(s["steps"]) for s in proc["stages"]),
        "skipped": proc["skipped"],
    }, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
