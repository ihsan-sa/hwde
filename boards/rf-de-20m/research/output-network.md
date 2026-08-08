# output-network research - rf-de-20m

Block: output network passives for the Class E stage (C_shunt, L_s, C_s, L_m, C_m).
Frozen targets (from requirements.md, not re-derived): C_shunt ~200pF ext (317pF w/ Coss),
L_s 184nH, C_s ~447pF, L_m ~115nH, C_m ~500pF. Tank carries **6.6A rms at 20MHz**.

Source: `scripts/parts_search.py` live LCSC/JLC search (all candidates below verified in
stock today) + 3 real vendor datasheets pulled and read (Sunlord MWSA0503S catalog, Murata
LQW18AN reference spec, Vishay IHLP-2020CZ-01) to check what AC/Q data actually exists at
20MHz, not just assumed. Raw sweeps: `research/raw/ind-*-sweep.json`, `research/raw/cap-*.json`.

---

## Q1: Does an adequate single LCSC inductor exist for L_s (6.6A rms @ 20MHz, high Q)?

**No.** Two disjoint part families exist at LCSC, and neither one works alone:

**A. "Shielded/molded power inductors" (Sunlord MWSA, Changjiang FXL, Sumida, TMPC, SPM,
Vishay IHLP, Bourns SRP, ...).** These have plenty of current rating (12-25A at 184-220nH)
and low DCR (3.7-6.6mOhm), which looks great until you check what frequency they're
characterized at:

- Pulled the full Sunlord MWSA-S catalog PDF (12MB, all series): inductance is specified
  **only at 100kHz, 1V**. No Q, no AC resistance, no SRF anywhere in the document. Stated
  applications: "TV, graphics, memory; notebooks, tablets; communication equipment" - i.e.
  buck-converter-class parts.
- Pulled the Vishay IHLP-2020CZ-01 datasheet (a reputable vendor that DOES publish AC data).
  Its own **Features** line states **"Frequency range up to 5.0MHz."** That's a vendor
  admission this family is not characterized for 20MHz use - 4x past their stated range.
  It does include an inductance-and-Q-vs-frequency chart out to 1GHz per value. Reading it
  for the two smallest values (closest to our range): Q peaks around 45-70 somewhere in the
  1-5MHz band, then **falls** through the rest of the decade toward the SRF collapse. By
  20MHz none of the plotted curves are anywhere near their peak; a defensible order-of-
  magnitude read is **Q(20MHz) ~ 20-40** for this class, not the Q=150 the frozen sizing
  assumed.
- At Q=20-40: `P = 43.6 * 23.1/Q` = **25-50W in a single 184nH inductor** of this
  technology, vs. the 6.7W budget. That's 4-8x over a single part's share, and comparable to
  or larger than the board's ENTIRE 35-50W total dissipation budget. Not viable as a single
  part, full stop.

**B. Genuine high-Q RF chip inductors (Murata LQW series, wire-wound ceramic core).** Pulled
Murata's real reference spec (JELF243A-0024Y-01) for LQW18AN. This family DOES target the
right frequency range and DOES publish real Q:

| L | Q min | DCR max | SRF min | Rated current |
|---|---|---|---|---|
| 150nH | 32 | 1.5 Ohm | 1400MHz | 160mA |
| 180nH | 25 | 2.2 Ohm | 1300MHz | 140mA |
| 220nH | 25 | 2.5 Ohm | 1200MHz | 120mA |

Q is measured at 100MHz (not 20MHz) per the spec's test-frequency table, so even this is an
extrapolation, but it's a much smaller one than family A's. The real killer is **current**:
120-160mA rated vs. 6.6A needed is a **41-55x** shortfall, and DCR of 1.5-2.5 Ohm would put
`I^2*DCR` at tens of watts in one part even ignoring saturation. Not usable, not even close,
regardless of parallel count.

**Conclusion: no single LCSC part, and no LCSC part family, closes this.** One class has the
current but not the frequency; the other has the frequency but not the current. This is a
real, structural sourcing gap, not a search-effort problem.

---

## Q2: Fallback (a) N-parallel vs (b) PCB air-core spiral

### (a) N catalog inductors in parallel - flagged as UNVERIFIED, not recommended as-is

