# pd-trigger - power tree

*Amended A1 after the P3 datasheet extracts: no LDO, no `+3V3` rail. See
`decisions.md` section A1.*

Not a rail tree - a **power path** plus two housekeeping stubs. Numbers are from
`research/power.json` / `power.md`, re-derived where the extracts
(`parts/C970725.json`) overruled them.

```
J1 VBUS (4 contacts) --+-- D1 TVS -> GND
                       |
                       +-- C1 22uF/50V + C2 100nF        [connector-side bulk]
                       |
                       +-- F1 PPTC 1A/30V --> /VAUX --> J3 aux header
                       |
                       +-- R14 0R link --> /VIND  [housekeeping, 50 mA, thin]
                       |                     |
                       |                     +-- R2 1k 2512 --> /VDD --+-- U1 pin 1 VDD
                       |                     |                         +-- C5 1uF
                       |                     |                         +-- R3..R5 100k
                       |                     |                              -> SW1 -> GND
                       |                     +-- R1 10k --> U1 pin 8 (sense)
                       |                     +-- R6 6k8 + D2 6V2 --> Q1A base
                       |                     +-- R8 10k --> /HV_OK
                       |                     +-- R10 3k3 --> D3 PWR --> GND
                       |                     +-- R13 4k7 --> D6 --> /HV_OK
                       |                     +-- R12 1k5 --> D5 --> Q1B collector
                       |
                       ===== VBUS, 1.75 mm F.Cu, no vias ===> J2 screw terminal (5 A)

GND: B.Cu pour, unslotted, J1 GND pads and J2 GND pad each >= 10 vias into it
```

## Rails

| Net | Source | V | I design | I typ | Consumers | Notes |
|---|---|---|---|---|---|---|
| `VBUS` | J1, PD-negotiated as SINK | 5 / 9 / 12 / 15 / 20 V (21 V worst case with PDO tolerance) | **5.0 A** | load-dependent | J2 (5 A), F1 (1 A), R14 (32 mA) | pass-through: input net and output net are the SAME copper |
| `/VAUX` | VBUS through F1 | same as VBUS | **1.0 A** | J3 only | own net so `check_current` does not demand 1.75 mm onto a 0.1 in header |
| `/VIND` | VBUS through R14 (0 R) | same as VBUS | **0.05 A** declared | 32 mA at 21 V, 3.8 mA at 4.4 V | R2, R1, R6, R8, R10, R12, R13 | width-only stub (`pdn: false`) so indicator traces route at the fab floor |
| `/VDD` | `/VIND` through R2 (1 k) | 3.24 - 3.36 V (internal shunt) | **0.02 A** declared | 17.7 mA at 21 V, 1.7 mA at 5 V | U1 pin 1, C5, R3-R5 | NOT a rail - a shunt node. `pdn` left true so `check_pdn` enforces the datasheet-mandated 1 uF |
| `GND` | return | 0 V | **5.0 A** | everything | B.Cu pour; deliberately NOT a `power[]` entry - see `decisions.md` D7 |

Uniform 5 A at every profile (P0 answer 1): 25 W at 5 V up to 100 W at 20 V. The
board never asks for more than the source advertises and cannot exceed a granted
PDO; copper, connectors and the aux cap are sized at 5 A regardless of profile.

## `/VIND` budget (the whole housekeeping load)

| Consumer | at 21 V | at 4.4 V (low line, 5 V profile) | Basis |
|---|---|---|---|
| R2 -> `/VDD` dropper | 17.7 mA | 1.1 mA | (V - 3.3) / 1 k |
| D3 PWR LED (R10 3k3) | 5.8 mA | 0.76 mA | (V - 1.9) / 3k3 |
| D6 green (R13 4k7) | 4.0 mA | 0 (Q1A off) | only conducts above the 6.7 V window |
| D5 red (R12 1k5) | 0 (Q1B off) | 1.7 mA | only conducts below the window |
| R8 window pull-up | 2.1 mA | 0.07 mA | 21 V / 10 k into Q1A when it conducts |
| R6 + D2 zener branch | 2.1 mA | ~0 | (V - 6.9) / 6k8 |
| R1 sense into pin 8 | 0.65 mA | 0.2 mA | pin clamps internally; R1 sets the current |
| **Total** | **~32 mA** | **~3.8 mA** | |
| **Declared** | **50 mA** | | `power[].current_a` - 1.5x headroom |

## `/VDD` budget - the number that constrains the strap resistors

| Item | Value | Basis |
|---|---|---|
| Delivered by R2 at 20 V | 16.7 mA | (20 - 3.3) / 1 k, inside the 30 mA shunt limit |
| Delivered by R2 at 5.0 V | **1.7 mA** | (5 - 3.3) / 1 k - the binding case |
| Delivered by R2 at 4.4 V | 1.1 mA | worst-case low line |
| CH224K IDD | **unpublished** | the extract is explicit: table 8.2.3 has no ICC/IDD row for CH224K, and the 1.8 mA typ / 12 mA max in 8.2.1 belongs to CH224Q/CH224A and **must not** be applied. WCH's own reference circuit uses this 1 k dropper, so IDD must fit inside 1.7 mA. |
| R3-R5 CFG pull-ups | 99 uA | 3 x 33 uA at 100 k - **6 %** of the 5 V budget (three 10 k pull-ups would have taken 58 %) |
| Shunt sink (the remainder) | 0 - 16.6 mA | chip dissipation 3.3 V x 16.7 mA = **55 mW**, against a 400 mW chip limit |

