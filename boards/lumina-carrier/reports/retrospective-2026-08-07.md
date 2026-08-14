# LUM-CAR-A retrospective review - 2026-08-07

**Task:** re-review the finished board; decide what needs rework and what will not work.
**Mode:** READ-ONLY by owner instruction ("dont change the board since it's already ordered").
Nothing on the board was touched. Renders, gate reports and the design doc were regenerated;
`state.json` records the four gate results and this review.

**What was reviewed:** the board is unchanged since commit `47c41ae`, and
`fab/lumina-carrier_gerbers.zip` hashes **`4e192c7e...aa050a`**, byte-identical to the
`sha256` recorded in `fab/order.json` for the uploaded package. So this review is against
the exact article that was fabricated, not a later edit of it.

**Order status:** batch **W2026073100331078**, **Shipped**, total 15.72 USD, qty 10,
`order_type 1` = **bare PCB only** (assembly was not part of this order). The API
`pcb/create` failures recorded in `state.json` are stale history - the order was placed by
hand through the JLC cart and is tracked normally.

---

## 1. Gate results today vs at sign-off

| Gate | At sign-off (2026-07-30) | Today (v2 checkers) | Change |
|---|---|---|---|
| `erc` | pass 0/0 | **pass 0/0** | - |
| `drc_routed` | pass 0/0 | **pass 0/0** | - |
| `verify` | **fail** 118 findings / 115 error | **fail** 132 findings / 108 error | composition moved; see s3 |
| `dfm` | pass 0 error / 87 warn | **fail** 1 error / 87 warn | one new check; see s4 |

Two things to be honest about up front:

1. **`verify` has never passed on this board.** It was `fail` at every one of its three
   attempts and the board went to P9, P10 and fabrication with it failing. That was a
   deliberate, recorded owner decision at H4 (the 94 `check_current` + creepage +
   return-path findings were each adjudicated and accepted), not an oversight - but the
   status board says `fail`, and it still does.
2. **H3 was never recorded.** `state.json` still lists checkpoint 3 as pending. H3 is
   optional by design, so nothing is blocked; it is a bookkeeping gap only.

The board did not change. **The checkers did.** Every T-step (T1-T10) landed *after*
2026-07-30, including T2 "gate blind-spot fixes" and T6 Batch I's new DFM checks. So the
deltas below are the v2 toolchain re-examining a v1 board - which is exactly what a
retrospective is for.

---

## 2. Verdict: will anything not work?

**One real electrical defect, already known: OI-1.** Everything else is either an
accepted-and-still-correct waiver, or an artifact of the checker rather than the board.

| # | Item | Verdict |
|---|---|---|
| **R1** | U21 buck has no HF input ceramic (OI-1) | **REWORK the assembled boards** |
| R2 | V48_RAW escape routed 0.250 mm from U22 pin 7 | rev-B copper fix; not a rework |
| R3 | MDI lands at 105.6 ohm, not 100 ohm | **works as-is**; fix the design data |
| R4 | +3V3 / LED nets unclamped (OI-2) | optional rev-B |
| R5 | 3 misattributed refdes, 86 silk-over-pad | cosmetic |

---

## 3. The `verify` findings, adjudicated

108 error-severity findings. They are not 108 problems.

### 3a. `check_current` = 94 - unchanged, previously accepted

51 `undersized_track`, 41 `insufficient_transition_vias`, 2 `pour_neckdown`. **Byte-identical
count to what the owner accepted at H4.** 0 of 44 companion vias were placeable; 33 of the
undersized are U10 escapes needing per-pin currents no datasheet publishes. No change, no
new information, no action.

### 3b. `check_creepage` = 11 errors - 8 are a units artifact, 3 are new and real

**The 8 that are not real.** `V48_RTN` to `V48_RAW`, gaps **0.657 / 0.658 / 0.660 / 0.662 /
0.666 / 0.672 / 0.680 / 0.745 mm**, all F.Cu, reported against a **0.80 mm** requirement
"for 114 V".

That 114 V does not exist on this board. `constraints.json` declares `V48_RAW: +57` and
`V48_RTN: -57`, so T2's new voltage-pair logic computes `dv = 57 - (-57) = 114 V` and
selects the 101-150 V IPC-2221 row. But the netlist says **U1 is the only part that touches
both `V48_RTN` and `GND`** - the TPS2378's return *becomes* system ground in this
non-isolated design. `V48_RTN` is the 0 V reference, not a -57 V rail, and two nets on one
57 V PoE bus cannot be 114 V apart.

