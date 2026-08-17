# bb-amp - power tree (P2)

One rail, no conversion. `research/power.json` does not exist (P1 skipped the
power-architect as trivially powered), so every number below is taken from
the chosen parts' data sheets and from the design point in `blocks.md`.

## Rail

| rail | source | range | who sets it |
|---|---|---|---|
| `+3V3` | J3 pole 1, external bench supply | 3.135 - 3.465 V (3.3 V +-5 %) | requirements 9a Q10 |
| `GND` | J3 pole 2 | 0 V, single node | J1 pole 3, J2 pole 2 and the B.Cu pour are the same net |

No on-board regulation, no second rail, no reverse-polarity or inrush
element, no sequencing: all excluded at `block-only`, and nothing on the
board needs them.

## Budget

| load | typ | worst case | source |
|---|---|---|---|
| U1 AD8226, quiescent | 325 uA | 400 uA at 25 degC, ~450 uA at 50 degC | Table 3 POWER SUPPLY (325 typ / 400 max at 25 degC; 425 / 500 at 85 degC) |
| U2 OPA2333, two channels | 34 uA | 56 uA over temperature | SBOS351E 6.6: 17 uA typ / 25 uA max per amplifier, 28 uA over temp |
| R2/R3 pedestal divider | 25 uA | 26 uA | 3.3 V / 131 k |
| stage-2 feedback network at full scale | 80 uA | 82 uA | (3.037 - 0.252) V / 34.9 k, sourced by U2B, sunk by U2A |
| output load (Q8, >= 100 k) | 30 uA | 30 uA | 3.037 V / 100 k |
| **total** | **~0.49 mA** | **~0.65 mA** | **6.5 % of the 10 mA budget of Q10** |

Dissipation: 3.465 V x 0.65 mA = **2.3 mW for the whole board**. U1 carries
1.6 mW of that in an SOIC-8 (theta_JA = 121 degC/W, 4-layer JEDEC) -> a
junction rise of ~0.2 degC. **Nothing on this board is thermally driven**:
no copper area, no via field, no spacing and no part of the outline is sized
by heat, and `constraints.json` therefore declares no `thermal` entry. (This
is a statement, not an omission - no scope tier excludes thermal; here the
requirement is provably nil.)

Current is far below any width rule: `constraints.json` declares
`current_a: 0.01` for `+3V3`, i.e. the stated budget rather than the 0.65 mA
actually drawn, so `rules_gen` sizes the rail for what the terminal may
legitimately deliver.

## Decoupling and the reference node

| ref | value | at | why |
|---|---|---|---|
| C1 | 100 nF X7R | U1 pin 8 (+VS), <= 2 mm, own ground via | AD8226 Figure 61 / Power Supplies: "a 0.1 uF capacitor should be placed as close as possible to each supply pin" |
| C2 | 10 uF X5R/X7R | at J3 | same figure: "a 10 uF tantalum capacitor can be used farther away from the part ... can be shared by other precision integrated circuits" - one bulk serves both ICs |
| C3 | 100 nF X7R | U2 pin 8 (V+), <= 2 mm | SBOS351E layout practice, same rule |
| C4 | 100 nF X7R | across R3, on the divider node | bypasses the 9.24 k Thevenin of the pedestal divider (corner 172 Hz). NOT on the buffer output - a follower driving a bare capacitor peaks |

Only these four. There is no bulk-per-IC, no ferrite, no pi filter and no
supply filtering beyond what the two data sheets ask for; added filtering is
out of scope at `block-only`, and the parts do not need it (AD8226 PSRR is
120 dB at G >= 100; OPA2333 PSRR is 5 uV/V max).

## The rail is an accuracy term, not just a supply

The pedestal is derived from `+3V3` by a resistor ratio, so the rail moves the
output zero with a gain of 0.0763 V/V (0.252 / 3.3), i.e. **548 uV of RTI
error per volt of rail change** at G_total = 139.2:

```
5 uV RTI of error  <->  9.1 mV of rail movement (0.28 % of 3.3 V)
```

After the downstream zero calibration of Q7, the rail must therefore stay
within about +-10 mV of its calibrated value for the pedestal to contribute
nothing measurable - against a stated tolerance of +-165 mV. This is recorded
as a limitation of the board, not designed out: a series voltage reference
would fix the term, but it is second order against the 13.9-56.4 uV of in-amp
offset drift that dominates the same budget (`blocks.md` Ruling 3), and a
reference IC on a `block-only` board must earn its place.

The same rail also feeds the off-board bridge excitation (Q1), and Q4 declared
the system **absolute, not ratiometric** - so a rail change is additionally a
direct 1:1 span error at the sensor. Both effects push the same way: this
board's accuracy is only as stable as the 3.3 V supply it is given.
