# Board review: stm32-blinky (P8 adversarial pass)

Reviewer: verify-reviewer (fresh context). Machine gate state re-verified
independently: verify_all re-run from scratch on the current board = PASS,
all 8 checks 0 violations (return_path, current, decoupling, diffpair,
creepage, thermal, silk, pdn). DRC routed 0/0. What follows is what the
scripts cannot see.

Renders referenced (made this pass, reports/renders/):
`stm32-blinky_top.png`, `stm32-blinky_bottom.png`, `stm32-blinky_iso.png`,
crops `crop_j1_d1.png`, `crop_c5_tant.png`, `crop_d2_j2.png`,
`crop_u1_cluster.png`, `crop_xtal.png`.

---

## ERROR 1 - J1 power input has no polarity legend on silk (requirements miss)

`requirements.md` sec 2 and `architecture/blocks.md` both promise the 5 V
input "polarity marked on silkscreen" (J1 pin 1 = +5 V, pin 2 = GND). The
as-built board has NO text or +/- legend anywhere: silk carries refdes only
(there is not a single gr_text on the board). What exists at J1 is a pin-1
dot and a square pad (see `crop_j1_d1.png`) - and the dot sits on the header
body outline, so after the header is soldered the plastic covers it. Post
assembly the top side shows nothing but "J1"; the square pad is visible only
from the bottom.

Consequence: the unkeyed 2-pin input can be plugged backwards with no
on-board hint. D1 (series SS34) prevents damage - reversed input just does
not conduct - but the user gets a dead board and no way to know why or which
way is right without opening the design files. This is the board's primary
human interface and an explicit requirements promise. Fix is two silk texts
("5V", "GND" or "+", "-") next to the holes, outside the header body. Must
fix before fab; there is ample empty silk area (left region is empty).

## WARNING 1 - J2 SWD pins unlabeled (architecture promise miss)

`blocks.md` promises "Canonical pin order (silk-labeled): 1 = SWDIO,
2 = SWCLK, 3 = 3V3, 4 = GND". Electrical order verified correct from the
netlist (pads: SWDIO/SWCLK/+3V3/GND, U1 PA13/PA14 to pins 1/2). But there
are no labels - only a pin-1 square cell (`crop_d2_j2.png`) which the header
body covers after assembly. ST-Link clones are wired pin-by-pin; swapping
3V3/GND shorts the debugger's 3.3 V rail to ground. Same trivial fix as
ERROR 1 (four small silk texts below the header row - the area under J2 is
clear). Strongly recommend fixing together with ERROR 1; warning rather
than error only because requirements.md itself demands the ORDER (met), the
labels are an architecture-level promise.

## WARNING 2 - refdes association ambiguity (cap cluster + C3-under-J2)

Confirmed the P6-flagged issue on `crop_u1_cluster.png` and
`crop_d2_j2.png`; judged as follows:

- "C11" text sits directly above R1's body; "C1" text below-left of R1;
  "C7"/"C8" labels float between parts they do not touch. Among these
  0603s are four DIFFERENT cap values (22 pF, 10 nF, 100 nF, 1 uF) plus a
  1 k resistor - a hand-rework or debug probe guided by silk has a real
  chance of landing on the wrong part.
- "C3" text renders directly under J2 pads 3-4 and reads like a header
  label (its own body is 3.6 mm away). Mildly reinforces the J2 labeling
  problem: someone may read "C3" while counting SWD pins.

Assembly itself is CPL-driven, so production risk is nil; consequence is
limited to bench rework/debug confusion. WAIVER RECOMMENDED for rev A -
but since ERROR 1 forces a silk edit session anyway, nudging these labels
onto their parts at the same time costs minutes.

## WARNING 3 - BOM of record drifted from the board (100 nF qty, stale roles)

`parts/parts.json` (LCSC BOM of record) lists C14663 100 nF at
`qty_per_board: 5` with role "C1-C3 VDD + C4 VDDA 100nF, C9 NRST (5/board)".
The board mounts FOUR 100 nF (C1, C2, C3, C9): the schematic-review fix that
added the DS5319 VDDA pair made C4 = 1 uF (C15849) and C10 = 10 nF (C57112),
and the 100 nF line was never decremented. The 1 uF / 10 nF entries carry no
refdes in their roles. Anything in P9 that quotes or orders from parts.json
over-counts one part line and cannot map refdes for two others. One-line
fix before ordering. (Values/nets on the board itself verified correct:
VDDA pin 9 gets 1 uF + 10 nF, three VDD pairs get 100 nF, NRST gets 100 nF.)

## WARNING 4 - stale reports/verify_all.json contradicts the gate

`reports/verify_all.json` (written 00:31, before commit e827d25's
check_pdn parse fix + /VIN width-only opt-out) still records 1 error /
2 warnings, while `reports/gate-verify.json` says pass 0/0. An auditor at
checkpoint 4 reading the named summary artifact sees a failing state that
no longer exists. Re-running verify_all (done this review, to scratchpad)
yields PASS with 0 violations - refresh the committed artifact.

---

## Warnings triage (every prior verify_all finding gets a verdict)

The 00:31 verify_all's three findings, against the current board:

