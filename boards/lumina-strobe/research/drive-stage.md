# drive-stage - pulsed constant-current LED drive (LUM-DTR-STROBE-A)

Scope: candidate parts only. Circuit design and final part selection belong to the architect (P2)
and the part-sourcer (P3).

Method: every candidate below was re-verified live through
`.claude/skills/ai-ee/scripts/parts_search.py` against the JLCPCB parts endpoint on **2026-07-28**.
Stock, price and Basic/Extended are that day's live figures. Nothing here is from memory: parts that
parts_search could not see were dropped. Web search was used only for the linear-mode-SOA literature
check and for the two datasheet PDFs read directly (IRF540N, IRF640N/S).

Prices are USD unit price at the qty-6 and qty-100 break. Quantity for this build is 6.

---

## 0. The operating point every candidate is judged against

Derived from `requirements.md` sections 2.5, 3.2, 3.4, 4 and 8.2, plus the architect's topology
(low-side N-FET in series with the string and a shunt, closed-loop to a settable current).

| Quantity | Value | Where it comes from |
|---|---|---|
| Bank | 2800 uF, 48 V nominal, **57 V worst case**, usable 48 -> 40 V | D-02 closed, ICD s6.4 |
| String | series white, **2.6 A peak**, Vf_total <= 38 V at 2.6 A | STR-REQ-12 |
| Shunt (this doc recommends) | 200 mohm -> **520 mV** at 2.6 A | see section 3 |
| **Pass FET Vds at flash start** (bank 48 V) | 48 - 38 - 0.52 = **9.5 V** -> **24.7 W** | arithmetic |
| **Pass FET Vds at window end** (bank 40 V) | **1.5 V** -> **3.8 W** | arithmetic |
| Dropout point | 38 + 0.52 + (2.6 A x Rds_on) = **38.9 V** with IRF640N | 1.1 V below the 40 V window floor |
| Full-output flash length at 2.6 A | `dt = C*dV/I = 2800u * 8 / 2.6` = **8.6 ms** | matches requirements s3.4 |
| **Energy into the FET per full flash** | `2.6 A * 5.5 V avg * 8.6 ms` = **0.123 J** | arithmetic |
| **FET average dissipation at 8.6 Hz** | **1.06 W** | 0.123 J x 8.6 Hz |
| Long-flash case (STR-REQ-01, 150 ms) | ~0.4 A, Vds 9.5 -> 1.5 V, **3.8 W peak / 0.33 J** | requirements s3.4 table |
| **Fault case: LED string shorted** | loop still regulates 2.6 A -> **48 V x 2.6 A = 125 W**, 148 W at 57 V | see risk R1 |

The FET's average dissipation (1.06 W) is the thermal number. Its peak (24.7 W for <= 8.6 ms) is the
SOA number. The fault case (125-148 W) is the number that actually decides the part.

---

## 1. The pass MOSFET

Ranked. Full candidate objects (incl. all price breaks and attributes) are in `drive-stage.json`.