To keep 184nH total from N identical parallel units you need per-unit L = N x 184nH (e.g.
N=4 -> ~680-750nH units), because paralleling **identical** parts divides L and R by the
same factor N and leaves **Q unchanged** (Q_total = Q_unit, independent of N - verified
algebraically and against Vishay's own DCR-vs-L table). Paralleling therefore does NOT fix a
fundamentally core-loss-limited Q ceiling; it only spreads current/heat across more physical
parts. Worse: per the Vishay Q-vs-F chart, **peak-Q frequency drops as L increases** within
a family, so the larger per-unit part needed for N-parallel scaling sits proportionally
**further past its own Q peak at a fixed 20MHz** than a smaller unit would - paralleling can
buy less margin than the frozen doc's shorthand implies, or even make it worse. This is the
single biggest reason I'm not recommending this path without a bench check first.

If pursued anyway, best-in-class 680nH-ish building blocks found (N=4 -> ~170nH, 7.6% low,
trimmable via C_s/geometry):

- **Sunlord MWSA0503S-R68MT** - LCSC C408354, SMD 5.4x5.2mm, 680nH/9A/12mOhm typ DCR,
  stock 811, $0.1525@1pc.
- **Sunltech SLO0630HR68MTT** - LCSC C207835, SMD 7.1x6.6mm, 680nH/15A/5.5mOhm, stock 1759,
  $0.1168@1pc. Lower DCR, more thermal mass, better pick if this path is taken.

**Action needed before trusting this path**: buy 2-3 samples across families, measure real
S11/impedance at 20MHz under ~1.6A bias (6.6/N) on a VNA or impedance analyzer. No datasheet
answers this question - it has to be measured.

### (b) PCB air-core spiral - RECOMMENDED

Unlike catalog magnetics, this is first-principles-computable (modified Wheeler formula +
skin-depth sheet resistance), not vendor-guesswork:

- Geometry: 2 turns, OD 30mm / ID 20mm (davg 25mm, rho 0.2), 1.5mm trace / 1mm gap, 1oz Cu.
  Wheeler: **L = 189.7nH** (trim OD down ~1mm to land exactly on 184nH).
- Skin depth at 20MHz = 14.6um (matches the value already cited in requirements.md); sheet
  resistance = 1.15 mOhm/square. Trace length ~157mm -> **R_isolated = 121mOhm**,
  **Q_isolated ~ 198**.
- Derating for turn-to-turn proximity effect (turns are close, 1mm gap): 1.3-1.5x -> **Q ~
  130-150, P ~ 6.8-7.9W** - lands almost exactly on the frozen design's own Q=150/6.7W
  target. Even a pessimistic 2x derate (covering some ground-plane coupling loss too) gives
  **Q~99, P~10.5W** - over budget but not catastrophic, and tunable by widening the trace.
- **Caveat that must go to whoever does the layout (P4/P5)**: requirements.md mandates L2 be
  an "unbroken GND plane directly under the power loop." A solid plane directly under a
  spiral induces eddy/image currents that add loss beyond the isolated estimate above and
  aren't captured by the hand calc. Standard RF practice is a local L2 keepout under just the
  spiral footprint (plane resumes immediately around it) to protect Q. Flagging as an open
  item - this fallback's real achievable Q depends on a layout decision that hasn't been made
  yet, not just on the copper geometry.
- Board area: ~30x30mm = 900mm^2, ~11% of the 100x80mm soft outline budget - the outline was
  deliberately left soft in the P0 answers specifically to keep this option open.
- Zero BOM cost, no lead time, no authenticity risk, and - critically - trimmable at bring-up
  (add/remove a turn, widen the trace) if the bench Q comes in low, unlike a fixed catalog
  part.

**Recommendation: (b), primary.** It is the only path whose Q at 20MHz is actually
knowable before hardware exists, its computed numbers land close to the design's own budget,
and the owner already reserved the board area for exactly this reason. Treat (a) as a
documented Plan B only if a bench-measured catalog part beats the spiral's numbers.

---

## Q3: How many parallel C0G caps for C_s and C_shunt?

First finding worth surfacing: **>=250-500V C0G/NP0 in a plain search is almost entirely a
dead catalog at LCSC** - both a "500V C0G" and "250V NP0" text search return only THT
leaded parts (5mm/10mm pitch, all **0 stock**), unusable for JLC SMD assembly anyway.
Real SMD candidates only turned up once I searched by capacitance value directly and read
the voltage-rating attribute off the results - the high-voltage C0G stock is there, it's
just not surfaced by an explicit "500V" keyword search.

**C_s (target 447pF, sees ~152Vrms/~215Vpk -> want >=500V, ideally 1kV margin):**

Loss is dielectric-limited (tanD), not part-count-limited: for C0G, `ESR = tanD / (wC)`.
Using EIA C0G tanD <= 0.001-0.0015 (typical spec, measured at 1MHz - NP0/C0G loss is known to
stay flat well past 100MHz, a much safer extrapolation than the ferrite-core case above, but
still an assumption not a 20MHz-cited number): **total effective ESR ~ 17.8-26.7mOhm,
total P ~ 0.77-1.16W for the whole C_s bank, regardless of how many parts you split it
across** - splitting is a thermal/per-part-current move, not a total-loss move.

**Recommendation: 8x 56pF, 1kV, C0G, 1206** - `CC1206JKNPOCBN560`, **LCSC C113875**, YAGEO,
stock 8106, $0.0524@1pc (~$0.42/board). 8x56pF = **448pF** (0.2% off target). Per part:
0.825A rms, ~145mW - comfortable for a 1206 C0G. Single BOM line, 1kV rating gives 4.6x
margin over the ~215Vpk peak estimate.

**C_shunt (target ~200pF external, sits directly at the drain - same or worse voltage
stress, current waveform is a switched charge/discharge, not the tank's clean 6.6A rms, so
exact current needs P2 circuit simulation, not this sourcing pass):**

Same building block, same conservative assumption: **4x 56pF, 1kV, C0G, 1206** (same LCSC
C113875) = 224pF (12% over the 200pF nominal - acceptable, this value gets tuned against
Coss tolerance anyway). If P2's simulation shows lower current than the tank, fewer/larger
parts (e.g. 1x 220pF/500V, LCSC C576977) is also fine on the numbers, but I'd default to the
same 56pF/1kV building block for BOM commonality unless there's a reason not to.

Both nets: **avoid X7R anywhere** (per requirements) - all candidates below are pure C0G/NP0.

---

## Candidate tables

See `research/output-network.json` for the machine-readable version. Highlights:

| Need | Pick | LCSC | Pkg | V | Stock | $@1pc | Note |
|---|---|---|---|---|---|---|---|
| L_s (primary) | PCB air-core spiral, 2T, 25mm davg | N/A | copper | - | - | $0 | Q~130-150 computed; needs L2-keepout layout decision + bench confirm |
| L_s (Plan B, unverified) | Sunltech SLO0630HR68MTT x4 | C207835 | SMD 7.1x6.6 | - | 1759 | $0.1168 | 680nH/15A/5.5mOhm; 20MHz Q NOT vendor-published - bench first |
| L_s (Plan B, unverified) | Sunlord MWSA0503S-R68MT x4 | C408354 | SMD 5.4x5.2 | - | 811 | $0.1525 | 680nH/9A/12mOhm; same caveat |
| C_s | YAGEO CC1206JKNPOCBN560 x8 | C113875 | 1206 | 1kV | 8106 | $0.0524 | 8x56pF=448pF, C0G, 0.825A rms/part |
| C_s (alt, cheaper, less margin) | YAGEO CC0805JRNPOBBN221 x2 | C576977 | 0805 | 500V | 21591 | $0.0201 | 2x220pF=440pF, fewer/bigger parts, more per-part heat |
| C_shunt | YAGEO CC1206JKNPOCBN560 x4 | C113875 | 1206 | 1kV | 8106 | $0.0524 | 4x56pF=224pF, same BOM line as C_s |
| C_shunt (alt, huge V margin) | YAGEO CC1206JKNPODBN221 | C469629 | 1206 | 2kV | 105005 | $0.067 | 220pF single part, 2kV if ringing margin is a worry |

## Risks / open items for the architect

1. **The single biggest unresolved BOM risk on this board is L_s.** Neither catalog path is
   vendor-verified at 20MHz; the PCB spiral is computed, not measured. Recommend a bench
   prototype (either the spiral coupon or 2-3 sampled catalog inductors on a VNA) before this
   is allowed to leave "verify-later" status.
2. The spiral's real Q depends on an L2 ground-plane keepout decision that belongs to P4/P5
   layout, not this research pass - flagging the dependency so it isn't lost.
3. C_shunt's actual RMS current (needed to firm up its parallel count precisely) depends on
   the switched drain waveform, which is P2's job to simulate - the 4x56pF number above is a
   reasonable planning default, not a verified final value.
4. L_m (~115nH) and C_m (~500pF) were not sized here (out of the frozen scope given to this
   pass - only C_shunt/L_s/C_s were named as the risk items) but will hit the **same** two
   problems (L_m is even smaller than L_s, in the same dead zone; C_m at ~500pF and lower
   node impedance likely sees somewhat lower current than the series tank). Flagging so P2/P3
   don't get surprised - the L_m match inductor should probably also be a PCB spiral for
   consistency, and C_m can likely reuse the same 56pF-C0G-x-N building block.
