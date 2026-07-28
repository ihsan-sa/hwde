# pd-trigger - architecture decisions

Every decision below is settled unless it appears in s16 (verify-later). Items
D0.x were settled by the orchestrator before P2 and are recorded, not re-opened.

## D0 - settled upstream (recorded)

| # | Decision | Source |
|---|---|---|
| D0.1 | **No main-path series fuse.** PD source OCP + the mandatory TVS are the protection. The aux tap gets a 1 A 1206 PPTC and silk `AUX 1A MAX`. | P0 answer 2, REVISED by the orchestrator on P1 evidence. Chain documented in D1. |
| D0.2 | **2 oz outer copper, stackup `JLC2313_1.6_2oz`, 2 layers.** `stackups.yaml` gained the entry at P1. | power research IPC-2152 math |
| D0.3 | **Lead controller CH224K** (scout-verified, its live query returned C970725), alternate HUSB238A. | scout |
| D0.4 | P0 answers 1/3/4/5/6: uniform 5 A at every profile; screw terminal 18 AWG-capable and >= 8 A; aux header low-current only; size a soft target; 5 V fallback acceptable but must be visibly indicated. | P0 |

## D1 - the safety chain that replaces the main-path fuse

The board carries a 5 A / 100 W path with **no series protective element**. That
is a deliberate, evidence-backed choice on a >3 A board, so the whole chain is
written out here.

**The hazard.** A short or sustained overload at the screw terminal (or at the
aux header) on copper capable of 5 A at 20 V.

**What actually interrupts it: the source.** The USB-C Source Power Test
Specification requires a PD source to implement over-current protection and to
survive a shorted output. A 20 V/5 A source current-limits just above its
advertised PDO and hard-resets VBUS to vSafe5V within milliseconds. This is the
only element in the system fast enough to matter, and it is present on every
compliant charger the board can negotiate with.

**Why a series PPTC could not help.** Three independent facts, each sufficient:

1. *It would have to be an 8 A part.* PPTC hold current is specified at 23 C and
   derates steeply: from the Bourns MF-R derating chart, a 5 A part holds
   **4.15 A at 40 C** and a 6 A part **4.98 A** - both nuisance-trip at a 5 A
   commitment on a warm bench, and the ambient beside 5 A of copper is not room
   air. 8 A hold is the honest minimum.
2. *An 8 A PPTC trips at 16 A, with 18.8 s max time-to-trip.* The source folds
   back at 5-6 A in milliseconds. **The two windows do not overlap** - there is
   no fault a compliant PD source can produce that the PPTC could interrupt.
3. *It does not fit and it is not free.* Every 8 A / 30 V PPTC in the JLC catalog
   is a radial through-hole disc, ~24 x 25 mm - larger than half this board -
   outside the economy PCBA tier, dissipating 0.125 W new and up to **0.75 W at
   its datasheet end-of-life resistance**, with 25-150 mV of drop. The one SMD
   candidate (a 6 A / 2920 part) holds ~5.0 A at 40 C, i.e. it trips at the
   design current: worse than no device, because it turns a working board into
   an intermittent one.

**What protects the board instead.**

- **Source OCP** (above) - the fast element.
- **D1 TVS at the connector**, 22 V standoff / ~28 V clamp. This addresses the
  actual observed failure mode for this exact board class: a published CH224
  trigger-board teardown with no TVS and no fuse reports the chip destroyed at
  20 V under load, attributed to a cable inductive spike. Cable inductance times
  a 5 A interrupt is the real fault here, and it is a transient - a fuse would
  not have caught it either.
- **Series pin resistors into the controller** - R1 10 k on the sense pin, R2
  1 k as the VDD dropper. These are what keep a 3.3 V-class chip alive on a 21 V
  rail; the datasheet requires both and this design does not omit them.
- **Copper sized with margin**: 2 oz, dt_c 10, 1.750 mm for 5 A, plus a
  continuous B.Cu return pour.
- **F1, 1 A PPTC on the aux tap** - the resettable element from P0 answer 2, put
  where its 1.8 A trip current is actually reachable by a source, protecting
  2.54 mm pins rated 3 A each. This is what makes the "low-current aux" promise
  physically true rather than merely silkscreened.

**Residual risk, stated plainly.** (a) Energy pushed *backwards* into the output
terminal from an external supply is unprotected - not the stated use, and a
PPTC rated for this current would not have survived it either. (b) A
non-compliant source with broken OCP is unprotected - outside the board's
control. (c) A bench user who shorts the terminal relies on the charger's OCP,
which is exactly what every commercial PD trigger board does.

**If policy later mandates a series element anyway**: take the 8 A radial
(JK30-800 class, cheapest with real stock per the power research), accept
~50 x 28 mm and through-hole assembly, split `VBUS` into `VBUS` + `VOUT` in
`constraints.json` with identical 5 A entries, and add
`{"ref": "F2", "power_w": 0.75, "net": "VOUT", "dt_c": 40}`.

## D2 - CH224K supply: the datasheet's dropper (AMENDED A1 - the LDO is gone)

**Settled: R2 = 1 kOhm, 2512, 1 W, from `/VIND` (i.e. VBUS) to pin 1, with
C5 = 1 uF from VDD to GND. No regulator anywhere on the board.**

