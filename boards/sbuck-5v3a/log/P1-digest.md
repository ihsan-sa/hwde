# P1 Research digest - sbuck-5v3a  (detail: log/P1-findings-full.md)

- Roster: 3 scouts + power architect + reference-design, plus 1 re-scout to correct
  magnetics against the architect's budget. All fragments in research/.
- TPS54360 and MP1584EN are ASYNCHRONOUS per their own datasheets - disqualified.
- Every ferrite-wound inductor fails Isat/Itemp derated to 50 C; metal-composite only.
- First inductor sweep missed the DCR ceiling 2x by only searching <=6x6 mm. Re-search:
  DCR <= 25 mOhm reachable (FAUL1050-6R8MT, 18.5 mOhm cold / 24.05 mOhm hot).
- AP64350 UVLO divider draws 7-10 mA (~120 mW, 6% of budget); LMR33630 does it at 23 uA.
- Loss budget IS the thermal budget: 19 C/W per watt, worst Tj 99.7 C vs 105 C limit.
- Exposed pad alone = 138 C/W -> Tj 188 C. Package rule: pad + thetaJA <= 45 C/W.
- Inrush benign (body diode forward - a gate RC cannot limit it); real hazards are the
  25.4 V hot-plug ring (15 V Vgs Zener) and bulk ESR as damping (50-300 mOhm, no polymer).
- Board surface 83-87 C forces X7R everywhere; X5R is a latent failure.
- 4 research conflicts resolved explicitly (DCR, bulk ESR, dielectric, Vgs clamp).
- Left for P2: IC choice (4.0 A floor is revisitable - it was a delegate tightening),
  fsw coupled to inductor stock, and vendor 2 oz layouts vs "2 oz does not help".
