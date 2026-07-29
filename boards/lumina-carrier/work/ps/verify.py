import json, subprocess, sys, os
sys.stdout.reconfigure(encoding='ascii', errors='replace')
PY = r".venv\Scripts\python.exe"
SC = r".claude\skills\ai-ee\scripts\parts_search.py"
codes = ["C337500","C140293","C32843","C5124114","C116592","C49208507","C1849461","C2913198",
"C2913204","C2913205","C2913197","C83836","C688857","C91754","C19724782","C37208","C7430403",
"C7430408","C70593","C19078191","C2891331","C19829453","C2987148","C19229","C65011","C2297",
"C2286","C2687129","C720477","C526032","C475920","C325964","C25804","C23162","C21190","C23138",
"C23345","C22935","C23130","C23223","C30908","C149504","C17514","C17719","C17414","C14663",
"C29936","C1779","C57112","C1588","C107045","C6119968","C5156756","C153036","C106243","C9196"]
out = {}
for c in codes:
    p = subprocess.run([PY, SC, "--query", c, "--limit", "5"], capture_output=True, text=True)
    d = json.loads(p.stdout)
    hit = next((r for r in d.get("results", []) if r["lcsc"] == c), None)
    if hit is None:
        print("MISS", c, [r["lcsc"] for r in d.get("results", [])])
        continue
    out[c] = hit
    print(f"{c:<12} {hit['mpn'][:34]:<34} {hit.get('package','')[:16]:<16} {'B' if hit.get('basic') else 'E'} stk={hit['stock']:<9} p1={hit['price']} ds={'Y' if hit.get('datasheet') else 'N'} brand={hit.get('brand','')[:20]}")
json.dump(out, open(r"boards\lumina-carrier\work\ps\verified.json","w"), indent=1)
print("saved", len(out))
