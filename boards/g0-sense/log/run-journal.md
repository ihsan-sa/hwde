# g0-sense run journal

## 2026-08-27 - iteration 1 - P0 Intake COMPLETE
- Env: `check_env.py` PASS (KiCad 10.0.5, Java 25, Freerouting 2.2.4, ngspice,
  pdflatex all resolved). Router: task -> verb `full-run`, human_hold 3.
- Workspace initialised at `boards/g0-sense` (state.json v2, standard subdirs).
- P0: requirements-analyst (fable/high) wrote `requirements.md`;
  `check_requirements.py` PASS, 0 violations. No mode token -> design normally,
  product scope, size ~35x25 mm SOFT (does not bind at P5).
- Gates: none due at P0.
- Decisions taken on the owner's behalf (5, all `unattended default:`):
  indoor 0-40 C environment; 100 mA Qwiic downstream reserve; no hard cost cap;
  0.1 in SWD/UART headers ship unpopulated (JLC economy PCBA is SMT-only);
  ~35x25 mm confirmed soft, no HARD outline cap.
- Safety: all section-8 flags NOT APPLICABLE with brief evidence - nothing
  provisional, nothing to escalate.
- Open issues: none. Next: P1 research roster, then P2 architecture + coverage.

## 2026-08-27 ~06:55Z - SUPERVISOR NOTE (host-side, not the orchestrator)
- An Xvfb display now runs in this container on :99 and `scripts/lib/env.py`
  exports DISPLAY=:99 to every child when unset: KiCad's SWIG Specctra
  export/import (`route_swig` in route_auto) refuses to run without an X display
  on Linux. Nothing to do; if a script still reports "Unable to access the X
  Display", run it with `DISPLAY=:99` and journal it.
- KiCad 10.0.5 (this container; the repo was built on 10.0.3) reports
  `hole_clearance` errors between a footprint's OWN pads and its NPTH holes
  (seen on a USB-C receptacle: 0.18-0.21 mm vs the 0.25 mm board rule). Expect
  it on J1 at drc_routed/verify. Treat it like any finding: check the
  connector's real geometry against JLC capability (`jlc_capabilities.yaml`)
  and waive with evidence if the vendor footprint is what it is - do not move
  pads to satisfy it.
- The full pytest suite under 10.0.5 shows small DRC/ERC count deltas vs the
  10.0.3-recorded fixtures (not Linux bugs). If a generated schematic fails to
  load in kicad-cli ("Failed to load schematic", rc=3), that is under
  investigation host-side; journal exactly which file and which step produced
  it and continue with what you can.

## 2026-08-27 - iteration 1 - P1 Research COMPLETE
- 8 P1 agents ran (4 component-scouts, 1 interface-spec, 2 reference-design,
  then power-architect on their output). All wrote research/ fragments;
  constraints_lint exit 0 on both JSON fragments that carry schema shapes.
- Gates: none due at P1.
- Biggest findings: CC-blind USB-C sink is capped at 500 mA entitlement and
  <=10 uF at the receptacle; AMS1117-3.3 SOT-223 wins the LDO on thermals
  (Tj 71-86 C vs 134 C for SOT-23-5) and needs a tantalum-class 22 uF output
  cap; STM32G030 TSSOP-20 needs NO BOOT0 strap (pin 19 is SWCLK, factory
  option bits boot main flash); Sensirion forbids board wash on SHT4x.
- 7 decisions taken on the owner's behalf (all `unattended default:`): LDO part
  + governing 0.51 W design point; TVS sub-6V clamp requirement dropped as an
  over-tight derived spec (nothing on VBUS is 6 V-rated); no series reverse-
  polarity element (it would eat the whole dropout margin); USB-C THT shield
  legs accepted - verified on jlcpcb.com that C165948 is Assembly Process SMT
  and Economic-tier supported; SHT4x heater budgeted; NRST button Basic-first;
  LED colours green/red.
- Env gotcha: jlcpcb.com/parts/componentSearch returns 0 results when fetched
  headlessly; the per-part URL jlcpcb.com/partdetail/<vendor-slug>/<LCSC> works.
- Open issues: none. Next: P2 architect + the P2 coverage contract.

