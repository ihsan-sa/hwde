# afe-support - candidate research (vref, divider, buffer)

Block: the three accuracy-critical support parts around the converter - NOT the
converter itself (a sibling scout owns `research/adc.json`/`adc.md`). Source:
`parts_search.py` (live JLC/LCSC) for every stock/price figure, cross-checked
against manufacturer datasheets pulled through LCSC's PDF mirror (or, where
that mirror served only a placeholder, through a second-source clone
datasheet or a direct manufacturer/distributor fetch - each noted below).
Full JLC sweeps (30 queries, script-written): `research/raw/afe-support-sweep.json`.

**Cross-reference, not re-derived here.** `research/refdesign-afe.md` (topology
research) already concluded: a buffer is structurally required because Q9's
>=100 kOhm board-input-impedance floor forces the divider's Thevenin
resistance into the tens-of-kOhm range, two orders of magnitude above what a
SAR can settle against directly; a naive two-discrete-resistor divider risks
the WHOLE +/-12 mV over-temp budget on TCR **mismatch** alone (not
tolerance); and LT5400-class matched networks are the structural fix. This
file supplies the real, JLC-stock-verified numbers behind that estimate-level
conclusion, plus the reference and buffer legs it flagged as separate,
additive budget items. `research/adc.md` (converter scout) picked MCP3201
(VREF pin independent of VDD, accepts 0.25-VDD, draws 100/150 uA typ/max) as
top converter pick - every vref candidate below outputs 5-20 mA, far more
than that draw needs.

## Error budget frame (per candidate, not summed across sub-functions - that
sum is a sibling agent's job)

Target: **+/-5 mV of a 5 V terminal reading at 25 C (0.1%), +/-12 mV across
0-50 C, uncalibrated** (requirements.md Sec. 9, Q2 answer). Every number below
converts a datasheet spec into mV (or the ppm-of-5V-FS equivalent) so these
are directly comparable to that budget and to each other. "0-50 C total" =
initial accuracy + (max tempco x 25 C), arithmetic sum from a 25 C anchor -
conservative, matches how the requirement itself is stated (an uncalibrated
total, not an RSS combination).

## Sub-function 1: vref - precision voltage reference

| Rank | MPN | LCSC | Pkg | Vout | Stock | $@1 | Init acc | Tempco (max) | mV@25C | mV@0-50C | VIN min | Headroom@3.135V |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | ADR4525ARZ-R7 | C403698 | SOIC-8 | 2.5V | 5127 | $7.10 | 0.04% | 8ppm/C | 2.0mV | ~3.0mV | 2.8V | 335mV |
| 2 | MAX6070AAUT25+T | C143530 | SOT-23-6 | 2.5V | 670 | $2.97 | 0.04% | 6ppm/C* | 2.0mV | ~2.75mV* | 2.8V | 335mV |
| 3 | REF3320AIDCKR | C469907 | SC-70-3 | 2.048V | 3188 | $1.71 | 0.15% | 30ppm/C | 7.5mV | ~11.25mV | 2.248V | **887mV** |
| 4 | REF3325AIDCKR | C139629 | SC-70-3 | 2.5V | 5666 | $1.06 | 0.15% | 30ppm/C | 7.5mV | ~11.25mV | 2.7V | 435mV |
| 5 | MCP1501T-25E/CHY | C625319 | SOT-23-6 | 2.5V | 3098 | $1.69 | 0.1% | 50ppm/C | 5.0mV | ~11.25mV | 2.70V | 435mV |
| 6 | LM4040A25IDBZR (shunt) | C9421 | SOT-23 | 2.5V | 5351 | $1.97 | 0.1% | 100ppm/C | 5.0mV | **17.5mV** | n/a | n/a |

