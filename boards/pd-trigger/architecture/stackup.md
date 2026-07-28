# pd-trigger - stackup

## Chosen: `JLC2313_1.6_2oz` (2-layer, 1.6 mm, **2 oz** outer copper, HASL)

Name is verbatim from `reference/stackups.yaml`. Pass it explicitly:

```
board_init.py --stackup JLC2313_1.6_2oz --outline 45x25 ...
```

**The `--stackup` flag is not optional.** `defaults: {2: JLC2313_1.6}` is the
1 oz stack; `board_init` writes the `(stackup)` block from that file,
`check_current` reads copper thickness back out of it, and `rules_gen` derives
its capability class from `copper_oz`. Omitting the flag silently sizes the whole
board at 1 oz and the P8 gate then demands a 3.500 mm VBUS trace.

| Layer | Type | Thickness | Role |
|---|---|---|---|
| F.Cu | copper, 2 oz | 0.070 mm | VBUS 5 A run (1.75 mm), all signals, all parts |
| dielectric 1 | FR4 core, er 4.5 | 1.460 mm | |
| B.Cu | copper, 2 oz | 0.070 mm | **GND pour** - the 5 A return, unslotted under the power path |

## Why 2 layers

- No data pairs at all: D+/D-, SBU and SuperSpeed are unconnected at the
  receptacle; CC1/CC2 are 300 kbit/s BMC with 300 ns edges (critical length
  ~7.5 m against a 40 mm board).
- No controlled impedance anywhere - `JLC2313_1.6_2oz` ships
  `controlled_impedance: []` and correctly so: a 2-layer board has no adjacent
  reference plane, and nothing on this board needs one.
- One power net, one return, ~32 components. A 4-layer board would buy an inner
  GND plane the B.Cu pour already provides, at extra cost and no benefit.
- `constraints.json` carries **no `high_speed` key**, so `check_return_path` and
  the `rules_gen` impedance rules no-op cleanly, and `planes_gen`'s 2-layer
  default (B.Cu GND pour) is exactly what this board wants - no `planes` key
  either.

## Why 2 oz copper (the decision that changed the fab class)

The pipeline's own IPC-2152 model, run this session:

| I | dT | 1 oz | 2 oz |
|---|---|---|---|
| 5.0 A | 10 C | **3.500 mm** | **1.750 mm** |
| 5.0 A | 20 C | 2.383 mm | 1.191 mm |

3.500 mm is 14 % of a 25 mm-tall board, and `check_current` applies the same
minimum to *every track segment* on the net - not just the main run, but each tap
stub to the TVS, the bulk caps, the aux PPTC and the housekeeping link. On 1 oz
you are not choosing
"pour instead of trace", you are choosing "the entire 5 A net is one 3.5 mm-wide
object", which does not survive placement next to a USB-C receptacle, a 5.08 mm
terminal block, an ESSOP-10 and a DIP switch. 1.750 mm is an ordinary power
trace. Verdict: **2 oz, dt_c 10, 1.750 mm.**

Costs of the 2 oz choice, stated honestly:

- JLC supports it as a standard option; `reference/jlc_capabilities.yaml` already
  carried the matching `2layer_2oz` design-rule class. Small per-order adder at
  qty 10, no schedule or capability risk.
- Coarser fab floor: **min trace / clearance 0.1524 mm** (vs 0.127 mm at 1 oz),
  min via drill 0.3 mm, min annular ring 0.15 mm, min copper-to-edge 0.3 mm. The
  board's finest feature is U1's ESSOP-10 at **1 mm pitch** (per the scout's
  package string `ESSOP-10-150mil-1mm`), and after that Q1's SOT-363 at 0.65 mm -
  so the coarser floor costs nothing here. (The power research's "0.5 mm pitch"
  remark about the ESSOP-10 is superseded by the scout's package data; either
  way the conclusion is unchanged.)
- `stackups.yaml` had no 2-layer 2 oz entry until this board; the orchestrator
  added `JLC2313_1.6_2oz` at P1 (derived core 1.6 - 2 x 0.070 = 1.460 mm).

## Board outline

**45 x 25 mm** nominal, single-sided SMT (top) plus three through-hole parts
hand-soldered after economy PCBA (J2, J3, and nothing else).

- The brief's ~40 x 25 mm is a **soft** target with ~20 % allowed (P0 answer 5);
  45 x 25 mm is +12.5 % on the long axis and 1125 mm2 total.
- Why not 40 x 25: J1's body is ~7.3 mm deep from the left edge and J2's ~10 mm
  from the right, leaving only ~23 mm of mid-board at 40 mm length for U1, SW1,
  the 2512 dropper, the window detector and three LEDs plus a readable profile
  table on silk.
  45 mm makes that comfortable without touching the 25 mm height that the two
  connectors set.
- **Hard ceiling 48 x 28 mm** (the +20 % allowance). If P6 closes placement at
  40 x 25 mm, take it - nothing in the architecture depends on the extra 5 mm.
- No mounting holes (bench use, no enclosure, requirements s5). No height limit
  beyond the receptacle and terminal block themselves.
- Dropping the main-path PPTC is what keeps this in the target band at all: the
  8 A radial PPTC that a 5 A commitment would have required is a 24 x 25 mm
  through-hole disc - larger than half the board.
