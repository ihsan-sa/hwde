# P4 schematic review - sbuck-5v3a (adversarial, fresh context)

Reviewer: `schematic-reviewer`. Inputs read: `kicad/sbuck-5v3a.kicad_sch`,
`kicad/sbuck-5v3a.net` (exported netlist, 15 nets / 44 components / 86 pins),
`kicad/gen/root.py`, `reports/sbuck-5v3a-schematic.pdf`, `parts/C2071691.json`
and the AP64350 PDF itself (**pp.10-12 and pp.18-21 read directly, not via the
extract**), `parts/C16072.json`, `parts/parts.json`, `architecture/*`,
`lib/aiee.kicad_sym`, `lib/aiee.pretty/*`, `lib/EDITS.md`,
`reference/checklists/power.md`, `reports/erc-p4.json`,
`reports/netlist_audit-p4.json`.

**Verdict: 0 errors, 7 warnings.** Nothing in this schematic prevents bring-up,
damages hardware, or contradicts a datasheet. Every one of the nine claims the
assignment put up for challenge was checked with independent arithmetic; eight
verified outright and one (the loop-model *calibration*, not the loop *values*)
did not reproduce.

---

## 1. Compensation - RE-DERIVED INDEPENDENTLY (claim 1)

I built my own model from the datasheet constants only (`gm = 0.15 mS`,
`Ri = RT(sense) = 0.089 V/A`, `VFB = 0.8 V`, `fsw = 500 kHz`, all from
`parts/C2071691.json` pin 6 / DS41976 p.18): PCMC single-order plant
`Zout(s)/Ri`, Ridley sampling term, gm Type-II compensator, resistive divider.
I did **not** read the author's numbers before running it.

First, the closed-form check. Eq.17 rearranged for fc gives
`fc = R5 / (4659.9 * VOUT * COUT)`:

| COUT | fc from Eq.17 alone | fc from my model |
|---|---|---|
| 75.0 uF | 42.9 kHz | 42.23 kHz |
| 85.2 uF | 37.8 kHz | 37.28 kHz |
| 96.8 uF | 33.3 kHz | 32.88 kHz |

(The constant checks out: `2*pi*0.089/(0.15e-3*0.8) = 4659.9`, which is the
datasheet's own `4.67e3`.)

My model, R5 = 75 k / C2 = 3.3 nF / C3 = 10 pF COMP-to-GND, R6/R7 = 105k/20.0k,
swept over IOUT 0.3-3.0 A:

| COUT | fc | phase margin | \|T\| at fsw/2 | GM at the -180 deg crossing |
|---|---|---|---|---|
| 75.0 uF | 42.23 kHz | 65.0-66.6 deg | -15.0 dB | -12.2 dB @ 165 kHz |
| 85.2 uF | 37.28 kHz | 68.0-69.6 deg | -16.0 dB | -13.4 dB @ 167 kHz |
| 96.8 uF | 32.88 kHz | 70.7-72.2 deg | -17.0 dB | -14.6 dB @ 170 kHz |
| +5 pF COMP stray | 32.4-41.3 kHz | 62.0-68.3 deg | -17.3..-19.4 dB | |

**These are the author's numbers to the digit** (root.py s2.5 claims fc
42.2/37.3/32.9, PM 65.0-66.6 / 68.0-69.6 / 70.7-72.2, |T| -15.0/-16.0/-17.0,
stray case 32.4-41.3 kHz / 62.0-68.3 deg). Independent re-derivation
**CONFIRMS** the values: fc is inside the required 25-50 kHz band and under
fsw/10 = 50 kHz at every corner, phase margin is 20+ deg over the 45 deg floor,
gain margin beats the vendor's -10 dB target both as the author measures it
(|T| at fsw/2) and as the datasheet defines it (|T| at the phase crossing).

