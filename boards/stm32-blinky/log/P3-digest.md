# P3 digest (stm32-blinky)
parts.json: 12 distinct parts, 9 Basic + STM32 Extended + 2 THT headers
(hand-solder; economy PCBA is SMT-only). $2.77/board at qty 1 prices.
Architect's from-memory crystal LCSC corrected (C32828 vref -> C12674).
Extracts: C8734 (48 pins x2-source cross-check, VDD 24/36/48 VDDA 9, decoupling
100nF/pin + 4.7uF@VDD_3 + VDDA 1uF//10nF + NRST 100nF, LQFP48 land Fig63),
C6186 (pin1 GND/2 VOUT/3 VIN/tab VOUT, 22uF tantalum COUT stability).
Librarian: 12/12 pulled+registered, fp_verify 4 pass/0 fail/1 benign warning
(STM32 pad 0.27x1.50 vs 0.30x1.20 rec), courtyard-less list EMPTY, polarity
marks present+correct (SS34 band@K, LED chevron@pad1-cathode). Tab=VOUT ok.
