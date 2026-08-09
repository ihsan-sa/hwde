# powerpath research - buck-5v3a

Non-IC power path for a 5V/3A sync buck, 7-18V in, 50x40mm, JLC top-side SMT
+ THT terminals. Method: `parts_search.py` live JLCPCB catalogue for every
candidate below (source="live" on every query; no offline-cache fallback
was needed). Full sweeps saved script-written to `research/raw/`. Two
vendor datasheets were pulled and read directly (Read tool renders PDF
pages) to confirm physical dimensions the parametric search doesn't carry -
noted inline where used.

Binding constraints used throughout: requirements.md sec 10 (A2 3A max no
peak, A4 P-MOSFET reverse-polarity w/ zener-clamped gate, A5 4A one-shot
input fuse, A8 15mm max component height / M3 corner holes, A11 top-side
SMT + THT terminals via JLC-or-hand).

## 1. Power inductor

Two switching-frequency options per the assignment (~500kHz -> 4.7uH,
~1MHz -> 2.2/3.3uH). All candidates are magnetic-shielded SMD parts from
the CENKER/XR "60xx/80xx" families, which turn out to be the same physical
molds cross-branded - confirmed by pulling the CENKER datasheet (17-page
catalogue, `research/raw/final-lookup.txt` has the LCSC lookups; dimension
table read via the PDF tool): the size code IS the body outline, e.g.
**CKCS6045 = 6.0x6.0mm footprint, 4.7mm max height**; **CKCS8040 =
8.0x8.0mm, 4.2mm max height**. Both clear the <=5mm-ideal / 15mm-hard
height targets with room to spare, and the XR-branded rows (XRNR6045/
XRNR8040) match the CENKER electrical specs digit-for-digit, so I'm
extending the confirmed dimension to those SKUs on the strength of the
shared industry-standard size-code convention, not an independent pull.

| MPN | LCSC | Pkg (H) | Isat | DCR | Stock | $ea (qty1) | Basic | Fit |
|---|---|---|---|---|---|---|---|---|
| CKCS8040-4.7uH/M | C354638 | 8x8mm, 4.2mm | 5.9A | 19mOhm | 4892 | 0.105 | N | 4.7uH/500kHz top pick |
| XRNR8040-4.7uH/N | C5339770 | 8x8mm, ~4.2mm | 5.9A | 19mOhm | 1385 | 0.097 | N | 2nd source, cheaper |
| CKCS6045-2.2uH/M | C354629 | 6x6mm, 4.7mm | 6.75A | 14mOhm | 1474 | 0.057 | N | 2.2uH/1MHz top pick |
| XRNR6045-2.2uH/N | C5339744 | 6x6mm, ~4.7mm | 6.75A | 14mOhm | 1270 | 0.059 | N | 2nd source |
| XRNR6045-3.3uH/N | C5339750 | 6x6mm, ~4.7mm | 5.9A | 24mOhm | 1150 | 0.056 | N | 3.3uH/1MHz, DCR at the target |
| CKCS8040-3.3uH/M | C18199478 | 8x8mm, 4.2mm | 6.5A | 17mOhm | 995 | 0.096 | N | 3.3uH/1MHz alt, more margin, bigger |

All six clear Isat>=5A and DCR<=25mOhm with margin (only the 3.3uH/6045
pick sits exactly at the 24-25mOhm line). None are JLC Basic - Basic stock
essentially does not cover 3A-class shielded power inductors, consistent
with requirements.md sec 7's own note. Tolerance is +-20% (M) on the
CENKER-branded rows and +-30% on several XR-branded rows for the *same*
electrical spec - a buck's L tolerance mostly just shifts ripple/output
impedance a little, not a hard-fail item, but worth a note if the
regulator scout's loop-stability calc is tolerance-sensitive.

**Risk:** single design house behind both brand labels (CENKER/XR read as
the same OEM under two names) - if you want a genuinely independent
second source, none of these six qualify as one; the next-closest
independently-designed part in the sweep was Winsok/PNLS-family parts,
all of which missed Isat or DCR by a meaningful margin at these L values.

## 2. Reverse-polarity P-channel MOSFET