Sub-checks, all verified: Eq.17 at fc=38 kHz/COUT=85.2 uF -> 75,434 ohm (E24
75 k); Eq.18 -> 1.67/1.89/2.15 nF, and 3.3 nF puts the comp zero at
`1/(2*pi*75k*3.3n) = 643 Hz` below the 1121 Hz full-load pole (the conservative
direction, confirmed by the model); Eq.19 = `max(2.27, 8.49) = 8.49 pF` -> 10 pF,
pole at `1/(2*pi*75k*10p) = 212.2 kHz`; Eq.20 window at fc=38 kHz/R6=105k =
[7.98, 19.9] pF; a 47 pF COMP cap would pole at 45.1 kHz and cost ~36 deg. All
match. I also reproduced the failure D6 predicted: the vendor's 14k/3.3n/47p/33p
copied onto this bank crosses at 6.8-8.6 kHz.

### 1a. WARNING - the model's calibration against the vendor's plot does not reproduce

root.py s2.5 claims the model was validated by running the vendor's worked
example "(R5=14k, C5=3.3n, C6=47p, C4=33p, COUT=30u, IOUT=3.5A)" and getting
"PM 79-84 deg against the datasheet's published 81.6 deg... fc 19.8-22.3 kHz".

I read **Figure 29, p.21** of the actual PDF: the plotted circuit **does have
C4 = 33 pF fitted across R1**, and Figs 30/31 are that circuit (BW ~16.6 kHz,
PM ~81.6 deg, GM ~-26.8 dB). Running the same model class on that full set:

| configuration | fc | PM | GM (at -180 deg) |
|---|---|---|---|
| vendor values **with** its own 33 pF feedforward | 22.34 kHz | **101.0 deg** | -8.3 dB @ 243 kHz |
| vendor values **without** the feedforward | 19.79 kHz | 79.4 deg | -18.4 dB @ 162 kHz |
| datasheet Figs 29-31 (published) | 16.6 kHz | **81.6 deg** | **-26.8 dB** |

The quoted 19.8 and 22.3 kHz are exactly the two rows above, so the author's
*fc* range spans both variants - but the quoted "PM 79-84 deg" spans only the
**no-feedforward** variants (79.4 with C6, 83.9 with neither). The
configuration the vendor actually plotted gives 101 deg in this model, 19 deg
off the published figure, and the gain margin misses by 18.5 dB. Even the
best-case reading (assume Figs 30/31 were plotted without C4) still leaves the
gain margin 8.4 dB adrift.

Consequence, stated plainly: **the x0.83 realisation factor and the 65-72 deg
phase-margin claim rest on a calibration that does not hold up.** The design
still passes on every reading I can construct - if the model carries the same
~19 deg optimism seen against Fig.31, this board's real PM is ~46-53 deg, above
the 45 deg floor but with a fraction of the claimed margin. This is a warning,
not an error, and P8's small-signal bench is the right place to close it.
Minor related nit: the author reports "|T| at fsw/2" as the gain margin against
the vendor's "< -10 dB" target; the datasheet's gain margin is at the phase
crossing, which for this network is 2.4-2.8 dB *worse* (-12.2 dB vs -15.0 dB at
the 75 uF corner). Still passes.

## 2. C3 as the Eq.19 COMP pole, not the Eq.20 feedforward - CORRECT, and understated (claim 2)

The author's reasoning verifies, and my run says the case is stronger than
claimed:

| C3 role | fc | PM | \|T\| at fsw/2 | GM at -180 |
|---|---|---|---|---|
| Eq.19 COMP HF pole, 10 pF | 32.9-42.2 kHz | 65-72 deg | -15.0..-17.0 dB | -12.2..-14.6 dB |
| no third cap at all | 33.4-43.2 kHz | 77.5-80.9 deg | -11.2..-13.2 dB | -10.6..-12.2 dB |
| Eq.20 feedforward, 10 pF | 34.2-45.1 kHz | 90.8-91.3 deg | **-5.7..-7.8 dB** | no crossing |
| Eq.20 feedforward, 22 pF | 38.0-55.3 kHz | 103-105 deg | **-0.9..-3.0 dB** | **+11.2..+19.1 dB** |

The author said the feedforward "breaks the vendor's own gain-margin target".
It does worse than that: at 22 pF the loop gain is **above 0 dB where the phase
has already passed -180**, i.e. this model says it would be conditionally
unstable, not merely low-margin. The Eq.19 choice buys 4-6 dB of gain margin for
8-11 deg of phase, from a starting point (77-81 deg) that had phase to spare.
The second argument - that 8.5 pF is the same order as the COMP node's
unavoidable 3-8 pF stray, so a fitted 10 pF makes the pole *designed* rather
than parasitic - is also sound; my +5 pF-stray row shows the design still holds
at 62-68 deg. **VERIFIED, decision correct.**

