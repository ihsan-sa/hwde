# P1 Research - digest

- Roster: component-scout (`inamp`) + reference-design (`bridge-front-end`).
  Power-architect skipped (trivially powered); interface-spec skipped (screw
  terminals are not standards-bound).
- REF-pin impedance is the architecture fork, cross-checked TI+ADI: classic
  3-op-amp in-amps (AD8226/INA333/INA828) need REF driven low-Z (AD8226 Fig.59
  marks the bare divider "INCORRECT"); ICF parts (AD8237/AD8420) have 100M-800M
  REF and tolerate a divider.
- Bandwidth vs drift squeeze at 3.3 V: INA333 makes drift (0.1 uV/C) but only
  ~2.2 kHz at G~150; INA828 has the bandwidth but needs 4.5 V min. AD8226
  (2.2-36 V, ~13.6 kHz at G=147, CMRR 120 dB min, 22-24 nV/rtHz) clears both.
- Discrete 3-op-amp killed quantitatively: TI SBOA582 Eq.7 puts 0.01% resistors
  ~44 dB short of the ~118 dB this board needs.
- RECONCILED BY ORCHESTRATOR: the scout's grounded-REF split dies on AD8226's
  (V-)+0.1 V output floor - at G1=100 the bottom 2 mV of span sits in stage-1
  saturation. A positive buffered REF is unavoidable; handed to P2 with the math.
- P2 must verify: BW-at-gain (interpolated), real RTI drift (VOSI+VOSO/G), and
  the Vout-vs-Vcm diamond plot at Vs=3.3 V.
