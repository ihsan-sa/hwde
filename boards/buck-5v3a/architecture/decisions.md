# buck-5v3a - P2 decisions, rejections, open items, and the P8 sim plan

For the orchestrator to log. Derivations live in `blocks.md`, `power_tree.md`,
`stackup.md`; this file is the decision record.

---

## D1 - STACKUP: 4 layers, `JLC04162H-7628A`, 2 oz outer / 0.5 oz inner, 1.6 mm

**4 layers are required.** Machine-verified with the repo's own `check_thermal.py`
against a synthetic model of the intended layout (`stackup.md` s2.3): the lead
regulator dissipating 0.88 W at the 7 V low-line corner rises **45.0 C on 4 layers
(Tj 95 C) and 65.0 C on 2 layers (Tj 115 C)** at 50 C ambient. The 2-layer number is
a fail even with the pour modelled as fully saturated - i.e. **no amount of copper
rescues a 2-layer build**, because on 2 layers the theta_JA floor is the layer count,
not the area. The 2-layer option is closed.

**2 oz outer** (rather than the repo's 1 oz default `JLC04161H-1080B`) because
`/SW` carries 3.6 A peak and IPC-2152 wants **1.56 mm at 1 oz vs 0.78 mm at 2 oz** -
halving the aggressor node is a containment win (buck.md s5), not just a routing
convenience; because DS41948's PCB Layout rule 1 asks for 2 oz on this part at this
load; and because `check_thermal`'s multilayer model is itself calibrated as
"2 oz / 4-layer". **The 1 oz fallback stays open in one direction only**: a board
routed to the `4layer_2oz` rule class (min trace 0.1524 mm) also passes the 1 oz
class, so retreating at P10 costs a `board_init` re-run and nothing else.

**Cost caveat:** `reference/jlc_pricing.yaml` has no copper-weight term and forbids
inventing one; a live 4L quote once showed `insideCuprumThicknessFee` at 48 % of the
bare-PCB price. The 2 oz adder is real and unpriced - P10 `order_quote --api` is the
only authority.

## D2 - CONFLICT RESOLVED: theta_JA 25 C/W (datasheet) vs 51 C/W (repo model). 25 loses.

`research/regulator.json` ranked the AP6335x #1 partly on a **datasheet-confirmed
25 C/W**; `research/power.json` designed against the repo's **51 C/W (4L) / 74 C/W
(2L)** calibrated model. **The repo model wins.** The 25 C/W figure is a JESD51-class
measurement on a 76.2 x 114.3 mm four-layer 2 oz coupon - **4.4x this board's area**,
unbroken and unloaded planes. TI publishes the same class of number for a comparable
part (42.9 C/W) with the verbatim caveat that it "can not be used for design
purposes". The repo model's 51 C/W is ~19 % worse than that JEDEC anchor, which is
the right direction and the right magnitude for a 2000 mm^2 board, **and it is the
number the P8 gate will apply** - designing to 25 C/W would produce a board that
passes on paper and fails its own verification. 25 C/W is retained only as the
optimistic bound; the post-fab check is `Tj = T_case_top + psi_JT x P`, not theta_JA.

## D3 - LEAD PART: AP63356QZV-7 (PWM-only), not AP63357QZV-7 (PFM/PWM). ENDORSED.

The reference-design agent's recommendation is adopted, with the reasoning restated
because it is the load-bearing spec call: **A3 requires <= 50 mV pk-pk ripple over
the FULL 0-3 A load range, and no minimum load is stated.** AP63357Q enters PFM below
a ~700 mA COMP-clamped threshold and its own datasheet scope captures (Fig.32 vs
Fig.20, same 50 mA / 50 mV-div conditions) show a visibly larger, burstier envelope
there. AP63356Q's forced-PWM-always behaviour holds ripple flat to zero load. The
thing AP63357Q buys - 22 uA vs 258 uA quiescent current and 86 % efficiency at 5 mA -
is worth nothing on a bench/adapter-fed 15 W converter. At 3 A the two parts are
electrically identical (both in PWM, same die, same package, same thermal). **They
are pin-identical**, so AP63357QZV-7 remains a drop-in alternate with the ripple
caveat; it is NOT an independent second source (same footprint, same die).

## D4 - `research/power.json`'s "<= 90 mohm RDS(on)" selection filter is DELETED

Read out of the datasheet during this merge (DS41948 Rev.1-2, Electrical
Characteristics p.5): **R_DS(ON) 74 mohm HS / 40 mohm LS typ at Tj = 25 C, no maximum
published.** That is 114 mohm total - the power model's filter would have rejected
**every part on the regulator shortlist**. The filter loses: it was a derived
criterion (the RDS(on) that lands a 0.63 W IC at 105 C), invented before anyone had
looked at what LCSC stocks, and the quantity it protects - junction temperature - is
now checked directly with the real numbers (D1). Consequences, all re-derived in
`power_tree.md` s3: **P_IC 0.88 W (not 0.63), board loss 1.48 W (not 1.20),
efficiency 91.0 % (not 92.6 %), input current 2.35 A (not 2.31 A)** at the 7 V
corner. `research/power.md`'s method, its Cin/Cout/inductor reasoning and its layout
prescriptions all stand; only its loss table is superseded.

**Bookkeeping:** `research/regulator.md` cites the datasheet as "DS41949 Rev.3". The
document actually is **DS41948 Rev.1-2, September 2020**. Every number they quoted
from it (74/40 mohm, 25 C/W, 35 V DC / 40 V-400 ms, 5.0 A HS limit) matches the real
document - only the document id was wrong.

## D5 - In2.Cu is GND, not +5V

Overrides `planes_gen`'s 4-layer default (In1 = GND, In2 = dominant power net).
`+5V` travels ~20 mm on F.Cu and needs no plane; a second GND plane is worth more as
thermal mass and lets the exposed-pad via array see copper on both inner layers.
DS41948 PCB Layout rule 6 asks for exactly this ("dedicate layers 2 and 3 to GND").
Declared explicitly in `constraints.json.planes`, together with F.Cu and B.Cu GND
pours, because declaring the key replaces the defaults wholesale.

## D6 - Reverse-polarity gate resistor is 10 kohm, NOT the 100-330 ohm the app note gives

`research/refdesign-buck.md` s4 quotes a components101 app note recommending
100-330 ohm "for circuits susceptible to sudden polarity reversal". **Overruled on
dissipation.** With the gate zener clamping at ~15 V and 18 V on the input, the gate
node sits ~3 V above GND and the pull-down carries `3 V / R` continuously: at 220 ohm
that is 13.6 mA, i.e. **0.25 W burnt in R6 and D3 for nothing - 17 % of this board's
entire 1.48 W loss budget** on a board whose thermal margin is ~0 C. The failure mode
being defended against is a technician swapping screw-terminal wires on a
current-limited bench supply: a millisecond event, which 10 kohm against ~2 nF of
Ciss turns off in ~20 us, three orders of magnitude faster than needed. 10 kohm costs
5 mW. The app-note band is right for a hot-swapped, inductively-fed input; this is
not one.

The zener itself is **load-bearing, not optional**: the input TVS clamps at 32.4 V,
above every shortlisted FET's Vgs(max) (AO4407A +/-20 V, AOD403 +/-25 V). **P3 must
confirm Vz <= Vgs(max) - 5 V for the FET it actually buys** - 12-15 V for an
AO4407A-class part.

## D7 - Fit the EN/UVLO divider (R3/R4), ~6.2 V rising / ~5.3 V falling

Two resistors that stop the converter operating below its own 7 V specification on a
slow ramp or a sagging supply. They do real work: the deep-low-line corner is exactly
where input current climbs and where the thermally-derated 4 A fuse is closest to
nuisance-opening (D13). A6's "no external enable input" is about an external control
line, not about internal UVLO. Suggested 86.6k/20k with the datasheet's 1.5 uA /
5.5 uA EN pull-up currents included; **P4 must re-derive with DS41948 Eq.1-2 and the
VEN_H/VEN_L min-max spread (1.15-1.21 V / 1.02-1.14 V)**. Fallback if that math comes
out unsatisfiable: **tie EN directly to `+VIN`** (a documented, high-voltage-tolerant
option) and drop both resistors.

## D8 - L1 = 6.8 uH. The P1 inductor shortlist has NO 6.8 uH part and cannot be used as-is.

At the AP6335x's 450 kHz, `L = 6.8 uH` (DS41948 Table 1's own 5.0 V row) gives a peak
inductor current of **3.59 A at the 18 V corner against a 4.0 A MINIMUM high-side
current limit - 11 % margin**. The powerpath scout swept 4.7 uH (assuming ~500 kHz)
and 2.2/3.3 uH (assuming ~1 MHz); **4.7 uH gives 3.85 A, i.e. 4 % margin, which is a
current-limit trip at high line on a min-spec part.** `grep` of every raw sweep in
`research/raw/` returns **zero 6.8 uH rows**. **This is a P3 blocker**: sweep 6.8 uH
+/-20 %, Isat >= 6 A, DCR <= 30 mohm (DS41948 s10), shielded composite, 125 C, body
<= 8 x 8 mm, height <= 5 mm. The CENKER/XR 8040 family is the obvious place to look,
with the caveat the scout already flagged - CENKER and XR are one OEM under two
labels, so they are not an independent second source.

