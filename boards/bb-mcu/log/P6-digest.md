# P6 Placement - digest (2026-08-16)

- Gate **place PASS 0/0**, attempt 2, commit 503723c. Attempt 1 is the
  agent's honest FAIL against the provisional outline - see the defect below.
- **PIPELINE DEFECT**: at a geometry-OUTPUT binding the place gate must run
  AFTER `board_edit --outline fit`, not before as the recipe documents.
  Legality measures declared edges against the CURRENT outline, so a
  canonically placed J1 sat 16.9 mm from the provisional edge and failed;
  satisfying it would spread the connectors to the provisional size, which
  fit then "earns" - bb-buck with the sign flipped. The fix is the ORDER.
- Size EARNED **34.77 x 22.26 mm** (774 mm2) from a 51.15 x 43.52 provisional.
  Hand layout beat both annealer candidates (HPWL 161.36 vs 200.12); route
  probe completion 1.00, 0 unrouted.
- U1 rot 270 is the floorplan: SWD end -> J2/top, VDD/VSS -> J1/right,
  PA0-PA3 -> J3/left, all three escapes non-crossing. Decoupler loops
  4.70-7.46 nH, all inside class limits.
- J1 rotation PROVEN by side render: its wire mouth is at footprint-local -Y,
  the REVERSE of the KF128 family in root LEARNINGS. Guessing would have
  faced the wire opening into the board - a defect no gate checks.
- Silk verified by me on the render: J2/J3 per-pin labels in the ruled order
  with pin-1 markers; J1 +3V3/-GND each beside its own pole.
