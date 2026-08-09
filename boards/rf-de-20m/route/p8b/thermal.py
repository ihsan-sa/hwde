"""rf-de-20m P8-b - theta_BS and Tj, before and after the E3/E5 fixes.

The bulk (board-through) leg reproduces the P8 review's realistic model
EXACTLY - same spreading lengths (3.38 / 4.65 / 2.23 mm), same effective areas
(110 / 392 / 589 mm2), same 7.3 C/W at 18 vias - so the two are directly
comparable and only the via count and the mask term change.
"""
import math
import sys
sys.path.insert(0, r'C:/dev/ai-ee3/.claude/skills/ai-ee/scripts')
from lib.geom import load_board
from shapely.geometry import Point

PCB = r'C:/dev/ai-ee3/boards/rf-de-20m/kicad/rf-de-20m.kicad_pcb'
OX, OY = 6.634999, 39.334999
K_CU, K_FR4 = 400.0, 0.30
T_OUT, T_IN = 35e-6, 15.2e-6            # 1 oz outer, 0.5 oz inner
H = (0.2444e-3, 1.065e-3, 0.2444e-3)    # F-In1, In1-In2, In2-B
T = (T_OUT, T_IN, T_IN)
SRC = (2.65, 4.90)                      # die-pair land envelope, mm
BOARD_T = 1.6e-3
PLATE = 20e-6                           # JLC barrel plating, spec floor ~18-20 um


def bulk():
    a, b = SRC
    R = 0.0
    for h, t in zip(H, T):
        lam = math.sqrt(K_CU * t * h / K_FR4) * 1e3       # mm
        a, b = a + 2 * lam, b + 2 * lam
        A = a * b * 1e-6
        R += h / (K_FR4 * A)
    return R


def r_via(plate=PLATE):
    ri = 0.15e-3
    A = math.pi * ((ri + plate) ** 2 - ri ** 2)
    return BOARD_T / (K_CU * A)


def array_R(dists, plate=PLATE):
    """Parallel sum over vias, each = F.Cu lateral access + barrel.
    Lateral access is radial spreading in the 35 um outer copper,
    ln(r/r0)/(2.pi.k.t), r0 = equivalent radius of the die-pair source."""
    r0 = math.sqrt(SRC[0] * SRC[1] / math.pi)
    per = 1.0 / (2 * math.pi * K_CU * T_OUT)
    rb = r_via(plate)
    g = 0.0
    for r in dists:
        lat = per * math.log(max(r, r0) / r0)
        g += 1.0 / (lat + rb)
    return 1.0 / g if g else float('inf')


bg = load_board(PCB)
c1 = Point(31.5 + OX, 22.9 + OY)
c2 = Point(31.5 + OX, 27.1 + OY)
d = [min(Point(v.at).distance(c1), Point(v.at).distance(c2))
     for v in bg.vias_of() if v.net == 'GND']
d = sorted(x for x in d if x <= 5.0)
RB = bulk()
print(f'bulk board-through (pair)          {RB:6.2f} C/W')
print(f'single 0.3 mm barrel, {PLATE*1e6:.0f} um plating  {r_via():6.1f} C/W'
      f'   (25 um: {r_via(25e-6):.1f})')
print(f'  epoxy POFV fill adds  '
      f'{1.6e-3/(0.6*math.pi*0.15e-3**2):.0f} C/W in parallel -> '
      f'{100*(r_via())/(1.6e-3/(0.6*math.pi*0.15e-3**2)):.1f} % better, i.e. nothing')
for n, lab in ((18, 'BEFORE (9 per FET)'), (len(d), f'AFTER ({len(d)} <= 5 mm)')):
    dd = d[:n] if n <= len(d) else d
    Ra = array_R(dd)
    tot = 1.0 / (1.0 / RB + 1.0 / Ra)
    print(f'{lab:24s} array {Ra:6.2f}  ||  bulk {RB:5.2f}  ->  theta_BS {tot:5.2f} C/W')
