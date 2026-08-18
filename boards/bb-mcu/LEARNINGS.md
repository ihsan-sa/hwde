# LEARNINGS - bb-mcu (workspace learnings)

Workspace-local. Every entry gets a date, tags (stage tag first: P0-P10), and a
one-line claim as its title. `learnings.py compile --workspace boards/bb-mcu` turns new
entries into `learnings/queue.yaml`; the `promote` verb rules on them.
Research tasks (research.py close) append their entries here automatically.

## 2026-08-16 [P2][research][knowledge][block:B2] research task block-swd-debug-port-1: 5 verified record(s) for block:B2
Gap: research block 'swd-debug-port': produce its coverage checklist, then populate it
Operating point: {"board_layers": 2, "connector_kind": "header-100mil", "debug_kind": "swd", "edge_ns": 5, "fclk_mhz": 4, "header_pins": 5, "keying_kind": "none", "probe_kind": "flying-lead", "source_kind": "dc-input", "tamb_max_c": 50, "vio_v": 3.3}
Missing classes: coverage-checklist

Verified records (second reader signed). Promotion = the research verb's promote step (copies record + sources into the library), then the queue ruling with kind knowledge_record targeting reference/knowledge/records/<id>.yaml, then the owner's approval block:
- swd-debug-port-edge-rate-sets-layout-demand [emi] boards/bb-mcu/research/records/swd-debug-port-edge-rate-sets-layout-demand.yaml
- swd-debug-port-nrst-on-the-header [sequencing] boards/bb-mcu/research/records/swd-debug-port-nrst-on-the-header.yaml
- swd-debug-port-stm32f0-internal-pulls [selection] boards/bb-mcu/research/records/swd-debug-port-stm32f0-internal-pulls.yaml
- swd-debug-port-termination-follows-silicon [selection] boards/bb-mcu/research/records/swd-debug-port-termination-follows-silicon.yaml
- swd-debug-port-unkeyed-header-pin-order [selection, return-path] boards/bb-mcu/research/records/swd-debug-port-unkeyed-header-pin-order.yaml
Draft coverage checklist(s) for the owner to approve:
- swd-debug-port boards/bb-mcu/research/checklists/swd-debug-port.yaml (7 classes)
Sources (quarantined, sha-pinned in the task ledger):
- research/sources/2304140030_STMicroelectronics-STM32F030F4P6TR_C89040.pdf tier vendor-layout sha256 faac9340687f <https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/2304140030_STMicroelectronics-STM32F030F4P6TR_C89040.pdf>
- research/sources/infineon-an220270-hardware-design-guide-for-the-traveo-t2g-family-applicationnotes-en.pdf tier cross-vendor sha256 34d9156d68dd <https://www.infineon.com/assets/row/public/documents/10/42/infineon-an220270-hardware-design-guide-for-the-traveo-t2g-family-applicationnotes-en.pdf>
- research/sources/snla026a.pdf tier cross-vendor sha256 3a5604e61cbe <https://www.ti.com/lit/pdf/snla026>
Task file: boards/bb-mcu/research/tasks/block-swd-debug-port-1.json

## 2026-08-16 [P2][research][knowledge][block:B1] research task block-mcu-1: 8 verified record(s) for block:B1
Gap: research block 'mcu': produce its coverage checklist, then populate it
Operating point: {"board_layers": 2, "boot_kind": "external-strap", "clock_kind": "internal-rc", "debug_kind": "swd", "edge_ns": 5, "fcpu_mhz": 48, "idd_ma": 100, "package_kind": "tssop", "pdiss_w": 0.33, "reset_kind": "internal-pullup", "source_kind": "dc-input", "supply_kind": "single-rail", "tamb_max_c": 50, "vdd_max_v": 3.6, "vdd_min_v": 3.0, "vdd_v": 3.3}
Missing classes: coverage-checklist

