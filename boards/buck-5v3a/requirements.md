# Requirements: buck-5v3a

## 1. Function
Standalone synchronous step-down (buck) DC-DC converter board. It takes a
DC input of 7-18 V (12 V nominal) on a 2-pin 5.08 mm screw terminal and
produces a regulated 5 V output at 3 A continuous (15 W) on a second 2-pin
5.08 mm screw terminal, with reverse-polarity protection on the input so a
swapped supply does not damage the board or the load. Power-only board: no
MCU, no digital interface, no communication bus stated. Must run at up to
50 C ambient with no forced airflow, in a 50 x 40 mm outline.

## 2. Interfaces
- Power input (J1): 2-pin screw terminal, 5.08 mm pitch (stated). DC only.
  ASSUMED: through-hole terminal block, standard 5.08 mm 2-pole (e.g.
  Phoenix MKDS / MSTB-style clone as stocked by LCSC); rated >= 10 A and
  >= 250 V so it is not the limiting element at 2.5 A input. Polarity is
  silkscreen-marked (+ / -), and the board tolerates the reverse case by
  design (see Power).
- Power output (J2): 2-pin screw terminal, 5.08 mm pitch (stated). 5 V,
  3 A continuous. ASSUMED: same terminal family/part as J1 for BOM
  consolidation, but physically separated and silk-labelled distinctly
  (VIN vs 5V OUT) so the two cannot be confused in the field.
- No other external interfaces stated: no USB, no RF, no header, no
  comms bus, no external enable/on-off line, no fault output. Indicators
  and test points are unspecified - see Open questions 6.

## 3. Power
- Source: external DC supply, 7-18 V, 12 V nominal (stated). Source TYPE
  is NOT stated (bench supply / AC-DC brick / battery / vehicle 12 V
  system) and is safety-relevant - see Open questions 1. The pipeline
  will not proceed on a guessed answer.
- Input current (GUESS, for sizing only): 15 W out at an assumed 90-93%
  efficiency -> ~16.1-16.7 W in. At 12 V nominal ~1.4 A; at the 7 V
  low-line corner ~2.3-2.4 A. Input path (terminal, reverse-polarity
  device, fuse if fitted, inductor-side copper) sized for >= 2.5 A
  continuous.
- Output rail: single 5 V rail, 3 A continuous = 15 W (stated). No other
  rail stated - no auxiliary 3.3 V, no bias rail exposed. Accuracy and
  ripple limits are not stated - see Open questions 3.
- Topology: synchronous buck (stated) - integrated-FET regulator or
  controller-plus-FETs is the architect's call at P1/P2, but synchronous
  rectification is a requirement, not a preference (a non-synchronous
  design is out of spec).
- Reverse-polarity protection: REQUIRED on the input (stated). Method not
  stated - see Open questions 4. GUESS for thermal budgeting: a series
  P-channel MOSFET costs ~50-100 mW at 2.4 A, a Schottky diode ~1.0-1.2 W
  at the same current, which is a meaningful share of the total loss
  budget on a 50 C-ambient, no-airflow board.
- Loss/thermal budget (GUESS): ~1.1-1.7 W total board dissipation at
  12 V in / 3 A out. With 50 C ambient, no airflow, and a 50 x 40 mm
  outline, copper area and via stitching under the regulator are design
  drivers, not afterthoughts. Peak component temperature target ASSUMED
  as <= 105 C junction-equivalent hotspot (derated), unless the answer to
  Open questions 9 imposes an enclosure that raises the internal ambient.
- No battery, no charging circuit, and no energy storage function stated
  on this board - PENDING confirmation that the SOURCE is not a battery
  (Open questions 1).

## 4. Environment
- Ambient: up to 50 C (stated).
- Cooling: natural convection only, no forced airflow (stated). ASSUMED:
  no heatsink and no thermal interface to a chassis unless the answer to
  Open questions 9 says the board mounts to metal.
- Minimum ambient not stated. ASSUMED: 0 C (indoor/benign). If the source
  turns out to be automotive or outdoor, this becomes -40 C and changes
  capacitor and inductor selection - covered by Open questions 1 and 9.
- Enclosure, ingress (IP) rating, vibration/shock, humidity, conformal
  coating: none stated - see Open questions 9.

## 5. Size & mounting
- Outline: 50 x 40 mm maximum (stated). Treated as a HARD cap - it binds
  permanently at P5 board_init and cannot be relaxed later without a
  restart of the mechanical baseline. Smaller is allowed; larger is not.
- Mounting holes: not stated - see Open questions 8.
- Height limit: not stated - see Open questions 8. Relevant because a
  15 W buck at 50 C ambient may want a taller shielded inductor and/or a
  tall electrolytic input capacitor, and screw terminals themselves stand
  ~10-12 mm tall with wiring.
- Connector edge placement: not stated. ASSUMED: both screw terminals sit
  on board edges with their wire-entry openings facing outward so field
  wiring does not cross the board; the architect picks which edges.

