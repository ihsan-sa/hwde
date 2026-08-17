# P0 Intake - digest (2026-08-16)

- Mode `learning block-basics:` -> block-only scope, canonical binding,
  geometry OUTPUT (no size stated, none invented; earned at P6).
- `requirements.md` written; `check_requirements.py` exit 0, 0 violations.
- Scope: MCU + datasheet-required support + the three connectors the brief
  states (J1 screw terminal 3V3 in, J2 debug, J3 4x GPIO). Protection,
  filtering, indicators, buttons, test points, straps, second rail: out.
- 3 questions asked in one batch, all defaults taken: 3.3 V is a bench/board
  rail and NOT a battery (last safety flag CLOSED); J2 = 5-pin
  3V3/SWDIO/SWCLK/NRST/GND with 3V3 sense-only; four plain digital GPIO.
- Owner then delegated design rulings ("best learning for the basic system"):
  H1-H4 become orchestrator-ruled digests. Gates, coverage, research, DFM and
  safety are untouched by that delegation.
- Fable out of credits -> every fable tier substituted one step up
  (fable/high -> opus/xhigh), logged in the spawn ledger.
- Library has 16 records, all buck-domain: expect P2/P3 coverage gaps.
