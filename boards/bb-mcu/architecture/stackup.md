# stackup.md - bb-mcu layer count, stackup, and why there is no outline here

## 1. Chosen stackup

**`JLC2313_1.6`** - JLCPCB standard 2-layer, 1.6 mm, **1 oz outer copper**,
HASL. `available: true` in `reference/stackups.yaml` (verified 2026-08-06) and
the `defaults: 2` entry, so `board_init.py` takes it by layer count with no
override needed.

```
F.Cu        0.035 mm   1 oz   signals + the +3V3 rail + every SMT part
dielectric  1.530 mm   FR4 core, er 4.5 (ASSUMED FR4 value, not JLC data)
B.Cu        0.035 mm   1 oz   UNBROKEN GND pour: return path AND reference
                              total 1.6 mm
```

Rejected by name, so a later phase cannot pick them up by accident:
`JLC04161H-3313` (PHANTOM - never sold) and `JLC04161H-7628G` (withdrawn
2026-08-06) are both `available: false`, and `board_init` / `rules_gen` REFUSE
them by name. `JLC2313_1.6_2oz` is real and available but is rejected here on
its merits: 2 oz exists in the library for a 5 A path that could not otherwise
be routed (`pd-trigger`); the widest requirement on this board is 0.1 A.

## 2. Layer count: 2, and this is not a close call

| Driver | Verdict on 2 layers |
|---|---|
| **Controlled impedance** | **Not needed, and not purchasable.** See s3. |
| **Reference plane** | **One is enough, and 2L provides it.** The only nets wanting a reference are SWDIO/SWCLK, and that is ADVISORY (`blocks.md` s3), not a rule. An unbroken B.Cu pour 1.53 mm below F.Cu is the reference, and single-sided assembly reserves the whole bottom face for it. |
| **Routing density** | **Trivial.** 9 electrical parts, 10 nets, one IC in a 0.65 mm-pitch TSSOP-20 whose used pins fan out to three edges from three separate regions of the package (`blocks.md` s4). No BGA, no bus, no crossing pair. |
| **Current** | **Nothing to route.** 0.1 A on 1 oz needs less width than the fab's own minimum; `rules_gen` buckets `+3V3` into Default. |
| **Thermal** | **Not a driver.** 0.33 W at the budget CEILING and ~0.07 W realistically, no exposed pad, no via array; Tj lands at 83-100 C worst-case-of-two-guesses against a ~105 C limit, and 57-65 C at the real figures (`power_tree.md` s4 does the arithmetic). The contrast with `bb-buck` - where 4 layers was a live escalation trigger - is the point: here there is no trigger and no escalation condition to write. |
| **Planes wanted** | **One (GND), and 2L gives it.** There is no second plane-worthy net: `+3V3` is a 0.1 A rail with four caps on it, not a plane candidate. |

**There is no 4-layer escalation condition on this board.** Not "unlikely" - it
does not exist. `bb-buck`'s stackup.md carried an explicit numeric trigger
because its junction temperature was 2.1 C from failing at a power figure that
P3 could plausibly move. Here the only quantity that could move is the current
budget, and 4 layers would not help it: a TSSOP-20 with no exposed pad has no
thermal path into an inner plane to buy. There is nothing a trigger could
trigger, so writing one would be theatre.
AN4325 5.1/5.2's preference for "a multilayer board with dedicated GND and VDD
layers" is explicitly qualified by ST itself as not always economical, and is
informational here - `requirements.md` s5 says this board's layer count is
earned, and 2 is what it honestly needs.

## 3. Controlled impedance: JLC sells none on 2 layers, and nothing here wants one

`JLC2313_1.6` carries `controlled_impedance: []`, with the provenance recorded
in `stackups.yaml`: JLC's `getImpedanceTemplateSettingList` returns **zero
templates for `stencilLayer=2`** at 1 oz AND 2 oz, live-verified 2026-08-06,
because JLCPCB offers no impedance-controlled 2-layer product at all.

