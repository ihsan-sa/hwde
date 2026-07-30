"""READ-ONLY: does JLC04161H-3313 appear under ANY parameter shape?

Sweeps plateType and delamination (both undocumented) and a couple of
thickness/copper variants, collecting every distinct templateName seen.
Never touches pcb/create.
"""
import json
import os
import sys

sys.path.insert(0, r'C:\dev\ai-ee3\.claude\skills\ai-ee\scripts\lib')
import jlcapi  # noqa: E402

PATH = "/overseas/openapi/pcb/getImpedanceTemplateSettingList"
s = jlcapi.JlcSession(
    appid=os.environ.get("AIEE_JLCPCB_APPID") or os.environ.get("AIEE_JLCPCB_KEY"),
    accesskey=os.environ.get("AIEE_JLCPCB_KEY"),
    secret=os.environ.get("AIEE_JLCPCB_SECRET"),
)

base = {"stencilLayer": 4, "stencilPly": 1.6, "cuprumThickness": "1",
        "insideCuprumThickness": "0.5", "plateType": 1, "delamination": 0}

variants = []
for pt in (0, 1, 2, 3):
    v = dict(base); v["plateType"] = pt
    variants.append((f"plateType={pt}", v))
for dl in (1, 2, 3):
    v = dict(base); v["delamination"] = dl
    variants.append((f"delamination={dl}", v))
v = dict(base); v.pop("delamination"); v.pop("plateType")
variants.append(("minimal", v))

seen = {}
rows = []
for name, payload in variants:
    try:
        r = s.post_json(PATH, payload)
        cls = jlcapi.classify(r)
        data = r.get("data") if isinstance(r.get("data"), list) else []
        names = []
        for t in data:
            tn = str(t.get("templateName"))
            names.append(tn)
            seen.setdefault(tn, t.get("impedanceTemplateCode"))
        rows.append({"variant": name, "verdict": cls, "code": r.get("code"),
                     "message": r.get("message"), "n": len(data),
                     "names": names})
    except Exception as exc:  # noqa: BLE001
        rows.append({"variant": name, "error": str(exc)})

print(json.dumps({"rows": rows,
                  "all_template_names_seen": seen,
                  "any_3313": [n for n in seen if "3313" in n]},
                 indent=1, ensure_ascii=True))
