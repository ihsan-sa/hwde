# inamp - candidate ranking for the bb-amp amplifier block

Assignment: rank candidates across three families for a 165 V/V-class bridge
front end on a bare 3.3 V +-5% rail (3.13-3.47 V). Every number below is read
directly from a manufacturer datasheet (PDF pulled and parsed this session) or
computed from one; JLC stock/price/Basic verified live via `parts_search.py`
today. See `research/refdesign-bridge-front-end.md` (sibling P1 topology
research, already in this workspace) for the circuit-shape citations this
ranking builds on - not duplicated here.

## Winner: Family B, and it is not an add-on cost over Family A

**AD8226 at reduced front-end gain (~G=100) feeding an OPA2333 second stage
(~G=1.65)** - see s3. The reason this beats "just use one IC" (Family A) is
structural, not electrical: AD8226's REF pin is low-impedance-required (s2,
Fig.59), so even the best single-IC candidate needs a second active part
purely to drive REF safely. Family B spends that *same* second IC on gain
headroom AND the pedestal AND REF (grounded directly, no buffer needed) for
no extra part count. Family A alone is documented in full below because it is
the correct answer if the architect wants fewer conceptual stages, not because
it is cheaper.

---

## A. Integrated instrumentation amplifiers, single gain resistor

Two failure modes recur and split the field cleanly:
- **Supply-floor disqualification**: every in-amp with effortless bandwidth
  margin at G~150-165 needs >=4.5 V single supply - more than the 3.47 V rail
  ceiling. Not a design workaround, a hard electrical fact.
- **Bandwidth disqualification**: every in-amp that runs happily from 1.8-2.7 V
  falls well under the 7 kHz corner at G~150-165 - the "micropower/zero-drift
  trades away bandwidth" warning in requirements.md 9a, now with real numbers.

AD8226 is the only part found this session that clears both bars.

| MPN | -3dB BW @ G~150-165 | Offset drift (RTI) | DC CMRR @ G>=100 | Noise density / 0.1-10Hz | Swing @ light load | REF | Min Vs | Verdict |
|---|---|---|---|---|---|---|---|---|
| **AD8226** | ~12-13 kHz (tab. 20kHz@G100, 2kHz@G1000) | 0.5-2 uV/C max (B/A grade) | 120 dB min (G=100 AND G=1000) | 22-24 nV/rtHz; 0.4 uVpp | (V-)+0.1 / (V+)-0.1 V @ 100k, -40..125C | **LOW-Z required** (Fig.59) | 2.2 V | **WINNER** |
| AD8237 | ~6.1-6.7 kHz (tab. 100kHz@G10, 1kHz@G1000, BW pin -> +VS) | 0.3 uV/C typ | 120 dB min (grade-dep, up to 140) | 68 nV/rtHz; not pulled | ~0.02-0.07V @ 10-100k (per sibling doc) | **HIGH-Z** (ICF - divider OK) | 1.8 V | Runner-up, BW marginal |
| INA828 | 160-181 kHz (huge margin) | 0.5 uV/C max | 130 dB min | 7 nV/rtHz; 0.14 uVpp | (V-)+0.15/(V+)-0.15V @ 10k | LOW-Z required | **4.5 V** | DISQUALIFIED: supply |
| AD8422 | >>7kHz (120kHz@G100 tab.) | 0.3-0.4 uV/C | 126-150 dB (grade-dep) | 8 nV/rtHz; 0.15 uVpp | (V-)+0.2/(V+)-0.2V @ 10k | LOW-Z required (<1 ohm!) | **4.6 V** | DISQUALIFIED: supply |
| LT1167 | 73-80 kHz (huge margin) | 0.05-0.3 uV/C | 120-126 dB | 7.5 nV/rtHz; 0.28 uVpp | -Vs+1.1 / +Vs-1.2V @ 10k (**not RRIO**) | LOW-Z required | ~4.6 V (dual +-2.3V) | DISQUALIFIED: supply, not RRIO, stock=1 |
| INA333 | ~2.1-2.3 kHz | **0.1 uV/C typ** | 100-115 dB | 50 nV/rtHz; 1 uVpp | (V-)+0.05/(V+)-0.05V @ 10k | LOW-Z required | 1.8 V | DISQUALIFIED: BW |
| AD627 | ~1.9-2.1 kHz | 0.1 uV/C typ | 90-96 dB (@G=5 only, tab.) | 38 nV/rtHz; 0.56 uVpp | (V-)+0.007/(V+)-0.025V @ 100k (best-in-class) | not confirmed this session | 2.2 V | DISQUALIFIED: BW |
| AD8420 | ~1.5-2.5 kHz (2.5kHz@G100 tab, already short) | 1 uV/C max | 100 dB min | 55 nV/rtHz | RRIO, not pulled | MODERATE (gain-compensable, not free) | 2.7 V | DISQUALIFIED: BW - the "traded away for micropower" case the brief warned about |

