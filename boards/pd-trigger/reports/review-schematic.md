# Schematic review - pd-trigger (adversarial, P4)

Reviewer stance: hostile senior EE, assume the schematic is wrong until traced to
ground truth. Authority order: `parts/C970725.json` (CH224K extract, manual V2.1)
> `architecture/` (decisions.md incl. A1) > `parts/parts.json`. Evidence:
`reports/schematic.pdf` (rendered and read), `reports/top.net` (regenerated this
session), `reports/lib_verify.json`, Nexperia BC847BS product data sheet
(fetched and read directly, pinning table page 2). ERC 0/0 and netlist audit
"pass" were confirmed, then ignored - every claim below was re-derived from the
netlist and the extracts, not from the gates.

**GATE: 0 errors / 2 warnings.** No bring-up killer found. Two real risks
documented below; both have contingencies and neither has a traceable path to a
dead board or wrong output voltage.

---

## 1. THE QUESTION - DP/DM disposition (ruled on, as assigned)

**What was built** (netlist net 1): U1 pin 4 (DP) and pin 5 (DM) shorted
together on `/BC12_DIS`, connected to nothing else. Connector A6/A7/B6/B7
(Dp1/Dn1/Dp2/Dn2) all explicitly no-connect.

**What the authority says**: the extract's ONLY documented CH224K configuration
(reference schematic 6.2) wires DP/DM straight to the connector data pins - the
part also speaks legacy D+/D- protocols (BC1.2 / QC / Apple divider). The
manual documents neither "short them for PD-only" nor "float them". The
interface research's claimed "PD-only: short them" instruction is NOT in the
extract and could not be verified (V12 remains unresolved against a primary
source).

**Hazard trace, pin by pin:**

- *Chip hardware*: DP/DM are VDD-domain pins (abs max VDD+0.5 = ~3.8 V). Shorted
  to each other and isolated from the connector, no external potential can ever
  reach them. The reference wiring is the RISKIER option at this receptacle: a
  VBUS-to-D+ short (partial insert / debris - the same fault class V4 already
  accepts on CC) would put up to 21 V on a 3.8 V-abs-max pin. The short-at-chip
  REMOVES a hardware kill path.
- *Chip's own drivers*: worst case is the chip driving D+ while sensing/driving
  D- during legacy probing. Both drivers are the chip's own weak
  protocol-detection sources in one supply domain; contention into the short is
  self-limited to mA-scale at <= VDD. No damage mechanism.
- *False BC1.2 detection*: D+ shorted to D- is electrically what a DCP charger
  presents. If the chip runs sink-side primary detection (0.6 V on D+, sense
  D-), the short reflects it and reads "charging port". Consequence bounded: PD
  negotiation runs on CC regardless (the part's primary function; the extract's
  own 20 V reference drawing relies on CC-based PD with this same silicon), and
  the window LEDs verify the granted rail independently. No path from a spurious
  DCP read to a wrong output voltage.
- *Non-PD sources*: a QC-only or dumb 5 V adapter never sees the board's D+/D-
  (connector pins NC), so no legacy handshake can complete. Output stays 5 V,
  D5 "5V ONLY" lights - exactly the specified fallback behavior (P0 answer 6).
  NOTE the capability cost: a connector-wired CH224K can pull 9/12 V from
  QC-only adapters; this board deliberately cannot. Compliant with the brief
  (PD SINK only, no data), but users who expect trigger boards to speak QC
  should learn it from the docs, not the bench.
- *Floating pair*: the short defines no DC level, so the PAIR still floats
  relative to GND when the chip tri-states both. With no external counterparty
  attached, a "spurious handshake" has no second party; every probe sequence
  terminates in the benign outcomes above. mm-scale antenna, negligible.
- *Connector D+/D- floating at the receptacle*: acceptable. Source-side D+/D-
  are outputs (DCP short, Apple divider) or absent; no charger requires
  sink-side termination to deliver vSafe5V; a PC host seeing no device still
  supplies 5 V per Rp. No damage path, standard practice on PD-only triggers.

