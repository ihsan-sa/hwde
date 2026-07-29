# LUMINA — Hardware System Context

**Version:** 2.0 | **Date:** 2026-07-28 | **Status:** Living document
**Supersedes:** all hardware decisions recorded in *LUMINA Project Plan v1.0* §6

---

## 0. How to use this document

This is the shared context for all LUMINA fixture PCBs. Each board has its own brief
(`01-…` through `04-…`) which is self-contained enough to hand to a designer alone, but
assumes the constraints below. Read this first, then the board brief.

**Requirement IDs** are stable. Reference them in design decisions and review notes.
**Open decisions** are labelled `D-nn` and must be closed before layout — not before schematic.
**Flagged as judgement** marks a statement that is engineering interpretation, not a
sourced fact or a prior decision of record. Challenge those first.

---

## 1. What the system is

An AI host analyses music in real time and drives custom PoE-networked light fixtures over
Ethernet. The host decides *what* the lighting should do (genre-aware, structure-aware —
builds, drops, breakdowns, vocal energy); the fixtures execute colour, intensity, and strobe
parameters. The fixtures contain no musical intelligence.

**Deployment target (first build):**

| Parameter | Value |
|---|---|
| Room | ~5 m × 7 m × 2.5 m, basement/garage |
| Fixture count | 8–12 |
| Fixture types (Phase 1) | Strobe, RGBW par, UV bar |
| Budget (fixtures + switch + enclosures) | $500–$1000 |
| Host | Jetson Orin Nano (owned) |
| Network | Managed PoE switch, 8–16 ports |

---

## 2. Architecture of record

**Modular carrier + daughter board.** One universal carrier board carries PoE PD, DC-DC
conversion, ESP32-S3, W5500 Ethernet, and RJ45. Fixture-specific daughter boards carry only
LED drivers, energy storage, and load circuitry, and connect via a defined expansion
connector. This is settled — every board brief inherits it.

Rationale: the hard part of the design (PoE front end, 48 V power conversion, Ethernet
mixed-signal layout) is designed and validated once and reused. Daughter boards become
trivial and independently revisable.

**MCU of record: ESP32-S3 + W5500 over SPI.** Settled. Both candidate MCU paths required an
external W5500 anyway (the S3 dropped the RMII support the original ESP32 had), so the
STM32F4's timing advantage did not justify its ecosystem cost. STM32F4 remains reserved for a
future laser/galvo fixture only.

---

## 3. Control contract (what the fixture must honour)

Defined by the host software, already implemented on the host side. Fixtures conform to it;
they do not get to renegotiate it.

| Item | Value |
|---|---|
| Transport | UDP over IPv4, port 5568 |
| Update rate | 60 fps target, 44 fps floor |
| Packet → PWM latency | < 100 µs |
| Addressing | mDNS discovery or static IP |
| Watchdog | No valid packet for > 2 s → fade all outputs to zero over 500 ms |
| Payload | Fixture ID, per-channel levels, strobe rate, strobe intensity, timestamp |

**Critical consequence for hardware and firmware:** at 60 fps the command stream can only
express modulation up to ~30 Hz, and in practice much less. Fast effects — strobe up to 25 Hz,
bass-tracking "wobble" intensity modulation, sub-100 ms accent flashes — are *parameterised*
by the host and *generated locally* by the fixture. The fixture must therefore be able to
produce these waveforms from its own timer, without a packet per transition.

---

## 4. Behavioural requirements derived from the genre profiles

These come from *LUMINA Genre Lighting Deep-Dive v1.1* and are the real optical spec. They
are what makes this a lighting instrument rather than a networked lamp.

| ID | Requirement | Source profile |
|---|---|---|
| SYS-REQ-01 | Full-output flash of 100–200 ms with **instant** blackout between flashes — no visible decay tail | P1 Rage trap: "Binary: BLINDING or DARK" |
| SYS-REQ-02 | Single-fixture accent flashes as short as 50 ms | P1 ad-libs |
| SYS-REQ-03 | Repetitive strobe, continuously variable 1–25 Hz | P1 build ramp 2→12 Hz; P7 drop |
| SYS-REQ-04 | Smooth, visually stepless dimming at 5–10 % of full output | P2 outro, P6 intro |
| SYS-REQ-05 | Pulse-and-decay envelope: rise to 80 %, decay to 30 % over ~200 ms, repeating on every kick | P2 São Paulo funk lock |
| SYS-REQ-06 | Intensity tracking a continuously varying control signal (bass wobble) at up to ~20 Hz | P8 UK bass — *flagged as judgement*: the profile says "the lights should wobble too" without specifying a rate |
| SYS-REQ-07 | Clean, neutral white — not RGB-mixed white | P1, P4 white blasts; drives the RGBW-over-RGB decision |
| SYS-REQ-08 | Deep saturated colour at medium brightness (purple, cyan, magenta, hot pink, UV) | P2, P8 |

