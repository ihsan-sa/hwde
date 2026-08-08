# P4 adversarial schematic review - rf-de-20m

20 MHz Class E GaN power stage, 200 W into 50 ohm, 40 V bus.
Reviewed 2026-08-08 against `reports/schematic.pdf` (4 sheets, rendered here),
`reports/top.net` (69 components / 19 nets), the `parts/*.json` datasheet
extractions (LMG1020 C6423790, EPC2019 C2836675, LM5017 C34355), the LM5017 PDF
itself, `architecture/{blocks,decisions}.md`, `parts/parts.json` and the
`power` + `connector` checklists (the only two whose domains appear here).

Machine gates were green going in: ERC 0, netlist_audit 0, constraints_lint 0,
165/165 pins connected. Everything below is what those gates cannot see.

**Gate: 6 errors / 4 warnings.**

The scope rulings were honoured and are NOT reported: no protection parts, no
MCU/telemetry, L301/L302 footprintless PCB spirals, J101 THT exception.

---

## E1 - Gate drive presents 0.975 ohm at OUTH/OUTL, less than half TI's 2 ohm floor

`refs U201, Q201, Q202, R203-R210` | `net /stage/GATE_ON, /stage/GATE_OFF`

The LMG1020 datasheet (Sec 8.2 Typical Application, carried verbatim into
`parts/C6423790.json` layout_notes) states: *"use AT LEAST a 2-ohm resistor at
each OUTH and OUTL to avoid voltage overstress from inductive ringing; ringing
overshoot must not exceed the absolute max supply voltage (5.75 V)."*
`architecture/blocks.md` s258 restates it as the board's own spec: *"Gate
resistors: 2 ohm minimum per leg (TI floor)."*

As wired, **both** paralleled FETs hang off the same two output pins:

    OUTH (A2) --+-- R203 || R204 (1.95 R) --> GATE_Q1
                +-- R205 || R206 (1.95 R) --> GATE_Q2
    OUTL (B2) --+-- R207 || R208 (1.95 R) --> GATE_Q1
                +-- R209 || R210 (1.95 R) --> GATE_Q2

OUTH therefore drives **4 x 3R9 in parallel = 0.975 ohm**, and OUTL likewise.
The per-branch value is 1.95 ohm - already under the 2 ohm floor by itself, and
the schematic's own component notes admit it ("TI floor >=2R; pair = 1.95R") -
but the aggregation across the two FETs is the part nobody costed. Consequences:

- Peak source current doubles from the analysed ~2.5 A to **5.1 A** (VDD/0.975),
  and gate-loop di/dt doubles with it. The 2 ohm floor exists precisely to bound
  that di/dt.
- Headroom is **0.85 V** to the LMG1020's 5.75 V VDD/OUTx abs max and **1.1 V**
  to the EPC2019's **+6 V VGS abs max** at the 4.90 V nominal rail (0.69 V and
  0.94 V after E3's low corner is admitted). An eGaN gate has no avalanche
  margin: exceeding +6 V is a one-way, non-recoverable failure of both $3.93
  FETs and it happens on the first pulse.
- Second-order but real: building 1.95 ohm from **two** 0603s per leg puts eight
  resistors inside the loop that `LEARNINGS.md` calls "the tightest layout spec
  on the board" (0.48 nH/FET). One resistor per leg is strictly better copper.
  The architecture already carries a sanctioned fallback of **R_G = 3 ohm**
  (+0.3 W, +1.6 C) - taking it satisfies TI at the pin (1.5 ohm... still short;
  3 ohm *per branch* gives 1.5 ohm at the pin, so the floor genuinely needs
  >=4 ohm per branch for a 2-FET parallel pair, or a per-FET driver).

This is the single highest-risk defect on the board.

## E2 - C101/C102 electrolytic polarity is unverified and the available evidence conflicts

`refs C101, C102` | `net +40V`

The generator's own note is honest about this, so here is what I could and could
not close:

