# LEARNINGS - bb-mcu (workspace learnings)

Workspace-local. Every entry gets a date, tags (stage tag first: P0-P10), and a
one-line claim as its title. `learnings.py compile --workspace boards/bb-mcu` turns new
entries into `learnings/queue.yaml`; the `promote` verb rules on them.
Research tasks (research.py close) append their entries here automatically.

## 2026-08-16 [P2][research][knowledge][block:B2] research task block-swd-debug-port-1: 5 verified record(s) for block:B2
Gap: research block 'swd-debug-port': produce its coverage checklist, then populate it
Operating point: {"board_layers": 2, "connector_kind": "header-100mil", "debug_kind": "swd", "edge_ns": 5, "fclk_mhz": 4, "header_pins": 5, "keying_kind": "none", "probe_kind": "flying-lead", "source_kind": "dc-input", "tamb_max_c": 50, "vio_v": 3.3}
Missing classes: coverage-checklist

Verified records (second reader signed). Promotion = the research verb's promote step (copies record + sources into the library), then the queue ruling with kind knowledge_record targeting reference/knowledge/records/<id>.yaml, then the owner's approval block:
- swd-debug-port-edge-rate-sets-layout-demand [emi] boards/bb-mcu/research/records/swd-debug-port-edge-rate-sets-layout-demand.yaml
- swd-debug-port-nrst-on-the-header [sequencing] boards/bb-mcu/research/records/swd-debug-port-nrst-on-the-header.yaml
- swd-debug-port-stm32f0-internal-pulls [selection] boards/bb-mcu/research/records/swd-debug-port-stm32f0-internal-pulls.yaml
- swd-debug-port-termination-follows-silicon [selection] boards/bb-mcu/research/records/swd-debug-port-termination-follows-silicon.yaml
- swd-debug-port-unkeyed-header-pin-order [selection, return-path] boards/bb-mcu/research/records/swd-debug-port-unkeyed-header-pin-order.yaml
Draft coverage checklist(s) for the owner to approve:
- swd-debug-port boards/bb-mcu/research/checklists/swd-debug-port.yaml (7 classes)
Sources (quarantined, sha-pinned in the task ledger):
- research/sources/2304140030_STMicroelectronics-STM32F030F4P6TR_C89040.pdf tier vendor-layout sha256 faac9340687f <https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/2304140030_STMicroelectronics-STM32F030F4P6TR_C89040.pdf>
- research/sources/infineon-an220270-hardware-design-guide-for-the-traveo-t2g-family-applicationnotes-en.pdf tier cross-vendor sha256 34d9156d68dd <https://www.infineon.com/assets/row/public/documents/10/42/infineon-an220270-hardware-design-guide-for-the-traveo-t2g-family-applicationnotes-en.pdf>
- research/sources/snla026a.pdf tier cross-vendor sha256 3a5604e61cbe <https://www.ti.com/lit/pdf/snla026>
Task file: boards/bb-mcu/research/tasks/block-swd-debug-port-1.json

## 2026-08-16 [P2][research][knowledge][block:B1] research task block-mcu-1: 8 verified record(s) for block:B1
Gap: research block 'mcu': produce its coverage checklist, then populate it
Operating point: {"board_layers": 2, "boot_kind": "external-strap", "clock_kind": "internal-rc", "debug_kind": "swd", "edge_ns": 5, "fcpu_mhz": 48, "idd_ma": 100, "package_kind": "tssop", "pdiss_w": 0.33, "reset_kind": "internal-pullup", "source_kind": "dc-input", "supply_kind": "single-rail", "tamb_max_c": 50, "vdd_max_v": 3.6, "vdd_min_v": 3.0, "vdd_v": 3.3}
Missing classes: coverage-checklist