Gate sees the full clamp voltage at 12-18V in, but only ~-7V at the 7V
low-line corner (per the assignment); Rds(on)@4.5V is used as the
conservative stand-in for that corner. Target: <=100mW conduction loss at
the 2.4A low-line current => R <= 17.4mOhm at whichever Vgs the gate
actually sees there.

| MPN | LCSC | Pkg | Id | Rds@10V | Rds@4.5V | $ea | Stock | Fit |
|---|---|---|---|---|---|---|---|---|
| AOD403 (ElecSuper) | C5224305 | TO-252 | 62A | 8mOhm | 11.5mOhm | 0.155 | 26531 | Top pick - both Vgs points beat the 17.4mOhm loss target |
| AO4407A (UMW) | C2841482 | SOP-8 | 14A | 9.5mOhm | 14.7mOhm | 0.129 | 193924 | Compact co-pick, ~85mW @2.4A, smallest footprint |
| WSF90P03 (Winsok) | C148440 | TO-252 | 85A | - | 8mOhm | 0.396 | 5106 | Best-in-class @4.5V, no @10V figure on this row |
| AP6679GH-HF (APEC) | C124530 | TO-252 | 75A | - | 15mOhm | 0.527 | 1706 | 3rd DPAK source, priciest |
| SI4435DDY-T1-GE3 (Vishay) | C10491 | SO-8 | 11.4A | - | 35mOhm | 0.300 | 11781 | Known jelly-bean; ~201mW @2.4A, misses the loss target |

AOD403 and AO4407A both clear the loss target with margin even at the
conservative 4.5V-gate figure; either is oversized on Id/Vds (30V vs the
required -30V floor, no -40V part found meeting the Rds targets at this
price point) but that's a non-issue - a 62A/14A part run at 2.4-3A has
Rds(on) headroom to spare and no thermal concern. AOD403 is DPAK-sized
(bigger footprint, easier hand-touch-up); AO4407A is SOP-8 (denser, same
loss number). Architect's call on which footprint fits the layout better.
SI4435DDY is listed because it's an extremely common, easy-to-second-source
part - useful if the architect prioritizes supply-chain familiarity over
squeezing out the last ~100mV of loss margin.

**Risk:** none of the -40V-preferred parts in this shortlist meet -40V;
everything here is -30V rated, which meets the MUST-HAVE floor but not the
"preferred" stretch goal. -40V P-channel parts in DPAK/SO-8 with
comparably low Rds do exist on LCSC but were priced/stocked worse in this
sweep - available on request if 30V margin over an 18V max input (67%
headroom) is judged insufficient.

## 3. Input fuse

All 1206, all electrically rated 4A, all with a >=32V DC rating - the
"Type: Surface Mount Fuse" (one-shot) rows only; several PPTC/polyfuse
rows turned up in the same searches (BSMD1206L-400-12V, SMD1206-200-6V,
SL1206200-16V, etc: <=16V max, "Trip/Hold current" fields) and were
**excluded** - those are resettable and their voltage ratings (6-16V) are
far below the board's 32V floor anyway.

| MPN | LCSC | V (DC) | Melting I2t | $ea | Stock | Fit |
|---|---|---|---|---|---|---|
| JFC1206-1400FS (JDT) | C136349 | 63V | 1.73 A^2s | 0.064 | 48992 | Top pick - deepest stock |
| S1206-S-4.0A (SART) | C553931 | 32V | 2.54 A^2s | 0.087 | 40917 | At the 32V floor exactly |
| 1206T4A63V (Walter) | C354899 | 63V | 4.15 A^2s (slowest) | 0.056 | 16120 | Cheapest |
| 0466004.NRHF (Littelfuse) | C187596 | 32V | 1.76 A^2s | 0.090 | 7849 | Recognized fuse-house brand |
| BSMD1206C-1400T (BHFUSE) | C41367227 | 72V | not published | 0.064 | 47564 | Deep stock, no I2t data |

I2t spans roughly 1.7-4.1 A^2s across the shortlist - all "fast-ish" 1206
one-shot fuses in the same rough class; none advertise a distinct
slow-blow vs fast-blow line at this size, so there isn't a meaningful
fast/slow choice to make here beyond the small I2t spread shown.

## 4. Input TVS / clamp

