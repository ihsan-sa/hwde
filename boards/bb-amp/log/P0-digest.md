# P0 Intake - digest

- Mode `learning block-basics:` -> scope `block-only`, binding `canonical`
  (geometry is an OUTPUT; P5 opens `--outline auto`).
- `requirements.md` written; `check_requirements.py` pass, 0 violations,
  sections 1-9, mode named. (opus/xhigh - fable tier unavailable, logged.)
- 10 questions batched in one round, all answered, appended as section 9a.
- Design-changing answers: excitation 3.3 V shared-ground (CM 1.65 V, so a
  single-supply in-amp stays viable); output span ~0.05-3.25 V with a positive
  pedestal (the brief's literal 0-3.3 V loses to its own rail); 12-bit usable
  calibrated (~5 uV RTI = drift + noise); flat within 1% at 1 kHz.
- Derived and binding: ~7 kHz -3 dB corner => ~1 MHz gain-bandwidth at gain
  ~150. Dominant part constraint; rules out low-power zero-drift in-amps.
- Carried to P2: the pedestal needs a low-impedance REF drive, or an in-amp
  with a high-impedance REF - a divider on a 3-op-amp REF kills CMRR.
- Owner delegated remaining judgment; H1-H4 are records, run stops at P9.
- Safety: no flags apply (3.3 V SELV bench board, milliamps).
