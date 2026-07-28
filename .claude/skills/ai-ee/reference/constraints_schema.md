# constraints.json - the merged, machine-readable constraint set

Written at P2 by the architect (from P1 research fragments), placed next to the
board (`kicad/constraints.json`) at P5. Every key is optional: a script whose
key is absent no-ops cleanly. Net names must match the FINAL netlist names
(local-label nets carry a leading `/` like `/MCO`; power nets are bare: `+3V3`,
`GND`, `VBUS`).

Consumers per key (script -> phase):

```jsonc
{
  // check_return_path (P8), rules_gen impedance (P5), planes_gen (P7 -
  // every referenced plane net/layer is guaranteed a pour)
  "high_speed": [{
    "net": "/USB_DP",
    "reference": "GND",              // or {"F.Cu": "GND", "B.Cu": "+3V3"}
    "k": 3,                          // corridor = k x trace width (default 3)
    "t_rise_ns": 1.0,                // sets return-via radius + stitch pitch
    "return_via_radius_mm": 2.0,     // fallback when t_rise_ns absent
    "impedance_ohm": 50              // optional; rules_gen sizes the width
  }],

  // check_current (P8), rules_gen per-net width rules (P5),
  // route_critical power routing (P7), place_anneal rule term (P6),
  // check_pdn decoupling inventory (P8)
  "power": [{
    "net": "+3V3", "current_a": 0.4, "dt_c": 10, "via_amps": 0.5,
    "overrides": [{"near": [118.5, 108.0], "radius_mm": 5, "current_a": 0.2}]
  }, {
    // width-only entry: "pdn": false opts a net OUT of check_pdn's
    // decoupling inventory. Use for nets declared solely so rules_gen sizes
    // their trace (e.g. the raw-input stub BEFORE a reverse-polarity
    // element) - nothing decouples them by design.
    "net": "/VIN", "current_a": 0.3, "pdn": false
  }],

  // check_diffpair (P8), rules_gen gap rules (P5), route_critical (P7).
  // Omit entirely to auto-discover pairs by name suffix (_P/_N, DP/DM,
  // D+/D-); an EXPLICIT empty list disables the check.
  "diff_pairs": [{
    "p": "/USB_DP", "n": "/USB_DM", "base": "USB",
    "impedance_ohm": 90,             // differential target
    "gap_mm": 0.2, "max_skew_mm": 5, "max_uncoupled_mm": 5
  }],

  // check_creepage (P8): IPC-2221 spacing for pairs > 30 V apart
  "voltages": [{"net": "HV_BUS", "voltage": 48}],

  // check_thermal (P8), place_anneal spreading term (P6)
  "thermal": [{"ref": "U2", "power_w": 0.8, "net": "GND", "dt_c": 40,
               "min_vias": 4}],

  // placelib/place_seed/place_metrics/place_anneal (P6)
  "placement": {
    "edges": [{"ref": "J1", "edge": "left", "pos": 0.5, "rot": 90}],
    //        edge in left|right|top|bottom (render-oriented: top = min y);
    //        pos 0..1 along the edge (omit = distributed); rot optional
    "groups": [{"name": "xtal", "anchor": "Y1", "members": ["C8", "C9"]}],
    "keepouts": [{"rect": [x1, y1, x2, y2], "side": "front",
                  "reason": "antenna"}],   // or "poly": [[x,y], ...]
    "fixed": ["H1", "H2"],
    "separation": [{"a": ["U3"], "b": ["U5"], "min_mm": 10}]
  },

  // planes_gen (P7). Defaults when absent: 2-layer -> B.Cu GND pour;
  // 4-layer -> In1 GND + In2 dominant-power; high_speed references are
  // always guaranteed a plane.
  "planes": [{"layer": "In2.Cu", "net": "+3V3",
              "region": [x1, y1, x2, y2]}]   // region optional (full board)
}
```

The board-adjacent `decoupling.json` (associations of cap -> IC power pin) is
a SEPARATE file emitted by the schematic generators (schlib
`place_ic_with_decoupling` + `Project.save(decoupling=...)`); shape:
`{"associations": [{"cap": "C1", "ic": "U1", "pin": "48", "rail": "+3V3",
"value": "100nF", "gnd": "GND", "class": "hf", "max_dist_mm": 5,
"max_loop_nh": 6}]}` (class/max_* optional; consumed by check_decoupling,
check_pdn, place_seed satellite clustering, place_metrics).

Sources for the numbers: interface budgets from research (P1 interface-spec),
currents from the power tree (P1 power-architect), impedances from
`reference/stackups.yaml` controlled_impedance tables (P2 stackup selection).
