# P4 Schematic + sim - digest

- ONE sheet (recorded): 14 refdes, 11 nets, 41/41 pins. ERC 0/0, netlist_audit
  0 violations, regenerate-and-compare identical. Gate `erc` PASS, committed.
- Load-bearing net verified in the NETLIST by a fresh reviewer, not the drawing:
  R5 returns to /VREF, U1 pin 6 REF driven by U2A as a true unity buffer, both
  OPA2333 units placed with power pins present.
- R6 REMOVED, reversing my own P3 call. Fig.15's ~35% overshoot is a UNITY-GAIN
  figure; U2B runs at noise gain 3.49. The bench reproducing Fig.15 exactly
  (32% at 1 nF unity) gives 6.6% for the as-built stage with none fitted.
  Board measures better without it: slope 139.235, -5% rail FS 3.0221 ->
  3.02513 V, span 99.974%.
- 11 benches / 76 bounds green. Six seeded defects verified to TRIP the gate;
  the analyst caught two defects in its own models; the removal exposed two
  stale bench constants - the sidecars caught their own author.
- Reviewer 0 errors / 5 warnings, nothing electrically wrong. Four FIXED (rail
  term missing from the error budget, an unqualified <2 ohm REF claim its own
  bench contradicts, a misattributed diamond number, a connector prefix that
  would break on re-annotate); one waived (J3 polarity - protection excluded).
- Text edits proven non-electrical: canonical netlist digest byte-identical,
  plus --compare showing 0 diffs and 0 renames.