## D9 - Q1 = AO4407A class (SO-8), AOD403 (DPAK) as the alternate

Both clear A4's 100 mW target at the conservative Vgs = -4.5 V figure that the 7 V
corner forces: **AO4407A 14.7 mohm -> 81 mW, AOD403 11.5 mohm -> 64 mW** at 2.35 A.
AOD403 wins on loss and on heat spreading (large drain tab) but costs ~35 mm^2 more
on a size-capped outline; SO-8 is the lead for that reason. If P6 wants thermal
margin back, swapping to the DPAK is worth ~17 mW and a better spreader - see
`stackup.md` s2.4. Note the LCSC AO4407A row is a **UMW rebrand**, not original
Alpha & Omega silicon: P3 must confirm Vds >= -30 V, Vgs(max), and Rds(on) at
Vgs = -4.5 V on the row it actually orders.

## D10 - ONE FLAT SCHEMATIC SHEET (deviation from the hierarchical default)

25 parts, one function, one rail. Hierarchy would buy nothing and would cost the
`/<sheet>/<LABEL>` net-prefix trap that has already forced an amendment on a prior
board. Full reasoning and the revisit threshold in `sheets.md` s1. `pwr_base = 100`
declared anyway so a later split starts from a convention.

## D11 - OUTLINE: take the full 50 x 40 mm cap