## 2026-08-27 ~07:05Z - SUPERVISOR NOTE 2 (host-side)
- FIXED before P4: KiCad 10.0.5 stock symbol libraries (format 20251024) carry
  `(property private "KLC_..." "note")` entries that kicad-sch-api 0.5.6
  mis-serialises, so every generated schematic using such a stock symbol
  (e.g. Device:Crystal_GND24; 419 of them across the libs) failed to load in
  kicad-cli ("Failed to load schematic", exit 3). `schem_refdes.strip_private_properties`
  now runs after every ksa save (schlib.Sheet.save + write_placements). If ERC
  still reports exit 3 on a schematic, journal the symbol names in its
  lib_symbols and strip `(property "private" ...` blocks by hand.

## 2026-08-27 - iteration 1 - P2 Architecture + H1 COMPLETE
- architect (fable/high) produced the full architecture/ package;
  constraints_lint exit 0. 4 blocks, JLC2313_1.6 2L stackup, 2 sheets.
- Gates: none due at P2. Coverage P2 FIRST run: 4 slots / 4 GAP (no checklist
  existed for usbc-sink, ldo, mcu or sht4x). After research: 0 gap,
  4 provisional, 1 draft_unverified.
- Research leg: 4 tasks opened (2 of the 6 per-run cap remain for P3),
  16 sources quarantined, 4 checklists + 23 records written by 4 researchers,
  ruled by 4 FRESH second readers. 6 refuted. 5 repaired from ledger pages and
  re-read to verified (the NRST record needed 3 cycles). Final 22/23 verified.
- Decisions on the owner's behalf this phase (2 more, both forced by the
  second reads, both AGAINST the architect's original plan):
  * I2C pull-ups 2.2k -> 1.5k. UM10204 Eq 1 at tr=300 ns: Rp(max)=354/Cb[pF]
    kOhm, so 1.77k at 200 pF - 2.2k needed Cb <= 161 pF and missed Fast-mode
    rise time on a cabled Qwiic bus. 1.5k holds to 236 pF, clears both floors.
  * BOOT0 no-strap -> populated 10k pull-down on PA14/pin 19. The no-strap
    reasoning rested on a forum-only record that a fresh reader refuted; the
    pull-down makes the board boot main flash under either option-byte state,
    so the design no longer depends on unverified knowledge.
- H1 packet written (log/H1.md) and approved as delegated. report_gen exit 0.
- Env gotcha (also in LEARNINGS.md): st.com PDF fetches TIME OUT from this
  container (curl HTTP/2 INTERNAL_ERROR, HTTP/1.1 hangs, agent fetch 0 bytes
  at 280 s). ST reference manuals are unobtainable here; LCSC mirrors serve
  ST *datasheets* but not RMs/ANs.
- Open issues: 1 knowledge gap accepted with a recorded mitigation (above).
  Next: P3 parts + library (part-sourcer, datasheet-extractor x3, librarian),
  then the P3 coverage exit.

## 2026-08-27 - iteration 1 - P3 Parts + Library COMPLETE
- part-sourcer -> parts.json (20 parts, 12 Basic / 8 Extended, 7 fee-bearing,
  ~$4.42/board). 3 datasheet-extractors -> C724040/C2909890/C6186.json, all
  validate exit 0. librarian -> 20/20 symbols+footprints pulled, 85 pins
  retyped, lib tables registered.
- Gates: none due at P3. fp_verify 3 passed / 0 failed / 2 accepted warnings.
  P3 coverage: 7 slots, 0 gap (3 part slots covered).
- Real defects caught and fixed at P3 (this is what the phase is for):
  * pulled SHT40 DFN-4 SOLDERED the die pad - would have shorted the sensor's
    thermal-isolation design to the board. Pad deleted (copper+paste+mask),
    courtyard closed, rationale recorded in the footprint descr.
  * C3 22 uF TANTALUM had no polarity marking anywhere - a reverse-mounted
    tantalum on 3V3 fails short. Pin 1 = anode established twice (vendor PDF
    + live EasyEDA CAD data); silk "+" and bar added.
  * SHT40 symbol->footprint link was broken (easyeda2kicad bug); all 20
    symbols audited, this was the only one.
  * J2 Qwiic pin-1 verified against JST's own eSH.pdf - no flip needed.
