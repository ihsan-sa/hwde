# P7 Routing digest - LUMINA carrier (LUM-CAR-A)

Artifacts: `work/p7/*` (DRC ladder, diff-pair and barrier measurements, plane
repairs), `work/p8/drc_confirm.json` (the standing 0/0 proof),
`kicad/lumina-carrier.kicad_pcb`.

- **Gate `drc_routed`: PASS, err+warn = 0** (1 attempt, ~3089 track segments,
  4 layers, In1 = GND / In2 = +3V3 planes with stitching).
- MDI routed as two matched pairs; final `check_diffpair` **0 violations**:
  TX skew **0.0012 mm (0.008 ps)**, RX skew **0.98 mm (6.58 ps)** as the gate
  measures it (see the caveat below - the gate under-measures RX).
- Worst measured pad-to-track clearance on the HV domain **1.4221 mm**.

## Measurement record settled (shape-aware), including a retraction

Three different numbers were produced for one barrier because a rectangle model was
twice applied to circular pads. Definitive figures come from a single shape-aware
tool (`work/p7/pad_gap.py`; capsule model: circle = degenerate segment, oval =
stadium spine, rect = per-axis):

- **J1 chip-side/line-side barrier = 1.6130 mm** as built (1.4510 mm at pad 2's
  original size). Both pass the 1.30 mm DRU rule and HALO's 1.40 mm guidance. The
  original P4 figure of 1.451 mm was **correct all along**; the P7 "correction" to
  1.148 mm was wrong and is retracted.
- **Shield board-lock to PoE tap = 0.6029 mm** (pad 19 to pad 11) and
  **0.6127 mm** (pad 20 to pad 14). These **pass IPC-2221B B2** (0.60 mm for the
  51-100 V band) and fall 0.032 mm short only of the 0.635 mm adopted board-wide
  from TI's guidance.
- **Deliberate non-reversion:** J1 pad 2 stays at 1.200 mm although the shrink that
  produced it was based on the wrong model. 0.150 mm ring on a 0.900 mm drill is
  exactly JLC's PTH minimum, the barrier is *better* as built, and enlarging the pad
  now would shrink every pad-to-track gap around it on a board just brought to zero
  clearance errors. Recorded so the next reader knows this is an accepted state, not
  an unexamined leftover.

## The expensive lesson of this phase

A 0.300 mm placement nudge of C35 - made to open a claimed 0.681 -> 1.681 mm GND
fan-out corridor for U10 - **introduced a short**. Two compounding errors:
(1) the corridor figure read C35's *footprint origin* y, not its *pad-1 centre* y,
off by exactly 0.700 mm, so the real corridor was 0.9811 mm; and (2) it was
validated with `gate place` (PASS) and `check_decoupling` (unchanged) - **both of
which are structurally blind to routed copper** - while at the new position C35's
pad 1 landed on an existing /ETH_RSTn run, giving +6 DRC errors including a
`SHORTING_ITEMS` and a `solder_mask_bridge`. The router caught it and reverted.
The corridor could never have closed the item anyway: the real blocker was a
**void in the In1 GND fill** created by neighbouring +3V3 plane vias' clearance
holes, so a via there would have connected to nothing (0 legal 0.5 mm centres
across the whole corridor at 0.025 mm step). The router solved it properly by
escaping U10 pad 9 **north** into the LQFP's own die shadow.

**Rule of record: on a routed board, DRC is the authoritative oracle for any
placement or silk change.** This is in `LEARNINGS.md`.

## Caveat carried into P8

`check_diffpair`'s `matched_terminals` pairs a p-pad with an n-pad only within
`TERM_PAIR_MM = 2.5`. J1's RX pads are **4.58 mm** apart, so **J1 is not recognised
as a terminal** and the "trunk" is measured from the ESD array to the PHY only. The
RX pair therefore **passes at 0.98 mm** while the true magjack-pad-to-PHY-pad skew
is **6.451 mm (43.0 ps)**, with **4.326 mm of it inside the J1 escape the gate never
inspects**. This is an open owner decision at H4, not a waiver.
