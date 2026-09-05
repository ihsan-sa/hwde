# P4 schematic waivers - g0-sense

ERC gate itself is 0 errors / 0 warnings (reports/erc.json), and
`netlist_audit` (log/netlist_audit-P4.json) is 0 violations with 99/99
expected pins connected. Nothing below is an ERC violation: these are the
three WARNINGS raised by the fresh-context `schematic-reviewer`
(reports/review-schematic.{md,json}), with the disposition taken on the
owner's behalf under the unattended run contract. 0 errors were raised.

| # | kind | refs | severity | disposition |
|---|---|---|---|---|
| W1 | qwiic-esd-unwaived | J2, U2, U3 | warning | WAIVED (recorded decision, P4) |
| W2 | sht4x-vdd-slew-unclosed | U3, U1, C3 | warning | CLOSED as accepted risk (recorded decision, P4) |
| W3 | dnp-not-native | J3, J4 | warning | FIXED (work order wo-w3-dnp) |

## W1 - no ESD array on the J2 Qwiic SDA/SCL - WAIVED

Finding: J2 is a populated, user-facing, hot-pluggable connector; SDA/SCL
and +3V3 leave the board with no clamps and no series impedance, so a
cable-borne strike reaches U2 PA11/PA12 and U3 (2 kV HBM) directly. The
product-scope connector checklist requires this expectation met OR waived,
and no waiver existed. Field-reliability only - it cannot prevent bring-up.

Waived on four grounds:

1. Ecosystem norm. The Qwiic / STEMMA-QT reference implementations
   (SparkFun, Adafruit) are a bare 4-pin JST SH with no array. A
   user-facing part that behaves the way the ecosystem's users expect is
   the conservative choice here, not the exceptional one.
2. Both silicon endpoints carry internal ESD structures and are rated
   2 kV HBM - the standard handling rating for an indoor bench device.
3. The recorded operating environment (P0 decision) is indoor bench /
   room ambient, bare board, no ingress rating - not a field-exposed port.
4. Cost of the alternative at this point in the run: a new Extended MPN
   plus its JLC setup fee, a fresh library pull + fp_verify, and re-opening
   a green schematic - real regression risk traded against a
   warning-severity exposure.

If the owner wants the array anyway, the cheap retrofit is a 4-channel
low-capacitance array on SDA/SCL at J2 (the 1.5 k pull-up budget has room:
the bus was sized to 236 pF and an array adds single-digit pF). That is a
post-run `add-part` task, not a rewind.

## W2 - carried SHT4x VDD-slew verify item - CLOSED as accepted risk

Finding: `power_tree.md` / `decisions.md` carried "verify SHT4x VDD slew
<= 20 V/ms vs the AMS1117 startup ramp"; the reviewer found it unclosed,
found no slew spec in `parts/C2909890.json`, and computed ~40 V/ms from
AMS1117 current-limit charging of the ~27 uF on +3V3.

Closed, no hardware change, on three findings:

1. **Provenance is on file** (the reviewer looked in the wrong artifact).
   The number is `research/records/sht4x-vdd-slew-power-up.yaml`, sourced
   to `research/sources/HT_DS_Datasheet_SHT4x.pdf` p9 Table 4, read
   visually by the researcher and again by a fresh second reader
   (`maturity: verified`). `parts/C2909890.json` is the P3 extraction, a
   different artifact with a different scope.
2. **The worst-case number is an upper bound that cannot occur.** I/C
   (~1 A into ~27 uF) assumes the LDO drives its output cap independently
   of its input. The AMS1117 is a series-pass follower: on a cold start
   VOUT cannot rise faster than VIN minus dropout, so the +3V3 edge is set
   by the USB source's VBUS ramp filtered by C2 = 10 uF, not by the LDO's
   current limit.
3. **The named failure mode is benign at cold start.** The datasheet says
   only "faster slew rates MAY lead to a reset" - and the second reader
   already flagged the researcher's added "or hung until re-powered" as
   unsupported by any cited page. A reset during the power-up ramp leaves
   the part in exactly the state a power-up is meant to produce. The
   limit's real bite is in-operation supply excursions, and hot-plugging a
   DOWNSTREAM breakout onto an already-live Qwiic rail - that one is the
   breakout's decoupling problem, not this board's.

Hardware alternatives considered and rejected: a series R at U3 VDD to
slow the local ramp is disqualified by the SHT4x on-chip heater (75 mA
peak across the ~100 ohm needed for a 100 us tau = 7.5 V drop); raising C3
past ~50 uF to force I/C under 20 V/ms buys nothing against finding 2 and
costs a part change on a green schematic.

Belt and braces, documentation only: "issue an SHT4x soft reset (0x94) at
init" (Sensirion's own recommended start-up sequence) goes into the design
doc and `fab/README`, and the Qwiic hot-plug caveat is carried as a known
limit of the board.

## W3 - J3/J4 DNP intent not KiCad-native - FIXED

Not waived. The headers carried DNP only in a custom `Variant=DNP` field
and the value string, so a native KiCad BOM/POS export would have emitted
the two THT headers as populate lines into a JLC economy (SMT-only) order.
Dispatched as work order `log/workorders/wo-w3-dnp.json`: native `dnp`
attribute set through the board's own generator, and
`refdes_class: {J3, J4 -> hand_install}` added to the header line in
`parts/parts.json` so `bom_cpl.py` keeps them out of the assembler upload
and the CPL while still listing them in the documentation BOM. ERC re-run
after the change.

## Reviewer OPEN items and where they went

- **AMS1117 SOT-223 tab = VOUT not stated in the on-file PDF.** Already a
  recorded P3 decision (the pulled symbol's pin 4 = VOUT, and SOT-223
  construction fuses the tab to the pin-2 lead frame in every 1117-family
  part). No further action.
- **SW1 pairing verified from a live fetch, not archived.** The evidence
  (A/B common, C/D common; NRST on 1/2, GND on 3/4) is recorded in
  `reports/review-schematic.md` with its source URL and is committed. Not
  re-fetched: the finding is a CLEAR, and the archive would only make an
  already-recorded pass reproducible.
- **Extend the CPL rotation check from J1 to the polarized 2-pin parts
  (D1, D2, D10) and to C3.** Carried into P9 as a required check; recorded
  as a decision so it cannot be lost.
