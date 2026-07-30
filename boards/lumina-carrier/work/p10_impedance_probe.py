"""READ-ONLY probe: getImpedanceTemplateSettingList for lumina-carrier.

Free integration surface per contract.md section 9. Never touches pcb/create.

Board: JLC04161H-3313, 4 layer, 1.6 mm, 1 oz outer / 0.5 oz inner, HASL.
Param names per contract.md:62 -
  {stencilLayer, stencilPly, cuprumThickness, insideCuprumThickness,
   plateType, delamination}
Field meanings are not documented, so several shapes are tried and every
response is reported verbatim.
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

# stencilLayer = layer count (audit/get returned stencilLayer 4 for this board)
# stencilPly   = board thickness in mm
# delamination = unknown; tried present and absent
attempts = [
    ("layers+thickness+delam0", {"stencilLayer": 4, "stencilPly": 1.6,
                                 "cuprumThickness": "1",
                                 "insideCuprumThickness": "0.5",
                                 "plateType": 1, "delamination": 0}),
    ("no delamination", {"stencilLayer": 4, "stencilPly": 1.6,
                         "cuprumThickness": "1",
                         "insideCuprumThickness": "0.5", "plateType": 1}),
    ("numeric copper", {"stencilLayer": 4, "stencilPly": 1.6,
                        "cuprumThickness": 1, "insideCuprumThickness": 0.5,
                        "plateType": 1, "delamination": 0}),
    ("thickness as string", {"stencilLayer": 4, "stencilPly": "1.6",
                             "cuprumThickness": "1",
                             "insideCuprumThickness": "0.5",
                             "plateType": 1, "delamination": 0}),
]

out = {"script": "p10_impedance_probe", "path": PATH, "attempts": []}
for name, payload in attempts:
    rec = {"name": name, "payload": payload}
    try:
        r = s.post_json(PATH, payload)
        rec.update({"verdict": jlcapi.classify(r), "code": r.get("code"),
                    "message": r.get("message"), "data": r.get("data")})
    except Exception as exc:  # noqa: BLE001
        rec["error"] = str(exc)
    out["attempts"].append(rec)
    if rec.get("verdict") == "ok" and rec.get("data"):
        break

print(json.dumps(out, indent=1, default=str))
