# LUM-PAR-A schematic review - adversarial P4 pass

Reviewer: schematic-reviewer (fresh context). Inputs: `reports/top.net` (146 parts,
72 nets, exported this session), `reports/schematic.pdf` (6 pages, read), the
`parts/<lcsc>.json` extracts, `brief/06-connector-icd.md` (ICD-01 rev A6),
`architecture/p4-wiring-notes.md` (binding), `architecture/constraints.json`,
`reference/checklists/` (connector + power apply; mcu and interface-usb do not).

ERC is clean and `netlist_audit` is clean; nothing below is re-reporting either.
All arithmetic in this report was recomputed from the datasheet extracts, not
taken from `parts.json` role notes.

**Result: 3 errors, 2 warnings.**

---

## E-1 (error) - the COFF shunt-compensation network cannot trip the OFF-timer

`kind: coff-shunt-timer-dead` - all four channels
(U301/U321/U341/U361, R305/R306, R325/R326, R345/R346, R365/R366, C304/C324/C344/C364)

The network is wired exactly as `p4-wiring-notes.md` s2 demands - ROFF1 reaches the
`/LEDn_A` anode net, ROFF2 comes from the driver's own VCC pin 2, COFF sits at pin 1
with a GND return. **The topology is right and the values are wrong.**

ROFF2 = 47 k was sized from TI Equation 9,
`ROFF2 = -tOFF_shunt / (COFF * ln(1 - 1/VCC))`, which models VCC charging COFF
through ROFF2 *alone*. That equation is only valid when ROFF1 >> ROFF2. Here
ROFF1 = 10 k and ROFF2 = 47 k, so when the shunt FET pulls `/LEDn_A` to VSHUNT the
COFF node is a **divider**, not an RC to VCC, and its asymptote is:

```
  Vasym = (VCC/ROFF2 + VSHUNT/ROFF1) / (1/ROFF1 + 1/ROFF2)
  Rth   = ROFF1 || ROFF2 = 8.246 k      tau = Rth * 470 pF = 3.875 us
```

