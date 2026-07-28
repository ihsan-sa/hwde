# usb-buck - stackup selection

## Chosen: `JLC04161H-3313` (board class: 4-layer, 1.6 mm)

JLCPCB standard impedance-controlled 4-layer stack, 1.6 mm FR4, 1 oz outer /
0.5 oz inner copper, HASL - the `stackups.yaml` default for 4 copper layers.
board_init emits its `(stackup)` block verbatim.

```
F.Cu    1 oz    signals: USB pair, buck hot loop, MCU fanout
  prepreg 0.2104 mm, FR4 7628, er 4.05   <- the microstrip dielectric
In1.Cu  0.5 oz  SOLID GND plane          <- reference for every F.Cu signal
  core    1.065  mm, FR4, er 4.6
In2.Cu  0.5 oz  +3V3 plane               <- dominant power net (see below)
  prepreg 0.2104 mm, FR4 7628, er 4.05
B.Cu    1 oz    signals / spillover routing
```

## Why 4 layers

- **USB 90 ohm differential needs an adjacent reference plane.** The
  `diff_90` profile on this stack is w 0.314 mm / gap 0.210 mm (edge-to-edge),
  0.524 mm centre-to-centre - routable, and free: it is a published JLC
  profile, not a special order. On a 2-layer board 90 ohm is unachievable
  (no adjacent plane) and the honest move would be to drop the target
  entirely.
- **Return path.** A solid In1 GND plane directly under the whole USB pair is
  the single highest-value SI decision on this board - more so than the
  impedance number, because at FS (t_rise 4 ns, ~115 mm critical length vs a
  20-40 mm run) the pair is electrically short but its return current still
  has to go somewhere clean.
- **The 1.1 MHz buck.** In1 GND under the switch node and input loop contains
  the noise locally instead of letting it wander across a 2-layer pour.
- **PDN.** In2 as a +3V3 plane gives the MCU's transient demand and the USB
  transceiver a low-impedance rail with no routing effort.
- **Cost.** jlc_pricing.yaml: 4-layer at qty 10 is $9.90 vs $2.00 for
  2-layer - $8 total on a prototype run. Not a reason to compromise the pair.

## Planes (defaults are correct - no `planes` key in constraints.json)

planes_gen's 4-layer default is In1 = GND + In2 = dominant power net, where
"dominant" = the net with the most pads among the `power` constraint entries.
**In2 carries `+3V3`**: it has ~20 pads (3 x VDD, VDDA, VBAT, 8 decoupling
caps, 2 output caps, R1, R2, R4, J2.1) against VBUS's ~5 (J1.1, C1, C2,
U2.VIN, U3 VBUS pin). The default therefore lands on exactly the intended
plan, so `constraints.json` deliberately omits the `planes` key. Both
`high_speed` reference nets are GND, which additionally guarantees the In1
pour.

Consequence for routing: **the USB pair belongs on F.Cu**, referenced to In1
GND. A B.Cu run would reference In2 (+3V3), and check_return_path will flag
it - that is intended, not a false positive.

## Controlled impedance: use the geometry, do NOT order the service

FS USB does not require controlled impedance (AN11392 3.2 is explicit: "for
full-speed USB, it is not critical"). We adopt the `diff_90` geometry because
it costs nothing and buys cable-match/EMI margin, but the board is ordered as
a **standard 4-layer**, not as JLC's impedance-controlled option. Nothing
downstream depends on a measured impedance.

VERIFY-LATER V12 still applies if that ever changes: `stackups.yaml`
impedance geometry is computed by `lib/impedance.py` (IPC-2141A microstrip),
not transcribed from JLC's calculator - confirm against JLC's calculator
before ordering a genuinely impedance-controlled board.

## Board size and assembly class

- Target outline **40 x 30 mm** (estimate for cost/fit; final at P6
  placement). Hard limit 55 x 45 mm per requirements. ~28 components with one
  LQFP-48 and a micro-B receptacle; component-courtyard area is ~330 mm2, so
  40 x 30 = 1200 mm2 is a comfortable ~27% density.
- Well inside JLC's 100 x 100 mm promo tier, so the headline price holds.
- **Single-sided top SMT assembly**, JLCPCB economy tier. The 1x4 SWD header
  is THT and ships loose for hand-soldering (economy tier is SMT-only; the
  brief permits hand-solderable connectors). P3 must pick a micro-B
  receptacle JLC can machine-place; if only THT-legged variants are in stock,
  it ships loose too.
- No mounting holes, no height limit (P0 answer 2).

## Fab class summary (checkpoint cost picture, ESTIMATE)

| Line | Estimate | Basis |
|---|---|---|
| PCB, 4-layer, 40 x 30 mm, HASL, qty 10 | $9.90 | jlc_pricing base 4L @ 10 |
| Assembly setup + stencil | $16.00 | $8 + $8 |
| Extended-part feeders | $9-12 | ~3-4 Extended parts x $3 (STM32, AP63203, micro-B, TVS - P3 confirms which are Basic) |
| Solder joints, ~120/board x 10 | $2.00 | $0.0017/joint |
| BOM | $25-35 | $2.50-3.50/board, STM32 ~$1.5-2.5 of it |
| **Total, qty 10** | **~$62-75** | **~$6-8 per board**, dominated by one-time fees |

Estimate only - real numbers at P10 `order_quote`, which always emits the
instant-quote deep link as the authoritative path.
