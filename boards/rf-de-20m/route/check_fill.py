"""rf-de-20m P7 - measure the ACTUAL fills: per net/layer island count, and
which pads each net's copper reaches.  The fill is the authority, not the
planned rectangle (LEARNINGS 2026-08-08 [PIPELINE BUG][planes][constraints]).
"""
import sys
sys.path.insert(0, r'C:/dev/ai-ee3/.claude/skills/ai-ee/scripts')
from lib.geom import load_board                                    # noqa: E402
from shapely.ops import unary_union                                # noqa: E402

PCB = r'C:/dev/ai-ee3/boards/rf-de-20m/kicad/rf-de-20m.kicad_pcb'
NETS = ['GND', '+40V', '/SW', '/tank/TANK_A', '/tank/TANK_B', '/tank/RFOUT']

bg = load_board(PCB)
OX, OY = bg.outline.bounds[0], bg.outline.bounds[1]

for net in NETS:
    print(f'=== {net}')
    for layer in bg.copper_layers:
        cu = bg.net_copper(net, layer)
        if cu.is_empty:
            continue
        geoms = list(cu.geoms) if cu.geom_type == 'MultiPolygon' else [cu]
        geoms = [g for g in geoms if g.area > 0.05]
        print(f'  {layer:8s} area={cu.area:8.1f} mm2  islands={len(geoms)}')
        if len(geoms) > 1:
            for g in sorted(geoms, key=lambda g: -g.area)[:8]:
                x0, y0, x1, y1 = g.bounds
                print(f'      {g.area:8.2f} bbox_local=[{x0-OX:6.1f},'
                      f'{y0-OY:6.1f},{x1-OX:6.1f},{y1-OY:6.1f}]')
    # pads not touched by any copper of their own net
    miss = []
    for p in bg.pads_of(net=net):
        ok = False
        for layer in p.layers:
            cu = bg.net_copper(net, layer)
            if not cu.is_empty and cu.distance(p.poly) < 1e-6:
                ok = True
                break
        if not ok:
            miss.append(f'{p.ref}.{p.number}')
    if miss:
        print(f'  PADS WITH NO OWN-NET COPPER: {sorted(set(miss))}')
