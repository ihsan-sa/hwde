# P2 Architecture - digest

Adopted connector ICD **rev A2** (`boards/lumina-carrier/architecture/connector-icd.md`)
over the DRAFT-A copy in `brief/`: it adds s6.6 (binding current-limited bank-charging
contract) and s8.4 (carrier guarantees 0 V at J3 when unprogrammed/crashed/reset), and
raises board-wide 48 V outer clearance from 0.60 to 0.635 mm.

- **4 layers, `JLC04161H-3313`.** Forced by thermals, not routing: `check_thermal`'s 2L
  model floors at 55 C/W vs 4L's 45 C/W, and the linear pass FET fails P8 on 2 layers at
  ANY pour size. In1 AND In2 both solid GND - a deliberate override of `planes_gen`'s 4L
  default. Antenna column is voided on all four layers.
- **Four sheets**: conn (ICD boundary), charge (0.20 A hard-limited hot-swap + 2720 uF /
  100 V bank + self-powered bleed), drive (op-amp + 200 mohm shunt + D2PAK planar HEXFET,
  no inductor and no output cap), protect (2x dual comparator on +12V: board OT, LED OT,
  Vds fault latch, bank UVLO + ceiling).
- **Operating point: 38.0 V string at 2.6 A, 39.7 V window floor, bank ceiling 44.5 V
  normal / 48.0 V armed.** 38 V reproduces the ICD's own headline 0.99 J exactly while
  cutting board dissipation 2.33 -> 1.89 W (-19 %). The 44.5 V ceiling is what takes the
  pass FET from 1.03x its P8 allowance to 1.77x margin, at identical light output.
- **Charge limit 0.20 A, not the ICD's 0.25 A ceiling**: 0.25 A is 12.0 W instantaneous
  which, plus the carrier's 2.4 W, exceeds the 12.95 W af class envelope for longer than
  the PSE's 50-75 ms overload timer. Also found: the charge path is a permanently-cycling
  limiter in regulation ~88 % of the time, not a start-up element.
- **LED-short fault decided** (not deferred): ratiometric Vds comparator, drain vs
  0.45 x bank off identical dividers so no voltage reference is needed, ~20 us,
  arming-blanked, latched until ENABLE cycles - plus an NTC in the pass FET's own pour.
  A max-on-time one-shot was rejected as primary: it bounds one pulse, not the repetitive
  9.9 W mean.
- **Emitter re-decided** off the false JLC constraint (the array is off-board, so it is
  not a JLC PCBA line item): single 3S string of >=2.6 A-DC-rated multi-die emitters
  (XHP70.3 12 V class). No parallel paths means no ballast and no Vf binning. P3's
  part-sourcer will not find it on JLC; that is correct and expected.
- **Cost ~$24.50/board at qty 6** (~$14.00 BOM + ~$3 PCB + ~$7.50 Extended setup),
  against the $25 default target. Light engine separate at ~$46-65/fixture.
- Two things carried to H1: **802.3at does not close thermally on this daughter**, and
  **the RJ45 notch cannot be cut by this pipeline**.
