# P10 Ordering digest - g0-sense (2026-08-27)

- **Release attestation rev 2, verifies valid**, disposition **order-ready**
  (sha256 2a0035eb). All five gates PASS and FRESH; 0 open issues; H4 approved.
- **H5 NOT taken. Nothing was ordered.** The run contract withholds payment,
  there are no credentials in this container, and `order_submit --api-create`
  was never run. `fab/order.json` sits at `ready_for_human`.
- Quote (`fab/quote.json`, every figure `estimated: true` - the JLC cart is the
  only real quote; the API path needs credentials this container does not have):
  **qty 5 = USD 42.68 total, 8.54/unit** (PCB 2.00 + assembly 40.68: setup 8.00,
  feeders 24.00 for 8 Extended parts, stencil 8.00, joints 0.68 over 80 joints).
  qty 10 = 43.36 (4.34/unit); qty 30 = 52.98 (1.77/unit).
- **A COVERAGE HOLE WAS FOUND AND CLOSED HERE**, by the artifact sweep rather
  than by any gate: `state.py freshness` showed the registered artifact `parts`
  (`kicad/parts.json`) as exists=False, because parts.json lived only in
  `parts/`. The recorded dfm gate had therefore been running **7 of 8 legs**
  with `skipped_error {'bom': 'no parts.json'}` and still reporting PASS - and
  attestation rev 1 was built on it. Copied the sidecar beside the board (the
  established convention, verified by diff on bb-amp/bb-buck/bb-mcu), re-ran
  dfm to **8/8 legs, no skips, PASS**, and the attestation correctly refused to
  verify ("input parts: changed since attestation") until reissued as rev 2.
- `fab/` holds the JLC package (gerbers + drill + zip, BOM, BOM-full, CPL),
  `quote.json`, `order.json`, `attestation.json` and a `README.md` checklist
  carrying the Sensirion no-wash rules, the "no break-off tabs on the sensor
  tongue" panelization remark, the full J3/J4 pinout (owed because the silk
  could not fit 4 of 8 pin labels) and the polarity/rotation table.
- Toolchain fix committed separately from the board: `releaselib._ws_rel`.
  A waiver sidecar resolves absolute while `--workspace` stays relative, so
  `Path.relative_to` raised and broke `attest.py build` outright while silently
  degrading `state.py resume`'s `release_disposition` to null - the exact field
  the done-check reads. g0-sense is the first attested board carrying a waiver,
  which is why it surfaced now. Regression-tested on both pre-existing attested
  boards in both path forms; pre-fix attestations still verify unchanged.
