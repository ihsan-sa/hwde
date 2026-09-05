"""impedance.py - controlled-impedance geometry for board setup (SPEC P5).

Closed-form approximations, used by rules_gen.py to turn an impedance TARGET
(from constraints.json / stackups.yaml) into a trace width + differential gap,
and by stackups.yaml authoring to populate its `controlled_impedance` table.

Formulas (cited, approximate - NOT a field solver):

  Single-ended surface microstrip, IPC-2141A eq. (a trace on an outer layer
  over the nearest reference plane, height h of the intervening dielectric):

      Z0 = (87 / sqrt(er + 1.41)) * ln(5.98*h / (0.8*w + t))

  valid ~ 0.1 <= w/h <= 3.0, er 1..15, t << h. h,w,t in the same unit.

  Edge-coupled differential microstrip - the widely-published coupling
  correction (Howard Johnson, "High-Speed Digital Design", and many fab app
  notes), s = edge-to-edge gap:

      Zdiff = 2 * Z0(w) * (1 - 0.48 * exp(-0.96 * s / h))

These are first-order estimates for sizing DRC rules and giving S5 a target to
check against; final controlled-impedance geometry on a real order should be
confirmed with the fab's own impedance calculator (JLC's tool) - VERIFY-LATER.

All lengths mm. No I/O, no toolchain: a pure, unit-tested helper.
"""
from __future__ import annotations

import math

# Copper foil finished thickness by weight (mm) - JLC: 1 oz ~= 0.035, 0.5 oz ~= 0.0175.
CU_OZ_MM = {1.0: 0.035, 0.5: 0.0175, 2.0: 0.070}


def microstrip_z0(w: float, h: float, t: float, er: float) -> float:
    """Single-ended surface-microstrip Z0 (ohms), IPC-2141A. w,h,t in mm."""
    if w <= 0 or h <= 0:
        raise ValueError("w and h must be positive")
    return (87.0 / math.sqrt(er + 1.41)) * math.log(5.98 * h / (0.8 * w + t))


def solve_width(z0_target: float, h: float, t: float, er: float,
                lo: float = 0.02, hi: float = 20.0, tol: float = 1e-4) -> float:
    """Trace width (mm) whose microstrip Z0 == z0_target. Bisection.

    Z0 decreases monotonically as w grows, so bisect on w.
    """
    f = lambda w: microstrip_z0(w, h, t, er) - z0_target
    flo, fhi = f(lo), f(hi)
    if flo * fhi > 0:
        # Target outside the achievable range for this stackup; clamp to the
        # nearest endpoint rather than raise (callers want a usable width).
        return lo if abs(flo) < abs(fhi) else hi
    for _ in range(100):
        mid = 0.5 * (lo + hi)
        fm = f(mid)
        if abs(fm) < tol:
            return mid
        if flo * fm <= 0:
            hi = mid
        else:
            lo, flo = mid, fm
    return 0.5 * (lo + hi)


def _zdiff(w: float, s: float, h: float, t: float, er: float) -> float:
    return 2.0 * microstrip_z0(w, h, t, er) * (1.0 - 0.48 * math.exp(-0.96 * s / h))


def _bisect(f, lo: float, hi: float, tol: float = 1e-4) -> float:
    flo = f(lo)
    if flo * f(hi) > 0:  # target unreachable in range: clamp to nearer endpoint
        return lo if abs(flo) < abs(f(hi)) else hi
    for _ in range(100):
        mid = 0.5 * (lo + hi)
        if flo * f(mid) <= 0:
            hi = mid
        else:
            lo, flo = mid, f(mid)
        if hi - lo < tol:
            break
    return 0.5 * (lo + hi)


def diff_pair(zdiff_target: float, h: float, t: float, er: float,
              width: float | None = None,
              gap: float | None = None) -> tuple[float, float]:
    """(width, gap) mm for an edge-coupled differential microstrip.

    Real pairs are drawn tightly coupled (small gap for noise immunity), so the
    default pins a manufacturable gap = clamp(h, 0.13, 0.30) mm and solves the
    width for the target - NOT the loosely-coupled "width for Z0=Zdiff/2, huge
    gap" solution, which is impedance-valid but nobody routes it. Pin `width`
    to solve the gap instead, or pin `gap` to solve the width explicitly.
    """
    if width is not None and gap is None:
        s = width  # placeholder; solve gap below
        smin, smax = max(h * 0.1, 0.05), h * 5.0
        s = _bisect(lambda ss: _zdiff(width, ss, h, t, er) - zdiff_target, smin, smax)
        return round(width, 4), round(s, 4)
    s = gap if gap is not None else min(max(h, 0.13), 0.30)
    w = _bisect(lambda ww: _zdiff(ww, s, h, t, er) - zdiff_target, 0.05, 5.0)
    return round(w, 4), round(s, 4)


def geometry_for(profile: dict, h: float, er: float, cu_oz: float = 1.0) -> dict:
    """Resolve one impedance profile against a physical stackup gap.

    profile: {impedance_ohm, kind: "single"|"diff", [width_mm]}. Returns the
    profile augmented with computed width_mm (+ gap_mm for diff).
    """
    t = CU_OZ_MM.get(cu_oz, 0.035)
    z = float(profile["impedance_ohm"])
    out = dict(profile)
    if profile.get("kind") == "diff":
        w, s = diff_pair(z, h, t, er, profile.get("width_mm"))
        out["width_mm"], out["gap_mm"] = w, s
    else:
        out["width_mm"] = round(solve_width(z, h, t, er), 4)
    return out
