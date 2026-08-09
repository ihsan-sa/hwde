# rf-de-20m - DIGI-KEY BOM (P10 alternate sourcing)

Companion to `BOM-digikey.csv`. Built 2026-08-09 by the part-sourcer, at the owner's
instruction to **order every part from Digi-Key instead of LCSC/JLCPCB**.

Every line below was verified against a **live digikey.com product page fetched today**.
Stock and price are same-day values and will drift - re-check at cart time.

Source of record for the design is unchanged: `parts/parts.json`, `fab/BOM.csv`,
`fab/CPL.csv`, `fab/README.md`. **Nothing in this pass modified the board, the schematic,
`parts.json` or the existing fab outputs.**

---

# 1. HEADLINE: EPC2019 IS IN STOCK AT DIGI-KEY. THE ORDER IS UNBLOCKED.

| | LCSC | **Digi-Key** |
|---|---|---|
| Stock | **0** (blocking the whole order since P3) | **21,326** |
| Digi-Key PN | - | **917-1087-1-ND** (cut tape) |
| MPN / Mfr | EPC2019 / EPC | EPC2019 / EPC |
| Price | $3.93 reference-only | $5.31 @1, **$3.52 @10**, $2.76 @25 |
| Status | Out of Stock | Active, ships today |

`fab/README.md` s1 says "DO NOT ORDER YET" and names this part as the sole reason.
**That hold is released by this BOM.** 12 pieces at $3.52 = **$42.24**.

Two things to keep in view:

- **Factory lead time is 16 weeks.** Distributor stock is the only realistic supply.
  If the board may ever be rebuilt, buy the die now rather than later.
- **No substitute exists and none is offered.** The P3 survey already established that
  every other 200 V-class GaN either fails the reopening window (Coss(er) <= 300 pF,
  Rds(on) <= 12 mohm typ, RthJB <= 4.0 C/W) or has no stock anywhere.

---

# 2. THIS CSV IS NOT THE WHOLE ORDER

## 2.1 The PCB is still a JLCPCB order

**Digi-Key does not make the board.** `BOM-digikey.csv` covers components only. The bare
PCB is a separate JLCPCB order and every requirement in `fab/README.md` s3.1 and s3.2 still
stands, unchanged:

| field | value |
|---|---|
| Layers / size / qty | 4 layer, 120.000 x 80.000 mm, **5 pcs**, 1.6 mm |
| Stackup | **`JLC04161H-1080B`** - the 0.2444 mm L1-L2 dielectric is load-bearing |
| Copper | 1 oz outer, 0.5 oz inner |
| **TG155 or better** | mandatory - the etched spirals run 100-140 C |
| **ENIG, not HASL** | mandatory - EPC AN009, plus a 0.4 mm WCSP and a flat heatsink land |
| **POFV (resin-filled, capped vias)** | mandatory - 17 GND vias are open at both ends |

Those three order-time options exist **only if a human ticks them**. None is expressible in
a gerber. Upload `rf-de-20m_gerbers.zip` as before.

## 2.2 Assembly is now YOUR problem, and it is genuinely hard

The LCSC/JLC path assumed **JLC sourced every part and ran the PCBA line**. Digi-Key ships
loose cut tape. So this becomes a **hand-assembly order, or a self-supplied-parts order**
to a third-party assembler.

State plainly what that means on this specific board:

- **U201 (LMG1020) is a 0.4 mm-pitch DSBGA-6 WCSP, 0.8 x 1.2 mm.** It is not
  hand-solderable with an iron. Stencil plus reflow or hot air, and you cannot inspect the
  joints without X-ray.
- **Q201/Q202 are two bare passivated EPC2019 die** with 0.23 mm mask-defined lands on a
  0.6 mm solder-bar pitch. These are the hardest parts to place on the board, they are the
  most expensive, and there is no package to grip or self-align against. Misplacing one is
  a $3.52 mistake plus a dead board.
- Everything else is 0201-and-up SMD plus one THT terminal block - ordinary.

If you are not set up for fine-pitch reflow with a stencil, get the board assembled by a
shop that accepts consigned parts. Do not plan to iron-solder U201.

Related, and unchanged: the **nine DNP sites** (`fab/README.md` s2) are still DNP.
C203, C205, C206, C308, C309, C318, C321, C322, C323 **must not be fitted** - fitting
C203/C308/C309 silently undoes the P8 ZVS fix and gives you ~53 W instead of ~113.8 W.
Hand assembly makes this easier to get wrong, not harder: there is no placement preview to
count against. Work from `fab/CPL.csv` (59 placements), not from this CSV.

---

# 3. COST

| | |
|---|---|
| **Total order, 25 lines, as specified** | **$242.07** |
| Per board, total divided by 5 | **$48.41** |
| Per board, parts *actually fitted* on one board | **$31.33** |