Verified records (second reader signed). Promotion = the research verb's promote step (copies record + sources into the library), then the queue ruling with kind knowledge_record targeting reference/knowledge/records/<id>.yaml, then the owner's approval block:
- mcu-analog-rail-tracks-digital-rail [sequencing] boards/bb-mcu/research/records/mcu-analog-rail-tracks-digital-rail.yaml
- mcu-boot-select-strap-stm32f0 [selection] boards/bb-mcu/research/records/mcu-boot-select-strap-stm32f0.yaml
- mcu-decoupler-is-the-local-source [decoupling, return-path] boards/bb-mcu/research/records/mcu-decoupler-is-the-local-source.yaml
- mcu-package-power-budget [thermal] boards/bb-mcu/research/records/mcu-package-power-budget.yaml
- mcu-reset-sampled-pin-audit [selection] boards/bb-mcu/research/records/mcu-reset-sampled-pin-audit.yaml
- mcu-supply-pin-pair-decoupling [decoupling] boards/bb-mcu/research/records/mcu-supply-pin-pair-decoupling.yaml
- mcu-supply-return-continuity [return-path, emi] boards/bb-mcu/research/records/mcu-supply-return-continuity.yaml
- mcu-swd-port-live-at-reset-stm32f0 [selection] boards/bb-mcu/research/records/mcu-swd-port-live-at-reset-stm32f0.yaml
Draft coverage checklist(s) for the owner to approve:
- mcu boards/bb-mcu/research/checklists/mcu.yaml (5 classes)
Sources (quarantined, sha-pinned in the task ledger):
- research/sources/2304140030_STMicroelectronics-STM32F030F4P6TR_C89040.pdf tier vendor-layout sha256 faac9340687f <https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/2304140030_STMicroelectronics-STM32F030F4P6TR_C89040.pdf>
- research/sources/00002519A.pdf tier cross-vendor sha256 6cbc68c178d1 <https://ww1.microchip.com/downloads/en/AppNotes/00002519A.pdf>
- research/sources/AN13033.pdf tier cross-vendor sha256 9e14d7d0dda5 <https://www.nxp.com/docs/en/application-note/AN13033.pdf>
Task file: boards/bb-mcu/research/tasks/block-mcu-1.json

## 2026-08-16 [P6][placement][kicad][render] WJ500V-5.08-2P wire entry is at local -Y - the OPPOSITE of the KF128 / DB128L family
Root LEARNINGS records twice (2026-07-28 KF128, 2026-08-09 DB128L-5.08-2P) that a
5.08 mm screw terminal's wire mouth is at footprint-local **+Y**, so rot 270 points it
out the LEFT edge and rot 90 out the RIGHT. `aiee:CONN-TH_2P-P5.00_WJ500V-5.08-2P`
(C8465, Ningbo Kangnex) is the reverse: `render.py <board> --views right,left` shows the
two square wire cavities FACE-ON in the **right** view at footprint angle 270, and the
closed back (screw-clamp bodies behind plastic) in the left view. So for this footprint
**rot 270 = mouth out the RIGHT edge, rot 90 = out the LEFT**.
Two corroborating cues, and one that lies: the courtyard is asymmetric about the pad row
(local y[-5.5, +4.5]) and the LONGER 5.5 mm side is the mouth side - i.e. the mouth is at
local -Y, matching the render. The cue that lies is the TOP view: at rot 270 the rendered
top view shows dark slot-like recesses on the body's LEFT (board-inboard) face and a
plain lip on the right, which reads exactly backwards. Do not shortcut the side render -
"same pitch, same family, same +Y" is not transitive across vendors.

