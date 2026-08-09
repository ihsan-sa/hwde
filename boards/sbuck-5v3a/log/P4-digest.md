# P4 Schematic digest - sbuck-5v3a

- Gates: `erc` **0 errors / 0 warnings** (2 attempts, both pass; 2nd after the snubber
  rewire). `netlist_audit` exit 0, 0 violations. 15 nets, 44 components, 86/86 pins
  connected. Regen identity confirmed (two builds electrically identical).
- Fresh-context review: **0 errors / 7 warnings**. No netlist change was required by
  any finding. 2 warnings FIXED, 5 waived -> `reports/erc-waivers.md`.
- Vout = 5.0000 V exactly (105k/20.0k, both 0.1%), corners 4.9417/5.0585 V = +/-42 mV
  margin. The reviewer showed 1% parts MISS by 32-36 mV, so 0.1% is proven, not asserted.
- UVLO VON 6.230 / VOFF 5.325 V, 0.905 V hysteresis, verified against the vendor's
  pull-up-inclusive Eq.2/3 - and the vendor's own constants shown self-consistent.
- Compensation R5=75k, C2=3.3nF, C3=10pF. The reviewer reproduced P4's table TO THE
  DIGIT independently, then falsified its calibration: the vendor's Fig.29 plot has
  C4=33pF fitted, so the claimed validation compared the wrong variant. Claim withdrawn.
  Like-for-like factor is 0.743, not 0.83 - the model is optimistic on all three axes.
- **Honest standing of the loop**: PM 45.6-52.8 deg vs a 45 deg floor. Load step
  **200 mV against a 200 mV limit** on the corrected reading (148 mV modelled). No R5
  value clears fc, PM and dV together (sweep in root.py s2.5a), and dV is INVARIANT in
  COUT, so more capacitance would be pure cost. Accepted as an at-limit disclosure and
  logged as the board's #1 bring-up bench item; R5/C2/C3 are 3 adjacent 0603 parts.
- The fc "24.4 kHz vs 25 kHz" shortfall is NOT a requirement miss - 25 kHz was the
  orchestrator's own proxy; the real spec is 100 us recovery and settling is 32.6 us (3.1x).
- Fixed, not waived: DNP snubber overstressed its own resistor (162 mW at 18 V into an
  0603 rated 0.1 W). R9 -> 1206 0.25 W, C16 -> 470pF C0G 1206. Now 76 mW, 30% of rating.
- C3 refitted as the Eq.19 COMP pole; the reviewer measured the Eq.20 feedforward as
  CONDITIONALLY UNSTABLE, not merely low-margin - a stronger result than P4 knew.
- Caveat on evidence quality: the clean ERC is WEAK proof for U1, since nearly every
  U1 pin is `passive` in the pulled library. Pin-level confidence comes from the
  datasheet extract + the reviewer's independent netlist read, not from the gate.
- Carried forward: silkscreen connector labelling (Q30's ONLY mitigation for a swapped
  input/output, unreachable from a generator) -> P6/P8. DNP filtering -> P9 manual.
  SIM-1/SIM-2 -> P8.
