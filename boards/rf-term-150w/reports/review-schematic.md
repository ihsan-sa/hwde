# P4 adversarial schematic review - rf-term-150w

Reviewer: schematic-reviewer subagent, fresh context. Everything below was
produced by running the tool, not by reading a claim. Verdict first:

**The circuit is correct.** Topology, the C1 safety pin assignment, R1's cold
end, the BOM budget, the field set and all five assembly notes check out
end-to-end against the netlist AND against the committed `.kicad_pcb`. One
real defect found, and it is downstream: **R1 silently falls out of the
delivered BOM and CPL.**

Gate: **1 error / 3 warnings.**

> Timing note: the workspace advanced under this review. The schematic was
> regenerated at 01:58:35 (J1's footprint vendored into `aiee:`, a `Description`
> field added to C1) and P5 `board_init` ran and committed (`56c5e8d`) while the
> review was in progress. **Every finding and every clean result below was
> re-verified against the current committed files**, not the snapshot the review
> started on.

---

## What was verified clean

### 1. Netlist implements the intended topology exactly

`kicad/rf-term-150w.net`, current file, verbatim:

```
(net (code "1") (name "/RF")
  (node (ref "C1") (pin "2") (pinfunction "ROTOR_2"))
  (node (ref "J1") (pin "1") (pinfunction "In_1"))
  (node (ref "R1") (pin "1") (pinfunction "RF_1")))
(net (code "2") (name "GND")
  (node (ref "C1") (pin "1") (pinfunction "STATOR_1"))
  (node (ref "H1") (pin "1")) (node (ref "H2") (pin "1")) (node (ref "H3") (pin "1"))
  (node (ref "J1") (pin "2") (pinfunction "Ext_2"))
  (node (ref "R1") (pin "2") (pinfunction "GND_2")))
```

Two nets, nine pins, zero unconnected. C1 has **one** pin on `/RF` and **one**
on `GND`, i.e. it is a genuine shunt at the port node - not in series. R1 pin 2
is on GND. J1 shield is on GND. H1-H3 pads are on GND.

Net *names* match `kicad/constraints.json` byte for byte (`/RF` from a root
local label, bare `GND` from the global power symbol). The trap in state.json
decision 26 - a mis-spelled net making every check pass on an empty set - is
avoided. There are 7 local labels spelled `GND` on the sheet; each shares its
stub with a `power:GND` symbol, and the power symbol wins the naming priority,
which is why the exported name is `GND` and not `/GND`. Confirmed in the export.

### 2. C1 case-to-GND: the safety property holds, verified through four layers

This is the highest-consequence item on the sheet and nothing reverses it.

| layer | evidence |
|---|---|
| generator | `sh.wire_pins("C1", {"1": GND, "2": RF})` |
| schematic instance | `lib_id aiee:5602`, pins wired as above |
| netlist | C1 pin 1 -> `GND`, C1 pin 2 -> `/RF` (quoted above) |
| footprint | `CAP-ADJ-TH_2P-BD7.5_5602.kicad_mod`: pad **1** = `drill 6.3` (the .234-64 UNS-2A threaded case), pad **2** = `drill 0.8` (the 0.38 mm insulated lead) |
| board (`.kicad_pcb`, committed) | pad 1 `(drill 6.3) (net "GND")`, pad 2 `(drill 0.8) (net "/RF")` |

The 6.30 mm hole is the case; it is on GND. The 0.80 mm hole is the lead; it is
on RF. The metal a hand or a Johanson 8764 tool brushes is at ground potential
while the port sits at 122.5 Vpeak.

The symbol's pin NAMES are `STATOR` (1) and `ROTOR` (2). They are mechanical
descriptors, they are `(hide yes)` on the plot, and they do not drive the net
assignment - matching state.json decision 40, `parts/5602.json`, the footprint
`descr` and the symbol `ki_description`, which all say the same thing in the
same direction. No source in the chain disagrees with any other.

### 3. BOM / CPL budget - 3 lines exactly, run not assumed

```
$ kicad-cli sch export bom --output bom.csv kicad/rf-term-150w.kicad_sch
"Refs","Value","Footprint","Qty","DNP"
"C1","1-30pF","aiee:CAP-ADJ-TH_2P-BD7.5_5602","1",""
"J1","SMA","aiee:SMA_BAT_Wireless_BWSMA-KWE-Z001","1",""
"R1","50R 250W","aiee:R_LapPad_T50R0-250-12X","1",""
```