The gap between $48.41 and $31.33 is spares, DNP-site coverage and the tank trim reserve -
deliberate, see s5.

Parts only. Excludes shipping, tax, the PCB, and the stencil.

**Four lines are 64% of the money:**

| line | cost | share |
|---|---|---|
| Q201/Q202 EPC2019 x12 | $42.24 | 17% |
| J201/J301 SMA x12 | $37.80 | 16% |
| U201 LMG1020 x7 | $35.07 | 14% |
| U101 LM5017 x7 | $26.60 | 11% |
| **subtotal** | **$141.71** | **59%** |
| tank caps (56 pF x200 + 27 pF x100) | $43.00 | 18% |

Everything else on the board - every resistor, every bypass cap, both inductors, the bead,
the terminal block - totals **$57.36**, under a quarter of the order.

Comparison to the LCSC BOM is not apples-to-apples (LCSC prices are reel-rate and JLC would
have sourced them into an assembly), but for orientation the same parts at LCSC unit price
came to roughly $65-70 of material for 5 boards' worth. **Digi-Key is roughly 3-4x the
component cost.** That is the price of authorised-distributor stock, genuine TI silicon, and
an EPC2019 you can actually buy today.

---

# 4. OUT OF STOCK / LONG LEAD - READ THIS BEFORE YOU BUILD THE CART

## 4.1 !!! The 27 pF tank capacitor is OUT OF STOCK at Digi-Key !!!

**Yageo `CC1206JKNPOCBN270` - the exact MPN on `parts.json` - shows 0 in stock at Digi-Key,
backorder only, 16-week factory lead.** Digi-Key carries it (product 5884402, DKPN
`13-CC1206JKNPOCBN270CT-ND`) but does not stock it.

This is not a minor line. It is the **tank fine-trim value**: C319 completes the C_m match
bank, C320 is part of the P8 ZVS fix, and C204 sets C_shunt. Ordering the Yageo would have
put a 16-week hold on the build in exactly the way the EPC2019 did.

**Substituted: Murata `GRM31A5C3A270JW01D`, DKPN `490-11628-1-ND`, 16,178 in stock.**
27 pF, +/-5%, **1 kV, C0G/NP0, 1206** - same value, same tolerance, same voltage, same
dielectric, same package. This is a like-for-like part from a different vendor, not a
downgrade. Cost of the swap: +$8.50 on 100 pieces.

## 4.2 The 56 pF tank capacitor has THIN stock

**Yageo `CC1206JKNPOCBN560`, DKPN `311-3644-1-ND`: 1,557 in stock.** That covers the
200-piece order 7.8x, so it is fine today - but it is the lowest-stock line in the order by
three orders of magnitude, and it is the *same series* as the 27 pF part that already went
to zero. Factory lead is 16 weeks.

**Buy the tank capacitors in one go. Do not plan on a top-up order later.**

Verified drop-in backup if the Yageo goes to zero between now and checkout:
**Murata `GRM31A5C3A560JW01D`, DKPN `490-GRM31A5C3A560JW01DCT-ND`, 2,240 in stock,
$0.1603 @100** - 56 pF, +/-5%, 1 kV, C0G/NP0, 1206. Identical spec, +$8.40 on 200 pieces.

## 4.3 Long factory lead times on in-stock parts

Everything below **ships today**; the lead time only matters if you need a re-order.

| part | stock | factory lead |
|---|---|---|
| EPC2019 | 21,326 | 16 wk |
| Yageo tank caps (both values) | 1,557 | 16 wk |
| Murata 27 pF substitute | 16,178 | 23 wk |
| BLM21PG121SN1D bead | 81,851 | 27 wk |
| LM5017MRX/NOPB | 10,618 | 16 wk |
| ERJ-P06F1003V | 115,815 | 15 wk |
| LMG1020YFFR | 8,152 | 9 wk |
| CONSMA001-SMD-G-T | 8,698 | 4 wk |

**Nothing in this order is obsolete, NRND, or last-time-buy.** All 25 lines show Part
Status = Active.

---

# 5. QUANTITIES - THE REASONING

Build quantity is 5 boards. Quantities are **not** a flat 5x.

## 5.1 EPC2019: 12

10 for five boards plus **2 spares**, exactly as briefed. They are bare passivated die,
they are the most expensive part on the board, and they are the hardest thing on it to
place. Two spares cost $7.04 against the certainty that at least one placement goes wrong
on a hand-built first article.

## 5.2 The tank capacitors are the BENCH TRIM KNOB - ordered generously

This is the quantity decision that matters most, and it is driven by
`reports/sim-notes.md` s9, which leaves **two open items that both move the same knob**:

- **OPEN-13**: the zone-B tank bridge stray is an **estimate of 25-35 nH, not a
  measurement**, and the recommended C_s populate is a direct function of it.
- **OPEN-11**: `spiral-design.md` says the two etched spirals' realised inductance must be
  measured on the first article - methods A and B disagree by 14-17%, which is **+/-41 nH
  on L_s + L_m, larger than the bridge stray**.

