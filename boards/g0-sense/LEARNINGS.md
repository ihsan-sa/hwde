# LEARNINGS - g0-sense (workspace learnings)

Workspace-local. Every entry gets a date, tags (stage tag first: P0-P10), and a
one-line claim as its title. `learnings.py compile --workspace boards/g0-sense` turns new
entries into `learnings/queue.yaml`; the `promote` verb rules on them.
Research tasks (research.py close) append their entries here automatically.

## 2026-08-27 [P2][research][knowledge][block:B1] research task block-usbc-sink-1: 7 verified record(s) for block:B1
Gap: research block 'usbc-sink': produce its coverage checklist, then populate it
Operating point: {"board_layers": 2, "iout_a": 0.5, "pdiss_w": 0.003, "source_kind": "usb", "vin_v": 5.0, "vout_v": 5.0}
Missing classes: coverage-checklist

Verified records (second reader signed). Promotion = the research verb's promote step (copies record + sources into the library), then the queue ruling with kind knowledge_record targeting reference/knowledge/records/<id>.yaml, then the owner's approval block:
- usbc-sink-attach-capacitance-10uf [inrush, decoupling] boards/g0-sense/research/records/usbc-sink-attach-capacitance-10uf.yaml
- usbc-sink-cc-independent-rd-principle [selection] boards/g0-sense/research/records/usbc-sink-cc-independent-rd-principle.yaml
- usbc-sink-constraints-emission [constraints-emission] boards/g0-sense/research/records/usbc-sink-constraints-emission.yaml
- usbc-sink-default-current-entitlement [selection] boards/g0-sense/research/records/usbc-sink-default-current-entitlement.yaml
- usbc-sink-rd-5k1-per-pin [selection] boards/g0-sense/research/records/usbc-sink-rd-5k1-per-pin.yaml
- usbc-sink-receptacle-land-all-shell-bond [selection, emi] boards/g0-sense/research/records/usbc-sink-receptacle-land-all-shell-bond.yaml
- usbc-sink-vbus-tvs-before-series-element [esd] boards/g0-sense/research/records/usbc-sink-vbus-tvs-before-series-element.yaml
Draft coverage checklist(s) for the owner to approve:
- usbc-sink boards/g0-sense/research/checklists/usbc-sink.yaml (6 classes)
Sources (quarantined, sha-pinned in the task ledger):
- research/sources/USB-20Type-C-20Spec-20R2.0-20--20August-202019.pdf tier vendor-appnote sha256 87d15160bf8b <https://www.usb.org/sites/default/files/USB%20Type-C%20Spec%20R2.0%20-%20August%202019.pdf>
- research/sources/usb4105.pdf tier vendor-layout sha256 fb331fbabee8 <https://gct.co/files/drawings/usb4105.pdf>
- research/sources/TVS_App_Notes-SI21-03-ESD_Protection_of_USB_Type-C_Interfaces_New_Template.pdf tier cross-vendor sha256 cb7fb1ce0edc <https://www.semtech.com/uploads/design-support/TVS_App_Notes-SI21-03-ESD_Protection_of_USB_Type-C_Interfaces_New_Template.pdf>
- research/sources/slva680a.pdf tier cross-vendor sha256 414236c18903 <https://www.ti.com/lit/pdf/slva680>
Task file: boards/g0-sense/research/tasks/block-usbc-sink-1.json

## 2026-08-27 [P2][research][knowledge][block:B2] research task block-ldo-1: 5 verified record(s) for block:B2
Gap: research block 'ldo': produce its coverage checklist, then populate it
Operating point: {"board_layers": 2, "integration_kind": "integrated-fet", "iout_a": 0.3, "pdiss_w": 0.51, "source_kind": "usb", "vin_v": 5.0, "vout_v": 3.3}
Missing classes: coverage-checklist

