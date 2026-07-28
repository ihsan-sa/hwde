# stm32-blinky - stackup selection

## Chosen: `JLC2313_1.6` (board class: 2-layer)

JLCPCB standard 2-layer, 1.6 mm FR4, 1 oz outer copper, HASL - the
`stackups.yaml` default for 2 copper layers. board_init emits its (stackup)
block verbatim.

## Why 2 layers (the drivers, none of which push to 4)

- Impedance control: none needed. Fastest activity is the 8 MHz crystal loop
  (handled as a short guarded route with GND reference, not a transmission
  line) and SWD at a few MHz over ~20 mm. The 2-layer stack offers no
  controlled-impedance profiles anyway (no adjacent reference plane - see
  stackups.yaml note); nothing on this board wants one.
- Plane needs: a single B.Cu GND pour (planes_gen 2-layer default) gives the
  oscillator and decoupling loops their return. One 3.3 V rail at ~50 mA
  routes as ordinary traces.
- Density: 18 parts on ~35 x 30 mm, one LQFP-48. Trivial for 2 layers.
- Cost: brief states 2-layer + economy PCBA; 4-layer would roughly double the
  fab line item for zero technical gain.

## Board size

Target outline 35 x 30 mm (estimate for cost/fit; final at P6 placement).
Hard limit 50 x 40 mm per requirements. Single-sided top assembly; the two
THT headers may ship loose for hand-soldering (requirements sec 7).

## Fab class summary (for the checkpoint cost picture)

2-layer economy, <= 50 x 40 mm, HASL, 1 oz, qty 5 assembled: PCB ~$2-4 total;
economy SMT assembly + one Extended-part fee (STM32) ~$15-20; BOM ~$2.5-3.0
per board (STM32 ~$2 dominates). Ballpark order total $35-50 before shipping.
Real numbers at P10 order_quote.
