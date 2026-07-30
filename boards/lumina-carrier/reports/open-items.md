# LUM-CAR-A - deferred open items (explicitly NOT fixed)

**Status:** recorded at H4 (2026-07-30) by owner decision. The owner's ruling was
**NO REBUILD** - the board keeps its P6 placement and P7 routing. Everything below is
deferred *because of that ruling*, not because it was judged unimportant. Two of the
three are deferred by the same mechanical cause: **nothing in this pipeline can add a
footprint to a placed board.**

---

## OI-1 - U21 needs an HF input ceramic at VIN. **Highest-priority rev-B item.**

**Severity: error.** Found by the fresh-context P8 reviewer; `check_decoupling` did
not report it.

U21 is a TPS563201DDCR synchronous buck, 12 V -> 3.3 V. It has **exactly one input
capacitor and it is 9.2 mm away**, with **no HF ceramic at the pin at all**:

| Measured | Value |
|---|---|
| C55, 22 uF 25 V X5R 1206, board-rel | (36.83, 55.87) / (40.01, 55.87) |
| C55 to U21 pin 3 (VIN) | **9.89 mm Manhattan / 8.99 mm euclidean / 8.378 nH** |
| 100 nF or 1 uF ceramic on U21 VIN | **none anywhere** |
| C52 / C53 (22 uF) | the 48->12 V *output* caps, 32+ mm away |

**Why the check missed it:** `check_decoupling` classed the 22 uF part as *bulk* and
applied the loose bulk distance limit. Its model is a decoupling loop. On a
synchronous buck the input ceramic carries the **full trapezoidal switch current with
no diode softening**, and TI's datasheet layout section requires it directly across
pins 3 and 1.

**Consequence:** several volts of VIN ringing on every switching edge, plus a large
radiating current loop **18 mm from J4** - on the converter that feeds the ESP32-S3,
the W5500 and J3 pins 12/14 to **every daughter board**. The reviewer's words: *the
worst power-stage layout defect on the board.*

**Why deferred:** the fix is to add a 100 nF + 1 uF 0402/0603 ceramic pair across
U21 pins 3 and 1. That is a **new footprint**, which forces a P4 schematic change and
then a full re-place and re-route (see OI-3). Owner ruled no rebuild.

**Rev-B action:** add the ceramics in the schematic, and add them to the `buck33`
placement group in `constraints.json` so the annealer keeps them at the pin -
`buck33` currently reads anchor `U21`, members `[L21, C55, C56, C57, C58]`.

---

## OI-2 - +3V3 and the RJ45 LED nets are unclamped

**Severity: warning, with a specific escalating path.**

There is **no PESD device on any LED net**. D31/D32/D40/D41/D42 all sit on expansion
signals; D10 (TPD4E1U06) clamps **only** the MDI pairs.

The path that makes this matter: `/poe/LED_Y_A` has exactly two pads - J1 pin 17 and
R7 pin 2 - and **R7 is a 330 ohm 0603 whose pin 1 is on +3V3**. So a breakdown from a
57 V PoE tap onto that net injects 57 V into **+3V3 through 330 ohm, unclamped**, and
+3V3 leaves the board on **J3 pins 12 and 14 to every daughter**.

The *geometric* half of this was fixed at H4: `/poe/POE_TAP_A2` to `/poe/LED_Y_A` went
from **0.2031 mm (226 pairs under 0.635 mm) to 1.1500 mm (0 pairs)**, and the new
`hv_tap_general_clearance` DRU rule now holds the line at 0.600 mm. So the trigger is
much less likely. But the *clamp* half needs a part.

**Why deferred:** a PESD diode on +3V3 is a new footprint. Same cause as OI-1.

**Rev-B action:** PESD on +3V3 near J3, and consider clamping the two RJ45 LED nets
where they leave the connector.

---

## OI-3 - Skill gap: there is no incremental board-from-netlist update

**This is the root cause of OI-1 and OI-2 both being deferred rather than fixed.**

- `board_init.py` regenerates the board **from scratch** - it does not sync a netlist
  into an existing `.kicad_pcb`.
- `place_edit.py` ops are `place / move / rotate / flip / lock / add_text / move_text`.
  **There is no `add_footprint`.**

Consequence: **any component addition after P5 costs the entire placement and the
entire routing.** On this board that is a P6 anneal plus a P7 route of ~3294 track
segments, and it would discard a hand-tuned oscillator island, four hand-solved 57 V
creepage geometries, 188 hand-widened tracks and a 111-op silkscreen pass - to add two
0402 capacitors.

That asymmetry is what forced the owner's no-rebuild ruling, and it will force the
same ruling on every future board that finds a missing passive at P8.

**Recorded as a known limit of the skill**, alongside the existing entry that
kipy/IPC is the KiCad-11 migration target. The natural fix is a
`place_edit add_footprint` op plus a netlist-diff step, so a late passive can be
added and locally routed without discarding the board.

---

## Also carried, already accepted at H4 (not defects to fix - listed so they are in one place)

| Item | Measured | Verdict |
|---|---|---|
| RX MDI intra-pair skew | 6.451 mm / **43.0 ps** | **ACCEPT.** 0.54 % of the 8 ns 100BASE-TX unit interval, ~1.9 deg at the 125 Mbaud fundamental, ~-35 dB mode conversion. Well inside Clause 25's ~1.4 ns jitter budget. The 2.5 mm rule is a gigabit-era heuristic. |
| 48 V intra-footprint DRU relaxation | U1 0.200, U22 0.250/0.375, U20 0.295, C1 0.590 mm | **KEEP**, enumerated per refdes, never wildcarded. Package lead frames, not routing choices. |
| J1 In1-antipad GND deficit on MDI legs | 1.33 / 2.09 / 5.56 mm2 | **ACCEPT.** Caused by +3V3 plane vias' clearance holes voiding the In1 fill under a frozen connector land. |
| `check_return_path` = 13 | all `corridor_void` | **STACKUP WAIVER CLASS.** On F / In1=GND / In2=+3V3 / B, the nearest plane to any B.Cu trace is +3V3, so every GND-referenced B.Cu run fails by construction. Unfixable without resolving the reference plane per signal layer. |
| `check_current` = 94 | 41 transition-via, 51 undersized, 2 pour-neck | **ACCEPT.** 0 of 44 companion vias placeable; 33 undersized are U10 escapes needing per-pin currents no datasheet publishes. |
| `check_creepage` = 10 | 0.200-0.375 mm | **ACCEPT.** Every one a pad inside a single package (U1 x7, U22 x2, U20 x1). |
| +12V trunk segment `e109de59` | 0.620 mm, ceiling 0.626 mm | **ACCEPT.** dT ~14.6 C at the 2.0 A OCP fault ceiling, ~5.0 C at the 1.25 A 802.3at sustained, ~1.6 C at 0.75 A af. 2.0 A x 12 V = 24 W exceeds the 18.5 W at-envelope, so it cannot be sustained from PoE. |
| Tightest tap clearance | +3V3 via to J1 pad 11, **0.6215 mm** | **ACCEPT.** Clears IPC-2221B B2 (0.600 mm) by 21.5 um; misses the board-wide 0.635 mm by 13.5 um. |
| ICD B4 question | - | **CLOSED by geometry, not by argument.** The B4 (coated, 0.13 mm) re-adjudication was retracted as contradicting frozen ICD s5.1; the pair was then physically rerouted to 1.1500 mm, so no IPC-row reinterpretation is needed. ICD s5.1 stands unchanged. |