## 6. Quantity & budget
- Build quantity: not stated - see Open questions 10. ASSUMED default of
  a small prototype run (qty 5) for costing purposes only.
- Target unit cost: not stated - see Open questions 10. ASSUMED: no hard
  per-unit cap; cost minimized by preferring JLC Basic parts and an
  economy fab/assembly tier, rather than hitting a fixed number.

## 7. Assembly
- Not stated - see Open questions 11. ASSUMED: JLCPCB PCBA, single-sided
  (top) SMT assembly, which suits a power board where the bottom copper
  is wanted as an unbroken thermal/return plane.
- The two 5.08 mm screw terminals are through-hole parts. ASSUMED: fitted
  by JLCPCB through-hole assembly if offered at acceptable cost for the
  chosen part, otherwise hand-soldered after SMT - either is acceptable
  and does not change the schematic or the footprint.
- No stated restriction on package sizes or on Extended/Basic library
  parts; ASSUMED preference for JLC Basic where a Basic part meets the
  electrical requirement, with Extended allowed for the regulator IC and
  the power inductor (Basic stock rarely covers 3 A-class buck parts).

## 8. Compliance/safety flags
Two flags apply; one is pending an answer.
- High current (>3 A): APPLIES at the boundary - 3 A continuous output is
  the stated rating, and any specified peak/inrush allowance pushes the
  board above 3 A (Open questions 2). Consequences carried forward:
  trace/copper sizing with a defined temperature rise, thermal relief and
  via stitching, input/output capacitor RMS ripple current ratings,
  connector and fuse ratings, and a defined short-circuit behavior
  (Open questions 5).
- >30 V: DOES NOT APPLY at the stated steady-state maximum of 18 V, but
  the input transient environment is unknown. If the source is a vehicle
  12 V system (Open questions 1), load-dump and ISO 7637-2 transients can
  exceed 40 V and this flag flips to APPLIES, forcing input clamping
  (TVS), a higher-voltage regulator, and higher-voltage input capacitors.
  Not guessed - asked.
- Batteries: UNKNOWN, PENDING Open questions 1. The brief gives a voltage
  window (7-18 V) that is equally consistent with a bench supply, an
  AC-DC adapter, a 12 V lead-acid battery, or a 4S Li-ion pack. No
  charging function is requested on this board, but battery-source status
  changes reverse-polarity expectations (a mis-clipped battery is a
  sustained, low-impedance reverse fault, not a brief supply glitch),
  deep-discharge/UVLO behavior, and the minimum ambient. Per the P0
  rules, this is asked, never assumed.
- Mains voltage: does not apply - the board sees DC only, and generating
  the DC input is out of scope for this board.
- Motors: does not apply - no motor drive stated. If the 5 V load is
  actually a motor or an inductive/stalling load, the peak-current answer
  (Open questions 2) must reflect it.
- RF transmit: does not apply - no radio function.

## 9. Open questions
STATUS: ALL RESOLVED 2026-08-08 by the user (Q1, Q2, Q4, Q11 answered
explicitly; Q3, Q5-Q10 accepted at their stated DEFAULT). The binding
answers are in section 10 - where section 10 and this section differ,
section 10 wins.

1. What exactly powers the input? Pick one: (a) bench power supply,
   (b) AC-DC wall adapter or brick, (c) a battery - and if so, which
   chemistry (lead-acid, LiFePO4, Li-ion pack, other), (d) a vehicle /
   automotive 12 V system, or (e) something else. This is the one
   safety-relevant question with NO default: it decides whether the board
   needs load-dump/surge clamping (up to 40 V+), a wider temperature
   range, and battery-specific reverse-connection and under-voltage
   behavior. Please answer explicitly.
2. Is 3 A the absolute maximum output current, or must the board also
   survive brief peaks above it (for example a motor or capacitive load
   drawing 4-5 A for tens of milliseconds at startup)? If there are
   peaks, how much current and for how long?
   DEFAULT: 3 A continuous is the maximum; no specified peak above it,
   and the regulator's own current limit provides the headroom.
3. How tight does the 5 V output need to be? Two numbers: DC accuracy
   (how far from exactly 5.00 V is acceptable) and ripple (how much
   high-frequency wobble riding on the 5 V is acceptable).
   DEFAULT: +/-3% DC accuracy (4.85-5.15 V) over the full line and load
   range, and <= 50 mV peak-to-peak output ripple.
4. Which style of reverse-polarity protection do you want? A series
   P-channel MOSFET wastes very little power (tens of mW) but adds a few
   parts; a Schottky diode is one cheap part but burns roughly 1 W as
   heat, which is significant on a fanless board at 50 C ambient.
   DEFAULT: P-channel MOSFET (low loss - the right call for this thermal
   budget).
