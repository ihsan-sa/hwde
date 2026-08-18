# P0 Intake - digest

- Mode `learning block-basics:` -> scope **block-only**, binding **canonical**,
  stage none. Geometry is an OUTPUT: no size stated, none invented, `--outline auto`.
- `requirements.md` written; `check_requirements.py` exit 0 / 0 violations, mode leg live.
- Owner answered all 9 questions in one batch: **0.1 % class** at the terminal
  uncalibrated (+/-5 mV @25 C, +/-12 mV over 0-50 C), **SPI**, **3.3 V only on J2**,
  low-voltage bench source, Q4/5/6/7/9 at defaults.
- The problem this board teaches, fixed at P0: 0.1 % delivered THROUGH an attenuator
  that brings 0-5 V into a 3.3 V domain - ratio error and TCR are first-class terms
  beside the reference, not the converter's bit count.
- Safety: 5 V max on any net; mains/battery/motor/>30 V/high-I/RF do not apply, each
  contingent on the Q1 envelope (no isolation, no protection, input GND = host GND).
- Mode boundary for P1/P2: block-only excludes a second rail the block does not need
  *to work*; if 0-5 V from 3.3 V honestly needs one, that is support, and a decision.
- Owner then delegated design decisions ("decide yourself, best learning for the basic
  system"): H1-H4 become report-and-proceed; only a safety change re-blocks.
- Run-level: fable 5 out of credits -> every fable tier substitutes one step up.
- Defect: `modeslib.detect` skips `>`-lines, so a blockquoted brief silently disables
  the mode leg of the lint. Fixed here; `bb-mcu` has it too (reported, not touched).
