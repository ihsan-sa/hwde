# refdesign - sht4x (Sensirion SHT4x family: SHT40/41/43/45)

No matching file in reference/topologies/ - researched from Sensirion primary
sources (datasheet, handling instructions, design guide) plus two independent
carrier-board precedents. No component-scout shortlist existed yet for this
block at research time, so this assumes the generic SHT4x package (any grade)
unless noted.

Primary sources fetched and read in full (PDF -> text/image, not just search
snippets):
- [DS] Sensirion Datasheet - SHT4x, Version 6.5 - April 2024.
  https://sensirion.com/media/documents/33FD6951/661CD142/HT_DS_Datasheet_SHT4x.pdf
- [HI] Sensirion Handling Instructions for SHTxx, Version 9 - June 2025.
  https://sensirion.com/media/documents/6D95AA80/6840311F/HT_Handling_Instructions_SHTxx.pdf
- [DG] Sensirion Design Guide for Humidity and Temperature Sensors, Version 2 -
  March 2024.
  https://sensirion.com/media/documents/FC5BED84/662B494D/Sensirion_Humidity_Temperature_Design_Guide.pdf
- [I2C] NXP UM10204 I2C-bus specification and user manual, Rev. 7.0 - 2021
  (cited by [DS] Table 4 / section 4.2 for the mandatory Rp/Cb/trise numbers).
  https://www.nxp.com/docs/en/user-guide/UM10204.pdf
