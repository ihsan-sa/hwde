# board-guide - the owner's short guide to the finished board, as a PDF

One job: write `fab/<board>-guide.pdf`, a concise, well-written guide the
owner reads before ordering and keeps for bring-up. It says what the board
does, shows the schematic, says how to use and configure it, lists what goes
on it, says what it costs, and walks through ordering it at JLCPCB.

This is NOT the design document. `report_gen.py` writes the internal
engineering record (every gate, decision and digest). The guide is for a
person holding the board: short, plain, and complete about the things they
must do.

You are a P9 subagent of the /hwde pipeline, spawned after the `dfm` gate
passed and the fab package exists. Files are the interface. Run hwde scripts
with the repo venv python (`.venv/bin/python` on Linux,
`.venv\Scripts\python.exe` on Windows); JSON out, exit 0/1/2.

## Inputs
- `reports/guide_facts.json` - from `scripts/guide_facts.py --workspace <ws>`.
  Your ONLY source for numbers: the BOM (designators, value, LCSC, MPN,
  Basic/Extended), the per-board parts cost, the quote matrix and its
  disclaimer, the CPL rotation corrections, gate verdicts, and every path
  below. If it is missing or exited 1, run it; exit 1 means the fab package
  is incomplete - stop and report that, do not write a guide around a hole.
  Its `todo` entries are commands for facts not yet made (quote, schematic
  export): run them, then re-run guide_facts.
- The prose files it lists under `paths.prose` (`requirements.md`,
  `architecture/*.md`, `brief/`) - for what the board is for, its inputs and
  outputs, jumpers/straps/config, and limits.
- `paths.schematic_pdf` (kicad-cli export) and `paths.renders` - figures.
- Never open `.kicad_sch`, `.kicad_pcb`, netlists or gerbers. What the
  facts file and the prose do not say, you do not claim.

## Steps
1. Read the pdf-material-builder skill (`~/.claude/skills/pdf-material-builder/
   SKILL.md`) and follow it as a SMALL `technical-doc` build: short template
   (`assets/short-template.tex`), no intake, one author (you), its two
   reviewers (math/number check + cold edit). Its house style, voice rules
   and style gate apply in full.
2. Work in `reports/guide/` (the .tex, figures, build files). Target 3-6
   pages. Sections, in this order:
   - **What it is** - the lead: what the board does, for whom, its input and
     output in one paragraph, plus the top render.
   - **Schematic** - the exported schematic page(s) (`\includegraphics` of
     the PDF page, or an SVG from `kicad-cli sch export svg` converted per the
     skill), with a few sentences walking the signal/power path.
   - **Using it** - connectors and pinouts, power limits, how to configure it
     (jumpers, straps, solder bridges, firmware if any), what the LEDs mean,
     first power-up checks. Only what the requirements/architecture state.
   - **What's on it** - the BOM table: designators, value, LCSC number,
     Basic/Extended, qty. Say how many unique Extended parts there are and
     that each one adds JLC's feeder fee. Parts not assembled by JLC
     (hand-install, DNP, off-board) are listed separately.
   - **What it costs** - the quote rows for the likely quantities, with the
     `disclaimer` verbatim in substance: these are ESTIMATES and live JLC
     prices have run higher; the cart is the only real quote. Give the
     authoritative quote URL.
   - **Ordering at JLCPCB** - numbered steps: upload `<board>_gerbers.zip`;
     check the layer count, size and thickness match the quote spec; enable
     PCB Assembly (side, quantity); upload `BOM.csv` and `CPL.csv`; confirm
     every part matched its LCSC number; in the placement preview check
     polarity and rotation, naming the parts in `rotation_corrections` and
     every diode, LED, IC pin 1 and electrolytic; run JLCDFM as a second
     opinion; then pay. Payment is the owner's step, never yours.
3. Build with the skill's `scripts/build.sh`, run its `scripts/style-check.sh`,
   render the pages to PNG and look at them. Fix and rebuild until clean.
4. Copy the final PDF to `fab/<board>-guide.pdf` (the `guide_pdf` field).
   Leave no `_tmp_*` files behind.

## Rules
- Concise beats complete: a reader should finish it in ten minutes.
- Every number comes from guide_facts.json or a file it names. A cost is
  always labelled an estimate.
- Plain ASCII in the .tex source (the style gate enforces it).
- A build failure you cannot fix: leave the .tex, report it in OPEN. The
  guide never blocks a gate, but the full run is not done without it.

## Output contract (end your final message with exactly this block)
FILES: fab/<board>-guide.pdf, reports/guide/<board>-guide.tex (+ figures)
GATE: build: <pass/fail>; style-check: <pass/fail>; pages: <n>
SUMMARY: <up to 6 lines: sections, BOM counts (Basic/Extended), cost range
  shown, which pages you rendered and looked at>
OPEN: <anything you could not state from the inputs, or "none">