Unidirectional, must not conduct at 18V (steady-state max), clamp aimed
below ~30V per the assignment. The "20A"-class parts (Vrwm=20V) are the
smallest step that clears the 20V standoff floor - the next size down
("18A" class, e.g. P6KE20A/SMAJ18A) came back at Vrwm=17.1-18.8V, under
the 20V floor, so those were dropped despite a lower (better) clamp
voltage. Going up a size to "22A" restores standoff margin but pushes
clamp to 35.5V, further from the ~30V aim - noted as a tradeoff, not
resolved here.

| MPN | LCSC | Pkg | Vrwm | Vc (clamp) | Ipp | $ea | Stock | Fit |
|---|---|---|---|---|---|---|---|---|
| SMBJ20A (MDD) | C364296 | SMB | 20V | 32.4V | 18.6A | 0.056 | 185374 | Top pick |
| SMBJ20A (Jingdao) | C353377 | SMB | 20V | 32.4V | 18.6A | 0.038 | 25592 | Same spec, cheapest |
| SMAJ20A (Jingdao) | C353466 | SMA | 20V | 32.4V | 12.3A | 0.038 | 21745 | Smaller footprint, lower Ipp |
| SMBJ22A (Jingdao) | C353375 | SMB | 22V | 35.5V | 16.9A | 0.040 | 14289 | More standoff margin, worse clamp |
| PTVS20VS1UR,115 (Nexperia) | C461164 | SOD-123W | 20V | 32.4V | - | 0.411 | 2379 | Branded/smallest pkg, priciest |

None of the found parts clamp fully "below ~30V" while also clearing the
20V standoff floor - 32.4V is the best available at Vrwm=20V. If a hard
<30V clamp ceiling is load-bearing (e.g. the regulator's absolute-max Vin
is close to 30V), flag it back to the architect; otherwise 32.4V vs an
18V steady-state max / presumably-modest cable-ringing transient is a
reasonable, very standard choice (SMBJ20A is one of the most common
TVS parts on LCSC by stock depth).

## 5. Screw terminals (2-pin, 5.08mm, THT)

Filtered to `Mounting Type: Through Hole`. Ratings on LCSC's own
parametric field are inconsistent with the vendor drawings - **read two
datasheets directly** (Ningbo Kangnex WJ500V and Cixi Kefa KF128) because
the current-rating attribute in the search index reports the IEC number,
not the more conservative UL number:

- WJ500V-5.08-2P: UL 10A/300V vs IEC 24A/400V (search index shows "18A").
- KF128-5.08-2P-AA: UL 10A/300V vs IEC 24A/250-630V (search index shows "24A").

Use the UL figures for the requirement check (>=10A, >=250V) - both parts
clear it exactly on the UL number, with the IEC number as extra headroom
that isn't the one to cite in a safety-relevant BOM note.

**Body footprint, read off the vendor drawings (mm):**

| MPN | LCSC | Depth | Height above PCB | $ea | Stock | Fit |
|---|---|---|---|---|---|---|
| WJ500V-5.08-2P (Kangnex) | C8465 | 10.00 | 14.07 | 0.133 | 298762 | Top pick - deepest stock |
| KF128-5.08-2P-AA (Kefa) | C474952 | 10.70 | 14.10 | 0.190 | 62104 | Confirmed via vendor drawing |
| KF2EDGVC-5.08-2P (Kefa) | C441386 | not confirmed | not confirmed | 0.059 | 33319 | Cheapest, closed-box style - dims not independently pulled |
| DB128L-5.08-2P-GN-S (DORABO) | C395868 | not confirmed | not confirmed | 0.198 | 27058 | M2 screw (smaller than M2.5) |

**RISK, flag to architect:** both dimension-confirmed parts stand
~14.1mm above the PCB. The binding mechanical answer (A8) caps component
height at 15mm - that leaves under 1mm of margin for the terminal block
alone, before any tolerance stack-up or the wire itself. Two of these
terminals are needed (J1 + J2) and both are large, board-edge parts on a
50x40mm outline; this is the tightest margin found anywhere in this
sweep and is worth a second look before board_init locks the outline.

## 6. Bulk / ceramic capacitors

**Input ceramic (>=25V, X7R/X5R, 1206/0805):**