sim-notes' own instruction is *"measure the spirals and the bridge in the same session,
then set C_s once."* The capacitor banks are the **only** knob that answers that
measurement. So the order must cover not just the shipped populate but a re-tune.

| | 56 pF (`311-3644-1-ND`) | 27 pF (`490-11628-1-ND`) |
|---|---|---|
| sites per board | 21 (15 populated + 6 DNP) | 6 (3 populated + 3 DNP) |
| **x 5 boards, every site** | **105** | **30** |
| trim / rework reserve | 95 | 70 |
| **ordered** | **200** | **100** |

Why the reserve is that size:

1. **Every site on all 5 boards, populated AND DNP** - 105 and 30. A retune can populate
   any DNP site, so all 21 and all 6 must be covered.
2. **Removing a fitted 1206 is destructive on this board.** The tank sites sit on heavy
   poured copper with a large thermal mass. Reworking a bank means lifting parts you will
   not re-use.
3. **The bank is re-solved at least once by design.** The trim sequence is measure ->
   re-run `cshunt_sweep.cir` -> re-stuff. A single full re-stuff of one board's C_s + C_m
   banks is 18 x 56 pF.
4. **Both land exactly on Digi-Key's 100-piece break**, which is the last break before a
   500-piece jump. 200 @ $0.1183 = $23.66; going to 500 costs $45.71 and buys nothing.
   100 @ $0.1934 = $19.34; 500 costs $77.25.

The reserve is therefore ~90% on the 56 pF and ~230% on the 27 pF. The 27 pF gets the
deeper reserve deliberately: it is the **fine** knob (both banks trim in 27 pF steps,
against 56 pF steps for the coarse part), so it is the value a retune consumes.

Total tank spend $43.00 - 18% of the order to keep the board tunable.

## 5.3 Everything else

- **Passives**: 5 boards' worth plus spares, rounded **up** to a real Digi-Key cut-tape
  break (1 / 10 / 25 / 50 / 100). Where a part costs under $0.10, the 50 or 100 break is
  taken outright - 50 x 0603 caps cost $1.81 and remove any chance of running out.
- **C202 at 100**: 0201s are 0.6 x 0.3 mm. They get lost. 100 of them cost $0.72.
- **R203-R206 at 25**: 20 fitted + 5. `parts.json` is emphatic that all four gate legs come
  from **one reel** for static sharing and differential-mode damping symmetry - do not
  split this line or top it up from a different order.
- **ICs and connectors at 5 + 2**: U101, U201 at 7. J201/J301 at 12 (10 + 2) and J101 at 6
  (5 + 1) - the SMAs are $3.15 each so the spare count is deliberate, not generous.
- **L201/L202 at 12**: two per board **in series**, 10 + 2.

---

# 6. DIRECT CROSSES - 11 lines, same MPN, no substitution

These are the parts where Digi-Key is an authorised distributor of the identical
manufacturer part number already on `parts.json`. Nothing changes electrically.

| refdes | MPN | DKPN | Mfr | Stock |
|---|---|---|---|---|
| C103,C104 | CC1206KKX7R0BB225 | 311-3450-1-ND | YAGEO | 31,920 |
| C105,C109,C111 | CC0603KRX7R0BB104 | 311-1523-1-ND | YAGEO | 1,976,606 |
| C106 | CC0805KKX7R9BB225 | 311-3420-1-ND | YAGEO | 192,164 |
| C107,C207-C210 | CC0603KRX7R0BB103 | 311-1788-1-ND | YAGEO | 102,796 |
| C110,C211,C212 | CC0603JRNPO0BN102 | 311-1746-1-ND | YAGEO | 26,880 |
| C201 | CC0402KRX7R7BB104 | 311-1338-1-ND | YAGEO | 4,607,818 |
| **C203,C205,C206,C301-C318** | **CC1206JKNPOCBN560** | **311-3644-1-ND** | YAGEO | **1,557** |
| C213 | CC0603KRX7R7BB105 | 311-1446-1-ND | YAGEO | 4,609,362 |
| FB201 | BLM21PG121SN1D | 490-5986-1-ND | Murata | 81,851 |
| J201,J301 | CONSMA001-SMD-G-T | 343-CONSMA001-SMD-G-TCT-ND | TE Connectivity Linx | 8,698 |
| R203-R206 | RK73H2ATTD4R70F | 2019-RK73H2ATTD4R70FCT-ND | KOA Speer | 19,446 |
| U101 | LM5017MRX/NOPB | 296-41308-1-ND | Texas Instruments | 10,618 |
| Q201,Q202 | EPC2019 | 917-1087-1-ND | EPC | 21,326 |

Two of these are worth calling out as **upgrades over the LCSC path**, not merely crosses:

