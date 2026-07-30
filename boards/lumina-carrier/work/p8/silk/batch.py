"""Split the final ops into batches whose INTERMEDIATE board states are clean.

Edge(A,B) whenever A's new inked box overlaps B's old box (or vice versa): those
refs must land together or an intermediate state carries a silk overlap. Batches
are unions of connected components of that graph, packed to <= MAXB refs, so no
conflict ever crosses a batch boundary.
"""
import json, sys

MAXB = 25
BASE = r'C:/dev/ai-ee3/boards/lumina-carrier/work/p8/silk'
geom = json.load(open(f'{BASE}/geom.json', encoding='utf-8'))
fps = {f["ref"]: f for f in geom["footprints"]}
ops = json.load(open(sys.argv[1], encoding='utf-8'))["ops"]
M = 0.10


def shape(ref, ang):
    t = fps[ref]["ref_text"]
    w, h, off = ((t["inked_w0"], t["inked_h0"], t["off0"]) if ang == 0
                 else (t["inked_w90"], t["inked_h90"], t["off90"]))
    return (off[0] - w / 2, off[1] - h / 2, off[0] + w / 2, off[1] + h / 2)


old, new = {}, {}
for ref, f in fps.items():
    icx, icy, iw, ih = f["ref_text"]["inked"]
    old[ref] = (icx - iw / 2, icy - ih / 2, icx + iw / 2, icy + ih / 2)
for o in ops:
    s = shape(o["ref"], o["deg"])
    new[o["ref"]] = (s[0] + o["x"], s[1] + o["y"], s[2] + o["x"], s[3] + o["y"])


def hit(a, b):
    return not (a[2] + M < b[0] or a[0] - M > b[2]
                or a[3] + M < b[1] or a[1] - M > b[3])


refs = [o["ref"] for o in ops]
adj = {r: set() for r in refs}
for a in refs:
    for b in refs:
        if a >= b:
            continue
        if hit(new[a], old[b]) or hit(new[b], old[a]) or hit(new[a], new[b]):
            adj[a].add(b)
            adj[b].add(a)

seen, comps = set(), []
for r in refs:
    if r in seen:
        continue
    stack, comp = [r], []
    seen.add(r)
    while stack:
        c = stack.pop()
        comp.append(c)
        for n in adj[c]:
            if n not in seen:
                seen.add(n)
                stack.append(n)
    comps.append(sorted(comp))
comps.sort(key=len, reverse=True)

batches = []
for comp in comps:
    placed = False
    for b in batches:
        if len(b) + len(comp) <= MAXB:
            b.extend(comp)
            placed = True
            break
    if not placed:
        batches.append(list(comp))

opmap = {o["ref"]: o for o in ops}
out = []
for i, b in enumerate(batches, 1):
    p = f'{BASE}/ops_batch{i}.json'
    json.dump({"version": 1, "ops": [opmap[r] for r in sorted(b)]},
              open(p, "w", encoding="utf-8"), indent=1)
    out.append({"batch": i, "n": len(b), "file": p, "refs": sorted(b)})
json.dump(out, open(f'{BASE}/batches.json', "w", encoding="utf-8"), indent=1)
print(json.dumps({"batches": [(o["batch"], o["n"]) for o in out],
                  "biggest_component": len(comps[0]),
                  "components": len(comps)}, indent=1))
