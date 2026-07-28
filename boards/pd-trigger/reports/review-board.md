# Board review (P8 adversarial) - pd-trigger

Scope: hunt for what the green gates cannot see. Board `kicad/pd-trigger.kicad_pcb`
(routed, drc_routed 0/0 err/warn, verify 8/8 checks 0 findings). Methods: renders
(`reports/render_routed/`), raw-copper rasters from the board file (validated against
plane_repair's own area figure: 1322 vs 1307 mm2), pad/segment/via extraction, and the
pipeline's own IPC-2152 model (`check_current.required_width_mm`) for every neck.
Settled items (fuse policy, pour legality, netclass split, LED ceiling, DIP choice) not
re-opened.

## Verdict summary

The 5 A FORWARD path is genuinely good: solid pour fan-in at J1, one 3.0 mm F.Cu trunk
(model: 4 C rise at 5 A), zero VBUS vias, taps compliant. The board's two real problems
are (1) the 5 A RETURN transition at J1 - the architecture's own ">= 10 vias at J1's
GND pads" substitute for the undeclared-GND blind spot was never implemented; what is
there is two 0.2 mm trace necks and a single signal via, and (2) the entire functional
silkscreen package promised by the architecture (profile table, AUX 1A MAX, PD-only,
LED legends, polarity) does not exist - the board file contains zero gr_text; the only
text anywhere is refdes. check_silk gates legibility of existing silk only; nothing
machine-checks silk content, and constraints.json carries no silk key.

## Findings (worst first)

### E1 - 5 A return chokes at J1's GND contact pads (error, checker-blind by design D7)

The 4 GND cable contacts land on two merged SMD pads (F.Cu only): A1-B12 at
(17.63,39.31) and B1-A12 at (17.63,45.71), nominally 2.5 A each at the 5 A rating.
Their ONLY copper into the B.Cu return pour:

- A1-B12 (top): a 0.2 mm wide, 2.7 mm long F.Cu chain (3 segments) into shell pad 1's
  THT barrel, plus one 0.6/0.3 via whose annulus grazes the pad corner by ~0.05 mm
  (etch-tolerance-level). 0.2 mm at 2 oz = 0.80 A capacity at 10 C rise (pipeline
  model); at 2.5 A the same model gives ~133 C rise (short-neck heatsinking will
  moderate this, but it is a >3x overcurrent on the model's own terms). ~13.6 squares
  = 3.3 mohm.
- B1-A12 (bottom): a 0.2 mm x 1.3 mm trace into ONE 0.6/0.3 via. The board's own via
  budget (constraints via_amps 0.5) says 2.5 A needs 5 vias; there is 1. Shell pad 4
  sits 0.32 mm away but is NOT connected on F.Cu - its copper does not help.

Architecture D7/power_tree structural requirement ">= 10 vias at J1's GND pads" (the
stated substitute for keeping GND out of power[] so check_current stays quiet): not
delivered. DRC cannot see it (0.2 mm is netclass-legal), check_current cannot see it
(GND undeclared), check_return_path no-ops (no high_speed key). Failure mode: sustained
5 A at any profile heats the two necks far past the 10 C design intent; long-term
trace/joint fatigue, intermittent ground, and full return current cascading onto the
surviving 0.2 mm chain. Fix is cheap at P9: an F.Cu GND spandrel bonding each contact
pad to its shell pad (the VBUS pour top edge is at y 39.7 - the strip above it, and the
strip x < 17.2 plus the region south of y 46, are free) plus 4-5 vias per side.

### E2 - Safety/waiver silk markings absent (error, promised artifact)

Board-wide gr_text count is ZERO; B.SilkS carries nothing at all (both B.SilkS
references in the file are the stackup layer table). Missing, each one a written
promise:

- `AUX 1A MAX` + `V+`/`GND` at J3 (P0 answer 4 "silk-marked", V10). F1 makes overload
  safe-by-hardware, but polarity of the 2-pin aux header is unmarked.
- `PD SOURCES ONLY` (ERC waiver W1's standing condition: "goes on B.SilkS + order
  docs"). The waiver's silk half is currently unfulfilled.
- J2 screw-terminal polarity. Trunk lands on J2 pad 1 = the LOWER screw (board-bottom
  side); nothing anywhere tells the bench user which screw is V+. Reverse-wiring a
  load on a 100 W output is the single easiest field mistake this board can cause.

### E3 - User-interface silk absent (error, promised artifact)

- The five-row profile table on B.SilkS - D3 calls silk "the user interface" and
  specifies the table verbatim; the bottom is a clean pour with room. Without it the
  ON/OFF-to-voltage map exists only off-board; a user WILL set 9 V expecting 12 V by
  trial and error. (Fail-safe floor: any wrong guess >= the 5 V fallback, and OFF-fail
  = 5 V - the mistake is bounded but real.)
- LED legends `PWR` / `5V ONLY` / `PROFILE OK` (D4/V10): the render shows refdes
  D3/D5/D6 only. The entire P0-answer-6 "visible fallback indication" scheme is mute
  without the words - a lit red LED labeled "D5" indicates nothing.
- Cable disclaimer "20V @ 5A needs a 5A e-marked cable and a 100W source" (V10 lists
  it as silk; power_tree s7 allows documentation - at minimum it must reach the order
  docs at P9/P10, which do not exist yet; fab/ is empty).
- PRESENT and correct: SW1's own footprint prints `ON` + `1 2 3` (the compact F.SilkS
  marker D3 asked for) - confirmed on the top render.

### W1 - J1 mouth recessed ~0.4-0.5 mm behind the board edge (warning, flagged at P6)

Courtyard/silk front edge x = 10.18 vs board edge x = 9.8. USB-C receptacles are
normally flush-to-overhanging; a recessed mouth lets thick/molded plug overmolds butt
the board edge and hold the plug fractionally short of latch - intermittent CC, no PD,
"works with some cables". On a bare bench board with arbitrary cables this is a real
annoyance risk. Fix: nudge J1 -x 0.5-1.0 mm at P9 (pour edge follows; nothing else in
that corridor), or accept and note in order docs.

### W2 - Outline 48 x 30 mm exceeds the architecture's hard ceiling (warning, drift)

Edge.Cuts = (9.8,27.51)-(57.8,57.51) = 48 x 30 mm. D9: nominal 45 x 25, "hard ceiling
48 x 28 mm"; 30 mm violates D9's own ceiling by 2 mm even though it equals P0 answer
5's literal +20 % (40x25 -> 48x30, +44 % area vs the brief's target). No digest
discloses the growth past D9. Consequence is cost/footprint only, but it must be
disclosed to the user at the checkpoint rather than discovered.

### A1 - J2 GND pad ties to the return pour through 4 thermal spokes (advisory)

J2 pad 2 (THT, 2.4 mm pad / 1.6 mm drill) connects via 4 x 0.5 mm diagonal spokes =
2.0 mm total at 2 oz -> model 8 C rise at 5 A. Legal and functional, but these are the
most-loaded copper necks on the whole return after E1, at a hand-soldered joint.
Recommend a solid-connect override (or a short fat GND strap) at P9; zero cost.
(Verified all 4 spokes present; the VBUS pad 1 island below it is barrel-tied, normal.)

### A2 - F1's VBUS feed branch is 18.3 mm long (advisory, V8 letter-violation)

V8/D8 wanted all five VBUS taps hugging the run with 2-3 mm stubs. D1, C1A, C1B, C2,
R14 comply; F1's feed runs 8.4 + 6.5 + 3.4 mm at 1.75 mm width to the top-left corner.
Width-compliant (V8's actual purpose), carries <= 1 A in service; only cost is ~30 mm2
of extra always-live 20 V copper. No action needed; recorded as drift.

### A3 - Floating 0.65 mm2 GND sliver at (20.0, 28.5) (advisory, cleanup)

plane_repair's own dead-island fact (0 anchors), between J3/SW1 clearances. Cosmetic /
minor DFM nit; remove at P9 cleanup or accept.

### A4 - /VAUX at PPTC max-non-trip current (advisory)

/VAUX routes at 0.3 mm (required 0.25 at the declared 1.0 A -> 7 C). F1's worst
sustained NON-trip current is ~1.8 A -> model 27 C rise on those runs until/unless the
PPTC trips. Bounded, no damage threshold approached (70-80 C copper on a 20 V node);
acceptable. Recorded so nobody "fixes" it blind later.

## Disclosed-item ruling (hunt item 1): C1B pour channels - ACCEPTED

P7's disclosure: C1B's tap reaches the VBUS pour bottom lobe through two pour channels
1.11 + 1.25 mm wide (between D1's GND-pad keepouts and the stitch-via keepouts) -
checker-blind because zones are exempt from track width rules. Judgment with numbers:

- The channels are NOT in series with the 5 A path (trunk exits the pour at y 43.5;
  C1B hangs at y 51, a dead-end stub). Verified geometrically.
- Worst realistic channel current: PD transition slew (30 mV/us x 10 uF) = 0.3 A for
  ~0.5 ms -> model rise ~1 C on the 1.11 mm channel alone (3.49 A capacity at 10 C).
  Hot-plug edge cases are adiabatic (trivial I2t). No converter on board -> no
  sustained ripple duty.
- Combined 2.36 mm >= the net's own 1.75 mm rule anyway.

Acceptable for a bulk cap's duty by >= 10x margin. Recommend recording as a standing
waiver so P9's DFM pass does not re-litigate it.

## Hunt-list verdicts not already covered

- 5 A path on render: J1 fan-in solid (pour wraps both merged VBUS pads, solid-connect,
  CC-pad ladder slots stay left of x 18.35, > 4 mm continuous corridor); 3.0 mm trunk
  continuous (20,43.5)->(52.2,43.5) straight into J2 pad 1; 0 VBUS vias. PASS.
- GND under trunk: B.Cu pour solid and unslotted beneath the entire trunk shadow
  (verified on raster; one connected component, 1322 mm2). The 9 B.Cu signal crossings
  (CC1 x2, CC2 x2, /VIND x1, /VAUX x4) all sit peripheral - CC pair slots the J1 fan
  region where the funnel feeds around them from N and S; /VIND slot is 7 mm north of
  J2's GND pad; /VAUX slots the far top-left corner. None slot the return. PASS
  (E1 is the return's real problem, not the crossings).
- TVS D1: inside the pour 3.2-3.6 mm from J1's VBUS pads, first element on the net; GND
  side = 3 short 0.2/0.3 mm traces into 3 vias into solid pour. Est. clamp-loop L well
  under 10 nH; at the design threat's di/dt (~5 A/us cable-spike class) that is tens of
  mV on top of a 28 V clamp - negligible. Surge I2t through 3 vias: adiabatic, fine.
  PASS. Bulk at entry: C1A/C2 tap the trunk 2.5-6.5 mm from the pour, C1B in the pour;
  20 uF total < 100 uF cSnkBulkPd. PASS.
- User-facing reality: DIP reachable at top edge, actuators clear; J2 wire entry faces
  off-board (P6 WRL-verified rotation); J3 pluggable at top-left; LED row visible at
  bottom edge. All PASS mechanically - every labeling promise FAILS (E2/E3).
- Waiver soundness: W1 (DP/DM short at chip) re-verified in copper - U1's DP/DM are
  net /BC12_DIS, J1's A6/A7/B6/B7 pads unconnected; hardware-safer than connector
  wiring, no downstream copper effect; waiver stands but its silk condition is
  unfulfilled (E2). W2 (VDD worst corner) unaffected by routing; R2A+R2B = 2x 510R
  1206 in series confirmed placed 25 mm from U1 (>= 8 mm rule met); bring-up
  measurement stands. U1 pad 11 (baseplate, "pin 0" trap V11) confirmed net GND with
  3 vias under it.
- Warnings triage: the machine record contains zero warnings anywhere (ERC 0/0, DRC
  0/0 err+warn, verify 8 checks 0 findings). Only tool-emitted advisories: plane_repair
  dead island (A3, triaged) and stitch_vias relocations (benign, verified placed).
  route completion 1.0 at final; the 0.956 probe figure is historical.

## Open (could not judge from artifacts)

1. SW1 slide direction: whether the physical actuator closes toward the footprint's
   "ON" label on this exact SHOU HAN part cannot be proven from the board file. Wrong
   direction inverts the (missing) table's ON column. Fail-safe floor exists (open =
   5 V), but add to bring-up: verify one non-5 V profile before trusting the map.
2. Real steady-state temperature of the E1 necks (IPC long-trace model overstates
   short heatsunk necks; could be 30-60 C rise instead of 133 C). Irrelevant if E1 is
   fixed - the fix is minutes of work.
3. Order-doc promises (PD-only, e-marked-cable disclaimer, Q1 pinout buzz-out, VDD
   measurement) - P9/P10 artifacts do not exist yet; carried forward, not judgeable.
