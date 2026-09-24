# pd-trigger-lite-dip - decisions (variant of pd-trigger-lite, 2026-09-24)

D1, D3-D7 carry over from pd-trigger-lite unchanged; D2 is replaced, D8-D10 are new.

- D1 CH224A (C42459160, $0.45): VHV rated 32 V takes VBUS directly; published Rset table.
- D2 (rewritten) Voltage select = SW1, a 5-position DIP switch used one-hot.
  Pos1: CFG1 -> R5 100k -> VHV = CFG1 high = 5 V (manual 5.2.2 table 5-2, CFG2/CFG3
  don't care; 6.1.2 names exactly this 100k pull-up to VHV). Pos2-5: CFG1 -> 6.8k / 24k /
  56k / 120k -> GND = 9 / 12 / 15 / 20 V (5.2.1 table 5-1). CFG2/CFG3 float on their
  internal pull-ups. Rules for the owner: exactly one switch ON, set before plugging in.
  All off = CFG1 floating (request undefined). Two on = not allowed: pos1 plus an Rset
  divides VHV, and once VHV rises above 5 V that can drive CFG1 past its 3.8 V absolute
  max (manual 7.1).
- D3 J1 6-pin power-only USB-C (C2798175); DP/DM unconnected.
- D4 No TVS, fuse or bulk capacitor (datasheet asks only 1 uF on VHV). Hot-plug risk disclosed.
- D5 Output = two unassembled 2.54 mm plated holes.
- D6 LED on VBUS via 10k.
- D7 2-layer 1.6 mm 1 oz; VBUS 3 A band on F.Cu (solid pad connection), B.Cu GND pour.
- D8 SW1 = SHOU HAN 1.27-5P TPPT (C7421518, extended, $0.53, 9.8k in stock, 24 V / 25 mA
  contacts): half-pitch SMD, the most-stocked 5-position 1.27 mm part JLC can place. An open
  switch sees at most VHV = 20 V (< 24 V rating); contact current is microamps.
- D9 Board grows 25 x 15 -> 25 x 21 mm: the switch block (8.9 x 8 mm switch + Rset column)
  replaces the link grid and needs 6 mm more height. Everything below it is lite's layout
  moved down.
- D10 Silk: voltage beside each switch row (20/15/12/9/5 from top), "<ON" above the switch
  on the CFG1 side. Confirmed 2026-09-24 from LCSC's product photo of C7421518
  (assets.lcsc.com/images/lcsc/900x900/20230615_SHOU-HAN-1-27-5P-TPPT_C7421518_front.jpg): "ON"
  is printed on the edge opposite the 1-5 position numbers, which is the pin 6-10 row - the
  CFG1 row here. The datasheet has no drawing of it. R1-R5 refdes hidden (no room; the voltage labels do that job).