## 3. Feedback divider 105k / 20.0k, 0.1% - VERIFIED (claim 3)

`VOUT = 0.8 * (1 + 105.0/20.0) = 0.8 * 6.2500 = 5.0000 V` exactly. Divider
current 40 uA. Corners recomputed from the datasheet's real VFB spread
(792 / 800 / 808 mV, DS p.5) with resistors at +/-0.1% stacked adversely:

| corner | Vout | margin to the 4.90 / 5.10 V window |
|---|---|---|
| VFB 792 mV, R6 -0.1%, R7 +0.1% | **4.9417 V** | +41.7 mV |
| nominal | 5.0000 V | |
| VFB 808 mV, R6 +0.1%, R7 -0.1% | **5.0585 V** | +41.5 mV |
| same corners with 1% parts | 4.8677 / 5.1357 V | **FAILS both ends** |

The author's "~4.94 V, ~40 mV of margin" is right, and the 0.1% requirement is
proven, not asserted - 1% parts miss by 32 mV / 36 mV. Worth passing to SIM-1:
its stated scope is initial tolerance only, and both parts are +/-25 ppm/C; at
the board's ~85 C local temperature (+60 C) worst anti-tracking drift moves the
corners to 4.9375 / 5.0627 V, so ~5 mV of the 42 mV is spent by TCR. Still
passes; SIM-1 should sweep it rather than ignore it.

## 4. UVLO 105k / 24.0k - VERIFIED (claim 4)

Forward: `R3 = (0.924*6.2 - 5.3)/4.114uA = 104,229 -> 105 k`;
`R4 = 1.1*104229/(5.3 - 1.09 + 5.5uA*104229) = 23,969 -> 24.0 k`. Back-solved on
the snapped values: `VOFF = 1.09 + 1.1*105k/24.0k - 5.5uA*105k = 5.325 V`,
`VON = (5.325 + 4.114uA*105k)/0.924 = 6.230 V`, hysteresis 0.905 V, 93 uA at
12 V. Every figure the author states is correct, and both trip points clear the
datasheet's stated validity floors (VON > 3.7 V, VOFF > 3.3 V, DS p.11).

I also checked that the vendor's Eq.2/Eq.3 are internally coherent rather than
taking them on faith: writing the node equations directly with VEN_H = 1.18 V,
VEN_L = 1.09 V and pull-ups I_rising / I_falling, the datasheet's 0.924
coefficient and 4.114 uA constant fall out **only** if I_rising = 1.50 uA and
I_falling = 5.5 uA - exactly the 1.5 uA / (1.5+4) uA sources drawn in Fig.23,
p.11 (which I read in the PDF). The equations are self-consistent and the
author used them correctly. Direct node equations give VON 6.185 / VOFF 5.281,
within 45 mV of the Eq.2/3 answer.

Corner sweep (VEN_H max 1.25 V, VEN_L min 1.03 V, 1% resistors): VON 6.084 to
**6.670 V**, VOFF 4.875 to 5.372 V - inside SIM-2's declared [5.6, 6.8] /
[4.6, 6.0] window, but see warning 6 below.

## 5. Q1 reverse-polarity topology - VERIFIED CORRECT (claim 5)

Netlist, checked pin by pin against `parts/C16072.json` (1,2,3 = S; 4 = G;
5,6,7,8 = D):

```
/VIN     Q1.5/D  Q1.6/D  Q1.7/D  Q1.8/D      <- all four drains, input side
+VIN     Q1.1/S  Q1.2/S  Q1.3/S              <- all three sources, load side
/QGATE   Q1.4/G  R1.1  D2.2/A
+VIN     D2.1/K
GND      R1.2
```

All 3 sources and all 4 drains wired. Orientation is the correct one and the
only correct one: a P-FET's body diode runs anode = drain -> cathode = source,
so with the drain on the input side the diode is **forward** in the normal
direction (load powers up through it at Vin - Vf), the source then rises,
R1 holds the gate at GND, `Vgs = -(+VIN)` enhances the channel and shorts the
diode out. Reversed, /VIN goes to -Vin while +VIN is held near 0 by the load,
the body diode is reverse-biased, `Vgs = 0` and the FET is off - it blocks. I
checked the opposite orientation (source to input) for completeness: it
enhances fine forward but its body diode conducts load->supply on reversal, so
it does not block. The schematic has the right one.

