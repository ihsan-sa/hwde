"""Merge solver op files (later files win) -> ops_final.json; also emit a frozen map."""
import json, sys

out_ops = sys.argv[1]
out_frozen = sys.argv[2]
merged = {}
for p in sys.argv[3:]:
    for o in json.load(open(p, encoding="utf-8"))["ops"]:
        merged[o["ref"]] = o
ops = [merged[r] for r in sorted(merged)]
json.dump({"version": 1, "ops": ops}, open(out_ops, "w", encoding="utf-8"), indent=1)
json.dump({o["ref"]: {"x": o["x"], "y": o["y"], "deg": o["deg"]} for o in ops},
          open(out_frozen, "w", encoding="utf-8"), indent=1)
print(json.dumps({"ops": len(ops)}))