Binds permanently at P5 `board_init` - there is no shrink step later. Part footprints
total ~557 mm^2 (itemised in `stackup.md` s5); at the 25-35 % utilisation a power
board with wide copper and two 10 x 10 mm edge terminals actually achieves, that
needs 1600-2200 mm^2. **50 x 40 = 2000 mm^2 fits; 45 x 35 = 1575 mm^2 does not**, with
anything left for the GND pour the thermal argument depends on. Both sizes sit inside
JLC's 100 x 100 mm promo tier, so **shrinking saves nothing and costs thermal
margin.** J1 left edge, J2 right edge, power flowing left to right.
`board_init` call is written out verbatim in `stackup.md` s6.

## D12 - FB divider 158k / 30.1k at 0.5 %, not the datasheet table's 157k / 30k at 1 %

This family is **adjustable-only** (the LCSC "Fixed" attribute is a scrape artifact,
closed by the reference-design agent against the ordering table), so the divider sets
the output and its tolerance stacks on the +/-1 % reference. 158k/30.1k (both E96)
puts the nominal at **5.000 V** instead of the table's 4.987 V, for free. **0.5 %
parts**: 1 % resistors contribute +/-1.68 % which, stacked on the reference's +/-1 %,
leaves ~nothing against A3's +/-3 % window once line and load regulation are counted;
0.5 % brings the worst case to +/-1.84 % (4.91-5.09 V).

## D13 - Fuse stays at A5's 4 A; the derating problem is attacked by placement instead

