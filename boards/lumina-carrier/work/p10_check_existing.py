"""READ-ONLY: ask JLC whether any order already exists on this account.

Calls pcb/wip/get (work-in-progress list). Touches no create path.
JSON to stdout.
"""
import json
import os
import sys

sys.path.insert(0, r'C:\dev\ai-ee3\.claude\skills\ai-ee\scripts\lib')
import jlcapi  # noqa: E402

appid = os.environ.get("AIEE_JLCPCB_APPID") or os.environ.get("AIEE_JLCPCB_KEY")
key = os.environ.get("AIEE_JLCPCB_KEY")
secret = os.environ.get("AIEE_JLCPCB_SECRET")

out = {"script": "p10_check_existing", "checked": []}
try:
    s = jlcapi.JlcSession(appid=appid, accesskey=key, secret=secret)
except Exception as exc:  # noqa: BLE001
    print(json.dumps({"status": "error", "error": f"session: {exc}"}, indent=1))
    raise SystemExit(2)

for name, payload in (("wip", {}), ("wip_paged", {"page": 1, "pageSize": 50})):
    try:
        r = s.post_json(jlcapi.PATHS["wip"], payload)
        out["checked"].append({"call": name, "payload": payload,
                               "verdict": jlcapi.classify(r),
                               "code": r.get("code"),
                               "message": r.get("message"),
                               "data": r.get("data")})
    except Exception as exc:  # noqa: BLE001
        out["checked"].append({"call": name, "payload": payload,
                               "error": str(exc)})

print(json.dumps(out, indent=1, default=str)[:6000])