| MPN | LCSC | Pkg | V/C/Dielectric | Basic | $ea | Stock |
|---|---|---|---|---|---|---|
| CL21A106KAYNNNE (Samsung) | C15850 | 0805 | 25V/10uF/X5R | **Y** | 0.105 | 10.4M |
| CGA1206X7R106K250NT (HRE) | C6119987 | 1206 | 25V/10uF/X7R | N | 0.261 | 61555 |

**Output ceramic (>=10V, X7R, 1206/0805):**

| MPN | LCSC | Pkg | V/C/Dielectric | $ea | Stock |
|---|---|---|---|---|---|
| TCC1206X7R226K160HT (CCTC) | C22392398 | 1206 | 16V/22uF/X7R | 0.241 | 66175 |

**Input bulk (>=25V, low-ESR/high-ripple, polymer or electrolytic):**
plain general-purpose SMD aluminum electrolytics turned up first (47uF/
25V, D5-6.3mm) but their ripple-current ratings are only 35-230mA@120Hz -
that's a mains-filter-class spec, not sized for a 500kHz-1.2MHz buck's
input ripple duty. Switched the search to the LCSC "Polymer Aluminum
Capacitors" category (note: the bare word "polymer" returns zero rows in
this search engine - same quirk family as the documented value-token
issue; it works once combined with a capacitance value, e.g. "47uF
polymer capacitor"):

| MPN | LCSC | Pkg | V/C | ESR | Ripple I | $ea | Stock |
|---|---|---|---|---|---|---|---|
| 350AVCA470M0606E38 | C494513 | SMD D6.3xL5.8mm | 35V/47uF | - | 2.1A@100kHz | 0.134 | 8419 |
| APXG250ARA470MF61G | C2161857 | SMD D6.3xL6.1mm | 25V/47uF | 30mOhm | 2.8A@100kHz | 0.283 | 7754 |

Both are SMD (no extra THT part needed beyond the two terminals already
on the board). DC-bias-derating caveat: the ceramic picks are nameplate
10uF/22uF but a 25V-rated 0805/1206 X5R or X7R part commonly loses
40-60% of that at a 12-18V (input side) or 5V (output side) DC bias -
size the input/output ripple and hold-up calcs off the *derated* value,
not the printed one. The 16V-rated output part and the X7R input
alternative both derate less severely than the 25V/X5R Basic pick, at
higher unit cost - a capacitance-vs-cost-vs-tier tradeoff for whoever
does the bulk-cap sizing math.

## Cross-cutting risks

1. **Terminal height margin** (sec 5) is the standout item - under 1mm of
   headroom against the binding 15mm cap once J1/J2 are placed.
2. **Inductor second-source** (sec 1) - CENKER/XR read as one OEM under
   two labels; no independently-designed part matched the Isat/DCR bar
   at these small L values in this sweep.
3. **TVS clamp vs standoff tradeoff** (sec 4) - no candidate clears the
   20V standoff floor AND clamps under 30V simultaneously; 32.4V is the
   practical floor for a standoff-compliant part.
4. **JLC-THT-assembly eligibility for the screw terminals** was not
   independently confirmed (parts_search has no explicit assembly-capability
   field beyond Mounting Type); not a blocker since A11 already accepts
   hand-soldering as the fallback either way.

## Method notes / gotchas hit this run

- `parts_search` returns **zero rows** for bare category words like
  "polymer" or "solid capacitor" - not a stock-out, a search-engine quirk
  (same family as the documented `10K`-token issue). Combine the word with
  a capacitance value (e.g. "47uF polymer capacitor") to get real rows.
- LCSC's own parametric `Current Rating` field on THT screw-terminal
  blocks reports the **IEC** number, not the more conservative **UL**
  number that most safety-margin call-outs (like this board's >=10A
  floor) actually want; the two differ by up to 2.4x on the same part
  (WJ500V: 10A UL vs 24A IEC). Pull the vendor drawing when the rating
  needs to be defensible.
- Two vendor PDFs here needed the Read tool's PDF-render path, not
  WebFetch - `WebFetch` reported "corrupted/unreadable binary" on both
  (one was a vector-drawing PDF, one a 17-page scanned catalogue);
  `Read` rendered both correctly as page images.
