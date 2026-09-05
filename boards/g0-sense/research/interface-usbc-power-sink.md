# interface: usbc-power-sink (g0-sense)

P1 research fragment, 2026-08-27. USB-C receptacle used for POWER ONLY:
5 V VBUS in, independent 5.1 k Rd on CC1 and CC2, D+/D- unconnected, no PD,
no VCONN, no alt mode. Machine-readable half:
`interface-usbc-power-sink.json`.

Adapted from `reference/interfaces/usbc-pd-sink.{md,json}` (T6 canon, shipped
board). Everything PD-specific was dropped; the delta list is section 4. New
numbers below were verified against the USB Type-C spec text directly (the
R2.0 PDF from usb.org, downloaded and read 2026-08-27), not from blogs.

## 1. Sources

| Tag | Document |
|-----|----------|
| TC2.0 | USB Type-C Cable and Connector Specification, Release 2.0, Aug 2019 (usb.org PDF, full text read 2026-08-27; section/table numbers below are from this release) |
| TA0357 | ST "Overview of USB Type-C and Power Delivery" (Rd 5.1k value canon, inherited from the reference fragment) |
| PI4 | Documented shared-Rd field failure: Benson Leung "How to design a proper USB-C power sink"; scorpia.co.uk 2019-06-28 Pi 4 CC analysis |
| GCT | GCT USB4085/USB4105 receptacle product specs (collective current nameplate; inherited from reference fragment - re-check against P3's exact part) |
| SI21-03 | Semtech "ESD Protection of USB Type-C Interfaces" (TVS-at-connector practice, inherited; working voltage re-derived for 5 V) |
| CC-PIPE | Pipeline-computed: `scripts/check_current.py` IPC-2152 table (`required_width_mm`, run 2026-08-27); `reference/jlc_capabilities.yaml`; `reference/stackups.yaml` JLC2313_1.6 |

## 2. The numbers that bind design

| # | Constraint | Value | Source |
|---|-----------|-------|--------|
| 1 | Rd, per CC pin | 5.1 kohm to GND on CC1 AND on CC2, two separate resistors, "independently terminated" | TC2.0 4.5.2.2.3.1 (quote below); TA0357 |
| 2 | Rd tolerance | +/-20% legal for a sink that never reads CC (Table 4-25 "±20% resistor to GND, 5.1 kΩ, can detect power capability: No"); fit ordinary 1% parts | TC2.0 Table 4-25 |
| 3 | Series elements in CC | none - anything in series adds to Rd; never tie CC1 to CC2 | TC2.0 Table 4-25 + PI4 |
| 4 | Current entitlement, CC-blind sink | default USB power only; as a Power Sinking Device (no data function): up to 500 mA. 1.5 A / 3.0 A require monitoring vRd (tSinkAdj) | TC2.0 4.5.2.3.1.1, 4.6.2.1 |
| 5 | Board VBUS budget | <= 0.5 A total (on-board + Qwiic reserve); design 0.5 A, fault/inrush sizing 1.5 A | requirements.md s3 + row 4 |
| 6 | VBUS capacitance at receptacle | <= 10 uF between VBUS and GND when not attached ("VBUS Capacitance, Maximum 10 μF", sink table) | TC2.0 Table 4-3 |
| 7 | cSnkBulkPd 100 uF | DOES NOT APPLY - PD-contract number, no PD here | TC2.0 (absence); reference fragment row 8 dropped |
| 8 | VBUS max voltage | 5.5 V at light loads (sizes TVS stand-off >= 5.5 V) | TC2.0 4.4.2 |
| 9 | D+/D- | may float; no termination requirement for an unimplemented UFP data function; board never enumerates (hence row 4) | TC2.0 4.6.2.1 (PSD has no data function by definition); USB 2.0 has no floating-DP/DM prohibition for non-devices |
| 10 | SBU1/SBU2 | float; open = >= 950 kohm, floating complies | TC2.0 Table 4-28 |
| 11 | VCONN / Ra | none on board - receptacle sink never sources VCONN; Ra lives in the cable plug (0.8-1.2 kohm) | TC2.0 4.4.3, Table 4-26 |
| 12 | Receptacle current | collective nameplate: land ALL 4 VBUS (A4/A9/B4/B9) + ALL 4 GND (A1/A12/B1/B12) contacts ganged | GCT (class rule, inherited) |
| 13 | Shield/shell | direct to GND at the connector, own vias into B.Cu GND pour; legs double as retention | TC2.0 3.2.1 note 6 (shield-GND bonded in every plug anyway); reference fragment practice |
| 14 | Board edge | mating face flush/proud of outline (>= 0.05 mm overmold clearance to product surface); top-mount = no cutout; ~13 mm edge swath clear of tall parts (ASSUMED from Fig 3-79 12.85 mm pitch) | TC2.0 Fig 3-80, Fig 3-79 |
| 15 | VBUS trace width, 1 oz outer | 0.800 mm min (1.5 A fault @ dT 10 C); 0.250 mm would cover 0.5 A steady | CC-PIPE check_current IPC-2152 |
| 16 | Creepage/clearance at 5 V | IPC-2221 band 0-15 V: 0.13 mm exposed lands (A6), 0.05 mm masked (B4); JLC 2L/1oz fab min 0.127 mm dominates | CC-PIPE check_creepage ROW_TABLE + jlc_capabilities.yaml |
| 17 | High-speed / diff pairs | NONE on this board - D+/D- unconnected, CC is DC, everything else is power/LED/slow logic | board definition; requirements.md s2 |

Spec quotes (TC2.0, exact text):
- 4.5.2.2.3.1: "Both CC1 and CC2 pins shall be independently terminated to
  ground through Rd."
- 4.5.2.3.1.1: "The port shall draw no more than the default USB power from
  VBUS. ... If the port wants to consume more than the default USB power, it
  shall monitor vRd."
- 4.6.2.1: "It attaches as a USB Type-C Power Sinking Device (PSD), after
  which the Sink may draw up to 500 mA." / "A Sink that takes advantage of
  the additional current offered (e.g., 1.5 A or 3.0 A) shall monitor the CC
  pins and shall adjust its current consumption within tSinkAdj."
- 4.5.2.2.3.2 legitimizes the whole architecture: "A USB 2.0 only Sink that
  doesn't support accessories and is self-powered or requires only default
  power and does not support USB PD may transition directly to Attached.SNK
  when VBUS is detected."

Consequence of getting Rd wrong (row 1/3): a single shared Rd (Pi 4 rev 1.0)
meets an e-marked cable's Ra on the second CC pin; the source reads an
Ra-class impedance on both lines, classifies the board as an AUDIO ACCESSORY,
and never enables VBUS. The board is dead with precisely the better cables
(all Apple / 100 W / 5 A cables are e-marked). One resistor stuffed instead
of two is a silent field failure, not a lab failure - lab cables are usually
not e-marked. With independent Rds the same cable is harmless (Ra parallels
the unused pin's Rd; the source reads the true Rd on the CC wire).

Safe design assumption for a board that never reads CC (row 4/5): budget
<= 500 mA total. Any compliant source - default Type-C host, legacy host via
A-to-C cable (56 kohm Rp in the plug, TC2.0 Table 4-25 area note 1), 1.5 A or
3.0 A Rp source - supplies at least default USB power once it sees Rd. The
1.5/3.0 A advertisements are a superset this board may not exploit; nothing
extra is needed to coexist with them. This board's honest load (MCU + sensor
+ LEDs, tens of mA, plus 100 mA Qwiic reserve) fits under 500 mA with 3x
margin.

Input capacitance (row 6): the binding number for a NON-PD sink is the
Type-C attach limit - 10 uF max effective between VBUS and GND at the
receptacle. One nominal 10 uF X5R (derates to ~6-8 uF at 5 V DC bias) plus
100 nF is compliant and plenty for an LDO front end; any larger bulk goes on
+3V3 after the LDO. The reference fragment's 100 uF cSnkBulkPd ceiling and
10-22 uF slew-rate sizing are PD-contract mechanics - dropped (section 4).

## 3. VBUS copper (2-layer, 1 oz outer - stackup JLC2313_1.6)

Computed with the pipeline's own IPC-2152 function (what check_current will
enforce at P8), copper 0.035 mm:

