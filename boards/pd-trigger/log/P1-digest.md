# P1 digest (pd-trigger)
3 researchers (scout sonnet, interface+power opus). Scout: LEAD CH224K
(C970725 ESSOP-10, straps verified from datasheet), alt HUSB238A (QFN);
IP2721/CYPD3177/FUSB302/CH224Q disqualified with reasons; JLC placeholder-row
hazard found. Interface: CC no-impedance (BMC 300k), receptacle 5A =
collective 1.25A/contact + 20V-rating trap, TVS MANDATORY (chip-death
precedent), VDD shunt-dropper 0.28W trap, DP/DM-short vs check_diffpair trap
(diff_pairs: [] required). Power: 2oz REQUIRED (stackups.yaml entry added),
main-path PTC dropped (decision), LDO over dropper, VDD IDD unresolved ->
extract confirms, thermal entries J1/U2.
