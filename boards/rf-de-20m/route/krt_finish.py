"""rf-de-20m P7 - route the remaining signal nets with KRT.

Freerouting 2.2.4 WEDGES reading this design (rung1 log stops after the
version banner, no pass lines, no SES) - the documented failure mode on a
board that already carries router-generated copper, and this one carries a
lot of it.  route_auto's own KRT fallback then measured "not strictly better"
because `grading_floors` takes the LOOSEST netclass clearance as KRT's base,
and the HV power classes had been raised to 0.8 mm for Freerouting's benefit -
so KRT tried to route the buck's 0.4 mm-pitch signals at 0.8 mm clearance.

This drives KRT directly at the 0.2 mm routing floor with an explicit
--net-clearances map (built from the .kicad_pro AND the .kicad_dru, so the
HV nets keep their 0.5-0.8 mm), which is the sanctioned path for a DRU-only
clearance to reach the router.
"""
import json
import os
import shutil
import sys
from pathlib import Path

S = r'C:/dev/ai-ee3/.claude/skills/ai-ee/scripts'
sys.path.insert(0, S)
sys.path.insert(0, S + '/lib')
import route_critical as rc                                        # noqa: E402
import kc                                                          # noqa: E402
from lib import env, geom                                          # noqa: E402

PCB = Path(r'C:/dev/ai-ee3/boards/rf-de-20m/kicad/rf-de-20m.kicad_pcb')
WORK = Path(r'C:/dev/ai-ee3/boards/rf-de-20m/route/krt')
TIMEOUT = int(os.environ.get('AIEE_KRT_TIMEOUT', 1800))
GRID = float(os.environ.get('AIEE_KRT_GRID', 0.05))

cli = env.find_kicad_cli()
WORK.mkdir(parents=True, exist_ok=True)
staged = WORK / PCB.name
for ext in ('.kicad_pcb', '.kicad_pro', '.kicad_dru', '.kicad_prl'):
    src = PCB.with_suffix(ext)
    if src.is_file():
        shutil.copy2(src, WORK / src.name)

before = kc.run_drc(cli, staged, all_track_errors=True)


def errs(rep):
    out = {}
    for v in rep['violations']:
        if v.get('severity') == 'error':
            out[v['check']] = out.get(v['check'], 0) + 1
    return out


b = errs(before)
import re                                                          # noqa: E402
NET_RE = re.compile(r'\[([^\]]+)\]')
nets = sorted({m.group(1)
               for v in before['violations']
               if v.get('check') == 'unconnected_items'
               for i in v.get('items', [])
               for m in [NET_RE.search(i.get('msg', ''))] if m}
              - {'GND'})   # plane-carried: handing KRT GND blew 1800 s
print('before errors:', b)
print('unrouted nets:', nets)

bg = geom.load_board(staged)
floors = rc.grading_floors(WORK / (PCB.stem + '.kicad_pro'))
print('KRT floors:', floors)
fab = rc.write_fab_overrides(WORK, floors)
ncl = rc.build_net_clearances(WORK / (PCB.stem + '.kicad_pro'),
                              WORK / (PCB.stem + '.kicad_dru'), bg.nets)
ncl_file = None
if ncl:
    ncl_file = WORK / 'net_clearances.json'
    ncl_file.write_text(json.dumps(ncl, indent=1), encoding='utf-8')
    print('net clearances:', {k: v for k, v in ncl.items() if v > 0.2})

krt = env.find_krt()
out = WORK / 'krt_out.kicad_pcb'
sink = []
summary = rc.run_krt(krt, 'route.py', staged, out, ['--nets', *nets],
                     floors, fab, GRID, TIMEOUT,
                     net_clearances=ncl_file, stdout_sink=sink)
print('KRT summary:', json.dumps(summary)[:600])
(WORK / 'krt_stdout.log').write_text('\n'.join(sink), encoding='utf-8')
os.replace(out, staged)
kc.run_drc(cli, staged, refill=True, save_board=True)
after = kc.run_drc(cli, staged, all_track_errors=True)
a = errs(after)
print('after errors:', a)
print('delta:', {k: a.get(k, 0) - b.get(k, 0) for k in set(a) | set(b)})

# keep it only if the routing actually closed and nothing new broke
gained = {k: a.get(k, 0) - b.get(k, 0) for k in set(a) | set(b)}
new_kinds = set(a) - set(b)
if a.get('unconnected_items', 0) < b.get('unconnected_items', 0) and not new_kinds:
    shutil.copy2(staged, PCB)
    print('KEPT: copied back to', PCB)
else:
    print('DISCARDED: new error kinds', new_kinds, 'delta', gained)
