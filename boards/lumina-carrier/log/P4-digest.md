# P4 Schematic digest - LUMINA carrier (LUM-CAR-A)

Artifacts: `kicad/lumina-carrier.kicad_sch` + `poe/pwr/eth/mcu/expansion` sheets,
`reports/lumina-carrier-schematic.pdf`, `reports/erc-waivers.md`,
`work/erc_final.json`, `work/netlist_audit.json`.

- **Gate `erc`: PASS, 0 errors / 0 warnings** (2 attempts recorded).
- **Netlist audit clean**; 109 placed components, 50 BOM lines.
- **Reviewer (fresh context) returned 19 findings** and independently verified all
  ten known-critical items as correct: R69 ENABLE fail-safe, TPS2378 EP-to-VSS,
  APD-to-RTN, the 1.2 V divider, the EN abs-max chain, W5500 RSVD asymmetry,
  GPIO45, the magjack map, and both frozen ICD pin maps.
- **Triage: 1 error to the fix loop, 7 fixed in copper, 2 fixed by ICD amendment
  (rev A6), 7 waived, 2 raised for the owner at H2.**

## The most important finding is an HONESTY item, not a defect

Because `lib_pin_types` types every non-supply pin `passive`, KiCad's
output-vs-output, input-not-driven and driver-conflict checks are structurally
**inert** on this schematic. The ERC 0/0 therefore proves only that no `power_in`
pin lacks a driver and no wire dangles. **Real pin-level coverage came from the
reviewer's per-IC datasheet audit, not from ERC**, and the design document must not
claim otherwise.

## Two findings fixed by amending the ICD rather than the board

- **FAULT sink current published as ~4.3 mA** (the schematic implied 0.33 mA).
  Publishing the real number is cheaper for daughters than a carrier respin plus a
  GPIO.
- **IMON governor claim softened**: the eFuse current-monitor pin's specified
  accuracy starts at 0.6 A while the rail's sustained limits are 0.25/0.5 A - both
  *below* the accuracy floor, so the closed-loop governor claim needed qualifying
  rather than asserting.

## H2 verdict: approved

Owner delegated the remaining decisions. Two items went to the owner and both were
resolved in favour of the recommendation: the 0.1 % OVP divider (taken, and
upgraded to thin-film for tempco - see P3) and the magjack choice (OPEN-A closed on
LPJG0926HENL).
