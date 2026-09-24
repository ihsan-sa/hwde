# ERC / schematic-review waivers (pd-trigger-lite, 2026-09-24, delegate)
ERC: 0 errors, 0 warnings - nothing waived.
Schematic review (reports/review-schematic.md), 0 errors, 2 warnings, both accepted:
- W1 no interlock for "exactly one link": zero links floats CFG1, two links parallel two Rset values.
  Accepted: the board ships with one link (R5) fitted; the guide and silk labels say move the one 0R.
  All links are now identical 0603 lands, so "relocate the 0R" is the natural rework.
- W2 no TVS/fuse/bulk against 20 V hot-plug ringing: decision D4 (datasheet requires none, brief says
  none). Disclosed in the guide.
Post-review edits (not re-reviewed, ERC re-run 0/0): R7 0R VBUS->/VHV split (width rule vs 1 mm pitch),
JP1-3 moved from solder-jumper footprints to empty 0603 lands (DNP).
