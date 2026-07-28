# Interface research: PoE PD electrical envelope + the 48 V high-voltage domain

Board: `lumina-carrier` (LUM-CAR-A). Interface: `poe-48v` - IEEE 802.3af/at **PD side**
electrical behaviour and every net in the 37-57 V domain, including the 48 V raw
pass-through to the expansion connector (D-02, CAR-REQ-17).

This is the **high-voltage half** of the Ethernet story. The 10/100 data half
(TX/RX pairs, W5500, magnetics data side) is a sibling fragment and is deliberately
absent here - see section 8 for the merge trap that creates.

Companion machine-readable fragment: `interface-poe-48v.json`.

Every number below carries a source tag `[Sn]` resolved in section 9. Numbers that
could not be sourced are marked `ASSUMED` and given a conservative value.

---

## 1. Constraint table (what binds, where it lands, who enforces it)

| # | Constraint | Value | Lands in | Enforced by |
|---|---|---|---|---|
| C1 | Worst-case voltage on the board | **57 V DC** (PSE max output) | `voltages[].voltage` | check_creepage (P8) |
| C2 | Same-layer copper spacing, 48 V domain to anything, **outer** layers | **0.60 mm** (IPC-2221B B2, 51-100 V band) | `voltages[]` + a P5 net class | check_creepage (P8) |
| C3 | Same-layer copper spacing, 48 V domain, **inner** layers | 0.10 mm (IPC-2221B B1) - below fab minimum, non-binding | `voltages[]` | check_creepage (P8) |
| C4 | Vendor corroboration of C2 | 0.635 mm (0.025 in) between VSS and VDD [S1] | layout practice | manual |
| C5 | PD input voltage range | 37-57 V (Type 1) / 42.5-57 V (Type 2) [S2] | part ratings, UVLO | manual (gate 2) |
| C6 | Converter input rating | >= 60 V with margin; **>= 80 V preferred** (see 2.4) | parts (P3) | manual (CAR-REQ-02) |
| C7 | Detection signature | 23.7-26.3 kohm + 50-120 nF; 24.9 kohm 1% external [S2] | schematic (P4) | manual (gate: PD topology) |
| C8 | Classification, build 1 = **Class 3** (af) | 26-30 mA; R_CLASS 45.3 ohm (Microchip) / 90.9 ohm (TI) [S1][S2] | schematic (P4) | manual (D-01) |
| C9 | Classification, upgrade = **Class 4** (at) | 36-44 mA; R_CLASS 30.9 ohm (Microchip) / 63.4 ohm (TI) [S1][S2] | BOM variant | manual (D-01) |
| C10 | MPS keep-alive floor | PD input current must never fall below **10 mA** (0.57 W at 57 V) | firmware + no-deep-sleep rule | manual |
| C11 | Max current the PoE source can ever deliver | 350 mA DC / 400 mA peak (af); 600 mA DC / 686 mA peak (at) [S2] | connector ICD, power tree | manual (see 5.3) |
| C12 | PD input TVS | **58 V standoff**, clamp must stay < 100 V controller abs max [S1][S2][S3][S4] | parts (P3) | manual |
| C13 | Resistor package on the 48 V domain | **0805 or larger** (0402/0603 are typically 50 V working) [S2] | parts (P3) | manual |
| C14 | Expansion connector rated voltage | **>= 57 V**, prefer >= 100 V; 2.54 mm headers are 250 V / 3 A [S8][S9] | ICD (H1) | manual (ICD-01) |
| C15 | Expansion connector pitch for the 48 V pins | **>= 2.00 mm** so the land pattern clears C2 (see 5.2) | ICD (H1) | check_creepage (P8) |
| C16 | Guard pin between 48 V and logic | GND pin mandatory-by-analysis, empty position recommended (see 5.4) | ICD (H1) | manual |
| C17 | Isolation barrier on the carrier | **none** in a non-isolated PD; 48 V and logic share one GND (see 6) | design doc | manual |
| C18 | If an isolation barrier ever exists | 2 mm (0.080 in) on FR4 for 1500 Vrms [S2] | layout | manual |
| C19 | No `high_speed` / no `diff_pairs` entries in THIS fragment | see section 8 | constraints.json | - |

---

## 2. PD electrical envelope (IEEE 802.3 clause 33)

### 2.1 af (Type 1) vs at (Type 2) - the D-01 columns

D-01: **at-sized power stage, af-classified for build 1, upgrade must be a resistor
change only.** These are the two columns that must appear in the gate-2 power budget.

| Parameter | Type 1 (802.3af) - build 1 | Type 2 (802.3at) - upgrade | Source |
|---|---|---|---|
| Guaranteed power at PD input after 100 m | **12.95 W** | **25.50 W** | [S2] Table 1-2 |
| PD input voltage range | **37 - 57 V** | **42.5 - 57 V** | [S2] Table 1-2 |
| Max DC current at PD input | **350 mA** | **600 mA** | [S2] Table 1-2 |
| PSE output voltage | 44 - 57 V | 50 - 57 V | [S2] Table 1-1 |
| PSE guaranteed current | 350 mA DC, up to **400 mA peaks** | 600 mA DC, up to **686 mA peaks** | [S2] Table 1-1 |
| Max cable loop resistance | 20 ohm | 12.5 ohm | [S2] Table 1-1 |
| Physical-layer classification | mandatory for the PD (no class = Class 0) | mandatory, **Class 4** | [S2] Table 1-2 |
| **2-event classification** | not required | **MANDATORY** | [S2] Tables 1-1/1-2 |
| Class programmed for this build | Class 3 (6.49-12.95 W) | Class 4 (12.95-25.5 W) | [S1] Table 1, [S2] Table 1-3 |

