# P6 Placement - digest

- Gate `place` PASS, 0 failing across all 5 legality legs. DRC --severity-all
  + parity: 30 findings, ALL unconnected (unrouted) - 0 copper, 0 silk,
  0 courtyard, 0 parity. check_decoupling pass. Route probe on a scratch copy:
  completion 1.00, 0 unrouted of 30.
- BOARD SIZE EARNED: 47.98 x 28.251 mm (content 45.980 x 26.250, margin 1.0).
  Geometry was an OUTPUT throughout; no dimension was ever a target.
- My P5 digest misread `outline_bbox` as a size. It is min/max CORNERS: the
  provisional room was 28.02 x 44.69, not 41.0 x 57.7. The canonical layout
  needs ~46 mm of width, so the room had to be grown. Order is
  PLACE -> GROW -> FIT, because fit CLIPS and growing a fresh shelf pack refuses.
- The annealer's 4 candidates were all REJECTED: movable_clusters 2 of 5, so
  every candidate HPWL was dominated by connectors pinned to a provisional
  outline. Canonical tile hand-built instead, 2 of 8 edit iterations used.
- J1 PIN SWAP (pole 1 = IN-, pole 2 = IN+) taken on the agent's finding that the
  connector's pole order and the AD8226's pin order are reversed, forcing one
  crossing under all 8 rotation/edge combinations. Cost a P5 re-init because
  board_update refuses pad-net rewires; ops trail made the replay exact.
  Result: pair HPWL 15.23 -> 11.43 mm/leg, crossings 6 -> 5, length delta
  0.000000 mm, mirror axis y=30.0000 exact. Verified by machine: two straight
  segments, ZERO vias, 0 non-unconnected DRC findings, unconnected 30 -> 28.
- Decoupling: C1 1.50 mm, C3 1.53 mm (both straight-shot), C2 bulk 15.99 mm
  under the 20 mm warn - and vendor-correct, the 10 uF is explicitly allowed
  farther out. /VREF is a 4.11 mm straight hop. J1-to-J2 ~35 mm, pour between.
