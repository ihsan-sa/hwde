"""drcsum.py - one-line-per-kind summary of a kc.py drc report.

usage: python drcsum.py <report.json> [max_detail]
"""
import collections
import json
import sys

d = json.load(open(sys.argv[1], encoding="utf-8"))
limit = int(sys.argv[2]) if len(sys.argv) > 2 else 40
v = d.get("violations", [])
c = collections.Counter((x["check"], x["severity"]) for x in v)
print("status:", d.get("status"), "total:", len(v))
for (check, sev), n in sorted(c.items(), key=lambda kv: -kv[1]):
    print("  %-28s %-8s %d" % (check, sev, n))
shown = 0
for x in v:
    if x["check"] == "unconnected_items":
        continue
    if shown >= limit:
        print("  ... more suppressed")
        break
    shown += 1
    print("  * %s %s %s %s | %s" % (x["check"], x["severity"],
                                    x.get("layer"), x.get("refs"),
                                    x["msg"][:110]))
    for it in x.get("items", [])[:2]:
        print("      -", it["msg"][:110], it.get("pos"))
