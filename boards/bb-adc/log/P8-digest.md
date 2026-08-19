# P8 Verification - digest

- Gates: `sim` PASS (6 benches / 47 bounds), `drc_routed` PASS 0/0, `verify` PASS with
  ONE waiver. kicad-cli DRC 0 violations, 0 unconnected, 0 parity.
- SIM closed the board's largest open risk BY MEASUREMENT: zero-scale swing is 4.50 uV
  = 0.090 ADC codes against the vendor's "loses a small number of codes" warning, and
  the sampled value recovers to within 10 nV of ground in 1.24 us of a 9.0 us window.
  The pre-authorised -0.3 V generator is NOT needed. C7 stays 1 nF (guaranteed 950 pF
  settles 115x inside budget). Seeding the REJECTED OPA333 as a defect moved settling
  0.136 -> 4509 uV, independently re-auditing that rejection by a different method.
- Return path: /SCLK and /DOUT cleared by rebuilding the /CS crossing as a PERPENDICULAR
  VIA PAIR so both crossings fall inside the vias' 0.95 mm excision disks. /CS residual
  0.20 mm2 / 0.03 mm WAIVED (2-layer: a B.Cu trace has no adjacent GND plane, so its
  coplanar return is outside the checker's model; and J2 vs converter pin order is a
  3-cycle, so the crossing is topologically forced). Refused to shorten the tunnel
  0.09 mm to close it - no physics, ~0.04 mm of DRC margin.
- Board review (fresh context) 5 errors / 5 warnings. ALL FIVE ERRORS FIXED:
  E1 J1 was BACKWARDS - throats faced into the board; rotated, re-routed (a 180 deg
  rotation swaps the pads). E5 GND inside the guard ring - fixed by re-routing the
  GUARDED net's spanning tree, not the intruder: 1.20 -> 0.52 mV. E2/E3/E4 silk:
  J2 pin-1 mark outside the body, J1 SIG/GND, and both impedance numbers.
- Guard ring re-proved CLOSED after every refill (1 polygon, 1 hole containing all
  /AIN_DIV, min width 0.612 mm) - and it closes ONLY at the 0.127 mm floor.
- Board 54.750 x 34.920 mm, 1911.9 mm2. A 17 um re-fit was refused as sub-noise.
