"""First-principles theta_JA cross-check for AP63356QZV-7 on buck-5v3a.

Two-sheet 1-D radial finite-difference model of a PCB heat spreader.

  node A = the top copper (F.Cu), where ALL of U1's heat enters, because the
           part has NO exposed pad: the die couples to the board only through
           its VIN land + GND land + SW land, all of which are F.Cu copper.
  node B = the lumped inner + bottom copper (the spreader stack).

  A and B are coupled by (a) the dielectric over the whole area and (b) the
  thermal vias near the part.  Both sheets lose heat to ambient through h.
  theta_JA = theta_JC (vendor, 5 C/W, die -> lands) + T_A(r_source) / P.

Calibration check: run with JEDEC 2s2p geometry and compare to the vendor's
published 25 C/W (DS41948 p.4, Note 6).
"""
import math

import numpy as np

K_CU = 390.0          # W/m.K
K_FR4 = 0.30          # W/m.K through-plane
OZ = 34.8e-6          # m per oz of copper


def solve(board_mm2, t_top_m, t_bot_m, d_ab_m, h_top, h_bot,
          n_via=0, g_via=0.0, r_via_mm=2.5, r_src_mm=1.0,
          p_source=1.0, p_spread=0.0, nodes=600):
    """Return (theta_board C/W at the source, mean board rise C).

    theta_board = rise of the top copper at the source / p_source, with
    p_spread W injected uniformly over the board (neighbour parts)."""
    R = math.sqrt(board_mm2 / math.pi) * 1e-3          # equal-area disc radius
    r0 = r_src_mm * 1e-3
    r = np.geomspace(r0, R, nodes)
    # annulus areas
    edges = np.concatenate(([r0], np.sqrt(r[:-1] * r[1:]), [R]))
    area = math.pi * (edges[1:] ** 2 - edges[:-1] ** 2)

    n = nodes
    G = np.zeros((2 * n, 2 * n))
    b = np.zeros(2 * n)

    def add(i, j, g):
        G[i, i] += g
        G[j, j] += g
        G[i, j] -= g
        G[j, i] -= g

    def add_gnd(i, g):
        G[i, i] += g

    for i in range(n - 1):                              # radial conduction
        lg = math.log(r[i + 1] / r[i])
        add(i, i + 1, 2 * math.pi * K_CU * t_top_m / lg)
        add(n + i, n + i + 1, 2 * math.pi * K_CU * t_bot_m / lg)

    g_diel = K_FR4 / d_ab_m                             # W/m2.K, A <-> B
    via_area_frac = None
    if n_via:
        rv = r_via_mm * 1e-3
        sel = r <= rv
        via_area_frac = area * sel
        tot = via_area_frac.sum() or 1.0
    for i in range(n):
        add(i, n + i, g_diel * area[i])
        if n_via:
            add(i, n + i, n_via * g_via * (via_area_frac[i] / tot))
        add_gnd(i, h_top * area[i])                     # top -> ambient
        add_gnd(n + i, h_bot * area[i])                 # bottom -> ambient
        if p_spread:
            b[i] += p_spread * 0.5 * area[i] / area.sum()
            b[n + i] += p_spread * 0.5 * area[i] / area.sum()

    b[0] += p_source                                    # U1 into the top copper
    T = np.linalg.solve(G, b)
    mean_rise = float((T[:n] * area).sum() / area.sum())
    return float(T[0]) / p_source if p_source else 0.0, mean_rise, float(T[0])


def via_G(drill_mm, plate_um, length_m):
    ro = drill_mm / 2e3
    ri = ro - plate_um * 1e-6
    a = math.pi * (ro ** 2 - ri ** 2)
    return K_CU * a / length_m, 1.0 / (K_CU * a / length_m)


THETA_JC = 5.0