- [ADA] Adafruit SHT40/41/45 breakout, Pinouts page (independent carrier-board
  precedent - a real, shipped board, not Sensirion's own reference).
  https://learn.adafruit.com/adafruit-sht40-temperature-humidity-sensor/pinouts
- [XD] xdevs.com "TMP11X/SHT4X based precision thermometer/humidity sensor"
  (independent hobbyist/pro build with a real BOM and layout notes).
  https://xdevs.com/guide/xth/
- [QC] i2c.net Qwiic standards page (bus-capacitance framing for Qwiic
  chains). https://i2c.net/standards/qwiic/

## 1. Supply decoupling

**Decision: one 100 nF ceramic capacitor from VDD to GND, placed with the
shortest possible loop directly at the sensor's VDD/GND pins.**
- Source: [DS] Figure 1 "Typical application circuit" (p.3) shows exactly
  this: SH4x with SDA/SCL to the MCU, a 100 nF cap across VDD/GND at the
  sensor, and two pull-ups.
- Cross-check: [XD] independently lists "three 100 nF, X7R MLCC, 0402" - one
  per RH/T sensor on that board, confirming 100 nF as the field-standard
  value for this sensor family, not a Sensirion-only artifact.
- No additional bulk cap is datasheet-mandated at the sensor; bulk/local
  decoupling for the 3.3 V rail as a whole is the LDO block's concern, not
  this one.

## 2. I2C pull-up sizing (3.3 V bus, on-board SHT4x + Qwiic cable up to ~0.5 m)

**Decision: 2.2 kOhm per line (SDA, SCL), placed once, on this board (the I2C
host), not duplicated on any downstream Qwiic device.**

Reasoning chain (all inputs cited):
- [DS] Table 4 gives the mandatory floor for VDD >= 1.62 V: Rp,min = 390 Ohm
  (this is the sensor's own output-sink limit, not a system recommendation).
  It also gives the governing capacitance/rise-time relation used by the I2C
  spec: `Cb < trise / (0.8473 * Rp)`, with trise = 300 ns for Fast-mode (400
  kHz) and 120 ns for Fast-mode Plus - both numbers sourced from [I2C] and
  restated in [DS] section 4.2 ("follow mandatory capacitor and resistor
  requirements given in Table 4... following the interface specification of
  NXP's UM10204").
- Generic I2C-compliant sink capability (3 mA at VOL <= 0.4 V, per [I2C])
  gives a system Rp,min of roughly (3.3 - 0.4)/0.003 = ~970 Ohm if the design
  wants to stay interoperable with any Fast-mode device, not just the SHT4x's
  own looser 390 Ohm floor.
- Bus capacitance budget: on-board parasitics (SHT4x pins, STM32G0 I2C pins,
  a few cm of trace) are small (rule-of-thumb tens of pF); the Qwiic leg adds
  the JST-SH cable (up to ~0.5 m) plus one external device's pins. No
  Sensirion or SparkFun source gives an exact pF/m figure for the Qwiic
  cable specifically (flagged - see OPEN); as a stand-in, generic 4-wire
  ribbon/round cable runs ~40-50 pF/m (multiple cable-vendor datasheets),
  so 0.5 m contributes roughly 20-25 pF, plus another ~10-20 pF for a
  downstream IC's pins. Budgeting generously to ~150-200 pF total bus
  capacitance: `Rp,max = 300ns / (0.8473 * 200pF) ~= 1.8 kOhm` down to
  `300ns / (0.8473*150pF) ~= 2.4 kOhm` for Fast-mode (400 kHz).
- That places the valid window at roughly 1 kOhm (generic sink floor) to
  ~1.8-2.4 kOhm (rise-time ceiling at 400 kHz with the assumed cable/device
  load). **2.2 kOhm sits inside that window with margin on both sides** and
  still leaves headroom if the firmware only ever clocks the bus at
  Standard-mode 100 kHz (trise <= 1000 ns), which relaxes Rp,max further.
- Cross-check / precedent: [ADA]'s simple (non-chained) SHT40 breakout uses
  10 kOhm - fine for a short, single-device, no-cable-budget case, but too
  high once a 0.5 m external cable and a downstream device share the bus
  (10 kOhm pushes trise past the Fast-mode 300 ns limit for even modest added
  capacitance). [XD] deliberately omits on-board pull-ups on its sensor
  carrier and relies on the host board's resistors - i.e., pull-ups belong
  at the I2C host, which for this board is exactly this MCU/sensor board
  driving the Qwiic bus, confirming decision placement (not a distributed
  pull-up per node).
- OPINION (not vendor-sourced): if the architect later plans to daisy-chain
  more than one additional Qwiic device off this connector, revisit down to
  ~1.5 kOhm or add a bus buffer; 2.2 kOhm is sized for "this sensor + one
  Qwiic cable + one external device," per the brief's stated interface.

## 3. Thermal isolation (load-bearing item for this block)

The brief requires a thermal isolation slot/cutout OR, at minimum, distance
from the LDO and MCU. Sensirion's own guidance ([DG] section 3, "Thermal
Considerations") makes the case for doing both, cross-checked across two
distinct Sensirion documents ([DG] and [DS]) that address different halves
of the problem:

- **Why it matters, quantitatively**: [DG] p.8 states "at 90 %RH, a deviation
  of 1 degC will result in a deviation of the humidity signal of 5 %RH" -
  i.e., RH error scales roughly 5x the temperature error at high humidity.
  Heat conduction through the PCB from nearby power/digital parts (the
  brief's LDO and STM32G030) is called out as "the more severe and most
  common source of temperature deviations" ([DG] p.8).
- **Mitigation named explicitly** ([DG] p.8, Figure 8): "sufficient
  distances and removal of unnecessary metal around the sensor (e.g. trough
  milling or etching slits)"; "keep metal connections on the PCB as thin as
  possible"; a flex-PCB mount is offered as a stronger alternative (not
  applicable to this rigid 2-layer board).
- **Design-in rule of thumb** ([DG] section 3.3, p.10): "the sensor should be
  implemented as isolated as possible and as exposed to the environment as
  possible. In the best case with a flow of ambient air around the sensor."
  Figure 11 caption: "The sensor may be thermally decoupled from the PCB by
  small PCB connections."
- **Copper-under-sensor rule** ([DS] section 5.3, p.15): "There shall be no
  copper under the sensor other than at the pin pads," and "Soldering of the
  central die pad, as well as an exposed copper pad underneath it, is not
  recommended by Sensirion due to it acting as a heat sink which prevents
  the heater from functioning according to its specifications" - this is
  about the on-chip heater's own effectiveness (Table 10, p.16: junction-to-
  ambient thermal resistance is 246 K/W die-pad-soldered vs. 297 K/W
  die-pad-not-soldered; Sensirion bolds/recommends the higher-resistance,
  not-soldered configuration), a related but distinct mechanism from
  isolating the sensor from the LDO/MCU. Both point the same direction
  (minimize copper at the sensor island), so they reinforce rather than
  conflict.
- **Convection/radiation** ([DG] p.8-9, Figure 9): keep heat sources as far
  away as possible; consider airflow direction; the sensor "should not be
  exposed to heated air from other electronic components"; physically
  shielding with a wall also reduces dead volume (response-time benefit).
- **No numeric slot width or minimum clearance distance is published** by
  Sensirion in any of [DS]/[DG]/[HI] - the guidance is qualitative ("as thin
  as possible," "as far away as possible," "sufficient distance"). Any
  specific millimeter value for a slot geometry or LDO/MCU keepout below is
  therefore my OPINION for the layout step to adjust against the real
  floorplan, not a vendor number:
  - OPINION: route the sensor's 4 pads onto a small copper island connected
    to the rest of the board only by the 4 necessary signal/power traces
    (VDD, GND, SDA, SCL), each as narrow as the fab's DFM minimum trace
    width allows; mill/rout a U-shaped or full slot around the remaining
    three sides of that island where board outline and structural integrity
    allow.
  - OPINION: keep the sensor >= ~8-10 mm (or as much as the ~35x25 mm
    footprint honestly allows) from the LDO and MCU body outlines, on the
    board edge/corner with open sides for ambient air exchange, per [DG]
    Figure 17's "large opening... allows for good air exchange and reduces
    self-heating."
  - Do not route a ground/power pour under or through the sensor island
    beyond its own pads - a solid pour is itself "unnecessary metal" per
    [DG] Figure 8c/8d.
- This is a genuine engineering trade against the brief's soft ~35x25 mm
  size preference (section 5 of requirements.md) - isolating the sensor
  well may cost board area; per requirements.md the size preference yields
  to layout honesty, so isolation quality should not be sacrificed to hit
  the size target.

## 4. Handling / assembly constraints (JLC economy PCBA relevant)

- **Reflow profile**: standard reflow ovens are fine. Profile per IPC/JEDEC
  J-STD-020, peak 260 degC for up to 30 s, Pb-free, IR/convection reflow
  ([HI] section 2, p.4). This is standard JLC assembly practice - no special
  profile request expected to be needed.
- **No board wash** (load-bearing for the fab package): [HI] explicitly lists
  as a "Key Instruction": "Do not apply board wash." "The use of 'no clean'
  type >=3 solder paste is strongly recommended as it eliminates the need
  for a board wash, which can be harmful to the sensors" ([HI] p.4).
  Section 1.3 adds: "Avoid contact with cleaning agents, such as when
  washing the PCB after soldering, or strong air blasts from an air-pistol,
  as they can cause drift in the reading or complete breakdown of the
  sensor." **Action for the fab/order step**: this board must go through
  JLC's standard no-clean SMT process with NO post-assembly aqueous/board
  wash step selected; if JLC's PCBA order form or remarks field allows a
  note, add "no board wash - humidity sensor on board" explicitly. This is a
  real constraint on what can be told JLCPCB, not just a nicety.
- **No board-level cleaning after assembly** for the same reason - flag to
  whoever inspects/reworks the assembled boards on receipt.
- **Manual/rework soldering discouraged**: "Manual soldering is not
  recommended, and rework soldering should be limited to five seconds at up
  to 350 degC" ([HI] p.4). Given this board also has hand-soldered
  through-hole headers (per requirements.md section 7), keep the SHT4x well
  clear of any hand-soldering heat/flux path, and do not plan on hand rework
  of a marginal SHT4x joint - treat as scrap/replace.
- **Vapor-phase soldering not recommended** without a separate compatibility
  qualification ([HI] footnote 5, p.4) - moot if JLC uses standard IR/
  convection reflow (typical), but do not request vapor-phase.
- **Conformal coating / potting**: not in this board's scope (indoor, bare
  board per requirements.md section 4), but if ever added: use high-
  viscosity coating/potting that cannot flow into the sensor opening, or
  order the "P" protective-cover part variant designed for brush/spray-over
  coating ([DS] section 6.2; [HI] "Cover the sensing element during
  coating"). Do not use polyethylene antistatic bags for shipping/storage
  of loose parts ([HI] section 1.2) - a procurement/kitting note, not a
  board note.
- **MSL1** (IPC/JEDEC J-STD-020): recommended to process within 1 year of
  date of delivery ([DS] section 5.1; [HI] section 2) - routine reel/stock
  freshness note for procurement, no baking required at MSL1.
- **Post-reflow offset**: humidity reading may show a transient -1 to -2 %RH
  negative offset for 1-3 days after reflow before self-normalizing ([HI]
  p.4). Relevant to bring-up/test-limit setting later, not to the schematic
  or layout.

## 5. Placement relative to board edge / airflow / keepout

- Prefer a board edge or corner location with open space on 2-3 sides so the
  sensor has ambient air exchange rather than being boxed in by other parts
  ([DG] Figure 17 caption: "large opening on the top left corner allows for
  good air exchange and reduces self-heating of the whole device").
  Requirements.md doesn't specify an enclosure, so "board edge, away from
  other components" is the practical equivalent of that opening.
- No component or connector shroud should sit directly over the sensor's top
  aperture; the sensing element must remain physically exposed to room air.
- Keepout: nothing thermally significant (LDO, MCU, any future heater/high-
  current part) should be the sensor's nearest neighbor; the nearest
  neighbors should be low-power passives (e.g. the pull-ups/decoupling cap
  for this same net) if unavoidable.

## 6. Known errata / footguns

- **Heater**: max 10% duty cycle over the sensor's lifetime; die temperature
  (base + heater rise) must stay <= 125 degC; draws up to ~75 mA at the
  highest heater setting, so the 3.3 V rail/traces must tolerate that
  transient without provoking a brownout/reset if firmware ever uses the
  heater for creep mitigation or decontamination ([DS] section 4.9, p.14).
  The brief's rail budget (requirements.md section 3) does not currently
  reserve heater current - flag for the architect/power-budget step if
  heater use is planned.
- **VDD slew-rate limit**: supply slew rate between VDD,min and VDD,max must
  stay <= 20 V/ms during power-up or the sensor may reset ([DS] Table 4) -
  relevant to the LDO's soft-start/inrush behavior, already a brief
  requirement (section 3) for other reasons.
- **Clock stretching**: the SHT4x can stretch the I2C clock; the bus master
  (STM32G030 I2C peripheral/firmware) must tolerate this or reads can
  corrupt ([DG] section 4.4, p.13).
- **I2C address is fixed per part variant** (0x44 / 0x45 / 0x46 depending on
  ordering code, e.g. SHT40-xD1B = 0x44) and is not field-reconfigurable
  ([DS] Device Overview table; [XD] independently confirms "SHT45... cannot
  be reconfigured... default 0x44"). If a second SHT4x is ever added on the
  Qwiic chain, it must be ordered as a different address variant.
  This board uses one on-board sensor at the default address; no conflict
  expected unless a same-address SHT4x is plugged into the Qwiic port.
  Cross-check: [ADA], [XD] both confirm 0x44 as the common default marking.
  Cross-check: [DS] confirms the address is set by the ordering code
  ("xD1B" etc.), not a strap pin - no ADDR pin exists on this package.
- **ESD sensitivity**: mandatory EPA handling; "no mechanical force should
  be applied to any part of the sensor during assembly or usage" ([HI]
  section 1.1, section 2).
- **VOC/chemical sensitivity**: irreversible drift/damage possible from
  ketenes, acetone, ethanol, isopropyl alcohol, toluene, acids/bases, or
  outgassing epoxies/glues/adhesives near the sensor opening ([HI] section
  1.3). Relevant if this board is later potted or put in a sealed enclosure
  with adhesives.
- **Reversible "creep"** in sustained high humidity is a known, named
  Sensirion phenomenon, mitigated by periodic heater pulses; an irreversible
  long-term drift component also exists and is not heater-fixable ([DG]
  section 2.7). Not actionable at the schematic/layout stage; worth noting
  for firmware/test planning.
- **No exact Qwiic-cable capacitance figure found** from Sensirion or
  SparkFun (see OPEN below) - the pull-up sizing in section 2 uses a
  generic-cable stand-in, flagged explicitly.

## Interface-spec flags for later steps

- 100 nF decoupling cap must land immediately adjacent to the SHT4x VDD/GND
  pins (P4/layout).
- 2.2 kOhm x2 pull-ups (SDA, SCL to 3V3) on this board only, near the I2C
  host end (P3/schematic, P4/layout).
- Reserve board-edge/corner placement + thin/necked traces + slot-capable
  outline for the sensor island (P4/layout) - do not let the ~35x25 mm size
  target crowd this out (requirements.md section 5 already says size yields
  to layout honesty).
- Fab/order note: no board wash, no-clean paste, no vapor-phase reflow
  (P9/fab package or wherever assembly remarks are recorded).