The P2 draft specified a 3.3 V LDO feeding VDD through 47 R. **The P3 extract
(`parts/C970725.json`, tables 4-2 / 8.1.3 / 8.2.3) says that is the wrong
topology**, and the correction is not negotiable:

- VDD is an **internal shunt regulator** - 3.24 / 3.30 / 3.36 V, sink capability
  0-30 mA - with an absolute maximum of **3.6 V**. It is not a regulator input.
- The datasheet's own reference circuit (6.2) drops the entire bus-to-3.3 V
  difference across a **1 kOhm** resistor and lets the chip shunt the excess.
- An external 3.3 V regulator would sit *inside or above* the shunt band. An AC-
  grade L78L33 is +/-4 %, i.e. up to **3.432 V** against a shunt that may bin at
  **3.24 V** - the chip would sink whatever the regulator could source, up to its
  30 mA limit, and 3.6 V abs max leaves no headroom for the error.

**The field-death evidence was misread in the P2 draft, and this correction
matters.** The published CH224 trigger-board failure used a **510 Ohm** dropper
burning **0.55 W in a small package** - that is a *sizing* error, not a topology
error. At 1 kOhm the dropper carries 16.7 mA / 0.279 W at 20 V and 17.7 mA /
0.313 W at 21 V, inside the 30 mA shunt limit and inside a 1 W part with 3x
margin. So:

- **R2 is a 2512, 1 W part**, not an 0603/0805. Alternate if 2512 stock is a
  problem: 2x 510 Ohm 1206 in series (0.157 W each in 0.25 W parts). Not 2x 2 k
  0805 in parallel - that is 0.157 W each in 0.125 W parts, over-rated.
- It is a continuous ~0.3 W heat source: `constraints.json` keeps it 8 mm from
  U1 (whose baseplate is its only thermal path) and it stays off the connector.

**The binding consequence is at the OTHER end of the range.** At the 5 V profile
the dropper delivers only **(5 - 3.3) / 1 k = 1.7 mA** (1.1 mA at 4.4 V low
line), and the extract is explicit that **CH224K has no published IDD** (the
1.8 mA typ / 12 mA max ICC in 8.2.1 belongs to CH224Q/CH224A and must not be
applied). WCH's own reference circuit accepts that operating point, which is the
only evidence available that IDD fits inside it. Everything hung on VDD is
therefore rationed - see D3 (100 k straps) and D4 (no PG LED).

Contingency if VDD sags at 5 V during bring-up: **R2 -> 680 Ohm** (24.6 mA at
20 V, still under the 30 mA shunt limit, 0.41 W in the same 1 W part). Floor is
~600 Ohm ((21 - 3.24) / 30 mA).

Rejected: an LDO into VDD (fights the shunt - above); a switching pre-regulator
(a converter on a board whose entire selling point is that it does not convert);
keeping an LDO for the LEDs alone (see A1).

## D3 - profile selection: 3-position DIP switch, pull-ups, table on silk

**Settled: SW1 = SMD SPST x3 DIP switch, 2.54 mm pitch, with R3-R5 = 100 k
pull-ups to `/VDD` and each switch shorting its CFG pin to GND (ON = logic 0).**
*(Amended A1: the pull-up rail is VDD, not a 3.3 V logic rail, and the value went
from 10 k to 100 k.)*

- **DIP over jumpers**: three shunts on a bench tool are three parts to lose,
  and a missing shunt reads as an ambiguous float rather than a defined level.
- **DIP over rotary/BCD**: a coded rotary is ~7 x 7 mm, several times the price,
  needs 4 poles to reach 5 states, and its 16 positions map awkwardly onto 5
  profiles. Hand access on a bare bench board is fine with a DIP actuator.
- **Pull-UP polarity is the safety-relevant half.** Open contact, unpopulated
  switch and broken contact all resolve to `1XX` = **5 V**, the lowest profile
  and the same thing an unconfigured PD sink does. Pull-downs would fail to 9 V.
- **The pull-up rail is `/VDD`** - the extract's fig 7-2 shows exactly this
  topology (R3/R5/R7 up to VDD, R4/R6/R8 down to GND, the pull-downs replaced
  here by the switch). CFG2/CFG3 are absolute-max **VDD + 0.5 V**, so they may
  never see VBUS; CFG1 is in the 8 V VIOCC class but references VDD anyway.
- **Strap resistors are mandatory, not optional**: the extract states CH224K has
  **no internal pull-ups** on CFG2/CFG3 (CH224A's 7-10-15 k pull-ups are a
  different part).
- **100 k, not 10 k.** At the 5 V profile the whole VDD node is fed by 1.7 mA
  through R2. Three 10 k pull-ups draw 990 uA - 58 % of that budget - and would
  starve a chip whose IDD is unpublished. Three 100 k pull-ups draw 99 uA (6 %).
  This is the single most consequential number the P3 extract changed.
- The pull-ups go to VDD, not to GND, so they can never be misread as a to-GND
  resistance code in the CH224's alternate single-resistor mode (V2).

**Silk (this is the user interface, so it is specified here):** the full
five-row table goes on **B.SilkS** (the bottom is a clear GND pour with room for
a 1 mm-height legend), with a compact `1 2 3` + `ON` marker beside SW1 on
F.SilkS.

