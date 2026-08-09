# P0 Intake digest - sbuck-5v3a

- Function: open-frame synchronous buck module. 7-18 V DC in (12 V nom) -> 5.0 V
  +/-2% at 3 A continuous (15 W). No MCU, no digital interface.
- Artifacts: `brief/brief.md`, `requirements.md` (analyst, 9/9 sections,
  check_requirements pass, 0 violations), `requirements-answers.md` (delegate).
- 33 open questions answered as DELEGATE per the brief's DECISION POLICY. No
  safety unknown was guessed: no mains, no battery, no motors, nothing >30 V, no
  RF transmit. 3.0 A sits ON the >3 A threshold - treated as high-current for
  copper/connector sizing, no certification path triggered.
- Binding constraints: 50 x 40 mm HARD (binds at P5 board_init), 4x M3 3.2 mm
  NPTH, 50 C free-air ambient with no airflow, every part LCSC-stocked.
- Derived arithmetic handed forward so P1/P2 do not re-derive: D = 0.71/0.42/0.28
  at Vin 7/12/18 V; Iin = 2.44/1.42/0.95 A; input-cap RMS current peaks at 1.50 A
  at Vin = 10 V (INSIDE the range, not at 12 V nominal); loss budget 2.05 W at
  the 88% efficiency floor.
- Riskiest item: thermal. 2.05 W by natural convection at 50 C ambient on a
  <=50x40 mm board with no heatsink is the binding case, and the brief forbids
  assuming the exposed pad alone closes it.
- Decisions recorded: 4-layer 1oz/0.5oz; 4 A slow-blow input fuse added beyond
  the brief's protection list; fsw target band 400-700 kHz; Opus substituted for
  Fable across judgment roles (out of credits) - recorded, not silent.
- Second-riskiest: input and output connectors are physically identical, so a
  user swap is a real failure mode. Resolution is silkscreen only (Q30).
