# P8 Verification digest - LUMINA carrier (LUM-CAR-A)

Artifacts: `reports/checks/*.json` (verify_all, 8 checks), `reports/render_silk/*.png`,
`work/p8/creepage_adjudication.json`, `work/p8/ipc_adjudicate.json`,
`work/p8/silk/refdes_{before,after}.json`, `work/p8/{tapcreep,hvpwr,silk}/`,
`reports/review-board.{md,json}`.

- **`drc_routed` re-confirmed 0 errors / 0 warnings** after every single copper and silk
  edit in this phase, and again at H4. It never left 0/0.
- **`verify` gate: 118 findings** (114 error-severity + 4 warnings).
  `check_current` 94, `check_creepage` 11, `check_return_path` 11 (9 error + 2 warning),
  `check_decoupling` 2 (both warning). **`check_diffpair`, `check_thermal`, `check_silk`
  and `check_pdn` are all 0.**

## Four real defects fixed, none of which any gate reported

1. **A-side PoE tap differential creepage, 0.3292 -> 0.6502 mm** (F.Cu; 0.6524 mm on the
   other three layers). `/poe/POE_TAP_A1` and `/poe/POE_TAP_A2` are the two AC inputs of
   bridge D2, so the full line potential sits between them - but both are declared 57 V,
   `check_creepage` computes `dv = 0`, and the pair is **never evaluated**. Found by hand.
   Fixed by moving both transition vias (0.6 -> 0.5 mm, annular 0.1 mm = the board and JLC
   minimum) to a grid-searched optimum that maximises the **worst** margin rather than the
   headline gap - the first optimum bought a 0.726 mm tap gap while leaving +0.005 mm to
   SHIELD, i.e. robbed one 57 V gap to pay another.
2. **A SECOND tap pair at 0.5500 mm**, on the same two nets, hidden behind the first and only
   visible after it was fixed. Also fixed.
3. **Four J1 SHIELD-to-tap creepage errors**, previously classified as package-internal but
   actually routed copper: 0.213 -> 0.6390, 0.2142 -> 0.6388, 0.220 -> 1.7700,
   0.2129 -> 0.6620 mm, by replacing a 39-segment SHIELD staircase with a 6-segment polyline
   at the analytic optimum. The corridor has **0.0778 mm of total slack**, so the topology was
   forced, not chosen. Re-swept: 0 of 31 SHIELD items now under 0.600 mm.
4. **Two 0.200 mm power-trunk segments now 0.500 mm** (V48_RAW, 1.0 A). All five candidates
   were first proven to be **bridges** in their net's connectivity graph, so each really does
   carry the whole rail - no parallelism was assumed.

A new `.kicad_dru` rule, **`poe_tap_differential_pair` (0.60 mm)**, now holds defect 1 from
recurring, because `check_creepage` structurally cannot. It was **proven live** rather than
assumed: raised to 0.90 mm it fires 17 times and independently reports `actual 0.6502` /
`0.6524 mm`, confirming the fix with a second oracle.

## Silkscreen legibility (owner requirement) - 95 mis-attributed labels -> 3

| metric | before | after |
|---|---|---|
| median refdes offset | 4.079 mm | **1.600 mm** |
| >1 mm beyond own pad extent (excl. H1-H5) | 95 | **3** |
| >1.5 mm beyond own pad extent | 86 | **1** |
| median beyond-extent | 2.769 mm | **0.119 mm** |
| visible refdes | 116/116 | 116/116 |

Root cause was a **library** defect, not the P6 sweep alone: `easyeda2kicad` emits every
footprint's Reference at a blanket `(0, -4.0)` mm regardless of part size, and the large
packages instead derive theirs from the silk outline (WROOM-1 at -12.955 mm). The library was
normalized centrally (31/31 footprints, idempotent, `lib/EDITS.md` edit 8); the board needed
111 `move_text` ops because it carries its own copies. Applied in 5 batches, DRC-verified
after each. Non-regression proven by snapshot diff: 3294 tracks, 359 vias, 8 zones, every pad,
every footprint silk and every `value` field byte-identical; 0 footprints moved.
**Attribution beat closeness on 17 refs**; 110 of 111 have their own part as nearest.
One residual: **C35 at 3.861 mm**, boxed in on four sides, whose only wide-enough channel is
C34's only attributable slot - a P6 placement consequence, not a silk problem.

## The measurement lesson of this phase

**`check_creepage` cannot express a coated board.** It hardcodes IPC-2221 rows B2 (external
**uncoated**) and B1 only. Re-adjudicated per item type against the correct rows - B4 for a
mask-covered conductor (**0.13 mm** at 51-100 V), A6 for an exposed land (**0.50 mm**, and
0.80 mm at 101-150 V per IPC 6.3.4), B1 for inner layers - the count goes **11 -> 10**, and the
one that clears is the largest: `/poe/POE_TAP_A2 <-> /poe/LED_Y_A`, whose **217 pairs** under
0.600 mm are all trace-to-trace under soldermask and pass B4 with +0.0731 mm. Two bounded fixer
attempts and one applied-then-retracted edit were spent on a requirement that does not apply to
that geometry. The remaining 10 are every one of them a pad inside a single package
(U1 x7, U22 x2, U20 x1) and fail every applicable row, because 0.200 mm is the inter-lead gap
of the SOIC-8 that TI ships.

## Also worth carrying forward

`gate dfm` already reads **194 errors, 189 of them "trace width 0.1000 mm below JLC minimum
0.1016 mm"**. Root cause is a configuration defect from P5: `board_init` writes
`min_track_width: 0.1` - below **every** JLC profile - and this board's hand-written
`.kicad_dru` contains none of `rules_gen`'s generated floors. So `drc_routed` 0/0 currently
does **not** imply fabricable, and the gap is 1.6 micrometres. This is a P9 item, reported not
fixed.
