"""Restore the D-01 class-4 upgrade resistor to parts.json as a NOT-FITTED line.

bom_sync.py correctly rebuilt refs from the netlist, but that dropped C23223 -
the 63.4R class-4 alternate - because it has zero refs BY DESIGN. It is the
single component that makes D-01's "resistor change, no respin" promise real,
so it must stay in the BOM as a documented, deliberately-unfitted option.

Also acts on reviewer finding 16: the 0603 alternate dissipates ~105 mW during
classification against a 100 mW package rating. Restored as an 0805 instead.
Idempotent.
"""
import io
import json
import sys

P = r'C:\dev\ai-ee3\boards\lumina-carrier\parts\parts.json'
d = json.loads(io.open(P, encoding='utf-8').read())
parts = d['parts']

if any(p.get('lcsc') == 'C334927' for p in parts):
    print('already applied - no change')
    sys.exit(0)

fitted = next((p for p in parts if p.get('lcsc') == 'C23130'), None)
if fitted is None:
    print('ABORT - could not find the fitted 90.9R line (C23130)')
    sys.exit(1)

entry = {k: v for k, v in fitted.items()}
entry.update({
    'lcsc': 'C334927',
    'mpn': 'WR08X63R4FTL',
    'value': '63.4R 1% 0805',
    'package': '0805',
    'basic': False,
    'stock': 4814,
    'price': 0.0031,
    'refs': [],
    'qty_per_board': 0,
    'ref_prefix_hint': 'R',
    'block': 'poe',
    'alternates': [{'mpn': 'CR0805F863R4G', 'lcsc': 'C3037301'},
                   {'mpn': '0805W8F634JT5E', 'lcsc': 'C17786'}],
    'role': ('*** NOT FITTED - DO NOT PLACE ON BUILD 1. *** This is the entire D-01 upgrade '
             'lever: swapping R3 from 90.9R (Class 3, 802.3af) to 63.4R (Class 4, 802.3at) is '
             'the ONLY board change needed to move to a PoE+ power stage - no respin. Ordered '
             'as a loose kit item, qty 0 on the assembly BOM. '
             'PACKAGE CHANGED 0603 -> 0805 at P4 review (finding 16): classification draws '
             '2.5 V x 42 mA = ~105 mW, against a 100 mW 0603 rating. Sub-second transient so an '
             '0603 would survive, but D-01 promises a clean resistor-only upgrade and an '
             'out-of-spec part does not deliver that. The fitted 90.9R (73 mW) is fine on 0603.'),
})
parts.append(entry)

io.open(P, 'w', encoding='utf-8').write(json.dumps(d, indent=1, ensure_ascii=True))
print('restored C334927 63.4R 0805 as a NOT-FITTED upgrade line')
print('bom lines now: %d (placed components unchanged: %d)'
      % (len(parts), sum(p.get('qty_per_board', 0) for p in parts)))
