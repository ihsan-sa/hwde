# Adversarial schematic review - bb-buck (LMR33630ADDAR, 18-30 V -> 5 V / 2 A)

Reviewer: P4 schematic-reviewer, fresh context. Mode: **ultra-bare-bones** - scope
exclusions (ESD, reverse polarity, fuse, TVS, indicators, spare rails, extra test
points) are owner scope decisions and are NOT reported below. Rigor is not relaxed.

Artifacts read: `reports/schematic.pdf` (rendered here), `reports/top.net` (rendered
here), `parts/C841384.json`, `parts/lmr33630.pdf` (TI SNVSAN3F, pages cited by
printed page number), `parts/parts.json`, `architecture/constraints.json`,
`kicad/decoupling.json`, `requirements.md`, checklists `power.md` + `connector.md`.
ERC (`reports/gate-erc.json`, 0/0) and netlist_audit are taken as green and not
re-litigated.

**Gate: 1 error, 2 warnings.**

---

## 1. The charged question: is there a datasheet MINIMUM C_OUT for LOOP STABILITY, and does 2 x 22 uF sit inside it?

**Answer: yes, there is a stability-scoped constraint, it is distinct from the
transient sizing in Sec 9.2.2.5, and 2 x 22 uF sits OUTSIDE it. This is an error.**
No hedging - the citations are below.

### What the datasheet actually says

The earlier phase was right that Equation 6 is a transient bound. Page 22, Sec
9.2.2.5, says so in its own words: *"Equation 6 can be used to estimate a lower bound
on the total output capacitance and an upper bound on the ESR, **which is required to
meet a specified load transient**."* The 52 uF / 72 uF / "4 x 22 uF, 16 V" chain that
follows is the worked answer to a dVOUT <= 250 mV at dIOUT = 2 A requirement. That
reasoning is sound and is not what this finding rests on.

The stability clause is somewhere else, and the earlier reasoning never reached it.
**Page 19, Sec 9.2, first paragraph:**

> "This device is designed to function over a wide range of external components and
> system parameters. **However, the internal compensation is optimized for a certain
> range of external inductance and output capacitance.** As a quick start guide,
> Figure 9-1 provides typical component values..."

That is a compensation statement, not a transient statement, and it names exactly two
parameters: L and C_OUT. The datasheet quantifies that range in exactly one place -
**Table 9-2, "Typical External Component Values", page 20**:

| fSW (kHz) | VOUT (V) | L (uH) | **COUT (RATED CAPACITANCE)** | RFBT | RFBB | CIN + CHF | CBOOT | CVCC | CFF |
|---|---|---|---|---|---|---|---|---|---|
| 400  | 3.3 | 6.8 | **4 x 22 uF** | 100 k | 43.2 k | 10 uF + 220 nF | 100 nF | 1 uF | open |
| 1400 | 3.3 | 2.2 | 2 x 22 uF | 100 k | 43.2 k | 10 uF + 220 nF | 100 nF | 1 uF | open |
| 2100 | 3.3 | 1.2 | 2 x 22 uF | 100 k | 43.2 k | 10 uF + 220 nF | 100 nF | 1 uF | open |
| **400** | **5** | **8** | **4 x 22 uF** | **100 k** | **24.9 k** | **10 uF + 220 nF** | **100 nF** | **1 uF** | **open** |
| 1400 | 5   | 2.2 | 2 x 22 uF | 100 k | 24.9 k | 10 uF + 220 nF | 100 nF | 1 uF | open |
| 2100 | 5   | 1.5 | 2 x 22 uF | 100 k | 24.9 k | 10 uF + 220 nF | 100 nF | 1 uF | open |
| 400  | 12  | 15  | **4 x 22 uF** | 100 k | 9.09 k | 10 uF + 220 nF | 100 nF | 1 uF | open |
| 1400 | 12  | 4.7 | 4 x 10 uF | 100 k | 9.09 k | 10 uF + 220 nF | 100 nF | 1 uF | open |
| 2100 | 12  | 3.3 | 4 x 10 uF | 100 k | 9.09 k | 10 uF + 220 nF | 100 nF | 1 uF | open |