**The upgrade lever is only a resistor if the controller is Type 2 capable.** Type 2
requires the PD to *recognise 2-event classification* and assert an AT flag - that is
silicon, not a resistor [S2]. See section 10, open item O-1: the requirements' power
budget cites the Skyworks Si3402-B, and its datasheet says plainly *"The Si3402
supports IEEE 802.3 Type 1 (Class 3 and below) Powered Device applications"* [S4].
Choosing it makes D-01's "no respin" upgrade impossible.

### 2.2 Detection

- PSE applies test pulses **2.80 - 10.0 V** [S2].
- Valid PD signature: differential resistance **23.7 - 26.3 kohm** and input capacitance
  **50 - 120 nF** [S2]. Standard implementation: **24.9 kohm 1%** detection resistor
  ([S2]; TI uses R_DEN = 24.9 kohm for 802.3at compliance [S1]) plus an **82-100 nF /
  100 V ceramic** across the port [S2].
- The detection resistor is switched out by the controller once powered, so it may be a
  low-voltage (0402/0603) part - it only ever sees <= 12.8 V [S2].

### 2.3 Classification

- Class finger: PSE raises the port to **15.5 - 20.5 V**; the PD draws a constant class
  current [S2]. (Measured at the PD, [S2] Table 1-3 note says 14.5-20.5 V.)
- Mark event (between fingers): PSE drops to **6.3 - 10.1 V** [S2].

| Class | PD class current min / nom / max | R_CLASS (Microchip) [S2] | R_CLS (TI TPS2378) [S1] | PD power band [S1] |
|---|---|---|---|---|
| 0 | 0 / - / 4 mA | not installed | 1270 ohm | 0.44 - 12.95 W |
| 1 | 9 / 10.5 / 12 mA | 133 ohm | 243 ohm | 0.44 - 3.84 W |
| 2 | 17 / 18.5 / 20 mA | 69.8 ohm | 137 ohm | 3.84 - 6.49 W |
| **3 (build 1)** | **26 / 28 / 30 mA** | **45.3 ohm** | **90.9 ohm** | **6.49 - 12.95 W** |
| **4 (upgrade)** | **36 / 40 / 44 mA** | **30.9 ohm** | **63.4 ohm** | **12.95 - 25.5 W** |

