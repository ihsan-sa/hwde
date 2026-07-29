# P1 Research - digest

Roster: 4 `research-component-scout` (led-emitter, drive-stage, energy-store,
protection-sense) + 1 `research-reference-design` (pulsed-led-driver) + 1
`research-power-architect`. No `research-interface-spec`: the only standards-bound
interface is the expansion connector and it is frozen and fully specified.

- **led-emitter**: no JLC-stocked white LED is DC-rated for 2.6 A, and every published
  pulse rating in this market is at ~100 us / 10 % duty - 50x to 2000x shorter than the
  5-200 ms flashes here. Cree's XP-G2 datasheet contains the word "pulse" zero times.
  Design rule adopted: budget ZERO pulsed headroom, keep peak inside each die's DC max.
  Verdict: array goes OFF-BOARD on an aluminium MCPCB + heatsink (on-board FR4 would be
  120-200 C of rise). The right optic is no optic - bare 120 deg at 2.3 m already covers
  the 5x7 m room; any TIR narrows it to the STR-REQ-16 failure mode.
- **drive-stage**: JLC has no HV linear CC driver near 2.6 A and no wide-SOA linear-mode
  MOSFET at all, so the discrete op-amp + shunt + FET loop is forced, not preferred.
  200 mohm 2512 shunt beats 50 mohm (13 % vs 54 % offset error at STR-REQ-04's 10 % dim
  point). Found the LED-short fault: the loop keeps regulating 2.6 A into a shorted
  string, 125-148 W in the FET, no self-termination.
- **energy-store**: 4 x 680 uF/100 V = 2720 uF, 27 mm tall, $6.18/board. Ripple and ESR
  are NOT binding (8.7x ripple margin, 1.43 % IR sag); height, endurance and Extended
  fees are. Growing the bank 4x does not fit (64 % of the board, 37 mm tall) and even
  then holds full output only 36.9 ms.
- **refdesign-pulsed-led-driver**: TI TIDA-01081 is direct prior art. The decay tail is
  the driver's inductor, output capacitance and soft-start - never the LED (phosphor
  persistence ~60 ns, four orders below the 1 ms spec). Shunt-FET dimming REJECTED: it
  keeps burning current while dark. Linear-mode SOA rules: pick older generations and
  higher voltage classes, never select on Rds(on).
- **power**: zero local regulators, zero magnetics, one current limiter. Board
  dissipation is an invariant, `P_rail x (48 - V_string)/48 + housekeeping` - string
  voltage is the only first-order lever. Exactly ONE full-energy flash from a full bank.
  And the finding that matters beyond this board: **the 802.3at upgrade does not close
  thermally.**