## 2026-08-16 [P6][gates][build-modes][PIPELINE BUG] `placement.edges` pins the connectors to the PROVISIONAL outline, so under a `canonical` binding the place gate cannot pass BEFORE `--outline fit`
`placelib.legality_violations` measures every `placement.edges` ref against
`edge_line(model.outline, ...)` with `EDGE_TOL = 2.5 mm`, and the outline it reads is
whatever `board_init --outline auto` produced. On bb-mcu that was 51.15 x 43.524 mm, a
shelf-pack artifact; the canonical layout is 33.77 x 21.26 mm of content. Placing to the
canonical layout leaves J1 16.85 mm from the provisional right edge -> `edge_violation`,
gate FAIL. Placing to satisfy the edge means spreading the three connectors to the
provisional edges, and then `--outline fit` measures the spread and "earns" the
provisional size - the bb-buck lesson (2026-08-16 board_edit entry) with the sign
flipped: fit measures the placement in front of it, and a placement stretched to a big
outline has already spent the difference.
Both `reference/recipes/resize-board.md` ("Place (P6) against that room, gate `place`",
then fit) and the P6 agent contract order it place -> gate -> fit. For a `canonical`
binding with ANY `placement.edges` entry the order has to be **place -> fit -> gate**.
Measured on this board: after `board_edit --outline fit --margin M` the place gate is
clean (0 violations, all five coverage legs green) at M = 0.5 / 1.0 / 2.0, giving
34.77 x 22.26 / 35.77 x 23.26 / 37.77 x 25.26 mm. The fix is the ORDER, not the
placement. Second-order trap in the same shape: `silk_place` and `board_edit --outline
fit` disagree about what is on the board - fit measures courtyards + copper + rule areas
and ignores silk, while silk_place solves refdes positions against the CURRENT outline,
so on the provisional board it parked J1/J3/H1/H2's refdes where the earned edge later
cuts them. Hand-place any refdes outside the future content bbox, or re-run silk_place
after the fit.

## 2026-08-16 [P3][librarian][footprint][fp_verify][PIPELINE BUG] A pulled THT footprint was under-drilled 1.30 mm against the vendor's own 1.50 mm, and nothing in the pipeline could have caught it

J1 (WJ500V-5.08-2P, LCSC C8465) pulled with a 1.30 mm drill. The vendor's own
"PCB LAYOUT" panel recommends **1.50 mm**, and the datasheet dimensions the pin
0.90 mm wide. If that pin is square - which the square screw-clamp opening
drawn above it indicates, though the shape is never explicitly labelled - its
worst-case diagonal is 0.90 * sqrt(2) = **1.273 mm**, leaving **0.027 mm** of
total diametral clearance. That is a terminal that does not seat, discovered at
assembly, on every board in the batch.

Why no gate saw it, and this is the part worth keeping:

1. `fp_verify` has **no drill-vs-pin check at all**. It checks pad count,
   pitch, pin-1, pad size and a fab annulus floor. Nothing compares the hole to
   the thing that goes through it.
2. `fp_verify`'s land-pattern diff needs a `parts/<lcsc>.json`, and connectors
   do not get datasheet extractions by default - the P3 roster runs an
   extractor "per nontrivial IC". So the diff never ran, and the librarian
   correctly reported the connectors as verified only for courtyard, pin-1 and
   annulus floor.

It surfaced ONLY because the librarian reported honestly what it could NOT
verify instead of reporting a clean pass, and that gap was then chased with two
extra extractions. An agent that had summarised "3/3 footprints pass" would
have shipped it.

Two fixes worth making: extract datasheets for THROUGH-HOLE CONNECTORS as well
as ICs at P3 (their drill is a board-killer and their datasheets are short),
and give `fp_verify` a drill-vs-stated-pin check with the square-pin diagonal
built in.

## 2026-08-16 [P3][fp_verify][footprint] fp_verify never compares row_spacing_mm, although land_pattern carries the field

The U1 SOP-20 diff returned pad_count 20/20, pitch ok, pin-1 present and ONE
pad_size warning. Hand measurement found what the tool does not look at:

    pad size     0.35 x 1.494 mm  vs datasheet 0.40 x 1.35 mm  -> warned
    row spacing  6.00 mm          vs datasheet 5.75 mm         -> NOT CHECKED