R_CLASS values are **part specific** (they absorb the controller's own bias current) -
take them from the datasheet of the part actually chosen, never from another vendor's
table. The two columns above differ by 2x for exactly this reason.

### 2.4 Power-up, inrush, UVLO

- Isolation/hot-swap switch turns **on at >= 42 V**, **off below 30.5 V** [S2]. TI's
  equivalent: UVLO rising 36.3-40.0 V, falling 30.5-33.6 V [S1].
- PD inrush is actively limited: **<= 350 mA** (Type 1, [S2] p10); TI's part limits to
  **140 mA typ (100-180 mA)** [S1]. Type 2 inrush limit is quoted as 450 mA in the
  802.3bt literature - `ASSUMED` (secondary source [S10]), not needed for build 1.
- **80 ms inrush-to-operating-state delay is required by IEEE 802.3** [S2] - anything
  the carrier enables downstream (the 48 V high-side switch to the daughter) must not
  fire before that delay expires.
- Max PD bulk capacitance is a **part** limit, not a free choice: 240 uF for the
  Microchip family [S2]. Oversized bulk both stalls inrush and can trip the PSE.
- Controller absolute maximum on the port pins: **100 V** ([S1] VDD/RTN -0.3..100 V;
  [S4] CT/SP -100..100 V). This is what sets the TVS clamp ceiling (section 4).
- **C6 rationale:** 57 V is the steady-state maximum, but the rail is behind a TVS that
  clamps in the 90 V region and behind a hot-swap FET rated 100 V. A 60 V converter has
  3 V of margin on a rail whose own controller is rated 100 V. Recommend an input
  rating of **>= 80 V** (100 V preferred) rather than the literal ">= 60 V" of
  CAR-REQ-02. This is a recommendation, not a re-opening of CAR-REQ-02.

### 2.5 Maintain Power Signature (MPS)

`ASSUMED` sourcing: the exact clause text is behind the IEEE paywall; the values below
are consistent across two independent secondary sources [S10].

- **DC MPS: >= 10 mA**, presented either continuously or as a >= 10 mA pulse of at least
  **75 ms** duration at least once every **325 ms**.
- AC MPS component: PD AC impedance below **26.3 kohm in parallel with 0.05 uF**.
- A PSE that sees no MPS for roughly **300-400 ms** removes port power.
- MPS current for Classes 1-4 is 10 mA (Classes 5-8 use 16 mA - not applicable here).

**Design consequence for this board (computed):** 10 mA at 57 V = **0.57 W**. The
carrier's own overhead budget is 1.5 W (requirements 3.2) = ~26 mA at 57 V, so MPS is
satisfied by normal operation and **no dummy load is needed**. The constraint is
therefore a *negative* one: **no sleep/standby mode may take total PD input current
below 10 mA**, or the PSE drops the port and the fixture reboots. Record it against the
firmware watchdog behaviour (requirements section 1).

---

## 3. Creepage and clearance for the 48 V domain (the load-bearing section)

### 3.1 The numbers

IPC-2221B Table 6-1, electrical conductor spacing, DC or AC-peak **between** the two
conductors. 48 V (nominal) and 57 V (worst case) fall in the 31-50 V and 51-100 V
bands respectively and, for the two columns that matter, **give the same answer**:

| Column | Meaning | 31-50 V | **51-100 V (57 V worst case)** |
|---|---|---|---|
| B1 | Internal conductors | 0.10 mm | **0.10 mm** |
| **B2** | **External conductors, uncoated, sea level to 3050 m** | 0.60 mm | **0.60 mm** |
| B3 | External conductors, uncoated, above 3050 m | 0.60 mm | 1.50 mm |
| B4 | External conductors, **permanent polymer coating** | 0.13 mm | 0.13 mm |

Source [S5] / [S5b]. [S5b] is the same table the pipeline's `check_creepage.py`
transcribes, so the checker and this document agree by construction.

**Design number: 0.60 mm on F.Cu and B.Cu, 0.10 mm on In1.Cu/In2.Cu.**

Three corroborations that 0.6 mm is the right practical figure:

1. TI recommends **0.025 in = 0.635 mm** between VSS and high-voltage signals such as
   VDD on a PD front end [S1].
2. The inner-layer 0.10 mm is *below* JLCPCB's own minimum clearance (0.127 mm at 1 oz),
   so on inner layers the **fab minimum dominates** and the HV requirement is free.
3. 0.60 mm is ~4x the fab minimum on outer layers, so it is a real design constraint
   that will not be met by accident.

### 3.2 Do NOT claim the coated column

B4 (0.13 mm) requires a *permanent polymer coating*. **Do not claim it on the strength
of soldermask alone:**

- Soldermask over a narrow gap is not a guaranteed void-free dielectric, and JLC's
  standard LPI mask is not qualified as a conformal coating.
- Decisive for this pipeline: `check_creepage.py` implements **only B2 and B1**. A layout
  designed to 0.13 mm on the strength of soldermask will **fail the P8 gate** with no
  way to waive it short of editing the checker. Design to 0.60 mm.

### 3.3 Creepage vs clearance, and whether anything above "functional" applies

**Plain answer: functional insulation only. No safety-mandated creepage applies.**

- 57 V DC is below the IEC 62368-1 **ES1** limit of **60 V DC** (subclause 5.2.1.1,
  <= 60 V at > 2 mA) [S6]. ES1 is the class that is not capable of causing an electric
  shock, so no basic/supplementary/reinforced safeguard is required between the 48 V
  domain and anything a person could touch. The same 60 V threshold appears in IEC
  62368-1 LPS (Table Q.1, <= 60 V open circuit) and IEC 61140 SELV (5.2.6, touch voltage
  <= 60 V in dry locations) [S6].
- Therefore the 48 V-to-logic spacing is **functional insulation**: it exists to prevent
  arcing/tracking and to protect the logic, not to protect a person. IPC-2221B Table 6-1
  is the governing number, and IPC-2221 does not separate creepage from clearance -
  0.60 mm covers both at this voltage.
- No IEC 60664-1 creepage computation is invoked. If a formal 62368-1 assessment is ever
  required it is a **system**-level activity (enclosure, cabling, the PSE's own mains
  isolation), not a board-level one.

### 3.4 What changes if the converter is non-isolated

Q5 default (PROVISIONAL, human unconfirmed): **non-isolated buck, plastic enclosure,
Ethernet the only external connection.**

What does **not** change: the ES1 classification and the 0.60 mm functional spacing. The
voltage is the same either way.

What **does** change, and it is the whole ball game:

1. **There is no isolation barrier on the board at all** (section 6). "48 V to logic" is
   not a barrier to be crossed by an isolator - it is spacing within one continuous
   circuit whose reference is the PoE return.
2. IEEE 802.3 requires the PD to provide isolation **between the MDI leads (the RJ-45
   input) and all accessible external conductors, including any frame ground** [S3
   sec 4], withstanding 1500 Vrms / 2250 Vdc / 1500 V 10/700 us impulse [S3 sec 1].
   With a non-isolated converter the DC-DC cannot provide that. Microchip states it
   directly: *"The PoE domain has to have 1500 V AC isolation from earth ground and from
   user accessible parts... With non-isolated designs, the end application would have to
   provide this isolation."* [S2 p7].
3. So the requirement is satisfied **only** by there being no accessible external
   conductor: non-conductive enclosure, no chassis earth, no second port, no exposed
   metal bonded to board GND. The Q5 default is not a convenience - it is the
   compliance argument. If any of those three facts changes, the converter must become
   isolated (or that second port must be isolated). Flagged as O-2/O-3 in section 10.
4. If an isolated flyback is ever chosen instead, the on-board barrier spacing is a
   **completely different number**: minimum **0.080 in = 2.0 mm** on FR4 between traces
   either side of a 1500 Vrms barrier [S2 p22]. Do not confuse 0.6 mm (functional,
   inside one domain) with 2.0 mm (barrier, between two domains).

### 3.5 Component working voltage, not just spacing

Spacing is not the only 57 V constraint. From [S2 p22]: *"PoE signals contain voltages
up to 57 VDC. Component working voltage must be considered... 0402 and 0603 resistors
have typical maximum working voltage specifications of 50 V, whereas 0805 resistors are
typically specified at 150 V."*

**Any resistor that sits across the 48 V domain must be 0805 or larger** (or split into
two in series). This bites the classification resistor's neighbours, any bleed/discharge
resistor, and any 48 V divider for rail sensing. The detection resistor is exempt - the
controller disconnects it above ~12.8 V [S2]. Capacitors on the port must be 100 V rated
[S2].

---

## 4. Surge and transient expectation on the PD input

### 4.1 What the standard demands

IEEE 802.3 requires the PD to withstand at least one of [S3 sec 1]:

- 1500 Vrms at 50-60 Hz for 60 s (per IEC 60950-1 subclause 5.2.2), or
- 2250 Vdc for 60 s, or
- ten 1500 V, 10/700 us impulses at >= 1 s intervals (IEC 60950-1 Annex N).

For a non-isolated PD this is a system-level statement (see 3.4), not a board test.

### 4.2 What the environment demands

IEC 61000-4-5:2005 Table A.1, symmetrical communication lines, all-lines-to-ground
coupling [S3 Table 3]:

| Installation class | Test level |
|---|---|
| 1 (protected) | 500 V |
| 2 (partly protected, indoor, no parallel power runs) | 1000 V |
| 3 | 2000 V |
| 4-5 (harsh / outdoor) | 2000-4000 V |

An indoor basement/garage fixture on a short indoor CAT-5 run (requirements section 4)
is **class 1-2, i.e. 500-1000 V**. `ASSUMED` - no brief states an EMC target.

Resulting per-line surge current from the 8-wire test setup [S3 Table 2]:

| Open-circuit voltage | All 8 lines shorted | One line shorted |
|---|---|---|
| 500 V | 1.56 A | 2.33 A |
| **1000 V** | **3.13 A** | **4.65 A** |
| 2000 V | 6.25 A | 9.30 A |

### 4.3 The protection constraint

**Mandatory: a 58 V TVS across the rectified PD input (bridge outputs, VPP to the raw
negative), physically at the front end, before the PD controller.**

- Microchip: *"a 58 V TVS (such as SMBJ58A or equivalent) should be connected between
  VPP pin and VPNIN"* for basic protection against transients < 1 kV, both 10/700 us and
  1.2/50 us [S2].
- TI: a 58 V TVS across the input rails of the PD/DC-DC controller *"should be included
  as a minimum requirement for all of the test levels"* [S3 sec 5].
- **Why 58 V:** the standoff must sit above the 57 V maximum port voltage so the TVS
  never conducts in normal operation, and the clamp must stay below the controller's
  100 V absolute maximum [S1][S4].
- **Sizing check (computed):** SMAJ58A (400 W) is V_RWM 58 V, V_BR 64.4-71.2 V at 1 mA,
  **V_C 93.6 V at I_PP 4.3 A**, 10/1000 us [S7b]. 93.6 V leaves only **6.4 V of margin**
  to the 100 V absolute maximum, and 4.3 A is **below** the 4.65 A per-line peak a 1 kV
  class-2 surge delivers into one shorted line [S3 Table 2]. **Prefer the 600 W SMBJ58A**
  - which is the part Microchip actually names [S2] - and confirm its I_PP at P3.
- **The unearthed-PD dividend:** with no earth connection there is no inviting return
  path for a common-mode surge. TI: *"the normally-used input filter and TVS devices
  included at the front-end of a PD... should also serve to provide adequate lightning
  surge protection for unearthed PD applications"* [S3 sec 3]. The MOV-to-earth network
  ([S3] SPD2-SPD5) that an earthed PD needs is **not applicable** here and must not be
  copied from reference designs. This is a direct, and cheap, consequence of the Q5
  default.
- **If the controller already integrates it:** Si3402-B *"integrates the required diode
  bridges and transient surge suppressor"* [S4]. Check the chosen part before adding a
  redundant external TVS - but note that an integrated suppressor is sized for the chip,
  not necessarily for a 1 kV line surge.
- **ESD:** a PD front end is expected to survive system-level ESD applied between the
  RJ-45, the adapter and the output rails - TI claims 15 kV air / 8 kV contact per
  EN 61000-4-2 for the TPS2378 [S1]. Do not add ESD diodes to the 48 V domain that are
  rated below 57 V working.
- **Bob Smith termination:** the unused/PHY-side centre taps terminate through 75 ohm
  resistors and a capacitor to a "chassis" node; in an unearthed design that node is an
  isolated copper island tied to GND through a high-voltage cap (2 kV class) [S3 Fig 5].
  It is a magjack-pinout item for P4, listed here so it is not forgotten.

---

## 5. The expansion connector's 48 V spacing implication (ICD-01 input)

This section is written to be liftable into `architecture/connector-icd.md` at H1.

### 5.1 Connector rated voltage - a real disqualifier

The connector's own **rated (working) voltage must be >= 57 V**, not >= 48 V. Prefer
>= 100 V so the TVS clamp region is also covered.

| Candidate class | Rated voltage | Rated current | Verdict | Source |
|---|---|---|---|---|
| 0.4 mm pitch mezzanine (Hirose DF40) | **50 V AC/DC** | 0.3 A | **DISQUALIFIED** on both counts | [S7] |
| 2.54 mm dual-row header | **250 V AC/DC**, DWV 600 V AC 1 min | **3 A** | qualifies | [S8] |
| 2.54 mm header (Harwin M20) | not published on the product page | 3 A max/contact | qualifies on current | [S9] |

The DF40 line is the point of the table: a fine-pitch mezzanine connector that looks
perfect for a stacked daughter is **rated 50 V** and would be a silent violation at
57 V. Any candidate part must have its rated-voltage clause read, not assumed.

### 5.2 Land-pattern spacing - the number that binds

The **PCB land pattern**, not the connector body, is what `check_creepage` measures. Each
48 V pad must clear every neighbouring pad by **>= 0.60 mm** (C2). Computed pad-to-pad
gaps (gap = pitch - pad diameter):

| Pitch | Typical pad | Gap | Meets 0.60 mm? |
|---|---|---|---|
| 2.54 mm THT | 1.60 mm round | **0.94 mm** | yes, comfortable |
| 2.54 mm THT | 1.70 mm round | 0.84 mm | yes |
| 2.00 mm THT | 1.20 mm round | 0.80 mm | yes |
| 1.27 mm | 0.80 mm | 0.47 mm | **no** (needs pad <= 0.67 mm, zero margin) |
| 0.50 mm SMT | 0.30 mm | 0.20 mm | **no** |

**Recommendation: >= 2.00 mm pitch for the 48 V pins; 2.54 mm if the pin budget allows.**
1.27 mm is only possible with deliberately shrunk pads and no margin; anything at or
below 1.00 mm pitch is out. A 2.54 mm THT dual-row header also satisfies CAR-REQ-16
(shrouded + keyed variants exist), CAR-REQ-13 (3 A/contact [S8][S9]) and requirements
section 7's "no exotic processes".

Also applies **through the board**: a signal on an inner layer or the opposite face
passing under a 48 V pin's antipad needs the same clearance (0.10 mm inner / 0.60 mm on
B.Cu). check_creepage checks every copper layer independently.