- Decisions on the owner's behalf (4 total this phase): 4 sourcing corrections
  (3 remove Extended setup fees, 1 fixes a 0.9 mA worst-Vf-bin dim user LED);
  AMS1117 SOT-223 tab treated as VOUT so the +3V3 thermal pour is valid;
  SHT4x 20 V/ms slew carried item CLOSED (the limit bounds in-operation
  supply changes, not the cold-start ramp, and a POR at power-up is intended).
- Open issue found OUTSIDE the board: three ai-ee SKILL scripts (lib/env.py,
  schem_refdes.py, schlib.py) were modified in the working tree during this
  run by a subagent acting outside its lane. They look like genuine toolchain
  fixes (headless DISPLAY for KiCad SWIG; stripping KiCad-10 `private` lib
  properties that kicad-sch-api 0.5.6 mangles into invalid s-expressions).
  NOT taken on faith - `make check` is running against them before P4; they
  will be judged and committed separately from the board, never swept in.
- Next: P4 schematic (2 sheet agents + root stitch), gate erc, reviewer, H2.

## 2026-08-27 - iteration 1 - P4 sheets built (gate erc still pending)
- Two schematic-block agents (fable/medium) wrote kicad/gen/power_sheet.py and
  kicad/gen/main_sheet.py; both generators run clean and build their sheets.
  26 parts placed across the two sheets. Root stitch + gate erc + reviewer +
  H2 still to come.
- Both agents grounded every IC against `schlib.py --pins` + the P3 extraction
  JSON before wiring, and both reported the checks that matter here:
  * R1/R2 are INDEPENDENT 5.1k Rd on CC1/CC2 (never shared) - netlist checked.
  * C3 tantalum pin 1 (+) on +3V3, pin 2 (-) on GND, re-asserted at build time
    so a library refresh cannot silently flip it.
  * D1 TVS polarity settled two independent ways (symbol cathode-bar side and
    footprint silk band both land on pin 1) -> pin 1 = cathode -> VBUS.
  * U1 SOT-223 TAB (pin 4, VOUT) wired to +3V3, not floating.
  * R13 10k BOOT0 pull-down and R12 = 100R both carry do-not-delete comments
    with their reasoning, so a later pass cannot "correct" them back.
- Env/toolchain finding, resolved honestly rather than swept in: three ai-ee
  SKILL scripts (lib/env.py, schem_refdes.py, schlib.py) were modified in the
  working tree during this run by a subagent acting outside its lane. `make
  check` was run against them: 1968 passed, 25 FAILED (make exit 1, not 0).
  8 of the 25 are the documented KiCad-10.0.5-vs-10.0.3 bench-baseline
  failures; 3 are LEARNINGS.md triage rows this run itself owes. The other 14
  are being isolated right now by reverting the three edits and re-running the
  same subset, so the edits are judged on evidence instead of plausibility.
  The board is NOT gated on this, but the edits will not be committed - or
  relied on - until the comparison says what they actually do.
- Gates: none passed yet (erc is the next one due). Open issues: the script
  question above. Next: resolve it, then root stitch -> erc -> reviewer -> H2.

## 2026-08-27 10:00Z - SUPERVISOR NOTE 3 (host-side) - the three script edits were MINE, now committed
- The modifications to lib/env.py, schem_refdes.py and schlib.py seen during
  iteration 1 were made by the host-side supervisor of this run, not by a
  subagent. They are now a proper commit on this branch: `git log -1
  --grep='\[supervisor\]'`. Do not revert or re-investigate them; the
  run-contract now has a "Supervisor commits" section saying the same.
- What they do: env.py hands children DISPLAY=:99 (Xvfb) - REQUIRED at P7 for
  route_auto's Specctra export/import; schem_refdes/schlib strip KiCad-10
  `private` library properties ksa mangles (not needed by this board's aiee:* +
  power:* symbols, needed for any Device:* symbol).
- The 25 `make check` failures you measured are all pre-existing on this
  branch and unrelated to those files: bench baselines pinned to 10.0.3 (8),
  10.0.5 DRC/ERC deltas on frozen fixtures (board_update 4, lib_hygiene 3),
  Windows-only test path hardcodes (plane_repair 4, task_router 1, check_env 1,
  intake 1), and 3 missing triage rows. All are fixed or documented on the
  env/linux-container branch (PR #1); do not spend board time on them.
- Board status unchanged: erc PASS committed (b2758dc). Continue with the
  schematic reviewer -> H2 -> P5.