| Current | dT 10 C | dT 20 C |
|---------|---------|---------|
| 0.5 A (design) | 0.250 mm | 0.184 mm |
| 1.0 A | 0.500 mm | 0.369 mm |
| 1.5 A (fault/inrush dwell) | 0.800 mm | 0.563 mm |

The JSON power entry declares `current_a: 1.5, dt_c: 10` -> P5 netclass
generator sizes VBUS at 0.800 mm. Rationale: a PTC holding >= 0.5 A passes
~1.5 A for seconds before tripping; sizing the copper for the trip dwell is
free on this board and removes a fault-mode thermal question. 2 oz
(JLC2313_1.6_2oz) is NOT needed - do not pay for it.

## 4. Deltas vs reference/interfaces/usbc-pd-sink

Kept (class rules, re-verified applicable):
- Rd = 5.1 k, one path per CC line, no series elements (rows 3/4 there).
- CC wiring straight through, no crossover.
- Receptacle collective-nameplate rule: land/gang all 4 VBUS + 4 GND.
- TVS at connector BEFORE the resettable element; protection order
  connector -> TVS -> fuse -> bulk/regulator.
- Shell to GND directly on a bare single-ground board; SBU float.
- GND deliberately NOT a `power` entry; provisional-net-name exit-2 trap.

