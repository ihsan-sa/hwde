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

## 2026-08-15 [P4][erc][kicad-sch-api][schematic] An ALREADY-retyped pulled library can still hide exactly one ERC-blocking pin: BOOT on a buck
The pulled `LMR33630ADDAR` symbol arrived with a sane typing pass already applied
(PGND/VIN/EP `power_in`, SW/VCC `power_out`, EN/PG/FB `passive`) - so the usual
"easyeda types are junk, retype everything" reflex reads as unnecessary here. It is
not: BOOT (pin 7) came typed `power_in`, and `/BST` has no schematic-visible driver
(the bootstrap diode VCC->BOOT is inside the package; the net's only other member is
C6, a passive). Measured with the fix disabled, `kc.py erc` on the finished sheet
returned EXACTLY ONE finding - `power_pin_not_driven` "Input Power pin not driven by
any Output Power pins" on U1 pin 7 - and zero of everything else, so the whole ERC
gate hung on that single library attribute.
Two ways out, and they are not equivalent. A PWR_FLAG on `/BST` clears ERC but leaves
the pin `power_in`, which pulls `/BST` into `netlist_audit`'s `power_undeclared`
warning - and `architecture/sheets.md` s4 deliberately leaves `/BST` undeclared
(a `power` entry would give a gate-charge node a width rule). Retyping the pin to
`passive` in `lib/aiee.kicad_sym` clears both, matches sbuck-5v3a's AP64350 BST pin,
and matches the standing retype rule (supplies/grounds power_in, regulator output
power_out, everything else passive - a bootstrap node is not the part's supply).
Done in `kicad/gen/lib_pin_types.py`, which lists only DEVIATIONS from the pulled
typing so a later `lib_pull` refresh cannot be silently re-typed wholesale, and which
`gen/root.py` calls before the symbol cache reads the library. Generalisation: judge a
pulled symbol pin-by-pin against the datasheet extract even when the file looks
already-fixed, and prefer the library fix over a PWR_FLAG whenever the net is one the
architecture deliberately leaves out of constraints.json.