- **U201 `LMG1020YFFR` (`296-50208-1-ND`, 8,152 in stock, $5.01).** Digi-Key's listing is
  **Texas Instruments**, confirmed on the product page. LCSC's C6423790 brands the identical
  MPN **"Tokmas"**, which `parts.json` carries as an explicit authenticity flag (OPEN-6) on
  the fastest-switching part on the board. **Buying from Digi-Key closes OPEN-6 outright.**
  You are paying $5.01 against LCSC's $0.72, but the LCSC alternate that *was* genuine TI
  (C506817) was $2.79 with 554 in stock, so the real delta for a genuine part is ~$2.20 each.
- **J201/J301 `CONSMA001-SMD-G-T`** is confirmed on the Digi-Key page as *"Surface Mount
  Solder"*, which is the spec P3 spent an entire re-source establishing (LEARNINGS
  2026-08-07: LCSC's package fields are useless for connector mount style). It is also
  **$3.15 vs LCSC's $2.97** - essentially the same price, from a distributor whose
  mounting-type field can be trusted.

**Do not substitute the KOA gate resistors.** 4R7 is settled twice over by simulation
(`sim-notes.md` s4) - do not fit 6R8, and do not split the four legs across reels.

---

# 7. SUBSTITUTIONS - 12 lines, every one justified

## 7.1 The tank capacitors - dielectric and voltage were held absolutely

**Both tank lines keep C0G/NP0 at 1 kV in 1206.** No X7R was considered anywhere in the
tank, at any point, for any reason. `parts.json` and the architecture are unambiguous:
X7R's voltage and temperature coefficients would detune the resonance and destroy ZVS, and
the 56 pF / 27 pF values are what set the resonant frequency.

- **56 pF: no substitution.** Yageo `CC1206JKNPOCBN560`, direct cross.
- **27 pF: Yageo -> Murata `GRM31A5C3A270JW01D`** because the Yageo is 0-stock (s4.1).
  27 pF, +/-5%, 1 kV, C0G/NP0, 1206 - **identical on every spec that matters.**

Per-part duty is unchanged from the P8 fix a3 analysis: each populated 56 pF C_s part
carries **0.93 A rms / ~150 mW**, and the C_s bank's temperature rise remains a **bring-up
measurement, not an assumption** (`sim-notes.md` s1). Murata's GRM31 series is at least as
capable as the Yageo here; if anything its RF characterisation is better documented.

## 7.2 L201/L202 - the drain choke. THE SRF RISK IS NOW CLOSED.

**This is the best outcome of the whole pass.**

`parts.json` carries the FXL0630-R47-M with an explicit unresolved risk:
*"SRF NOT DATASHEET-PUBLISHED for either candidate and STILL NOT CLOSED - a choke
resonating near 20 MHz stops being a choke."* The P4 review listed it under "what could not
be verified" and it survived to P9 unclosed.

**Substituted: Vishay Dale `IHLP2525CZERR47M01`, DKPN `541-1003-1-ND`, 2,526 in stock,
$0.932.**

| spec | required | FXL0630-R47-M (LCSC) | **IHLP2525CZERR47M01** |
|---|---|---|---|
| Inductance | >= 470 nH | 470 nH | **470 nH** (pair = 940 nH) |
| **SRF** | **>> 20 MHz** | **NOT PUBLISHED** | **75 MHz typ, PUBLISHED** |
| Isat | >= 12 A | 20 A (criterion unstated) | **26 A at -20% drop** |
| DCR | <= 12 mohm each | 4.1 mohm | **4.2 mohm max** |
| Size | 7.0 x 6.6 mm | 7.0 x 6.6 mm | **6.86 x 6.47 mm** |

**SRF 75 MHz typ is printed in Vishay's own IHLP-2525CZ-01 datasheet** (doc 34104, rev
24-Mar-2025, "SRF TYP (MHz)" column, 0.47 uH row). That is **3.75x above 20 MHz** and it is
a published number, not an inference. Isat is defined in Vishay footnote (2) as the current
causing an approximate **20%** inductance drop - the strict definition, so 26 A is a real
2.2x margin, not a -30% figure dressed up.

Footprint delta is **-0.14 mm x -0.13 mm** - the closest dimensional match found anywhere.
Check Vishay's pad drawing (3.18 x 3.429 mm pads on an 8.255 mm span) against the board's
`IND-SMD_L7.0-W6.6_FXL0630` land before reflow, but this is as near a drop-in as
substitution gets.

**Two honest caveats, neither of them new:**

1. **Tolerance is +/-20% ("M"), so a worst-case series pair is 752 nH against the stated
   820 nH floor.** This is equally true of the FXL0630-R47-M, which is also an "M" grade -
   the substitution does not make it worse, and it is worth knowing that the 820 nH floor
   was never guaranteed by the original part either. If it is a hard floor, it needs a
   tighter-tolerance part on both sourcing paths.