`datasheet_extract` populates `land_pattern.row_spacing_mm`, so the data is
there and only the comparison is missing. On a two-row leaded package the row
spacing is what decides whether the pads capture the lead FEET at all - it is
more load-bearing than pad size, because getting it wrong slides both rows off
the leads while pad-count and pitch still pass.

Here it was benign and was accepted on a worked argument (the pulled land spans
2.253-3.747 mm from the centreline against a lead foot at ~2.6-3.2 mm, so it
captures the foot with MORE toe and a WIDER inter-pad gap than ST's own land).
But it was found by hand, not by the gate.

## 2026-08-16 [P2][research][network][fetch] Being on the fetch allowlist says NOTHING about being reachable - st.com and analog.com are both dark from this host

Measured, not inferred:

    curl --max-time 20 https://www.st.com/     -> HTTP 000, 0 bytes, timeout
    curl --max-time 20 https://www.analog.com/ -> HTTP 000, 0 bytes, timeout
    curl --max-time 20 https://wmsc.lcsc.com/  -> HTTP 301 in 0.93 s

Both dead hosts are ON the allowlist, so `research.py fetch` accepts the URL
and then burns a depth unit on a timeout. The P2 swd-debug-port researcher
spent two attempts discovering analog.com before giving up on MT-097.

The working route to a manufacturer's own PDF is `wmsc.lcsc.com`, which serves
the genuine vendor document (verified: ST DocID024849 Rev 3 branding on every
page read). Tier is unaffected - domains.yaml says the tier is a fact about the
DOCUMENT vs the SUBJECT part, not about the host, so an ST datasheet fetched
via LCSC is still `vendor-layout`.

What it does not solve: ST application notes, reference manuals and errata are
on NO allowlisted host, so RM0360 could not be acquired and the BOOT0
level-to-boot-memory mapping stayed unsourceable all run. Hosts confirmed
working: wmsc.lcsc.com, infineon.com, ti.com, microchip.com, nxp.com.

## 2026-08-16 [P8][silk][silk_place] silk_place SKIPS board_only refs by design, so a mounting hole's refdes is never solved and can end up labelling the IC

`check_silk` flagged `silk_misattributed`: H3's refdes sat 1.67 mm from its own
hole and **0.23 mm from U1**, reading as U1's designator on a board whose only
IC it is. The obvious remedy fails silently in the right direction:

    silk_place --refs H1,H2,H3,H4 --apply
    -> moved 0, skipped [{H1 board_only} {H2 board_only} {H3 board_only} {H4 board_only}]

`silk_place` solves "every visible non-board_only silk refdes", and mounting
holes are board_only. It exits 0 and reports honestly - it just cannot help.
The fix is the one `check_silk`'s own message names: a direct
`place_edit move_text`, which needs the hole's real coordinates (they are in
the P6 place-edit report, not in the silk report).

Worth considering: mounting-hole refdes carry no assembly information at all -
nothing is placed at H3 - so hiding them may beat placing them.

## 2026-08-16 [P3][process][windows][state] Backticks in a Bash-tool argument are COMMAND SUBSTITUTION, and a state.py decision silently lost a word to it

Recording a decision whose `--why` prose contained a backtick-quoted term:

    ... with the floor at `proven`, a verified-but-unapproved record ...

Bash ran `proven` as a command, substituted its empty output, and state.py
stored "... with the floor at , a verified-but-unapproved record ...". state.py
exited 0; the only signal was one `proven: command not found` line on stderr
from a different process than the one being checked.

Same family as the recorded `\`-in-a-quoted-heredoc collapse: prose destined
for a file should not travel through the shell. Long `--why` / `--note` text is
exactly that, and it is the audit trail, so a silent deletion there is worse
than most places. Read a long decision back out of state.json once after
recording it - that is how this was caught.