# ---------------- stackup JLC04162H-7628A ------------------------------------
T_OUT = 0.070e-3          # 2 oz
T_IN = 0.0152e-3          # 0.5 oz
D_F_IN1 = 0.4284e-3       # prepreg 7628x2
D_F_B_2L = 1.46e-3        # 2-layer core

COV_TOP = 0.70            # F.Cu is a pour with traces/clearances
COV_BOT = 0.90

g4, r4 = via_G(0.30, 25, D_F_IN1)
g2, r2 = via_G(0.30, 25, D_F_B_2L)
print(f"per-via 0.30mm/25um: to In1 (0.4284 mm) {r4:.1f} C/W ; "
      f"to B.Cu on 2L (1.46 mm) {r2:.1f} C/W")
g4s, r4s = via_G(0.20, 25, D_F_IN1)
print(f"per-via 0.20mm/25um to In1: {r4s:.1f} C/W")

print("\n--- calibration: JEDEC 2s2p (76.2 x 114.3 mm, 2 oz outer / 1 oz inner) ---")
for h in (10, 12, 14):
    th, _, _ = solve(76.2 * 114.3, T_OUT * 0.5, 2 * OZ + T_OUT * 0.5,
                     D_F_IN1, h * 1.15, h * 0.85, n_via=8, g_via=g4,
                     p_source=0.88)
    print(f"  h={h:>2} W/m2K -> theta_JA = {THETA_JC + th:5.1f} C/W "
          f"(vendor 25 C/W)")

print("\n--- buck-5v3a, 50 x 40 mm, 4L 2oz/0.5oz, U1 = 0.881 W --------------")
hdr = f"{'n_vias':>7} {'h=20':>8} {'h=30':>8} {'h=40':>8}"
print(hdr)
for nv in (0, 4, 6, 8, 12, 16):
    row = f"{nv:>7}"
    for htot in (20, 30, 40):
        th, _, _ = solve(2000, T_OUT * COV_TOP, 2 * T_IN + T_OUT * COV_BOT,
                         D_F_IN1, htot * 0.58, htot * 0.42,
                         n_via=nv, g_via=g4, p_source=0.881)
        row += f" {THETA_JC + th:8.1f}"
    print(row)

print("\n--- same board on 2 LAYERS (2 oz outers, no inner planes) -----------")
print(hdr)
for nv in (0, 6, 12, 16):
    row = f"{nv:>7}"
    for htot in (20, 30, 40):
        th, _, _ = solve(2000, T_OUT * COV_TOP, T_OUT * COV_BOT,
                         D_F_B_2L, htot * 0.58, htot * 0.42,
                         n_via=nv, g_via=g2, p_source=0.881)
        row += f" {THETA_JC + th:8.1f}"
    print(row)

print("\n--- Tj at the 7 V corner, 50 C ambient, U1 0.881 W + 0.60 W neighbours")
for label, tb, dab, gv, nv in (("4L, 12 vias", 2 * T_IN + T_OUT * COV_BOT,
                                D_F_IN1, g4, 12),
                               ("4L,  6 vias", 2 * T_IN + T_OUT * COV_BOT,
                                D_F_IN1, g4, 6),
                               ("4L,  0 vias", 2 * T_IN + T_OUT * COV_BOT,
                                D_F_IN1, g4, 0),
                               ("2L, 12 vias", T_OUT * COV_BOT,
                                D_F_B_2L, g2, 12)):
    for htot in (20, 30):
        th, mean, tsrc = solve(2000, T_OUT * COV_TOP, tb, dab,
                               htot * 0.58, htot * 0.42, n_via=nv, g_via=gv,
                               p_source=0.881, p_spread=0.602)
        print(f"  {label}  h={htot}: board mean +{mean:4.1f} C, "
              f"top copper at U1 +{tsrc:5.1f} C, "
              f"Tj = {50 + tsrc + THETA_JC * 0.881:5.1f} C "
              f"(theta_JA_eff {(tsrc + THETA_JC * 0.881) / 0.881:4.1f} C/W)")