Contingency if VDD sags at the 5 V profile during bring-up (measure it): drop R2
to **680 Ohm** - 24.6 mA at 20 V, still under the 30 mA shunt limit, 0.41 W in
the same 1 W part. The practical floor is ~600 Ohm ((21 - 3.24) / 30 mA), below
which the shunt is overrun at the top of the range.

## Dissipation at full throughput (5 A, 20 V, 100 W)

| Element | P at 5 A | Basis | `thermal` entry |
|---|---|---|---|
| J1 VBUS contacts (4) | 0.06 - 0.25 W | 40 mohm max initial per contact (USB-C spec), 4 in parallel = 10 mohm worst; 10 mohm/contact realistic | sheds into the F.Cu VBUS pour (not modelled) |
| J1 GND contacts (4) | 0.06 - 0.25 W | same, return side | **yes: 0.25 W on GND** |
| VBUS F.Cu run, ~35 mm at 1.75 mm / 2 oz | 0.14 W | 0.285 mohm/sq at 60 C, 20 squares = 5.7 mohm | no |
| B.Cu GND pour return | < 0.05 W | plane, not a trace | no |
| J2 screw terminal, both poles | 0.05 - 0.50 W | dominated by how well the user tightens the screw | no |
| **R2 VDD dropper** | **0.28 W at 20 V, 0.31 W at 21 V** | (V - 3.3)^2 / 1 k - the largest single component loss on the board | no: 1 W 2512, 3x derated (see `decisions.md` D11) |
| U1 CH224K (shunt) | 0.055 W | 3.3 V x 16.7 mA, vs a 400 mW chip limit | no |
| R10 PWR LED leg | 0.11 W | 5.8 mA^2 x 3k3 - hence 1206 | no |
| R13 green LED leg | 0.08 W | 4.0 mA^2 x 4k7 - hence 0805 | no |
| R8 / R6 window network | 0.07 W | 21 V^2 / 10 k + 2.1 mA^2 x 6k8 | no |
| LEDs (3, one of D5/D6 lit) | 0.01 W | ~2 mA x ~2 V each | no |
| F1 aux PPTC at 0.5 A | 0.025 W | 0.5^2 x 100 mohm | no |
| **Board total** | **~1.0 W typ, ~1.7 W worst** | 1.0 - 1.7 % of 100 W | |

Stated honestly: a linear dropper plus bus-referenced LEDs waste ~0.6 W at the
20 V profile, roughly double what the (rejected) regulated rail would have. At
0.6 % of throughput on a board with no enclosure, that buys the topology the
datasheet actually endorses - see `decisions.md` A1.

## Copper sizing (verified against the pipeline's own model)

`check_current.required_width_mm(I, dT, cu_mm)`, run on the repo venv - these are
literally the widths `rules_gen` writes and `check_current` enforces:

| Net | I | dt_c | 2 oz (0.070 mm) required | 1 oz (0.035 mm) would need |
|---|---|---|---|---|
| `VBUS` | 5.0 A | 10 | **1.750 mm** | 3.500 mm (unroutable here) |
| `/VAUX` | 1.0 A | 10 | **0.250 mm** | 0.500 mm |
| `/VIND` | 0.05 A | 10 | 0.013 mm -> fab floor 0.1524 mm | same |
| `/VDD` | 0.02 A | 10 | 0.005 mm -> fab floor 0.1524 mm | same |

`dt_c = 10` throughout (2 oz makes the margin free). The interface fragment's
`dt_c = 20` recommendation was contingent on 1 oz copper and is superseded -
see `decisions.md` D12.

## Structural requirements the numbers do not capture

1. **All four VBUS contacts and all four GND contacts of J1 bonded in copper at
   the pads.** The USB-C 5 A rating is *collective* across A4/A9/B4/B9 = 1.25 A
   per contact; dropping one raises the other three to 1.67 A.
2. **The whole 5 A forward path stays on F.Cu.** `check_current` demands
   `ceil(5.0 / 0.5) = 10` vias per via cluster on a declared net, so a single
   layer transition costs a 10-via field. With zero vias on VBUS there is nothing
   to fail.
3. **GND return is the B.Cu pour, unslotted under the whole power path**, with
   **>= 10 vias at J1's GND pads and >= 10 at J2's GND pad**. This is the
   structural substitute for a GND `power[]` entry (`decisions.md` D7).
4. **`VBUS` has exactly five taps** - D1, C1, C2, F1 and **R14** - and each must
   hug the run so its 1.75 mm-wide stub stays 2-3 mm long. Everything else
   (R1, R2, R6, R8, R10, R12, R13) hangs off `/VIND` and routes thin. This is
   what the 0 ohm link buys; without it, eight fat stubs would have to reach the
   controller and the LED row.
5. **`rules_gen` builds ONE `Power` net class** whose track width is the max
   across all declared power nets, so `/VAUX`, `/VIND` and `/VDD` will
   default-route at 1.75 mm as well. Per-net DRC minimums stay correct; this is a
   routing default worth a P5 hand-edit on a board this small.
6. **R2 (2512, 0.31 W continuous) sits clear of U1's baseplate** - `constraints.
   json` carries a `separation` term of 8 mm between them - and away from the
   receptacle.
7. **e-marked cable disclaimer** (documentation, nothing on the board can change
   it): 20 V at 5 A requires a 5 A e-marked cable AND a source advertising a
   20 V/5 A PDO. A generic 3 A cable silently caps the board at 60 W.
