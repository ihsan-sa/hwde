# bb-amp - schematic sheet plan (P2)

## Ruling: ONE sheet. No hierarchy.

The whole board is 14 components on one signal path (J1 -> U1 -> U2B -> J2)
plus a two-resistor reference and four capacitors. A hierarchical sheet
buys navigation at the cost of hierarchical pins, sheet instances and a
netlist whose names carry sheet paths - all of it overhead against a schematic
that fits on one A4 page with room for the design equations in a text box.
Splitting it would also hide the one thing a reader of this board should see
at a glance: that `/VREF` is a single node touching U1 pin 6, U2A output and
the stage-2 gain return, which is what makes the pedestal exact
(`blocks.md` section 2).

Root sheet = the only sheet. Net names carry a leading `/` for local labels
(`/IN_P`), power nets are bare (`+3V3`, `GND`).

## Sheet: root (`bb-amp.kicad_sch`)

**Blocks on it:** B1 input interface, B2 in-amp, B3 reference/pedestal,
B4 output gain stage, B5 output interface, B6 power entry.

**Layout of the drawing** (left to right, matching the board's own chain, so
placement groups at P6 read straight off the schematic): J1 / input pair at
the far left; U1 with R1 across its RG pins; the reference cluster
(R2, R3, C4, U2A) below U1; U2B with R4/R5 to the right of U1; J2 at the far
right; J3 and C2 along the bottom with C1/C3 drawn at their IC supply pins.

**Nets that leave a block** (these become the placement groups at P6 and the
net classes at P5):

| net | from | to | note |
|---|---|---|---|
| `/IN_P` | J1 pin 1 | U1 pin 4 (+IN) | differential pair with `/IN_N`; matched, symmetric, over unbroken B.Cu |
| `/IN_N` | J1 pin 2 | U1 pin 1 (-IN) | same |
| `GND` | J1 pin 3, J2 pin 2, J3 pin 2 | plane | bias-current return path for both inputs (refdesign D12) - not a convenience pole |
| `/VREF_SET` | R2/R3 junction, C4 | U2A + input | high-Z divider node, bypassed by C4 |
| `/VREF` | U2A output | U1 pin 6 (REF), R5 | must stay below 2 ohm of source impedance (AD8226 Reference Terminal); one node, three loads |
| `/AMP1_OUT` | U1 pin 7 (OUT) | U2B + input | 0.21 - 1.05 V over the input range |
| `/FB2` | R4/R5 junction | U2B - input | stage-2 summing node |
| `/VOUT` | U2B output | J2 pin 1 | 0.113 - 3.037 V into >= 100 k |
| `+3V3` | J3 pin 1 | U1 pin 8, U2 pin 8, R2, C1, C2, C3 | 0.65 mA worst case |

## Refdes ranges

One sheet, so uniqueness is trivial - the ranges are still fixed here so P4
and any later `schem_refdes` renumber land in the same places, and so a second
sheet added later cannot collide.

| class | range | assigned on this board |
|---|---|---|
| U (ICs) | U1 - U9 | U1 AD8226 in-amp; U2 OPA2333 dual (U2A buffer, U2B gain) |
| R | R1 - R19 | R1 RG 1.27 k; R2 121 k, R3 10.0 k divider; R4 24.9 k fb, R5 10.0 k gain return |
| C | C1 - C19 | C1 100 n at U1; C2 10 u bulk; C3 100 n at U2; C4 100 n on `/VREF_SET` |
| J | J1 - J9 | J1 input 3-pole; J2 output 2-pole; J3 power 2-pole |
| H (mounting) | H1 - H4 | none required; optional M3 clearance holes only if the earned outline leaves corner room |
| `#PWR` | `pwr_base = 100` -> `#PWR0101...` | power/GND symbols on the root sheet |
| `#FLG` | `#FLG0101...` | one PWR_FLAG on `+3V3` and one on `GND` (external rail, no on-board source - ERC needs them) |

## Values and tolerances the schematic must carry

Calibration removes initial error but not tempco, so tolerance and TCR are
split deliberately (`blocks.md` Ruling 3 quantifies each term):

| ref | value | tolerance / TCR | why |
|---|---|---|---|
| R1 (RG) | 1.27 k | 0.1 %, 25 ppm/degC | sets G1 = 39.90; its TCR adds directly to the AD8226's -100 ppm/degC gain drift |
| R2 / R3 | 121 k / 10.0 k | 0.1 %, 25 ppm/degC | sets the 0.252 V pedestal; ratio TCR mismatch is a 1.1 uV RTI drift term |
| R4 / R5 | 24.9 k / 10.0 k | 0.1 %, 25 ppm/degC | sets G2 = 3.49; ratio TCR mismatch adds to gain drift |
| C1, C3, C4 | 100 nF | X7R, 16 V+ | supply and reference bypass |
| C2 | 10 uF | X5R/X7R, 16 V+ | bulk at the power entry (AD8226 Figure 61) |

Absolute tolerance is not what buys accuracy here (zero and span are
calibrated downstream per Q7) - TCR is. If P3 finds 1 % / 25 ppm parts
cheaper and in stock, they are acceptable everywhere; 100 ppm/degC thick film
is NOT, because it would triple the pedestal drift term and add ~50 ppm/degC
to the gain drift.