2. **The 75 MHz SRF is for a single unit.** Neither Vishay nor anyone else publishes an SRF
   for a series pair, and I did not estimate one. The architecture's bring-up requirement
   for an **empirical SRF sweep (dummy load + RF detector)** stands regardless of any
   datasheet claim - a published number reduces the risk, it does not retire the test.

Rejected alternate for the record: **Coilcraft XGL5030-651MEC** (650 nH, SRF 68 MHz
published, 4.0 mohm) clears Isat only at the -20% definition with almost no margin
(12.9 A vs 12 A required), is 5.48 x 5.28 mm - a real land mismatch - and is a Digi-Key
Marketplace item at $47.16 for 12 against $11.18. The Vishay wins on every axis.

Note also: **Digi-Key's product pages report Isat inconsistently between vendors** - the
-20% figure for Vishay and the -30% figure for Coilcraft. Do not compare two Digi-Key
inductor pages directly; read the datasheet footnote.

## 7.3 R201/R202 - the 50 ohm input termination, 750 mW held exactly

**Yageo `RC2010FK-07100RL`, DKPN `YAG3378CT-ND`, 30,014 in stock, $0.117.**
100 ohm, **+/-1%, 2010 (5025 metric), 0.75 W**.

No compromise was needed or taken: 0.75 W is the standard 2010 rating. The requirement
exists because P4 review E6 found the original 0805 sizing was off by exactly 2x - it had
been computed for a bipolar +/-2.5 V waveform when the design mandates unipolar 0/+5 V,
which puts 0.125 W in each part, i.e. 100% of an 0805's rating at 70 C and ~154% in the
100 C-class local environment. The 2010 at 750 mW (485 mW derated to 100 C) is **25.8%
used, 3.9x margin**. Package parasitics are irrelevant at 20 MHz (~1.5 nH per 2010,
j0.09 ohm against 50 ohm).

Second source if Yageo moves: Vishay CRCW2010 e3, same 0.75 W / 400 V.

## 7.4 R103/R104 - THE SUBTLEST SUBSTITUTION ON THE LIST, and it went UP a grade

**Panasonic `ERJ-P06F1003V`, DKPN `P16060CT-ND`, 115,815 in stock, $0.0748.**
100 kohm, +/-1%, **0805, 0.5 W**, AEC-Q200 pulse-withstanding.

The obvious answer here is Yageo `RC0805FR-07100KL` at $0.0256 - the ordinary 1/8 W 0805.
**It was rejected, and the reason is worth recording**, because it is the same class of
error that P4 review W2 caught in the first place.

`parts.json` moved R103/R104 from 0402 to 0805 specifically because **working voltage, not
power, is the limit**: R103 stands the whole bus (RON pin held near ground, other end at
+40 V) continuously, and an 0402's 50 V ceiling is exceeded outright by the ~51 V LC
turn-on overshoot P1 predicted. The note records the 0805 as "rated 150 V".

**But 150 V is the RC0805 *series* maximum working voltage, and it is not what a 100 k part
in that series actually gets.** Yageo's own datasheet defines the rated voltage as
`V = sqrt(P x R)`, **or the series maximum, whichever is less**. At 0.125 W and 100 kohm
that is `sqrt(0.125 x 100000)` = **111.8 V**. A 1/8 W 0805 at 100 k can never reach 150 V.
The same trap applies to Vishay CRCW0805100KFKEA and Stackpole RMCF0805FT100K.

111.8 V would still have been 2.2x the 51 V overshoot, so the ordinary part is not unsafe -
but it does not deliver the 150 V the design record claims, and the fix costs $1.23 across
the whole line. The Panasonic ERJ-P06 is 0.5 W with a 400 V limiting element voltage, so
`RCWV = min(sqrt(0.5 x 100000), 400)` = **223.6 V**: clears the stated 150 V with 1.5x
margin and the 51 V ring with 4.4x.

Caveat: Digi-Key does not expose a working-voltage attribute on chip-resistor pages, so the
400 V / 223.6 V figures come from the Panasonic ERJ P/PA/PM datasheet ratings table, not
from the Digi-Key listing. Do not confuse **ERJ-P06** with **ERJ-P6W**, a different 0805
anti-surge series that is stamped "not recommended for new design".

Verified Vishay alternate: `CRCW0805100KFKEAHP`, DKPN `541-100KTCT-ND`, 54,833 in stock,
0.5 W - lower confidence, its max working voltage was not read from the datasheet.

## 7.5 R101, R102 - the buck feedback divider

| ref | need | part | DKPN | stock |
|---|---|---|---|---|
| R101 | 30.9 k **1%** 0402 | Yageo `RC0402FR-0730K9L` | `YAG3110CT-ND` | 41,909 |
| R102 | 10.0 k **1%** 0402 | Yageo `RC0402FR-0710KL` | `311-10.0KLRCT-ND` | 8,462,854 |