At the true 57 V the requirement is **0.60 mm** (IPC-2221 B2). All eight gaps clear it, and
all eight also clear the board's own stricter **0.635 mm** house rule (tightest margin
+0.022 mm). **No rework. The defect is in `constraints.json`, not in copper.**

**The 3 that are real - and are new information.**

| Gap | Geometry | Against |
|---|---|---|
| **0.250 mm** | `V48_RAW` **track** -> **pad U22.7** (UVLO) | 0.60 mm |
| **0.350 mm** | `V48_RAW` **track** -> `/pwr/UVLO` **track** | 0.60 mm |
| **0.457 mm** | `V48_RAW` **track** -> **pad U22.7** | 0.60 mm |

These were never reported before T2 taught `check_creepage` to evaluate all pairs. All three
are **routed copper**, and that matters: the H4 waiver covering U22 was explicitly scoped to
*"package lead frames, not routing choices"*. These are routing choices, so they sit outside
the letter of the waiver the owner granted.

Scale of the miss: U22's own package floor is **0.375 mm** (`V48_RAW`/`+48V_SW` pads to GND
pad 21), and U20's is 0.295 mm. The routing is **0.125 mm tighter than the package it
serves** - so rerouting buys real margin, but only down to the package's own limit.

Real-world risk is low, not zero: 0.250 mm of mask-covered F.Cu at 57 V DC clears IPC-2221
**B4** (coated, 0.13 mm at 51-100 V) by ~1.9x. It fails the board's frozen ICD s5.1
(0.635 mm board-wide), and the B4 reinterpretation was deliberately **retracted** at H4
rather than adopted. **Rev-B item, not a rework** - the boards will run.

### 3c. `check_return_path` = 3 errors - previously accepted, and the count improved

Was 13, now 3 errors + 1 warning. T2's "return_path stackup reference resolution + waiver
class" fixed the structural false-fail where every GND-referenced B.Cu trace failed by
construction on an F/GND/+3V3/B stack. What survives is exactly the **J1 In1-antipad GND
deficit** the owner accepted at H4 (**1.33 / 2.09 / 5.56 mm2** on `/ETH_TXN`, `/ETH_RXP`,
`/ETH_RXN`). No action.

### 3d. Warnings worth naming (24 total)

- **16 creepage warnings** - every one a genuine pad-to-pad pair inside a single package
  (U1.9 to U1.x at 0.200 mm x7, U22.x to U22.21 at 0.375 mm x7, U20.3-U20.9 at 0.295 mm,
  C1.1-C1.2 at 0.590 mm). These are the H4-accepted lead-frame class, now correctly demoted
  from error to warning by T2's coating rows.
- **`check_diffpair` RX skew 4.50 mm / ~30 ps** (limit 2.5 mm). H4 accepted this at the
  then-measured **6.451 mm / 43.0 ps**; T2's via+pad graph re-measures it *lower*. The
  accept reasoning holds with more margin than it was granted on: 30 ps is 0.375 % of the
  8 ns 100BASE-TX unit interval. TX skew is 0.54 mm. No action.
- **`check_decoupling` x2** - C1's loop 13.7 nH vs a 10 nH class limit, and C1's ground pad
  10.1 mm from the nearest `V48_RTN` via. Both accepted at H4. Note these are on **U1**, not
  U21 - the checker still cannot see OI-1 (see s5).
- **`constraints_drift` (NEW)** - `architecture/constraints.json` diverges from
  `kicad/constraints.json`; checks ran against the latter. Housekeeping, but it is the file
  that produced the bogus -57 V above, so reconcile both when fixing it.
- **3 `silk_misattributed`** - `D23` (1.06 mm, reads as R73), `C35` (2.41 mm, reads as U10),
  `L21` (1.22 mm, reads as R61). C35 was the known residual from the P8 silk pass; D23 and
  L21 are newly visible. Assembly readability only.

---

## 4. The `dfm` regression is a tooling artifact - but it hid two dead checks

`dfm` now reports one error: *"Edge.Cuts present but does not form a closed outline"*. This
check did not exist at P9 (it arrived in T6 Batch I).

**The outline is not broken.** Measured: Edge.Cuts exports as 8 segments with 8 endpoints and
**zero dangling ends**. Three corner joints disagree by exactly **1e-6 mm - one nanometre** -
gerber round-off at the format's own resolution, roughly 1/100,000 of the fab tolerance.
Shapely's `polygonize` has no snap tolerance, so it returns nothing and the outline reads
EMPTY. Snapping at 1e-5 mm closes it immediately. JLC's own audit independently read
`setLength 100.0 x setWidth 80.0` off these very files.

