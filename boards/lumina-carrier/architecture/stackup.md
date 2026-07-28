# LUM-CAR-A - stackup, board class and the common LUMINA footprint (MECH-02)

---

## 1. Chosen stackup

**`JLC04161H-3313`** - JLCPCB standard impedance-controlled **4 layer**, 1.6 mm, 1 oz outer /
0.5 oz inner, HASL.

```
F.Cu      35 um  1 oz    signal: MDI, SPI, PWM, 48 V domain, all placement
  prepreg 0.2104 mm  FR4 7628, er 4.05
In1.Cu    17.5 um 0.5 oz SOLID GND - the reference plane for everything on F.Cu
  core    1.065 mm   FR4, er 4.6
In2.Cu    17.5 um 0.5 oz +3V3 power plane
  prepreg 0.2104 mm  FR4 7628, er 4.05
B.Cu      35 um  1 oz    signal + GND pour
```

Controlled-impedance profile used: **`diff_100`** - 0.260 mm width, 0.210 mm gap (0.470 mm
centre-to-centre), outer-layer microstrip referenced to the nearest inner plane.

**Board class: 4L.**

`board_init.py` invocation for P5 (all flags confirmed present on this host via `--help`):

```
board_init.py --netlist ... --name lumina-carrier --out boards/lumina-carrier/kicad \
              --layers 4 --stackup JLC04161H-3313 \
              --outline 100x80 --margin 10 --corner-radius 3 --mounting-holes 4
```

---

## 2. Why 4 layers - three independent reasons, in order of strength

### 2.1 100 ohm differential MDI. Decisive.

`JLC04161H-3313` is the only stackup in `reference/stackups.yaml` that publishes a 100 ohm
differential profile. `JLC2313_1.6` ships `controlled_impedance: []` and the file's own comment
explains why - **a 2-layer board has no adjacent reference plane.** Running the pipeline's own
solver against the 2-layer stack anyway gives:

| Stackup | h (mm) | er | 100 ohm diff width | gap | pitch |
|---|---|---|---|---|---|
| **JLC04161H-3313 (4L)** | 0.2104 | 4.05 | **0.260 mm** | **0.210 mm** | **0.470 mm** |
| JLC2313_1.6 (2L, 1 oz) | 1.530 | 4.5 | 1.081 mm | 0.300 mm (solver clamp, not a solution) | 1.381 mm |

A **2.4 mm-wide differential pair** on a board that also has to fit a PD front end, a 100 V
converter, a module, a magjack and two expansion connectors is not a layout - it is a refusal.

### 2.2 Reference-plane discipline. Also decisive.

On 2 layers, B.Cu would simultaneously be the MDI reference, the SPI clock reference, the PD
return, the 12 V distribution and the 3.3 V distribution. There is no arrangement of that which
survives `check_return_path` at P8, which raises an **error** (not a warning, and `gate.py` has no
waiver mechanism) for any corridor deficit where >= 0.01 mm of trace centreline crosses missing
reference copper.

On 4 layers: **In1 is solid GND under the entire board**, which is the reference for both MDI pairs
and for `/ETH_SCLK`, and In2 carries +3V3. The two 48 V-domain nets and +12V route as sized traces
on F.Cu, which also keeps the 0.60 mm creepage requirement (an *outer-layer* number) in one place.

### 2.3 Both silicon vendors say so, independently

- TI SNLA079D section 8: "To meet signal integrity and performance requirements, **at minimum a four
  layer PCB is recommended**."
- Skyworks AN956 section 8, for the PD half: "In general, **four-layer PCB designs yield the most
  robust design** ... Two-layer PCB designs must be carefully considered", and Skyworks offers
  pre-fabrication layout review for 2-layer PD designs.

### 2.4 What is *not* a reason (stated so it is not over-claimed)

Thermals. `research/power.json` argued that the 48->12 converter's dissipation forces 4 layers
(1.35 W x 51.1 C/W = 69 C passes on 4L; x 73.9 C/W = 100 C fails on 2L). That argument treated the
whole converter block as one refdes. Once the loss is split across its real parts - **U20 0.43 W,
D20 0.54 W, L20 0.17 W** at the at operating point (`power_tree.md` s7.1) - no single part is
thermally decisive. Layer count is settled by impedance and plane discipline; thermals are
supporting, not load-bearing.

### 2.5 Copper weight: 1 oz is sufficient

Widest declared power net is `+12V` at 2.0 A, which is **1.10 mm at 1 oz / dT 10 C** by IPC-2152 -
routable on a 100 x 80 mm board. No 2 oz stackup is needed, and 1 oz keeps the `diff_100` geometry
valid (the impedance table is computed for t = 0.035 mm).

