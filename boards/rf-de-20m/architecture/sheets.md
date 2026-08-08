# rf-de-20m - hierarchical sheet plan

**AMENDED 2026-08-07 (P2-A):** part values and net currents re-derived at the
corrected operating point (**R = 4.13 ohm**, from Sokal's Q_L = 5 coefficients) on
the real EPC2019 datasheet. The sheet split, refdes blocks and net-naming contract
are unchanged. See `blocks.md` s0 and `decisions.md` D11.

Three sheets under a root that contains nothing but the sheet symbols and the
inter-sheet wiring. ~60 parts. **Deliberately not decomposed further** - this is
one function (a Class E stage) and the only organising principle that earns its
keep is the floorplan, so the sheets map 1:1 onto the zones in `stackup.md` s3.

| Sheet | Blocks (`blocks.md`) | Zone | Refdes block | `#PWR` base |
|---|---|---|---|---|
| **`hk`** | B1 bus entry + bulk, B2 +5 V buck | A | **100-199** | **100** |
| **`stage`** | B3 drive input, B4 gate driver, B5 FET pair, B6 drain feed + bus decoupling | A | **200-299** | **200** |
| **`tank`** | B7 series tank, B8 L-match, B9 RF output | B and C | **300-399** | **300** |

Refdes are unique across sheets by construction: each sheet owns a hundreds block
for every prefix, and each sheet has its own `#PWR` base.

---

## 1. Net-naming contract - BINDING ON P4

KiCad names a net from a hierarchical label alone as **`/<sheet>/<LABEL>`**. A net
that lives entirely inside one sheet therefore comes out with the sheet prefix, and
`constraints.json` uses those names. **A net whose name does not match is silently
no-op'd by every P5-P8 consumer** - this exact trap cost the lumina-par run a P4
amendment.

Power nets are **bare global symbols**: `+40V`, `+5V`, `GND`.

**Exactly one signal net crosses a sheet boundary: `/SW`.** For it to be named
`/SW` and not `/stage/SW`, **P4 must place a root-sheet local label spelled `SW` on
the inter-sheet wire.** Everything else is sheet-internal and is named with its
sheet prefix on purpose.

| Canonical net | Scope | Carries |
|---|---|---|
| `+40V` | global | **5.96 A** DC nominal, 7.0 A declared. Ring to 51 V |
| `+5V` | global | **99 mA** avg (real Qg 1.8 nC), ~1.6 A/gate peaks |
| `GND` | global | In1 + In2 + B.Cu plane stack, zones A and C |
| **`/SW`** | **`stage` -> `tank`, root label required** | drain node. **9.17 A rms, 17.1 A pk, 142.5 V pk** |
| `/stage/DRIVE` | `stage` | J201 -> R201/R202 -> U201 IN+ |
| `/stage/GATE_ON` | `stage` | U201 OUTH -> the two turn-on legs |
| `/stage/GATE_OFF` | `stage` | U201 OUTL -> the two turn-off legs |
| `/stage/GATE_Q1` | `stage` | gate of Q201 |
| `/stage/GATE_Q2` | `stage` | gate of Q202 |
| **`/tank/TANK_A`** | `tank` | L301 / C_s junction. **6.96 A rms, 156 V pk - the highest node on the board** |
| `/tank/TANK_B` | `tank` | C_s / L302 junction. 6.96 A rms, 41 V pk |
| `/tank/RFOUT` | `tank` | L302 -> C_m -> J301. 6.96 A rms at the C_m node, 2.0 A into the load, 141 V pk |

**The OUTH/OUTL nets are named `_ON`/`_OFF`, NOT `_H`/`_L`, on purpose.**
`rules_gen.detect_diff_pairs` auto-pairs `high_speed` nets whose names end in
`_H`/`_L` (as well as `_P`/`_N`, `_DP`/`_DM`, `+`/`-`) and would silently treat the
turn-on and turn-off legs as a 100 ohm differential pair, emitting a `diff_pair_gap`
rule and an inner-layer `disallow track` rule on the two most inductance-critical
nets on the board. Do not rename them back.

**Do not "tidy" `/stage/*` or `/tank/*` into bare names.** Promoting a
sheet-internal net to a root-crossing name means the root sees wire + label + one
sheet pin, which raises ERC `label_dangling`; buying the bare name would mean
adding a part to the root sheet. The netlist is the authority.

---

## 2. `hk` (100-199, `#PWR` 100) - zone A

| Ref | Part / class | Note |
|---|---|---|
| **J101** | 2-pos screw terminal, 5.08 mm, >= 24 A / 250 V (KF128-5.08-2P class) | **The only THT part on the board.** Left edge, x < 5 mm, clear of the heatsink land (HS-3) |
| C101, C102 | 2x 100 uF / **63 V** SMD polymer can | bulk. SMD can, not leaded - no bottom-face solder |
| C103, C104 | 2x 2.2 uF / 100 V **X7R** 0805 | mid tier, 100 kHz-5 MHz. **X7R is correct here and nowhere else on this board** |
| **U101** | **LM5017-class 100 V synchronous COT buck**, SOIC-8-EP | Vin abs max >= 63 V; no comp network, no catch diode |
| L101 | 15-47 uH shielded, >= 0.5 A | placeholder value; **P4 sizes against the chosen Fsw** |
| C105 | Vin local, 100 V | |
| C106, C107 | VCC decoupler, bootstrap | per the buck datasheet |
| C108, C109 | Vout bulk + HF on `+5V` | |
| R101, R102 | feedback divider | sets 5.0 V +/-4% |
| R103 | RON / on-time resistor | sets Fsw |

**Placement rule:** at the DC-input end, as far from the gate loop and the tank as
zone A allows. Its 0.5-2 MHz switching noise is spectrally clear of 20 MHz but its
switch node is still a dV/dt source next to a 1.4 V gate threshold.

---

## 3. `stage` (200-299, `#PWR` 200) - zone A

This sheet is the board. Everything on it lives in one ~15 x 15 mm cluster except
the drive connector.

| Ref | Part / class | Note |
|---|---|---|
| **J201** | SMD edge-launch SMA, 50 ohm (BWSMA-KE-P001 class) | **SMD, not the THT bulkhead jack** - a THT jack solders through the bottom face and breaks the heatsink land |
| R201, R202 | **2x 100 R 0805 in parallel** = 50 ohm | ~0.125 W in the termination; a single 0603 is over its rating. **DC-coupled - see `blocks.md` B3** |
| **U201** | **LMG1020YFFR**, 6-ball WCSP 0.8 x 1.2 mm | **Sits ON the mirror axis, equidistant from both gate bars.** LCSC brands it "Tokmas" - authenticity check on receipt |
| C201 | 100 nF 0402 X7R | VDD bypass, **< 0.5 mm from the VDD ball, via-in-pad return** |
| C202 | 10 nF 0201 C0G | second VDD bypass, straddling the ball |
| R203, R204 | 2x 4.0 R 0603 in parallel | OUTH -> `/stage/GATE_Q1` |
| R205, R206 | 2x 4.0 R 0603 in parallel | OUTH -> `/stage/GATE_Q2` |
| R207, R208 | 2x 4.0 R 0603 in parallel | OUTL -> `/stage/GATE_Q1` |
| R209, R210 | 2x 4.0 R 0603 in parallel | OUTL -> `/stage/GATE_Q2` |
| **Q201, Q202** | **2x EPC2019** 200 V eGaN | **MIRRORED PAIR about the U201 axis.** Both populated by default |
| C203-C206 | 4x 33 pF / 1 kV C0G 1206, **0-133 pF in 33 pF steps** | **C_shunt trim - POPULATE 3 (99 pF) at P2-A**, no longer DNP. The FET pair supplies 316 pF of the 403 pF shunt; this bank supplies the balance AND is the only absorber of the part's 110-150 pF Coss spread. **In the power loop, not on a stub** |
| **L201** | RF choke, **>= 0.82 uH, SRF >= 80 MHz, DCR <= 25 mohm, I_sat >= 12 A, >= 8 A rms** | Hardest part on the BOM. **Pre-authorised escape: 2x 0.47 uH in series.** Not authorised: a smaller choke - see `blocks.md` B6 |
| C207-C210 | 4x 10 nF / 100 V C0G 0603 | bus HF bank, **within 3 mm of L201's bus-side pad** |
| C211, C212 | 2x 1 nF / 100 V C0G 0603 | terminates the bank's self-resonance |

**Four resistors per FET pair per polarity is not over-specification.** Individual
gate resistors are what damp the differential mode between the two gate loops; a
shared resistor leaves the two gate nodes coupled through the driver output and
free to oscillate. Two 0603s in parallel per leg rather than one 0805 keeps each
part at **0.029 W** (the real Qg of 1.8 nC drops the pair's gate-loop energy to
0.36 W) and roughly halves the leg's parasitic inductance. See `blocks.md` s3.

**The gate-loop budget is the acceptance criterion for this whole cluster, and
P2-A TIGHTENED it: <= 0.48 nH per FET, matched to +/-0.1 nH.** The datasheet gives
Ciss 200 pF and Crss 0.7 pF, so C_GS ~ 199 pF, and EPC WP008 Eq.1 at
R_G + R_src = 3.1 ohm gives 0.48 nH (the retracted Qg of 2.4 nC had implied
~350 pF and 0.84 nH). **This is the tightest layout spec on the board** - two
parallel 0603s are ~0.15-0.2 nH, leaving ~0.3 nH for vias and interconnect.
**Stated fallback: R_G = 3 ohm relaxes the budget to 0.84 nH** at ~+0.3 W turn-off
loss and ~+1.6 C of Tj; take it consciously.

**Match the loops geometrically, not the trace lengths electrically** - FR4 is
~6.7 ps/mm, so length matching is not the mechanism. The +/-0.1 nH exists to damp
the differential mode and equalise static sharing; **skew itself is benign** in a
soft-switched topology (at turn-on the drain is at ~0 V, so an early device has
nothing to hog).

**Common source star.** Both source bars return to **one** via cluster on the mirror
axis, and the LMG1020's GND connects to the source plane **only at that star point**
(TI LMG1020DS s10.1.1 - single-point ground). Separate source returns would make
common-source inductance differential and imbalance the pair.

---

## 4. `tank` (300-399, `#PWR` 300) - zones B and C

| Ref | Part / class | Zone | Note |
|---|---|---|---|
| **L301** | **L_s 164 nH - etched PCB air-core spiral** | B | 2 turns, OD 30-34 mm, **~2.5-3 mm trace** (wider than before - the lower L target at the same OD needs it, and it buys Q), **>= 1430 mm^2 at Q 100**. **No LCSC code. `PCB feature - do not place`.** SPIRAL-1..6 |
| C301-C309 | **9x 56 pF / 1 kV C0G 1206 = 504 pF** (target 518 pF **+/-5%**) | B | C_s. 0.77 A rms and ~105 mW each. **No X7R.** The +/-5% is OPEN-12: the P1 fragment's C_series coefficient is refuted and SIM-4 is the arbiter - keep it a parallel bank so it trims by depopulation |
| **L302** | **L_m 110 nH - etched PCB air-core spiral** | B | **>= 950 mm^2 at Q 100 - nearly as large as L301 despite being 67% of the inductance**, because the constraint is dissipation area, not L (SPIRAL-3) |
| C310-C319 | **10x 1206 C0G 1 kV = 530 pF +/-3%** | C | C_m. Carries **6.66 A rms**, not the 2 A load current - 0.67 A each |
| **J301** | SMD edge-launch SMA, 50 ohm - **same part as J201** | C | right edge. 100 Vrms / 2.0 A rms |

**Why C_m sits in zone C and C_s does not.** C_s is a *series* element and floats -
it needs no ground reference and belongs beside the coils. C_m returns to GND and
carries 6.66 A rms, so it must sit where the ground plane exists.

**L301 and L302 are schematic symbols with custom footprints, not annotations.**
The footprint carries the spiral copper on F.Cu (and B.Cu under SPIRAL-2), a
courtyard equal to the thermal footprint, and its two terminal pads. Copper that no
tool knows about gets routed over, poured under and placed on top of.

---

## 5. Placement plan for P6

### 5.1 Placement groups (declared in `constraints.json.placement.groups`)

| Group | Anchor | Members | Purpose |
|---|---|---|---|
| `switch` | **Q201** | Q202, U201, R203-R210, C201-C212, L201 | **The whole thing.** Power loop + gate loop + choke + bus HF in one ~15 x 15 mm cluster |
| `drive_in` | J201 | R201, R202 | 50 ohm termination at the connector, not at the driver |
| `tank_ls` | L301 | C301-C309 | C_s bank adjacent to the L_s spiral |
| `tank_lm` | L302 | C310-C319, J301 | L_m -> C_m -> SMA, in that order, shortest possible |
| `hk` | U101 | L101, C105-C109, R101-R103 | buck and its loop |
| `bus_in` | J101 | C101-C104 | bulk at the terminal |

### 5.2 Edges

| Ref | Edge | pos | Why |
|---|---|---|---|
| J101 | **left** | 0.5 | DC entry. **x < 5 mm so its THT pins clear the heatsink land** (HS-3) |
| J201 | **top** | 0.2 | drive input, in zone A near the driver |
| J301 | **right** | 0.5 | RF output, in zone C. Must be adjacent to the C_m node |

### 5.3 Parts that must be placed by explicit `place_edit` and LOCKED before the annealer runs

The annealer optimises a cost function; none of the constraints below are
expressible in it.

| Ref | Why locking is mandatory |
|---|---|
| **Q201, Q202** | mirror symmetry about the U201 axis is the whole of `blocks.md` s4.1(c). An annealer will not produce a mirror pair |
| **U201** | must sit **on** the axis, equidistant from both gate bars |
| **R203-R210** | four matched legs; two arms must be geometric mirrors |
| **L301, L302** | zone B, centre-to-centre >= 38 mm, >= 14 mm clear of the heatsink land (SPIRAL-5, SPIRAL-6) |
| **J301** | zone C, adjacent to the C_m node, so `/tank/RFOUT` stays <= 15 mm |
| **J101** | x < 5 mm (HS-3) |

**After L301 and L302 are placed and locked, hand-add KiCad rule areas (keepouts)
over both courtyards on all four layers.** No pipeline check enforces "no other
copper here" and `planes_gen` has no void support. Verify geometrically at P8.

### 5.4 Zone assignment for P6 (board-local, translate by `outline_bbox` first)

| Zone | x | Sheets | Contents |
|---|---|---|---|
| **A** | 0 - 48 | `hk`, `stage` | everything except the tank |
| **B** | 48 - 88 | `tank` | L301, L302, C301-C309. **Nothing else may be placed here** |
| **C** | 88 - 100 | `tank` | C310-C319, J301 |

Heatsink land on B.Cu: **[5, 10, 36, 70]**, declared as a back-side keepout.

---

## 6. Sheet-level P4 notes

1. **The C_shunt trim bank (C203-C206) must be in the netlist, and at P2-A it is
   POPULATED (3 of 4 sites, 99 pF), not DNP.** The FET pair supplies 316 pF of the
   403 pF shunt; the bank supplies the balance and is the **only** mechanism that
   absorbs the part's 110-150 pF Coss spread. The fourth site stays unpopulated as
   headroom. All four have pads either way, so their clearance and area are
   accounted for at P6/P7 and the trim stays a populate change rather than a respin.
2. **`/SW` needs a root-sheet local label** or it becomes `/stage/SW` and six
   `constraints.json` entries silently stop matching.
3. **Both spirals need schematic symbols.** Do not let them become a layout-only
   feature; their nets must be real.
4. **The drive input is DC-coupled.** Do not add a series blocking capacitor "for
   safety" - it destroys duty-cycle control (`blocks.md` B3). Record it on the
   schematic.
5. **No protection parts.** No TVS, no fuse, no clamp, no OCP, no OVP, no thermal
   shutdown. Owner-acknowledged at P0 Q11. If ERC or a reviewer wants one, the
   response is *"waived, owner-acknowledged at P0"*.
6. **L201's value is a floor, not a target.** >= 0.82 uH. If P3 cannot source it,
   the answer is 2x 0.47 uH in series - **not** a smaller single part.
7. **`IN-` on U201 ties to GND.** No bias divider, no buffer.
8. **Silkscreen hazard markings**: zone B (two ~130 C copper structures, one on
   each face if SPIRAL-2 is adopted), `/tank/TANK_A` (**156 V pk**), `/SW`
   (142.5 V pk), and J301 (200 W RF - burn and RF-exposure hazard). This is an
   unenclosed bench board with no interlocks of any kind.
9. **Silkscreen the bus voltage as a RANGE, not a value: "40 V max, 34-40 V".**
   P2-A makes the bus a deliberate bring-up and derating knob (`decisions.md` D1),
   and ZVS is Vdd-independent, so a 36 V bench setting is a valid operating point at
   ~160 W - not a fault.
