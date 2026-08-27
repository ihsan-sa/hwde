# P4 Schematic digest - g0-sense (2026-08-27)

- 2 schematic-block agents + root stitch: 26 electrical refdes (+4 conditional
  M2 holes) on 2 sheets, 35 nets, 99/99 expected pins connected.
- Gate erc PASS 0/0 (attempt 2; re-run after the W3 fix). netlist_audit 0
  violations: 3 constraint nets, 20 refs, 5 decoupling associations.
- schematic-reviewer (fresh, adversarial): 0 errors / 3 warnings. It hunted and
  CLEARED every bring-up killer: TVS D1 orientation, SW1 contact pairing (settled
  by live-fetching the XKB datasheet), LED + tantalum polarity, AMS1117 pinout /
  cap types / dropout, the full STM32G030 pin map incl. I2C orientation and the
  BOOT0 strap, SHT40 pinout+EP, USB-C sink topology, decoupling, abs-max.
- Dispositions (reports/erc-waivers.md): W1 Qwiic ESD WAIVED (ecosystem norm,
  2 kV HBM endpoints, indoor bench env); W2 SHT4x VDD slew CLOSED as accepted
  risk (provenance IS on file; LDO is a follower so I/C is unreachable; the
  datasheet's failure mode is "a reset", which cold start produces anyway);
  W3 native DNP missing on J3/J4 FIXED, not waived.
- W3 fix (wo-w3-dnp): `(dnp yes)` on J3/J4 via new schlib.Sheet.mark_dnp() +
  refdes_class hand_install in parts.json; netlist proven identical (35/35 nets).
- Carried to P9: CPL rotation check for D1/D2/D10/C3, not only J1.
