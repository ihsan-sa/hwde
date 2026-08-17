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
