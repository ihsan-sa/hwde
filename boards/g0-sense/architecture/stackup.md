# stackup - g0-sense (P2)

## Chosen: `JLC2313_1.6` (reference/stackups.yaml, `available: true`)

JLCPCB standard 2-layer, 1.6 mm FR-4, 1 oz outer copper, HASL - exactly the
brief-stated board class (2 layers, 1.6 mm, HASL, green soldermask; green is
an ordering option, not a stackup property).

## Why 2 layers (drivers)

- Impedance control: NONE needed. No high-speed nets, no differential pairs
  anywhere (D+/D- unconnected, CC is DC, I2C <= 400 kHz, UART, SWD). The
  JLC2313_1.6 entry's empty controlled_impedance list is irrelevant here.
- Planes: one ground is enough. B.Cu carries the default full-board GND pour
  (planes_gen 2-layer default - no `planes` override declared); F.Cu carries
  a local +3V3 pour at the LDO tab (~600-1000 mm^2, drawn at P7 as thermal
  compliance for the U1 `thermal` entry, NOT a declared full-board plane).
- Density: ~27 fitted parts + 2 DNP headers + 4 conditional holes on
  ~875 mm^2 - low. Routing is a handful of slow signals plus one power
  corridor; 2 layers is honestly sufficient, and the fewest layers the
  blocks need is the rule.
- Current: worst fault sizing is 1.5 A (PTC dwell) -> 0.80 mm at 1 oz,
  dT 10 C. 2 oz (`JLC2313_1.6_2oz`) buys nothing - do not pay for it.

## Copper plan (informative for P6/P7)

- B.Cu: GND pour, full board, VOIDED under the SHT4x sensor island (both
  layers copper-free there except the four pin lands and necked traces).
- F.Cu: components + routing; +3V3 thermal pour tied to U1's tab, kept away
  from the sensor island; VBUS/+5V runs at >= 0.8 mm from J1 pads through
  D1/F1 to U1 VIN.
- Sensor island: no pour either side, fab-minimum necked traces, milled
  U-slot on the inboard sides where the outline allows (P6 geometry).

## Board size: an OUTPUT, not chosen here

Stated ~35 x 25 mm is a SOFT preference with no hard cap. What the layout
NEEDS: (1) USB-C at one edge with a ~13 mm swath clear of tall parts;
(2) the SHT4x island at the OPPOSITE edge with >= 8 mm to U1/U2 plus slot
room; (3) ~600-1000 mm^2 of top +3V3 pour near U1; (4) edge access for J2
Qwiic and the two 1x4 headers; (5) four M2 pads (4.0-4.5 mm annulus) in
corners, conditional. Sum of needs estimates to ~800-1000 mm^2: the 35 x 25
target (875 mm^2) is plausibly earned with the pour at its ~600 mm^2 lower
bound (theta-JA ~65-70 C/W, Tj ~75 C rated case - fine); if the M2 corners
plus the isolation slot will not coexist at 35 x 25, the honest outline
grows toward ~40 x 28 OR the hole count drops per the conditional rule
(decisions.md) - P5 opens with `board_init --outline auto`, P6 earns the
size with `board_edit --outline fit`, and any excess over 35 x 25 is
recorded as a relaxation at H1.