3 lines. H1-H3 absent (`in_bom no` set at the symbol, agreeing with
`MountingHole_3.2mm_M3_Pad`'s own `exclude_from_bom` - the lumina-carrier H5
parity trap in LEARNINGS 2026-07-29 is avoided). `#PWR01-07` and `#FLG01`
absent. 6 footprints total. Budget (<=4 lines, <=6 placements) met.

### 4. Fields

Re-exported with the sourcing columns; all present on the current file:

| ref | Value | Footprint | Datasheet | MPN | Manufacturer | LCSC | DigiKey |
|---|---|---|---|---|---|---|---|
| C1 | 1-30pF | aiee:CAP-ADJ-TH_2P-BD7.5_5602 | Knowles catalog URL | 5602 | Johanson/Knowles | - | 1956-1000-ND |
| J1 | SMA | aiee:SMA_BAT_Wireless_BWSMA-KWE-Z001 | research/SMA-KWE...pdf | SMA-KWE | Lian Xin | C7498154 | - |
| R1 | 50R 250W | aiee:R_LapPad_T50R0-250-12X | research/T50R0...pdf | T50R0-250-12X | Vishay/Barry | - | 4353-T50R0-250-12X-ND |

The prior agent's flag is **confirmed**: see WARNING W1.

### 5. The five assembly text blocks - present, accurate, decision-matched

All five render on the PDF (extracted from the plot, not from the source):

1. flange straps are R1's only GND path; 418 pF = 15.2 ohm at 25 MHz on an
   anodised sink; solder straps to the loose flange BEFORE bolting down.
   Matches decisions "Adopt architect B3" / blocks.md s2.3, numbers identical.
2. three 1.0 mm shims, top copper 2.635 mm vs tab underside 2.667 mm, solder
   gap 0.032 mm. Matches the P2 decision digit for digit.
3. C1's threaded case is GND by design; tune at reduced drive or with a VNA,
   NEVER at 150 W; tool Johanson 8764. Matches decisions 40, 41 and 35.
4. R1 is a +/-5% catalogue part, 50 ohm +/-2% met by select-on-test,
   accept 49.00-51.00 ohm. Matches decision 11 and acceptance criterion 1's
   numeric window.
5. BeO substrate, do not machine/drill/grind/break, scrap whole. Matches
   decision 12.

No note contradicts a decision. No decision that belongs on the sheet is missing
from it (see NOTES for two hazards that requirements.md assigns to the README).

### 6. P5-P9 hazards that turned out to be non-issues

- **R1 2-pin symbol vs 3-pad footprint.** Correctly handled, not a parity
  problem. Pads are numbered `1`, `2`, `2`; pins are `1`, `2`. KiCad matches on
  pad *number*, and duplicate pad numbers on one net are the normal idiom (J1's
  four shield legs use it too). `kicad-cli pcb drc --schematic-parity` on the
  committed board: **0 parity violations**.
- **The H1-H3 `in_pos_files` question.** Closed, and it was never live. KiCad 10
  writes only `exclude_from_sim / in_bom / on_board / dnp` on a schematic symbol
  instance - there is no per-instance `in_pos_files`, so parity has nothing to
  compare. Measured on the committed board: 0 parity findings for H1/H2/H3.
- **Footprint references resolving.** All four (`aiee:R_LapPad_T50R0-250-12X`,
  `aiee:CAP-ADJ-TH_2P-BD7.5_5602`, `aiee:SMA_BAT_Wireless_BWSMA-KWE-Z001`,
  `MountingHole:MountingHole_3.2mm_M3_Pad`) resolve - proven twice: an ERC run
  with default severities is 0/0, and `board_init` imported all six footprints
  without a `footprint not found`.
- **Refdes sanity.** J1, C1, R1, H1-H3, `#PWR01-07`, `#FLG01`. No duplicates, no
  gaps, exactly one PWR_FLAG on GND (correct - nothing on a passive board drives
  anything, and a second flag would raise power_out<->power_out).
- **ERC.** Re-run on the current file: `{'total': 0}`, status pass.

---

## ERROR

### E1. R1 - the entire function of the board - is absent from the delivered BOM and CPL

Run against the **committed** board, not a hypothetical:

