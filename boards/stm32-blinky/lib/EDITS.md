# Manual library edits (traceability log)

Manual footprint edits require orchestrator approval (librarian role contract).
Append-only; one entry per approved edit.

## 2026-07-27 LED0805-RD.kicad_mod - relocate pin-1/cathode silk dot off pad 1 copper

- Part: C84256 (NCD0805R1 / EasyEDA "FC-2012HRK-620D"), red 0805 LED, D2.
- Approval: orchestrator follow-up assignment (P5 board_init DRC found
  `silk_over_copper` intrinsic to this footprint).
- Symptom reproduced on a minimal scratch board (KiCad 10.0.3 kicad-cli pcb drc,
  severity-all): exactly one `silk_over_copper` warning - "Silkscreen clipped by
  solder mask": the F.SilkS fp_circle vs Pad 1. All other silk elements keep
  >= 0.175 mm to pad copper (line width 0.25 accounted) and were left untouched.
- Root cause: easyeda2kicad placed the pin-1 dot at the 0805 BODY corner
  (-1.00, 0.62), which is inside pad 1's copper/mask aperture (pad 1 spans
  x -1.60..-0.60, y -0.625..0.625). (The F.CrtYd rect is that same body
  outline - see open issue below.)
- Edit (minimal, one line):
  - BEFORE: `(fp_circle (center -1.00 0.62) (end -0.97 0.62) (layer F.SilkS) (width 0.06))`
  - AFTER:  `(fp_circle (center -2.35 0.00) (end -2.32 0.00) (layer F.SilkS) (width 0.06))`
  - Dot radius (0.03) and stroke (0.06) unchanged; relocated to the horizontal
    centerline just left of the cathode chevron tip (chevron spans x -1.75..-2.10).
    Clearance to pad 1 copper edge: 0.69 mm (>= 0.15 required). No silk-silk
    contact (0.065 mm gap to the chevron vertical stroke).
- Polarity indicators after edit (all preserved): cathode chevron + relocated dot
  at the pad-1 (K/"-") end, "+" glyph toward pad 2 (A). Symbol pin 1 = "-",
  pin 2 = "+" - unchanged.
- Verification:
  - Scratch-board DRC after edit: 0 silk violations (only the scratch board's
    own `invalid_outline` artifact remains - no Edge.Cuts on a bare test board).
  - fp_verify: pass, 0 violations (reports/fp_verify_C84256.json,
    overlay reports/fp_C84256_LED0805.overlay.svg).
  - kicad-cli fp export svg renders: reports/fp_svg/LED0805-RD.svg (dot visible
    as r=0.03 circle left of chevron, svg coords (2.656, 4.848)).
- NOT changed (out of approved scope, reported upstream): the F.CrtYd rectangle
  is the 2.0 x 1.25 mm body outline, SMALLER than the pad extents (x +-1.6) -
  courtyard-based overlap/placement checks under-estimate this part. Also note
  the dot's 0.12 mm outer diameter is below typical 0.15 mm fab min silk feature
  (pre-existing; the 0.25 mm-wide chevron is the reliable printed polarity mark).
