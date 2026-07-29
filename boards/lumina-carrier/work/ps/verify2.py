import json, subprocess, sys
sys.stdout.reconfigure(encoding='ascii', errors='replace')
PY = r".venv\Scripts\python.exe"; SC = r".claude\skills\ai-ee\scripts\parts_search.py"
out = json.load(open(r"boards\lumina-carrier\work\ps\verified.json"))
for c in ["C7430362","C380359","C185372","C4216","C25803","C176653"]:
    p = subprocess.run([PY, SC, "--query", c, "--limit", "5"], capture_output=True, text=True)
    d = json.loads(p.stdout)
    hit = next((r for r in d.get("results", []) if r["lcsc"] == c), None)
    if hit is None: print("MISS", c); continue
    out[c] = hit
    print(f"{c:<12} {hit['mpn'][:32]:<32} stk={hit['stock']:<8} p1={hit['price']} ds={'Y' if hit.get('datasheet') else 'N'}")
json.dump(out, open(r"boards\lumina-carrier\work\ps\verified.json","w"), indent=1)
print("total", len(out))
