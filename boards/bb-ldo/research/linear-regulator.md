# linear-regulator - candidate research (bb-ldo)

Block: single 5V->3.3V linear regulator, 500mA continuous, ~1W dissipation,
Ta=50C still air, 2-layer board, copper-only cooling. Full method/must-haves in
`requirements.md`. Source: `parts_search.py` (live JLCPCB, verified per
candidate) + manufacturer datasheets (cited per number). Full sweeps:
`research/raw/linear-regulator-sweep.json`, `research/raw/linear-regulator-to263-sweep.json`.

**Design point:** Pd = 0.975 W, Ta = 50 C -> Tj = 50 + 0.975 x theta_JA.
Threshold used below: Tj should stay clear of ~125 C with margin (datasheet
Tj(max) is 125-150 C depending on part; running at the max rating is not
"meeting" the requirement, it is zero-margin).

## Ranked candidates

### 1. AMS1117-3.3 - SOT-223 - Basic - top pick
LCSC C6186 | stock 1,364,865 | $0.2012 @qty5 (5000+: $0.1054) | [datasheet](https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/2410121508_Advanced-Monolithic-Systems-AMS1117-3-3_C6186.pdf)

- **Thermal:** Datasheet gives theta_JA as BOTH a single headline figure and a
  copper-area table (rare and useful) - Abs. Max. Ratings: SOT-223 theta_JA =
  90 C/W "with package soldered to copper area over backside ground plane...
  can vary from 46 C/W to >90 C/W depending on mounting technique and copper
  area." Table 1 (1/16" FR-4, 1oz Cu) gives concrete points: 100mm2 top /
  2500mm2 back / 2500mm2 board = 80 C/W; 1000mm2 top / 0 back / 1000mm2 board
  (single-layer, no ground-plane coupling) = 65 C/W; 1000mm2 top+back on
  1000mm2 board = 60 C/W; 225mm2 top / 2500mm2 back = 65 C/W; 1000-2500mm2 top
  / 2500mm2 back / 2500mm2 board = 55 C/W (best case shown).
  Tj(max) = 125 C steady state (thermal shutdown trips at 165 C).
  - At the headline 90 C/W (minimum-copper case): Tj = 50 + 0.975x90 =
    **137.8 C -> EXCEEDS 125 C. RISK if the placement doesn't earn enough
    copper.**
  - At a realistic 2-layer bench-board pour (~1000mm2 top, 1000mm2 board,
    60-65 C/W): Tj = **~113-114 C (11-12 C margin).**
  - At the datasheet's best case (2500mm2/2500mm2, ~50x50mm of copper, needs
    a backside ground plane too): Tj = **103.6 C (21.4 C margin).**
  - This is exactly the "copper area drives the outline" mechanism the board
    is built around (section 5): AMS1117 gives P6/P7 a real curve to place
    against instead of a single number.