The **1% tolerance is the load-bearing spec, not the brand** - `parts.json` says so
explicitly, and P4 review E3 exists because the previous R101 was a 5% part that dragged
the +5 V rail's low corner to 4.586 V, under the LMG1020's 4.75 V minimum VDD and past the
IN+ absolute maximum. Both replacements are genuine F-grade +/-1%, confirmed on the page.

Working voltage checked even though not flagged: Yageo RC0402 series is 50 V, and
`sqrt(P x R)` gives 44.1 V for the 30.9 k and 25.1 V for the 10 k. Fine on a buck FB node -
this is the same 50 V ceiling that drove R103/R104 to 0805.

R101 is the thinnest of the four resistor lines at 41,909 (30.9 k is not a high-runner
value; note its DKPN uses the low-volume `YAG####` prefix). Fine for 10 pieces.

## 7.6 C101/C102 - the bulk electrolytics. 63 V held; can size matches; ONE thing to check.

**Nichicon `UCD1J101MNL1GS`, DKPN `493-6185-1-ND`, 59,886 in stock, $0.547.**
100 uF +/-20%, **63 V**, SMD V-chip, 105 C, **2000 h**, 350 mohm ESR, 400 mA ripple.

| | required | Nichicon UCD1J101MNL1GS |
|---|---|---|
| Voltage | **>= 63 V** | **63 V** |
| Can diameter | 10.0 mm | **10.00 mm** |
| Seated height | ~10.2-10.5 mm | **10.50 mm max** |
| Endurance | 2000 h @ 105 C | **2000 h @ 105 C** |
| Mount | SMD V-chip, no bottom leads | **SMD V-chip** |

The **63 V rating is load-bearing** and was held: the bus sees a predicted ~51 V LC inrush
overshoot, which is 81% of 63 V - inside the usual 80%-ish electrolytic derating guideline,
1.24x margin. Adequate, not generous.

**A voltage upgrade is not available in this can size.** `parts.json` carries a
"RECOMMENDED FREE UPGRADE" alternate at LCSC (JVJ80V100M10x10, 80 V, same can, marginally
cheaper). **Digi-Key has no equivalent**: no 80 V or 100 V, 100 uF SMD V-chip in a 10 mm can
is stocked. The 100 V/100 uF Nichicon that surfaces (UPJ2A101MHD6) is a **through-hole
radial can**, which is a footprint change and puts leads through the bottom heatsink face -
disqualified on HS-2 grounds, not just convenience. **The free 80 V upgrade does not survive
the move to Digi-Key.** If the 51 V overshoot is a concern, tame the inrush rather than
chase the rating.

**RISK TO CHECK BEFORE REFLOW:** Digi-Key states a **10.30 x 10.30 mm land envelope** for
this part; the board's footprint (`CAP-SMD_BD10.0-L10.3-W10.3-LS11.0-FD_1`) is drawn for a
**~11.0 mm land span**. The terminals will land **inboard** of the pad outer edges by about
0.35 mm per side rather than centred. Almost certainly solderable by hand, but **verify
against Nichicon's recommended land drawing** - this is not a clean pass and it is not being
reported as one.

Also worth a sanity check, though the substitution does not make it worse: ripple rating is
400 mA @ 100 kHz per cap, 800 mA for the pair. The JIERR original was 200 mA @ 120 Hz, so
this is an improvement - but these caps are DC-bus hold-up only (far past self-resonance at
20 MHz; the C103/C104 and C207-C212 banks carry the HF ripple), so it was never the binding
spec.

**Polarity, carried forward unchanged:** pad 1 = anode; the board's footprint chamfers are
on the pad-1 side and the silk "+" added at P6 sits outside the body square. See workspace
LEARNINGS 2026-08-08 - on this family the **chamfer marks the ANODE**, which is the opposite
of the usual convention. A different manufacturer's can may mark it differently: **check the
Nichicon part's own polarity band against the board's "+" silk before fitting.**

## 7.7 C108 - 22 uF 16 V X7R 1206. The weakest line, and it is outside the preferred list.

**Taiyo Yuden `EMK316BB7226ML-T`, DKPN `587-4319-1-ND`, 206,899 in stock, $0.413.**

22 uF / 16 V / **X7R** / 1206 is at the physical edge of what the package can do, and
Digi-Key stock in that exact combination is thin. Stating the situation plainly:

- The preferred-brand match, **Murata `GRM31CZ71C226ME15L`**, is **0 in stock** at Digi-Key.
  Digi-Key's own page offers the Taiyo Yuden as its substitute.
- Nothing at 22 uF / 16 V / **X7R** / 1206 from TDK, Samsung, KEMET, Vishay or Wurth is in
  stock. Samsung and KEMET top out at 6.3-10 V in that capacitance/package combination, and
  their 16 V 22 uF 1206 parts are **X5R**, not X7R.
