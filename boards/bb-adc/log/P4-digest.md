# P4 Schematic - digest

- ONE schematic agent, FLAT root sheet (a child-sheet label exports as
  /<sheet>/<LABEL> and silently unhooks every constraints.json entry - the defect that
  cost lumina-par). 24 components, 14 canonical nets, 61/61 pins connected.
- Gate `erc` PASS 0/0 (2 attempts; commits 1befa1e then d1738e6). netlist_audit exit 0
  with one accepted warning (`power_no_consumers` on VREF - the REF pin is typed
  `passive` in the pulled symbol; not hand-retyped because lib_pin_types.py would
  silently revert U2's five no_connect pins).
- Adversarial review 1 error / 5 warnings. E1 was the important one and it overturned
  my own guidance: -IN on GND with the Kelvin intent carried by PLACEMENT does not
  survive the pour, because the pour TERMINATES pin 3 locally and the sense node stops
  being the string bottom at all. Fixed by giving it its own net /AGND_SENSE =
  {U1.3, R5.2, R8.1} with a single 0 ohm tie R8 - netlist-enforced, so every gate now
  checks it. Residual is the J1-return-to-string-bottom offset at sub-1 uV.
- Warnings actioned: the error budget had been computed on the OPA333 and was restated
  for the OPA320 actually fitted; the host power-up wait rose 10 -> 50 ms (charging
  49.2 uF at the reference's 10 mA limit is ALREADY 7-10 ms); J2's destructive
  mis-mate stated; C7's floor to be sized on GUARANTEED minimum at P8.
- The reviewer parsed the s-expression and the netlist directly rather than trusting
  the rendered PDF - which is how E1 was found at all.
