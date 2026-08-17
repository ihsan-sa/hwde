# bb-amp - stackup (P2)

## Choice

**`JLC2313_1.6`** - JLCPCB standard 2-layer, 1.6 mm, 1 oz outer copper, HASL.
`available: true` in `reference/stackups.yaml` (vendor_page provenance,
verified 2026-08-06); it is also that file's declared default for a 2-layer
board. Fab class: **2L**, standard process, no controlled impedance, no
impedance template, no extra cost class.

```
F.Cu        0.035 mm  1 oz   - all components, all signal routing
dielectric  1.530 mm  FR4 core, er 4.5 (assumed)
B.Cu        0.035 mm  1 oz   - one unbroken GND pour, no signals
```

## Why two layers - the ground-reference argument

The "fewest layers the block honestly needs" default is not a cost decision
here; it follows from what a reference plane is being asked to do on this
board.

**What the reference has to do.** The one CMRR-relevant layout mechanism on
this board is path symmetry at the in-amp inputs (`blocks.md` section 5, from
refdesign L1/L3 and the AD8226 Layout section: unequal frequency response
between the + and - input paths converts common mode into differential).
That requires a *continuous, unslotted* conductor beneath the input pair so
both traces see the same distributed capacitance to the same return, plus a
low-impedance return from each decoupling cap back to its supply pin. A
single solid B.Cu pour delivers exactly that. What it must NOT have is a
split, a slot, or a via field punched through it under the input pair - which
is a placement and routing rule, not a layer-count rule.

**What a reference plane is NOT being asked to do here.** There is no
controlled impedance anywhere: the fastest edge on this board is a 1 kHz
signal band with a 41 kHz amplifier corner, so the shortest wavelength of
interest is kilometres and every trace is electrically a lumped wire.
`stackups.yaml` records that JLC sells no impedance-controlled 2-layer
product at all (the API returns zero templates for stencilLayer=2) - and
nothing on this board would use one. There is no return-path discontinuity to
manage, no plane-to-plane cavity to worry about, no digital aggressor, and no
current worth a power plane (0.65 mA total, `power_tree.md`).

**What 4 layers would buy: nothing measurable.** A JLC04161H-1080B stack
would add a dedicated In1 GND and an In2 power plane. In1 would duplicate a
job B.Cu already does perfectly for a 14-part, DC-to-1 kHz chain; In2 would
distribute a rail carrying 0.65 mA. The only real change would be moving the
GND reference from 1.53 mm below the signal layer to 0.24 mm below it, which
tightens loop area for currents this board does not have. It would also cost
a fab class, an impedance-template decision the design does not need, and -
because the third and fourth copper layers are unused - would make the board
harder to probe on a bench, which is the entire point of this board.

**Ruling: 2 layers.** The mechanism that decides it is that the ground
reference here must be *continuous*, not *close*; continuity is a pour
property, not a layer-count property.

## Consequences the later phases must honour

- `planes_gen` default for 2 layers (B.Cu GND pour) is correct, so
  `constraints.json` declares no `planes` override.
- All parts on F.Cu (`placement.sides` pins U1, U2, J1, J2, J3 to the front):
  single-sided top assembly is a requirements section 7 constraint, and every
  part moved to the back would cut a hole in the reference this stackup
  depends on.
- Routing on F.Cu only where it can be avoided on B.Cu; any B.Cu segment that
  must exist has to route *around* the input-pair corridor rather than under
  it, and `check_return_path` has nothing declared to enforce that - it is a
  P7 reviewer item.
- 1 oz copper, HASL, soldermask, no conformal coating (`coating: soldermask`
  in `constraints.json`, matching requirements section 4).
