# P6 Placement digest - LUMINA carrier (LUM-CAR-A)

Artifacts: `reports/gate-place.json`, `reports/place_seed.json`,
`reports/place_anneal.json`, `reports/place_metrics_final.json`,
`reports/place_region_audit.json`, `reports/place/*.ops.json`,
`reports/render_place/*.png`, `reports/route-probe-p6.json`.

- **Gate `place`: PASS, 0 violations** (1 attempt).
- **HPWL 4212 -> 3601 mm**, crossings **955 -> 613**, utilisation **24.7 %**.
- **Route probe completion 0.9842** (5 unrouted of 317), above the 0.98 bar - i.e.
  the placement was confirmed routable before P7 was entered.
- 116 footprints placed (109 schematic components + 5 board-only mounting holes,
  plus fiducial/board items).

## Two self-inflicted issues found and fixed here

1. **My own `.kicad_dru` HV rules were over-scoped.** With no pad-pair exclusion
   they fired **30 times between adjacent pins of the SAME package**: U1's own
   VDD/VSS at 0.200 mm, U22's HTSSOP pitch, and C1/C61/C62/C63's own two pads at
   0.590 mm. No placement can fix a 0.65 mm-pitch package, and that was never the
   rule's purpose - TI's 0.635 mm guidance governs **board copper around** the part,
   not the vendor's lead frame. Added `!(A.Type=='Pad' && B.Type=='Pad')` plus a
   per-refdes same-courtyard exclusion (enumerated, never wildcarded) to all three
   rules: **30 -> 0**. This loses no coverage because P8 `check_creepage`
   independently models pad-to-pad from the `voltages` table.
2. **A blanket silk-clip sweep was over-aggressive and was caught before commit.**
   The first pass was scoped board-wide and removed **241** silk primitives,
   stripping legitimate silkscreen from nearly every passive - a 0603's body outline
   naturally overlaps its own pad bboxes. Caught by sanity-checking the count,
   restored from backup, and re-scoped to only the refs DRC actually flagged:
   **exactly 5 clipped** (J1 x4, D22 x1), verified by differencing the silk-layer
   references against the backup.

## Debt this phase created, and it is real

Silk DRC violations were taken **236 -> 5** by 9 ops files carrying **160
`move_text` ops** that pushed refdes *outward* to clear overlaps. Nothing pulled
them back. The board was therefore optimised for a zero-warning gate at the cost of
assembly legibility: baseline **median refdes offset 4.079 mm, max 12.955 mm, and
100 of 116 refdes more than 1 mm beyond their own part's pad extent** (worst: C2 at
+10.067 mm). The owner raised this as a requirement and it is repaid in P8, as a
constrained minimisation - pull each label back toward its own part while
`silk_overlap` / `silk_over_copper` / `silk_edge_clearance` stay at zero.
