# Research: the converter (bb-adc)

Block: single-channel ADC, 12-bit+, up to 10 kSa/s, SPI peripheral, 3.3V-ONLY
supply, 0.1% accuracy class (+/-5mV @25C, +/-12mV over 0-50C at the terminal,
uncalibrated). Source: JLCPCB/LCSC live search (`parts_search.py`), cross-checked
against manufacturer datasheets pulled through LCSC's PDF mirror. All prices are
the qty-5 build-quantity break (== the qty-1 unit price for every candidate below;
none of them have a price break at or under qty 5).

## Must-haves derived from requirements.md section 9

- Resolution >=12 bit, SPI, 3.3V CMOS peripheral, single-ended-to-ground.
- Must reach 10 kSa/s (not sustained) - disqualifies anything with a hard max
  sample rate below 10 kSa/s (e.g. delta-sigma parts like ADS1220/MCP3550, not
  shortlisted below for that reason).
- Reference architecture is the dominant ranking axis (owner's Q2 = 0.1% class):
  whether a candidate has a VREF pin independent of VDD, that can take an
  external precision reference below AVDD, decides whether the 0.1% target is
  even reachable without an unusual topology.
- Source impedance default (Q9): source <=1 kOhm, board presents >=100 kOhm.

## Ranked candidates

| Rank | MPN | Pkg | Stock | Price@5 | Basic | Ext VREF? | INL (LSB) | Fit |
|---|---|---|---|---|---|---|---|---|
| 1 | MCP3201-BI/SN | SOIC-8 | 1199 | $2.33 | Ext | **YES**, separate pin | 0.75typ/1max | True 1-ch, best grade+stock+price, no tradeoff |
| 2 | MCP3204-CI/SL | SOIC-14 | 693 | $2.47 | Ext | **YES**, separate pin | 1typ/2max | Same core, 4ch/use 1, hedge/2nd source |
| 3 | ADS7042IDCUR | VSSOP-8 | 2167 | $2.95 | Ext | **NO** pin exists | 0.7typ/1max | Best stock/speed/native-3.3V, ratiometric to AVDD |
| 4 | MCP3202-CI/SN | SOP-8 | 1347 | $2.06 | Ext | **NO** - shares VDD pin | 1typ/2max | Cheapest but reference-trap, see below |
| 5 | ADS8681IPWR | TSSOP-16 | 292 | $9.86 | Ext | Internal 4.096V + REFIO override | 0.5typ/1max(16b) | Exceeds-own-supply answer; needs 5V AVDD - disqualified here |
| 6 | AD7091RBCPZ-RL7 | LFCSP-10 | 36 | $12.61 | Ext | Unclear (catalog: internal-only) | 0.8typ (no max given) | Thin stock, pricey, weak fallback |

Top pick: **MCP3201-BI/SN** (C49274). Runner-up: **MCP3204-CI/SL** (C32816) as a
pin-different second source with identical analog front end, only needed if
MCP3201 stock ever tightens.

## Sub-question 1: does the candidate have a true external-reference pin?

This is the single most important split, and datasheet-checking it caught a
real trap (parts_search's `Voltage Reference` attribute is NOT reliable here -
same class of error as the buck-5v3a Fixed/Adjustable catalog defect in
LEARNINGS.md).

**Genuinely external, VREF independent of VDD (confirmed from datasheet pin
tables, not the catalog attribute):**
- **MCP3201** (DS21290F): 8-pin part, VREF = pin 1, VDD = pin 8, physically
  separate. VREF accepts 0.25V to VDD. Reference current drain: 100uA typ /
  150uA max - the downstream reference-regulator sizing needs to supply that.
- **MCP3204/3208** (DS21298E): VREF and VDD are separate pins in every package
  (MCP3204: VREF=pin13, VDD=pin14; MCP3208: VREF=pin15, VDD=pin16). Same VREF
  range and current drain as MCP3201.

**Trap - catalog says "External", datasheet pinout says otherwise:**
- **MCP3202** (DS21034F): the 8-pin package (SOP-8/MSOP-8/PDIP-8/TSSOP-8) has
  only **7 unique signals for 8 pins** because VDD and VREF are tied to the
  SAME physical pin, silkscreened "V<sub>DD</sub>/V<sub>REF</sub>" (pin 8) on
  the datasheet's own package drawing. There is no way to feed VREF a precision
  voltage independent of the chip's own 3.3V supply short of powering the
  entire part from a dedicated precision-regulated rail. parts_search's scraped
  "Voltage Reference: External" attribute is misleading for this part - do not
  trust it for MCP3202 specifically. This is why MCP3202 is NOT the top pick
  despite being the cheapest, best-stocked MCP32xx variant.

**No external reference pin exists at all:**
- **ADS7042** (SBAS608/ZHCSD00C): the electrical-characteristics table has no
  "Reference Input" section anywhere, full-scale span is defined directly as
  "0 to AVDD", and the datasheet's own typical-application schematic is
  labelled "AVDD used as Reference for device". AVDD IS the reference; there is
  no separate low-current REF pin to decouple from supply noise. Achieving
  0.1% would require AVDD itself to be a dedicated precision/low-noise rail
  (not the raw noisy host 3.3V) - and even then, the chip's own worst-case gain
  error alone (+/-0.1% FS max @ AVDD=3V, calibrated) consumes the *entire*
  0.1%/+/-5mV budget with no margin left for offset/INL/attenuator on top.
  Typical (not max) performance (+/-0.05% gain, +/-0.5 LSB offset calibrated)
  leaves real margin, but the part offers no architectural insurance against
  worst-case units. Two low-stock ADS7042 grades (IDCUT, 10pcs; IRUGR, 1pc)
  show "External" in the catalog reference attribute, but the tiny 1.5x1.5mm
  X2QFN-8 package has no pin budget for both AVDD and a separate REF pin -
  that catalog flag is very likely the same kind of scrape artifact as
  MCP3202's, not re-verified given the part is already deprioritized on this
  axis regardless.
- **AD7091R family**: catalog attribute is "Built-in" only (never "External")
  across every stocked SPI/I2C variant searched. ADI's AD7091R series is
  sometimes documented elsewhere as allowing an external reference to override
  the internal 2.5V on the same REF pin, but this was NOT confirmed against
  the actual datasheet (deprioritized before spending that budget - thin stock
  and ~5x MCP3201 price already rank it last). Flag for P3 if pursued.

**Has both, cleanly (per catalog, not independently re-verified since
disqualified on supply anyway):** AD7887 lists "External, Built-in" and
ADS8681/ADS8688/ADS8318 all have a genuine external-reference-input pin
(ADS8318's REFIN, ADS8681's REFIO) - see the supply-voltage note below for why
none of these are usable on this board as specified.

## Sub-question 2: sampling input model (for the buffer-amp decision)

Requirement default (Q9): source impedance <=1 kOhm, board presents >=100 kOhm.
Numbers below are as-published; the derived "how much margin" reasoning is
mine, flagged as such, for the downstream buffer-decision agent to use or
redo.

**MCP3201/3202/3204/3208 (identical SAR front end across the family, Fig 4-1
of DS21290F/DS21298E):**
- Switch resistance R<sub>SS</sub> = 1 kOhm typ (internal).
- Sample capacitor C<sub>SAMPLE</sub> = 20 pF typ.
- Acquisition window t<sub>SAMPLE</sub> = 1.5 SPI clock cycles - this SCALES
  with whatever SCLK the design chooses, it is not a fixed ns number.
- Max throughput 100 ksps @ VDD=5V / 50 ksps @ VDD=2.7V, i.e. 5-10x our
  required 10 kSa/s - that headroom can be spent as extra acquisition time by
  simply running SCLK slower than the part's rated max, which lengthens the
  1.5-cycle window in absolute time.
- The datasheet's own Fig 4-2 (max SCLK vs. R<sub>S</sub> for <0.1 LSB INL
  deviation) shows the max-SCLK curve is completely FLAT (no derating at all)
  out to R<sub>S</sub> ~1-2 kOhm at BOTH VDD=5V and VDD=2.7V - i.e. at the
  requirement's own default source impedance (<=1 kOhm), this family needs
  **zero clock derating even at its fastest rated throughput**, let alone at
  our slower 10 kSa/s target. The curve only starts rolling off above roughly
  2-3 kOhm, approaching (not reaching) zero somewhere past 8 kOhm on the
  charted range (10 kOhm axis max) - and our 5-10x throughput margin is
  available to push into that region if a higher-impedance source ever shows
  up. Reading: at Q9's default, no external buffer is indicated by this data;
  a downstream buffer call should hinge on some other reason (protection,
  isolation from a real high-Z source per Q9's "tell us if above 10 kOhm"
  clause), not on this family's settling behavior.
