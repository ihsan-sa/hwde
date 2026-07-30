import collections
import json
import sys
from pathlib import Path

P = Path(sys.argv[1])
d = json.loads(P.read_text(encoding="utf-8"))
v = d.get("failing") or d.get("violations") or []


def kind(m):
    if "Reference field of" in m:
        return "REF:" + m.split()[-1]
    if "Value field of" in m:
        return "VAL:" + m.split()[-1]
    if " of " in m and " on " in m:
        what = m.split(" of ")[0]
        ref = m.split(" of ")[1].split(" on ")[0]
        return "%s:%s" % (ref, what)
    return m


c = collections.Counter()
for x in v:
    if x.get("check") != "silk_overlap":
        continue
    c[tuple(sorted(kind(i["msg"]) for i in x["items"]))] += 1
for k, n in sorted(c.items(), key=lambda t: -t[1]):
    print("%2d  %s" % (n, " <-> ".join(k)))
print("total silk_overlap:", sum(c.values()))
other = collections.Counter(x.get("check") for x in v
                            if x.get("check") != "silk_overlap")
print("other checks:", dict(other))
