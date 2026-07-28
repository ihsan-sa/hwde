# ERC/schematic review waivers (stm32-blinky)

W1 (reviewer warning 4, issue 4): "erc-pintypes-vacuous" - easyeda2kicad symbols
carry mostly-passive pin types even after datasheet-driven retyping of supplies,
so ERC's driver-conflict/float checks have reduced power on this board. Waived:
connectivity was independently hand-verified by the adversarial reviewer against
both datasheet extracts (all 9 supply pins, polarity, strapping). Tooling fix
(retype at lib_pull time, GPIOs as bidirectional) queued as S14 hardening item.

Note: reviewer warnings 2 (VDDA 1uF//10nF) and 3 (VDD_3 bulk) were FIXED, not
waived, along with error 1 (22uF tantalum LDO output cap) - see state.json
issues 1-3 and the second erc gate commit.
