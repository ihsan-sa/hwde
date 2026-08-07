# Topology reference: step-down (buck) converter

Trigger: a detected buck block at P1/P2 (most boards have one). Seeded T6
(2026-08-06) from three shipped/verified runs that each re-derived this from
scratch: usb-buck (AP63203 sync, 5 V -> 3.3 V @ 57 mA), lumina-carrier
(SCT2A25STER async COT, 48 V -> 12 V @ 2 A, PoE), lumina-par (TPS92515-class
CC bucks driving LEDs). CLASS-level decisions only - part-SPECIFIC errata,
efficiency curves and current budgets stay in the run's `research/`.

HOW TO USE (research-reference-design agents): read this FIRST, then research
only the part-specific delta (exact external-component table, errata, the
family's FB flavor). Cite deltas against this file.

## 1. Selection: sync vs async vs controller vs LDO

| Choice | When | Evidence |
|---|---|---|
| Integrated synchronous buck | default at <= ~60 V input, <= ~3 A: no catch diode, best efficiency/heat | usb-buck AP63203 (DS41326) |
| Asynchronous + Schottky | when the V/I corner has no stocked sync part (carrier: only 100 V-rated 2 A part was async COT; needs a Schottky rated >= Vin, e.g. SS510 class) | carrier poe-power.md s4 |
| Controller + external FETs | the efficiency/current escape hatch (~2-3 pts over async, any current) at the cost of 2 FETs + gate/sense network + layout area | carrier poe-power.md (LM5146 fallback) |
| LDO instead | honest option at light load: 3 parts vs 6, no switch node near analog/RF, at the cost of (Vin-Vout)*I heat. Do the table before assuming the buck | usb-buck power.md s4 |

State the tradeoff in one line each; if the brief names a part, the named
part stands - record the alternative as an override option.

## 2. Inductor selection (the rule every run re-derived)

- **L value**: start from the vendor's recommended-components table row for
  your Vout; the next STANDARD value up is usually right (light-load
  efficiency improves with larger L - DS41326 s10 says so explicitly;
  usb-buck: table 3.9 uH -> chosen 4.7 uH).
- **Isat**: must beat the part's PEAK CURRENT LIMIT / PFM clamp, not the load
  current (usb-buck: 450 mA clamp -> 1 A part ample at a 57 mA load).
- **DCR**: budget it as real dissipation - target < 30 mohm for A-class
  rails (usb-buck P3 rule, waived at 60 mohm with math); ~0.1 ohm cost
  0.29 W at 2 A on the carrier. DCR losses scale I^2 - cheap inductors tax
  high-current rails hard.

## 3. Input caps + the hot loop (layout rule #1)

The input cap carries the DISCONTINUOUS switch current: C_IN + a 100 nF HF
bypass AT the VIN pin, same layer as the IC, the C_IN -> VIN -> GND -> C_IN
loop the shortest on the board, SW-node copper minimal. At ~1 MHz this
matters more than copper weight (usb-buck power.md s7-9; every vendor layout
section). GND pour + vias under the IC.

**Upstream bulk limit trap**: the input capacitance is bounded by the SOURCE,
not the buck - USB 2.0 allows 10 uF || 44 ohm at attach (s7.2.4.1), USB-PD
sinks 100 uF under contract (cSnkBulkPd). Check the source's rule BEFORE
sizing C_IN; soft-start makes output caps invisible to the source's inrush
test (usb-buck power.md s6).

## 4. Bootstrap, FB, output caps

- **BST**: integrated-FET parts need the 100 nF BST-SW cap - it is required,
  not optional (DS41326 s13); confirm value/rating in the family datasheet.
- **FB trap (cost a near-miss once)**: FIXED-output family members tie FB
  straight to the output sense point - do NOT copy the ADJUSTABLE variant's
  divider from the shared datasheet figure (AP63203 vs AP63200/1, DS41326
  fig 20/21). Adjustable parts: divider AT the FB pin, short FB trace routed
  away from SW and L, sense point AFTER the output caps.
- **Output caps**: ceramic, inside the datasheet's stated C/ESR window -
  internal compensation assumes it (DS41326 s12); count DC-bias derating
  (a "22 uF" X5R at bias is ~12-15 uF).

## 5. Switch-node containment (the constraint that reshapes boards)

Keep SW copper as small as electrically possible and treat SW + L as an
aggressor: par's 2.4 GHz antenna 11 mm from a switch node drove a 4-layer
stackup + containment plan (par P2 digest); usb-buck keeps the USB pair away
from SW/L per AN4879 3.3. Hand P6 a separation/keepout entry when any
antenna, high-Z analog, or diff pair shares the board; the switch node is
also why `high_speed` references demand an unbroken plane under victims.

## 6. EN / soft-start / sequencing

Check the EN pin's own behavior before adding parts: many parts auto-start
(AP63203: internal 1.5 uA pull-up - tie to VIN or float). Soft-start time
sets output-cap inrush as seen by the source (s3 above). Single-rail boards
rarely need sequencing; multi-rail: state the order requirement or "none"
explicitly in power.md.

## 7. What to emit for the pipeline

- `power` entries with `current_a` from the RAIL BUDGET (consumer sum + ~30%
  headroom, rounded to a design ceiling), `dt_c` from ambient.
- A `thermal` entry when regulator dissipation > ~0.5 W (async parts: add
  the Schottky's V_f * I * (1-D); the diode often out-heats the IC).
- `layout_notes` for P6/P7: hot-loop grouping, SW containment/separation,
  FB routing - these become placement groups and route_critical facts.
