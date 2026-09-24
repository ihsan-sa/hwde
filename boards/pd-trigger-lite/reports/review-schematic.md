# pd-trigger-lite - schematic review (P4, adversarial)

Fresh-context review of `kicad/pd-trigger-lite.kicad_sch` against
`architecture/decisions.md` (CH224A, 6-pin USB-C, Rset mode), the CH224A
manual extraction (`parts/C42459160.json`, tables 4-1/5-1, sections 5.2.1/
6.1.1/7.1), `parts/parts.json`, and a freshly-exported netlist. ERC and
netlist_audit are already 0/0; this pass looks for what those machines
cannot see. No `reference/checklists/` directory exists for this board (or
in this repo layout at all) - noted under OPEN, not treated as a gap in the
design itself.

## Verified correct (no finding)

- CH224A application circuit matches manual 6.1.1 exactly: VHV (pin 1) from
  VBUS with C1 1 uF/50 V X5R at the pin; VBUS-sense (pin 8) shorted to VHV;
  CC1/CC2 direct to J1 (Rd internal, matches decision D1); CFG1 (pin 9) to
  Rset network; CFG2/CFG3 floating is explicitly allowed in single-resistor
  mode (5.2.1); DP/DM/PG left unconnected is correct for a 6-pin
  power-only receptacle with PG's sink current unpublished (decision D6).
- Rset values match table 5-1 exactly: R1 6.8k=9V, R2 24k=12V, R3 56k=15V,
  R4 120k=20V, all 1% JLC Basic. As-shipped state (R5 0R fitted, JP1-3
  open) correctly requests 12 V with no stray resistance from the other
  three open branches.
- Every IC/passive rating clears 20 V operation: U1 VHV/VBUS/CC1/CC2 abs
  max 32 V vs 20 V applied; CFG1 abs max 3.8 V is never exposed to the bus
  (internal reference only); C1 rated 50 V vs 20 V bus; R6+D1 draw 1.8 mA /
  33 mW at 20 V (33 mW vs a 0603's ~100 mW rating - fine); R1-R4 carry only
  the CFG1 bias current, never the bus.
- Footprint/symbol pin correspondence checked pin-by-pin: J1
  (TYPE-C-6M-001) symbol pin names (A5/B5/A9/B9/A12/B12 + shell 1-4) match
  the footprint's named pads exactly - no silent swap possible. D1
  (KT-0603R): symbol pin 1=A, pin 2=K; footprint pad 2 (cathode) sits
  inside the chamfered-corner silkscreen box, pad 1 (anode) inside the
  square-cornered one - marking and pin numbering agree.
- Netlist confirms GND net picks up all 4 J1 shell stakes, U1's exposed
  baseplate (pin 11), and every board GND node; VBUS net ties C1, J1's two
  VBUS contacts, J2, R6 and U1 pins 1+8 together with no series element in
  the power path, as required.
- BOM is already lean for JLC Basic: every resistor/cap/LED is Basic;
  only U1 (PD sink IC) and J1 (matching 6-pin connector) are Extended, and
  neither has a Basic substitute. No cost-saving opportunity found.

## Findings

### WARNING: voltage-select network has no interlock against 0 or 2+ closed links
`kind: select-network-no-interlock` | refs: U1, R1, R2, R3, R4, R5, JP1,
JP2, JP3 | net: CFG1

The four Rset branches (R1..R4) share CFG1 and are individually gated to
GND by R5 (fitted, 0R) or JP1/JP2/JP3 (open). Nothing in the hardware
enforces "exactly one closed" - it's a silkscreen/assembly instruction
only:
- **Zero closed** (plausible mid-rework state: R5 desoldered before the
  new jumper is bridged) leaves CFG1 floating with no internal pull
  documented for that pin (unlike CFG2/CFG3, which have one) - the
  single-resistor-mode detection result is undefined in that state.
- **Two closed** (e.g. R5 left fitted while JP2 is also bridged) puts two
  Rset resistors in parallel - 24k || 56k = 16.9k here - which is not a
  table 5-1 value, so the requested voltage is whatever the chip
  interpolates to, not either labeled voltage.
Both states are reachable by an ordinary rework mistake and are invisible
to ERC/netlist_audit (both are electrically legal). Worth a silkscreen
note ("bridge the new link before lifting the old one") or, better, a
break-before-make caution in the assembly doc; not a fix to the schematic
itself.

### WARNING: no surge/transient protection on a 20 V hot-plug bus
`kind: no-transient-protection` | refs: U1, J1 | net: VBUS

Decision D4 already records this as an accepted risk ("hot-plug spikes at
20 V; the showcase added a TVS for this") and requirements.md confirms the
datasheet requires nothing beyond the 1 uF cap, so this is not schematic
drift - re-flagging only because the prompt asked specifically what could
be unsafe at 20 V. With no TVS, no fuse and no bulk cap beyond the 1 uF at
VHV, a connector hot-plug event at a 20 V contract has nothing to clamp
ringing before it reaches U1's VHV pin (32 V abs max, ~12 V of headroom at
20 V nominal - not a lot against connector/cable inductance ringing).
Given it's a recorded, deliberate decision, treat this as a risk to keep
watching in bring-up (does the board survive repeated hot-plug at 20 V),
not a blocking defect.

## OPEN
- No `reference/checklists/` directory exists anywhere for this board (or
  for pd-trigger-lite specifically) to apply per-domain checklists against
  - could not run that step of the protocol.
- Could not verify KT-0603R's forward-voltage / max-current spec against
  its own datasheet PDF (only the LCSC listing URL was available, not a
  cached parts/ extraction) - the 1.8 mA @ 20 V figure from blocks.md was
  taken as given and cross-checked only against a generic red-LED Vf
  assumption (~1.9 V), not the manufacturer datasheet directly.
- PCB-layout-level concerns (VBUS trace/via width for 3 A, board outline
  fit at <=25x15 mm, decoupling-cap physical distance to U1) are out of
  scope for a schematic-only review and were not assessed here.