VSHUNT is the SSM3K2615R drop at the 0.320 A peak: 0.122 V at its 380 mOhm typ,
0.186 V at its 580 mOhm max (both at Vgs = 3.3 V, the datasheet's own test point).

| Rds(on) | VSHUNT | VCC 4.8 | VCC 5.0 | VCC 5.2 |
|---|---|---|---|---|
| typ 380 mOhm | 0.122 V | 0.942 V | **0.978 V** | 1.013 V |
| max 580 mOhm | 0.186 V | 0.995 V | 1.030 V | 1.065 V |
| ideal short | 0.000 V | 0.842 V | 0.877 V | 0.912 V |

VOFT is 0.95 / **1.00** / 1.05 V. At the nominal corner (VCC 5.0, Rds(on) typ) the
COFF node asymptotes **below** the threshold and the timer **never trips**. It trips
only where the FET happens to sit at its published maximum Rds(on) *and* VCC sits high,
and even then it takes 10.8-13.7 us against the 4.78-5.15 us Equation-8 target. At
the VSHUNT -> 0 limit it cannot trip at any corner.

Consequence, which is the exact behaviour the network exists to prevent
(TPS92515HV sec 8.3.4, Figure 43): every shunted cycle runs to **tOFF(max) = 230 us**
(the block diagram says 250 us). The inductor fully decays in 24 us, so the converter
sits in deep DCM and free-runs at roughly **4.3 kHz** - against a 4.883 kHz shunt-PWM
carrier. Constant inductor ripple is lost, shunt-dimming linearity is lost, the two
near-equal rates beat, and the inductors sing in-band. `parts.json` calls this network
"the ONLY thing that closes PAR-REQ-01's 141 ns wall"; as valued it does not work.

The **unshunted** state is fine and I confirmed it: asymptote 6.484 V, tOFF 0.649 us,
dIL 93.9 mA - the 90 mA design point, and the 10 k-instead-of-8.2 k re-solve for
ROFF2's parallel loading is correct *for that state*. The same parallel loading was
simply never applied to the shunted state. The `parts.json` back-check that
"shunted-state ripple error across that band is only -4 % / +3 %" and
"at the pathological limits it is -18 % (VSHUNT = 0, ideal short)" is wrong: at
VSHUNT = 0 the timer does not trip at all.

Direction of a fix (not prescribed here): ROFF2 must be small enough that
`VCC * ROFF1 / (ROFF1 + ROFF2)` clears VOFT_max = 1.05 V with margin at VCC_min =
4.8 V and VSHUNT = 0 - and re-solving ROFF2 changes the unshunted ripple, so both
states have to be solved together.

## E-2 (error) - `/NTC_LED` enters three comparator inputs straight off the harness

`kind: ntc-harness-input-unprotected` - U401 pins 4, 7, 11; J5 pin 10

`/NTC_LED` is J5 pin 10 -> R403 divider node -> U401 pins 7 (1IN+), 4 (2IN-) and
11 (4IN+). There is **no series limiting resistor and no clamp** between the
connector pin and the silicon. `R402` (1 k) protects only the `/ADC0` branch, and
the carrier protects its own ADC pin.

The LM339LV extract is explicit: inputs are abs-max **-0.3 to 6 V**, recommended
-0.1 to 5.6 V, **"diode-clamped to GND only - there is no ESD clamp from the inputs
to V+"**, input current abs-max +/-10 mA, and *"if an input is driven from a
low-impedance source, add a series current-limiting resistor"*.

Four LED anodes share the same 10-way JST PH harness. In normal operation they sit
at up to 6.8 V - already over the 6 V abs max on a plain conductor-to-conductor
short - and when a string is open the anode node runs to the SMF15A standoff/clamp
region, **16.7 V to 24.4 V**. So a single crimp error, a pinched conductor, or a
mis-made bring-up harness applies 7-24 V to an unprotected 6 V pin and destroys the
board's only over-temperature protection. The broken harness wire is the fault
`blocks.md` B4 names as "the most likely fault in an off-board module" and is the
reason the window detector exists; the detector does not survive it.

Secondary, same edit: the comparator inputs also have no HF filter. The 100 nF
`C402`/`C403` sit behind the 1 k ADC resistors, so U401 sees the raw divider node
on a metre-class harness running beside four 275 mA switching strings, with only
~3 K of external hysteresis (see W-1) and no internal hysteresis at all.

## E-3 (error) - `/DRV_EN0..3` are undriven whenever +3V3 is absent and +12V is up

`kind: drv-en-undriven-no-3v3` - R214-R217, U201, U301/U321/U341/U361 pin 9

There is no pull-down anywhere on `/DRV_EN0..3`. The nets carry only R214-R217
(0 ohm to `/EN_OK`), the DNP U204 outputs, and the four TPS92515HV PWM pins. With
+3V3 absent:

- U201's Y output is **high-Z by design** - the SN74LVC1G08 abs-max table has the
  partial-power-down entry *"voltage applied to any output in the high-impedance or
  power-off state: -0.5 to 6.5 V"*, i.e. no clamp back into VCC;
- U202's and U204's inputs on `/EN_OK` are 5.5 V-tolerant LVC inputs, so they do not
  clamp either;
- the TPS92515HV PWM pin draws 10 nA below threshold - no pull-down.

The window is not hypothetical. The carrier's D-02 chain is 48 -> 12 -> 3.3, so
**+12V is up before +3V3 on every single power-on**, and a bench bring-up on 12 V
alone makes the condition permanent. Worse, the pin latches: TPS92515HV
`IPWM(uvlo-hys)` is **-15/-20/-25 uA flowing OUT of the pin above the 1.0 V
threshold** (it is the UVLO hysteresis mechanism). On a node with no DC path to
ground, one noise excursion past 1.0 V turns on 4 x 20 uA of pull-up and holds all
four drivers enabled for the rest of the window. Meanwhile U202 is unpowered, so
R303/R323/R343/R363 hold the shunt FETs OFF and the strings get full current.

That is a full-brightness flash of indeterminate length on every power-up, and it
defeats ICD s8.2's binding requirement to *"gate every output stage with ENABLE"* -
the requirement whose stated purpose is to make exactly this class of power-up
glitch a no-op. Every other fail-safe on this board is a pull-down for this reason
(R201 on ENABLE, R202-R205 on PWM0-3, R303/R323/R343/R363 on the shunt gates);
`/DRV_ENn` is the one that was missed.

## W-1 (warning) - comparator hysteresis is returned to the sensor nodes, not the ladder

`kind: hysteresis-on-sensor-node` - R409, R410, R411, R412, U401, RT401

`parts.json` sizes R409-R412 as *"56 k feedback ... against the ~2.6 kOhm ladder
source impedance at that tap"*. The netlist does not do that. R409+R411 (112 k in
series) land on `/NTC_LED` and R412 (56 k) lands on `/thermal/NTC_BRD` - the
**sensor** divider nodes. Only R410 reaches a ladder tap (`/thermal/VREF_OPEN`).
Because those nodes are also pulled up by the idle-high `/FAULT` node, the feedback
shifts the DC operating point as well as adding hysteresis:

