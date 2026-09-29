# The firmware manifest (/fwe -> /npie)

/fwe writes `firmware/fwe-manifest.json` next to every build; /npie reads it
to flash the board and drive the firmware. It is the whole interface: /npie
never reads firmware sources, and /fwe never assumes a bench.
`scripts/fw_manifest.py --check` validates one.

```json
{
  "schema": "fwe-manifest/1",
  "board": "PCB-0018-A",
  "mcu": {"part": "STM32G431CBT6", "core": "cortex-m4", "flash_base": "0x08000000"},
  "stage": "bringup",
  "version": "0.1.0+g<sha>",
  "artifact": {"elf": "build/fw.elf", "bin": "build/fw.bin", "hex": "build/fw.hex",
               "sha256": {"elf": "...", "bin": "...", "hex": "..."}},
  "flash": {
    "interface": "swd", "connector": "J601",
    "commands": {
      "probe-rs": ["probe-rs", "download", "--chip", "STM32G431CBTx", "{elf}"],
      "openocd": ["openocd", "-f", "interface/stlink.cfg", "-f", "target/stm32g4x.cfg",
                  "-c", "program {elf} verify reset exit"]
    }
  },
  "uart": {"connector": "J701", "tx_pin": "3", "rx_pin": "4", "baud": 115200,
           "format": "8N1", "levels": "3V3", "banner_regex": "^fwe PCB-0018-A "},
  "commands": [{"name": "status", "args": "", "reply": "OK {json}", "safe": true}],
  "test_hooks": [{"name": "selftest", "send": "selftest", "expect": "^OK ",
                  "timeout_s": 5, "needs": ["3V3"]}],
  "safety": {"pwm_at_reset": "off", "i_trip_a": 20.0, "vbus_ov_v": 30.0,
             "vbus_uv_v": 9.0, "fault_clear": "clear"},
  "verified": {"build": true, "host_tests": true, "sim": "renode", "hardware": false}
}
```

## UART protocol (line-based ASCII)

- One command per line, `\n`-terminated, lowercase words separated by spaces.
- Every command gets exactly one reply line: `OK <json>` or `ERR <code> <text>`.
  The JSON is a single object on one line so a script can parse it.
- Asynchronous events are lines starting `EVT <json>` (a fault trip, a
  button press); a driver must accept them between a command and its reply.
- Boot prints one banner line matching `banner_regex`, then `EVT {"boot":...}`
  carrying the reset cause.
- Commands a motor board firmware implements at the bringup stage:
  `version`, `status`, `selftest`, `adc` (raw + scaled channels),
  `offsets` (re-run current-sense offset calibration, bridge off),
  `led <status|fault> <on|off>`, `arm` (MOE on, 0 duty), `disarm`,
  `duty <a> <b> <c>` (0..1, refused unless armed and capped by `max_duty`),
  `clear` (clear a latched fault), `reset`.
  Each is listed in `commands` with `safe: false` when it can energise the
  bridge, so /npie can require its own human confirmation step first.

## Test hooks

`test_hooks` are what /npie runs unattended after flashing: a `send` line, a
regex `expect` on the reply, a timeout, and the rails the hook needs powered
(`needs`), so /npie can order them after its power-up steps. A hook never
energises the bridge; anything that does is a `commands` entry with
`safe: false` and belongs in a human-confirmed /npie step.

## Versioning

`schema` changes its number on any breaking change. Additive keys are
allowed within a version, and a reader ignores keys it does not know.