- Note 3 on the same datasheet page: SPI clock should stay above ~10 kHz
  (not sample rate - bit clock) or the sample cap droops between conversions
  at elevated temperature. Worth keeping in mind if a design is tempted to
  slow SCLK far down for power savings.

**ADS7042 (SBAS608):**
- Sampling capacitance C<sub>S</sub> = 15 pF typ.
- Acquisition time t<sub>ACQ</sub> = 200 ns MIN - a fixed absolute-time spec
  (not clock-cycle-relative like the MCP32xx family), at the part's full 1 MSPS
  rating.
- Because our required rate (10 kSa/s) is 100x below the part's 1 MSPS max,
  the 100 us available per conversion cycle leaves enormous room to extend the
  acquisition phase past the 200 ns minimum if the host chooses to - two
  orders of magnitude more settling time than the datasheet's own worst-case
  spec point.

**ADS8318 (SLAS568A) - for reference only, not usable on this board (see
below):** C<sub>IN</sub> = 59 pF, t<sub>ACQ</sub> = 600 ns min, leakage
1000 pA during acquisition.

**AD7887, AD7091R:** not pulled - both already ranked below the top four on
reference-architecture and/or stock+price grounds; datasheet-level sampling
detail wasn't worth the research budget for a part unlikely to be picked.