**That is the layer-count justification, not an apology.** Nothing on this
board is a transmission line: the fastest edge the MCU can produce is 5 ns,
reflections on a 40 mm trace settle in ~1.5 ns, and SWD samples 125 ns later at
the 4 MHz bench ceiling (80x margin; 14x at STLINK-V3's 24 MHz). A 50 ohm
single-ended target on this stack would need a ~2.7 mm trace - a number no fab
would honour and no signal here asks for.

**No `impedance_ohm` key appears anywhere in `constraints.json`, and none may
be added.** Inventing a 50 ohm target is precisely how a fake requirement would
propagate into P5 rules and P7 routing on a stackup that cannot deliver it.

`epsilon_r 4.5` is an ASSUMED FR4 value, not JLC data. Nothing on this board
depends on it - no impedance, no length matching, no delay budget that is not
already 80x oversatisfied.

## 4. Copper pours - the 2-layer default is correct, so `planes[]` is absent

`constraints.json` declares **no `planes[]` section**. `planes_gen`'s 2-layer
default is a B.Cu GND pour, which is exactly right here, and declaring a
`planes[]` list would REPLACE the defaults entirely - a foot-gun for zero gain.

No F.Cu GND pour is declared either. On this board the top face carries the
whole circuit and every SMT part; a top pour would buy no thermal path (there
is nothing to cool) and no additional reference (B.Cu already is one), while
adding fragmentation and neck findings around a 0.65 mm-pitch escape. If P7
judges a top pour worthwhile after routing, that is a P7 decision with the
routed board in front of it - not a P2 constraint.

**Note for anyone who edits `planes[]` later:** `planes_gen` validates each
entry against a fixed key set and raises on ANY unknown key, INCLUDING the
`_note` convention used elsewhere in this repo. Put the reasoning here, not in
the entry.

## 5. Outline: there is none, by design

**No dimension appears in this package.** Binding is `canonical`, so geometry
is an OUTPUT:

1. `board_init --outline auto` at P5 - generous provisional room. It will
   REFUSE a fixed `--outline WxH` because the workspace's recorded mode makes
   geometry an output, and that refusal is the mechanism working, not an error.
2. Place at P6 to the canonical layout, pass the `place` gate.
3. `board_edit --outline fit --margin M` - the board becomes what the placement
   needs. Re-run `planes_gen` if it GREW.
4. Route at P7.

**Nothing was relaxed at P2.** The brief states no size, so there is no stated
value to lose and no `state.py decision` to record for a relaxation - the
contrast with `bb-buck`, where P2 derived 40 x 30 from R_ba and H1 handed P5
35 x 25. Any dimension introduced at a later checkpoint on THIS board is a
preference that LOSES to the earned layout, with the loss recorded.

What the placement is spending, in place of a number, is enumerated in
`blocks.md` s6: three THT connectors on three different edges (the perimeter
floor, and the largest claim), decoupling tight to the supply pins, R1 in the
pin-1 window, and four M3 clearance holes with washer keepouts - the one item
that can push the earned outline past what the electronics need, with the
4-vs-2-hole call belonging to P6.

**Deliberately no planning figure is offered.** `requirements.md` s5 says a
number here would be an anchor with nothing behind it, and the P2 job under
this binding is to state what the layout NEEDS, not to guess what it will get.

## 6. Fab class and verification status

- **Class: the cheapest standard tier JLC sells.** 2 layers, 1.6 mm, 1 oz
  HASL, soldermask, no controlled impedance, no blind/buried vias, 0.3 mm
  minimum drill, geometry well inside the standard 5/5 mil class. The board
  area is unknown by design but cannot approach the 100 x 100 mm ceiling of
  JLC's headline price tier, so the PCB sits at the floor price for a 5-piece
  order whatever the placement earns.
- **`coating: "soldermask"`** is declared in `constraints.json`. It is the
  physical truth (no conformal coating - `requirements.md` s4) and it selects
  the IPC-2221 Table 6-1 row for `check_creepage`. With nothing on the board
  above 3.3 V, `check_creepage` is a clean no-op either way.
- **`JLC2313_1.6` provenance is `vendor_page`, not a live API read - and that
  is correct rather than weak.** JLC returns zero impedance templates for
  2-layer boards because it sells no such product, so there is nothing to read
  back. The physical stack (1.6 mm, 1 oz, HASL) is the standard catalogue item.
- **The offering churns** - `JLC04161H-7628G` was real on 2026-07-30 and gone
  by 2026-08-06 - but this board depends on no impedance template at all, so
  there is nothing here for a churn to invalidate.
