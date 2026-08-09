# Reference-design research: synchronous buck power stage - sbuck-5v3a

Block: buck power stage, Vin 7-18V (12V nom) -> Vout 5.0V +/-2% @ 3.0A, fsw 400-700kHz,
50C ambient natural convection, 4L 1oz/0.5oz (default), 50x40mm.

Method: read the full manufacturer datasheet/app-note PDF for each of the 3 assigned
candidates via the LCSC PDF links the component scout already verified live. Deltas
below are cited against `reference/topologies/buck.md` (house buck reference) s2-6.
Ranks 4-5 (async, out of scope) not reviewed.

---

## 1. AP64350SP-13 (Diodes Inc, C2071691, SO-8-EP) - PRIMARY

Source: AP64350 datasheet, DS41976 Rev. 5-2, Diodes Incorporated, Dec 2024 (25p, all
read). https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/2210280930_Diodes-Incorporated-AP64350SP-13_C2071691.pdf

### 1.1 Part identity (item 6)
**AP64350SP-13 is the ONLY orderable SKU under "AP64350"** (Ordering Info p.23:
`AP64350[Package]-[Packing]`, Package="SP"=SO-8-EP, Packing="13"=T&R). No separate
"AP64350S" fixed-output sibling - unlike the AP63203-vs-AP63200/1 trap buck.md warns
about, **AP64350 is adjustable-output only** (0.8V ref + external divider, "Setting the
Output Voltage" p.13). An automotive sibling "AP64350Q" exists under its own datasheet
- unrelated, don't confuse. No pinout/FSW variant risk.

### 1.2 External components (item 1)
Vendor's "Recommended Components Selections, fsw=500kHz" table (Table 1 p.13), VOUT=5V
row - the exact BOM published for our operating point:

| R1 | R2 | L | Cin | Cout | Cbst | Rcomp | Ccomp | C6(opt) |
|---|---|---|---|---|---|---|---|---|
| 115.8k | 22.1k | 5.5uH | 10uF | 2x22uF | 100nF | 14.0k | 3.3nF | 47pF |

- **BST**: 100nF ceramic BST-SW, "recommended" (p.3) - no voltage rating stated.
- **No VCC pin exists** - internal LDO is fully self-contained (block diagram p.3);
  nothing to decouple beyond VIN.
- **RT**: `RT[kOhm]=100000/fSW[kHz]` (Eq.7 p.13) -> 200k for 500kHz (matches scout).
- **Soft-start**: internal, fixed 2ms typ, no external cap (p.10).
- **Compensation: EXTERNAL** (COMP pin exposed, peak current-mode) - NOT internally
  compensated, unlike buck.md's "most parts" default assumption. Full Type-II
  procedure (Eqs 12-20, p.16-18); worked 5V/12Vin/3.5A/500kHz example = Table-1 row
  exactly, predicted loop ~16.6kHz BW / 81.6deg phase margin / -26.8dB gain margin.
- **Fixed-frequency peak-current-mode PWM. Light load: automatic PFM, NOT
  pin-selectable** to forced-PWM (no FPWM pin in the 8-pin+EP set). PFM engages at the
  750mA COMP-clamp; IZC (zero-cross) = 0mA typ = true diode emulation, clean 0A
  handling. Up to 85% efficiency at 5mA (p.1).

### 1.3 FB divider rule (item 2)
VFB = 792/800/808mV min/typ/max = **+/-1% reference tolerance** (p.5). **FB bias
current is NOT published anywhere in this datasheet** - a real gap (both other parts
below do publish it). R1=115.8k/R2=22.1k checks out: R1=R2*(VOUT/0.8-1)=22.1k*5.25=
116.0k, rounds to the table value.

**Reference-tolerance-alone setpoint window** (dominant error term since IFB is
unpublished): VOUT at VFB_min=792mV*(1+115.8/22.1)=**4.94V (-1.2%)**; at
VFB_max=808mV*6.24=**5.04V (+0.84%)**. Already consumes 60-84% of the +/-2%
(4.90-5.10V) budget before resistor tolerance/drift - see s4.2.

### 1.4 EN / UVLO (item 3) - biggest single finding of this research
Thresholds (p.5): VEN_H (rising) 1.18/1.25V typ/max; VEN_L (falling) 1.03/1.09V
min/typ. **Internal 1.5uA pull-up always present + 4uA more once tripped** (Fig 23) -
gives auto-start if EN floats or ties to VIN ("leave floating for automatic startup,"
p.10). **EN tolerates VIN directly** (abs max 42.0V).

Vendor's UVLO-divider equations (Eqs 2-3 p.11, R3=VIN-EN, R4=EN-GND):
```
R3 = (0.924*VON - VOFF) / 4.114uA
R4 = (1.1*R3) / (VOFF - 1.09V + 5.5uA*R3)
```
**Plugging in the project's own target (VON=6.5V, VOFF=6.0V, Q14): R3 =
(0.924*6.5-6.0)/4.114uA = 0.006V/4.114uA = 1.46 kOhm; R4 = 326 Ohm.** Not an
arithmetic error - inherent to the formula: coefficient 0.924 nearly cancels the
numerator at an 8% VON/VOFF gap. **Consequence: 6.7-10mA continuous VIN draw
(80-180mW)** - non-negligible against the 88% efficiency floor and self-heats the
divider on an already thermally-tight board. Widening the gap fixes it: VON=7.0V/
VOFF=6.0V (1V gap, still clears the 7V floor) gives R3=113.8k, R4=22.6k, <100uA.
**Recommend widening the UVLO hysteresis target if AP64350 is chosen**, or prefer
LMR33630 (s2.4) which has no such pathology at the literal 6.5V/6.0V target. (VON
must be >3.7V, VOFF >3.3V per datasheet caveats - both clear.)

### 1.5 Layout (item 4) - "PCB Layout" p.22, Fig.32
1. **2oz copper, top AND bottom, explicitly recommended** ("3.5A load... heat
   dissipation is a major concern") - **conflicts with the project's 1oz outer/0.5oz
   inner default** (Q21). Given the board's own binding 2.05W/<=50x40mm/50C-ambient
   constraint, this is a real escalation signal for P5, not just a contingency.
2-5. Input caps flush to VIN/GND; inductor tight to SW; output caps tight to GND;
   FB components (R1/R2) tight to FB pin.
6. 4+ layers: use layers 2 and 3 as GND for thermal.
7-8. **"Add as many vias as possible"** around GND pin/plane and VIN pin/plane - no
   numeric count/drill/pitch (contrast LMR33630's explicit 4x3/10-mil spec, s2.5 -
   borrow that number here if a numeric target is needed).
9. Fig.32: Cin/Cbst flank VIN/BST; inductor+SW sit opposite; Cout and the FB/comp
   group sit on the far edge, away from SW; GND pour wraps the input-cap corner.

Single GND pin (#7) doubles as power ground; exposed pad (#9) ties to the same net/
plane. No true Kelvin/star point defined beyond "GND pour under the IC, vias to all
layers."

### 1.6 Errata / footguns (item 5)
- **SW ringing**: handled internally by a "proprietary multi-level gate driver," not
  a board snubber, plus FSS (+/-6% jitter, RT mode only).
- **Bootstrap refresh / dropout**: if BST<2.3V, Q2 pulses on 300ns to refresh (back
  above 2.55V). Separately, as Vin approaches Vout the part enters LDO mode (Q1 held
  ~100% duty, Q2 forced-refreshes BST) - not engaged at our 7V/D=0.714 point
  (Vin_min=3.8V gives large margin), but the mechanism is internal/automatic, no
  external network needed if Vin ever sags further.
- **Min on-time**: 100ns typ only (no min/max). At 18V/D=0.278/500kHz: 556ns, 5.6x
  margin. At 7V/D=0.714: 1.43us, trivial.
- **RC snubber**: typical app circuit has **no snubber at all** across SW-PGND; relies
  entirely on the internal gate driver. No vendor R/C values anywhere. See s4.3.
- **Input cap RMS current**: vendor rule of thumb ("RMS rating > half of max load
  current") = 1.5A at our 3.0A load - **lands almost exactly on our own worst-case
  computed 1.50A RMS** (requirements.md s3, Vin=10V). Not extra margin; the chosen
  MLCC(s) RMS rating must be independently verified, not assumed covered by ">10uF."
- **OCP**: cycle-by-cycle peak (HS Ipeak MIN 4.25A, clears the 4.0A floor); 512
  cycles at limit -> hiccup 8192 cycles -> restart w/ soft-start. Matches Q7/Q29.
- **OVP**: >110% trips HS-off/LS-on, clears <105%, independent of the FB loop - a
  free extra layer relevant to the output back-drive question (Q30).

---

## 2. LMR33630ADDAR (TI, C841384, HSOIC-8 PowerPAD/"DDA") - FALLBACK

Source: LMR33630 datasheet, TI ZHCSHQ3F (Eng. base SNVSAN3), rev.F Nov 2020 (36p, all
read). https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/2410121900_Texas-Instruments-LMR33630ADDAR_C841384.pdf

### 2.1 Part identity
Device Comparison Table (p.4): "A"=400kHz, "B"=1.4MHz, "C"=2.1MHz; DDA(HSOIC-8) and
RNX(VQFN-12); **all variants adjustable-output only** - no fixed-output naming trap.
LMR33630ADDAR = 400kHz, HSOIC-8, matches our fsw target directly (fixed, not
RT-programmable like AP64350).

### 2.2 External components
Vendor's "Typical External Component Values" (Table 9-2 p.19) cross-checked against
the app-curves BOM (Table 9-3 p.29), 400kHz/5V row:

| RFBT | RFBB | L | Cout | Cin+CHF | Cboot | Cvcc | Cff |
|---|---|---|---|---|---|---|---|
| 100k | 24.9k | 8uH | 4x22uF | 10uF+220nF | 100nF | 1uF | open |

- **BST**: 100nF ceramic, >=10V rating "required" (p.22).
- **VCC decoupling**: this part DOES expose VCC (5V internal LDO) - 1uF/16V ceramic,
  avoid external loading beyond an optional PG pull-up (100k). (AP64350 has none.)
- **RFBT**: 100k recommended / 1M max, noise-vs-light-load-efficiency tradeoff
  (matches buck.md s4); Cff REQUIRED if RFBT>100k (Eq.9) - not needed at 100k.
- **Soft-start**: internal, 2.9-6ms typ 4ms, no external cap.
- **Compensation: INTERNAL** ("reduces design time," p.10) - simpler than AP64350's
  external Type-II network; no COMP pin.
- **Fixed-frequency peak-current-mode PWM. Light load: automatic PFM (DCM), NOT
  pin-selectable** - same non-selectable story as AP64350; PFM burst set by
  IPEAK-MIN (typ 0.69A).

### 2.3 FB divider rule
VFB = 0.985/1.0/1.015V = **+/-1.5%**. **IFB published: 0.2 typ / 50 max nA** (p.6).
RFBT=100k/RFBB=24.9k (vendor's own p.19 pair). Formula check: RFBB=RFBT/(VOUT/VREF-1)
=100k/4=25k, rounds to 24.9k -> VOUT(typ)=1.0*(1+100/24.9)=**5.016V**.

**FB-bias-current error, using the published 50nA max**: R_FBT||R_FBB=100k*24.9k/
124.9k=19.94kOhm; error=50nA*19.94k=**1.0mV on the 1.0V ref (0.1%)** - negligible
(~5mV on the output).

**Reference-tolerance-alone window**: VOUT at VFB_min=0.985*5.016=**4.94V (-1.18%)**;
at VFB_max=1.015*5.016=**5.09V (+1.82%)** - tighter against the +2% rail than
AP64350's window. See s4.2.

### 2.4 EN / UVLO
Thresholds (p.6): VEN-H (rising, "start switching") 1.2/1.231/1.26V; hysteresis
100mV typ (falling); separate lower VEN-VCC-H/L (~1V/0.3V) gate the internal LDO
(3-state EN behavior AP64350 lacks: standby-VCC-only / full-on / full-off).
**EN leakage only 0.2nA - not an active pull-up.** Unlike AP64350, **LMR33630 has NO
internal EN pull-up**; pin description explicitly warns "Do not float," no
auto-start safety net. EN abs-max = VIN+0.3V, tolerates direct-to-VIN.

**External UVLO formula (Eq.10 p.22, Fig 9-2) - structurally different, no low-R
pathology:**
```
R_ENT = (VON/VEN-H - 1) * R_ENB    [pick R_ENB freely, 10k-100k]
V_OFF = VON * (1 - VEN-HYS/VEN-H)   [VOFF is a RESULT, not independently set]
```
Plugging VON=6.5V, VEN-H=1.231V typ, VEN-HYS=100mV: **VOFF = 6.5*(1-0.1/1.231) =
5.97V** - lands almost exactly on the project's 6.0V target with zero tuning. With
R_ENB=100k: R_ENT=(6.5/1.231-1)*100k=428k. Divider current at 12V = 12/528k=**23uA**
- two orders of magnitude below AP64350's forced ~7-10mA for the same target (s1.4).
**Strongest single differentiator between the two lead candidates for this board's
UVLO requirement.**

### 2.5 Layout - Section 10 p.31-34 (Fig 10-1/10-2/10-3)
1-3. Input caps close to VIN/GND (VQFN has symmetric dual pairs, N/A to our DDA pkg);
   VCC bypass close w/ short traces; wide traces for Cboot, careful SW-to-Cboot path.
4. **FB divider (RFBB/RFBT/CFF) physically close to FB pin; VOUT-side trace "must not
   be routed near any noise source (such as the SW node)"** - explicit FB/SW keepout.
5-6. Middle-layer ground plane (shielding + heat sink); thermal pad soldered to it,
   directly affects RthJA.
7. Wide/direct VIN/VOUT/GND paths.
8. **Numeric spec: "minimum 4x3 array of 10-mil thermal vias... evenly distributed
   under the PAD."** Stackup: **"2oz/1oz/1oz/2oz"** top-to-bottom (p.32) - **same
   conflict with the project's 1oz/0.5oz default as AP64350** (Q21); two independent
   vendors both pushing heavier copper at this power level.
9. **Keep SW-to-inductor copper area small** - explicit radiated-EMI rationale.

AGND/PGND tied internally at the die; PGND net (switching-freq noise) must stay
confined to one side of the mid-layer ground plane, far side reserved for sensitive
routes (p.32) - a single-reference/quiet-side instruction, no true Kelvin point
beyond this.

### 2.6 Errata / footguns
- **Bootstrap refresh**: VBOOT-UVLO=2.2V typ, LS FET turns on to recharge Cboot when
  below it - same mechanism class as AP64350, less narrative detail.
- **Min on-time (DDA)**: 75typ/108max ns. At 18V/400kHz/D=0.278: 695ns, 6.4x margin.
  At 7V/D=0.714: 1.79us, trivial.
- **Dropout/frequency foldback**: explicit mechanism (fsw drops to extend duty as
  Vin->Vout). VDROP only characterized AT 1A (150mV, fsw folds to 140kHz) - **not
  characterized at our 3A load**; dropout at 3A will be materially higher
  (RDS(on)*I term) and isn't given by this datasheet. 0.4V hiccup threshold is
  explicitly disabled while in dropout.
- **Power Supply Recommendations (p.30), new vs. AP64350's doc**: explicit warning
  against thyristor/snap-back TVS on the input, and against ever letting VIN fall
  below VOUT (output caps discharge through the internal VIN-SW parasitic diode,
  possible damage) - use a Schottky between input and output if that fault is
  likely. Worth a P4 cross-check against the reverse-polarity P-FET's fault path
  (Q29/Q30).
- **Current-limit margin** (re-confirms scout): ISC(HS) MIN=3.85A misses the 4.0A
  floor; guaranteed max Iout via TI's Eq.1 `(ILIMIT_min+ISC_min)/2=(2.9+3.85)/2=
  3.375A` - only 12% above the 3.0A load.
- **RC snubber**: none anywhere in this 36-page document. Same conclusion, s4.3.

---

## 3. SY8205FCC (Silergy, C111875, SO8E) - shorter treatment per assignment

Source: "Application Notes: AN_SY8205," Rev 0.4, Silergy Corp - **marked "Preliminary
Specification"/"Confidential" throughout** (11p, all read; this app note IS the
datasheet, no separate formal doc exists). https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/1809050154_Silergy-Corp-SY8205FCC_C111875.pdf

### 3.1 External components
- BST: 100nF ceramic BS-LX (p.9), no voltage rating stated.
- VCC: internal 3.3V LDO, exposed, 1uF ceramic bypass, <=20mA external load allowed.
- **Soft-start: external, required** - `Tss=Css*0.6V/10uA` (p.3, p.8).
- fsw: fixed, "pseudo-constant 500kHz under CCM" (p.1) - no RT pin, no freq select.
- Compensation: internal; optional 100pF across R1 speeds transient response.
- **Light-load mode: undocumented.** The word "PFM" never appears anywhere in this
  document; only marketing language ("Instant PWM," light-load efficiency claims)
  and a typical PFM-shaped efficiency droop in the curves. **Real documentation gap**
  against the assignment's explicit light-load-matters ask - cannot confirm 0A
  handling or light-load ripple/noise behavior from this document.

### 3.2 FB divider rule
VREF=0.591/0.6/0.609V = +/-1.5% (p.5). IFB published: -50/+50nA (test cond VFB=VCC).

Vendor's worked example is for **3.3V, not 5V**: R1=100k -> R2=22.1k via
`R2=0.6V/(VOUT-0.6V)*R1` (p.8). **Applying the same formula to 5.0V (derived, NOT a
vendor-published pair)**: R1=100k -> R2=0.6/4.4*100k=13.64k, nearest standard 13.7k
-> VOUT(typ)=0.6*(1+100/13.7)=4.98V. FB-bias error: R1||R2=12.05k; error=50nA*12.05k
=0.6mV on 0.6V ref (0.1%) - negligible, same conclusion as the other two.

**Reference-tolerance-alone window**: VOUT at VREF_min=0.591*8.299=**4.90V (-1.9%)**;
at VREF_max=0.609*8.299=**5.05V (+1.0%)** - close to the -2% edge.

### 3.3 EN / UVLO
"EN falling threshold" 1.1/1.2/1.3V, hysteresis 0.1V typ (p.5) - table only labels a
falling threshold; rising isn't separately stated (a gap). Pin description mentions a
"1.2V rising threshold... program turn-on delay by adding RC before EN" - implies an
RC-delay use case, not a VIN-referenced UVLO divider. **No divider-design formula or
worked example given** (unlike both other parts) - real gap against item 3. EN
tolerates VIN directly (shared 33V abs-max row).

### 3.4 Layout
"Layout Design" p.9, 5 points, qualitative only (no numeric via/copper spec):
1. Maximize GND-pin copper / ground plane if space allows.
2. Cin close to IN/GND, minimize loop area.
3. LX-associated copper minimized ("potential noise problem").
4. **R1/R2 and the FB trace "must NOT be adjacent to the LX net"** - explicit FB/SW
   keepout, matches the assignment ask directly.
5. If EN driven from a high-Z source and IN from a high-Z supply (e.g. battery), add
   a 1Mohm EN-GND pulldown - N/A to our design (EN is a low-Z VIN divider).

### 3.5 Errata / footguns
- Min on-time 80ns typ / min off-time 120ns typ (single-typ-value only, like
  AP64350). At 18V/D=0.278/500kHz: 556ns, 6.9x margin.
- **No dropout-mode or frequency-foldback mechanism described anywhere** (contrast
  both other parts, which name an explicit mechanism) - documentation gap.
- No RC snubber values anywhere in the 11 pages. See s4.3.
- Whole document marked "Preliminary Specification" - treat every number as
  provisional relative to AP64350 (Rev 5-2) and LMR33630 (Rev F), both
  revision-controlled production datasheets.
- **Current-limit MIN spec conflicts with the component scout's characterization** -
  see s4.6.

---

## 4. Cross-cutting findings

1. **FB-bias-current setpoint error is negligible for all 3 parts** (<=0.1% of ref,
   ~5mV on a 5V output) - NOT where the +/-2% budget is actually at risk.
2. **Reference-tolerance-alone error is NOT negligible**, and IS the dominant DC-
   accuracy risk for all 3: AP64350 -1.2%/+0.84%, LMR33630 -1.18%/+1.82%, SY8205
   (derived pair) -1.9%/+1.0%. **Recommend 0.1% (min 0.5%) FB divider resistors on
   whichever part is chosen** - standard 1% resistors stacked on top of these windows
   risk exceeding the 4.90-5.10V budget even before line/load/temp drift.
3. **None of the 3 vendor docs gives an RC snubber value.** All lean on IC-internal
   EMI mitigation instead (AP64350: proprietary gate driver+FSS; LMR33630: low-
   parasitic package; SY8205: no claim at all). **DNP snubber values must come from
   general practice, not a vendor citation** - a common ~500kHz-node starting point
   is 10-33 Ohm series R + 470pF-2.2nF series C, sized generously (0603) so it's
   tunable at bring-up. Flag as NOT vendor-sourced.
4. **Copper-weight tension**: AP64350 recommends 2oz top+bottom; LMR33630 recommends
   2oz/1oz/1oz/2oz. Both conflict with the project default (1oz/0.5oz, Q21,
   "escalate only if thermal calc fails"). Given the board's binding constraint IS
   exactly this thermal budget (2.05W, <=50x40mm, 50C, no airflow), **two
   independent vendors both pointing toward heavier copper here is a real signal**,
   not coincidence - flag prominently for P5/P6.
5. **Thermal via array**: only LMR33630 gives a numeric spec (4x3, 10-mil, evenly
   distributed). AP64350 says only "as many as possible"; SY8205 gives none. If a
   numeric target is needed regardless of final part, **borrow LMR33630's 4x3/10-mil
   figure as the floor** - the only vendor-published number among the three, and pad
   sizes (SO-8-EP/HSOIC-8 PowerPAD/SO8E) are similar enough for it to apply.
6. **Current-limit MIN-spec conflict with `research/buck-ic.md`**: the scout's file
   states SY8205 "gives only a typical value (5A) with no MIN/MAX." Reading
   AN_SY8205's Electrical Characteristics table directly (p.5) shows a row **"Bottom
   FET Current Limit | Min 5 | Typ - | Max - | A"** - a MIN spec DOES exist, but for
   the **low-side ("Bottom") FET**, not a high-side/peak limit like AP64350's
   IPEAK_LIMIT or LMR33630's ISC. No formula is given (unlike TI's Eq.1) to convert
   this into a guaranteed-Iout number. Whether it satisfies the project's 4.0A floor
   is genuinely ambiguous - see OPEN.
7. **EN pull-up architecture differs**: AP64350 has an active internal pull-up
   (auto-starts floating/VIN-tied EN). LMR33630 has only 0.2nA leakage and must not
   float. SY8205's floating/auto-start behavior isn't stated. Doesn't change our
   design (dedicated VIN-divider on EN regardless, Q14), but matters if EN is ever
   left unpopulated as a fallback path.

---

## Citations (documents opened and read in full this session)

- AP64350 datasheet, DS41976 Rev. 5-2, Diodes Incorporated, Dec 2024 (25p).
  https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/2210280930_Diodes-Incorporated-AP64350SP-13_C2071691.pdf
- LMR33630 datasheet, TI, ZHCSHQ3F / Eng. base SNVSAN3, Aug 2017 - rev.F Nov 2020
  (36p; Chinese-market mirror, tables/figures/units identical to the English SNVSAN3
  base doc referenced on its own cover page).
  https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/2410121900_Texas-Instruments-LMR33630ADDAR_C841384.pdf
- "Application Notes: AN_SY8205," Rev 0.4, Silergy Corp, "Preliminary Specification"
  (11p). https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/1809050154_Silergy-Corp-SY8205FCC_C111875.pdf
- `boards/sbuck-5v3a/research/buck-ic.json` / `buck-ic.md` (component scout's
  shortlist/spec table) - rank order source, cross-checked against s4.6.
- `.claude/skills/ai-ee/reference/topologies/buck.md` (house buck reference, cited
  inline throughout where a part-specific delta applies).
