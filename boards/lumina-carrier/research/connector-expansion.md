# Expansion connector - candidate scan (LUM-CAR-A, block `connector-expansion`)

Date: 2026-07-28. Source: `parts_search.py` live JLCPCB search (all rows below were
returned live today, `source: "live"`; nothing here is from memory). Machine-readable
copy with full `lcsc`/`mpn`/`basic`/`stock`/`price`/`datasheet` records:
`research/connector-expansion.json`.

Feeds ICD-01 (`architecture/connector-icd.md`, frozen at H1). Constraints applied:
CAR-REQ-13 (>=50 % current margin), CAR-REQ-15 (standoff -> stack height),
CAR-REQ-16 (keying), CAR-REQ-17 (48 V raw, 57 V worst case, adjacent to logic),
section 7 assembly assumption (JLCPCB PCBA, top side, 8-14 units).

---

## 1. Headline

**Recommendation: split it into two connectors, both 2.54 mm CONNFLY DS1021/DS1023.**

| | Part |
|---|---|
| Power block, carrier (male) | **DS1021-2x7SF11-B / C7430403** - 14 pos, 250 V, 3 A/pin, THT |
| Power block, daughter (socket) | **DS1023-2\*7SF11 / C113344** - 14 pos, 600 V, 3 A/pin, 8.5 mm |
| Signal block, carrier (male) | **DS1021-2x12SF11-B / C7430408** - 24 pos, 250 V, 3 A/pin, THT |
| Signal block, daughter (socket) | **DS1023-2\*12SF11 / C92265** - 24 pos, 600 V, 3 A/pin, 8.5 mm |

**Total 38 positions (14 power + 24 signal).** Carrier BOM cost $0.22/board at qty 50.

The two numbers that decide it:

- **Rated working voltage 250 V** (male; socket 600 V - the pair is bound by the lower
  number). That is **4.4x** the 57 V worst case. Every fine-pitch mezzanine family JLC
  actually stocks rates **50 V or 60 V** and fails or barely grazes CAR-REQ-17 (section 4).
- **3 A/pin single-circuit -> 1.8 A/pin with a 60 % adjacent-pin derate.** Arithmetic in
  section 3. 3 pins carry the 48 V rail's 4.5 A requirement with 20 % spare.

**Runner-up: a single DS1021-2x20SF11-B / C7430416 + DS1023-2\*20SF11 / C132132 pair**
(40 pos, same ratings, best-stocked count on LCSC: 3 028 / 8 845). Electrically identical
and simpler as an ICD. It is rejected on two mis-mating failure modes, not on ratings -
see section 5. Choose it only if the mechanical answer forces one connector.

**Loudest finding:** a 15 mm board-to-board stack is **not reachable** with an ordinary
2.54 mm header/socket pair. Standard hardware mates at **11.0 mm**. See section 6 - the
human's Q4 standoff answer probably has to move to 11 mm, or the connector has to become
a PC/104-class stackthrough (which only exists in 2x20 and 2x40, i.e. it forces the
single-connector scheme).

---

## 2. Ranked candidate table

Stock/price are today's live figures. "Vrated" = the manufacturer's own rated working
voltage as published on the LCSC part record; "-" = not published (a real strike against
a part whose job is to carry 48 V).