### 5.3 Current rating - the ICD must not over-promise

Q6's default asks for "48 V raw 2 A continuous with 3 A capability". **The PoE source
physically cannot deliver that.** From [S2] Tables 1-1/1-2:

- Type 1 (build 1): 350 mA DC at the PD, 400 mA peak from the PSE.
- Type 2 (upgrade): 600 mA DC, 686 mA peak.

Anything above ~0.4 A (af) / ~0.7 A (at) on the 48 V raw pin must come from **local
capacitance**, and the carrier deliberately holds none beyond the PD controller's own
bulk (<= 240 uF part limit [S2]). Sustained overdraw trips the PSE's current limit and
the port drops.

Consequence for CAR-REQ-13 (">= 50 % margin over worst-case daughter draw"): a 3 A-rated
contact is fine and cheap, and gives enormous thermal margin - **keep it**. But the ICD
text must state the *source* limit, not just the *contact* limit, or a daughter designer
will size a cap bank against 2 A of continuous 48 V that will never arrive. Suggested
ICD wording: *"48 V raw: contact rated 3 A; source limited to 0.35 A DC / 0.40 A peak
(af build) and 0.60 A DC / 0.686 A peak (at upgrade). Charging current above this must
be governed in firmware."* This is the hardware half of the "average-energy governor"
already required by requirements section 3.2.

