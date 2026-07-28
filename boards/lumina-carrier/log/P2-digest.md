# P2 Architecture digest - LUMINA carrier (LUM-CAR-A)

Artifacts: `blocks.md`, `power_tree.md`, `stackup.md`, `sheets.md`,
`constraints.json`, `connector-icd.md` (ICD-01), `decisions.md`.

- **Chain:** PoE magjack (integrated bridge) -> TPS2378-class PD interface ->
  100 V buck to 12 V -> sync buck to 3.3 V; 60 V eFuse gates 48 V to the daughter;
  W5500 + 25 MHz crystal on SPI2 IO_MUX at 20 MHz; ESP32-S3-WROOM-1-N8;
  split 2x7 power + 2x12 signal expansion connectors.
- **Stackup:** JLC04161H-3313, 4 layer, 1 oz. Forced by 100 ohm MDI (2L needs
  1.081 mm/leg), not by thermals.
- **Outline (MECH-02 proposal):** 100 x 80 mm, 3 mm radius, 4x M3 at 5 mm inset
  plus a 5th M3 at (46,74) for CAR-REQ-15. From 4410 mm2 of block area at 55-60 %
  utilisation; 80x60 needs 92 % and is impossible.
- **Budget re-derived** from the chosen parts, because the brief's "10 W regulated"
  describes a disqualified part: **8.6-9.3 W (af) / 18.7-20.0 W (at)** to the
  daughter. D-01's 8.5/18.5 W holds with margin. Carrier overhead 2.4/3.7 W.
- **Cost:** ~$26-32 per assembled carrier at qty 14 against a $30 provisional
  target. 12 carriers is ~$360 of a $500-1000 programme budget that also owes
  daughters, enclosures and a PoE switch.
- **Four sign-off gates drafted:** two-column af/at budget; PWM 4+4 across LEDC
  timers 0/1 (works for either D-04 answer); ENABLE fail-safe (one net, one 10k
  pull-down, on the only GPIO band with no power-up glitch); full 28-pin
  ESP32-S3 legality map.
- **constraints.json validated:** schema-clean (5 high_speed, 5 power, 2 diff_pairs,
  6 voltages, 1 thermal, 2 planes, placement edges/groups/separation).

## Deliberate omissions with a mandatory P5 recipe

`placement.keepouts` and `planes[].region` are absent **on purpose**: `board_init`
does not origin the outline at (0,0) - the origin comes from the packed component
bbox - so absolute rectangles cannot be authored at P2. `stackup.md` s7.1 carries
the exact P5 recipe: after `board_init`, read `reports/board_init.json.outline_bbox`
and patch `kicad/constraints.json` with the antenna keepout and the six plane
regions. **Skipping it leaves the ESP32-S3 antenna over a solid GND plane.**

## Three pipeline traps carried forward

1. `rules_gen` never reads `voltages` (grep-verified) - nothing makes the P7 router
   honour 0.60 mm 48 V clearance. Add a named `.kicad_dru` rule keyed on
   `A.NetName` (`A.Net` silently matches nothing) at P5.
2. `planes_gen` has no keepout key - the magjack plane void must be built from
   plane `region` rectangles or P8 `check_return_path` fails unwaivably.
3. `rules_gen` puts every power net in ONE Power netclass at the widest width, so
   +12V's 1.10 mm would be applied to V48_RTN's 0.6 A stub and to Freerouting's
   DSN - split `netclass_patterns` before `route_auto`.

## Riskiest decisions

1. **No LCSC PoE magjack publishes an 802.3at tap rating.** HR871150C's own 17.5 W
   two-tap figure disqualifies it; the stock-safe integrated-bridge part is only
   af-rated. D-01's at upgrade stays a board-level resistor change but acquires two
   non-board dependencies: magjack qualification and enclosure vents.
2. **The outline is permanent and two unanswered questions move it** - Q8 (radio)
   and Q4/Q12 (stack height vs the ~15 mm-tall RJ45). Recommendation: 11 mm
   standoff plus a 30x26 mm top-edge notch in every daughter, which doubles as a
   mechanical interlock against 180-degree mating.