| # | Role | MPN | LCSC | Pitch | Pos | Vrated | A/pin | Type | Stock | $ @1 / @50 | Rationale |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | **PICK** power, carrier | DS1021-2x7SF11-B | C7430403 | 2.54 | 14 | **250 V** | 3 A | Ext | 5 575 | 0.085 / 0.068 | 4.4x voltage margin, 3 A/pin, THT strength, deep stock, whole family shares one footprint |
| 1 | **PICK** power, daughter | DS1023-2\*7SF11 | C113344 | 2.54 | 14 | **600 V** | 3 A | Ext | 3 922 | 0.156 / 0.122 | Mates #1; 8.5 mm body sets the 11 mm stack |
| 1 | **PICK** signal, carrier | DS1021-2x12SF11-B | C7430408 | 2.54 | 24 | 250 V | 3 A | Ext | 3 652 | 0.134 / 0.107 | 20 signals + 4 GND with zero spare pins wasted |
| 1 | **PICK** signal, daughter | DS1023-2\*12SF11 | C92265 | 2.54 | 24 | 600 V | 3 A | Ext | 2 313 | 0.222 / 0.174 | Mates #1 |
| 2 | Runner-up, single, carrier | DS1021-2x20SF11-B | C7430416 | 2.54 | 40 | 250 V | 3 A | Ext | 3 028 | 0.231 / 0.184 | Same ratings, one part, 7 spare pins; loses the free keying |
| 2 | Runner-up, single, daughter | DS1023-2\*20SF11 | C132132 | 2.54 | 40 | **600 V** | 3 A | Ext | 8 845 | 0.481 / 0.376@10 | Best-stocked socket found in any family |
| 3 | 15 mm stackthrough | 2.54-2\*20P Female longPC104 | C35165 | 2.54 | 40 | - | 3 A | Ext | 5 333 | 1.03 / 0.75@30 | 8.3 mm body + **12.3 mm tails** = the only stocked route to a ~15 mm stack; 2x20 / 2x40 only |
| 3b | 15 mm stackthrough alt | PC104-2\*20 | C5307344 | 2.54 | 40 | - | 2.5 A | Ext | 862 | 0.98 / 0.65@40 | Second source for #3; 2.5 A, thinner stock |
| 4 | Budget 2.54 pair | 2541WV-2x20P / 2541FV-2x20P-B | C25503140 / C25503128 | 2.54 | 40 | **-** | 3 A | Ext | 4 068 / 5 891 | 0.136 / 0.109 | 40 % cheaper than #2 but **no published working voltage** - weak CAR-REQ-17 evidence for a 48 V pin |
| 5 | Pure-SMT 2.54 pair | PZ254-2-20-S / HC-PM254-8.5H-2x20PS | C3294478 / C22436166 | 2.54 | 40 | 250 V / - | 3 A | Ext | 1 586 / 3 214 | 0.47 / 0.33@30 | Avoids JLC through-hole hand-solder cost; SMD pads take the mating force - worse for a repeatedly-mated connector |
| 6 | 2.00 mm pair | A2211WV-2X20P / 2.0-2\*20PM | C338696 / C110426 | 2.00 | 40 | 250 V / - | 2 A / 3 A | Ext | 3 468 / 2 425 | 0.36 / 0.31@10 | Voltage OK, but socket is only 4.3 mm -> **max ~6.5 mm stack**, and 2 A/pin needs more 48 V pins. Fails CAR-REQ-15 geometry |
| 7 | 1.27 mm, signal only | X1321FVS-2x20-C43D48 | C2881867 | 1.27 | 40 | 250 V | **1 A** | Ext | 1 641 | 0.96 / 0.77@10 | The only 1.27 mm part found that publishes 250 V. 1 A/pin and a 4.3 mm stack rule it out for 48 V/12 V; viable **only** as the signal half of a split |
| 7b | 1.27 mm male | HC-PZ127-7.2L-2x10PS | C41375929 | 1.27 | 20 | - | 1 A | Ext | 2 013 | 0.16 / 0.13 | Mate for the 1.27 mm option; no published voltage |

Everything above is **JLC Extended**. `parts_search --basic-only` over the connector
keyword space returns **zero** rows - there is no JLC Basic part in any of these
families, so "prefer Basic" is not achievable for this block and should not be held
against the pick.

---

## 3. CAR-REQ-13 current arithmetic (show-your-work)

Inputs (Q6 default, **human-unconfirmed**): 48 V raw 2 A continuous / **3 A capability**,
12 V 2 A, 3.3 V 0.5 A.

Per-pin base rating: **3 A** (CONNFLY DS1021/DS1023, 2.54 mm, gold-over-copper-alloy).
That is the usual single-circuit-energised figure. For a fully loaded two-row connector,
apply an adjacent-pin derate; **60 %** is the conservative working number, 70 % the
optimistic one:

- 60 % -> **1.80 A/pin**
- 70 % -> 2.10 A/pin

