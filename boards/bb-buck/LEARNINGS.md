# LEARNINGS - bb-buck (workspace learnings)

Workspace-local. Every entry gets a date, tags (stage tag first: P0-P10), and a
one-line claim as its title. `learnings.py compile --workspace boards/bb-buck` turns new
entries into `learnings/queue.yaml`; the `promote` verb rules on them.
Research tasks (research.py close) append their entries here automatically.

## 2026-08-15 [P2][research][knowledge][block:B1] research task block-buck-1: 9 verified record(s) for block:B1
Gap: research block 'buck': populate selection, power-loop, emi, feedback, decoupling, return-path, thermal-via, inrush, sequencing, constraints-emission (application delta only - principle parents exist)
Operating point: {"board_layers": 2, "control_kind": "cmode", "fsw_khz": 400, "injection_kind": "none", "integration_kind": "integrated-fet", "iout_a": 2, "pdiss_w": 1.2, "rectifier_kind": "sync", "source_kind": "dc-input", "switching_kind": "hard", "vin_v": 30, "vout_v": 5}
Missing classes: selection, power-loop, emi, feedback, decoupling, return-path, thermal-via, inrush, sequencing, constraints-emission

Verified records (second reader signed). Promotion = the research verb's promote step (copies record + sources into the library), then the queue ruling with kind knowledge_record targeting reference/knowledge/records/<id>.yaml, then the owner's approval block:
- buck-cmode-inductor-window [selection] boards/bb-buck/research/records/buck-cmode-inductor-window.yaml
- buck-cmode-internal-comp-cout-window [feedback] boards/bb-buck/research/records/buck-cmode-internal-comp-cout-window.yaml
- buck-constraints-emission-layout-groups [constraints-emission] boards/bb-buck/research/records/buck-constraints-emission-layout-groups.yaml
- buck-dc-input-hot-plug-overshoot [inrush] boards/bb-buck/research/records/buck-dc-input-hot-plug-overshoot.yaml
- buck-ep-agnd-thermal-via-array [thermal-via, return-path] boards/bb-buck/research/records/buck-ep-agnd-thermal-via-array.yaml
- buck-integrated-fet-bypass-trio [decoupling] boards/bb-buck/research/records/buck-integrated-fet-bypass-trio.yaml
- buck-precision-en-fixed-softstart [sequencing] boards/bb-buck/research/records/buck-precision-en-fixed-softstart.yaml
- buck-sync-hot-loop-cin-placement [power-loop, emi] boards/bb-buck/research/records/buck-sync-hot-loop-cin-placement.yaml
- buck-two-layer-ground-shield-continuity [emi, return-path] boards/bb-buck/research/records/buck-two-layer-ground-shield-continuity.yaml
Sources (quarantined, sha-pinned in the task ledger):
- research/sources/lmr33630.pdf tier vendor-layout sha256 3b0920a4e56a <https://www.ti.com/lit/ds/symlink/lmr33630.pdf>
- research/sources/sluaal8.pdf tier vendor-appnote sha256 05ba68c6736a <https://www.ti.com/lit/pdf/sluaal8>
- research/sources/snva721a.pdf tier vendor-appnote sha256 293daf0da2cb <https://www.ti.com/lit/pdf/snva721>
Task file: boards/bb-buck/research/tasks/block-buck-1.json
