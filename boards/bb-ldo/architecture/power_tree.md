# bb-ldo - power tree (P2)

One source, one rail, one consumer. Budgets lifted from `research/power.json`
and reconciled against the final block choices in `blocks.md` - **nothing
changed**: P2 added no part, no rail and no consumer, so P1's numbers stand as
emitted. Derivations and citations: `research/power.md`.

## 1. Rails

| rail | source | topology | budget | dissipation | why it costs what it costs |
|---|---|---|---|---|---|
| `+5V` | J1, bench supply 4.75-5.25 V, fault limit 2 A | direct (no conversion) | 515 mA | 0 W | it is the input node; nothing to trade |
| `+3V3` | `+5V` | linear series regulator (`ldo` token; the part is standard-dropout, not a true LDO) | 510 mA | **1.00 W in U1** | the owner chose linear: zero switching noise and a four-part regulator block, paid for at ~63% efficiency and 1 W of heat the board must radiate |
| `GND` | - | return | 515 mA | - | single return, B.Cu pour |

**Per consumer** (no bare totals):

| rail | consumer | current | basis |
|---|---|---|---|
| `+3V3` | J2 -> external static resistive load | 500 mA | owner-stated, continuous 100% duty (answer 6) |
| `+3V3` | R1 min-load bleed (CONTINGENT, `blocks.md` s.4) | 10 mA | datasheet min load 3 mA typ / 10 mA max |
| `+3V3` | **budget** | **510 mA** | |
| `+5V` | U1 pass current (= the `+3V3` budget) | 510 mA | series pass device, 1:1 |
| `+5V` | U1 ground / quiescent current | 5 mA | **ASSUMED** - implied by requirements s.3 ("~505 mA in at 500 mA out"); the part's own Iq is not in the research fragments (gap 1) |
| `+5V` | **budget** | **515 mA** | |
| `GND` | return of the above | 515 mA | |

**No 30% headroom, deliberately.** 500 mA is an owner-stated hard maximum for
an external load, not an estimate of unknown consumers. Padding it would
inflate the copper requirement on a board whose entire point is that the copper
area is earned from a real number.

Input power 2.58 W nominal / 2.70 W high line; output 1.65 W; efficiency
61-64% - a property of the chosen topology, not a spec to meet.

## 2. Trace and via sizing (what `rules_gen` / `check_current` derive)

0.515 A at dT 10 C on 1 oz outer copper needs **0.26 mm**; any sane routing
width clears it 2-4x. Via ampacity default 0.5 A -> 2 vias per layer
transition on either rail. Current is a non-event here; it is declared so the
gates hold the numbers, not because anything is tight.

`+3V3` carries `plane_fed: true`. That is doing real work: it downgrades
via-count findings on a plane-fed rail to advisory AND makes `check_current`
error `plane_missing` if the `+3V3` pour is ever absent. The thermal design IS
that pour, so the rail's own gate now enforces its existence - something
`check_thermal` alone cannot do.

`GND` carries `pdn: false` (a return, not a rail: `check_pdn` inventories every
`power` entry and would otherwise error "power rail GND has no decoupling").

## 3. Dissipation in U1 (the number that sizes the board)

| term | arithmetic | W |
|---|---|---|
| pass-device conduction, high line, load only | (5.25 - 3.3) x 0.500 | 0.975 |
| quiescent / ground current | 5.25 x 0.005 (ASSUMED Iq) | 0.026 |
| **design point (frozen, = `power_w`)** | | **1.00** |
| + min-load bleed, if fitted | (5.25 - 3.3) x 0.010 | +0.020 |
| + Iq at a 10 mA max instead of 5 mA typ | 5.25 x 0.005 | +0.026 |
| + Vout at its -3% corner | (0.510) x (3.30 - 3.20) | +0.051 |
| **stacked worst-case corner** | | **~1.10** |

At theta_JA = 65 C/W: **Tj = 115 C** at the design point (10 C under the 125 C
steady-state limit), **121 C** at the stacked corner (4 C margin). 1.00 W is
2x the 0.5 W "hot part" threshold - this is the board's only hot spot, and the
only reason the board has a size.

## 4. Copper area -> theta_JA (the deliverable of this tree)

Chain: Ta 50 C, Tj target 115 C -> allowed rise 65 C -> at 1.00 W,
**theta_JA <= 65 C/W**.

