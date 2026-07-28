# Schematic review: stm32-blinky (adversarial, P4)

Reviewer stance: hostile senior EE, fresh context. Inputs: reports/schematic.pdf
(rendered this session), reports/top.net (exported this session), parts/C8734.json,
parts/C6186.json, parts/parts.json, architecture/, requirements.md,
kicad/decoupling.json, reports/gate-erc.json. reference/checklists/ is empty
(known gap); the hunt list was applied in full instead.

Verdict: connectivity is correct and complete; the board will most likely blink.
The one credible bring-up killer is the LDO output-capacitor stability
configuration (finding 1). 1 error / 3 warnings.

## Findings

### 1. ERROR - AMS1117 output cap (C5) is outside the only stability
configuration the datasheet gives
- Board: C5 = 10uF 25V X5R ceramic 0805 on +3V3 (kicad/decoupling.json, netlist).
- Ground truth (parts/C6186.json, decoupling): "Required for stability: the
  output capacitor is part of the device frequency compensation. 22uF solid
  tantalum on the output ensures stability for ALL operating conditions...
  No numeric ESR window is given - the stated stable case is specifically
  22uF solid tantalum." Ripple-rejection specs are also conditioned on
  COUT=22uF tantalum.
- Deviation is two-axis: a 10uF X5R 0805 at 3.3V DC bias delivers roughly
  6-8uF effective (vs 22uF), and ceramic ESR is ~3-10 mOhm vs solid tantalum's
  ~0.5-3 ohm. The 1117 family is documented ESR-sensitive (TI's LM1117
  datasheet bounds output-cap ESR to 0.3-22 ohm; near-zero ESR is outside the
  compensation design). The datasheet clause allowing "smaller capacitors...
  with equally good results" covers value only, still in the tantalum context;
  nothing blesses low-ESR ceramic.
- Why it kills bring-up: an unstable loop oscillates the board's ONLY rail
  (typically tens-to-hundreds of kHz, hundreds of mVpp). Symptoms are erratic
  resets, flash/SWD flakiness, and "software" bugs that are not - the classic
  unfindable bring-up failure. Many hobby boards get away with it; that is
  lot-luck, not design margin, and this pipeline's schematic has never been
  powered on.
- Cheap deterministic fixes exist (any one): 22uF tantalum for C5; or keep the
  ceramic and add ~0.3-1 ohm series R; or a second-source LDO specified stable
  with ceramics. Flagged as error so the decision is made consciously, not
  inherited silently from the golden.

### 2. WARNING - VDDA decoupling is 100nF vs the datasheet's 1uF//10nF
- Board: C4 = 100nF at VDDA pin 9 (decoupling.json). Ground truth
  (parts/C8734.json): VDDA requires "1 uF // 10 nF", 10nF as close as possible
  to the chip (DS5319 Figure 40 / 5.3.18) - stated unconditionally, not
  ADC-only. VDDA also feeds the PLL and HSI, which this board uses to run at
  72 MHz.
- power_tree.md records the cut as deliberate (no analog use, golden-proven).
  A blinky will boot and blink with degraded VDDA filtering, so this is not an
  error; it is eroded clock-jitter margin and a documented-requirement
  deviation that must be revisited the moment any spin touches the ADC.

### 3. WARNING - No 4.7uF bulk at VDD_3 despite a datasheet "must"
- Ground truth (parts/C8734.json, pin 48 and 5.1.6 caution): "the 4.7 uF
  capacitor must be connected to VDD3". Board has no bulk at U1 at all; the
  10uF C5 lives at the LDO output and is claimed to double as bulk.
- On a ~35mm board the extra trace inductance is small and this will work; it
  is still a flat deviation from a "must" in the reference design, and the
  substitute cap is the same one already flagged undersized/derated in
  finding 1. Add a local 4.7-10uF at pin 48 on any respin.

### 4. WARNING - The green ERC is largely vacuous: symbol pin types are wrong
- In the exported netlist, U1's NRST, BOOT0, OSC_IN/OSC_OUT and every GPIO are
  typed "passive" (ground truth: bidirectional/input/output), as are both
  headers, D1, D2 and Y1. Only VDD/VSS pins carry power types.