Notes on the table:
- BW@G150-165 for every part except AD8237 (sibling-sourced) is my own
  log-log interpolation between the datasheet's tabulated G=100 and G=1000
  rows (AD8226, LT1167, INA333, AD8420 all show an almost exact constant-GBW
  slope across that decade; AD8422/INA828 slightly less than -1). **Verify
  against the actual bandwidth-vs-gain curve (not just the two table points)
  before this number is load-bearing for P2/P4** - flagged in OPEN.
- AD8226 offset drift figure is the datasheet's own worst case; input-stage
  term dominates (output-stage term/G at G=100-165 is <0.05 uV/C, negligible).
- REF-pin split is a real, verified architecture fact, not a guess: AD8226's
  own datasheet Figure 59 literally draws a bare resistor divider into REF
  and marks it "INCORRECT" (crossed out), with an op-amp buffer marked
  "CORRECT" [Reference Terminal s, AD8226 Rev.C p.20]. AD8237's datasheet says
  the opposite in as many words - "resistance at the reference pin has no
  effect on CMRR" [cited full-text in refdesign-bridge-front-end.md D5]. Every
  other classic-topology part checked this session (INA828, AD8422, LT1167,
  INA333) matches AD8226's low-Z requirement, each with its own explicit
  datasheet warning.
- AD8226 output swing (0.1 V headroom at 100k, -40..125C) is *tighter* than
  the 0.05/3.25V window requirements.md 9a Q6 asks for - trivially absorbed by
  letting P2 target 3.2V not 3.25V as the top of scale (gain is P2's to fix,
  not a value locked by this research), and the pedestal ~0.1V floor matches
  AD8226's guaranteed bottom exactly.
- Every part in this table shares the industry-standard 8-pin in-amp pinout
  (RG,-IN,+IN,-Vs / RG,REF,OUT,+Vs or a permutation of it) - single-source risk
  is low, pin-compatible fallback exists across brands for most of these.

---

## B. Two-stage split: lower-gain in-amp + precision op-amp

Front end: **AD8226 at G~100** (RG per the gain equation `G=1+49.4k/RG`), not
the full 150-165. This is a strict improvement over running AD8226 alone at
full gain: every number above is now the *directly tabulated* G=100 datasheet
row, not an interpolation - BW=20 kHz (0.13% droop at 1 kHz, 2.85x margin over
7 kHz), same 120 dB CMRR floor, same drift/noise.