| Rail | Worst case | x1.5 (CAR-REQ-13) | Pins needed @1.8 A | Pins allocated | Capacity @1.8 A | Margin over worst case |
|---|---|---|---|---|---|---|
| 48 V raw | 3.0 A | **4.5 A** | 2.5 -> 3 | **3** | 5.4 A | **80 %** |
| 12 V | 2.0 A | 3.0 A | 1.67 -> 2 | **2** | 3.6 A | 80 % |
| 3.3 V | 0.5 A | 0.75 A | 0.42 -> 1 | **2** | 3.6 A | 620 % |
| GND (return for all three simultaneously) | 5.5 A | **8.25 A** | 4.58 -> 5 | **7** | 12.6 A | 129 % |

Two things the architect should not skip:

1. **GND is the binding rail, not 48 V.** If all three rails are at worst case at once,
   the shared return carries 5.5 A, and CAR-REQ-13's 50 % margin makes that 8.25 A -
   which needs **5 pins minimum**. The brief's ">= 4 GND" is *below* what CAR-REQ-13
   requires. Allocate 7 in the power block (plus 4 signal-return GNDs in the signal
   block, 11 total).
2. The 50 % margin is applied to the **3 A capability** figure, not the 2 A continuous
   figure, per the assignment wording. If Q6 comes back with a higher 48 V peak, each
   +1.8 A of requirement costs exactly one more pin - a 2x7 has no spare, so a Q6 answer
   above 3 A pushes the power block to 2x8 or 2x9. Both exist but stock is **much**
   thinner than 2x7: DS1021-2x8 C7430404 (370), DS1021-2x9 C7430405 (246),
   DS1023-2\*8 C92267 (**47**), DS1023-2\*9 C132125 (4 609). Enough for 14 units, not
   enough to be casual about - another reason to get Q6 answered before H1.

---

## 4. CAR-REQ-17 - working voltage is where the fine-pitch families die

Every board-to-board/mezzanine part JLC stocks below 1.27 mm pitch was checked. Their
own published working voltage:

| Family | MPN / LCSC | Pitch | **Vrated** | A/pin | Verdict |
|---|---|---|---|---|---|
| Panasonic AXK | AXK5F80337YG / C425110 | 0.5 mm | **60 V** | 500 mA | **REJECT** - 3 V above the 57 V worst case, no derating headroom |
| Panasonic AXK | AXK724147G / C114816 | 0.4 mm | **60 V** | 300 mA | **REJECT** - same |
| Hirose FX10 | FX10A-168S-SV / C598051 | 0.5 mm | **50 V** | 300 mA | **REJECT** - below 57 V |
| Molex | 555600207 / C127345 | 0.5 mm | **50 V** | 500 mA | **REJECT** - below 57 V |
| Molex | 5054730810 / C127347 | 0.4 mm | **50 V** | - | **REJECT** - below 57 V |
| Hirose BM22 | BM22-6S-V(51) / C92283 | - | **50 V** | 300 mA | **REJECT** - below 57 V |
| TE | 3-1827253-6 / C194182 | 0.5 mm | **50 V** | 500 mA | **REJECT** - below 57 V |
| HCTL SHD | HC-SHD-2\*20PLT-G-04 / C5342484 | 1.0 mm | **50 V** | 1 A | **REJECT** - below 57 V |
| Samtec QTH/QSH | C116054 / C2909821 | 0.5 mm | **175 V** | 2 A | Passes voltage; **rejected on cost** - $8.72 + $6.58 per mated pair, stock 229/310. Two of them is >50 % of the $30/carrier target (Q15) |

So: **the fine-pitch mezzanine route is closed** for anything except Samtec, and Samtec
is closed on cost. This is the single most consequential result of the scan and it is
what pushes the answer back to 2.54 mm.

Geometry of the recommended 2.54 mm pick, for the sibling agent deriving IPC-2221B mm:

- **Pitch:** 2.540 mm, both directions (row spacing = pitch).
- **Pin-to-pin air gap:** 2.54 - 0.64 (square pin across flats) = **1.90 mm**.
- **PCB pad-to-pad copper gap:** ~0.84 mm with a 1.70 mm annulus on a 1.02 mm drill,
  ~1.14 mm with a 1.40 mm annulus. The *pad* gap, not the pin gap, is the tight number
  and it is the layout designer's lever.
