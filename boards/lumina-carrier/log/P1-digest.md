# P1 Research digest - LUMINA carrier (LUM-CAR-A)

Roster: 8 parallel agents - power-architect, refdesign-poe-pd, interface-poe-48v,
interface-ethernet, and 4 component scouts (connector-expansion, poe-power,
mcu-net, rail-protect). All 8 fragments written and JSON-validated.

## Findings that change the brief

- **The brief's named PD part is disqualified.** Si3402-B/-C AND Si3404 are IEEE
  802.3 Type 1 only (no Class 4 at any resistor value); Type 2 additionally needs
  2-event classification *recognition*, which is silicon. D-01's "resistor change,
  no respin" is unachievable with them. Skyworks' actual PoE+ parts are effectively
  unstocked on JLC. Consequence: the "~10 W regulated" figure in requirements 3.2
  comes from AN956 and describes a part this board cannot use - re-derive, do not
  inherit.
- **Lead pair: TPS2378DDAR (PD interface) + SCT2A25STER (100 V buck), ~$2.70 @30.**
  Class program 90.9R (class 3, af) -> 63.4R (class 4, at) = one 0603 change.
  Every at-capable PD IC on JLC that integrates a converter is transformer-based,
  so a non-isolated buck at Type 2 REQUIRES the two-chip solution.
- **48 V raw at "2 A continuous" is not deliverable by any PSE.** 2 A at 48 V is
  96 W on a 25.5 W supply. Resolution proposed: 2-3 A stays the connector PIN
  rating; load switch limits at 1.0 A with latch-off; ICD publishes 0.25 A (af) /
  0.5 A (at) sustained.
- **The 48 V load switch is a COMPLIANCE requirement, not just protection.**
  802.3 caps PD port capacitance near 180 uF; the strobe daughter holds ~2800 uF,
  so the switch must be off through PD power-up.
- **Carrier overhead is higher than the brief's 1.5 W:** 2.44 W (af) / 3.75 W (at)
  computed; the brief's chain double-counts regulator loss. ESP32-S3 + W5500 alone
  measure 0.70-0.76 W before converter losses.
- **HR911105A and all 7 other high-stock HanRun jacks are NOT PoE-capable.** Only
  4 PoE magjacks exist on LCSC. All three HanRun PoE jacks are JLC-assemblable
  (wave soldering), so THT is not an assembly blocker.
- **Fine-pitch mezzanine is closed by CAR-REQ-17.** Every 0.4-1.0 mm family JLC
  stocks rates 50-60 V. Pitch floor is >= 2.00 mm. 2.54 mm THT is the viable class.
- **The 15 mm standoff default is unachievable** (stocked 2.54 mm parts mate at
  11.0 mm), and at 11 mm a board-edge THT RJ45 (~13-16 mm tall) collides with the
  daughter board.

## Binding numbers for later phases

- Stackup: **4-layer JLC04161H-3313 required** - the only stackup with a diff_100
  profile (0.260/0.210). 2-layer computes to 1.081 mm per leg. Also independently
  forced by thermal (buck 1.35 W at dt_c 70 passes on 4L, fails on 2L).
- 48 V spacing: **0.60 mm outer / 0.10 mm inner** (IPC-2221B B2/B1, 51-100 V band).
  57 V < the IEC 62368-1 ES1 limit of 60 V, so this is functional insulation only.
- MDI: 2 pairs, 100 ohm diff, t_rise 3.0 ns, GND reference, max_skew 2.5 mm.
- W5500 SPI ceiling is **33.3 MHz guaranteed** (80 MHz is "theoretical design
  speed"). Recommend 20 MHz on SPI2 IO_MUX pins.
- ESP32-S3 forbidden pins: GPIO0/3/45/46 (strapping), GPIO19/20 (USB),
  GPIO35-37 on octal-PSRAM SKUs. Legal set proposed: SCLK 12 / MOSI 11 / MISO 13 /
  CS 10 / INT 14 / RST 21 with a 10k CS pull-up.
- 48 V and logic **share one ground**. The magjack's 1500 Vrms protects the PHY
  from the power, not the board from the cable - PoE taps the cable-side centre
  taps, bypassing the barrier by design.

## Two verified pipeline traps (recorded as decisions)

1. `rules_gen.py` never reads the `voltages` key - the 0.60 mm HV clearance is not
   enforced during routing and only surfaces at P8. Needs an explicit HV net class
   or `.kicad_dru` rule at P5.
2. `planes_gen` has no keepout key, so the magjack plane void must come from plane
   `region` rectangles, or P8 `check_return_path` fails unwaivably.

## Orchestrator process note

One decision record ("Power topology") was written before the corresponding scout
reported and without reading its file. The part numbers happened to match, but the
efficiency figures in it were not verified. A CORRECTION entry supersedes it; the
verified basis is `research/poe-power.md` section 0.