- **Taiyo Yuden is not on the preferred manufacturer list.** It is a tier-1 Japanese MLCC
  maker and I am comfortable recommending it, but flagging the deviation rather than
  quietly making it.

Two deltas from the original:

1. **Tolerance is +/-20%, not the +/-10% of the TCC part.** This is the buck output bulk on
   the +5 V rail - not a tolerance-critical role.
2. **Thickness is 1.80 mm max**, thick for a 1206. Check z-clearance and, if you are having
   a stencil cut, the paste volume for this aperture.

And a reminder that applies to the original part just as much: a **16 V X7R 22 uF 1206 on a
5 V rail loses a large fraction of its nameplate capacitance to DC bias** - realistically
11-15 uF effective. If the buck output bulk was sized tight, budget for that. This is not a
consequence of the substitution.

## 7.8 C202 - clean

**Murata `GRM033R71E103KE14D`, DKPN `490-14454-1-ND`, 750,722 in stock, $0.0072.**
10 nF, +/-10%, **25 V**, X7R, **0201** (0.60 x 0.30 mm).

Matches the original's 25 V rating exactly. **0201 is mandatory** - this cap straddles the
LMG1020's VDD ball on a 0.4 mm-pitch WCSP, and an 0402 does not fit the geometry. X7R is
correct here and is not a compromise: `parts.json` records that 10 nF at 0201 size is only
physically achievable in X7R (every 0201 C0G tops out around 50 pF), and TI's own reference
design specifies "X7R or better" for this exact bypass network. The architecture's rule is
"no X7R in the **tank**", which this is not.

## 7.9 L101 - the buck inductor. Drop-in form factor chosen over current headroom.

**Abracon `ASPI-4030S-220M-T`, DKPN `535-ASPI-4030S-220M-TCT-ND`, 15,050 in stock, $0.259.**
22 uH, shielded, **4.00 x 4.00 x 3.00 mm**, 1.0 A Irms / 1.3 A Isat, **225 mohm** DCR.

This is the **same 4030S form factor** as the Sunlord SWPA4030S220MT it replaces, so it is a
true drop-in on the board's existing `IND-SMD_L4.0-W4.0_SLW4010S` land pattern - zero
footprint risk. DCR improves 292 -> 225 mohm. Current rating is **identical** to the
original (1.0 A / 1.3 A), so it buys no headroom - but none was needed: `parts.json` states
22 uH "clears the >= 0.5 A budget comfortably (1 A rated)".

Rejected in favour of the drop-in: **Bourns `SRN5040TA-220M`** (`SRN5040TA-220MCT-ND`, 5,832
in stock, $0.36) has better numbers - 123 mohm DCR, 1.5 A Irms, 1.62 A Isat - but is
**4.95 x 4.95 x 4.10 mm**, i.e. ~+0.95 mm on each side and +1.1 mm taller than the drawn
land, and Bourns' own datasheet calls the series **"semi-shielded"** where Digi-Key's
attribute says "Shielded". On a Class E PA board that distinction is not cosmetic. Take the
Bourns only if you are willing to re-check the land pattern and the leakage flux.

**Digi-Key stocks no 4x4 composite-molded 22 uH from any preferred vendor** - this was
searched exhaustively (XAL4040, XEL6030, SRP5030TA-220M, SPM4030T-220M, IHLP2020BZER220M11
and others all return no Digi-Key results).

## 7.10 J101 - the DC input terminal block

**On Shore Technology `OSTTC022162`, DKPN `ED2609-ND`, 17,699 in stock, $0.57.**
2 positions, **5.08 mm pitch**, 15 A / 300 V, 14-22 AWG, through hole, side entry,
screw clamp with wire guard, M2.6 screw.

**Fit verified against the manufacturer drawing** (OSTTCXX2162, On Shore, read directly):

| | OSTTC022162 drawing | board footprint `CONN-TH_P5.08_KF128-5.08-2P_EDGETRIM` |
|---|---|---|
| Pitch | 5.08 mm | **5.08 mm** (pads at +/-2.54) |
| Pin | **phi 1.00 mm round** | drill **1.60 mm**, pad 2.40 mm |
| Recommended hole | phi 1.30 mm | 1.60 mm - **oversize, not undersize** |
| Body | 2 x 5.08 = 10.16 mm L, 7.5 mm D, 10.0 mm H | courtyard 10.16 x 10.70 mm |

The board's 1.60 mm drill is **0.30 mm larger** than the part's recommended 1.30 mm hole, so
the pin sits loose with 0.30 mm of radial slop. It **fits and solders** - annular ring is
still 0.40 mm - it is just a sloppier joint than a purpose-drawn land would give. For a
hand-soldered THT part carrying the DC bus, that is acceptable; fill the barrel properly.

