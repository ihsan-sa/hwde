# decisions.md - bb-buck P2 architecture decisions (for the orchestrator's log)

Each entry: the decision, the number or rule behind it, and what would
reverse it. Conflicts between research fragments are resolved EXPLICITLY -
the losing source is named. Nothing is averaged.

## D1 - Topology: SYNCHRONOUS integrated-FET buck

P1's call, adopted unchanged. Async costs +0.42 W (+33 %) of board heat at
30 V / 2 A and adds a second 0.66-0.77 W hot spot landing at Tj ~126 C
against a 125 C diode rating; at D = 0.167 the free-wheel element conducts
83 % of every cycle. Rejected with numbers: asynchronous + Schottky, LDO
((24-5) x 2 = 38 W), controller + external FETs (1-2 points at 10 W for two
FETs and a gate network). **Reverses if** no stocked synchronous 36 V-class
3 A part exists - then re-run the whole budget and expect 4 layers.

## D2 - Lead part class, and the fixed-vs-adjustable conflict

**36 V-class synchronous integrated-FET buck, 3 A-class, exposed-pad
SOIC-8-EP/HSOIC-8, fixed 400 kHz, internally compensated, peak-current-mode.
Lead MPN: LMR33630ADDAR** (scout rank 1). No LCSC code is recorded anywhere
in this package - P3 owns codes.

**CONFLICT RESOLVED: P1 (power.md s5) preferred a FIXED 5 V part to delete
the divider tolerance term and two parts. The component scout found no fixed
5 V synchronous 36 V-class part in its JLC sweep; its only fixed-output
candidate (XL1509-5.0E1) is +/-4 % guaranteed, which alone exceeds A3's
+/-3 % budget, and is a bipolar output stage. P1's PREFERENCE loses to the
scout's stock reality** - it was a preference, not a filter, and P1 supplied
the adjustable path with numbers (see D6). If P3's sweep turns up a stocked
fixed 5 V sync part at >= 36 V abs-max, take it: R1/R2 and the whole s5
tolerance budget disappear.

Scout ranks 2-4 (AOZ1284PI, TPS54560B, TPS54360B) are all ASYNCHRONOUS and
are NOT drop-in fallbacks - D1 rejects that topology here with numbers. Rank
5 is excluded twice over (accuracy, efficiency).

## D3 - fsw 400 kHz, L = 15 uH

P1 recommended 500 kHz / 10 uH (band 350-600). The lead part is a FIXED
400 kHz device with no RT pin, and 400 kHz is inside P1's own band; power.md
s8b states the coupling: **at 400 kHz, L must be 15 uH** (10 uH gives 52 %
ripple), and `P_U1` improves 0.924 -> 0.854 W. Adopted: 400 kHz / 15 uH,
`dI 0.694 A`, `I_L,pk 2.35 A`, output ripple 10.4 mVpp. **Reverses if** the
part's internal-compensation L/C table excludes 15 uH - fallback 10 uH at
400 kHz (ripple 15.6 mVpp, `I_L,pk 2.52 A`, both still inside spec), or a
different part restores 500 kHz / 10 uH.

## D4 - 2 layers, stackup `JLC2313_1.6`, 1 oz - CONDITIONAL

Conditions: synchronous (D1), `P_U1 <= 0.95 W` at 30 V / 2 A, outline
>= ~1000 mm^2 with an unbroken B.Cu GND pour, >= 16 thermal vias,
`Tj_max = 150 C`. **Escalation trigger, named: P_U1 > 0.95 W (at 400 kHz that
is `Rds_LS > ~110 mOhm` at 25 C; at 500 kHz, 85 mOhm), OR a 125 C part, OR an
async part, OR check_thermal erroring at dt_c 70 -> switch to 4 layers,
`JLC04161H-1080B`.** The outline does not change on escalation. P3 must
re-run this arithmetic with the chosen part's real datasheet Rds BEFORE P5
freezes the stackup. Rejected: `JLC2313_1.6_2oz` (nothing on this board needs
2 oz; the widest requirement is 1.52 mm at 2.6 A on 1 oz).

## D5 - Outline 40 x 30 mm (1200 mm^2), FINAL

The mode's "smallest honest outline" has a numeric floor here because the
outline IS the radiator: R_ba 39 / 34 / 31 C/W at 875 / 1064 / 1200 mm^2, so
area buys more junction temperature than layers do (~10 C vs ~11 C, and area
is free at the fab up to 100 x 100 mm). 40 x 30 is 20 % above P1's ~1000 mm^2
floor and is a row P1 actually computed (Tj 107 C at 0.92 W, 25 vias). The
increment over 38 x 28 is bought by physical parts, not padding: a 10-12.5 mm
inductor (D11), two ~10 mm-deep screw terminals, and 4 x M3 with 6.5 mm
keepouts. **There is no outline-shrink step later in this pipeline** - if
P3's inductor is smaller than assumed, the board stays 40 x 30 and runs
cooler. J1 on the LEFT edge, J2 on the BOTTOM edge (different edges,
openings outward).

## D6 - FB divider tightened to 0.1 % / 25 ppm (P1 floor was 0.5 %)

With 1 % resistors the worst-case SUM is ~3.7 % and does not close against
A3; 0.5 % closes only on RSS (~1.8 %); **0.1 % / 25 ppm closes on the
worst-case SUM (~2.5 %)** for a few cents and zero change in part count.
Same family, TCR-tracking, sense point after the output caps. P1's 0.5 % is
retained as the floor if 0.1 % is not stocked.

