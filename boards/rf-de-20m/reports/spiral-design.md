# rf-de-20m - etched PCB air-core spiral inductors (L301, L302)

Authored 2026-08-08. Generator: `kicad/gen/spirals.py`. Footprints:
`lib/aiee.pretty/SPIRAL_L164N.kicad_mod`, `lib/aiee.pretty/SPIRAL_L110N.kicad_mod`.

Both parts hit their inductance target to better than 0.05 % and clear the
Q >= 130 requirement by ~3x. **Total magnetics dissipation is 4.6 W nominal /
6.4 W on a pessimistic proximity derate**, against the 16.3 W that
`power_tree.md` budgets for the single-layer case and the ~10 W SPIRAL-2
projects. The 200 W operating point is NOT re-derived here - it is frozen.

| | **L301 / L_s** | **L302 / L_m** |
|---|---|---|
| footprint | `aiee:SPIRAL_L164N` | `aiee:SPIRAL_L110N` |
| turns / OD | 3 / **33.10 mm** | 2 / **32.57 mm** |
| trace / gap | 2.5 mm / 1.0 mm | 2.5 mm / 1.0 mm |
| L (method B, as drawn) | **163.99 nH** (target 164, -0.01 %) | **110.03 nH** (target 110, +0.03 %) |
| L (method A, Mohan) | 161.4 nH single-layer, **-13.7 %** vs B | 105.6 nH single-layer, **-16.9 %** vs B |
| R at 20 MHz, 120 C | **53.1 mOhm** | **42.6 mOhm** |
| **Q** | **388** nominal / 279 pessimistic | **325** nominal / 235 pessimistic |
| **dissipation at 6.96 A rms** | **2.57 W** / 3.58 W pessimistic | **2.06 W** / 2.85 W pessimistic |
| plan area | 860 mm2 -> 2.99 mW/mm2 | 833 mm2 -> 2.48 mW/mm2 |
| **SRF** | **400 MHz** (20x f0) | **446 MHz** (22x f0) |
| courtyard | 39.99 x 33.69 mm | 39.46 x 33.16 mm |

---

## 1. Geometry as drawn

Archimedean spiral, outermost point at angle 0 (+x), winding clockwise inwards
in the footprint frame. Both parts share trace/gap because both carry the same
6.96 A rms and obey the same fab rules; only OD and turn count carry the
inductance.

| | L301 | L302 |
|---|---|---|
| outer conductor centreline radius | 15.30 mm | 15.035 mm |
| inner conductor centreline radius | 4.80 mm | 8.035 mm |
| outer copper edge | 16.55 mm | 16.285 mm |
| `d_out` / `d_in` (copper edges) | 33.10 / 7.10 mm | 32.57 / 13.57 mm |
| `d_avg`, fill ratio `rho` | 20.10 mm, 0.647 | 23.07 mm, 0.412 |
| turn mean radii | 13.55 / 10.05 / 6.55 mm | 13.29 / 9.78 mm |
| conductor length (incl. leads) | 198.6 mm | 153.9 mm |
| open centre (no copper) | 7.1 mm dia | 13.6 mm dia |

Terminals: **pad 1 east**, **pad 2 west**, diametrically opposite, which suits
the board's west-to-east signal flow (`/SW` -> L301 -> `TANK_A`, and
`TANK_B` -> L302 -> `RFOUT`). Each terminal land is 2.8 x 8.0 mm with a
**2 x 7 = 14 via** cluster (0.3 mm drill / 0.6 mm pad); a third 7 x 2 = 14 via
cluster sits in the inner land.

---

## 2. Inductance - two independent methods, and they disagree

**Method B (used for the design value): regularised Neumann double integral
over the actual drawn centreline.**
`L = (mu0/4pi) * int int (dl . dl') / sqrt(|dr|^2 + a^2)`, with `a` the
geometric mean distance of the cross-section, `a = 0.2235*(w + t) = 0.5666 mm`
(Rosa). This integrates the real Archimedean path, not a 4-parameter
abstraction. Validated before use:

