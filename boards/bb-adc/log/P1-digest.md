# P1 Research - digest

Roster: 2x component-scout (`adc`, `afe-support`), reference-design (`afe`),
power-architect. No `research-interface-spec`: SPI-into-an-unspecified-host and a
screw terminal bind no standard. Detail lives in research/*.md.

- Topology = attenuator -> low-Ibias RRIO buffer -> SAR + external reference.
  Ratiometric-to-+3V3 dead (+/-5 % rail = +/-250 mV vs a 5 mV budget, and nothing
  cancels: the source is not excited by that rail). Bufferless dead by
  t = (N+1)*ln2*(Rs+Rss)*Cs against the >=100 kohm input-impedance requirement.
- Leads: MCP3201 (C49274, separate VREF pin) / ADR4525A (C403698, 300 mV dropout
  leaves 335 mV at a 3.135 V rail) / LT5400B (C1739858) or a 0.01 %-2 ppm discrete
  pair / OPA333 (C30878). MCP3202 disqualified (VDD and VREF share one pin in
  SOIC-8); every >=16-bit-ACCURACY SAR in stock needs >=4.5 V AVDD.
- Rail +3V3 `direct` from J2, 11 mA, 36 mW, no thermal constraints, no AVDD/DVDD
  ferrite (one net, 100 nF per pin, unsplit pour).
- Rulings recorded: RSS claim (4.8 mV) with the 10.6 mV worst-case published beside
  it; no second rail; Extended tier for all four accuracy parts; non-ratiometric;
  input range must include 0 V; ADI-branded only for AD8605-pattern parts.
- Open for P2: source impedance and divider Rtot are ONE number pair and the
  answered specs are jointly impossible at 0.1 % (1 kohm into 100 kohm = 1 %).
  Matched networks cap near 100 kohm/element - network-grade matching and
  megohm-grade input impedance cannot both be had.
