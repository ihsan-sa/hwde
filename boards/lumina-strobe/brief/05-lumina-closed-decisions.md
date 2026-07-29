# LUMINA - Closed Decisions & Cross-Board Constraints

**Date:** 2026-07-28 | **Authority:** project owner, via /ai-ee intake batch
**Status:** binding on every LUMINA board run. Supersedes the "Open decisions"
table in `00-lumina-system-context.md` section 6 for D-01, D-02 and D-03.

---

## Closed decisions

### D-01 - PoE class: **802.3at power stage, 802.3af classification for the first build**

A deliberate hedge. The stated closing criterion (measured optical output at the
8.5 W sustained budget) requires a prototype that does not exist yet, so the
decision is made non-fatal instead of guessed.

- PD front end, DC-DC converter, magnetics and thermal design are sized for
  **802.3at Type 2** (~20 W usable at the application).
- Classification is **programmed to Type 1 (af)** for the first build via the
  class-program resistor.
- The upgrade path is a resistor change plus a PoE+ switch - **no board
  respin**. Protect this: do not allow any other component to become the part
  that pins the design to Type 1.
- **Daughter power budgets are designed against the af figure: ~8.5 W sustained
  to the light engine** (10 W regulated minus 1.5 W carrier overhead, per `00`
  section 5.1).
- The carrier's power budget table (carrier review gate 2) must show **both
  columns**, af and at.

### D-02 - Expansion connector rails: **48 V raw + 12 V regulated + 3.3 V logic**

- **48 V raw** - the PD rail, switched/fused per CAR-REQ-14. Exists for the
  strobe's energy store: it collapses the bank from ~33,000 uF to ~2,800 uF and
  the drive current from ~8.3 A to ~2.6 A (STR-REQ-12).
- **12 V regulated** - for daughters that need a modest rail without duplicating
  a >=60 V converter on every fixture (the par, and any future low-power
  daughter). The carrier needs a >=60 V input converter for its own 3.3 V rail
  regardless, so 48->12->3.3 is the natural chain.
- **3.3 V logic** - daughter logic and sense only, never LED current.
- **CAR-REQ-17 is now active and binding:** the connector requires
  creepage/clearance appropriate to 48 V, and **every daughter board that taps
  the 48 V rail must carry a bleed path** for stored energy (STR-REQ-10).
- Inrush limiting remains the daughter board's responsibility (CAR-REQ-14,
  STR-REQ-09).

### D-03 - UV bar: **no board**

Resolved to option (c). The UV bar is not designed in this program.
`04-uv-bar-daughter-brief.md` is out of scope. Do not allocate connector budget,
PWM channels, enclosure provision or power budget for it.

---

## Still open

### D-04 - Strobe colour capability (white-only vs RGBW)

**Owner: the strobe board run.** Put it to the human in the P0 intake batch,
together with that board's other open questions. It is not a system-level
decision and must **not** be assumed by the carrier or the par run.

---

## Cross-board constraints

### ICD-01 - The carrier owns the expansion connector

The carrier run freezes the connector as an interface control document at its
**H1 architecture checkpoint**: connector part number, pin assignment, current
rating per pin, and the creepage scheme for the 48 V rail. It writes this to
`boards/lumina-carrier/architecture/connector-icd.md`.

**Daughter runs treat the frozen ICD as a hard input and never redefine it.** A
daughter that needs a change to the ICD raises it as a blocking issue and stops;
it does not implement a variant.

### MECH-01 - Rounded corners and mounting holes (project owner, this session)

Every LUMINA board has rounded board corners and mounting holes.

- Mounting holes are native to P5: `board_init.py --mounting-holes N` (0..4,
  M3 3.2 mm at the outline corners, flagged board-only so schematic parity
  ignores them). Use 4 unless the outline makes that impossible.
- Rounded corners: **`board_init.py --corner-radius R`** (mm). This was added
  centrally this session and is verified end-to-end. The default is 0 (square),
  so you must pass it explicitly. Use R = 3 mm unless the enclosure dictates
  otherwise.
- **The radius is clamped to the mounting-hole inset**, which is `margin / 2` -
  so 3.0 mm at the default `--margin 6`. Parts are packed on a shelf grid that
  already routes around the holes at that inset, so an oversized radius shrinks
  itself rather than relocating a hole (relocating collides with neighbouring
  courtyards). To get R > 3, pass a larger `--margin` (e.g. `--margin 10` gives
  inset 5 and allows R up to 5) and re-check the resulting size against MECH-02.
- The board_init report's `corner_radius` field states what you actually got and
  `worker_notes` records any clamp. Read both; do not assume the requested value
  was honoured.

### MECH-02 - Enclosure outline is still undefined

CAR-REQ-19 flags this as a genuine unknown, and ai-ee **has no outline-shrink
step - the P5 outline is final** (`--outline WxH` at board_init binds
permanently). Each run must therefore close its board outline in mm with the
human **at H1, before P5**.

