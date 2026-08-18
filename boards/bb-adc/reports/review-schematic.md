# Schematic review - bb-adc (adversarial, P4)

Reviewer: `schematic-reviewer`, fresh context. Date 2026-08-17.
Scope tier `block-only`, binding `canonical`. Protection, ESD, non-datasheet
filtering, indicators, test points, config straps and second rails are OUT BY
MODE and are not reported here. Everything else is judged at full rigor.

Inputs read: `kicad/bb-adc.kicad_sch` (rendered to `reports/schematic.pdf` and
read, plus the s-expression parsed directly for wire/label/power-symbol
topology), `reports/top.net`, `parts/C544731.json`, `parts/C579305.json`,
`parts/C92494.json`, `parts/parts.json`, `architecture/{constraints.json,
sheets.md, blocks.md, power_tree.md}`, `requirements.md`, `reports/erc.json`
(0 violations), `reports/netlist_audit.json` (1 known cosmetic warning), the 32
VERIFIED knowledge records for this board's four topologies, and the
`power` + `connector` checklists (the two whose domains appear here).

**Gate: 1 error, 5 warnings.**

---

## ERRORS

### E1 - the -IN Kelvin sense has no carrier that survives into copper

**The schematic does this right.** I checked it at the s-expression level rather
than trusting the render:

- `U1` pin 3 (`-IN`) carries **no `GND` power symbol and no `GND` local label**.
- It is wired by an explicit five-segment run:
  `(62.23,115.57) -> (52.07,115.57) -> (52.07,95.25) -> (121.92,95.25) ->
  (121.92,50.8) -> (124.46,50.8)`, terminating on `R5`'s bottom pad.
- `(124.46,50.8)` is the **only** place on the whole sheet where a `power:GND`
  symbol is instantiated (`#PWR01`). Every other ground mark is a local label.
  Defining the board's ground *at the string bottom* is a good touch.
- A text item sits on the wire (`U1 -IN SENSE RUN to R5 bottom pad - NOT a GND
  symbol at U1`) and NOTE 1 in the sheet's text box carries the full mechanism,
  the 1/K = 2.5 weighting and the -0.3/+0.5 V bound.

**The architecture is also right, and I am not objecting to it.** The ADS8326
captures `+IN - (-IN)` once at Hold and does not resample `-IN`, so the
cancellation is exact at the sample instant. `R5`'s pad sits within microvolts
of `U1`'s GND pin - three orders inside the window. And `C544731.json` closes
the P3 caveat in `blocks.md` s8.1: the `-0.3 V to +0.5 V` limit is a **flat**
row confirmed identically in Recommended Operating Conditions and in *both* the
5 V and 2.7 V characteristics tables, with no VDD or VREF term, so this board
being off Figure 39's plotted range does not matter. Figure 39's mechanism is a
different, `+IN`-side ceiling that only binds as VREF approaches VDD. Floating a
separate analog ground would be strictly worse. Keep the approach.

**What is wrong is that nothing enforces it past P4.** On the netlist `U1.3` is
one of sixteen nodes on `GND`. At P6/P7 the B.Cu `GND` pour will thermal-connect
pin 3 to local ground copper exactly as it connects pin 4, because on the
netlist they are the same net. The moment it does, `-IN` senses the local pour
potential instead of `R5`'s pad, the dedicated corridor run becomes a redundant
parallel path carrying nothing, and the board's largest layout-controlled error
term is back - referred to the terminal at 1/K = 2.5, up to 2.5 mV, half the
25 degC budget.

Everything stays green while that happens: ERC, DRC, `netlist_audit`,
`check_return_path`, `check_pdn`. The `R5 -> U1` entry in `constraints.json` is
a 3 mm keep-clear **corridor**, which reserves area; it is not a rule that says
"`U1` pad 3 connects to `R5` pad 2 and to nothing else".

Two ways to give it a carrier, either is enough:

1. Put `-IN` on its own net (`AGND_SNS`) and join it to `GND` through a net-tie
   footprint at `R5`'s pad. This is the standard EDA expression of a
   single-point/Kelvin tie and it makes the intent visible to the router, the
   pour and every gate. It costs one library part and one net-name reconcile in
   `constraints.json` s2.
2. Or keep one net and carry an explicit P6/P7 rule: `U1` pad 3 zone connection
   = `none`, plus a P7 assertion that pin 3's only copper neighbour is `R5`
   pad 2.