`research/power.md` open item 2 recommends 5 A because SMD fuses derate ~30 % at
85-95 C. That relaxes a binding answer, so it goes to the human (H1 open 2) and **the
board is designed to 4 A**. Two mitigations that do not need permission: F1 is placed
next to J1 at the cool end of the board (15 mm centroid separation from U1 in
`constraints.json`), where the local rise over ambient is a few degrees rather than
the 40 C found under the regulator; and the EN/UVLO divider (D7) prevents the
deep-low-line, high-input-current state entirely. Lead part **1206T4A63V class**,
chosen from the shortlist for the **highest** melting I2t (4.145 A^2s) because A5 asks
for time-lag behaviour and no 1206 part in the sweep publishes a true slow-blow curve;
JFC1206-1400FS (1.73 A^2s) is the deeper-stocked alternate. Cin inrush I2t is
~0.04 A^2s, so either survives power-up.

## D14 - C7 (output polymer) is a RESERVED refdes and reserved area, NOT fitted

The unknown external load transient is H1 open question 1. A3 is written as a **DC**
accuracy spec, so the default reading is defensible and this board designs to it.
What P6 must do is leave **~40 mm^2 beside J2** so that a "fit it" answer at H1 is a
BOM change and not a re-layout. Same treatment for A7's optional input filter:
**~60 mm^2 reserved between J1 and F1, with no unpopulated footprints** - the
requirement is for room, and a DNF part on a JLC PCBA BOM buys confusion.

---

## Rejected, with reasons