- circular loop r = 15 mm: Neumann **59.894 nH** vs analytic
  `mu0*r*(ln(8r/a) - 2)` = 59.859 nH -> **+0.06 %**
- coplanar mutual M(15 mm, 11 mm): Neumann **20.965 nH** vs Maxwell's elliptic
  expression = 20.965 nH -> **+0.00 %**

**Method B' (independent cross-check of B): Grover's classical ring model** -
each revolution replaced by a *closed* circular filament at its mean radius,
`L = sum L_i + 2 sum_{i<j} M_ij`, self terms from `mu0 r (ln(8r/a) - 2)` and
mutual terms from Maxwell's elliptic-integral formula. This shares no code path
and no open-path (partial-inductance) assumption with B.

**Method A: Mohan et al. current-sheet expression** (IEEE JSSC 34(10), 1999),
circular coefficients `c1 1.00, c2 2.46, c3 0.00, c4 0.20`,
`L = (mu0 n^2 d_avg c1 / 2)[ln(c2/rho) + c3 rho + c4 rho^2]`, with `d_in` and
`d_out` read off the drawn copper. Wheeler's 1928 flat-spiral formula
`L(uH) = a^2 n^2 / (8a + 11c)` is reported alongside it as a fourth datum.

Single-layer inductance of the drawn geometry:

