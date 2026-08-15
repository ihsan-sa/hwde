# P0 Intake - digest (2026-08-15)

- bb-buck: non-isolated buck, 18-30 V DC in (24 nom) -> 5 V @ 0-2 A out, screw
  terminal both ends, bench supply + resistive load.
- Mode **ultra-bare-bones** recorded as a decision: buck block + datasheet-required
  support only. Defaults applied (qty 5, JLC PCBA single-sided, 0-50 C bench, no
  enclosure, fewest honest layers, smallest honest outline, stop at P9).
- requirements.md by `requirements-analyst`; `check_requirements.py` PASS 9/9, 0
  violations, before and after fold-in.
- Section 8 closed with NO safety question open, derived: bench source (no battery),
  resistive load (no motor), ~2.5 A peak (< 3 A), 30 V is not >30 V and < 60 V ES1.
- 4 questions asked in ONE batch, owner took all four defaults -> now requirements:
  A1 30 V hard max operating, part abs-max >= 36 V (headroom in the PART, no clamp);
  A2 no live hot-plug (drops the ~60 V ring case); A3 +/-3 % DC over full line+load,
  <= 50 mV pk-pk; A4 one switch-node probe pad + adjacent GND pad, nothing else.
- Left open for P1/P2: sync vs async rectification; 2L vs 4L (2L assumed, revisable
  on thermal grounds at ~0.8-1.8 W / 50 C ambient).
- Fable tier out of credits -> fable/high spawns run opus/xhigh (ledgered).
