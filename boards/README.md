# ai-ee3 boards

Board workspaces designed by the `/ai-ee` skill (github.com/ihsan-sa/ai-ee).
This repo is a derived view of the `boards/` subtree of the private build repo
`ai-ee3` (the canonical source) - synced via `git subtree split --prefix=boards`.

| Board | Class | State |
|---|---|---|
| stm32-blinky | 2L STM32 blinky (v1 hardening run a) | order-ready package |
| usb-buck | 4L USB-FS + buck (v1 hardening run b) | order-ready package |
| pd-trigger | USB-C PD trigger (novel, run c) | ORDERED (JLC, 2026-07) |
| lumina-carrier | 4L PoE ESP32 carrier | ORDERED (JLC web, 2026-07); rework R1 before power-on |
| lumina-par | PoE RGB+W par light daughter | in design (P8) |
| lumina-strobe | PoE strobe daughter | in design (P4) |
| sbuck-5v3a | 4L 12V -> 5V/3A synchronous buck (v2 live run) | order-ready package (P10) |
| buck-5v3a | first attempt at the same buck brief | **SUPERSEDED by sbuck-5v3a**, closed at P3 - do not resume |
| rf-term-150w | 150 W RF terminator, tuned launch (v2 live run) | P9, order-ready package |
| rf-de-20m | 20 m receive down-converter (external intake) | P9, constrained prototype - see `fab/README.md` |
| xhp-driver | high-power LED driver | brief only (P0) |

Per-board layout: `brief/` `research/` `architecture/` `parts/` `lib/` `kicad/`
`routing/` `reports/` `fab/` `log/` + `state.json` (phase, gates, decisions,
human holds). `fab/` contains the order-ready JLCPCB package (gerbers, BOM, CPL,
quotes, order/tracking records).

Private: fab records carry order numbers and ship-region metadata.
