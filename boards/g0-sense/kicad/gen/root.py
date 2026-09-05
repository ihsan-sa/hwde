"""g0-sense ROOT sheet: stitches `power` + `main` into `g0-sense.kicad_sch`.

The schematic SOURCE is this file (+ the two sibling sheet generators);
`../g0-sense.kicad_sch`, `../power.kicad_sch`, `../main.kicad_sch` and
`../decoupling.json` are BUILD OUTPUT. Rebuild (from repo root):

    .venv/bin/python boards/g0-sense/kicad/gen/root.py

Both child sheets carry all four rails (VBUS/+5V/+3V3/GND) as GLOBAL power
symbols with bare netlist names (architecture/sheets.md "Root:" section) -
verified against the code (neither power_sheet.py nor main_sheet.py calls
`Sheet.hier_pin`; each ends with `sh.hier_pins == {}`, and main_sheet's own
`main()` prints that empty list). So the root sheet has NO components and
NO sheet pins of its own: `Project.add_sheet(..., nets=[])` for both
children, and this generator's only job is placing the two sheet symbols
and stitching + saving.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
BOARD = HERE.parents[2]          # boards/g0-sense
REPO = HERE.parents[4]           # repo root
sys.path.insert(0, str(REPO / ".claude" / "skills" / "ai-ee" / "scripts"))
sys.path.insert(0, str(HERE.parent))  # sibling sheet generators

import kicad_sch_api as ksa  # noqa: E402

# kicad-sch-api resolves lib_ids through its GLOBAL cache, which does not
# read kicad/sym-lib-table (LEARNINGS [python] 2026-07-27/2026-07-28) -
# register the pulled lib before either child generator's build() runs.
ksa.get_symbol_cache().add_library_path(BOARD / "lib" / "aiee.kicad_sym")

import schlib  # noqa: E402
import power_sheet  # noqa: E402
import main_sheet  # noqa: E402


def build() -> schlib.Project:
    root = schlib.Sheet(
        "g0-sense",
        title="g0-sense: USB-C powered STM32G0 + SHT40 sensor node",
        paper="A4", date="2026-08-27", company="ai-ee")

    proj = schlib.Project(root)
    # Both children expose no hier pins (all four rails are global power
    # symbols); nets=[] is correct, not an omission.
    proj.add_sheet(power_sheet.build(), at=(50.80, 50.80),
                   size=(63.50, 50.80), nets=[])
    proj.add_sheet(main_sheet.build(), at=(152.40, 50.80),
                   size=(63.50, 50.80), nets=[])
    return proj


def _fix_klc_private_properties(path: Path) -> None:
    """kicad-sch-api 0.5.6 mis-serialises stock KiCad-10 symbols' private
    KLC lint properties: `(property private "KLC_..." "note" ...)` comes
    back out of ksa missing required sub-tokens, and kicad-cli then refuses
    to load the schematic ("Failed to load schematic", exit 3). None of
    this board's own parts carry such a property (the `power:*` globals
    and PWR_FLAG are the only stock-library symbols in play), but this is
    cheap insurance at the one place that touches the final merged file -
    strip any `(property private "KLC_..." ...)` block entirely; KiCad
    does not need it to load or run ERC. Text-level, not a lib edit (the
    hard rule is: generators only, never hand-edit a .kicad_sch, and this
    runs as part of the generator's own save step).
    """
    text = path.read_text(encoding="utf-8")
    out = []
    i = 0
    needle = '(property private "KLC_'
    n_stripped = 0
    while True:
        j = text.find(needle, i)
        if j < 0:
            out.append(text[i:])
            break
        out.append(text[i:j])
        # find the matching close paren for this (property ...) sexpr by
        # depth counting from the opening "(" at j.
        depth = 0
        k = j
        while k < len(text):
            if text[k] == "(":
                depth += 1
            elif text[k] == ")":
                depth -= 1
                if depth == 0:
                    k += 1
                    break
            k += 1
        i = k
        n_stripped += 1
    if n_stripped:
        path.write_text("".join(out), encoding="utf-8")
    return n_stripped


def main(argv=None) -> int:
    out_dir = Path(argv[0]) if argv else BOARD / "kicad"
    try:
        proj = build()
        sch = proj.save(out_dir, decoupling=out_dir / "decoupling.json")
        stripped = 0
        for p in [sch, out_dir / "power.kicad_sch", out_dir / "main.kicad_sch"]:
            stripped += _fix_klc_private_properties(p) or 0
    except Exception as exc:  # noqa: BLE001  (SPEC 6: any error -> exit 2)
        print(json.dumps({"script": "gen.root", "status": "error",
                          "error": f"{type(exc).__name__}: {exc}"}))
        return 2
    print(json.dumps({
        "script": "gen.root", "status": "pass",
        "files": sorted(str(p) for p in out_dir.glob("*.kicad_sch")),
        "root": str(sch),
        "decoupling_associations": len(proj.decoupling),
        "klc_private_properties_stripped": stripped,
    }, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
