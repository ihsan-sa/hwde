"""rf-de-20m P7 - which pre-routed WIRE wedges Freerouting's DSN reader?

fr_spiral_probe.py established:
  * the spirals' custom pad polygons are NOT the cause (v1/v2 still wedge);
  * the `(wiring)` scope is: with it emptied FR runs (v3), with only the vias
    kept it runs (v5), with only the wires kept it wedges (v4);
  * dropping just the four >2 mm land tracks is NOT enough (v6 wedges).

A healthy run prints "Job '...' started" ~1.5 s in and finishes in ~10 s, so
a 60 s budget is ample and a missing "started" line is the wedge signature.
This bisects the 34 wires by dropping candidate subsets.

Usage: python fr_wire_bisect.py           # runs the built-in ladder
"""
import json
import math
import re
import shutil
import sys
from pathlib import Path

S = r'C:/dev/ai-ee3/.claude/skills/ai-ee/scripts'
sys.path.insert(0, S)
sys.path.insert(0, S + '/lib')
from lib import env, routelib                                      # noqa: E402

WORK = Path(r'C:/dev/ai-ee3/boards/rf-de-20m/route/fr2')
BASE = WORK / 'base.dsn'
BUDGET = 90

WIRE_RE = re.compile(
    r'^\s*\(wire \(path (\S+) ([0-9.]+)\s+([-0-9.\s]+)\)\(net (\S+)\)')


def wires(text):
    """[(line_index, layer, width_um, length_um, net)] over the whole file."""
    out = []
    for i, line in enumerate(text.splitlines()):
        m = WIRE_RE.match(line)
        if not m:
            continue
        c = m.group(3).split()
        pts = [(float(c[k]), float(c[k + 1])) for k in range(0, len(c), 2)]
        ln = sum(math.dist(pts[k], pts[k + 1]) for k in range(len(pts) - 1))
        out.append((i, m.group(1), float(m.group(2)), ln, m.group(4)))
    return out


def build(text, drop_idx):
    keep = [ln for i, ln in enumerate(text.splitlines()) if i not in drop_idx]
    return '\n'.join(keep)


def run(name, text, drop_idx, tools):
    java, jar = tools
    dsn = WORK / ('%s.dsn' % name)
    dsn.write_text(build(text, drop_idx), encoding='utf-8')
    ses = WORK / ('%s.ses' % name)
    ses.unlink(missing_ok=True)
    f = routelib.run_freerouting(java, jar, dsn, ses, rung={'mp': 4},
                                 timeout=BUDGET,
                                 log_file=WORK / ('%s.log' % name))
    ok = f.get('session_completed') and f.get('ses_written')
    print('%-6s dropped %2d wires -> %s  (unrouted %s)'
          % (name, len(drop_idx), 'RUNS' if ok else 'WEDGES',
             f.get('unrouted')))
    return bool(ok), f


def main():
    cli = env.find_kicad_cli()
    java, _ = env.find_java()
    jar = env.find_freerouting_jar()
    tools = (java, jar)
    text = BASE.read_text(encoding='utf-8', errors='replace')
    w = wires(text)
    w.sort(key=lambda r: -(r[2] / r[3] if r[3] else 9e9))
    print('%d wires, widest-aspect first:' % len(w))
    for i, lay, wid, ln, net in w[:8]:
        print('   line %5d  w %8.1f  len %8.1f  aspect %7.2f  %s'
              % (i, wid, ln, wid / ln if ln else 9e9, net))

    results = {}
    # ladder: drop the N highest-aspect wires, N = 4, 5, 7, 9, 12, 34
    order = [r[0] for r in w]
    for n in (4, 5, 7, 9, 12, len(order)):
        name = 'b%02d' % n
        ok, f = run(name, text, set(order[:n]), tools)
        results[name] = {'dropped': n, 'runs': ok,
                         'aspect_cut': (w[n - 1][2] / w[n - 1][3]
                                        if n <= len(w) and w[n - 1][3] else None),
                         'unrouted': f.get('unrouted')}
        if ok:
            break
    (WORK / 'bisect.json').write_text(json.dumps(results, indent=1),
                                      encoding='utf-8')


main()
