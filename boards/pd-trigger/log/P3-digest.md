# P3 digest (pd-trigger)
parts.json 24 lines / 28 refs (post-amendment); extracts C970725 (CH224K:
pin map verified, CFG table verified, VDD shunt + 1k dropper canonical,
VBUS sense 13.5V abs max + 10k mandatory, NO CC Rd, IDD unpublished ->
bring-up item) + C14170 (L78L33 - later REMOVED by amendment). P2 bounce-
back executed: LDO dropped (5 reasons), dropper 2x510R-1206-series 3x
derated, straps 100k to /VDD, PG unconnected, R14 0R /VIND stub, LEDs
re-specced (green-gap catalog ceiling flagged). Librarian: 24/24 pulled
clean first pass, U1 pad-11=GND trap RESOLVED (symbol+footprint agree),
J1 land exact vs GCT, 4 approved edits (peg np_thru x2 + LED dots + SW1
internal texts) -> scratch DRC 17->0; model paths abs-fixed; EDITS.md.
SW1 pairs 1-6/2-5/3-4 (generator must hard-code). 14/16 courtyards < pad
field (placelib compensates).
