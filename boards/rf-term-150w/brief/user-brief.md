# User brief (verbatim)

Design a single-port 50 ohm / 150W RF termination board.

Fill in before running:
- Fc (operating frequency): **up to 25 MHz** (user answer, given mid-run)
- Duty: [CW | pulsed, ___% duty, ___ ms max on-time]  -> LEFT BLANK, see A2

## Requirements
- One SMA female (jack) port, mating with a standard male-terminated
  SMA cable. 50 ohm resistive termination. DC resistance 50 ohm +/-2%.
- 150W dissipation at Fc. Board provides the RF launch and mechanical
  interface only; thermal path is a bolt-on external heatsink or coldplate
  that is not part of this design.
- Return loss >= 26 dB at Fc after adjustment; >= 20 dB across Fc +/-10%.
- Must include an operator-adjustable means of nulling residual reactance
  at Fc, adjustable after assembly without desoldering or unbolting the
  board. Document the procedure and the achievable adjustment range.

## Constraints
- <= 4 unique BOM line items, <= 6 total placements.
- 2 layers, JLCPCB standard FR4 process only - no upcharge options, no
  controlled-impedance service.
- Board outline <= 30x30 mm.
- <= $40 total for a build of 5, BOM at qty-5 pricing included.
- All parts in stock at LCSC or DigiKey; no NRND or obsolete.

## Resource budget
- Trivial board. Single pass - no alternates exploration, no iterative
  placement/route optimization beyond what DRC requires.
- Do not ask clarifying questions. Make assumptions, record them in the
  README, and proceed.

## Deliverables
- KiCad project, ERC and DRC clean against JLCPCB 2-layer rules.
- Gerbers, drill, BOM, CPL.
- One-page README: tuning procedure, tuning range, and the heatsink
  thermal resistance required to hold the termination at its rated flange
  temperature at 150W and 25 C ambient - computed from the actual
  datasheet derating curve, with the derated air-cooled power stated.

## Report asked for
One-line status, BOM cost at qty 5, and the assumptions taken.
</content>
</invoke>