### 5.4 Guard pin: required by analysis, not by standard

**No standard mandates a guard pin.** IPC-2221B specifies spacing only, and IEEE 802.3
says nothing about a PD's internal connectors. So this is engineering practice - but the
failure analysis makes it close to mandatory:

- The failure mode is **57 V on a 3.3 V logic pin**, which destroys the ESP32-S3 or the
  daughter's silicon instantly and unrecoverably. Realistic mechanisms: a solder bridge
  at assembly, conductive debris, flux residue tracking, or a partially seated connector.
  CAR-REQ-16's keying prevents a gross one-position offset; it does not prevent a bridge.
- **A GND pin adjacent to the 48 V pin converts that failure into a 48 V-to-GND short**,
  which the carrier's current-limited high-side switch already has to survive under
  CAR-REQ-14. That is the whole argument: it turns an unbounded fault into the one fault
  the design is already required to tolerate.
- **An empty (depopulated) position multiplies the spacing**: at 2.54 mm pitch it turns a
  0.94 mm gap into 3.48 mm. Cheap if the pin budget allows.
- Recommended arrangement for the ICD:
  1. Put the 48 V raw pin(s) at **one end** of the connector, never in the middle of the
     signal field.
  2. **GND on both sides** of every 48 V pin.
  3. At least one **GND pin plus, budget permitting, one empty position** between the
     48 V group and the first logic pin.
  4. Order the rails 48 V -> 12 V -> 3.3 V along the connector so adjacent pins are never
     more than one rail step apart (D-02's 48 -> 12 -> 3.3 chain, applied to pin order).
  5. Do not rely on mating sequence: a 2-row header has no first-mate/last-mate control,
     so the ICD must state that the daughter tolerates 48 V arriving before or after
     3.3 V.
- CAR-REQ-17's second half (every 48 V-tapping daughter carries a bleed path) is a
  **daughter** obligation, but it belongs in the ICD text because the carrier freezes the
  ICD. The carrier must not defeat it - i.e. no series diode on the 48 V pin that would
  strand the daughter's stored charge above the carrier's own bleed path.

---

## 6. Isolation barrier: where it is, and what the magjack actually protects

**Answer to "do the 48 V domain and the logic domain share a ground": YES, in a
non-isolated PD they are one ground.**

### 6.1 Where the barrier is (and is not)

- In a **non-isolated (buck) PD there is no isolation barrier anywhere on the carrier**.
  The board's logic GND is the PD return (the switched negative, downstream of the
  hot-swap FET), which is DC-connected through the input bridges to the Ethernet pair
  conductors. Every net named GND on this board floats at PoE potential relative to earth.
