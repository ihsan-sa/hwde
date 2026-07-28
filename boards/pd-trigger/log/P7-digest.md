# P7 digest (pd-trigger)
Both prescribed premises FALSIFIED by measurement: 1.75mm tracks cannot
touch J1 VBUS pads (1.465 max), CC-displacement wouldn't have helped (pads
pinch, not escapes). Solution: F.Cu POUR fan-in/merge (3.5mm copper, zones
exempt from track width rules) + 3.0mm trunk + 0 VBUS vias. route_critical
KRT attempt self-rolled-back (9 shorts) - abandoned honestly. rules_gen
netclass defect found (one Power class at max width would force 1.75mm into
0.5mm-pitch pads): split in .kicad_pro, DRU untouched. FR rung 1 completion
1.0; dedup removed 3 echoes (S14 fix live); stitch 8 GND vias (2 relocated);
plane_repair 0 splits. C1B pour-channel honesty disclosed (1.11+1.25mm,
checker-blind). Gate PASS 0/0. Cleanup skipped per V13.