---

## 3. Plane assignment

Declared explicitly in `constraints.json.planes` rather than left to `planes_gen`'s
"In1 GND + In2 dominant-power" default, because the dominant-power heuristic is a pad count and this
board's answer must not depend on one:

| Layer | Net | Region |
|---|---|---|
| **In1.Cu** | **GND** | full board **except** the antenna keepout (s7) |
| **In2.Cu** | **+3V3** | full board **except** the antenna keepout (s7) |

`+12V`, `V48_RAW`, `V48_RTN` and `+48V_SW` are **routed nets, not planes**. `rules_gen` sizes them
from `constraints.json.power` (2.0 / 1.5 / 0.6 / 1.0 A).

### 3.1 Deliberate conflict resolution: the plane void under the magjack

Three vendors disagree about whether to void the planes under an Ethernet connector:

| Source | Says |
|---|---|
| WIZnet HW design guide | "All PCB layers under the Transformer and RJ45 Connector must have no power and GND plane." |
| TI SNLA079D 10.2 | "void the planes under **discrete** magnetics" |
| Pulse layout note p.4 | "no ground planes beneath a **discrete** LAN magnetics package ... **For integrated connector modules, the chassis ground plane should run under the component** ... within the connector module, all magnetic components are far enough away from the PCB to prevent any unwanted coupling." |

**Resolution: keep In1 GND continuous under the magjack. WIZnet's blanket rule loses.** Four reasons,
and the last one is the decisive one:

1. **The part is an integrated connector module**, which is exactly Pulse's stated exception. TI's
   rule is scoped to discrete magnetics and does not apply either.
2. **Under Q5's non-isolated default there is no chassis ground to island.** The void's purpose is
   to separate a chassis plane from signal ground; on this board GND *is* the PD return and floats
   at PoE potential, and there is no earth anywhere. Voiding would isolate nothing from nothing.
3. **There is no cable-side copper on the board.** With integrated magnetics the only board copper
   at the connector is the PHY-side pads and the two pre-rectified PoE pins - both already inside the
   board's own floating domain. Pulse's "15 mil of FR-4 for 1500 Vrms" concern (JLC's prepreg is
   8.3 mil) has nothing to hold off, because the 1500 V barrier lives inside the connector.
4. **A void near the MDI pads is the single most likely unwaivable P8 failure on this board.** The
   MDI pairs terminate on the connector's PHY-side pad row; any void that reaches under them makes
   `check_return_path` raise an error, and `gate.py` has no waiver. `planes_gen` supports only
   rectangular *positive* regions - no keepouts, no holes - so a void here would have to be built by
   sizing region rectangles to stop short of the connector, with zero tolerance against the pad row.
   The research fragment flagged exactly this as its OPEN-2. **This resolution closes it.**

What survives from the void idea:
- **In2 (+3V3) is voided under the connector body and the shield tabs** - a power plane under a
  57 V-adjacent pin field and under a shield tab buys nothing. Implemented at P5 as an In2 region
  that stops ~2 mm short of the connector's outboard pad row.
- If a **shielded** jack is used (it is - the HanRun candidates are shielded, tab-down), the shield
  tabs get their own small F.Cu island tied to GND through a **1 Mohm || 1 nF / 2 kV hybrid** with a
  fitted-by-default 0 ohm alternative, so EMC testing can move the strap without a respin.

---

## 4. MECH-02 - the common LUMINA board outline

**Proposal: 100.0 x 80.0 mm, 3 mm corner radius, 4x M3 (3.2 mm) at 5 mm inset, plus a 5th M3 at
(46, 74).**

This is permanent (`board_init.py --outline WxH`, no shrink step) and every daughter inherits it.

### 4.1 Derivation from block area, not from a round number

Zone areas below are footprint + fan-out + mandated keep-clear, not raw courtyards:

