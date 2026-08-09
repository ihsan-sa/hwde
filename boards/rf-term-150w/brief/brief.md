# Standing assumptions (user said: do not ask, assume and record)

These are orchestrator-level assumptions handed to every downstream agent.
Every one of them must appear in the final README.

A1. **Band**: DC - 25 MHz. Fc = 25 MHz taken as the worst-case design point
    (highest residual-reactance mismatch). "Fc +/-10%" = 22.5 - 27.5 MHz;
    the design targets >= 20 dB from DC to 27.5 MHz, a superset.

A2. **Duty (left blank by the user)**: assume **CW, 100% duty, continuous**.
    This is the thermally worst case; a pulsed spec can only be easier. All
    thermal numbers in the README are steady-state CW at 150 W.

A3. **Ambient / cooling**: 25 C ambient, natural convection for the
    "derated air-cooled power" figure; forced-air / coldplate handled by
    quoting the required heatsink thermal resistance instead.

A4. **Mechanical**: the resistor bolts DIRECTLY to the user's heatsink or
    coldplate through its own flange holes. The PCB is a launch/interface
    carrier only, sits on the same surface, and is not in the thermal path.
    No heat is intentionally conducted through FR4.

A5. **Assembly**: hand-solder / bench build of 5. Not JLC PCBA (the flange
    resistor and the SMA jack are through-hole/mechanical parts; PCBA of a
    5-off with a bolt-down power part is not sensible). BOM+CPL are still
    produced as deliverables.

A6. **Adjustment element**: a shunt trimmer capacitor at the launch is the
    operator-adjustable reactance null. It must be reachable by a tuning
    tool with the board bolted down and the SMA cable mated (adjust from the
    top, no desoldering, no unbolting).

A7. **RF power vs DC test**: "DC resistance 50 ohm +/-2%" is met by the
    resistor element's own tolerance (+/-1% or +/-2% part). No trimming of
    the DC value is provided or required.

A8. **Cost**: the $40 / build-of-5 cap is BOM + bare PCB. PCB shipping and
    any tax are excluded (they are order-time, not design, costs) - if the
    cap still cannot be met, report the real number rather than degrading
    the design.

A9. **No ordering**: deliverables stop at fab artifacts (gerbers, drill, BOM,
    CPL) + README. The pipeline runs P0-P9; P10/ordering is not requested.
</content>
</invoke>
