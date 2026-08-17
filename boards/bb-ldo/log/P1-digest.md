# P1 Research - digest

- Roster: component-scout + reference-design (parallel), then power-architect.
  No interface-spec agent: a screw terminal is standards-free.
- **Lead part AMS1117-3.3 SOT-223, C6186 (Basic, $0.20).** Rejected MCP1825S -
  better on paper, but its only theta_JA (62 C/W) is a JEDEC 4-LAYER number,
  unreachable on 2L with no curve to design against. AMS1117 is the only
  candidate with a copper-area table on OUR board class (1oz FR-4): 90 C/W min
  pad -> 65 at 1000 mm2 -> 55 at 2500 mm2; TI's LM1117 sweep agrees ~1 C/W.
- Design point: Pd 1.00 W, target theta_JA 65 C/W -> Tj 115 C (121 C stacked
  corner). Needs >= 1000 mm2 contiguous F.Cu +3V3 pour, 645 mm2 floor.
- Tab = VOUT: heatsink pour is +3V3 and CANNOT be stitched to bottom GND;
  B.Cu = GND + a +3V3 island, 12 vias AROUND the pad (via-in-pad wicks solder).
- Caps are datasheet requirements: Cout 22 uF SOLID TANTALUM (bare MLCC sits
  below the ESR window - the 1117 oscillation trap), Cin 10 uF tantalum.
- **Gate conflict surfaced now**: check_thermal clamps credited copper at
  645 mm2 -> 73.85 C/W floor on 2L, so dt_c 65 can never pass (verified in
  source). Keep 65, waive at P8 with both vendor tables; do NOT relax to 75.
- Into P2: what Table 1's backside copper connects to; fixed-variant min-load
  requirement; actual Iq (P3). Expected outline ~35-45 mm/side - not a cap.
