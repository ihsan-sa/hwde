# Checklist: connector (every external connector)

- Pinout vs the MATING side (cable/debugger/host), not just internal nets;
  pin-1 convention stated and marked on silk.
- Power pins: polarity legend on silk visible AFTER assembly; reverse-plug
  consequence stated (protected or destructive - if destructive, flag).
- Mount style matches the exact orderable variant (vertical/RA, SMD/THT);
  shield strategy stated (chassis vs signal GND, one point or direct).
- Mechanical: retention (THT or SMD-with-anchors for force-loaded
  connectors); edge overhang intended; no tall part blocking mating.
- ESD protection expectation for user-facing connectors met or waived.
- Hand-solder access if not PCBA-assembled.
