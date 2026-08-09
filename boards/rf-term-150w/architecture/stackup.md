# rf-term-150w - stackup

## Chosen: JLC2313_1.6 (2 layer, 1.6 mm, 1 oz outer, HASL)

Selected by name from `reference/stackups.yaml` (`available: true`, `layers: 2`,
`copper_finish: HASL`, `dielectric_constraints: false`, `controlled_impedance: []`).
It is the file's own `default` for 2-layer and the only non-upcharge 2-layer stack modelled.

| Layer | Type | Thickness | Notes |
|---|---|---|---|
| F.Cu | copper | 0.035 mm (1 oz) | RF launch, trimmer, flange-bond lands, GND pour |
| dielectric 1 | FR4 core | 1.530 mm | er 4.5 **assumed** (`epsilon_r_assumed: true`), tan-d 0.02 |
| B.Cu | copper | 0.035 mm (1 oz) | solid GND pour, the microstrip return |
| **total** | | **1.600 mm** | |

`epsilon_r_assumed: true` matters here only for the L'/C' table in `blocks.md` s4; at
25 MHz an er error of +/-10% moves the launch inductance by ~5% of 6.9 nH = 0.35 nH, which
is 0.05 ohm. Not load-bearing.

## Why 2 layers, and why controlled impedance costs nothing

**2 layers is a HARD brief constraint** (requirements s5, crit. 11) and it is also the
right answer on the merits:

- 6 footprints, 2 nets. There is no density driver.
- One reference plane is enough: B.Cu is a solid GND pour and is the microstrip return for
  the entire RF launch. A 4-layer stack would add a second plane with nothing to reference.
- **The board is electrically tiny.** Free-space lambda at 25 MHz is 12 m; in FR4 microstrip
  (eps_eff ~ 3.2-3.5) it is ~6.6 m. The 11.5 mm launch is **0.0017 lambda = 0.63 degrees**.
  Transmission-line behaviour does not exist at this scale - the launch is a lumped series
  inductance with a little shunt capacitance, and the trimmer's whole job is to cancel it.

That is why the brief's "no controlled-impedance service" costs literally nothing, and JLC
sells no impedance-controlled 2-layer product anyway (`stackups.yaml` provenance:
`getImpedanceTemplateSettingList` returns 0 templates for `stencilLayer=2` at both 1 oz and
2 oz, live-verified 2026-08-06). `controlled_impedance: []` in the stackup entry is the
correct, honest empty list, not a gap.

**Consequence for P5:** do NOT ask `rules_gen` to solve a 50 ohm single-ended width on this
board. `constraints.json.high_speed` deliberately omits `impedance_ohm` - `rules_gen` only
solves impedance for differential pairs, so a lone single-ended target would look declared
and silently do nothing (LEARNINGS, rf-de-20m `constraints.json`). And it would be the wrong
target anyway: see below.

## The launch is deliberately a LOW-impedance line

Because the structure is lumped, series inductance is the only thing that matters and

    L' = Z0 * sqrt(eps_eff) / c

falls monotonically as the trace gets wider. On this stackup:

| w (mm) | Z0 (ohm) | L' (nH/mm) |
|---|---|---|
| 1.1 (neck between J1's ground pads) | 82.4 | 0.489 |
| 2.83 ("50 ohm") | 49.4 | 0.303 |
| 4.4 (R1 lap pad) | 33.8 | 0.211 |

The 4.4 mm lap pad therefore carries **30% less inductance per mm than a 50 ohm line would**.
The extra shunt capacitance it brings (0.176 pF/mm) lands at the resistor end where it is
nearly free, and the trimmer absorbs the port-end share. Full budget in `blocks.md` s4.

## 1 oz copper, HASL - both confirmed against the physics

- **1 oz (35 um) at 25 MHz is 2.7 skin depths** (skin depth in Cu at 25 MHz = 13.1 um). More
  copper buys almost nothing above ~2 skin depths, and 2 oz is an upcharge the brief forbids.
  AC/DC resistance factor ~2.5; the whole launch is ~3.3 mohm, i.e. 10 mW at 1.732 Arms.
- **HASL is the free finish and drives the creepage row.** Exposed HASL lands take IPC-2221
  row **A6** (external component lead/termination, uncoated) = **0.80 mm** in the 101-150 V
  band; masked traces take row **B4** = 0.40 mm. Machine-checked against
  `check_creepage.py`'s `ROW_TABLE`: `A6[101-150 V] = 0.80`, `B4[101-150 V] = 0.40`,
  `B2[101-150 V] = 0.60`. The board-wide 0.80 mm clearance covers the strictest row for every
  item type, so no per-item adjudication is needed anywhere on this board.
  `constraints.json` declares `"coating": "soldermask"` - the physically correct statement
  for an LPI-masked board, and the one that stops `check_creepage` over-reporting traces at
  row B2 (LEARNINGS 2026-07-29 [check_creepage][gates][ipc]).

**Derived-copper-weight gotcha (LEARNINGS 2026-07-29):** `derive_copper_oz` scans this file
for a line starting with `## Chosen`. Line 3 above is exactly that, and names the stackup, so
the 1 oz derivation resolves from the stackup entry rather than silently defaulting.

## Planes

`constraints.json.planes` declares **both** copper layers as GND pours, overriding
`planes_gen`'s 2-layer default (which pours B.Cu only):

| Layer | Net | Why |
|---|---|---|
| B.Cu | GND | the microstrip return directly under the launch - this is what makes L' = 0.2-0.5 nH/mm instead of ~0.8 nH/mm for a wire |
| F.Cu | GND | (a) provides the flange ground-bond lands at the R1 end without adding a footprint, (b) gives the C1 shunt return a short path back to J1's ground legs, (c) tightens the launch slightly by coplanar coupling |

The F.Cu pour keeps 0.80 mm from every RF item via the `aiee_hv_*` DRU rule that `rules_gen`
emits from `voltages` - never hand-author that rule. A ring of GND stitching vias at the
bottom edge, flanking the R1 lap pad, ties the two pours where the return current has to
transfer from B.Cu up to F.Cu and out through the flange straps; that transition is inside
term E of the inductance budget (`blocks.md` s4.2) and is the reason
`high_speed[0].return_via_radius_mm = 2.0` is declared.

## Mechanical stack (not the fab stackup, but it binds P6 and the README)

Heights above the heatsink mounting plane:

    0.000  flange bottom / heatsink face      1.000  PCB bottom (on 3x 1.0 mm shims)
    1.575  flange top                         2.600  PCB top (FR4)
    2.667  R1 tab underside   <-------------  2.635  PCB top copper     gap 0.032 mm
    2.794  R1 tab top                         3.556  R1 element top

The 1.0 mm shim washers exist solely to bring the top copper up to the tab. Full tolerance
argument (why 0.032 mm nominal is honest and not false precision) in `blocks.md` s2.3.
**P6 must not change the board thickness** - 1.6 mm is load-bearing mechanically, not just a
fab default.
