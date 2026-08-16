# LEARNINGS - bb-buck (workspace learnings)

Workspace-local. Every entry gets a date, tags (stage tag first: P0-P10), and a
one-line claim as its title. `learnings.py compile --workspace boards/bb-buck` turns new
entries into `learnings/queue.yaml`; the `promote` verb rules on them.
Research tasks (research.py close) append their entries here automatically.

## 2026-08-15 [P2][research][knowledge][block:B1] research task block-buck-1: 9 verified record(s) for block:B1
Gap: research block 'buck': populate selection, power-loop, emi, feedback, decoupling, return-path, thermal-via, inrush, sequencing, constraints-emission (application delta only - principle parents exist)
Operating point: {"board_layers": 2, "control_kind": "cmode", "fsw_khz": 400, "injection_kind": "none", "integration_kind": "integrated-fet", "iout_a": 2, "pdiss_w": 1.2, "rectifier_kind": "sync", "source_kind": "dc-input", "switching_kind": "hard", "vin_v": 30, "vout_v": 5}
Missing classes: selection, power-loop, emi, feedback, decoupling, return-path, thermal-via, inrush, sequencing, constraints-emission

Verified records (second reader signed). Promotion = the research verb's promote step (copies record + sources into the library), then the queue ruling with kind knowledge_record targeting reference/knowledge/records/<id>.yaml, then the owner's approval block:
- buck-cmode-inductor-window [selection] boards/bb-buck/research/records/buck-cmode-inductor-window.yaml
- buck-cmode-internal-comp-cout-window [feedback] boards/bb-buck/research/records/buck-cmode-internal-comp-cout-window.yaml
- buck-constraints-emission-layout-groups [constraints-emission] boards/bb-buck/research/records/buck-constraints-emission-layout-groups.yaml
- buck-dc-input-hot-plug-overshoot [inrush] boards/bb-buck/research/records/buck-dc-input-hot-plug-overshoot.yaml
- buck-ep-agnd-thermal-via-array [thermal-via, return-path] boards/bb-buck/research/records/buck-ep-agnd-thermal-via-array.yaml
- buck-integrated-fet-bypass-trio [decoupling] boards/bb-buck/research/records/buck-integrated-fet-bypass-trio.yaml
- buck-precision-en-fixed-softstart [sequencing] boards/bb-buck/research/records/buck-precision-en-fixed-softstart.yaml
- buck-sync-hot-loop-cin-placement [power-loop, emi] boards/bb-buck/research/records/buck-sync-hot-loop-cin-placement.yaml
- buck-two-layer-ground-shield-continuity [emi, return-path] boards/bb-buck/research/records/buck-two-layer-ground-shield-continuity.yaml
Sources (quarantined, sha-pinned in the task ledger):
- research/sources/lmr33630.pdf tier vendor-layout sha256 3b0920a4e56a <https://www.ti.com/lit/ds/symlink/lmr33630.pdf>
- research/sources/sluaal8.pdf tier vendor-appnote sha256 05ba68c6736a <https://www.ti.com/lit/pdf/sluaal8>
- research/sources/snva721a.pdf tier vendor-appnote sha256 293daf0da2cb <https://www.ti.com/lit/pdf/snva721>
Task file: boards/bb-buck/research/tasks/block-buck-1.json

