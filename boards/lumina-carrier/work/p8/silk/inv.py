"""Dump a full geometry inventory of the board for the silk solver. JSON to stdout."""
import json, math, sys
sys.path.insert(0, r'C:/dev/ai-ee3/.claude/skills/ai-ee/scripts/lib')
import sexpdata

def tok(x): return x.value() if hasattr(x, "value") else x
def isnode(x): return isinstance(x, list) and x and not isinstance(x[0], list)
def head(n): return tok(n[0]) if isnode(n) else None
def kids(n, name): return [c for c in n[1:] if isnode(c) and head(c) == name]
def kid(n, name):
    for c in n[1:]:
        if isnode(c) and head(c) == name: return c
    return None
def nums(n): return [float(v) for v in n[1:] if isinstance(v, (int, float))]
def strs(n): return [v for v in n[1:] if isinstance(v, str)]
def syms(n): return [tok(v) for v in n[1:] if not isinstance(v, (list, str, int, float))]

root = sexpdata.loads(open(sys.argv[1], encoding="utf-8").read())

SILK = ("F.SilkS", "B.SilkS")

def layers_of(n):
    out = []
    for name in ("layer", "layers"):
        k = kid(n, name)
        if k:
            out += [tok(v) for v in k[1:]]
    return out

def graphic_pts(g):
    """Return list of (x,y) sample points describing the graphic, plus width."""
    h = head(g)
    pts = []
    w = 0.0
    st = kid(g, "stroke")
    if st:
        wk = kid(st, "width")
        if wk: w = nums(wk)[0] if nums(wk) else 0.0
    wk = kid(g, "width")
    if wk and nums(wk): w = nums(wk)[0]
    if h in ("fp_line", "gr_line"):
        s = nums(kid(g, "start")); e = nums(kid(g, "end"))
        if len(s) >= 2 and len(e) >= 2: pts = [tuple(s[:2]), tuple(e[:2])]
    elif h in ("fp_rect", "gr_rect"):
        s = nums(kid(g, "start")); e = nums(kid(g, "end"))
        if len(s) >= 2 and len(e) >= 2:
            x0, y0, x1, y1 = s[0], s[1], e[0], e[1]
            pts = [(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)]
    elif h in ("fp_circle", "gr_circle"):
        c = nums(kid(g, "center")); e = nums(kid(g, "end"))
        if len(c) >= 2 and len(e) >= 2:
            r = math.hypot(e[0]-c[0], e[1]-c[1])
            pts = [(c[0]+r*math.cos(a*math.pi/12), c[1]+r*math.sin(a*math.pi/12)) for a in range(24)]
    elif h in ("fp_arc", "gr_arc"):
        for nm in ("start", "mid", "end"):
            v = nums(kid(g, nm) or [nm])
            if len(v) >= 2: pts.append(tuple(v[:2]))
    elif h in ("fp_poly", "gr_poly"):
        p = kid(g, "pts")
        if p:
            for xy in kids(p, "xy"):
                v = nums(xy)
                if len(v) >= 2: pts.append(tuple(v[:2]))
    return pts, w

fps = []
for fp in kids(root, "footprint"):
    name = strs(fp)[0] if strs(fp) else "?"
    at = nums(kid(fp, "at") or ["at"])
    fx, fy = at[0], at[1]
    fdeg = at[2] if len(at) > 2 else 0.0
    lay = kid(fp, "layer")
    side = "back" if lay and tok(lay[1]) == "B.Cu" else "front"
    props = {}
    for p in kids(fp, "property"):
        sv = strs(p)
        if not sv: continue
        pname = sv[0].lower()
        if pname not in ("reference", "value"): continue
        pat = nums(kid(p, "at") or ["at"])
        hidden = kid(p, "hide") is not None or "hide" in syms(p)
        hk = kid(p, "hide")
        if hk and nums(hk) == [] and [tok(v) for v in hk[1:]] == ["no"]:
            hidden = False
        if hk and [tok(v) for v in hk[1:]] == ["yes"]:
            hidden = True
        eff = kid(p, "effects")
        size = None; thick = None; mirror = False; just = []
        if eff:
            f = kid(eff, "font")
            if f:
                s = kid(f, "size")
                if s and nums(s): size = nums(s)
                t = kid(f, "thickness")
                if t and nums(t): thick = nums(t)[0]
            j = kid(eff, "justify")
            if j: just = [tok(v) for v in j[1:]]
            mirror = "mirror" in just
        props[pname] = {
            "text": sv[1] if len(sv) > 1 else "",
            "lx": pat[0] if len(pat) >= 2 else None,
            "ly": pat[1] if len(pat) >= 2 else None,
            "ldeg": pat[2] if len(pat) > 2 else 0.0,
            "hidden": bool(hidden), "size": size, "thickness": thick,
            "justify": just, "unlocked": "unlocked" in syms(p),
        }
    pads = []
    for pad in kids(fp, "pad"):
        pat = nums(kid(pad, "at") or ["at"])
        sz = nums(kid(pad, "size") or ["size"])
        if len(pat) < 2 or len(sz) < 2: continue
        pads.append({"n": strs(pad)[0] if strs(pad) else "?",
                     "x": pat[0], "y": pat[1], "rot": pat[2] if len(pat) > 2 else 0.0,
                     "w": sz[0], "h": sz[1],
                     "shape": syms(pad)[1] if len(syms(pad)) > 1 else "?",
                     "layers": layers_of(pad)})
    silk = []
    for g in fp[1:]:
        if not isnode(g): continue
        if head(g) not in ("fp_line", "fp_rect", "fp_circle", "fp_arc", "fp_poly"): continue
        ls = layers_of(g)
        if not any(l in SILK for l in ls): continue
        pts, w = graphic_pts(g)
        if pts: silk.append({"type": head(g), "pts": pts, "w": w, "layers": ls})
    fps.append({"name": name, "ref": props.get("reference", {}).get("text", "?"),
                "x": fx, "y": fy, "deg": fdeg, "side": side,
                "props": props, "pads": pads, "silk": silk})

# board-level graphics
board_silk = []
edges = []
for g in root[1:]:
    if not isnode(g): continue
    h = head(g)
    if h in ("gr_line", "gr_rect", "gr_circle", "gr_arc", "gr_poly"):
        ls = layers_of(g)
        pts, w = graphic_pts(g)
        if not pts: continue
        if any(l in SILK for l in ls):
            board_silk.append({"type": h, "pts": pts, "w": w, "layers": ls})
        if "Edge.Cuts" in ls:
            edges.append({"type": h, "pts": pts, "w": w})
    elif h == "gr_text":
        ls = layers_of(g)
        if any(l in SILK for l in ls):
            at = nums(kid(g, "at") or ["at"])
            eff = kid(g, "effects"); size = None; thick = None
            if eff:
                f = kid(eff, "font")
                if f:
                    s = kid(f, "size")
                    if s and nums(s): size = nums(s)
                    t = kid(f, "thickness")
                    if t and nums(t): thick = nums(t)[0]
            board_silk.append({"type": "gr_text", "text": strs(g)[0] if strs(g) else "",
                               "x": at[0], "y": at[1], "deg": at[2] if len(at) > 2 else 0.0,
                               "size": size, "thickness": thick, "layers": ls, "pts": [], "w": 0.0})

json.dump({"footprints": fps, "board_silk": board_silk, "edges": edges},
          open(sys.argv[2], "w", encoding="utf-8"), indent=1)
print(json.dumps({"footprints": len(fps), "board_silk": len(board_silk), "edges": len(edges)}))