Three things make this decisive rather than advisory:

1. **The bolded row is this board.** Same part variant (A = 400 kHz), same VOUT, same
   RFBT (100 k), same RFBB (24.9 k), same CBOOT (100 nF), same CVCC (1 uF), same CFF
   (open). The board matches Table 9-2 on **every entry except L and C_OUT** - which
   are precisely the two the Sec 9.2 sentence says the internal compensation is
   optimized around.
2. **Every 400 kHz row in the table is 4 x 22 uF.** 2 x 22 uF appears only at 1400 kHz
   and 2100 kHz. That is not an accident of the example - it is the fc-scales-with-fSW
   relationship showing through: at 3.5x the switching frequency you can cross over
   3.5x higher and therefore need less capacitance. At 400 kHz you cannot.
3. **The column header says "RATED CAPACITANCE".** So the 4 x 22 uF is a nameplate
   figure, and the board's 2 x 22 uF is exactly half of it on the same basis - before
   any derating argument is even opened.

**The only capacitance limit the datasheet explicitly ties to stability is a MAXIMUM**
(p23: *"The maximum value of total output capacitance must be limited to about 10 times
the design value, or 1000 uF... Large values... can adversely affect the start-up
behavior of the regulator as well as the loop stability"*). There is **no closed-form
minimum-C_OUT-for-stability equation and no minimum-ESR / ESR-zero condition** anywhere
in the datasheet - Eq 6 bounds ESR from ABOVE only (0.11 ohm in the example). So the
range is stated qualitatively in Sec 9.2 and quantified only by Table 9-2. That is the
whole of the datasheet's stability guidance on C_OUT, and 2 x 22 uF is outside it.

Corroboration: **Table 9-3, page 31, "BOM for Typical Application Curves DDA Package"**
- the 5 V / 400 kHz / LMR33630ADDA row (this exact orderable) used **COUT = 4 x 22 uF,
L = 8 uH**. Every characterization curve TI publishes for this part at this operating
point was measured with the 4-cap bank.

### Why it matters physically, not just on paper

For a peak-current-mode converter with a **fixed internal Type-II compensator**, the
mid-band loop gain is an integrator whose crossover is set by C_OUT and nothing else:

    fc ~= gm * Rcomp * (VREF/VOUT) / (2*pi * Ri * C_OUT)

Halving C_OUT roughly doubles fc. TI does not publish gm/Rcomp/Ri, so the absolute
number is not computable from the datasheet - but the **inverse proportionality is
exact and independent of load**, and this bank is all-ceramic: two 1210s in parallel
give roughly 1.5 mohm ESR, putting the ESR zero near **3 MHz**, so there is no phase
boost anywhere near crossover to absorb the shift. fSW/2 = 200 kHz is where the
current-loop sampling double-pole lives. Doubling fc walks the crossover toward it.

The failure mode is the nasty kind: the board comes up, the DC rail measures correct,
and the deficit only shows as ringing or sustained oscillation on a load step, a line
step, or at a particular load current. This board has **no way to detect it** - there
is no injection resistor and no series element to break the loop, so a Bode plot cannot
be taken, which is exactly the validation Sec 9.2.2.5 says *"must always be completed"*.

Quantified consequence (Eq 6 run backwards, for scale only - **this board has no
binding transient spec and this is NOT reported as a violation**): at D = 0.208,
K = 0.33, a 0 -> 2 A step gives ~**506 mV** of output excursion at 32 uF effective
versus ~**261 mV** at the table's 4-cap bank (~62 uF effective), the latter matching
TI's own 250 mV worked example. A bench operator clipping a resistive load on and off
is that step.

### On the inductor - checked, and deliberately NOT reported

L = 15 uH is 1.9x Table 9-2's 8 uH for this row, and L is the *other* parameter Sec 9.2
names. I checked whether it compounds the C_OUT problem. **It does not, and it is not a
defect:**

- Eq 4 at this board's own 2 A rating, 24 V, K = 0.3 gives 16.5 uH; 15 uH is the nearest
  standard value below. TI's 8 uH came from a **3 A** example.
- Eq 5 (p22, read from the rendered page to confirm direction): **L_MIN >= 0.28 * VOUT /
  fSW** = 3.5 uH. 15 uH clears it 4.3x. (Internally consistent: TI's own 8 uH and the
  12 V row's 15 uH would both violate it if it were a maximum.)
- The "ripple no less than ~10% of device max rated current" rule-of-thumb = 0.3 A.
  Actual dI_L is 0.60 A at 18 V and 0.69 A at 30 V. Clears.
- Small-signal direction: larger L means a smaller inductor on-slope Sn, hence larger
  mc = 1 + Se/Sn against the fixed internal slope compensation, hence **lower Q at
  fSW/2**. That is damping, not peaking. It does not add to the C_OUT problem.

What it does do is confirm the board sits at no characterized point at all: **no row of
Table 9-2 pairs 15 uH with 2 x 22 uF, and no 400 kHz row anywhere uses 2 x 22 uF.**

### DC-bias derating sanity check on 22 uF / 25 V / X7R / 1210 at 5 V bias

Asked for explicitly. **The ~16 uF/each assumption is fair - if anything mildly
optimistic - and it does not rescue the 2x decision.**

- A 25 V part in 1210 has a thicker dielectric than the 16 V part TI's reference used,
  so it derates *less*. Class-typical published curves for 22 uF / 25 V / X7R / 1210
  (Murata GRM32ER71E226K, TDK C3225X7R1E226M, Samsung CL32B226KAJ) show roughly
  **-13% to -20% at 5 V bias** -> 17.6 to 19 uF each. Commodity grades such as this
  Samwha CS3225 typically sit at the worse end or below: **-20% to -25% -> 16.5 to
  17.6 uF each**. So ~16 uF each is a reasonable central figure for this MPN.
- It is a 25 C, nominal-tolerance figure though. Fold in the "K" tolerance code
  (+/-10%, so -10%) and X7R's temperature coefficient at the 85-90 C local board
  temperature constraints.json itself predicts (another -5% to -10% off the 25 C value)
  and the **worst-case bank is ~27-30 uF, not 32 uF**.
- Against TI's reference bank of 4 x 22 uF / **16 V**, which at 5 V bias loses more
  (-25% to -35% is typical for a 16 V 1210) and lands near 60-62 uF effective, the
  board is at **~0.5x the effective capacitance the compensation was designed around** -
  the effective ratio and the rated ratio agree. There is no derating argument that
  makes 2x equivalent to 4x here.
- Caveat carried to OPEN: the Samwha CS3225X7R226K250NRL bias curve was **not
  independently pulled**; the numbers above are class-typical, not MPN-verified.
  `parts.json` records the same gap for the 10 uF sibling C2918502.

### Fix (reported, not applied)

Two more of the already-selected MPN (C2918511, 22 uF / 25 V / X7R / 1210) as C8/C9,
restoring the bank to Table 9-2's 4 x 22 uF. Cost is ~$0.45/board and two 1210 lands
next to L1. Doing it now is free; doing it after P5/P6 means re-opening placement, the
output pour and the Cout-ground-separation constraint. If the owner instead wants to
keep 2x deliberately, the datasheet-sanctioned partial mitigation is CFF across R1
(Sec 9.2.2.9, p23-24, explicitly offered to *"improve the loop-phase margin"*), but
that is a compensation patch on an operating point outside the characterized range, not
an equivalent - and it is an owner call, not a reviewer's.

---

## 2. Findings

### ERROR

**E1 - `cout-below-compensation-range` (+5V; U1, C4, C5).** Section 1 above. Output
bank is half the rated capacitance Table 9-2 (p20) specifies for this board's exact
400 kHz / 5 V row, which is the only quantified expression of the range Sec 9.2 (p19)
says the internal compensation is optimized for. Roughly doubles loop crossover toward
fSW/2 with no ESR zero to compensate, and the board cannot measure the result.

### WARNING

**W1 - `cin-effective-marginal-high-line` (+VIN; U1, C2, C3).** Sec 9.2.2.6 (p23)
requires *"a minimum of 10 uF of ceramic capacitance... on the input"*, and Sec 9.1's
note (p19) defines capacitance datasheet-wide as *"the actual capacitance under D.C.
bias and temperature; not the rated or nameplate values"*. The bank is 2 x 10 uF / 50 V
/ 1210 X7R. Class-typical 50 V 1210 10 uF curves lose ~35% at 24 V and ~38-42% at 30 V,
giving **10-12 uF effective at the 30 V corner**; with the -10% tolerance and 85-90 C
board temperature the worst case is **8.5-10.5 uF** - straddling the 10 uF line rather
than clearing it. The same clause's *"preferably twice the maximum input voltage"* wants
60 V parts at this 30 V ceiling; 50 V meets the hard requirement but not the preference.
Note Table 9-2's CIN column carries no "(RATED)" qualifier where the COUT column does,
which under the p19 note reads as effective. Consequence at bring-up: input-rail sag and
hot-loop ringing at high line - the corner where A2 already spent the hot-plug margin.
Not an error: the board carries 2x TI's reference count and the shortfall is a corner
case, not a certainty. A third 10 uF or a 100 V part closes it.

**W2 - `fb-divider-ground-reference` (/FB; U1, R1, R2).** Layout carry-forward that
nothing currently enforces. Table 6-1 (p5) states AGND is the pin *"all electrical
parameters are measured with respect to"*, and Sec 10.1 rule 4 requires the FB divider
close to the FB pin with short FB-to-GND connections. The schematic is correct - one GND
net, EP and PGND both on it, which is what the datasheet prescribes - but
`constraints.json` constrains only that /FB stay short and away from /SW and L1
(`placement.groups.feedback`, `placement.separation`), and `_review_enforced` item 5
covers only the Cin/Cout returns. Nothing stops P6/P7 from landing R2's ground in the
PGND hot-loop return, which sums switching ripple into the 1 V reference and reads as
output jitter or an off-target rail. Add R2's return to the AGND/EP island as an
explicit `_review_enforced` item before P6.

---

## 3. Checked and cleared - the things this board was most likely to get wrong

### Absolute maximum vs applied, every U1 pin, at the 30 V operating corner (Sec 7.1, p6)

| Pin | Applied at VIN = 30 V | Abs max | Verdict |
|---|---|---|---|
| 1 PGND | 0 V, tied to GND net | reference | ok |
| 2 VIN | 30 V | 38 V (rec. op. max 36 V) | ok, 8 V / 6 V headroom - **A1's ">= 36 V class" is met by the part, no clamp needed** |
| 3 EN | 30 V, tied to +VIN | VIN + 0.3 V | **cannot be violated by construction** - tied to the very rail it is limited against |
| 4 PG | open, undriven | 0 to 22 V, and <= VIN + 0.3 | ok, nothing drives it |
| 5 FB | 1.0 V | 5.5 V | ok; FB reaches 5.5 V only if VOUT hits 27.6 V |
| 6 VCC | internal LDO, 4.75/5/5.25 V | 5.5 V | ok, self-limited; only C7 on the net (Sec 9.2.2.8 "avoid loading this output" honored) |
| 7 BOOT | ~4.5-5 V across C6 | 5.5 V, BOOT-to-SW only | ok; the datasheet publishes **no** BOOT-to-GND rating, so the 35 V absolute node potential is not a violation |
| 8 SW | 0 to 30 V switched | VIN + 0.3 steady; -3.5 / +38 V for <100 ns | ok on the schematic; the transient window is layout-bounded (hot-loop area), already an E-level constraint |
| 9 EP / AGND | GND, same net as PGND | AGND-to-PGND +/-0.3 V | ok, 0 V on the schematic |

Footnote (2) on the abs-max table - *"the voltage on this pin must not exceed the voltage
on the VIN pin by more than 0.3 V"* - applies to EN and PG and is satisfied by both.

### EN tied directly to +VIN - **sanctioned verbatim**

Table 6-1, page 5, pin 3: *"Enable input to regulator. High = ON, low = OFF. **Can be
connected directly to VIN**; Do not float."* Sec 9.3's "Don't: Allow the EN input to
float" is satisfied. External UVLO (Sec 9.2.2.10) is optional and not needed - the
supply range is 18-30 V, far above the internal UVLO. Nothing to report.

### PG (pin 4) as an explicit no-connect - **permitted verbatim**

Table 6-1, page 5, pin 4: *"Open drain power-good flag output... **Can be left open when
not used.**"* The schematic carries a real KiCad no-connect flag (one `no_connect`
element, netlist pintype `passive+no_connect`), so this is a declared intent, not an
omission. Nothing to report.

### Exposed pad = AGND, wired to GND - **correct, and no separation requirement exists**

Table 6-1 (p5) THERMAL PAD row assigns AGND and instructs *"Connect to system ground on
PCB"*; the pin 1 PGND row instructs *"Connect to system ground and AGND"*. Sec 10.1.1:
*"AGND and PGND must both be tied to the ground plane(s)."* So the datasheet **requires**
the tie the board makes. There is no AGND/PGND split to violate. The real constraint is
the +/-0.3 V abs-max between them, which is a layout matter and is already covered by the
>=16-via array in `constraints.json.thermal` and `_review_enforced` item 1. Nothing to
report at schematic level.

### BOOT / bootstrap cap

C6 = 100 nF / 50 V / X7R / 0603, BOOT (pin 7) to SW (pin 8). Sec 9.2.2.7 (p23):
*"a high-quality ceramic capacitor of 100 nF and at least 10 V is required."* Table 9-2
CBOOT = 100 nF. At the ~5 V it actually sees, a 50 V X7R derates negligibly, so effective
is ~95-100 nF. The Table 6-1 "connect SW to NC on the PCB" note is **VQFN-only** and does
not apply to this DDA part (there is no NC pin on the 8-lead HSOIC). Clean.

### FB divider 100k / 24.9k, and the CFF question

- Arithmetic: VOUT = VREF x (1 + RFBT/RFBB) = 1.000 x (1 + 100/24.9) = **5.016 V**.
  Eq 3 (p21) gives RFBB = 100k/4 = 25.0 k; 24.9 k is the E96 neighbor and is **TI's own
  choice** in both Table 9-2 (p20) and Table 9-3 (p31).
- Tolerance stack against A3's 4.850-5.150 V: VREF 0.985/1.015 (Sec 7.5) with
  +/-0.1% resistors gives a worst-case window of **4.933 to 5.100 V**. Inside, with
  ~83 mV on each side - enough to absorb the 2 A IR drop from the sense point to J2.
- **CFF confirmed "open", and the extraction's reasoning is correct with one
  refinement.** Sec 9.2.2.3 (p21): *"The recommended value for RFBT is 100 kOhm; with a
  maximum value of 1 MOhm. **If a 1 MOhm is selected for RFBT, then a feedforward
  capacitor must be used**..."* - so the MUST threshold is 1 M, and RFBT = 100 k is the
  *recommended* value, not merely below the threshold. Sec 9.2.2.9 (p23) adds that CFF is
  *"especially true when values of RFBT > 100 kOhm are used"*; 100 k is not > 100 k.
  Table 9-2's 5 V row lists CFF = open. Three independent confirmations. **No CFF
  required.** (Its other listed use - improving loop phase margin - is what makes it
  relevant to E1, but that is a mitigation discussion, not a defect here.)

### Values and operating point

- **Output ripple, Eq 7 (p22), 30 V corner:** dI_L = 0.694 A, C_OUT_eff ~32 uF gives
  1/(8 fSW C) = 9.77 mohm against ~1.5 mohm ESR, so Vr = **6.9 mV pk-pk** against A3's
  50 mV budget - 8.1 mV even at the 27 uF worst case. **Ripple is not the issue and E1
  is not a ripple claim.** A3's light-load PFM carve-out is honored and not reported.
- **Minimum on-time at the 30 V corner:** ton = (5/30)/400 kHz = **417 ns** against the
  DDA spec of 75 ns min / 108 ns max. 3.9x margin. The requirements-stage worry about
  this corner clears.
- **Inductor saturation:** I_L,pk = 2.35 A at 30 V. L1 Isat = 8 A clears not just the
  low-side ILIMIT max (4.1 A) that Sec 9.2.2.4 calls the floor, but the **stricter
  "ideally >= high-side ISC" criterion (5.05 A max)** with 58% margin. Irms 4.5 A vs
  I_L,rms ~2.0 A. Clean.
- **Current limits vs 2 A:** valley 1.65 A vs ILIMIT min 2.9 A; peak 2.35 A vs ISC min
  3.85 A. No nuisance limiting.
- **Do not allow VOUT to exceed VIN (Sec 9.3):** 5 V out from 18 V min in. Clean.

### Decoupling, per-pin, against the datasheet JSON - not just "some caps"

| Datasheet requirement | Board | Verdict |
|---|---|---|
| CIN bulk >= 10 uF eff at VIN/PGND (9.2.2.6) | C2, C3 = 2 x 10 uF / 50 V 1210 | **W1** - marginal at 30 V effective |
| CHF 220 nF **50 V X7R**, small case, at VIN (9.2.2.6) | C1 = 220 nF / 50 V / X7R / 0603 | exact match, incl. the explicit 50 V + X7R call |
| CBOOT 100 nF >= 10 V, BOOT-SW (9.2.2.7) | C6 = 100 nF / 50 V / 0603 | clean |
| CVCC 1 uF 16 V, VCC-GND (9.2.2.8) | C7 = 1 uF / **25 V** / 0603 | clean - see note |
| COUT, 400 kHz / 5 V row (Table 9-2) | C4, C5 = 2 x 22 uF / 25 V 1210 | **E1** - half |
| CFF (Table 9-2, 5 V row) | absent | correct, "open" |

Note on applying Sec 9.1's effective-capacitance rule consistently: it bites in exactly
two places. C7 at 5 V bias loses only ~12-15% (25 V 0603) and therefore beats TI's own
16 V reference part at the same nameplate - **better than the datasheet asks, not worse**.
C1's heavy derating at 24-30 V is priced in by TI, which specified the rating and
dielectric itself and matches the board part for part. C6 sits at ~5 V and barely
derates. C2/C3 sit at 30 V, where the loss is severe (W1). C4/C5 sit at 5 V, where the
loss is mild - which is precisely why E1 cannot be argued away on derating grounds: the
effective ratio to TI's bank (~0.52) tracks the rated ratio (0.50).

### Interfaces (connector checklist)

- J1 pin 1 = +VIN / pin 2 = GND; J2 pin 1 = +5V / pin 2 = GND. **Same polarity
  convention on both**, same orderable (KF128-5.08-2P, C474952), so there is no pin-order
  trap between them. THT screw terminal, no mating cable to mis-key. 250 V / 24 A against
  30 V / 2.5 A applied - the requirements' ">= 300 V" was an arbitrary assumption, not a
  datasheet or IEC 62368-1 requirement at 30 V DC, and 24 A clears >= 10 A by 2.4x.
- Reverse-plug consequence: destructive, and the checklist asks it be *stated* - it is,
  in requirements.md s8, which also rules it explicitly not-a-finding. Recorded, not
  reported.
- **Carry-forward to P6/P7, not a schematic finding:** the polarity legend and the
  distinct VIN / 5V OUT silk are the only defence against a swap, and must be visible
  after assembly with the wire openings facing off-board. `constraints.json` places J1
  left / J2 bottom and flags both rotations as PROVISIONAL until a footprint exists.
- TP1 (/SW) + TP2 (GND) are exactly A4's ruling: one probe pad, one adjacent ground pad,
  nothing else.

### Polarity

Every part on this board is non-polarized - all ceramic X7R, one shielded power
inductor, two resistors, two screw terminals. No diode, LED or electrolytic exists to
get backwards. Nothing to check beyond the connector pin order above, which is clean.

---

## 4. Deliberately NOT reported (mode-excluded or owner-answered)

Listed so it is visible that they were checked and consciously dropped, per
`reference/build-modes.md`:

- Absent input TVS / clamp, reverse-polarity FET or diode, input fuse, pi/EMI filter,
  OVP/OCP/UVLO beyond the IC, output LC filter. All mode exclusions.
- Absent PG pull-up and indicator LED, absent test points beyond TP1/TP2. Mode + A4.
- Absent external UVLO divider on EN (Sec 9.2.2.10). Optional; not needed in 18-30 V.
- The optional 1-100 nF output HF ceramic that Sec 9.2.2.5 says *"can help reduce high
  frequency noise"*. "Can help", not required - optional filtering, mode-excluded.
- Light-load / PFM burst ripple below ~200 mA. A3 as amended accepted it explicitly;
  this DDA package has no MODE pin, so there is no design choice to critique.
- 30 V input with no clamp. A1 + A2 are binding requirements, and the part carries 38 V
  abs max / 36 V recommended, which is the ">= 36 V class" A1 asked for.

---

## 5. Open - what could not be verified

- **MPN-specific DC-bias curves were not pulled for any of the three bulk ceramics**
  (Samwha CS3225X7R226K250NRL / C2918511 output, CS3225X7R106K500NRL / C2918502 input,
  and the YAGEO 0603s). Every effective-capacitance number in this review is
  class-typical for the case size / voltage rating / dielectric, not measured or vendor-
  curve-confirmed. `parts.json` already records the same gap for C2918502. This affects
  the *magnitude* of E1 and W1, not their direction: E1 rests on the rated-capacitance
  column of Table 9-2, which needs no derating argument at all, and W1 is explicitly
  flagged as marginal rather than proven short.
- **Loop phase margin cannot be computed from the datasheet.** TI publishes no gm,
  Rcomp or Ri for the internal compensator and no Bode plots, so the fc-doubling claim in
  E1 is a proportionality (exact) rather than an absolute number (unavailable). The only
  way to close this is measurement, and Sec 9.2.2.5 says measurement *"must always be
  completed"* - which this board cannot do without a loop-injection element it does not
  have. Worth an owner decision at bring-up: either restore the 4-cap bank, or accept
  that the phase margin will be unknown and unmeasurable on this article.
- **Equation 5's label** reads `L_MIN >=` on the rendered page while the sentence above it
  discusses "maximum inductance". I resolved the contradiction by internal consistency
  (TI's own 8 uH example and the 12 V row's 15 uH both violate it if read as a maximum)
  and treated it as a minimum, which 15 uH clears 4.3x. If TI intended a maximum, the
  datasheet contradicts its own Table 9-2 and the point is moot.
- Everything downstream of the netlist - actual copper, via counts, pour continuity,
  hot-loop area, silk legends - is outside a schematic review and is left to P6/P7
  against `constraints.json._review_enforced`.
