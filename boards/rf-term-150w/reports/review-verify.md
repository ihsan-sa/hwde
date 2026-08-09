# review-verify - rf-term-150w, P8 adversarial review

Fresh-context review. Everything below was verified by running scripts and reading
files in this workspace, not by reading the run's own summaries.

**Verdict: the copper is clean and both waivers are legitimate. Zero errors.**
The defects that remain are in the *documentation and the verification model*, not
in the board. Two of them are worth fixing before this is called done (V1, V2);
the rest are cheap corrections.

`README.md` and `state.json` were being rewritten while I reviewed
(README mtime moved from 03:39 to 04:13:50 mid-pass, changing "~8.1 nH / 9.5x
margin" to "7.21 nH / 10.7x"). All line references below are to the
**04:13:50** version.

---

## Part 1 - waiver audit (the priority). Both waivers CONFIRMED. No hidden defect.

### W-A. `check_silk` / `silk_over_pad` x5 on J1 - CONFIRMED FALSE POSITIVE

The waiver's claim is exactly right, and it is stronger than the waiver states.
Five independent confirmations:

1. **The script never reads the fill token.** `grep -n "fill" check_silk.py`
   returns *nothing*. `_shape_geom()` at
   `.claude/skills/ai-ee/scripts/check_silk.py:161-166` is:
   ```python
   if kind.endswith("rect"):
       s, e = _nums(_kid(node, "start")), _nums(_kid(node, "end"))
       ...
       return Polygon(pts).buffer(w2)
   ```
   Any `fp_rect`/`gr_rect` becomes a solid polygon. Compare the `line` branch two
   lines above, which correctly buffers a `LineString`.
2. **The board's own token says `(fill no)`.**
   `kicad/rf-term-150w.kicad_pcb:624-634` - `fp_rect (start -3.91 -3.91)
   (end 3.91 3.91) (stroke (width 0.12)) (fill no) (layer "F.SilkS")`.
3. **The reported areas are exact whole-pad areas.** Reported 5.2555 mm2 vs the
   exact roundrect(2.3 x 2.3, rratio 0.087) area 5.2556 mm2; reported 3.7986 mm2
   vs pi*1.1^2 = 3.8013 mm2. Only a filled interior yields whole-pad coverage.
4. **The real geometry has 0.20 mm of clearance, not overlap.** Silk half-extent
   3.91, stroke 0.12 -> inner ink edge at 3.85 mm. Nearest pad copper: corner pads
   at (+/-2.55, +/-2.55) r=1.1 reach 3.65 mm -> **0.20 mm clear**. Centre pad
   reaches 1.15 mm -> 2.70 mm clear. There is no overlap anywhere.
5. **KiCad's own DRC agrees, and no silk rule is suppressed.** I re-ran it:
   `kc.py drc ... --parity --all-track-errors --refill` -> `status pass,
   counts {"total": 0}`. The project ignores only `lib_footprint_issues` and
   `lib_footprint_mismatch`; no silkscreen severity is set to ignore.

**Verdict: waiver stands. Do not touch the footprint.** Deforming a correct stock
outline to satisfy a mis-parsing checker would be the actual defect. The tool bug
is real and should be fixed in `check_silk.py` (honour `(fill no)` by returning
`Polygon(pts).exterior.buffer(w2)`); that is a skill-repo fix, not a board fix.

### W-B. `check_return_path` / `corridor_void` x2 on /RF - CONFIRMED STRUCTURAL

I rebuilt the B.Cu pour geometry from the board rather than trusting the report.
The GND pour on B.Cu is **one island, 452.576 mm2, with exactly two interior
voids and nothing else**:

| void | area | centroid | bbox | identity |
|---|---|---|---|---|
| 1 | 14.369 mm2 | (34.585, 24.812) | 3.900 x 3.901 | J1.1 antipad: 2.3 mm roundrect + 0.80 mm rule -> rounded square, half-extent 1.95, exact area 14.35 |
| 2 | 8.064 mm2 | (40.135, 24.812) | 3.200 x 3.201 | C1.2 antipad: 1.6 mm pad + 0.80 mm -> circle r=1.6, exact area 8.042 |

Both centroids land **exactly** on the two /RF through-hole pads
(J1.1 at 34.585/24.8125, C1.2 at 40.135/24.8125). There is no third void, no
split, no unanchored island. F.Cu GND is likewise a single island (340.448 mm2)
with **zero** interiors. `/RF` has no B.Cu copper except the two annular rings
(7.26 mm2 = 5.256 + 2.011, i.e. the pads themselves).

**Verdict: waiver stands.** These voids are the definition of a THT RF launch;
removing them shorts RF to GND.

### Bonus: the three UNWAIVED `corridor_void` warnings are also benign, and nobody said so

`reports/check_return_path.json` carries 3 more findings (warning severity, so
they never reached the waiver file): 623.26 mm2 at (18.74, 22.49), 4.71 mm2 at
(56.31, 28.61), 16.91 mm2 at (38.75, 43.79). All three are **outside the board
outline** (24.285-50.285 x 20.5125-40.5125) - west, east and south respectively -
and all three report `0.00 mm of trace crossing`. They are the return corridor
overhanging the board edge, not missing plane. That is also why the check reports
`corridor_coverage 0.2329`, which reads alarming and is not. Worth one sentence
somewhere so a future reader does not chase 623 mm2 of "missing" plane.

### Strap lands, checked because everything electrical depends on them

R1's cold end reaches GND **only** through the two soldered flange straps, so I
verified the lands independently:

- Two F.Cu SMD pads, `net GND`, 3.5 x 2.0 mm at (32.185, 39.182) and
  (42.385, 39.182) - symmetric at +/-5.10 mm about the tab axis.
- Both are **100% contained** in the F.Cu GND pour union (containment ratio 1.000).
- Stitching vias touch both (nearest-via distance **0.000 mm** to each land, not
  the 0.30 mm the waiver text claims - the waiver is pessimistic, not wrong).
- Both carry `F.Mask` and `F.Paste` (footprint `R_LapPad_T50R0-250-12X.kicad_mod`
  pads at lines 52-63), so they are solderable.
- Clearance to the RF lap pad is 5.10 - 2.50 - 1.75 = **0.85 mm**, above the
  0.80 mm HV floor.
- The flange-side landing zones are on `Dwgs.User` in R1's footprint and fall
  outside the 9.525 mm body block, so a strap has bare flange metal to land on.

Nothing else on the board breaks the return. 79 stitching vias, both pours single
islands, `connect: solid` (decision 57) so J1's four ground legs carry the full
1.732 Arms without thermal-relief spokes.

---

## Part 2 - headline spec claim: CONFIRMED, arithmetic reproduced independently

`R_eff = R + X^2/R` is the right identity (shunt B = X/(R^2+X^2) cancels the
imaginary part, leaving `Y = R/(R^2+X^2)`). I re-derived every number:

| claim | source value | my value | verdict |
|---|---|---|---|
| X at 7.21 nH, 25 MHz | 1.13 ohm | 1.1325 ohm | OK |
| R_eff at +5% corner | 52.524 | 52.5244 | OK |
| RL at +5% corner | 32.2 dB | **32.17 dB** | OK |
| RL at 51.0 ohm | 39.9 dB | 39.87 dB | OK |
| RL at 50.0 ohm | 71.8 dB | 71.82 dB | OK |
| 26 dB cap, R=50 | X <= 16.24 ohm | 16.241 ohm (103.4 nH) | OK |
| 26 dB cap, R=52.5 | X <= 12.07 ohm / 76.9 nH | 12.072 ohm / 76.9 nH | OK |
| margin | 10.7x | 12.072 / 1.1325 = 10.66x | OK |
| null endpoints (2.3 / 31.3 pF) | 0.904 / 13.14 ohm, 5.75 / 83.65 nH | 0.9037 / 13.140, 5.753 / 83.65 | OK |
| "+/-10% of C costs ~7.4 dB" | 7.4 dB | sim `dopt_p10` 7.40641 | OK |
| thermal chain (120 C / 0.633 / 0.212 / 0.421 / 168.5 W / 116 C / 85.5 W / 133 C) | all | all reproduce exactly | OK |

I also validated my method against the run's own ngspice output: at R=52.5,
X=13.0 my closed form gives 25.34 dB and `reff_limit.cir` measures
`s_b_x130 = -25.3366`. The headline is sound.

Gates re-run from scratch, all reproduced:
- `verify_all` -> 11 findings, `{"warning": 4, "error": 7}` - byte-identical to
  `reports/gate-verify.json`.
- `kc.py drc --parity --all-track-errors --refill` -> 0 at all severities.
- `check_irdrop` -> pass (skips /RF as `pdn:false`), correct for a board with no PDN.
- `check_pdn_z` needs `--metadata`; not applicable, no PDN declared. No hole.
- `check_decoupling` SKIPPED ("no decoupling") - correct for a 3-part passive board.

---

## Part 3 - findings

### WARNINGS

**V1. The port shunt-capacitance budget is stale by ~3x, so the trimmer will
almost certainly bottom out - which contradicts the README *and* the stated reason
the router stopped flaring.** (`architecture/blocks.md` s4.3, `README.md:79-89`,
state decision "Router stopped flaring deliberately at 7.21 nH")

`blocks.md` s4.3 budgets **1.30 pF** of port-side parasitic. That table was
computed against a **3.55 mm x 1.1 mm** launch. The as-built launch is
**15.065 mm** of track flaring to **7.34 mm** wide plus a **5.0 x 7.0 mm** lap
pad, and the figure was never re-derived after P7. Recomputing from the board's
own stackup (h=1.53 mm, er=4.5) with the repo's own `impedance.microstrip_z0`:

| element | shunt C |
|---|---|
| /RF tracks, 15.065 mm (0.077 -> 0.409 pF/mm as it flares) | 2.27 pF |
| R1 lap pad, 5.0 x 7.0 mm | 1.50 pF |
| J1.1 pad | 0.25 pF |
| J1 internal + C1 pads (blocks.md's own estimate) | 0.60 pF |
| **total on the net** | **~4.7 pF** |

Nulling 7.21 nH needs **2.883 pF** total. C1's low stop is 1.0 pF, so the whole
parasitic budget is 1.88 pF. A fair lumped-pi split puts ~2.0 pF at the port -
already at or past the stop before the trimmer is touched.

- **Return loss is not at risk.** Bounding case, all 4.7 pF lumped at the port and
  the trimmer hard at 1.0 pF: **39.1 dB at R=50, 31.2 dB at the +5% corner** -
  still 5.2 dB inside a 26 dB spec.
- **The claims are at risk.** `README.md:82-83` "sits just inside the exact-null
  window **with authority in both directions**" is probably false on the bench,
  and `README.md:85-89` / decision 58 justify the entire flare-stopping choice by
  preserving that two-sided null. If the binding constraint is really the port
  capacitance and not the residual L, that rationale collapses.
- `blocks.md` s8 OPEN-3 predicted exactly this for the old 3 pF trimmer and was
  closed when the 1 pF part was adopted - but the parasitic side of the inequality
  was never revisited.

Fix is documentation + a re-derivation, **not copper**: re-run s4.3 against the
as-built geometry, and either soften the README to "the trimmer will sit at or
near its low stop; RL is >= 39 dB there" or adopt blocks.md OPEN-3's build-time
answer (add ~15 nH with a wire loop in series with the tab; costs 0.3 dB).

**V2. The sim gate validates a trimmer that is not on the BOM.** All four benches
set `.param cmax=35e-12` (`tuning_authority.cir:38`, same in `s11_band.cir:49`
and `s11_corners.cir:30`). The delivered C1 is a Johanson 5602, **1-30 pF**. With
`cpad=1.3p` that models a 2.3-36.3 pF part; the real in-circuit range is
2.3-31.3 pF. `cmin=1e-12` happens to match the 5602, `cmax` matches nothing (the
retired BFC was 3-33 pF). Consequences:
- `lnull_hi_nh = 99.64` / `xnull_hi_ohm = 15.65` / `lnull_span_nh = 93.89` are all
  wrong for the shipped part (correct: 83.65 nH / 13.14 ohm / 77.90 nH). The
  README states 83.65 nH correctly - so its tuning table and its sim disagree, and
  only the README is right.
- `README.md:81-82` **">= 26 dB is actually held from 0 nH to ~103 nH"** is
  inherited from the stale bench. With the real 31.3 pF maximum the crossing is at
  **99.0 nH**, not 103.2 nH. I bisected both cases to confirm.
- "sim PASS, 4 benches / 116 bounds" therefore does not cover C1's high stop. The
  board lives at the *low* stop, where `cmin` is correct, so no board risk - but
  the verification claim is overstated and should be re-run with `cmax=30e-12`.

**V3. `README.md:108-110` understates its own argument by 2 dB.** "at the typical
0.1 uH spec limit, X = 15.7 ohm gives 26.6 dB at best and **25.5 dB with a +5 %
part**". At R=52.5, X=15.708: R_eff = 57.200, |G| = 0.06716, **RL = 23.46 dB** -
not 25.5. (26.55 dB at R=50 is correct.) The conclusion is unaffected and in fact
strengthened; the number is simply wrong.

**V4. `README.md:80-81` "over-correction there is worth under 0.4 % reflection" -
actual figure is 0.90 %.** At L=0 with the 2.3 pF floor, |G| = 0.00903, RL =
40.88 dB. The run's own bench agrees: `tuning_authority` measures
`s_l0 = -40.8861`. Harmless (still 15 dB inside spec), but it is a factor of 2.25
against the README's own simulation.

**V5. Acceptance criterion 13 is not met by the delivered BOM.** The criterion
requires each line "in stock at LCSC or DigiKey ... **verified per line with a
stock figure and a date**". `fab/BOM.csv` has no stock column and no date. The
data exists (`parts/5602.json`: "373 in stock", re-confirmed this pass) but was
not carried into the deliverable. Cheap to fix, and it is a numbered criterion.

**V6. Acceptance criterion 7 is unaddressed for R1.** The criterion is "**Every**
component on the port node is rated >= 250 V working, verified against its
datasheet". README covers C1 (250 VDC) and J1 (335 Vrms) and is silent on R1. Per
`parts/T50R0-250-12X.json`, R1's datasheet publishes **no max working voltage at
all** ("MAX VOLTAGE / MAX CURRENT: ABSENT"). The physical risk is nil - a 250 W /
50 ohm part is designed for 111.8 Vrms at rating and sees 86.6 Vrms here - but the
criterion asks for a datasheet verification that cannot be produced, and that
should be stated rather than skipped.

**V7. Two README statements that `requirements.md` explicitly mandates are
missing.** Section 2 of requirements says, verbatim: "No isolation, no protection.
An open or shorted port, or drive above 150 W, is outside the design envelope;
nothing on the board detects or survives it. **README must say so.**" It does not.
The same section asks for the SMA mating-cycle / hot-connect wear note as "a usage
note for the README"; also absent. (The three section-8 hazards F1/F2/F3 and the
BeO warning **are** all present and well written - README s5 covers >30 V,
never-key-unmated, hot surface with cool-down, and do-not-machine-BeO.)

### NOTES (real, low value - listed so they are not re-discovered, not all worth a work order)

- **N1. The 0.032 mm lap gap is false precision.** `README.md:171-173` derives top
  copper at 2.635 mm as "1.6 mm PCB + 35 um copper". JLC's 1.6 mm is a *finished*
  thickness that already includes outer copper and mask, and its tolerance is
  +/-10% = **+/-0.16 mm** - five times the quoted gap, and enough to make it
  slightly negative. Harmless in practice (the tab is 0.127 mm compliant copper and
  will flex), but the README quotes an "ideal flat lap joint" to three decimal
  places with no tolerance statement.
- **N2. The no-machining alternative silently disables a mounting hole.**
  `README.md:186-187` offers "let the J1/C1 end of the board overhang the heatsink
  edge". H3 sits at board-local (2.95, 4.2) - i.e. *in* the J1/C1 end. Overhanging
  leaves only H1 and H2, both on y=13.8, i.e. two screws on one line. Worth a
  half-sentence.
- **N3. C1's lead has to be formed 3.7 mm outward and nothing says so.** The
  catalogue lead exits ~2.29 mm off the case axis (`parts/5602.json` note [4]); the
  footprint puts pad 2 at **6.00 mm** pitch (clearance-driven, correctly - 5.4 mm
  would be the 0.80 mm minimum). Lead *length* is unpublished. R1's tab has a
  "measure at incoming inspection" step; C1's lead has no equivalent.
- **N4. `constraints_drift` (the 4th verify_all warning) is unwaived and
  unexplained.** I diffed the two files: the only substantive difference is that
  `kicad/constraints.json` carries `planes[0..1].connect = "solid"` (decision 57)
  and `architecture/constraints.json` does not. Checks ran against the as-built
  copy. Sync the architecture copy and the warning disappears.
- **N5. `architecture/blocks.md` still describes a 24.0 x 16.0 mm board and
  +/-4.75 mm strap lands.** As-built is 26.0 x 20.0 and +/-5.10 (decision 44, and
  reconciled inside R1's footprint `descr`). blocks.md was never updated.
- **N6.** `README.md:252` says "3 placements", `README.md:259` says "CPL contains
  2 rows". Both pass the <=6 cap; pick one number.
- **N7.** R1's footprint `descr` says the flange strap-landing zones are "centred
  at the same +/-5.10 mm X as the PCB lands so each strap runs straight across the
  gap with no diagonal offset". The `Dwgs.User` rects it actually draws are at
  x 5..7 (centre **6.00**). 0.9 mm of doc-vs-geometry mismatch on the drilling
  template.
- **N8.** `README.md:38-40` "Every clearance on this board is set to 0.80 mm".
  `rf-term-150w.kicad_dru` applies 0.80 mm only through `aiee_hv_122p5v_RF`
  (`condition "A.NetName == '/RF'"`); the baseline floor is 0.127 mm. Correct
  engineering, loose sentence.
- **N9.** R1's lap pad and both strap lands sit **0.33 mm** from `Edge.Cuts`
  against the 0.30 mm rule - 0.03 mm of margin, and JLC's routing tolerance is
  ~+/-0.2 mm, so expect some edge-exposed copper on the real boards. All three are
  hand-soldered lap joints and the nearest opposing metal (flange top, at GND) is
  >= 1.1 mm away in 3D, so this is cosmetic. DRC passes.
- **N10.** Both `ERC 0/0` and `DRC 0/0` are quoted as evidence, and both are blind
  to library mismatches: `lib_symbol_issues`, `lib_symbol_mismatch`,
  `footprint_link_issues`, `lib_footprint_issues` are all `ignore`. Those are set
  by the pipeline itself (`board_init.py:187,194-196`, `schlib.py:571,583,585`),
  not by this board, and `--parity` covers the important case. Already raised by
  the schematic reviewer; repeated only because the gate claims lean on it.
- **N11.** `README.md:247` says the board runs "74-88 C"; `blocks.md` s8 computes
  ~72 C for the insulating-shim case it recommends. 2 C of drift, immaterial.
- **N12.** `fab/CPL.csv` uses absolute board coordinates (X 34.585 / 46.135), not
  origin-relative. Consistent with the gerbers, and the board is hand-built (A5),
  so this is only a note.

### Checked and clean - no finding

- **C1's case is on GND** (pad 1, 7.6 mm annulus / 6.3 mm plated hole, net GND);
  the insulated lead is /RF. The metal an operator touches is at ground potential,
  as required by requirements s8 F1. Confirmed from the board, not the decision log.
- **J1 mating access.** The footprint's courtyard runs to -12 mm in y, so with J1
  at y=24.812 the barrel projects **7.70 mm clear of the north board edge**. A
  mated SMA nut (~9.1 mm across corners, centred on x=34.585) reaches x=39.14; C1's
  7.49 mm body envelope starts at x=42.39. **3.25 mm of clearance** - the P6 move
  recorded in decision 52 did its job.
- **C1 top-adjust access** (criterion 6): tuning slot is on the far face from the
  lead, nothing above it, 17.3 mm of body standing proud of the board. Reachable
  with a cable mated and the board bolted down.
- **Heatsink clearance hole vs placement** (README s4.5): C1's case centre is at
  board-local (21.85, 4.30); a 7 mm hole spans local 18.35-25.35 x 0.80-7.80, which
  fits inside the 26 x 20 outline (0.65 mm from the east edge). Consistent.
- **Shim stack** arithmetic itself: 1.0 + 1.6 + 0.035 = 2.635 vs the datasheet's
  **2.667 mm** tab underside (`parts/T50R0-250-12X.json` note [17], an explicitly
  annotated drawing dimension, not an inference). See N1 for the tolerance caveat.
- **Outline** 24.285-50.285 x 20.5125-40.5125 = exactly **26.0 x 20.0 mm**,
  criterion 10 (30 x 30 HARD) met with 43% of the area.
- **DFM** 1 warning, 6 silk strokes at 0.12 mm vs JLC's 0.15 mm - all six are J1's
  stock-footprint graphics (2 `fp_line` + the 4 sides of the `fp_rect`). README
  s7 documents it accurately.
- **All four blocks.md open items (OPEN-1..5) are closed** in the delivered
  artifacts: trimmer swapped for temperature (OPEN-1), measure-and-trim step
  present (OPEN-2), range documented (OPEN-3, but see V1/V2), hardware in a
  separate BOM.csv table (OPEN-4), strap-loop uncertainty in README s7 (OPEN-5).
- **The insulating-shim reversal is properly recorded**, not an accident: the
  earlier "shims must be METAL" decision is explicitly superseded by the B3
  adoption ("the mounting shims no longer need to be conductive, which frees them
  to be INSULATING").

---

## Waiver recommendation for checkpoint 4

**Approve both waiver groups as written.** Neither hides a defect; I attacked both
independently and they got stronger, not weaker. Two amendments worth making to
`verify-waivers.json` while it is open:

1. The silk waiver's third proof (KiCad DRC finds nothing) is the weakest of the
   three because it is an argument from absence. Lead with the geometry instead:
   the silk ink stops **0.20 mm** short of the nearest pad. That is checkable by
   anyone in ten seconds.
2. The return-path waiver says the nearest stitching via is "0.30 mm from R1's
   west strap land". It is **0.000 mm** - vias touch both lands. Understating your
   own evidence invites a re-litigation.

Also file the `check_silk.py` rect/fill bug against the skill repo. It will
mis-fire on every board that uses a stock KiCad connector footprint.
