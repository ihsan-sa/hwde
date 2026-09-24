# pd-trigger-lite - sheet plan

One flat root sheet `kicad/pd-trigger-lite.kicad_sch`, pwr_base 1, generator
`kicad/gen/root.py`. 14 symbols, one chain, every cross-block net is a rail
(VBUS, GND) or a two-part stub - hierarchy would buy nothing.

Canonical nets: `VBUS`, `GND` (power symbols, bare); `/CC1`, `/CC2`, `/CFG1`,
`/SEL5`, `/SEL9`, `/SEL12`, `/SEL15`, `/SEL20` (resistor-to-switch nodes), `/LED_A`.