- **Verified:** the pulled symbol `RVT63V100M10X10` in `lib/aiee.kicad_sym` draws
  a "+" glyph at (-2.29..-1.27, 1.27) adjacent to **pin 1** (flat plate left,
  curved plate right). Pin 1 = anode is what the schematic wired to +40V. Symbol
  and footprint came from one easyeda2kicad pull of C51953411, so their pin
  numbering is internally consistent.
- **Conflicting:** the footprint `CAP-SMD_BD10.0-L10.3-W10.3-LS11.0-FD_1` carries
  **no polarity mark of any kind**, and its only asymmetric silk feature - the
  two chamfered corners at (-3.09, +/-5.23) -> (-5.23, +/-3.09) - sits on the
  **pad-1** side. On V-chip aluminium electrolytics the chamfered/bevelled base
  corner is conventionally the **cathode** indicator. Taken at face value the
  footprint says pad 1 = minus, i.e. the opposite of the symbol.
- **Missing:** `parts.json`'s `datasheet` field for C51953411 is the empty
  string, and there is no manufacturer drawing or datasheet PDF for it anywhere
  in `parts/`. Nothing in the workspace can adjudicate.

Failure mode if wrong: a 100 uF 63 V can reverse-biased at 40 V from a >=6 A
supply vents - on a bench, next to a person. Two of them. This must be closed
against a manufacturer land-pattern drawing before fab release, and the silk
polarity mark P6 is already tasked with must be derived from that same drawing,
not from the symbol.

## E3 - +5 V rail low corner is 4.59 V: below the driver's minimum VDD, and it breaks the IN+ absolute maximum

`refs U101, R101, R102, U201` | `net +5V`

`parts.json`'s own role text for R101 says *"PLACEHOLDER VALUE (30k/10k gives
5.0V for a 1.25V-class COT reference) - P4 confirms exact ratio against the
actual LM5017 FB reference."* P4 did not close it. Two things are wrong:

1. The real LM5017 reference is **1.225 V typ, 1.200/1.250 V min/max**
   (`parts/C34355.json`, pin 5). 30.0k/10.0k gives **4.90 V nominal**, not 5.0 V
   - already 100 mV low, and the error eats the low-side margin asymmetrically.
2. **R101 is a 5 % part.** LCSC C25553 = `0402WG**J**0303TCE` (J = +/-5 %), while
   R102/R103/R104 are all `...WG**F**...` (1 %). The schematic labels R102/R103/
   R104 "1%" and leaves R101 bare - it knows. The top leg is the dominant term.

Rail span, combining the reference tolerance with 5 %/1 % legs:

| corner | VOUT |
|---|---|
| min (1.200 V, 28.5k/10.1k) | **4.586 V** |
| nom | 4.900 V |
| max (1.250 V, 31.5k/9.9k) | 5.227 V |

- LMG1020 **recommended VDD is 4.75-5.40 V** - the low corner is outside it.
- LMG1020 **IN+ abs max is VDD + 0.3 V** = **4.886 V** at that corner. The drive
  is a mandated unipolar **0/+5 V** (decisions.md D8, and stage sheet note
  DRV-M-1). At the low rail corner the drive signal exceeds the input abs max
  by 114 mV on every cycle, forward-biasing the input clamp into VDD. Even at
  nominal the margin is only 200 mV, before any SMA-line overshoot.
- EPC2019 Rds(on) 36 mohm typ / 50 mohm max is specified **at VGS = 5 V**; the
  whole 11.25 W two-FET thermal budget assumes it.

Swapping R101 to a 1 % part is necessary but not sufficient - it only lifts the
low corner to 4.729 V, still under 4.75 V. The divider also has to be re-centred
to ~5.05-5.10 V nominal (e.g. 31.6k/10.0k -> 4.92 V min / 5.28 V max, both in
spec).

## E4 - BOM of record maps C107 (bootstrap) to the wrong part: 2.2 nF where the LM5017 needs 10 nF

`refs C107` | `net /hk/BST`