- **Manufacturer working voltage: 250 V (male) / 600 V (socket).**

For contrast, the 1.27 mm option (#7): pin gap ~0.87 mm, pad gap ~0.5-0.65 mm, published
250 V. Electrically defensible; killed by 1 A/pin and 4.3 mm stack height, not by creepage.

---

## 5. CAR-REQ-16 keying - why split beats single

Both schemes are electrically fine. The split wins on failure modes:

1. **Keying comes free and is mechanical.** A 2x7 and a 2x12 at fixed asymmetric board
   positions cannot be cross-mated, cannot be mated rotated 180 deg, and cannot be mated
   to each other. A single 2x20 has no intrinsic key - it needs a plugged-position key
   (a manual operation JLC will not do) or it depends entirely on the standoff pattern.
   Note MECH-01's default 4x M3 pattern is **symmetric** (90 x 70 rectangle), so a
   daughter can physically be bolted down rotated 180 deg. With one centre-line
   connector that mis-orientation mates.
2. **One-position mis-seat is contained.** This is the real safety argument, and it
   speaks to CAR-REQ-14 as well as CAR-REQ-16. Offset a single 2x20 by one position and
   **48 V lands on an ESP32-S3 GPIO**. Offset the 2x7 power block by one position and
   48 V lands on 12 V or GND - all power pins, all rated for it, and the carrier's
   current-limited high-side switch sees it as a fault, not the MCU.
3. **48 V is physically away from logic**, so CAR-REQ-17 becomes a placement problem
   solved by tens of millimetres of separation rather than by 1.9 mm of pin gap. It also
   lets the 48 V group get its own clearance zone (and a routing slot if the layout
   review wants one) without disturbing the signal fan-out.
4. Cost of the split: **one extra part per board and one extra footprint**. Alignment is
   a non-issue - 2.54 mm THT has ~0.3 mm of positional slack and a 6 mm lead-in; Arduino
   shields mate four separate headers this way.

Single-connector 2x20 remains the right answer **if** the mechanical answer forces
stackthrough hardware (section 6), because stackthrough only exists in 2x20/2x40.

Proposed 38-position allocation (pin *assignment* is the designer's call per CAR-REQ-06;
this is the pin *budget*):

```
POWER  2x7  row A: 48V  48V  48V  12V  12V  3V3  3V3
             row B: GND  GND  GND  GND  GND  GND  GND      <- every supply pin gets an adjacent return
SIGNAL 2x12 20 signals (8 PWM, 4 SPI, 2 I2C, 2 ADC, ENABLE, FAULT, 2 ID) + 4 GND
             GNDs interleaved between PWM groups per the section 2.1 note
```

Totals: 48 V 3, 12 V 2, 3V3 2, GND 11, signals 20 = 38. Satisfies section 2.1
(">= 3 pins total across the power rails" - 7 here; ">= 4 GND" - 11 here) and CAR-REQ-13
(section 3).

---

## 6. CAR-REQ-15 / Q4 - mated stack height. **The 15 mm default does not work.**

Measured from the parts, not assumed:

| Hardware | Male mating pin | Socket body | Achievable board-to-board |
|---|---|---|---|
| DS1021 male + DS1023 socket (the pick) | 6.0 mm | 8.5 mm | **11.0 mm** hard-seated (2.5 mm insulator + 8.5 mm body). Can be stretched to ~13 mm by shortening engagement to 4 mm, but 11.0 mm is the only value with a positive mechanical stop |
| 2.00 mm family (#6) | 4.0 mm | 4.3 mm | ~4.3-6.5 mm |
| 1.27 mm family (#7) | 3.0 mm | 4.3 mm | ~4.3-5 mm |
| PC/104 stackthrough (#3, C35165) | n/a - **12.3 mm tails** | 8.3 mm | **up to ~15.2 mm** (PC/104 standard 15.24 mm) with ~5.5 mm engagement |
| Samtec QTH/QSH | - | - | family offers 5/7/9/11/13/16 mm - but rejected on cost |

So the honest answer to the human's Q4:

- If the standoff must be **15 mm**, the connector must be the **PC/104 stackthrough
  2x20** (C35165 or C5307344). That exists, is in stock (5 333), and costs ~$0.75-1.03.
  It **forces the single-connector scheme** (no 2x7/2x12 stackthrough exists) and so
  gives up the section 5 keying argument.
- If the standoff can move to **11 mm**, the recommended split works with ordinary,
  cheap, deeply-stocked hardware.
- **Recommendation: move the standoff to 11 mm** unless something else on the carrier's
  top side needs more headroom.

**And something probably does.** A board-edge RJ45 magjack (CAR-REQ-05/20, Q12 default
"board-edge THT magjack") is a tall part - a standard 8P8C jack body is in the 13-16 mm
range. With MECH-02's common 100 x 80 mm outline, the daughter sits directly over it.
An 11 mm stack collides; even 15.24 mm may be tight. This is a genuine cross-block
conflict and it is **not mine to resolve** - flagged in OPEN below. Options are: notch
the daughter over the RJ45 (breaks "identical outline"), use a low-profile/right-angle
jack, or set the standoff from the jack height and accept a stackthrough connector.

Note also that the daughter's socket has to face **downward**, i.e. it is a
reverse-mounted THT part on the daughter's bottom side, or a bottom-side SMD part. That
is a daughter-board assembly instruction, but it belongs in the ICD because it is the
mating geometry.

---

## 7. Assembly notes (JLCPCB PCBA, top side, 8-14 units)

- All picks are **through-hole**. JLC assembles them, but as PTH/hand-solder work with a
  per-joint charge rather than SMT placement - a real, small cost. At 14 boards with
  38 joints, budget for it explicitly rather than discovering it at quote time.
- **The all-SMT escape hatch is row #5** (PZ254-2-20-S + HC-PM254-8.5H-2x20PS, both SMD
  vertical, 250 V/3 A). It removes the hand-solder line item. It is ranked below the THT
  pick because SMD pads carry the insertion/extraction force of a 40-way connector that
  is mated every time a daughter is swapped; with CAR-REQ-15's standoff taking the board
  flex this is defensible, but it is a downgrade in mechanical robustness.
- Carrier connector cost at qty 50: split **$0.22/board**, single 2x20 **$0.18/board**.
  Irrelevant against the $30/carrier target (Q15) - do **not** trade ratings for cents here.

---

## 8. Risks

- **Q6 is unconfirmed.** The entire pin allocation in section 3 rests on a provisional
  worst case. A 48 V peak above 3 A adds one pin per 1.8 A and pushes the power block to
  2x8/2x9. Cheap to absorb *if* it lands before H1; expensive after, because ICD-01
  freezes at H1 and two daughters are blocked on it.
- **Single-source: no.** Low risk. The pick is a commodity 2.54 mm THT footprint with at
  least four independent stocked vendors on the *same* footprint (CONNFLY DS1021/DS1023,
  HanElectricity 2541WV/2541FV, Boomele 2.54-2\*nnP, hanxia HX PZ2.54, Hong Cheng
  HC-PZ254/HC-PM254). A second source can be dropped in with no board change. This is a
  significant argument for 2.54 mm over any mezzanine family, where the footprint is
  proprietary and a stockout is a respin.
- **No JLC Basic part exists** anywhere in this space - the pick is Extended and that is
  unavoidable, not a selection error.
- **Working voltage not published** for the budget pair (#4), both PC/104 stackthroughs
  (#3/#3b) and several sockets. If the stackthrough route is taken for a 15 mm stack,
  CAR-REQ-17 evidence has to come from the vendor datasheet (linked in the JSON) rather
  than the LCSC attribute table - **do not freeze the ICD on a stackthrough part until
  someone has read its datasheet voltage rating.**
- **2x17 does not exist** in the CONNFLY male family (DS1021-2x17 returns nothing; 2x16
  has 11 pcs in stock, 2x18 has 125). If the architect wants a single ~34-position
  connector, the practical stocked counts are **2x15, 2x20 or 2x22** - 2x20 by a wide
  margin. Position counts are not free parameters; design the pin map to a stocked count.
- Contact plating is gold on all picks; operating range -40..+105 degC covers the
  assumed 0-40 degC ambient (Q13) with room for the CAR-REQ-18 hot zone.
