"""Bring architecture/constraints.json in line with the magjack swap.

Three staleness items flagged by the swap agent, plus the magjack isolation
separation entry the LEARNINGS entry asks for.
Idempotent.
"""
import io
import json
import sys

P = r'C:\dev\ai-ee3\boards\lumina-carrier\architecture\constraints.json'
d = json.loads(io.open(P, encoding='utf-8').read())

if 'LPJG0926HENL' in d.get('_comment', ''):
    print('already applied - no change')
    sys.exit(0)

# --- 1. the _comment describes a part the board no longer fits ---------------
c = d.get('_comment', '')
old = ("(2) research/interface-poe-48v.json's POE_TAP_A1/A2/B1/B2 are DELETED, not renamed: "
       "the selected magjack rectifies internally, so no centre-tap net exists on the board - "
       "see architecture/decisions.md D-A2.")
new = ("(2) SUPERSEDED AT P4: the board no longer uses an internally-rectified magjack. "
       "J1 is now a LINK-PP LPJG0926HENL (C22457393), which brings out four RAW line-side "
       "centre taps VC1..VC4 and has NO internal bridge. Two external bridges (D2 Alt-A, "
       "D3 Alt-B, ABS210/C2892567) rectify onto V48_RAW / V48_RTN. The centre-tap nets "
       "therefore DO exist on the board again - decisions.md D-A2 is superseded.")
if old in c:
    d['_comment'] = c.replace(old, new, 1)
    print('_comment: updated (D-A2 superseded)')
else:
    d['_comment'] = c + (' P4 UPDATE: J1 is a LINK-PP LPJG0926HENL (C22457393) with NO '
                         'internal bridge; two external bridges D2/D3 (ABS210) rectify the '
                         'four raw taps VC1..VC4 onto V48_RAW / V48_RTN.')
    print('_comment: appended (anchor not found, so appended instead)')

pl = d.setdefault('placement', {})

# --- 2. pd_front group must include the two new bridges ----------------------
grp = None
for g in pl.get('groups', []):
    if g.get('name') == 'pd_front':
        grp = g
        break
if grp is not None:
    members = grp.setdefault('members', [])
    for r in ('D2', 'D3'):
        if r not in members:
            members.append(r)
    print('pd_front members: %s' % members)
else:
    pl.setdefault('groups', []).append(
        {'name': 'pd_front', 'anchor': 'U1', 'members': ['D1', 'D2', 'D3']})
    print('pd_front group: created with D2/D3')

# --- 3. magjack chip-side / line-side separation -----------------------------
# check_creepage CANNOT see this barrier - it only derives spacing from working
# voltage (0.635 mm at 57 V) and the barrier is a hipot/vendor-guidance number.
# See LEARNINGS 2026-07-28 [check_creepage][gates][magnetics].
sep = pl.setdefault('separation', [])
if not any(s.get('reason', '').startswith('magjack isolation') for s in sep):
    sep.append({
        'a': ['J1'], 'b': ['U10', 'Y10', 'D10'],
        'min_mm': 1.4,
        'reason': ('magjack isolation barrier - chip-side to line-side. NOT derived from '
                   'working voltage, so check_creepage cannot enforce it; HALO app-note '
                   'guidance is 55 mils = 1.40 mm at this pitch. The J1 land itself was '
                   'edited to 1.451 mm at P4; this keeps neighbouring parts out of the gap.')})
    print('separation: added magjack isolation entry (1.40 mm)')

io.open(P, 'w', encoding='utf-8').write(json.dumps(d, indent=1, ensure_ascii=True))
allowed = {'high_speed', 'power', 'diff_pairs', 'voltages', 'thermal', 'placement', 'planes'}
extra = sorted(set(d) - allowed - {'_comment'})
print('schema check: non-schema keys =', extra or 'none (only _comment)')
print('placement subkeys:', {k: len(v) if isinstance(v, list) else v for k, v in pl.items()})
