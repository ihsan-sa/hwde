# g0-sense - unattended container run: close-out (supervisor, 2026-08-27)

**Result: order-ready package, nothing ordered.** 2-layer 35.79 x 28.34 mm USB-C
(power only) -> 3.3 V LDO -> STM32G030F6P6 + SHT40 sensor node; SWD/UART headers,
Qwiic, LEDs, reset, 4 x M2. 26 parts, 24 SMT-placed (J3/J4 THT DNP). All five
machine gates PASS and fresh (erc, place, drc_routed, verify, dfm), attestation
rev 2 VALID / order-ready, H1-H4 delegated and recorded, H5 (pay) not taken.

| Item | Where |
|---|---|
| Fab package (gerbers zip, BOM, BOM-full, CPL, pos, checklist) | `fab/` - read `fab/README.md` first (Sensirion no-wash rules) |
| Quote (jlc_pricing.yaml ESTIMATE, no API credentials) | `fab/quote.json`: qty 5 = USD 42.68 (8.54/unit); 10 = 43.36; 30 = 52.98 |
| Release attestation | `fab/attestation.json` (rev 2, sha 2a0035eb) |
| Renders / schematic / design doc | `reports/renders/`, `reports/schematic.pdf`, `reports/design_doc/g0-sense-design-doc.pdf` |
| Checkpoint packets, phase digests | `log/H1.md`..`H5.md`, `log/P0..P10-digest.md` |
| Run journal (full narrative, supervisor notes) | `log/run-journal.md` |
| Decisions on the owner's behalf | `state.json` decisions (43), all tagged `unattended default:` / delegated |
| Waivers | `reports/verify-waivers.json` (1 durable: check_thermal U1, evidence-bound, expires 2027-08-27); `reports/erc-waivers.md` |
| Learnings | `LEARNINGS.md` (8 entries, compiled -> `learnings/queue.yaml`), root LEARNINGS + triage rows 330-335 |

## Timeline / cost

- 06:35Z launch (ccbox `ai-ee-run`, Opus 5 xhigh, bypass, open egress) -> 09:59Z P4 erc PASS (loop 1: 136 turns, $120).
- 10:00Z killed by a Claude usage limit (3 x 429 tripped the loop's error cap); revived 12:50Z with limit-aware loop.
- 12:50Z -> 20:10Z loop 2: P4 review/H2 -> P5 -> P6 (place PASS, size earned) -> P7 (drc_routed PASS; one 52-min limit wait, one iteration lost to a backgrounded agent) -> P8 (verify PASS after 5 errors, H4) -> P9 (dfm PASS) -> P10 (package, attestation, quote). 3 iterations, $163.
- Wall clock 13.6 h, ~3.4 h of it lost to limits/relaunch. Nominal spend $291 (subscription accounting).

## What the run did well

- Research with fresh second readers (22/23 records verified, 6 refuted) changed the design twice on evidence (I2C pull-ups 1.5 k; BOOT0 pull-down).
- P3 caught two fab-reaching library defects (SHT40 die pad soldered; tantalum with no polarity marking).
- P4 review turned a THT-into-SMT-order defect into a fix (native DNP) and added `schlib.Sheet.mark_dnp()` to the skill.
- P6 earned the outline, silk 13 -> 0 via a new `place_edit silk_clear` op (SWIG traps documented).
- P8: 4/5 errors fixed on the merits, 1 proven a checker artifact (pour_neckdown on tiled pours), thermal waiver with measured theta_JA anchors; constraints/gates untouched (git-verified).
- P10: found the dfm gate had PASSED with a skipped BOM leg (missing sidecar), fixed it, re-ran 8/8, reissued the attestation.

## Open items (owner)

1. **Curved traces** where straight/45 would do (owner, 18:19Z) - style; post-run `reroute-net` pass or a router default. Not changed in this run.
2. **Ordering** - H5 packet in `log/H5.md`; the JLC cart is the only real quote. Put the Sensirion remarks in the order.
3. **Silk** - 4 of 8 header pin labels have no legal spot on this outline (full pinout in `fab/README.md` + design doc).
4. **Skill: a skipped gate leg must not read as PASS** (`coverage.skipped_error`) - lesson recorded; candidate fix in gate.py.
5. **10.0.5 fixture deltas / bench baselines** - env PR #1; and the root `LEARNINGS.md` / `design/ladder-triage.md` rows (this branch 315-335 vs env 315-321) need renumbering when both merge.

## Environment (what the port needed, all on `env/linux-container`, PR #1)

Xvfb display for SWIG Specctra routing; KiCad-10 `private` library-property sanitizer for generated schematics; loop waits out usage limits; milestone-only watcher; `[supervisor]` commits are legitimate; headless rule (never background an agent and end the turn).
