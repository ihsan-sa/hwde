# Human-made board corpus: gate baseline

Written by `human_corpus.py table`; docs/human-corpus.md says how to read it. verify and dfm counts are errors / warnings for verify_all and errors / all findings for dfm_check.

| board | domain | layers | outcome | verify_all | errors / warnings | dfm_check | errors / findings |
|---|---|---|---|---|---|---|---|
| [egg-ldo-1000](#egg-ldo-1000) | power | 2 |  | violations | 0 / 7 | violations | 4 / 5 |
| [egg-ldo-250](#egg-ldo-250) | power | 2 |  | violations | 0 / 3 | violations | 4 / 4 |
| [tp4056-power-path](#tp4056-power-path) | power | 2 |  | violations | 1 / 10 | pass | 0 / 2 |
| [usbc-pd-reflow-plate](#usbc-pd-reflow-plate) | power | 4 |  | violations | 9 / 9 | violations | 72 / 74 |
| [atx12vo-5vsb-adapter](#atx12vo-5vsb-adapter) | power | 4 |  | violations | 43 / 8 | violations | 31 / 33 |
| [led-driver-9w](#led-driver-9w) | power | 2 |  | violations | 0 / 4 | violations | 1 / 3 |
| [bratwurst-power](#bratwurst-power) | power | 4 |  | error | 37 / 144 | violations | 757 / 760 |
| [xt30-power-module](#xt30-power-module) | power | 2 |  | violations | 0 / 6 | violations | 1 / 3 |
| [soleil-power](#soleil-power) | power | 4 |  | violations | 1 / 13 | violations | 41 / 43 |
| [type-c-recessed](#type-c-recessed) | power | 2 |  | violations | 0 / 2 | violations | 10 / 15 |
| [libresolar-bms-c1](#libresolar-bms-c1) | power | 4 |  | violations | 4 / 19 | violations | 4 / 5 |
| [placebo-stm32g0](#placebo-stm32g0) | mcu-usb | 2 |  | violations | 8 / 42 | violations | 2 / 4 |
| [atsamd20-breakout](#atsamd20-breakout) | mcu-usb | 2 |  | violations | 31 / 0 | violations | 3 / 11 |
| [samd21e-breakout](#samd21e-breakout) | mcu-usb | 2 |  | violations | 16 / 33 | violations | 33 / 37 |
| [rp-micro](#rp-micro) | mcu-usb | 2 |  | violations | 112 / 13 | violations | 76 / 78 |
| [usb-i2c-bridge](#usb-i2c-bridge) | mcu-usb | 2 |  | violations | 13 / 27 | violations | 84 / 86 |
| [pdk-prog](#pdk-prog) | mcu-usb | 2 |  | violations | 12 / 14 | violations | 2 / 3 |
| [rp2040-dmxsun](#rp2040-dmxsun) | mcu-usb | 2 |  | violations | 24 / 4 | violations | 6 / 8 |
| [rp2040-dmxsun-iso-io](#rp2040-dmxsun-iso-io) | analog | 2 |  | violations | 2 / 5 | violations | 7 / 12 |
| [buspirate5-rev10](#buspirate5-rev10) | mcu-usb | 4 | fixed-in-later-rev | violations | 309 / 60 | violations | 196 / 257 |
| [buspirate5-rev10a](#buspirate5-rev10a) | mcu-usb | 4 |  | violations | 311 / 61 | violations | 198 / 260 |
| [glasgow-revc3](#glasgow-revc3) | mcu-usb | 4 | product | violations | 488 / 298 | violations | 106 / 121 |
| [glasgow-revd0](#glasgow-revd0) | mcu-usb | 6 |  | violations | 73 / 296 | violations | 1917 / 1926 |
| [glasgow-revd1](#glasgow-revd1) | mcu-usb | 6 | errata | violations | 21 / 293 | violations | 2024 / 2041 |
| [usbc-cable-tester](#usbc-cable-tester) | mcu-usb | 2 |  | violations | 49 / 1 | violations | 50 / 51 |
| [gulu-esp32c3-epaper](#gulu-esp32c3-epaper) | mcu-usb | 2 |  | violations | 1 / 1 | violations | 1 / 2 |
| [esp32-poe-m1](#esp32-poe-m1) | mcu-usb | 4 | product | violations | 12 / 159 | violations | 59 / 68 |
| [esp32-poe-m2](#esp32-poe-m2) | mcu-usb | 4 | product | violations | 13 / 159 | violations | 64 / 75 |
| [thatmicpre](#thatmicpre) | analog | 2 |  | violations | 6 / 0 | violations | 382 / 386 |
| [micro-pico-synth](#micro-pico-synth) | analog | 4 |  | violations | 8 / 87 | violations | 27 / 29 |
| [current-probe](#current-probe) | analog | 2 |  | violations | 2 / 0 | violations | 27 / 29 |
| [thunderscope](#thunderscope) | analog | 6 | errata | violations | 417 / 274 | violations | 4129 / 4129 |
| [scan2000](#scan2000) | analog | 4 |  | error | 2 / 57 | violations | 39 / 41 |
| [anthracite-fuzz](#anthracite-fuzz) | analog | 4 |  | violations | 69 / 42 | violations | 10 / 12 |
| [usb2speakon](#usb2speakon) | analog | 4 |  | violations | 1 / 71 | violations | 10 / 14 |
| [nodepilot](#nodepilot) | analog | 2 |  | violations | 0 / 7 | pass | 0 / 1 |
| [moco](#moco) | motor | 2 |  | violations | 5 / 9 | violations | 129 / 133 |
| [moco-rd501](#moco-rd501) | motor | 4 |  | violations | 3 / 33 | violations | 102 / 109 |
| [mini-motor-controller](#mini-motor-controller) | motor | 2 |  | violations | 5 / 48 | violations | 319 / 322 |
| [bt-dc-motor-board](#bt-dc-motor-board) | motor | 4 |  | violations | 67 / 2 | violations | 5 / 11 |
| [openesc-30x30](#openesc-30x30) | motor | 6 |  | violations | 258 / 29 | violations | 5526 / 5740 |
| [mighty-micro-motors](#mighty-micro-motors) | motor | 4 |  | violations | 4 / 10 | violations | 56 / 62 |
| [rf-prototype-boards](#rf-prototype-boards) | rf | 2 |  | pass | 0 / 0 | violations | 12 / 12 |
| [mountaineer](#mountaineer) | rf | 2 |  | violations | 3 / 12 | violations | 1135 / 1144 |
| [beaglebone-lora-adapter](#beaglebone-lora-adapter) | rf | 4 |  | violations | 0 / 2 | violations | 33 / 34 |
| [rf-wifi-bridge](#rf-wifi-bridge) | rf | 2 |  | violations | 17 / 1 | violations | 22 / 23 |
| [lorapowerbox](#lorapowerbox) | rf | 4 |  | violations | 46 / 6 | violations | 23 / 24 |
| [s-band-antenna](#s-band-antenna) | rf | 2 |  | violations | 1 / 1 | violations | 1 / 2 |
| [ocxo-breakout](#ocxo-breakout) | rf | 4 |  | violations | 5 / 2 | violations | 52 / 54 |
| [jetson-orin-baseboard](#jetson-orin-baseboard) | 4-layer | 8 |  | error | 555 / 875 | no report (exit 2) | 0 / 0 |
| [tokay-lite](#tokay-lite) | 4-layer | 4 |  | violations | 51 / 199 | violations | 38 / 40 |
| [tokay-lite-rev3.1](#tokay-lite-rev3.1) | 4-layer | 4 |  | violations | 46 / 218 | violations | 38 / 40 |
| [ottercast-audio-v2](#ottercast-audio-v2) | 4-layer | 4 |  | violations | 23 / 290 | violations | 152 / 160 |
| [mackerel-68k](#mackerel-68k) | 4-layer | 4 |  | violations | 20 / 10 | violations | 7 / 8 |

## Error findings by kind

How many boards each kind of error finding fires on: a kind that fires on most boards is a gate to question before it is a board to blame.

| check / kind | boards |
|---|---|
| check_silk / silk_over_pad | 42 |
| check.dfm / dfm_hole_to_hole | 33 |
| check.dfm / dfm_clearance | 28 |
| check.dfm / dfm_copper_to_edge | 27 |
| check.dfm / dfm_silk_over_pad | 25 |
| check.dfm / dfm_annular_ring | 24 |
| check.dfm / dfm_hole_to_edge | 9 |
| check.dfm / dfm_open_outline | 7 |
| check_mating / mating_zone_blocked | 7 |
| check_diffpair / diffpair_skew | 6 |
| check.dfm / pad_net_mismatch | 4 |
| check_diffpair / diffpair_uncoupled | 4 |
| castellation / castellated_unmarked | 3 |
| check.dfm / dfm_hole_size | 3 |
| check.dfm / dfm_trace_width | 3 |
| castellation / castellated_pad_extension | 2 |
| check.dfm / dfm_pad_tented | 2 |
| check_mating / mating_faces_inward | 2 |
| check.dfm / dfm_missing_layer | 1 |
| check_mating / mating_mouth_inset | 1 |

## Per-board findings

### egg-ldo-1000

https://github.com/Plaenkler/Egg_LDO_1000 at `f91ce292fac7`, `Egg_LDO_1000.kicad_pcb`, BSD-3-Clause, power, 2 layers.

verify_all checks: check_creepage skipped, check_current skipped, check_decoupling skipped, check_diffpair pass, check_mating pass, check_pdn skipped, check_ratings skipped, check_return_path skipped, check_route_style violations, check_silk violations, check_thermal skipped

| severity | check | finding | where |
|---|---|---|---|
| error | castellation / castellated_pad_extension | J2.1: pad reaches 0.350 mm inward past the hole, JLC minimum 0.5 mm | J2 @ (143.0, 104.4) |
| error | castellation / castellated_pad_extension | J3.1: pad reaches 0.350 mm inward past the hole, JLC minimum 0.5 mm | J3 @ (157.0, 106.9) |
| error | castellation / castellated_pad_extension | J5.1: pad reaches 0.350 mm inward past the hole, JLC minimum 0.5 mm | J5 @ (143.0, 106.9) |
| error | castellation / castellated_pad_extension | J1.1: pad reaches 0.350 mm inward past the hole, JLC minimum 0.5 mm | J1 @ (157.0, 104.4) |
| warning | check_silk / silk_thin | silk text "EGG LDO 1000" stroke 0.100 mm (< 0.12 mm min) | @ (150.0, 96.8) |
| warning | check_silk / silk_thin | silk text "Github.com/Plaenkler" stroke 0.100 mm (< 0.12 mm min) | @ (151.3, 94.8) |
| warning | check_route_style / route_style | 10 track arc(s) - owner style is straight and 45-degree copper on +5V F.Cu | +5V @ (148.5, 100.0) |
| warning | check_route_style / route_style | 1 track arc(s) - owner style is straight and 45-degree copper on Net-(J4-PadA5) B.Cu | Net-(J4-PadA5) @ (153.9, 98.5) |
| warning | check_route_style / route_style | 1 track arc(s) - owner style is straight and 45-degree copper on Net-(J4-PadA5) F.Cu | Net-(J4-PadA5) @ (150.6, 97.7) |
| warning | check_route_style / route_style | 1 track arc(s) - owner style is straight and 45-degree copper on Net-(J4-PadB5) B.Cu | Net-(J4-PadB5) @ (147.9, 97.7) |
| warning | check_route_style / route_style | 2 track arc(s) - owner style is straight and 45-degree copper on Net-(J4-PadB5) F.Cu | Net-(J4-PadB5) @ (145.3, 102.5) |
| warning | check.dfm / dfm_silk_width | 299 silk strokes below JLC minimum width 0.15 mm (narrowest 0.1000 mm) on B.Silkscreen | @ (149.5, 97.2) |

### egg-ldo-250

https://github.com/Plaenkler/Egg_LDO_250 at `7b009505f8d6`, `Egg_LDO_250.kicad_pcb`, BSD-3-Clause, power, 2 layers.

verify_all checks: check_creepage skipped, check_current skipped, check_decoupling skipped, check_diffpair pass, check_mating pass, check_pdn skipped, check_ratings skipped, check_return_path skipped, check_route_style violations, check_silk pass, check_thermal skipped

| severity | check | finding | where |
|---|---|---|---|
| error | castellation / castellated_pad_extension | J5.1: pad reaches 0.350 mm inward past the hole, JLC minimum 0.5 mm | J5 @ (156.8, 102.5) |
| error | castellation / castellated_pad_extension | J3.1: pad reaches 0.350 mm inward past the hole, JLC minimum 0.5 mm | J3 @ (142.8, 102.5) |
| error | castellation / castellated_pad_extension | J2.1: pad reaches 0.350 mm inward past the hole, JLC minimum 0.5 mm | J2 @ (142.8, 105.0) |
| error | castellation / castellated_pad_extension | J1.1: pad reaches 0.350 mm inward past the hole, JLC minimum 0.5 mm | J1 @ (156.8, 105.0) |
| warning | check_route_style / route_style | 11 track arc(s) - owner style is straight and 45-degree copper on +5V F.Cu | +5V @ (146.5, 101.8) |
| warning | check_route_style / route_style | 1 track arc(s) - owner style is straight and 45-degree copper on Net-(J4-PadA5) F.Cu | Net-(J4-PadA5) @ (150.3, 97.1) |
| warning | check_route_style / route_style | 1 track arc(s) - owner style is straight and 45-degree copper on Net-(J4-PadB5) F.Cu | Net-(J4-PadB5) @ (149.2, 97.1) |

### tp4056-power-path

https://github.com/DoImant/TP4056-Power-Path-PCB at `70636f5a07e7`, `TC4056-Bypass.kicad_pcb`, CC-BY-SA-4.0, power, 2 layers.

verify_all checks: check_creepage skipped, check_current skipped, check_decoupling skipped, check_diffpair pass, check_mating pass, check_pdn skipped, check_ratings skipped, check_return_path skipped, check_route_style pass, check_silk violations, check_thermal skipped

| severity | check | finding | where |
|---|---|---|---|
| error | check_silk / silk_over_pad | silk "hide" on F.SilkS covers pad ?.1 (2.12 mm2) | ? @ (63.5, 46.3) |
| warning | check_silk / silk_thin | silk text "OUT+" stroke 0.100 mm (< 0.12 mm min) | @ (76.1, 44.7) |
| warning | check_silk / silk_thin | silk text "GND" stroke 0.100 mm (< 0.12 mm min) | @ (76.1, 40.5) |
| warning | check_silk / silk_thin | silk text "GND" stroke 0.100 mm (< 0.12 mm min) | @ (61.3, 40.5) |
| warning | check_silk / silk_thin | silk text "BAT+" stroke 0.100 mm (< 0.12 mm min) | @ (76.2, 48.6) |
| warning | check_silk / silk_thin | silk text "IN+" stroke 0.100 mm (< 0.12 mm min) | @ (61.5, 48.6) |
| warning | check_silk / silk_thin | silk text "BAT+" stroke 0.100 mm (< 0.12 mm min) | @ (76.1, 48.6) |
| warning | check_silk / silk_thin | silk text "IN+" stroke 0.100 mm (< 0.12 mm min) | @ (61.3, 48.6) |
| warning | check_silk / silk_thin | silk text "OUT+" stroke 0.100 mm (< 0.12 mm min) | @ (76.1, 44.7) |
| warning | check_silk / silk_thin | silk text "GND" stroke 0.100 mm (< 0.12 mm min) | @ (76.1, 40.5) |
| warning | check_silk / silk_thin | silk text "GND" stroke 0.100 mm (< 0.12 mm min) | @ (61.3, 40.5) |
| warning | check.dfm / dfm_silk_width | 131 silk strokes below JLC minimum width 0.15 mm (narrowest 0.1000 mm) on F.Silkscreen | @ (76.0, 49.7) |
| warning | check.dfm / dfm_silk_width | 122 silk strokes below JLC minimum width 0.15 mm (narrowest 0.1000 mm) on B.Silkscreen | @ (76.5, 45.9) |

### usbc-pd-reflow-plate

https://github.com/incend1um3/USB-C-PD-Reflow-Plate at `cdb72bbe5601`, `hardware/Reflow Plate Controller/Reflow Plate Controller.kicad_pcb`, CERN-OHL-S-2.0, power, 4 layers.

verify_all checks: check_creepage skipped, check_current skipped, check_decoupling skipped, check_diffpair pass, check_mating pass, check_pdn skipped, check_ratings skipped, check_return_path skipped, check_route_style violations, check_silk violations, check_thermal skipped

| severity | check | finding | where |
|---|---|---|---|
| error | check_silk / silk_over_pad | silk "THERMISTOR" on F.SilkS covers pad TP2.1 (0.78 mm2) | TP2 @ (173.5, 119.2) |
| error | check_silk / silk_over_pad | silk "3V3" on F.SilkS covers pad TP1.1 (0.48 mm2) | TP1 @ (101.5, 111.5) |
| error | check_silk / silk_over_pad | silk "SWDIO" on F.SilkS covers pad J1.2 (1.26 mm2) | J1 @ (144.7, 80.0) |
| error | check_silk / silk_over_pad | silk "SWCLK" on F.SilkS covers pad J1.3 (1.31 mm2) | J1 @ (147.2, 80.0) |
| error | check_silk / silk_over_pad | silk "~{RST}" on F.SilkS covers pad J1.5 (1.48 mm2) | J1 @ (152.3, 80.0) |
| error | check_silk / silk_over_pad | silk "3V3" on B.SilkS covers pad J4.4 (1.39 mm2) | J4 @ (172.4, 80.2) |
| error | check_silk / silk_over_pad | silk "GND" on B.SilkS covers pad J4.3 (1.39 mm2) | J4 @ (174.9, 80.2) |
| error | check_silk / silk_over_pad | silk rect on F.SilkS covers pad LED1.1 (0.79 mm2) | LED1 @ (119.4, 107.7) |
| error | check_silk / silk_over_pad | silk rect on F.SilkS covers pad LED1.2 (0.79 mm2) | LED1 @ (119.4, 106.2) |
| error | check.dfm / dfm_copper_to_edge | copper 0.2005 mm from board edge, JLC minimum 0.3 mm on F.Cu | @ (130.6, 81.8) |
| error | check.dfm / dfm_copper_to_edge | copper 0.2005 mm from board edge, JLC minimum 0.3 mm on F.Cu | @ (151.9, 116.3) |
| error | check.dfm / dfm_copper_to_edge | copper 0.2005 mm from board edge, JLC minimum 0.3 mm on In1.Cu | @ (146.1, 100.0) |
| error | check.dfm / dfm_copper_to_edge | copper 0.2005 mm from board edge, JLC minimum 0.3 mm on In2.Cu | @ (145.7, 100.8) |
| error | check.dfm / dfm_copper_to_edge | copper 0.2005 mm from board edge, JLC minimum 0.3 mm on B.Cu | @ (146.3, 100.6) |
| error | check.dfm / dfm_hole_to_hole | hole-to-hole 0.4500 mm below JLC minimum 0.5 mm | @ (107.8, 83.8) |
| error | check.dfm / dfm_hole_to_hole | hole-to-hole 0.4500 mm below JLC minimum 0.5 mm | @ (107.8, 83.8) |
| error | check.dfm / dfm_hole_to_hole | hole-to-hole 0.4500 mm below JLC minimum 0.5 mm | @ (107.8, 84.5) |
| error | check.dfm / dfm_hole_to_hole | hole-to-hole 0.4500 mm below JLC minimum 0.5 mm | @ (107.8, 84.5) |
| error | check.dfm / dfm_hole_to_hole | hole-to-hole 0.4500 mm below JLC minimum 0.5 mm | @ (107.8, 85.2) |
| error | check.dfm / dfm_hole_to_hole | hole-to-hole 0.4500 mm below JLC minimum 0.5 mm | @ (107.8, 86.8) |
| error | check.dfm / dfm_hole_to_hole | hole-to-hole 0.4500 mm below JLC minimum 0.5 mm | @ (107.8, 86.8) |
| error | check.dfm / dfm_hole_to_hole | hole-to-hole 0.4500 mm below JLC minimum 0.5 mm | @ (107.8, 87.5) |
| error | check.dfm / dfm_hole_to_hole | hole-to-hole 0.4500 mm below JLC minimum 0.5 mm | @ (108.5, 83.8) |
| error | check.dfm / dfm_hole_to_hole | hole-to-hole 0.4500 mm below JLC minimum 0.5 mm | @ (108.5, 84.5) |
| error | check.dfm / dfm_hole_to_hole | hole-to-hole 0.4500 mm below JLC minimum 0.5 mm | @ (108.5, 86.8) |

67 more in `runs/usbc-pd-reflow-plate/reports/`.

### atx12vo-5vsb-adapter

https://github.com/RandomDelta6/ATX12VO-5VSB-to-12VSB-Adapter at `9f0151848011`, `12VSB.kicad_pcb`, CC-BY-SA-4.0, power, 4 layers.

verify_all checks: check_creepage skipped, check_current skipped, check_decoupling skipped, check_diffpair pass, check_mating pass, check_pdn skipped, check_ratings skipped, check_return_path skipped, check_route_style violations, check_silk violations, check_thermal skipped

| severity | check | finding | where |
|---|---|---|---|
| error | check_silk / silk_over_pad | silk "12VSB04112023 Rev.002" on F.SilkS covers pad ?.1 (0.42 mm2) | ? @ (57.8, 68.3) |
| error | check_silk / silk_over_pad | silk "12VSB04112023 Rev.002" on F.SilkS covers pad ?.2 (0.42 mm2) | ? @ (59.5, 68.3) |
| error | check_silk / silk_over_pad | silk "hide" on F.SilkS covers pad ?.1 (0.81 mm2) | ? @ (63.1, 58.8) |
| error | check_silk / silk_over_pad | silk "hide" on F.SilkS covers pad ?.2 (0.81 mm2) | ? @ (63.1, 57.3) |
| error | check_silk / silk_over_pad | silk "hide" on F.SilkS covers pad ?.1 (0.33 mm2) | ? @ (66.1, 62.0) |
| error | check_silk / silk_over_pad | silk "hide" on F.SilkS covers pad ?.2 (0.33 mm2) | ? @ (67.1, 62.0) |
| error | check_silk / silk_over_pad | silk "hide" on F.SilkS covers pad ?.1 (0.73 mm2) | ? @ (57.8, 68.3) |
| error | check_silk / silk_over_pad | silk "hide" on F.SilkS covers pad ?.2 (0.73 mm2) | ? @ (59.5, 68.3) |
| error | check_silk / silk_over_pad | silk "hide" on F.SilkS covers pad ?.1 (2.86 mm2) | ? @ (63.4, 54.4) |
| error | check_silk / silk_over_pad | silk "hide" on F.SilkS covers pad ?.2 (4.15 mm2) | ? @ (59.1, 54.4) |
| error | check_silk / silk_over_pad | silk "hide" on F.SilkS covers pad ?.1 (2.86 mm2) | ? @ (63.4, 54.4) |
| error | check_silk / silk_over_pad | silk "hide" on F.SilkS covers pad ?.2 (4.15 mm2) | ? @ (59.1, 54.4) |
| error | check_silk / silk_over_pad | silk "hide" on F.SilkS covers pad ?.2 (0.82 mm2) | ? @ (66.6, 60.0) |
| error | check_silk / silk_over_pad | silk "hide" on F.SilkS covers pad ?.1 (0.73 mm2) | ? @ (64.8, 57.2) |
| error | check_silk / silk_over_pad | silk "hide" on F.SilkS covers pad ?.2 (0.73 mm2) | ? @ (64.8, 58.9) |
| error | check_silk / silk_over_pad | silk "hide" on F.SilkS covers pad ?.1 (0.73 mm2) | ? @ (59.9, 58.9) |
| error | check_silk / silk_over_pad | silk "hide" on F.SilkS covers pad ?.1 (0.75 mm2) | ? @ (63.1, 58.8) |
| error | check_silk / silk_over_pad | silk "hide" on F.SilkS covers pad ?.1 (0.81 mm2) | ? @ (61.5, 58.8) |
| error | check_silk / silk_over_pad | silk rect on F.SilkS covers pad ?.1 (1.20 mm2) | ? @ (58.8, 60.7) |
| error | check_silk / silk_over_pad | silk rect on F.SilkS covers pad ?.2 (1.20 mm2) | ? @ (58.8, 62.0) |
| error | check_silk / silk_over_pad | silk rect on F.SilkS covers pad ?.3 (1.20 mm2) | ? @ (58.8, 63.2) |
| error | check_silk / silk_over_pad | silk rect on F.SilkS covers pad ?.4 (1.20 mm2) | ? @ (58.8, 64.5) |
| error | check_silk / silk_over_pad | silk rect on F.SilkS covers pad ?.5 (1.20 mm2) | ? @ (64.0, 64.5) |
| error | check_silk / silk_over_pad | silk rect on F.SilkS covers pad ?.6 (1.20 mm2) | ? @ (64.0, 63.2) |
| error | check_silk / silk_over_pad | silk rect on F.SilkS covers pad ?.7 (1.20 mm2) | ? @ (64.0, 62.0) |

59 more in `runs/atx12vo-5vsb-adapter/reports/`.

### led-driver-9w

https://github.com/RandomDelta6/9w_LED_Driver_PCB at `e03c52eb1c99`, `9W LED driver.kicad_pcb`, CC-BY-SA-4.0, power, 2 layers.

verify_all checks: check_creepage skipped, check_current skipped, check_decoupling skipped, check_diffpair pass, check_mating pass, check_pdn skipped, check_ratings skipped, check_return_path skipped, check_route_style violations, check_silk violations, check_thermal skipped

| severity | check | finding | where |
|---|---|---|---|
| error | check.dfm / dfm_silk_over_pad | silkscreen printed over a solder-mask opening (0.1069 mm2) on F.Silkscreen - pad of ? | ? @ (68.4, 52.3) |
| warning | check_silk / silk_illegible | silk text "github.com/RandomDelta6" is 0.50 mm tall (< 0.8 mm min legible height) | @ (88.3, 52.9) |
| warning | check_silk / silk_illegible | silk text "SIC9752_22082022_REV.002" is 0.75 mm tall (< 0.8 mm min legible height) | @ (89.4, 51.8) |
| warning | check_route_style / route_style | 1 needless jog(s): a sidestep smaller than the track clears nothing on +ve_output F.Cu | +ve_output @ (95.0, 55.1) |
| warning | check_route_style / route_style | 2 needless jog(s): a sidestep smaller than the track clears nothing on Net-(D2-K) F.Cu | Net-(D2-K) @ (94.0, 69.3) |
| warning | check.dfm / dfm_silk_width | 547 silk strokes below JLC minimum width 0.15 mm (narrowest 0.1000 mm) on F.Silkscreen | @ (83.6, 53.0) |
| warning | check.dfm / dfm_silk_width | 340 silk strokes below JLC minimum width 0.15 mm (narrowest 0.1200 mm) on B.Silkscreen | @ (53.2, 61.9) |

### bratwurst-power

https://github.com/Qeteshpony/BratwurstPower at `0db7d3d3a7f7`, `pcb/BratwurstPower.kicad_pcb`, BSD-2-Clause, power, 4 layers.

verify_all checks: check_creepage skipped, check_current skipped, check_decoupling skipped, check_diffpair error, check_mating violations, check_pdn skipped, check_ratings skipped, check_return_path skipped, check_route_style violations, check_silk violations, check_thermal skipped

| severity | check | finding | where |
|---|---|---|---|
| error | check_silk / silk_over_pad | silk "Raspi EN -> IO1" on B.SilkS covers pad JP4.1 (0.09 mm2) | JP4 @ (143.2, 109.8) |
| error | check_silk / silk_over_pad | silk "Raspi EN -> IO1" on B.SilkS covers pad JP4.2 (0.09 mm2) | JP4 @ (141.8, 109.8) |
| error | check_silk / silk_over_pad | silk "EXT EN" on B.SilkS covers pad JP3.1 (0.09 mm2) | JP3 @ (149.8, 101.2) |
| error | check_silk / silk_over_pad | silk "EXT EN" on B.SilkS covers pad JP3.2 (0.09 mm2) | JP3 @ (149.8, 102.6) |
| error | check_silk / silk_over_pad | silk "3V3 IO1 IO2 IO3 IO4 GND" on B.SilkS covers pad J10.3 (1.14 mm2) | J10 @ (154.5, 106.2) |
| error | check_silk / silk_over_pad | silk "3V3 IO1 IO2 IO3 IO4 GND" on B.SilkS covers pad J10.4 (1.14 mm2) | J10 @ (157.0, 106.2) |
| error | check_silk / silk_over_pad | silk "TP1" on B.SilkS covers pad TP1.1 (0.52 mm2) | TP1 @ (142.2, 125.0) |
| error | check_silk / silk_over_pad | silk "3V3 SDA SCL GND" on B.SilkS covers pad TP4.1 (0.67 mm2) | TP4 @ (138.8, 91.8) |
| error | check_silk / silk_over_pad | silk "3V3 SDA SCL GND" on B.SilkS covers pad J5.2 (1.40 mm2) | J5 @ (140.8, 86.7) |
| error | check_silk / silk_over_pad | silk "3V3 SDA SCL GND" on B.SilkS covers pad J5.3 (1.40 mm2) | J5 @ (138.8, 86.7) |
| error | check_silk / silk_over_pad | silk "USB2 EN" on B.SilkS covers pad JP2.1 (0.09 mm2) | JP2 @ (181.2, 120.5) |
| error | check_silk / silk_over_pad | silk "USB2 EN" on B.SilkS covers pad JP2.2 (0.09 mm2) | JP2 @ (179.8, 120.5) |
| error | check_silk / silk_over_pad | silk "G G D+ D- VB" on B.SilkS covers pad J11.3 (0.91 mm2) | J11 @ (132.5, 124.8) |
| error | check_silk / silk_over_pad | silk "USB1 In" on B.SilkS covers pad J3.S1 (0.97 mm2) | J3 @ (210.1, 120.8) |
| error | check_silk / silk_over_pad | silk "USB1 In" on B.SilkS covers pad J3.S1 (0.97 mm2) | J3 @ (210.1, 112.2) |
| error | check_silk / silk_over_pad | silk "3V3 SDA SCL GND" on B.SilkS covers pad J6.2 (1.40 mm2) | J6 @ (151.8, 86.7) |
| error | check_silk / silk_over_pad | silk "3V3 SDA SCL GND" on B.SilkS covers pad J6.3 (1.40 mm2) | J6 @ (149.8, 86.7) |
| error | check_silk / silk_over_pad | silk "OTG" on B.SilkS covers pad J11.MP (1.66 mm2) | J11 @ (128.6, 121.5) |
| error | check_silk / silk_over_pad | silk "USB2 In" on B.SilkS covers pad J7.S1 (0.97 mm2) | J7 @ (210.1, 133.8) |
| error | check_silk / silk_over_pad | silk "USB2 In" on B.SilkS covers pad J7.S1 (0.97 mm2) | J7 @ (210.1, 125.2) |
| error | check_silk / silk_over_pad | silk "${VERSION} ${DATE}" on F.SilkS covers pad R44.1 (0.33 mm2) | R44 @ (203.0, 117.8) |
| error | check_silk / silk_over_pad | silk "${VERSION} ${DATE}" on F.SilkS covers pad R44.2 (0.33 mm2) | R44 @ (202.0, 117.8) |
| error | check_silk / silk_over_pad | silk "+     -" on F.SilkS covers pad J9.1 (2.61 mm2) | J9 @ (136.9, 97.2) |
| error | check_silk / silk_over_pad | silk "+     -" on F.SilkS covers pad J9.2 (2.30 mm2) | J9 @ (136.9, 99.8) |
| error | check_silk / silk_over_pad | silk "Bratwurst Power" on F.SilkS covers pad RV3.1 (0.80 mm2) | RV3 @ (183.0, 111.2) |

916 more in `runs/bratwurst-power/reports/`.

### xt30-power-module

https://github.com/stephendade/XT30PowerModule at `757916f6520f`, `XT30PowerV2.kicad_pcb`, CERN-OHL-W-2.0, power, 2 layers.

verify_all checks: check_creepage skipped, check_current skipped, check_decoupling skipped, check_diffpair pass, check_mating pass, check_pdn skipped, check_ratings skipped, check_return_path skipped, check_route_style violations, check_silk violations, check_thermal skipped

| severity | check | finding | where |
|---|---|---|---|
| error | check.dfm / dfm_hole_to_hole | hole-to-hole 0.4500 mm below JLC minimum 0.5 mm | @ (107.0, 131.7) |
| warning | check_silk / silk_thin | silk text "XT30PowerV2 June 2026 Stephen Dade" stroke 0.100 mm (< 0.12 mm min) | @ (119.1, 139.5) |
| warning | check_silk / silk_thin | silk text "5V Out" stroke 0.100 mm (< 0.12 mm min) | @ (93.0, 125.8) |
| warning | check_silk / silk_thin | silk text "I2C Batt monitor" stroke 0.100 mm (< 0.12 mm min) | @ (98.5, 124.0) |
| warning | check_silk / silk_thin | silk text "Battery In" stroke 0.100 mm (< 0.12 mm min) | @ (89.2, 138.8) |
| warning | check_silk / silk_thin | silk text "Power Out" stroke 0.100 mm (< 0.12 mm min) | @ (116.0, 138.8) |
| warning | check_route_style / route_style | 1 needless jog(s): a sidestep smaller than the track clears nothing on /V_sw F.Cu | /V_sw @ (113.8, 126.4) |
| warning | check.dfm / dfm_silk_width | 330 silk strokes below JLC minimum width 0.15 mm (narrowest 0.1000 mm) on F.Silkscreen | @ (98.2, 126.2) |
| warning | check.dfm / dfm_silk_width | 363 silk strokes below JLC minimum width 0.15 mm (narrowest 0.1000 mm) on B.Silkscreen | @ (118.6, 135.7) |

### soleil-power

https://github.com/protolux-electronics/soleil_hardware at `8c7c922c1e52`, `soleil.kicad_pcb`, CERN-OHL-P-2.0, power, 4 layers.

verify_all checks: check_creepage skipped, check_current skipped, check_decoupling skipped, check_diffpair pass, check_mating violations, check_pdn skipped, check_ratings skipped, check_return_path skipped, check_route_style violations, check_silk pass, check_thermal skipped

| severity | check | finding | where |
|---|---|---|---|
| error | check_mating / mating_zone_blocked | J1 (wire_to_board_side): J3 sit in the plug's insertion zone in front of its mouth (12.0 mm plug + 3.0 mm grip) | J1, J3 @ (157.0, 112.9) |
| error | check.dfm / dfm_copper_to_edge | copper 0.1100 mm from board edge, JLC minimum 0.3 mm on F.Cu | @ (154.3, 90.8) |
| error | check.dfm / dfm_copper_to_edge | copper 0.1100 mm from board edge, JLC minimum 0.3 mm on F.Cu | @ (125.0, 78.0) |
| error | check.dfm / dfm_copper_to_edge | copper 0.1100 mm from board edge, JLC minimum 0.3 mm on F.Cu | @ (133.5, 75.9) |
| error | check.dfm / dfm_copper_to_edge | copper 0.1100 mm from board edge, JLC minimum 0.3 mm on F.Cu | @ (136.0, 75.9) |
| error | check.dfm / dfm_copper_to_edge | copper 0.1100 mm from board edge, JLC minimum 0.3 mm on F.Cu | @ (138.6, 75.9) |
| error | check.dfm / dfm_copper_to_edge | copper 0.1000 mm from board edge, JLC minimum 0.3 mm on F.Cu | @ (141.2, 103.2) |
| error | check.dfm / dfm_copper_to_edge | copper 0.1100 mm from board edge, JLC minimum 0.3 mm on F.Cu | @ (143.7, 75.9) |
| error | check.dfm / dfm_copper_to_edge | copper 0.1100 mm from board edge, JLC minimum 0.3 mm on F.Cu | @ (153.8, 75.9) |
| error | check.dfm / dfm_copper_to_edge | copper 0.1100 mm from board edge, JLC minimum 0.3 mm on F.Cu | @ (146.2, 75.9) |
| error | check.dfm / dfm_copper_to_edge | copper 0.1100 mm from board edge, JLC minimum 0.3 mm on F.Cu | @ (151.3, 75.9) |
| error | check.dfm / dfm_copper_to_edge | copper 0.1000 mm from board edge, JLC minimum 0.3 mm on F.Cu | @ (147.8, 103.2) |
| error | check.dfm / dfm_copper_to_edge | copper 0.1000 mm from board edge, JLC minimum 0.3 mm on F.Cu | @ (153.7, 103.2) |
| error | check.dfm / dfm_copper_to_edge | copper 0.1100 mm from board edge, JLC minimum 0.3 mm on F.Cu | @ (158.9, 75.9) |
| error | check.dfm / dfm_copper_to_edge | copper 0.1100 mm from board edge, JLC minimum 0.3 mm on F.Cu | @ (156.3, 75.9) |
| error | check.dfm / dfm_copper_to_edge | copper 0.1100 mm from board edge, JLC minimum 0.3 mm on F.Cu | @ (164.0, 75.9) |
| error | check.dfm / dfm_copper_to_edge | copper 0.1000 mm from board edge, JLC minimum 0.3 mm on F.Cu | @ (160.3, 103.2) |
| error | check.dfm / dfm_copper_to_edge | copper 0.1100 mm from board edge, JLC minimum 0.3 mm on F.Cu | @ (171.6, 75.9) |
| error | check.dfm / dfm_copper_to_edge | copper 0.1100 mm from board edge, JLC minimum 0.3 mm on F.Cu | @ (169.1, 75.9) |
| error | check.dfm / dfm_copper_to_edge | copper 0.1100 mm from board edge, JLC minimum 0.3 mm on F.Cu | @ (174.1, 75.9) |
| error | check.dfm / dfm_copper_to_edge | copper 0.1000 mm from board edge, JLC minimum 0.3 mm on F.Cu | @ (181.5, 86.6) |
| error | check.dfm / dfm_copper_to_edge | copper 0.1000 mm from board edge, JLC minimum 0.3 mm on F.Cu | @ (181.5, 92.2) |
| error | check.dfm / dfm_hole_to_hole | hole-to-hole 0.4500 mm below JLC minimum 0.5 mm | @ (122.0, 97.4) |
| error | check.dfm / dfm_hole_to_hole | hole-to-hole 0.4500 mm below JLC minimum 0.5 mm | @ (126.9, 80.5) |
| error | check.dfm / dfm_hole_to_hole | hole-to-hole 0.4500 mm below JLC minimum 0.5 mm | @ (126.9, 81.2) |

32 more in `runs/soleil-power/reports/`.

### type-c-recessed

https://github.com/Jana-Marie/type-c-recessed at `1a46db05b3a6`, `hardware files/type-c_recessed.kicad_pcb`, CERN-OHL-S-2.0, power, 2 layers.

verify_all checks: check_creepage skipped, check_current skipped, check_decoupling skipped, check_diffpair pass, check_mating pass, check_pdn skipped, check_ratings skipped, check_return_path skipped, check_route_style pass, check_silk violations, check_thermal skipped

| severity | check | finding | where |
|---|---|---|---|
| error | check.dfm / dfm_copper_to_edge | copper 0.2000 mm from board edge, JLC minimum 0.3 mm on F.Cu | @ (50.6, 50.0) |
| error | check.dfm / dfm_copper_to_edge | copper 0.0000 mm from board edge, JLC minimum 0.3 mm on F.Cu | @ (53.7, 50.0) |
| error | check.dfm / dfm_copper_to_edge | copper 0.0000 mm from board edge, JLC minimum 0.3 mm on B.Cu | @ (54.4, 50.0) |
| error | check.dfm / dfm_copper_to_edge | copper 0.0000 mm from board edge, JLC minimum 0.3 mm on B.Cu | @ (52.4, 50.0) |
| error | check.dfm / dfm_hole_to_hole | hole-to-hole 0.3500 mm below JLC minimum 0.5 mm | @ (53.8, 49.5) |
| error | check.dfm / dfm_hole_to_hole | hole-to-hole 0.3500 mm below JLC minimum 0.5 mm | @ (54.8, 49.5) |
| error | check.dfm / dfm_hole_to_edge | hole 0.4000 mm from board edge, JLC minimum 0.5 mm | @ (50.6, 50.0) |
| error | check.dfm / pad_net_mismatch | J1 pad nets disagree with the schematic (pad 3: board 'Net-(J1-Pad3)' vs schematic 'Net-(J1-CC1)', pad 4: board 'Net-(J1-Pad4)' vs schematic | J1 @ (56.2, 49.4) |
| error | check.dfm / pad_net_mismatch | R1 pad nets disagree with the schematic (pad 1: board 'Net-(J1-Pad3)' vs schematic 'Net-(J1-CC1)') | R1 @ (58.2, 48.0) |
| error | check.dfm / pad_net_mismatch | R2 pad nets disagree with the schematic (pad 2: board 'Net-(J1-Pad4)' vs schematic 'Net-(J1-CC2)') | R2 @ (58.2, 52.0) |
| warning | check_silk / silk_illegible | silk text "JMH" is 0.70 mm tall (< 0.8 mm min legible height) | @ (58.4, 50.0) |
| warning | check_silk / silk_illegible | silk text "C1" is 0.45 mm tall (< 0.8 mm min legible height) | @ (53.7, 46.8) |
| warning | check.dfm / dfm_silk_width | 19 silk strokes below JLC minimum width 0.15 mm (narrowest 0.1000 mm) on F.Silkscreen | @ (58.2, 50.7) |
| warning | check.dfm / dfm_silk_over_pad | silkscreen printed over a solder-mask opening (0.0140 mm2) on F.Silkscreen (sliver; fab auto-clips silk at mask openings) | @ (58.1, 51.9) |
| warning | check.dfm / dfm_silk_over_pad | silkscreen printed over a solder-mask opening (0.0140 mm2) on F.Silkscreen (sliver; fab auto-clips silk at mask openings) | @ (58.3, 52.1) |
| warning | check.dfm / dfm_silk_width | 21 silk strokes below JLC minimum width 0.15 mm (narrowest 0.1000 mm) on B.Silkscreen | @ (53.9, 46.7) |
| warning | check.dfm / dfm_mask_dam | 1 solder-mask dams below 0.1 mm (narrowest 0.0422 mm) on F.Mask | @ (58.5, 51.6) |

### libresolar-bms-c1

https://github.com/LibreSolar/bms-c1 at `0ca09706f499`, `kicad/bms-c1.kicad_pcb`, CERN-OHL-W-2.0, power, 4 layers.

verify_all checks: check_creepage skipped, check_current skipped, check_decoupling skipped, check_diffpair violations, check_mating pass, check_pdn skipped, check_ratings skipped, check_return_path skipped, check_route_style violations, check_silk violations, check_thermal skipped

| severity | check | finding | where |
|---|---|---|---|
| error | check_diffpair / diffpair_skew | diff pair /BAT+//BAT- length skew 89.39 mm (~632 ps, eps_r 4.5); limit 5.0 mm | /BAT+ @ (204.1, 100.8) |
| error | check_diffpair / diffpair_skew | diff pair /C1+//C1- length skew 12.33 mm (~87 ps, eps_r 4.5); limit 5.0 mm | /C1+ @ (196.1, 71.5) |
| error | check_diffpair / diffpair_skew | diff pair /PACK+//PACK- length skew 54.77 mm (~388 ps, eps_r 4.5); limit 5.0 mm | /PACK+ @ (155.0, 74.6) |
| error | check_diffpair / diffpair_uncoupled | diff pair /PACK+//PACK- has 12.36 mm of /PACK+ running uncoupled (> 43.23 mm from its partner); limit 5.0 mm | /PACK+ @ (155.0, 74.6) |
| error | check.dfm / dfm_clearance | copper clearance 0.0547 mm below JLC minimum 0.1016 mm on F.Cu | @ (171.4, 105.0) |
| error | check.dfm / dfm_clearance | copper clearance 0.0880 mm below JLC minimum 0.1016 mm on F.Cu | @ (175.2, 105.1) |
| error | check.dfm / dfm_clearance | copper clearance 0.0500 mm below JLC minimum 0.1016 mm on B.Cu | @ (145.4, 99.0) |
| error | check.dfm / pad_net_mismatch | J3 pad nets disagree with the schematic (pad A4: board 'Net-(J3-VBUS-PadA4)' vs schematic 'unconnected-(J3-VBUS-PadA4)', pad A9: board 'Net- | J3 @ (154.7, 107.7) |
| warning | check_diffpair / diffpair_open_trunk | diff pair /BAT+//BAT-: /BAT+ trunk is open - cannot connect terminal(s) C34.1, C39.1, D12.1, J1.12; its length 120.61 mm is total copper len | /BAT+ @ (204.1, 100.8) |
| warning | check_diffpair / diffpair_open_trunk | diff pair /BAT+//BAT-: /BAT- trunk is open - cannot connect terminal(s) C39.2, C48.2, D12.2, J1.3; its length 31.23 mm is total copper lengt | /BAT- @ (203.2, 73.8) |
| warning | check_diffpair / diffpair_via_asymmetry | diff pair /BAT+//BAT- via count asymmetric: /BAT+ has 158, /BAT- has 94 | /BAT+ @ (204.1, 100.8) |
| warning | check_diffpair / diffpair_open_trunk | diff pair /C1+//C1-: /C1+ trunk is open - cannot connect terminal(s) J1.4; its length 23.44 mm is total copper length, so the reported skew  | /C1+ @ (196.1, 71.5) |
| warning | check_diffpair / diffpair_open_trunk | diff pair /C1+//C1-: /C1- trunk is open - cannot connect terminal(s) J1.15; its length 11.12 mm is total copper length, so the reported skew | /C1- @ (199.9, 73.2) |
| warning | check_diffpair / diffpair_open_trunk | diff pair /PACK+//PACK-: /PACK+ trunk is open - cannot connect terminal(s) D22.1; its length 60.89 mm is total copper length, so the reporte | /PACK+ @ (155.0, 74.6) |
| warning | check_diffpair / diffpair_open_trunk | diff pair /PACK+//PACK-: /PACK- trunk is open - cannot connect terminal(s) D22.2; its length 6.12 mm is total copper length, so the reported | /PACK- @ (155.3, 64.3) |
| warning | check_diffpair / diffpair_via_asymmetry | diff pair /PACK+//PACK- via count asymmetric: /PACK+ has 161, /PACK- has 91 | /PACK+ @ (155.0, 74.6) |
| warning | check_silk / silk_misattributed | refdes "R39" sits 1.67 mm beyond its own pads and 0.92 mm from P5 - reads as P5's label; scripted fix: place_edit.py move_text | R39 @ (83.5, 90.0) |
| warning | check_silk / silk_misattributed | refdes "R30" sits 2.00 mm beyond its own pads and 0.43 mm from TP6 - reads as TP6's label; scripted fix: place_edit.py move_text | R30 @ (160.2, 88.4) |
| warning | check_silk / silk_misattributed | refdes "C19" sits 2.22 mm beyond its own pads and 0.47 mm from C46 - reads as C46's label; scripted fix: place_edit.py move_text | C19 @ (181.1, 108.4) |
| warning | check_silk / silk_misattributed | refdes "R43" sits 1.67 mm beyond its own pads and 0.17 mm from R39 - reads as R39's label; scripted fix: place_edit.py move_text | R43 @ (85.0, 90.0) |
| warning | check_route_style / route_style | 1 needless jog(s): a sidestep smaller than the track clears nothing on /BQ76952/CP1 F.Cu | /BQ76952/CP1 @ (167.7, 84.7) |
| warning | check_route_style / route_style | 1 needless jog(s): a sidestep smaller than the track clears nothing on /BQ76952/VC2 F.Cu | /BQ76952/VC2 @ (176.9, 69.5) |
| warning | check_route_style / route_style | 1 needless jog(s): a sidestep smaller than the track clears nothing on /BQ76952/VC3 F.Cu | /BQ76952/VC3 @ (177.2, 71.6) |
| warning | check_route_style / route_style | 1 needless jog(s): a sidestep smaller than the track clears nothing on /C15+ F.Cu | /C15+ @ (195.0, 97.3) |
| warning | check_route_style / route_style | 1 needless jog(s): a sidestep smaller than the track clears nothing on /ESP32-C3 MCU/RS485_DE B.Cu | /ESP32-C3 MCU/RS485_DE @ (165.9, 105.6) |

3 more in `runs/libresolar-bms-c1/reports/`.

### placebo-stm32g0

https://github.com/dotcypress/placebo at `c5da1b37fa3a`, `placebo.kicad_pcb`, Apache-2.0, mcu-usb, 2 layers.

verify_all checks: check_creepage skipped, check_current skipped, check_decoupling skipped, check_diffpair pass, check_mating pass, check_pdn skipped, check_ratings skipped, check_return_path skipped, check_route_style violations, check_silk violations, check_thermal skipped

| severity | check | finding | where |
|---|---|---|---|
| error | check_silk / silk_over_pad | silk "hide" on F.SilkS covers pad ?.1 (1.45 mm2) | ? @ (66.7, 83.3) |
| error | check_silk / silk_over_pad | silk "hide" on F.SilkS covers pad ?.2 (1.01 mm2) | ? @ (66.7, 85.9) |
| error | check_silk / silk_over_pad | silk "hide" on F.SilkS covers pad ?. (0.77 mm2) | ? @ (71.7, 84.6) |
| error | check_silk / silk_over_pad | silk "hide" on F.SilkS covers pad ?.1 (0.84 mm2) | ? @ (66.7, 83.3) |
| error | check_silk / silk_over_pad | silk "hide" on F.SilkS covers pad ?. (0.77 mm2) | ? @ (71.7, 84.6) |
| error | check_silk / silk_over_pad | silk "hide" on F.SilkS covers pad ?.2 (0.32 mm2) | ? @ (73.0, 83.9) |
| error | check_silk / silk_over_pad | silk "hide" on F.SilkS covers pad ?. (0.77 mm2) | ? @ (76.8, 85.6) |
| error | check_silk / silk_over_pad | silk "hide" on F.SilkS covers pad ?.2 (0.42 mm2) | ? @ (69.3, 107.9) |
| error | check.dfm / dfm_open_outline | Edge.Cuts present but does not form a closed outline - copper/hole edge-distance checks cannot run |  |
| error | check.dfm / dfm_clearance | copper clearance 0.1102 mm below JLC minimum 0.127 mm on F.Cu | @ (76.5, 104.7) |
| warning | check_silk / silk_illegible | silk text "Placebo Proto Board rev. 0x9" is 0.75 mm tall (< 0.8 mm min legible height) | @ (80.2, 97.6) |
| warning | check_silk / silk_illegible | silk text "vitaly.codes/placebo" is 0.65 mm tall (< 0.8 mm min legible height) | @ (74.2, 101.0) |
| warning | check_silk / silk_illegible | silk text "C4" is 0.60 mm tall (< 0.8 mm min legible height) | @ (69.1, 96.2) |
| warning | check_silk / silk_illegible | silk text "C1" is 0.60 mm tall (< 0.8 mm min legible height) | @ (79.8, 101.5) |
| warning | check_silk / silk_illegible | silk text "C5" is 0.60 mm tall (< 0.8 mm min legible height) | @ (79.5, 90.3) |
| warning | check_silk / silk_illegible | silk text "R4" is 0.60 mm tall (< 0.8 mm min legible height) | @ (77.6, 103.9) |
| warning | check_silk / silk_illegible | silk text "hide" is 0.70 mm tall (< 0.8 mm min legible height) | @ (78.2, 84.7) |
| warning | check_silk / silk_illegible | silk text "R2" is 0.60 mm tall (< 0.8 mm min legible height) | @ (71.3, 103.8) |
| warning | check_silk / silk_illegible | silk text "C2" is 0.60 mm tall (< 0.8 mm min legible height) | @ (68.8, 101.5) |
| warning | check_silk / silk_illegible | silk text "R1" is 0.60 mm tall (< 0.8 mm min legible height) | @ (72.1, 90.4) |
| warning | check_silk / silk_illegible | silk text "C3" is 0.60 mm tall (< 0.8 mm min legible height) | @ (70.6, 90.3) |
| warning | check_silk / silk_illegible | silk text "R3" is 0.60 mm tall (< 0.8 mm min legible height) | @ (74.4, 103.9) |
| warning | check_silk / silk_illegible | silk text "hide" is 0.60 mm tall (< 0.8 mm min legible height) | @ (69.3, 106.7) |
| warning | check_silk / silk_illegible | silk text "hide" is 0.00 mm tall (< 0.8 mm min legible height) | @ (74.1, 102.7) |
| warning | check_silk / silk_illegible | silk text "hide" is 0.00 mm tall (< 0.8 mm min legible height) | @ (74.1, 110.7) |

29 more in `runs/placebo-stm32g0/reports/`.

### atsamd20-breakout

https://github.com/elevendroids/atsamd20-breakout at `923de8305832`, `atsamd20-breakout.kicad_pcb`, CC-BY-SA-4.0, mcu-usb, 2 layers.

verify_all checks: check_creepage skipped, check_current skipped, check_decoupling skipped, check_diffpair pass, check_mating pass, check_pdn skipped, check_ratings skipped, check_return_path skipped, check_route_style pass, check_silk violations, check_thermal skipped

| severity | check | finding | where |
|---|---|---|---|
| error | check_silk / silk_over_pad | silk "PA03" on F.SilkS covers pad ?.5 (2.07 mm2) | ? @ (127.0, 96.5) |
| error | check_silk / silk_over_pad | silk "PA11" on F.SilkS covers pad ?.13 (2.07 mm2) | ? @ (127.0, 116.8) |
| error | check_silk / silk_over_pad | silk "PA10" on F.SilkS covers pad ?.12 (2.07 mm2) | ? @ (127.0, 114.3) |
| error | check_silk / silk_over_pad | silk "PA09" on F.SilkS covers pad ?.11 (2.07 mm2) | ? @ (127.0, 111.8) |
| error | check_silk / silk_over_pad | silk "LED" on F.SilkS covers pad ?.15 (1.60 mm2) | ? @ (127.0, 121.9) |
| error | check_silk / silk_over_pad | silk "GND" on F.SilkS covers pad ?.16 (1.60 mm2) | ? @ (127.0, 124.5) |
| error | check_silk / silk_over_pad | silk "PA02" on F.SilkS covers pad ?.4 (2.07 mm2) | ? @ (127.0, 94.0) |
| error | check_silk / silk_over_pad | silk "PA01" on F.SilkS covers pad ?.3 (2.07 mm2) | ? @ (127.0, 91.4) |
| error | check_silk / silk_over_pad | silk "PA00" on F.SilkS covers pad ?.2 (2.07 mm2) | ? @ (127.0, 88.9) |
| error | check_silk / silk_over_pad | silk "PA08" on F.SilkS covers pad ?.10 (2.07 mm2) | ? @ (127.0, 109.2) |
| error | check_silk / silk_over_pad | silk "PA07" on F.SilkS covers pad ?.9 (2.07 mm2) | ? @ (127.0, 106.7) |
| error | check_silk / silk_over_pad | silk "PA06" on F.SilkS covers pad ?.8 (2.07 mm2) | ? @ (127.0, 104.1) |
| error | check_silk / silk_over_pad | silk "PA05" on F.SilkS covers pad ?.7 (2.07 mm2) | ? @ (127.0, 101.6) |
| error | check_silk / silk_over_pad | silk "PA04" on F.SilkS covers pad ?.6 (2.07 mm2) | ? @ (127.0, 99.1) |
| error | check_silk / silk_over_pad | silk "VDD" on F.SilkS covers pad ?.1 (1.77 mm2) | ? @ (147.3, 124.5) |
| error | check_silk / silk_over_pad | silk "PA14" on F.SilkS covers pad ?.14 (2.07 mm2) | ? @ (127.0, 119.4) |
| error | check_silk / silk_over_pad | silk "PA15" on F.SilkS covers pad ?.2 (2.07 mm2) | ? @ (147.3, 121.9) |
| error | check_silk / silk_over_pad | silk "PA18" on F.SilkS covers pad ?.5 (2.07 mm2) | ? @ (147.3, 114.3) |
| error | check_silk / silk_over_pad | silk "PA16" on F.SilkS covers pad ?.3 (2.07 mm2) | ? @ (147.3, 119.4) |
| error | check_silk / silk_over_pad | silk "~{RESET}" on F.SilkS covers pad ?.13 (2.10 mm2) | ? @ (147.3, 94.0) |
| error | check_silk / silk_over_pad | silk "PA19" on F.SilkS covers pad ?.6 (2.07 mm2) | ? @ (147.3, 111.8) |
| error | check_silk / silk_over_pad | silk "PA22" on F.SilkS covers pad ?.7 (2.07 mm2) | ? @ (147.3, 109.2) |
| error | check_silk / silk_over_pad | silk "PA23" on F.SilkS covers pad ?.8 (2.07 mm2) | ? @ (147.3, 106.7) |
| error | check_silk / silk_over_pad | silk "PA24" on F.SilkS covers pad ?.9 (2.07 mm2) | ? @ (147.3, 104.1) |
| error | check_silk / silk_over_pad | silk "PA25" on F.SilkS covers pad ?.10 (2.07 mm2) | ? @ (147.3, 101.6) |

17 more in `runs/atsamd20-breakout/reports/`.

### samd21e-breakout

https://github.com/mitsake/samd21e-breakout at `d1896ddeb5ca`, `hardware/samd21e_breakout.kicad_pcb`, CC-BY-SA-4.0, mcu-usb, 2 layers.

verify_all checks: check_creepage skipped, check_current skipped, check_decoupling skipped, check_diffpair pass, check_mating pass, check_pdn skipped, check_ratings skipped, check_return_path skipped, check_route_style pass, check_silk violations, check_thermal skipped

| severity | check | finding | where |
|---|---|---|---|
| error | check_silk / silk_over_pad | silk "hide" on F.SilkS covers pad ?.1 (0.77 mm2) | ? @ (41.8, 31.1) |
| error | check_silk / silk_over_pad | silk "hide" on F.SilkS covers pad ?.2 (0.77 mm2) | ? @ (42.9, 32.2) |
| error | check_silk / silk_over_pad | silk "hide" on F.SilkS covers pad ?.1 (0.79 mm2) | ? @ (41.2, 26.8) |
| error | check_silk / silk_over_pad | silk "hide" on F.SilkS covers pad ?.2 (0.79 mm2) | ? @ (40.6, 26.2) |
| error | check_silk / silk_over_pad | silk "hide" on F.SilkS covers pad ?.1 (0.79 mm2) | ? @ (40.5, 32.4) |
| error | check_silk / silk_over_pad | silk "hide" on F.SilkS covers pad ?.1 (0.77 mm2) | ? @ (41.8, 31.1) |
| error | check_silk / silk_over_pad | silk "hide" on F.SilkS covers pad ?.9 (0.57 mm2) | ? @ (35.2, 22.8) |
| error | check_silk / silk_over_pad | silk "hide" on F.SilkS covers pad ?.10 (0.57 mm2) | ? @ (34.6, 23.4) |
| error | check_silk / silk_over_pad | silk "hide" on F.SilkS covers pad ?.11 (0.57 mm2) | ? @ (34.0, 23.9) |
| error | check_silk / silk_over_pad | silk "hide" on F.SilkS covers pad ?.12 (0.57 mm2) | ? @ (33.5, 24.5) |
| error | check_silk / silk_over_pad | silk "hide" on F.SilkS covers pad ?.1 (0.39 mm2) | ? @ (26.3, 26.7) |
| error | check_silk / silk_over_pad | silk "hide" on F.SilkS covers pad ?.2 (0.39 mm2) | ? @ (25.4, 26.7) |
| error | check_silk / silk_over_pad | silk "hide" on F.SilkS covers pad ?.3 (0.39 mm2) | ? @ (24.4, 26.7) |
| error | check_silk / silk_over_pad | silk "hide" on F.SilkS covers pad ?.4 (0.39 mm2) | ? @ (24.4, 28.9) |
| error | check_silk / silk_over_pad | silk "hide" on F.SilkS covers pad ?.5 (0.39 mm2) | ? @ (26.3, 28.9) |
| error | check_silk / silk_over_pad | silk "hide" on F.SilkS covers pad ?.2 (1.08 mm2) | ? @ (47.6, 25.7) |
| error | check.dfm / dfm_hole_size | drill 0.2540 mm below JLC minimum 0.3 mm | @ (22.4, 29.4) |
| error | check.dfm / dfm_hole_size | drill 0.2540 mm below JLC minimum 0.3 mm | @ (22.5, 27.3) |
| error | check.dfm / dfm_hole_size | drill 0.2540 mm below JLC minimum 0.3 mm | @ (22.5, 28.2) |
| error | check.dfm / dfm_hole_size | drill 0.2540 mm below JLC minimum 0.3 mm | @ (25.4, 25.6) |
| error | check.dfm / dfm_hole_size | drill 0.2540 mm below JLC minimum 0.3 mm | @ (27.1, 28.9) |
| error | check.dfm / dfm_hole_size | drill 0.2540 mm below JLC minimum 0.3 mm | @ (34.4, 25.5) |
| error | check.dfm / dfm_hole_size | drill 0.2540 mm below JLC minimum 0.3 mm | @ (35.0, 24.9) |
| error | check.dfm / dfm_hole_size | drill 0.2540 mm below JLC minimum 0.3 mm | @ (35.6, 31.2) |
| error | check.dfm / dfm_hole_size | drill 0.2540 mm below JLC minimum 0.3 mm | @ (36.1, 31.9) |

61 more in `runs/samd21e-breakout/reports/`.

### rp-micro

https://github.com/siderakb/rp-micro at `a7baf36025b9`, `hardware/rp-micro.kicad_pcb`, CERN-OHL-P-2.0, mcu-usb, 2 layers.

verify_all checks: check_creepage skipped, check_current skipped, check_decoupling skipped, check_diffpair violations, check_mating pass, check_pdn skipped, check_ratings skipped, check_return_path skipped, check_route_style violations, check_silk violations, check_thermal skipped

| severity | check | finding | where |
|---|---|---|---|
| error | check_diffpair / diffpair_skew | diff pair USB_D+/USB_D- length skew 10.83 mm (~77 ps, eps_r 4.5); limit 5.0 mm | USB_D+ @ (140.0, 65.0) |
| error | check_silk / silk_over_pad | silk "3V3" on B.SilkS covers pad ?.4 (1.21 mm2) | ? @ (147.3, 68.6) |
| error | check_silk / silk_over_pad | silk "RPMicro" on B.SilkS covers pad ?.8 (1.79 mm2) | ? @ (147.3, 78.7) |
| error | check_silk / silk_over_pad | silk "~{RST}" on B.SilkS covers pad ?.3 (1.88 mm2) | ? @ (147.3, 66.0) |
| error | check_silk / silk_over_pad | silk "GND" on B.SilkS covers pad ?.2 (0.64 mm2) | ? @ (147.3, 63.5) |
| error | check_silk / silk_over_pad | silk "hide" on F.SilkS covers pad ?.6 (0.32 mm2) | ? @ (135.8, 68.8) |
| error | check_silk / silk_over_pad | silk "hide" on F.SilkS covers pad ?.7 (0.32 mm2) | ? @ (135.0, 68.8) |
| error | check_silk / silk_over_pad | silk "hide" on F.SilkS covers pad ?.8 (0.32 mm2) | ? @ (134.2, 68.8) |
| error | check_silk / silk_over_pad | silk "hide" on F.SilkS covers pad ?.1 (0.33 mm2) | ? @ (144.4, 74.3) |
| error | check_silk / silk_over_pad | silk "hide" on F.SilkS covers pad ?.2 (0.33 mm2) | ? @ (145.4, 74.3) |
| error | check_silk / silk_over_pad | silk "hide" on F.SilkS covers pad ?.1 (0.33 mm2) | ? @ (143.5, 73.6) |
| error | check_silk / silk_over_pad | silk "hide" on F.SilkS covers pad ?.10 (2.16 mm2) | ? @ (132.1, 83.8) |
| error | check_silk / silk_over_pad | silk "hide" on F.SilkS covers pad ?.11 (2.16 mm2) | ? @ (132.1, 86.4) |
| error | check_silk / silk_over_pad | silk "BOOT" on F.SilkS covers pad ?.2 (0.65 mm2) | ? @ (134.7, 83.4) |
| error | check_silk / silk_over_pad | silk "hide" on F.SilkS covers pad ?.34 (0.15 mm2) | ? @ (143.1, 79.0) |
| error | check_silk / silk_over_pad | silk "hide" on F.SilkS covers pad ?.35 (0.15 mm2) | ? @ (143.1, 78.6) |
| error | check_silk / silk_over_pad | silk "hide" on F.SilkS covers pad ?.36 (0.15 mm2) | ? @ (143.1, 78.2) |
| error | check_silk / silk_over_pad | silk "hide" on F.SilkS covers pad ?.37 (0.15 mm2) | ? @ (143.1, 77.8) |
| error | check_silk / silk_over_pad | silk "hide" on F.SilkS covers pad ?.4 (1.83 mm2) | ? @ (147.3, 68.6) |
| error | check_silk / silk_over_pad | silk "hide" on F.SilkS covers pad ?.5 (0.83 mm2) | ? @ (147.3, 71.1) |
| error | check_silk / silk_over_pad | silk "hide" on F.SilkS covers pad ?.4 (0.32 mm2) | ? @ (136.6, 72.6) |
| error | check_silk / silk_over_pad | silk "hide" on F.SilkS covers pad ?.1 (0.33 mm2) | ? @ (143.5, 73.6) |
| error | check_silk / silk_over_pad | silk "hide" on F.SilkS covers pad ?.2 (0.33 mm2) | ? @ (143.5, 72.7) |
| error | check_silk / silk_over_pad | silk "hide" on F.SilkS covers pad ?.1 (1.31 mm2) | ? @ (143.1, 65.5) |
| error | check_silk / silk_over_pad | silk "hide" on F.SilkS covers pad ?.2 (1.31 mm2) | ? @ (143.1, 67.4) |

178 more in `runs/rp-micro/reports/`.

### usb-i2c-bridge

https://github.com/Jana-Marie/USB-I2C-BRIDGE at `a772e442bc65`, `USB-I2C-BRIDGE.kicad_pcb`, CERN-OHL-S-2.0, mcu-usb, 2 layers.

verify_all checks: check_creepage skipped, check_current skipped, check_decoupling skipped, check_diffpair violations, check_mating pass, check_pdn skipped, check_ratings skipped, check_return_path skipped, check_route_style violations, check_silk violations, check_thermal skipped

| severity | check | finding | where |
|---|---|---|---|
| error | check_silk / silk_over_pad | silk "  VIO VSENS      3.3V" on B.SilkS covers pad ?. (0.64 mm2) | ? @ (116.4, 105.1) |
| error | check_silk / silk_over_pad | silk "  VIO VSENS      3.3V" on B.SilkS covers pad ?. (0.64 mm2) | ? @ (119.3, 105.5) |
| error | check_silk / silk_over_pad | silk "USB-I2C-BRIDGE 2023 v1.0.0 @jana@mystical.garden" on B.SilkS covers pad ?. (0.33 mm2) | ? @ (105.6, 97.1) |
| error | check_silk / silk_over_pad | silk "USB I2C BRIDGE" on F.SilkS covers pad ?. (0.33 mm2) | ? @ (105.6, 102.9) |
| error | check_silk / silk_over_pad | silk "USB I2C BRIDGE" on F.SilkS covers pad ?.B1 (0.87 mm2) | ? @ (107.0, 103.2) |
| error | check_silk / silk_over_pad | silk "USB I2C BRIDGE" on F.SilkS covers pad ?.B4 (0.86 mm2) | ? @ (107.0, 102.4) |
| error | check_silk / silk_over_pad | silk "USB I2C BRIDGE" on F.SilkS covers pad ?.B9 (0.86 mm2) | ? @ (107.0, 102.4) |
| error | check_silk / silk_over_pad | silk "USB I2C BRIDGE" on F.SilkS covers pad ?.B12 (0.87 mm2) | ? @ (107.0, 103.2) |
| error | check_silk / silk_over_pad | silk "USB I2C BRIDGE" on F.SilkS covers pad ?.1 (0.30 mm2) | ? @ (108.5, 102.8) |
| error | check_silk / silk_over_pad | silk "USB I2C BRIDGE" on F.SilkS covers pad ?. (0.45 mm2) | ? @ (116.4, 105.1) |
| error | check_silk / silk_over_pad | silk "USB I2C BRIDGE" on F.SilkS covers pad ?. (0.80 mm2) | ? @ (114.4, 103.7) |
| error | check_silk / silk_over_pad | silk "Jana M 2023" on F.SilkS covers pad ?.1 (0.16 mm2) | ? @ (118.6, 95.7) |
| error | check_silk / silk_over_pad | silk "Jana M 2023" on F.SilkS covers pad ?.2 (0.20 mm2) | ? @ (118.6, 96.2) |
| error | check.dfm / dfm_copper_to_edge | copper 0.2000 mm from board edge, JLC minimum 0.3 mm on F.Cu | @ (121.6, 100.7) |
| error | check.dfm / dfm_copper_to_edge | copper 0.2000 mm from board edge, JLC minimum 0.3 mm on F.Cu | @ (116.5, 95.7) |
| error | check.dfm / dfm_copper_to_edge | copper 0.2966 mm from board edge, JLC minimum 0.3 mm on F.Cu | @ (114.1, 105.8) |
| error | check.dfm / dfm_copper_to_edge | copper 0.1206 mm from board edge, JLC minimum 0.3 mm on F.Cu | @ (122.4, 94.3) |
| error | check.dfm / dfm_copper_to_edge | copper 0.2000 mm from board edge, JLC minimum 0.3 mm on B.Cu | @ (120.4, 100.0) |
| error | check.dfm / dfm_hole_size | drill 0.2000 mm below JLC minimum 0.3 mm | @ (109.5, 97.6) |
| error | check.dfm / dfm_hole_size | drill 0.2000 mm below JLC minimum 0.3 mm | @ (110.0, 100.5) |
| error | check.dfm / dfm_hole_size | drill 0.2000 mm below JLC minimum 0.3 mm | @ (111.0, 96.0) |
| error | check.dfm / dfm_hole_size | drill 0.2000 mm below JLC minimum 0.3 mm | @ (112.5, 97.0) |
| error | check.dfm / dfm_hole_size | drill 0.2000 mm below JLC minimum 0.3 mm | @ (113.2, 94.9) |
| error | check.dfm / dfm_hole_size | drill 0.2000 mm below JLC minimum 0.3 mm | @ (113.8, 97.6) |
| error | check.dfm / dfm_hole_size | drill 0.2000 mm below JLC minimum 0.3 mm | @ (114.0, 99.8) |

101 more in `runs/usb-i2c-bridge/reports/`.

### pdk-prog

https://github.com/brainsmoke/pdk_prog at `7894067fdba0`, `pcb/pdk_prog/project.kicad_pcb`, CC-BY-4.0, mcu-usb, 2 layers.

verify_all checks: check_creepage skipped, check_current skipped, check_decoupling skipped, check_diffpair pass, check_mating pass, check_pdn skipped, check_ratings skipped, check_return_path skipped, check_route_style violations, check_silk violations, check_thermal skipped

| severity | check | finding | where |
|---|---|---|---|
| error | check_silk / silk_over_pad | silk "GND  A0  A4  A3" on F.SilkS covers pad J3.8 (1.32 mm2) | J3 @ (19.9, 8.9) |
| error | check_silk / silk_over_pad | silk "VDD  A7  A6  VPP" on F.SilkS covers pad R15.1 (0.17 mm2) | R15 @ (8.9, 8.8) |
| error | check_silk / silk_over_pad | silk "VDD  A7  A6  VPP" on F.SilkS covers pad R15.2 (0.17 mm2) | R15 @ (9.9, 8.8) |
| error | check_silk / silk_over_pad | silk "VDD  A7  A6  VPP" on F.SilkS covers pad C10.1 (0.33 mm2) | C10 @ (9.9, 9.9) |
| error | check_silk / silk_over_pad | silk "VDD  A7  A6  VPP" on F.SilkS covers pad C10.2 (0.33 mm2) | C10 @ (8.9, 9.9) |
| error | check_silk / silk_over_pad | silk "VDD  A7  A6  VPP" on F.SilkS covers pad J2.8 (1.32 mm2) | J2 @ (12.3, 8.9) |
| error | check_silk / silk_over_pad | silk "VDD  A7  A6  VPP" on B.SilkS covers pad J2.8 (1.32 mm2) | J2 @ (12.3, 8.9) |
| error | check_silk / silk_over_pad | silk "pdk_prog v0.1  https://github.com/brainsmoke/usb_proto" on B.SilkS covers pad REF**. (4.42 mm2) | REF** @ (25.0, 15.0) |
| error | check_silk / silk_over_pad | silk "pdk_prog v0.1  https://github.com/brainsmoke/usb_proto" on B.SilkS covers pad REF**. (4.42 mm2) | REF** @ (-10.0, 15.0) |
| error | check_silk / silk_over_pad | silk "GND  A0  A4  A3" on B.SilkS covers pad J3.8 (1.32 mm2) | J3 @ (19.9, 8.9) |
| error | check_silk / silk_over_pad | silk "GND" on B.SilkS covers pad J39.SWDGND (1.70 mm2) | J39 @ (4.5, -8.2) |
| error | check_silk / silk_over_pad | silk "CLK" on B.SilkS covers pad J39.SWDCLK (1.70 mm2) | J39 @ (4.5, -5.6) |
| error | check.dfm / dfm_copper_to_edge | copper 0.2005 mm from board edge, JLC minimum 0.3 mm on F.Cu | @ (7.9, -0.5) |
| error | check.dfm / dfm_copper_to_edge | copper 0.2005 mm from board edge, JLC minimum 0.3 mm on B.Cu | @ (7.2, 0.2) |
| warning | check_silk / silk_illegible | silk text "GND  A0  A4  A3" is 0.79 mm tall (< 0.8 mm min legible height) | @ (18.9, 9.5) |
| warning | check_silk / silk_illegible | silk text "VDD  A7  A6  VPP" is 0.79 mm tall (< 0.8 mm min legible height) | @ (13.5, 9.5) |
| warning | check_silk / silk_illegible | silk text "VDD  A7  A6  VPP" is 0.79 mm tall (< 0.8 mm min legible height) | @ (13.5, 9.5) |
| warning | check_silk / silk_illegible | silk text "GND  A0  A4  A3" is 0.79 mm tall (< 0.8 mm min legible height) | @ (18.9, 9.5) |
| warning | check_route_style / route_style | 2 needless jog(s): a sidestep smaller than the track clears nothing on 3V3 F.Cu | 3V3 @ (-3.1, -10.1) |
| warning | check_route_style / route_style | 1 needless jog(s): a sidestep smaller than the track clears nothing on BOOST_EN B.Cu | BOOST_EN @ (-0.6, -10.6) |
| warning | check_route_style / route_style | 1 needless jog(s): a sidestep smaller than the track clears nothing on D+ F.Cu | D+ @ (-2.5, 0.8) |
| warning | check_route_style / route_style | 1 needless jog(s): a sidestep smaller than the track clears nothing on D- F.Cu | D- @ (-2.6, -0.4) |
| warning | check_route_style / route_style | 3 needless jog(s): a sidestep smaller than the track clears nothing on GND F.Cu | GND @ (3.0, -12.5) |
| warning | check_route_style / route_style | 1 needless jog(s): a sidestep smaller than the track clears nothing on Net-(U1-PB5) F.Cu | Net-(U1-PB5) @ (10.0, -1.8) |
| warning | check_route_style / route_style | 1 needless jog(s): a sidestep smaller than the track clears nothing on PDK_A6 F.Cu | PDK_A6 @ (10.9, 6.3) |

4 more in `runs/pdk-prog/reports/`.

### rp2040-dmxsun

https://github.com/OpenLightingProject/rp2040-dmxsun at `f3b1749c982d`, `hardware/baseboard_4slots/baseboard_4slots.kicad_pcb`, Apache-2.0, mcu-usb, 2 layers.

verify_all checks: check_creepage skipped, check_current skipped, check_decoupling skipped, check_diffpair pass, check_mating pass, check_pdn skipped, check_ratings skipped, check_return_path skipped, check_route_style violations, check_silk violations, check_thermal skipped

| severity | check | finding | where |
|---|---|---|---|
| error | check_silk / silk_over_pad | silk "Pin sockets to the bottom solder this side" on F.SilkS covers pad C5.1 (0.81 mm2) | C5 @ (166.2, 83.4) |
| error | check_silk / silk_over_pad | silk "Pin sockets to the bottom solder this side" on F.SilkS covers pad C10.1 (0.81 mm2) | C10 @ (168.8, 83.4) |
| error | check_silk / silk_over_pad | silk "Pin sockets to the bottom solder this side" on F.SilkS covers pad C6.1 (0.81 mm2) | C6 @ (272.4, 83.4) |
| error | check_silk / silk_over_pad | silk "Pin sockets to the bottom solder this side" on F.SilkS covers pad C11.1 (0.80 mm2) | C11 @ (274.8, 83.4) |
| error | check_silk / silk_over_pad | silk "Pin sockets to the bottom solder this side" on F.SilkS covers pad C7.1 (0.81 mm2) | C7 @ (343.8, 83.4) |
| error | check_silk / silk_over_pad | silk "Pin sockets to the bottom solder this side" on F.SilkS covers pad C12.1 (0.81 mm2) | C12 @ (341.7, 83.4) |
| error | check_silk / silk_over_pad | silk "Mechanical stands GND connection pins to the bottom solder this side" on F.SilkS covers pad H3. (5.30 mm2) | H3 @ (374.0, 30.0) |
| error | check_silk / silk_over_pad | silk "Mechanical stands GND connection pins to the bottom solder this side" on F.SilkS covers pad H1. (5.30 mm2) | H1 @ (30.0, 30.0) |
| error | check_silk / silk_over_pad | silk "Pin sockets to the bottom solder this side" on F.SilkS covers pad C4.1 (0.81 mm2) | C4 @ (60.3, 83.4) |
| error | check_silk / silk_over_pad | silk "Pin sockets to the bottom solder this side" on F.SilkS covers pad C9.1 (0.81 mm2) | C9 @ (62.2, 83.4) |
| error | check_silk / silk_over_pad | silk "Pin sockets to the bottom solder this side" on F.SilkS covers pad C23.1 (0.81 mm2) | C23 @ (35.2, 83.2) |
| error | check_silk / silk_over_pad | silk "Pin sockets to the bottom solder this side" on F.SilkS covers pad C23.2 (0.81 mm2) | C23 @ (33.6, 83.2) |
| error | check_silk / silk_over_pad | silk "Raspberry Pi Pico or Pico-W" on F.SilkS covers pad U2.8 (2.17 mm2) | U2 @ (193.1, 47.4) |
| error | check_silk / silk_over_pad | silk "Raspberry Pi Pico or Pico-W" on F.SilkS covers pad U2.8 (4.47 mm2) | U2 @ (193.1, 47.4) |
| error | check_silk / silk_over_pad | silk "Raspberry Pi Pico or Pico-W" on F.SilkS covers pad U2.33 (2.17 mm2) | U2 @ (210.9, 47.4) |
| error | check_silk / silk_over_pad | silk "Raspberry Pi Pico or Pico-W" on F.SilkS covers pad U2.33 (4.47 mm2) | U2 @ (210.9, 47.4) |
| error | check_silk / silk_over_pad | silk "Adafruit 1833 or similar µUSB breakout" on F.SilkS covers pad J5. (0.50 mm2) | J5 @ (239.3, 29.6) |
| error | check_silk / silk_over_pad | silk "Adafruit 1833 or similar µUSB breakout" on F.SilkS covers pad J5.1 (0.40 mm2) | J5 @ (238.1, 30.7) |
| error | check_silk / silk_over_pad | silk "Adafruit 1833 or similar µUSB breakout" on F.SilkS covers pad J5.2 (0.40 mm2) | J5 @ (237.5, 30.7) |
| error | check_silk / silk_over_pad | silk "Adafruit 1833 or similar µUSB breakout" on F.SilkS covers pad J5.3 (0.40 mm2) | J5 @ (236.8, 30.7) |
| error | check_silk / silk_over_pad | silk "Adafruit 1833 or similar µUSB breakout" on F.SilkS covers pad J5.4 (0.32 mm2) | J5 @ (236.2, 30.7) |
| error | check_silk / silk_over_pad | silk "Adafruit 1833 or similar µUSB breakout" on F.SilkS covers pad J5.6 (1.65 mm2) | J5 @ (240.6, 30.7) |
| error | check_silk / silk_over_pad | silk line on F.SilkS covers pad U2.42 (0.25 mm2) | U2 @ (202.0, 77.6) |
| error | check_silk / silk_over_pad | silk line on F.SilkS covers pad U2.42 (0.52 mm2) | U2 @ (202.0, 77.6) |
| error | check.dfm / dfm_clearance | copper clearance 0.0268 mm below JLC minimum 0.127 mm on F.Cu | @ (181.5, 58.2) |

11 more in `runs/rp2040-dmxsun/reports/`.

### rp2040-dmxsun-iso-io

https://github.com/OpenLightingProject/rp2040-dmxsun at `f3b1749c982d`, `hardware/ioboard_4ports_isolated/ioboard_4ports_isolated.kicad_pcb`, Apache-2.0, analog, 2 layers.

verify_all checks: check_creepage skipped, check_current skipped, check_decoupling skipped, check_diffpair pass, check_mating violations, check_pdn skipped, check_ratings skipped, check_return_path skipped, check_route_style violations, check_silk violations, check_thermal skipped

| severity | check | finding | where |
|---|---|---|---|
| error | check_mating / mating_mouth_inset | J14 (rj45) cannot be mated: its mouth is 8.0 mm inside the +y edge (limit 1.0 mm) | J14 @ (77.9, 56.5) |
| error | check_mating / mating_zone_blocked | J14 (rj45): J4, J5, J8, J9 sit in the plug's insertion zone in front of its mouth (30.0 mm plug + 3.0 mm grip) | J14, J4, J5, J8, J9 @ (77.9, 88.4) |
| error | check.dfm / dfm_silk_over_pad | silkscreen printed over a solder-mask opening (0.1502 mm2) on F.Silkscreen - pad of U2 | U2 @ (45.0, 43.9) |
| error | check.dfm / dfm_silk_over_pad | silkscreen printed over a solder-mask opening (0.1502 mm2) on F.Silkscreen - pad of U2 | U2 @ (50.0, 43.9) |
| error | check.dfm / dfm_silk_over_pad | silkscreen printed over a solder-mask opening (0.0504 mm2) on F.Silkscreen - pad of J5 | J5 @ (68.8, 67.0) |
| error | check.dfm / dfm_silk_over_pad | silkscreen printed over a solder-mask opening (0.3609 mm2) on F.Silkscreen - pad of J14 | J14 @ (83.6, 56.5) |
| error | check.dfm / dfm_silk_over_pad | silkscreen printed over a solder-mask opening (0.3533 mm2) on F.Silkscreen - pad of J14 | J14 @ (72.2, 56.5) |
| error | check.dfm / dfm_silk_over_pad | silkscreen printed over a solder-mask opening (0.2177 mm2) on F.Silkscreen - pad of U3 | U3 @ (102.6, 44.1) |
| error | check.dfm / dfm_silk_over_pad | silkscreen printed over a solder-mask opening (0.2177 mm2) on F.Silkscreen - pad of U3 | U3 @ (107.7, 44.1) |
| warning | check_silk / silk_misattributed | refdes "PS1" sits 1.42 mm beyond its own pads and 1.00 mm from U2 - reads as U2's label; scripted fix: place_edit.py move_text | PS1 @ (55.5, 40.5) |
| warning | check_route_style / route_style | 1 needless jog(s): a sidestep smaller than the track clears nothing on /RJ45_OUT_5 F.Cu | /RJ45_OUT_5 @ (90.1, 45.9) |
| warning | check_route_style / route_style | 1 needless jog(s): a sidestep smaller than the track clears nothing on /RJ45_OUT_8 F.Cu | /RJ45_OUT_8 @ (117.6, 53.0) |
| warning | check_route_style / route_style | 1 needless jog(s): a sidestep smaller than the track clears nothing on /VBUS_1+2 F.Cu | /VBUS_1+2 @ (42.4, 46.1) |
| warning | check_route_style / route_style | 1 needless jog(s): a sidestep smaller than the track clears nothing on /VBUS_3+4 F.Cu | /VBUS_3+4 @ (99.0, 44.3) |
| warning | check.dfm / dfm_silk_width | 1542 silk strokes below JLC minimum width 0.15 mm (narrowest 0.0100 mm) on F.Silkscreen | @ (104.4, 26.3) |
| warning | check.dfm / dfm_silk_over_pad | silkscreen printed over a solder-mask opening (0.0249 mm2) on F.Silkscreen - pad of J3 (sliver; fab auto-clips silk at mask openings) | J3 @ (38.2, 62.0) |
| warning | check.dfm / dfm_silk_over_pad | silkscreen printed over a solder-mask opening (0.0249 mm2) on F.Silkscreen - pad of J5 (sliver; fab auto-clips silk at mask openings) | J5 @ (64.8, 62.0) |
| warning | check.dfm / dfm_silk_over_pad | silkscreen printed over a solder-mask opening (0.0249 mm2) on F.Silkscreen - pad of J9 (sliver; fab auto-clips silk at mask openings) | J9 @ (91.2, 62.0) |
| warning | check.dfm / dfm_silk_over_pad | silkscreen printed over a solder-mask opening (0.0249 mm2) on F.Silkscreen - pad of J11 (sliver; fab auto-clips silk at mask openings) | J11 @ (117.8, 62.0) |

### buspirate5-rev10

https://github.com/DangerousPrototypes/BusPirate5-hardware at `acb9cd667ce6`, `bus_pirate_pcb/development/5-REV10-PFET-bug/BusPirate-5-rev10.kicad_pcb`, MIT, mcu-usb, 4 layers.

Outcome: **fixed-in-later-rev** (directory bus_pirate_pcb/development/5-REV10-PFET-bug at the pinned commit; REV10A is the released revision)

Revision pair: before of [buspirate5-rev10a](#buspirate5-rev10a). REV10 has a P-FET bug, named in its directory; REV10A replaces it

verify_all checks: check_creepage skipped, check_current skipped, check_decoupling skipped, check_diffpair pass, check_mating pass, check_pdn skipped, check_ratings skipped, check_return_path skipped, check_route_style violations, check_silk violations, check_thermal skipped

| severity | check | finding | where |
|---|---|---|---|
| error | check_silk / silk_over_pad | silk "GND" on F.SilkS covers pad ?.1 (1.35 mm2) | ? @ (148.0, 70.8) |
| error | check_silk / silk_over_pad | silk "SWDIO" on F.SilkS covers pad ?.2 (2.20 mm2) | ? @ (150.6, 70.8) |
| error | check_silk / silk_over_pad | silk "SWCLK" on F.SilkS covers pad ?.3 (2.20 mm2) | ? @ (153.1, 70.8) |
| error | check_silk / silk_over_pad | silk "hide" on F.SilkS covers pad ?.4 (0.17 mm2) | ? @ (151.8, 98.7) |
| error | check_silk / silk_over_pad | silk "hide" on F.SilkS covers pad ?.2 (0.12 mm2) | ? @ (153.4, 102.0) |
| error | check_silk / silk_over_pad | silk "hide" on F.SilkS covers pad ?.3 (0.25 mm2) | ? @ (152.8, 102.0) |
| error | check_silk / silk_over_pad | silk "hide" on F.SilkS covers pad ?.3 (0.26 mm2) | ? @ (147.0, 102.0) |
| error | check_silk / silk_over_pad | silk "hide" on F.SilkS covers pad ?.1 (0.20 mm2) | ? @ (147.3, 98.7) |
| error | check_silk / silk_over_pad | silk "hide" on F.SilkS covers pad ?.4 (0.16 mm2) | ? @ (149.8, 103.9) |
| error | check_silk / silk_over_pad | silk "hide" on F.SilkS covers pad ?.5 (0.16 mm2) | ? @ (150.5, 103.9) |
| error | check_silk / silk_over_pad | silk "hide" on F.SilkS covers pad ?.6 (0.16 mm2) | ? @ (151.1, 103.9) |
| error | check_silk / silk_over_pad | silk "hide" on F.SilkS covers pad ?.1 (0.36 mm2) | ? @ (129.7, 74.7) |
| error | check_silk / silk_over_pad | silk "hide" on F.SilkS covers pad ?.2 (0.36 mm2) | ? @ (129.7, 75.7) |
| error | check_silk / silk_over_pad | silk "hide" on F.SilkS covers pad ?.1 (0.26 mm2) | ? @ (130.7, 75.7) |
| error | check_silk / silk_over_pad | silk "hide" on F.SilkS covers pad ?.2 (0.26 mm2) | ? @ (130.7, 74.7) |
| error | check_silk / silk_over_pad | silk "hide" on F.SilkS covers pad ?.4 (0.26 mm2) | ? @ (108.6, 104.0) |
| error | check_silk / silk_over_pad | silk "hide" on F.SilkS covers pad ?.21 (0.52 mm2) | ? @ (128.3, 101.2) |
| error | check_silk / silk_over_pad | silk "hide" on F.SilkS covers pad ?.22 (0.52 mm2) | ? @ (127.6, 101.2) |
| error | check_silk / silk_over_pad | silk "hide" on F.SilkS covers pad ?.23 (0.52 mm2) | ? @ (127.0, 101.2) |
| error | check_silk / silk_over_pad | silk "hide" on F.SilkS covers pad ?.24 (0.52 mm2) | ? @ (126.3, 101.2) |
| error | check_silk / silk_over_pad | silk "hide" on F.SilkS covers pad ?.2 (0.33 mm2) | ? @ (125.2, 101.1) |
| error | check_silk / silk_over_pad | silk "hide" on F.SilkS covers pad ?.2 (0.33 mm2) | ? @ (156.0, 98.5) |
| error | check_silk / silk_over_pad | silk "hide" on F.SilkS covers pad ?.3 (0.26 mm2) | ? @ (149.8, 102.0) |
| error | check_silk / silk_over_pad | silk "hide" on F.SilkS covers pad ?.1 (0.26 mm2) | ? @ (148.3, 102.0) |
| error | check_silk / silk_over_pad | silk "hide" on F.SilkS covers pad ?.2 (0.26 mm2) | ? @ (147.6, 102.0) |

601 more in `runs/buspirate5-rev10/reports/`.

### buspirate5-rev10a

https://github.com/DangerousPrototypes/BusPirate5-hardware at `acb9cd667ce6`, `bus_pirate_pcb/5-REV10A/REV10a.kicad_pcb`, MIT, mcu-usb, 4 layers.

Revision pair: after of [buspirate5-rev10](#buspirate5-rev10). fixes the REV10 P-FET bug

verify_all checks: check_creepage skipped, check_current skipped, check_decoupling skipped, check_diffpair pass, check_mating pass, check_pdn skipped, check_ratings skipped, check_return_path skipped, check_route_style violations, check_silk violations, check_thermal skipped

| severity | check | finding | where |
|---|---|---|---|
| error | check_silk / silk_over_pad | silk "GND" on F.SilkS covers pad ?.1 (1.35 mm2) | ? @ (148.0, 70.8) |
| error | check_silk / silk_over_pad | silk "SWDIO" on F.SilkS covers pad ?.2 (2.20 mm2) | ? @ (150.6, 70.8) |
| error | check_silk / silk_over_pad | silk "v.trocio" on F.SilkS covers pad ?.2 (0.27 mm2) | ? @ (140.0, 82.2) |
| error | check_silk / silk_over_pad | silk "Ian Lesnet" on F.SilkS covers pad ?. (0.71 mm2) | ? @ (150.4, 78.5) |
| error | check_silk / silk_over_pad | silk "SWCLK" on F.SilkS covers pad ?.3 (2.20 mm2) | ? @ (153.1, 70.8) |
| error | check_silk / silk_over_pad | silk "hide" on F.SilkS covers pad ?.4 (0.17 mm2) | ? @ (151.8, 98.7) |
| error | check_silk / silk_over_pad | silk "hide" on F.SilkS covers pad ?.2 (0.12 mm2) | ? @ (153.4, 102.0) |
| error | check_silk / silk_over_pad | silk "hide" on F.SilkS covers pad ?.3 (0.25 mm2) | ? @ (152.8, 102.0) |
| error | check_silk / silk_over_pad | silk "hide" on F.SilkS covers pad ?.3 (0.26 mm2) | ? @ (147.0, 102.0) |
| error | check_silk / silk_over_pad | silk "hide" on F.SilkS covers pad ?.1 (0.20 mm2) | ? @ (147.3, 98.7) |
| error | check_silk / silk_over_pad | silk "hide" on F.SilkS covers pad ?.4 (0.16 mm2) | ? @ (149.8, 103.9) |
| error | check_silk / silk_over_pad | silk "hide" on F.SilkS covers pad ?.5 (0.16 mm2) | ? @ (150.5, 103.9) |
| error | check_silk / silk_over_pad | silk "hide" on F.SilkS covers pad ?.6 (0.16 mm2) | ? @ (151.1, 103.9) |
| error | check_silk / silk_over_pad | silk "hide" on F.SilkS covers pad ?.1 (0.36 mm2) | ? @ (129.7, 74.7) |
| error | check_silk / silk_over_pad | silk "hide" on F.SilkS covers pad ?.2 (0.36 mm2) | ? @ (129.7, 75.7) |
| error | check_silk / silk_over_pad | silk "hide" on F.SilkS covers pad ?.1 (0.26 mm2) | ? @ (130.7, 75.7) |
| error | check_silk / silk_over_pad | silk "hide" on F.SilkS covers pad ?.2 (0.26 mm2) | ? @ (130.7, 74.7) |
| error | check_silk / silk_over_pad | silk "hide" on F.SilkS covers pad ?.4 (0.26 mm2) | ? @ (108.6, 104.0) |
| error | check_silk / silk_over_pad | silk "hide" on F.SilkS covers pad ?.21 (0.52 mm2) | ? @ (128.3, 101.2) |
| error | check_silk / silk_over_pad | silk "hide" on F.SilkS covers pad ?.22 (0.52 mm2) | ? @ (127.6, 101.2) |
| error | check_silk / silk_over_pad | silk "hide" on F.SilkS covers pad ?.23 (0.52 mm2) | ? @ (127.0, 101.2) |
| error | check_silk / silk_over_pad | silk "hide" on F.SilkS covers pad ?.24 (0.52 mm2) | ? @ (126.3, 101.2) |
| error | check_silk / silk_over_pad | silk "hide" on F.SilkS covers pad ?.2 (0.33 mm2) | ? @ (125.2, 101.1) |
| error | check_silk / silk_over_pad | silk "hide" on F.SilkS covers pad ?.2 (0.33 mm2) | ? @ (156.0, 98.5) |
| error | check_silk / silk_over_pad | silk "hide" on F.SilkS covers pad ?.3 (0.26 mm2) | ? @ (149.8, 102.0) |

607 more in `runs/buspirate5-rev10a/reports/`.

### glasgow-revc3

https://github.com/GlasgowEmbedded/glasgow at `50c97c429656`, `hardware/boards/glasgow/revC3/glasgow.kicad_pcb`, 0BSD, mcu-usb, 4 layers.

Outcome: **product** (Crowd Supply campaign https://www.crowdsupply.com/1bitsquared/glasgow shipped revC3)

verify_all checks: check_creepage skipped, check_current skipped, check_decoupling skipped, check_diffpair pass, check_mating pass, check_pdn skipped, check_ratings skipped, check_return_path skipped, check_route_style violations, check_silk violations, check_thermal skipped

| severity | check | finding | where |
|---|---|---|---|
| error | check_silk / silk_over_pad | silk "5V" on B.SilkS covers pad ?.1 (0.66 mm2) | ? @ (81.5, 116.0) |
| error | check_silk / silk_over_pad | silk "SCL" on B.SilkS covers pad ?.1 (0.78 mm2) | ? @ (88.3, 113.5) |
| error | check_silk / silk_over_pad | silk "GND" on B.SilkS covers pad ?.1 (0.78 mm2) | ? @ (88.3, 111.0) |
| error | check_silk / silk_over_pad | silk "D-" on B.SilkS covers pad ?.1 (0.66 mm2) | ? @ (57.9, 94.7) |
| error | check_silk / silk_over_pad | silk "GND" on B.SilkS covers pad ?.1 (0.78 mm2) | ? @ (57.9, 96.8) |
| error | check_silk / silk_over_pad | silk "3V3" on B.SilkS covers pad ?.1 (0.78 mm2) | ? @ (81.5, 111.0) |
| error | check_silk / silk_over_pad | silk "VDAC" on B.SilkS covers pad ?.1 (0.78 mm2) | ? @ (124.6, 91.2) |
| error | check_silk / silk_over_pad | silk "VDAC" on B.SilkS covers pad ?.1 (0.78 mm2) | ? @ (122.0, 99.8) |
| error | check_silk / silk_over_pad | silk "SDA" on B.SilkS covers pad ?.1 (0.78 mm2) | ? @ (88.3, 116.0) |
| error | check_silk / silk_over_pad | silk "Pull-Up/Down Resistors Bank A" on B.SilkS covers pad ?.2 (0.79 mm2) | ? @ (120.7, 89.6) |
| error | check_silk / silk_over_pad | silk "Pull-Up/Down Resistors Bank A" on B.SilkS covers pad ?.2 (0.79 mm2) | ? @ (122.5, 89.6) |
| error | check_silk / silk_over_pad | silk "Pull-Up/Down Resistors Bank B" on B.SilkS covers pad ?.1 (0.36 mm2) | ? @ (101.0, 101.7) |
| error | check_silk / silk_over_pad | silk "https://glasgow-embedded.org" on B.SilkS covers pad ?.1 (0.36 mm2) | ? @ (95.2, 104.5) |
| error | check_silk / silk_over_pad | silk "CLKREF" on F.SilkS covers pad ?.1 (0.78 mm2) | ? @ (73.1, 89.0) |
| error | check_silk / silk_over_pad | silk "B" on F.SilkS covers pad ?.5 (0.23 mm2) | ? @ (91.3, 106.3) |
| error | check_silk / silk_over_pad | silk "SCL" on F.SilkS covers pad ?.1 (0.76 mm2) | ? @ (76.4, 105.0) |
| error | check_silk / silk_over_pad | silk "5V" on F.SilkS covers pad ?.1 (0.47 mm2) | ? @ (94.7, 109.0) |
| error | check_silk / silk_over_pad | silk "3V3" on F.SilkS covers pad ?.1 (0.78 mm2) | ? @ (94.7, 107.3) |
| error | check_silk / silk_over_pad | silk "SDA" on F.SilkS covers pad ?.1 (0.76 mm2) | ? @ (76.4, 103.3) |
| error | check_silk / silk_over_pad | silk "CLKIF" on F.SilkS covers pad ?.1 (0.78 mm2) | ? @ (64.4, 99.9) |
| error | check_silk / silk_over_pad | silk "1V2" on F.SilkS covers pad ?.1 (0.78 mm2) | ? @ (77.3, 101.4) |
| error | check_silk / silk_over_pad | silk "Glasgow revC3" on F.SilkS covers pad ?.1 (0.79 mm2) | ? @ (56.2, 83.0) |
| error | check_silk / silk_over_pad | silk "Glasgow revC3" on F.SilkS covers pad ?.2 (0.79 mm2) | ? @ (57.8, 83.0) |
| error | check_silk / silk_over_pad | silk "Glasgow revC3" on F.SilkS covers pad ?.1 (0.36 mm2) | ? @ (59.0, 83.5) |
| error | check_silk / silk_over_pad | silk "Glasgow revC3" on F.SilkS covers pad ?.2 (0.36 mm2) | ? @ (59.0, 82.5) |

882 more in `runs/glasgow-revc3/reports/`.

### glasgow-revd0

https://github.com/GlasgowEmbedded/glasgow at `50c97c429656`, `hardware/boards/glasgow/revD0/glasgow.kicad_pcb`, 0BSD, mcu-usb, 6 layers.

verify_all checks: check_creepage skipped, check_current skipped, check_decoupling skipped, check_diffpair violations, check_mating pass, check_pdn skipped, check_ratings skipped, check_return_path skipped, check_route_style violations, check_silk violations, check_thermal skipped

| severity | check | finding | where |
|---|---|---|---|
| error | check_diffpair / diffpair_skew | diff pair /ADC/A1_P//ADC/A1_N length skew 12.82 mm (~87 ps, eps_r 4.1); limit 5.0 mm | /ADC/A1_P @ (159.2, 85.7) |
| error | check_diffpair / diffpair_uncoupled | diff pair /ADC/A1_P//ADC/A1_N has 19.40 mm of /ADC/A1_N running uncoupled (> 0.69 mm from its partner); limit 5.0 mm | /ADC/A1_N @ (159.2, 85.7) |
| error | check_diffpair / diffpair_uncoupled | diff pair /ADC/A2_P//ADC/A2_N has 14.51 mm of /ADC/A2_P running uncoupled (> 0.70 mm from its partner); limit 5.0 mm | /ADC/A2_P @ (157.9, 86.8) |
| error | check_diffpair / diffpair_uncoupled | diff pair /ADC/A3_P//ADC/A3_N has 11.67 mm of /ADC/A3_N running uncoupled (> 0.69 mm from its partner); limit 5.0 mm | /ADC/A3_N @ (158.5, 87.8) |
| error | check_silk / silk_over_pad | silk "~{SYNC}" on F.SilkS covers pad D35.1 (0.13 mm2) | D35 @ (239.7, 70.1) |
| error | check_silk / silk_over_pad | silk "~{SYNC}" on F.SilkS covers pad D32.2 (0.18 mm2) | D32 @ (238.7, 73.5) |
| error | check_silk / silk_over_pad | silk "~{SYNC}" on F.SilkS covers pad R41.1 (0.33 mm2) | R41 @ (238.5, 74.8) |
| error | check_silk / silk_over_pad | silk "~{SYNC}" on F.SilkS covers pad R41.2 (0.33 mm2) | R41 @ (239.6, 74.8) |
| error | check_silk / silk_over_pad | silk "U1 U2 U3 U4 U5" on F.SilkS covers pad R43.1 (0.33 mm2) | R43 @ (238.5, 78.6) |
| error | check_silk / silk_over_pad | silk "U1 U2 U3 U4 U5" on F.SilkS covers pad R43.2 (0.33 mm2) | R43 @ (239.5, 78.6) |
| error | check_silk / silk_over_pad | silk "U1 U2 U3 U4 U5" on F.SilkS covers pad R46.2 (0.33 mm2) | R46 @ (236.4, 78.3) |
| error | check_silk / silk_over_pad | silk "U1 U2 U3 U4 U5" on F.SilkS covers pad D26.1 (0.79 mm2) | D26 @ (242.4, 78.6) |
| error | check_silk / silk_over_pad | silk "U1 U2 U3 U4 U5" on F.SilkS covers pad D26.2 (0.79 mm2) | D26 @ (240.8, 78.6) |
| error | check_silk / silk_over_pad | silk "ON CY DN AC ER" on F.SilkS covers pad D3.1 (0.79 mm2) | D3 @ (242.4, 99.4) |
| error | check_silk / silk_over_pad | silk "ON CY DN AC ER" on F.SilkS covers pad D3.2 (0.79 mm2) | D3 @ (240.8, 99.4) |
| error | check_silk / silk_over_pad | silk "ON CY DN AC ER" on F.SilkS covers pad R3.1 (0.33 mm2) | R3 @ (238.5, 99.4) |
| error | check_silk / silk_over_pad | silk "ON CY DN AC ER" on F.SilkS covers pad R3.2 (0.33 mm2) | R3 @ (239.6, 99.4) |
| error | check_silk / silk_over_pad | silk "S 0 1 2 3 4 5 6 7" on F.SilkS covers pad H5.1 (0.67 mm2) | H5 @ (176.9, 89.0) |
| error | check_silk / silk_over_pad | silk "S 0 1 2 3 4 5 6 7" on F.SilkS covers pad C103.1 (0.19 mm2) | C103 @ (174.8, 78.2) |
| error | check_silk / silk_over_pad | silk "S 0 1 2 3 4 5 6 7" on F.SilkS covers pad C103.2 (0.33 mm2) | C103 @ (175.7, 78.2) |
| error | check_silk / silk_over_pad | silk "S 0 1 2 3 4 5 6 7" on F.SilkS covers pad C104.1 (0.23 mm2) | C104 @ (176.8, 78.6) |
| error | check_silk / silk_over_pad | silk "S 0 1 2 3 4 5 6 7" on F.SilkS covers pad J10.9 (5.05 mm2) | J10 @ (175.7, 73.8) |
| error | check_silk / silk_over_pad | silk "S 0 1 2 3 4 5 6 7" on F.SilkS covers pad J10.10 (4.26 mm2) | J10 @ (175.7, 66.2) |
| error | check_silk / silk_over_pad | silk "S 0 1 2 3 4 5 6 7" on F.SilkS covers pad U21.6 (0.21 mm2) | U21 @ (175.0, 82.3) |
| error | check_silk / silk_over_pad | silk "S 0 1 2 3 4 5 6 7" on F.SilkS covers pad U21.7 (0.21 mm2) | U21 @ (175.5, 82.3) |

2270 more in `runs/glasgow-revd0/reports/`.

### glasgow-revd1

https://github.com/GlasgowEmbedded/glasgow at `50c97c429656`, `hardware/boards/glasgow/revD1/glasgow.kicad_pcb`, 0BSD, mcu-usb, 6 layers.

Outcome: **errata** (https://github.com/GlasgowEmbedded/glasgow/issues/1302 (revD1 errata, open))

verify_all checks: check_creepage skipped, check_current skipped, check_decoupling skipped, check_diffpair violations, check_mating violations, check_pdn skipped, check_ratings skipped, check_return_path skipped, check_route_style violations, check_silk violations, check_thermal skipped

| severity | check | finding | where |
|---|---|---|---|
| error | check_diffpair / diffpair_skew | diff pair /ADC/A1_P//ADC/A1_N length skew 13.09 mm (~89 ps, eps_r 4.2); limit 5.0 mm | /ADC/A1_P @ (165.6, 95.0) |
| error | check_diffpair / diffpair_uncoupled | diff pair /ADC/A1_P//ADC/A1_N has 19.40 mm of /ADC/A1_N running uncoupled (> 0.69 mm from its partner); limit 5.0 mm | /ADC/A1_N @ (165.6, 95.0) |
| error | check_diffpair / diffpair_uncoupled | diff pair /ADC/A2_P//ADC/A2_N has 15.15 mm of /ADC/A2_P running uncoupled (> 0.71 mm from its partner); limit 5.0 mm | /ADC/A2_P @ (202.9, 110.4) |
| error | check_diffpair / diffpair_uncoupled | diff pair /ADC/A3_P//ADC/A3_N has 11.67 mm of /ADC/A3_N running uncoupled (> 0.69 mm from its partner); limit 5.0 mm | /ADC/A3_N @ (202.1, 109.5) |
| error | check_silk / silk_over_pad | silk "JTAG" on F.SilkS covers pad J5.10 (0.66 mm2) | J5 @ (203.8, 93.2) |
| error | check_silk / silk_over_pad | silk "0" on F.SilkS covers pad C11.2 (0.33 mm2) | C11 @ (137.9, 97.7) |
| error | check_silk / silk_over_pad | silk "7" on F.SilkS covers pad U3.3 (0.23 mm2) | U3 @ (193.0, 97.6) |
| error | check_silk / silk_over_pad | silk "ENVB" on F.SilkS covers pad D60.1 (0.46 mm2) | D60 @ (125.8, 125.4) |
| error | check_silk / silk_over_pad | silk "ENVC" on F.SilkS covers pad D80.1 (0.79 mm2) | D80 @ (204.8, 91.0) |
| error | check_silk / silk_over_pad | silk "ENVC" on F.SilkS covers pad D29.1 (0.18 mm2) | D29 @ (203.6, 90.3) |
| error | check_silk / silk_over_pad | silk "ENVD" on F.SilkS covers pad D100.1 (0.79 mm2) | D100 @ (204.8, 127.0) |
| error | check_silk / silk_over_pad | silk "Glasgow revD1" on F.SilkS covers pad J6. (0.28 mm2) | J6 @ (147.3, 99.9) |
| error | check_silk / silk_over_pad | silk "Glasgow revD1" on F.SilkS covers pad J6.1 (0.35 mm2) | J6 @ (147.0, 101.0) |
| error | check_silk / silk_over_pad | silk "Glasgow revD1" on F.SilkS covers pad J6.2 (0.35 mm2) | J6 @ (147.0, 101.5) |
| error | check_silk / silk_over_pad | silk "Glasgow revD1" on F.SilkS covers pad J6.31 (0.48 mm2) | J6 @ (150.6, 101.0) |
| error | check_silk / silk_over_pad | silk "Glasgow revD1" on F.SilkS covers pad J6.32 (0.48 mm2) | J6 @ (150.6, 101.5) |
| error | check_silk / silk_over_pad | silk "Glasgow revD1" on F.SilkS covers pad J6.MP (0.90 mm2) | J6 @ (148.8, 99.2) |
| error | check_silk / silk_over_pad | silk "Fully Automated 2026" on B.SilkS covers pad TP27.1 (0.13 mm2) | TP27 @ (164.8, 118.1) |
| error | check_silk / silk_over_pad | silk "Fully Automated 2026" on B.SilkS covers pad R54.1 (0.30 mm2) | R54 @ (163.2, 118.3) |
| error | check_silk / silk_over_pad | silk "Fully Automated 2026" on B.SilkS covers pad R54.2 (0.30 mm2) | R54 @ (162.2, 118.3) |
| error | check_mating / mating_zone_blocked | J11 (wire_to_board_top): H5 (5.0 mm) within 2.5 mm - taller than 3.0 mm leaves no room for the plug housing and a finger | H5, J11 @ (186.4, 101.7) |
| error | check.dfm / dfm_clearance | copper clearance 0.0133 mm below JLC minimum 0.0889 mm on F.Cu | @ (138.1, 103.4) |
| error | check.dfm / dfm_clearance | copper clearance 0.0600 mm below JLC minimum 0.0889 mm on F.Cu | @ (136.5, 104.3) |
| error | check.dfm / dfm_clearance | copper clearance 0.0600 mm below JLC minimum 0.0889 mm on F.Cu | @ (144.5, 104.2) |
| error | check.dfm / dfm_clearance | copper clearance 0.0703 mm below JLC minimum 0.0889 mm on F.Cu | @ (138.7, 97.8) |

2330 more in `runs/glasgow-revd1/reports/`.

### usbc-cable-tester

https://github.com/Qeteshpony/USB-C-Cable-Tester at `b30a134b17b6`, `pcb/USB-Cable-Tester.kicad_pcb`, BSD-2-Clause, mcu-usb, 2 layers.

verify_all checks: check_creepage skipped, check_current skipped, check_decoupling skipped, check_diffpair pass, check_mating pass, check_pdn skipped, check_ratings skipped, check_return_path skipped, check_route_style violations, check_silk violations, check_thermal skipped

| severity | check | finding | where |
|---|---|---|---|
| error | check_silk / silk_over_pad | silk "2" on F.SilkS covers pad ?.2 (0.41 mm2) | ? @ (163.3, 80.0) |
| error | check_silk / silk_over_pad | silk "3" on F.SilkS covers pad ?.2 (0.41 mm2) | ? @ (163.3, 95.0) |
| error | check_silk / silk_over_pad | silk "1" on F.SilkS covers pad ?.2 (0.41 mm2) | ? @ (163.3, 115.0) |
| error | check_silk / silk_over_pad | silk "3.x" on F.SilkS covers pad ?.2 (0.79 mm2) | ? @ (163.3, 110.0) |
| error | check_silk / silk_over_pad | silk "3.x" on F.SilkS covers pad ?.2 (0.79 mm2) | ? @ (163.3, 107.5) |
| error | check_silk / silk_over_pad | silk "4" on F.SilkS covers pad ?.2 (0.41 mm2) | ? @ (163.3, 85.0) |
| error | check_silk / silk_over_pad | silk "2.0" on F.SilkS covers pad ?.2 (0.79 mm2) | ? @ (163.3, 105.0) |
| error | check_silk / silk_over_pad | silk "1" on F.SilkS covers pad ?.2 (0.41 mm2) | ? @ (163.3, 90.0) |
| error | check_silk / silk_over_pad | silk "2" on F.SilkS covers pad ?.2 (0.41 mm2) | ? @ (163.3, 117.5) |
| error | check_silk / silk_over_pad | silk "4" on F.SilkS covers pad ?.2 (0.41 mm2) | ? @ (163.3, 97.5) |
| error | check_silk / silk_over_pad | silk "2" on F.SilkS covers pad ?.2 (0.41 mm2) | ? @ (163.3, 92.5) |
| error | check_silk / silk_over_pad | silk "3" on F.SilkS covers pad ?.2 (0.41 mm2) | ? @ (163.3, 82.5) |
| error | check_silk / silk_over_pad | silk "1" on F.SilkS covers pad ?.2 (0.41 mm2) | ? @ (163.3, 77.5) |
| error | check_silk / silk_over_pad | silk rect on F.SilkS covers pad ?.1 (0.79 mm2) | ? @ (161.7, 122.5) |
| error | check_silk / silk_over_pad | silk rect on F.SilkS covers pad ?.2 (0.79 mm2) | ? @ (163.3, 122.5) |
| error | check_silk / silk_over_pad | silk rect on F.SilkS covers pad ?.1 (0.79 mm2) | ? @ (161.7, 117.5) |
| error | check_silk / silk_over_pad | silk rect on F.SilkS covers pad ?.2 (0.79 mm2) | ? @ (163.3, 117.5) |
| error | check_silk / silk_over_pad | silk rect on F.SilkS covers pad ?.1 (0.79 mm2) | ? @ (161.7, 115.0) |
| error | check_silk / silk_over_pad | silk rect on F.SilkS covers pad ?.2 (0.79 mm2) | ? @ (163.3, 115.0) |
| error | check_silk / silk_over_pad | silk rect on F.SilkS covers pad ?.1 (0.79 mm2) | ? @ (161.7, 110.0) |
| error | check_silk / silk_over_pad | silk rect on F.SilkS covers pad ?.2 (0.79 mm2) | ? @ (163.3, 110.0) |
| error | check_silk / silk_over_pad | silk rect on F.SilkS covers pad ?.1 (0.79 mm2) | ? @ (161.7, 105.0) |
| error | check_silk / silk_over_pad | silk rect on F.SilkS covers pad ?.2 (0.79 mm2) | ? @ (163.3, 105.0) |
| error | check_silk / silk_over_pad | silk rect on F.SilkS covers pad ?.1 (0.79 mm2) | ? @ (161.7, 107.5) |
| error | check_silk / silk_over_pad | silk rect on F.SilkS covers pad ?.2 (0.79 mm2) | ? @ (163.3, 107.5) |

76 more in `runs/usbc-cable-tester/reports/`.

### gulu-esp32c3-epaper

https://github.com/Plaenkler/Gulu_ESP32-C3_ePaper at `d0042d3d2785`, `Gulu_ESP32-C3_ePaper.kicad_pcb`, BSD-3-Clause, mcu-usb, 2 layers.

verify_all checks: check_creepage skipped, check_current skipped, check_decoupling skipped, check_diffpair pass, check_mating violations, check_pdn skipped, check_ratings skipped, check_return_path skipped, check_route_style violations, check_silk pass, check_thermal skipped

| severity | check | finding | where |
|---|---|---|---|
| error | check_mating / mating_zone_blocked | J2 (pin_header): IC1 (4.0 mm) within 2.5 mm - taller than 3.0 mm leaves no room for the plug housing and a finger | IC1, J2 @ (173.9, 107.0) |
| error | check.dfm / dfm_copper_to_edge | copper 0.0000 mm from board edge, JLC minimum 0.3 mm on F.Cu | @ (146.2, 101.3) |
| warning | check_route_style / route_style | 1 needless jog(s): a sidestep smaller than the track clears nothing on Net-(D1-K) F.Cu | Net-(D1-K) @ (139.8, 90.7) |
| warning | check.dfm / dfm_silk_width | 5 silk strokes below JLC minimum width 0.15 mm (narrowest 0.1000 mm) on F.Silkscreen | @ (124.2, 87.4) |

### esp32-poe-m1

https://github.com/OLIMEX/ESP32-POE at `deb38a377d50`, `HARDWARE/ESP32-PoE-hardware-revision-M1/ESP32-PoE_Rev_M1.kicad_pcb`, Apache-2.0, mcu-usb, 4 layers.

Outcome: **product** (OLIMEX sells the ESP32-PoE https://www.olimex.com/Products/IoT/ESP32/ESP32-POE/ (which revision ships is not recorded))

verify_all checks: check_creepage skipped, check_current skipped, check_decoupling skipped, check_diffpair violations, check_mating pass, check_pdn skipped, check_ratings skipped, check_return_path skipped, check_route_style violations, check_silk violations, check_thermal skipped

| severity | check | finding | where |
|---|---|---|---|
| error | check_diffpair / diffpair_skew | diff pair /D+//D- length skew 15.76 mm (~112 ps, eps_r 4.5); limit 5.0 mm | /D+ @ (97.8, 158.2) |
| error | check_diffpair / diffpair_skew | diff pair /TD+//TD- length skew 14.53 mm (~103 ps, eps_r 4.5); limit 5.0 mm | /TD+ @ (109.3, 153.3) |
| error | check_silk / silk_over_pad | silk "www.olimex.com" on B.SilkS covers pad ?.Fid1 (0.47 mm2) | ? @ (116.6, 168.5) |
| error | check_silk / silk_over_pad | silk "(C) 2025" on B.SilkS covers pad ?.1 (0.20 mm2) | ? @ (94.1, 96.0) |
| error | check_silk / silk_over_pad | silk "Compliant" on B.SilkS covers pad ?.39 (1.13 mm2) | ? @ (101.3, 100.6) |
| error | check_silk / silk_over_pad | silk "ESP32-PoE" on F.SilkS covers pad ?.9 (1.28 mm2) | ? @ (108.0, 118.2) |
| error | check_silk / silk_over_pad | silk "hide" on F.SilkS covers pad ?.37 (0.95 mm2) | ? @ (112.6, 92.6) |
| error | check_silk / silk_over_pad | silk "hide" on F.SilkS covers pad ?.38 (0.95 mm2) | ? @ (112.6, 91.3) |
| error | check_silk / silk_over_pad | silk "o" on F.SilkS covers pad ?.1 (0.09 mm2) | ? @ (103.0, 151.6) |
| error | check_silk / silk_over_pad | silk "hardware" on B.SilkS covers pad ?. (0.38 mm2) | ? @ (116.9, 99.2) |
| error | check_silk / silk_over_pad | silk line on B.SilkS covers pad ?. (0.25 mm2) | ? @ (115.1, 99.2) |
| error | check_silk / silk_over_pad | silk line on B.SilkS covers pad ?. (0.27 mm2) | ? @ (115.1, 99.2) |
| error | check.dfm / dfm_copper_to_edge | copper 0.2545 mm from board edge, JLC minimum 0.3 mm on F.Cu | @ (92.2, 97.7) |
| error | check.dfm / dfm_copper_to_edge | copper 0.2545 mm from board edge, JLC minimum 0.3 mm on F.Cu | @ (91.1, 110.9) |
| error | check.dfm / dfm_copper_to_edge | copper 0.2545 mm from board edge, JLC minimum 0.3 mm on F.Cu | @ (92.8, 121.0) |
| error | check.dfm / dfm_copper_to_edge | copper 0.2545 mm from board edge, JLC minimum 0.3 mm on F.Cu | @ (90.8, 149.2) |
| error | check.dfm / dfm_copper_to_edge | copper 0.2545 mm from board edge, JLC minimum 0.3 mm on F.Cu | @ (91.8, 164.1) |
| error | check.dfm / dfm_copper_to_edge | copper 0.2545 mm from board edge, JLC minimum 0.3 mm on F.Cu | @ (104.1, 91.2) |
| error | check.dfm / dfm_copper_to_edge | copper 0.2545 mm from board edge, JLC minimum 0.3 mm on F.Cu | @ (92.9, 168.0) |
| error | check.dfm / dfm_copper_to_edge | copper 0.2545 mm from board edge, JLC minimum 0.3 mm on F.Cu | @ (108.7, 165.6) |
| error | check.dfm / dfm_copper_to_edge | copper 0.2545 mm from board edge, JLC minimum 0.3 mm on F.Cu | @ (116.4, 112.7) |
| error | check.dfm / dfm_copper_to_edge | copper 0.2545 mm from board edge, JLC minimum 0.3 mm on F.Cu | @ (117.1, 96.7) |
| error | check.dfm / dfm_copper_to_edge | copper 0.2545 mm from board edge, JLC minimum 0.3 mm on F.Cu | @ (117.2, 120.4) |
| error | check.dfm / dfm_copper_to_edge | copper 0.2545 mm from board edge, JLC minimum 0.3 mm on In1.Cu | @ (103.6, 124.5) |
| error | check.dfm / dfm_copper_to_edge | copper 0.2545 mm from board edge, JLC minimum 0.3 mm on In1.Cu | @ (109.0, 165.7) |

214 more in `runs/esp32-poe-m1/reports/`.

### esp32-poe-m2

https://github.com/OLIMEX/ESP32-POE at `deb38a377d50`, `HARDWARE/ESP32-PoE-hardware-revision-M2/ESP32-PoE_Rev_M2.kicad_pcb`, Apache-2.0, mcu-usb, 4 layers.

Outcome: **product** (OLIMEX sells the ESP32-PoE https://www.olimex.com/Products/IoT/ESP32/ESP32-POE/ (which revision ships is not recorded))

verify_all checks: check_creepage skipped, check_current skipped, check_decoupling skipped, check_diffpair violations, check_mating pass, check_pdn skipped, check_ratings skipped, check_return_path skipped, check_route_style violations, check_silk violations, check_thermal skipped

| severity | check | finding | where |
|---|---|---|---|
| error | check_diffpair / diffpair_skew | diff pair /D+//D- length skew 15.76 mm (~112 ps, eps_r 4.5); limit 5.0 mm | /D+ @ (97.8, 158.2) |
| error | check_diffpair / diffpair_skew | diff pair /TD+//TD- length skew 14.53 mm (~103 ps, eps_r 4.5); limit 5.0 mm | /TD+ @ (109.3, 153.3) |
| error | check_silk / silk_over_pad | silk "www.olimex.com" on B.SilkS covers pad ?.Fid1 (0.47 mm2) | ? @ (116.6, 168.5) |
| error | check_silk / silk_over_pad | silk "(C) 2025" on B.SilkS covers pad ?.1 (0.20 mm2) | ? @ (94.1, 96.0) |
| error | check_silk / silk_over_pad | silk "Compliant" on B.SilkS covers pad ?.39 (1.13 mm2) | ? @ (101.3, 100.6) |
| error | check_silk / silk_over_pad | silk "ESP32-PoE" on F.SilkS covers pad ?.9 (1.28 mm2) | ? @ (108.0, 118.2) |
| error | check_silk / silk_over_pad | silk "hide" on F.SilkS covers pad ?.37 (0.95 mm2) | ? @ (112.6, 92.6) |
| error | check_silk / silk_over_pad | silk "hide" on F.SilkS covers pad ?.38 (0.95 mm2) | ? @ (112.6, 91.3) |
| error | check_silk / silk_over_pad | silk "o" on F.SilkS covers pad ?.1 (0.09 mm2) | ? @ (103.0, 151.6) |
| error | check_silk / silk_over_pad | silk "hardware" on B.SilkS covers pad ?. (0.38 mm2) | ? @ (116.9, 99.2) |
| error | check_silk / silk_over_pad | silk line on B.SilkS covers pad ?. (0.25 mm2) | ? @ (115.1, 99.2) |
| error | check_silk / silk_over_pad | silk line on B.SilkS covers pad ?. (0.27 mm2) | ? @ (115.1, 99.2) |
| error | check_silk / silk_over_pad | silk "D7" on B.SilkS covers pad ?.1 (2.19 mm2) | ? @ (98.9, 143.8) |
| error | check.dfm / dfm_clearance | copper clearance 0.0130 mm below JLC minimum 0.1016 mm on B.Cu | @ (96.9, 147.8) |
| error | check.dfm / dfm_copper_to_edge | copper 0.2545 mm from board edge, JLC minimum 0.3 mm on F.Cu | @ (92.2, 97.7) |
| error | check.dfm / dfm_copper_to_edge | copper 0.2545 mm from board edge, JLC minimum 0.3 mm on F.Cu | @ (91.1, 110.9) |
| error | check.dfm / dfm_copper_to_edge | copper 0.2545 mm from board edge, JLC minimum 0.3 mm on F.Cu | @ (92.8, 121.0) |
| error | check.dfm / dfm_copper_to_edge | copper 0.2545 mm from board edge, JLC minimum 0.3 mm on F.Cu | @ (90.8, 149.2) |
| error | check.dfm / dfm_copper_to_edge | copper 0.2545 mm from board edge, JLC minimum 0.3 mm on F.Cu | @ (91.8, 164.1) |
| error | check.dfm / dfm_copper_to_edge | copper 0.2545 mm from board edge, JLC minimum 0.3 mm on F.Cu | @ (104.1, 91.2) |
| error | check.dfm / dfm_copper_to_edge | copper 0.2545 mm from board edge, JLC minimum 0.3 mm on F.Cu | @ (92.9, 168.0) |
| error | check.dfm / dfm_copper_to_edge | copper 0.2545 mm from board edge, JLC minimum 0.3 mm on F.Cu | @ (108.7, 165.6) |
| error | check.dfm / dfm_copper_to_edge | copper 0.2545 mm from board edge, JLC minimum 0.3 mm on F.Cu | @ (116.4, 112.7) |
| error | check.dfm / dfm_copper_to_edge | copper 0.2545 mm from board edge, JLC minimum 0.3 mm on F.Cu | @ (117.1, 96.7) |
| error | check.dfm / dfm_copper_to_edge | copper 0.2545 mm from board edge, JLC minimum 0.3 mm on F.Cu | @ (117.2, 120.4) |

222 more in `runs/esp32-poe-m2/reports/`.

### thatmicpre

https://github.com/ojg/thatmicpre at `c9735275db93`, `rack/thatmicpre_v2.kicad_pcb`, CC-BY-SA-4.0, analog, 2 layers.

verify_all checks: check_creepage skipped, check_current skipped, check_decoupling skipped, check_diffpair pass, check_mating pass, check_pdn skipped, check_ratings skipped, check_return_path skipped, check_route_style pass, check_silk violations, check_thermal skipped

| severity | check | finding | where |
|---|---|---|---|
| error | check_silk / silk_over_pad | silk "LED Header" on B.SilkS covers pad ?.1 (2.01 mm2) | ? @ (194.0, 106.1) |
| error | check_silk / silk_over_pad | silk "Gain Header" on B.SilkS covers pad ?.2 (2.01 mm2) | ? @ (194.0, 74.5) |
| error | check_silk / silk_over_pad | silk "hide" on F.SilkS covers pad ?.2 (1.54 mm2) | ? @ (140.0, 113.7) |
| error | check_silk / silk_over_pad | silk "hide" on F.SilkS covers pad ?.1 (1.18 mm2) | ? @ (123.6, 113.7) |
| error | check_silk / silk_over_pad | silk line on B.SilkS covers pad ?.1 (0.20 mm2) | ? @ (181.2, 98.9) |
| error | check_silk / silk_over_pad | silk line on B.SilkS covers pad ?.1 (0.20 mm2) | ? @ (181.3, 74.3) |
| error | check.dfm / dfm_trace_width | trace width 0.0100 mm below JLC minimum 0.127 mm on F.Cu | @ (132.2, 119.1) |
| error | check.dfm / dfm_trace_width | trace width 0.0100 mm below JLC minimum 0.127 mm on F.Cu | @ (132.4, 119.4) |
| error | check.dfm / dfm_trace_width | trace width 0.0100 mm below JLC minimum 0.127 mm on F.Cu | @ (132.7, 119.5) |
| error | check.dfm / dfm_trace_width | trace width 0.0100 mm below JLC minimum 0.127 mm on F.Cu | @ (133.1, 119.5) |
| error | check.dfm / dfm_trace_width | trace width 0.0100 mm below JLC minimum 0.127 mm on F.Cu | @ (133.3, 119.3) |
| error | check.dfm / dfm_trace_width | trace width 0.0100 mm below JLC minimum 0.127 mm on F.Cu | @ (133.4, 119.3) |
| error | check.dfm / dfm_trace_width | trace width 0.0100 mm below JLC minimum 0.127 mm on F.Cu | @ (133.5, 119.2) |
| error | check.dfm / dfm_trace_width | trace width 0.0100 mm below JLC minimum 0.127 mm on F.Cu | @ (133.6, 119.2) |
| error | check.dfm / dfm_trace_width | trace width 0.0100 mm below JLC minimum 0.127 mm on F.Cu | @ (133.6, 119.1) |
| error | check.dfm / dfm_trace_width | trace width 0.0100 mm below JLC minimum 0.127 mm on F.Cu | @ (133.7, 119.1) |
| error | check.dfm / dfm_trace_width | trace width 0.0100 mm below JLC minimum 0.127 mm on F.Cu | @ (133.7, 119.1) |
| error | check.dfm / dfm_trace_width | trace width 0.0100 mm below JLC minimum 0.127 mm on F.Cu | @ (133.7, 119.1) |
| error | check.dfm / dfm_trace_width | trace width 0.0100 mm below JLC minimum 0.127 mm on F.Cu | @ (133.7, 119.2) |
| error | check.dfm / dfm_trace_width | trace width 0.0100 mm below JLC minimum 0.127 mm on F.Cu | @ (133.8, 119.2) |
| error | check.dfm / dfm_trace_width | trace width 0.0100 mm below JLC minimum 0.127 mm on F.Cu | @ (133.9, 119.3) |
| error | check.dfm / dfm_trace_width | trace width 0.0100 mm below JLC minimum 0.127 mm on F.Cu | @ (134.0, 119.4) |
| error | check.dfm / dfm_trace_width | trace width 0.0100 mm below JLC minimum 0.127 mm on F.Cu | @ (134.0, 119.5) |
| error | check.dfm / dfm_trace_width | trace width 0.0100 mm below JLC minimum 0.127 mm on F.Cu | @ (134.1, 119.6) |
| error | check.dfm / dfm_trace_width | trace width 0.0100 mm below JLC minimum 0.127 mm on F.Cu | @ (134.2, 119.6) |

367 more in `runs/thatmicpre/reports/`.

### micro-pico-synth

https://github.com/JordanAceto/micro-pico at `db0dd1ef577c`, `main_pcb/kicad_6/micro_pico.kicad_pcb`, CC-BY-4.0, analog, 4 layers.

verify_all checks: check_creepage skipped, check_current skipped, check_decoupling skipped, check_diffpair pass, check_mating pass, check_pdn skipped, check_ratings skipped, check_return_path skipped, check_route_style violations, check_silk violations, check_thermal skipped

| severity | check | finding | where |
|---|---|---|---|
| error | check_silk / silk_over_pad | silk "SW301" on F.SilkS covers pad ?.2 (0.97 mm2) | ? @ (109.9, 97.5) |
| error | check_silk / silk_over_pad | silk "SW301" on F.SilkS covers pad ?.3 (0.97 mm2) | ? @ (112.4, 97.5) |
| error | check_silk / silk_over_pad | silk "SW301" on F.SilkS covers pad ?.4 (0.97 mm2) | ? @ (114.9, 97.5) |
| error | check_silk / silk_over_pad | silk "hide" on B.SilkS covers pad ?.9 (1.39 mm2) | ? @ (109.9, 115.8) |
| error | check_silk / silk_over_pad | silk "hide" on B.SilkS covers pad ?.10 (1.39 mm2) | ? @ (107.4, 115.8) |
| error | check_silk / silk_over_pad | silk "hide" on B.SilkS covers pad ?.1 (0.68 mm2) | ? @ (97.6, 108.0) |
| error | check_silk / silk_over_pad | silk "hide" on B.SilkS covers pad ?.2 (0.68 mm2) | ? @ (95.9, 108.0) |
| error | check_silk / silk_over_pad | silk "hide" on B.SilkS covers pad ?.2 (0.73 mm2) | ? @ (126.7, 104.1) |
| error | check.dfm / dfm_copper_to_edge | copper 0.2151 mm from board edge, JLC minimum 0.3 mm on F.Cu | @ (196.2, 142.8) |
| error | check.dfm / dfm_copper_to_edge | copper 0.0802 mm from board edge, JLC minimum 0.3 mm on In1.Cu | @ (159.3, 141.4) |
| error | check.dfm / dfm_copper_to_edge | copper 0.2151 mm from board edge, JLC minimum 0.3 mm on In1.Cu | @ (196.2, 142.8) |
| error | check.dfm / dfm_copper_to_edge | copper 0.1858 mm from board edge, JLC minimum 0.3 mm on In2.Cu | @ (160.5, 114.3) |
| error | check.dfm / dfm_copper_to_edge | copper 0.1040 mm from board edge, JLC minimum 0.3 mm on B.Cu | @ (160.3, 132.9) |
| error | check.dfm / dfm_copper_to_edge | copper 0.2151 mm from board edge, JLC minimum 0.3 mm on B.Cu | @ (203.7, 133.7) |
| error | check.dfm / dfm_silk_over_pad | silkscreen printed over a solder-mask opening (2.5438 mm2) on F.Silkscreen - pad of ? | ? @ (80.2, 35.6) |
| error | check.dfm / dfm_silk_over_pad | silkscreen printed over a solder-mask opening (2.5438 mm2) on F.Silkscreen - pad of ? | ? @ (93.9, 35.6) |
| error | check.dfm / dfm_silk_over_pad | silkscreen printed over a solder-mask opening (2.5438 mm2) on F.Silkscreen - pad of ? | ? @ (91.6, 35.6) |
| error | check.dfm / dfm_silk_over_pad | silkscreen printed over a solder-mask opening (2.5438 mm2) on F.Silkscreen - pad of ? | ? @ (88.5, 35.6) |
| error | check.dfm / dfm_silk_over_pad | silkscreen printed over a solder-mask opening (2.5438 mm2) on F.Silkscreen - pad of ? | ? @ (107.6, 35.6) |
| error | check.dfm / dfm_silk_over_pad | silkscreen printed over a solder-mask opening (2.5438 mm2) on F.Silkscreen - pad of ? | ? @ (105.3, 35.6) |
| error | check.dfm / dfm_silk_over_pad | silkscreen printed over a solder-mask opening (2.5438 mm2) on F.Silkscreen - pad of ? | ? @ (102.2, 35.6) |
| error | check.dfm / dfm_silk_over_pad | silkscreen printed over a solder-mask opening (2.5438 mm2) on F.Silkscreen - pad of ? | ? @ (115.9, 35.6) |
| error | check.dfm / dfm_silk_over_pad | silkscreen printed over a solder-mask opening (2.5438 mm2) on F.Silkscreen - pad of ? | ? @ (121.3, 35.6) |
| error | check.dfm / dfm_silk_over_pad | silkscreen printed over a solder-mask opening (2.5438 mm2) on F.Silkscreen - pad of ? | ? @ (119.0, 35.6) |
| error | check.dfm / dfm_silk_over_pad | silkscreen printed over a solder-mask opening (2.5438 mm2) on F.Silkscreen - pad of ? | ? @ (135.0, 35.6) |

99 more in `runs/micro-pico-synth/reports/`.

### current-probe

https://github.com/Qeteshpony/Current-Probe at `a5f5ff8346d7`, `pcb/Current-Probe.kicad_pcb`, BSD-2-Clause, analog, 2 layers.

verify_all checks: check_creepage skipped, check_current skipped, check_decoupling skipped, check_diffpair pass, check_mating pass, check_pdn skipped, check_ratings skipped, check_return_path skipped, check_route_style pass, check_silk violations, check_thermal skipped

| severity | check | finding | where |
|---|---|---|---|
| error | check_silk / silk_over_pad | silk line on F.SilkS covers pad ?.1 (0.38 mm2) | ? @ (146.2, 93.5) |
| error | check_silk / silk_over_pad | silk line on F.SilkS covers pad ?.1 (0.38 mm2) | ? @ (153.8, 93.5) |
| error | check.dfm / dfm_copper_to_edge | copper 0.0005 mm from board edge, JLC minimum 0.3 mm on F.Cu | @ (144.7, 98.8) |
| error | check.dfm / dfm_copper_to_edge | copper 0.0005 mm from board edge, JLC minimum 0.3 mm on F.Cu | @ (158.4, 88.7) |
| error | check.dfm / dfm_copper_to_edge | copper 0.0005 mm from board edge, JLC minimum 0.3 mm on B.Cu | @ (141.7, 88.9) |
| error | check.dfm / dfm_copper_to_edge | copper 0.0005 mm from board edge, JLC minimum 0.3 mm on B.Cu | @ (151.1, 112.2) |
| error | check.dfm / dfm_copper_to_edge | copper 0.0005 mm from board edge, JLC minimum 0.3 mm on B.Cu | @ (158.5, 88.6) |
| error | check.dfm / dfm_annular_ring | annular ring 0.0998 mm below JLC minimum 0.15 mm | @ (145.0, 98.0) |
| error | check.dfm / dfm_annular_ring | annular ring 0.0998 mm below JLC minimum 0.15 mm | @ (145.0, 99.0) |
| error | check.dfm / dfm_annular_ring | annular ring 0.0998 mm below JLC minimum 0.15 mm | @ (145.0, 101.0) |
| error | check.dfm / dfm_annular_ring | annular ring 0.0998 mm below JLC minimum 0.15 mm | @ (145.0, 102.0) |
| error | check.dfm / dfm_annular_ring | annular ring 0.0998 mm below JLC minimum 0.15 mm | @ (146.0, 97.5) |
| error | check.dfm / dfm_annular_ring | annular ring 0.0998 mm below JLC minimum 0.15 mm | @ (146.0, 102.5) |
| error | check.dfm / dfm_annular_ring | annular ring 0.0998 mm below JLC minimum 0.15 mm | @ (148.0, 97.5) |
| error | check.dfm / dfm_annular_ring | annular ring 0.0998 mm below JLC minimum 0.15 mm | @ (149.0, 97.0) |
| error | check.dfm / dfm_annular_ring | annular ring 0.0998 mm below JLC minimum 0.15 mm | @ (151.0, 97.0) |
| error | check.dfm / dfm_annular_ring | annular ring 0.0998 mm below JLC minimum 0.15 mm | @ (151.2, 99.2) |
| error | check.dfm / dfm_annular_ring | annular ring 0.0998 mm below JLC minimum 0.15 mm | @ (151.2, 100.8) |
| error | check.dfm / dfm_annular_ring | annular ring 0.0998 mm below JLC minimum 0.15 mm | @ (151.2, 102.2) |
| error | check.dfm / dfm_annular_ring | annular ring 0.0998 mm below JLC minimum 0.15 mm | @ (151.2, 103.8) |
| error | check.dfm / dfm_annular_ring | annular ring 0.0998 mm below JLC minimum 0.15 mm | @ (152.0, 97.5) |
| error | check.dfm / dfm_annular_ring | annular ring 0.0998 mm below JLC minimum 0.15 mm | @ (154.0, 97.5) |
| error | check.dfm / dfm_annular_ring | annular ring 0.0998 mm below JLC minimum 0.15 mm | @ (154.0, 102.5) |
| error | check.dfm / dfm_annular_ring | annular ring 0.0998 mm below JLC minimum 0.15 mm | @ (155.0, 98.0) |
| error | check.dfm / dfm_annular_ring | annular ring 0.0998 mm below JLC minimum 0.15 mm | @ (155.0, 99.0) |

6 more in `runs/current-probe/reports/`.

### thunderscope

https://github.com/EEVengers/ThunderScope at `bbe8f30e970d`, `Hardware/Thunderscope_Rev5.3/Thunderscope_Rev5.3.kicad_pcb`, MIT, analog, 6 layers.

Outcome: **errata** (Rev 5.3 issues https://github.com/EEVengers/ThunderScope/issues/431 (+3V3_ACQ current draw), /433 (ADC output resistors), /434 (LDO replacement))

verify_all checks: check_creepage skipped, check_current skipped, check_decoupling skipped, check_diffpair pass, check_mating pass, check_pdn skipped, check_ratings skipped, check_return_path skipped, check_route_style violations, check_silk violations, check_thermal skipped

| severity | check | finding | where |
|---|---|---|---|
| error | check_silk / silk_over_pad | silk "TDI" on B.SilkS covers pad TP75.1 (0.48 mm2) | TP75 @ (196.9, 112.0) |
| error | check_silk / silk_over_pad | silk "CLK25" on B.SilkS covers pad TP62.1 (0.78 mm2) | TP62 @ (179.2, 111.8) |
| error | check_silk / silk_over_pad | silk "TERM3" on B.SilkS covers pad TP1014_3.1 (0.78 mm2) | TP1014_3 @ (107.7, 112.1) |
| error | check_silk / silk_over_pad | silk "HWID0" on B.SilkS covers pad TP85.1 (0.78 mm2) | TP85 @ (179.1, 107.3) |
| error | check_silk / silk_over_pad | silk "HWID2" on B.SilkS covers pad TP83.1 (0.78 mm2) | TP83 @ (174.1, 108.0) |
| error | check_silk / silk_over_pad | silk "Your hardware is yours You have the right to modify it - Abortion Rights - Trans Rights - Right to Repair " on B.SilkS covers pad C100 | C1007_1 @ (124.3, 76.7) |
| error | check_silk / silk_over_pad | silk "ACQ_PG" on B.SilkS covers pad TP24.1 (0.78 mm2) | TP24 @ (150.7, 96.6) |
| error | check_silk / silk_over_pad | silk "TRIM2" on B.SilkS covers pad TP1017_2.1 (0.78 mm2) | TP1017_2 @ (132.6, 87.3) |
| error | check_silk / silk_over_pad | silk "QSPI_DQ0" on B.SilkS covers pad TP47.1 (0.78 mm2) | TP47 @ (154.2, 106.2) |
| error | check_silk / silk_over_pad | silk "+5V" on B.SilkS covers pad TP35.1 (0.48 mm2) | TP35 @ (181.5, 70.2) |
| error | check_silk / silk_over_pad | silk "LED_R" on B.SilkS covers pad TP56.1 (0.78 mm2) | TP56 @ (92.2, 110.6) |
| error | check_silk / silk_over_pad | silk "TRIM_SCL_5V" on B.SilkS covers pad TP6.1 (0.78 mm2) | TP6 @ (153.5, 61.4) |
| error | check_silk / silk_over_pad | silk "+VUSB" on B.SilkS covers pad TP71.1 (0.78 mm2) | TP71 @ (194.4, 68.0) |
| error | check_silk / silk_over_pad | silk "TRIM_SDA" on B.SilkS covers pad TP60.1 (0.78 mm2) | TP60 @ (159.5, 68.8) |
| error | check_silk / silk_over_pad | silk "CPL3" on B.SilkS covers pad TP1018_3.1 (0.74 mm2) | TP1018_3 @ (124.9, 113.5) |
| error | check_silk / silk_over_pad | silk "+1V8_R" on B.SilkS covers pad TP63.1 (0.78 mm2) | TP63 @ (149.3, 117.6) |
| error | check_silk / silk_over_pad | silk "+3V3_PGA" on B.SilkS covers pad TP39.1 (0.78 mm2) | TP39 @ (138.2, 72.8) |
| error | check_silk / silk_over_pad | silk "+1V0_R" on B.SilkS covers pad TP65.1 (0.78 mm2) | TP65 @ (180.3, 125.0) |
| error | check_silk / silk_over_pad | silk "PLL_RSTn" on B.SilkS covers pad R45.1 (0.24 mm2) | R45 @ (178.4, 88.9) |
| error | check_silk / silk_over_pad | silk "PLL_RSTn" on B.SilkS covers pad R45.2 (0.18 mm2) | R45 @ (178.4, 88.0) |
| error | check_silk / silk_over_pad | silk "PLL_RSTn" on B.SilkS covers pad TP18.1 (0.78 mm2) | TP18 @ (177.1, 88.5) |
| error | check_silk / silk_over_pad | silk "ADC_CSn" on B.SilkS covers pad TP10.1 (0.78 mm2) | TP10 @ (151.8, 93.0) |
| error | check_silk / silk_over_pad | silk "CPL4" on B.SilkS covers pad TP1018_4.1 (0.74 mm2) | TP1018_4 @ (124.9, 134.0) |
| error | check_silk / silk_over_pad | silk "VARIANT" on B.SilkS covers pad TP82.1 (0.78 mm2) | TP82 @ (172.1, 108.0) |
| error | check_silk / silk_over_pad | silk "-VBIAS" on B.SilkS covers pad TP9.1 (0.78 mm2) | TP9 @ (168.8, 61.9) |

4795 more in `runs/thunderscope/reports/`.

### scan2000

https://github.com/PatrickBaus/SCAN2000 at `41fb4ee67ef8`, `SCAN2000.kicad_pcb`, CERN-OHL-W-2.0, analog, 4 layers.

verify_all checks: check_creepage skipped, check_current skipped, check_decoupling skipped, check_diffpair error, check_mating pass, check_pdn skipped, check_ratings skipped, check_return_path skipped, check_route_style violations, check_silk violations, check_thermal skipped

| severity | check | finding | where |
|---|---|---|---|
| error | check_silk / silk_over_pad | silk "20 CH" on F.SilkS covers pad JP1.3 (0.79 mm2) | JP1 @ (40.0, 77.5) |
| error | check_silk / silk_over_pad | silk "10 CH" on F.SilkS covers pad JP1.1 (0.79 mm2) | JP1 @ (37.4, 77.5) |
| error | check.dfm / dfm_clearance | copper clearance 0.0657 mm below JLC minimum 0.1016 mm on F.Cu | @ (41.4, 53.4) |
| error | check.dfm / dfm_clearance | copper clearance 0.0516 mm below JLC minimum 0.1016 mm on F.Cu | @ (59.8, 45.1) |
| error | check.dfm / dfm_clearance | copper clearance 0.0516 mm below JLC minimum 0.1016 mm on F.Cu | @ (55.8, 45.1) |
| error | check.dfm / dfm_clearance | copper clearance 0.0742 mm below JLC minimum 0.1016 mm on F.Cu | @ (52.4, 51.7) |
| error | check.dfm / dfm_copper_to_edge | copper 0.0255 mm from board edge, JLC minimum 0.3 mm on F.Cu | @ (159.6, 59.6) |
| error | check.dfm / dfm_copper_to_edge | copper 0.0255 mm from board edge, JLC minimum 0.3 mm on In1.Cu | @ (138.1, 60.1) |
| error | check.dfm / dfm_copper_to_edge | copper 0.0255 mm from board edge, JLC minimum 0.3 mm on In2.Cu | @ (172.9, 59.2) |
| error | check.dfm / dfm_copper_to_edge | copper 0.0255 mm from board edge, JLC minimum 0.3 mm on B.Cu | @ (145.5, 60.1) |
| error | check.dfm / dfm_hole_to_hole | hole-to-hole 0.4071 mm below JLC minimum 0.5 mm | @ (53.1, 51.4) |
| error | check.dfm / dfm_hole_to_hole | hole-to-hole 0.4620 mm below JLC minimum 0.5 mm | @ (67.1, 69.3) |
| error | check.dfm / dfm_hole_to_hole | hole-to-hole 0.4620 mm below JLC minimum 0.5 mm | @ (68.5, 74.8) |
| error | check.dfm / dfm_hole_to_hole | hole-to-hole 0.4620 mm below JLC minimum 0.5 mm | @ (75.6, 64.1) |
| error | check.dfm / dfm_annular_ring | annular ring 0.0249 mm below JLC minimum 0.1 mm | @ (30.7, 78.7) |
| error | check.dfm / pad_net_mismatch | J6 pad nets disagree with the schematic (pad 1: board '/Relays/Input/Sense pins/IN.LO16' vs schematic '/Relays/Input{slash}Sense pins/IN.LO1 | J6 @ (109.2, 84.8) |
| error | check.dfm / pad_net_mismatch | J7 pad nets disagree with the schematic (pad 1: board '/Relays/Input/Sense pins/IN.LO11' vs schematic '/Relays/Input{slash}Sense pins/IN.LO1 | J7 @ (161.3, 84.8) |
| error | check.dfm / pad_net_mismatch | J8 pad nets disagree with the schematic (pad 1: board '/Relays/Input/Sense pins/Sense_LOW' vs schematic '/Relays/Input{slash}Sense pins/Sens | J8 @ (193.0, 84.8) |
| error | check.dfm / pad_net_mismatch | R62 pad nets disagree with the schematic (pad 1: board '/Relays/Input/Sense pins/IN.HI11' vs schematic '/Relays/Input{slash}Sense pins/IN.HI | R62 @ (181.6, 79.8) |
| error | check.dfm / pad_net_mismatch | U26 pad nets disagree with the schematic (pad 4: board '/Relays/Input/Sense pins/IN.HI20' vs schematic '/Relays/Input{slash}Sense pins/IN.HI | U26 @ (85.1, 72.4) |
| error | check.dfm / pad_net_mismatch | U27 pad nets disagree with the schematic (pad 4: board '/Relays/Input/Sense pins/IN.LO20' vs schematic '/Relays/Input{slash}Sense pins/IN.LO | U27 @ (90.2, 72.4) |
| error | check.dfm / pad_net_mismatch | U28 pad nets disagree with the schematic (pad 4: board '/Relays/Input/Sense pins/IN.HI19' vs schematic '/Relays/Input{slash}Sense pins/IN.HI | U28 @ (95.2, 72.4) |
| error | check.dfm / pad_net_mismatch | U29 pad nets disagree with the schematic (pad 4: board '/Relays/Input/Sense pins/IN.LO19' vs schematic '/Relays/Input{slash}Sense pins/IN.LO | U29 @ (100.3, 72.4) |
| error | check.dfm / pad_net_mismatch | U30 pad nets disagree with the schematic (pad 4: board '/Relays/Input/Sense pins/IN.HI18' vs schematic '/Relays/Input{slash}Sense pins/IN.HI | U30 @ (105.4, 72.4) |
| error | check.dfm / pad_net_mismatch | U31 pad nets disagree with the schematic (pad 4: board '/Relays/Input/Sense pins/IN.LO18' vs schematic '/Relays/Input{slash}Sense pins/IN.LO | U31 @ (110.5, 72.4) |

75 more in `runs/scan2000/reports/`.

### anthracite-fuzz

https://github.com/trope-oshw/anthracite at `6614992f37ef`, `hardware/bottom/anthracite-bottom.kicad_pcb`, CERN-OHL-S-2.0, analog, 4 layers.

verify_all checks: check_creepage skipped, check_current skipped, check_decoupling skipped, check_diffpair pass, check_mating pass, check_pdn skipped, check_ratings skipped, check_return_path skipped, check_route_style violations, check_silk violations, check_thermal skipped

| severity | check | finding | where |
|---|---|---|---|
| error | check_silk / silk_over_pad | silk "MIDI " on F.SilkS covers pad R136.1 (0.19 mm2) | R136 @ (82.3, 66.8) |
| error | check_silk / silk_over_pad | silk "MIDI " on F.SilkS covers pad R136.2 (0.19 mm2) | R136 @ (83.3, 66.8) |
| error | check_silk / silk_over_pad | silk "Power" on F.SilkS covers pad R102.1 (0.60 mm2) | R102 @ (84.1, 47.0) |
| error | check_silk / silk_over_pad | silk "Power" on F.SilkS covers pad R102.2 (0.60 mm2) | R102 @ (82.4, 47.0) |
| error | check_silk / silk_over_pad | silk "V1.0  CERN-OHL-S-2.0 github.com/trope-oshw/anthracite" on B.SilkS covers pad J103.17 (1.90 mm2) | J103 @ (92.5, 103.8) |
| error | check_silk / silk_over_pad | silk "V1.0  CERN-OHL-S-2.0 github.com/trope-oshw/anthracite" on B.SilkS covers pad J103.18 (1.90 mm2) | J103 @ (90.0, 103.8) |
| error | check_silk / silk_over_pad | silk rect on F.SilkS covers pad SW103.1 (2.43 mm2) | SW103 @ (91.6, 76.8) |
| error | check_silk / silk_over_pad | silk rect on F.SilkS covers pad SW103.2 (2.43 mm2) | SW103 @ (87.4, 76.8) |
| error | check_silk / silk_over_pad | silk rect on F.SilkS covers pad D111.1 (0.79 mm2) | D111 @ (93.3, 66.8) |
| error | check_silk / silk_over_pad | silk rect on F.SilkS covers pad D111.2 (0.79 mm2) | D111 @ (91.7, 66.8) |
| error | check_silk / silk_over_pad | silk rect on F.SilkS covers pad D110.1 (0.79 mm2) | D110 @ (93.3, 71.8) |
| error | check_silk / silk_over_pad | silk rect on F.SilkS covers pad D110.2 (0.79 mm2) | D110 @ (91.7, 71.8) |
| error | check_silk / silk_over_pad | silk rect on F.SilkS covers pad D112.1 (0.79 mm2) | D112 @ (93.3, 69.2) |
| error | check_silk / silk_over_pad | silk rect on F.SilkS covers pad D112.2 (0.79 mm2) | D112 @ (91.7, 69.2) |
| error | check_silk / silk_over_pad | silk rect on F.SilkS covers pad SW103.1 (2.43 mm2) | SW103 @ (91.6, 76.8) |
| error | check_silk / silk_over_pad | silk rect on F.SilkS covers pad SW103.2 (2.43 mm2) | SW103 @ (87.4, 76.8) |
| error | check_silk / silk_over_pad | silk "${Name}" on F.SilkS covers pad R505.1 (0.20 mm2) | R505 @ (66.1, 102.8) |
| error | check_silk / silk_over_pad | silk "${Name}" on F.SilkS covers pad R501.2 (0.27 mm2) | R501 @ (66.2, 107.2) |
| error | check_silk / silk_over_pad | silk "${Name}" on F.SilkS covers pad R801.2 (0.27 mm2) | R801 @ (76.7, 107.2) |
| error | check_silk / silk_over_pad | silk "${Name}" on F.SilkS covers pad R805.1 (0.20 mm2) | R805 @ (76.6, 102.8) |
| error | check_silk / silk_over_pad | silk "${Name}" on F.SilkS covers pad D111.1 (0.66 mm2) | D111 @ (93.3, 66.8) |
| error | check_silk / silk_over_pad | silk "${Name}" on F.SilkS covers pad D111.2 (0.79 mm2) | D111 @ (91.7, 66.8) |
| error | check_silk / silk_over_pad | silk "${Name}" on F.SilkS covers pad R905.1 (0.20 mm2) | R905 @ (80.1, 102.8) |
| error | check_silk / silk_over_pad | silk "${Name}" on F.SilkS covers pad R901.2 (0.27 mm2) | R901 @ (80.2, 107.2) |
| error | check_silk / silk_over_pad | silk "${Name}" on F.SilkS covers pad R1005.1 (0.20 mm2) | R1005 @ (83.6, 102.8) |

98 more in `runs/anthracite-fuzz/reports/`.

### usb2speakon

https://github.com/RainbowLabsDE/USB2Speakon at `69c398a24398`, `USB2Speakon_PCB/USB2Speakon_PCB.kicad_pcb`, CERN-OHL-W-2.0, analog, 4 layers.

verify_all checks: check_creepage skipped, check_current skipped, check_decoupling skipped, check_diffpair pass, check_mating pass, check_pdn skipped, check_ratings skipped, check_return_path skipped, check_route_style violations, check_silk violations, check_thermal skipped

| severity | check | finding | where |
|---|---|---|---|
| error | check_silk / silk_over_pad | silk "C11" on B.SilkS covers pad C10.2 (0.15 mm2) | C10 @ (148.6, 104.7) |
| error | check.dfm / dfm_open_outline | Edge.Cuts present but does not form a closed outline - copper/hole edge-distance checks cannot run |  |
| error | check.dfm / dfm_clearance | copper clearance 0.0793 mm below JLC minimum 0.1016 mm on F.Cu | @ (143.4, 103.7) |
| error | check.dfm / dfm_clearance | copper clearance 0.0793 mm below JLC minimum 0.1016 mm on F.Cu | @ (146.2, 103.8) |
| error | check.dfm / dfm_clearance | copper clearance 0.0889 mm below JLC minimum 0.1016 mm on F.Cu | @ (144.7, 92.9) |
| error | check.dfm / dfm_clearance | copper clearance 0.0918 mm below JLC minimum 0.1016 mm on F.Cu | @ (151.0, 102.7) |
| error | check.dfm / dfm_clearance | copper clearance 0.0889 mm below JLC minimum 0.1016 mm on F.Cu | @ (144.7, 107.8) |
| error | check.dfm / dfm_clearance | copper clearance 0.0940 mm below JLC minimum 0.1016 mm on In1.Cu | @ (141.9, 108.6) |
| error | check.dfm / dfm_clearance | copper clearance 0.0350 mm below JLC minimum 0.1016 mm on In2.Cu | @ (143.1, 90.4) |
| error | check.dfm / dfm_hole_to_hole | hole-to-hole 0.4657 mm below JLC minimum 0.5 mm | @ (149.9, 102.7) |
| error | check.dfm / dfm_hole_to_hole | hole-to-hole 0.3350 mm below JLC minimum 0.5 mm | @ (142.8, 90.4) |
| warning | check_silk / silk_illegible | silk text "JLCJLCJLCJLC" is 0.70 mm tall (< 0.8 mm min legible height) | @ (140.9, 104.8) |
| warning | check_silk / silk_illegible | silk text "-" is 0.70 mm tall (< 0.8 mm min legible height) | @ (137.8, 109.0) |
| warning | check_silk / silk_illegible | silk text "v0.2  LeoDJ" is 0.70 mm tall (< 0.8 mm min legible height) | @ (138.9, 86.6) |
| warning | check_silk / silk_illegible | silk text "CAP" is 0.65 mm tall (< 0.8 mm min legible height) | @ (138.4, 106.6) |
| warning | check_silk / silk_illegible | silk text "L -+" is 0.70 mm tall (< 0.8 mm min legible height) | @ (138.6, 111.7) |
| warning | check_silk / silk_illegible | silk text "USB2Speakon 4W" is 0.70 mm tall (< 0.8 mm min legible height) | @ (149.9, 86.6) |
| warning | check_silk / silk_illegible | silk text "R +-" is 0.70 mm tall (< 0.8 mm min legible height) | @ (151.0, 111.7) |
| warning | check_silk / silk_illegible | silk text "+" is 0.70 mm tall (< 0.8 mm min legible height) | @ (137.7, 104.1) |
| warning | check_silk / silk_illegible | silk text "R9" is 0.70 mm tall (< 0.8 mm min legible height) | @ (150.0, 103.7) |
| warning | check_silk / silk_illegible | silk text "C5" is 0.70 mm tall (< 0.8 mm min legible height) | @ (147.5, 96.7) |
| warning | check_silk / silk_illegible | silk text "C17" is 0.70 mm tall (< 0.8 mm min legible height) | @ (145.3, 96.0) |
| warning | check_silk / silk_illegible | silk text "U2" is 0.70 mm tall (< 0.8 mm min legible height) | @ (147.8, 107.1) |
| warning | check_silk / silk_illegible | silk text "C22" is 0.70 mm tall (< 0.8 mm min legible height) | @ (140.6, 107.6) |
| warning | check_silk / silk_illegible | silk text "C24" is 0.70 mm tall (< 0.8 mm min legible height) | @ (151.0, 105.8) |

61 more in `runs/usb2speakon/reports/`.

### nodepilot

https://github.com/tushroy/NodePilot at `3dc6193e7c2d`, `NodePilot.kicad_pcb`, CC-BY-SA-4.0, analog, 2 layers.

verify_all checks: check_creepage skipped, check_current skipped, check_decoupling skipped, check_diffpair pass, check_mating pass, check_pdn skipped, check_ratings skipped, check_return_path skipped, check_route_style pass, check_silk violations, check_thermal skipped

| severity | check | finding | where |
|---|---|---|---|
| warning | check_silk / silk_misattributed | refdes "T1" sits 1.03 mm beyond its own pads and 0.00 mm from  - reads as 's label; scripted fix: place_edit.py move_text | T1 @ (167.5, 88.7) |
| warning | check_silk / silk_misattributed | refdes "C3" sits 1.12 mm beyond its own pads and 0.00 mm from  - reads as 's label; scripted fix: place_edit.py move_text | C3 @ (187.5, 71.0) |
| warning | check_silk / silk_misattributed | refdes "T2" sits 1.03 mm beyond its own pads and 0.00 mm from  - reads as 's label; scripted fix: place_edit.py move_text | T2 @ (167.5, 70.3) |
| warning | check_silk / silk_misattributed | refdes "C2" sits 2.07 mm beyond its own pads and 0.00 mm from  - reads as 's label; scripted fix: place_edit.py move_text | C2 @ (162.2, 71.8) |
| warning | check_silk / silk_misattributed | refdes "RV1" sits 2.37 mm beyond its own pads and 0.00 mm from  - reads as 's label; scripted fix: place_edit.py move_text | RV1 @ (183.4, 69.5) |
| warning | check_silk / silk_misattributed | refdes "RV2" sits 2.06 mm beyond its own pads and 0.00 mm from  - reads as 's label; scripted fix: place_edit.py move_text | RV2 @ (183.4, 92.3) |
| warning | check_silk / silk_misattributed | refdes "C1" sits 1.32 mm beyond its own pads and 0.00 mm from  - reads as 's label; scripted fix: place_edit.py move_text | C1 @ (152.0, 97.0) |
| warning | check.dfm / dfm_silk_width | 2129 silk strokes below JLC minimum width 0.15 mm (narrowest 0.0100 mm) on F.Silkscreen | @ (144.8, 117.2) |

### moco

https://github.com/ziteh/moco at `e0caae5762ac`, `hardware/moco-bkd8316/moco-bkd8316.kicad_pcb`, CERN-OHL-P-2.0, motor, 2 layers.

verify_all checks: check_creepage skipped, check_current skipped, check_decoupling skipped, check_diffpair pass, check_mating pass, check_pdn skipped, check_ratings skipped, check_return_path skipped, check_route_style pass, check_silk violations, check_thermal skipped

| severity | check | finding | where |
|---|---|---|---|
| error | check_silk / silk_over_pad | silk "-" on F.SilkS covers pad ?.1 (0.20 mm2) | ? @ (141.8, 125.8) |
| error | check_silk / silk_over_pad | silk "${TITLE}" on F.SilkS covers pad ?.3 (1.14 mm2) | ? @ (133.8, 101.1) |
| error | check_silk / silk_over_pad | silk "v${REVISION}" on F.SilkS covers pad ?.5 (1.64 mm2) | ? @ (133.8, 103.7) |
| error | check_silk / silk_over_pad | silk "hide" on F.SilkS covers pad ?.1 (0.38 mm2) | ? @ (151.2, 95.7) |
| error | check_silk / silk_over_pad | silk "~{SLEEP}" on F.SilkS covers pad ?.1 (0.58 mm2) | ? @ (151.2, 95.7) |
| error | check.dfm / dfm_hole_to_hole | hole-to-hole 0.4000 mm below JLC minimum 0.5 mm | @ (148.4, 122.1) |
| error | check.dfm / dfm_hole_to_hole | hole-to-hole 0.4500 mm below JLC minimum 0.5 mm | @ (148.7, 117.8) |
| error | check.dfm / dfm_hole_to_hole | hole-to-hole 0.4500 mm below JLC minimum 0.5 mm | @ (148.7, 118.5) |
| error | check.dfm / dfm_hole_to_hole | hole-to-hole 0.4500 mm below JLC minimum 0.5 mm | @ (148.7, 119.2) |
| error | check.dfm / dfm_hole_to_hole | hole-to-hole 0.4500 mm below JLC minimum 0.5 mm | @ (148.7, 120.0) |
| error | check.dfm / dfm_hole_to_hole | hole-to-hole 0.4500 mm below JLC minimum 0.5 mm | @ (149.2, 121.5) |
| error | check.dfm / dfm_hole_to_hole | hole-to-hole 0.4500 mm below JLC minimum 0.5 mm | @ (150.0, 121.5) |
| error | check.dfm / dfm_hole_to_hole | hole-to-hole 0.4500 mm below JLC minimum 0.5 mm | @ (150.8, 117.0) |
| error | check.dfm / dfm_hole_to_hole | hole-to-hole 0.4500 mm below JLC minimum 0.5 mm | @ (150.8, 117.8) |
| error | check.dfm / dfm_hole_to_hole | hole-to-hole 0.4500 mm below JLC minimum 0.5 mm | @ (150.8, 118.5) |
| error | check.dfm / dfm_hole_to_hole | hole-to-hole 0.4500 mm below JLC minimum 0.5 mm | @ (150.8, 119.2) |
| error | check.dfm / dfm_hole_to_hole | hole-to-hole 0.4500 mm below JLC minimum 0.5 mm | @ (150.8, 120.0) |
| error | check.dfm / dfm_hole_to_hole | hole-to-hole 0.4500 mm below JLC minimum 0.5 mm | @ (150.8, 120.8) |
| error | check.dfm / dfm_hole_to_hole | hole-to-hole 0.4500 mm below JLC minimum 0.5 mm | @ (150.8, 121.5) |
| error | check.dfm / dfm_hole_to_hole | hole-to-hole 0.4500 mm below JLC minimum 0.5 mm | @ (151.5, 121.5) |
| error | check.dfm / dfm_hole_to_hole | hole-to-hole 0.4500 mm below JLC minimum 0.5 mm | @ (152.8, 117.8) |
| error | check.dfm / dfm_hole_to_hole | hole-to-hole 0.4500 mm below JLC minimum 0.5 mm | @ (152.8, 118.5) |
| error | check.dfm / dfm_hole_to_hole | hole-to-hole 0.4500 mm below JLC minimum 0.5 mm | @ (152.8, 119.3) |
| error | check.dfm / dfm_hole_to_hole | hole-to-hole 0.4500 mm below JLC minimum 0.5 mm | @ (152.8, 120.0) |
| error | check.dfm / dfm_hole_to_hole | hole-to-hole 0.2500 mm below JLC minimum 0.5 mm | @ (146.1, 126.3) |

122 more in `runs/moco/reports/`.

### moco-rd501

https://github.com/ziteh/moco at `e0caae5762ac`, `hardware/moco-rd501/moco-rd501.kicad_pcb`, CERN-OHL-P-2.0, motor, 4 layers.

verify_all checks: check_creepage skipped, check_current skipped, check_decoupling skipped, check_diffpair pass, check_mating pass, check_pdn skipped, check_ratings skipped, check_return_path skipped, check_route_style violations, check_silk violations, check_thermal skipped

| severity | check | finding | where |
|---|---|---|---|
| error | check_silk / silk_over_pad | silk "3.3V" on B.SilkS covers pad ?.1 (1.52 mm2) | ? @ (129.9, 98.2) |
| error | check_silk / silk_over_pad | silk "R8" on F.SilkS covers pad ?.1 (0.33 mm2) | ? @ (108.5, 97.2) |
| error | check_silk / silk_over_pad | silk "R8" on F.SilkS covers pad ?.2 (0.33 mm2) | ? @ (109.5, 97.2) |
| error | check.dfm / dfm_clearance | copper clearance 0.0814 mm below JLC minimum 0.1016 mm on F.Cu | @ (112.5, 96.9) |
| error | check.dfm / dfm_clearance | copper clearance 0.0203 mm below JLC minimum 0.1016 mm on In1.Cu | @ (146.3, 73.1) |
| error | check.dfm / dfm_clearance | copper clearance 0.0204 mm below JLC minimum 0.1016 mm on In1.Cu | @ (145.6, 73.7) |
| error | check.dfm / dfm_clearance | copper clearance 0.0200 mm below JLC minimum 0.1016 mm on In1.Cu | @ (145.3, 74.5) |
| error | check.dfm / dfm_clearance | copper clearance 0.0203 mm below JLC minimum 0.1016 mm on In1.Cu | @ (147.2, 73.2) |
| error | check.dfm / dfm_clearance | copper clearance 0.0204 mm below JLC minimum 0.1016 mm on In1.Cu | @ (147.9, 73.7) |
| error | check.dfm / dfm_clearance | copper clearance 0.0200 mm below JLC minimum 0.1016 mm on In1.Cu | @ (148.2, 74.5) |
| error | check.dfm / dfm_clearance | copper clearance 0.0204 mm below JLC minimum 0.1016 mm on In1.Cu | @ (147.9, 75.3) |
| error | check.dfm / dfm_clearance | copper clearance 0.0204 mm below JLC minimum 0.1016 mm on In1.Cu | @ (145.6, 77.2) |
| error | check.dfm / dfm_clearance | copper clearance 0.0200 mm below JLC minimum 0.1016 mm on In1.Cu | @ (145.3, 78.0) |
| error | check.dfm / dfm_clearance | copper clearance 0.0204 mm below JLC minimum 0.1016 mm on In1.Cu | @ (147.9, 77.2) |
| error | check.dfm / dfm_clearance | copper clearance 0.0200 mm below JLC minimum 0.1016 mm on In1.Cu | @ (148.2, 78.0) |
| error | check.dfm / dfm_clearance | copper clearance 0.0204 mm below JLC minimum 0.1016 mm on In1.Cu | @ (145.6, 78.8) |
| error | check.dfm / dfm_clearance | copper clearance 0.0204 mm below JLC minimum 0.1016 mm on In1.Cu | @ (147.9, 78.8) |
| error | check.dfm / dfm_clearance | copper clearance 0.0200 mm below JLC minimum 0.1016 mm on In1.Cu | @ (145.3, 81.5) |
| error | check.dfm / dfm_clearance | copper clearance 0.0204 mm below JLC minimum 0.1016 mm on In1.Cu | @ (145.6, 82.3) |
| error | check.dfm / dfm_clearance | copper clearance 0.0203 mm below JLC minimum 0.1016 mm on In1.Cu | @ (146.3, 82.8) |
| error | check.dfm / dfm_clearance | copper clearance 0.0204 mm below JLC minimum 0.1016 mm on In1.Cu | @ (147.9, 80.7) |
| error | check.dfm / dfm_clearance | copper clearance 0.0200 mm below JLC minimum 0.1016 mm on In1.Cu | @ (148.2, 81.5) |
| error | check.dfm / dfm_clearance | copper clearance 0.0204 mm below JLC minimum 0.1016 mm on In1.Cu | @ (147.9, 82.3) |
| error | check.dfm / dfm_clearance | copper clearance 0.0203 mm below JLC minimum 0.1016 mm on In1.Cu | @ (147.2, 82.8) |
| error | check.dfm / dfm_clearance | copper clearance 0.0203 mm below JLC minimum 0.1016 mm on In2.Cu | @ (146.3, 73.1) |

120 more in `runs/moco-rd501/reports/`.

### mini-motor-controller

https://github.com/Jana-Marie/mini-motor-controller at `d8c1c296229c`, `mini-motor-controller.kicad_pcb`, CERN-OHL-S-2.0, motor, 2 layers.

verify_all checks: check_creepage skipped, check_current skipped, check_decoupling skipped, check_diffpair pass, check_mating violations, check_pdn skipped, check_ratings skipped, check_return_path skipped, check_route_style violations, check_silk violations, check_thermal skipped

| severity | check | finding | where |
|---|---|---|---|
| error | check_silk / silk_over_pad | silk "VIN SCL SDA GND INPUT" on F.SilkS covers pad J1.MP (1.15 mm2) | J1 @ (77.5, 77.6) |
| error | check_silk / silk_over_pad | silk "VIN SCL SDA GND INPUT" on F.SilkS covers pad J1.MP (1.15 mm2) | J1 @ (77.5, 86.4) |
| error | check_mating / mating_zone_blocked | J2 (wire_to_board_side): J3 sit in the plug's insertion zone in front of its mouth (12.0 mm plug + 3.0 mm grip) | J2, J3 @ (110.5, 94.0) |
| error | check_mating / mating_faces_inward | J4 (wire_to_board_side) cannot be mated: its nearest edge is -y (1.0 mm) but its mouth faces +x, into 3.7 mm of board | J4 @ (96.0, 82.0) |
| error | check_mating / mating_zone_blocked | J4 (wire_to_board_side): J3 sit in the plug's insertion zone in front of its mouth (12.0 mm plug + 3.0 mm grip) | J3, J4 @ (109.3, 82.0) |
| error | check.dfm / dfm_clearance | copper clearance 0.1060 mm below JLC minimum 0.127 mm on F.Cu | @ (90.3, 78.3) |
| error | check.dfm / dfm_copper_to_edge | copper 0.2000 mm from board edge, JLC minimum 0.3 mm on F.Cu | @ (77.9, 82.5) |
| error | check.dfm / dfm_copper_to_edge | copper 0.2500 mm from board edge, JLC minimum 0.3 mm on F.Cu | @ (80.0, 94.3) |
| error | check.dfm / dfm_copper_to_edge | copper 0.2000 mm from board edge, JLC minimum 0.3 mm on F.Cu | @ (77.6, 98.0) |
| error | check.dfm / dfm_copper_to_edge | copper 0.2000 mm from board edge, JLC minimum 0.3 mm on F.Cu | @ (97.9, 87.4) |
| error | check.dfm / dfm_copper_to_edge | copper 0.2000 mm from board edge, JLC minimum 0.3 mm on B.Cu | @ (89.3, 87.1) |
| error | check.dfm / dfm_hole_size | drill 0.2000 mm below JLC minimum 0.3 mm | @ (75.6, 94.9) |
| error | check.dfm / dfm_hole_size | drill 0.2000 mm below JLC minimum 0.3 mm | @ (76.3, 85.7) |
| error | check.dfm / dfm_hole_size | drill 0.2000 mm below JLC minimum 0.3 mm | @ (76.3, 87.2) |
| error | check.dfm / dfm_hole_size | drill 0.2000 mm below JLC minimum 0.3 mm | @ (76.3, 76.8) |
| error | check.dfm / dfm_hole_size | drill 0.2000 mm below JLC minimum 0.3 mm | @ (76.3, 78.3) |
| error | check.dfm / dfm_hole_size | drill 0.2000 mm below JLC minimum 0.3 mm | @ (76.3, 94.0) |
| error | check.dfm / dfm_hole_size | drill 0.2000 mm below JLC minimum 0.3 mm | @ (76.6, 89.5) |
| error | check.dfm / dfm_hole_size | drill 0.2000 mm below JLC minimum 0.3 mm | @ (76.6, 92.5) |
| error | check.dfm / dfm_hole_size | drill 0.2000 mm below JLC minimum 0.3 mm | @ (76.7, 91.0) |
| error | check.dfm / dfm_hole_size | drill 0.2000 mm below JLC minimum 0.3 mm | @ (77.1, 96.0) |
| error | check.dfm / dfm_hole_size | drill 0.2000 mm below JLC minimum 0.3 mm | @ (77.4, 92.9) |
| error | check.dfm / dfm_hole_size | drill 0.2000 mm below JLC minimum 0.3 mm | @ (78.7, 85.7) |
| error | check.dfm / dfm_hole_size | drill 0.2000 mm below JLC minimum 0.3 mm | @ (78.7, 87.2) |
| error | check.dfm / dfm_hole_size | drill 0.2000 mm below JLC minimum 0.3 mm | @ (78.8, 76.8) |

350 more in `runs/mini-motor-controller/reports/`.

### bt-dc-motor-board

https://github.com/VinnyCordeiro/BT_DC_motor_board at `b8736f8c4bbb`, `BoxTurtle_DC_motors_RPiPico.kicad_pcb`, CERN-OHL-S-2.0, motor, 4 layers.

verify_all checks: check_creepage skipped, check_current skipped, check_decoupling skipped, check_diffpair pass, check_mating pass, check_pdn skipped, check_ratings skipped, check_return_path skipped, check_route_style violations, check_silk violations, check_thermal skipped

| severity | check | finding | where |
|---|---|---|---|
| error | check_silk / silk_over_pad | silk "BoxTurtle DC motors standalone board Rev 2.6.4" on B.SilkS covers pad U1.14 (2.09 mm2) | U1 @ (173.4, 78.7) |
| error | check_silk / silk_over_pad | silk "BoxTurtle DC motors standalone board Rev 2.6.4" on B.SilkS covers pad U1.27 (2.09 mm2) | U1 @ (191.1, 78.7) |
| error | check_silk / silk_over_pad | silk "BoxTurtle DC motors standalone board Rev 2.6.4" on B.SilkS covers pad U2.14 (1.82 mm2) | U2 @ (170.8, 78.7) |
| error | check_silk / silk_over_pad | silk "BoxTurtle DC motors standalone board Rev 2.6.4" on B.SilkS covers pad U2.27 (1.82 mm2) | U2 @ (186.1, 78.7) |
| error | check_silk / silk_over_pad | silk rect on F.SilkS covers pad U1.1 (2.09 mm2) | U1 @ (173.4, 45.7) |
| error | check_silk / silk_over_pad | silk rect on F.SilkS covers pad U1.2 (2.09 mm2) | U1 @ (173.4, 48.3) |
| error | check_silk / silk_over_pad | silk rect on F.SilkS covers pad U1.3 (2.09 mm2) | U1 @ (173.4, 50.8) |
| error | check_silk / silk_over_pad | silk rect on F.SilkS covers pad U1.4 (2.09 mm2) | U1 @ (173.4, 53.3) |
| error | check_silk / silk_over_pad | silk rect on F.SilkS covers pad U1.5 (2.09 mm2) | U1 @ (173.4, 55.9) |
| error | check_silk / silk_over_pad | silk rect on F.SilkS covers pad U1.6 (2.09 mm2) | U1 @ (173.4, 58.4) |
| error | check_silk / silk_over_pad | silk rect on F.SilkS covers pad U1.7 (2.09 mm2) | U1 @ (173.4, 61.0) |
| error | check_silk / silk_over_pad | silk rect on F.SilkS covers pad U1.8 (2.09 mm2) | U1 @ (173.4, 63.5) |
| error | check_silk / silk_over_pad | silk rect on F.SilkS covers pad U1.9 (2.09 mm2) | U1 @ (173.4, 66.0) |
| error | check_silk / silk_over_pad | silk rect on F.SilkS covers pad U1.10 (2.09 mm2) | U1 @ (173.4, 68.6) |
| error | check_silk / silk_over_pad | silk rect on F.SilkS covers pad U1.11 (2.09 mm2) | U1 @ (173.4, 71.1) |
| error | check_silk / silk_over_pad | silk rect on F.SilkS covers pad U1.12 (2.09 mm2) | U1 @ (173.4, 73.7) |
| error | check_silk / silk_over_pad | silk rect on F.SilkS covers pad U1.13 (2.09 mm2) | U1 @ (173.4, 76.2) |
| error | check_silk / silk_over_pad | silk rect on F.SilkS covers pad U1.14 (2.09 mm2) | U1 @ (173.4, 78.7) |
| error | check_silk / silk_over_pad | silk rect on F.SilkS covers pad U1.15 (2.09 mm2) | U1 @ (173.4, 81.3) |
| error | check_silk / silk_over_pad | silk rect on F.SilkS covers pad U1.16 (2.09 mm2) | U1 @ (173.4, 83.8) |
| error | check_silk / silk_over_pad | silk rect on F.SilkS covers pad U1.17 (2.09 mm2) | U1 @ (173.4, 86.4) |
| error | check_silk / silk_over_pad | silk rect on F.SilkS covers pad U1.18 (2.09 mm2) | U1 @ (173.4, 88.9) |
| error | check_silk / silk_over_pad | silk rect on F.SilkS covers pad U1.19 (2.09 mm2) | U1 @ (173.4, 91.4) |
| error | check_silk / silk_over_pad | silk rect on F.SilkS covers pad U1.20 (2.09 mm2) | U1 @ (173.4, 94.0) |
| error | check_silk / silk_over_pad | silk rect on F.SilkS covers pad U2.1 (2.09 mm2) | U2 @ (170.8, 45.7) |

55 more in `runs/bt-dc-motor-board/reports/`.

### openesc-30x30

https://github.com/OpenDrone-hw/OpenESC-30x30 at `682268f901f6`, `hardware/4in1.kicad_pcb`, CERN-OHL-S-2.0, motor, 6 layers.

verify_all checks: check_creepage skipped, check_current skipped, check_decoupling skipped, check_diffpair pass, check_mating pass, check_pdn skipped, check_ratings skipped, check_return_path skipped, check_route_style violations, check_silk violations, check_thermal skipped

| severity | check | finding | where |
|---|---|---|---|
| error | check_silk / silk_over_pad | silk "+ - C X 1 2 3 4" on F.SilkS covers pad Q19.1 (0.59 mm2) | Q19 @ (64.0, 30.4) |
| error | check_silk / silk_over_pad | silk "+ - C X 1 2 3 4" on F.SilkS covers pad Q19.1 (0.63 mm2) | Q19 @ (64.0, 31.6) |
| error | check_silk / silk_over_pad | silk "+ - C X 1 2 3 4" on F.SilkS covers pad Q19.1 (0.51 mm2) | Q19 @ (64.0, 32.9) |
| error | check_silk / silk_over_pad | silk "+ - C X 1 2 3 4" on F.SilkS covers pad Q19.3 (0.60 mm2) | Q19 @ (69.7, 30.4) |
| error | check_silk / silk_over_pad | silk "+ - C X 1 2 3 4" on F.SilkS covers pad Q19.3 (0.63 mm2) | Q19 @ (69.7, 31.6) |
| error | check_silk / silk_over_pad | silk "+ - C X 1 2 3 4" on F.SilkS covers pad Q19.3 (12.22 mm2) | Q19 @ (67.6, 32.3) |
| error | check_silk / silk_over_pad | silk "+ - C X 1 2 3 4" on F.SilkS covers pad Q19.3 (0.50 mm2) | Q19 @ (69.7, 32.9) |
| error | check_silk / silk_over_pad | silk "+ - C X 1 2 3 4" on F.SilkS covers pad Q17.3 (0.57 mm2) | Q17 @ (81.6, 32.9) |
| error | check_silk / silk_over_pad | silk "+ - C X 1 2 3 4" on F.SilkS covers pad Q17.3 (6.66 mm2) | Q17 @ (83.8, 32.2) |
| error | check_silk / silk_over_pad | silk "+ - C X 1 2 3 4" on F.SilkS covers pad Q17.3 (0.63 mm2) | Q17 @ (81.6, 31.6) |
| error | check_silk / silk_over_pad | silk "+ - C X 1 2 3 4" on F.SilkS covers pad Q17.3 (0.55 mm2) | Q17 @ (81.6, 30.3) |
| error | check_silk / silk_over_pad | silk "+ - C X 1 2 3 4" on F.SilkS covers pad U3.11 (11.54 mm2) | U3 @ (60.4, 32.1) |
| error | check_silk / silk_over_pad | silk "2" on F.SilkS covers pad Q17.1 (0.41 mm2) | Q17 @ (87.3, 31.6) |
| error | check_silk / silk_over_pad | silk "2" on F.SilkS covers pad Q17.2 (0.41 mm2) | Q17 @ (87.3, 30.3) |
| error | check_silk / silk_over_pad | silk "4 3 2 1   C - +" on B.SilkS covers pad TP7.1 (0.76 mm2) | TP7 @ (70.9, 36.9) |
| error | check_silk / silk_over_pad | silk "4 3 2 1   C - +" on B.SilkS covers pad R36.1 (0.18 mm2) | R36 @ (81.1, 36.2) |
| error | check_silk / silk_over_pad | silk "4 3 2 1   C - +" on B.SilkS covers pad R36.2 (0.18 mm2) | R36 @ (81.1, 36.8) |
| error | check_silk / silk_over_pad | silk "4 3 2 1   C - +" on B.SilkS covers pad C35.2 (0.18 mm2) | C35 @ (67.8, 37.3) |
| error | check_silk / silk_over_pad | silk "4 3 2 1   C - +" on B.SilkS covers pad R79.1 (0.18 mm2) | R79 @ (69.1, 36.5) |
| error | check_silk / silk_over_pad | silk "4 3 2 1   C - +" on B.SilkS covers pad R79.2 (0.18 mm2) | R79 @ (68.4, 36.5) |
| error | check_silk / silk_over_pad | silk "4 3 2 1   C - +" on B.SilkS covers pad Q12.1 (0.45 mm2) | Q12 @ (89.0, 37.2) |
| error | check_silk / silk_over_pad | silk "4 3 2 1   C - +" on B.SilkS covers pad Q12.2 (0.63 mm2) | Q12 @ (89.0, 36.0) |
| error | check_silk / silk_over_pad | silk "4 3 2 1   C - +" on B.SilkS covers pad R10.1 (0.18 mm2) | R10 @ (76.2, 37.0) |
| error | check_silk / silk_over_pad | silk "4 3 2 1   C - +" on B.SilkS covers pad R10.2 (0.18 mm2) | R10 @ (76.8, 37.0) |
| error | check_silk / silk_over_pad | silk "4 3 2 1   C - +" on B.SilkS covers pad R13.1 (0.18 mm2) | R13 @ (78.7, 36.1) |

6002 more in `runs/openesc-30x30/reports/`.

### mighty-micro-motors

https://github.com/techy-robot/Mighty-Micro-Motors at `8bfaabd3ca5a`, `Kicad/DRV8311 on motor driver/DRV8311 on motor driver.kicad_pcb`, CERN-OHL-S-2.0, motor, 4 layers.

verify_all checks: check_creepage skipped, check_current skipped, check_decoupling skipped, check_diffpair pass, check_mating pass, check_pdn skipped, check_ratings skipped, check_return_path skipped, check_route_style violations, check_silk violations, check_thermal skipped

| severity | check | finding | where |
|---|---|---|---|
| error | check_silk / silk_over_pad | silk "+" on B.SilkS covers pad C4.1 (0.26 mm2) | C4 @ (172.4, 96.3) |
| error | check_silk / silk_over_pad | silk "-" on F.SilkS covers pad C2.2 (0.21 mm2) | C2 @ (169.9, 96.5) |
| error | check_silk / silk_over_pad | silk "J3" on F.SilkS covers pad J1.1 (0.61 mm2) | J1 @ (166.9, 102.3) |
| error | check_silk / silk_over_pad | silk "J1" on F.SilkS covers pad J2.1 (0.78 mm2) | J2 @ (166.6, 101.1) |
| error | check.dfm / dfm_clearance | copper clearance 0.0633 mm below JLC minimum 0.1016 mm on F.Cu | @ (173.4, 102.7) |
| error | check.dfm / dfm_clearance | copper clearance 0.0633 mm below JLC minimum 0.1016 mm on B.Cu | @ (170.2, 100.2) |
| error | check.dfm / dfm_copper_to_edge | copper 0.1997 mm from board edge, JLC minimum 0.3 mm on F.Cu | @ (172.9, 97.0) |
| error | check.dfm / dfm_copper_to_edge | copper 0.2003 mm from board edge, JLC minimum 0.3 mm on F.Cu | @ (168.0, 98.6) |
| error | check.dfm / dfm_copper_to_edge | copper 0.2537 mm from board edge, JLC minimum 0.3 mm on F.Cu | @ (167.6, 100.9) |
| error | check.dfm / dfm_copper_to_edge | copper 0.2024 mm from board edge, JLC minimum 0.3 mm on F.Cu | @ (167.8, 101.9) |
| error | check.dfm / dfm_copper_to_edge | copper 0.2284 mm from board edge, JLC minimum 0.3 mm on F.Cu | @ (168.4, 102.7) |
| error | check.dfm / dfm_copper_to_edge | copper 0.2004 mm from board edge, JLC minimum 0.3 mm on F.Cu | @ (169.5, 104.9) |
| error | check.dfm / dfm_copper_to_edge | copper 0.2141 mm from board edge, JLC minimum 0.3 mm on F.Cu | @ (171.6, 104.3) |
| error | check.dfm / dfm_copper_to_edge | copper 0.2421 mm from board edge, JLC minimum 0.3 mm on F.Cu | @ (174.2, 102.1) |
| error | check.dfm / dfm_copper_to_edge | copper 0.2006 mm from board edge, JLC minimum 0.3 mm on F.Cu | @ (176.2, 99.7) |
| error | check.dfm / dfm_copper_to_edge | copper 0.2025 mm from board edge, JLC minimum 0.3 mm on F.Cu | @ (175.4, 102.9) |
| error | check.dfm / dfm_copper_to_edge | copper 0.1996 mm from board edge, JLC minimum 0.3 mm on F.Cu | @ (174.1, 104.6) |
| error | check.dfm / dfm_copper_to_edge | copper 0.1997 mm from board edge, JLC minimum 0.3 mm on In1.Cu | @ (171.6, 100.5) |
| error | check.dfm / dfm_copper_to_edge | copper 0.2871 mm from board edge, JLC minimum 0.3 mm on In1.Cu | @ (166.7, 98.8) |
| error | check.dfm / dfm_copper_to_edge | copper 0.2537 mm from board edge, JLC minimum 0.3 mm on In1.Cu | @ (166.6, 101.1) |
| error | check.dfm / dfm_copper_to_edge | copper 0.2024 mm from board edge, JLC minimum 0.3 mm on In1.Cu | @ (166.9, 102.3) |
| error | check.dfm / dfm_copper_to_edge | copper 0.2284 mm from board edge, JLC minimum 0.3 mm on In1.Cu | @ (167.6, 103.5) |
| error | check.dfm / dfm_copper_to_edge | copper 0.2006 mm from board edge, JLC minimum 0.3 mm on In1.Cu | @ (176.2, 99.7) |
| error | check.dfm / dfm_copper_to_edge | copper 0.2025 mm from board edge, JLC minimum 0.3 mm on In1.Cu | @ (175.2, 103.6) |
| error | check.dfm / dfm_copper_to_edge | copper 0.1996 mm from board edge, JLC minimum 0.3 mm on In1.Cu | @ (174.1, 104.6) |

51 more in `runs/mighty-micro-motors/reports/`.

### rf-prototype-boards

https://github.com/maelh/radio-frequency-prototype-boards at `9814f4fe2385`, `RF_ProtoBoard/RF_ProtoBoard.kicad_pcb`, BSD-3-Clause, rf, 2 layers.

verify_all checks: check_creepage skipped, check_current skipped, check_decoupling skipped, check_diffpair pass, check_mating pass, check_pdn skipped, check_ratings skipped, check_return_path skipped, check_route_style pass, check_silk pass, check_thermal skipped

| severity | check | finding | where |
|---|---|---|---|
| error | check.dfm / dfm_silk_over_pad | silkscreen printed over a solder-mask opening (0.3093 mm2) on B.Silkscreen | @ (103.8, 49.5) |
| error | check.dfm / dfm_silk_over_pad | silkscreen printed over a solder-mask opening (0.3093 mm2) on B.Silkscreen | @ (106.4, 49.5) |
| error | check.dfm / dfm_silk_over_pad | silkscreen printed over a solder-mask opening (0.2044 mm2) on B.Silkscreen | @ (105.1, 49.4) |
| error | check.dfm / dfm_silk_over_pad | silkscreen printed over a solder-mask opening (0.2379 mm2) on B.Silkscreen | @ (104.6, 49.5) |
| error | check.dfm / dfm_silk_over_pad | silkscreen printed over a solder-mask opening (0.3093 mm2) on B.Silkscreen | @ (109.0, 49.5) |
| error | check.dfm / dfm_silk_over_pad | silkscreen printed over a solder-mask opening (0.2044 mm2) on B.Silkscreen | @ (107.6, 49.4) |
| error | check.dfm / dfm_silk_over_pad | silkscreen printed over a solder-mask opening (0.2379 mm2) on B.Silkscreen | @ (107.2, 49.5) |
| error | check.dfm / dfm_silk_over_pad | silkscreen printed over a solder-mask opening (0.2379 mm2) on B.Silkscreen | @ (109.7, 49.5) |
| error | check.dfm / dfm_silk_over_pad | silkscreen printed over a solder-mask opening (0.3093 mm2) on B.Silkscreen | @ (111.6, 49.5) |
| error | check.dfm / dfm_silk_over_pad | silkscreen printed over a solder-mask opening (0.2044 mm2) on B.Silkscreen | @ (110.2, 49.4) |
| error | check.dfm / dfm_silk_over_pad | silkscreen printed over a solder-mask opening (0.2044 mm2) on B.Silkscreen | @ (112.8, 49.4) |
| error | check.dfm / dfm_silk_over_pad | silkscreen printed over a solder-mask opening (0.2379 mm2) on B.Silkscreen | @ (112.3, 49.5) |

### mountaineer

https://github.com/k0swe/mountaineer at `0555552a2d3e`, `mountaineer.kicad_pcb`, CC-BY-4.0, rf, 2 layers.

verify_all checks: check_creepage skipped, check_current skipped, check_decoupling skipped, check_diffpair violations, check_mating pass, check_pdn skipped, check_ratings skipped, check_return_path skipped, check_route_style violations, check_silk violations, check_thermal skipped

| severity | check | finding | where |
|---|---|---|---|
| error | check_silk / silk_over_pad | silk "hide" on F.SilkS covers pad ?.1 (2.32 mm2) | ? @ (126.5, 97.0) |
| error | check_silk / silk_over_pad | silk "hide" on F.SilkS covers pad ?.2 (3.43 mm2) | ? @ (129.0, 97.0) |
| error | check_silk / silk_over_pad | silk "hide" on F.SilkS covers pad ?.3 (2.32 mm2) | ? @ (131.5, 97.0) |
| error | check.dfm / dfm_trace_width | trace width 0.0100 mm below JLC minimum 0.127 mm on F.Cu | @ (189.6, 91.4) |
| error | check.dfm / dfm_trace_width | trace width 0.0100 mm below JLC minimum 0.127 mm on F.Cu | @ (189.7, 91.4) |
| error | check.dfm / dfm_trace_width | trace width 0.0100 mm below JLC minimum 0.127 mm on F.Cu | @ (189.7, 91.3) |
| error | check.dfm / dfm_trace_width | trace width 0.0100 mm below JLC minimum 0.127 mm on F.Cu | @ (189.8, 91.3) |
| error | check.dfm / dfm_trace_width | trace width 0.0100 mm below JLC minimum 0.127 mm on F.Cu | @ (189.8, 91.3) |
| error | check.dfm / dfm_trace_width | trace width 0.0100 mm below JLC minimum 0.127 mm on F.Cu | @ (189.9, 91.3) |
| error | check.dfm / dfm_trace_width | trace width 0.0100 mm below JLC minimum 0.127 mm on F.Cu | @ (189.9, 91.3) |
| error | check.dfm / dfm_trace_width | trace width 0.0100 mm below JLC minimum 0.127 mm on F.Cu | @ (189.9, 91.3) |
| error | check.dfm / dfm_trace_width | trace width 0.0100 mm below JLC minimum 0.127 mm on F.Cu | @ (189.9, 91.4) |
| error | check.dfm / dfm_trace_width | trace width 0.0100 mm below JLC minimum 0.127 mm on F.Cu | @ (189.9, 91.4) |
| error | check.dfm / dfm_trace_width | trace width 0.0100 mm below JLC minimum 0.127 mm on F.Cu | @ (189.9, 91.4) |
| error | check.dfm / dfm_trace_width | trace width 0.0100 mm below JLC minimum 0.127 mm on F.Cu | @ (189.9, 91.4) |
| error | check.dfm / dfm_trace_width | trace width 0.0100 mm below JLC minimum 0.127 mm on F.Cu | @ (189.8, 91.4) |
| error | check.dfm / dfm_trace_width | trace width 0.0100 mm below JLC minimum 0.127 mm on F.Cu | @ (189.8, 91.5) |
| error | check.dfm / dfm_trace_width | trace width 0.0100 mm below JLC minimum 0.127 mm on F.Cu | @ (189.8, 91.5) |
| error | check.dfm / dfm_trace_width | trace width 0.0100 mm below JLC minimum 0.127 mm on F.Cu | @ (189.8, 91.6) |
| error | check.dfm / dfm_trace_width | trace width 0.0100 mm below JLC minimum 0.127 mm on F.Cu | @ (189.8, 91.6) |
| error | check.dfm / dfm_trace_width | trace width 0.0100 mm below JLC minimum 0.127 mm on F.Cu | @ (189.8, 91.6) |
| error | check.dfm / dfm_trace_width | trace width 0.0100 mm below JLC minimum 0.127 mm on F.Cu | @ (189.8, 91.7) |
| error | check.dfm / dfm_trace_width | trace width 0.0100 mm below JLC minimum 0.127 mm on F.Cu | @ (189.9, 91.7) |
| error | check.dfm / dfm_trace_width | trace width 0.0100 mm below JLC minimum 0.127 mm on F.Cu | @ (190.0, 91.7) |
| error | check.dfm / dfm_trace_width | trace width 0.0100 mm below JLC minimum 0.127 mm on F.Cu | @ (190.1, 91.7) |

1134 more in `runs/mountaineer/reports/`.

### beaglebone-lora-adapter

https://github.com/VioletEternity/BeagleBoneLoRaAdapter at `867ef41c5f8e`, `BeagleBoneLoRaAdapter.kicad_pcb`, CERN-OHL-P-2.0, rf, 4 layers.

verify_all checks: check_creepage skipped, check_current skipped, check_decoupling skipped, check_diffpair pass, check_mating pass, check_pdn skipped, check_ratings skipped, check_return_path skipped, check_route_style violations, check_silk pass, check_thermal skipped

| severity | check | finding | where |
|---|---|---|---|
| error | check.dfm / dfm_open_outline | Edge.Cuts present but does not form a closed outline - copper/hole edge-distance checks cannot run |  |
| error | check.dfm / dfm_silk_over_pad | silkscreen printed over a solder-mask opening (0.1802 mm2) on F.Silkscreen - pad of ? | ? @ (100.5, 59.1) |
| error | check.dfm / dfm_silk_over_pad | silkscreen printed over a solder-mask opening (0.1802 mm2) on F.Silkscreen - pad of ? | ? @ (100.5, 61.1) |
| error | check.dfm / dfm_silk_over_pad | silkscreen printed over a solder-mask opening (0.1802 mm2) on F.Silkscreen - pad of ? | ? @ (100.5, 63.1) |
| error | check.dfm / dfm_silk_over_pad | silkscreen printed over a solder-mask opening (0.1802 mm2) on F.Silkscreen - pad of ? | ? @ (100.5, 65.1) |
| error | check.dfm / dfm_silk_over_pad | silkscreen printed over a solder-mask opening (0.1802 mm2) on F.Silkscreen - pad of ? | ? @ (100.5, 67.1) |
| error | check.dfm / dfm_silk_over_pad | silkscreen printed over a solder-mask opening (0.1802 mm2) on F.Silkscreen - pad of ? | ? @ (100.5, 69.1) |
| error | check.dfm / dfm_silk_over_pad | silkscreen printed over a solder-mask opening (0.1802 mm2) on F.Silkscreen - pad of ? | ? @ (100.5, 71.1) |
| error | check.dfm / dfm_silk_over_pad | silkscreen printed over a solder-mask opening (0.1802 mm2) on F.Silkscreen - pad of ? | ? @ (100.5, 73.1) |
| error | check.dfm / dfm_silk_over_pad | silkscreen printed over a solder-mask opening (0.1802 mm2) on F.Silkscreen - pad of ? | ? @ (117.9, 73.1) |
| error | check.dfm / dfm_silk_over_pad | silkscreen printed over a solder-mask opening (0.1802 mm2) on F.Silkscreen - pad of ? | ? @ (117.9, 71.1) |
| error | check.dfm / dfm_silk_over_pad | silkscreen printed over a solder-mask opening (0.1802 mm2) on F.Silkscreen - pad of ? | ? @ (117.9, 69.1) |
| error | check.dfm / dfm_silk_over_pad | silkscreen printed over a solder-mask opening (0.1802 mm2) on F.Silkscreen - pad of ? | ? @ (117.9, 67.1) |
| error | check.dfm / dfm_silk_over_pad | silkscreen printed over a solder-mask opening (0.1802 mm2) on F.Silkscreen - pad of ? | ? @ (117.9, 65.1) |
| error | check.dfm / dfm_silk_over_pad | silkscreen printed over a solder-mask opening (0.1802 mm2) on F.Silkscreen - pad of ? | ? @ (117.9, 63.1) |
| error | check.dfm / dfm_silk_over_pad | silkscreen printed over a solder-mask opening (0.1802 mm2) on F.Silkscreen - pad of ? | ? @ (117.9, 61.1) |
| error | check.dfm / dfm_silk_over_pad | silkscreen printed over a solder-mask opening (0.1802 mm2) on F.Silkscreen - pad of ? | ? @ (117.9, 59.1) |
| error | check.dfm / dfm_silk_over_pad | silkscreen printed over a solder-mask opening (0.1802 mm2) on F.Silkscreen - pad of ? | ? @ (100.5, 87.1) |
| error | check.dfm / dfm_silk_over_pad | silkscreen printed over a solder-mask opening (0.1802 mm2) on F.Silkscreen - pad of ? | ? @ (100.5, 89.1) |
| error | check.dfm / dfm_silk_over_pad | silkscreen printed over a solder-mask opening (0.1802 mm2) on F.Silkscreen - pad of ? | ? @ (100.5, 91.1) |
| error | check.dfm / dfm_silk_over_pad | silkscreen printed over a solder-mask opening (0.1802 mm2) on F.Silkscreen - pad of ? | ? @ (100.5, 93.1) |
| error | check.dfm / dfm_silk_over_pad | silkscreen printed over a solder-mask opening (0.1802 mm2) on F.Silkscreen - pad of ? | ? @ (100.5, 95.1) |
| error | check.dfm / dfm_silk_over_pad | silkscreen printed over a solder-mask opening (0.1802 mm2) on F.Silkscreen - pad of ? | ? @ (100.5, 97.1) |
| error | check.dfm / dfm_silk_over_pad | silkscreen printed over a solder-mask opening (0.1802 mm2) on F.Silkscreen - pad of ? | ? @ (100.5, 99.1) |
| error | check.dfm / dfm_silk_over_pad | silkscreen printed over a solder-mask opening (0.1802 mm2) on F.Silkscreen - pad of ? | ? @ (100.5, 101.1) |

11 more in `runs/beaglebone-lora-adapter/reports/`.

### rf-wifi-bridge

https://github.com/KHit6/RF-WiFi-Bridge at `4283ae0797d0`, `RF-Wifi-Bridge.kicad_pcb`, CERN-OHL-W-2.0, rf, 2 layers.

verify_all checks: check_creepage skipped, check_current skipped, check_decoupling skipped, check_diffpair pass, check_mating pass, check_pdn skipped, check_ratings skipped, check_return_path skipped, check_route_style violations, check_silk violations, check_thermal skipped

| severity | check | finding | where |
|---|---|---|---|
| error | check_silk / silk_over_pad | silk rect on F.SilkS covers pad AE2.1 (0.78 mm2) | AE2 @ (94.4, 70.5) |
| error | check_silk / silk_over_pad | silk rect on F.SilkS covers pad AE2.2 (0.50 mm2) | AE2 @ (95.5, 86.0) |
| error | check_silk / silk_over_pad | silk rect on F.SilkS covers pad AE2.A (0.78 mm2) | AE2 @ (95.6, 70.5) |
| error | check_silk / silk_over_pad | silk rect on F.SilkS covers pad U6.1 (1.13 mm2) | U6 @ (92.0, 70.5) |
| error | check_silk / silk_over_pad | silk rect on F.SilkS covers pad U6.2 (2.09 mm2) | U6 @ (92.0, 67.2) |
| error | check_silk / silk_over_pad | silk rect on F.SilkS covers pad U7. (7.06 mm2) | U7 @ (87.2, 74.5) |
| error | check_silk / silk_over_pad | silk rect on F.SilkS covers pad U7. (7.06 mm2) | U7 @ (96.8, 74.5) |
| error | check_silk / silk_over_pad | silk rect on F.SilkS covers pad U7.1 (1.44 mm2) | U7 @ (88.2, 93.1) |
| error | check_silk / silk_over_pad | silk rect on F.SilkS covers pad U7.2 (1.13 mm2) | U7 @ (88.2, 90.5) |
| error | check_silk / silk_over_pad | silk rect on F.SilkS covers pad U7.3 (1.13 mm2) | U7 @ (90.8, 93.1) |
| error | check_silk / silk_over_pad | silk rect on F.SilkS covers pad U7.4 (1.13 mm2) | U7 @ (90.8, 90.5) |
| error | check_silk / silk_over_pad | silk rect on F.SilkS covers pad U7.5 (1.13 mm2) | U7 @ (93.3, 93.1) |
| error | check_silk / silk_over_pad | silk rect on F.SilkS covers pad U7.6 (1.13 mm2) | U7 @ (93.3, 90.5) |
| error | check_silk / silk_over_pad | silk rect on F.SilkS covers pad U7.7 (1.13 mm2) | U7 @ (95.8, 93.1) |
| error | check_silk / silk_over_pad | silk rect on F.SilkS covers pad U7.8 (1.13 mm2) | U7 @ (95.8, 90.5) |
| error | check_silk / silk_over_pad | silk rect on F.SilkS covers pad U7.9 (1.13 mm2) | U7 @ (92.0, 70.5) |
| error | check_silk / silk_over_pad | silk line on F.SilkS covers pad AE1.1 (0.12 mm2) | AE1 @ (65.6, 109.5) |
| error | check.dfm / dfm_hole_to_hole | hole-to-hole 0.0000 mm below JLC minimum 0.5 mm | @ (67.5, 109.5) |
| error | check.dfm / dfm_hole_to_hole | hole-to-hole 0.0000 mm below JLC minimum 0.5 mm | @ (92.0, 70.5) |
| error | check.dfm / dfm_annular_ring | annular ring 0.0998 mm below JLC minimum 0.15 mm | @ (87.2, 74.5) |
| error | check.dfm / dfm_annular_ring | annular ring 0.0998 mm below JLC minimum 0.15 mm | @ (96.8, 74.5) |
| error | check.dfm / dfm_silk_over_pad | silkscreen printed over a solder-mask opening (0.2125 mm2) on F.Silkscreen - pad of U2 | U2 @ (70.5, 106.9) |
| error | check.dfm / dfm_silk_over_pad | silkscreen printed over a solder-mask opening (0.2125 mm2) on F.Silkscreen - pad of U4 | U4 @ (67.5, 106.9) |
| error | check.dfm / dfm_silk_over_pad | silkscreen printed over a solder-mask opening (0.2112 mm2) on F.Silkscreen - pad of U1 | U1 @ (70.6, 127.0) |
| error | check.dfm / dfm_silk_over_pad | silkscreen printed over a solder-mask opening (0.2112 mm2) on F.Silkscreen - pad of U1 | U1 @ (70.6, 129.6) |

16 more in `runs/rf-wifi-bridge/reports/`.

### lorapowerbox

https://github.com/h0lad/LoRaPowerBox at `a8856c6bea8a`, `pcb/LoraPowerBox.kicad_pcb`, CERN-OHL-S-2.0, rf, 4 layers.

verify_all checks: check_creepage skipped, check_current skipped, check_decoupling skipped, check_diffpair pass, check_mating pass, check_pdn skipped, check_ratings skipped, check_return_path skipped, check_route_style violations, check_silk violations, check_thermal skipped

| severity | check | finding | where |
|---|---|---|---|
| error | check_silk / silk_over_pad | silk "OUT" on F.SilkS covers pad SW3.6 (0.80 mm2) | SW3 @ (115.7, 43.0) |
| error | check_silk / silk_over_pad | silk "APP" on F.SilkS covers pad SW1.6 (0.80 mm2) | SW1 @ (126.8, 42.9) |
| error | check_silk / silk_over_pad | silk "STAT" on F.SilkS covers pad TP1.1 (0.40 mm2) | TP1 @ (133.7, 69.2) |
| error | check_silk / silk_over_pad | silk "PGn" on F.SilkS covers pad D3.2 (1.11 mm2) | D3 @ (142.2, 82.5) |
| error | check_silk / silk_over_pad | silk "3V3 " on F.SilkS covers pad J12.4 (0.73 mm2) | J12 @ (158.2, 46.5) |
| error | check_silk / silk_over_pad | silk rect on F.SilkS covers pad J6.1 (2.05 mm2) | J6 @ (153.3, 63.4) |
| error | check_silk / silk_over_pad | silk rect on F.SilkS covers pad J6.2 (1.79 mm2) | J6 @ (155.3, 63.4) |
| error | check_silk / silk_over_pad | silk rect on F.SilkS covers pad J6.3 (1.79 mm2) | J6 @ (157.3, 63.4) |
| error | check_silk / silk_over_pad | silk rect on F.SilkS covers pad J6.4 (1.79 mm2) | J6 @ (159.3, 63.4) |
| error | check_silk / silk_over_pad | silk rect on F.SilkS covers pad J12.1 (2.05 mm2) | J12 @ (152.2, 46.5) |
| error | check_silk / silk_over_pad | silk rect on F.SilkS covers pad J12.2 (1.79 mm2) | J12 @ (154.2, 46.5) |
| error | check_silk / silk_over_pad | silk rect on F.SilkS covers pad J12.3 (1.79 mm2) | J12 @ (156.2, 46.5) |
| error | check_silk / silk_over_pad | silk rect on F.SilkS covers pad J12.4 (1.79 mm2) | J12 @ (158.2, 46.5) |
| error | check_silk / silk_over_pad | silk rect on F.SilkS covers pad J12.5 (1.79 mm2) | J12 @ (160.2, 46.5) |
| error | check_silk / silk_over_pad | silk rect on F.SilkS covers pad J10.1 (2.05 mm2) | J10 @ (155.3, 80.5) |
| error | check_silk / silk_over_pad | silk rect on F.SilkS covers pad J10.2 (1.79 mm2) | J10 @ (157.3, 80.5) |
| error | check_silk / silk_over_pad | silk rect on F.SilkS covers pad J2.1 (2.05 mm2) | J2 @ (123.9, 61.9) |
| error | check_silk / silk_over_pad | silk rect on F.SilkS covers pad J2.2 (1.79 mm2) | J2 @ (123.9, 59.9) |
| error | check_silk / silk_over_pad | silk rect on F.SilkS covers pad J2.3 (1.79 mm2) | J2 @ (123.9, 57.9) |
| error | check_silk / silk_over_pad | silk rect on F.SilkS covers pad J2.4 (1.79 mm2) | J2 @ (123.9, 55.9) |
| error | check_silk / silk_over_pad | silk rect on F.SilkS covers pad J3.1 (2.05 mm2) | J3 @ (153.3, 52.2) |
| error | check_silk / silk_over_pad | silk rect on F.SilkS covers pad J3.2 (1.79 mm2) | J3 @ (155.3, 52.2) |
| error | check_silk / silk_over_pad | silk rect on F.SilkS covers pad J3.3 (1.79 mm2) | J3 @ (157.3, 52.2) |
| error | check_silk / silk_over_pad | silk rect on F.SilkS covers pad J3.4 (1.79 mm2) | J3 @ (159.3, 52.2) |
| error | check_silk / silk_over_pad | silk rect on F.SilkS covers pad J11.1 (2.05 mm2) | J11 @ (126.7, 83.7) |

51 more in `runs/lorapowerbox/reports/`.

### s-band-antenna

https://github.com/ICDT-Inatel-Cubesat-Design-Team/S-Band-Antenna at `8ef9c60349d1`, `hardware/PCB/Antenna.kicad_pcb`, CERN-OHL-W-2.0, rf, 2 layers.

verify_all checks: check_creepage skipped, check_current skipped, check_decoupling skipped, check_diffpair pass, check_mating violations, check_pdn skipped, check_ratings skipped, check_return_path skipped, check_route_style pass, check_silk violations, check_thermal skipped

| severity | check | finding | where |
|---|---|---|---|
| error | check_silk / silk_over_pad | silk "Part No.: 23b835b2 Version: 1.0b Designed by: Rodrigo Andrade" on B.SilkS covers pad H4.1 (0.50 mm2) | H4 @ (160.8, 129.9) |
| error | check.dfm / dfm_copper_to_edge | copper 0.0005 mm from board edge, JLC minimum 0.3 mm on B.Cu | @ (123.8, 92.5) |
| warning | check_mating / mating_direction_unknown | U1 (sma_edge): cannot read its mouth direction from the pad layout - add a `mouth` entry to reference/connector_mating.yaml | U1 @ (113.2, 92.5) |
| warning | check.dfm / dfm_silk_width | 96 silk strokes below JLC minimum width 0.15 mm (narrowest 0.1000 mm) on B.Silkscreen | @ (100.9, 82.6) |

### ocxo-breakout

https://github.com/Quantum-Electronic-Devices/OCXO_breakout at `2fafd619b224`, `ocxo_breakout.kicad_pcb`, CERN-OHL-W-2.0, rf, 4 layers.

verify_all checks: check_creepage skipped, check_current skipped, check_decoupling skipped, check_diffpair pass, check_mating pass, check_pdn skipped, check_ratings skipped, check_return_path skipped, check_route_style violations, check_silk violations, check_thermal skipped

| severity | check | finding | where |
|---|---|---|---|
| error | check_silk / silk_over_pad | silk rect on F.SilkS covers pad Y1.1 (3.24 mm2) | Y1 @ (78.3, 77.8) |
| error | check_silk / silk_over_pad | silk rect on F.SilkS covers pad Y1.2 (2.49 mm2) | Y1 @ (78.3, 86.7) |
| error | check_silk / silk_over_pad | silk rect on F.SilkS covers pad Y1.3 (2.54 mm2) | Y1 @ (78.3, 95.6) |
| error | check_silk / silk_over_pad | silk rect on F.SilkS covers pad Y1.4 (2.54 mm2) | Y1 @ (103.7, 95.6) |
| error | check_silk / silk_over_pad | silk rect on F.SilkS covers pad Y1.5 (2.54 mm2) | Y1 @ (103.7, 77.8) |
| error | check.dfm / dfm_open_outline | Edge.Cuts present but does not form a closed outline - copper/hole edge-distance checks cannot run |  |
| error | check.dfm / dfm_clearance | copper clearance 0.0600 mm below JLC minimum 0.1016 mm on In2.Cu | @ (64.9, 91.0) |
| error | check.dfm / dfm_clearance | copper clearance 0.0500 mm below JLC minimum 0.1016 mm on In2.Cu | @ (65.5, 91.0) |
| error | check.dfm / dfm_clearance | copper clearance 0.0500 mm below JLC minimum 0.1016 mm on In2.Cu | @ (65.5, 91.4) |
| error | check.dfm / dfm_clearance | copper clearance 0.0600 mm below JLC minimum 0.1016 mm on In2.Cu | @ (64.9, 91.4) |
| error | check.dfm / dfm_clearance | copper clearance 0.0600 mm below JLC minimum 0.1016 mm on In2.Cu | @ (66.1, 91.0) |
| error | check.dfm / dfm_clearance | copper clearance 0.0600 mm below JLC minimum 0.1016 mm on In2.Cu | @ (66.1, 91.4) |
| error | check.dfm / dfm_hole_to_hole | hole-to-hole 0.3951 mm below JLC minimum 0.5 mm | @ (64.9, 90.8) |
| error | check.dfm / dfm_hole_to_hole | hole-to-hole 0.2100 mm below JLC minimum 0.5 mm | @ (64.9, 90.8) |
| error | check.dfm / dfm_hole_to_hole | hole-to-hole 0.3950 mm below JLC minimum 0.5 mm | @ (64.9, 91.2) |
| error | check.dfm / dfm_hole_to_hole | hole-to-hole 0.2100 mm below JLC minimum 0.5 mm | @ (64.9, 91.2) |
| error | check.dfm / dfm_hole_to_hole | hole-to-hole 0.3951 mm below JLC minimum 0.5 mm | @ (64.9, 91.6) |
| error | check.dfm / dfm_hole_to_hole | hole-to-hole 0.3951 mm below JLC minimum 0.5 mm | @ (65.5, 90.8) |
| error | check.dfm / dfm_hole_to_hole | hole-to-hole 0.2000 mm below JLC minimum 0.5 mm | @ (65.5, 90.8) |
| error | check.dfm / dfm_hole_to_hole | hole-to-hole 0.3950 mm below JLC minimum 0.5 mm | @ (65.5, 91.2) |
| error | check.dfm / dfm_hole_to_hole | hole-to-hole 0.2000 mm below JLC minimum 0.5 mm | @ (65.5, 91.2) |
| error | check.dfm / dfm_hole_to_hole | hole-to-hole 0.3951 mm below JLC minimum 0.5 mm | @ (65.5, 91.6) |
| error | check.dfm / dfm_hole_to_hole | hole-to-hole 0.2100 mm below JLC minimum 0.5 mm | @ (66.1, 90.8) |
| error | check.dfm / dfm_hole_to_hole | hole-to-hole 0.2100 mm below JLC minimum 0.5 mm | @ (66.1, 91.2) |
| error | check.dfm / dfm_hole_to_hole | hole-to-hole 0.4071 mm below JLC minimum 0.5 mm | @ (103.0, 90.0) |

36 more in `runs/ocxo-breakout/reports/`.

### jetson-orin-baseboard

https://github.com/antmicro/jetson-orin-baseboard at `34f0e7f5fbca`, `jetson-orin-baseboard.kicad_pcb`, Apache-2.0, 4-layer, 8 layers.

dfm_check wrote no report: CheckError: no capability entry '8layer_1oz' (have: 2layer_1oz, 2layer_2oz, 4layer_1oz, 4layer_2oz, 6layer_1oz)

verify_all checks: check_creepage skipped, check_current skipped, check_decoupling skipped, check_diffpair violations, check_mating violations, check_pdn skipped, check_ratings skipped, check_return_path skipped, check_route_style error, check_silk violations, check_thermal skipped

| severity | check | finding | where |
|---|---|---|---|
| error | check_diffpair / diffpair_uncoupled | diff pair /USB Debug, DP/USBC0_SBU_P//USB Debug, DP/USBC0_SBU_N has 7.57 mm of /USB Debug, DP/USBC0_SBU_P running uncoupled (> 0.90 mm from  | /USB Debug, DP/USBC0_SBU_P @ (69.1, 110.6) |
| error | check_silk / silk_over_pad | silk "SDA" on B.SilkS covers pad J14.3 (0.49 mm2) | J14 @ (131.2, 123.5) |
| error | check_silk / silk_over_pad | silk "SDA" on B.SilkS covers pad J14.4 (0.34 mm2) | J14 @ (130.2, 123.5) |
| error | check_silk / silk_over_pad | silk "GND" on B.SilkS covers pad TP23.1 (0.44 mm2) | TP23 @ (68.2, 127.6) |
| error | check_silk / silk_over_pad | silk "VBUS1" on B.SilkS covers pad TP29.1 (0.44 mm2) | TP29 @ (68.2, 118.6) |
| error | check_silk / silk_over_pad | silk "+5V" on B.SilkS covers pad TP53.1 (0.44 mm2) | TP53 @ (68.2, 121.6) |
| error | check_silk / silk_over_pad | silk "VCC" on B.SilkS covers pad TP14.1 (0.44 mm2) | TP14 @ (68.2, 120.1) |
| error | check_silk / silk_over_pad | silk "+1V8" on B.SilkS covers pad TP55.1 (0.44 mm2) | TP55 @ (68.2, 126.1) |
| error | check_silk / silk_over_pad | silk "SCL" on B.SilkS covers pad J14.4 (0.51 mm2) | J14 @ (130.2, 123.5) |
| error | check_silk / silk_over_pad | silk "+3V3" on B.SilkS covers pad TP54.1 (0.44 mm2) | TP54 @ (68.2, 123.1) |
| error | check_silk / silk_over_pad | silk "GND" on B.SilkS covers pad J14.1 (0.47 mm2) | J14 @ (133.2, 123.5) |
| error | check_silk / silk_over_pad | silk "GND" on B.SilkS covers pad J14.2 (0.37 mm2) | J14 @ (132.2, 123.5) |
| error | check_silk / silk_over_pad | silk "STARTUP MANUAL     AUTO" on B.SilkS covers pad TP33.1 (0.39 mm2) | TP33 @ (63.2, 70.2) |
| error | check_silk / silk_over_pad | silk "VBUS0" on B.SilkS covers pad TP17.1 (0.44 mm2) | TP17 @ (68.2, 115.6) |
| error | check_silk / silk_over_pad | silk "3V3 STDB" on B.SilkS covers pad TP52.1 (0.44 mm2) | TP52 @ (68.2, 124.6) |
| error | check_silk / silk_over_pad | silk "VBUS3" on B.SilkS covers pad TP1.1 (0.44 mm2) | TP1 @ (68.2, 117.1) |
| error | check_silk / silk_over_pad | silk "M.2 KEY M" on B.SilkS covers pad R143.1 (0.29 mm2) | R143 @ (119.6, 99.3) |
| error | check_silk / silk_over_pad | silk "3V3" on B.SilkS covers pad J14.2 (0.49 mm2) | J14 @ (132.2, 123.5) |
| error | check_silk / silk_over_pad | silk "3V3" on B.SilkS covers pad J14.3 (0.34 mm2) | J14 @ (131.2, 123.5) |
| error | check_silk / silk_over_pad | silk "USB-C 0 DP" on F.SilkS covers pad J9. (0.73 mm2) | J9 @ (80.1, 124.2) |
| error | check_silk / silk_over_pad | silk line on F.SilkS covers pad U6.59 (0.07 mm2) | U6 @ (63.8, 102.1) |
| error | check_silk / silk_over_pad | silk rect on F.SilkS covers pad R66.1 (0.36 mm2) | R66 @ (134.8, 111.8) |
| error | check_silk / silk_over_pad | silk rect on F.SilkS covers pad R66.2 (0.36 mm2) | R66 @ (134.8, 112.8) |
| error | check_silk / silk_over_pad | silk rect on F.SilkS covers pad C106.1 (0.36 mm2) | C106 @ (136.9, 113.1) |
| error | check_silk / silk_over_pad | silk rect on F.SilkS covers pad C106.2 (0.36 mm2) | C106 @ (137.9, 113.1) |

1405 more in `runs/jetson-orin-baseboard/reports/`.

### tokay-lite

https://github.com/maxlab-io/tokay-lite-pcb at `fd04d94a332d`, `ai-camera-rev3.2/ai-camera-rev3.2.kicad_pcb`, CERN-OHL-P-2.0, 4-layer, 4 layers.

verify_all checks: check_creepage skipped, check_current skipped, check_decoupling skipped, check_diffpair pass, check_mating pass, check_pdn skipped, check_ratings skipped, check_return_path skipped, check_route_style violations, check_silk violations, check_thermal skipped

| severity | check | finding | where |
|---|---|---|---|
| error | check_silk / silk_over_pad | silk "NOTES: Battery connector: JST-PH 2mm pitch IRCUT connector: MolexPicoblade 1.25mm pitch  " on B.SilkS covers pad J5.2 (0.50 mm2) | J5 @ (116.5, 60.4) |
| error | check_silk / silk_over_pad | silk "NOTES: Battery connector: JST-PH 2mm pitch IRCUT connector: MolexPicoblade 1.25mm pitch  " on B.SilkS covers pad TP22.1 (0.58 mm2) | TP22 @ (146.2, 60.8) |
| error | check_silk / silk_over_pad | silk "NOTES: Battery connector: JST-PH 2mm pitch IRCUT connector: MolexPicoblade 1.25mm pitch  " on B.SilkS covers pad TP3.1 (0.75 mm2) | TP3 @ (158.8, 60.2) |
| error | check_silk / silk_over_pad | silk "NOTES: Battery connector: JST-PH 2mm pitch IRCUT connector: MolexPicoblade 1.25mm pitch  " on B.SilkS covers pad R25.1 (0.33 mm2) | R25 @ (119.6, 60.3) |
| error | check_silk / silk_over_pad | silk "NOTES: Battery connector: JST-PH 2mm pitch IRCUT connector: MolexPicoblade 1.25mm pitch  " on B.SilkS covers pad R25.2 (0.33 mm2) | R25 @ (118.6, 60.3) |
| error | check_silk / silk_over_pad | silk "IO39" on F.SilkS covers pad J4.17 (1.35 mm2) | J4 @ (151.7, 77.4) |
| error | check_silk / silk_over_pad | silk "BOOT " on F.SilkS covers pad J4.5 (1.69 mm2) | J4 @ (151.7, 62.2) |
| error | check_silk / silk_over_pad | silk "Multi-Purpose Camera Devkit maxlab.io hi@maxlab.io ${REVISION}-${ISSUE_DATE}" on F.SilkS covers pad C11.1 (1.68 mm2) | C11 @ (118.2, 101.2) |
| error | check_silk / silk_over_pad | silk "Multi-Purpose Camera Devkit maxlab.io hi@maxlab.io ${REVISION}-${ISSUE_DATE}" on F.SilkS covers pad C11.2 (1.68 mm2) | C11 @ (115.1, 101.2) |
| error | check_silk / silk_over_pad | silk "Multi-Purpose Camera Devkit maxlab.io hi@maxlab.io ${REVISION}-${ISSUE_DATE}" on F.SilkS covers pad J1.MP (1.83 mm2) | J1 @ (104.1, 100.8) |
| error | check_silk / silk_over_pad | silk "Multi-Purpose Camera Devkit maxlab.io hi@maxlab.io ${REVISION}-${ISSUE_DATE}" on F.SilkS covers pad L2.1 (0.84 mm2) | L2 @ (123.1, 100.7) |
| error | check_silk / silk_over_pad | silk "Multi-Purpose Camera Devkit maxlab.io hi@maxlab.io ${REVISION}-${ISSUE_DATE}" on F.SilkS covers pad L2.2 (0.84 mm2) | L2 @ (121.0, 100.7) |
| error | check_silk / silk_over_pad | silk "Multi-Purpose Camera Devkit maxlab.io hi@maxlab.io ${REVISION}-${ISSUE_DATE}" on F.SilkS covers pad C22.1 (0.17 mm2) | C22 @ (154.4, 101.9) |
| error | check_silk / silk_over_pad | silk "Multi-Purpose Camera Devkit maxlab.io hi@maxlab.io ${REVISION}-${ISSUE_DATE}" on F.SilkS covers pad C22.2 (0.33 mm2) | C22 @ (154.4, 100.9) |
| error | check_silk / silk_over_pad | silk "IO38" on F.SilkS covers pad J4.15 (1.35 mm2) | J4 @ (151.7, 74.9) |
| error | check_silk / silk_over_pad | silk "C5" on F.SilkS covers pad C5.1 (0.23 mm2) | C5 @ (106.7, 92.0) |
| error | check_silk / silk_over_pad | silk "C5" on F.SilkS covers pad R12.2 (0.12 mm2) | R12 @ (104.7, 91.8) |
| error | check_silk / silk_over_pad | silk "R21" on F.SilkS covers pad R21.1 (0.23 mm2) | R21 @ (109.3, 111.0) |
| error | check_silk / silk_over_pad | silk "SW2" on F.SilkS covers pad SW2.2 (0.52 mm2) | SW2 @ (158.1, 72.2) |
| error | check_silk / silk_over_pad | silk "R26" on F.SilkS covers pad R26.2 (0.26 mm2) | R26 @ (159.3, 73.9) |
| error | check_silk / silk_over_pad | silk "R5" on F.SilkS covers pad R5.2 (0.18 mm2) | R5 @ (110.1, 91.8) |
| error | check_silk / silk_over_pad | silk "R29" on F.SilkS covers pad R29.1 (0.32 mm2) | R29 @ (144.5, 107.0) |
| error | check_silk / silk_over_pad | silk "R29" on F.SilkS covers pad R30.2 (0.22 mm2) | R30 @ (144.5, 109.7) |
| error | check_silk / silk_over_pad | silk rect on F.SilkS covers pad SW4. (2.27 mm2) | SW4 @ (139.6, 52.0) |
| error | check_silk / silk_over_pad | silk rect on F.SilkS covers pad SW4. (2.27 mm2) | SW4 @ (132.4, 52.0) |

265 more in `runs/tokay-lite/reports/`.

### tokay-lite-rev3.1

https://github.com/maxlab-io/tokay-lite-pcb at `fd04d94a332d`, `ai-camera-rev3.1/ai-camera-rev3.1.kicad_pcb`, CERN-OHL-P-2.0, 4-layer, 4 layers.

verify_all checks: check_creepage skipped, check_current skipped, check_decoupling skipped, check_diffpair pass, check_mating pass, check_pdn skipped, check_ratings skipped, check_return_path skipped, check_route_style violations, check_silk violations, check_thermal skipped

| severity | check | finding | where |
|---|---|---|---|
| error | check_silk / silk_over_pad | silk "IO39" on F.SilkS covers pad ?.17 (1.35 mm2) | ? @ (151.7, 77.4) |
| error | check_silk / silk_over_pad | silk "BOOT " on F.SilkS covers pad ?.5 (1.69 mm2) | ? @ (151.7, 62.2) |
| error | check_silk / silk_over_pad | silk "Multi-Purpose Camera Devkit maxlab.io hi@maxlab.io ${REVISION}-${ISSUE_DATE}" on F.SilkS covers pad ?.1 (1.68 mm2) | ? @ (118.2, 101.2) |
| error | check_silk / silk_over_pad | silk "Multi-Purpose Camera Devkit maxlab.io hi@maxlab.io ${REVISION}-${ISSUE_DATE}" on F.SilkS covers pad ?.2 (1.68 mm2) | ? @ (115.1, 101.2) |
| error | check_silk / silk_over_pad | silk "Multi-Purpose Camera Devkit maxlab.io hi@maxlab.io ${REVISION}-${ISSUE_DATE}" on F.SilkS covers pad ?.MP (1.83 mm2) | ? @ (104.1, 100.8) |
| error | check_silk / silk_over_pad | silk "Multi-Purpose Camera Devkit maxlab.io hi@maxlab.io ${REVISION}-${ISSUE_DATE}" on F.SilkS covers pad ?.1 (0.84 mm2) | ? @ (123.1, 100.7) |
| error | check_silk / silk_over_pad | silk "Multi-Purpose Camera Devkit maxlab.io hi@maxlab.io ${REVISION}-${ISSUE_DATE}" on F.SilkS covers pad ?.2 (0.84 mm2) | ? @ (121.0, 100.7) |
| error | check_silk / silk_over_pad | silk "Multi-Purpose Camera Devkit maxlab.io hi@maxlab.io ${REVISION}-${ISSUE_DATE}" on F.SilkS covers pad ?.1 (0.17 mm2) | ? @ (154.4, 101.9) |
| error | check_silk / silk_over_pad | silk "Multi-Purpose Camera Devkit maxlab.io hi@maxlab.io ${REVISION}-${ISSUE_DATE}" on F.SilkS covers pad ?.2 (0.33 mm2) | ? @ (154.4, 100.9) |
| error | check_silk / silk_over_pad | silk "IO38" on F.SilkS covers pad ?.15 (1.35 mm2) | ? @ (151.7, 74.9) |
| error | check_silk / silk_over_pad | silk "C5" on F.SilkS covers pad ?.1 (0.23 mm2) | ? @ (106.7, 92.0) |
| error | check_silk / silk_over_pad | silk "C5" on F.SilkS covers pad ?.2 (0.12 mm2) | ? @ (104.7, 91.8) |
| error | check_silk / silk_over_pad | silk "R21" on F.SilkS covers pad ?.1 (0.23 mm2) | ? @ (109.3, 111.0) |
| error | check_silk / silk_over_pad | silk "SW2" on F.SilkS covers pad ?.2 (0.52 mm2) | ? @ (158.1, 72.2) |
| error | check_silk / silk_over_pad | silk "R26" on F.SilkS covers pad ?.2 (0.26 mm2) | ? @ (159.3, 73.9) |
| error | check_silk / silk_over_pad | silk "R5" on F.SilkS covers pad ?.2 (0.18 mm2) | ? @ (110.1, 91.8) |
| error | check_silk / silk_over_pad | silk "R29" on F.SilkS covers pad ?.1 (0.32 mm2) | ? @ (144.5, 107.0) |
| error | check_silk / silk_over_pad | silk "R29" on F.SilkS covers pad ?.2 (0.22 mm2) | ? @ (144.5, 109.7) |
| error | check_silk / silk_over_pad | silk rect on F.SilkS covers pad ?. (2.27 mm2) | ? @ (139.6, 52.0) |
| error | check_silk / silk_over_pad | silk rect on F.SilkS covers pad ?. (2.27 mm2) | ? @ (132.4, 52.0) |
| error | check_silk / silk_over_pad | silk rect on F.SilkS covers pad ?.1 (2.27 mm2) | ? @ (138.2, 49.5) |
| error | check_silk / silk_over_pad | silk rect on F.SilkS covers pad ?.2 (2.27 mm2) | ? @ (133.8, 49.5) |
| error | check_silk / silk_over_pad | silk "R10" on F.SilkS covers pad ?.1 (0.33 mm2) | ? @ (108.9, 79.8) |
| error | check_silk / silk_over_pad | silk "C17" on F.SilkS covers pad ?.1 (0.15 mm2) | ? @ (113.3, 104.5) |
| error | check_silk / silk_over_pad | silk "R23" on F.SilkS covers pad ?.1 (0.32 mm2) | ? @ (113.3, 102.6) |

279 more in `runs/tokay-lite-rev3.1/reports/`.

### ottercast-audio-v2

https://github.com/Ottercast/OtterCastAudioV2 at `199395d7249a`, `OtterCastAudioV2.kicad_pcb`, MIT, 4-layer, 4 layers.

verify_all checks: check_creepage skipped, check_current skipped, check_decoupling skipped, check_diffpair violations, check_mating pass, check_pdn skipped, check_ratings skipped, check_return_path skipped, check_route_style violations, check_silk violations, check_thermal skipped

| severity | check | finding | where |
|---|---|---|---|
| error | check_silk / silk_over_pad | silk "by @lucysrausch @toble_miner @manawyrm @janamarie" on B.SilkS covers pad ?. (1.90 mm2) | ? @ (85.4, 112.1) |
| error | check_silk / silk_over_pad | silk "D6" on F.SilkS covers pad ?.1 (0.15 mm2) | ? @ (102.3, 112.0) |
| error | check_silk / silk_over_pad | silk "hide" on F.SilkS covers pad ?.2 (0.70 mm2) | ? @ (84.3, 84.1) |
| error | check_silk / silk_over_pad | silk "hide" on F.SilkS covers pad ?.2 (0.88 mm2) | ? @ (95.5, 115.9) |
| error | check_silk / silk_over_pad | silk "hide" on F.SilkS covers pad ?.3 (0.38 mm2) | ? @ (100.7, 111.6) |
| error | check_silk / silk_over_pad | silk "hide" on F.SilkS covers pad ?.1 (0.30 mm2) | ? @ (91.8, 91.3) |
| error | check_silk / silk_over_pad | silk "hide" on F.SilkS covers pad ?.1 (0.26 mm2) | ? @ (90.1, 91.3) |
| error | check_silk / silk_over_pad | silk "hide" on F.SilkS covers pad ?.2 (0.30 mm2) | ? @ (91.1, 91.3) |
| error | check_silk / silk_over_pad | silk "hide" on F.SilkS covers pad ?.1 (0.19 mm2) | ? @ (101.0, 88.4) |
| error | check_silk / silk_over_pad | silk "hide" on F.SilkS covers pad ?.1 (0.30 mm2) | ? @ (99.8, 88.4) |
| error | check_silk / silk_over_pad | silk "hide" on F.SilkS covers pad ?.1 (0.61 mm2) | ? @ (109.8, 91.8) |
| error | check_silk / silk_over_pad | silk "hide" on F.SilkS covers pad ?.1 (1.04 mm2) | ? @ (85.1, 87.1) |
| error | check_silk / silk_over_pad | silk "hide" on F.SilkS covers pad ?.1 (1.04 mm2) | ? @ (85.1, 88.8) |
| error | check_silk / silk_over_pad | silk "hide" on F.SilkS covers pad ?.2 (0.54 mm2) | ? @ (90.5, 112.5) |
| error | check_silk / silk_over_pad | silk "hide" on B.SilkS covers pad ?. (0.25 mm2) | ? @ (86.6, 111.1) |
| error | check_silk / silk_over_pad | silk "hide" on B.SilkS covers pad ?. (0.85 mm2) | ? @ (91.0, 87.3) |
| error | check_silk / silk_over_pad | silk "hide" on B.SilkS covers pad ?. (0.74 mm2) | ? @ (91.0, 81.3) |
| error | check_silk / silk_over_pad | silk "hide" on B.SilkS covers pad ?. (1.13 mm2) | ? @ (91.0, 87.3) |
| error | check_silk / silk_over_pad | silk "hide" on B.SilkS covers pad ?. (1.00 mm2) | ? @ (100.0, 84.3) |
| error | check_silk / silk_over_pad | silk "hide" on B.SilkS covers pad ?. (1.13 mm2) | ? @ (100.0, 84.3) |
| error | check_silk / silk_over_pad | silk "hide" on B.SilkS covers pad ?. (0.96 mm2) | ? @ (109.0, 87.3) |
| error | check_silk / silk_over_pad | silk "hide" on B.SilkS covers pad ?. (0.62 mm2) | ? @ (109.0, 81.3) |
| error | check_silk / silk_over_pad | silk "hide" on B.SilkS covers pad ?. (1.13 mm2) | ? @ (109.0, 87.3) |
| error | check.dfm / dfm_open_outline | Edge.Cuts present but does not form a closed outline - copper/hole edge-distance checks cannot run |  |
| error | check.dfm / dfm_clearance | copper clearance 0.0500 mm below JLC minimum 0.1016 mm on F.Cu | @ (103.7, 108.2) |

448 more in `runs/ottercast-audio-v2/reports/`.

### mackerel-68k

https://github.com/crmaykish/mackerel-68k at `50786ed64897`, `hardware/mackerel-10-v1/mackerel-10-v1.kicad_pcb`, MIT, 4-layer, 4 layers.

verify_all checks: check_creepage skipped, check_current skipped, check_decoupling skipped, check_diffpair pass, check_mating pass, check_pdn skipped, check_ratings skipped, check_return_path skipped, check_route_style violations, check_silk violations, check_thermal skipped

| severity | check | finding | where |
|---|---|---|---|
| error | check_silk / silk_over_pad | silk "SIMM A0" on F.SilkS covers pad C21.1 (1.64 mm2) | C21 @ (44.8, 87.2) |
| error | check_silk / silk_over_pad | silk "IACK" on F.SilkS covers pad J13.7 (1.48 mm2) | J13 @ (82.1, 183.3) |
| error | check_silk / silk_over_pad | silk "GND " on F.SilkS covers pad J10.6 (1.68 mm2) | J10 @ (227.1, 176.8) |
| error | check_silk / silk_over_pad | silk "github.com/crmaykish/mackerel-68k Colin Maykish - Nov 2024" on F.SilkS covers pad C37.2 (2.01 mm2) | C37 @ (140.7, 168.7) |
| error | check_silk / silk_over_pad | silk "github.com/crmaykish/mackerel-68k Colin Maykish - Nov 2024" on F.SilkS covers pad C38.2 (1.69 mm2) | C38 @ (169.9, 168.6) |
| error | check_silk / silk_over_pad | silk "DTACK" on F.SilkS covers pad J13.8 (1.63 mm2) | J13 @ (82.1, 180.8) |
| error | check_silk / silk_over_pad | silk "SIMM A1" on F.SilkS covers pad C25.1 (1.86 mm2) | C25 @ (44.8, 53.6) |
| error | check_silk / silk_over_pad | silk "MACKEREL-10 SBC v1.2" on F.SilkS covers pad C37.1 (2.01 mm2) | C37 @ (140.7, 163.7) |
| error | check_silk / silk_over_pad | silk "MACKEREL-10 SBC v1.2" on F.SilkS covers pad U13.15 (2.01 mm2) | U13 @ (156.5, 163.6) |
| error | check_silk / silk_over_pad | silk "MACKEREL-10 SBC v1.2" on F.SilkS covers pad U13.16 (2.01 mm2) | U13 @ (153.9, 163.6) |
| error | check_silk / silk_over_pad | silk "MACKEREL-10 SBC v1.2" on F.SilkS covers pad U13.17 (2.01 mm2) | U13 @ (151.4, 163.6) |
| error | check_silk / silk_over_pad | silk "MACKEREL-10 SBC v1.2" on F.SilkS covers pad U13.18 (2.01 mm2) | U13 @ (148.8, 163.6) |
| error | check_silk / silk_over_pad | silk "MACKEREL-10 SBC v1.2" on F.SilkS covers pad U13.19 (2.01 mm2) | U13 @ (146.3, 163.6) |
| error | check_silk / silk_over_pad | silk "MACKEREL-10 SBC v1.2" on F.SilkS covers pad U13.20 (2.01 mm2) | U13 @ (143.8, 163.6) |
| error | check_silk / silk_over_pad | silk "SIMM B0" on F.SilkS covers pad C23.1 (1.55 mm2) | C23 @ (44.8, 70.4) |
| error | check_silk / silk_over_pad | silk "SIMM B1" on F.SilkS covers pad C27.1 (1.98 mm2) | C27 @ (44.7, 37.3) |
| error | check_silk / silk_over_pad | silk rect on F.SilkS covers pad J13.5 (2.27 mm2) | J13 @ (79.6, 183.3) |
| error | check_silk / silk_over_pad | silk rect on F.SilkS covers pad J13.6 (2.27 mm2) | J13 @ (79.6, 180.8) |
| error | check_silk / silk_over_pad | silk rect on F.SilkS covers pad J13.7 (2.27 mm2) | J13 @ (82.1, 183.3) |
| error | check_silk / silk_over_pad | silk rect on F.SilkS covers pad J13.8 (2.27 mm2) | J13 @ (82.1, 180.8) |
| error | check.dfm / dfm_hole_to_hole | hole-to-hole 0.4700 mm below JLC minimum 0.5 mm | @ (208.0, 54.2) |
| error | check.dfm / dfm_hole_to_hole | hole-to-hole 0.4700 mm below JLC minimum 0.5 mm | @ (208.0, 56.6) |
| error | check.dfm / dfm_annular_ring | annular ring 0.0875 mm below JLC minimum 0.1 mm | @ (197.7, 24.5) |
| error | check.dfm / dfm_annular_ring | annular ring 0.0875 mm below JLC minimum 0.1 mm | @ (199.4, 24.5) |
| error | check.dfm / dfm_annular_ring | annular ring 0.0875 mm below JLC minimum 0.1 mm | @ (201.1, 24.5) |

13 more in `runs/mackerel-68k/reports/`.