Verified records (second reader signed). Promotion = the research verb's promote step (copies record + sources into the library), then the queue ruling with kind knowledge_record targeting reference/knowledge/records/<id>.yaml, then the owner's approval block:
- ldo-1117-family-output-cap-esr [feedback] boards/g0-sense/research/records/ldo-1117-family-output-cap-esr.yaml
- ldo-1117-input-cap-and-protection [decoupling] boards/g0-sense/research/records/ldo-1117-input-cap-and-protection.yaml
- ldo-dropout-headroom-budget [selection] boards/g0-sense/research/records/ldo-dropout-headroom-budget.yaml
- ldo-output-cap-esr-window-principle [feedback] boards/g0-sense/research/records/ldo-output-cap-esr-window-principle.yaml
- ldo-sot223-thermal-copper-sets-current [thermal] boards/g0-sense/research/records/ldo-sot223-thermal-copper-sets-current.yaml
Draft coverage checklist(s) for the owner to approve:
- ldo boards/g0-sense/research/checklists/ldo.yaml (4 classes)
Sources (quarantined, sha-pinned in the task ledger):
- research/sources/2304140030_Advanced-Monolithic-Systems-AMS1117-3-3_C6186.pdf tier vendor-layout sha256 189a2651878a <https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/2304140030_Advanced-Monolithic-Systems-AMS1117-3-3_C6186.pdf>
- research/sources/lm1117.pdf tier cross-vendor sha256 35892f3a8673 <https://www.ti.com/lit/ds/symlink/lm1117.pdf>
- research/sources/snva167a.pdf tier cross-vendor sha256 30ea0a571b22 <https://www.ti.com/lit/an/snva167a/snva167a.pdf>
- research/sources/AP2112.pdf tier cross-vendor sha256 ef8d376f2ec3 <https://www.diodes.com/assets/Datasheets/AP2112.pdf>
Task file: boards/g0-sense/research/tasks/block-ldo-1.json

## 2026-08-27 [P2][research][knowledge][block:B4] research task block-sht4x-1: 6 verified record(s) for block:B4
Gap: research block 'sht4x': produce its coverage checklist, then populate it
Operating point: {"board_layers": 2, "pdiss_w": 0.25, "source_kind": "usb", "vin_v": 3.3}
Missing classes: coverage-checklist

Verified records (second reader signed). Promotion = the research verb's promote step (copies record + sources into the library), then the queue ruling with kind knowledge_record targeting reference/knowledge/records/<id>.yaml, then the owner's approval block:
- sht4x-assembly-fab-contract [constraints-emission] boards/g0-sense/research/records/sht4x-assembly-fab-contract.yaml
- sht4x-i2c-pullup-bus-cap [selection] boards/g0-sense/research/records/sht4x-i2c-pullup-bus-cap.yaml
- sht4x-rht-pcb-conduction-principle [thermal] boards/g0-sense/research/records/sht4x-rht-pcb-conduction-principle.yaml
- sht4x-thermal-isolation-island [thermal] boards/g0-sense/research/records/sht4x-thermal-isolation-island.yaml
- sht4x-vdd-decoupling-heater-transient [decoupling] boards/g0-sense/research/records/sht4x-vdd-decoupling-heater-transient.yaml
- sht4x-vdd-slew-power-up [sequencing] boards/g0-sense/research/records/sht4x-vdd-slew-power-up.yaml
Draft coverage checklist(s) for the owner to approve:
- sht4x boards/g0-sense/research/checklists/sht4x.yaml (5 classes)
Sources (quarantined, sha-pinned in the task ledger):
- research/sources/HT_DS_Datasheet_SHT4x.pdf tier vendor-layout sha256 2d471eb9d9f5 <https://sensirion.com/media/documents/33FD6951/661CD142/HT_DS_Datasheet_SHT4x.pdf>
- research/sources/Sensirion_Humidity_Temperature_Design_Guide.pdf tier vendor-appnote sha256 b7db78c1e8a8 <https://sensirion.com/media/documents/FC5BED84/662B494D/Sensirion_Humidity_Temperature_Design_Guide.pdf>
- research/sources/HT_Handling_Instructions_SHTxx.pdf tier vendor-appnote sha256 80be25deb1b1 <https://sensirion.com/media/documents/6D95AA80/6840311F/HT_Handling_Instructions_SHTxx.pdf>
- research/sources/UM10204.pdf tier cross-vendor sha256 dc91f00f6558 <https://www.nxp.com/docs/en/user-guide/UM10204.pdf>
Task file: boards/g0-sense/research/tasks/block-sht4x-1.json