**VERDICT: acceptable as built - warning, not error.** The short-at-chip is
hardware-safer than the datasheet's own wiring at a charger-only receptacle, and
every traceable functional path ends at "PD works / non-PD gives 5 V + red
LED", which is the specified behavior. It remains a configuration the silicon
vendor does not document, resting on an unverified secondary source - so it
gets a warning and two bring-up checks: (1) sweep all five profiles from a real
PD source; (2) plug a non-PD 5 V and, if available, a QC-only adapter and
confirm 5 V + red with no anomalies (renegotiation loops, hot chip).

## 2. Hunt results (assigned suspicion list)

### 2.1 VDD budget arithmetic - HOLDS, with a sharper worst corner than the docs state

Netlist: `/VIND -> R2A 510R -> /R2_MID -> R2B 510R -> /VDD` (1020R total, the
pre-approved D2 alternate), C5 1uF /VDD-GND, R3/R4/R5 100k /VDD->CFG1/2/3,
U1 pin 1. Nothing else hangs on /VDD (verified: no PG pull-up, no LED, 6 nodes
total). Strap current flows only through CLOSED switches (33 uA each at 3.3 V).

| VBUS in | dropper gross | straps (all 3 ON) | net for U1 IDD |
|---|---|---|---|
| 5.25 V | 1.912 mA | 99 uA | 1.813 mA |
| 5.00 V | 1.667 mA | 99 uA | 1.568 mA |
| 4.40 V low line | 1.078 mA | 99 uA | **0.979 mA** |

The design's own figures (1.7 mA at 5 V gross, 1.1 mA at 4.4 V gross, straps
99 uA = 6 %) are all arithmetically correct. What the docs never state is the
COMBINED worst corner: 4.4 V low line WITH all three straps closed - which is
not exotic, it is precisely the advertised fallback scenario (user selects 9 V,
source refuses, bus sits at vSafe5V minus cable drop). Net budget there is
**0.979 mA** for an IDD the extract confirms is UNPUBLISHED. Ceiling before VDD
leaves the 3.0 V operating minimum at 4.4 V in: 1.28 mA. -> WARNING 2, with the
existing V1 contingency restated for the shipped implementation: "R2 -> 680R"
now means replacing BOTH 510R parts (e.g. 2x 330R = 660R, 24.1 mA / 0.19 W each
at 21 V - still inside the 0.25 W parts), not swapping one refdes.

Dropper checks at the top of the range: 16.37 mA at 20 V / 17.35 mA at 21 V -
inside the 30 mA shunt sink limit; 137/154 mW per 510R against 250 mW rating
(55/61 %) - matches the pre-approved D2/A1.3 figure exactly. Even at the TVS
clamp (28.4 V) the dropper delivers 24.6 mA < 30 mA, so a clamped transient
cannot push the shunt past its sink limit. Verified-OK.

### 2.2 VBUS sense R1 10k into pin 8 - implementation exactly per the authority

Netlist: `/VIND -> R1 10k -> /VSENSE -> U1.8`; nothing else on /VSENSE. This is
the reference schematic 6.2 topology and value verbatim (R14 0R in front is
electrically transparent). On "is a series R alone enough at 21 V": a series
resistor into a truly high-impedance pin would drop nothing - the pin must
present an internal load/clamp, and the extract's wording ("a series resistor
to the external VBUS input is REQUIRED", abs max 13.5 V, ref circuit drawn for
a 20 V request) is the manufacturer asserting that R + internal behavior keeps
the pin legal at 20-21 V. WCH does not publish the mechanism; if the internal
clamp sits at ~13.5 V the continuous current is (21-13.5)/10k = 0.75 mA,
5.6 mW in R1 - trivial. Implementation cannot be improved from here without
vendor data the manual does not contain. Verified-OK; suggested first-article
measurement: pin-8 node voltage at the 20 V profile (one probe, settles V12's
cousin question for the record).

### 2.3 Window detector truth table - HOLDS with these exact values