## 2026-08-15 [P4][erc][kicad-sch-api][schematic] An ALREADY-retyped pulled library can still hide exactly one ERC-blocking pin: BOOT on a buck
The pulled `LMR33630ADDAR` symbol arrived with a sane typing pass already applied
(PGND/VIN/EP `power_in`, SW/VCC `power_out`, EN/PG/FB `passive`) - so the usual
"easyeda types are junk, retype everything" reflex reads as unnecessary here. It is
not: BOOT (pin 7) came typed `power_in`, and `/BST` has no schematic-visible driver
(the bootstrap diode VCC->BOOT is inside the package; the net's only other member is
C6, a passive). Measured with the fix disabled, `kc.py erc` on the finished sheet
returned EXACTLY ONE finding - `power_pin_not_driven` "Input Power pin not driven by
any Output Power pins" on U1 pin 7 - and zero of everything else, so the whole ERC
gate hung on that single library attribute.
Two ways out, and they are not equivalent. A PWR_FLAG on `/BST` clears ERC but leaves
the pin `power_in`, which pulls `/BST` into `netlist_audit`'s `power_undeclared`
warning - and `architecture/sheets.md` s4 deliberately leaves `/BST` undeclared
(a `power` entry would give a gate-charge node a width rule). Retyping the pin to
`passive` in `lib/aiee.kicad_sym` clears both, matches sbuck-5v3a's AP64350 BST pin,
and matches the standing retype rule (supplies/grounds power_in, regulator output
power_out, everything else passive - a bootstrap node is not the part's supply).
Done in `kicad/gen/lib_pin_types.py`, which lists only DEVIATIONS from the pulled
typing so a later `lib_pull` refresh cannot be silently re-typed wholesale, and which
`gen/root.py` calls before the symbol cache reads the library. Generalisation: judge a
pulled symbol pin-by-pin against the datasheet extract even when the file looks
already-fixed, and prefer the library fix over a PWR_FLAG whenever the net is one the
architecture deliberately leaves out of constraints.json.

## 2026-08-15 [P4][spice][sim-analyst] The runner's injected `rshunt=1e9` is a ~1 nA current source at every node - on a high-impedance FB divider that is 2 % of the IFB spec you came to measure
`sim_run.py`/`prepare_circuit` injects `.options rshunt=1e9` unless the deck sets rshunt
itself (it exists so one floating node cannot make the solve singular). On a 100k/24.9k
feedback divider the tap sits at 1.0 V, so the injected shunt quietly pulls 1 nA out of it
- and the datasheet term the bench exists to bound, LMR33630 IFB, is 50 nA max. The shunt
is therefore 2 % of the modelled worst-case error term, and it lands with the SAME SIGN
(it raises the implied VOUT by ~0.1 mV), i.e. it silently flatters nothing but does
contaminate a corner that is being reported to 5 digits. The deck has no floating node
(every node reaches ground through R2, the reference source or the amplifier), so the fix
is one documented line: `.options rshunt=1e12`, which drops the artefact to 0.1 uV and
made all 15 measures match closed form to 6 significant digits. Generalisation: on any
bench whose measured quantity is a sub-microamp current or a megohm-class node, treat the
injected 1e9 shunt as a real circuit element and override it deliberately.

## 2026-08-15 [P4][spice][sim-analyst] A switcher's DC setpoint IS simmable without any converter model - one high-gain VCVS is the whole Tier-B boundary model
Policy forbids simulating the buck (no vendor model, and an agent-authored switcher model
would not be honest), which reads as "the output voltage cannot be verified at all". It
can: the only thing the regulator does to the divider at DC is drive VOUT until
v(FB) == VREF, and that is one ideal amplifier - `Vref nref 0 DC {vref}` plus
`Eu1 vout 0 nref fb 1e8`. The network then SOLVES for the divider ratio instead of the
deck restating it, which is the whole point (a retyped `Vout = vref*(1+r1/r2)` B-source
would pass even if R1/R2 were wrong). Gain 1e8 leaves 50 nV of residual setpoint error, six
decades under any useful bound. Corners come from N `.subckt` instances (ngspice has no
`.step`), and `.meas dc <n> find v(<node>) at=0` against a 2-point `.dc` sweep of a dummy
source is enough analysis to make `.measure` legal - 11 corners + 4 derived params solved
in 1.0 s. Keep the as-drawn `--fragment` lines verbatim at the TOP level as the nominal
instance: it is the one bound that still fires if a later editor changes the schematic
values without touching the `.param` corner block.

## 2026-08-15 [P4][easyeda2kicad][parts][erc] An in-stock LCSC part can have NO EasyEDA CAD record at all - lib_pull fails it while its own family siblings pull clean
The A3 setpoint recentring needed YAGEO `RT0603BRD07102KL` (LCSC **C861068**, 2009 in
stock, full parametrics from `parts_search`). `lib_pull --lcsc C861068 C861257` pulled
C861257 and returned `status: error` / exit 1 for C861068 with only
"Failed to fetch data from EasyEDA API". That reads like the known WAF/rate-limit class
(LEARNINGS 2026-07-28), and it is NOT: probed directly,
`EasyedaApi().get_cad_data_of_component()` returns `{}` for C861068 and a full dict for
C861257 and C136967 in the same second. **Distinguish the two before retrying or backing
off** - a rate limit clears, an absent CAD record never will, and retrying just burns the
WAF budget. Fix used: derive the symbol from the just-pulled SAME-FAMILY sibling
(RT0603BRD0725K5L -> RT0603BRD07102KL, identity fields only: symbol name, Value, MPN,
Datasheet, `LCSC Part`), which keeps the pulled geometry and the shared `aiee:R0603`
footprint - defensible because a 2-pin chip resistor's symbol carries no part-specific
pinout to get wrong. Do NOT hand-draw a symbol for a part whose pinout is non-trivial;
there, change the MPN instead.
Second fact from the same pull, and the reason the ERC gate did not break: the freshly
pulled `RT0603BRD0725K5L` came typed **`unspecified` on both pins** while
`RT0603BRD07100KL` / `RT0603BRD0724K9L` - same YAGEO RT0603BRD family, pulled at P3 -
came typed `passive`. Pin typing therefore varies WITHIN one family by pull date, so the
`gen/lib_pin_types.py` deviation list has to be re-checked after every single pull, not
just after a wholesale library refresh.

## 2026-08-16 [P7][routing][planes_gen] planes_gen's DEFAULT thermal-relief pad connection strands a pad in a tight corridor - `connect: solid` in a planes-only sidecar is the fix
On this 2-layer board U1's PGND pin (pad 1, 1.3 x 0.6 mm) sits in a 0.79 mm-tall corridor
between the +VIN bulk-feed track above and the C1->VIN hot-loop track below. KiCad's default
zone `connect_pads` is THERMAL RELIEF, whose ~0.5 mm thermal gap is applied from BOTH the pad
and the neighbouring exposed pad, so the two gaps overlapped and no fill could form between
U1.1 and the EP. Result: `starved_thermal` (min spoke count 2, actual 1) PLUS a genuine
`unconnected_items` - U1.1 + C1.2 sat on their own 1.2 mm2 pour island, electrically off the
GND net, while F.Cu GND reported only "2 islands" and looked healthy. Re-pouring the same
region with `{"layer":"F.Cu","net":"GND","connect":"solid"}` in a planes-only sidecar
(constraints.json untouched) cleared both in one step and is independently correct here: the
EP is AGND and the datasheet wants it soldered SOLID to the plane. Two corollaries: (a) a
zone-fill island COUNT is not a connectivity check - only kicad-cli DRC is; (b) planes_gen
will not restyle an existing zone (>=80% existing-fill coverage -> skip), so the pour must be
regenerated from a clean board, not patched.

## 2026-08-16 [P7][routing][geometry] Read pad extents from `geom.pads_of().poly.bounds`, never from the raw `(size w h)` - the pad carries its OWN rotation
Three hand-computed track endpoints landed 0.2-1.3 mm outside their target pad because a naive
read of L1's `(pad ... (size 5.4 2.9))` ignored the pad's own `at` rotation: the real land is
2.9 wide x 5.4 tall (x 45.72..48.62, y 38.53..43.93), not 5.4 x 2.9. route_edit ACCEPTS such an
op - it only verifies the segment landed where asked - and the error surfaces two steps later as
`unconnected_items` + `track_dangling` naming a track by LENGTH, not by endpoint. Cheap guard
before emitting any route_edit op list: assert every add_track endpoint is `covered` by the
target pad's `poly`; the footprint rotation, the pad rotation and the board transform are all
already baked into it.

## 2026-08-16 [P9][bom_cpl][fab] A THT footprint with `attr through_hole` but no `exclude_from_pos_files` defaults to `smt_placed` - the terminals shipped in CPL.csv

bb-buck P9. `bom_cpl.py` decides BOM/CPL membership from `assembly_class`, and its
auto-classifier keys on `exclude_from_pos_files`, NOT on `attr through_hole`. The
easyeda2kicad KF128-5.08-2P screw-terminal footprint carries `attr through_hole` and no
pos-file exclusion, so both terminals were classified `smt_placed` and written into
`CPL.csv` - onto a pick-and-place list for a machine that physically cannot place them.

`bom_cpl` reported `status: pass`, `violations: []`, `bom_complete: true`. Nothing in the
pipeline flags it, because from the script's point of view a placed part with an LCSC code
and a position is exactly what a CPL row is.

Fix: `"assembly_class": "hand_install"` on the parts.json line (applies to every ref in
`refs`), plus `refdes_notes` for the assembler. Class counts then read
smt_placed 14 / hand_install 2 / board_feature 4, and CPL.csv drops to the 14 real
placements.

**Check the class split by eye on any board with THT parts** - `n_placed == n_parts` is not
the reassurance it looks like. Candidate script fix: treat `attr through_hole` as a
hand_install signal in the auto-classifier the same way `exclude_from_pos_files` is.

## 2026-08-16 [P9][gates][dfm] The dfm gate reported PASS with its BOM/assembly leg SKIPPED - `parts.json` was not beside the board

Same board, same phase. `gate.py --gate dfm` returned `status: pass` while
`coverage.skipped_error` carried `{"bom": "no parts.json"}`. The dfm gate is non-strict, so
a leg that cannot run does not fail it - it just quietly does not run.

The sidecar rule ("constraints.json, decoupling.json, parts.json, schematic resolve from the
board's OWN directory from P5 onward") is easy to half-apply: constraints.json and
decoupling.json get copied because earlier phases need them, and parts.json does not get
copied because nothing before P9 reads it from there.

The skipped leg is the one the dfm-check recipe calls "not waivable paperwork":
`dfm_bom_incomplete`, `dfm_assembly_unplaced_smt`, `dfm_assembly_qty_mismatch`,
`dfm_unplaced_in_package`. On this board it was skipped in exactly the same phase that a real
CPL defect existed (the THT terminals above), so the two failures were one bad day apart from
catching each other.

**Read `coverage.skipped_error` on every non-strict gate before believing `status: pass`.**
The release gates (`verify_release`/`dfm_release`) are strict for this reason - but P9 is not
a release gate, and the mode stops at P9.
