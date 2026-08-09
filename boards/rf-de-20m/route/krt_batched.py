"""Fallback: route the remaining signal nets with KRT ONE NET AT A TIME.

The single batched invocation is cheaper when it converges, but it is
all-or-nothing: a 30-minute wall clock buys nothing if it does not finish.
Chaining per-net runs pays the startup cost each time and keeps every net
that does close.  Used only if `krt_finish.py` times out.
"""
import json
import os
import re
import shutil
import sys
from pathlib import Path

S = r'C:/dev/ai-ee3/.claude/skills/ai-ee/scripts'
sys.path.insert(0, S)
sys.path.insert(0, S + '/lib')
import route_critical as rc                                        # noqa: E402
import kc                                                          # noqa: E402
from lib import env, geom                                          # noqa: E402
from checklib import CheckError                                    # noqa: E402

PCB = Path(r'C:/dev/ai-ee3/boards/rf-de-20m/kicad/rf-de-20m.kicad_pcb')
WORK = Path(r'C:/dev/ai-ee3/boards/rf-de-20m/route/krtb')
PER_NET_S = int(os.environ.get('AIEE_KRT_NET_TIMEOUT', 420))
GRID = float(os.environ.get('AIEE_KRT_GRID', 0.05))
NET_RE = re.compile(r'\[([^\]]+)\]')

cli = env.find_kicad_cli()
if WORK.exists():
    shutil.rmtree(WORK)
WORK.mkdir(parents=True)
staged = WORK / PCB.name
for ext in ('.kicad_pcb', '.kicad_pro', '.kicad_dru', '.kicad_prl'):
    src = PCB.with_suffix(ext)
    if src.is_file():
        shutil.copy2(src, WORK / src.name)


SKIP = set(filter(None, os.environ.get(
    'AIEE_KRT_SKIP',
    'GND,+40V,/SW,/tank/TANK_A,/tank/TANK_B,/tank/RFOUT').split(',')))


def unrouted(rep):
    return sorted({m.group(1)
                   for v in rep['violations']
                   if v.get('check') == 'unconnected_items'
                   for i in v.get('items', [])
                   for m in [NET_RE.search(i.get('msg', ''))] if m} - SKIP)


def errs(rep):
    out = {}
    for v in rep['violations']:
        if v.get('severity') == 'error':
            out[v['check']] = out.get(v['check'], 0) + 1
    return out


rep = kc.run_drc(cli, staged, all_track_errors=True)
nets = unrouted(rep)
print('nets to route:', nets)
floors = rc.grading_floors(WORK / (PCB.stem + '.kicad_pro'))
fab = rc.write_fab_overrides(WORK, floors)
bg = geom.load_board(staged)
ncl = rc.build_net_clearances(WORK / (PCB.stem + '.kicad_pro'),
                              WORK / (PCB.stem + '.kicad_dru'), bg.nets)
ncl_file = WORK / 'net_clearances.json'
ncl_file.write_text(json.dumps(ncl or {}, indent=1), encoding='utf-8')
krt = env.find_krt()

done, failed = [], []
for net in nets:
    out = WORK / 'step.kicad_pcb'
    try:
        rc.run_krt(krt, 'route.py', staged, out, ['--nets', net],
                   floors, fab, GRID, PER_NET_S, net_clearances=ncl_file)
    except CheckError as exc:
        print(f'  {net}: FAILED ({exc})')
        failed.append(net)
        continue
    os.replace(out, staged)
    print(f'  {net}: routed')
    done.append(net)

kc.run_drc(cli, staged, refill=True, save_board=True)
after = kc.run_drc(cli, staged, all_track_errors=True)
print('routed:', done)
print('failed:', failed)
print('still unrouted:', unrouted(after))
print('after errors:', errs(after))
if len(unrouted(after)) < len(nets):
    shutil.copy2(staged, PCB)
    print('KEPT: copied back to', PCB)
else:
    print('DISCARDED: nothing closed')
