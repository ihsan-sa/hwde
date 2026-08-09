# rf-term-150w - P2 architecture decisions

Eight new decisions (D1-D8). The twelve P0/P1 orchestrator decisions in `state.json` are
DECIDED and are not re-litigated here; where the real geometry confirms one, the confirming
number is recorded, and where it breaks one, it is escalated in `blocks.md` s8, not designed
around.

## Confirmed, with the number that confirms it

| Decided item | Status | Confirming number |
|---|---|---|
| 0.80 mm board-wide clearance | **holds** | J1's own vendor land pattern gaps 0.963 mm - passes with 0.163 mm spare. `check_creepage` row A6 at 101-150 V = 0.80 mm exactly. |
| JLC2313_1.6, no controlled impedance | **holds** | launch is 0.0017 lambda = 0.63 deg. Z0 is meaningless; wide+low-Z is strictly better. |
| >= 250 W element | **holds** | 250 W part -> 120 C allowed flange at 150 W -> 0.633 C/W total, a real heatsink. A 150 W part needs 0 C/W. |
| residual X <= 5.0 ohm | **holds, 4.6x inside** | estimated 6.9 nH = 1.09 ohm. |
| R_eff = R + X^2/R is the real limit | **holds** | at the +5% corner R_eff = 52.52 -> RL 32.2 dB, 6.2 dB of margin. Failure needs X > 12.1 ohm = 77 nH. |
| shunt trimmer at the port end | **holds** | tap position is worth < 0.01 dB at 1.09 ohm, so P6 has freedom; but see D6. |
| off-board resistor, no notch, 1.0 mm shims | **holds** | 2.667 - 2.635 = 0.032 mm nominal gap; the tab absorbs +/-0.2 mm of stack tolerance at 1.4 N (k = 6.8 N/mm). |
| 3 board_only holes, 6 footprints total | **holds** | J1+R1+C1+H1..H3 = 6 exactly; BOM 3 lines, CPL 3 placements. |
| Rth 0.633 C/W total, 0.42 C/W heatsink | **re-derived, exact** | every one of the six figures reproduces to the digit (`blocks.md` s6.2). |
| select-on-test for +/-2% DC | **holds and is the load-bearing one** | it buys 7.7 dB of RL (32.2 -> 39.9). The entire launch inductance costs 0.02 dB. |
| BeO ship, AlN drop-in | **holds** | no geometry impact - one footprint serves both. |
| BFC280811339 trimmer kept | **AT RISK** | -40..+70 C rating vs a ~72-88 C board. Escalated: `blocks.md` s8 OPEN-1. |

---

## D1 - Board outline fixed at 24.0 x 16.0 mm

**What.** 24.0 x 16.0 mm, 384 mm^2 = 43% of the 30 x 30 HARD cap, both axes inside it.