| Profile | SW1-1 | SW1-2 | SW1-3 |
|---|---|---|---|
| 5 V | OFF | any | any |
| 9 V | ON | ON | ON |
| 12 V | ON | ON | OFF |
| 15 V | ON | OFF | OFF |
| 20 V | ON | OFF | ON |

(From the scout's datasheet-verified map `(CFG1,CFG2,CFG3)`: `1XX`=5, `000`=9,
`001`=12, `011`=15, `010`=20, inverted because ON shorts to GND.)

## D4 - visible fallback indication (P0 answer 6), no MCU

*(Amended A1: three LEDs, not four - the PG LED is gone and the LED supply is
`/VIND`, not a regulated rail. The window circuit itself is unchanged.)*

The CH224K's PG pin is a plain power-good output and **does not discriminate
"selected profile achieved" from "fell back to 5 V"** (scout finding). The
discriminator is therefore built from a **voltage window on VBUS**, with the LEDs
fed from `/VIND`:

- **D2 (6.2 V zener) + R6 (6k8) into Q1A's base, with R7 (4k7) base-emitter
  shunt.** Trips at Vz + Vbe ~= **6.7 V**: hard off at the 5 V profile's 5.25 V
  ceiling, hard on at the 9 V profile's 8.55 V floor. R7 is what makes it robust
  - it sinks zener knee leakage (needs > 149 uA to reach 0.7 V, versus a few uA
  of real leakage at 5.25 V) so a soft knee cannot fake a high profile. R6 at
  6k8 still delivers 243 uA of base drive at 8.55 V and only 1.93 mA / 25 mW at
  20 V.
- **Q1B inverts** (R8 10 k collector pull-up, R9 47 k base) so exactly one of
  **D5 "5V ONLY" (red, R12 1k5)** and **D6 "PROFILE OK" (green, R13 4k7)** is
  lit. Using an inverter rather than the cheaper single-transistor "current
  steal" trick is deliberate: the steal version depends on the two LEDs' forward
  voltages being ordered correctly, which is a part-substitution trap.
- **D3 "PWR"** (R10 3k3, 1206) off `/VIND` is the mandatory power-present LED.

**Why losing the regulated rail did not damage this scheme:** each window LED
conducts in exactly one voltage regime - D5 only *below* the 6.7 V trip (bus at
4.4-5.25 V, so 1.6-2.2 mA through a fixed 1k5) and D6 only *above* it (8.55-21 V,
1.4-4.0 mA through a fixed 4k7). Only the always-on D3 sees the full 4.8:1 range,
at 0.76 mA (4.4 V) to 5.8 mA (21 V) - visible at both ends with a >= 50 mcd-at-
5 mA part, which is now a P3 selection criterion.

| D3 PWR | D5/D6 | Meaning |
|---|---|---|
| on | D5 red | output is at 5 V: 5 V was selected, **or the selected profile was refused** |
| on | D6 green | output is above 5 V = **selected 9/12/15/20 V granted** |
| off | - | no VBUS |

D6 is an unambiguous "achieved" because the controller only ever has one non-5 V
request in flight: a granted request puts VBUS above the window, a refused one
leaves it at 5 V. Cost of the scheme: 1 dual NPN + 1 zener + 6 resistors +
2 LEDs, about $0.13.

**PG is left unconnected** (amendment A1), matching the datasheet's own reference
schematic. Two extract facts killed the PG LED: the manual publishes **no
absolute-maximum rating for the PG pin**, so it may not be pulled to VBUS or
`/VIND` (up to 21 V on an unrated pin); and a `/VDD`-referenced pull-up would
spend LED current out of a node whose entire budget at the 5 V profile is 1.7 mA.
Restoring it would cost a third transistor plus a level shifter for a diagnostic
("PD contract present" vs "dumb 5 V source") that the brief never asked for and
that does not change the user's next action - in both cases the output is 5 V.

Rejected: a bicolour LED with a single transistor (Vf-ordering fragility above);
a "dark = fallback" scheme with only one window LED (a dark LED is
indistinguishable from a dead LED, which is a poor way to report a wrong
voltage); a load switch that blocks the output (P0 answer 6 chose to indicate,
not block).

LED constraint P3 must honour: **Vf <= 2.2 V classes (red / yellow /
yellow-green AlGaInP) with >= 50 mcd at 5 mA.** No 2.9-3.2 V InGaN greens: at
0.76 mA on a 4.4 V bus through 3k3 they would not light at all.

## D5 - VBUS sense resistor, TVS class, bulk placement

- **R1 = 10 k in series into U1 pin 8 is mandatory.** The pin is a voltage-detect
  input with a **13.5 V absolute maximum** sitting on a 21 V rail, and the
  extract is unambiguous: "a series resistor to the external VBUS input is
  REQUIRED", 10 k in reference schematic 6.2. *(Amended A1: the P2 draft justified
  keeping the sense connection because PG drove an indicator LED. PG is now
  unconnected, so the justification is simply that the reference circuit connects
  pin 8 and voltage detection is part of the part's normal operation - the
  resistor value and its necessity are unchanged.)*
