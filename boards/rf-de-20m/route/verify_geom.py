"""rf-de-20m P7 - geometric acceptance on the ACTUAL fills.

The pour is the authority, not the planned rectangle (LEARNINGS 2026-08-08
[PIPELINE BUG][planes][constraints]).  Checks:
  1. B.Cu GND is ONE island spanning zone A to zone C (the RF return bridge)
  2. In1 / In2 carry NO copper under either spiral (a plane under a PCB
     air-core spiral is a shorted turn) - STRICT interior test, because the
     plane regions deliberately abut the keepout (LEARNINGS 2026-07-29
     [geometry][keepout][planes])
  3. per-net island counts and the coupling the tank pours add
"""
import sys

sys.path.insert(0, r'C:/dev/ai-ee3/.claude/skills/ai-ee/scripts')
from lib.geom import load_board                                    # noqa: E402
from shapely.geometry import Point                                 # noqa: E402

import os
PCB = os.environ.get('AIEE_PCB', r'C:/dev/ai-ee3/boards/rf-de-20m/kicad/rf-de-20m.kicad_pcb')
SPIRALS = [('L301', 72.0, 17.6, 20.550), ('L302', 85.0, 62.6, 20.285)]
EPS = 0.01

bg = load_board(PCB)
OX, OY = bg.outline.bounds[0], bg.outline.bounds[1]
fail = 0

print('=== 1. B.Cu GND bridge: one island, zone A <-> zone C')
cu = bg.net_copper('GND', 'B.Cu')
gs = [g for g in (cu.geoms if cu.geom_type == 'MultiPolygon' else [cu])
      if g.area > 0.5]
big = max(gs, key=lambda g: g.area)
x0, y0, x1, y1 = big.bounds
spans = (x0 - OX < 5) and (x1 - OX > 115)
print(f'  islands={len(gs)}  largest={big.area:.0f} mm2  '
      f'x {x0-OX:.1f}..{x1-OX:.1f} mm  spans A->C: {spans}')
if not spans:
    fail += 1
    print('  FAIL: B.Cu GND does not span zone A to zone C')

print('=== 2. In1 / In2 POUR under the spirals (strict interior)')
# the spirals' own In1+In2 inner-terminal bridge pads are the SPIRAL-4
# structure and are expected; only ZONE FILL there would be a shorted turn.
for layer in ('In1.Cu', 'In2.Cu'):
    total = 0.0
    for name, cx, cy, r in SPIRALS:
        disc = Point(cx + OX, cy + OY).buffer(r - EPS, quad_segs=128)
        a = 0.0
        for z in bg.zones_of(layer=layer):
            f = z.fill_on(layer)
            if f is not None and not f.is_empty:
                a += f.intersection(disc).area
        print(f'  {layer} pour under {name}: {a:.4f} mm2')
        total += a
    if total > 0.01:
        fail += 1
        print(f'  FAIL: {layer} pour intrudes under a spiral')

print('=== 3. per-net island counts (F.Cu)')
for net in ['GND', '+40V', '/SW', '/tank/TANK_A', '/tank/TANK_B',
            '/tank/RFOUT']:
    row = []
    for layer in bg.copper_layers:
        c = bg.net_copper(net, layer)
        if c.is_empty:
            continue
        g = [p for p in (c.geoms if c.geom_type == 'MultiPolygon' else [c])
             if p.area > 0.05]
        row.append(f'{layer}:{len(g)}i/{c.area:.0f}mm2')
    print(f'  {net:14s} ' + '  '.join(row))

print('=== 4. shunt capacitance the F.Cu pours add (nearest GND plane wins)')
E0 = 8.854e-12
# (layer, dielectric height below F.Cu, effective eps_r of that stack)
STACK = [('In1.Cu', 0.2444e-3, 4.05),
         ('In2.Cu', 1.3094e-3, 4.34),
         ('B.Cu', 1.5538e-3, 4.38)]
for net in ('/SW', '/tank/TANK_A', '/tank/TANK_B', '/tank/RFOUT'):
    top = bg.net_copper(net, 'F.Cu')
    if top.is_empty:
        continue
    seen, total, parts = None, 0.0, []
    for layer, h, er in STACK:
        g = bg.net_copper('GND', layer)
        if g.is_empty:
            continue
        ov = top.intersection(g)
        if seen is not None:
            ov = ov.difference(seen)          # shielded by a closer plane
        seen = ov if seen is None else seen.union(ov)
        if ov.area <= 0.01:
            continue
        c = E0 * er * ov.area * 1e-6 / h
        total += c
        parts.append(f'{layer} {ov.area:6.1f} mm2 -> {c*1e12:5.2f} pF')
    print(f'  {net:14s} total {total*1e12:6.2f} pF   ' + ' | '.join(parts))

print()
print('GEOM CHECKS:', 'PASS' if fail == 0 else f'{fail} FAIL')
sys.exit(1 if fail else 0)