| top-side copper on the tab net | theta_JA | source |
|---|---|---|
| bare pad | 136-150 C/W | both vendors (worst case, never a target) |
| 342 mm2 | 75 C/W | TI SOT-223 1 oz, top-only |
| 490 mm2 | 69 C/W | TI SOT-223 1 oz, top-only |
| 645 mm2 | 66 C/W | TI SOT-223 1 oz, top-only |
| **1000 mm2** | **65 C/W** | **vendor Table 1, 1/16 in FR-4, 1 oz, ZERO backside copper - the design row** |
| 2500 mm2 (+ backside) | 55 C/W | vendor Table 1 best case (backside rows unusable - see `blocks.md` s.6.3) |

**Emitted requirement:** F.Cu `+3V3` pour contiguous with the tab pad,
**>= 1000 mm2**, floor 645 mm2, 1500-2500 mm2 preferred. Two independent vendor
sweeps of the same package on the same copper weight agree within ~1 C/W, and
below ~650 mm2 the curve climbs steeply. Confidence HIGH on the design row (a
direct table row, no interpolation, no backside dependency); the residual risk
is clone die variance, not the reading.

## 5. Layout arrangement, and what `check_thermal` will say

**The tab is VOUT, not GND.** So the heatsink pour is the `+3V3` net and it can
NEVER be via-stitched to a bottom GND pour - the vias would short the rail.
Arrangement (unchanged from P1, and now in `constraints.json`):

- **F.Cu**: `+3V3` pour, `connect: solid` (no thermal relief - relief spokes
  would neck the tab's only heat path). Declared as a plane so `planes_gen`
  builds it and `check_current` enforces it.
- **B.Cu**: GND pour (the 515 mA return, milliohms, no high-speed content),
  **plus a `+3V3` island directly under the tab** stitched to the top pour with
  the 12 declared vias. The island costs a hole in the GND return under U1;
  on a board with no switch node and no fast edges that costs milliohms and
  nothing else.
- **The island is a P6/P7 handoff, not authorable now.** It needs a `region`
  in board coordinates and the outline does not exist yet (geometry is an
  output). Until it is added to `constraints.json["planes"]`, the 12 stitching
  vias have nothing on B.Cu to land in. See OPEN.

**`check_thermal` will report `thermal_area` as an ERROR at P8, for any
layout.** Its 2-layer model is `theta = 55 + 119 * exp(-A/350)` with credited
area capped at 645 mm2, i.e. a floor of **73.8 C/W** no matter how much copper
the board earns; 1.00 W x 73.8 = 73.8 C rise against the declared 65 C. The
same package measures 65-66 C/W over that area in two vendors' sweeps and keeps
improving to 55 C/W at 2500 mm2, where the model has stopped counting. **The
number stays honest at 65** and the P8 finding is waived with the vendor tables
as evidence. Verified in the checker source, not taken on report.

`min_vias` is set explicitly to **12** (a 3x4 array at ~1.3 mm pitch in the
pour around the tab; that array spans ~2.3 mm from the centroid, inside the
~4 mm radius the gate counts - `max(2.0, sqrt(pad-hull area / pi) + 1.5)`).
The gate's own default computes ~34-36 vias for a SOT-223 pad hull, which no
tab region can physically hold.
**Keep them out of the tab pad itself** - JLC leaves standard vias unfilled and
via-in-pad wicks solder out of the joint that IS the thermal path.

## 6. Sequencing, inrush, protection

One rail, always on: nothing to sequence, no soft-start requirement, no
power-good, no consumer that cares. Inrush is the charge of C1 (10 uF) + C2
(22 uF) at power-on, bounded by the bench supply's own 2 A limit (owner answer
2). No input protection by scope tier, accepted by the owner (answer 3), with
the miswire hazard recorded in `requirements.md` s.8.

## 7. Gaps carried into P3 (none blocks P2)

1. **Quiescent current is not in the research fragments** (5 mA inferred). At a
   10 mA max, Pd = 1.03 W and the required theta_JA tightens to 63 C/W. P3
   reads it off the datasheet when it pins the manufacturer.
2. **What Table 1's backside copper is connected to** - a via tie to a ground
   plane is impossible for a VOUT tab, which suggests dielectric coupling only,
   but that is an inference from the pinout, not a sentence in the datasheet.
   Rows 1/4/5 stay unusable until it is read.
3. **Dropout at 500 mA is not tabulated** (only the 0.8-1.0 A point, 1.3 V
   max). Budgeted to 1.3 V against 1.45 V of worst-case headroom: it fits with
   0.15 V to spare, and the real 500 mA figure is well below it.
4. **Cout ESR of a real orderable part** (target 0.3-0.5 ohm at 100 kHz, MnO2
   not polymer) - P3 selection, `blocks.md` s.6.1.
5. **Whether R1 is fitted** - P3, with the page citation for the FIXED
   variant's minimum load.