- **D1 TVS: unidirectional, >= 22 V working / ~28 V max clamp** (TDS2221PW class:
  22 V operating, 23 V min breakdown, 28 V clamp, 22 A at 8/20 us, DFN
  1.6 x 1.0 mm). **Explicitly not a 24 V SMAJ/SMBJ** - that class clamps at
  38-39 V, above the 34 V ceiling guidance and far above the CH224's 22 V
  operating limit. Low capacitance is not a consideration on VBUS. Placement: at
  the connector, first element on the net, with a short wide return and multiple
  GND vias.
- **Bulk: C1 22 uF / 50 V + C2 100 nF, on the connector side of the run** (there
  is no PTC to be "before" any more, so "connector side" is the whole
  requirement). 50 V rating, not 25 V: X5R at 20 V DC bias on a 25 V part keeps
  a fraction of its marking. Total sink bulk must stay under **cSnkBulkPd =
  100 uF**; at 22 uF the charging current during a 5 V -> 20 V transition is
  0.66 A at the source's 30 mV/us slew limit, against 3 A for 100 uF.
- **No caps on CC1/CC2** without knowing U1's own pin capacitance - the PD spec's
  CC receiver window is 200-600 pF *total*, and 200 pF is a minimum.

## D6 - canonical net names, and why there is no VOUT

**`VBUS`, `/VAUX`, `/VIND`, `/VDD`, `GND`. That is the whole list of declared
nets** (amended A1: `+3V3` is gone with the LDO; `/VIND` and `/VDD` replaced it).

With the main-path series element gone (D0.1/D1), the receptacle VBUS contacts,
the TVS, the bulk caps, all five taps and the screw terminal are **one copper
object**. Naming it `VBUS` at the connector and `VOUT` at the terminal would
invent a net boundary that does not exist in copper, and `check_current` raises
`CheckError` (exit 2) on a declared power net that is absent from the board. The
interface fragment's `VOUT` entries (which assumed the PPTC split the net) are
therefore **deduplicated INTO the `VBUS` entry** - one entry, one net, one width
rule, end to end.

`/VAUX` is genuinely a second net: F1 separates it, and it must stay separate
because `check_current` applies a net's declared current to *every* track
segment on it - an aux stub sharing `VBUS` would have to be 1.75 mm wide all the
way onto a 0.1 in header pin.

## D7 - GND stays OUT of `power[]`

GND carries the same 5 A return, and it is still **not** declared. Reason:
`check_current` checks every track segment on a declared net and demands
`ceil(5.0 / 0.5) = 10` vias per via cluster. A 2-layer board accumulates short
thin GND stubs (TVS return, decoupling, LED cathodes, test points) that would
each error, with no per-region exception available before coordinates exist at
P7 - and every GND via cluster on the board would need 10 vias.

The requirement is **structural instead**, and it is stated in `power_tree.md`
s"Structural requirements" and `stackup.md`:

- continuous, unslotted B.Cu GND pour under the entire power path (the 2-layer
  `planes_gen` default already produces exactly this pour, which is why
  `constraints.json` carries no `planes` key);
- **>= 10 vias at J1's GND pads and >= 10 at J2's GND pad**;
- receptacle pads given copper on both sides, not a thermally isolated island.

Adding `GND` with `current_a: 5.0` *after* routing, purely to exercise the pour
neckdown check, and then hand-clearing the stub violations, is a legitimate
informed choice at P8 - it is not the default and P8 should not do it silently.

## D8 - placement edges

| Ref | Edge | pos | Why |
|---|---|---|---|
| J1 USB-C | left | 0.5 | input; centred so all four VBUS contacts feed one straight run |
| J2 screw terminal | right | 0.5 | **opposite edge**: the 5 A path is one short straight run and the two hot connectors are not adjacent |
| J3 aux header | top | 0.2 | user-accessible, near the connector end, and far from J2 |
| SW1 DIP | top | 0.62 | hand access from the top edge, clear of the 5 A corridor and of J2's screwdriver |

Plus `separation: J2 <-> J3, min 15 mm` (centre-to-centre, soft term in the
annealer) - a 5 A load must not be pluggable onto the 1 A header by muscle
memory.

`rot` is deliberately omitted everywhere: `place_seed` rotates an edge cluster so
its body overhang points off-board, which is the correct answer for all four
parts, and a hand-specified angle would be a guess about footprint frames.

Groups: `window` (Q1 anchoring D2/R6-R9) keeps the detector compact; `status_leds`
(D3 anchoring D5-D6) keeps the three LEDs adjacent so they share one silk legend.
The LEDs are deliberately **not** edge-pinned - on a bare bench board they are
visible anywhere, and pinning a 0603 flush to the outline pushes its pads inside
the 0.3 mm copper-to-edge minimum.

Amendment A1 adds one separation term: **R2 (the 0.31 W dropper) stays 8 mm from
U1**, whose exposed baseplate is its only heat path.

Not expressed as constraints, but P6/P7 must honour (see V8): **the five VBUS
taps (D1, C1, C2, F1, R14) sit hugging the main run**, so their 1.75 mm-wide
stubs stay 2-3 mm long. Everything else is behind R14 on `/VIND` and routes thin.

## D9 - board outline: 45 x 25 mm