1. ERROR "power rail /VIN has no decoupling capacitors" - JUSTIFIED
   OPT-OUT (now `"pdn": false` in constraints.json). /VIN is the 4 mm raw
   stub from J1.1 to D1's anode. A capacitor there would sit in front of
   the reverse-protection diode: useless for the LDO (C6 10 uF sits on the
   protected +5V node 1.9 mm from U2's input, verified) and wrong for a
   polarized part (it would see reverse voltage in the fault case the
   diode exists for). Endorse the opt-out as permanently correct, not a
   convenience waiver.
2. WARNING "+5V ... no bulk reservoir; only ceramics" - PARSER ARTIFACT,
   RESOLVED. Old check_pdn could not parse "10uF 25V X5R"-style values
   (its own report said total_uf 0.0 with caps present). Post-fix run:
   +5V bulk_count 1, 10.0 uF total (C6). No board change was needed or made.
3. WARNING "+3V3 ... no bulk reservoir" - same artifact, RESOLVED. Post-fix:
   7 caps, bulk_count 3, 33.3 uF total (C5 = 22 uF tantalum, ESR-matched to
   the AMS1117 per the settled user decision; C11 = 10 uF; C2/C3/C1 100 nF;
   VDDA pair). Real bulk was always present.

Fresh run has zero warnings and zero skipped checks: diff_pairs is an
explicit empty list (no pairs exist - correct), thermal no-ops by
documented budget (77 mW worst on U2, SOT-223 - trivially fine), creepage
trivial at 5 V. No skipped-check holes in the verify suite. DFM/fab checks
(dfm_check, fab export) are P9 scope and have NOT run yet - `fab/` is
empty; that hole belongs to the next phase, not this gate.

## Hunted and found clean (visual + cross-artifact)

- Polarity marks, decoded from silk geometry and checked against nets, all
  CORRECT and all visible after assembly: D1 cathode band + end brackets on
  the +5V side (brackets outside the SMA body); C5 tantalum "+" brackets on
  the pad-1/+3V3 end, outside the CASE-B body; D2 LED cathode chevron+bar
  on the /LED (PC13) end, outside the 0805 body (`crop_j1_d1.png`,
  `crop_c5_tant.png`, `crop_d2_j2.png`). U1 pin-1 dot clear of the LQFP body.
- Netlist vs intent: AMS1117 pinout (GND/VOUT/VIN/tab=VOUT) correct; D1 in
  series with cathode toward the LDO (conducts forward, blocks reverse);
  LED chain +3V3 -> R1 1k -> anode, cathode -> PC13 (active-low sink,
  ~1.3 mA, honors the PC13 3 mA / no-source limit); BOOT0 via R2 10k to
  GND; VBAT tied to +3V3; NRST 100 nF; PB2/BOOT1 floating (don't-care with
  BOOT0=0); all 3 VDD pairs + VDDA/VSSA mapped; SWD order per spec. Every
  requirements interface (5V in, SWD, LED) and every architecture block is
  present. No reset button / BOOT0 jumper / power LED / mounting holes -
  matches the user-confirmed minimal set.
- Connector reality: J1 3.5 mm from the left edge, J2 within 3.3 mm of the
  right edge, both vertical THT male headers with open space around and
  below - hand-solder access trivial (bottom face is bare pour,
  `stm32-blinky_bottom.png`), jumper access unobstructed, no tall parts
  anywhere near. Board is enclosureless by requirement, so no reach issues.
- EMI/robustness: no RF, no switcher on board (antenna/keepout hunt: N/A).
  Crystal Y1 is mid-board, 6.9 mm from the nearest edge, over continuous
  B.Cu GND pour; return-path check green. One deliberate oddity reviewed:
  C7 (OSC_IN load cap) sits at the MCU end, 12.6 mm from Y1 pad 1
  (`crop_xtal.png`) while C8 hugs Y1 pad 2 - unconventional, but the
  8 MHz Pierce loop rides a solid pour, the HC-49S itself is 11.5 mm long,
  and F103 HSE drive has wide margin. ACCEPT as-is (no board change);
  noting it so nobody "fixes" it into a worse route later.
- Bottom copper: near-solid GND pour, exactly one ~12 mm diagonal signal
  excursion plus one stub in the J2/D2 quadrant - nowhere near the
  oscillator or the LDO loop; stitching vias distributed. Clean.
- Assembly: single-sided top SMT (economy PCBA compatible), two THT headers
  hand-solder per settled plan. No fiducials - acceptable: JLC economy
  panelizes small boards on their own rails with their own fiducials; note
  only.
- Settled items verified as-built and NOT re-litigated: SS34 drop/headroom
  math (power_tree), 22 uF tantalum on LDO output present with correct
  polarity, minimal feature set, empty bottom-left region (intentional
  spread on the fixed 50x40 outline). One doc nit: blocks.md/decisions.md
  still say "target outline 35 x 30 mm"; the delivered board is the full
  50 x 40 (within the hard limit, zero JLC cost impact at qty 5). Update
  the doc line or accept the drift - no board action.

## Waiver recommendations (human decides at checkpoint 4)

- WARNING 2 (refdes ambiguity): waive for rev A if the silk session from
  ERROR 1 is not extended to labels - rework-only consequence.
- /VIN pdn:false opt-out: endorse permanently (see triage 1) - it is the
  electrically correct treatment, not a suppression.
- Architecture outline text 35x30 vs built 50x40: accept or one-line doc fix.

NOT waivable in this reviewer's judgment: ERROR 1 (J1 polarity legend) -
explicit requirements promise, primary user interface, zero-cost fix.

## Open (could not judge from renders alone)

- No 3D models render in the iso view (bare footprints), so assembled-body
  absurdities (header plastic orientation, crystal can height vs nothing)
  could not be visually confirmed; at this part mix the residual risk is
  negligible.
- fp_verify overlay reports exist for 6 footprints but were skipped for D1
  (SS34/SMA) and Y1 (HC-49S). Mitigated here by manual geometry decode
  (D1 band-vs-net correct; Y1 pad span LS 12.7 matches HC-49S-SMD), but the
  physical-part-vs-footprint pad-1 convention for D1 rests on the LCSC
  footprint being band-on-pad-1, which lib_pull pulled but no overlay
  confirmed.
