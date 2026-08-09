# Brief - synchronous buck converter board (sbuck-5v3a)

Design a synchronous buck converter board.

## SPECIFICATION

- Input:        7-18V DC, nominal 12V, via 2-pin 5.08mm screw terminal
- Output:       5.0V +/-2%, 3A continuous, via 2-pin 5.08mm screw terminal
- Load step:    0 to 3A, recovery within 100us, <200mV excursion
- Output ripple: <50mV pk-pk at full load
- Efficiency:   >88% at 12V in, 3A out
- Ambient:      up to 50C, no forced airflow
- Protection:   input reverse polarity, output overcurrent, thermal shutdown
- Board:        <=50x40mm, 4x M3 mounting holes, 2 or 4 layer (your call, justify it)

## PART SELECTION

- Prefer an integrated synchronous buck IC over a controller + discrete FETs at
  this power level. Candidate families to evaluate: TI TPS54xxx/TPS56xxx, MPS
  MP23xx/MP15xx, Diodes AP63xxx, Silergy SY82xx. Do not trust remembered ratings
  for any of these - pull the datasheet and confirm Vin range, Iout, and switching
  frequency before committing.
- Verify LCSC stock and basic/extended tier for every part before finalising. A
  part that is out of stock is a failed design.
- Inductor: compute ripple current dI = (Vin - Vout) * D / (L * fsw), where
  D = Vout/Vin. Target 20-40% of full load current. Size saturation current above
  Iout + dI/2 with margin, at temperature, not at 25C. Check DCR against your
  efficiency target.
- Input capacitance: ceramic close-in for the switching loop plus bulk for the
  cable inductance. Input cap RMS current is roughly Iout * sqrt(D * (1-D)) -
  check the ceramic's ripple rating and derate MLCC capacitance for DC bias, which
  can cost more than half the nameplate value at rated voltage.
- Output capacitance: ripple is roughly dI/(8 * fsw * Cout) + dI * ESR. Check the
  load-step requirement too, which usually sets Cout above what ripple alone needs.
- Every MLCC needs voltage derating; X7R or X5R only, no Y5V.

## SCHEMATIC

- Feedback divider sized for the IC's internal reference; keep divider impedance low
  enough that FB bias current does not shift the setpoint.
- Include the bootstrap capacitor, enable/UVLO divider if the IC supports it, and a
  soft-start component if it is not internal.
- Reverse polarity: a P-channel FET in the supply path is more efficient than a
  series diode at 3A. Confirm Vgs rating against maximum input voltage.
- Add an optional RC snubber footprint across the low-side switch, DNP by default.
- Provide test points for VIN, SW, VOUT, FB, EN, GND, plus a low-inductance scope
  ground point near the output.

## LAYOUT

Placement first, routing second. Placement decides this design.

- The high di/dt loop is input capacitor -> high-side switch -> low-side switch ->
  back to the capacitor's ground. Minimise its enclosed area above everything else.
  Put the smallest input ceramic directly across the IC's VIN and PGND pins on the
  same layer, no vias in that loop.
- The switch node is the primary radiator. Make its copper large enough to carry
  current and conduct heat, and no larger. Do not pour it as a plane.
- Keep the feedback trace short, away from SW and the inductor body, and tap it from
  the output capacitor terminal rather than the inductor pin so it senses the
  regulated node.
- Bootstrap capacitor directly at its pins.
- Single low-impedance ground reference under the converter. Avoid routing signal
  returns through the power ground path. If 4 layer, put an uninterrupted ground
  plane on the layer directly under the switching components and do not cut it.
- Size copper by current using IPC-2152, accounting for the 10-20C rise you can
  accept. 1oz outer copper is 35um; check whether inner layers are 0.5oz in the
  stackup you pick.
- Place a via array under the IC's thermal pad and stitch the ground planes together
  around the loop.

## THERMAL

- Estimate dissipation at 12V/3A from the IC's efficiency curve, then check junction
  temperature against RthJA for the copper area you actually have, at 50C ambient.
- Inductor DCR loss is I^2 * DCR; confirm the part's own temperature rise.
- If the numbers do not close, increase copper area or change parts. Do not assume
  the exposed pad alone is sufficient.

## EMI / DFM

- Keep the switching loop and SW node away from the board edge and connectors.
- No unnecessary ground plane splits or slots under the converter.
- Silkscreen legible, none on pads, polarity and pin 1 marked on every polarised part.
- Respect JLCPCB's minimum trace/space, annular ring, and hole sizes for the process
  class you select. Confirm every footprint's rotation against JLCPCB's CPL
  convention, not the KiCad default.

## BEFORE DECLARING DONE

1. DRC and ERC clean, zero unrouted nets.
2. Recompute inductor peak current, input cap RMS current, output ripple, and
   junction temperature from the parts you actually chose, and state the numbers.
3. Confirm each part is in stock at LCSC with its part number recorded.
4. Report the input loop enclosed area, switch node copper area, feedback trace
   length, and thermal via count.

## DECISION POLICY

Make every remaining decision yourself. Do not ask clarifying questions. Where this
brief is silent, take the conventional, conservative option. Record each non-obvious
choice in DECISIONS.md with one line of reasoning.

Deliver: schematic, layout, gerbers, BOM, CPL, DECISIONS.md, and the computed
numbers above.