| Channel (by pin number) | intended | as wired: trip / release | band |
|---|---|---|---|
| p1, IN+ p7 = NTC_LED, IN- p6 = VREF_EHOT (emitter hot) | 90.0 C | **92.5 / 89.6 C** | 2.96 K |
| p13, IN+ p11 = NTC_LED, IN- p10 = VREF_HOT2 (emitter short) | - | 114.0 / 110.8 C | 3.18 K |
| p14, IN+ p9 = NTC_BRD, IN- p8 = VREF_HOT2 (board hot) | 110.0 / 95.0 C | **117.0 / 110.9 C** | 6.15 K |
| p2, IN+ p5 = VREF_OPEN, IN- p4 = NTC_LED (emitter open) | - | see below | **inverted** |

Three separate effects, none of which the logged H2 hysteresis item covers:

1. **DC threshold shift.** The unloaded ladder gives 89.7 C and 110.8 C, matching the
   design intent. As wired the board-hot trip moves to **117.0 C** - 7 K above the
   limit it is supposed to enforce - and emitter-hot to 92.5 C.
2. **Telemetry bias.** `/ADC0` and `/ADC1` are tapped off the same two nodes through
   R402/R404, so the temperatures the carrier reads are pulled **cold** by ~1.9 K at
   25 C and ~6.6 K at 110 C on `/ADC1`. Firmware's graceful duty roll-back
   (`blocks.md` B4: *"firmware can roll duty back long before FAULT asserts"*) runs on
   those numbers.
