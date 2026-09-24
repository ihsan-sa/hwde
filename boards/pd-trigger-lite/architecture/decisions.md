# pd-trigger-lite - decisions (delegate answers, unattended run 2026-09-24)

- D1 CH224A (C42459160, $0.45) over the brief's CH224K (C970725): its VHV pin is rated
  32 V and takes VBUS directly, so the 1 k dropper (a 0.28 W resistor), the 10 k sense
  resistor and the CFG pull-ups all disappear, and WCH publishes an Rset table for it
  (it does not for CH224K). Net cheaper and safer. Requirements already named CH224A.
- D2 Rset mode with one link per voltage (9/12/15/20 V), 12 V shipped as a 0R. I/O mode
  cannot give "one link per voltage" with 3 CFG lines.
- D3 J1 6-pin power-only USB-C (C2798175, 20 V / 3 A rated, $0.067) instead of a 16-pin
  part: no D+/D- contacts, so DP/DM stay unconnected (PD negotiates on CC only). Chosen
  over C456012 (larger stock, but its listing rates 5 V).
- D4 No TVS, no fuse, no bulk capacitor: the datasheet requires none (only 1 uF on VHV);
  brief says none unless required. Risk noted in the guide: hot-plug spikes at 20 V; the
  showcase added a TVS for this.
- D5 Output pads are a board feature (unassembled 1x2 2.54 mm holes); no screw terminal.
- D6 LED on VBUS (not PG): PG's sink current is unpublished. 10k keeps it under 35 mW.
- D7 2-layer 1.6 mm 1 oz; VBUS sized for 3 A at dt 20 C; B.Cu GND pour.
