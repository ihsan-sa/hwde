# P8 Verification - digest

- All five gates green: erc PASS, place PASS, drc_routed PASS (DRC 0/0,
  completion 1.00), verify PASS (8/8 checks ran, 8/8 passed), sim PASS
  (11 benches, 76 bounds). Advisory legs check_irdrop and check_pdn_z: pass.
- check_diffpair initially FAILED the gate demanding sub-0.75 mm coupling over
  a deliberately mirror-symmetric pair. Fixed the PREMISE, not the symptom:
  max_uncoupled_mm 5.0 -> 12.0 with a note that this pair has no coupling
  requirement. FOURTH sighting of the diff_pairs symmetry-vs-impedance
  conflation on this board (P2 slot typing, P5 netclass width, P7 route_critical,
  P8 check_diffpair).
- Fresh verify-reviewer found 2 ERRORS, both fixed rather than waived:
  1. THE BOARD HAD NO CONNECTOR POLE LEGEND AT ALL - 14 silk items, all refdes,
     7 hand-wired poles unmarked. J3 reversed destroys both ICs; J1 reversed
     reads as a dead amplifier. Invisible to every gate. 7 legends now placed
     outside the housings, board NOT grown, DRC 0.
  2. Every human-facing doc stated the OPPOSITE pole order (requirements.md
     s2 + 9a Q2, blocks.md B1 + diagram, the H1 design-doc PDF). The P6 swap
     reached the netlist and schematic but not upstream. All corrected.
- Reviewer independently VERIFIED the board's two central claims by measurement,
  not by trusting reports: input pair one F.Cu segment per leg, 0 vias,
  10.808963 mm each, delta 0.000000, mirroring /IN_P about y=30.0000 reproduces
  /IN_N endpoint for endpoint; B.Cu pour one polygon, 528 vertices,
  1236.8224 mm2, bit-identical to its pre-routing area, 2400 mirrored corridor
  samples with zero asymmetry.
- 1 warning waived with reasoning: C4's refdes reads as U2's label; silk_place
  finds no collision-free position at 0.5 mm and KiCad's own DRC reports 0 silk
  findings.
- Tooling defects logged: verify_all without sidecars runs 2 of 8 checks while
  the gate reports 8/8 coverage; render.py's out-dir does not match
  report_gen's search ladder, silently dropping the layout section.
