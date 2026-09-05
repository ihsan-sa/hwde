# protection - g0-sense (P1 research)

Block: VBUS input protection for the USB-C-powered 5V device. Product-scope board,
so protection is required (requirements.md sec 3). Full live-search sweeps are in
`research/raw/protection-*.json` (script-written via `parts_search.py --out`); this
file is the ranked digest. All prices are the qty-5 break (this is a 5-board proto
run). None of the candidates below are JLC Basic parts except the reverse-protection
options - flagged per sub-function.

## 1. VBUS TVS / ESD clamp

Must-haves: unidirectional, standoff covering the real VBUS range with margin,
low capacitance NOT required (no USB data on this board), SMD, JLC-stocked.

| rank | MPN | LCSC | pkg | Basic | stock | $@5 | VRWM/VBR/Vc | notes |
|---|---|---|---|---|---|---|---|---|
| 1 | SMAJ5.0A | C113952 | SMA (DO-214AC) | No | 738,576 | 0.041 | 5V/6.4V/9.2V@43.5A | 400W, the de-facto standard part for 5V USB VBUS |
| 2 | SMF5.0A | C284108 | SOD-123 | No | 239,023 | 0.0192 | 5V/6.4V/9.2V@21.7A | same electricals, smallest/cheapest, 200W |
| 3 | SMBJ5.0A | C113974 | SMB (DO-214AA) | No | 167,477 | 0.0585 | 5V/6.4V/9.2V@65.3A | same electricals, 600W, bigger footprint |
| 4 | PESD5V0U1UA | C19829579 | SOD-323 | No | 19,085 | 0.0618 | 5V/7.5V/10V@4A(8/20us) | Nexperia ESD-array class; verify unidirectional in datasheet |
| 5 | SM05T1G-N | C2929246 | SOT-23 | No | 6,307 | 0.0616 | 5V/7V standoff | confirmed unidirectional in description; lower stock |

Recommendation: SMAJ5.0A (rank 1) as the default, SMF5.0A (rank 2) if board area is
tight - both are the same 5V/6.4V/9.2V family used across essentially every
commercial 5V-USB VBUS design (confirmed against Littelfuse/vendor app notes), just
in different packages/power ratings.

### Risk - the "clamp under 6V" ask is not physically achievable with a passive TVS

The assignment asks for standoff >= 5.5V while also clamping "well under" the 6V
downstream abs-max. No standoff-5V-class TVS does both: breakdown (VBR) floors
around 6.4V min for every unidirectional 5V part found (SMAJ/SMBJ/SMF/SM05T
family), and clamping voltage (Vc) at the rated surge current is 9.2-10V - well
above 6V. This is standard TVS physics, not a sourcing gap: Vc is measured at a
high pulse current (tens of amps, 8/20us or 10/1000us) and is inherently higher
than VBR by design; a device that clamped at <6V would need a breakdown far
below the 5V/5.25V real-world VBUS range and would nuisance-trigger continuously.
Web-search cross-check (Littelfuse/Digikey/Farnell app notes) confirms SMAJ5.0A
is the standard recommended part for exactly this "5V USB line" duty, with VRWM
chosen ~5-10% over nominal (5.25-5.5V) - i.e. the accepted real-world practice
already uses this exact "5.0V-class, 6.4V+ breakdown" family on 5V VBUS, and the
"6V clamp" framing does not match how TVS diodes are actually specified or used.
**Open question for the architect**: the 6V/9.2V gap is only crossed during the
transient surge event itself (microseconds); most silicon tolerates brief
transient overshoot above its steady-state abs-max (that's what ESD/surge specs
on the downstream parts are for), but this is NOT the same guarantee as staying
under abs-max continuously, and the brief did not hand me the downstream parts'
actual transient rating to check it against. If a hard <6V clamp ceiling is a
true requirement, no diode-based TVS in this catalog meets it; an active
clamp/OVP-eFuse would be a different tier of complexity and is out of this
scout's scope to spec.

### Risk - no JLC Basic TVS exists

Searched `TVS diode`, `TVS diode SOD-323`, `SOD-523 TVS`, `0402 TVS diode`, and
the SMAJ/SMBJ/SMF/PESD/SM05T families directly with `--basic-only`: zero Basic
results across the board (jlcparts has no Basic-tagged TVS at all in this
catalog snapshot). Every candidate above pays the JLC Extended per-unique-part
fee; at 5-unit qty that fee dominates the TVS's own unit price, so this is a
part-count consideration for the sourcer, not a reason to avoid TVS protection.

