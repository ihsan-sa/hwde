import json, re, sys, collections

d = json.load(open(r"C:\dev\ai-ee3\boards\lumina-carrier\work\rv_map.json"))
comps = d['comps']; nets = d['nets']

def key(r):
    m = re.match(r'([A-Za-z_]+)(\d+)', r)
    return (m.group(1), int(m.group(2))) if m else (r, 0)

mode = sys.argv[1] if len(sys.argv) > 1 else 'comps'

if mode == 'comps':
    filt = sys.argv[2] if len(sys.argv) > 2 else ''
    bysheet = collections.defaultdict(list)
    for r in comps:
        bysheet[comps[r]['sheet']].append(r)
    for sh in sorted(bysheet):
        if filt and filt not in sh:
            continue
        print("=" * 70)
        print("SHEET", sh)
        for r in sorted(bysheet[sh], key=key):
            c = comps[r]
            lcsc = c['props'].get('LCSC', c['props'].get('lcsc', ''))
            print("  %-6s %-28s %-14s %s" % (r, c['value'], lcsc, c['fp'].split(':')[-1]))
            for pin in sorted(c['pins'], key=lambda x: (len(x), x)):
                n, pf, pt = c['pins'][pin]
                print("        %-4s %-12s %-14s -> %s" % (pin, pf, pt, n))
elif mode == 'nets':
    pat = sys.argv[2] if len(sys.argv) > 2 else ''
    for n in nets:
        if pat and not re.search(pat, n, re.I):
            continue
        print("%-40s  %s" % (n, ", ".join("%s.%s(%s)" % (m[0], m[1], m[2]) for m in nets[n])))
elif mode == 'netlist':
    for n in nets:
        print("%-40s [%d]" % (n, len(nets[n])))
