# P0 Intake - digest

- buck-5v3a: 7-18 V (12 nom) -> 5 V / 3 A cont (15 W), screw terminals both
  ends, RPP on input, 50 C ambient natural convection, 50x40 mm HARD cap.
- requirements.md written; check_requirements.py pass (0 violations, 1-9).
- 11 open questions batched to user, ALL resolved; binding answers = section 10.
- Safety flags CLOSED by A1 (bench/adapter source): no load dump, no battery
  case, 0-50 C. A2 caps output at 3 A, no peak allowance. High-current
  consequences (copper, cap RMS, thermal vias) carried forward.
- User calls: P-FET RPP (not Schottky, thermal); JLC PCBA top-side SMT only,
  bottom = thermal/return plane; 4 A input fuse; LED + 3 TPs; 4x M3, 15 mm
  height; qty 5 proto; JLC Basic preference.
- Deviation: requirements-analyst ran opus/high, not fable/high - Fable 5 out
  of usage credits.
- Next P1: power-architect + scout(regulator) + scout(magnetics/protection)
  in parallel, then reference-design(buck stage). No interface-spec agent.
