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
- Rounded corners are **not** in the frozen v1 skill (the P5 outline was a
  hardcoded sharp rectangle). Support is being added centrally as a
  `--corner-radius` flag on `board_init.py`; it will be in place before any run
  reaches P5. Confirm the flag exists with `board_init.py --help` at P5 rather
  than assuming a default.

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