- Schematic: `10nF 100V X7R 0603`, LCSC C107059, note "Bootstrap BST-SW, 0.01uF
  per LM5017 s8.2.1.2.6". Correct - the datasheet (`parts/C34355.json`
  decoupling, BST) requires **0.01 uF (10 nF)**.
- `parts/parts.json`: **C519422, `CC0603KRX7R8BB222`, 2.2 nF 25 V**, role text
  *"PLACEHOLDER VALUE - P4 confirms against LM5017's internal HS driver
  bootstrap spec."* P4 fixed the schematic and never wrote back.

`bom_cpl.py` builds the BOM from `parts.json` (parts_json entries override the
board's own footprint LCSC fields), so the assembled boards get 2.2 nF - 4.5x
under spec. The bootstrap cap has to hold the high-side gate rail for the whole
225 ns on-time and be recharged inside the 144 ns minimum off-time; at 2.2 nF
the high-side drive sags, raising SW-node loss and risking erratic COT
behaviour. No downstream gate catches this: the ref *has* an LCSC number, it is
just the wrong one.

## E5 - 26 schematic refs have no BOM-of-record entry, including the entire output network

`refs C110, C111, C213, R104, L201, L202, C301-C319, C206`

`parts/parts.json` is stale against the schematic:

| missing / malformed in parts.json | what it is |
|---|---|
| C301..C319 (19 caps) | the **whole C_s and C_m banks** - parts.json carries the literal range strings `"C301..C308"` and `"C309..C317"`, which `bom_cpl` does not expand, and which do not even span C318/C319 |
| L201, L202 | the **drain RF choke** - entered as `L201A`/`L201B` |
| C110, C111, R104 | the **Type 3 ripple-injection network** (Cr, Cac, Rr) |
| C213 | the LMG1020's mandated additional 1 uF |
| C206 | entered as the literal ref `"C206 (DNP by default)"` |

Reinforcing this from the other side: the placed symbol instances for U101,
U201, C105, C106, C201, C202 and C213 carry a `"LCSC Part"` property (inherited
from the symbol) but **no `"LCSC"` instance property**, and `bom_cpl.board_lcsc_map`
matches on `pname.upper() == "LCSC"` only - so the board-file fallback misses
them too. Both paths to an LCSC number fail for the same refs.

Left as-is, the fab release either trips the "refs with no LCSC" gate (best
case, late) or ships boards with no tank, no drain choke and no ripple
injection. The board cannot be brought up in that state.

## E6 - R201/R202 termination runs at 100 % of rating, ~150 % of its derated capability

`refs R201, R202` | `net /stage/DRIVE`

`architecture/blocks.md` s237: *"~5 Vpp square into 50 ohm is 0.125 W - over a
0603's rating, in a 100 C-class local environment."* `parts.json` repeats it:
*"125mW rating per part comfortably covers the ~0.0625W each sees."*

That is the **bipolar +/-2.5 V** number. The design explicitly forbids bipolar:
the DC-coupling ruling (D8 / stage sheet DRV-M-1) mandates **unipolar 0 to
+5 V**. For a unipolar 0/+5 V square at the Class-E nominal 50 % duty:

    P_total = (5^2 / 50) x 0.5 = 0.250 W   ->   0.125 W per 0805

C17408 is `0805W8F1000T5E` - **1/8 W = 0.125 W** at 70 C. So each part sits at
exactly 100 % of rating at 70 C, and in the 100 C-class local environment
blocks.md itself assumes, linear derating to 155 C leaves ~0.081 W, i.e. the
parts run at **~154 % of capability**, continuous duty. The figure was off by
exactly 2x. They will drift then open; when they do, the SMA line is
unterminated and the reflected edge lands on an input whose abs max is already
only 200 mV away (E3).

Four 200 R 0805 in parallel, or 2 x 100 R in 1206/2010, fixes it.

---

## W1 - C_m built at 560 pF against a 530 pF target: match presents 3.74 + j0.68 ohm, ~221 W

`refs C310-C319, L302` | `net /tank/RFOUT`

`blocks.md` s174 specifies "C310-C319 C_m **530 pF**, 10x 1206 C0G 1 kV" -
arithmetic that never closed, since 10 x 56 pF = 560 pF and no 53 pF part
exists on this BOM. The schematic carries 560 pF and its own component note
still says "target 530pF". The ideal L-match for 50 -> 4.13 ohm is Cm = 530.4 pF
/ Lm = 109.5 nH, so the built bank is **+5.7 %**. Computed at 20 MHz:

| build | Z seen by the tank | VSWR at drain | series X/R | Pout at 40 V |
|---|---|---|---|---|
| target 164n/518p/110n/530p | 4.136 + j0.050 | 1.012 | 1.28 | 200 W |
| **as built 164n/504p/110n/560p** | **3.737 + j0.675** | **1.220** | **1.47** | **221 W** |

Two effects, both pushing the same way (C_s at 9 x 56 = 504 pF vs the 518 pF
target does not compensate - it adds to the reactance error):

- Load resistance 9.5 % low -> **~221 W instead of 200 W** at a 40 V bus. Every
  derived quantity scales with it: I_dc, FET conduction loss, and the 11.25 W /
  Tj 114 C two-FET thermal budget that the whole paralleling decision rests on.
- Total series reactance moves to **X/R = 1.47** against the Class-E optimum
  1.1525 - ZVS is off, so switching loss appears on top of the raised
  conduction loss.

Neither C_s nor C_m has a trim site; only C_shunt got DNP pads (C205/C206). If
the intent was to trim the match at bring-up, the sites are missing; if the
intent was 530 pF, the bank needs re-solving (e.g. 9 x 56 pF = 504 pF plus one
27 pF, or a documented owner ruling that 560 pF and 221 W are accepted).

## W2 - R103 is an 0402 carrying the full 40 V bus continuously

`refs R103` | `net +40V`

The hk sheet note claims "*every +40V part >=63 V*". R103 is the exception it
misses: it sits from the RON pin (held near ground by the LM5017 on-timer) to
+40V, so the whole bus appears across a single 0402. Thick-film 0402 maximum
**working** voltage is 50 V - 40 V DC is 80 % of it with no margin left for the
~51 V LC turn-on overshoot P1 predicted on this bus, which exceeds it outright.
Power is a non-issue (16 mW); voltage is the limit. Two 0402s in series, or one
0603/0805 (100 V-class working voltage), closes it. R104 sees ~35 V and is
inside the limit.

## W3 - C106 (LM5017 VCC) derates to ~0.5-0.65 uF against a 1.0 uF requirement

`refs C106` | `net /hk/VCC`

`parts/C34355.json` decoupling: VCC wants **1.0 uF ceramic, >=16 V**. C106 is
1 uF **16 V** X7R 0603 (C106248) on a rail regulated to **7.6 V typ** (up to
8.55 V over temperature). A 16 V 0603 X7R at ~48-53 % of rated bias typically
loses 35-50 % of its capacitance, landing at 0.5-0.65 uF effective. That cap
also sources the internal-diode recharge of the bootstrap cap every cycle, so it
compounds E4. Same footprint in 25 V or 50 V removes the problem for no cost.

## W4 - No series filtering between the buck output and the driver VDD

`refs U101, U201, C108` | `net +5V`

`parts/C34355.json` layout_notes[7] flagged this and explicitly deferred it:
*"filtering on the +5V feed to LMG1020 [is] needed regardless of the exact
RON/fSW chosen; not resolved by component selection alone. **P4/P6 concern**."*
P4 resolved the decoupling (C201/C202/C213 at the driver, C108/C109 at the buck
- both correct per their datasheets) but added no series element, so +5V is one
low-impedance node from L101 to U201.A1.

The driver pulls 72 mA typ / 100 mA max of gate charge at a 20 MHz repetition
rate (2 x Qg x fsw, Qg 1.8/2.5 nC). With nothing in series, that 20 MHz current
returns across the board to C108 rather than staying inside the driver's local
1.1 uF - a board-scale 20 MHz loop next to an FB trace TI's layout guideline 3
says to keep away from switching nodes. A bead or small inductor between C108
and C201/C202/C213 turns the existing caps into a pi filter and contains it.

---

## Checked and found correct (recorded so it is not re-reviewed)

- **EPC2019 pin 7 SUBSTRATE -> SOURCE.** Q201.7 and Q202.7 are both on GND with
  pins 2/4/6; drains 3/5 both on /SW. The datasheet's three-times-stated
  requirement is met on both parts. (Symbol names pin 7 "SOURCE" rather than
  "SUBSTRATE" - cosmetic, but it hides the requirement from any downstream tool.)
- **LMG1020 input wiring.** IN- (C2) tied to GND, drive to IN+ (C1). Matches
  Table 1: only (IN-=L, IN+=H) drives OUTH high. Correct, and *necessary* - IN-
  has a 150k internal pull-**up** to VDD, so leaving it floating would hold the
  stage permanently off. IN+'s internal pull-**down** makes an open drive input
  fail safe. No AC coupling anywhere on /stage/DRIVE (confirmed in the netlist:
  J201.5 -> R201/R202 -> U201.C1, resistive only).
- **Split-output usage.** OUTH sources only / OUTL sinks only, each with its own
  resistor leg, no steering diode. No shoot-through path: OUTH is high-Z
  whenever OUTL is driving and vice versa. Topologically correct - only the
  *values* are wrong (E1).
- **LM5017 Type 3 ripple injection.** R104 (Rr 100k) SW -> node, C110 (Cr 1 nF)
  node -> VOUT, C111 (Cac 100 nF) node -> FB. Verified against the datasheet's
  own equations (p.12, Sec 7.3.11 + design eqs 6/7), at fSW = VOUT/(K.RON) =
  544 kHz, tON = 225 ns:
  - eq 7: Rr.Cr must be < (VIN-VOUT).tON/25mV = **316 us**; built = **100 us**
    -> pass, 3.16x margin. Ramp at FB **79 mV pk-pk** vs the 25 mV floor.
  - eq 6: Cac must be > 5/(fSW.(RFB2||RFB1)) = **1.22 nF**; built = **100 nF**
    -> pass.
  - Ramp is in phase (rises during on-time, falls monotonically during
    off-time). Cr returning to VOUT rather than GND is the equivalent variant -
    node A's DC level is VOUT either way and the AC amplitude is identical.
  - Timers: tON 225 ns > 100 ns floor (176 ns even at a 51 V bus), tOFF 1612 ns
    > 144 ns floor. Current limit 0.7 A min vs an 85-100 mA load.
- **UVLO tied to VIN.** Sanctioned explicitly by the datasheet ("*If tied
  directly to VIN, regulator starts as soon as VCC UVLO (4.5 V) is satisfied*");
  UVLO abs max is 100 V, so 40 V is fine. Side effect worth knowing at bring-up:
  the +5 V rail comes alive at ~5-6 V of bus, well before the bus reaches 40 V -
  which is the *good* direction, since it guarantees the driver's OUTL is
  holding the GaN gates low before the drain sees any appreciable voltage.
- **Abs-max vs applied, every IC.** LM5017 VIN 40 V (51 V transient) vs 100 V
  abs max / 7.5-100 V operating - fine; RON, UVLO, BST-to-SW (7.6 V vs 13 V),
  VCC, FB (1.225 V vs 5 V) all inside. EPC2019 VDS 142.5 V pk vs 200 V (1.4x).
  LMG1020 VDD is the only one that fails, via E3.
- **C_shunt sizing.** Sokal C1 = 403.3 pF (infinite choke) + 40.4 pF
  finite-choke correction for the 0.94 uH feed = 443.8 pF; the stage sheet
  states a 403-449 pF band and populates 316 pF (2 x Coss(tr) 158 pF) + 112 pF
  (C203/C204) = 428 pF, mid-band, with C205/C206 DNP as headroom for the
  +36 % Coss spread. Self-consistent. (Note the band was derived at R = 4.13
  ohm; W1 moves the real R to 3.74 and the band with it.)
- **Drain choke.** 0.94 uH (L201+L202 in series) is 66 % of the Sokal RFC
  minimum 1.432 uH, i.e. this is deliberately a *finite* DC feed - and the
  finite-feed correction was correctly applied to C_shunt above, so it is a
  legitimate design point rather than an undersized choke. X_choke = 118 ohm =
  28.6x R at 20 MHz; AC ripple through it ~0.36 A pk against 5.9 A DC.
- **Tank dielectric and ratings.** Every part in the tank is 56 pF **1 kV C0G**
  (C113875) - no X7R anywhere in C_shunt, C_s, C_m or the bus HF bank's
  resonance terminators. Against decisions.md D9's node/element peaks (TANK_A
  156 V, C_s 151 V pk across) that is >6x margin. Current splitting is right:
  C_s bank 9 caps at 0.77 A rms each, C_m bank 10 caps at 0.70 A rms each - and
  the C_m note correctly identifies that the bank carries the ~7 A circulating
  current, not the 2 A load current.
- **Decoupling, per pin, against each datasheet.** LMG1020 A1: C201 100 nF 0402
  + C213 1 uF 0603 - exactly TI's "0.1 uF closest + an additional 1 uF" rule -
  plus C202 10 nF 0201. LM5017: C105 100 nF at VIN/RTN + C103/C104 2.2 uF 100 V
  bulk, C106 at VCC (see W3), C107 at BST (see E4). `kicad/decoupling.json`
  carries all five associations with distance and loop-inductance limits for P6.
- **+5 V rail budget.** 72 mA typ / 100 mA max gate charge + ~24 mA driver
  operating current, against the LM5017's 600 mA capability and 0.7 A min
  current limit. Transient sag across the local 1.1 uF is microvolts; the real
  constraint is ESL, which is a P6 problem and is already specified
  (max_loop_nh 0.3).
- **Connector checklist.** J201/J301 are the same CONSMA001 SMD SMA; pin 5 is
  the centre conductor, pins 1-4 the shield, all four on GND (no split-shield
  strategy to get wrong). J101 pinout 1=+40V / 2=GND with a documented THT
  exception. Reverse-plug on J101 is destructive and unprotected - which is the
  owner-accepted no-protection ruling, so not filed; the silk polarity legend
  P6 owes J101 is the mitigation.
- **Polarity, everything else.** No diodes, no LEDs on this board. C101/C102 are
  the only polarized parts (E2).

## What could not be verified

- **C51953411 (C101/C102) pad-1 polarity** - no datasheet, no manufacturer
  drawing anywhere in the workspace; `parts.json`'s datasheet field is empty.
  See E2.
- **FXL0630-R47-M self-resonant frequency.** The BRIEF requires the drain choke's
  SRF to be "well above 20 MHz" and these are molded power inductors, not RF
  chokes. No datasheet for C167212 is in `parts/`, so neither SRF nor 20 MHz
  core loss could be checked against the vendor curve. The two-in-series +
  "place PHYSICALLY SEPARATED" note suggests the risk was considered, but the
  number was never pinned. Worth closing before fab - a choke resonating near
  20 MHz stops being a choke.
- **EPC2019 Coss(tr) 158 pF.** The datasheet extraction gives Coss_typ 110 pF /
  max 150 pF and Qoss 18 nC at 100 V; the 158 pF figure comes from blocks.md's
  power-law fit (156.8 pF typ / 203.3 pF max), not a datasheet field. The fit
  looks sound and the DNP trim sites cover the max corner, but the underlying
  number is derived, not extracted.
- **Uniohm tolerance/rating decoding.** R101 = 5 %, R201/R202 = 1/8 W and
  R203-R210 = 1/10 W are read from the manufacturer part-number coding
  (`...WGJ...` vs `...WGF...`, `0805W8`, `0603WA`), which is self-consistent
  across all eight parts on this BOM and corroborated by the schematic's own
  "1%" labels on R102/R103/R104 and their absence on R101 - but no Uniohm
  datasheet is in `parts/` to confirm it directly.