Filed as an **error** deliberately. It does not stop the board converting - I
want that stated plainly - but it silently voids the specification the board
exists to make, and unlike a dead board nobody would notice.

---

## WARNINGS

### W1 - the 87 mV reference headroom was never multiplied by the rail noise the board already accepted

`series-voltage-reference-input-headroom-gate` (VERIFIED) says in its own words:
`compare_against: worst-case rail (tolerance + IR drop + ripple trough), never
nominal`.

The design compares the ADR4520's guaranteed 3.048 V floor (VIN table condition
3 V min, dropout 1 V max at both no load and 2 mA, over -40..+125 degC) against
3.135 V - **tolerance only** - and books 87 mV. That number is recorded
exhaustively and re-verified against the current Rev 0 datasheet, which is good
work. What is missing is the second term: `requirements.md` answered Q7 grants
the host **"tens of mV" of noise**. Subtract it and the margin is 40-60 mV, or
nothing at the top of "tens".

I checked what erodes it on-board and found nothing significant: no series
element between J2.1 and U2.2, and trace IR plus header contact resistance at
~2.7 mA is under 0.15 mV. So the 87 mV is real - it is simply entirely spoken
for by a noise figure nobody has bounded.

The consequence is not graceful. The design itself records that dropout is
*defined* as the point where VOUT has **already** degraded 0.1 pct: 2.05 mV on
VREF, which maps 1:1 to gain error = **5 mV at a 5 V reading = the whole 25 degC
budget** - and recovery is slow because VOUT carries 49 uF.

Existing mitigation is C1 (10 uF at J2) and C4 (100 nF at U2's VIN); both shunt
AC and neither touches the DC tolerance. Note the ADR4520's own Applications
Information offers a 1-10 uF bulk at VIN "where the supply voltage may
fluctuate", which describes this board, and it is currently satisfied only by
C1 at the far connector - C1 is also at the bottom of the
`sar-adc-supply-bypass-and-rail-isolation` record's "10 uF to 100 uF at the
supply entry" range.

Action: get a number for the host's rail trough at H1 instead of "tens of mV",
or make measuring it the first bring-up step before the accuracy claim is
trusted.

### W2 - the published accuracy claim is computed on OPA333; the board fits OPA320

`U3` is `OPA320AIDBVR` (C92494) and P3 verification item 2 made that **final**
(acquisition is a clock-cycle count, 4.5 DCLOCKs = 9.0 us exactly, and OPA333
cannot settle in it at any legal DCLOCK). But `blocks.md` s5 rows 7 and 8 and
the design doc still carry OPA333's numbers, and the headline claim is built on
them. s8.3 flagged the direction ("moves RSS 3.23 -> ~3.30 mV") and the table
was never re-run - and s8.3 also missed that one row moves the *other* way.

Recomputed from the OPA320 datasheet, Rthev 240 kohm, x2.5 to the terminal:

| row | term | was 25 C | now 25 C | was 0-50 C | now 0-50 C |
|---|---|---|---|---|---|
| 7 | Buffer Vos + drift (150 uV max; 5 uV/degC max) | 0.03 | **0.375** | 0.03 | **0.69** |
| 8 | Buffer Ib x Rthev (0.9 pA max 25 C; 50 pA max -40..+85 C) | 0.12 | **~0.001** | 0.24 | **0.030** |

Row 8 improves by ~200x - OPA320's bias current is dramatically better than
OPA333's - which partly pays for row 7.

| | was | now |
|---|---|---|
| RSS, 25 degC | 3.23 mV | **3.25 mV** |
| RSS, 0-50 degC | 3.36 mV | **3.42 mV** |
| Worst-case sum, 25 degC | 8.35 mV | **8.58 mV** |
| Worst-case sum, 0-50 degC | 10.29 mV | **10.74 mV** |

The verdict does not change: RSS still closes 5.00/12.00 at both temperatures
and the over-temperature worst case still closes 12.00. But the margin on that
last one falls from 1.71 mV (14 pct) to 1.26 mV (10.5 pct), and the numbers on
the board's own published claim are simply wrong. Restate before H1.

### W3 - the recorded ">= 10 ms before trusting a conversion" has no margin left

`power_tree.md` s5 records the right requirement and derives it from the wrong
capacitance: ">= 10 ms ... that is >= 50x the worst case in this class", built
on a ~120-200 us class settling figure. The ADR4520's own tabulated turn-on is
tR = 90 us **at CL = 1 uF**, and the datasheet says more output capacitance
"will increase the turn-on time of the device";
`series-voltage-reference-output-cap-window` names the same cost
(`cost_of_more_c: longer turn-on time and start-up input current up to ISC`).

This board hangs **49.2 uF** on VREF (C3 47 uF + C5 2.2 uF; ~35 uF after DC-bias
derating). At the ADR4520's +10 mA output current capacity, slew-limited
charging to 2.048 V is Q/I = 35e-6 x 2.048 / 10e-3 = **7 ms** derated, ~10 ms at
nominal - *before* any settling toward 10 ppm on top of that.

So the stated 10 ms is roughly 1x the charge time, not 50x. Apply the same 50x
rule to the real figure and it is >= 50 ms, or measure it at bring-up. A host
obeying the number as written reads during reference settling and will see the
first samples walk.

### W4 - J2's reverse-plug consequence is destructive and is stated nowhere

The `connector` checklist requires: *"Power pins: polarity legend on silk
visible AFTER assembly; reverse-plug consequence stated (protected or
destructive - if destructive, flag)."*

J2 is a plain 1x6 2.54 mm male header, pin 1 = `+3V3`, pin 6 = `GND`. A
180-degree mis-mate maps host pin 1 onto board pin 6 and host pin 6 onto board
pin 1, i.e. **the host's 3.3 V rail is shorted to its own ground through the
board, at both ends of the connector**. The board itself survives (it is
unpowered); the host's supply takes it. Pins 2-5 are benign by comparison (GND
onto DOUT, CS and SCLK swapped).