Verified records (second reader signed). Promotion = the research verb's promote step (copies record + sources into the library), then the queue ruling with kind knowledge_record targeting reference/knowledge/records/<id>.yaml, then the owner's approval block:
- mcu-analog-rail-tracks-digital-rail [sequencing] boards/bb-mcu/research/records/mcu-analog-rail-tracks-digital-rail.yaml
- mcu-boot-select-strap-stm32f0 [selection] boards/bb-mcu/research/records/mcu-boot-select-strap-stm32f0.yaml
- mcu-decoupler-is-the-local-source [decoupling, return-path] boards/bb-mcu/research/records/mcu-decoupler-is-the-local-source.yaml
- mcu-package-power-budget [thermal] boards/bb-mcu/research/records/mcu-package-power-budget.yaml
- mcu-reset-sampled-pin-audit [selection] boards/bb-mcu/research/records/mcu-reset-sampled-pin-audit.yaml
- mcu-supply-pin-pair-decoupling [decoupling] boards/bb-mcu/research/records/mcu-supply-pin-pair-decoupling.yaml
- mcu-supply-return-continuity [return-path, emi] boards/bb-mcu/research/records/mcu-supply-return-continuity.yaml
- mcu-swd-port-live-at-reset-stm32f0 [selection] boards/bb-mcu/research/records/mcu-swd-port-live-at-reset-stm32f0.yaml
Draft coverage checklist(s) for the owner to approve:
- mcu boards/bb-mcu/research/checklists/mcu.yaml (5 classes)
Sources (quarantined, sha-pinned in the task ledger):
- research/sources/2304140030_STMicroelectronics-STM32F030F4P6TR_C89040.pdf tier vendor-layout sha256 faac9340687f <https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/2304140030_STMicroelectronics-STM32F030F4P6TR_C89040.pdf>
- research/sources/00002519A.pdf tier cross-vendor sha256 6cbc68c178d1 <https://ww1.microchip.com/downloads/en/AppNotes/00002519A.pdf>
- research/sources/AN13033.pdf tier cross-vendor sha256 9e14d7d0dda5 <https://www.nxp.com/docs/en/application-note/AN13033.pdf>
Task file: boards/bb-mcu/research/tasks/block-mcu-1.json

## 2026-08-16 [P6][placement][kicad][render] WJ500V-5.08-2P wire entry is at local -Y - the OPPOSITE of the KF128 / DB128L family
Root LEARNINGS records twice (2026-07-28 KF128, 2026-08-09 DB128L-5.08-2P) that a
5.08 mm screw terminal's wire mouth is at footprint-local **+Y**, so rot 270 points it
out the LEFT edge and rot 90 out the RIGHT. `aiee:CONN-TH_2P-P5.00_WJ500V-5.08-2P`
(C8465, Ningbo Kangnex) is the reverse: `render.py <board> --views right,left` shows the
two square wire cavities FACE-ON in the **right** view at footprint angle 270, and the
closed back (screw-clamp bodies behind plastic) in the left view. So for this footprint
**rot 270 = mouth out the RIGHT edge, rot 90 = out the LEFT**.
Two corroborating cues, and one that lies: the courtyard is asymmetric about the pad row
(local y[-5.5, +4.5]) and the LONGER 5.5 mm side is the mouth side - i.e. the mouth is at
local -Y, matching the render. The cue that lies is the TOP view: at rot 270 the rendered
top view shows dark slot-like recesses on the body's LEFT (board-inboard) face and a
plain lip on the right, which reads exactly backwards. Do not shortcut the side render -
"same pitch, same family, same +Y" is not transitive across vendors.

## 2026-08-16 [P6][gates][build-modes][PIPELINE BUG] `placement.edges` pins the connectors to the PROVISIONAL outline, so under a `canonical` binding the place gate cannot pass BEFORE `--outline fit`
`placelib.legality_violations` measures every `placement.edges` ref against
`edge_line(model.outline, ...)` with `EDGE_TOL = 2.5 mm`, and the outline it reads is
whatever `board_init --outline auto` produced. On bb-mcu that was 51.15 x 43.524 mm, a
shelf-pack artifact; the canonical layout is 33.77 x 21.26 mm of content. Placing to the
canonical layout leaves J1 16.85 mm from the provisional right edge -> `edge_violation`,
gate FAIL. Placing to satisfy the edge means spreading the three connectors to the
provisional edges, and then `--outline fit` measures the spread and "earns" the
provisional size - the bb-buck lesson (2026-08-16 board_edit entry) with the sign
flipped: fit measures the placement in front of it, and a placement stretched to a big
outline has already spent the difference.
Both `reference/recipes/resize-board.md` ("Place (P6) against that room, gate `place`",
then fit) and the P6 agent contract order it place -> gate -> fit. For a `canonical`
binding with ANY `placement.edges` entry the order has to be **place -> fit -> gate**.
Measured on this board: after `board_edit --outline fit --margin M` the place gate is
clean (0 violations, all five coverage legs green) at M = 0.5 / 1.0 / 2.0, giving
34.77 x 22.26 / 35.77 x 23.26 / 37.77 x 25.26 mm. The fix is the ORDER, not the
placement. Second-order trap in the same shape: `silk_place` and `board_edit --outline
fit` disagree about what is on the board - fit measures courtyards + copper + rule areas
and ignores silk, while silk_place solves refdes positions against the CURRENT outline,
so on the provisional board it parked J1/J3/H1/H2's refdes where the earned edge later
cuts them. Hand-place any refdes outside the future content bbox, or re-run silk_place
after the fit.