## 2. Resettable fuse (PTC) / current limit

Must-haves: hold current comfortably above ~350 mA worst case (on-board load +
100 mA Qwiic reserve per requirements.md sec 3), rated >= 6V (ideally 16V), low
initial resistance (Ri) so the LDO keeps dropout headroom.

Design-margin cross-check (web search, PTC application-note consensus): pick
Ihold >= 1.2-1.5x operating current (20-50% margin), and separately
Ihold(25C) >= Iop / 0.75 (~33% margin for ambient derating) - both point to
Ihold ~470-525 mA as the bare floor, with more margin preferred over exactly
meeting it.

| rank | MPN | LCSC | pkg | stock | $@5 | Ihold/Itrip | Vmax | Ri(init) |
|---|---|---|---|---|---|---|---|---|
| 1 | BSMD1206-075-16V | C883128 | 1206 | 28,114 | 0.0551 | 750mA/1.5A | 16V | 90mOhm |
| 2 | BSMD0805-075-16V | C976303 | 0805 | 58,154 | 0.059 | 750mA/1.5A | 16V | 70mOhm |
| 3 | nSMD100-16V | C70082 | 1206 | 75,637 | 0.0488 | 1A/1.8A | 16V | 55mOhm |
| 4 | JK-SMD0805-050-16V | C968441 | 0805 | 16,334 | 0.026 | 500mA/1A | 16V | 150mOhm |
| 5 | BSMD1206-050-16V | C883124 | 1206 | 49,550 | 0.0517 | 500mA/1A | 16V | 150mOhm |

All five are 16V-rated (2.9x the VBUS nominal), well past the ">=6V" floor, so
voltage margin is not the differentiator - hold current and Ri are.

Recommendation: BSMD1206-075-16V or BSMD0805-075-16V (rank 1/2, identical
electricals, pick by package/footprint preference) - 750 mA hold clears both
margin rules with room, and Ri of 70-90 mOhm at 350 mA worst case is only
25-32 mV of drop, negligible against the LDO's dropout budget. The 500 mA-hold
parts (rank 4/5) meet the literal "aim >= 0.5A" instruction but sit at only
1.43x the worst-case load - thinner than the margin rules recommend - and their
150 mOhm Ri costs ~53 mV at 350 mA, worth flagging if the LDO's dropout is
already tight. nSMD100-16V (rank 3) has the lowest Ri and highest stock/cheapest
price but its 1A hold means a partial fault in the 350mA-1A range will never
trip - a legitimate design choice (favors nuisance-trip avoidance over fault
sensitivity) but the architect should pick it knowingly, not by default.

**No JLC Basic PTC fuse exists either** (checked: `any(basic)` false across the
full 16V-family sweep and the general `PTC resettable fuse`/`0805 PTC fuse`
queries) - same Extended-fee note as the TVS.

### Alternative to a PTC (per assignment: report, don't pick)

A small P-channel MOSFET ideal-diode/eFuse (see sub-function 3 candidates,
AO3401A/SI2301CDS-T1-GE3) can also serve as the current-limit element if paired
with a current-sense/foldback circuit, but that is materially more design and
validation work (a true eFuse needs a sense resistor + comparator or a
purpose-built eFuse IC, not just the bare MOSFET) than a PTC for a board this
simple. A plain series Schottky (SS34/SS14/B5819W SL, sub-function 3) does NOT
current-limit at all - it only adds a fixed forward drop - so it is not a
substitute for the PTC's fault-clearing function, only for reverse-polarity
blocking. Recommend keeping the PTC as the current-limit element regardless of
what (if anything) gets added for reverse polarity.

## 3. Reverse-polarity / inrush

**Honest framing first**: a USB-C receptacle wired per requirements.md sec 2
(VBUS/GND on the fixed USB-C power pins, D+/D- unconnected) cannot have VBUS and
GND swapped by a compliant cable - the connector's own mechanical/electrical
contract keeps VBUS-to-VBUS and GND-to-GND regardless of plug orientation. The
only realistic ways to reverse-power this board are bench-supply miswiring or a
non-compliant/damaged cable during hand assembly and bring-up - low-probability,
caught quickly on a 5-unit prototype run, and not a field/end-use risk. Also
worth noting: the unidirectional TVS from sub-function 1 (cathode at VBUS, anode
at GND) already forward-conducts and crowbars a genuine reverse-polarity event,
working with the PTC to limit fault current, at zero extra parts. Given this,
**dedicated reverse-polarity protection is low-value on this specific board** -
it is cheap insurance for bring-up mistakes, not a load-bearing safety feature.