| | Neumann (B) | Grover rings (B') | Mohan (A) | Wheeler flat |
|---|---|---|---|---|
| L301 | **186.90 nH** | 187.00 nH (+0.06 %) | 161.35 nH (**-13.7 %**) | 160.20 nH (-14.3 %) |
| L302 | **127.07 nH** | 127.59 nH (+0.41 %) | 105.60 nH (**-16.9 %**) | 106.48 nH (-16.2 %) |

**The disagreement exceeds the 15 % flag on L302 and is close to it on L301,
so: stated plainly.** B and B' agree to 0.4 %; A and Wheeler agree with each
other to ~1 %. The split is method-family, not arithmetic:

- B/B' are exact filament electromagnetics, each validated to <0.1 % against a
  closed-form result on a geometry where the closed form is exact.
- A and Wheeler are *empirical fits*. Mohan's coefficients were regressed over
  on-chip spirals; the current-sheet abstraction smears `n` turns into a
  uniform annulus, and it needs `d_in` to mean what its own layout convention
  says (`d_in = d_out - 2nw - 2(n-1)s`, i.e. exactly `n` conductors on a
  radius). **A drawn Archimedean spiral of n revolutions has n+1 conductor
  crossings on a radius**, so its measured `d_in` is one pitch too small and
  `rho` lands at 0.41-0.65 - which is what drives the log term down.

  Fed geometries that *do* match its convention, Mohan reproduces the Grover
  ring model closely, and the agreement improves with turn count exactly as a
  current-sheet model should:

  | `d_out` / w / s / n | rho | Mohan | Grover rings | |
  |---|---|---|---|---|
  | 36 / 3.0 / 1.5 / 2 | 0.263 | 161.09 nH | 157.42 nH | +2.3 % |
  | 33.10 / 2.5 / 1.0 / 3 | 0.403 | 245.89 nH | 239.00 nH | +2.9 % |
  | 40 / 2.0 / 2.0 / **4** | 0.538 | 412.25 nH | 411.38 nH | **+0.2 %** |
  | 30 / 1.0 / 1.0 / **6** | 0.579 | 650.56 nH | 647.51 nH | **+0.5 %** |

  So neither method is broken; **the 14-17 % is a definition mismatch at low
  turn count**, and method B - which integrates the copper that is actually
  drawn - is the one that answers the question being asked.

**Design value = method B.** If A were right instead, both parts land ~14-17 %
low, which the C_s/C_m banks cannot fully trim *upward* (they reach +54 pF,
about +11 %). That is the single largest risk in this design and it is why
**bring-up must measure L before the banks are finalised** - which is exactly
what the four 27 pF DNP trim sites exist for.

---

## 3. F.Cu || B.Cu parallel winding (SPIRAL-2)

Identical plan-view geometry on both outer layers, tied at both terminals, In1
and In2 voided between. Copper-to-copper spacing from `stackup.md`:
1.6542 - 0.035 = **1.619 mm**.

**Inductance.** Two identical coupled coils in parallel give
`L_par = L*(1 + k)/2`. The coupling is **computed, not assumed** - the same
Neumann integrator with an axial offset:

| | k (F.Cu <-> B.Cu) | L single | **L parallel** |
|---|---|---|---|
| L301 | **0.755** | 186.90 nH | **163.99 nH** |
| L302 | **0.732** | 127.07 nH | **110.03 nH** |

k ~0.75, *not* ~0.95: at a 1.62 mm spacing and ~10 mm mean coil radius the two
windings are far from perfectly coupled. Assuming 0.95 would have oversized
both coils by ~9 %.

**Resistance - the parallel benefit is NOT 2x, and here is the model.** Two
co-directed current sheets 1.619 mm apart partially cancel each other's field
in the gap, so current crowds onto the *outer* faces and each winding's
AC resistance rises. For a strip of width w at height z the tangential field is
`H(z) = (I/(pi w)) atan(w/2z)` against an on-surface value `I/2w`, so

    beta = atan(w / 2z) / (pi/2)                      = 0.419  (w 2.5, z 1.619)
    R_parallel / R_single = (1 + beta^2) / 2          = 0.588

i.e. **a 1.70x reduction, not 2x**. The limits are right by inspection:
beta -> 0 (windings far apart) gives exactly 0.5; beta -> 1 (windings touching)
gives 1.0, no benefit at all. This independently lands inside SPIRAL-2's
predicted "Q up 1.6-1.8x".

Current sharing is assumed 50/50, which follows from geometric symmetry: the
two windings are identical and tied at both ends.

---

## 4. AC resistance, Q and dissipation

Copper at **120 C** (the design temperature): `rho = 2.4015e-8 ohm.m`,
sheet resistance **0.6862 mOhm/sq** for 1 oz (0.4926 at 20 C).
Skin depth **14.78 um at 20 C, 17.44 um at 120 C**, so `t/delta = 2.01`.

**Skin factor.** A wide flat trace with no plane under it conducts on *both*
faces, so the correct 1-D result is the slab solution with equal tangential H
on each face:

    R_ac/R_dc = (u/2) * [sinh u + sin u] / [cosh u - cos u],  u = t/delta
              = 1.087   at 35 um / 17.44 um

**This is the number that separates this result from the architecture's
Q ~100-150 planning figure.** A 35 um trace at 20 MHz is barely affected by
skin effect - it is *not* a `t/delta = 2.4` derate - and the trace here is
2.5 mm wide rather than the ~1.5 mm the earlier estimate assumed.

**Proximity / current-crowding derate** is taken from SPIRAL-1: **x1.4
nominal**, with **x2.0** reported as a pessimistic bound (SPIRAL-1 offers
1.3-1.5). This is the least-defensible term in the budget and is quoted as a
range on purpose.

**Inner-terminal bridge.** In1 || In2, 5.0 mm wide (SPIRAL-4 wants >= 4 mm),
0.0152 mm each -> 0.790 mOhm/sq for the pair.

| | winding F||B | bridge | vias | **total** | **Q** | **P** |
|---|---|---|---|---|---|---|
| L301 nominal | 48.72 mOhm | 4.11 (26.0 mm) | 0.23 | **53.06 mOhm** | **388** | **2.57 W** |
| L301 pessimistic | 69.60 | 4.11 | 0.23 | 73.94 | 279 | 3.58 W |
| L302 nominal | 37.77 | 4.58 (29.0 mm) | 0.23 | **42.58 mOhm** | **325** | **2.06 W** |
| L302 pessimistic | 53.96 | 4.58 | 0.23 | 58.77 | 235 | 2.85 W |

Cross-check against the architecture's identity `P = 200*Q_L/Q_ind`:
1000/388 = 2.58 W and 666/325 = 2.05 W. Consistent.

**Single-layer fallback** (if P7 has to drop the B.Cu winding): L301 Q 270 /
4.22 W, L302 Q 232 / 3.34 W nominal; Q 192 / 166 and 5.94 W / 4.67 W
pessimistic. Even that fallback clears Q >= 130.

**Total magnetics: 4.63 W nominal, 6.43 W pessimistic**, against 16.3 W in
`power_tree.md`. Worth ~1.5-3 points of board efficiency - but the loss numbers
downstream should NOT be edited on the strength of this note alone; they should
be edited when a bench measurement confirms the Q.

**Thermal.** SPIRAL-1's rule is copper area >= P / 7 mW.mm-2. L301 needs
367 mm2 and has 860; L302 needs 294 and has 833. Both are ~2.3x clear even on
the pessimistic derate.

**Radiation** is negligible and was checked, not assumed: a 2-3 turn,
33 mm loop at 20 MHz (lambda 15 m) has R_rad ~2e-6 ohm, 4 orders below the
copper loss.

---

## 5. Self-resonance

Inter-turn capacitance from the coplanar-strip conformal map,
`C' = eps0 * eps_eff * K(k')/K(k)` with `k = s/(s+2w)` and `eps_eff = (1+4.3)/2
= 2.65` (half air, half FR4) -> **49.7 pF/m**. For an n-turn coil the potential
difference across each gap is ~V/n, so `C_self = C' * (gap length) / n^2`.
F.Cu-to-B.Cu capacitance contributes nothing: the two windings sit at identical
potential at every point.

| | C_self | **SRF** | L uplift at 20 MHz |
|---|---|---|---|
| L301 | 0.96 pF (incl. 0.3 pF lead) | **400 MHz** = 20x f0 | +0.25 % |
| L302 | 1.16 pF | **446 MHz** = 22x f0 | +0.20 % |

Both are far above 20 MHz; the reactance correction is inside the trim range.

---

## 6. Mutual coupling between the two spirals (SPIRAL-5)

Computed by the same Neumann integrator over both drawn paths, side by side and
coplanar. Same handedness -> negative M; mirroring one part flips the sign.
**L301 and L302 are in the same series chain, so M adds to each and the series
total moves by 2M.**

| centres | edge gap | M | k | series dL of 274 nH |
|---|---|---|---|---|
| **38 mm** (SPIRAL-5 min) | +5.2 mm | **-2.05 nH** | 1.52 % | **-4.09 nH (-1.49 %)** |
| 40 mm | +7.2 mm | -1.67 nH | 1.24 % | -3.34 nH (-1.22 %) |
| 42 mm | +9.2 mm | -1.38 nH | 1.03 % | -2.76 nH (-1.01 %) |
| 45 mm | +12.2 mm | -1.06 nH | 0.79 % | -2.12 nH (-0.77 %) |

This confirms SPIRAL-5's "k ~2 % at ~39 mm" estimate. At the 38 mm minimum the
effect is -1.5 % on the series inductance - inside the trim range, but P8 should
fold the number in rather than ignore it.

---

## 7. Voltage, clearance and temperature

- Across L301: `I * omega * L` = **143.4 V rms / 203 V pk**. Across L302:
  96.2 V rms / 136 V pk. (Matches `LEARNINGS.md`'s 203 V pk figure.)
- **Adjacent turns** differ by roughly one turn's share, ~**68 V pk**, over the
  1.0 mm gap. IPC-2221 B1 (external, uncoated, sea level) wants 0.6 mm in the
  51-150 V band -> **1.0 mm passes with 1.7x margin**.
- **Inner land to the nearest non-contact turn**: 0.736 mm (L301) / 0.741 mm
  (L302), also >= 0.6 mm. This clearance is *invisible to DRC* because the net
  tie exempts pad 1 <-> pad 2, so it is enforced by construction
  (`TURN_CLR = 0.75` in the generator) and measured in this note.
- **West land (pad 2) to the winding (pad 1)**: 2.091 mm on both parts, against
  the 1.25 mm IPC-2221 B1 requires at 203 V pk. This is the real high-voltage
  gap on the part.
- **Via drill to winding copper**: 0.451 mm (L301) / 0.425 mm (L302), against a
  0.25 mm hole-clearance rule.
- Copper runs 100-140 C. **High-Tg FR4 (TG155+) is mandatory** and is an
  order-time option, not a BOM line - `stackup.md` already carries this to P10.
  No clearance value changes with temperature, but 1.0 mm gaps and 2.5 mm
  traces leave the fab class (JLC 0.127 mm min) untouched at any temperature.

---

## 8. How the part is encoded in KiCad 10.0.3

Three format facts were machine-verified before relying on them (see repo
`LEARNINGS.md`, 2026-08-08):

1. **The whole winding is a PAD, never a graphic.** KiCad's connectivity engine
   ignores footprint copper *graphics* (`fp_poly` on a copper layer): they plot
   to Gerber but every pad they touch is still reported `unconnected_items`,
   and without a net tie they also raise `shorting_items` against "no net".
   So the spiral is a **custom-shaped SMD pad** (one on F.Cu, one on B.Cu), the
   terminal/inner lands are rect pads, and the In1+In2 bridge is a rect pad.
2. **`(net_tie_pad_groups "1, 2")`.** An inductor *is* a DC short between its
   terminals; a net tie is the correct - and only - KiCad-native encoding.
   Verified that pads of different numbers may overlap inside a tie with no
   `shorting_items` violation.
3. **Footprint-level rule areas work.** Each part carries two, out to a
   20.5 mm radius: no copper pour on F.Cu/B.Cu, and no tracks, vias or pour on
   In1.Cu/In2.Cu. The "a plane under a spiral is a shorted turn" rule therefore
   travels with the part instead of depending on P6/P7 remembering it.

**One deliberate DRC warning per part**: `padstack - Padstack is questionable
(SMD pad has no outer layers)`, from the inner-layer-only bridge pad. It is
intentional and must be waived at P7. Scratch-board DRC (both parts, nets
assigned, at the SPIRAL-5 38 mm spacing) is otherwise **0 errors**: no
clearance, hole-clearance, courtyard, silk, shorting or unconnected items.

---

## 9. Assumptions, and what could still be wrong

1. **Method A vs B, 14-17 %.** Argued in s2; B is taken. **Highest-impact
   open item** - measure L on the first article before committing the banks.
2. **Proximity derate 1.4x** (SPIRAL-1's 1.3-1.5). 2.0x is carried as a
   pessimistic column throughout. Not independently modelled.
3. **`(1 + beta^2)/2` for the F||B pair** is a 1-D surface-impedance argument
   and assumes 50/50 current sharing. It is a model, not a measurement.
4. **eps_eff = 2.65** for the inter-turn capacitance (half air, half FR4).
   SRF is 20x f0, so even a 2x error here does not matter.
5. **The inner via land crosses the coil centre** (10.0 x 2.5 mm), where axial
   flux is highest. Bounded estimate: **~-1 % on L and <= 0.15 W** of induced
   loss. Not included in the tables above. A solid *disc* there would have been
   ~-2.7 % and ~40 mW; the narrow bar was chosen to keep this small. Unverified
   analytically beyond the bound.
6. **Copper at 120 C** for every resistance. At 20 C every R falls ~28 % and
   every Q rises correspondingly - the quoted numbers are the hot, pessimistic
   end.
7. **Terminal and lead resistance beyond the modelled 26/29 mm of bridge** is
   not itemised; it is small but non-zero.
8. **Courtyard 39.99 mm** (L301) fits zone B's 40 mm width with ~0.01 mm to
   spare, **in the E-W orientation only**. Rotating either part 90 deg needs
   2 x 40 mm of the 80 mm y budget and will not fit. If P6 wants any placement
   slack at all, grow the board ~4 mm in x - which `blocks.md` s3 already
   pre-authorises ("grow the board ... not shrink a spiral").
9. **`check_current` cannot see this copper** - the winding is pads, not
   tracks. Its 6.96 A rating is established here, not by the P8 gate.

## 10. Reproduce

    .venv/Scripts/python boards/rf-de-20m/kicad/gen/spirals.py   # footprints
    .venv/Scripts/python boards/rf-de-20m/kicad/gen/root.py      # schematic