Netlist topology verified node by node: D2 cathode on /VIND (correct breakdown
orientation), anode -> /ZBIAS -> R6 6k8 -> /HV_B = Q1A base; R7 4k7 base-GND;
Q1A = E1/B2/C6 (TR1, see 3.2), collector /HV_OK carrying R8 10k pull-up to
/VIND, D6 cathode, and R9 47k -> /FB_B = Q1B base (TR2 = E4/B5/C3); D5 cathode
on /FB_K = Q1B collector. LED legs: /VIND -> R12 1k5 -> D5(A), /VIND -> R13
4k7 -> D6(A), /VIND -> R10 3k3 -> D3(A) -> GND.

Computed (Vf red 2.2, green 2.0, Vbe 0.65, Vce_sat 0.2):

| VBUS | D5 red | D6 green | margin notes |
|---|---|---|---|
| 4.40 V | ON 1.33 mA | off (leg dV 0.66 V << Vf) | Q1B forced beta 20 vs hFE min 200 |
| 5.25 V | ON 1.90 mA | off (leg dV 0.81 V) | zener leakage needs >138 uA through R7 to fake a trip; BZX84C6V2 IR is uA-class at 5.25 V reverse - cannot |
| 6.70 V | transition band | transition band | trip tolerance 6.15-7.25 V across Vz 5.8-6.6; no PD profile rests here, transit-only |
| 9.00 V | off | ON 1.45 mA | Q1A net base 112-178 uA, forced beta 13-20; worst Vz corner (6.6 V) still leaves 53 uA = 10x the needed drive |
| 20.0 V | off | ON 3.79 mA | zener 13 mW vs 350 mW; R13 75 mW vs 125 mW (documented 1.56x) |

Exactly one LED lit in every steady state; trip window (6.15-7.25 V worst-case)
clears the 5 V ceiling (5.25 V) by >= 0.9 V and the 9 V floor (8.55 V) by
>= 1.3 V. Q1B collector when off floats to ~VBUS through the dark D5 leg: 21 V
steady / 28.4 V clamped transient vs Vceo 45 V - safe, and no LED ever sees
reverse bias (both window LEDs sit sub-threshold-forward when dark, verified).
Arithmetic nit in D4 (no action): "R6 delivers 243 uA of base drive at 8.55 V"
ignores R7's ~138 uA steal - NET drive is ~112 uA. Conclusion unchanged
(forced beta 20 vs hFE 200).

### 2.4 5 A path integrity in the netlist - CLEAN

Net `VBUS` members, complete: J1 `A4-B9` + `B4-A9` (= all four VBUS contacts,
ganged in the verified footprint), D1 IN 4/5/6, C1A, C1B, C2, F1.1, R14.1,
J2.1. J2 pin 1 sits ON the net - **nothing in series between receptacle and
screw terminal**; F1 and R14 are taps that leave the net, not links in it.
J2.2, J3.2 on GND; GND return = J1 `A1-B12` + `B1-A12` (all four GND contacts)
plus shell stakes EH1-4 (datasheet: SHELL -> GND, per lib_verify). Bookkeeping
for P6: D16 V8 says "exactly five taps" - the documented C1 -> C1A+C1B split
makes it SIX stubs to keep hugging the run. Update the count when placing;
not a schematic defect.

### 2.5 CFG strap polarity vs the verified table - CORRECT and convention-proof

R3/R4/R5 pull UP to /VDD (never VBUS - CFG2/3 abs max VDD+0.5 honored; CFG1
high = 3.3 V < 8 V). SW1 pins 1/2/3 = CFG1/2/3, pins 4/5/6 ALL on GND. Open =
1, closed = 0. CFG1 open -> `1XX` -> 5 V: unpopulated/broken switch fails to
the lowest profile - the safety polarity, as designed. Map re-derived against
the extract's CH224K-specific table (1XX=5, 000=9, 001=12, 011=15, 010=20):
the D3 silk table (9 V = ON ON ON ... 20 V = ON OFF ON) inverts it correctly.
Robustness found: because ALL of pins 4/5/6 are grounded, the wiring is correct
under BOTH DIP pairing conventions ((1,6)(2,5)(3,4) per lib_verify's footprint
geometry, or (1,4)(2,5)(3,6)) - a pairing mistake cannot scramble profiles.
Actuator k = column k = CFGk holds regardless. Straps-to-VDD also cannot be
misread as an Rset-to-GND code (extract: Rset reads a resistor to ground).

