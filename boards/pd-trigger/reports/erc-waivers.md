# Schematic review waivers (pd-trigger)

W1 dp-dm-short-at-chip: architecture's PD-only short (/BC12_DIS) ACCEPTED by
the reviewer as hardware-SAFER than the datasheet's connector wiring (removes
a 21V-onto-3.8V-abs-max fault path). Cost: no QC/BC legacy support - the
board is "PD sources only"; goes on B.SilkS + order docs.
W2 vdd-worst-corner: true worst case 0.979mA at 4.4V low-line all-straps-
closed vs unpublished CH224K IDD - bounded by WCH's own reference circuit;
V1 bring-up step: measure VDD at the 5V profile; contingency = both 510R -> 
smaller (documented floor 600R total).
Bring-up addenda: buzz out Q1 E/B/C once (clone PDF JS-gated; Nexperia-
standard pinning verified as the compatibility claim).
