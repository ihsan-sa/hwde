# bb-amp - P4 schematic review (adversarial, fresh context)

Mode `learning block-basics:` -> scope `block-only`, binding `canonical`.
Reviewed against the exported netlist (`kicad/bb-amp.net`), the rendered sheet
(`reports/schematic.pdf`), the datasheet extracts (`parts/C34250.json`,
`parts/C38732.json`), `reference/checklists/connector.md` and
`reference/checklists/power.md`. Scope exclusions (protection, ESD,
non-required filtering, indicators, config, second rail, mechanical) are not
reported and were not looked for.

**Verdict: nothing is electrically wrong with this board. 0 errors, 5 warnings**
- three documentation/analysis gaps, one library-metadata trap, one unstated
consequence. None blocks bring-up.

---

## The six load-bearing claims - all verified, in the netlist, not the drawing

| # | claim | netlist evidence | verdict |
|---|---|---|---|
| 1 | R5 returns to /VREF, not GND | net `/VREF` = {R5.2, U1.6, U2.1, U2.2}; R5.1 is on `/FB2` | **holds** |
| 2 | U1 REF driven by U2A, never grounded; U2A is a unity buffer | U1.6 (REF) on `/VREF`; U2.1 (OUTA) tied to U2.2 (INA-) on the same net; U2.3 (INA+) on `/VREF_SET` | **holds** |
| 3 | both OPA2333 units used, supply pins present | unit A = pins 1,2,3 + 4,8; unit B = pins 5,6,7; U2.8 -> `+3V3`, U2.4 -> `GND`; all 8 pins of U1 and all 8 of U2 wired, no NC anywhere | **holds** |
| 4 | single-supply headroom at Vdiff = -1 mV | see arithmetic below | **holds, ~100 mV margin at the worst rail** |
| 5 | the gain values | see arithmetic below | **holds, 139.24** |
| 6 | R6 removal left no orphan | zero hits for `R6`/`C22775` in `.kicad_sch`, `.net` and `parts.json`; `/VOUT` = {U2.7, R4.1, J2.1}, one node | **holds** |

**Item 4, recomputed against `parts/C34250.json` rather than blocks.md.**
The AD8226's guaranteed floor is `output_swing_min_RL10k_neg40to125C = 0.1 V`.
Stage-1 output at Vdiff = -1 mV is `Vref - G1*1 mV = Vref - 0.0399 V`, and
Vref tracks the rail at `Vs*10.0k/131.0k`:

```
Vs = 3.300 V ->  0.2519 - 0.0399 = 0.2120 V   vs 0.10 V floor   (+112 mV)
Vs = 3.135 V ->  0.2393 - 0.0399 = 0.1994 V   vs 0.10 V floor   ( +99 mV)
```

B1 measured `amp1_m1m = 0.212327` at the nominal rail - agrees. The pedestal
falling with the rail is what preserves the margin at -5 %, and it is also the
subject of W1 below.

**Item 5, recomputed from the netlist's own values.**

```
G1 = 1 + 49.4k/R1 = 1 + 49.4k/1.27k = 39.898
G2 = 1 + R4/R5    = 1 + 24.9k/10.0k = 3.490
G1*G2 = 139.24     (B1 measured slope 139.235; sheet says 139.2)
Vped  = 3.3 * 10.0k/131.0k = 0.2519 V
Vout  = 0.2519 + 139.24*Vdiff   ->  -1 mV: 0.1127 V,  +20 mV: 3.0367 V
```

Matches requirements 9a's `Vout = Vped + G*Vin_diff` in form. Vped is 0.252 V
where Q6 sketched "about 0.1 V" - that is **not drift**: a 0.1 V pedestal puts
stage 1 at 0.060 V at -1 mV, below the AD8226's own 0.10 V floor, so Vped >=
0.14 V is forced by the part. The deviation is recorded in blocks.md s7 with
that reason.

## What else I attacked and found clean

- **Every net, all 11**, walked pin by pin against the intended topology. No
  correct-but-wrong connection.