**But the consequence is real.** `check_copper_to_edge` and the hole-to-edge leg of
`check_holes` both early-return on an empty outline - silently. So at P9, **`dfm` PASSED with
those two checks never having run**, and nobody could have known.

So I ran them. Patching the outline and re-running produced 2 `dfm_copper_to_edge` errors -
which then proved to be artifacts of my own patch: gerblib flattens the corner arcs to
**chords**, cutting each rounded corner ~0.879 mm inboard, and both hits sat exactly in those
corners. Rebuilt against the **true 3.0 mm-radius arc outline** (area 7992.27 mm2,
cross-checked against the `.kicad_pcb`'s own arc-aware outline at 7992.23 mm2, bounds
identical):

> **Zero copper-to-edge violations. Zero hole-to-edge violations.**

The board is clean on both. The remaining 87 warnings are 86 `silk_over_pad` + 1 silk width -
cosmetic, and JLC clips silk over pads in production anyway.

**Skill defects this exposes** (not board defects): `gerblib.FabStack.outline` needs a snap
tolerance before `polygonize`, and it should interpolate Edge.Cuts arcs instead of chording
them - the chording alone would generate two false `copper_to_edge` errors on every
rounded-corner board the moment the snap is added. **Every 4-layer board in this repo shares
this generator**, so `lumina-par`, `lumina-strobe` and `pd-trigger` should be re-checked once
it is fixed.

---

## 5. R1 - the one thing that needs a soldering iron

**OI-1: U21 (TPS563201, 12 V -> 3.3 V synchronous buck) has no HF input ceramic.** Severity
error, found by the P8 reviewer, invisible to `check_decoupling` because it classed the
22 uF part as *bulk* and applied the loose bulk distance limit.

Measured, and re-confirmed this session from the netlist and board geometry:

| | |
|---|---|
| U21 pin 3 = VIN (`+12V`) | abs (65.350, 112.050), board-rel (45.770, 54.917) |
| Nearest input cap C55 (22 uF 1206) | **9.89 mm Manhattan / 8.378 nH** |
| 100 nF or 1 uF ceramic at the pin | **none anywhere** |
| U21 pin 1 = GND | 1.900 mm from pin 3 - **pin 2 = SW sits between them** |
| Nearest GND via | **2.335 mm** at abs (65.882, 114.324), rel (46.302, 57.191) |

On a synchronous buck the input ceramic carries the full trapezoidal switch current with no
diode softening, and TI's layout section requires it directly across pins 3 and 1. The
consequence is several volts of VIN ringing every switching edge plus a large radiating loop
18 mm from J4 - on the converter feeding the ESP32-S3, the W5500, and J3 pins 12/14 to
**every daughter board**.

**Rework on the assembled boards.** Fit a 0402/0603 100 nF X7R (a 1 uF alongside it is
better) from U21 pin 3 to ground. Two anchors, both measured above:

- **pin 3 -> pin 1**, 1.9 mm, the electrically ideal loop - but the cap body must bridge
  *over* pin 2 (SW). Insulate it (kapton) or stand it off; a solder bridge to SW is fatal.
- **pin 3 -> the GND via at rel (46.302, 57.191)**, 2.335 mm, no part underneath. Slightly
  longer loop, materially safer to hand-fit. **Recommended.**

Either beats 9.89 mm by ~4x on loop inductance. Worth doing before bring-up rather than
after, and worth doing on every board in the batch.

**For rev B this is no longer a rewind.** OI-1 and OI-2 were deferred for exactly one reason
- OI-3, *"nothing in this pipeline can add a footprint to a placed board"*. **T8's
`board_update.py` closed that gap**: `add-part` does netlist-diff surgery that preserves
placement and routing. The caveat in the playbook is that its region scan for added parts is
**front-side only** - U21 is on the front, so this applies cleanly. Add the ceramics in the
schematic and to the `buck33` placement group (`anchor U21, members [L21, C55, C56, C57,
C58]`) and the annealer will hold them at the pin.

---

## 6. R3 - the stackup the board was designed to does not exist

The single biggest "is this even the board we verified" question, and it resolves benignly.

`reference/stackups.yaml` defined **JLC04161H-3313** (0.2104 mm 1080-equivalent prepreg over
a 1.065 mm core) and `architecture/stackup.md` called it *"the only stackup in
reference/stackups.yaml that publishes a 100 ohm differential profile"*. **That is what made
this board 4-layer**, and it produced the MDI geometry actually routed: **0.2597 mm trace /
0.2104 mm gap**.