## 2026-08-27 [P2][research][knowledge][block:B3] research task block-mcu-1: 4 verified record(s) for block:B3
Gap: research block 'mcu': produce its coverage checklist, then populate it
Operating point: {"board_layers": 2, "fsw_khz": 16000, "pdiss_w": 0.008, "source_kind": "usb", "vin_v": 3.3}
Missing classes: coverage-checklist

Verified records (second reader signed). Promotion = the research verb's promote step (copies record + sources into the library), then the queue ruling with kind knowledge_record targeting reference/knowledge/records/<id>.yaml, then the owner's approval block:
- mcu-decoupling-bonded-vdda-single-pair [decoupling] boards/g0-sense/research/records/mcu-decoupling-bonded-vdda-single-pair.yaml
- mcu-decoupling-per-supply-pin-pair [decoupling] boards/g0-sense/research/records/mcu-decoupling-per-supply-pin-pair.yaml
- mcu-internal-rc-accuracy-vs-interface-budget [selection] boards/g0-sense/research/records/mcu-internal-rc-accuracy-vs-interface-budget.yaml
- mcu-nrst-internal-pullup-and-cap [sequencing] boards/g0-sense/research/records/mcu-nrst-internal-pullup-and-cap.yaml
Refuted (left draft, not promotable):
- mcu-boot-strap-only-when-option-bytes-consult-pin: Datasheet half holds: p.14 3.5 verbatim ('the boot pin is shared with a standard GPIO and can be enabled through the boot selector option bit'; bootloader on USART PA9/PA10 or PA2/PA3, I2C PB6/PB7 or PB10/PB11); Table 12 p.33 shows PA14-BOOT0 at TSSOP20 pin 19 with alternate functions SWCLK/USART2_TX and additional functions ADC_IN18/BOOT0, and the PA15 row carries the same TSSOP20 pin 19, so 'BOOT0 shares pin 19 with SWCLK, bonded with PA15' is supported; p.34 note 5 verbatim (upon reset these pins are SW debug AF, pull-up on PA13 and pull-down on PA14 active). REFUTED on tier and support: the entire load-bearing claim - factory user option bytes 0xDFFF E1AA, nBoot0=nBoot1=nBOOT_SEL=1, 'the BOOT0 pin state is ignored', empty flash still enters the bootloader (AN2606 pattern 11), clear nBOOT_SEL to make the pin matter - rests SOLELY on the community.st.com thread, which is forum tier. That page is a moderator quoting RM0454 3.4.1 and AN2606; neither document is in this ledger, so the record cites no vendor-tier page for its own conclusion. Text-searched the whole datasheet: no occurrence of nBOOT, no option-byte default value, no boot-mode table; p.14 says only that the pin CAN be enabled through the option bit and never that it is disabled as shipped. Rule fields boot0_strap_required:false, factory_user_option_bytes and factory_nboot_sel are therefore unsupported by the acquired sources, and the record itself flags RM0454 2.5 as an open cite-and-verify. Since the board's no-BOOT0-strap decision rests on this record, it must not go active until RM0454 2.5 + 3.4.1 (or AN2606) is acquired; the pinout/pin-sharing half can be kept as-is.
Draft coverage checklist(s) for the owner to approve:
- mcu boards/g0-sense/research/checklists/mcu.yaml (3 classes)
Sources (quarantined, sha-pinned in the task ledger):
- research/sources/2009240934_STMicroelectronics-STM32G030F6P6_C724040.pdf tier vendor-layout sha256 bd4d70f72b2e <https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/2009240934_STMicroelectronics-STM32G030F6P6_C724040.pdf>
- research/sources/AN2519-AVR-Microcontroller-Hardware-Design-Considerations-00002519B.pdf tier cross-vendor sha256 26b325f16f52 <https://ww1.microchip.com/downloads/en/Appnotes/AN2519-AVR-Microcontroller-Hardware-Design-Considerations-00002519B.pdf>
- research/sources/stm32g030-does-not-enter-bootloader-when-boot0-is-3-3v-what-is-boot-selector-option-bit-thank-you-40845.html tier forum sha256 30c70b4d58c9 <https://community.st.com/t5/stm32-mcus-embedded-software/stm32g030-does-not-enter-bootloader-when-boot0-is-3-3v-what-is/td-p/222450>
- research/sources/GUID-3FD21524-1116-412C-8139-B7FBEA62950A.html tier cross-vendor sha256 e7161109a097 <https://onlinedocs.microchip.com/oxy/GUID-E9CAC59E-138C-416E-BE25-C5E915288E6D-en-US-3/GUID-3FD21524-1116-412C-8139-B7FBEA62950A.html>
Task file: boards/g0-sense/research/tasks/block-mcu-1.json