Adapted (same rule, new number for 5 V-only):
- `power`: 5.0 A / 20 V worked example -> 1.5 A (fault sizing) / 5 V. No
  VOUT entry (no pass-through output).
- `voltages`: 20 -> 5. check_creepage stays a no-op by design (was already
  below 30 V there; stated here so the checker has the number).
- TVS: working >= 22 V / clamp <= 34 V -> stand-off >= 5.5 V (TC2.0 4.4.2
  5.5 V light-load max), clamp << LDO abs-max input. 5 V parts (SMF5.0A /
  PESD5V0 class).
- Receptacle voltage-rating trap (48 V vs 20 V twins) -> moot at 5 V; any
  Type-C receptacle qualifies. Current rating also moot at 0.5 A but the
  gang-all-contacts rule stays.

Dropped (PD-only mechanics - no PD controller, no BMC, no contract):
- CC node capacitance 200-600 pF receiver budget (PD 5.8.6): CC here is a DC
  divider node, no BMC receiver exists. No CC caps needed at all.
- CC TVS >= 20 V working: the VBUS-short-to-CC threat at 20 V drove that;
  at a 5 V-only port a CC short to VBUS puts 5 V on a 5.1 k Rd (~1 mA,
  ~5 mW) - harmless. CC ESD protection is OPTIONAL here (user-facing
  connector; the two Rds already give a DC path; waiver recorded).
- cSnkBulkPd 100 uF ceiling + 30 mV/us slew-rate cap sizing: PD contract
  numbers. Replaced by the Type-C 10 uF attach limit (Table 4-3).
- E-marked cable documentation item (>3 A): board draws <= 0.5 A.
- DP/DM-shorted-at-chip trap + controller-specific rows (CH224 VDD dropper,
  sense pins, CFG straps): no controller exists. D+/D- are simply
  unconnected - they never become nets, so the diff_pairs auto-discovery
  trap cannot fire on this board (still documented in the JSON notes for the
  architect's merge decision).
- 5 A copper table / 2 oz stackup check: replaced by section 3.

## 5. Layout constraints binding THIS board

- Receptacle on a board edge, mating face flush with or slightly proud of
  the outline (TC2.0 Fig 3-80: >= 0.05 mm product-surface-to-overmold
  clearance; bare board -> zero setback). P2 should pin it via
  `placement.edges` + `placement.sides` (front).
- Prefer a TOP-MOUNT receptacle: no board-edge cutout needed at 1.6 mm.
  Mid-mount variants need a routed notch - avoid unless P3 has a stock
  reason (record it if taken).
- Keep a ~13 mm wide swath at that edge clear of tall parts so the plug
  overmold seats (ASSUMED width, derived from TC2.0 Fig 3-79's 12.85 mm
  recommended connector pitch).
- Solder every mechanical: THT shield legs get their own GND vias (retention
  + shield bond); SMD-anchor variants must have anchors on paste.
- VBUS pour/trace >= 0.8 mm from receptacle pads to TVS/fuse/LDO input;
  land all four VBUS contacts in one copper gang at the pad (no neck).
- Clearance: JLC 2L/1oz fab minimum 0.127 mm dominates at 5 V; keep the
  IPC-2221 A6 0.13 mm for exposed lands (any manufacturable footprint
  already does).
- ESD: CC/VBUS TVS choice per architect (VBUS TVS required by
  requirements.md s3; CC protection waived above). No data pins to protect.

## 6. ASSUMED (could not source, conservative defaults)

- ~13 mm board-edge keepout swath width (derived from informative Fig 3-79
  spacing, not a normative number).
- 1.5 A fault/inrush dwell current for copper sizing (PTC-class behavior;
  actual number depends on the architect's protection part choice - safe
  upper bound for any sane <= 1 A PTC).
- Receptacle class rows (collective nameplate, THT-leg retention) inherited
  from GCT-class parts; re-check the exact P3 part's product spec.
- JLC min clearance 0.127 mm taken from reference/jlc_capabilities.yaml
  (pipeline-pinned, not re-verified against jlcpcb.com today).

## 7. Open items for the architect

1. Merged-file `diff_pairs` policy: omit (auto-discovery finds nothing -
   D+/D- have no nets) or explicit []. Both safe here; omission recommended.
2. VBUS protection topology + parts (TVS stand-off >= 5.5 V, PTC hold
   >= 0.5 A) - brief delegates it; numbers above bound it.
3. Exact receptacle part at P3 (JLC-assemblable, top-mount preferred,
   16-pin USB 2.0 or power-only variant); re-verify its collective current
   clause and mounting style against section 5.
4. Confirm total VBUS draw stays <= 500 mA including the Qwiic reserve
   (requirements.md open question 2 reserved 100 mA - fits).
