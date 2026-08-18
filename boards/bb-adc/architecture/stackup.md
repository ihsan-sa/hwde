# stackup.md - bb-adc

## Chosen: `JLC2313_1.6`

2 layers, 1.6 mm, 1 oz outer copper, HASL, FR4. From
`reference/stackups.yaml`, `available: true`, `live_verified: false`
(vendor_page provenance - JLC returns ZERO impedance templates for
`stencilLayer=2` at either copper weight, because it sells no
impedance-controlled 2-layer product, so there is nothing to read back). It is
also `defaults[2]`, so `board_init` picks it without an override.

```
F.Cu          0.035 mm  1 oz   - every track, every part, the guard ring
dielectric 1  1.530 mm  FR4 core, er 4.5 (ASSUMED - the API returns no er)
B.Cu          0.035 mm  1 oz   - ONE unbroken GND pour, nothing else
```

## Why two layers, and what the analog return actually needs

The honest question at `block-only` is not "is two enough to route" - with 18
electrical parts it obviously is - but **"can an honest analog return and a
guarded high-impedance node be had on two?"** Section 5 of `requirements.md`
allows four if they cannot. They can, and the reason is that this board's
assembly rule hands the whole bottom side to the return:

1. **Single-sided SMT assembly (mode default, requirements s7) reserves B.Cu
   entirely.** No SMT part, no pad, no bottom-side track. So B.Cu is a
   continuous, unbroken GND pour under the whole board - which is exactly, and
   literally, what constraint D1 demands: no B.Cu track, slot or keepout may
   cross the analog region. A four-layer board would give the same unbroken
   reference and nothing more, because the second inner plane would have to be
   `+3V3` and this board's only rail carries 11 mA into three decoupled pins.
2. **Nothing needs controlled impedance.** The only fast nets are three SPI
   lines run at fDCLOCK <= 500 kHz with ~5 ns CMOS edges. A 5 ns edge has a
   ~100 MHz knee; a quarter-wavelength in FR4 at 100 MHz is ~380 mm, so on a
   board of this size the SPI nets are lumped by two orders of magnitude. There
   is no transmission line here to control, and `JLC2313_1.6` publishes
   `controlled_impedance: []` for exactly that reason.
3. **The guard ring wants to be on the SAME layer as the node it guards.** The
   leakage this board fears is SURFACE leakage - no-clean flux residue, dust
   and humidity across a solder-mask surface, and JLC does not wash boards. The
   fix is a ring of `/AIN_BUF` copper on F.Cu encircling the `/AIN_DIV` trace
   and the buffer's + input pad, which intercepts the surface path before it
   reaches the node. **Bulk leakage through the dielectric to the GND pour
   underneath is not a competing path and was checked, not assumed:** FR4's
   volume resistivity (>=1e14 ohm-cm) through 1.53 mm under a ~5 mm^2 trace is
   >=3e14 ohm, versus the ~1e9 ohm surface path the guard exists to break -
   five orders of magnitude apart. So a solid GND pour directly beneath the
   240 kohm node is harmless, and it is positively useful: it shields the node
   from the D2 coupling paths and adds only ~1.2 pF (tau = 0.3 us into
   240 kohm, irrelevant at DC).
4. **Thermal: nothing.** 36 mW whole-board. No copper is being asked to move
   heat.
5. **Cost and fab class.** The cheapest class JLC sells: 2 layers, 1.6 mm,
   1 oz, HASL, no impedance control, no blind or buried vias, no controlled
   dielectric. `check_creepage` is a clean no-op (5 V is the highest potential
   on any net).

**1 oz, not 2 oz.** The largest current on the board is 11 mA declared; IPC-2152
width at that current is a hairline. `JLC2313_1.6_2oz` exists and is available,
but 2 oz buys nothing here and costs money and etch tolerance.

**What would have forced four layers, and did not happen:** a rail that needed
a plane of its own; a differential or controlled-impedance interface; a part
that could not be routed without a bottom-side jumper crossing the analog
region (which is why blocks.md s6 lists "generous enough that F.Cu carries
every track" as an outline REQUIREMENT - if P6/P7 discovers it cannot, that is
a real trigger to revisit this choice, not a routing workaround).

## Consequences that P5/P7 inherit

- `board_init` writes this stackup by name. Geometry is an OUTPUT under the
  `canonical` binding, so P5 runs `board_init --outline auto` and a fixed
  `--outline WxH` is REFUSED. That refusal is correct.
- `planes_gen` gets the 2-layer default it would pick anyway - a B.Cu `GND`
  pour - and `constraints.json` declares it explicitly so nobody has to infer
  it. If `board_edit --outline fit` GROWS the board at P6 close, re-run
  `planes_gen` (a zone outline does not follow the edge outward).
- `rules_gen` emits no impedance rules: no `impedance_ohm` is declared
  anywhere, which is deliberate, not an omission.
- **Re-verify before ordering.** The offering churns - `JLC04161H-7628G` was
  live on 2026-07-30 and gone by 2026-08-06, and `JLC04161H-3313` never existed
  at all. This entry is `vendor_page` provenance verified 2026-08-06; the
  pipeline stops at P9 so nothing is ordered from it, but P10 (if it ever runs)
  re-probes.
