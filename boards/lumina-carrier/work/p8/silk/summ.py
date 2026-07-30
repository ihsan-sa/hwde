import json, collections, sys
inv = json.load(open(r'C:/dev/ai-ee3/boards/lumina-carrier/work/p8/silk/inv.json', encoding='utf-8'))
fps = inv["footprints"]
print("total", len(fps))
print("sides", collections.Counter(f["side"] for f in fps))
print("rots", collections.Counter(f["deg"] for f in fps))
print("val visible", sum(1 for f in fps if not f["props"].get("value", {}).get("hidden", True)))
print("ref visible", sum(1 for f in fps if not f["props"].get("reference", {}).get("hidden", True)))
print("ref sizes", collections.Counter(tuple(f["props"]["reference"]["size"] or []) for f in fps))
print("ref thick", collections.Counter(f["props"]["reference"]["thickness"] for f in fps))
print("ref just", collections.Counter(tuple(f["props"]["reference"]["justify"]) for f in fps))
print("ref ldeg", collections.Counter(f["props"]["reference"]["ldeg"] for f in fps))
print()
byname = collections.Counter(f["name"] for f in fps)
for n, c in sorted(byname.items()):
    ex = [f for f in fps if f["name"] == n]
    print(f"{c:3d}  {n}   refs={[e['ref'] for e in ex][:6]}  local_ref={[(e['props']['reference']['lx'], e['props']['reference']['ly']) for e in ex][:4]}")
print()
print("silk graphic counts:", collections.Counter(len(f["silk"]) for f in fps))
print("nosilk fps:", [f["ref"] for f in fps if not f["silk"]])