The carrier and the daughters share one enclosure and mate through the
expansion connector, so the outlines are not independent. The carrier proposes
the common footprint and mounting-hole pattern at H1; daughters inherit it.

### DOC-01 - Design document is a required deliverable

Every run ends by generating its design document:

```
.venv\Scripts\python.exe .claude\skills\ai-ee\scripts\report_gen.py --workspace boards/<name>
```

-> `reports/design_doc/<board>-design-doc.pdf` (exit 0 required; exit 1 means
degraded - core artifacts missing or the compile failed, and must be resolved,
not waived). Verified working on this host.

### GIT-01 - Scoped commits, not `gate.py --commit`

Multiple LUMINA runs share one git working tree, and `gate.py --commit` runs
`git add -A` on the repo root, which would sweep other runs' ungated in-flight
files into this run's gate commit. **Do not pass `--commit`.** After each gate
pass, commit with a scoped add instead:

```
git add boards/<name> && git commit -m "ai-ee <name>: <gate> pass"
```

If the commit fails on `index.lock`, wait a few seconds and retry once - another
run is mid-commit. Never `git add -A`, never push.

---

## Closed at carrier H1 (2026-07-28)

H1 verdict: **approved**. The carrier proceeds to P3.

### H1-Q5 - Enclosure and isolation: **plastic, heatsink enclosed**
Non-conductive enclosure; the LED heatsink is NOT user-accessible. The
non-isolated PD topology stands - no isolated DC-DC, no earth path required.
Daughter boards must not expose a touchable heatsink or any conductor tied to
the 48 V rail through the enclosure wall.

### H1-Q8 - Wi-Fi: **functional, a supported control path**
**This is a deliberate deviation from carrier brief section 6**, which lists
wireless operation as out of scope and the radio as "a debugging fallback only,
Ethernet is the control path." The project owner overrode that at H1.

Consequences the carrier run must carry:
- ESP32-S3-WROOM-1 sits at a board edge with the full antenna keepout honoured -
  no copper, no pour, no plane under the antenna on any layer.
- RF review is now in scope at layout sign-off.
- The permanent outline must be settled with the antenna clearance already
  allocated, not retrofitted.

Open consequence for the project owner, outside this board's scope: the control
contract in `00` section 3 (UDP/IPv4 port 5568, 60 fps, <100 us packet-to-PWM)
is specified over Ethernet. A functional Wi-Fi path either honours that same
contract over Wi-Fi - with materially worse jitter and no PoE - or is scoped to
commissioning and diagnostics only. **The hardware is agnostic; the firmware and
host are not.** Raise this before firmware work assumes one or the other.

### H1-Q4 - Stack height: **11.0 mm, with a notch in every daughter**
Stocked 2.54 mm parts mate at 11.0 mm; the original 15 mm standoff is
unachievable without non-stock parts. At 11 mm the carrier's board-edge RJ45
(~13-16 mm) collides with the daughter.

**Binding on the strobe and the par:** every daughter board carries a
**30 x 26 mm notch** positioned to clear the carrier's RJ45. Treat the notch as
a hard mechanical requirement from P2 onward, not a late layout fix - and note
that ai-ee has no outline-shrink step, so it must be in the P5 outline. The
notch doubles as an anti-180-degree insertion interlock (CAR-REQ-16).

### H1-Q6 - Daughter rail current contract: **adopt the derived numbers**
The ICD publishes, and daughters design within:

| Rail | Sustained (af) | Sustained (at) | Pin rating | Protection |
|---|---|---|---|---|
| +48V_SW | 0.25 A | 0.5 A | 1.80 A/pin derated | eFuse limits at 1.0 A |

Derived from the power budget and 60% adjacent-pin derating (3 A single-circuit).
J3's 2x7 has **zero spare pins** - every extra 1.8 A of 48 V costs one more pin
and a re-issued ICD, so treat the allocation as fixed.

The strobe's peak flash current comes from its own on-board energy store, not
from this rail; the rail only has to recharge the bank at the average rate the
governor permits (STR-REQ-06).

### PD controller - supersedes the reference documents
`00` section 8 cites Skyworks AN956 / Si3402-B as the PD front-end reference.
**Si3402-B and Si3404 are Type 1 only** - no resistor programming reaches Type 2,
so the D-01 hedge is unachievable with them. The carrier uses a **TPS2378-class
PD controller plus a 100 V buck**. The "~10 W regulated" figure in `00` section
5.1 describes a part this design does not use; the budget was re-derived
(8.6-9.3 W af / 18.7-20.0 W at to the daughter, carrier overhead 2.4/3.7 W).

### Connector - GND is the binding rail
CAR-REQ-13 requires **7 GND pins** on J3. The brief's ">= 4 GND" in section 4.1
is below requirement. The frozen ICD is authoritative.
