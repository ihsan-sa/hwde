# What the five breadboard runs learned: four rulings

**Nothing becomes approved until you answer these four questions. One of them,
the screw-terminal facing, needs settling before any breadboard is ordered.**

The five breadboard boards (bb-buck, bb-mcu, bb-ldo, bb-amp and bb-adc) produced 82
research records and 76 workshop lessons, and none of them has been ruled yet. Until the
records are approved, every future board that uses one of these blocks researches it
again from scratch. Each question below comes with my recommendation, so you can reply
"as recommended" to all four or override single rows. I've listed every record and
lesson with its recommendation in `docs/u22-candidates.yaml`. The detailed reasoning is
in `design/u22-ruling-packet.md`.

I merged duplicates first. Only one rule turned up on two boards, so the 82 records come
down to 80 once the merge and one fold into the library are taken. The 76 lessons fold
into 62 to promote and 14 to decline, and 10 of the declines are the same lesson written
on two boards. I found one real contradiction (Q2), and I've listed it instead of
averaging it.

## Q1. Approve 76 records, 12 of them with an edit

76 records have passed a second reader. For 62 of them I checked "what does this rule
scale with" the way we did in the first approval session, and their limits hold. The
other 14 need a change first:

- **Merge.** bb-amp wrote the input-bias return path twice, once as a principle and
  once tied to one part's bias-current range. I've merged them into one principle
  with five sources, staged in `design/u22-staged/records/`.
- **Fold into the library.** The buck enable-pin record says the same thing as the
  approved `buck-en-softstart-sequencing`. Its three new facts should go into that
  record, which you then re-approve, so it doesn't sit there as a duplicate.
- **Wrong level (4).** Two records claim "family" with no family named, one uses a
  one-part range as its limit, and one has a limit that every board meets.
- **Missing key (4).** Three zero-drift records need `amp_kind: zero-drift` so that a
  board can find them. The fixed-LDO minimum-load rule should be limited by the
  fixed variant, not by the 0.8 A where the datasheet table stops.
- **Missing link (3).** Three reference-charge records should point to their
  switched-capacitor parent.
- **Supply band.** One SWD record says 2.7-3.6 V while its sibling says 2.4-3.6 V for
  the same parts, and both of their own pages support 2.4-3.6 V.

I've also flagged three limits that I'd accept but you may want to widen to a
principle: two temperature ranges that are only where the part is characterised, and
one 0-5 V range that is only what we tested.

**Recommendation:** approve all 76 with these edits.

## Q2. One screw terminal, two facings

bb-mcu and bb-adc use the same WJ500V-5.08-2P footprint, the same 3D model and the same
rotation. bb-mcu's lesson says the wire goes in at -Y, from a side render. bb-adc's
says +Y, from the vendor drawing matched to the footprint's fab outline. They can't both
be right, so on one of those boards the terminal faces into the board.

**Recommendation:** settle it against the vendor drawing or a part in hand before
either board is ordered. I think bb-adc is right, because it used a dimensioned drawing
rather than a render. Promote the checking method now and the direction once you've
ruled.

One smaller disagreement stays as it is. The attenuator record says a guard ring earns
its copper above 100 kohm, and the in-amp draft says above 1 Mohm. They describe
different circuits, a single tap and a differential pair where matching the two paths
is an option, so I'd keep both numbers in their own records rather than pick one.

## Q3. Six unfinished bb-amp records and nine checklists

Six bb-amp records never got their second read, so they can't be approved, and bb-amp's
status check fails until they're resolved. I can either run six second reads, which is
a small research job, or close them as drafts that won't satisfy coverage. Five are
worth keeping. The sixth is the draft that the Q1 merge replaces, and it only needs its
two part-specific pages re-read.

The five boards also drafted nine coverage checklists: linear regulator, MCU, SWD port,
in-amp, instrumentation input, precision buffer, attenuator, SAR ADC and voltage
reference. A checklist row that only a principle can cover has to be lowered to
"principle" before approval, or it can never be satisfied. That was the third mistake
in the first approval session.

**Recommendation:** run the six second reads. Approve the checklists after a coverage
run on test boards, lowering any row that only a principle covers.

## Q4. Promote 62 lessons and decline 14

The 76 lessons are mostly pipeline bugs and traps. Among them are a quoted brief that
silently turns off the brief check, vias placed inside large pads, zone pad connections
that can only be set per zone, a Freerouting failure that wastes the whole routing
ladder, and a converter that should be ranked by error in volts rather than in LSB.
Each one I promote gets a row in the root LEARNINGS and a triage row naming the file
that should fix it. I decline 13 as duplicates, 3 of them because a verified record
already says the same thing. The 14th is bb-mcu's terminal lesson, which waits on Q2.

Two of them have partly landed since I first wrote the packet. The unreachable-vendor
lesson now only adds analog.com and the Farnell mirror, and the connector lesson's
graphics gap is down to the missing mirror operation.

**Recommendation:** rule them as one block, as listed in the candidate file.

## After you answer

Your rulings go into one session that writes them. That session promotes the approved
records into the library with your answer as the approval note, marks every queue entry
promoted or declined, and then runs strict validation and a coverage check. Nothing has
been written to the boards repo or marked approved yet.