- **Sense of both feedback loops.** U2A: OUTA on INA-, divider on INA+ - a
  follower, not a latch. U2B: signal on INB+ (5), divider tap on INB- (6),
  R4 from OUTB - non-inverting, negative feedback. Swapping either pair would
  latch and ERC would not care. Neither is swapped.
- **Input polarity.** J1.1 (IN+) -> U1.4 (+IN), J1.2 (IN-) -> U1.1 (-IN);
  positive Vdiff gives positive output, per requirements s2's convention.
- **Divider orientation.** R2 121k on the +3V3 side, R3 10.0k on the GND side.
  Reversed, Vref would be 3.05 V. It is not reversed.
- **R4/R5 not transposed.** 24.9k is the feedback leg, 10.0k the return leg;
  transposed, G2 would be 1.40.
- **Decoupling per pin, against the datasheet JSONs.** C1 100 n at U1.8; C2
  10 uF shared bulk (AD8226 Fig.61's "farther away ... can be shared"); C3
  100 n across U2 pins 8-4. U1 pin 5 (-VS) takes no cap because on a single
  supply it *is* the return - the AD8226 extract says so explicitly. C4 is on
  `/VREF_SET`, the divider node, **not** on U2A's output; the follower-into-a-
  cap trap was deliberately avoided and is called out in the part's own Note.
- **Abs-max on every IC.** AD8226 2.2-36 V single supply, REF within +-VS,
  inputs inside `+VS - 0.7 V` at Vcm <= 1.73 V. OPA2333 abs-max 7 V, inputs
  -0.3 to V+ +0.3, applied 0.21-1.25 V. C2 25 V / C1,C3,C4 50 V on 3.3 V.
  Nothing is close to a limit.
- **Output drive.** U2B sources ~110 uA (79.8 uA into R4 + 30 uA load), U2A
  ~87 uA (79.8 uA into R5 + ~7 uA into the AD8226 REF pin) against the
  OPA2333's +-5 mA. B7 measured both.
- **The hidden loop /VREF -> U1 REF -> U1 out -> U2B -> R4 -> R5 -> /VREF.**
  A perturbation on Vref moves `/FB2` and `/VREF` by the same amount, so no net
  current returns through R5 - loop gain ~0 at DC. At 41 kHz, U2A's Zout of
  116 ohm against R5's 10k caps the residual at ~0.012. No instability path.
- **BOM/netlist agreement.** 10 distinct parts / 14 refdes, LCSC codes matching
  the per-component fields the P9 export reads. No stale line.

## Findings

### W1 (warning) - the error budget omits the term the rail feeds into the pedestal

`kind: pedestal-rail-sensitivity`  refs R2, R3, U2  net /VREF

The design's best property is that the output pedestal is *exactly* Vref at
gain 1. The cost of that, which nothing writes down, is that the rail reaches
the output zero at gain 1 too:

```
Vped = Vs * R3/(R2+R3) = 0.076336*Vs      dVout/dVs = 0.0763 V/V  (22.3 dB)
B6 measured: dvr_dvs = 0.0763352, v0_lo = 0.2404 V, v0_hi = 0.2659 V
  -> 25.4 mV of output-zero movement across Q10's +-5 % rail = 182 uV RTI p-p
```

blocks.md Ruling 3's table counts `pedestal drift (R2/R3 TCR mismatch
25 ppm/degC) = 1.1 uV typ / 2.3 uV max`. That is the drift of the *ratio*; the
rail the ratio multiplies is not in the table at all, and it is 40-80x larger
than the term that is. Inverting it:

```
rail movement after calibration -> RTI error:  dVs * 0.0763 / 139.24
   9.1 mV (0.28 %)  ->  5.0 uV   = the entire Q7 budget, on its own
  25.4 mV (0.77 %)  -> 13.9 uV   = the whole recorded typical error
