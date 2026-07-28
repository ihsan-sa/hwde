# Brief: pd-trigger (S14 run c - novel brief chosen by the user)

USB-C PD trigger/load board:
- USB-C receptacle, negotiating USB Power Delivery as a SINK
- PD sink controller (CH224-class or equivalent)
- Output voltage selectable among PD profiles (5/9/12/15/20V) via an
  onboard selector (DIP switch / jumper / button per architect's choice)
- Output on a screw terminal (plus an auxiliary 2.54mm header)
- Status indication: at least power-present; profile indication welcome
- Input protection appropriate for a bench tool (TVS; fusing if warranted)
- Power path sized for 5A CONTINUOUS (up to 100W at 20V) - copper, terminal
  and connector ratings must reflect this
- JLCPCB 2-layer, economy PCBA where possible, compact (~40x25mm target)
- Prototype qty 10; JLC Basic parts preferred
- Bench use, no enclosure, no battery