| Zone | Contents | mm2 |
|---|---|---|
| A | RJ45 PoE magjack: 16.0 x 21.6 body + panel cutout + 14-pin field + MDI fan-out | 520 |
| B | PD front end: PD interface, TVS, 0.1 uF/100 V, 2x 22 uF/100 V bulk, split RDEN, RCLS, T2P network - **all inside the 0.60 mm creepage envelope** | 550 |
| C | Ethernet PHY: W5500 LQFP-48, EXRES1, TOCAP, 1V2O, 6x decoupling, MDI TVS array, SPI series R | 440 |
| C2 | Crystal group: 3225 crystal + 2 C0G load caps + its GND land + 2 mm keepout ring | 130 |
| D | ESP32-S3-WROOM-1: 25.5 x 18 module + 2 mm halo + 40-pad fan-out | 650 |
| E | DC-DC hot zone: 100 V buck + 68 uH inductor + SS510 with its own copper + 4x 100 V ceramics, and the 12->3.3 buck + 4.7 uH | 730 |
| F | 48 V eFuse: HTSSOP-20 + ILIM/UVLO/OVP/dV-dT network + IMON + bleed, inside the 0.60 mm envelope | 250 |
| G+H | Two expansion connectors: 2x7 (19.6 x 7.6) + 2x12 (30.5 x 7.6) bodies + 0.60 mm envelopes + fan-out | 840 |
| I | Recovery header, status LEDs, I2C/FAULT pull-ups, ID divider + its clamp, ADC clamps | 300 |
| **Sum of blocks** | | **4410** |

A 4-layer board carrying a 0.60 mm board-wide creepage envelope, a no-vias MDI corridor, an antenna
keepout and five mounting-hole exclusions realistically places at **55-60 % area utilisation** on a
first spin. `4410 / 0.57 = 7740 mm2`, plus ~135 mm2 of mounting-hole exclusion and ~8 mm2 of
corner-radius loss -> **~7900 mm2 required.**

| Candidate | Area | Utilisation needed | Verdict |
|---|---|---|---|
| 80 x 60 (Q2 option c) | 4800 | **92 %** | **impossible.** Confirms the brief's own suspicion |
| **100 x 80 (Q2 option a)** | **8000** | **55 %** | **selected** |
| 100 x 100 (Q2 option b) | 10000 | 44 % | works, but a 25 % bigger enclosure for headroom nobody has asked for |

Two cross-checks:
- **Same JLC price tier.** 100 x 80 and 100 x 100 are both inside the <= 100 x 100 mm low-cost tier,
  so 100 x 80 costs the same to fabricate as 100 x 100 and buys a smaller box.
- **The strobe daughter fits.** ~2800 uF at 63 V is 4x 680 uF radial (16 mm dia, ~25 mm tall) =
  ~1200 mm2 with spacing, plus the LED driver, the inrush limiter, the bleed path and the two
  sockets. Comfortable inside 8000 mm2 minus the RJ45 relief of s5.

The thermal model in `power_tree.md` s7.2 assumed a 110 x 90 x 45 mm internal box - which is exactly
a 100 x 80 board with 5 mm of clearance all round. The two are consistent by construction.

### 4.2 Corner radius: 3 mm

`--corner-radius` **exists on this host** (confirmed by `board_init.py --help`, not assumed).

`board_init` **clamps the corner radius to the mounting-hole inset** and the inset is `--margin / 2`.
So `--margin 10` gives a 5 mm inset and permits a radius up to 5 mm. **3 mm requested, 5 mm
available - no clamping, no warning.** Do not reduce `--margin` below 10 or the radius silently
shrinks.

### 4.3 Mounting holes

- **4x M3 (3.2 mm) at 5 mm inset** = a **90 x 70 mm hole rectangle**, matching Q3's default. Generated
  natively by `--mounting-holes 4` as `board_only` footprints (excluded from schematic parity).
- **A 5th M3 at (46, 74)** - board-relative, i.e. on the bottom edge between the two expansion
  connectors, 6 mm in - **required by CAR-REQ-15**: J3 and J4 sit mid-span between the bottom corner
  standoffs (19 mm and 12 mm from the nearest, but 40+ mm from the other), and board flex across a
  mated 38-position connector pair must be carried by a standoff, not by the pins.
  **Implementation note:** `board_init --mounting-holes` generates corner holes only (0..4). The 5th
  hole is added at **P4 as a `MountingHole_3.2mm_M3` symbol with refdes `H5`** so it carries a
  netlist entry and a deterministic placement (`constraints.json.placement.edges`: bottom, pos 0.5).
  It is **also a keying feature** - see `connector-icd.md` s7.

### 4.4 The permanent-outline risk register

Everything below is baked in at the first `board_init` call and cannot be undone:

| Baked in | If the human answers differently |
|---|---|
| 100 x 80 outline | a smaller board is not reachable; a larger one is a full re-run of P5-P10 |
| 3 mm radius, 4x M3 at 5 mm inset, 5th M3 at (46,74) | every daughter inherits it; changing it orphans any daughter already built |
| **10 x 22 mm antenna keepout at the right edge** | **Q8 = "radio permanently dead"** removes it entirely and frees 220 mm2 plus a whole board edge (s7) |
| RJ45 on the top edge | **Q12 = "panel-mount on a pigtail"** frees zone A and removes the daughter relief of s5 |