If the architect adds it anyway, candidates (JLC Basic where possible):

| rank | MPN | LCSC | pkg | Basic | stock | $@5 | type | notes |
|---|---|---|---|---|---|---|---|---|
| 1 | SS34 | C8678 | SMA | Yes | 4,895,137 | 0.0351 | Schottky, 3A/40V, Vf 550mV@3A | simplest: 1 part, no support components |
| 2 | SS14 | C2480 | SMA | Yes | 1,558,894 | 0.019 | Schottky, 1A/40V, Vf 550mV@1A | cheapest, same footprint as SS34 |
| 3 | B5819W SL | C8598 | SOD-123 | Yes | 602,062 | 0.0301 | Schottky, 1A/40V | smaller footprint option |
| 4 | AO3401A | C15127 | SOT-23 | Yes | 634,056 | 0.0968* | P-FET, 30V/4A, Rds 47-85mOhm | ideal-diode approach, see tradeoff below |
| 5 | SI2301CDS-T1-GE3 | C10487 | SOT-23 | Yes | 199,019 | 0.0946 | P-FET, 20V/2.2-3.1A | alt P-FET if AO3401A unfavorable |

\* this Basic-tagged AO3401A listing prices higher per unit than non-Basic dupes
of the same MPN (~$0.037-0.043 seen in the sweep) - the Extended-fee-vs-unit-price
tradeoff is a BOM-costing call, noted here for the part-sourcer/P3.

**Tradeoff (architect decides)**: a series Schottky (rank 1-3) is one part, no
gate drive, and costs a fixed ~0.35-0.55V forward drop at load current - at
~350 mA worst case that is roughly 125-190 mV, which most 3.3V LDOs (needing
~1-1.2V dropout headroom from a 5V rail) can absorb without issue, but it does
eat into the same headroom budget the PTC's Ri already uses. A P-channel
MOSFET ideal diode (rank 4-5) drops only ~15-50 mV at this load (Rds x I) but
needs a gate pull-down resistor (and ideally a gate-source clamp/Zener for
hot-plug transient survival) - 2-3 parts and a bit of design/verification
work versus 1 part and zero drop-budget risk. Given the low value of reverse
protection on this board (see framing above), the Schottky's simplicity is
likely the better trade if anything is added at all; the P-FET only earns its
keep if the architect independently needs the extra dropout headroom for
other reasons (e.g., a tight-Vin-max, low-dropout LDO choice).

**Inrush**: no motor, no bulk electrolytic/polymer capacitance is called for
anywhere in requirements.md (a small MCU + sensor + LEDs load), so LDO input
capacitance will be a few uF of ceramic at most - not enough stored energy to
need dedicated inrush limiting. USB-C sources also apply their own soft-start/
current-limit on connect. Recommend no dedicated inrush element; if one is
wanted anyway, the PTC's own resistance already provides mild soft-start at
zero extra part cost, which is preferable to adding a series resistor/NTC
purely for inrush on a load this small.

## Sourcing notes for P3

- LCSC datasheet URLs above use the `wmsc.lcsc.com/.../pdf/v2/lcsc/` form
  (fetchable); `www.lcsc.com/datasheet/...` URLs for the same parts serve an
  HTML shell, not a PDF - already rewritten here, but re-verify the `%PDF`
  magic bytes before trusting any pinout pulled from these.
- Several MPNs above are stocked by multiple LCSC codes (different
  manufacturers/date-stamp batches at the same price point) - the ones listed
  are the highest-stock instance at time of search; P3 should re-verify stock
  at order time regardless, per this catalog being a live-search snapshot.
- Two datasheet stamps (`2304140030` for JK-SMD0805-050-16V and B5819W SL) are
  shared across otherwise-unrelated parts - this is LCSC's own batch-upload
  date, not a duplicate/fabricated link; a known, harmless artifact per
  LEARNINGS.md.