`*` MAX6070 numbers are LCSC-catalog-sourced only - not independently
page-verified this session (analog.com and mouser.com both timed out from
this environment; LCSC's own PDF mirror returns a placeholder "Datasheet
Notice" stub for every MAX6070 row tried, not the real Maxim/ADI datasheet).
Every other row's initial-accuracy/tempco/VIN-min number was read directly off
a manufacturer (or verified second-source clone) datasheet table - see Sources.

**Why this order.** Rank 1-2 (ADR4525, MAX6070) are the only candidates whose
own datasheet numbers land comfortably inside the 25 C AND 0-50 C budget with
real margin left for the divider/buffer/ADC to spend. Rank 3-5 (REF33xx,
MCP1501) are popular, well-stocked, cheap, low-dropout parts whose *tolerance
alone* meets or exceeds the entire 25 C figure before tempco is even added -
**not accuracy-budget-compliant on their own, uncalibrated, full stop** -
ranked here for completeness and for their genuinely better dropout margin
and stock depth, not because they hit the target. Rank 6 (LM4040) is the
required shunt-reference example; it is the worst performer on every axis
checked.

**Dropout is a live, evidence-based flag, not a guess.** ADR4525's actual
guaranteed minimum supply (VIN = Vout + 0.3 V, confirmed both from a Tokmas
second-source clone's measured DC table and independently from ADI's own
"low dropout... 300 mV" marketing claim, cross-checked via web search) leaves
only 335 mV of margin at the worst-case 3.135 V host rail floor - thin,
though still positive. The REF33xx family's 2.048 V option (REF3320) is the
standout on this axis: 887 mV of margin, more than double every 2.5 V-class
candidate, purely a consequence of needing less absolute headroom above a
lower output voltage. **This is a genuine, quantified reason to prefer the
2.048 V output class over 2.5 V if dropout margin matters more than the
accuracy shortfall** - though REF3320 does not close the accuracy gap either
way (see above). MCP1501 shows the identical pattern between its -20 (885 mV
margin) and -25 (435 mV margin) options.

**Shunt-reference (LM4040) consequence, as required.** A shunt reference
needs an external bias resistor from the 3.135-3.465 V rail; at a
representative ~1 mA bias point the resistor sees the rail's own +/-5%
excursion directly as a bias-current swing, which LM4040's own
dV<sub>Z</sub>/dI<sub>Z</sub> spec (2.5 typ / 6 max mV across a 1-15 mA
excursion, TI datasheet) turns into a small (sub-1 mV) extra error term on
top of the 17.5 mV tempco+tolerance figure above. The topology-level cost is
larger than that one number: a shunt reference has **no PSRR spec at all** -
line rejection is whatever the bias resistor and the diode's own 0.3-1.1 ohm
dynamic impedance passively divide down to, versus a series reference's
active 80-130 dB PSRR spec. Not recommended for this board.

## Sub-function 2: divider - the 0-5V to 3.3V-domain attenuator

Two approaches ranked together, ratio numbers only (absolute tolerance/TCR is
not the relevant spec here - see the requirement's own framing).

| Rank | Type | MPN | LCSC | Stock | $@1 | Ratio tol | Ratio TCR | mV@25C | mV@0-50C |
|---|---|---|---|---|---|---|---|---|---|
| 1 | (a) matched IC | LT5400B (-6#TRPBF) | C1739858 | 1278 | $13.87 | 0.025% | 0.2ppm/C typ | 1.25mV | ~1.3mV |
| 2 | (b) discrete pair | RNCF0603TKW1K00 x2 | C2601959 | 932* | $3.51 ea | ~0.014%** | ~2.83ppm/C** | 0.71mV | ~1.06mV |
| 3 | (a) matched IC | MPMT1003AT1 (1:1) | C2654068 | 594 | $3.22 | 0.05% | 2ppm/C typ | 2.5mV | ~2.75mV |
| 4 | (a) matched array | ACASA1001U1001P1AT | C1731577 | 715 | $2.93 | 0.05% | 5ppm/C | 2.5mV | ~3.1mV |
| 5 | (b) discrete pair | ERA-3VRW1001V x2 | C1863024 | 3265* | $0.67 ea | ~0.071%** | ~14.1ppm/C** | 3.54mV | ~5.3mV |
| 6 | (b) discrete pair | RT0603BRD0710KL x2 | C95204 | 1.27M* | $0.03 ea | ~0.141%** | ~35.4ppm/C** | 7.07mV | ~11.5mV |

`*` stock shown is for the one value queried; discrete pairs need two
(usually different) resistance values, each independently in stock - not a
concern at these depths except RNCF (60-1006 units per specific value/package,
adequate for qty 5 but worth re-checking against P2's actual chosen values).
`**` discrete-pair ratio numbers use the assignment's own convention for two
uncorrelated parts: ratio tolerance ~ sqrt(2) x each resistor's tolerance,
ratio TCR ~ sqrt(2) x each resistor's TCR - not a matched/tracked spec, an
estimate from independent absolute specs.

**Why this order.** LT5400 wins on raw tempco stability (0.2 ppm/C typical
ratio drift is 10x tighter than anything else found, confirmed against ADI's
own product page after LCSC's mirror served only a placeholder) but costs
4-40x more per package than every alternative. The Stackpole RNCF discrete
pair is the standout finding here: **an ordinary 2-piece 0.01%/2ppm chip
resistor pair gets to within ~20% of LT5400-B's total error budget at roughly
half the cost**, using a BOM line (two chip resistors) the board already has
elsewhere, instead of a specialty 8-pin part - genuinely worth the architect's
attention as the value pick. MPM and ACAS (both purpose-built Vishay
divider/array parts) sit in a clear middle tier: meaningfully better than
generic 0.05-0.1% discretes, meaningfully worse than LT5400 or a
tight-discrete pair, at a lower unit cost than LT5400. Rank 5-6 quantify why
a "reach for whatever's already in the BOM" discrete pair does not meet this
board's target: the cheapest, best-stocked resistor at JLC (YAGEO 0.1%/25ppm,
over a million units in stock, $0.03 each) alone consumes the entire 25 C
budget and nearly all of the 0-50 C budget as a divider, before the reference
or buffer contribute anything.

**Stock reality, stated plainly.** JLC/LCSC does NOT stock Vishay's tightest
MPM grades (Q/Z: 0.05% absolute / 0.01% ratio) - only the mid grade (B: 0.1%
absolute / 0.05% ratio) turned up in live search, and only two specific
ratios (1:1 at 50k/50k, and 9:1 at 1k/9k). ACAS mixed-value (non-1:1) rows
are stocked only at the loosest S-grade (25ppm absolute / 15ppm tracking);
the tighter U-grade (5ppm tracking) is stocked only as equal-value (1:1)
4-packs, which need the series/parallel-combination technique from Vishay's
own application note to synthesize a non-1:1 ratio from the matched elements.
LT5400 stock is genuinely present but thin at the A-grade (52-154 units per
SKU) - workable for a qty-5 build but not a part to over-commit to without
checking again close to order time.

**A free cross-sub-function finding.** A 2.5V-class vref (ADR4525, MAX6070-2.5,
REF3325, MCP1501-25) pairs with an exact, off-the-shelf 2:1 divide - MPMT1003AT1
IS that ratio (50k/50k, 1:1 internal tap = 2:1 total), and any equal-value
matched pair (ACAS 1:1, or two identical RNCF/YAGEO resistors) trivially gives
the same 2:1 split. A 2.048V-class vref needs a non-round ~2.442:1 ratio
instead - fully achievable with the same resistor product families, just
different absolute values, not a stock-blocking issue, but a small BOM/design
convenience the architect may want to weigh against the 2.048V option's
better dropout margin (Sub-function 1).

## Sub-function 3: buffer - the op-amp between divider and ADC

Requirement per `refdesign-afe.md`: CMOS input mandatory (a bipolar part's
tens-hundreds of nA bias current times the divider's tens-of-kOhm Thevenin
resistance would alone consume the entire 25 C budget). All six candidates
below are CMOS-input, single-supply RRIO parts - that filter is already
applied.

| Rank | MPN | LCSC | Stock | $@1 | Vos max@25C | dVos/dT max | GBW/SR | mV@25C | mV@0-50C |
|---|---|---|---|---|---|---|---|---|---|
| 1 | OPA333AIDBVR (chopper) | C30878 | 8448 | $1.42 | 10uV | 0.05uV/C | 350kHz/0.16V/us | 0.01mV | 0.013mV |
| 2 | OPA320AIDBVR | C92494 | 2191 | $1.50 | 150uV | 5uV/C | 20MHz/10V/us | 0.15mV | 0.28mV |
| 3 | AD8605ARTZ-REEL7 | C9641 | 13600 | $3.04 | not verified* | not verified* | - | - | - |
| 4 | TLV9001IDBVR | C398363 | 8305 | $0.11 | 1.6mV | 0.6uV/C (typ) | 1MHz/2V/us | 1.6mV | ~1.6mV |
| 5 | MCP6001T-I/OT | C116490 | 175426 | $0.26 | 4.5mV | 2.0uV/C (typ) | 1MHz/0.6V/us | 4.5mV | ~4.55mV |
| 6 | ADA4505-1ARJZ-R7 | C2058974 | 66 | $2.32 | not verified* | not verified* | - | - | - |

`*` ADI does not mirror these datasheets on LCSC (placeholder notice only for
both parts, every SKU tried), and both analog.com and mouser.com timed out
from this environment - genuinely not verifiable this session, ranked by
stock/power/reputation rather than a confirmed number. **Do not substitute
this for actually checking before layout.**

**Why this order.** OPA333 (zero-drift/chopper) and OPA320 (fast conventional
precision CMOS) both clear the ENTIRE budget by one to three orders of
magnitude - the buffer is a rounding error next to the reference and divider
terms above for either part. OPA320's real edge is settling time (0.32 us to
0.01% on a 2-V step, TI's own SAR-ADC-driver part) if the converter's
acquisition window ever gets tight; OPA333's edge is power (17-25 uA vs
OPA320's 1.45 mA) and being unconditionally negligible in the budget. TLV9001
and MCP6001 are included because they are the parts a bare-bones build
reaches for by default - their real, verified offset specs (1.6 mV and 4.5 mV
respectively, both AT 25 C ALONE) show concretely why neither is compatible
with the vref/divider picks that actually meet budget (which leave only
~1.3-3 mV of combined headroom): TLV9001 would consume the largest single
share of whatever margin is left, and MCP6001 alone consumes 90% of the
entire 5 mV 25 C figure.

**Input bias current is not a differentiator here.** Every candidate's
I<sub>B</sub> is sub-nA (CMOS input); even at a pessimistic 100 kOhm divider
Thevenin resistance, the worst case (MCP6001, ~1.1 nA at 125 C) is only
~0.11 mV - small next to its own 4.5 mV offset problem. Vos and its drift are
what actually separate these parts; bias current would only matter if a
bipolar-input part were considered, which none of these are.

**PSRR is not a differentiator either**, checked and stated so it is not
re-raised later: at the host rail's full +/-5% DC excursion (330 mV), every
candidate's max PSRR spec converts to single-digit-to-tens of uV of output
error (OPA333 ~1.7uV, OPA320 ~6.6uV, TLV9001 ~33uV) - one to two orders of
magnitude under each part's own Vos term.

**Is a buffer avoidable?** Not this scout's call (topology is
`refdesign-afe.md`'s job, which already concluded it is structurally required
by Q9), but the cost of adding one is small and now quantified: OPA333 adds
~$1.42 + 17-25 uA + one SOT-23-5 BOM line (genuine TI; a UMW-brand clone
row exists at ~$0.23-0.43 but was not independently checked); OPA320 adds
~$1.50 + 1.45 mA if settling speed is prioritized over quiescent current.
Both are trivial against the board's <15 mA worst-case current budget
(requirements.md Sec. 3).

**AD8605 clone-brand risk, verified directly - the single sharpest finding in
this file.** JLC's catalog lists six "AD8605"-branded rows from six different
manufacturers sharing the genuine part's pinout/footprint (TECH
PUBLIC/XBLW/JSMSEMI/HGSEMI/MSKSEMI/Tokmas), none of which is Analog Devices.
One clone datasheet was pulled directly (TECH PUBLIC's TPAD8605ARTZ, a real
PDF, not a placeholder): its guaranteed Vos is **5 mV MAX** - by itself larger
than this entire board's 25 C budget, and roughly 30-300x looser than genuine
AD8605's reputation for sub-100uV-class offset. A part-sourcer or layout
agent that substitutes any clone row for the genuine `AD8605ARTZ-REEL7`
(C9641, Analog Devices brand, the only AD8605 row independently checked as
electrically trustworthy) on stock/price grounds alone would silently blow
the accuracy budget. Treat every clone-brand row for every part in this
family class the same way going forward - verify the actual manufacturer, not
just the part number, before treating a JLC catalog match as equivalent.

## Cross-cutting risks and open questions for the architect

1. **Mode-boundary tension, not resolved here.** requirements.md Sec. 6 names
   only "the converter" and "a precision voltage reference" as pre-authorized
   for JLC Extended tier when Basic stock is thin. None of the divider or
   buffer candidates that actually meet the accuracy budget are Basic either
   (nothing tighter than ~1% tolerance passives is Basic at JLC) - the same
   Extended-allowance logic almost certainly needs to extend to the
   attenuator resistors and the buffer op-amp too, since Sec. 9's own analysis
   states the attenuator is a first-class error-budget term "alongside the
   reference," but the requirements text does not say so explicitly. Flag for
   H1/the owner, analogous to the second-rail tension already recorded in
   Sec. 1.
2. **Ratiometric-vs-independent assumption, stated so it can be checked.**
   All accuracy math above assumes the vref serves ONLY the converter's
   reference pin while the divider taps the raw 0-5V input independently (a
   non-ratiometric architecture) - the only reading consistent with the
   brief's description of an independent external 0-5V source. If a future
   architecture instead excited the divider FROM the same reference
   (ratiometric), the vref's own initial-accuracy/tempco terms would cancel
   out of the divider math entirely, changing this ranking's weighting
   significantly. Not assumed here; flagged as a live "what if" for whoever
   owns the final topology.
3. **No candidate in any sub-function is JLC Basic** - expected for
   precision parts at this accuracy class, stated per the mode's own
   cost-relaxation rule rather than left implicit.

## Sources

- REF3312/3318/3320/3325/3330/3333 datasheet (TI, SBOS392G) - vref dropout,
  tolerance, tempco, line/load regulation, long-term stability.
- ADR4525/4520/4530/4533/4540/4550 datasheet (ADI) - via a Tokmas second-source
  clone datasheet (ADI's own PDF not mirrored on LCSC; numbers cross-checked
  against ADI's "300 mV headroom" marketing claim independently).
- MCP1501 datasheet (Microchip, DS20005474G) - DC characteristics table.
- LM4040 datasheet (TI, SLOS456K) - shunt reference electrical characteristics,
  dV<sub>Z</sub>/dI<sub>Z</sub>, dynamic impedance.
- ACAS 0612 - Precision datasheet (Vishay Beyschlag, doc 28751) - absolute vs
  relative (ratio) tolerance/TCR grade table.
- MPM (Divider) datasheet (Vishay Dale Thin Film, doc 60001) - ratio
  tolerance/tracking spec table, standard divider ratios.
- LT5400 product page (analog.com/en/products/lt5400.html, via web search
  after LCSC's PDF mirror served a placeholder) - A/B grade ratio matching,
  0.2 ppm/C typical matching drift, <2 ppm/2000h long-term stability.
- OPA333/OPA2333 datasheet (TI, ZHCSGL8E) - offset, drift, PSRR, noise, CMRR.
- OPA320/OPA2320/OPA320S/OPA2320S datasheet (TI, SBOS513F) - offset, drift,
  bias current, settling time, output swing.
- TLV9001/TLV9002/TLV9004 datasheet (TI, SBOS833L) - offset, drift, PSRR,
  CMRR, settling time.
- MCP6001/1R/1U/2/4 datasheet (Microchip, DS20001733L) - offset, drift, PSRR,
  bias current, CMRR, output swing.
- TPAD8605ARTZ datasheet (TECH PUBLIC, sot23.com.tw) - clone-brand
  cross-check only, NOT used for the genuine AD8605 row's ranking.
- `research/refdesign-afe.md`, `research/adc.md` (this board, sibling P1
  scouts) - topology/converter context this file builds on, not re-derived.
- LCSC/JLCPCB live search: `parts_search.py` (this repo), 30 raw sweeps saved
  to `research/raw/afe-support-sweep.json`.