3. **Wrong sign on the emitter-open channel.** For that unit the sensor node is IN-,
   so the 112 k path is *negative* feedback and it outweighs R410's positive path.
   Measured: trip requires Rntc > 106.2 k (-20.1 C), release requires Rntc < 191.0 k
   (-29.3 C) - both conditions are satisfied simultaneously between 106 k and 191 k,
   so the detector oscillates anywhere in that window. R411's own schematic note
   (*"in SERIES with R409 on purpose - 56k alone makes the open-harness detector
   chatter"*) treats the symptom: at 56 k the release condition is unreachable at any
   Rntc, i.e. continuous oscillation. 112 k bounds it; it does not fix the sign. The
   affected band sits outside the operating envelope, which is why this is a warning
   and not an error, but the sign is still wrong.

Supporting evidence for the existing R207 100 k -> 10 k proposal, not a separate
finding: with the hysteresis resistors loading it, `/FAULT` idles at **2.402 V**
unmated (against U201's 2.0 V VIH - 0.4 V of margin, less LVC input leakage) and
2.983 V mated. Everything computed above already uses the mated case; unmated, the
hysteresis is a further ~25 % smaller.

## W-2 (warning) - `led_if` carries no ICD s9 bench-hazard note for TP501/TP502

`kind: missing-bench-hazard-note` - TP501, TP502

`sheets.md` s1.5 assigns the ICD s9 bench-hazard silkscreen to TP501/TP502, and
ICD s9 requires it: *"daughters must carry the same warning on any test point."*
The `power` sheet does this properly for TP101-TP103 (with the note that the silk
itself is a P6/P7 `place_edit add_text` op). The `led_if` sheet contains **no text
objects at all** - grep-verified - so the P6/P7 op has no source. TP501/TP502 are
bare-copper 2.0 x 2.0 mm pads tied to a GND that floats at PoE potential, and they
exist specifically to be touched with an instrument at bring-up: an earthed
thermocouple there is the exact case ICD s9 says *"breaks PD signature detection
outright"*.

---

## Verified clean - the ten claims I was asked to be hostile about

1. **COFF network topology** - correct on all four channels. R305/R325/R345/R365 pin 1
   is on `/LEDn_A` (the real anode net, reaching J5), not a local node.
   R306/R326/R346/R366 pin 1 is on `/drivers/VCCn`, which is the driver's own pin 2
   (`power_out`) and nothing else - no external rail, so the internal COFF-to-VCC
   diode cannot start the device with VIN unpowered. C304 is 470 pF C0G at pin 1 with
   pin 2 on GND. **Values are the defect (E-1), not the wiring.**
2. **BOOT network** - correct and complete on all four channels. D302/D322/D342/D362:
   anode on `/drivers/VCCn`, cathode on `/drivers/BOOTn` - VCC -> BOOT, right way
   round. C305/C325/C345/C365 (100 nF, the datasheet's own value) from BOOT to SWn,
   not to GND. C306/C326/C346/C366 (4.7 uF) VCC to GND, satisfying sec 8.3.6's
   ">= 1 uF and >= 10x the BOOT capacitance, max 10 uF". Per-pin coverage complete:
   VIN pin 8 has C301+C302 on the VIN side of RSENSE (Figure 33 topology, LOOP2
   intact), VCC pin 2 has C306, COFF pin 1 has C304, BOOT/SW has C305.
3. **No output capacitor across any LED string** - confirmed absent. `/LED0_A`..
   `/LED3_A` each carry exactly five nodes: D50n cathode, J5, L30n pin 2, Q30n drain,
   R3n5 pin 1. No capacitor on any of them. The DNP snubbers C303/C323/C343/C363 are
   on the SW nodes, not the output.
4. **`/FAULT` open drain** - clean. Ten nodes: J4-24, R207 (100 k pull-up to +3V3),
   the three hysteresis resistors, U201 pin 2 (an *input*), and U401 pins 1, 2, 13, 14
   - all four of which the LM339LV extract confirms are open-drain sinking-only and
   explicitly wire-OR-able. Nothing can drive the net high. Sink capability against
   ICD rev A6's >= 5 mA: the real load is 341 uA of pull-up plus the carrier's ~4 mA
   indicator; LM339LV VOL is 200 mV max at 4 mA (300 mV over temperature) with
   60 mA typ / 100 mA max sink per output. Comfortable.
5. **U401 four-unit grouping** - all four units present and all four wired by the
   corrected pin-number groupings, verified against the datasheet extract rather than
   the transposed labels: out p1 <-> in p6/p7, out p2 <-> in p4/p5, out p13 <-> in
   p10/p11, out p14 <-> in p8/p9. Functional polarity is right too: emitter-hot and
   emitter-short take NTC_LED on IN+, emitter-open takes it on IN-, board-hot takes
   NTC_BRD on IN+ - each asserting low into `/FAULT` on its own fault. (Cosmetic note,
   no action: the symbol names pins 1/2 per Table 5.2 but pins 13/14 per Figure 5-3.
   The pin *groupings* are correct in both, and KiCad units bind them, so it cannot be
   mis-wired - but it reads inconsistently.)
6. **U202 SN74LVC00A** - wired from the package diagram, not the shifted Pin Functions
   table. 1A/1B/1Y = 1/2/3, 2A/2B/2Y = 4/5/6, GND = 7, 3Y/3A/3B = 8/9/10,
   4Y/4A/4B = 11/12/13, VCC = 14. Exactly right. `/SHUNTn = NOT(PWMn AND /EN_OK)`
   as specified.
7. **U203 M24C32** - E0/E1/E2 (pins 1/2/3) tied to VSS through R208 (0 ohm) -> 0x50.
   WC (pin 7) held at VSS through R209 (10 k), so the active-HIGH write protect is
   de-asserted and the part is writable. VCC pin 8 on +3V3 (part is the -W, 2.5-5.5 V
   grade), VSS pin 4 on GND, SDA/SCL on J4-19/J4-18.
8. **No I2C pull-ups** - confirmed. `/control/I2C_SCL` has exactly two nodes
   (J4-18, U203-6) and `/control/I2C_SDA` exactly two (J4-19, U203-5). No resistor
   anywhere on either. ICD s3.3 respected, and the control sheet records the decision
   in text.
9. **Abs-max sweep** - every IC clears its applied rail:
   - TPS92515HV: VIN 12 V vs 65 V; PWM pin driven from 3.3 V logic vs the 5.5 V
     abs max (nothing 12 V-referenced touches it); IADJ tied to VCC (~5 V) vs 5.5 V
     abs max - this is TI Figure 17, a bare wire to VCC using the internal 2.4 V
     clamp, and sec 8.3.7.4 calls it "the most accurate stand-alone implementation",
     so it is correct, not an output-shorted-to-a-rail defect; BOOT-SW 5 V vs 5.5 V.
     VIN-to-CSN differential worst case (VCST max 251 mV + the tDEL 130 ns overshoot
     with the string shunted) is **276 mV against the 300 mV abs max** - in spec, but
     that is only 8 % of margin on the board's most-repeated circuit and it is worth
     knowing.
   - SN74LVC00A VCC = +3V3, inside 1.65-3.6 V; nothing above 3.3 V reaches its inputs.
     SN74LVC1G08 (1.65-5.5 V) and SN74LVC14A (1.65-3.6 V) likewise.
   - M24C32-W 2.5-5.5 V at 3.3 V; LM339LV 1.65-5.5 V at 3.3 V.
   - SSM3K2615R: 60 V Vds against a ~7 V string, Vgs 3.3 V against +/-20 V, and its
     Rds(on) is specified *at* 3.3 V drive. D301 DFLS160 60 V / 1 A against 12 V and
     0.275 A. D302 1N4148W 75 V against 12 V reverse. SMF15A 15 V standoff above the
     12 V an open-circuit CC buck drives toward.
   - Every capacitor's voltage rating clears its net, including the ICD s5.4 rules on
     the 48 V domain (C106/C107/C108 all 100 V, R101/R102/R103/R104 all 0805).
10. **DNP option sets** - all three are in the netlist with pads and none is reported
    as an unpopulated defect. Their wiring is correct: the branch-B front end
    (Q101 S on +48V_SW, D on the V48_B bulk, gate held off by R101 to source and
    pulled down through R102 by Q102 from `/EN_OK`, C108 as the gate-drain dV/dt
    element) is coherent; the converter-idle one-shot's diodes D201-D204 are cathode
    on `/SHUNTn` and anode on `/control/IDLEn`, which is the correct fast-reset
    orientation, and R21n/C21n give ~0.79 ms to the LVC14A threshold - shorter than
    the shortest possible shunt-high interval at any usable duty, so it retriggers
    correctly. The snubbers are SW -> C -> R -> GND. No fitted part depends on a DNP
    part: `/DRV_ENn` reaches U301 through the fitted R214-R217, and the control sheet
    carries the "if it is ever populated, remove R214-R217" instruction.

## Also checked, also clean

- **J3 pinout against ICD s3.1**, pin by pin: `+48V_SW` on 1/3/5, `+12V` on 9/11,
  `+3V3` on 12/14, GND on 2/4/6/7/8/10/13. All 14 positions accounted for, exact match.
- **J4 pinout against ICD s3.2**, pin by pin: PWM0-3 on 1/2/5/6, GND on 3/4/9/10/13,
  I2C_SCL/SDA on 18/19, ADC0/ADC1 on 20/21, ID_ADC on 22, ENABLE on 23, FAULT on 24;
  PWM4-7 (7/8/11/12) and DSPI (14-17) deliberately open. Exact match. No deviation
  from ICD-01 anywhere.
- **R206 = 4.7 k 1 %** -> ICD s3.4 code 2, V_ID = 1.055 V. Correct code, and the
  bottom leg is to GND as the ICD requires.
- **R201 = 100 k ENABLE pull-down directly across J4-23**, no series element in
  front of it (ICD s8.2).
- **J5 harness map**: 4 anodes on odd pins 1/3/5/7, per-channel returns on 2/4/6/8,
  dedicated NTC sense return on 9, `/NTC_LED` on 10 - matches `sheets.md` s1.5.
- **Every diode polarity**: catch diodes cathode-to-SW, BOOT diodes anode-to-VCC, TVS
  cathode-to-anode-net, one-shot diodes cathode-to-SHUNT. All four classes correct.
- **No 48 V net reaches `led_if`** (D-T13 holds); no electrolytics anywhere on the board.
- **No floating IC inputs**: every pin of U201, U202, U203, U301/321/341/361 and U401
  reaches a net; U204's only unconnected pins are its two unused *outputs* (5Y, 6Y)
  and its two unused inputs 5A/6A are tied to GND. The twelve `pin_no_net` entries
  `netlist_audit` reports are J4's deliberate ICD no-connects, J5's two mechanical
  solder tabs, and those two U204 outputs.
- **ADC source impedance**: 1 k + (10 k || Rntc) <= 6 k at 25 C, against ICD s3.3's
  10 k ceiling. The 112 k / 56 k hysteresis paths change this by under 5 %.
- **Ladder current** 101.5 uA, matching `power_tree` s4's 0.10 mA allowance.
- The `+12V` 8.5 W-total question, the CAR-REQ-17 bleed exemption on branch A, and the
  R207 100 k value are all analysed and recorded in `power_tree.md` s3.3 / `blocks.md`
  s153 / the H2 agenda. Not re-litigated here.