## 2026-08-27 [P7][routing][stitch_vias] Redundant pad vias violate hole_to_hole when the pad is track-connected through a multi-segment chain
stitch_vias' already-connected detection missed pads (C10.2, C12.2, C11.2) whose GND
connection runs pad -> 2-3 track segments -> existing via; it placed new pad vias 0.22-0.45 mm
(hole edge) from those existing vias, tripping aiee_hole_to_hole_floor (0.5 mm) 4 times.
It also placed D1.2's needed via too close to a route via. Fix pattern: after stitch_vias,
DRC immediately; remove the redundant new vias (the old track chain stands), move the needed
ones. Measured on this board, kicad-cli 10.0.5.

## 2026-08-27 [P7][routing][plane_repair] VBUS bridge routed through the connector body - restore-and-restrict pattern works
plane_repair (unrestricted) joined the two F.Cu VBUS pours with 0.5 mm tracks straight
through J1's footprint: shorting_items vs no-net pad B8, 2x NPTH hole_clearance, 5x
track_width vs the 0.8 mm VBUS rule - while exiting 0 ("pass", repaired: true). Its own
success signal is untrusted, like Freerouting's: only kicad-cli DRC counts. The +3V3 repair
in the same run was clean. Pattern: snapshot before plane_repair (role prompt already says
so), DRC after, and on garbage restore + re-run with --net/--layer restricted to the nets
whose repair was clean; hand-fix the rest with route_edit.

## 2026-08-27 [P7][routing][route_auto] On the 2-layer chain a route_auto placement_adjust_request naming plane-carried nets is premature
route_auto (chain position: before stitch_vias/plane_repair on 2L) emitted a
placement_adjust_request for {+3V3, /main/SDA, GND, VBUS} "unrouted after 3 freerouting
rungs" - but GND/+3V3/VBUS were plane-carried by design and later chain steps own them;
SDA needed one point-fix trunk. Finishing the chain closed all four: DRC 0, completion 1.0.
Judge such a request against the chain position before taking the P7->P6 backward edge.

## 2026-08-27 [P7][routing][drc] starved_thermal (min spoke 2, actual 1) clears with a same-net track stub into open fill
Two pads (C11.1, U2.4) were geometry-capped at 1 thermal spoke. Adding a short same-net
track from the pad into open fill area (0.15-0.2 mm, few mm, no other copper touched)
cleared DRCE_STARVED_THERMAL on kicad-cli 10.0.5 - no zone min-spoke edit, no solid-connect
override needed. Cheapest lawful fix; try it before touching zone properties.
