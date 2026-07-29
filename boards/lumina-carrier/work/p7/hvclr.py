import json, pathlib, sys
val = float(sys.argv[1])
p = pathlib.Path('boards/lumina-carrier/kicad/lumina-carrier.kicad_pro')
pro = json.loads(p.read_text(encoding='utf-8'))
HV = {"PWR_V48RAW", "PWR_48V_SW", "PWR_V48RTN"}
for c in pro['net_settings']['classes']:
    if c['name'] in HV:
        c['clearance'] = val
p.write_text(json.dumps(pro, indent=2), encoding='utf-8')
print("HV netclass clearance ->", val)