- **Dropout:** 1.1V typ / 1.3V max @ 0.8A (Note 4: "for currents over 0.8A
  dropout will be higher"; datasheet does not give a 500mA point). Dropout
  scales down with current for a saturated pass transistor, so 500mA will be
  measurably below the 0.8A number, but this is not a guaranteed datasheet
  value - budget to the 0.8A max (1.3V) is still comfortably under the 1.45V
  ceiling but does NOT clear the <=1.0V preference at 800mA; likely does at
  500mA but unverified.
- **Accuracy:** Vout min/max at 25C = 3.251/3.349V (+/-1.5% initial). Over
  -40..125C (boldface): 3.201/3.399V (-3.0%/+3.0%). Adding load regulation
  (7 typ/25 max mV boldface) and line regulation (1.0 typ/10 max mV boldface)
  on top, worst-case arithmetic stacking can reach ~3.166-3.434V (**~-4.1%/
  +4.1%), i.e. it can exceed the board's +/-3% spec in the absolute worst
  case.** Typical performance will be well inside +/-3%; this is a
  worst-case-stack risk shared by every fixed 1%-class part in this table,
  flagged here because AMS1117's base tolerance is the loosest of the group.
- **Output cap / ceramic stability: DOES NOT meet the "ceramic-stable"
  want.** Datasheet: "addition of 22uF solid TANTALUM on the output will
  ensure stability for all operating conditions." This is a bipolar-NPN pass
  device compensated for a specific ESR window - pure low-ESR ceramic is a
  known real-world instability risk for this family. BOM impact: a tantalum
  (or equivalent min-ESR) output cap, not a plain MLCC.
- **Fit:** meets dropout/current/package; thermal is achievable but not
  free (needs real copper, which this design earns by construction);
  accuracy and ceramic-stability are the two open risks. JLC Basic, huge
  stock, cheapest by a wide margin, single de-facto industry standard part
  (also the only Basic option with adequate current/package - see risk below).

### 2. MCP1825S-3302E/DB - SOT-223 - Extended - best technical fit
LCSC C148031 | stock 566 | $1.3802 @qty5 | [datasheet](https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/2304140030_Microchip-Tech-MCP1825S-3302E-DB_C148031.pdf)

- **Thermal:** theta_JA (3-lead SOT-223) = 62 C/W typ, per EIA/JEDEC
  JESD51-751-7 4-layer standard test board (note: this is a JEDEC reference
  board with internal planes, not identical to our 2-layer bench board, but
  same order of magnitude and better than AMS1117's minimum-pad number).
  Tj(max) = 125 C steady state / 150 C transient (higher headroom than
  AMS1117's 125/165).
  - Tj = 50 + 0.975x62 = **110.5 C (14.5 C margin to 125, 39.5 C to 150).**
    Comfortable margin without needing a large copper investment.
- **Dropout:** 210mV typ / 350mV max @ 500mA (Vin=2.1V min) - this is the
  EXACT test point our load needs, not an extrapolation, and it clears the
  <=1.0V preference with ~3x margin.
- **Accuracy:** Fixed-output voltage regulation +/-0.5% typ / +/-2.5% max
  (boldface, full -40..125C Tj range, Note 2). Load regulation +/-1.0% max
  additional (1mA-500mA). Tightest realistic worst-case stack of the group
  after MIC29300; clears +/-3% with margin even stacked.
- **Ceramic stability: explicitly stable.** Feature line: "Stable with 1.0uF
  Ceramic Output Capacitor... Only 1uF of output capacitance is needed to
  stabilize the LDO." AC/DC table default test condition uses 4.7uF X7R
  ceramic for both Cin/Cout. No tantalum required - simplest BOM of the group.
- **Fit:** best combination of thermal margin, dropout, accuracy and ceramic
  compatibility in this search. Extended part - JLCPCB applies its standard
  per-unique-extended-part feeder/setup fee on top of unit price (amount not
  looked up here; verify at quote time), and stock (566) is thin next to
  AMS1117's 1.36M, though still >>5x build qty. Worth the fee if P3 weighs
  eliminating the ceramic-cap and accuracy risks above AMS1117's unit cost.

### 3. AP7361C-33E-13 - SOT-223 - Extended - best raw electricals, thermal gap
LCSC C500795 | stock 1444 | $0.466 @qty5 | [datasheet](https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/2304140030_Diodes-Incorporated-AP7361C-33E-13_C500795.pdf)
(Note: the JLC listing for plain **AP7361** (non-C), e.g. C260935 in TO-252,
is marked "NOT RECOMMENDED FOR NEW DESIGN - USE AP7361C" on its own
datasheet - excluded from this table; AP7361C is the current part.)

- **Thermal:** theta_JA (SOT-223) = 110 C/W, "device mounted on FR-4
  substrate PC board, with minimum recommended pad layout" - a single number,
  minimum-pad only, no copper-area scaling curve like AMS1117's Table 1.
  Tj(max) = 150 C (single rating, no separate steady/transient split stated).
  - Tj = 50 + 0.975x110 = **157.3 C -> EXCEEDS even the 150 C absolute max
    at the documented (minimum-pad) footprint. RISK: this part's own
    thermal number is worse than AMS1117's at a comparable minimum-copper
    reference, and there is no datasheet guidance on how much copper would
    fix it.** The TO-252 (DPAK) variant of this family has better tab
    thermal (theta_JA 95 C/W on a 2"x2" board per the AP7361/AP7361C
    datasheets) but that exact TO-252 LCSC part (C5564289) has **0 stock**
    today - not orderable.
- **Dropout:** 90mV typ @ 300mA / 340mV typ @ 1A for the 2.6-3.3V output
  bin (datasheet gives these two points, not 500mA directly). Linear
  interpolation estimate ~150-180mV typ @ 500mA - best dropout of the group,
  unverified at the exact point.
- **Accuracy:** +/-1% initial (Iout=100mA, 25C), output voltage temperature
  coefficient +/-100 ppm/C, load regulation +/-1.0-1.5% max. Tightest
  initial tolerance in this table.
- **Ceramic stability: explicit.** "Stable with MLCC, E-Cap, Tan-Cap or
  Solid Capacitor >= 2.2uF" - ceramic is fine, 2.2uF min at OUT, 1uF min at
  IN.
- **Other:** has an EN pin (active high, internal ~3M ohm pulldown - defaults
  OFF if floated). Must be tied to VIN for the board's always-on operation;
  this is a datasheet-required support connection, not an exposed config
  feature, so it stays in scope at block-only per section 2's own rule.
- **Fit:** best dropout/accuracy numbers on paper, but the thermal picture at
  its documented (and only in-stock) footprint fails the design point
  outright, with no data to say how much more copper would rescue it. Do not
  select without a P2/P3 empirical thermal check (or unless the TO-252
  variant comes back in stock).

### 4. MIC29300-3.3WU-TR - TO-263 (D2PAK) - Extended - electricals strong, thermal data gap
LCSC C481370 | stock 1467 | $2.7766 @qty5 | [datasheet](https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/2210181000_Microchip-Tech-MIC29300-3-3WU-TR_C481370.pdf)

- **Thermal:** the Temperature Specifications table gives theta_JC (junction-
  to-case) = 2 C/W for TO-263, and separately theta_JA = 56 C/W for the
  unrelated TO-252 package in the same family table - **no theta_JA is
  published for TO-263 at all** in the sections reviewed. This is the
  "no copper-referenced theta_JA" case the assignment calls out explicitly:
  TO-263/D2PAK parts are commonly characterized this way (the tab is meant
  to be soldered to a copper plane the designer sizes), but it means this
  candidate cannot be scored against the 0.975W/50C point without a P2
  empirical measurement or a vendor app-note curve not found here. Tj(max)
  = 125 C steady state (same family absolute-max convention as the others).
- **Dropout:** table gives 80mV typ/175mV max @ 100mA and 370mV typ/600mV
  max @ 3A (full load) for the MIC2930x (3A) family; no 500mA point. Rough
  interpolation ~125-135mV typ @ 500mA - very good if the interpolation
  holds.
- **Accuracy:** +/-1% max (10mA<=Iout<=Ifull, 25C), +/-2% max over -40..125C
  boldface - tightest full-range spec of the group on paper.
- **Ceramic stability: NOT CONFIRMED.** The typical-application circuit in
  the datasheet specifies a 10uF TANTALUM output capacitor; this is a PNP
  pass-device architecture (same general family concern as AMS1117). Ceramic-
  only compatibility was not found in the pages reviewed - treat as
  tantalum-oriented until checked further.
- **Fit:** electrically the strongest part in the table, and its D2PAK tab
  is the most thermally capable package class if given real copper - but
  between the missing theta_JA, the tantalum-oriented app circuit, the
  Extended/low-stock/highest-price profile ($2.78/pc, ~14x AMS1117), and
  zero margin advantage demonstrated over the SOT-223 options once real
  copper is on the board, it is not recommended for this small a load
  without a dedicated P2 thermal study.

### 5. HT7533-1 - SOT-89 - Basic - DISQUALIFIED (shown for contrast only)
LCSC C14289 | stock 185,364 | $0.112 @qty5 | [datasheet link 404'd this
session - see note below]

- **Disqualifying number: Output Current max = 100mA** (JLC listing
  attribute, corroborated by the part family's known rating), against a
  500mA CONTINUOUS requirement - **5x under**, package thermal is moot
  because the part cannot supply the load current at all, let alone the
  power. This is the SOT-89 "too small at ~1W" contrast the assignment
  asked for; no copper area rescues an output-current shortfall.
- Datasheet dropout/accuracy attributes as listed by JLC: 25mV@1mA dropout
  (a CMOS-LDO-class low-current part, not a 500mA/1W part), -40..85C Ta.
  The manufacturer PDF at the LCSC-hosted URL returned an empty/404 response
  during this research session, so theta_JA and Tj(max) could not be
  independently verified; not material to the ranking since the current
  rating alone disqualifies the part.

## Risks and open items (roll up)

1. **JLC Basic thermally-capable 3.3V fixed regulators = exactly one part
   (AMS1117-3.3, C6186).** Every other candidate that meets the 500mA/1W/
   SOT-223-or-larger bar is JLC Extended. This is a real single-source risk
   on the Basic tier: if AMS1117-3.3 stock or pricing changes, the next-best
   Basic-tier fallback is the disqualified HT7533 (SOT-89, 100mA) - i.e.
   there is no Basic-tier backup that actually meets the electrical spec.
   TO-252/TO-263 packages returned ZERO Basic parts in this search entirely.
2. **Accuracy worst-case stacking**: every fixed-output 3.3V part's headline
   tolerance (0.5-2%) can add with load/line regulation to approach or pass
   +/-3% in a strict worst-case arithmetic sum. Typical performance is well
   inside spec for all candidates; whether P2/P3 treats this as pass/fail
   on worst-case-arithmetic vs. typical/RSS stacking is a judgment call
   flagged here, not resolved here.
3. **Ceramic-vs-tantalum splits the field**: MCP1825 and AP7361C are
   explicitly ceramic-stable; AMS1117 explicitly requires a min-ESR
   (tantalum-class) output cap; MIC29300's app circuit implies the same.
   This is a real BOM/sourcing fork depending which part P3 picks.
4. **Thermal margin at the documented (in-stock) footprint, worst case to
   best case**: MCP1825 (62 C/W, JEDEC board) > AMS1117 at good copper
   (~55-65 C/W) > AMS1117 at minimum copper (90 C/W, fails) > AP7361C at
   minimum pad (110 C/W, fails outright) > MIC29300 (no number). Only
   AMS1117 gives a full copper-area-to-theta_JA curve to design the
   placement/outline against, which is exactly what section 5's canonical-
   outline binding needs at P6/P7 - this is a real point in AMS1117's favor
   beyond just Basic/price.
5. Two LCSC/manufacturer PDF fetches (HT7533-1 and, on the first attempt,
   several others) returned corrupted or empty responses via the automated
   fetch tool; all numbers reported above for AMS1117, MCP1825, AP7361/
   AP7361C and MIC29300 were confirmed by reading the actual datasheet
   pages (not inferred), cited by URL. HT7533-1's PDF genuinely 404'd this
   session and its full thermal data was not recovered - noted above,
   not material to its disqualification.
