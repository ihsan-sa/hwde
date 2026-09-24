# Brief: pd-trigger-lite

Owner's words: "a simple pd trigger board like the showcase one ... No need to copy the
existing ... Ideally low cost ... the zips and component placement files so I can order
PCB cheaply from JLC".

Design intent (set by the dispatching planning session; unattended run - the owner is away,
every recipe question is decided here and recorded with state.py decision):
- USB-C PD SINK trigger, 2-layer, 1 oz, small (aim <= ~25 x 15 mm; bigger only if DRC needs it).
- CH224K (LCSC C970725) with its minimal application circuit.
- Voltage selectable after assembly with no tool beyond a soldering iron (solder jumpers /
  0R links), sensible assembled default 12 V.
- Output: VBUS + GND on two large 2.54 mm-compatible through-hole pads, no screw terminal.
  Rated 3 A (no e-marker, so 3 A is the cable/source ceiling).
- One power LED if it costs one basic resistor + one basic LED.
- A bulk/input cap per datasheet. No TVS/fuse unless the datasheet requires it.
- JLC BASIC parts everywhere possible; USB-C connector and CH224K are extended - cheapest
  widely stocked power-only receptacle exposing CC1/CC2.
- Deliverables: gerber zip, JLC BOM.csv + CPL.csv, order quote for qty 5 with assembly,
  owner guide PDF, README. Never place an order.
- Showcase boards/pd-trigger: learn from it, reuse its CH224K extraction, do not copy its
  layout or feature set.
