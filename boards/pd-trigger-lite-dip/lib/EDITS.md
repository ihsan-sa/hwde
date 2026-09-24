# lib edits (pd-trigger-lite)
- ESSOP-10 (CH224A): pin-1 silk dot moved from (-1.92,1.26) r0.28 to (-2.1,1.45) r0.15 - the pulled dot touched the exposed pad (fpfix residue, 3 silk_over_copper).
- SolderJumper-2_P1.3mm_Open_RoundedPad1.0x1.5mm: copied from KiCad 10 Jumper.pretty unchanged.
- OUT_2P_P2.54_D1.1: from KiCad PinHeader_1x02_P2.54mm_Vertical; pads 2.0 mm, drill 1.1 mm (20 AWG wire or header pin), silk body lines removed, excluded from BOM/pos.
- (dip) SW-SMD_5P-P1.27_1.27-5P (C7421518): pulled attr through_hole -> smd (all pads SMD; keeps it in the CPL).
- (dip) every footprint's 3D model path rewritten from an absolute worktree path to ${KIPRJMOD}/../lib/aiee.3dshapes/.
- (dip) SW-SMD_5P-P1.27_1.27-5P: courtyard grown from the body (7.93 x 5.4) to 8.6 x 9.5 so it encloses the gull-wing pads.