5. Should the board include its own input fuse, and what should happen on
   an output short-circuit? Options for the fuse: a one-shot cartridge or
   SMD fuse (must be replaced after a fault), a resettable polyfuse
   (recovers by itself), or none (rely on the upstream supply's limit).
   DEFAULT: fit one non-resettable SMD fuse rated ~4 A on the input, and
   rely on the regulator IC's built-in hiccup-mode current limit and
   thermal shutdown for output short-circuit and overload protection.
6. What local indicators and test access do you want? Options: a power
   LED on the 5 V output, test points for probing, an external
   enable/on-off input, a power-good signal brought out.
   DEFAULT: one green power LED on the 5 V output plus three test points
   (VIN, 5V, GND); no external enable input and no power-good output
   (nothing in the brief needs to talk to this board).
7. Does this board have to pass a formal EMC/emissions test (for example
   CISPR 32 for an information-technology product, or CISPR 25 if it goes
   in a vehicle), or is it an internal/prototype board where good layout
   practice is enough?
   DEFAULT: no formal EMC test campaign; design with power-loop-tight
   layout and normal input filtering, and leave room for an optional
   input filter if you later need it.
8. Mechanically: does the board need mounting holes, and is there a
   height limit above the PCB? If it bolts into something, what hole size
   and pattern?
   DEFAULT: four M3 holes (3.2 mm drill) inset from the corners of the
   50 x 40 mm outline, and a 15 mm maximum component height (the screw
   terminals themselves are about 10-12 mm tall).
9. Where does the board live? Specifically: open on a bench, inside a
   plastic or metal enclosure, exposed to dust/water (any IP rating),
   subject to vibration, or needing conformal coating? Also, what is the
   coldest ambient it will see?
   DEFAULT: open board, indoors, no enclosure, no ingress rating, no
   vibration requirement, no conformal coating, and a 0 C minimum
   ambient.
10. How many boards will be built, and is there a hard per-unit cost
    target?
    DEFAULT: a prototype run of 5 boards, with no hard cost cap - cost is
    minimized by preferring JLC Basic parts and an economy fab tier.
11. How should it be assembled? Options: JLCPCB machine assembly of the
    surface-mount parts only (you hand-solder the two screw terminals),
    JLCPCB assembly including the through-hole screw terminals, or full
    hand assembly. Also: is it acceptable for all surface-mount parts to
    sit on the top side only?
    DEFAULT: JLCPCB PCBA, top-side surface-mount assembly only, with the
    two screw terminals added by JLCPCB through-hole assembly if the cost
    is reasonable and hand-soldered otherwise; bottom side kept clear as
    a thermal/ground plane.

## 10. Answers (binding, user-confirmed 2026-08-08)
A1. SOURCE: bench power supply or AC-DC adapter/brick. NOT a battery, NOT
    automotive. Consequences: the >30 V flag stays CLOSED - no load-dump
    clamping campaign, no ISO 7637-2, no -40 C rating. Input steady-state
    max stays 18 V; parts rated 25-40 V with a modest input TVS for hot-
    plug/inductive-cable ringing are sufficient. Battery flag CLOSED: no
    UVLO/deep-discharge behavior required, and the reverse-connect fault
    is supply-current-limited rather than a pack short.
A2. PEAK LOAD: 3 A is the absolute maximum. No peak allowance above 3 A.
    Size the inductor saturation and current limit for the regulator's
    own limit (target ~4-5 A), not for an external burst.
A3. OUTPUT TIGHTNESS (default accepted): +/-3 % DC (4.85-5.15 V) over the
    full 7-18 V line and 0-3 A load range; <= 50 mV pk-pk output ripple.
A4. REVERSE-POLARITY: series P-channel MOSFET in the input path (gate
    clamped, e.g. gate resistor + zener). Schottky rejected on thermal
    grounds. Target conduction loss <= 100 mW at the 2.4 A low-line
    input current.
A5. FUSE / SHORT-CIRCUIT (default accepted): one non-resettable SMD fuse
    on the input, ~4 A rating; output short-circuit and overload handled
    by the regulator's hiccup current limit plus thermal shutdown.
A6. INDICATORS / TEST ACCESS (default accepted): one green power LED on
    the 5 V output; three test points (VIN, 5V, GND). No external enable
    input, no power-good output.
A7. EMC (default accepted): no formal test campaign. Tight power-loop
    layout and normal input filtering; leave room for an optional input
    filter.
A8. MECHANICAL (default accepted): four M3 (3.2 mm) holes inset from the
    corners; 15 mm maximum component height above the PCB.
A9. ENVIRONMENT (default accepted): open board, indoors, no enclosure, no
    IP rating, no vibration requirement, no conformal coating, 0 C
    minimum ambient. 50 C maximum ambient and natural convection stand.
A10. QUANTITY / COST (default accepted): prototype run of 5. No hard
    per-unit cap; prefer JLC Basic parts and an economy fab tier.
A11. ASSEMBLY: JLCPCB PCBA, TOP-SIDE SMT ONLY. The two 5.08 mm screw
    terminals go to JLC through-hole assembly if reasonably priced, and
    are hand-soldered otherwise - either way the schematic and footprint
    are unchanged. Bottom side stays clear of SMT parts and is used as a
    thermal/return plane. Prefer Basic/Preferred parts; Extended allowed
    for the regulator IC and the power inductor.