---

## 5. The RJ45 versus stack-height collision (Amendment 3 item 6)

**The 15 mm standoff of Q4's default is not reachable.** Measured from the parts:

| Hardware | Achievable board-to-board |
|---|---|
| DS1021 male (6.0 mm mating pin) + DS1023 socket (8.5 mm body) - the pick | **11.0 mm**, hard-seated against a positive mechanical stop |
| 2.00 mm family | 4.3 - 6.5 mm |
| 1.27 mm family | 4.3 - 5 mm |
| PC/104 stackthrough 2x20 (12.3 mm tails) | up to ~15.2 mm - **but 2x20/2x40 only**, so it forces the single-connector scheme and gives up the free keying, **and publishes no working-voltage rating**, which CAR-REQ-17 cannot accept |
| Samtec QTH/QSH (5/7/9/11/13/16 mm) | any of them - rejected on cost, ~$15 per mated pair |

**And the board-edge THT PoE magjack is ~15 mm tall**, so at an 11 mm stack it protrudes ~4 mm above
the daughter's underside. There is no low-profile escape: an 8P8C opening is ~11.7 x 13.5 mm, so no
magjack body can be much under 13.5 mm.

**Recommendation (one line for the human): set the standoff to 11.0 mm and give every daughter a
30 x 26 mm top-edge notch over the magjack** - board-relative `(6, 0) - (36, 26)`. The daughter's
outline rectangle, corner radius, 5-hole pattern and enclosure are unchanged - only a local relief
differs, in the least useful 10 % of the daughter's area (it sits directly over the carrier's own
jack). A top-*edge* notch rather than an internal cut-out, so it is a simple outline feature.

**Bonus: the notch is also the strongest keying feature on the board.** A daughter rotated
180 degrees puts its notch at the bottom edge and lands solid board on the carrier's ~15 mm-tall
jack, 4 mm above the 11 mm stack. It is a **hard mechanical stop** - the boards cannot be forced
flat. See `connector-icd.md` s7.4.

Ranked alternatives if the human dislikes that:
2. **Panel-mount RJ45 on a short pigtail** (Q12 option b). Removes the tall part entirely, no relief
   needed, 11 mm stack is clean. Costs 2 parts, a pigtail and an enclosure feature, and it changes
   zone A of the outline - so it must be decided **at H1, before P5**.
3. 15.24 mm PC/104 stackthrough. Rejected: single connector, no keying, no published voltage rating.

**The de-risking statement for H1: the outline, the corner radius and the hole pattern are identical
under all three answers.** MECH-02 can therefore be frozen at H1 even if the stack-height question
runs on.

---

## 6. Floorplan (P2 intent - P6 executes, P8 verifies)

Board-relative coordinates, `u = x - outline_x1`, `v = y - outline_y1`. Origin at the top-left of the
outline; `v` increases downward (render orientation, matching `placement.edges`' `top = min y`).

```
 (0,0)                                                            (100,0)
  +-----------------------------------------------------------------+
  | H1        [A] J1 magjack     [C] ETH PHY   [C2]   [I] J2 hdr H2 |
  |           TOP edge, pos 0.21 U10 + MDI TVS Y10    + status LED  |
  |           u10..32 v0..22     u40..60 v2..24 u62..  u78..96      |
  |                                             74     v2..18       |
  |                                             v4..18              |
  |  [B] PD FRONT END                                       +-------+
  |  U1 D1 CBULK RDEN RCLS        [F] 48 V eFuse            | [D]   |
  |  u4..34 v26..44               U22 + IMON + bleed        | U30   |
  |                               u40..62 v30..48           | MCU   |
  |  ---------------------------                            |RIGHT  |
  |  [E] DC-DC HOT ZONE                                     |edge   |
  |  U20 L20 D20 / U21 L21                                  |u74..  |
  |  u4..34 v48..66                                         |100    |
  |                                                         |v29..51|
  |                                                         +-------+
  |    [G] J3 POWER 2x7        H5      [H] J4 SIGNAL 2x12           |
  |    u14..34 v68..78       (46,74)   u56..88 v68..78              |
  | H4                                                         H3   |
  +-----------------------------------------------------------------+
```

Why it is arranged this way:
- **J1 on the top edge, U30 on the right edge** - different edges, **58 mm apart**. The magjack has
  a shielded metal shell plus a metre of shielded cable hanging off it and must not share an edge
  with a 2.4 GHz antenna.
- **B directly below A**, contiguous, so the PD power flow is point-to-point with no crossovers - the
  vendor rule. That zone is a routing keepout for MDI, SPI and PWM.
- **C about 20-25 mm from J1's PHY-side pins.** WIZnet wants the MDI run <= 25 mm; Pulse wants the
  PHY >= 25 mm from the magnetic for EMI. The two rules meet at 25 mm and this is the number.
- **C2 (crystal) on the far side of U10 from J1**, so "crystal close to the chip" and "crystal far
  from the MDI" stop fighting.
- **E is the ICD hot zone**, >= 25 mm from J1/U10/Y10 and >= 20 mm from U30 (enforced by
  `constraints.json.placement.separation`, which measures refdes to refdes, not zone to zone).
- **G and H straddle H5**, so CAR-REQ-15's support point sits between the two connectors.
- **G's 48 V group is at its left end**, ~24 mm from the nearest signal pin of H.
- **The bottom-edge order G - H5 - H is what makes the connector pair 180-degree-proof** - see
  `connector-icd.md` s7.4.

---

## 7. Antenna keepout - and the P5 step that must not be skipped

Q8's provisional default keeps the radio functional. The ESP32-S3-WROOM-1 datasheet marks a
**6 x 18 mm "Keepout Zone" / "Antenna Area"** at the module's antenna end - **no copper, no plane, no
traces, on any layer** - and Espressif's layout guidelines want the module as close to the board edge
as possible with the antenna overhanging or the board relieved.

**Declared keepout: 10 mm (u) x 22 mm (v) at the right edge, vertically centred** - i.e.
`u 90..100, v 29..51`. 10 mm rather than 6 mm so the module's outermost pad row (which ends 6.3 mm
from the antenna tip) sits 3.7 mm clear of the keepout boundary; 22 mm rather than 18 mm for a 2 mm
margin on each side. Both corner mounting holes (v = 5 and v = 75) are outside the band.

