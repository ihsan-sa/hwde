# Library edits - boards/g0-sense/lib/aiee.pretty

Hand edits to pulled easyeda2kicad footprints. Every edit here was made by the P6
`fixer` agent (work order `wo-p6-silk`, silk domain) to resolve DRC `silk_overlap` /
`silk_edge_clearance` warnings, then propagated into the library so `lib_footprint_mismatch`
does not reappear (kicad-cli DRC compares each board footprint instance against this
`.pretty` directory - if the board instance is edited but the library copy is not, DRC
trades the silk warning for a `lib_footprint_mismatch` warning instead of clearing it).

Untouched by every edit below: all pad geometry (position, size, shape, layers, drills),
all courtyard geometry, all 3D model references, `(property "LCSC Part" ...)` values,
and every footprint's Reference/Value `fp_text` (never deleted, per fixer hard rule -
only GRAPHIC silk items were removed).

## 2026-08-27 - P6 fixer (wo-p6-silk)

### Why

`kc.py drc --parity` on `kicad/g0-sense.kicad_pcb` reported 13 non-unconnected
violations at P6, three of which were the ones assigned to this work order plus
their root cause:

1. **`silk_overlap` C12/U2 (5) and C12/U1 (4).** C12 (the NRST cap, placed "as close
   as possible to the device" per knowledge record `mcu-nrst-internal-pullup-and-cap`)
   sits at (36.8, 40.65) directly between U1 (SOT-223, silk top edge at y=41.195) and
   U2 (TSSOP-20, silk bottom edge at y=39.905) - a 1.29mm vertical corridor. C12's own
   `aiee:C0603` F.SilkS body outline is 1.62mm tall (y 39.84-41.46), so it overlaps
   *both* neighbours by a combined 0.33mm no matter where in that corridor it sits:
   nudging C12 up by `dy` shrinks the U1-side overlap by `dy` but grows the U2-side
   overlap by the same `dy` (the corridor is fixed by U1 and U2, which this work order
   may not move) - the deficit is position-invariant. A move-only fix (fix-ladder rung
   a) is therefore geometrically impossible; verified by direct measurement, not
   assumed. Rung (b) (trim) is the least-invasive fix that remains: since the 0603
   body outline is decoration and the Reference text (not touched) is what assembly
   and debug actually read, C12's full F.SilkS was cleared via
   `place_edit.py {"op":"silk_clear","ref":"C12"}` (10 items: 6 `fp_line` + 4
   `fp_arc`; matches the library list below exactly).
2. **`silk_edge_clearance` J1 (3).** J1 (USB-C receptacle) is flush with the board's
   left edge (x=18.91mm) by design - it is a cable-mating connector. J1's own
   F.SilkS carries 5 lines: 2 draw the near (on-board) sides of its body outline, and
   3 draw the far (mouth-end) sides of the same outline, which land at x=18.92mm,
   0.01mm inside the nominal edge but with a 0.25mm stroke that puts the printed ink
   0.115mm *past* the board edge, under the connector shell where it cannot print.
   Cleared via `place_edit.py {"op":"silk_clear","ref":"J1","only_offboard":true}`
   (exactly 3 items removed; the 2 on-board sides are untouched).
3. **The trap.** Both clears above change the *board's* footprint instance only.
   `kc.py drc` then reported 6 new `lib_footprint_mismatch` warnings (one per
   changed board instance) because this `.pretty` directory still had the original
   geometry. `aiee:C0603` is shared by 5 caps on this board (C1, C10, C11, C12, C13),
   so all 5 had to be cleared on the board (not just C12) to stay consistent with one
   library edit; `aiee:USB-C_SMD-TYPE-C-31-M-12_1` has only the one instance, J1.

Acceptance rule (this work order): `kc.py drc --parity` on the board must report ZERO
violations whose source is not `unconnected` (the 64 unconnected ratsnest items are
P7's).

### C0603.kicad_mod (C14663 100nF; used by C1, C10, C11, C12, C13 on this board)

- DELETED all 10 `F.SilkS` graphic elements - the entire body-outline decoration:
  - `(fp_line (start -0.28 0.71) (end -1.08 0.71) ...)`
  - `(fp_line (start 0.28 0.71) (end 1.08 0.71) ...)`
  - `(fp_line (start -0.28 -0.71) (end -1.08 -0.71) ...)`
  - `(fp_line (start 0.28 -0.71) (end 1.08 -0.71) ...)`
  - `(fp_line (start -1.39 0.40) (end -1.39 -0.40) ...)`
  - `(fp_line (start 1.39 -0.40) (end 1.39 0.40) ...)`
  - `(fp_arc (start 1.08 -0.40) (end 1.39 -0.40) (angle -90.00) ...)`
  - `(fp_arc (start 1.08 0.40) (end 1.08 0.71) (angle -90.00) ...)`
  - `(fp_arc (start -1.08 0.40) (end -1.39 0.40) (angle -90.00) ...)`
  - `(fp_arc (start -1.08 -0.40) (end -1.08 -0.71) (angle -90.00) ...)`
- KEPT unchanged: `(fp_text reference REF** (at 0 -1.535) (layer F.SilkS) ...)` (the
  only silk left on this footprint), all pads, all `F.CrtYd`, the 3D model.
- No polarity/pin-1 mark existed on this footprint to lose - it is a symmetric
  2-pad passive body outline, purely decorative on a dense (35.79 x 28.34mm) board;
  the judgement call the work order pre-approved.
- Applied to the board with the same `place_edit.py silk_clear` call, once per ref
  (C1, C10, C11, C12, C13): 10/10 removed each time, `verified: true`.

### USB-C_SMD-TYPE-C-31-M-12_1.kicad_mod (C165948; used by J1 only)

- DELETED the 3 mouth-end `F.SilkS` lines (the far side of the body-outline
  rectangle, beyond the connector's mating face):
  - `(fp_line (start 4.47 5.09) (end -4.47 5.09) ...)` (far horizontal side)
  - `(fp_line (start -4.47 5.09) (end -4.47 3.61) ...)` (far-left vertical stub)
  - `(fp_line (start 4.47 5.09) (end 4.47 3.61) ...)` (far-right vertical stub)
- KEPT unchanged: the 2 near-side vertical lines
  (`(start -4.47 1.38) (end -4.47 -0.49)` and `(start 4.47 1.38) (end 4.47 -0.49)`),
  the Reference text, all pads (including the 4 wide GND/VBUS pads narrowed at P5 -
  untouched here), `F.CrtYd`, `Cmts.User` alignment circles, the 3D model.
  Identified by rotating the board instance's absolute silk-line endpoints back into
  footprint-local coordinates (J1 is at (24.01, 41.5), orientation -90 deg) and
  matching them 1:1 to these 5 library lines; the 3 deleted ones are exactly the
  ones whose local/board endpoints sit at x=18.92mm, at/past the 18.91mm board edge.
- This is the connector's mouth-end outline, not a polarity or pin-1 mark - USB-C is
  symmetric and this footprint has no such mark to lose.

### D1 (SOD-123, TVS diode) - not a library edit, listed here for the same audit trail

The 13th violation, `silk_over_copper` on D1's Reference field clipping J1's VBUS pad
A4B9's solder mask, was not a library-shared footprint issue - `place_edit.py
move_text` relocated D1's Reference text from (27.76, 38.3) to (35.6, 42.6) deg=90.
See `reports/place_edit_p6_silk.json` for the full geometric justification (the
J1-D1 corridor has no slot big enough for the 1.697 x 2.202mm reference text in
either orientation; nearest verified-clean slot is ~6.2mm from D1, inside the
copper-free interior of U1's own silk outline box).

### Verification (all re-run after the edits)

| Check | Result |
|---|---|
| `kc.py drc --parity` on `kicad/g0-sense.kicad_pcb`, non-`unconnected` violations | 13 -> 0 (64 `unconnected` untouched, P7's) |
| `lib_footprint_mismatch` (the trap) | 0 - board and library agree on all 6 touched footprints (C1, C10, C11, C12, C13, J1) |
| `gate.py --gate place` (no `--workspace`) | pass, 0/0, all 5 coverage checks (courtyard, outline, edges, keepouts, decoupler_distance) pass |
| Meaning-carrying marks (polarity bars, pin-1 marks, C3's tantalum "+") | none touched - neither edited footprint had one |
