# P0 Intake - digest

- `requirements-analyst` read all five brief files and wrote `requirements.md` (627 lines).
  Both connector pin maps transcribed verbatim from the ICD; nothing invented.
- Closed decisions recorded as settled, not re-raised: D-01 (at power stage / af
  classification, budgets against af), D-02 (~2800 uF bank on the 48 V raw rail, 100 V
  parts, ~2.6 A series string, mandatory bleed), D-03 (UV bar out of scope), the ICD rail
  contract, the 802.3 port-capacitance clause, the full mechanical footprint including the
  30 x 26 mm RJ45 notch and three keepouts, and the corrected 8.5 W (af) / 18.5 W (at)
  budget.
- Safety flags raised: 48 V domain (57 V worst case), 2.6 A pulsed drive, 3.23 J stored
  energy with the cable unplugged, non-isolated topology floating at PoE potential
  (LED wiring and heatsink included), sealed-box ambient 56-69 C.
- Substantive finding: STR-REQ-01 (100-200 ms flash at FULL output) and the closed bank
  sizing are not consistent. 0.99 J over 150 ms is ~15 W of drive, not the briefs' 100 W.
  Folded into open question 2 rather than silently resolved.
- Source conflict recorded, not averaged: `05` gives 8.6-9.3 W (af) to the daughter, the
  ICD s6.2 gives 8.5 W total. Per the ICD's own precedence clause the ICD governs.
- 9 open questions produced. D-04 (white-only vs RGBW) is this board's to close.
- Tooling gap found while checking mechanics: `board_init.py` cannot cut the mandatory
  notch (BLOCKING-01, logged as a P0 decision).
