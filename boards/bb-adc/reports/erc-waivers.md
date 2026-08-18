# ERC / schematic-review waivers - bb-adc

Machine ERC is 0/0 (gate `erc` PASS, commit 1befa1e). This file records the
schematic-review WARNINGS that are accepted rather than fixed, and why. The single
ERROR (E1, the Kelvin sense not surviving the pour) was FIXED, not waived.

## netlist_audit: `power_no_consumers` on VREF - ACCEPTED
U1's REF pin is typed `passive` in the pulled symbol, so a declared power net feeds no
`power_in` pin. The netlist is correct and nothing downstream keys off pin type for
this net (`check_current` reads the net name). NOT hand-fixed on purpose:
`lib_pin_types.py` has no NC concept and was dry-run-confirmed to silently revert U2's
five `no_connect` pins, so a manual retype becomes a standing re-apply obligation for
a cosmetic warning.

## W1 reference headroom vs rail ripple - ACCEPTED AS ANALYSIS
The 87 mV DC margin was compared against DC tolerance alone, while the verified record
says tolerance + IR drop + ripple trough, and the owner's answered rail carries "tens
of mV" of noise. Accepted because the output capacitance answers it: ~49 uF against a
microamp load holds VOUT through input dips of microseconds, and a series-reference
dropout spec is a DC condition. No input RC is added - the scope tier excludes
filtering the datasheet does not require, and this analysis says it is not required.
BINDING CONSEQUENCE, now stated: the design is validated for a host rail whose DC
level stays at or above 3.135 V. Below that the margin is gone and no capacitor
recovers it.

## W5 C7 guaranteed-minimum capacitance - DEFERRED TO THE P8 BENCH
The 20x C_SH floor (960 pF for a 48 pF sampling cap) was checked on NOMINAL 1 nF; the
fitted J-grade part guarantees only 950 pF. Not fixed now because R6/C7 are explicitly
provisional pending `acquisition-settling` and `buffer-stability`. The bench must
choose C7 on its GUARANTEED minimum, with R6 present - the isolation resistor is what
lifts the pure-capacitive-load limit that would otherwise cap C7 at 1 nF.

## Not waivers - fixed or actioned elsewhere
- E1 Kelvin sense: FIXED (own net `/AGND_SENSE` + a single 0 ohm tie R8).
- W2 error budget computed on the wrong amplifier: RESTATED for the OPA320
  (RSS 3.25 / 3.42 mV, worst case 8.58 / 10.74 mV).
- W3 host power-up wait: RAISED 10 ms -> 50 ms.
- W4 J2 mis-mate is destructive: STATED on the sheet, on the silkscreen at P6, and in
  the design doc. No protection hardware (excluded by scope; the checklist asks for a
  statement).
- constraints.json VREF current 7 uA -> 14 uA max per the datasheet row. Nothing moves.
