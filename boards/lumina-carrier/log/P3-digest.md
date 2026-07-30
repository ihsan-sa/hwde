# P3 Parts + Library digest - LUMINA carrier (LUM-CAR-A)

Artifacts: `parts/`, `lib/aiee.kicad_sym`, `lib/aiee.pretty`, `reports/lib_pull.json`,
`reports/fp_verify_*.json` + `fp_*.overlay.svg` (9 footprints verified against datasheet
pad geometry), `work/ps_*.json`, `work/pull_*.json`.

- **PD controller: TPS2378-class, NOT Si3402-B.** The briefs name Skyworks
  Si3402-B/AN956; both Si3402-B and Si3404 are IEEE 802.3 **Type 1 only** at any
  resistor value, so D-01's "resistor change, no respin" upgrade to Type 2 is
  unachievable with them. TPS2378 reaches Type 1/Type 2 on a **single** RCLS
  (90.9R af -> 63.4R at, 1 %). TPS2372/2373 rejected: two class resistors = a
  two-part upgrade. Consequence recorded: AN956's "~10 W regulated" figure is a
  Type-1-only statement and does not describe this design.
- **Magjack: LINK-PP LPJG0926HENL (C22457393)**, after the first choice failed
  qualification. Screening history matters because it changed the answer twice:
  - HY/original 10/100 part: publishes **no** tap current rating at all.
  - Best documented 10/100 PoE+ part (Wurth 7499410213) publishes 600 mA/tap =
    exactly the 802.3at DC maximum and **below** the 0.686 A peak; +7.20 USD/board,
    **zero** LCSC stock (DNP + hand-solder x14), internal Bob Smith network that
    cannot be removed, isolation pad gap collapsing 3.58 -> 1.05 mm.
  - Re-running the screen over **gigabit** ICMs (the earlier category rejection was
    an error) found LPJG0926HENL: **720 mA @ 57 VDC continuous**, 1.20x the at DC
    max and **1.05x the 0.686 A peak** - the first candidate that covers the peak.
    3109 in stock, 3.7852 USD at qty-10 (52.99 USD for 14, **80.57 USD cheaper**
    than the Wurth plan), and JLC Assembly = Wave Soldering so JLC **places** it.
  - Accepted costs: no integrated bridge (two external bridges), return loss
    -16 vs -18 dB, CMRR -30 vs -35 dB, and **0..+70 C** op temp makes it the
    lowest-temperature-rated part on the board (+15.9 K margin at the ICD's 30 C
    room ceiling for at).
- **OVP divider on precision thin-film** (R66/R67/R73 = Yageo RT 0.1 %,
  **25 ppm/C**). Tempco, not initial tolerance, was the defect: 100 ppm/C over a
  60 C excursion drags the OVP **falling** threshold to ~56.5 V, i.e. **below** the
  57 V legal PSE maximum, so a legal rail could fail to re-enable after an
  overvoltage event. 25 ppm/C moves worst-case falling to ~58.2 V: ~1.2 V of real
  margin instead of 0.18 V. R4/R5 (T2P level shift) deliberately stay 1 %.
- **Three library defects fixed that no later phase could have resolved**
  (all logged in `lib/EDITS.md`):
  1. J1 board-lock <-> VC creepage was **0.487 mm** against the board's own
     0.635 mm rule - voltage-derived, so P8 would have failed it after routing.
     Pads 19/20 made oval 2.00 x 2.60 and VC1/VC4 1.20 mm: gap now **0.687/0.697 mm**
     with every annular ring at JLC's 0.15 mm minimum. Side effect: the chip-side/
     line-side barrier improved 1.401 -> 1.451 mm, clearing HALO's 1.40 mm guidance.
  2. R3's land moved 0603 -> **0805** so the 63.4R class-4 upgrade at ~105 mW is
     in-spec on the SAME land - D-01's no-respin promise made real.
  3. D1 SMBJ58A courtyard was self-intersecting from zero-length `fp_line`
     segments (easyeda2kicad artifact); 5 removed across 2 footprints.
- **BOM sync hardened:** `bom_sync.py` now preserves `not_fitted` lines. The first
  sync silently dropped C334927, the 63.4R class-4 resistor, precisely because it
  has zero refs by design - deleting the one component that makes the upgrade
  promise real. Final: 50 BOM lines, 109 placed components, 0 lines changed on a
  repeat run, 0 netlist LCSC codes without a BOM line. Only H5 lacks an LCSC
  property (mounting hole, board-only by design).

## Process note of record

The orchestrator's own Task brief for the magjack swap carried the **Wurth** part's
pin deltas into a brief for the **LINK-PP** - a different part with a different pin
count. The agent detected the contradiction, built to the datasheet (VC1-4 = pins
11-14, LEDs 15-18, EH 19-20, confirmed against `parts/C22457393.json`) and reported
the override rather than splitting the difference. That behaviour is what kept a
wrong magjack pinout from flipping the connector end-for-end.