Vgs stress: -12 V nominal, -18 V at max line, -25.4 V on the hot-plug ring
against a +/-25 V rating - which is why D2 is mandatory. D2's polarity is right:
cathode (pin 1, name K) at the source/+VIN, anode (pin 2, name A) at the gate,
so the clamp is reverse-biased by exactly |Vgs| and breaks down at 15 V, with
the clamp current returning through R1 (30 uA at 18 V, 104 uA on the ring).
The SOD-123 footprint's silk cathode band and pad-1 tick marks sit on pad 1,
matching the symbol - polarity is consistent symbol-to-land.

## 6. No gate resistor on Q1 - REASONING CORRECT (claim 6)

The claim is that a gate RC cannot limit inrush because the body diode is
forward in the normal direction. That follows directly from the topology
verified in section 5: at hot-plug the input bank charges through the body
diode with the channel still off, so a gate RC delays only a channel that the
diode has already bypassed. Confirmed, and the corollary the author gives (a
gate cap would *delay* turn-off on a live polarity reversal) is also right.
**Do not let a fix loop add one.** The residual concern is R1's *value*, not the
absence of a series R - see warning 5.

## 7. Net contract - FULLY COMPLIANT (claim 7)

Exported net names, dumped from `kicad/sbuck-5v3a.net` (not read off the
schematic):

```
BARE  : +5V  +VIN  GND
SLASH : /BST /COMP /COMPZ /EN /FB /LEDA /QGATE /RT /SNUBZ /SW /VIN /VIN_RAW
```

All three power-symbol nets come out bare; every local label carries exactly
one leading slash; **no `/{slash}...` escaped name anywhere** (the failure mode
LEARNINGS 2026-08-09 records on this very board). No net ends in `_P`, `_N`,
`_H`, `_L`, `DP`, `DM`, `+` or `-`, so `rules_gen.detect_diff_pairs` cannot
pair `/SW`; `constraints.json.diff_pairs` is an explicit empty list as well.
The four added series nodes (`/VIN_RAW`, `/COMPZ`, `/SNUBZ`, `/LEDA`) are
genuine additions for internal nodes the chain notation cannot name, they are
suffix-safe, and `/VIN_RAW` already has matching `power[]` and `voltages[]`
entries in `constraints.json`. 86 of 86 pins connected, ERC 0/0,
`netlist_audit` 0.

## 8. C4 polarity - VERIFIED, and doubly so (claim 8)

The author keyed polarity off the footprint because the symbol's pin *names*
are generic. Both artifacts actually agree:

- `aiee.pretty/CAP-SMD_BD6.3-...FD.kicad_mod`: three solid silk polys - a
  horizontal bar + a vertical bar centred at x = -2.706 (a **`+`**) directly
  over pad 1 (x = -2.67), and a lone horizontal bar at x = +2.706 (a **`-`**)
  over pad 2. Pad 1 = positive.
- `aiee.kicad_sym` `KNM2100UF35V149EC0055`: it is **not** a non-polar glyph -
  it draws the straight plate at x = -0.51 (pin-1 side), the curved plate as an
  arc at x = +0.42..1.15 (pin-2 side), and a `+` sign from two polylines at
  (-1.78, 1.27), again on the pin-1 side.

root.py wires `{"1": "+VIN", "2": "GND"}`. **Correct.** The generator's comment
("symbol pin names are non-polar") is true but understates the evidence - the
symbol graphic independently agrees with the land.

Same check run on the other two polarised parts: D1 `0805G` symbol pin1 = A /
pin2 = K, and the LED land draws a left-pointing diode triangle with pad 1
(x = +1.05) on the base/anode side and the chamfered body corners on the pad-2
cathode side; netlist has D1.1/A on /LEDA and D1.2/K on GND. Correct.

## 9. Abs-max at the declared 26 V hot-plug ring - ALL PINS CLEAR (claim 9)