SYS-REQ-01 and SYS-REQ-04 pull in opposite directions and together set the hardest electrical
constraints: high peak current with fast edges, *and* fine low-end resolution without visible
stepping or flicker.

---

## 5. Power architecture and budget

### 5.1 Corrected budget — read this before designing anything

The earlier working assumption was "802.3af gives 12.95 W, a strobe needs ~13.7 W average,
close enough." **That does not close.** Two corrections:

1. **12.95 W is the PD *input* limit, not the usable output.** Skyworks AN956 (Si3402-B
   application note) states that at practical conversion efficiencies approximately **10 W of
   regulated power** is available to the application. Budget against 10 W, not 12.95 W.
2. **Carrier overhead comes out of that first.** ESP32-S3 + W5500 + magnetics + regulator
   losses. Allocate **1.5 W** until measured (*flagged as judgement* — verify on the first
   prototype).

**Usable sustained power for the light engine: ≈ 8.5 W per fixture on 802.3af.**

### 5.2 The burst/sustained distinction

A capacitor bank solves *peak* power, not *average* power. Storing 1 J and dumping it in 10 ms
delivers 100 W for that 10 ms — but repeating it at 12 Hz still draws 12 W continuously from
the rail, which the budget above does not support. Any fixture with a cap bank needs an
**average-energy governor in firmware**, not just storage in hardware. See `D-02`.

### 5.3 Rail topology

PoE PD input is nominally 37–57 V at the PD. Note that **the LM2596 and LMR33630 named in
Project Plan v1.0 §6.2 cannot be used on this rail**: the LMR33630 is a 3.8–36 V part per its
TI datasheet, and standard LM2596 is 40 V. Any converter on the PD rail needs ≥ 60 V rating
with margin. This is a correction to the plan, not an open question.

---

## 6. Open decisions — system level

| ID | Decision | Options | What closes it |
|---|---|---|---|
| **D-01** | 802.3af (Type 1) vs 802.3at (Type 2) | af: ~10 W usable, cheap switches, ~155 W switch budget for 12 fixtures. at: ~20 W usable, roughly doubles headroom, ~306 W switch budget and a materially more expensive switch. | Measured optical output of the chosen LED at the ~8.5 W sustained budget. If a 8.5 W-average strobe reads as underwhelming in a 5 × 7 m room, af is the wrong call and every carrier is affected. **Resolve first — it constrains every board.** |
| **D-02** | Where the strobe energy store lives, and at what voltage | (a) 12 V cap bank on the daughter board — the earlier assumption, needs ~33,000 µF for 1 J with a 12→9 V window. (b) Cap bank on the ~48 V PD rail — the same 1 J needs ~2,800 µF over a 48→40 V window, roughly a 10× capacitance reduction because stored energy scales with V². | Physical size and cost comparison of the two cap banks, plus whether the expansion connector should carry the PD rail at all. Option (b) is the strong candidate and reopens the connector definition. |
| **D-03** | Whether the UV bar needs a custom PCB at all | (a) Daughter board with a real driver. (b) Off-the-shelf 12 V UV strip switched by a single low-side FET. (c) Passive always-on strip, no board. | Whether the genre profiles require UV *modulation* or only UV *presence*. P8 uses UV as an atmospheric layer; P1/P7 do not use it at all. |
| **D-04** | Strobe colour capability | (a) White-only. (b) RGBW. | Cost per fixture against how often the profiles call for coloured blasts from the strobe specifically rather than from pars. |

---

## 7. Board inventory

| Brief | Board | Status |
|---|---|---|
| `01` | Carrier (universal) | Ready for design |
| `02` | Strobe daughter | Ready for design once `D-01`, `D-02` close |
| `03` | RGBW par daughter | Ready for design |
| `04` | UV bar daughter | Blocked on `D-03` |
| — | Laser daughter (STM32F4 + galvo) | **Not written.** Out of Phase 1 scope, and no settled decisions exist beyond "STM32F4 for the galvo path." Writing a brief now would be fabrication. Revisit after laser module selection. |

---

## 8. Reference documents

- `LUMINA_Project_Plan.docx` v1.0 — system architecture, operating modes, phasing.
  **§6.2 part suggestions are superseded by §5.3 above.**
- `LUMINA_Genre_Lighting_DeepDive.docx` v1.1 — the eight lighting profiles. This is the
  optical requirements spec; §4 above is only the hardware-relevant extract.
- ESP-IDF LEDC documentation (ESP32-S3 target) — PWM peripheral limits, see `01`.
- Skyworks AN956 / Si3402-B datasheet — PoE PD front-end reference design.