## The "exceeds its own 3.3V supply" flag (asked explicitly - answer: YES, one exists and is stocked)

**ADS8681IPWR** (C2670098, TSSOP-16, 292 in stock, $9.86 @ qty5) is a 16-bit,
1 MSPS SAR with an integrated precision attenuator/PGA front end. Per its
datasheet (ZHCSEV3E, shared with ADS8685/ADS8689): software-selectable
unipolar input ranges of 0-5.12V, 0-6.144V, 0-10.24V and 0-12.288V (plus
bipolar options), fed through a >=1 MOhm input impedance network ahead of the
SAR core, with an on-chip 4.096V low-drift reference (REFIO pin, which also
doubles as an external-reference input). The 0-5.12V range is a near-exact
match for this board's stated 0-5V input span - if this part could be used, it
would let the converter accept 0-5V directly with NO board-side attenuator and
NO separate precision-reference IC, eliminating the exact design tension
requirements.md section 1 flags as this board's hardest problem.

**Why it is not recommended here, loudly:** the datasheet's own block diagram
labels the analog supply "5V Analog supply", and the Power-Supply
Requirements table confirms AVDD = 4.75V-5.25V for this ordering code (DVDD,
the digital I/O supply, is independently flexible 1.65V-5.5V and could match
the host's 3.3V logic - only AVDD is the problem). This board's binding
constraint is "3.3V ONLY... no second rail" unless P1 shows the block cannot
work without one (requirements.md section 1). Using ADS8681 would mean adding
a small local rail (e.g. a boost regulator) purely to generate AVDD - a real,
stocked, in-family option that trades one small extra IC for eliminating the
attenuator/reference-error-budget problem entirely. That trade is an
architecture decision for P1/H1, not a research call; flagging per the brief's
instruction, not picking it.

ADS8688 (8-channel sibling, C527390, 2015 in stock, similar price) has the
same AVDD=5V constraint and is not separately ranked since ADS8681 already
covers the "exceeds own supply" case with a channel count that matches this
board's actual need.

## Risks

- **Single-source risk**: none of the top 4 candidates are pin-compatible with
  each other (different vendors/packages), so there's no drop-in second
  source for MCP3201 specifically - MCP3204 is the practical fallback (same
  vendor, same core, different pinout/footprint).
- **MCP320x drift is graph-only, not a tabulated max spec.** Both datasheets
  disclaim their Section 2 typical-performance graphs as "not tested or
  guaranteed... may be outside the specified operating range." The gain-error
  and offset-error-vs-temperature curves (Fig 2-19, 2-22 in DS21298E) suggest
  roughly <=1 LSB of drift band across -50C to +100C, comfortably inside the
  +/-12mV over-0-50C budget, but this is a read-the-graph estimate, not a spec
  P2 can hold the part to.
- **Every genuinely 16-bit-class accurate SAR found in JLC stock needs an
  analog supply >=4.5V** (ADS8318, ADS8681, ADS8688 all confirmed via
  datasheet) - nothing at that accuracy class runs natively off a bare 3.3V
  rail with a true external reference in current stock. If 12-bit + a good
  external 2.048V/2.5V reference (not this agent's block) can't close the
  0.1% budget, the realistic next options are ADS8681 (needs the second rail
  discussed above) rather than a different, undiscovered 3.3V-native 16-bit
  part.
- **parts_search's `Voltage Reference` attribute is not reliable for
  schematic-level decisions** - confirmed wrong for MCP3202 (says "External",
  pinout says shared-with-VDD) and unconfirmed/likely-wrong for two thin-stock
  ADS7042 grades. Treat it as a hint, not a fact, same caution LEARNINGS.md
  already records for JLC catalog attributes generally (Fixed/Adjustable
  buck-regulator case).

## Datasheets pulled and verified (PDF, not the HTML stub some LCSC mirror URLs serve)

- MCP3201 - DS21290F - `research/raw/adc-mcp3201-sweep.json` for stock rows.
- MCP3202 - DS21034F
- MCP3204/3208 - DS21298E
- ADS7042 - SBAS608 (ZHCSD00C, Chinese-language mirror; electrical tables
  read directly, no translation risk on the numeric content)
- ADS8318 - SLAS568A
- ADS8681/8685/8689 - ZHCSEV3E (Chinese-language mirror)

All six datasheet URLs above resolved to real PDFs (`%PDF` magic bytes) from
the `wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/...` host. Two URLs from the
initial parts_search results did NOT: `datasheet.lcsc.com/lcsc/...` served an
HTML page for the first ADS8318 row tried (fixed by swapping to the wmsc-host
form of the same stamp/part number), and AD7887's wmsc URL served a valid but
1-page "LCSC Datasheet Notice" stub (7.4 kB) instead of the real datasheet, on
BOTH grades tried - ADI's real AD7887 datasheet isn't mirrored on LCSC for
this part; not chased further given AD7887 was already a low-priority
candidate.

Raw sweeps for all 12 queries run (including AD7887, AD7920, ADS7883, ADS8688
- disqualified/lower candidates not in the top 6) are script-written under
`research/raw/adc-*-sweep.json`.