Realistic, with no through-hole PPTC to house: **45 x 25 mm** (+12.5 % on the
long axis, inside P0 answer 5's ~20 % allowance; 1125 mm2). J1's body eats
~7.3 mm from the left edge and J2's ~10 mm from the right; at 40 mm that leaves
~23 mm of mid-board for U1, SW1, the 2512 dropper, the window network and three
LEDs plus a readable silk table. 25 mm height is set by the two connectors and
does not need to grow. Hard ceiling **48 x 28 mm**; if P6 closes at 40 x 25 mm,
take it. `board_init --outline 45x25`. (A1 removed three parts but added a 2512,
so the area argument is unchanged.)

## D10 - `diff_pairs` is an EXPLICIT empty list

Not an omission. Omitting the key makes `check_diffpair` **auto-discover** pairs
by name suffix including `DP`/`DM` - and this board deliberately **shorts** the
CH224K's DP and DM pins together (PD-only mode, CH224 datasheet 5.5), which
would be reported as skew/gap violations on a node that is a short by design.
Belt and braces: that node is named **`/BC12_DIS`**, carrying no `DP`/`DM`/`_P`/
`_N` token, so even auto-discovery could not assemble a pair from it.

`high_speed` is absent for the same class of reason but with no trap: there are
no data pairs at all, CC is 300 kbit/s BMC with a ~7.5 m critical length, and a
2-layer stack has no reference plane. `check_return_path` and the `rules_gen`
impedance rules no-op cleanly.

## D11 - thermal entries

| Ref | power_w | net | dt_c | Basis |
|---|---|---|---|---|
| J1 | **0.25** | GND | 40 | Worst-case connector loss is ~0.5 W at 5 A (40 mohm max initial per contact, 4 in parallel = 10 mohm, 0.25 W on the VBUS side + 0.25 W on the GND side). The entry declares the **GND-side half**, because that is the half `check_thermal` can model - the VBUS-side half sheds into the F.Cu VBUS pour, which is not the named heatsink net. Realistic contacts (10-20 mohm) put the true figure near 0.12 W. |

*(Amended A1: the U2 entry is deleted with the LDO. J1 is now the only entry.)*

`dt_c` 40 is the model default and physically right here: a 40 C bench ambient
plus a 40 C rise is 80 C, just inside the receptacle's class.

**Why R2 (0.31 W) gets no thermal entry even though it is the largest component
loss on the board.** `check_thermal` is a junction-to-ambient screen calibrated
on IC packages (`theta_JA = 55 + 119 exp(-A / 350)` for 2-layer), and its remedy
vocabulary is "grow the pour / add thermal vias". Neither applies to a chip
resistor: the part is a **1 W 2512 carrying 0.31 W**, i.e. 3x derated by
nameplate, and its heat leaves through its own terminations. Feeding it to the
check would mean naming a heatsink net it does not have (`/VIND` and `/VDD` are
both thin stubs by design) and would produce a violation whose only "fix" is to
pour copper the design does not want. The requirement is stated structurally
instead: 2512/1 W, 8 mm from U1 (a `separation` term in `constraints.json`), and
clear of the receptacle.

J2 gets **no** entry on purpose either - its resistance band is dominated by how
hard the user tightens the screw, which no copper check can influence.

**`check_thermal` hard-errors (exit 2) on a refdes with no pads**, so J1 must
survive P4 renumbering unchanged.

## D12 - dt_c 10, not 20 (conflict resolved)

The interface fragment recommends `dt_c: 20`; the power fragment recommends
`dt_c: 10`. **Power wins**, because the interface recommendation was explicitly
contingent on 1 oz copper ("dt_c = 10 demands 3.5 mm at 1 oz, which does not fit
sensibly"). At 2 oz, dt_c 10 costs 1.750 mm - already an ordinary trace - so
there is no reason to buy back 0.56 mm of width with 10 C of copper
temperature. Every `power[]` entry uses dt_c 10 consistently.

## D13 - other research conflicts, resolved explicitly

| Conflict | Resolution |
|---|---|
| Interface emits `VBUS` **and** `VOUT` at 5 A; power emits one net | **One net, `VBUS`.** The duplicate existed only because a series PPTC was assumed. D6. |
| Interface: PTC after the controller tap, bulk before it. Power: no PTC at all | **No main-path PTC** (D0.1/D1), so the ordering question dissolves; the bulk stays at the connector, which was the shared intent of both. |
| Interface: `+3V3` is the CH224K's shunt VDD node, "not a usable logic rail", 0.02 A. Power: `+3V3` is a real LDO rail, 0.05 A | **INTERFACE wins - reversed at A1.** The P2 draft gave this to the power fragment and specified an LDO; the P3 extract confirms VDD is a shunt node an external regulator would fight. There is no logic rail on this board: the node is `/VDD`, declared at 0.02 A, and the indicators moved to `/VIND`. |
| Interface: CH224K VDD dropper = 1 k, 0.28 W, needs 2010/2512 | **Adopted verbatim at A1** (the P2 draft had superseded it with the LDO). R2 = 1 k in a 2512 1 W part, 0.279 W at 20 V / 0.313 W at 21 V. |
| Power: ESSOP-10 is "0.5 mm pitch"; scout package string is `ESSOP-10-150mil-1mm` | **Scout wins** (it read the catalogue entry): 1 mm pitch. Either way the 2 oz 0.1524 mm fab floor is not binding. |
| Interface: prefer a 16-pin/power-only receptacle without SuperSpeed pads | Adopted - eight fewer fine-pitch pads on a 5 A board, and no function lost. |

## D14 - cost picture for checkpoint 1

Rough, at prototype qty 10; `order_quote` does the real numbers at P10.

| Item | Each | Note |
|---|---|---|
| U1 CH224K | $0.39 | scout's live qty-10 break |
| J1 USB-C receptacle 16p | $0.15 - 0.35 | 5 A-collective clause required |
| J2 screw terminal 5.08 mm 2P | $0.19 | KF128 class, 24 A / 250 V |
| SW1 DIP-3, D1 TVS | $0.15 - 0.45 | two Extended parts, P3 prices them |
| F1 1 A PPTC 1206 | $0.10 | |
| Q1, D2, D3/D5/D6, J3 | $0.08 | dual NPN, zener, 3 LEDs, header |
| 13 R + 3 C (incl. 22 uF/50 V 1210, 1 k 2512) | $0.15 | |
| **BOM total** | **~$1.15 - 1.60** | A1 removed the LDO and its 2 caps and a LED+resistor; added a 0 R link |
| PCB: 2-layer, 45 x 25 mm, 1.6 mm, **2 oz**, HASL, qty 10 | ~$1.00 - 1.50 | 2 oz is a small per-order adder |
| Economy PCBA, SMT top only | ~$1.50 - 2.50 | J2 and J3 are THT, hand-soldered after |
| **Landed, per board** | **~$5 - 7** | |

Fab class: 2-layer, `2layer_2oz` rule set (min trace/clearance 0.1524 mm, min
via drill 0.3 mm, min copper-to-edge 0.3 mm). Nothing on the board approaches
those limits - the finest feature is a 1 mm-pitch ESSOP-10.

## D15 - riskiest decisions (for the human checkpoint)

*(Amended A1: the old risk 2 - sourcing a >= 30 V LDO - is retired with the LDO
itself. Risk 3 sharpened now that the extract confirms IDD is unpublished.)*

1. **No series protection in a 5 A / 100 W path** (D1). Evidence-backed and
   orchestrator-approved, but it is the one place where the board's safety rests
   on a component that is not on the board (the charger's OCP).
2. **CH224K IDD is unpublished and the 5 V profile budget is 1.7 mA** (V1). The
   whole housekeeping design - 100 k straps, no PG LED, no VDD-fed indicators -
   is rationing that budget on the strength of WCH's own reference circuit using
   the same 1 k dropper. If VDD sags at 5 V on the first article, R2 drops to
   680 Ohm (D2); if it still sags, the CFG straps and the supply topology both
   need rework.
3. **The indicator LEDs now run straight off the bus** (A1). D3's brightness
   varies 4.8:1 across profiles by design. It is visible at both ends only if P3
   honours the >= 50 mcd-at-5 mA / Vf <= 2.2 V criterion; a low-efficiency LED
   would be invisible at the 5 V profile, which is exactly the profile the
   indication scheme exists to report.

## D16 - verify-later items (carried into P3/P4/P6)

| # | Item | Owner |
|---|---|---|
| V1 | **CH224K IDD is UNPUBLISHED** (extract: 8.2.3 has no ICC/IDD row; the 1.8 mA typ / 12 mA max in 8.2.1 is CH224Q/CH224A and must not be applied). The design rations the 1.7 mA that the 1 k dropper delivers at 5 V on the strength of WCH's own reference circuit. **Measure VDD at the 5 V profile on the first article**; if it sags toward the 2.2-2.6 V POR threshold, R2 -> 680 Ohm. | P4 wiring / bring-up |
| V2 | **RESOLVED by the extract**: fig 7-2 shows the CH224K I/O-level strap topology as resistors to VDD and to GND, and 5.2.2 defines '0' = shorted to GND, '1' = high level. 100 k to `/VDD` with a switch to GND is that topology, and cannot be read as a to-GND single-resistor (Rset) code. | - |
| V3 | **RESOLVED by the extract**: the CH224K reference schematic 6.2 wires CC1/CC2 straight to the connector with **no external 5.1 k**, while CH224D (6.3) and CH221K (6.4) do show them. Fit no Rd. | - |
| V4 | **RESOLVED by the extract**: CC1/CC2/CFG1 absolute max is **8 V** (VIOCC). Consequence: **no CC TVS is fitted** - a 24 V-class CC TVS (the only kind that keeps CC capacitance legal) cannot protect an 8 V pin from a 20 V VBUS-to-CC short anyway, and a low-voltage clamp would load Rd and break source detection. The exposure is accepted and documented: a partial insert or conductive debris that shorts VBUS to CC kills U1. | - |
| V5 | **Receptacle clause**: the datasheet must say 5.00 A **collectively** across A4/A9/B4/B9, and the voltage rating must be >= 24 V (the USB4105 class is 20 V DC = zero margin). | P3 |
| V6 | **RETIRED with the LDO** (amendment A1). No regulator on the board, so no >= 30 V-input part to source. | - |
| V7 | **22 uF / 50 V 1210 post-DC-bias capacitance >= 10 uF** at 20 V; total sink bulk < 100 uF. | P3 |
| V8 | **VBUS tap stubs**: `VBUS` has exactly five taps (D1, C1, C2, F1, R14) and each must hug the main run so its 1.75 mm stub stays short; everything else is behind R14 on `/VIND`. Fallback is `power[].overrides {"near": [x,y], "radius_mm": 3, "current_a": 0.02}` once coordinates exist. | P6/P7 |
| V9 | **`rules_gen` builds one `Power` net class** at the widest declared width (1.75 mm), so `/VAUX`, `/VIND` and `/VDD` default-route fat. Per-net DRC minimums stay correct; worth a P5 hand-edit - it matters more after A1, since `/VIND` now fans out to seven parts. | P5 |
| V10 | **Silk content** is functional on this board, not decoration: the profile table (B.SilkS), `AUX 1A MAX` + `V+`/`GND` at J3, LED legends (`PWR`, `5V ONLY`, `PROFILE OK`), and the cable disclaimer "20 V @ 5 A needs a 5 A e-marked cable and a 100 W source". `check_silk` gates legibility. | P4/P9 |
| V11 | **Pin 0 vs pad 11.** The datasheet numbers U1's exposed baseplate "pin 0"; it is both the thermal pad and the **only** ground terminal. KiCad/EasyEDA ESSOP-10 footprints usually number that pad **11**. Verify symbol and footprint pad numbering before wiring - a mismatch silently leaves U1 ungrounded. | P4 (lib pull) |
| V12 | **DP/DM: shorted at the chip, or wired to the connector?** The extract reads reference schematic 6.2 as wiring DP/DM straight to the Type-C connector (the part also does legacy BC1.2/QC protocols); the interface research cites a PD-only-mode instruction to keep them off the interface and short them together, which is what this architecture specifies (`/BC12_DIS`). Resolve against manual V2.1 before wiring. Either way they must not float - a floating protocol-detect input can enable spurious handshakes. | P4 |
| V13 | **PG left unconnected** (D4). If a later revision wants the contract-present diagnostic, it needs a 100 k pull-up to `/VDD` plus a level shifter to a `/VIND`-fed LED - not a direct pull to `/VIND` (no published abs-max on the pin). | future |

---

# A1 - amendment after the P3 datasheet extracts (2026-07-28)

Trigger: P3 landed `parts/C970725.json` (CH224K, WCH manual V2.1) and
`parts/C14170.json` (L78L33ACUTR) and bounced the housekeeping design back. The
extracts overturned the P2 draft's supply topology. **Everything else in this
document stands unchanged** - the 5 A path, the missing main-path fuse (D1), the
stackup (D0.2), net naming (D6), GND handling (D7), placement (D8), outline (D9),
`diff_pairs` (D10) and dt_c (D12) are untouched.

## A1.1 What the extracts said, and what changed

| Extract fact | Consequence |
|---|---|
| VDD is an **internal shunt regulator** (3.24/3.30/3.36 V, sinks 0-30 mA), abs max 3.6 V; the reference circuit feeds it through a **1 kOhm dropper from VBUS** | **The LDO-into-VDD topology was wrong.** U2 removed; R2 becomes the 1 k dropper (D2). A +/-4 % LDO reaching 3.432 V would sit inside/above the shunt band and be sunk against. |
| The published field death used **510 Ohm = 0.55 W in a small package** | That was a **sizing** error, not a topology error. The P2 draft cited it as evidence against the dropper - **corrected**. R2 is a **2512, 1 W** part carrying 0.31 W. |
| The dropper delivers only **1.7 mA at the 5 V profile**, and **CH224K has no published IDD** | VDD is a rationed node. Nothing that draws real current may hang on it: strap pull-ups go to **100 k** (99 uA total, 6 % of budget) instead of 10 k (990 uA, 58 %); the PG LED is dropped. |
| **CFG2/CFG3 have no internal pull-ups**; abs max VDD+0.5; fig 7-2 references the straps **to VDD** | Strap resistors are mandatory and referenced to `/VDD`, never to VBUS (D3). |
| L78L33 (30 V abs max OK) has **Iq 6 mA max** and **1.7 V typ dropout with no max** | At 4.4 V low line it is **in dropout** (Vout ~2.7 V) exactly at the 5 V profile the LED rail existed to serve, and its quiescent current alone exceeds the LED load. **U2 dropped entirely** (A1.2). |
| **PG has no published absolute maximum** for CH224K, and the reference schematic leaves it NC | PG left unconnected; the PG LED and its resistor are removed (D4). |
| CC1/CC2/CFG1 abs max = **8 V**; CH224K reference wires CC with **no external Rd** | V3 and V4 resolved; no CC TVS (it cannot protect an 8 V pin from a 20 V short). |
| Baseplate is **"pin 0"**, is the only GND terminal, and libraries usually number it **11** | New verify item V11 - a numbering mismatch silently leaves U1 ungrounded. |

## A1.2 Decision: drop U2 rather than keep it as an LED-only rail

The coordinator's bounce-back left this open: keep the L78L33 for the indicators,
or run them off the bus. **Dropped, for five reasons:**

1. **Its only remaining load is three indicator LEDs** (~6 mA). Everything else
   it was justifying - VDD, the CFG references - moved to `/VDD` behind the
   dropper.
2. **It is in dropout precisely where it was supposed to help.** 1.7 V typ
   dropout (no max published) puts Vout at ~2.7 V on a 4.4 V bus, so the "stable
   brightness" argument fails at the 5 V profile and holds only over 9-20 V.
3. **Its 6 mA max quiescent current is comparable to the load it serves** and
   burns 0.12 W at 20 V - more than the LEDs themselves.
4. **The window LEDs never needed a stable rail.** D5 conducts only below the
   6.7 V trip and D6 only above it, so each has a fixed resistor sized for one
   regime. Only D3 (always on) sees the 4.8:1 range, at 0.76-5.8 mA - visible at
   both ends with the LED criterion now imposed on P3.
5. **It removes a single point of failure in the indication path** (a dead LDO
   blinds every indicator; resistors cannot), 3 parts, one net, one thermal
   entry, and the #2 checkpoint risk (sourcing a >= 30 V-abs-max LDO).

Accepted cost: D3's brightness varies 4.8:1 across profiles, and the board has no
3.3 V rail for any future feature. Both are fine for a fixed-function bench tool.

**New in its place: R14, a 0 ohm 0603 link from `VBUS` to `/VIND`** (blocks.md
B4). Without it, all eight housekeeping taps would hang directly off the 5 A net
and `check_current` would demand **1.75 mm** copper on every one of them,
including the runs out to the LED row. Behind the link, `/VIND` is declared
width-only (`"pdn": false`, 50 mA) and routes at the fab floor. It follows the
schema's own documented pattern for a stub that is declared purely so `rules_gen`
sizes it.

## A1.3 Parts delta for the sourcer (P3)

**REMOVE from the BOM (5 line items):**

| Ref | Was | Why |
|---|---|---|
| U2 | 3.3 V LDO, Vin abs max >= 30 V (L78L33ACUTR / C14170 was the candidate) | A1.2 - no regulator on the board |
| C3 | 0.33 uF LDO input cap | goes with U2 |
| C4 | 0.1 uF / 1 uF LDO output cap | goes with U2 |
| D4 | PG LED (yellow) | PG left unconnected (D4) |
| R11 | PG LED series resistor | goes with D4 |

**ADD (1 line item):**

| Ref | Part | Notes |
|---|---|---|
| R14 | **0 ohm, 0603** | VBUS -> `/VIND` housekeeping link; any current rating (carries 32 mA max) |

**CHANGE (6 line items):**

| Ref | Was | Now | Why |
|---|---|---|---|
| R2 | 47 Ohm 0603 (LDO-to-VDD isolation) | **1 kOhm, 2512, 1 W** | the datasheet's dropper; 0.313 W at 21 V needs 3x derating. Alternate: 2x 510 Ohm 1206 in series. **Not** 2x 2 k 0805 in parallel (0.157 W each in 0.125 W parts). |
| R3, R4, R5 | 10 k 0603 | **100 k 0603** | 10 k would eat 58 % of the 1.7 mA VDD budget at the 5 V profile |
| R10 | 680 Ohm 0603 (PWR LED) | **3.3 kOhm, 1206** | now bus-referenced: 0.11 W at 21 V |
| R12 | 680 Ohm 0603 (red LED) | **1.5 kOhm 0603** | conducts only at 4.4-5.25 V; 7 mW |
| R13 | 680 Ohm 0603 (green LED) | **4.7 kOhm, 0805** | conducts only at 8.55-21 V; 0.08 W |
| D3, D5, D6 | LED Vf <= 2.4 V at 2 mA | **LED Vf <= 2.2 V, >= 50 mcd at 5 mA** | must still be visible at 0.76 mA on a 4.4 V bus |

**UNCHANGED:** U1, J1, J2, J3, D1, D2, Q1 (add criterion: **Vceo >= 30 V** - Q1B's
collector floats to the bus when it is off), SW1, F1, C1, C2, C5, R1, R6, R7, R8,
R9.

Component count 32 -> **28**. BOM ~$1.30-1.80 -> **~$1.15-1.60**. Refdes gaps at
U2/C3/C4/D4/R11 are intentional - **do not renumber** (sheets.md s2).

## A1.4 Constraint-file delta

| Key | Change |
|---|---|
| `power` | `+3V3` (0.05 A) **removed**; `/VIND` (0.05 A, `pdn: false`) and `/VDD` (0.02 A, `pdn` true) **added**. VBUS and /VAUX unchanged. |
| `voltages` | `+3V3` -> `/VIND` (20 V) + `/VDD` (3.3 V) |
| `thermal` | U2 entry **removed**; J1 (0.25 W) is now the only entry. R2 deliberately not added - see D11. |
| `placement.groups` | `status_leds` loses D4 (members now D5, D6) |
| `placement.separation` | **added** `R2 <-> U1, min 8 mm` (0.31 W dropper away from the baseplate that is U1's only heat path) |
| `placement.edges` | unchanged (J1 left, J2 right, J3 top 0.2, SW1 top 0.62) |
| `diff_pairs` | unchanged - still an explicit `[]` |

`/VDD` is declared with `pdn` left true on purpose: it is what makes `check_pdn`
enforce the datasheet's mandated 1 uF (C5) on the shunt node.