- The Si3402-B and the Microchip/TI parts all support both topologies [S2][S4]; the
  topology choice (Q5) is what decides whether a barrier exists at all.
- In an **isolated (flyback) PD** the barrier is the DC-DC transformer, and it needs
  2.0 mm of FR4 spacing plus a Y-capacitor across it [S2][S3].

### 6.2 What the magjack's 1500 Vrms actually does

An RJ45 with integrated magnetics isolates the **cable-side windings from the PHY-side
windings**. In a PD:

- **It protects the PHY.** The W5500's TX/RX pins are transformer-coupled and DC-blocked,
  so they never see the 48 V that sits on the pairs, nor the cable's common-mode voltage.
  That is real and valuable protection, and it is why the data half of this interface can
  ignore the 48 V entirely.
- **It does not isolate the board from the cable.** PoE power is tapped from the
  **cable-side centre taps** (Mode A) and the spare pairs (Mode B), and those taps go
  straight into the input bridges. In a non-isolated PD that path galvanically connects
  the board's power domain - and therefore its logic ground - to the cable conductors.
  The transformer's 1500 Vrms rating is bypassed by design, by the PoE tap itself.
- Net effect: **the magjack protects the PHY from the power, not the board from the
  cable.** The thing that keeps a person safe is that 57 V DC is ES1 [S6] and the PSE
  inside the switch is mains-isolated - not the magjack.

### 6.3 What must therefore be true of the system (Q5, PROVISIONAL)

IEEE 802.3 wants isolation between the MDI and *all accessible external conductors,
including any frame ground* [S3 sec 4]. With no barrier on the board, that is satisfied
only by there being **no accessible external conductor**:

- Non-conductive enclosure (Q5 default: plastic/3D-printed). **Load-bearing.**
- No chassis earth, no earthed mounting hardware bonded to board GND.
- Ethernet is the **only** external connection (Q5 default). **Load-bearing.**
- Everything downstream of the expansion connector is at PoE potential too - including
  the daughter, its LED drivers and **its LED wiring**.

Two live consequences the architect must resolve - see O-2 and O-3 in section 10.

---

## 7. What this fragment emits to constraints.json

```json
"voltages": [
  {"net": "V48_RAW",    "voltage":  57},
  {"net": "V48_SW",     "voltage":  57},
  {"net": "V48_RTN",    "voltage": -57},
  {"net": "POE_TAP_A1", "voltage":  57},
  {"net": "POE_TAP_A2", "voltage":  57},
  {"net": "POE_TAP_B1", "voltage":  57},
  {"net": "POE_TAP_B2", "voltage":  57}
]
```

| Net (proposed) | What it is | Declared V | Why |
|---|---|---|---|
| `V48_RAW` | rectified PoE positive, bridge outputs -> PD controller VDD/VPP -> converter input | +57 | PSE maximum |
| `V48_SW` | switched/fused 48 V to the expansion connector (CAR-REQ-14) | +57 | the D-02 pass-through; its connector pad is the spacing-critical one |
| `V48_RTN` | PD **raw** negative (bridge negative, PD controller VSS/VPNIN), **upstream** of the hot-swap FET | **-57** | see below |
| `POE_TAP_A1/A2` | cable-side centre taps of the two data pairs (Mode A power) | +57 | at PoE potential, either polarity |
| `POE_TAP_B1/B2` | spare pairs 4/5 and 7/8 (Mode B power) | +57 | at PoE potential, either polarity |

