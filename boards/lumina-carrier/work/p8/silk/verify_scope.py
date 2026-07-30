"""Prove the fix touched ONLY reference-field silk text: diff snapshot vs current."""
import json, sys
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


def load(p):
    root = sexpdata.loads(open(p, encoding="utf-8").read())
    fps, tracks, vias, zones, grs = {}, [], [], [], []
    for fp in kids(root, "footprint"):
        at = nums(kid(fp, "at") or ["at"])
        lay = kid(fp, "layer")
        props = {}
        for pr in kids(fp, "property"):
            sv = strs(pr)
            if not sv: continue
            nm = sv[0].lower()
            if nm not in ("reference", "value"): continue
            pat = nums(kid(pr, "at") or ["at"])
            props[nm] = (tuple(pat), tok(kid(pr, "layer")[1]) if kid(pr, "layer") else None,
                         kid(pr, "hide") is not None)
        pads = tuple(sorted((strs(p)[0] if strs(p) else "?", tuple(nums(kid(p, "at") or ["at"])),
                             tuple(nums(kid(p, "size") or ["size"])))
                            for p in kids(fp, "pad")))
        silk = tuple(sorted(
            (head(g), tuple(nums(kid(g, "start") or ["s"])), tuple(nums(kid(g, "end") or ["e"])),
             tuple(nums(kid(g, "center") or ["c"])))
            for g in fp[1:] if isnode(g)
            and head(g) in ("fp_line", "fp_rect", "fp_circle", "fp_arc", "fp_poly")))
        ref = props.get("reference")
        name = None
        for pr in kids(fp, "property"):
            sv = strs(pr)
            if sv and sv[0] == "Reference": name = sv[1]
        fps[name] = {"at": tuple(at), "layer": tok(lay[1]) if lay else None,
                     "props": props, "pads": pads, "silk": silk,
                     "fpname": strs(fp)[0] if strs(fp) else "?"}
    for s in kids(root, "segment") + kids(root, "arc"):
        tracks.append((head(s), tuple(nums(kid(s, "start") or ["s"])),
                       tuple(nums(kid(s, "end") or ["e"])),
                       tuple(nums(kid(s, "width") or ["w"])),
                       tok(kid(s, "layer")[1]) if kid(s, "layer") else None,
                       tuple(nums(kid(s, "net") or ["n"]))))
    for v in kids(root, "via"):
        vias.append((tuple(nums(kid(v, "at") or ["a"])), tuple(nums(kid(v, "size") or ["s"])),
                     tuple(nums(kid(v, "drill") or ["d"])), tuple(nums(kid(v, "net") or ["n"]))))
    for z in kids(root, "zone"):
        zones.append((tuple(nums(kid(z, "net") or ["n"])),
                      len(json.dumps(z, default=str))))
    for g in root[1:]:
        if isnode(g) and head(g) in ("gr_line", "gr_rect", "gr_circle", "gr_arc",
                                     "gr_poly", "gr_text"):
            grs.append((head(g), tuple(nums(kid(g, "start") or ["s"])),
                        tuple(nums(kid(g, "end") or ["e"])),
                        tuple(nums(kid(g, "at") or ["a"])),
                        tok(kid(g, "layer")[1]) if kid(g, "layer") else None))
    return fps, sorted(tracks), sorted(vias), sorted(zones), sorted(grs)


A = load(sys.argv[1])
B = load(sys.argv[2])
out = {"footprint_set_same": set(A[0]) == set(B[0]),
       "tracks_identical": A[1] == B[1], "n_tracks": [len(A[1]), len(B[1])],
       "vias_identical": A[2] == B[2], "n_vias": [len(A[2]), len(B[2])],
       "zones_identical": A[3] == B[3], "n_zones": [len(A[3]), len(B[3])],
       "board_graphics_identical": A[4] == B[4], "n_gr": [len(A[4]), len(B[4])]}
moved_fp, changed_pads, changed_silk, changed_val, changed_ref, hid = [], [], [], [], [], []
for r in A[0]:
    a, b = A[0][r], B[0].get(r)
    if b is None: continue
    if a["at"] != b["at"] or a["layer"] != b["layer"] or a["fpname"] != b["fpname"]:
        moved_fp.append(r)
    if a["pads"] != b["pads"]: changed_pads.append(r)
    if a["silk"] != b["silk"]: changed_silk.append(r)
    if a["props"].get("value") != b["props"].get("value"): changed_val.append(r)
    if a["props"].get("reference") != b["props"].get("reference"):
        changed_ref.append(r)
        ra, rb = a["props"]["reference"], b["props"]["reference"]
        if ra[1] != rb[1] or ra[2] != rb[2]:
            hid.append((r, ra[1:], rb[1:]))
out.update({"footprints_moved": moved_fp, "pads_changed": changed_pads,
            "footprint_silk_changed": changed_silk, "value_fields_changed": changed_val,
            "reference_fields_moved": len(changed_ref),
            "reference_layer_or_hide_changed": hid})
print(json.dumps(out, indent=1))