```
$ bom_cpl.py --pcb kicad/rf-term-150w.kicad_pcb --out-dir fab/
BOM.csv:
Comment,Designator,Footprint,LCSC
1-30pF,C1,CAP-ADJ-TH_2P-BD7.5_5602,
SMA,J1,SMA_BAT_Wireless_BWSMA-KWE-Z001,C7498154
CPL.csv:
Designator,Mid X,Mid Y,Layer,Rotation
C1,19.0750,-19.7500,Top,0.0000
J1,32.1250,-41.8500,Top,0.0000
```

`{"n_parts": 2, "missing_lcsc": ["C1"], "bom_complete": false}`

**Two lines. No R1.** A builder ordering from the delivered BOM receives an SMA
jack and a trimmer, and no 50 ohm 250 W termination.

Mechanism: `lib/aiee.pretty/R_LapPad_T50R0-250-12X.kicad_mod` carries
`(attr smd exclude_from_pos_files)`. `bom_cpl.py` derives **both** BOM.csv and
CPL.csv from the `kicad-cli pcb export pos` output (module docstring: "The pos
file already omits parts flagged exclude-from-pos/DNP, so BOM and CPL cover
exactly the assembled set"). Excluded from pos => excluded from CPL => excluded
from BOM. The pos export confirms it: only C1 and J1 rows.

Nothing catches this. `dfm_check.py`'s `missing_lcsc` check only inspects parts
that are *in* the pos report, so a part that vanished entirely produces no
warning at all. It breaks acceptance criteria 8 (BOM line count "counted from
the delivered BOM file"), 13 (sourcing per BOM line) and 16 (fab artifacts
complete).

Do **not** fix by deleting the attribute. `exclude_from_pos_files` is correct
for R1: it is an off-board hand-soldered part and must not appear in JLC's
placement file. The fix belongs at P9: author the delivered BOM from the
schematic (`kicad-cli sch export bom` gives all three lines) or append R1 to
`bom_cpl`'s output as an explicit hand-assembly line, and mark it "do not place"
so the CPL stays 2 rows.

## WARNINGS

### W1. `DigiKey` is a dead field - R1 and C1 will land in the BOM with no part number

The prior agent's flag is confirmed by grep: **zero** occurrences of "digikey"
(case-insensitive) anywhere in `.claude/skills/ai-ee/scripts/`,
`.claude/skills/ai-ee/reference/`, or the agent/SKILL markdown. `bom_cpl.py`
keys on `LCSC` only, through two paths and no others:

- `board_lcsc_map(pcb)` - reads a per-footprint field literally named `LCSC`.
- `load_parts_map(--parts parts.json)` - its `put()` helper is
  `if ref and lcsc:`, so a ref with an MPN/DigiKey PN but no LCSC is dropped.

And there is no `boards/rf-term-150w/parts/parts.json` to pass (`parts/` holds
only the four per-part datasheet JSONs). Net effect once E1 is fixed: R1 and C1
appear with an **empty LCSC column** and no orderable number anywhere in the
delivered file, while criterion 13 demands a stock figure and date per line.

What P9 must do, concretely: hand-author the sourcing columns rather than
relying on the generated CSV - carry `4353-T50R0-250-12X-ND` (R1) and
`1956-1000-ND` (C1) into the delivered BOM from the schematic's `DigiKey` field
or `parts/*.json`, and state the split-cart sourcing (J1 from LCSC, R1+C1 from
DigiKey) in the README. `dfm_check` will emit its non-failing `missing_lcsc`
warning for C1 regardless; that is expected, not a defect to chase.

### W2. The project's ERC config is blind to unresolvable footprints - mutation-proven

`kicad/rf-term-150w.kicad_pro` sets
`erc.rule_severities = {lib_symbol_issues: ignore, lib_symbol_mismatch: ignore,
footprint_link_issues: ignore}`. I tested whether that hides anything by
mutating a scratch copy - `aiee:R_LapPad_T50R0-250-12X` -> `aiee:R_LapPad_BOGUS_XYZ`:

- with default severities: **2 warnings** (the check is live and would catch it)
- with the project's severities: **0 total, status pass**

Today's board is genuinely clean (verified independently, see section 6), so
this is not a live defect - but the P4 ERC gate, whose criteria are
`fail_severities: [error, warning], max_count: 0`, cannot be trusted to catch a
footprint reference broken by any later edit. Either narrow the ignore list to
the two `lib_symbol_*` entries it actually needs, or record the blind spot as a
deliberate waiver.

### W3. The recorded ERC gate pass no longer refers to the schematic on disk

`state.json` `gates.erc.last.inputs`:

```
sch: sexpr_no_uuid:a6844623cff7843125fa373e73d7d58c538c6a9a6e6495fd251d1ac772a50213
pro: json_canonical:ac2fc2bf0113e4a737b4cf949e1b2a9d54731faa2f3edce9355c9a14c211b5aa
```

Recomputed on the current files with `statelib.hash_artifact`:

```
sch: sexpr_no_uuid:420fe62493c77c30d0907c71e55503312432940c837489b1a046fc30c898d275
pro: json_canonical:767fd0c802179e295e841c806a5f586b3071e4b47a139e1a5021a562afd55c29
```

Both inputs changed after the gate passed at 01:47 (schematic regenerated
01:58:35, `.kicad_pro` rewritten by rules_gen 02:00:13) and both rode into the
P5 commit `56c5e8d` without the ERC gate being re-run. `reports/schematic.pdf`
(01:45) is stale for the same reason.

I re-ran ERC on the current pair myself: still **0 errors / 0 warnings**, so no
defect got through this time. The problem is the record, not the board - a
resume that trusts the hash will believe P4 is current when it is not. Re-run
the erc gate against the current files.

---

## NOTES (no action required, recorded for the fix budget)

- **N1.** C1's pin names are `(hide yes)`, so the plotted sheet shows only pin
  numbers `1` and `2` beside the trimmer. A reader of the PDF alone learns
  "case = GND" only from assembly note 3. That is adequate (the note is explicit
  and unmissable) but the safety fact is single-sourced on the drawing.
- **N2.** requirements.md s8 raises F3 (HOT SURFACE - flange 75-120 C is the
  *normal* condition) and F2 (never key the transmitter with the port unmated).
  Neither is on the sheet. requirements.md assigns both to the README, with F3
  optionally to silk "budget permitting", so this is not a schematic defect -
  but the schematic PDF is the document a builder actually reads.
- **N3.** Sheet note 2 does not state the shim material. Decision 29 (P2,
  00:07:33) required METAL shims because the screws carried the RF return;
  decision 31 (00:10:28) superseded it - straps carry the return, so the shims
  are freed to be INSULATING and are "now the main lever on trimmer
  temperature". The sheet's silence is consistent with the final intent, but the
  README owes "insulating preferred", and a builder who reads only decision 29
  in the record would fit brass.
- **N4.** requirements.md criterion 1 still reads "Met by the termination
  element's own tolerance; no DC trimming is provided or required (A7)".
  Decision 11 superseded that with select-on-test, and sheet note 4 documents
  the real method. The schematic is right; the requirements text is stale.
- **N5.** J1's land pattern is BAT Wireless BWSMA-KWE-Z001 (LCSC C496551) used
  for the ordered Lian Xin SMA-KWE (LCSC C7498154). `parts/SMA-KWE.json` records
  that Lian Xin publishes no recommended pattern and that the 5.1 mm leg pitch
  is derived from the package outline; the footprint's ±2.55 mm pads match that
  derivation. The vendored copy in `lib/aiee.pretty/` is byte-identical to the
  KiCad 10 stock file except for the added `Datasheet` property (diffed) - pad
  numbering and geometry unchanged. Cross-part reuse is documented, not silent.
  Worth one look at P6/P9: 0.9 mm square legs into 1.4 mm round holes.
- **N6.** `netlist_audit`'s single warning, "declared power net '/RF' feeds no
  power_in pin", is an artifact of constraints.json listing `/RF` under `power`
  on a board that has no power_in pins anywhere. Benign.
- **N7.** R1's as-built lap pad is 5.0 x 7.0 mm; decision 21's inductance budget
  was computed on 4.4 mm wide x 7.1 mm. Immaterial - the failure threshold is
  76.9 nH against a 6.9 nH estimate (11x margin) - but the design doc's 6.9 nH
  is derived from a pad that no longer exists exactly.

---

## Method

Every claim above came from a command. ERC (`kc.py erc`, both with the project
config and with default severities), netlist export and byte-diff against the
committed `.net`, `kicad-cli sch export bom` (twice, default and with sourcing
fields), schematic PDF re-plot plus text extraction and zoomed crops of the
J1/C1/R1 regions, `board_init` into a scratch directory (two outline settings),
`kicad-cli pcb drc --schematic-parity` on the committed board, `bom_cpl.py` on
the committed board, `statelib.hash_artifact`, a deliberate footprint-name
mutation to prove the ERC blind spot, and a diff of the vendored J1 footprint
against KiCad 10 stock. Nothing was written to the workspace except this file
and its JSON sibling.