Nothing in `requirements.md`, `blocks.md`, `sheets.md` or J2's `Note` field says
this. I am not asking for keying or protection - the tier excludes it. The
checklist asks for the consequence to be *stated*, which costs nothing and is
not an excluded class. Note also that the pin-1 silk marking currently exists
only as intent in the `Note` fields; it becomes real at P6.

### W5 - C7's floor claim is made on nominal, not on the guaranteed value

`parts.json` for C7: *"1nF is inside the 1-2.2nF window and above the
20xC_SH=960pF floor."* The fitted part is `CC0603JRNPO9BN102`, **J grade =
+/-5 pct**, so its guaranteed minimum is **950 pF - below the board's own
960 pF floor**. C0G/NP0 contributes no temperature or DC-bias drift, so
tolerance is the entire spread and there is no recovery from the other
direction.

This is small in absolute terms (1 pct) but it is the one place the board
departs from its own stated discipline - the P2 ruling on the Rs contract chose
its configuration precisely so that "every dominant term [is] a number a vendor
guarantees".

The fix is not free in one direction: 1 nF is already the OPA320's stated
**maximum stable pure capacitive load in unity gain** (Sec 7.3.8), so raising C7
to 2.2 nF trades the charge-bucket floor against the phase margin the P8
`buffer-stability` bench has to prove. Hand both facts to that bench rather than
picking a value now.

(R6 = 49.9 ohm against TI's 10-20 ohm isolation recommendation and the ~27-31
ohm optimum from `precision-buffer-capacitive-load-isolation`'s own equation is
already recorded in the P3 decisions - not re-raised.)

---

## Checked and clean - what I could not break

**The attenuator arithmetic, from the netlist rather than the drawing.** Top arm
`R1+R2+R3` (`/AIN_RAW` - `/ATT_A` - `/ATT_B` - `/AIN_DIV`) = 600 kohm; bottom arm
`R4+R5` (`/AIN_DIV` - `/ATT_C` - `GND`) = 400 kohm. **The tap is on the correct
side: three above, two below.** K = 400/1000 = **0.4000 exactly**. Rtot =
1.00 Mohm, Rthev = 600k||400k = **240 kohm**. FS = 2.048/0.400 = **5.120 V**; a
5.000 V input lands at 2.000 V = 97.66 pct of VREF, headroom 120 mV =
**2.40 pct** - all four numbers confirmed. Loading at the contracted
Rs <= 200 ohm is 200 ppm = 1.00 mV. All five elements carry identical current, so
power is equal per element (5 uW), which satisfies
`resistive-attenuator-self-heating-and-gradient`'s "equal power per leg,
thermally symmetric string" for free - a real benefit of the equal-string form
that the docs do not claim. One MPN in all five positions
(`PTFR0805Q200KN9`, 0.02 pct / 10 ppm) with the 0805-vs-0603 package deviation
recorded and reasoned.