### 2.6 TVS D1 orientation and protection reach - CORRECT

Netlist: IN 4/5/6 on VBUS, GND 1/2/3 + EP(7) on GND - matches TI SLVSED5A
section 6 exactly (lib_verify checked the symbol/footprint against the TI
datasheet; this review checked the netlist put the right nets on those pins).
Protection audit at the numbers: standoff 22 V > 21 V max operating (no
conduction, uA leakage); clamp 27.7-28.4 V at 40 A 8/20us. Behind it: caps
50 V (1.8x clamp), F1 30 V max, Q1B Vceo 45 V, U1 pin 8 sees (28.4-13.5)/10k
= 1.5 mA into its clamp through R1, VDD dropper delivers 24.6 mA < 30 mA shunt
sink even AT the clamp voltage. The one thing D1 does not protect is CC1/CC2
(8 V abs max, wired straight to the connector) - that exposure is V4's
documented, accepted decision (a CC-legal TVS cannot protect an 8 V pin from a
20 V short), reviewed here as implemented-as-documented, not re-opened.

## 3. Beyond the assigned hunts

### 3.1 Every U1 pin traced against the extract - all correct

1 VDD (dropper + C5 1uF: the only cap the datasheet requires - present),
2 CFG2, 3 CFG3 (straps to VDD per fig 7-2 - the extract-confirmed topology; no
internal pull-ups on this die, external 100k present), 4/5 DP/DM (section 1),
6 CC2 = J1.B5, 7 CC1 = J1.A5 (straight through, NO external Rd - matches the
CH224K-specific reference; CH224D/CH221K's 5.1k must not be fitted and is not),
8 VBUS via 10k, 9 CFG1, 10 PG no-connect (exactly as reference 6.2; no pull to
anything - correct, the pin has no published abs max), 11 GND = the exposed
baseplate the datasheet calls pin 0 (V11 trap: symbol pin 11 + footprint pad 11
+ fp_verify agree - U1 is grounded).

### 3.2 Q1 dual-NPN pin pairing - the one unverified-by-librarian part, now verified

`lib_verify.json` checked pin maps for U1, J1, D1, D2, the LEDs and SW1 - but
NOT Q1, the one part where a die-pairing mistake is silent and fatal. The aiee
symbol claims 1=E 2=B 3=C 4=E 5=B 6=C, and the netlist pairs (E1,B2,C6) as Q1A
and (E4,B5,C3) as Q1B. Checked this review against the Nexperia BC847BS product
data sheet, pinning table read directly: pin 1 E1, 2 B1, 3 **C2**, 4 E2,
5 B2, 6 **C1** - i.e. TR1 = (1,2,6), TR2 = (4,5,3). The schematic's pairing is
EXACTLY the standard BC847BS die arrangement. (Caution for anyone re-deriving
this: the naive assumption TR1=(1,2,3)/TR2=(4,5,6) is wrong for this part
family and would have declared this schematic broken; conversely a part built
that way would break this schematic - see OPEN on the hongjiacheng clone PDF.)
Q1 emitters 1/4 both on GND, Vceo 45 V >= the 30 V criterion, re-verified.

### 3.3 Housekeeping partition - matches A1 exactly

/VIND (behind R14 0R) carries precisely the eight documented taps: R2A (VDD
dropper), R1 (sense), D2/R8 (window), R10/R12/R13 (LED legs), R14. Nothing
low-current hangs directly on VBUS; nothing on /VDD but the straps, C5 and U1.
/VAUX = F1 -> J3.1 only; J3.2 GND - the 1 A PPTC guards exactly and only the
aux header, per D0.1/D1 (no main-path series element - implementation of the
settled policy confirmed: F1 is NOT in the J1->J2 run).

### 3.4 ERC hygiene

PWR_FLAGs on VBUS, GND, /VDD; PG and D2 pin 2 (no-function pin, per LGE
datasheet) carry explicit no-connects; J1 SBU1/2 and all four data pins
explicit no-connects. ERC 0/0 reproduced; netlist audit's 3 warnings are
pin-type bookkeeping on connector-only nets (no power_in pin on VBUS//VAUX/
/VIND), not electrical findings.

## 4. Findings

### WARNING 1 - /BC12_DIS: DP/DM shorted at the chip is undocumented-by-vendor (accepted with bring-up checks)

Severity warning. Net /BC12_DIS, refs U1, J1. Full reasoning section 1.
The configuration is hardware-safer than the reference wiring and functionally
benign in every traceable scenario, but it deviates from the only documented
CH224K circuit on the strength of a secondary source V12 never verified, and
it removes legacy-adapter (QC/BC) voltage capability by design. Bring-up: sweep
all 5 profiles from a PD source; confirm non-PD adapter -> 5 V + red, no
renegotiation loop or hot chip. Document "PD sources only" for users.

### WARNING 2 - /VDD worst-corner budget is 0.98 mA against an unpublished IDD

Severity warning. Net /VDD, refs R2A R2B R3 R4 R5 U1. The design's stated
figures are correct but are quoted at 5.0 V gross; the real worst corner
(4.4 V low line, all straps closed - the advertised fallback scenario) nets
**0.979 mA** for the chip, 42 % below the 1.7 mA headline, against an IDD the
extract confirms WCH does not publish. Ceiling before VDD < 3.0 V at low line:
1.28 mA. Existing mitigation stands (V1: measure VDD at the 5 V profile on the
first article); contingency restated for the shipped 2x510R implementation:
replace BOTH resistors (e.g. 2x 330R), not one.

## 5. Checked and explicitly cleared (no findings)

- 5 A path continuity and purity (2.4); TVS orientation + reach (2.6); CFG
  polarity/table (2.5); window truth table incl. Vz corners (2.3); R1 sense
  per reference circuit (2.2); U1 pin-for-pin vs extract (3.1); Q1 pairing vs
  Nexperia standard (3.2); pad-11 grounding (V11 closed); CC straight-through
  with no Rd (V3 honored); PG NC (D4/A1 honored); C5 = the datasheet's one
  mandated cap; bulk 20 uF < 100 uF cSnkBulkPd; dropper inside shunt sink
  limit at every voltage up to and including the TVS clamp.
- Settled items verified as implemented, not re-opened: no main-path fuse
  (D0.1/D1 - confirmed absent, F1 on aux only), no CC TVS (V4), DIP selector
  choice, LED brightness catalog ceiling (documented in parts.json + D15 risk
  3), refdes gaps (U2/C3/C4/D4/R11 absent by amendment - correct).

## 6. Notes for later phases

- P6: V8's "five VBUS taps" is now six stubs (C1A + C1B) - keep all hugging
  the run.
- P9/V10 silk: profile table orientation verified against the extract here -
  print exactly the D3 table. `AUX 1A MAX`, `V+`/`GND` at J3, cable
  disclaimer per V10.
- Bring-up additions from this review: pin-8 node voltage at 20 V (one probe);
  non-PD adapter behavior check (WARNING 1); VDD at 4.4-5.0 V with all
  switches ON (sharper version of V1).

## OPEN (could not verify)

- The hongjiacheng C41375126 vendor PDF is JS-gated at LCSC and could not be
  machine-read this session. Q1 was verified against the Nexperia-standard
  BC847BS pinning the clone advertises drop-in compatibility with (and which
  the EasyEDA-derived symbol encodes). Residual risk judged negligible; if the
  paranoid want certainty, buzz out one part (B-E diode drops pin2-pin1 and
  pin5-pin4) before the first power-up.
- CH224K IDD and pin-8 internal clamp behavior: unpublished by WCH, not
  verifiable from any document on file - bounded here by arithmetic and by
  WCH's own reference circuit operating at the same points (V1 owns the
  measurement).
- V12's claimed "short DP/DM in PD-only mode" instruction: no primary source
  on file; ruled on from first principles + the extract instead (section 1).
