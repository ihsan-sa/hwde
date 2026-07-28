# P3 digest (usb-buck)
parts.json 18 distinct / 28 refs; 11 Basic / 7 Extended; ~$5.11/board.
Sourcer caught AP63203WU-7 stock=1 -> QWU-7 sibling swap. Extracts: C8734
(reused from run a), C5248536 (buck: FB->VOUT direct, EN float-enable, 4ms
SS confirmed, L 3.3-15uH DCR<30m - waived at 60m w/ math), C2687116 (ESD:
pin5 IS VBUS, flow-through 1+6/3+4 confirmed - architecture ESD Q closed).
Librarian: 18/18 pulled, fp_verify 4/0/2 benign; found easyeda2kicad dup
bug + API rate limit (3 LEARNINGS); 11/12 courtyards < pad field (placelib
fix carries it); silk-on-pad on 4 passive fps + U2 no printable pin-1 ->
approved sanitize in flight. J1 shield = 4 THT pins 6-9 all "EP" (netlist
must tie all to GND); J1 slots at JLC 0.5mm minimum (P9 note).