## D7 - `pdn: false` DROPPED from the GND power entry (P1 emitted it)

`pdn: false` also skips `check_irdrop` and `check_pdn_z`, and GND at 2.6 A is
exactly where IR drop matters (verified in `check_irdrop.py`: entries with
`pdn: false` are skipped). The `check_pdn` "no decoupling capacitors" finding
on a return net is a category error and belongs in
`reports/verify-waivers.json`. Same reasoning keeps `+5V` un-flagged. Kept on
`/SW` only, where it is correct - nothing decouples the switch node by
design. (Precedent: the identical reversal on `sbuck-5v3a` at P8.)

## D8 - Canonical net names: `+VIN`, `/SW`, `+5V`, `GND` (+ `/FB`, `/BST`)

P1 proposed `VIN` and `SW`; both are RENAMED to match the KiCad export
mechanism - power symbols export bare, root-sheet local labels export with
one leading slash. `/FB` and `/BST` are deliberately NOT declared in
`constraints.json` (a `power` entry would put a width rule on the
high-impedance feedback node and pull it into the decoupling inventory).
P4 must run `netlist_audit.py`; a rename surfaces as `missing_net` (error),
and nothing else catches it.

## D9 - ONE FLAT ROOT SHEET; hierarchy rejected

14 electrical parts, 6 nets. A child-sheet label exports as
`/<sheet>/<LABEL>` and silently unhooks every constraints entry spelling it
`/<LABEL>` (the P4 amendment class that cost `lumina-par`). Refdes ranges are
recorded anyway for a future split.

## D10 - `planes[]` declares BOTH F.Cu and B.Cu GND

`planes_gen` REPLACES the layer defaults entirely when `planes[]` is present
(verified in `planes_gen.build_plan`), so declaring only the F.Cu thermal
island would leave the board with no bottom pour - killing the return path,
the `/SW` reference and the radiator at once. Also verified: `planes[]`
entries reject unknown keys INCLUDING the `_note` comment convention, so the
rationale lives in a sibling top-level key instead.

## D11 - Inductor size is set by the part's CURRENT LIMIT, not the load

`buck-inductor-selection`: Isat must beat the part's PEAK CURRENT LIMIT, and
P1 adds a 1.3x factor at 100 C. For a 3 A-class part specified 3.85-5.05 A
that is **~6.6 A**, not 1.3 x the 2.35 A peak. At 15 uH and <= 40 mOhm that
is a 10 x 10 to 12.5 x 12.5 mm component - which is why the outline is what
it is (D5). Choosing the thermally better part therefore costs board area:
the two decisions are coupled, not independent.

## D12 - Sim: exactly ONE candidate, and it is not the converter

Buck SWITCHING is not simulated (no vendor models, by policy). The one
analog fragment with a numeric pass window a generic model card can express
is the **FB divider's DC accuracy against A3's 4.85-5.15 V window**: sweep
the divider with resistor corners (+/-0.1 %) and the FB reference corners
(+/-1.5 %) and require the implied `Vout` to stay inside the window. It
catches the wrong-value class (a 47k where 4.7k belongs) that ERC/DRC/DFM are
structurally blind to. **If P3 lands a fixed-output part, this candidate
disappears and the board has none** - say so rather than inventing a bench.

## D13 - Coverage: the `inrush` class is a LIBRARY hole, not a declaration gap

`knowledge.py --coverage` (run, P2, this workspace) returns 9 of 10 buck
checklist classes `covered` and `inrush` as a `gap`: the only inrush record
is enveloped to `source_kind in [usb, usb-pd, poe]` and this board is
honestly `dc-input`. No dim is undeclared - nothing reads `envelope-unknown`.
Do NOT "fix" this by mis-declaring `source_kind`. Under the mode's seeding
flags (`--maturity-floor proven --research-provisional`) ALL ten classes read
`gap`, because every buck record is `approved` and none is `proven` yet -
that is the mode working as designed, not a malformed `blocks[]`.

## Cost picture for checkpoint 1 (estimate, order_quote does real numbers at P10)

| Item | qty 5 batch |
|---|---|
| PCB, 2L, 40 x 30 mm (inside JLC's 100 x 100 headline tier) | $2.00 headline - **treat as a LOWER BOUND**: the measured estimate-vs-API bias on a 2L board was $2.00 vs $6.20 |
| SMT assembly setup + stencil | $16.00 |
| Extended-part feeders (U1, L1, likely the 0.1 % resistors) | $6-9 |
| Solder joints (~27/board x 5) | ~$0.25 |
| Parts (~$2.20-2.90/board: U1 ~$0.74, L1 ~$0.80-1.50, 6 MLCCs ~$0.40, 2 resistors ~$0.06, 2 terminals ~$0.30) | $11-15 |
| **Batch total** | **~$35-47, i.e. ~$7-9.50/board** |

Dominated by the one-time assembly setup, not by the BOM. **The layer
decision is not a cost decision at this quantity**: 4L would add roughly
$3-9 to the batch (headline $2.00 -> $5.00, same lower-bound caveat).
Through-hole assembly of J1/J2 is an open cost item - hand-soldering after
SMT is the fallback and changes neither the schematic nor the footprint.
