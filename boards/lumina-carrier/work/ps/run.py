import json, subprocess, sys, os
sys.stdout.reconfigure(encoding='ascii', errors='replace')
PY = r".venv\Scripts\python.exe"
SC = r".claude\skills\ai-ee\scripts\parts_search.py"
OUT = r"boards\lumina-carrier\work\ps"
def run(tag, args):
    p = subprocess.run([PY, SC] + args, capture_output=True, text=True)
    try:
        d = json.loads(p.stdout)
    except Exception:
        print(f"### {tag}: PARSE FAIL rc={p.returncode} {p.stdout[:200]} {p.stderr[:300]}")
        return
    with open(os.path.join(OUT, tag + ".json"), "w") as f:
        json.dump(d, f, indent=1)
    print(f"### {tag}  n={d.get('count')} src={d.get('source')}")
    for r in d.get("results", []):
        pb = {b['qty']: b['price'] for b in r.get('price_breaks') or []}
        p14 = pb.get(10) or pb.get(1) or r.get('price')
        print(f"  {r['lcsc']:<12} {r['mpn'][:38]:<38} {r.get('package','')[:18]:<18} {'B' if r.get('basic') else 'E'} stk={r.get('stock')} p1={r.get('price')} p10={p14} | {r.get('description','')[:75]}")
if __name__ == "__main__":
    spec = json.load(open(sys.argv[1]))
    for tag, args in spec:
        run(tag, args)
