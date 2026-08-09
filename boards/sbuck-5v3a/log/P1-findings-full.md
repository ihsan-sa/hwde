# P1 Research digest - sbuck-5v3a

Roster: 3 component scouts (buck IC / magnetics+caps / protection+IO), 1 power
architect, 1 reference-design (wave 2, seeded with the IC shortlist), plus one
re-scout to correct magnetics+caps against the architect's budget.

## Findings that changed the design

- **Two brief-named families are ASYNCHRONOUS.** TI TPS54360 and MPS MP1584EN
  integrate a high-side FET only and need an external catch diode, per their own
  datasheets. Hard disqualification. Exactly the failure the brief's "do not trust
  remembered ratings" instruction targets.
- **Every ferrite-wound shielded inductor fails** once vendor Isat/Itemp is derated
  to 50 C ambient - including the best-DCR parts (TDK VLS6045EX, FNR6045S, NR6045).
  Metal-composite/molded only.
- **The first inductor sweep only searched <=6x6 mm** and so missed the DCR ceiling
  by 2x. Re-searched at 7x7-13.5x12.8 mm: DCR <= 25 mOhm IS reachable.
- **AP64350's UVLO divider draws 7-10 mA** to hit 6.5/6.0 V (8% VON/VOFF gap forces
  near-cancellation) = ~120 mW always-on, 6% of budget. LMR33630 hits the same
  target at 23 uA. Single biggest differentiator found.
- **The loss budget IS the thermal budget**: 19 C/W per watt, board near-isothermal
  (33 mm spreading length > half-board). Worst Tj 99.7 C vs a 105 C derated limit.
- **Exposed pad alone = 138 C/W -> Tj 188 C**, quantitatively confirming the brief's
  warning. Package rule: exposed pad, thetaJC(bot) <= 5 C/W, thetaJA(2s2p) <= 45 C/W.
- **Inrush is benign, no gate RC** - the P-FET body diode is forward in the normal
  direction, so a gate RC cannot limit inrush at all. The real hazards are the
  25.4 V hot-plug ring (needs a 15 V Vgs Zener clamp) and bulk-cap ESR as a
  DAMPING requirement (50-300 mOhm, so no low-ESR polymer).
- **Board surface 83-87 C forces X7R everywhere**; X5R (85 C) is a latent failure.

## Conflicts resolved before P2

| Conflict | Resolution |
|---|---|
| Architect DCR <= 25 mOhm vs shortlist 53-60 mOhm | Re-scout: FAUL1050-6R8MT, 18.5 mOhm cold / ~24.05 mOhm hot |
| Scout polymer bulk 30 mOhm vs architect 50-300 mOhm damping window | Re-scout: KNM2100UF35V149EC0055, 80 mOhm @100 kHz |
| Scout X5R Cout vs architect X7R-only | X7R TCC1210X7R226K250MT; bias derate improves so 5-6 parts, not 6-7 |
| Protection scout "no Vgs clamp needed" vs architect "mandatory" | Clamp included - static 18 V is fine on +/-25 V, the 25.4 V ring is not |

## Left open for P2 (deliberately)

- IC choice AP64350 vs LMR33630 vs SY8205. The 4.0 A current-limit-min floor that
  disqualified LMR33630 was a DELEGATE tightening (Q5), not a user requirement, and
  P2 is explicitly authorised to revisit it.
- fsw is COUPLED to inductor availability: LMR33630A is fixed 400 kHz, and the
  400 kHz/10 uH inductor slot is the weak one (MDA1365-100M sits AT 25 mOhm hot,
  stock 645). AP64350 at 500 kHz gets the clean part.
- Vendor reference layouts use 2 oz copper; the architect computed that 2 oz does
  NOT help thermally. Must be reconciled, not averaged.
- SY8205 publishes a 5 A MIN current limit but labelled BOTTOM-FET (reference-design)
  vs "no MIN published" (component scout). Ambiguous; documentation gaps besides.

## Traps documented for later reuse

- cjiang-family Max/Typ column reversal in Isat/Itemp tables (parts_search surfaces
  Typ, not the conservative Max).
- TDK SLF12565T-100M4R8-PF is both ferrite-trapped AND EOL - stock count alone did
  not reveal the EOL status.
- No vendor DC-bias curve was obtainable for any MLCC (Murata publishes a 292-page
  catalogue pointing at its SimSurfing web tool). All bias-derated capacitance
  figures are flagged conventional estimates, not vendor data.
