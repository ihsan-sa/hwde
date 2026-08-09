# P6 Placement digest - sbuck-5v3a

Gate `place`: **PASS, 0 violations.** Final DRC: 2 warnings (a footprint defect,
not placement) + 71 unconnected (P7's). 8 of 8 edit iterations used.

## The four numbers the brief demanded

| Deliverable | Result | Limit |
|---|---|---|
| Input hot-loop enclosed area | **2.57 mm^2** (C9 out 2.14 mm, return 3.69 mm) | minimise |
| /SW copper area | **~26 mm^2** (17.4 pour + 8.6 taps) | <= 40 mm^2 |
| /FB run | **2.21 mm** R6->U1.5; 7.04 mm incl. R7 | short |
| Thermal vias under U1 | **12** (not 16 - see below) | - |

C9 (100 nF) sits 0.7 mm off U1's VIN pad on F.Cu, GND pad aligned to the BST|VIN
inter-pad slot, return through a 0.67 mm slot - **no vias in the loop**. C5-C8 form
the next ring 4-6 mm out. C4 is 22.2 mm away as constraints require. /SW is 5.97 mm
long, >= 2.5 mm wide, 6.25 mm from the nearest edge and 9.7 mm from J2. FB senses at
**C12's +5V terminal**, not the inductor pin.

## Findings that changed other phases

- **16 thermal vias is geometrically impossible.** EP 3.502 x 2.613 mm; four 0.55 mm
  lands at 1.0 mm pitch need 3.55 mm, and JLC's 0.5 mm hole-to-hole floor caps it at
  3x4 = 12 at 0.9-0.95 mm pitch. R_via 2.48 vs 1.90 K/W = **+0.5 C of Tj**, inside
  the margin. `check_thermal` would not have caught this.
- **`placement.fixed` silently disabled all 8 separation constraints** - fixed refs
  are excluded from the annealer's cluster list, so every pair landed in
  `separation_unknown_refs` at zero cost weight. Verified all 8 by hand; all pass.
- **P5 omitted the mandatory keepout translation** - rects were still board-local,
  three landed off-board, the fourth produced a phantom violation. Corrected.
- **Both connector rotations in `placement.edges` were wrong** (J1 0, J2 180 pointed
  both wire entries INTO the board). Correct: J1=270, J2=90. Proven by orthographic
  side render - the mouth is the SHORTER plastic face here, so the WRL bbox alone
  would have misled.

## Judgment calls

- **Anneal rejected on merit.** Candidates hit HPWL 224.6 vs the hand structure's
  234.0, but the 3.1% is almost entirely plane-fed GND, all four carried 5-7
  courtyard overlaps after repair, and cand1 pulled R7 3.5 mm closer to L1 and
  lengthened /FB.
- Silk complete and DRC-verified, 112 warnings -> 2: "VIN 7-18V" / "VOUT 5V 3A" with
  polarity at both terminals, pin-1/polarity on C4/D1/D2/U1, all 7 test points
  labelled by signal, board name + REV A + date. This is Q30's ONLY mitigation for a
  swapped connector, so it was a requirement, not decoration.

## Handed to P7

- **Pour the four GND planes AND pour /SW as a zone BEFORE any autoroute.** The 0.83
  route probe is an artifact: GND is 25 of 71 connections and plane-fed, so unpoured
  Freerouting tried it as 2.055 mm tracks. And `aiee_pwr_width_SW` (2.31 mm) applies
  to EVERY /SW track including the 0603 bootstrap cap's - a zone is not a track.
- 25 structural footprints are LOCKED; P8 fixers must unlock before nudging.
- 2 residual DRC warnings are a D2 SOD-123 footprint defect (silk clips pad 2's mask
  by ~0.05 mm) - library fix approved and in progress.
- Cosmetic: C9's refdes label sits over C7's body; `silk_place` found no better spot.
