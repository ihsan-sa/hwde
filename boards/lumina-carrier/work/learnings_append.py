"""Append the check_creepage blind-spot learning. Re-reads immediately before
writing so a concurrent run's append is not clobbered. Idempotent on the title.
"""
import io

P = r'C:\dev\ai-ee3\LEARNINGS.md'
TITLE = ("## 2026-07-28 [check_creepage][gates][magnetics] check_creepage only knows working VOLTAGE, "
         "so it cannot see a magjack isolation-barrier collapse")

ENTRY = TITLE + """
`check_creepage.py` derives required spacing from `constraints.json.voltages` via IPC-2221B - i.e.
purely from the DC working voltage between two nets. On a PoE board the 48 V domain gives 0.635 mm
(51-100 V band) and everything passes at that number.

That is the wrong model for an RJ45 magjack. The barrier that matters there is **chip-side to
line-side**, and it is not sized by the 57 V working voltage at all - it is sized by the cable-side
hipot requirement (1500 Vrms / 2250 VDC) and by the vendor's own land-pattern guidance. HALO's app
note asks **55 mils = 1.40 mm** at 2.54 mm pitch. `check_creepage` will happily pass a 1.05 mm gap,
because 1.05 mm > 0.635 mm and the checker has no concept of an isolation barrier.

Found on lumina-carrier while evaluating a replacement magjack: the candidate's land pattern
collapsed the chip-side/line-side pad gap from 3.58 mm to **1.05 mm** - a real defect that no gate in
the pipeline would have flagged. The P8 verify suite would have been green.

Recognise it whenever a part carries an isolation barrier that is NOT a function of the board's own
rail voltages: Ethernet magnetics, opto-isolators, isolated DC-DC, digital isolators, mains-facing
anything. For those, the spacing requirement comes from the *part's* datasheet and the safety
standard, not from `voltages[]`, and it must be enforced by hand - a `.kicad_dru` rule keyed on
`A.NetName`, plus a placement `separation` entry - and checked by a human reading the land pattern.

Related trap already recorded: `rules_gen.py` never reads the `voltages` key at all, so even the
0.635 mm figure is not enforced during routing and only surfaces at P8.
"""


def main() -> None:
    text = io.open(P, encoding='utf-8').read()
    if TITLE in text:
        print('already present - no change')
        return
    sep = '' if text.endswith('\n\n') else ('\n' if text.endswith('\n') else '\n\n')
    io.open(P, 'a', encoding='utf-8').write(sep + ENTRY)
    print('appended learning (%d chars)' % len(ENTRY))


main()
