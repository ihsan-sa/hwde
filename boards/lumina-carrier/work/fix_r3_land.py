"""Move R3 (the D-01 class lever) from an 0603 to an 0805 land.

Reviewer finding 16: the FITTED 90.9R (Class 3, af) dissipates 73 mW during
classification - fine on 0603. The documented class-4 ALTERNATE 63.4R
dissipates ~105 mW against a 100 mW 0603 rating.

Classification is a sub-second transient so an 0603 would survive, but D-01's
whole promise is that the at upgrade is "a resistor change only, no respin",
and swapping in an out-of-spec part does not deliver that. Both values now sit
on an 0805 land, so the upgrade is genuinely clean.

Fitted:    90.9R 0805 C3000584 (9303 stock)
Alternate: 63.4R 0805 C334927 (4814 stock, already the parts.json not-fitted line)

Idempotent. Edits the generator, not the .kicad_sch.
"""
import io
import re
import sys

P = r'C:\dev\ai-ee3\boards\lumina-carrier\kicad\gen\poe.py'
s = io.open(P, encoding='utf-8').read()

if 'C3000584' in s:
    print('already applied - no change')
    sys.exit(0)

# 1. LCSC map: R3 fitted part 0603 -> 0805
n_lcsc = len(re.findall(r'"R3":\s*"C23130"', s))
s = re.sub(r'"R3":\s*"C23130"', '"R3": "C3000584"', s)

# 2. the documented not-fitted alternate 0603 -> 0805
n_alt = s.count('C23223')
s = s.replace('C23223', 'C334927')

# 3. the symbol R3 is placed on: 0603 -> 0805 body
before = s
s = re.sub(r'(sh\.add_component\(\s*)SYM_R0603(\s*,\s*"R3")', r'\1SYM_R0805\2', s)
n_sym = 0 if s == before else 1

# 4. value strings
n_val = 0
for old, new in (('"90.9R 1% 0603"', '"90.9R 1% 0805"'),
                 ('"63.4R 1% 0603"', '"63.4R 1% 0805"')):
    n_val += s.count(old)
    s = s.replace(old, new)

io.open(P, 'w', encoding='utf-8').write(s)
print('poe.py updated:')
print('  LCSC map R3 -> C3000584 (90.9R 0805)   [%d replacement(s)]' % n_lcsc)
print('  alternate C23223 -> C334927 (63.4R 0805) [%d]' % n_alt)
print('  symbol body 0603 -> 0805                 [%d]' % n_sym)
print('  value strings                            [%d]' % n_val)
if not (n_lcsc and n_sym):
    print('WARNING: expected anchors not all found - inspect poe.py for R3 before rebuilding')
