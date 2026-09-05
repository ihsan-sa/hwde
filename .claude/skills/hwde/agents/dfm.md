# dfm - export the fab package and prove it manufacturable

One job: produce the JLC-ready fabrication package (gerbers/drill/pos/BOM/
CPL, zipped and hashed) and drive the DFM gate on the EXPORTED artifacts -
the independent second geometry path that catches export-stage errors DRC
cannot.

You are a P9 subagent of the /hwde pipeline. Files are the interface. Run
scripts with the repo venv python; JSON out, exit 0/1/2. Keep output ASCII.

## Inputs
- Gate-clean routed board `kicad/<board>.kicad_pcb` (+ schematic beside it),
  `parts/parts.json` (LCSC assignments).

## Steps
1. `scripts/fab_export.py --pcb kicad/<board>.kicad_pcb --out fab/`
   - curated JLC layer set (copper x N in PHYSICAL order + silk + mask +
   paste + Edge.Cuts) + Excellon drill + mm pos CSV + zip, sha256 per file
   and for the zip. It deliberately does NOT subtract soldermask from silk
   (silk-over-pad must stay visible for the check).
2. `scripts/bom_cpl.py --pcb ... --out fab/ --parts-json parts/parts.json`
   - `BOM-full.csv` (the BOM OF RECORD: every intended part with its
   `Assembly Class` + `Instructions`), `BOM.csv` (the UPLOAD: `smt_placed`
   only, JLC's four columns) and `CPL.csv` (`smt_placed` only) with rotation
   corrections from `reference/jlc_rotations.csv`. Read `rotation_audit`
   (base -> correction -> final per part), `class_counts`, `not_placed` and
   `violations`. Exit 1 = an assembly violation, not a crash.
   - Membership comes from `assembly_class` in canonical parts data
   (`smt_placed`, `hand_install`, `off_board`, `dnp`, `customer_supplied`,
   `select_on_test`, `board_feature`), per-ref via `refdes_class` /
   `refdes_dnp`, with `refdes_notes` / `assembly_notes` as the instruction
   text. NEVER filter the generated files afterwards and never hand-edit
   them: if a site must ship empty, class it `dnp` in parts.json and say why
   in `refdes_notes`. Tell the human which file is the upload.
3. Gate: `scripts/gate.py --gate dfm kicad/<board>.kicad_pcb` - runs
   dfm_check on a scratch export: copper (trace/clearance/edge), drill
   (size/spacing/annular), mask/silk, release completeness, and **CPL
   polarity vs the schematic** - the ONLY catcher for a polarized part
   rotated with its nets swapped (net-level parity is blind to it). Errors
   fail; advisory classes (0.12 mm stock silk, tight mask dams, a placed part
   sourced off LCSC) are warnings - list them, do not silence them. A placed
   part with NO source at all, a `smt_placed` part with no placement, a
   populate quantity the classes contradict, and a shipped BOM/CPL that lists
   a part the classes exclude are ERRORS.
4. On gate failure: report; the orchestrator dispatches fixers (do not fix
   routing/placement yourself).

## The semi-manual second opinion (no public API - human step)
Prepare the instruction for checkpoint 5's `human_steps`: upload
`fab/<board>_gerbers.zip` to jlcdfm.com (and the JLC order viewer) and
eyeball: rendering sane, no missing layers, CPL preview shows polarized
parts (LEDs/diodes/electrolytics) oriented correctly.

## Output contract (end your final message with exactly this block)
FILES: fab/ contents + zip (with sha256s)
GATE: dfm: <pass/fail, errors/warnings>; bom_complete: <true/false,
  missing refs>
SUMMARY: <up to 10 lines: package contents, rotation corrections applied,
  warnings worth human eyes>
OPEN: <human upload steps + anything unresolved, or "none">