```

Q7 calibrates zero downstream, so the *static* pedestal cancels and the board
is not wrong. What is missing is the flow-down: the accuracy this board claims
silently requires a post-calibration rail stability that Q10 never states (it
gives +-5 % as a tolerance, not a drift). On a board whose stated purpose is to
teach, and whose accuracy miss is otherwise carefully quantified, this is the
one term the analysis skips.

Not an error: fixing it with a voltage reference would add an IC the block does
not need to work, which `block-only` excludes. The fix is a line in the budget
and a stated rail-stability requirement.

*Waiver reason if accepted:* the static pedestal calibrates out per Q7; record
the required post-calibration rail stability (~9 mV for 5 uV RTI) as a bench
condition rather than adding a reference IC.

### W2 (warning) - the sheet's "< 2 ohm at U1 REF" is unqualified; the board's own bench says it is band-limited

`kind: ref-zout-band-overclaim`  refs U2, U1  net /VREF

Row note on the plotted sheet: *"PEDESTAL R2/R3 off +3V3 = 0.2519 V, C4 on the
DIVIDER node, U2A buffers it to < 2 ohm at U1 REF"*. B9 measured otherwise:

```
z1_dc  0.43 mohm   z1_60max 0.17 ohm   z1_1k 2.86 ohm   z1_f2ohm  700 Hz
z2_dc  0.85 mohm   z2_60max 0.34 ohm   z2_1k 5.71 ohm   z2_f2ohm  350 Hz
```

so the rule is met from DC to ~350-700 Hz and missed over the top half of the
DC-to-1 kHz band this board is specified for. B9's own bounds file already
carries this as a `warning` with the right argument (the AD8226's 2 ohm sits in
its DC-60 Hz CMRR context; this board's common mode is a static 1.65 V). That
argument is sound - the **board** is fine. The **sheet** is not: it states the
conclusion without the condition, and the condition is the lesson. A reader
takes away "a follower gets you under 2 ohm", when the transferable fact is
"a follower gets you under 2 ohm until ro*f/GBW catches up, here at a few
hundred hertz".

*Waiver reason if accepted:* electrically correct in the band where the AD8226
specifies CMRR; sheet wording only.

### W3 (warning) - the equations box states Eq.2 under the wrong corner

`kind: sheet-eq2-condition`  refs U1

Sheet: *"At Vcm = 1.65 V and the -5 % rail, Eq.2 allows |G*Vdiff| <= 1.33 V,
i.e. G <= 66 at 20 mV FS."* Recomputed from Table 8 in `parts/C34250.json`
(V+LIMIT interpolated to 0.7385 V at 0 degC, between the -40 degC 0.80 V and
the +25 degC 0.70 V rows):

```
Vcm = 1.6500, Vs = 3.135:  2*(3.135 - 0.7385 - 1.6500) = 1.493 V  -> G <= 75
Vcm = 1.7325, Vs = 3.135:  2*(3.135 - 0.7385 - 1.7325) = 1.328 V  -> G <= 66
```

blocks.md's Ruling 2 table has both rows and labels them correctly; the sheet
took the number from the second row and the condition from the first. The
+5 % excitation that puts Vcm at 1.7325 V is never mentioned on the sheet.
The conclusion (split the gain) is unaffected - 139 fails either bound - but a
student who recomputes the stated condition gets 1.49 V and concludes the sheet
is wrong.

*Waiver reason if accepted:* none recommended; this is a one-line text fix in
`kicad/gen/root.py`'s EQUATIONS string and it is cheap.

### W4 (warning) - KF128-5.08-2P carries reference prefix "U", its 3P sibling carries "J"

`kind: connector-refdes-prefix`  refs J2, J3

From `lib/aiee.kicad_sym`:

```
KF128-5.08-3P  -> J        (correct)
KF128-5.08-2P  -> U        (wrong - same connector family, J1 vs J2/J3)
```

Harmless on a normal rebuild, because `root.py` sets `"J2"` and `"J3"`
explicitly. It becomes a trap the moment anyone runs KiCad's annotate with
"reset existing annotation": J2/J3 move into the U series and take with them
`constraints.json` `placement.edges` (which names J2/J3 by refdes),
`parts.json` refs, and P9's ref->LCSC map. ERC and netlist_audit are both blind
to a reference *prefix*.

*Waiver reason if accepted:* the generator assigns refdes explicitly, so no
current flow re-annotates; fix is one string in the workspace symbol library.

### W5 (warning) - the reverse-plug consequence at J3 is stated nowhere

`kind: reverse-plug-not-flagged`  refs J3  net +3V3

`reference/checklists/connector.md` requires: *"Power pins: polarity legend on
silk visible AFTER assembly; reverse-plug consequence stated (protected or
destructive - if destructive, flag)."* The legend is planned (requirements s2
silkscreens +3V3 / GND per pole). The consequence is not stated in J3's Note
field, in requirements, or in blocks.md: reversing the two screws on a
hand-wired 2-pole terminal applies -3.3 V across both ICs and forward-biases
their substrate diodes with no series element anywhere to limit the current.

**This is not a request for a protection part.** Reverse-polarity protection is
excluded at `block-only` and must stay out. The unmet item is the flag itself -
a silk marking or a line in J3's Note.

*Waiver reason if accepted:* per-pole silk legend already specified in
requirements s2 gives the user what they need to wire it correctly.

## On the recorded accuracy miss - asked to judge, not to re-report

The acceptance is **honestly argued**, and I checked its arithmetic rather than
taking it:

- `RTI drift = VOSI_TC + VOSO_TC/G1` is the datasheet's own equation, and the
  numbers are the A-grade rows of `parts/C34250.json` (`vosi_tc` 0.5/2,
  `voso_tc` 2/10): 0.550 uV/degC typ, 2.251 uV/degC max -> 13.8 / 56.3 uV over
  a +-25 degC excursion. Correct.
- Gain drift: `gain_vs_temp_Ggt1 = -100 ppm/degC` max plus 25 ppm RG plus
  50 ppm R4/R5 mismatch, x 25 degC x 20 mV = 87 uV. Correct.
- The reframe - "5 uV RTI on 20 mV FS over 25 degC **is** 10 ppm of full scale
  per degC, a laboratory TC target, not a 12-bit one" - is arithmetically right
  and is the most useful sentence in Ruling 3. It corrects the scout's
  overstated drift spec rather than hiding behind it, and it says plainly that
  option (b) buys 2.5x on one term while another stays 7x over.

One criticism, and it is W1: the budget grades offset drift, gain drift, CMRR
and noise, and never names the rail term feeding the pedestal - which needs
only 0.28 % of post-calibration rail movement to equal the entire budget. The
reasoning is not wrong; it is incomplete in the one place the topology's own
elegance created the exposure.

## On the R6 removal - asked to check for orphans

Clean, and unusually well closed out. Zero textual references to `R6` or
`C22775` in the schematic, the netlist or the BOM. `/VOUT` is a single node
{U2.7, R4.1, J2.1}, back on `sheets.md`'s own net table with no delta. Label
counts on the sheet reconcile exactly to the netlist's pin counts on all 11
nets. The only residue is an unused `0603WAF1000T5E` symbol in
`lib/aiee.kicad_sym`, which `root.py` s5 names as known history rather than
design - not a defect, and removing it would be churn.

The removal reasoning also holds up independently: a unity-gain overshoot curve
does not transfer to a noise-gain-3.49 stage, an out-of-loop isolation resistor
has authority `R6/ro` so 100 R against ro = 1-2k buys 0.3-1.3 points (B11:
6.60 -> 6.28 % calibrated), and the 470 R that would actually isolate would
have pushed the -5 %-rail full scale under B6's own 3.02 V floor. Correct call.

## Machine gates (context, not re-run for bugs)

`reports/gate-erc.json` 0/0 pass; `reports/sim.json` 11 benches pass. I did not
re-run them looking for the defect - the findings above are the classes those
gates are structurally blind to: a term missing from a written budget, a claim
on a plotted sheet, a condition attached to the wrong corner, and a reference
prefix in a symbol library.