### 7.1 Mandatory P5 step - re-basing the keepout and the plane regions

`board_init` does **not** place the outline at (0,0): the outline origin is derived from the packed
component bounding box. Every rectangle below is therefore authored **after** `board_init`, from
`reports/board_init.json.outline_bbox = [ex1, ey1, ex2, ey2]`. That is why
`architecture/constraints.json` ships `planes` **without** regions and no `keepouts` at all - a
placeholder rectangle in the wrong place is worse than an absent one.

At P5, after `board_init` and before `place_seed`, patch `kicad/constraints.json`:

```jsonc
"placement": {
  "keepouts": [
    {"rect": [ex2-10, ey1+29, ex2, ey1+51], "side": "front",
     "reason": "ESP32-S3-WROOM-1 antenna keepout - no copper on ANY layer"}
  ]
},
"planes": [
  {"layer": "In1.Cu", "net": "GND",  "region": [ex1, ey1,    ex2,    ey1+29]},
  {"layer": "In1.Cu", "net": "GND",  "region": [ex1, ey1+29, ex2-10, ey1+51]},
  {"layer": "In1.Cu", "net": "GND",  "region": [ex1, ey1+51, ex2,    ey2   ]},
  {"layer": "In2.Cu", "net": "+3V3", "region": [ex1+26, ey1,    ex2,    ey1+29]},
  {"layer": "In2.Cu", "net": "+3V3", "region": [ex1+26, ey1+29, ex2-10, ey1+51]},
  {"layer": "In2.Cu", "net": "+3V3", "region": [ex1+26, ey1+51, ex2,    ey2   ]}
]
```

Three rectangles per plane layer rather than one, because a single positive rectangle cannot have a
hole. In1 GND runs the full width except the antenna band; In2 +3V3 additionally stops at
`ex1 + 26` so no power plane sits under the magjack, the PD front end or the shield tabs (s3.1).

B.Cu is left to `planes_gen`'s own handling; the antenna keepout on B.Cu is enforced by the
`side: "front"` keepout plus a manual check at P8 - **add a matching `side: "back"` keepout entry if
`place_seed` ends up putting anything on B.Cu.** Board target is single-sided (top) assembly per
section 7 of the requirements.

### 7.2 What changes if Q8 comes back "radio permanently dead"

Switch to **ESP32-S3-WROOM-1U-N8**: same 18 mm-wide 40-pad land pattern, 6.3 mm shorter, u.FL
connector instead of a PCB antenna, **no keep-out at all**, and $0.05/unit cheaper. The keepout and
all six plane regions above collapse to two full-board entries, and 220 mm2 plus a board edge come
back. Because the two modules share a footprint, **leaving Q8 open is survivable - but the outline
decision is not reversible, so Q8 must be answered at H1, not after.**