- Consequence: ERC 0/0 (reports/gate-erc.json) could not have detected
  output-to-output conflicts, driven-input floats, or a signal shorted to a
  rail - the checks the gate exists for. Connectivity was re-verified manually
  in this review (it is correct), but the library defect leaves later boards
  built on these symbols unguarded. Fix belongs in the aiee symbol generator,
  not this schematic.

## Judged items (assignment call-outs) - PASS with numbers

- VBAT tied directly to +3V3: PASS. No battery; operating VBAT range
  1.8-3.6V; the C8734.json ground truth lists no VBAT decoupling requirement;
  tie-to-VDD is the standard no-battery configuration. VBAT (pin 1) sits next
  to VDD_3 (pin 48) where C1 lands.
- Crystal load caps 22pF vs CL=20pF (C12674) : PASS. CL_eff = 22/2 + ~10pF
  board+pin stray (DS5319's own estimate) = ~21pF vs 20pF spec - essentially
  on-load. Caps are inside the DS 5-25pF window. Even a pessimistic 4pF stray
  (CL_eff ~15pF) only pulls frequency a few tens of ppm fast - irrelevant, no
  USB/RTC. Startup margin: gmcrit = 4*ESR*(2*pi*8MHz)^2*(C0+CL)^2 ~= 0.74mA/V
  at a conservative ESR=100R, C0=7pF, vs F103 HSE gm of 25mA/V -> ~34x, far
  above AN2867's 5x threshold. (Actual crystal ESR unverified - see OPEN.)
- NRST = 100nF only: PASS - exactly the DS-recommended network (permanent
  internal 30-50k pull-up + 0.1uF to ground).
- PC13 LED drive: PASS. Sink-only topology (+3V3 -> R1 1k -> D2 anode ->
  cathode -> PC13); I = (3.3-Vf)/1k = 0.7-1.7mA < 3mA PC13 limit; honors the
  "must not source" note. Worst-case (Vf=2.6V) the LED is dim but visible for
  a 195mcd part.
- D1 SS34 orientation: PASS. J1.1 -> anode, cathode -> +5V; forward path in
  normal use, and in the reversed-plug case every possible loop crosses D1
  reverse-biased (worst residual is sub-mA leakage) - the board survives.
- U2 pinout: PASS. GND=1, VOUT=2, VIN=3, tab(4)=VOUT - matches the C6186
  pinout including the "tab is output, never GND" trap.
- SWD header order: PASS. J2 1=SWDIO, 2=SWCLK, 3=+3V3, 4=GND - matches the
  requirements listing verbatim.

## Settled decisions (user-approved P0) - noted, not re-litigated

No reset button, no BOOT0 jumper, no power LED, no mounting holes, 4-pin SWD
without NRST. One operational consequence recorded: with no NRST at the header,
connect-under-reset is unavailable; first flash must attach to a powered,
running chip. A blinky never disables SWD or deep-sleeps, so this is safe for
the briefed use; any future firmware that remaps PA13/PA14 or stops the core
can brick-until-boot0-bodge.

## Residual risks accepted elsewhere (prose only, no violation)

- LDO headroom at the assumed 4.5V low-line corner rests on an extrapolated
  dropout guess (DS specifies 1.1V typ/1.3V max only at 0.8A). If real dropout
  at ~55mA is ~0.9-1.0V, the rail can sag below 3.3V at 4.5V input - the MCU
  (2.0-3.6V) still runs, LED dims; benign for this board, already recorded in
  power_tree.md.
- No ESD parts on SWD/5V input: bench prototype per requirements section 4;
  accepted practice at this class.

## OPEN (could not verify)

- reference/checklists/ is empty (known session gap) - per-domain checklists
  could not be applied; hunt list used instead.
- No datasheet JSON exists for Y1 (C12674), D1 (C8678), D2 (C84256) or the
  passives - crystal ESR/C0/drive-level and LED exact Vf reviewed from LCSC
  attributes and conservative assumptions only.
- Footprint pad-1-to-cathode mapping for the two polarized 2-pin parts (D1,
  D2) is not covered by any fp_verify report (only C6186/C8734/headers have
  them). Schematic polarity is correct; the physical orientation check moves
  to layout review.
- netlist_audit output was not found as a file in reports/ (assignment states
  it ran green; gate-erc.json pass 0/0 is present). Connectivity was
  independently re-verified by hand from top.net in this review.