**Why.** The 16.0 mm axis is fully determined: 4.2 (J1 pin inset, from the footprint's
3.65 mm copper half-extent + JLC's 0.30 mm edge rule) + 4.7 (R1 pad, floor 4.42 - see D2) +
6.6 (lap pad, see D3) + 0.5 (edge) = 16.0. The 24.0 mm axis is set by the trimmer's dia
7.5 mm body on one side (12.65 mm minimum from the RF axis) and by the M3 screw-head keepout
on the other (8.35 mm minimum: 2.2 pad + 0.80 HV clearance + 2.75 head radius + 2.6
hole-to-edge). True minimum is ~21.0 x 15.0. **The extra 3 x 1 mm is deliberate packing
margin and is the one number in this design not driven to its limit** - the outline is
unrecoverable after P5, JLC prices any 2-layer board flat below 100 x 100 mm, and P6 has to
fit three 7.1 mm keepouts, a dia 7.5 mm body and a 4.4 mm RF spine into it. Buying P6 freedom
for zero dollars and zero picohenries is the right trade; it is called out rather than buried.

## D2 - The launch length is 4.7 mm and its floor is 4.42 mm, set by clearance not by size

**What.** J1 centre pin to the near edge of R1's lap pad = 4.7 mm; nothing shorter is legal.

**Why.** The lap pad is on the RF net at 122.5 Vpeak and must clear J1's own ground pads by
0.80 mm: `sqrt((d-2.55)^2 + 0.35^2) >= 1.90` gives `d >= 4.417 mm`. **Shrinking the board
cannot shorten the launch** - which is why D1 does not chase the last millimetre. Two
corollaries recorded so nobody rediscovers them: rot 0 (RF exiting between two ground pads)
is optimal, and rotating J1 45 deg pushes the floor to 5.5 mm. Relaxing the board clearance
to the masked-trace row B4 (0.40 mm) would buy 0.9 mm and ~0.4 nH = 0.06 ohm - not worth
reopening a settled decision.

## D3 - Lap pad 4.4 x 6.6 mm, and the "3-5 mm overlap" premise is retired

**What.** Pad 1 of R1 is 4.4 mm wide x 6.6 mm long, 0.5 mm from the board edge; the flange
sits 0.5 mm beyond that.

**Why.** The tab is dimensioned `.125 [3.18] Min.` with **no maximum**. After the mandatory
0.5 mm flange gap (the board bottom is at 1.000 mm and the flange top at 1.575 mm, so they
physically interfere if they overlap in plan) and 0.5 mm of edge clearance, the *guaranteed*
lap is **2.18 mm**, not the 3-5 mm the brief assumed. That is still a sound joint - 6.6 mm^2
of lap solder carrying 1.732 Arms with a compliant tab taking essentially no load - so this
is a premise break, not a design break. The 6.6 mm pad exists so the *actual* lead (drawn
~9 mm) can be trimmed to a comfortable 4-5 mm lap. **Incoming inspection must measure the
lead.** Escalated as `blocks.md` s8 OPEN-2.

## D4 - The launch is deliberately a LOW-impedance line, not 50 ohm

**What.** 4.4 mm (Z0 34 ohm) wherever clearance allows, necking to 1.1 mm only for the
2.5 mm it spends between J1's ground pads. `constraints.json.high_speed` carries **no**
`impedance_ohm`.

**Why.** At 0.0017 lambda the structure is lumped, so the only figure of merit is
`L' = Z0*sqrt(eps_eff)/c`, which falls monotonically with width: 0.489 nH/mm at 1.1 mm,
0.303 at 2.83 mm ("50 ohm"), 0.211 at 4.4 mm. A 50 ohm launch would be **30% more inductive
per mm** than the one built. The extra shunt C lands mostly at the resistor end where it is
nearly free, and the trimmer absorbs the port-end share. Two traps closed: `rules_gen` only
solves impedance for differential pairs, so a declared single-ended `impedance_ohm` would
look real and do nothing; and this is the concrete reason the brief's "no controlled
impedance" constraint costs exactly zero.

## D5 - Two soldered copper ground straps bond the R1 flange to the F.Cu lands

**What.** R1's custom footprint gets pad 2 as **two** F.Cu SMD lands (3.5 x 2.0 mm) flanking
the lap pad, reaching out to +/-6.5 mm off the tab axis. Two 0.3 mm copper shim straps,
~3 mm long x 4 mm wide, are soldered from the flange top face (1.575 mm) up to those lands
(2.635 mm). Assembly order: strap-to-flange first while the flange is loose, then bolt the
resistor down, then set the PCB on its shims and solder the tab and the strap free ends.

**Why - this is the gap in the decided architecture and it is half the RF loop.** The
decisions cover the signal tab and are silent on how GND reaches the element's cold end. The
tempting answer - let the bolted flange-to-heatsink joint carry it - is quantifiably unsafe:
2.359 cm^2 of flange through 25 um of grease at er 5 is a **418 pF capacitor = 15.2 ohm at
25 MHz** if the sink is anodised and there is no asperity contact, plus a ~60 mm^2 detour
loop worth 15-25 nH. That is a ~10 dB board whose performance depends on a finish the user
chooses. The straps replace it with ~0.3 nH of well-defined return. Constraint that sizes
them: the element block covers the flange's central 9.525 mm, so exposed flange top starts
**4.76 mm** either side of the tab - the lands must reach past that, which is what forces the
strap/screw side of the board to 7.0 mm minimum (D1).

## D6 - C1's ROTOR goes to GND, its stator to RF

**What.** Binding on P3 pin mapping and P4 net assignment.

**Why.** requirements s8 F1: the operator turns the trimmer with a hand tool at 122.5 Vpeak
while transmitting - that is the intended use case, not a fault. The rotor is the terminal
mechanically continuous with the adjustment screw, so grounding it puts the touched metal at
ground potential. Stated fallback if the part does not distinguish the terminals: insulated
tuning tool + a README instruction to tune at reduced drive, **declared explicitly** rather
than picked silently.

## D7 - Both copper layers are GND pours

**What.** `planes: [{B.Cu, GND}, {F.Cu, GND}]`, overriding `planes_gen`'s 2-layer default of
B.Cu only. Plus GND stitching vias at the bottom edge flanking the lap pad, inside the
2.0 mm `return_via_radius_mm`.

**Why.** B.Cu is the microstrip return under the launch and is what makes L' 0.21-0.49 nH/mm
instead of ~0.8 nH/mm for a wire - it is the reason the budget closes at 6.9 nH against
31.9 nH. F.Cu is poured so the flange-bond lands and the C1 return exist without adding a
footprint (the placement budget is exactly full at 6). The stitching vias carry the return
where it has to transfer B.Cu -> F.Cu -> straps; that transition is term E of the budget and
is the least certain number in it.

## D8 - `thermal` is deliberately absent from constraints.json

**What.** No `thermal` key, despite a 150 W part on the board.

**Why.** A4 puts the entire 150 W through the flange to the user's heatsink, off-board.
Declaring `{"ref": "R1", "power_w": 150}` would make `check_thermal` demand thermal vias and
copper area for heat that never enters FR4, and `place_anneal`'s spreading term would fight
the edge placement the design requires. The board dissipates **< 0.25 W** in total
(`power_tree.md` s2). The real thermal risk on this board runs the other way - heat flowing
*into* the PCB from an 88 C heatsink base - and no schema key expresses that; it is escalated
as `blocks.md` s8 OPEN-1 instead.