**The reference capacitance window: PASS at both ends.** VREF carries C5
(2.2 uF 10 V X7R 0603) + C3 (47 uF 16 V X7R 1210) = 49.2 uF nominal. Upper
bound with +10 pct tolerance and X7R's positive temperature excursion is ~62 uF,
under the 100 uF maximum. Lower bound with DC-bias derating at 2.048 V is
~30-37 uF, far above the 1 uF minimum. The two-ended window is met with wide
margin on both sides. Worth recording: **C5 alone** derates to roughly 1.3 uF,
above the 1 uF floor but by much less than its 2.2x nominal suggests - so C5 is
correctly not a DNP candidate, and C3 must not be treated as the deletable one
either.

**No series R between U2 VOUT and C3 / U1 REF - correct, on two independent
sources.** The ADS8326's own wording places a current-limiting resistor "in
front of the capacitors" (source side), and
`sar-adc-reference-charge-loop` states
`isolation_resistor_is_a_different_element` for the same reason. The `OPEN` note
in `C544731.json` ("no resistor between U2 and the REF bypass network - flagged
for the coordinator") is answered by the recorded ruling, not outstanding.
SPRABY5's 0.1 ohm damped shunt branch is a third element again and is also
correctly not fitted.

**The converter's rail entry is exactly the datasheet circuit.** R7 (10 ohm)
between `+3V3` and `U1` VDD, **upstream of both caps**; C2 (100 nF, the smaller,
closest to the pin) and C8 (10 uF) on `VDD_ADC`; `U2` and `U3` upstream on
`+3V3`; C1 (10 uF) at the J2 entry. That is ADS8326 p.26 and figs 44/45, and it
matches `sar-adc-supply-bypass-and-rail-isolation`'s `two_cap_order` and
`analog_parts_rail` rules. VDD_ADC at the worst-case rail is 3.135 - (60 uA x
10 ohm) = 3.134 V, well inside 2.7-3.6 V. No ferrite anywhere.

**Abs-max and operating point on all three ICs: clear.**
`U1` VDD 3.3 V vs 7 V abs max (and inside the 2.7-3.6 V LVCMOS operating class,
which is also the correct characteristics table for the error budget);
REF 2.048 V vs VDD+0.3; `+IN` 0-2.048 V vs the VDD+0.2 recommended ceiling and
the `-IN + VREF` ceiling that full scale defines; `-IN` at ~0 V inside the flat
-0.3/+0.5 V window. `U2` VIN 3.3 V vs 16 V abs max. `U3` VS 3.3 V vs 6 V abs max
(TI: "supply voltages larger than 6 V can permanently damage the device"),
inputs 0-2.048 V well inside (V-)-0.5 to (V+)+0.5. Nothing on this board is near
a limit.

**Decoupling, per pin, against each part's own JSON - not "some caps".**
U1 VDD -> C2 (0.1 uF close) + C8 (10 uF) + R7; U1 REF -> C3 (47 uF class);
U2 VIN -> C4 (0.1 uF); U2 VOUT -> C5 (>= 1 uF, mandatory);
U3 V+ -> C6 (0.1 uF). U3 V- needs no separate cap because it is a hard GND tie,
which `C92494.json` says explicitly. **Every decoupling element any of the three
datasheets names is present.**

**Power-up ordering is benign.** VDD_ADC rises with a 101 us R7*(C2+C8) tail;
VREF needs 7-10 ms to charge 49 uF at the ADR4520's 10 mA. VREF therefore lags
VDD by two orders and the REF pin's clamp diode to VDD never conducts.
(Power-*down* into a host that actively discharges its rail could push the REF
pin above VDD through R7; the remedy is a sequencing element, which the tier
excludes as "sequencing the datasheet does not require", and the realistic
hot-unplug case is benign because the reference's 49 uF then supplies the
board's own ~2.5 mA rather than a short. Recorded, not filed.)

**U2's unused pins are treated correctly.** Pins 1/3/5/7 are true NC and pin 8
is a factory test pin the datasheet marks "Do not connect"; all five are typed
`no_connect` in the symbol and left floating. The librarian note warning that
`lib_pin_types.py` will silently revert those five to `passive` on any re-pull
is a real trap and is correctly attached to the symbol.

**The follower is wired correctly.** Feedback is taken from `U3` OUT (before
R6), not from `/AIN_ADC` - the right choice for a capacitively loaded follower,
keeping R6 out of the loop. No gain-setting network. `C6` sits across V+ and V-.

**The R6 droop is not a hidden error term, and I want to record why**, because
the naive reading books 0.12 mV of unbudgeted gain error. The
`R_eq = 1/(f*C_SH) = 2.08 Mohm` model that justifies the buffer (s8.4) does
**not** apply across R6: the `/AIN_ADC` node fully settles inside the
acquisition window (tau = R6*C7 = 50 ns against 9 us = 180 time constants), so at
the sample instant the only current through R6 is the ADS8326's 50 nA max input
leakage, i.e. 2.5 uV. The average-current divider is real only when settling is
incomplete - which is exactly the condition the `acquisition-settling` bench
exists to disprove.

**The one ground offset the Kelvin scheme does NOT cancel** is between J1 pin 2
(the source's return entry) and R5's bottom pad: that one arrives at the
terminal at *unity*, not divided out. I sized it - the board's ~2.5 mA of
quiescent return spreading through a solid B.Cu pour develops well under 1 uV
across that span, against a 78 uV terminal LSB - so it is not a finding. It is
the reason the J1->U3 corridor's "and its return" clause has to actually hold at
P7.

**TI's +IN/-IN impedance-matching advice is not followed, and that is fine
here.** `+IN` sits behind R6 with C7 to ground; `-IN` is bare copper. I checked
whether the asymmetry converts common mode to differential: it does not matter
at DC or at the sample instant (both legs settle inside 9 us, and the
common-mode term being rejected - the ground offset - is near-DC where
impedance matching is irrelevant), and at HF `-IN` is the *lower*-impedance leg
because it terminates on the pour, so it is the less coupling-sensitive of the
two. The board's protection effort is correctly aimed at `+IN`, `/AIN_DIV` and
`VREF`. TI's optional ~20 pF matching cap would buy little.

**Nothing on this board is polarised.** No diodes, no LEDs, no tantalums, no
electrolytics - all ceramics and film resistors. The polarity hunt is a clean
no-op and is recorded as such rather than skipped.

**J2 pinout** (1=+3V3, 2=GND, 3=/CS, 4=/SCLK, 5=/DOUT, 6=GND) matches
`sheets.md` and places a return reference at both ends of the digital group.
Read-only 3-wire SPI with no MOSI is correct for the ADS8326.

**Net names** export exactly as `sheets.md` s2 specifies (`+3V3`, `VDD_ADC`,
`GND`, `VREF` bare; the rest with one leading slash), which is why
`netlist_audit`'s constraint matching passes. One fragility worth knowing: the
sheet defines `GND` with a single `power:GND` symbol plus **16 local labels
literally named `GND`**. The power symbol wins, so the export is bare and
correct today - but this is the mixing LEARNINGS 2026-07-28 warns against, and
if `#PWR01` were ever removed the net would export as `/GND` and every
`constraints.json` `GND` entry would silently no-op. Since `#PWR01` is also the
Kelvin tie point, E1's remedy and this fragility are the same piece of work.

---

## Open - what I could not verify

- **C5 and C3 DC-bias derating** is estimated from class behaviour; neither
  vendor's bias curve is in the workspace. The 1-100 uF window conclusion is
  robust to +/-2x on those estimates, but the exact effective capacitance - and
  therefore the exact turn-on time in W3 - is unverified.
- **The ADR4520's start-up / short-circuit current limit** is not in
  `C579305.json` (only "output current capacity +10 mA / -8 mA"), so W3's
  7-10 ms is a bound based on the source rating, not the actual inrush.
- **The `zero-scale-swing` question** (OPA320's output floor at 0 V input, TI's
  "loses codes near ground" warning on this exact amplifier/converter pair) is a
  live P8 bench with a recorded P3 analysis that scales the 20 mV spec by the
  real ~1 uA load to ~153 uV at the terminal. I did not re-derive it and file
  nothing against it; note only that the scaling is an extrapolation from a
  10 kohm-load spec, which is why it is a bench and not a calculation.
- **`constraints.json`'s VREF `_why` cites "7 uA max at 10 kSa/s"**;
  `C544731.json`'s tabulated row is 14 uA max at 10 kHz (at VREF = 5 V), and the
  real rate is 22.7 kSa/s at the architected 500 kHz DCLOCK. Every derived
  allowance still passes by orders of magnitude (the trace-R budget halves from
  2.2 to 1.1 ohm and any track satisfies it), so nothing moves - flagged only so
  the 7 uA figure is not reused somewhere tighter.
