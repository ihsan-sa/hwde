"""Resync parts.json `refs` / `qty_per_board` from the exported netlist.

Reviewer finding 1 (the only ERROR): parts.json had drifted badly from the
schematic - refdes with no BOM line, lines with the wrong part, phantom lines,
and wrong quantities. The netlist is the authority: every component carries a
stamped LCSC property, so refs can be rebuilt rather than hand-maintained.

Reports, and does not silently hide, any component whose LCSC has no BOM line.
"""
from __future__ import annotations

import io
import json
import re
import sys
from collections import defaultdict

NET = r'C:\dev\ai-ee3\boards\lumina-carrier\work\bom_sync.net'
PARTS = r'C:\dev\ai-ee3\boards\lumina-carrier\parts\parts.json'

txt = io.open(NET, encoding='utf-8').read()

# Each (comp (ref "R12") ... ) block, up to the next (comp or (libparts
blocks = re.findall(r'\(comp\s+\(ref\s+"([^"]+)"\)(.*?)(?=\(comp\s+\(ref|\(libparts)', txt, re.S)
if not blocks:
    print('ABORT - parsed 0 components from the netlist')
    sys.exit(1)

ref_lcsc: dict[str, str] = {}
for ref, body in blocks:
    m = re.search(r'\(property\s+\(name\s+"LCSC"\)\s+\(value\s+"([^"]*)"\)', body)
    if m and m.group(1).strip():
        ref_lcsc[ref] = m.group(1).strip()
    else:
        ref_lcsc[ref] = ''

by_lcsc: dict[str, list[str]] = defaultdict(list)
for ref, lc in ref_lcsc.items():
    if lc:
        by_lcsc[lc].append(ref)


def natkey(r: str):
    m = re.match(r'([A-Za-z#]+)(\d*)', r)
    return (m.group(1), int(m.group(2) or 0))


d = json.loads(io.open(PARTS, encoding='utf-8').read())
parts = d['parts']

changed, dropped, unstamped = [], [], []
for p in parts:
    lc = p.get('lcsc')
    refs = sorted(by_lcsc.get(lc, []), key=natkey)
    old_refs = p.get('refs') or []
    old_qty = p.get('qty_per_board')
    if refs != old_refs or old_qty != len(refs):
        changed.append({'lcsc': lc, 'value': p.get('value'),
                        'refs_before': old_refs, 'refs_after': refs,
                        'qty_before': old_qty, 'qty_after': len(refs)})
    p['refs'] = refs
    p['qty_per_board'] = len(refs)

# Deliberately-unfitted lines (e.g. the D-01 class-4 upgrade resistor) have
# zero refs BY DESIGN and must survive the sync.
kept = [p for p in parts if p['qty_per_board'] > 0 or p.get('not_fitted')]
dropped = [{'lcsc': p['lcsc'], 'value': p.get('value'),
            'was_refs': p.get('refs')}
           for p in parts if p['qty_per_board'] == 0 and not p.get('not_fitted')]
d['parts'] = kept

bom_lcsc = {p['lcsc'] for p in kept}
orphans = sorted({lc for lc in by_lcsc if lc not in bom_lcsc})
unstamped = sorted(r for r, lc in ref_lcsc.items() if not lc)

io.open(PARTS, 'w', encoding='utf-8').write(json.dumps(d, indent=1, ensure_ascii=True))

print(json.dumps({
    'script': 'bom_sync',
    'components_in_netlist': len(ref_lcsc),
    'components_with_lcsc': sum(1 for v in ref_lcsc.values() if v),
    'bom_lines_before': len(parts),
    'bom_lines_after': len(kept),
    'lines_changed': len(changed),
    'lines_dropped_zero_refs': dropped,
    'netlist_lcsc_with_no_bom_line': orphans,
    'components_with_no_LCSC_property': unstamped,
    'total_placed_components': sum(p['qty_per_board'] for p in kept),
}, indent=1))
print()
for c in changed:
    print('  %-10s %-22s qty %s -> %s' % (c['lcsc'], str(c['value'])[:22],
                                          c['qty_before'], c['qty_after']))
