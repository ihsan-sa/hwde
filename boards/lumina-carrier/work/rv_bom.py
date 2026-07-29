import json, re, sys, collections
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

m = json.load(open(r"C:\dev\ai-ee3\boards\lumina-carrier\work\rv_map.json"))
comps = m['comps']
bom = json.load(open(r"C:\dev\ai-ee3\boards\lumina-carrier\parts\parts.json"))['parts']

sch = {}
for r, c in comps.items():
    lc = c['props'].get('LCSC') or c['props'].get('lcsc') or ''
    sch[r] = (lc, c['value'])

bomref = {}
for p in bom:
    for r in p.get('refs', []):
        bomref.setdefault(r, []).append((p.get('lcsc'), p.get('value'), p.get('qty_per_board')))

print("### refs in SCHEMATIC but not in parts.json refs")
for r in sorted(sch):
    if r not in bomref:
        print("   ", r, sch[r])
print("### refs in parts.json but not in schematic")
for r in sorted(bomref):
    if r not in sch:
        print("   ", r, bomref[r])
print("### refs with LCSC mismatch")
for r in sorted(sch):
    if r in bomref:
        lcs = [x[0] for x in bomref[r]]
        if sch[r][0] not in lcs:
            print("   ", r, "sch=", sch[r], "bom=", bomref[r])
        elif len(bomref[r]) > 1:
            print("   DUP", r, "sch=", sch[r], "bom=", bomref[r])
print("### qty_per_board vs actual count")
for p in bom:
    n = len(p.get('refs', []))
    q = p.get('qty_per_board')
    real = sum(1 for r in p.get('refs', []) if r in sch and sch[r][0] == p.get('lcsc'))
    if q != real:
        print("   %-10s %-32s qty=%s refs=%s actual_in_sch=%d" % (p.get('lcsc'), p.get('value','')[:32], q, p.get('refs'), real))
