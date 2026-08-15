# P1 Research - digest (2026-08-15)

- Roster: power-architect + component-scout(buck-regulator) only. No interface-spec
  (screw terminals bind no standard), no reference-design (P3 part-level coverage
  research produces the vendor layout digest for the CHOSEN IC instead).
- Topology ruled **synchronous integrated-FET, ~500 kHz (350-600), L = 10 uH**. Async
  rejected: +0.42 W (+33 %) plus a 0.77 W diode at Tj ~126 C vs a 125 C rating (D=0.17
  means it conducts 83 % of every cycle at 30 V). >= 1 MHz rejected: 1.58-1.93 W and
  t_on(30 V) collides with min-on-time.
- Part envelope for P3: Vin abs-max >= 36 V, **Rds_LS <= 85 mOhm (rank on LS not HS+LS;
  at D=0.167 the LS FET conducts 5x longer)**, t_on_min <= 130 ns, Tj 150 C, exposed pad
  mandatory, P_U1 <= 0.95 W at 30 V/2 A. A 3 A-class part, not a marginal 2 A one.
- **2L CONDITIONAL** - the screen passes by 2 C (0.92 W x 73.8 C/W = 67.9 vs dt_c 70).
  Needs sync + Rds_LS <= 85 mOhm + outline >= ~1000 mm^2 + >= 16 thermal vias + Tj 150 C.
  Layer count FOLLOWS THE PART; re-run at P3 before P5 fixes the stackup. Mode note:
  "smallest honest outline" has a numeric floor - the outline IS the radiator.
- Scout, 5 candidates, every figure datasheet-sourced: top **LMR33630ADDAR** C841384
  (sync, 38 V, 400 kHz, $0.74@5, stock 6885); AOZ1284PI C48060 async 40 V $0.85;
  TPS54560BDDAR C1850354 65 V $1.06. AP63357Q out at 35 V abs-max (1 V short of A1);
  LMR33630's 1.4/2.1 MHz siblings pulse-skip at 30 V - only the 400 kHz "A" clears it;
  XL1509 is the only Basic part but its own +/-4 % already breaks A3's +/-3 %.
- Convergence: the scout's top pick sits inside the architect's envelope.
