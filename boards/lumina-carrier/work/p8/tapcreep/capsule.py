"""Capsule geometry core - functions copied VERBATIM from work/p7/pad_gap.py.

pad_gap.py runs its J1-specific analysis at module level, so it cannot be
imported. These four functions (blocks / spine / seg_seg_dist / gap) are the
reusable part and are byte-identical to that file, so the numbers are the same
model that settled the J1 barrier record.

Added here (not in pad_gap.py): cap_dist(), which is the same seg_seg_dist
capsule model applied to TRACK segments (a track is a capsule: its centreline
segment with radius = width/2) rather than to pads.
"""
import math

BS = '\\'


def blocks(t, tok, st=0, en=None):
    en = len(t) if en is None else en
    i, pat = st, '(' + tok
    while True:
        i = t.find(pat, i, en)
        if i < 0:
            return
        j, d, q = i, 0, False
        while j < en:
            c = t[j]
            if c == '"' and t[j - 1] != BS:
                q = not q
            elif not q:
                if c == '(':
                    d += 1
                elif c == ')':
                    d -= 1
                    if d == 0:
                        yield (i, j + 1)
                        break
            j += 1
        i = j + 1


def spine(p):
    """Return (a, b, r) - a capsule: segment a-b with radius r.
    circle -> degenerate segment. oval -> segment along the long axis.
    rect/roundrect -> approximated by its inscribed capsule ONLY if square."""
    x, y, w, h, shape = p['x'], p['y'], p['w'], p['h'], p['shape']
    if shape == 'circle' or abs(w - h) < 1e-9:
        return (x, y), (x, y), w / 2.0
    if shape in ('oval', 'roundrect'):
        if w >= h:                      # long axis horizontal
            r = h / 2.0
            half = (w - h) / 2.0
            return (x - half, y), (x + half, y), r
        r = w / 2.0
        half = (h - w) / 2.0
        return (x, y - half), (x, y + half), r
    return None                          # rectangle: handled separately


def seg_seg_dist(a1, a2, b1, b2):
    def clamp(v, lo, hi):
        return max(lo, min(hi, v))

    def pt_seg(p, s1, s2):
        vx, vy = s2[0] - s1[0], s2[1] - s1[1]
        L2 = vx * vx + vy * vy
        if L2 == 0:
            return math.hypot(p[0] - s1[0], p[1] - s1[1])
        t = clamp(((p[0] - s1[0]) * vx + (p[1] - s1[1]) * vy) / L2, 0.0, 1.0)
        return math.hypot(p[0] - (s1[0] + t * vx), p[1] - (s1[1] + t * vy))
    return min(pt_seg(a1, b1, b2), pt_seg(a2, b1, b2),
               pt_seg(b1, a1, a2), pt_seg(b2, a1, a2))


def gap(p, q):
    sp, sq = spine(p), spine(q)
    if sp and sq:
        (a1, a2, r1), (b1, b2, r2) = sp, sq
        return seg_seg_dist(a1, a2, b1, b2) - r1 - r2, 'capsule'
    dx = max(0.0, abs(p['x'] - q['x']) - (p['w'] + q['w']) / 2)
    dy = max(0.0, abs(p['y'] - q['y']) - (p['h'] + q['h']) / 2)
    return math.hypot(dx, dy), 'rect'


def cap_dist(A, B):
    """Copper-to-copper gap between two capsules.

    A capsule is (a, b, r): centreline segment a-b, radius r. A track segment
    of width w is (start, end, w/2); a via or circular pad of diameter d is
    (at, at, d/2). Identical model to gap()'s capsule branch.
    """
    (a1, a2, r1) = A
    (b1, b2, r2) = B
    return seg_seg_dist(a1, a2, b1, b2) - r1 - r2
