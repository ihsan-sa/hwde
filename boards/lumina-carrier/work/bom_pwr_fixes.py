"""Fold the pwr-sheet BOM corrections into parts.json. Idempotent.

Source: P4 pwr sheet agent, after re-deriving the TPS16630 UVLO/OVP string to
meet the orchestrator's binding thresholds. The old 1M/12.4k/20k string failed
both (UVLO rising above the 37 V af legal minimum; OVP falling below the 57 V
legal PSE maximum).
"""
import io
import json
import sys

P = r'C:\dev\ai-ee3\boards\lumina-carrier\parts\parts.json'
d = json.loads(io.open(P, encoding='utf-8').read())
parts = d['parts']
by = {p.get('lcsc'): p for p in parts}

if 'C185284' in by:
    print('already applied - no change')
    sys.exit(0)

# --- 1. remove the two superseded, now single-use values -------------------
#   C17514 1M  0805 : was the UVLO top leg only (1M 0603 C22935 is a different
#                     line, used for the shield hybrid and crystal feedback)
#   C4328  20k 0805 : was the OVP bottom leg only
drop = {'C17514', 'C4328'}
before = len(parts)
parts[:] = [p for p in parts if p.get('lcsc') not in drop]
print('removed %d superseded lines: %s' % (before - len(parts), sorted(drop)))

# --- 2. add the two genuinely new values (stock verified this session) -----
tmpl = by['C149504']  # an existing 0805 1% thick-film line to copy shape from


def new_res(lcsc, mpn, value, package, basic, stock, price, role):
    e = {k: v for k, v in tmpl.items()}
    e.update({'lcsc': lcsc, 'mpn': mpn, 'value': value, 'package': package,
              'basic': basic, 'stock': stock, 'price': price,
              'ref_prefix_hint': 'R', 'block': 'pwr', 'role': role,
              'alternates': []})
    return e


parts.append(new_res(
    'C185284', 'RC0805FR-07620KL', '620k 1% 0805', '0805', False, 8603, 0.006,
    'R66 = UVLO/OVP string TOP leg (IN to UVLO) on U22. Replaces the 1M that failed '
    'the binding thresholds. Sees the full 57 V continuously. String is 620k/10k/12k, '
    'sum 642k, 74.8 uA at 48 V = 499x the 150 nA pin leakage. Alt C54921216 (30500 pcs).'))
parts[-1]['alternates'] = [{'mpn': 'HRC0805F6203FNTN', 'lcsc': 'C54921216'}]

parts.append(new_res(
    'C17444', '0805W8F1202T5E', '12k 1% 0805', '0805', True, 823002, 0.0041,
    'R73 = UVLO/OVP string BOTTOM leg (OVP to GND) on U22. Replaces the 20k that failed '
    'the binding thresholds. JLC Basic. Sets OVP rising 64.20 V / falling 60.03 V; '
    'worst-case-low falling 57.18 V stays above the 57 V legal PSE maximum.'))

# --- 3. re-role the lines whose usage changed -----------------------------
reroles = {
    'C30908': ('12.4k 1% 0805',
               'R1+R2 form the split 24.9k detection signature with the tap (poe), and '
               'W5500 EXRES1 bandgap-bias resistor to AGND (eth). NO LONGER the U22 '
               'UVLO middle leg - that moved to 10k (C17414) at the P4 re-derivation.'),
    'C17414': ('10k 1% 0805',
               'T2P level-shift network (poe), AND R67 = UVLO/OVP string MIDDLE leg '
               '(UVLO to OVP) on U22. Sets UVLO rising 35.02 V / falling 32.74 V; '
               'worst-case-high rising 36.42 V stays under the 37 V af legal minimum.'),
    'C21190': ('1k 1% 0603',
               'Series protection on /ID_ADC, /ADC0 and /ADC1 (expansion), AND R71 = '
               'PGOOD pull-up on U22. 330R was rejected there: it would sink 8.2 mA '
               'against the FLT/PGOOD 10 mA absolute maximum.'),
    'C149504': ('100k 1% 0805',
                'R70 = carrier-side bleed on +48V_SW (de-energises the connector 48 V '
                'pins whenever ENABLE is low), AND R62 = top leg of the mandatory U20 '
                'EN divider (EN abs max is 6 V; divider gives 2.56 V at 57 V).'),
    'C23162': ('4.7k 1% 0603',
               'I2C pull-ups CARRIER SIDE per ICD-01 s3.3 (daughters must not fit their '
               'own), AND R74 = bottom leg of the U20 EN divider.'),
    'C28233': ('100nF 100V X7R 0805',
               'U1 VDD-VSS bypass, inside the IEEE 802.3 50-120 nF detection-signature '
               'window, AND C61/C62/C63 = local HF bypass on the 48 V pins of U20 and '
               'U22, required by both datasheets.'),
}
for lcsc, (val, role) in reroles.items():
    e = by.get(lcsc)
    if e is not None:
        e['value'] = val
        e['role'] = role

io.open(P, 'w', encoding='utf-8').write(json.dumps(d, indent=1, ensure_ascii=True))
print('parts.json now %d lines' % len(parts))
for lc in ('C185284', 'C17444'):
    e = next(p for p in parts if p['lcsc'] == lc)
    print('  + %-10s %-16s basic=%-5s stock=%s' % (lc, e['value'], e['basic'], e['stock']))
