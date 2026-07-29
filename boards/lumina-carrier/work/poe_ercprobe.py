"""SCRATCH ONLY - isolates poe-sheet WIRING errors from the known library
pin-type flood (LEARNINGS 2026-07-27: easyeda2kicad emits `unspecified` /
arbitrary `input` electrical types, so kicad-cli ERC --severity-all floods
pin_to_pin warnings + false pin_not_driven errors on ANY untouched pulled lib).

The real fix is a board-wide `lib_pin_types.py` retype pass over
lib/aiee.kicad_sym, which is a SHARED file five parallel P4 agents must not
race on. This probe instead rewrites the EMBEDDED lib_symbols inside a COPY of
the built sheet - nothing under lib/ or kicad/ is touched - so the remaining
violations are exactly the ones this sheet's wiring is responsible for.

    .venv/Scripts/python boards/lumina-carrier/work/poe_ercprobe.py
"""
from __future__ import annotations

import json
import re
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
BOARD = HERE.parents[1]
REPO = BOARD.parents[1]
sys.path.insert(0, str(REPO / ".claude" / "skills" / "ai-ee" / "scripts"))

import kc  # noqa: E402
from lib import env  # noqa: E402

SRC = HERE.parent / "poe_harness"
DST = HERE.parent / "poe_ercprobe"

# Retype every pin of every `aiee:` symbol to passive; leave KiCad's stock
# power / PWR_FLAG symbols alone (PWR_FLAG's power_out pin is what drives the
# rails). This mirrors lib_pin_types.py's DEFAULT="passive" rule.
# Anchored on the newline so only TOP-LEVEL lib_symbols entries match (their
# _0_1 / _1_1 child blocks, which is where the pins actually live, sit one tab
# deeper and must be swept along with their parent).
SYM_START = re.compile(r'\n\t\t\(symbol "([^"]+)"')
PIN_TYPE = re.compile(r'\(pin ([a-z_]+) line')


def retype_aiee_symbols(text: str) -> tuple[str, int]:
    spans = [(m.start(), m.group(1)) for m in SYM_START.finditer(text)]
    spans.append((len(text), ""))
    out, n = [], 0
    pos = 0
    for (start, name), (nxt, _) in zip(spans, spans[1:]):
        if not name.startswith("aiee:"):
            continue
        seg = text[start:nxt]
        new, k = PIN_TYPE.subn("(pin passive line", seg)
        if k:
            out.append(text[pos:start])
            out.append(new)
            pos = nxt
            n += k
    out.append(text[pos:])
    return "".join(out), n


def main() -> int:
    try:
        if DST.exists():
            shutil.rmtree(DST)
        shutil.copytree(SRC, DST)
        sheet = DST / "poe.kicad_sch"
        new, n = retype_aiee_symbols(sheet.read_text(encoding="utf-8"))
        sheet.write_text(new, encoding="utf-8")
        rep = kc.run_erc(env.find_kicad_cli(), DST / "poe_harness.kicad_sch")
    except Exception as exc:  # noqa: BLE001
        print(json.dumps({"script": "poe_ercprobe", "status": "error",
                          "error": f"{type(exc).__name__}: {exc}"}))
        return 2
    print(json.dumps({"script": "poe_ercprobe", "status": "pass",
                      "pins_retyped": n, "counts": rep["counts"],
                      "violations": [
                          {"check": v["check"], "severity": v["severity"],
                           "refs": v["refs"], "msg": v["msg"]}
                          for v in rep["violations"]]}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