| Rejected | Why |
|---|---|
| **2-layer stackup** | 65 C rise / 115 C junction at the 7 V corner even with a saturated pour (D1). Not recoverable by copper. |
| **`JLC04161H-1080B` (1 oz outer)** | `/SW` would need 1.56 mm instead of 0.78 mm; vendor asks 2 oz; thermal model is calibrated on 2 oz (D1). Kept as the one-way fallback. |
| **`JLC04161H-3313`, `JLC04161H-7628G`** | `available: false` in `stackups.yaml` - a phantom that never existed, and one JLC withdrew. `board_init` refuses both by name. |
| **AP63357QZV-7 as lead** | PFM light-load ripple against a 0-3 A ripple spec (D3). Retained as pin-identical alternate. |
| **MP2315GJ-Z** | theta_JA 100 C/W (no exposed pad) - at 0.88 W that is 88 C of rise before neighbours. 24 V recommended max input is also below the 25 V floor. |
| **RT8293AHZSP** | 23 V absolute-max input is the tightest in the shortlist against an 18 V steady-state ceiling plus a 32.4 V TVS clamp - the exact failure mode the brief names. Cheapest part, wrong risk. |
| **MP2338GTL-Z** | theta_JA could not be confirmed from any reachable source. A leadless SOT-583 at 15 W with an unverified thermal path is not a candidate on this board. |
| **TI TPS54540 family** | Asynchronous. A2/topology is a hard requirement, not a preference. |
| **Schottky reverse-polarity diode** | ~1.1 W against a 1.48 W board budget. Closed by A4. |
| **100-330 ohm P-FET gate resistor** | 0.25 W of continuous burn at 18 V in (D6). |
| **Aluminium electrolytic anywhere** | 105 C / 2000 h part at a ~90 C board temperature has ~5.7 kh of life. Cin/Cout all-ceramic X7R; any bulk is polymer. |
| **25 V X5R 10 uF 0805 Basic input cap** (the scout's Basic-tier pick) | X5R stops at 85 C against a ~90 C board hotspot, and a 25 V part loses ~50 % at 12 V bias. The input needs **50 V X7R**. Being JLC Basic does not buy its way past a dielectric rating. |
| **Unpopulated input-filter footprints** | A7 asks for *room*, not parts (D14). |
| **`high_speed` constraint entries** | No standards-bound or clocked net exists; `/SW` is governed by containment rules, not a return-path check. Reasoning recorded in `constraints.json`. |

---

## OPEN - for the human at H1

Three carried unchanged from `research/power.md`, designed-to-default in the meantime:

1. **External load transient profile.** Ripple is met with ~4x margin (13 mV of a
   50 mV budget) but a 0 -> 3 A step against ~30 uF dips the rail ~300 mV (6 %).
   Confirm A3's +/-3 % is DC/line-load-regulation only (as written), or say yes to one
   100 uF polymer at J2. **Designed to: no polymer, area reserved (D14).**
2. **Fuse 4 A (A5) or 5 A time-lag?** SMD fuses derate ~30 % at 85-95 C.
   **Designed to: 4 A, with the two placement mitigations in D13.**
3. **Is Tj <= 105 C a hard part-selection filter?** It is an assumption the
   requirements analyst wrote, not a user answer, and it is the only line the design
   is tight against: the lead part lands at **~105 C with the neighbour-heating
   allowance, 45 C below the part's own 150 C recommended maximum**.
   **Designed to: 105 C treated as the target.**

Two more that P2 raises:

4. **Terminal height.** Both dimension-confirmed screw terminals stand **14.07-14.10
   mm against A8's 15 mm cap - 0.90 mm**, before wire bend radius or tolerance
   stack. A8 was a default, not a stated requirement. If the 15 mm number is real
   and firm, this wants a second look before P3 commits.
5. **Single-source regulator.** No pin-compatible alternate exists at this theta_JA
   tier in today's LCSC stock; AP63356Q/AP63357Q are die twins in one footprint, not
   two sources. Acceptable for a qty-5 prototype; flag it if this ever goes to volume.

## P3 must resolve (not human questions - sourcing gaps)

- **6.8 uH inductor: no candidate exists in any P1 sweep** (D8). Blocker.
- **10 uF 50 V X7R 1210 input caps: the P1 sweep only found 25 V parts.** 50 V is
  required twice over (DC bias + hot-plug ring). Needs a fresh sweep.
- **Cout**: 22 uF 25 V X7R 1210 preferred; the sweep's 22 uF 16 V X7R 1206 is
  acceptable if the **total effective capacitance at 5 V bias is >= 25 uF** - size off
  the derated value, not the nameplate.
- **Zener D3** (12-15 V, SOD-123 class) and the **0.5 % FB resistors** were not swept
  at all.
- Confirm the AO4407A row's Vds/Vgs(max)/Rds(on)@-4.5 V on the **UMW rebrand** that
  LCSC actually ships (D9).

---

## P8 `sim` candidates (numeric pass windows, no vendor models needed)

The **buck switching loop itself is NOT simmed** - house policy, and no vendor SPICE
model exists for this part. What is left is small, exact, and catches the wrong-value
defect class that ERC/DRC/verify/DFM are all blind to:

| Bench | What it proves | Measures and windows | Model risk |
|---|---|---|---|
| `fb_divider` (DC) | The output setpoint is what the BOM says | `Vout = 0.8 x (1 + R1/R2)` -> **4.85 V min / 5.15 V max** (error at 4.90/5.10) | **None** - resistors and a reference source only. Catches a 15.8k-for-158k transposition directly. |
| `en_uvlo` (DC sweep) | The UVLO divider actually starts at the intended input | V_EN crossing 1.18 V with a 1.5 uA pull-up -> **Vin_rising in 5.8-6.8 V**; crossing 1.08 V with 5.5 uA -> **Vin_falling in 4.9-5.8 V**, and **hysteresis >= 0.5 V** | **None** - resistors plus two ideal current sources; the datasheet publishes both currents. |
| `rpp_gate` (DC sweep 6 -> 18 V, plus -18 V) | The P-FET is fully enhanced at low line and its gate is never over-stressed at high line | `abs(Vgs)` at Vin = 7 V -> **>= 4.5 V**; at Vin = 18 V -> **<= 15.5 V** (and <= Vgs(max) - 5 V); R6 dissipation at 18 V -> **<= 20 mW** (the D6 check, made a gate) | Low - a generic zener (diode with BV) and a level-1 PMOS. The clamp voltage and the resistor current are the measured quantities; the FET model only has to be off or on. |
| `hotplug` (transient) | An 18 V hot plug does not exceed U1's 35 V DC absolute maximum | peak `V(+VIN)` on an 18 V step through 1 uH / 50 mohm into the Cin bank -> **<= 33 V** (error at 35 V) | Medium - the TVS needs a behavioural clamp, so treat a pass as "the LC ring is bounded", not as a TVS qualification. The unclamped ring itself is exact. |

Everything else this board claims is checked by a gate, not a sim: junction
temperature by `check_thermal` (already run - `stackup.md` s2.3), conductor sizing by
`check_current`, decoupling by `check_pdn`, and output ripple by hand against a 4x
margin.