| U1 pin | applied at the 26 V ring | abs max (DS p.4) | verdict |
|---|---|---|---|
| 2 VIN | 26 V | -0.3 to 42 V | clear, 1.6x |
| 3 EN | 26 * 24.0/129 = 4.84 V | -0.3 to 42 V | clear |
| 4 RT/CLK | ~0.5 V (internally driven, R4 to GND) | -0.3 to 6 V | clear |
| 5 FB | 0.8 V (0.88 V at the 110% OVP trip) | -0.3 to 6 V | clear |
| 6 COMP | internally driven, < 3 V | -0.3 to 6 V | clear |
| 8 SW | -0.3..VIN+0.3 DC, -2.5..VIN+2.0 for 20 ns | as stated | inherent/internal |
| 1 BST | VSW + ~5 V from the internal LDO | VSW-0.3 to VSW+6.0 | clear, C1 = 100 nF fitted |

Passives: C4 35 V vs 26 V (1.35x, and an alu surge rating is typically 1.15x
rated); C5-C9 and C1/C2/C3/C16 all 50 V; R2 sees 26 V in an 0603 rated 50 V
working. Q1: Vgs clamped at 15 V vs +/-25 V; forward Vds is the Rds(on) drop.
Nothing on this board violates an absolute maximum in the forward direction.
The reverse-polarity hot-plug case is a different question - warning 7.

---

## Other things I checked and found sound (not findings)

- **0 A load / PFM.** The load *can* go to 0 A and U1 has no MODE pin. Read
  DS Sec.2 p.10 directly: in PFM the COMP clamp corresponds to a 750 mA peak
  and "the buck converter does not sink current from the output" - no reverse
  inductor current. PFM ripple works out at `Q/C = 0.66 uC / 97 uF ~= 7 mV`
  per pulse, far inside the 50 mV allowance, and the same error amp still
  regulates FB, so the DC setpoint holds. R8/D1 also guarantee ~1 mA of
  standing load. **This board does not fail at 0 A.**
- **Startup.** Internal fixed 2 ms soft-start into ~97 uF needs
  `97u * 5/2m = 0.24 A` of charging current against a 4.25 A minimum current
  limit - no hiccup on startup, no SS pin to get wrong.
- **Duty-cycle limits.** D = 0.278 at 18 V -> 555 ns on-time against a 100 ns
  minimum; D = 0.71 at 7 V, well clear of dropout. Inductor ripple
  `5*(1-0.278)/(6.8u*500k) = 1.06 A`, peak 3.53 A against IPEAK_LIMIT min
  4.25 A (20% margin, matching the /SW 3.6 A constraint entry).
- **Thermal derating.** DS Fig.24 (p.12, VIN 12 V / 500 kHz) keeps VOUT = 5 V
  flat at 3.5 A up to ~57 C ambient; the board's 50 C spec ambient is inside
  the flat region, so 3.0 A does not contradict the vendor's own curve.
- **Decoupling per the datasheet, not "some caps".** VIN wants >10 uF ceramic
  with an RMS rating above half the load (>= 1.75 A): 4x 4.7 uF/50 V 1206 is
  ~13 uF after DC-bias derating, with `3*sqrt(D(1-D)) = 1.50 A` worst-case
  (at Vin = 10 V, inside the range) shared four ways plus C4. C9 100 nF is at
  the pin. BST wants 100 nF BST-to-SW: C1 is exactly that, and correctly
  excluded from `decoupling.json` (not a rail+gnd pair). Coverage is complete
  for U1's one power pin.
- **Every floating-input class.** RT/CLK cannot float and is tied through
  R4 = 200 k (`RT[kOhm] = 100000/fsw[kHz]` -> exactly 500 kHz, DS Eq.7); EN is
  divided, never left open; COMP is compensated; there are no NC pins and no
  open-drain outputs needing a pull.
- **Exposed pad.** Pin 9 is wired to GND as the datasheet requires (it is a
  real net-capable pad, and the 16-via array is correctly flagged forward as a
  P6/P7 review gate because `check_thermal` sits at 51.9 vs its 51.1 trigger).