Second stage: **OPA2333** (TI, zero-drift RRIO, C38732, stock 15520, $0.98@1)
at G~1.65 to close the gap to the board's overall ~150-165, injecting the
~0.1V pedestal as a summed offset at its own input and taking over the RRIO
output-swing job (0.05-3.25V is comfortably inside a CMOS RRIO op-amp's own
swing spec at light load, tighter than any in-amp's own output stage). This
also means **AD8226's REF can simply be tied to board ground** - the lowest
possible impedance - because the pedestal moves to stage 2's summing node
instead of AD8226's REF pin. No REF buffer needed at all; the "second IC" this
architecture needs is the same one, doing double duty.

Why the second stage's own precision does not matter: every in-amp datasheet
in this file defines input-referred offset as `Vosi + Voso/G` - the same
convention applies across a 2-stage chain [TI SBOA356, cited full-text in the
sibling refdesign doc D11]. OPA2333's own 10 uV Vos and 50 nV/C drift, divided
by the ~165 total system gain, contribute <0.06 uV and <0.0003 uV/C RTI -
negligible against the ~5 uV budget. What DOES matter for stage 2: RRIO swing
(met), enough BW at its own low gain (350kHz GBW / 1.65 = 212kHz, trivial
margin), and 3.3V compatibility (1.8-5.5V, met). A cheaper non-zero-drift RRIO
CMOS op-amp (MCP6002/TLV9002-class) would work by this same math - OPA2333 is
chosen for stock depth and price, not because zero-drift is required here.

SBOA356's own worked example (Table 7-1, cited in the sibling doc) quantifies
the general principle this design follows: putting most of the gain in the
FIRST (precision) stage and only a little in the second beats the reverse
split by ~5x in total input-referred offset, for the same total gain. AD8226
@ G=100 / OPA2333 @ G=1.65 (100:1.65, gain overwhelmingly front-loaded)
matches that shape.

**Rank 1 overall.**

---

## C. Fully discrete: 2/3-op-amp in-amp with matched resistors

Op-amp candidates (3.3V-compatible, RRIO, zero-drift): **OPA2333** again (x2
dual packages: one for the matched input pair, one for the output diff-amp +
spare channel) - same part as Family B's stage 2, one fewer distinct MPN to
stock. GBW=350kHz means front-end gain must stay modest (~G=15-20 per side,
same gain-splitting logic as Family B) or bandwidth is lost the same way the
zero-drift monolithic parts lose it in section A.

**CMRR is what actually kills this family, and it is quantifiable exactly**
[TI SBOA582, *Optimizing CMRR in Differential Amplifier Circuits With
Precision Matched Resistor Divider Pairs*, Nov 2023, Eq.7 - full text read
this session]:

    CMRR_R (V/V) = (G_diffstage + 1) / (4 * t)      t = resistor tolerance, Ohm/Ohm

For a properly-built 3-op-amp topology the OUTPUT diff-amp stage runs near
unity gain (G_diffstage=1) regardless of the system's overall 150-165x, since
the front pair does the gain differentially and only the output stage's own
4 resistors are exposed to this formula. That gives:

| Resistor tolerance | CMRR_R (this stage alone) | Sourceable at JLC, qty 5? |
|---|---|---|
| 1% | 2/(4*0.01) = 50 -> **34 dB** | yes, trivially |
| 0.1% | 2/(4*0.001) = 500 -> **54 dB** | yes |
| 0.01% (100 ppm) | 2/(4*0.0001) = 5000 -> **74 dB** | hard - hand-selected pairs, not a catalog part |
| RES11A10DDFR (TI precision matched divider pair, 1:1, verified at JLC: C52119176, stock 58, $3.14@1) | per SBOA582 Fig.3-2, roughly mid-50s dB at G=1 for this device class | yes, real part, but matched-ratio-tolerance spec not pulled this session |

**What CMRR this board actually needs**, computed from this board's own
numbers (Vcm=1.65V mid-rail, ~5uV RTI total error budget, requirements.md
9a): input-referred CMRR error = Vcm / CMRR(linear). Solving for the
CMRR that keeps just this ONE error term under ~2uV of the 5uV budget:
CMRR(linear) >= 1.65/2e-6 = 825,000 -> **CMRR >= ~118 dB**. The best
realistic discrete number above (74 dB, 0.01% resistors, hard to source) is
**44 dB (a factor of ~160x) short**; even a lab-grade 0.001% (10 ppm, not a
JLC catalog part at any quantity) only reaches 94dB, still 24dB short. This
has nothing to do with op-amp choice - it is a property of the resistor
network alone, and no op-amp fixes it. Cross-check: this is exactly why every
monolithic in-amp in section A specs 100-150dB CMRR - on-chip laser-trimmed
thin-film resistors reach tolerances (<0.01%, matched not absolute) that a
5-piece JLC/LCSC BOM of discrete parts cannot economically reach.

**Rank 3 (last) of the three families - CMRR shortfall is categorical, not a
tuning problem.** Family C is documented here because the assignment asked
for it and the quantification is the useful deliverable, not because it is a
buildable path to this board's spec without a specialty part TI does not sell
at the needed matched-ratio-tolerance for this project's qty.

---

## Pedestal source (the ~0.1V output zero)

Recommended: **no separate part.** Family B (and Family C) already need a
second op-amp stage for gain-splitting; that stage's own summing junction is
where the pedestal belongs (op-amp virtual-ground summing has no CMRR penalty,
unlike loading an in-amp's REF pin with a bare divider - s2). A resistor
divider off the same 3.3V rail already powering the amplifier, summed into
that stage, is sufficient: the pedestal's absolute value is explicitly NOT
calibrated-critical (requirements.md 9a "initial offset does NOT matter"),
and its DRIFT contribution (rail-derived divider TC, or the op-amp's own
offset drift) lands post-gain and is divided by the total system gain when
referred to input - same negligible-contribution math as stage 2's own Vos
above.

If a separate reference IC is wanted anyway (e.g. to decouple the pedestal
from rail noise/accuracy entirely): any low-voltage shunt/series reference
divided down works, since only ~0.1V is needed from any of them - not
separately scouted as its own ranked family because the resistor-divider
option above is simpler, cheaper, and already sufficient by the math shown.

---

## Risks

- **BW-at-gain numbers are interpolated, not all directly tabulated** (see
  table note) - the single exception is AD8226 run at G=100 in the Family B
  design, which uses the directly-tabulated row and is the most trustworthy
  number in this file.
- **AD8237's BW margin, if that path is chosen instead of Family B, is
  negative at G=165**: interpolated droop at 1kHz is ~1.1-1.4%, over the
  ~1% target, and depends on the BW pin being correctly strapped to +VS
  (wrong strap = 5x worse per the sibling doc's citation) - an assembly-time
  risk, not just a part-selection one.
- **LT1167 is effectively unbuyable at this qty** (JLC stock = 1 unit,
  C579674) on top of its supply-floor and non-RRIO disqualifications - listed
  for completeness only, not a real option.
- Every part in this file is **JLC Extended**, none Basic - instrumentation
  amplifiers and zero-drift precision op-amps are not a JLC Basic category;
  flagged, not a rankable differentiator here.
- AD8226/AD8237/AD8422/INA828/LT1167 are all placed by JLC SMT (SOIC-8 or
  MSOP-8) - no DFM flag.

## Files
research/inamp.md (this file), research/inamp.json (slim candidates),
research/raw/inamp-sweep.json (full `parts_search` sweep, script-written).
