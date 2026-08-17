# LEARNINGS recall for bb-mcu (grepped 2026-08-16, root LEARNINGS.md)

Prior gotchas that apply to THIS board, with the phase that must honor them.

- **P3 sourcing** - `[sourcing][jlcpcb]` 2026-08-07: LCSC's package/type fields
  are USELESS for connector mount style. This board has three through-hole
  connectors; verify TH vs SMD by the footprint's PAD LAYERS, never by the
  LCSC package string.
- **P2 architecture** - `[knowledge][coverage]` 2026-08-15: coverage envelopes
  are tested ONLY against a block's own `operating_point`. Board-level facts
  (board_layers, source_kind, ...) must be REPEATED in every block entry.
- **P5/P7** - `[P7][pipeline][rules_gen]` 2026-08-08: regenerating the
  schematic WIPES rules_gen's netclasses out of the .kicad_pro. Re-run
  rules_gen after any schematic regen.
- **P6 place gate** - `[placement][geometry][gates]` 2026-08-14: the
  effective-courtyard BBOX flags tight-but-legal decouplers next to a
  pad-field package (LQFP/QFP corners are pad-free but inside the bbox).
  Expect this on the MCU's decoupling caps; judge it, do not blindly spread.
- **P6 constraints** - `[placement][constraints][gates]` 2026-08-16:
  `keepouts` are board-LOCAL (never translated) and `separation` is
  centre-to-centre AND skipped when either ref is locked.
- **P6 fit** - `[board_edit][placement][build-modes]` 2026-08-16: `--outline
  fit` cannot recover the size a layout wanted if placement was told to FIT an
  outline. Placement must target the canonical layout, not the provisional
  edge. And `[planes][zones]` same day: a zone outline does not follow the
  board edge - re-run planes_gen if the board GREW.
- **P8** - `[P8][pipeline][decoupling]` 2026-08-08: `root.py` REWRITES
  `decoupling.json` from scratch; hand-added rail associations do not survive
  a schematic regen. And `[P8][gate][waivers]` same day: gate.py's default
  waiver sidecar path is `<pcb-dir>/reports/`, not the workspace `reports/`.
- **P9** - `[P9][gate][pipeline]` 2026-08-09: `gate.py --gate dfm` looks for
  `parts.json` BESIDE THE BOARD or the BOM-completeness leg silently skips.
- **This session (parallel runs)** - `[git][process][waves]` 2026-08-15:
  `git commit -- <dir>` stages MODIFICATIONS only, new files need `git add`
  first. gate.py's --commit is already workspace-scoped and refuses when
  anything outside boards/bb-mcu/ is pre-staged. And `[windows][process]`:
  the Bash tool collapses `\\` to `\` inside a quoted heredoc - author edit
  scripts with the Write tool.