- **LED branch.** `(5 - 2.8)/2.2k = 1.0 mA` as claimed. Vf = 2.8 V is an
  assumption (no `parts/C2297.json` exists) but the answer is insensitive: a
  2.0 V GaP green gives 1.36 mA and a 3.2 V InGaN green gives 0.82 mA, both
  fine on an 0805 rated 430 mcd at 5 mA, and no green LED has a Vf that could
  fail to light on a 5 V rail.
- **DNP handling.** J1, J2, R9, C16 all carry `Variant=DNP` in the netlist and
  R9/C16 exist as real nets/pads so P6/P7 account for their copper. Every
  purchased ref carries an `LCSC` field (44 components; only TP1-TP7 and H1-H4
  lack one, correctly). H1-H4 use the zero-pin `Mechanical:MountingHole`, so
  they are GND-isolated as delegate Q19 requires.
- **Fuse placement.** J1 -> F1 -> Q1 drain, so the fuse is upstream of the
  protection FET: it covers the shorted-high-side-switch fault it exists for
  (Q7/D5) and is *not* exposed to a reverse-polarity event, which Q1 blocks.

## Two observations for the orchestrator (not violations)

1. **The clean ERC is worth less than it looks on this board.** In
   `aiee.kicad_sym`, U1 declares only VIN/GND/EP as `power_in` and SW as
   `power_out`; BST, EN, RT/CLK, FB and COMP are all `passive`, and every
   discrete is passive. ERC's pin-conflict engine therefore has almost nothing
   to bite on, and 0 errors / 0 warnings is close to the only possible outcome.
   That is not a defect to fix, but it is the reason this human-level review is
   the real gate at P4.
2. **The plot is a stub-label schematic**, not a wired one - every part is drawn
   in isolation with net-name stubs, so a human cannot trace topology off the
   PDF and must read the netlist instead. That is this generator's idiom across
   the repo, so I am recording it rather than raising it, but bring-up will want
   the netlist open next to the board.
3. **sheets.md s5 item 7 lists silkscreen under "P4 notes"** - board name/rev,
   "VIN 7-18V" / "VOUT 5V 3A" with polarity marks at both terminals, pin-1
   marks, test-point labels. None of that is reachable from a schematic
   generator. Since delegate Q30 makes silk the *only* mitigation for a swapped
   in/out connection ("not survivable by design"), it must be carried forward as
   a hard P6/P8 `silk_place` requirement, not lost with the phase.

---

## Findings (7 warnings, 0 errors) - full text in `review-schematic.json`

| # | kind | refs | one-line |
|---|---|---|---|
| 1 | `loop-model-calibration` | R5 C2 C3 U1 | vendor-plot calibration does not reproduce with the vendor's own 33 pF feedforward fitted; PM claim may be ~19 deg optimistic |
| 2 | `load-step-margin` | R5, C10-C14 | 148 mV is the un-derated figure; the author's own x0.83 factor gives 181 mV vs 200 mV, and the 0->3 A step starts in PFM |
| 3 | `snubber-dissipation` | R9 C16 | if populated as documented, `C*V^2*f` = 162 mW at 18 V into an 0603 rated 0.1 W |
| 4 | `inrush-vs-idm` | Q1 C4 | 57 A comes from the 0.30 ohm row while the 26 V rating comes from the 0.05 ohm row; at 0.10 ohm the same formula gives 180 A vs a -60 A IDM |
| 5 | `gate-dvdt-immunity` | Q1 R1 D2 | reverse hot-plug couples the drain step to the gate through Crss; C16072.json publishes no Ciss/Crss, so it cannot be bounded |
| 6 | `uvlo-corner-margin` | R2 R3 F1 Q1 | drop budget is 0.58 V not 0.49 V (0.32 V of effective hysteresis); worst VON 6.67 V is 0.33 V under the 7.0 V floor |
| 7 | `reverse-hotplug-bvdss` | Q1 | reverse hot-plug rings against Coss with nothing on /VIN; ~36 V vs -30 V BVdss, benign avalanche (~0.2 uJ) but undeclared |

Findings 1, 2, 6 and 7 are analysis/margin items that P8's benches (SIM-1,
SIM-2, and a small-signal loop bench) should close. Finding 3 is a one-value BOM
change to a DNP part. Findings 4 and 5 are datasheet-coverage gaps, not
schematic edits - **no change to the netlist is required by any of the seven.**