**Why `V48_RTN` is declared negative.** `check_creepage` works on the *difference*
between declared voltages, and treats every unlisted net as 0 V. Board GND is the
*switched* negative (the hot-swap FET's drain), and the datasheet specifies that node as
sitting **0 to 57 V above** the raw negative ([S1] recommended operating conditions:
"RTN, VDD input voltage range 0 to 57 V" with respect to VSS). So relative to board GND,
the raw negative can be 57 V **below**. Declaring it as -57 makes the checker demand
0.60 mm between the raw negative and GND - which is exactly the hot-swap FET's
drain-to-source spacing, the detection/classification resistor network, and the bridge
negative. Declaring it as 0 would silently skip all of that.

Side effect, deliberate and harmless: `V48_RAW` to `V48_RTN` then reads as 114 V, whose
IPC band gives the same 0.60 mm on outer layers and 0.20 mm (instead of 0.10 mm) on
inner - conservative, and still below the fab minimum.

**Net names are proposals.** `netlist_audit` (P4) raises `missing_net` at **error**
severity for any `voltages[].net` absent from the netlist, so every name above must be
reconciled with the sheet plan before P4, or deleted. Names are written bare
(power-symbol style, like `+3V3`/`GND`/`VBUS`); if any of these ends up as a local label
instead, it needs a leading `/`.

---

## 8. Deliberate omissions (merge trap - read before merging)

This fragment emits **only** `voltages` and `notes`. `high_speed` and `diff_pairs` are
**omitted, not empty**, and that is deliberate:

- The Ethernet data pairs belong to the sibling `interface-ethernet` fragment. If this
  file carried `"diff_pairs": []` and the architect merged fragments with a dict update,
  the empty list could **clobber** the sibling's pairs - and per
  `reference/constraints_schema.md`, *an explicit empty `diff_pairs` list disables
  `check_diffpair` entirely*. Omitting the key cannot cause either failure.
- Same reasoning for `high_speed`: absent and empty are semantically identical to the
  checkers, but only "absent" is safe against a naive merge.
- Nothing in the 48 V domain is high-speed. The PoE rail is DC; the fastest edges are the
  DC-DC switching node (a `thermal`/`power` concern owned by the power-architect, not a
  transmission-line one) and the classification/detection handshake, which is measured in
  milliseconds.

`power[]` entries for the 48 V rails (currents, widths) are the **power-architect's**
fragment, not this one. Section 5.3's source-current limits are the input that fragment
needs.

---

## 9. Sources

- **[S1]** Texas Instruments, *TPS2378 - IEEE 802.3at PoE High-Power PD Interface*,
  SLVSB99A, March 2012. https://www.ti.com/lit/ds/symlink/tps2378
  (Table 1 class resistors; recommended operating conditions incl. "RTN, VDD 0 to 57 V";
  abs max 100 V; inrush 140 mA typ; UVLO; the 0.025 in VSS-to-VDD clearance
  recommendation; 15 kV/8 kV system ESD per EN 61000-4-2.)
- **[S2]** Microchip, *AN3471 - Designing a Type 1/2 802.3 or HDBaseT Type 3 Powered
  Device using PD702x1 and PD701x1*, DS00003471A, 2020.
  https://ww1.microchip.com/downloads/en/Appnotes/AN3471-Designing_a_PoE_PD_using_PD702x1_and_PD701x1.pdf
  (Table 1-1 PSE, Table 1-2 PD, Table 1-3 classification; detection 23.7-26.3 kohm /
  50-120 nF / 24.9 kohm; 58 V SMBJ58A TVS; 2 mm barrier for 1500 Vrms; 0402/0603 = 50 V
  working; non-isolated isolation statement; 240 uF bulk limit; 80 ms delay.)
- **[S3]** Texas Instruments, *SLUA736 - Lightning Surge Considerations for PoE Powered
  Devices*, March 2015. https://www.ti.com/lit/an/slua736/slua736.pdf
  (IEEE electrical strength tests; IEC 61000-4-5 Table A.1 levels; per-line surge
  currents; unearthed-PD guidance; 58 V TVS as the minimum requirement; the "isolation
  between MDI leads and all accessible external conductors" statement.)
- **[S4]** Skyworks, *Si3402-B - Fully-Integrated IEEE 802.3-Compliant PoE PD Interface
  and Low-EMI Switching Regulator*, Rev 1.1, August 2021.
  https://www.skyworksinc.com/-/media/Skyworks/SL/documents/public/data-sheets/Si3402-B.pdf
  ("supports IEEE 802.3 Type 1 (Class 3 and below)"; VPORT 2.8-57 V; abs max +/-100 V;
  integrated bridges + surge suppressor; isolated and non-isolated topologies.)
- **[S5]** Sierra Circuits / protoexpress, *Applying IPC-2221 Standards in Circuit Board
  Design*. https://www.protoexpress.com/blog/ipc-2221-circuit-board-design/
  (Table 6-1 extract: 31-50 V and 51-100 V rows, internal / external uncoated / >3050 m /
  coated.)
- **[S5b]** smpspowersupply.com, *IPC-2221B PCB Trace Spacing / Clearance by Voltage*.
  https://www.smpspowersupply.com/ipc2221pcbclearance.html - the same table the
  pipeline's `check_creepage.py` transcribes (columns B1/B2/B4).
- **[S6]** IEEE 802.3 PDCC ad hoc, *ES1, LPS and SELV voltage and source requirements
  summary*, v1.5, August 2021.
  https://www.ieee802.org/3/ad_hoc/PDCC/public/2021/ES1_LPS_SELV_1_0821.pdf
  (IEC 62368-1 5.2.1.1 ES1 dc limit <= 60 V at > 2 mA; LPS Table Q.1 <= 60 V open
  circuit; IEC 61140 SELV 5.2.6 <= 60 V touch voltage in dry locations.)
- **[S7]** Hirose DF40 series, 0.4 mm pitch board-to-board: rated 50 V AC/DC, 0.3 A,
  withstanding 150 V AC 1 min. https://info.hirose.com/products/df40 (via distributor
  specification summaries).
- **[S7b]** Littelfuse SMAJ58A (400 W SMA TVS): V_RWM 58 V, V_BR 64.4-71.2 V at 1 mA,
  V_C 93.6 V at I_PP 4.3 A, 10/1000 us, unidirectional, DO-214AC.
  https://www.utmel.com/components/smaj58a-tvs-diodes-features-pinout-and-datasheet?id=1266
  (secondary transcription of the Littelfuse SMAJ datasheet - re-verify against
  littelfuse.com at P3.)
- **[S8]** Multicomp 2213R series 2.54 mm double-row header (Farnell datasheet V1.0,
  2018): 3 A AC/DC, 250 V AC/DC, withstanding 600 V AC 1 min, insulation resistance
  1000 Mohm, contact resistance 20 mohm, -40 to +105 C.
  https://www.farnell.com/datasheets/2585485.pdf
- **[S9]** Harwin M20-8762042, 2.54 mm pitch vertical pin header: 3 A max per contact.
  https://www.harwin.com/products/M20-8762042
- **[S10]** MPS values (10 mA DC, 75 ms per 325 ms, 26.3 kohm || 0.05 uF AC component,
  ~300-400 ms PSE dropout, 10 mA for Classes 1-4): consistent across Microchip Developer
  Help's 802.3bt feature notes and Sifos Technologies' PSE MPS process analysis.
  **Secondary sources - the clause text is paywalled.** Marked ASSUMED in 2.5.

Pipeline references (not external): `reference/constraints_schema.md`,
`scripts/check_creepage.py`, `scripts/netlist_audit.py`, `scripts/rules_gen.py`,
`reference/stackups.yaml`.

---

## 10. ASSUMED, unsourced, and open

| ID | Item | Status |
|---|---|---|
| A-1 | MPS current/timing (section 2.5) | `ASSUMED` from secondary sources [S10]; the design rule (never below 10 mA) is conservative either way |
| A-2 | Type 2 inrush limit 450 mA | `ASSUMED` [S10]; not needed for the af build |
| A-3 | EMC target = IEC 61000-4-5 installation class 1-2 (500-1000 V) | `ASSUMED` - no brief states an EMC requirement |
| A-4 | IPC-2221B columns A5/A6/A7 (component lead/termination spacing) | **not publicly sourceable**; deliberately not used. Section 5 governs connector pins by the connector's own rated voltage plus B2 on the land pattern, which needs no A-column number |
| A-5 | SMAJ58A clamping numbers | secondary transcription [S7b]; re-verify at P3 |

**Open questions for the architect (also in the JSON `notes` and the OPEN block):**

- **O-1 (blocks D-01).** The requirements' power budget cites Skyworks AN956 / Si3402-B,
  but the Si3402-B datasheet states it supports **Type 1 (Class 3 and below) only** [S4].
  D-01 requires an at-sized stage whose upgrade is a **resistor change with no respin**.
  Type 2 additionally requires 2-event classification recognition, which is silicon, not
  a resistor [S2]. Either the PD controller must be a Type 2 part (TPS2378 class, or
  Microchip PD70201/PD70211 class), or D-01's "no respin" promise is void. This is a
  P2/P3 part decision, but it is a **D-01 conformance** question, not a preference.
- **O-2 (Q5 / Q4a interaction).** Q4a's default puts the LEDs on a **separate module on
  its own heatsink, wired to the daughter**. In a non-isolated PD that heatsink and its
  wiring are at PoE potential and are plausibly *accessible external conductors*, which
  IEEE 802.3 requires to be isolated from the MDI [S3 sec 4]. If the LED module is
  touchable, or metal, or shares a heatsink with anything earthed, the non-isolated
  topology is non-conformant. Needs an explicit answer before P2 commits the converter.
- **O-3 (Q9 interaction).** The default firmware-recovery answer is an internal
  UART/BOOT header. A USB-serial adapter plugged into an earthed laptop **is** a second
  earthed connection to a board floating at PoE potential. Either state in the design doc
  that the recovery header is used only with PoE disconnected, or specify an isolated
  USB-UART adapter. Not a board change; it is an ICD/design-doc line item.
- **O-4 (net names).** Seven proposed net names (section 7) must be reconciled with the
  sheet plan before P4 or `netlist_audit` fails at error severity.
- **O-5 (rules_gen gap - verified).** `rules_gen.py` **does not read the `voltages` key**
  (grep-verified), and the net class it does emit for power nets gets
  `max(fab_min, 0.2) mm` clearance. So **nothing makes the P7 router honour 0.60 mm** -
  the violation only surfaces at P8 `check_creepage`, after routing. The architect should
  add an explicit HV net class (or a named `.kicad_dru` clearance rule keyed on
  `A.NetName`, per the LEARNINGS entry that `A.Net` silently matches nothing) at P5, or
  plan on a P8-to-P7 rework loop.
- **O-6 (ICD wording).** Section 5.3: the connector's *contact* rating (3 A) and the PoE
  *source* limit (0.35-0.686 A) are different numbers and the ICD must state both, or a
  daughter designer will size a cap bank against current that cannot arrive.