**One genuine downgrade: current rating 24 A -> 15 A.** The KF128 claimed 24 A / 250 V; this
part is 15 A / 300 V. The requirement is >= 6 A, so 15 A is 2.5x margin and fine as
specified - but if anything downstream was reasoned against the 24 A number, **15 A is the
real ceiling now.** (Voltage improves, 250 -> 300 V.)

Termination style is **screw clamp with wire guard, not rising cage.** Verified rising-cage
alternative if that matters: **Phoenix Contact 1715721** (MKDS 1,5/2-5,08), DKPN
`277-1263-ND`, 2,790 in stock, $1.16 - same 5.08 mm / 2-pos / 15 A / 300 V, wider 14-30 AWG
range, roughly 2x the price. Its pin/hole geometry was **not** verified (Phoenix Contact's
site returns 403 and the Digi-Key-hosted PDF would not decode), so if you take it, pull the
drawing yourself first.

---

# 8. WHAT WAS HELD ABSOLUTELY - the forbidden-substitution checklist

| rule | status |
|---|---|
| Tank caps stay **C0G/NP0 at >= 1 kV, 1206** (56 pF and 27 pF) | **HELD.** 56 pF is the identical Yageo MPN; 27 pF moved Yageo -> Murata for stock, same 1 kV C0G 1206 +/-5%. No X7R anywhere in the tank. |
| **R201/R202 >= 750 mW** | **HELD exactly.** Yageo RC2010FK-07100RL, 2010, 0.75 W, 1%. |
| **R203-R206** keep 0805, 1%, >= 250 mW | **HELD - direct cross.** Same KOA RK73H2ATTD4R70F, 0805, 1%, 0.25 W. All four from one reel. |
| **L201/L202** >= 470 nH, >= 12 A Isat, low DCR, SRF >> 20 MHz | **HELD AND IMPROVED.** 470 nH, 26 A Isat @-20%, 4.2 mohm, **SRF 75 MHz published** - the risk that was open on this board is now closed. Series-pair SRF still unpublished; bring-up sweep still required. |
| **C101/C102 >= 63 V** | **HELD at exactly 63 V.** No higher rating exists in this can size at Digi-Key; the LCSC 80 V free upgrade does not survive the move. |
| **L101** 22 uH | **HELD**, same 4x4x3 form factor, better DCR. |

---

# 9. OPEN ITEMS

1. **C101/C102 land span.** Nichicon's stated 10.30 mm land envelope against the board's
   ~11.0 mm pad span. Terminals land inboard ~0.35 mm/side. Verify against Nichicon's
   recommended land drawing before reflow. Solderable by hand either way.
2. **C101/C102 polarity marking.** Pad 1 = anode is settled for the board; confirm the
   **Nichicon** can's own marking against the board's silk "+" before fitting. This family's
   chamfer convention is the reverse of the usual one.
3. **L201/L202 series-pair SRF is still unpublished** and the empirical bring-up sweep
   (dummy load + RF detector) is still required. The single-unit 75 MHz figure reduces the
   risk; it does not retire the test.
4. **L201/L202 +/-20% tolerance** means a worst-case series pair of 752 nH against the
   stated 820 nH floor. Equally true of the original part - **owner decision** whether
   820 nH is a hard floor, and if so this line needs a tighter grade on both sourcing paths.
5. **C108 vendor deviation** - Taiyo Yuden, outside the preferred list, because no preferred
   vendor stocks 22 uF/16 V/**X7R**/1206 at Digi-Key today. Owner may accept or may prefer
   an X5R from a preferred vendor - **do not make that swap without a ruling**, X5R is a
   temperature-range downgrade.
6. **J101 current ceiling 24 A -> 15 A.** Above the >= 6 A requirement; flagging in case
   anything was reasoned against 24 A.
7. **Assembly route is undecided.** This CSV assumes hand assembly or consigned parts to an
   assembler. The 0.4 mm WCSP and the two bare die need a stencil and reflow. **Owner
   decision** - and if it goes to an assembler, they will want a stencil ordered with the
   PCB.
8. **Stock re-check at checkout.** The 56 pF line (1,557) and the EPC2019 are the two to
   re-verify. Everything here was read live on 2026-08-09 and will drift.

---

# 10. WHAT DID NOT CHANGE

- **L301/L302 are not on this BOM.** They are etched PCB air-core spirals - copper features,
  not purchasable parts. Correctly absent, as in `fab/BOM.csv`.
- **The nine DNP sites are still DNP** (s2.2). This CSV is a *purchasing* document and
  deliberately orders parts for every site including the DNP ones; **`fab/CPL.csv` and
  `fab/README.md` s2 remain the authority on what gets fitted.**
- **The bench operating point is unchanged**: 25-30 V bus, 100-150 W, forced air.
  `theta_HS <= 0.7 C/W measured` is still a hard requirement, and 40 V is still not a
  drop-in bus with this populate (`fab/README.md` s9).
- **No board file, schematic, footprint, `parts.json` entry or existing fab output was
  modified by this pass.**
