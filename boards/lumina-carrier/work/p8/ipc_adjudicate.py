"""IPC-2221 row re-adjudication + IPC-2221 thermal check for the +12V residual.

Calibrates the classic IPC-2221 current/width formula against check_current's own
published requirement, then reports dT for the as-built width at each declared
current. JSON to stdout.
"""
import json

# IPC-2221 Table 6-1, 51-100 V band, verified 2026-07-29 against:
#   ema-eda.com/ema-resources/blog/pcb-clearance-and-creepage-distance-table/
#   help.altair.com/Pollex (quotes 6.3.4 verbatim)
#   protoexpress.com/blog/ipc-2221-circuit-board-design/
# All three tabulations agree.
ROWS = {
    "B1_internal":            {"0-15": 0.05, "16-30": 0.05, "31-50": 0.10, "51-100": 0.10, "101-150": 0.20},
    "B2_ext_uncoated_le3050": {"0-15": 0.10, "16-30": 0.10, "31-50": 0.60, "51-100": 0.60, "101-150": 0.60},
    "B3_ext_uncoated_gt3050": {"0-15": 0.10, "16-30": 0.10, "31-50": 0.60, "51-100": 1.50, "101-150": 3.20},
    "B4_ext_polymer_coated":  {"0-15": 0.05, "16-30": 0.05, "31-50": 0.13, "51-100": 0.13, "101-150": 0.40},
    "A5_ext_conformal":       {"0-15": 0.13, "16-30": 0.13, "31-50": 0.13, "51-100": 0.13, "101-150": 0.40},
    "A6_lead_uncoated":       {"0-15": 0.13, "16-30": 0.25, "31-50": 0.40, "51-100": 0.50, "101-150": 0.80},
    "A7_lead_conformal":      {"0-15": 0.13, "16-30": 0.13, "31-50": 0.13, "51-100": 0.13, "101-150": 0.40},
}

# IPC-2221 eq: I = k * dT^0.44 * A^0.725   (A in mil^2, I in A, dT in C)
K_EXTERNAL = 0.048
MM_PER_MIL = 0.0254
OZ1_MM = 0.035          # 1 oz finished outer copper


def area_mil2(w_mm, t_mm=OZ1_MM):
    return (w_mm / MM_PER_MIL) * (t_mm / MM_PER_MIL)


def current_for(w_mm, dt_c, k=K_EXTERNAL):
    return k * (dt_c ** 0.44) * (area_mil2(w_mm) ** 0.725)


def dt_for(w_mm, i_a, k=K_EXTERNAL):
    return (i_a / (k * area_mil2(w_mm) ** 0.725)) ** (1 / 0.44)


def width_for(i_a, dt_c, k=K_EXTERNAL):
    lo, hi = 0.01, 20.0
    for _ in range(200):
        mid = (lo + hi) / 2
        if current_for(mid, dt_c) < i_a:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


out = {"ipc_2221_table_6_1_51_100V": {k: v["51-100"] for k, v in ROWS.items()},
       "ipc_2221_table_6_1_101_150V": {k: v["101-150"] for k, v in ROWS.items()}}

# --- calibration: does the formula reproduce check_current's own numbers? ---
cal = []
for i_a, published in ((2.0, 1.1), (1.0, 0.5), (0.6, None)):
    cal.append({"current_a": i_a, "dt_c": 10,
                "formula_width_mm": round(width_for(i_a, 10), 4),
                "check_current_published_mm": published})
out["calibration_vs_check_current"] = cal

# --- the +12V residual: e109de59 (67.700,114.250)-(67.700,125.500) ---
W = 0.620
seg = {"uuid": "e109de59", "net": "+12V", "layer": "F.Cu",
       "width_mm": W, "length_mm": 11.25,
       "widen_ceiling_mm": 0.626, "blocker": "/pwr/SW33",
       "required_at_2A_dt10_mm": round(width_for(2.0, 10), 4),
       "area_mil2": round(area_mil2(W), 2)}
for label, i_a in (("fault_ceiling_2.0A_converter_OCP", 2.0),
                   ("sustained_at_1.25A_ICD_s6.2", 1.25),
                   ("sustained_af_0.75A_ICD_s6.2", 0.75)):
    seg[f"dt_c_at_{label}"] = round(dt_for(W, i_a), 2)
seg["dt_c_if_widened_to_ceiling_0.626_at_2A"] = round(dt_for(0.626, 2.0), 2)
seg["current_a_at_dt10_as_built"] = round(current_for(W, 10), 3)
out["plus12V_e109de59"] = seg

print(json.dumps(out, indent=1))