**JLC has never offered it.** Verified live twice (2026-07-30 sweeping plateType 0-3 and
delamination 0-3; again 2026-08-06). `stackups.yaml` has since been corrected - 3313 is
marked `available: false`, `PHANTOM`, and the 4-layer default is now the real
**JLC04161H-1080B**.

What the shipped boards actually are, computed with the skill's own `impedance.py`:

| Stackup | L1-L2 | Z_diff of the as-built 0.2597/0.2104 geometry |
|---|---|---|
| 3313 (phantom - designed to) | 0.2104 mm | 100.00 ohm |
| **1080B (real, and JLC's 4L/1.6/1oz lamination)** | 0.2444 mm | **105.60 ohm (+5.6 %)** |
| 7628G (the other real option) | 0.5124 mm | 127.70 ohm (+27.7 %) |

The order was placed through the web cart with no impedance control requested
(`impedanceFlag` is hardcoded `no`), so JLC built to their standard 4L/1.6 mm lamination -
the 1080B family. **The MDI pairs are ~105.6 ohm.**

**This works.** The PHY is a W5500 - 100BASE-TX, 125 Mbaud, 3 ns edges. A 5.6 % mismatch
against 100 ohm is a reflection coefficient of 0.027, i.e. **~31 dB return loss**, against
Clause 25's 16 dB requirement. Cable itself is specified 100 ohm +/-15 %. Measured MDI
lengths are 62.9/62.3 mm (TX) and 65.8/70.3 mm (RX); at ~0.38 ns of one-way delay against a
3 ns edge these are barely transmission lines at all. **No rework, no rev-B copper change.**

Two things do need fixing, neither on the board:

1. The 4-layer decision's stated justification is now void - it rested on a stackup that
   does not exist. 4 layers is still right (plane discipline under the MDI corridor, the
   0.635 mm creepage envelope), but `architecture/stackup.md` should say so honestly.
2. **`lumina-par` and `lumina-strobe` inherit the same entry** and are both 4-layer. If
   either solved geometry against 3313, it has the same +5.6 % shift - and if either is
   faster than 100BASE-TX, that margin is not automatically free.

The already-recorded rule is the right one: *validate any impedance-controlled stackup
against the vendor's live template list BEFORE solving geometry against it, not at order
time.*

---

## 7. Ranked actions

**On the shipped boards**

1. **R1** - fit a 100 nF (+1 uF) ceramic at U21 pin 3, anchored to the GND via 2.335 mm
   away. The only rework that changes whether the power stage behaves.

**Before a rev B**

2. **R2** - reroute the `V48_RAW` escape off U22 pin 7; recover 0.250 -> 0.375 mm (the
   package floor).
3. **R4 / OI-2** - PESD on +3V3 near J3, and clamp the two RJ45 LED nets. Now cheap via
   `add-part`.
4. **R5** - three `move_text` ops for D23, C35, L21.

**Design data, not copper**

5. Fix `V48_RTN: -57` -> `0` in `kicad/constraints.json`; reconcile or delete
   `architecture/constraints.json`. This alone drops `verify` from 108 to 100 errors and
   removes eight false alarms from every future review.
6. Correct `architecture/stackup.md`'s 4-layer justification and re-derive against 1080B.
7. Check `lumina-par` and `lumina-strobe` for the same 3313 inheritance.

**Skill defects found by this review**

8. `gerblib.FabStack.outline`: add a snap tolerance before `polygonize`, and interpolate
   Edge.Cuts arcs rather than chording them. Until then, a `dfm` PASS does not prove
   copper-to-edge or hole-to-edge were ever evaluated. Re-check the other boards after.
9. `check_decoupling` still cannot see a missing HF input ceramic on a switching regulator -
   the exact defect class that produced R1. Its model is a decoupling loop; a buck input cap
   is not one.

---

## 8. What was checked and is genuinely fine

Worth stating so a future session does not re-spend effort here.

- Board outline, copper-to-edge and hole-to-edge: **clean** against the true arc geometry.
- `erc` 0/0 and `drc_routed` 0/0, re-run today against the shipped files.
- MDI differential impedance on the stackup actually built: 105.6 ohm, comfortably inside
  100BASE-TX.
- TX pair skew 0.54 mm; RX 4.50 mm / 30 ps - better than the figure H4 accepted.
- All 16 creepage warnings are package lead frames, correctly demoted.
- `check_current`'s 94 findings are unchanged from the set the owner adjudicated.
- Gerber package is byte-identical to what was uploaded and fabricated.