| # | LCSC | MPN | Package | B/E | Stock | $ @6 | $ @100 | Datasheet | One line |
|---|---|---|---|---|---|---|---|---|---|
| 1 | **C23708** | **IRF640NSTRLPBF** | D2PAK (TO-263) | Ext | 11,380 | 0.778 | 0.512 | [pdf](https://www.lcsc.com/datasheet/lcsc_datasheet_2304140030_Infineon-Technologies-IRF640NSTRLPBF_C23708.pdf) | **Top pick.** 200 V / 18 A / 150 mohm planar HEXFET-5; 3.5x margin on the 57 V rail; SMD so it stays inside JLC top-side assembly |
| 2 | C2568 | IRF640NPBF | TO-220AB | Ext | 149,628 | 0.276 | 0.216 | [pdf](https://www.lcsc.com/datasheet/lcsc_datasheet_2304140030_Infineon-Technologies-IRF640NPBF_C2568.pdf) | Same die, THT. Cheapest and deepest stock of anything here - but see the thermal reversal in section 1.2 |
| 3 | C23982 | IRF540NSTRLPBF | D2PAK | Ext | 20,854 | 0.752 | 0.500 | [pdf](https://www.lcsc.com/datasheet/lcsc_datasheet_1806151820_Infineon-Technologies-IRF540NSTRLPBF_C23982.pdf) | 100 V / 33 A / 44 mohm. Lower dropout, but only 1.75x margin on 57 V |
| 4 | C2566 | IRF540NPBF | TO-220AB | Ext | 27,133 | 0.369 | 0.288 | [pdf](https://www.lcsc.com/datasheet/lcsc_datasheet_1811091924_Infineon-Technologies-IRF540NPBF_C2566.pdf) | THT form of #3 |
| 5 | C2616 | IRF3710STRLPBF | D2PAK | Ext | 2,435 | 1.088 | 0.700 | [pdf](https://www.lcsc.com/datasheet/lcsc_datasheet_1809192212_Infineon-Technologies-IRF3710STRLPBF_C2616.pdf) | Biggest 100 V SMD die on JLC (200 W, 23 mohm). Ciss 3.13 nF / Qg 130 nC slows the loop 2.7x; 45 % dearer |
| 6 | C169755 | IRF530NSTRLPBF | D2PAK | Ext | 16,906 | 0.773 | 0.510 | [pdf](https://www.lcsc.com/datasheet/lcsc_datasheet_2410121959_Infineon-Technologies-IRF530NSTRLPBF_C169755.pdf) | **Reject.** Pd only 70 W - smallest die of the family, least fault-case margin, no cost saving |
| 7 | C212023 | IRFP150NPBF | TO-247AC | Ext | 20,003 | 0.776 | 0.471 | [pdf](https://www.lcsc.com/datasheet/lcsc_datasheet_2304140030_Infineon-Technologies-IRFP150NPBF_C212023.pdf) | **Reject.** TO-247 is grossly oversized for 1.06 W and is THT-only |
| 8 | C3280469 | IXTP44N10T | TO-220-3 | Ext | 195 | 2.056 | 1.414 | [pdf](https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/2404031102_Littelfuse-IXYS-IXTP44N10T_C3280469.pdf) | **Reject.** The only IXYS/Littelfuse 100 V part JLC stocks - and it is a TrenchT2, not an IXYS Linear-L2. 195 pcs, 5x the price, no linear advantage |

### 1.1 SOA - read this before choosing

**Finding: no MOSFET on JLCPCB publishes a linear-mode / wide-SOA characterisation.** Searches for
IXYS Linear-L2 (`IXTP`, `IXTH`, `IXTA`, `IXTN`), ON `FQP`/`FDP`, Nexperia `PSMN`, and free-text
"wide SOA / linear mode" returned either high-voltage low-current IXYS parts (1.2-2.5 kV, 0.2-3 A),
modern trench switches, or nothing. The assignment asked me to flag a datasheet with no linear-mode
SOA plot as a red flag - **the honest answer is that this red flag applies to the entire JLC catalogue
for this function**, so the selection has to be made on generation (planar vs trench) plus derived
thermal headroom instead.

What the two datasheets I read actually publish (both PDFs read page-by-page, not inferred):

| Part | SOA figure | Curves plotted | Reference | DC curve? | 100 ms curve? |
|---|---|---|---|---|---|
| IRF640N/S/L | Fig. 8 "Maximum Safe Operating Area" | 10 us, 100 us, 1 ms, **10 ms** + an "operation in this area limited by Rds(on)" boundary | **Tc = 25 C**, Tj = 175 C, single pulse | **No** | **No** |
| IRF540N | Fig. 8 "Maximum Safe Operating Area" | 100 us, 1 ms, **10 ms** + Rds(on) boundary | **Ta = 25 C**, Tj = 175 C, single pulse | **No** | **No** |

Two things follow, and both are gotchas:

1. **The two plots are not directly comparable.** IRF640N's is referenced to *case*, IRF540N's to
   *ambient*. The IRF540N plot is the far more conservative of the two and reading them side by side
   will mislead. Compare on the tabulated thermal data instead (section 1.2).
2. **Nothing in this family is characterised past 10 ms.** STR-REQ-01's 100-200 ms flash therefore has
   **no published SOA curve at all** and must be derived from Pd / RthJC / RthJA. That derivation is
   comfortable (3.8 W at Vds <= 9.5 V for 150 ms, versus a 150 W Tc=25 C rating), but it is a
   derivation, not a datasheet guarantee. State it in the design document (DOC-01).

Literature check on linear-mode thermal instability (the failure mode a narrow-SOA trench part shows):
ST's FBSOA work puts the instability threshold at roughly **Vds > 25 V for advanced trench** and
**Vds > 15 V for advanced planar** devices. **The normal flash operating point is 9.5 V max - below
both thresholds**, so during a healthy flash this stage is not in the dangerous region for any of the
candidates. The **fault case (48-57 V at 2.6 A) is above both**, which is why R1 below is the real
risk and why I still recommend the planar HEXFET-5 generation over a modern low-Rds trench
(CRSS042N10N, IPB042N10N3, NCEP039N10D, AOD66923 and friends are all cheaper per milliohm and all
worse here).

Sources: [ST AN4901, low-voltage MOSFET behaviour in FBSOA](https://www.st.com/resource/en/application_note/an4901-low-voltage-mosfet-technology-behavior-in-fbsoa-stmicroelectronics.pdf),
[how2power: wide-SOA trench MOSFET enables rugged linear-mode operation](https://www.how2power.com/newsletters/2204/articles/H2PToday2204_design_STMicroelectronics.pdf),
[Nexperia IAN50006, power MOSFETs in linear mode](https://www.nexperia.com/applications/interactive-app-notes/IAN50006_Power_MOSFETs_in_linear_mode).

### 1.2 Package power capability on 1.6 mm FR4 - and a reversal worth knowing

Datasheet table values (read from the PDFs, not estimated):

| Part / package | Pd @ Tc=25 C | RthJC max | RthJA | Note |
|---|---|---|---|---|
| IRF640NS (D2PAK) | 150 W | 1.0 C/W | **40 C/W** (PCB mount) | Front page: "can dissipate up to **2.0 W** in a typical surface mount application" |
| IRF640N (TO-220AB) | 150 W | 1.0 C/W | **62 C/W** (free air) | - |
| IRF540NS (D2PAK) | 130 W | 1.15 C/W | **40 C/W** (PCB mount) | Footnote: "**when mounted on 1 inch square PCB** (FR-4 or G-10)" |
| IRF540N (TO-220AB) | 130 W | 1.15 C/W | 62 C/W | - |

Applied to this board's sealed-enclosure ambients (requirements s4: **56 C af / 69 C at**):

| Package | Allowed at Tj=175 C, 69 C air | Allowed at a **125 C design limit**, 69 C air | vs the required 1.06 W |
|---|---|---|---|
| D2PAK on 1 in^2 copper | 2.65 W | **1.40 W** | **1.3x margin - passes, tight** |
| TO-220AB in still air, no heatsink | 1.71 W | **0.90 W** | **FAILS at a 125 C design limit** |

**The reversal: the surface-mount D2PAK on a copper pour beats the TO-220 in still air.** In a sealed
plastic box with no forced airflow, the TO-220's convective path is worse than the D2PAK's conductive
path into the board. That inverts the usual "THT power part is the safe choice" instinct and is the
main reason #1 outranks #2 despite #2 being 2.8x cheaper with 13x the stock.

Placement consequences for that 1 in^2 (645 mm^2) pour - all three constraints bite at once:

- The pour is on the **drain**, which is a **48 V net** -> the **0.60 mm outer-layer clearance rule
  (requirements s8.1) applies around its entire perimeter**, on every layer, including through-board.
- It **cannot** go in the DC-DC hot zone **(2,46)-(36,68)**, which forbids LED drivers outright.
- It **cannot** go in the antenna column **(88,25)-(100,55)** - no copper on any layer there.

### 1.3 On the "fast fully-enhanced switch" alternative

Rejected, and it is worth writing down why so it does not come back. With no output inductor and no
bulk output capacitance (both forbidden by STR-REQ-01's no-decay-tail rule), a hard-switched FET makes
the string current `I = (Vbank - Vf) / R_series`. Over the 48 -> 40 V window that numerator goes
10 V -> 2 V, i.e. **a 5:1 current swing during a single flash** - the visible decay STR-REQ-01
forbids, just produced resistively instead of capacitively. A linear pass element is not a compromise
here; it is the only shape that satisfies STR-REQ-01 + STR-REQ-11 under the stated constraints. The
low duty cycle is what makes its dissipation affordable (1.06 W average, section 0).

---

## 2. The current-regulation loop

### 2a. Op-amp + shunt + FET (recommended shape)

The FET source sits on the shunt, within 520 mV of GND, so the error amp needs an input common-mode
range that **includes ground** - that, not bandwidth, is the hard filter. Running it from **+12 V**
(available on J3 pins 9/11) lets it swing the gate to ~10.5 V, matching every candidate FET's
Rds(on) @ Vgs=10 V spec.

| # | LCSC | MPN | Package | B/E | Stock | $ @6 | $ @100 | Datasheet | One line |
|---|---|---|---|---|---|---|---|---|---|
| 1 | **C18229** | **LM2904DR2G** | SOIC-8 | Ext | 732,316 | 0.068 | 0.055 | [pdf](https://www.lcsc.com/datasheet/lcsc_datasheet_1811012110_onsemi-LM2904DR2G_C18229.pdf) | **Top pick.** Industrial LM358: 3-32 V, CM includes GND, **-40..+105 C**, 700 kHz. 732k stock at 6.8 cents |
| 2 | C415708 | LM358A-SR (3PEAK) | SOIC-8 | Ext | 132,562 | 0.096 | 0.074 | [pdf](https://www.lcsc.com/datasheet/lcsc_datasheet_1912111437_3PEAK-LM358A-SR_C415708.pdf) | Pin-compatible, 3-36 V, **-40..+125 C**, 900 kHz, rail-to-rail output. Best pick if the +12 V rail is dropped |
| 3 | C1850238 | LM358BIDR (TI) | SOIC-8 | Ext | 60,000 | 0.106 | 0.087 | [pdf](https://www.lcsc.com/datasheet/lcsc_datasheet_2303020130_Texas-Instruments-LM358BIDR_C1850238.pdf) | 36 V, 1.2 MHz, RRO, **Vos 3 mV max** - the cheap way to halve the low-dim error (see R2) |
| 4 | C4366107 | TLV9152IDGKR | VSSOP-8 | Ext | 2,311 | 1.110 | 0.705 | [pdf](https://www.lcsc.com/datasheet/lcsc_datasheet_2302220430_Texas-Instruments-TLV9152IDGKR_C4366107.pdf) | 4.5 MHz, 21 V/us, **Vos 125 uV**, RRIO, -40..+125 C. Only candidate whose offset does not dominate a 10 % setpoint. 16 V max supply, 2.3k stock, 16x the price |
| 5 | C56285 | OPA2170AIDR | SOIC-8 | Ext | 683 | 0.818 | 0.568 | [pdf](https://www.lcsc.com/datasheet/lcsc_datasheet_1810181614_Texas-Instruments-OPA2170AIDR_C56285.pdf) | 36 V, 1.2 MHz, Vos 1.8 mV, -40..+125 C. 683 pcs is thin for a 6-board build plus spares |
| - | C7950 | LM358DR2G (onsemi) | SOIC-8 | **BASIC** | 695,848 | 0.057 | 0.046 | [pdf](https://www.lcsc.com/datasheet/lcsc_datasheet_2304140030_onsemi-LM358DR2G_C7950.pdf) | **Rejected on temperature.** See below |

**JLC Basic finding.** The entire JLC Basic op-amp shelf is three parts: **LM358DR2G (C7950),
LM324DT (C71035), NE5532DR (C7426)**. The only one that fits this circuit is the LM358DR2G - and it
is graded **0 to +70 C** against an internal air temperature of **56 C (af) / 69 C (at)**
(requirements s4). That is 1 C of margin in at-mode. **Reject the Basic part on temperature grade,
not on function**, and take the Extended LM2904 for one extra cent. Note the same trap for anyone
scanning the shelf later: the LM2904 is *not* on the Basic list (a `--basic-only` search for it
returns zero).

**Optional precision front end** - only if R2 pushes you there:

| # | LCSC | MPN | Package | B/E | Stock | $ @6 | $ @100 | Datasheet | One line |
|---|---|---|---|---|---|---|---|---|---|
| a | C122228 | INA180A1IDBVR | SOT-23-5 | Ext | 34,621 | 0.284 | 0.225 | [pdf](https://www.lcsc.com/datasheet/lcsc_datasheet_2410010302_Texas-Instruments-INA180A1IDBVR_C122228.pdf) | Gain 20 V/V, 350 kHz, **Vos 25 uV**, CM -0.2..26 V. Removes op-amp offset from the dim setpoint and lets the shunt drop to 20-50 mohm |
| b | C2058943 | INA181A1IDBVR | SOT-23-6 | Ext | 5,533 | 0.450 | 0.258 | [pdf](https://www.lcsc.com/datasheet/lcsc_datasheet_2302221300_Texas-Instruments-INA181A1IDBVR_C2058943.pdf) | Same core with an enable pin; thinner stock, 60 % dearer |

**Loop speed vs STR-REQ-11 (< 1 ms optical edge).** IRF640N Ciss 1160 pF, Qg 67 nC, Qgs 11 nC. The
gate only has to reach the ~5 V plateau, and the LM2904's own slew rate (0.3-0.6 V/us) dominates:
**8-17 us**, roughly 60x inside the 1 ms budget. Even the slowest candidate FET (IRF3710S, Ciss
3.13 nF) stays inside. **Turn-off is the weaker side**: the LM358/LM2904 output stage sinks poorly
near ground, so a gate pull-down resistor (4.7k discharges 1.2 nF in ~6 us) plus the hard clamp in
section 4 is the belt-and-braces. Bench-verify the falling edge - this is the one number in the block
that a datasheet will not give you.

### 2b. Dedicated high-voltage linear / hysteretic LED driver IC - NO SUITABLE JLC PART

**Finding: JLCPCB stocks no LED driver IC that can do this job.** Every candidate and its rejection:

| LCSC | MPN | Rating | $ @6 | Datasheet | Why rejected |
|---|---|---|---|---|---|
| C460648 | AL5812MP-13 | 1-60 V linear CC, adjustable, **150 mA** | 0.385 | [pdf](https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/2304140030_Diodes-Incorporated-AL5812MP-13_C460648.pdf) | Highest-voltage *adjustable linear* CC driver on JLC and it is **17x short on current**. Also 60 V abs max vs a 57 V worst-case rail = 3 V margin |
| C332295 | AL5809-20S1-7 | 2.5-60 V CCR, 20 mA | 0.156 | [pdf](https://www.lcsc.com/datasheet/lcsc_datasheet_2304140030_Diodes-Incorporated-AL5809-20S1-7_C332295.pdf) | 20 mA, and its dimming input is specified **100-200 Hz** - fails the 9.766 kHz carrier PWM outright |
| C154739 | BCR421UW6Q-7 | 40 V, 350 mA linear | 0.943 | [pdf](https://www.lcsc.com/datasheet/lcsc_datasheet_2304140030_Diodes-Incorporated-BCR421UW6Q-7_C154739.pdf) | 40 V input rating is below the 48 V rail before current is even considered |
| C128367 | NSI45020AT1G | 45 V, 20 mA CCR | 0.122 | [pdf](https://www.lcsc.com/datasheet/lcsc_datasheet_1810010411_onsemi-NSI45020AT1G_C128367.pdf) | 45 V < 48 V rail; 130x short on current |
| C213553 | TPS92515HVDGQR | 65 V, 2 A, analog + PWM dim | 2.192 | [pdf](https://www.lcsc.com/datasheet/lcsc_datasheet_2304140030_Texas-Instruments-TPS92515HVDGQR_C213553.pdf) | Electrically the closest part JLC has - but it is a **hysteretic buck**. Its inductor and output capacitance are exactly what STR-REQ-01 forbids (they hold LED current up after the gate closes = visible decay tail). Also 2 A < 2.6 A |
| C526360 | AL8862SP-13 | 5-60 V, 1 A buck, analog + PWM dim | 0.594 | [pdf](https://www.lcsc.com/datasheet/lcsc_datasheet_2412251118_Diodes-Incorporated-AL8862SP-13_C526360.pdf) | Same inductor / decay-tail objection; 1 A |
| C9099 | HV9910BLG-G | 8-450 V hysteretic buck controller, external FET | 1.210 | [pdf](https://www.lcsc.com/datasheet/lcsc_datasheet_2409301133_Microchip-Tech-HV9910BLG-G_C9099.pdf) | Voltage and current are fine, but still an inductor-based buck -> decay tail. Its PWM dimming input is also specified far below 9.766 kHz |

Two independent reasons this branch is closed, and the architect should record both:

1. **Topology.** Every CC driver at this power level on JLC is a switching buck. An inductor plus
   output capacitance is precisely the energy storage that produces the decay tail STR-REQ-01 forbids
   and blunts the < 1 ms edge STR-REQ-11 demands.
2. **Dimming bandwidth.** As the assignment predicted, the CC parts that do offer PWM dimming specify
   it at **100 Hz - 1 kHz** (AL5809: 100-200 Hz; HV9910B and the buck family: sub-kHz for a linear
   brightness response). The carrier's LEDC PWM is fixed at **9.766 kHz** and channels on one timer
   share both frequency and resolution (CAR-REQ-11), so this board cannot ask for a slower PWM without
   dragging the other channels down with it. **Reject all PWM-dim-limited CC modules on this ground.**

Conclusion: **option (a), the discrete op-amp + shunt + FET loop, is the only viable shape.** That is
not merely the architect's preference - it is what the JLC catalogue forces.

---

## 3. Current-sense resistor

Sizing argument (this is the one number in the block with real design freedom):

- The bank has ~10 V of headroom above the string (48 V vs Vf 38 V), so spending 0.5 V on the shunt is
  affordable, and it buys signal.
- At 200 mohm: full scale = **520 mV**, peak **1.35 W**, average **~0.10 W** (7.4 % duty at 8.6 Hz).
  A 2-3 W 2512 has 1.5-2.2x margin on the peak and 20x on the average.
- At 200 mohm the **10 % dim point is 52 mV**, so an LM2904's 7 mV worst-case offset is 13 %, not 50 %.
  At 50 mohm the same op-amp would be 54 % off at the 10 % setpoint. **This is why 200 mohm, not
  50 mohm.**
- Dropout cost: 0.52 V of the 8 V window - regulation is lost at 38.9 V bank, still 1.1 V below the
  40 V window floor.

| # | LCSC | MPN | Value | Package | B/E | Stock | $ @6 | $ @100 | Datasheet | One line |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | **C2903473** | **HoJLR2512-3W-200mR-1%** | 200 mohm 3 W 1 % 50 ppm | 2512 | Ext | 100,046 | 0.087 | 0.071 | [pdf](https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/2110101130_Milliohm-HoJLR2512-3W-200mR-1-_C2903473.pdf) | **Top pick.** 2.2x margin on the 1.35 W peak, 100k stock |
| 2 | C5375488 | HoYLR2512-3W-200mR-1% | 200 mohm 3 W 1 % | 2512 | Ext | 40,340 | 0.052 | 0.042 | **none published** | Same value, 40 % cheaper, 40k stock - but **LCSC lists no datasheet**. Fine as a second source, weak as the primary |
| 3 | C459674 | RLP25FEER200 (TA-I) | 200 mohm 2 W 1 % 50 ppm | 2512 | Ext | 25,060 | 0.063 | 0.051 | [pdf](https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/2304140030_TA-I-Tech-RLP25FEER200_C459674.pdf) | Branded alternative with a real datasheet; 2 W still gives 1.5x on the peak |
| 4 | C160587 | RLP25FEER100 (TA-I) | 100 mohm 2 W 1 % 50 ppm | 2512 | Ext | 141,313 | 0.055 | 0.044 | [pdf](https://www.lcsc.com/datasheet/lcsc_datasheet_2304140030_TA-I-Tech-RLP25FEER100_C160587.pdf) | Halves shunt burden (260 mV, 0.68 W peak) and doubles the relative offset error |
| 5 | C459687 | RLP25FEGR050 (TA-I) | 50 mohm 3 W 1 % 50 ppm | 2512 | Ext | 263,424 | 0.065 | 0.052 | [pdf](https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/2304140030_TA-I-Tech-RLP25FEGR050_C459687.pdf) | Minimum headroom cost (130 mV FS). Only viable behind an INA180 |

**Inductance:** 2512 alloy/metal-plate shunts are a few nH, and at a 1 ms current edge (di/dt ~ 2.6 kA/s)
the inductive term is picovolts - not a constraint here. It would be if the architect ever moved to a
sub-microsecond edge. **Kelvin (4-terminal) shunts:** a parametric search returned **zero** 4-terminal
2512 parts on JLC, so use a 2-terminal part with a Kelvin *layout* (sense traces to the pad ends).

---

## 4. Gate drive / level shift / ENABLE gating

**Finding: no gate driver and no level shifter are needed.** The FET source sits within 520 mV of GND,
so it is a true low-side device, and the op-amp on +12 V is simultaneously the error amplifier and the
gate driver. The 3.3 V PWM never touches the gate - **it steers the reference**, which is also what
gives the square optical edge without fighting the loop.

What *is* needed: a reference steering switch, and a hard ENABLE interlock that survives the ICD's
"no mate sequencing" clause (requirements s3.3 point 3: **48 V may arrive before 3.3 V**).

| # | LCSC | MPN | Function | Package | B/E | Stock | $ @6 | $ @100 | Datasheet | One line |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | **C8545** | **2N7002** | gate clamp + discrete inverter | SOT-23 | **BASIC** | 458,114 | 0.018 | 0.018 | [pdf](https://www.lcsc.com/datasheet/lcsc_datasheet_2304140030_Jiangsu-Changjing-Electronics-Technology-Co---Ltd--2N7002_C8545.pdf) | **Top pick for ENABLE.** Two of these (one inverting ENABLE, one clamping gate-to-source) build a hard disable that **works with the 3V3 rail dead**. JLC Basic, 1.8 cents |
| 2 | **C46744** | **SGM3157YC6/TR** | SPDT reference steering | SC-70-6 | Ext | 13,714 | 0.129 | 0.113 | [pdf](https://www.lcsc.com/datasheet/lcsc_datasheet_1809051511_SGMICRO-SGM3157YC6-TR_C46744.pdf) | **Top pick for flash gating.** 1.8-5.5 V, 4.5 ohm, 15/20 ns - steers the regulator reference between the RC setpoint and GND |
| 3 | C46388 | TS5A3159DCKR | SPDT reference steering | SC-70-6 | Ext | 37,122 | 0.292 | 0.237 | [pdf](https://www.lcsc.com/datasheet/lcsc_datasheet_1808031721_Texas-Instruments-TS5A3159DCKR_C46388.pdf) | 1 ohm Ron (4.5x better) at 2.3x the price; pin-compatible alternate to #2 |
| 4 | C19829652 | 74LVC1G08GW | AND(PWM, ENABLE) | SOT-353 | Ext | 9,436 | 0.056 | 0.045 | [pdf](https://www.lcsc.com/datasheet/lcsc_datasheet_2402021504_TECH-PUBLIC-74LVC1G08GW_C19829652.pdf) | Cleanest schematic form of the ENABLE gate - **but see the power-off caveat** |
| 5 | C19829650 | 74LVC1G04GW | NOT(ENABLE) | SOT-353 | Ext | 7,117 | 0.057 | 0.046 | [pdf](https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/2402021504_TECH-PUBLIC-74LVC1G04GW_C19829650.pdf) | Logic-gate form of the inverter that drives the gate clamp; same caveat |
| 6 | C133643 | SN74LVC1G66DBVR | SPST switch | SOT-23-5 | Ext | 38,857 | 0.175 | 0.138 | [pdf](https://www.lcsc.com/datasheet/lcsc_datasheet_1809251629_Texas-Instruments-SN74LVC1G66DBVR_C133643.pdf) | Single-throw, so it needs an added pull-down to force the reference to zero. Prefer the SPDT |
| 7 | C20623191 | UCC27517DBVR (UMW) | 4 A low-side gate driver | SOT-23-5 | Ext | 19,184 | 0.186 | 0.140 | [pdf](https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/2402211157_UMW-Youtai-Semiconductor-Co---Ltd--UCC27517DBVR-UMW_C20623191.pdf) | **Not usable inside the linear loop** (it saturates). Listed only in case the architect wants a hard sub-microsecond gate-discharge path in parallel with the op-amp |

**Two caveats the architect must not miss:**

- **JLC has no Basic single-gate logic at all.** A `--basic-only` search for a single AND gate returns
  zero. Every 74LVC1Gxx here is Extended. If the BOM is being pushed toward Basic-only, the discrete
  2N7002 route (#1) is the only Basic-compatible way to build the interlock.
- **Do not make an LVC gate the only ENABLE interlock.** LVC inputs have clamp diodes to Vcc; with
  3.3 V dead and a live 3.3 V PWM line still driven from the carrier, current flows into the dead rail
  and the gate's output state is undefined. The ICD explicitly refuses to guarantee mate order
  (requirements s3.3 point 3). **The interlock of record should be passive + discrete**: a gate-source
  pull-down resistor (off with *everything* dead) plus the 2N7002 clamp. STR-REQ-21 asks for outputs
  off during MCU reset and firmware update; this arrangement is off during those *and* during a
  half-mated connector.
- The same clamp node is the natural landing point for the **STR-REQ-20 firmware-independent
  over-temperature shutdown**. That comparator/thermostat belongs to another block, but this stage
  must expose the node - flag it in the interface list.

---

## 5. The intensity setpoint path (STR-REQ-04)

### 5.1 RC-filtered PWM - the recommendation, with the arithmetic

Carrier PWM: **13-bit at 9.766 kHz**, so T = **102.4 us**, amplitude = the +3V3 rail.
Worst-case single-pole ripple is at 50 % duty: `Vpp ~= Vdd * D(1-D) * T / tau`.

| Filter | tau | fc | Ripple pp @ D=0.5 | as % of 3.3 V FS | Settle to 1 % | Verdict |
|---|---|---|---|---|---|---|
| 10k + 100nF | 1.0 ms | 159 Hz | **84 mV** | 2.6 % | **4.6 ms** | **Recommended** |
| 22k + 100nF | 2.2 ms | 72 Hz | 38 mV | 1.2 % | 10.1 ms | Good if ripple bothers you |
| 100k + 100nF | 10 ms | 16 Hz | 8.4 mV | 0.26 % | 46 ms | **Too slow** - misses a 25 Hz flash period |
| 10k+100nF twice | 1.0 ms x2 | - | **1.4 mV** | 0.04 % | ~11 ms | Overkill; costs 2.4x the settling |

**Does a filtered 9.766 kHz PWM settle fast enough to be useful? Yes, with one firmware contract.**

- 2.6 % of ripple at **9.766 kHz** is optically invisible: it is far above any flicker-perception
  threshold, and the loop's own bandwidth plus the LED's response attenuate it further.
- 4.6 ms settling sits comfortably inside the **40 ms** period at SYS-REQ-03's 25 Hz ceiling, and
  inside the 116 ms period at the 8.6 Hz full-energy rate.
- **What it cannot do is change amplitude instantly.** A full-scale setpoint change takes ~4.6 ms to
  land inside 1 %, which is ~12 % of the 40 ms period at 25 Hz and most of a 10 ms full-output flash.
  **Firmware must program the amplitude at least ~5 ms before the flash it applies to** (in practice:
  one flash period ahead). That is a real constraint on the governor (STR-REQ-06) and belongs in the
  design document.
- Scaling: with a 200 mohm shunt, full scale is 520 mV, so the 3.3 V PWM needs a **6.35:1** divider
  (5k36 / 1k00, E96). Put the divider inside the filter and the Thevenin source impedance falls to
  845 ohm - which matters, because the LM2904's input bias current (45 nA typ, 250 nA max) across a
  bare 10k would add **0.45-2.5 mV** of error, comparable to its own offset.
- **Free improvement: buffer the setpoint with the second half of the same dual op-amp.** The loop
  uses one amplifier; the LM2904/LM358 package contains two. The spare one as a unity buffer kills
  both the source-impedance error and the analog switch's Ron error at **zero extra parts and zero
  extra cost**.

Accuracy chain note: the PWM amplitude *is* the +3V3 rail, so LED current inherits the 3V3 rail's
tolerance. That is the only reason the references below are listed at all.

### 5.2 Parts for the setpoint path

| # | LCSC | MPN | Function | Package | B/E | Stock | $ @6 | $ @100 | Datasheet | One line |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | **C17414** | 0805W8F1002T5E (10k, 1 %) | RC divider/filter | 0805 | **BASIC** | 15.8 M | 0.011 | 0.011 | [pdf](https://www.lcsc.com/datasheet/lcsc_datasheet_2411221126_UNI-ROYAL-Uniroyal-Elec-0805W8F1002T5E_C17414.pdf) | **Top pick: the whole setpoint path is an 0805 divider plus an X7R cap, ~$0.03.** 0805 also matches the size floor the 48 V-domain rule forces elsewhere on this board |
| 2 | C144198 | MCP4725A0T-E/CH | 12-bit I2C DAC | SOT-23-6 | Ext | 26,094 | 1.012 | 0.688 | [pdf](https://www.lcsc.com/datasheet/lcsc_datasheet_1811151442_Microchip-Tech-MCP4725A0T-E-CH_C144198.pdf) | The alternative: exact, 6 us settling, frees a PWM channel. **33x the cost**, needs I2C traffic in the flash path, and is **single-source** (see R4) |
| 3 | C478093 | MCP4728T-E/UN | quad 12-bit I2C DAC | MSOP-10 | Ext | 10,742 | 2.663 | 1.711 | [pdf](https://www.lcsc.com/datasheet/lcsc_datasheet_2410121924_Microchip-Tech-MCP4728T-E-UN_C478093.pdf) | Only worth it if open question 1 closes as **RGBW** and four setpoints are needed |
| 4 | C963380 | TL431 (JSMSEMI) | 2.5 V shunt reference | SOT-23 | Ext | 457,191 | 0.039 | 0.039 | [pdf](https://www.lcsc.com/datasheet/lcsc_datasheet_2308071512_JSMSEMI-TL431_C963380.pdf) | Optional: only if the 3V3 rail's own accuracy is judged insufficient. 457k stock, 4 cents |
| 5 | C107244 | LM4040D25FTA | 2.5 V 1 % shunt reference | SOT-23 | Ext | 3,781 | 0.436 | 0.253 | [pdf](https://www.lcsc.com/datasheet/lcsc_datasheet_2304140030_Diodes-Incorporated-LM4040D25FTA_C107244.pdf) | Tighter initial accuracy and 150 ppm/C, at 11x the TL431 price |
| - | C43499 | MCP4921-E/SN | 12-bit **SPI** DAC | SOIC-8 | Ext | 591 | 2.605 | 1.778 | [pdf](https://www.lcsc.com/datasheet/lcsc_datasheet_1806141522_Microchip-Tech-MCP4921-E-SN_C43499.pdf) | **Rejected.** Requirements s2.4 ASSUMES no SPI device and leaves `DSPI_*` unconnected; 591 pcs stock. Do not re-open the SPI bus for a setpoint |

**Note on JLC Basic and the TL431:** a `--basic-only` search for TL431 returns zero - none of the
457k-stock TL431s is a Basic part. Same shelf problem as the logic gates.

---

## 6. Recommended set and cost

| Function | Part | LCSC | $ @6 |
|---|---|---|---|
| Pass FET | IRF640NS D2PAK | C23708 | 0.778 |
| Error amp (dual; 2nd half buffers the setpoint) | LM2904DR2G | C18229 | 0.068 |
| Shunt | 200 mohm 3 W 2512 | C2903473 | 0.087 |
| Flash gating | SGM3157 SPDT | C46744 | 0.129 |
| ENABLE interlock | 2N7002 x2 | C8545 | 0.035 |
| Setpoint RC + gate/bias passives | 0805 1 % + X7R | C17414 etc. | ~0.10 |
| | | **Total** | **~$1.20 / board** |

Against open question 7's default **$25/board at qty 6**, the drive stage is about **5 %** of the
budget. The expensive things on this board remain the bank and the LED, not this stage - which means
there is room to trade up to the LM358B (+$0.04) or even the TLV9152 (+$1.04) if R2 says so.

---

## 7. Risks

**R1 - The LED-short fault, not the flash, is the SOA case. [highest]**
If the string shorts (solder bridge, wiring fault, dead emitter shorting), the loop keeps regulating
2.6 A and the FET absorbs the whole rail: **125 W at 48 V, 148 W at the 57 V worst case**, versus
IRF640N's 150 W Pd at Tc = 25 C - and it does *not* self-terminate, because the loop never enters
dropout, so it runs for the full PWM on-time (up to 200 ms per STR-REQ-01). This is above both
linear-mode instability thresholds from the literature (25 V trench / 15 V planar). **Needs an
architectural answer**: a Vds-sensing comparator that folds back or latches off, a hardware on-time
limit, or explicit reliance on the STR-REQ-20 over-temperature shutdown - and if it is the last one,
the thermal sensor has to be on or near the FET, not only on the LED.

**R2 - Op-amp offset sets the floor on STR-REQ-04's "barely visible 10-20 %" pulse.**
At 200 mohm the 10 % setpoint is 52 mV. Worst-case offset: **LM2904 7 mV = 13 %**, **LM358B 3 mV =
6 %**, **TLV9152 125 uV = 0.24 %**. Adequate if "barely visible" is subjective; **not** adequate if
4-6 fixtures must match each other at low levels. This is the one genuine spec decision inside the
loop, and it is a $0.04 (LM358B) or $1.04 (TLV9152) decision, not an architectural one.

**R3 - No linear-mode-rated MOSFET exists on JLCPCB.**
Nothing in the catalogue publishes a wide-SOA / linear-mode characterisation, and nothing in the
recommended family publishes any SOA curve past **10 ms**, so the 100-200 ms flash case is a
derivation rather than a datasheet guarantee. Mitigated by the fact that the healthy operating point
(9.5 V max) is below both published instability thresholds, and by choosing the planar HEXFET-5
generation over a modern trench. **Record the derivation in DOC-01.**

**R4 - Single-source exposure is confined to two optional parts.**
Everything in the recommended set has pin-compatible alternates: the D2PAK/TO-220AB power footprints
take IRF530N/IRF540N/IRF640N/IRF3710 from Infineon plus JSMSEMI/OSEN/Minos/UMW; the SOIC-8 dual op-amp
pinout takes LM2904/LM358/LM358B/OPA2170/TLV9152; 2512 shunts come from a dozen vendors; SGM3157 and
TS5A3159 are pin-compatible in SC-70-6. **The exceptions are optional parts**: the **MCP4725** has no
pin-compatible I2C DAC alternate on JLC (Microchip only), and the **INA180/INA181** pair is TI-only.
Both are avoidable by taking the RC setpoint and the direct shunt sense. **Net: no single-source risk
in the recommended BOM.**

**R5 - The D2PAK thermal pour fights three board-level constraints at once.**
The 40 C/W figure is conditioned on **1 inch square of copper**, that copper is a **48 V net** (0.60 mm
clearance all round, requirements s8.1), and it is excluded from both the DC-DC hot zone
**(2,46)-(36,68)** and the antenna column **(88,25)-(100,55)**. With a 100 x 80 mm board that also
loses 780 mm2 to the RJ45 notch and must host a 2800 uF / 100 V bank, 645 mm2 of dedicated drain pour
is a real placement claim. If it cannot be met, the D2PAK's RthJA rises and the **1.3x margin at a
125 C design limit disappears**. Worth an early placement sanity check at P5, not a P8 discovery.

**R6 - The Basic-parts shelf is thinner than it looks for this block.**
Only **two** parts in the whole drive stage are JLC Basic: the **2N7002** and the **0805 resistors**.
The Basic op-amp is temperature-disqualified, there is no Basic single-gate logic, no Basic TL431,
and no Basic MOSFET at 100 V (a `--basic-only` MOSFET search filtered to 100 V returns **zero**). If
the program has a Basic-parts preference, this is where it breaks, and it breaks for good reasons.

---

## 8. Verify-later / open items for the architect

1. **Turn-off edge.** The op-amp's weak low-side sink is the only part of STR-REQ-11 that a datasheet
   will not settle. Bench-measure the falling optical edge with the chosen gate pull-down.
2. **Fault-case answer for R1** - Vds comparator, on-time limit, or explicit over-temp reliance.
3. **Offset grade decision for R2** - LM2904 vs LM358B vs TLV9152.
4. **Firmware contract**: amplitude must be programmed at least one flash period before the flash it
   applies to (section 5.1).
5. **+12 V vs 48 V-derived bias** for the op-amp. ICD s6.3 prefers taking power from `+48V_SW`, but
   the amp draws ~1 mA and needs a clean low rail; +12 V (J3 pins 9/11) is the simple answer. The ICD
   preference is about *power*, not housekeeping, so this is likely fine - confirm.
6. **Shunt value 200 mohm** is a recommendation derived from the offset argument, not a constraint.
   If the architect adopts the INA180 front end, 50 mohm becomes the better choice and the bank
   headroom improves by 0.39 V.
