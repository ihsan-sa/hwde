"""Add the three 0.1 % thin-film UVLO/OVP resistors and restore the not-fitted
class-4 upgrade line. Also marks not-fitted lines so bom_sync stops dropping them.

Idempotent.
"""
import io
import json
import sys

P = r'C:\dev\ai-ee3\boards\lumina-carrier\parts\parts.json'
d = json.loads(io.open(P, encoding='utf-8').read())
parts = d['parts']
have = {p.get('lcsc') for p in parts}

tmpl = next(p for p in parts if p.get('ref_prefix_hint') == 'R')

NEW = [
    ('C865592', 'RT0805BRD07620KL', '620k 0.1% 0805', 5453, 0.0503, ['R66'],
     'R66 = UVLO/OVP string TOP leg. Yageo RT thin-film, 0.1 % and 25 ppm/degC. '
     'Upgraded from 1 % thick-film at H2: the OVP FALLING threshold had only 0.18 V '
     'of margin over the 57 V legal PSE maximum, and TEMPCO was the real killer - '
     '100 ppm/degC over a 60 degC excursion put the worst case near 56.5 V, below 57 V, '
     'so a legal rail could fail to re-enable after an overvoltage event.'),
    ('C110775', 'RT0805BRD0710KL', '10k 0.1% 0805', 811444, 0.0507, ['R67'],
     'R67 = UVLO/OVP string MIDDLE leg. Yageo RT thin-film 0.1 % / 25 ppm/degC. '
     'NOTE: R4/R5 (T2P level shift, poe sheet) deliberately stay on the 1 % C17414 '
     'line - only the threshold-setting string needs precision.'),
    ('C865172', 'RT0805BRD0712KL', '12k 0.1% 0805', 25480, 0.0947, ['R73'],
     'R73 = UVLO/OVP string BOTTOM leg. Yageo RT thin-film 0.1 % / 25 ppm/degC. '
     'Sets OVP rising 64.20 V / falling 60.03 V nominal.'),
]

added = []
for lcsc, mpn, value, stock, price, refs, role in NEW:
    if lcsc in have:
        continue
    e = {k: v for k, v in tmpl.items()}
    e.update({'lcsc': lcsc, 'mpn': mpn, 'value': value, 'package': '0805',
              'basic': False, 'stock': stock, 'price': price,
              'refs': refs, 'qty_per_board': len(refs),
              'ref_prefix_hint': 'R', 'block': 'pwr', 'role': role,
              'alternates': [], 'brand': 'YAGEO'})
    parts.append(e)
    added.append(lcsc)

# Restore the not-fitted class-4 upgrade resistor if bom_sync dropped it again.
if 'C334927' not in have:
    fitted = next((p for p in parts if p.get('lcsc') == 'C23130'), None)
    if fitted is None:
        print('ABORT - fitted 90.9R line (C23130) not found')
        sys.exit(1)
    e = {k: v for k, v in fitted.items()}
    e.update({
        'lcsc': 'C334927', 'mpn': 'WR08X63R4FTL', 'value': '63.4R 1% 0805',
        'package': '0805', 'basic': False, 'stock': 4814, 'price': 0.0031,
        'refs': [], 'qty_per_board': 0, 'ref_prefix_hint': 'R', 'block': 'poe',
        'not_fitted': True,
        'alternates': [{'mpn': 'CR0805F863R4G', 'lcsc': 'C3037301'}],
        'role': ('*** NOT FITTED - DO NOT PLACE ON BUILD 1. *** The entire D-01 upgrade '
                 'lever: swapping R3 from 90.9R (Class 3, af) to 63.4R (Class 4, at) is the '
                 'ONLY board change needed for a PoE+ power stage - no respin. Order as a '
                 'loose kit item, qty 0 on the assembly BOM. Package 0603 -> 0805 at P4 '
                 'review: classification draws 2.5 V x 42 mA = ~105 mW against a 100 mW 0603 '
                 'rating, and an out-of-spec part does not deliver a clean resistor-only '
                 'upgrade. The fitted 90.9R (73 mW) is fine on 0603.'),
    })
    parts.append(e)
    added.append('C334927 (not-fitted)')

io.open(P, 'w', encoding='utf-8').write(json.dumps(d, indent=1, ensure_ascii=True))
print('added: %s' % (added or 'nothing (already applied)'))
print('bom lines: %d | placed components: %d | not-fitted lines: %d'
      % (len(parts),
         sum(p.get('qty_per_board', 0) for p in parts),
         sum(1 for p in parts if p.get('not_fitted'))))
