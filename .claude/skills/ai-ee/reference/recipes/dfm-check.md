# dfm-check - "can this actually be made"

`drc_routed` at 0/0 does NOT imply fabricable: DRC grades the board against the
project's own rules, and those rules can sit below the fab's floor. That gap is
what this recipe closes.

## What runs

`fab_export.py` writes the JLC-shaped package (Protel extensions, X2, the JLC
layer set, drill files, zipped). `bom_cpl.py` writes BOM + CPL, applying the
per-package rotation corrections from `reference/jlc_rotations.csv` - the
catcher for a polarized part mounted backwards, which net-level schematic parity
is blind to by construction.

Then the `dfm` gate. Note what it reads: `gate.py` re-exports gerbers to a
SCRATCH directory from the BOARD, plus the sibling schematic (CPL polarity
oracle) and `parts.json` (BOM leg). The shipped `fab/<board>_gerbers.zip` is an
ORDERING artifact and is NOT a gate input - which is why a board edit stales the
zip through the invalidation MARK, not through any hash comparison.

## Reading the result

- Trace width / clearance / drill / annular ring / hole-to-copper-to-edge are
  errors. A width failure a micron under a floor is still a failure: fix the
  floor at `board_init` (fab floors come from the selected JLC profile at ERROR
  severity, `lib/fabfloors.py`) and re-route, do not waive it.
- KiCad's stock 0.12 mm silk, tight mask dams and missing LCSC numbers are
  advisory warnings by design.
- `cpl_polarity` with a `rotation_delta_deg` is the mounted-backwards class.
  Believe it: the pad geometry supplies that angle.

## The second opinion

JLCDFM (the fab's own 30+ checks) has no public API and stays a human browser
step: upload the zip at the ordering checkpoint. The local engine covers the big
classes so that step finds nothing new, not so it can be skipped.

## Do not

- Do not treat a passing dfm gate as a quote. Panelization, impedance control
  and part availability are priced at JLC, and `order_quote` numbers are
  transcribed estimates (`estimated: true`), never a quote.
- Do not re-export gerbers just to "refresh" them before ordering without
  re-running the gate - the export is what the latch binds to.
