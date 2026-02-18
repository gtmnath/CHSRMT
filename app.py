# ======================================================================
# BLOCK 1 — Imports, page config, utilities, session defaults
# ======================================================================
"""
CHSRMT — Proprietary Evaluation License

Copyright (c) 2025
Dr. Gummanur T. Manjunath, MD
All Rights Reserved
"""

import math
import pandas as pd
import requests
import streamlit as st
from datetime import datetime

APP_VERSION = "v2.0.1-WBGT-Field"

st.set_page_config(
    page_title="CHSRMT",
    layout="wide",
)

# ----------------------------
# Global CSS (compact + mobile-fit improvements)
# ----------------------------
st.markdown("""
<style>

/* ---------- Typography ---------- */
h1 {font-size: 1.40rem !important; margin-bottom: 0.25rem;}
h2 {font-size: 1.20rem !important; margin-bottom: 0.20rem;}
h3 {font-size: 1.00rem !important; margin-bottom: 0.15rem;}

div[data-testid="stMarkdownContainer"] p {
    margin-bottom: 0.12rem;
}

/* Tighten bullet spacing */
.stMarkdown ul {
    margin-top: 0.20rem;
    margin-bottom: 0.30rem;
    padding-left: 1.1rem;
}
.stMarkdown li {
    margin-bottom: 0.12rem;
}

/* ---------- Welcome Header ---------- */
.welcome-box {
    background: linear-gradient(90deg, #0f4c75, #3282b8);
    padding: 0.55rem 0.70rem;
    border-radius: 10px;
    color: white;
    margin-bottom: 0.30rem;
}

.welcome-box h2 {
    font-size: 1.10rem;
    margin-bottom: 0.10rem;
    font-weight: 700;
}

.welcome-box p {
    font-size: 0.85rem;
    opacity: 0.92;
    margin: 0.08rem 0;
}

/* ---------- Section Headings ---------- */
.section-title {
    color: #1f6fb2;
    font-weight: 700;
    font-size: 1.08rem;
    margin-top: 0.35rem;
    margin-bottom: 0.10rem;
}

.section-sub {
    color: #5f7f9c;
    font-size: 0.88rem;
    margin-bottom: 0.15rem;
}

/* ---------- Layout Tightening ---------- */
div.block-container {
    padding-top: 0.85rem;
    padding-bottom: 1.10rem;
}

div[data-testid="stVerticalBlock"] {
    gap: 0.32rem;
}

div[data-testid="stHorizontalBlock"] {
    gap: 0.50rem;
}

/* ---------- Mobile Optimization ---------- */
@media (max-width: 700px) {

  div[data-testid="stHorizontalBlock"] {
      gap: 0.30rem;
  }

  div.block-container {
      padding-left: 0.65rem;
      padding-right: 0.65rem;
  }

  h2 {
      margin-top: 0.05rem !important;
  }

}

</style>
""", unsafe_allow_html=True)

# ======================================================
# SESSION STATE HANDLE (MUST BE DEFINED BEFORE ANY ss[...] USE)
# ======================================================
ss = st.session_state

def ss_default(key, val):
    """Set a session default only if the key does not exist."""
    if key not in ss:
        ss[key] = val

# ----------------------------
# Unit conversion helpers
# ----------------------------
def c_to_f(c): return (c * 9/5) + 32
def f_to_c(f): return (f - 32) * 5/9
def ms_to_mph(v): return v * 2.23694
def mph_to_ms(v): return v / 2.23694
def kpa_to_inhg(k): return k * 0.2953
def inhg_to_kpa(i): return i / 0.2953

def fmt_temp(temp_c, unit):
    return f"{temp_c:.1f} °C" if unit == "metric" else f"{c_to_f(temp_c):.1f} °F"

# ----------------------------
# Locked HSP band edges (DO NOT change per run)
# ----------------------------
HSP_GREEN = 6.0   # Unrestricted
HSP_AMBER = 4.0   # Caution
# else -> Withdrawal

# ----------------------------
# MWL (Metabolic Work Load) model parameters
# These are "calibration knobs" that we will tune using your field scenarios.
# ----------------------------
ss_default("MWL_A0", 450.0)     # base W/m²
ss_default("MWL_A_wb", 12.0)    # wet-bulb adjustment weight
ss_default("MWL_A_rad", 4.0)    # radiant adjustment weight (GT-DB)
ss_default("MWL_A_wind", 10.0)  # wind benefit weight (sqrt(ws))
ss_default("MWL_MIN", 60.0)     # clamp
ss_default("MWL_MAX", 450.0)    # clamp

# Penalty → MWL capacity reductions (W/m² per °C-penalty bucket)
ss_default("MWL_PPE_W", 18.0)
ss_default("MWL_VEH_W", 12.0)
ss_default("MWL_RAD_W", 10.0)
ss_default("MWL_ADH_W",  8.0)

def estimate_mwl_wm2(db_c: float, rh_pct: float, ws_ms: float, gt_c: float, wbgt_c: float) -> float:
    """Estimate MWL (cooling capacity) in W/m².

    Design intent:
    - MWL should generally DECREASE as WBGT increases (more heat load).
    - MWL should INCREASE with wind (convective/evaporative support).
    - MWL should DECREASE with radiant load (GT-DB gap).
    - MWL should DECREASE as RH rises (evaporation suppressed), with a stronger penalty when Wet Bulb is high.

    Note: This is a conservative proxy (not a full physiological TWL engine).
    """
    # Guard rails
    db_c = float(db_c)
    rh_pct = float(max(0.0, min(100.0, rh_pct)))
    ws_ms = float(max(0.0, ws_ms))
    gt_c = float(gt_c)
    wbgt_c = float(wbgt_c)

    # ── 1) Base MWL from WBGT (smooth, bounded) ──
    mwl_base = 600.0 - 0.30 * (wbgt_c ** 2)  # higher WBGT → lower MWL
    mwl_base = max(0.0, min(450.0, mwl_base))

    # ── 2) Wind modifier (log response, capped) ──
    wind_mod = 1.0 + 0.18 * math.log1p(ws_ms)  # 0 m/s → 1.0, 1 m/s → ~1.12
    wind_mod = max(0.85, min(1.40, wind_mod))

    # ── 3) Radiant modifier (GT above DB reduces capacity) ──
    delta_gt = max(0.0, gt_c - db_c)
    rad_mod = 1.0 - 0.005 * delta_gt
    rad_mod = max(0.75, min(1.05, rad_mod))

    # ── 4) RH modifier (higher RH suppresses evaporation) ──
    if rh_pct <= 20.0:
        rh_mod = 1.0 + 0.08 * (20.0 - rh_pct) / 20.0   # up to +8%
    elif rh_pct <= 60.0:
        rh_mod = 1.0 - 0.10 * (rh_pct - 20.0) / 40.0   # down to 0.90
    else:
        rh_mod = 0.90 - 0.35 * (rh_pct - 60.0) / 40.0  # down to 0.55 at RH 100
    rh_mod = max(0.55, min(1.08, rh_mod))

    # ── 5) Extra penalty when Wet Bulb is high (evaporation “ceiling”) ──
    def _stull_wb_c(t_c: float, rh: float) -> float:
        rh = max(0.0, min(100.0, rh))
        return (
            t_c * math.atan(0.151977 * math.sqrt(rh + 8.313659))
            + math.atan(t_c + rh)
            - math.atan(rh - 1.676331)
            + 0.00391838 * (rh ** 1.5) * math.atan(0.023101 * rh)
            - 4.686035
        )

    wb_c = _stull_wb_c(db_c, rh_pct)
    ss["wb_mwl_c"] = wb_c  # ✅ diagnostic only; do not overwrite main WB used elsewhere
    if wb_c > 25.0:
        wb_pen = 1.0 - 0.015 * (wb_c - 25.0)   # 30°C WB → ~0.925
        wb_pen = max(0.55, min(1.0, wb_pen))
    else:
        wb_pen = 1.0

    mwl = mwl_base * wind_mod * rad_mod * rh_mod * wb_pen
    mwl = max(0.0, min(450.0, mwl))
    return float(mwl)

def apply_capacity_penalties(mwl_env: float, ppe_c: float, veh_c: float, rad_c: float, adh_c: float) -> float:
    """
    Convert your °C-style penalties into a reduction in metabolic capacity (W/m²).
    This is the key link that lets HSP change meaningfully AFTER penalties.
    """
    loss = (
        float(ss["MWL_PPE_W"]) * max(0.0, ppe_c) +
        float(ss["MWL_VEH_W"]) * max(0.0, veh_c) +
        float(ss["MWL_RAD_W"]) * max(0.0, rad_c) +
        float(ss["MWL_ADH_W"]) * max(0.0, adh_c)
    )
    mwl_op = max(float(ss["MWL_MIN"]), mwl_env - loss)
    return float(mwl_op)

# ----------------------------
# SESSION STATE BOOTSTRAP
# ----------------------------
ss_default("units", "metric")       # display units only
ss_default("band_units", "metric")  # risk band units for sidebar

# Core environmental storage (always internal °C, m/s, kPa)
ss_default("db_c", 32.0)
ss_default("rh_pct", 60.0)
ss_default("ws_ms", 1.0)
ss_default("p_kpa", 101.3)
ss_default("gt_c", 35.0)

# WBGT storage
ss_default("wbgt_raw_c", None)
ss_default("wbgt_eff_c", None)
ss_default("wbgt_base_frozen", None)
ss_default("penalties_applied", False)
ss_default("total_penalty_c", 0.0)

# Risk thresholds
ss_default("thr_A_c", 29.0)
ss_default("thr_B_c", 32.0)
ss_default("thr_C_c", 35.0)

# Penalties (internal °C)
ss_default("pen_clo_c", 0.0)
ss_default("pen_veh_c", 0.0)
ss_default("pen_rad_c", 0.0)
ss_default("pen_adhoc_c", 0.0)

# Instrument references (optional)
ss_default("twl_measured", 0.0)
ss_default("wbgt_instr", 0.0)

# Logging
ss_default("audit_log", [])

# ----------------------------
# Landing gate
# ----------------------------
ss_default("landing_open", False)

# --- Welcome gate latch (survives idle reconnect by using URL query param) ---
try:
    if st.query_params.get("started") == "1":
        ss["landing_open"] = True
except Exception:
    pass

if not ss["landing_open"]:
    st.markdown("""
    <h2 style='margin-bottom:0.2rem;'>CHSRMT</h2>
    <p style='margin-top:0; color: #555;'>
    Field-Ready Decision Support For Occupational Heat Stress And Heat Strain
    </p>
    """, unsafe_allow_html=True)

    st.markdown("<div style=\"border-top:1px solid rgba(0,0,0,0.10); margin:0.20rem 0 0.40rem 0;\"></div>", unsafe_allow_html=True)

    st.markdown("""
    <div class="welcome-box">
        <h2 style="margin-bottom:0.25rem;">☀️ CHSRMT-Field Heat-Stress Assessment Dashboard</h2>
        <p style="margin-top:0.15rem;">
          <b>WBGT</b> = Regulatory Screening / Compliance Guide For Environmental Heat Hazard.<br>
          <b>Heat Strain Profile (HSP)</b> = Human Cooling Ability vs Heat Load Using Cooling Capacity (W/m²).
        </p>
        <p style="margin-bottom:0;">
          <b>Workflow:</b> Inputs → Baseline WBGT → Exposure Adjustments → Effective WBGT → HSP → Guidance → Logging
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### What This Tool Does")
    st.markdown("""
- Computes **Baseline WBGT** and **Effective WBGT** (After Clothing/PPE, Vehicle/Enclosure, Radiant/Hot Surfaces, And Ad-Hoc Adjustments)
- Uses **Instrument TWL (W/m²)Readings** *if available* (sites with TWL instruments can enter the reading)
- Estimates **MWL (W/m²)** when an instrument TWL reading is not available
- Computes **HSP** (Heat-Strain Profile) to express **Human Cooling Margin** under current conditions
- Provides **Supervisor Guidance** and maintains an **Audit Log**
""")

    # Collapsible definitions / explanations (compact welcome screen)
    with st.expander("📘 Definitions & Explanations (tap to expand)", expanded=False):
        st.markdown("""
**Core terms**
- **Heat Stress**: External Thermal Load from the environment and work conditions
- **Heat Strain**: The Body’s Physiological Response while trying to maintain thermal balance
- **Wet-Bulb (WB)**: Reflects Evaporative Potential and how effectively sweat can evaporate (a key physiological limiter)
- **WBGT**: Screening / Regulatory Heat-Hazard Index used for compliance and baseline decisions
- **TWL (Thermal Work Limit)**: Instrument-Measured cooling capacity of the environment (W/m²)
- **MWL (W/m²)**: Modeled Cooling Capacity when TWL instrumentation is not available  
  – Higher MWL → Longer Sustainable Work Duration  
  – Lower MWL → Shorter Sustainable Work Duration
- **HSP (Heat-Strain Profile)**: Heat Demand Relative To Human Cooling Capacity  
  – Lower HSP = Safer  
  – Higher HSP = Reduced Ability To Dissipate Heat
- **Acclimatization**: Improves Sweat Efficiency, Cardiovascular Stability, And Overall Heat Tolerance

**HSP interpretation (practical)**
- 🟢 **HSP < 0.80** → Cooling Exceeds Heat Load  
- 🟠 **0.80–0.99** → Heat Balance Marginal  
- 🔴 **HSP ≥ 1.00** → Heat Gain Likely Exceeds Heat Loss
""")

    st.warning("Decision-Support Only. Does Not Replace Site HSE Policy, IH / OH Judgement, Or Medical Protocols.")

    # Make the start action prominent and near the bottom (but not buried)
    st.markdown("---")
    if st.button("🚀 Start Heat-Stress Assessment", type="primary", use_container_width=True):
        ss["landing_open"] = True
        try:
            st.query_params["started"] = "1"
        except Exception:
            pass
        st.rerun()

    st.stop()

# ----------------------------
# Working page header
# ----------------------------
st.markdown("""
<h2 style='margin-bottom:0.2rem;'>Calibrated Heat Stress Risk Management Tool (CHSRMT)</h2>
<p style='margin-top:0; margin-bottom:0.25rem; color:#222; font-weight:800;'>
CHSRMT - Field-Ready Decision Support For Occupational Heat Stress And Heat Strain
</p>
""", unsafe_allow_html=True)

st.markdown(
    "<span style='color:#444;'>Location → Weather → Baseline → Exposure adjustments → Effective WBGT → HSP (before/after) → Guidance → Logging</span>",
    unsafe_allow_html=True
)

# ======================================================
# MAIN-PANEL DISPLAY UNITS (MOBILE SAFE)
# ======================================================
st.markdown("### 🔧 Choose Display Units")

unit_choice_main = st.radio(
    "",
    ["Metric (°C, m/s, kPa)", "Imperial (°F, mph, inHg)"],
    horizontal=True,
    index=0 if ss["units"] == "metric" else 1,
    key="units_main_panel",   # UNIQUE KEY — NEVER reuse elsewhere
)

ss["units"] = "metric" if unit_choice_main.startswith("Metric") else "imperial"

st.markdown("""
**HSP (Heat-Strain Profile)** shows **two values**  
• Environmental HSP (before PPE/enclosure)  
• Operational HSP (after exposure adjustments)  

Lower HSP = **Better Cooling Margin**.
""")

# -------------------------
# Reset Assessment (main page, confirmed)
# -------------------------
st.markdown("---")
if st.button("🔄 Reset Assessment (Clear Current Inputs & Results)"):
    ss["confirm_reset"] = True

if ss.get("confirm_reset", False):
    st.warning("Are you sure you want to reset the current assessment? Please save or export current results before resetting.")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("✅ Yes, Reset Now"):
            keys_to_clear = [
                # Location / weather
                "city_query","place_name","lat","lon","weather_fetched","weather_provider",
                # Environmental inputs
                "db_c","rh_pct","ws_ms","p_kpa","gt_c","twb_c","wb_c",
                # Baseline / effective WBGT
                "wbgt_raw_c","wbgt_base_c","wbgt_base_frozen","wbgt_eff_c",
                # Exposure adjustments selections + totals
                "adj_ppe_pcls","adj_enclosure_c","adj_radiant_c","adj_solar_c","adj_misc_c",
                "penalties_applied","total_penalty_c",
                # HSP / MWL computed values and status flags
                "mwl_env_sig","mwl_env_prev","hsp_calib_ready",
                # Optional instrument field
                "wbgt_instr",
                # Any cached geo results
                "geo_results","geo_query_sig","place_query","place_label",
                # Diagnostics (safe to clear)
                "wb_mwl_c",
            ]
            for k in keys_to_clear:
                if k in ss:
                    del ss[k]

            # Clear welcome latch so it truly returns to fresh start
            try:
                st.query_params.pop("started", None)
            except Exception:
                pass

            del ss["confirm_reset"]
            st.rerun()
    with c2:
        if st.button("❌ Cancel"):
            del ss["confirm_reset"]


# ======================================================================
# BLOCK 2 — Sidebar controls (Mirror only — no duplicate masters)
# ======================================================================
with st.sidebar:
    st.title("Heat-Stress Controls")

    # ----------------------------
    # DISPLAY UNITS (MIRROR OF MAIN PANEL)
    # ----------------------------
    st.markdown("**Display Units**")

    units_now = ss.get("units", "metric")

    st.write("🧭 Currently selected:")
    st.success("Metric (°C, m/s, kPa)" if units_now == "metric"
               else "Imperial (°F, mph, inHg)")

    st.caption("Change Units From The Main Screen (Mobile-Safe).")

    st.markdown("---")

    # ----------------------------
    # RISK BAND DISPLAY UNITS
    # (this is allowed to be separate)
    # ----------------------------
    band_choice = st.radio(
        "Risk Band Display Units",
        ["Metric (°C)", "Imperial (°F)"],
        index=0 if ss.get("band_units", "metric") == "metric" else 1,
        key="band_units_sidebar"
    )

    ss["band_units"] = "metric" if band_choice.startswith("Metric") else "imperial"

    # ----------------------------
    # WBGT Reference Bands
    # ----------------------------
    A = ss.get("thr_A_c", 29.0)
    B = ss.get("thr_B_c", 32.0)
    C = ss.get("thr_C_c", 35.0)

    st.markdown("**WBGT Risk Band Reference**")
    st.write(f"🟢 LOW RISK: < {fmt_temp(A, ss['band_units'])}")
    st.write(f"🟠 CAUTION: {fmt_temp(A, ss['band_units'])} – {fmt_temp(B, ss['band_units'])}")
    st.write(f"🔴 WITHDRAWAL: ≥ {fmt_temp(C, ss['band_units'])}")

    st.markdown("---")

st.markdown("<div style='height:0.75rem;'></div>", unsafe_allow_html=True)


# ======================================================================
# BLOCK 3 — LOCATION SEARCH (OPEN-METEO GEOCODER)
# ======================================================================
with st.expander("📍 Location Search (City Lookup)", expanded=False):

    # (Optional compactness) Removing duplicate H2 header avoids extra vertical space
    # st.markdown("## 🛰 Location Search (City Lookup)")

    place_query = st.text_input(
        "Enter a city name",
        value=ss.get("place_query", ""),
        placeholder="Example: Dubai, Dallas, Chennai, Phoenix",
        key="place_query_box"
    )

    search_btn = st.button("🔍 Search city", key="geo_search_btn")

    # Store query so it survives reruns
    ss["place_query"] = place_query

    # ---------------------------
    # Trigger search
    # ---------------------------
    if search_btn and place_query.strip():

        try:
            params = {"name": place_query, "count": 10, "language": "en", "format": "json"}
            resp = requests.get(
                "https://geocoding-api.open-meteo.com/v1/search",
                params=params,
                timeout=8
            )
            resp.raise_for_status()
            results = resp.json().get("results", [])
        except Exception:
            results = []

        if not results:
            st.error("❌ No matching locations found — refine your spelling.")
            ss["geo_results"] = None
        else:
            ss["geo_results"] = results
            ss["geo_query_sig"] = place_query.lower().strip()   # 🔐 reset selector when city changes

    # ---------------------------
    # Location picker
    # ---------------------------
    if ss.get("geo_results"):

        results = ss["geo_results"]

        labels = []
        for r in results:
            name = r.get("name", "")
            admin = r.get("admin1", "")
            cc = r.get("country_code", "")
            labels.append(f"{name}, {admin}, {cc}")

        choice = st.selectbox(
            "Select the exact location",
            options=labels,
            key=f"place_pick_{ss.get('geo_query_sig','x')}"
        )

        if choice:
            idx = labels.index(choice)
            loc = results[idx]

            ss["lat"] = float(loc.get("latitude"))
            ss["lon"] = float(loc.get("longitude"))
            ss["place_label"] = choice

            st.success(
                f"📍 Selected: **{choice}**  "
                f"(lat {ss['lat']:.3f}, lon {ss['lon']:.3f})"
            )

    else:
        st.info("Enter a city name and press **Search city** to begin.")

 
# ======================================================================
# BLOCK 4 — RETRIEVE WEATHER & POPULATE ENVIRONMENTAL INPUTS (MOBILE SAFE)
# ======================================================================

st.markdown("## 🌡 Environmental Inputs")

# -----------------------------------------
# Retrieve live weather
# -----------------------------------------
fetch_btn = st.button("🌤 Retrieve Weather (Open-Meteo)")

if fetch_btn:
    lat = ss.get("lat", None)
    lon = ss.get("lon", None)

    if lat is None or lon is None:
        st.error("❗ Select a location first (use City Search above).")
    else:
        try:
            url = (
                "https://api.open-meteo.com/v1/forecast?"
                f"latitude={lat}&longitude={lon}"
                "&current=temperature_2m,relative_humidity_2m,wind_speed_10m"
                "&wind_speed_unit=ms"
                "&pressure_unit=hpa"
            )
            data = requests.get(url, timeout=8).json()
            current = data.get("current", {})
        except Exception:
            current = {}

        # Extract values (temperature °C; wind forced to m/s via wind_speed_unit=ms)
        temp_c = float(current.get("temperature_2m", ss.get("db_c", 30.0)))
        rh_pct = float(current.get("relative_humidity_2m", ss.get("rh_pct", 50.0)))
        ws_ms  = float(current.get("wind_speed_10m", ss.get("ws_ms", 1.0)))

        # Pressure not provided reliably → use standard
        p_kpa  = 101.3

        # Write into canonical session variables
        ss["db_c"]   = temp_c
        ss["rh_pct"] = rh_pct
        ss["ws_ms"]  = ws_ms
        ss["p_kpa"]  = p_kpa
        ss["gt_c"]   = temp_c + 3.0   # auto-estimate GT

        # Flag environment changed → forces baseline reset in Block 5
        ss["env_dirty"] = True

        st.success(
            f"Weather loaded from Open-Meteo ({datetime.utcnow().strftime('%H:%M UTC')})"
        )

# -----------------------------------------
# Manual input fields (unit aware)
# -----------------------------------------
col1, col2, col3, col4, col5 = st.columns(5)

# --- Dry bulb ---
with col1:
    if ss["units"] == "metric":
        ss["db_c"] = st.number_input("Dry Bulb (°C)", value=float(ss.get("db_c", 30.0)))
    else:
        db_f = st.number_input("Dry Bulb (°F)", value=float(c_to_f(ss.get("db_c", 30.0))))
        ss["db_c"] = f_to_c(db_f)

# --- RH ---
with col2:
    ss["rh_pct"] = st.number_input(
        "RH (%)", value=float(ss.get("rh_pct", 50.0)), min_value=0.0, max_value=100.0
    )

# --- Wind ---
with col3:
    if ss["units"] == "metric":
        ss["ws_ms"] = st.number_input("Wind (m/s)", value=float(ss.get("ws_ms", 1.0)))
    else:
        ws_mph = st.number_input("Wind (mph)", value=float(ms_to_mph(ss.get("ws_ms", 1.0))))
        ss["ws_ms"] = mph_to_ms(ws_mph)

# --- Pressure ---
with col4:
    if ss["units"] == "metric":
        ss["p_kpa"] = st.number_input("Pressure (kPa)", value=float(ss.get("p_kpa", 101.3)))
    else:
        p_inhg = st.number_input("Pressure (inHg)", value=float(kpa_to_inhg(ss.get("p_kpa", 101.3))))
        ss["p_kpa"] = inhg_to_kpa(p_inhg)

# --- Globe temperature ---
with col5:
    if ss["units"] == "metric":
        ss["gt_c"] = st.number_input("Globe Temp (°C)", value=float(ss.get("gt_c", ss.get("db_c", 30.0) + 3.0)))
    else:
        gt_f = st.number_input("Globe Temp (°F)", value=float(c_to_f(ss.get("gt_c", ss.get("db_c", 30.0) + 3.0))))
        ss["gt_c"] = f_to_c(gt_f)

# -----------------------------
# Mark environment dirty ONLY if something actually changed
# -----------------------------
_prev_env = ss.get("_prev_env_inputs_block4", None)

_env_now = (
    round(float(ss["db_c"]), 3),
    round(float(ss["rh_pct"]), 3),
    round(float(ss["ws_ms"]), 3),
    round(float(ss["p_kpa"]), 3),
    round(float(ss["gt_c"]), 3),
    ss.get("units", "metric")
)

# If first run, store and do NOT force reset
if _prev_env is None:
    ss["_prev_env_inputs_block4"] = _env_now
else:
    if _env_now != _prev_env:
        ss["env_dirty"] = True
        ss["_prev_env_inputs_block4"] = _env_now
    else:
        # leave env_dirty as-is (Block 5 will clear it after handling)
        ss["env_dirty"] = bool(ss.get("env_dirty", False))

st.markdown(
    "<span style='color:#444;'>If you entered weather manually, adjust Globe Temperature to reflect Sun and radiant load.</span>",
    unsafe_allow_html=True
)

# ======================================================================
# BLOCK 5 — COMPUTE NATURAL WET-BULB + WBGT BASELINE (with frozen baseline)
# ======================================================================

with st.expander("🧮 Baseline WBGT Calculation (Before exposure adjustments)", expanded=False):

    # Pull current internal values (always in °C internally)
    db_c  = float(ss["db_c"])
    rh    = float(ss["rh_pct"])
    ws_ms = float(ss["ws_ms"])
    gt_c  = float(ss["gt_c"])
    p_kpa = float(ss["p_kpa"])

    # ---------------------------------------------------------------
    # RESET frozen baseline when core environmental inputs change
    # (and clear any previously applied penalties)
    # ---------------------------------------------------------------
    if "prev_env" not in ss:
        ss["prev_env"] = {}

    # round to prevent float noise triggering resets
    env_now = {
        "db": round(db_c, 3),
        "rh": round(rh, 3),
        "gt": round(gt_c, 3),
        "ws": round(ws_ms, 3),
        "p":  round(p_kpa, 3),
    }

    # Optional “dirty” flag support (from Block 4)
    env_dirty = bool(ss.get("env_dirty", False))

    if env_dirty or (ss["prev_env"] != env_now):
        ss["wbgt_base_frozen"] = None
        ss["penalties_applied"] = False
        ss["total_penalty_c"] = 0.0
        ss["wbgt_eff_c"] = None
        ss["prev_env"] = env_now
        ss["env_dirty"] = False  # clear after reset

    # ---------------------------------------------------------------
    # Natural Wet-Bulb (Stull)
    # ---------------------------------------------------------------
    twb_c = (
        db_c * math.atan(0.151977 * math.sqrt(rh + 8.313659))
        + math.atan(db_c + rh)
        - math.atan(rh - 1.676331)
        + 0.00391838 * (rh ** 1.5) * math.atan(0.023101 * rh)
        - 4.686035
    )
    ss["twb_c"] = twb_c

    # ---------------------------------------------------------------
    # Wind-corrected Globe Temperature (ISO-7243 style damping)
    # (If you don’t want wind correction, set gt_adj = gt_c)
    # ---------------------------------------------------------------
    v = max(ws_ms, 0.1)  # avoid divide-by-zero
    f_v = 1.0 / (1.0 + 0.4 * math.sqrt(v))
    gt_adj = db_c + (gt_c - db_c) * f_v
    ss["gt_adj_c"] = gt_adj

    # ---------------------------------------------------------------
    # WBGT outdoor ISO (use gt_adj here)
    # ---------------------------------------------------------------
    wbgt_raw_c = 0.7 * twb_c + 0.2 * gt_adj + 0.1 * db_c
    ss["wbgt_raw_c"] = wbgt_raw_c
    ss["wbgt_base_c"] = wbgt_raw_c

    # Freeze baseline once per stable environment
    if ss.get("wbgt_base_frozen") is None:
        ss["wbgt_base_frozen"] = wbgt_raw_c

    # If penalties are NOT applied, keep effective tied to frozen baseline
    if not ss.get("penalties_applied", False):
        ss["wbgt_eff_c"] = ss["wbgt_base_frozen"]

    # ---------------------------------------------------------------
    # Display baseline metrics
    # ---------------------------------------------------------------
    st.subheader("Computed Baseline (No exposure adjustments applied)")
    c1, c2, c3 = st.columns(3)
    c1.metric("Natural Wet-Bulb", fmt_temp(twb_c, ss["units"]))
    c2.metric("WBGT Baseline (Frozen)", fmt_temp(ss["wbgt_base_frozen"], ss["units"]))
    c3.metric(
        "Wind",
        f"{ws_ms:.1f} m/s" if ss["units"] == "metric" else f"{ms_to_mph(ws_ms):.1f} mph"
    )

# ======================================================================
# BLOCK 5A — Instrument Reference (Calibration Mode)
# (Used ONLY for HSP calibration; does NOT change WBGT baseline logic)
# ======================================================================

st.markdown(
    "<span style='color:#444;'>Optional: Enter instrument values to display Heat Strain Profile (HSP). These values do NOT affect WBGT baseline or exposure adjustments.</span>",
    unsafe_allow_html=True
)

colA, colB = st.columns(2)

with colA:
    ss["twl_measured"] = st.number_input(
        "Instrument TWL (W/m²)",
        min_value=0.0,
        value=float(ss.get("twl_measured", 0.0)),
        step=5.0
    )

with colB:
    ss["wbgt_instr"] = st.number_input(
        "Instrument WBGT (°C)",
        min_value=0.0,
        value=float(ss.get("wbgt_instr", 0.0)),
        step=0.1
    )

# Flag if calibration is available (for Block 7 HSP display)
ss["hsp_calib_ready"] = bool(ss.get("twl_measured", 0.0) > 0 and ss.get("wbgt_instr", 0.0) > 0)

# ======================================================================
# Exposure adjustments (°C internal truth)
# ======================================================================

PPE_PRESETS     = {"None": 0.0, "Light": 1.0, "Moderate": 2.0, "Heavy": 3.0}
VEHICLE_PRESETS = {"None": 0.0, "Open": 1.0, "Enclosed": 2.0, "Poorly ventilated": 3.0}
RADIANT_PRESETS = {"None": 0.0, "Hot surfaces": 2.0, "Direct radiant": 4.0, "Extreme radiant": 5.0}
ADHOC_PRESETS   = {"None": 0.0, "Minor": 1.0, "Moderate": 2.0, "Severe": 4.0}

st.markdown("## 🔥 Exposure adjustments")

def delta_label(dc: float) -> str:
    return f"{dc:.1f}°C" if ss["units"] == "metric" else f"{dc * 9/5:.1f}°F"

def _ensure_number_follows_preset(preset_key: str, input_key: str, preset_c: float):
    """
    Streamlit widget keys 'remember' their values.
    So: when preset changes, force-reset the number_input state.
    """
    prev = ss.get(preset_key + "__prev", None)
    if prev != ss.get(preset_key, None):
        ss[input_key] = float(preset_c) if ss["units"] == "metric" else float(preset_c * 9/5)
        ss[preset_key + "__prev"] = ss.get(preset_key, None)

def number_delta(input_key: str) -> float:
    """
    Reads the number_input in display units, returns internal °C.
    """
    if ss["units"] == "metric":
        dc = st.number_input("", step=0.1, key=input_key)
        return float(dc)
    else:
        df = st.number_input("", step=0.1, key=input_key)
        return float(df) * 5/9

col1, col2, col3, col4 = st.columns(4)

# ---------------- PPE ----------------
with col1:
    st.subheader("Clothing / PPE")
    labels = {f"{k} (+{delta_label(v)})": float(v) for k, v in PPE_PRESETS.items()}
    choice = st.selectbox("", list(labels.keys()), key="ppe_preset")
    preset_c = float(labels[choice])
    _ensure_number_follows_preset("ppe_preset", "ppe_delta_input", preset_c)
    ss["pen_clo_c"] = number_delta("ppe_delta_input")

# ---------------- Vehicle ----------------
with col2:
    st.subheader("Vehicle / Enclosure")
    labels = {f"{k} (+{delta_label(v)})": float(v) for k, v in VEHICLE_PRESETS.items()}
    choice = st.selectbox("", list(labels.keys()), key="veh_preset")
    preset_c = float(labels[choice])
    _ensure_number_follows_preset("veh_preset", "veh_delta_input", preset_c)
    ss["pen_veh_c"] = number_delta("veh_delta_input")

# ---------------- Radiant ----------------
with col3:
    st.subheader("Radiant / Hot Surfaces")
    labels = {f"{k} (+{delta_label(v)})": float(v) for k, v in RADIANT_PRESETS.items()}
    choice = st.selectbox("", list(labels.keys()), key="rad_preset")
    preset_c = float(labels[choice])
    _ensure_number_follows_preset("rad_preset", "rad_delta_input", preset_c)
    ss["pen_rad_c"] = number_delta("rad_delta_input")

# ---------------- Adhoc ----------------
with col4:
    st.subheader("Ad-hoc / Site-specific")
    labels = {f"{k} (+{delta_label(v)})": float(v) for k, v in ADHOC_PRESETS.items()}
    choice = st.selectbox("", list(labels.keys()), key="adhoc_preset")
    preset_c = float(labels[choice])
    _ensure_number_follows_preset("adhoc_preset", "adhoc_delta_input", preset_c)
    ss["pen_adhoc_c"] = number_delta("adhoc_delta_input")

# ======================================================================
# BLOCK 5B — APPLY PENALTIES SAFELY (unit-aware, clamped, no negatives)
# ======================================================================

st.markdown("## 🚀 Apply Exposure Adjustments & Compute Effective WBGT")

if st.button("Apply Adjustments & Compute"):

    wbgt_base_c = ss.get("wbgt_base_frozen", None)  # use frozen baseline

    if wbgt_base_c is None:
        st.error("No frozen baseline WBGT available — set environmental inputs first.")
    else:
        # Values coming from UI are stored internally in °C
        ppe_c  = float(ss.get("pen_clo_c", 0.0))
        encl_c = float(ss.get("pen_veh_c", 0.0))
        rad_c  = float(ss.get("pen_rad_c", 0.0))
        ahoc_c = float(ss.get("pen_adhoc_c", 0.0))

        # Safety clamps per category
        ppe_c  = min(max(ppe_c,  0.0), 3.0)
        encl_c = min(max(encl_c, 0.0), 3.0)
        rad_c  = min(max(rad_c,  0.0), 5.0)
        ahoc_c = min(max(ahoc_c, 0.0), 4.0)

        # Total penalty (°C), global cap
        total_penalty_c = ppe_c + encl_c + rad_c + ahoc_c
        total_penalty_c = min(total_penalty_c, 10.0)

        # Effective WBGT (°C)
        wbgt_eff_c = float(wbgt_base_c) + float(total_penalty_c)

        # Persist results
        ss["total_penalty_c"] = total_penalty_c
        ss["wbgt_eff_c"] = wbgt_eff_c
        ss["penalties_applied"] = True

        # ------------------------------------------------------------
        # CRITICAL: log-safe compute trigger (runs only on click)
        # ------------------------------------------------------------
        ss["compute_counter"] = ss.get("compute_counter", 0) + 1
        ss["last_compute_ts"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # ------------------------------------------------------------
        # Unit-aware formatting (match the snapshot cards via ss["units"])
        # ------------------------------------------------------------
        if ss.get("units", "metric") == "imperial":
            penalty_str = f"+{(total_penalty_c * 9/5):.1f} °F"
            wbgt_display = f"{(wbgt_eff_c * 9/5 + 32):.1f} °F"
        else:
            penalty_str = f"+{total_penalty_c:.1f} °C"
            wbgt_display = f"{wbgt_eff_c:.1f} °C"

        # ------------------------------------------------------------
        # Display success message
        # ------------------------------------------------------------
        st.success(
            f"Exposure Adjustments Applied ({penalty_str}) → "
            f"Effective WBGT = {wbgt_display}. "
            "Scroll down for Heat-Stress Classification."
        )


# ======================================================================
# BLOCK 6 — NIOSH / OSHA WBGT & Wet-Bulb Thresholds (with Acclimatization)
# ======================================================================

with st.expander("🎯 Heat-Stress Thresholds (NIOSH / OSHA Reference)", expanded=False):

    # Worker acclimatization toggle
    accl_status = st.radio(
        "Worker acclimatization status",
        ["Acclimatized", "Not acclimatized"],
        horizontal=True,
        key="accl_status",
    )

    # ---------------------------
    # WBGT base cut-points (°C)
    # ---------------------------
    A_base = 29.0   # Info
    B_base = 32.0   # Caution
    C_base = 35.0   # Withdrawal

    # Non-acclimatized shift
    if accl_status == "Acclimatized":
        A, B, C = A_base, B_base, C_base
        wb_shift = 0.0
    else:
        A, B, C = A_base - 2.0, B_base - 2.0, C_base - 2.0
        wb_shift = -2.0

    # ---------------------------
    # Store WBGT thresholds
    # ---------------------------
    ss["wbgt_A_c"] = A
    ss["wbgt_B_c"] = B
    ss["wbgt_C_c"] = C

    # Legacy keys (used by Block-7 color logic)
    ss["thr_A_c"] = A
    ss["thr_B_c"] = B
    ss["thr_C_c"] = C

    # ---------------------------
    # Wet-Bulb physiological bands
    # (used by MWL + HSP ceiling logic)
    # ---------------------------
    # These come from industrial heat-strain literature
    ss["wb_safe_c"]     = 26.0 + wb_shift   # sweat effective
    ss["wb_strain_c"]   = 28.0 + wb_shift   # rising strain
    ss["wb_danger_c"]   = 30.0 + wb_shift   # evaporation ceiling

    # ---------------------------
    # Display
    # ---------------------------
    colA, colB, colC = st.columns(3)
    with colA:
        st.metric("WBGT Info (A)", fmt_temp(A, ss["units"]))
    with colB:
        st.metric("WBGT Caution (B)", fmt_temp(B, ss["units"]))
    with colC:
        st.metric("WBGT Withdrawal (C)", fmt_temp(C, ss["units"]))

    st.markdown("**Wet-Bulb Physiological Limits**")
    colW1, colW2, colW3 = st.columns(3)
    with colW1:
        st.metric("WB – Sweat Evaporation Effective", fmt_temp(ss["wb_safe_c"], ss["units"]))
    with colW2:
        st.metric("WB – Rising Strain", fmt_temp(ss["wb_strain_c"], ss["units"]))
    with colW3:
        st.metric("WB – Evaporation Ceiling", fmt_temp(ss["wb_danger_c"], ss["units"]))

    if accl_status == "Acclimatized":
        st.caption(
            "Values approximate **NIOSH/OSHA WBGT guidance** and **Physiological Wet-bulb limits** "
            "for acclimatized industrial workers."
        )
    else:
        st.caption(
            "All WBGT and Wet-Bulb thresholds are shifted lower for **Non-Acclimatized** workers "
            "to provide a conservative safety margin."
        )
# ======================================================================
# BLOCK 7 — HEAT STRESS RISK CLASSIFICATION (WBGT policy + HSP + Wet-Bulb)
# Single-screen compact dashboard
# FIX (Feb 2026):
# - KPI cards render FIRST (phone users see readings first)
# - Sticky bar is COMPACT and NOT misleading (no emergency line)
# - Sticky bar renders AFTER final_risk is computed (no NameError)
# - All emojis are inside strings (prevents U+1F7E2 invalid character errors)
# ======================================================================

# ss session-state handle is defined once in Block 1
# ---------- Compact CSS (safe) ----------
st.markdown("""
<style>
/* tighten vertical whitespace */
div.block-container { padding-top: 1.05rem; padding-bottom: 1.15rem; }
[data-testid="stVerticalBlock"] { gap: 0.55rem; }
[data-testid="stMarkdownContainer"] p { margin-bottom: 0.35rem; }

/* =========================
   STICKY ACTION BAR (COMPACT, NOT MISLEADING)
   ========================= */
.sticky-actions{
  position: sticky;
  top: 0.20rem;
  z-index: 999999;
  padding: 0.30rem 0.55rem;        /* reduced height */
  border-radius: 14px;
  background: linear-gradient(90deg, rgba(16,78,140,1.0), rgba(34,130,190,1.0)) !important;
  border: 1px solid rgba(255,255,255,0.18);
  box-shadow: 0 6px 18px rgba(0,0,0,0.18);
  overflow: hidden;
}

.sticky-row{
  display:flex;
  gap:10px;
  align-items:center;
  flex-wrap:wrap;
}

/* "Current risk" pill */
.current-pill{
  padding: 7px 11px;
  border-radius: 999px;
  background: rgba(255,255,255,0.16);
  border: 1px solid rgba(255,255,255,0.22);
  color: rgba(255,255,255,0.96);
  font-weight: 900;
  font-size: 0.90rem;
  user-select: none;
  white-space: nowrap;
}

/* Observe / Prevent / Manage pills */
.fake-btn{
  padding: 7px 11px;
  border-radius: 999px;
  background: rgba(255,255,255,0.12);
  border: 1px solid rgba(255,255,255,0.20);
  color: rgba(255,255,255,0.92);
  font-weight: 850;
  font-size: 0.88rem;
  user-select: none;
  letter-spacing: 0.2px;
}

@media (max-width: 900px){
  .sticky-actions{ top: 0.12rem; }
  .sticky-row{ gap: 8px; }
  .current-pill{ font-size: 0.88rem; padding: 6px 10px; }
  .fake-btn{ font-size: 0.86rem; padding: 6px 10px; }
}

/* KPI cards */
.kpi-grid{ display:grid; grid-template-columns: 1fr 1fr 1fr; gap:0.6rem; }
@media (max-width: 1100px){ .kpi-grid{ grid-template-columns: 1fr; } }

.kpi-card{
  padding: 10px;
  border-radius: 12px;
  background:#ffffff;
  border: 1px solid rgba(0,0,0,0.06);
}
.kpi-label{ font-size:0.86rem; color:#4a4a4a; margin-bottom:2px; }
.kpi-value{ font-size:1.55rem; font-weight:850; line-height:1.05; color:#0b2239; }
.kpi-sub{ margin-top:6px; font-size:0.93rem; line-height:1.15; color:#222; }
.kpi-foot{ margin-top:6px; font-size:0.90rem; color:#555; line-height:1.25; }

/* Risk pills */
.pill{
  display:inline-block;
  padding:0.18rem 0.55rem;
  border-radius:999px;
  font-size:0.78rem;
  font-weight:850;
  border:1px solid rgba(0,0,0,0.10);
}
.pill-amber{ background: rgba(255,170,0,0.14); }
.pill-red{ background: rgba(255,0,0,0.12); }
.pill-withdrawal{ background: rgba(142,0,0,0.14); border-color: rgba(142,0,0,0.25); color:#5a0000; }

/* Supervisor Actions grid (compact, phone friendly) */
.sa-grid{
  display:grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.6rem;
}
@media (max-width: 900px){
  .sa-grid{ grid-template-columns: 1fr; }
}
.sa-card{
  padding: 10px;
  border-radius: 12px;
  background:#ffffff;
  border: 1px solid rgba(0,0,0,0.06);
}
.sa-title{
  font-weight: 900;
  font-size: 0.98rem;
  margin-bottom: 6px;
  color: #0b2239;
}
.sa-card ul{
  margin: 0.25rem 0 0 1.15rem;
}
.sa-card li{
  margin-bottom: 0.25rem;
  line-height: 1.25;
}
</style>
""", unsafe_allow_html=True)

st.markdown("## 🧭 Heat-Stress Snapshot (WBGT Policy + HSP + Wet-Bulb)")

# -----------------------------
# WBGT policy banding (4-level)
# -----------------------------
def _wbgt_band_from_eff(wbgt_eff_c, A, B, C):
    if wbgt_eff_c < A:
        return ("🟢", "LOW RISK", "Routine/Normal work acceptable. Maintain hydration and routine supervision.", 0, "#2ecc71")
    if wbgt_eff_c < B:
        return ("🟠", "CAUTION", "Increase supervision. Enforce hydration and basic work–rest cycles.", 1, "#f39c12")
    if wbgt_eff_c < C:
        return ("🔴", "HIGH STRAIN", "Reduce exposure; Move to cooler/shaded areas; Use ventilation/A/C; Enforce short work–rest cycles.", 2, "#e74c3c")
    return ("⛔", "WITHDRAWAL", "Stop routine work. Only essential tasks with strict limits and close monitoring.", 3, "#8e0000")

wbgt_eff = ss.get("wbgt_eff_c", None)
wbgt_base = ss.get("wbgt_base_frozen", None)

if wbgt_eff is None:
    st.info("Press **Apply Adjustments & Compute** to calculate Effective WBGT, HSP, and guidance.")
    st.stop()

A = float(ss.get("thr_A_c", 29))
B = float(ss.get("thr_B_c", 32))
C = float(ss.get("thr_C_c", 35))

icon, wbgt_policy_band, wbgt_policy_msg, wbgt_policy_sev, band_color = _wbgt_band_from_eff(float(wbgt_eff), A, B, C)

# Keep legacy session keys if other blocks expect them
ss["risk_band"] = wbgt_policy_band
ss["wbgt_sev"] = wbgt_policy_sev

# -----------------------------
# Wet-bulb lookup + thresholds
# -----------------------------
def _get_wb_info_c():
    for k in ("twb_c", "wb_interp_c", "wb_c", "wb_calc_c", "wb_derived_c", "wetbulb_c"):
        v = ss.get(k, None)
        if v is None:
            continue
        try:
            return float(v)
        except Exception:
            pass
    return None

wb_info_c = _get_wb_info_c()
pen_c = float(ss.get("total_penalty_c", 0.0))

wb_safe_c   = float(ss.get("wb_safe_c", 26.0))
wb_strain_c = float(ss.get("wb_strain_c", 28.0))
wb_danger_c = float(ss.get("wb_danger_c", 30.0))

units_mode = ss.get("units", "metric")

def _c_to_f(x):
    return (x * 9/5 + 32)

if units_mode == "imperial":
    wbgt_disp = f"{_c_to_f(float(wbgt_eff)):.1f} °F"
    pen_disp  = f"+{(pen_c * 9/5):.1f} °F"  # delta °C → delta °F
    wb_disp   = f"{_c_to_f(wb_info_c):.1f} °F" if wb_info_c is not None else "—"
    wb1 = f"{_c_to_f(wb_safe_c):.0f} °F"
    wb2 = f"{_c_to_f(wb_strain_c):.0f} °F"
    wb3 = f"{_c_to_f(wb_danger_c):.0f} °F"
else:
    wbgt_disp = f"{float(wbgt_eff):.1f} °C"
    pen_disp  = f"+{pen_c:.1f} °C"
    wb_disp   = f"{wb_info_c:.1f} °C" if wb_info_c is not None else "—"
    wb1 = f"{wb_safe_c:.0f} °C"
    wb2 = f"{wb_strain_c:.0f} °C"
    wb3 = f"{wb_danger_c:.0f} °C"

# -----------------------------
# Wet-Bulb Cooling Bands (4-level)
# -----------------------------
wb_phys_msg = "Wet-bulb not available"
wb_phys_color = "#666"
wb_phys_icon = "⚪"

if wb_info_c is not None:
    if wb_info_c < wb_safe_c:
        wb_phys_icon, wb_phys_msg, wb_phys_color = "🟢", "Cooling Effective", "#2ecc71"
    elif wb_info_c < wb_strain_c:
        wb_phys_icon, wb_phys_msg, wb_phys_color = "🟡", "Cooling Starting to Limit", "#f1c40f"
    elif wb_info_c < wb_danger_c:
        wb_phys_icon, wb_phys_msg, wb_phys_color = "🟠", "Cooling Limited", "#f39c12"
    else:
        wb_phys_icon, wb_phys_msg, wb_phys_color = "🔴", "Cooling Compromised", "#e74c3c"

# -----------------------------
# HSP (Cooling Capacity)
# -----------------------------
hsp = None
h_icon = "⚪"
h_band = "HSP not available"
h_color = "#666"

db = float(ss.get("db_c", 0) or 0)
rh = float(ss.get("rh_pct", 0) or 0)
ws = float(ss.get("ws_ms", 0) or 0)
gt = float(ss.get("gt_c", 0) or 0)

wbgt_env = None if wbgt_base is None else float(wbgt_base)
wbgt_op  = float(wbgt_eff)

mwl_env = None
mwl_op = None
mwl_source = "—"
mwl_cap = None

if wbgt_env is not None:
    inst_cap = float(ss.get("twl_measured", 0) or 0)
    if inst_cap > 0:
        mwl_raw = inst_cap
        mwl_source = "Instrument capacity input"
    else:
        mwl_raw = float(estimate_mwl_wm2(db_c=db, rh_pct=rh, ws_ms=ws, gt_c=gt, wbgt_c=wbgt_env))
        mwl_source = "Model"

    if gt >= 50 and ws < 0.5:
        mwl_cap = 115
    elif gt >= 45:
        mwl_cap = 140
    elif wbgt_env >= 33:
        mwl_cap = 170
    elif wbgt_env >= 30:
        mwl_cap = 220
    else:
        mwl_cap = 280

    env_sig = (round(db,2), round(rh,2), round(ws,2), round(gt,2), round(wbgt_env,2), round(pen_c,2))
    if ss.get("mwl_env_sig") != env_sig:
        ss["mwl_env_sig"] = env_sig
        ss.pop("mwl_env_prev", None)

    prev_mwl = float(ss.get("mwl_env_prev", 9999.0))
    mwl_env = min(float(mwl_raw), float(mwl_cap), float(prev_mwl))
    ss["mwl_env_prev"] = mwl_env

    mwl_op = float(apply_capacity_penalties(
        mwl_env,
        ppe_c=float(ss.get("pen_clo_c", 0) or 0),
        veh_c=float(ss.get("pen_veh_c", 0) or 0),
        rad_c=float(ss.get("pen_rad_c", 0) or 0),
        adh_c=float(ss.get("pen_adhoc_c", 0) or 0),
    ))

    hsp = (wbgt_op * 200.0) / (max(1.0, mwl_op) * 30.0)
    ss["hsp"] = hsp

    if hsp < 0.8:
        h_icon, h_band, h_color = "🟢", "Cooling Exceeds Heat Load", "#2ecc71"
    elif hsp < 1.0:
        h_icon, h_band, h_color = "🟠", "Heat Balance Marginal", "#f39c12"
    else:
        h_icon, h_band, h_color = "🔴", "Heat Gain Likely Exceeds Cooling Capacity", "#e74c3c"

# -----------------------------
# Override logic (conservative): policy first; HSP only if more protective
# -----------------------------
use_phys = st.checkbox(
    "Use HSP only when it is more protective than WBGT policy",
    value=True,
    key="use_phys_override_block7"
)

if wbgt_policy_sev >= 3:
    final_risk = "WITHDRAWAL"
elif wbgt_policy_sev == 2:
    final_risk = "HIGH STRAIN"
elif wbgt_policy_sev == 1:
    final_risk = "CAUTION"
else:
    final_risk = "LOW"

if use_phys and (hsp is not None):
    if hsp >= 1.30:
        final_risk = "WITHDRAWAL"
    elif hsp >= 1.00 and final_risk in ["LOW", "CAUTION"]:
        final_risk = "HIGH STRAIN"
    elif 0.80 <= hsp < 1.00 and final_risk == "LOW":
        final_risk = "CAUTION"

ss["final_risk"] = final_risk

# -----------------------------
# KPI pills
# -----------------------------
if wbgt_policy_sev <= 0:
    pill = ""
elif wbgt_policy_sev == 1:
    pill = '<span class="pill pill-amber">CAUTION</span>'
elif wbgt_policy_sev == 2:
    pill = '<span class="pill pill-red">HIGH STRAIN</span>'
else:
    pill = '<span class="pill pill-withdrawal">WITHDRAWAL</span>'

hsp_value_disp = f"{hsp:.2f}" if hsp is not None else "—"
hsp_sub = f"{h_icon} {h_band}" if hsp is not None else "Baseline WBGT not available (HSP not computed)"
hsp_foot = f"Operational cooling capacity: {mwl_op:.0f} W/m² (source: {mwl_source})" if mwl_op is not None else "Provide baseline WBGT to enable HSP."

# -----------------------------
# KPI CARDS FIRST (phone: readings appear before sticky bar)
# -----------------------------
st.markdown(
f"""
<div class="kpi-grid">

  <div class="kpi-card" style="border-left:7px solid {band_color};">
    <div class="kpi-label">Effective WBGT (Policy)</div>
    <div class="kpi-value">{wbgt_disp}</div>
    <div class="kpi-sub">{icon} <b>{wbgt_policy_band}</b> {pill}</div>
    <div class="kpi-foot">{wbgt_policy_msg}<br>Exposure adjustments: <b>{pen_disp}</b></div>
  </div>

  <div class="kpi-card" style="border-left:7px solid {h_color};">
    <div class="kpi-label">Heat-Strain Profile (HSP)</div>
    <div class="kpi-value">{hsp_value_disp}</div>
    <div class="kpi-sub"><b>{hsp_sub}</b></div>
    <div class="kpi-foot">{hsp_foot}</div>
  </div>

  <div class="kpi-card" style="border-left:7px solid {wb_phys_color};">
    <div class="kpi-label">Wet-Bulb (Evaporation Capacity)</div>
    <div class="kpi-value">{wb_disp}</div>
    <div class="kpi-sub"><b>{wb_phys_icon} {wb_phys_msg}</b></div>
    <div class="kpi-foot">
      🟢 Cooling Effective (WB &lt; {wb1})<br>
      🟡 Cooling Starting to Limit ({wb1}–{wb2})<br>
      🟠 Cooling Limited ({wb2}–{wb3})<br>
      🔴 Cooling Compromised (≥ {wb3})
    </div>
  </div>

</div>
""",
unsafe_allow_html=True
)

# -----------------------------
# Sticky Supervisor Action Bar (COMPACT; NO emergency line)
# -----------------------------
risk_icon_map = {"LOW":"🟢","CAUTION":"🟠","HIGH STRAIN":"🔴","WITHDRAWAL":"⛔"}
risk_icon = risk_icon_map.get(final_risk, "⚪")
current_label = f"Current: {risk_icon} {final_risk} • {wbgt_disp}"

st.markdown(
    f'<div class="sticky-actions"><div class="sticky-row">'
    f'<div class="current-pill">{current_label}</div>'
    f'<div class="fake-btn">Observe / Care</div>'
    f'<div class="fake-btn">Prevent</div>'
    f'<div class="fake-btn">Manage</div>'
    f'</div></div>',
    unsafe_allow_html=True
)

# -----------------------------
# Consolidated risk summary
# -----------------------------
st.markdown("### 🧾 Risk Summary (Context-Relevant Significance)")

if final_risk == "LOW":
    r_icon, r_label, r_color = "🟢", "LOW (Routine Controls)", "#2ecc71"
elif final_risk == "CAUTION":
    r_icon, r_label, r_color = "🟠", "CAUTION (More Breaks and Monitoring)", "#f39c12"
elif final_risk == "HIGH STRAIN":
    r_icon, r_label, r_color = "🔴", "HIGH STRAIN (Active Controls Required)", "#e74c3c"
else:
    r_icon, r_label, r_color = "⛔", "WITHDRAWAL (Stop Routine Work)", "#8e0000"

hsp_show = f"{hsp:.2f}" if hsp is not None else "—"

st.markdown(
    f"""
<div style="padding:10px;border-radius:12px;background:#ffffff;border-left:7px solid {r_color};border:1px solid rgba(0,0,0,0.06);">
  <b style="font-size:16px;color:{r_color};line-height:1.15;">{r_icon} {r_label}</b><br>
  <span style="color:#222;">Effective WBGT: <b>{wbgt_disp}</b></span><br>
  <span style="color:#222;">HSP: <b>{hsp_show}</b></span><br>
  <span style="color:#666;font-size:0.92rem;line-height:1.15;">
    Use WBGT for policy alignment. Use HSP as a cooling-capacity cross-check when it is more protective.
  </span>
</div>
""",
    unsafe_allow_html=True
)

# -----------------------------
# Supervisor Actions — compact grid (phone friendly)
# -----------------------------
st.markdown("### 👷‍♂️ Supervisor Actions (Cooling Capacity & Process-Relevant)")

def _ul(items):
    return "<ul>" + "".join([f"<li>{x}</li>" for x in items]) + "</ul>"

if final_risk == "LOW":
    hydration_items = ["Encourage Regular Drinking (Cool Water)", "~250 mL Every 30 minutes", "Do Not Exceed ~1.5 L/hour"]
    workrest_items  = ["Continuous Self-paced Work acceptable", "Routine Breaks as per Site Practice"]
    cooling_items   = ["Shade Access and Airflow where possible"]
    monitor_items   = ["Routine Supervision; Remind Early Symptom Reporting"]

elif final_risk == "CAUTION":
    hydration_items = ["250 mL every 20–30 minutes", "If sweating heavily, 200 mL of hypotonic electrolytes every 4 hours", "Do not exceed ~1.5 L/hour"]
    workrest_items  = ["Planned Rest Breaks in Shade/Cool area", "Reduce Peak Workload; Encourage Self-pacing"]
    cooling_items   = ["Prioritize Shade + Airflow", "Cooling Towels if available"]
    monitor_items   = ["Active checks (Buddy System + Supervisor)", "Extra Attention to New/Returning workers"]

elif final_risk == "HIGH STRAIN":
    hydration_items = ["250–500 mL every 15–20 minutes (as tolerated)", "Electrolytes every 2 hours if sweating heavily", "Do not exceed ~1.5 L/hour"]
    workrest_items  = ["Short Work Bouts + Frequent Cooling Breaks", "Reduce Exposure Now; Defer Non-Urgent Tasks"]
    cooling_items   = ["Active Cooling: Fans and Wetting; Cooled Area / A/C Cabin"]
    monitor_items   = ["Close observation", "STOP WORK IMMEDIATELY If SYMPTOMS APPEAR"]

else:  # WITHDRAWAL
    hydration_items = ["Stop Routine Work; Move to Shade/Cool area", "Small Frequent Sips If Fully Alert", "Confused/Vomiting/Disoriented → No Oral Fluids; Call Site Medical"]
    workrest_items  = ["Only Essential Tasks with Strict Time Limits", "Rotate Staff; Keep Exposures Very Short"]
    cooling_items   = ["Immediate Active Cooling for Symptomatic Workers", "Escalate Quickly for Severe Signs"]
    monitor_items   = ["Continuous Observation", "Emergency Trigger: Confusion/Collapse/Seizure → Activate Response"]

st.markdown(
    f"""
<div class="sa-grid">
  <div class="sa-card"><div class="sa-title">Hydration</div>{_ul(hydration_items)}</div>
  <div class="sa-card"><div class="sa-title">Work–Rest</div>{_ul(workrest_items)}</div>
  <div class="sa-card"><div class="sa-title">Cooling</div>{_ul(cooling_items)}</div>
  <div class="sa-card"><div class="sa-title">Monitoring</div>{_ul(monitor_items)}</div>
</div>
""",
    unsafe_allow_html=True
)

with st.expander("ℹ️ HSP Details (Tap to Expand)", expanded=False):
    st.markdown("**HSP Field Guide**")
    st.markdown(
        """
- 🟢 **HSP < 0.80** → Cooling Exceeds Heat Load  
- 🟠 **0.80–0.99** → Heat Balance Marginal  
- 🔴 **HSP ≥ 1.00** → Heat Gain Likely Exceeds Heat Loss  
"""
    )
    if (mwl_env is not None) and (mwl_op is not None):
        st.markdown(
            f"""<div style="padding:10px;border-radius:10px;background:#ffffff;border:1px solid rgba(0,0,0,0.06);">
            Cooling capacity (environmental): <b>{mwl_env:.0f} W/m²</b><br>
            Cooling capacity (operational): <b>{mwl_op:.0f} W/m²</b><br>
            Source: <b>{mwl_source}</b> | Cap applied: <b>{mwl_cap:.0f} W/m²</b>
            </div>""",
            unsafe_allow_html=True
        )

with st.expander("🧑‍🏭 Worker Messages (Tap to Expand)", expanded=False):
    st.markdown("**English (simple)**")
    st.markdown(
        """
- Drink small amounts often (Do Not Wait for Thirst).
- Slow down (Self-Pace). Take Cooling Breaks in Shade when told — and Even Earlier if You feel unwell.
- Tell your supervisor immediately if you feel unwell, dizzy, weak, confused, or nauseated.
"""
    )
    st.markdown("**Local languages (Eg., Arabic / Hindi / Urdu / Spanish etc) — Planned For Future Versions**")
    st.info("Next Step: Adding Short, Field-Safe Translations for Key Messages.")

if ss.get("debug_mode", False):
    st.caption(
        f"DEBUG → wbgt_policy_sev={wbgt_policy_sev} | wbgt_eff_c={float(wbgt_eff):.2f} | "
        f"hsp={(hsp if hsp is not None else -1):.2f} | final_risk={final_risk}"
    )
# ======================================================================
# BLOCK 8 — AUDIT LOG & EXPORT
# ======================================================================

st.markdown("---")
st.markdown("## 📜 Heat-Stress Audit History (Saved Records)")

# Ensure audit log exists
if "audit_log" not in ss:
    ss["audit_log"] = []

# Monotonic save counter to avoid duplicate appends on Streamlit reruns
if "save_counter" not in ss:
    ss["save_counter"] = 0
if "last_saved_id" not in ss:
    ss["last_saved_id"] = -1

# Controls
colA, colB = st.columns([1.0, 1.0], vertical_alignment="center")
with colA:
    save_now = st.button(
        "💾 Save Record",
        type="primary",
        use_container_width=True,
        key="btn_save_record_block8",
    )
with colB:
    st.caption("Save stores the current computed decision. Compute does not create saved records.")

if save_now:
    ss["save_counter"] += 1

current_save_id = ss.get("save_counter", 0)

# Append ONLY when a new Save event happens (and we have computed values)
if (
    current_save_id != ss.get("last_saved_id", -1)
    and ss.get("wbgt_eff_c") is not None
):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    place = ss.get("place_label", "")

    # Inputs (stored internally as metric)
    db_c  = float(ss.get("db_c", 0.0) or 0.0)
    rh    = float(ss.get("rh_pct", 0.0) or 0.0)
    gt_c  = float(ss.get("gt_c", 0.0) or 0.0)
    ws_ms = float(ss.get("ws_ms", 0.0) or 0.0)

    # WBGT values
    wbgt_base_frozen = ss.get("wbgt_base_frozen", None)
    wbgt_eff_c = float(ss.get("wbgt_eff_c", 0.0) or 0.0)
    total_penalty_c = float(ss.get("total_penalty_c", 0.0) or 0.0)

    # HSP (as computed in Block 7)
    hsp_val = ss.get("hsp", None)

    # Final risk (prefer post-override)
    risk_final = ss.get("final_risk", ss.get("risk_band", ""))

    # Wet bulb if available (try common keys)
    wb_logged = None
    for k in ("twb_c", "wb_interp_c", "wb_c", "wb_calc_c", "wb_derived_c", "wetbulb_c"):
        v = ss.get(k)
        if v is not None:
            try:
                wb_logged = float(v)
                break
            except Exception:
                pass

    # Display-units for Effective WBGT in the saved record
    units_mode = ss.get("units", "metric")  # expected: "metric" or "imperial"
    if units_mode == "imperial":
        wbgt_eff_disp_val = (wbgt_eff_c * 9/5) + 32
        wbgt_eff_disp_unit = "°F"
    else:
        wbgt_eff_disp_val = wbgt_eff_c
        wbgt_eff_disp_unit = "°C"

    log_entry = {
        "timestamp": ts,
        "location": place,

        "DB (°C)": f"{db_c:.1f}",
        "RH (%)": f"{rh:.0f}",
        "GT (°C)": f"{gt_c:.1f}",
        "Wind (m/s)": f"{ws_ms:.2f}",

        "WB (°C)": f"{wb_logged:.1f}" if wb_logged is not None else "",

        "WBGT baseline frozen (°C)": f"{float(wbgt_base_frozen):.1f}" if wbgt_base_frozen is not None else "",
        "Exposure adjustment total (°C)": f"{total_penalty_c:.1f}",

        # Save both canonical and display-facing
        "Effective WBGT (°C)": f"{wbgt_eff_c:.1f}",
        f"Effective WBGT ({wbgt_eff_disp_unit})": f"{wbgt_eff_disp_val:.1f}",

        "HSP": f"{float(hsp_val):.2f}" if hsp_val is not None else "",
        "Final Risk": risk_final,
    }

    ss["audit_log"].append(log_entry)
    ss["last_saved_id"] = current_save_id
    st.success(f"Saved to Audit History. Effective WBGT: {wbgt_eff_disp_val:.1f} {wbgt_eff_disp_unit}")

# -----------------------------
# Audit Log Display & Export
# -----------------------------
has_log = bool(ss.get("audit_log"))

if has_log:
    df = pd.DataFrame(ss["audit_log"])
    st.dataframe(df, use_container_width=True)
    csv_data = df.to_csv(index=False).encode("utf-8")
else:
    st.info("No saved records yet. Press **Save Record** to store an entry.")
    csv_data = b""

st.info(
    "Export is optional. If you choose to export, select a folder and file name "
    "when prompted. After saving or cancelling, you will return to this assessment screen."
)

st.caption("Export saves a CSV file without leaving the assessment screen.")
st.download_button(
    label="📤 Export Audit Log (CSV)",
    data=csv_data,
    file_name=f"CHSRMT_Audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
    mime="text/csv",
    disabled=not has_log,
    key="btn_export_audit_block8",
)

# ======================================================================
# BLOCK 9 — APPENDIX & FIELD GUIDANCE (MASTER COLLAPSIBLE) + FOOTER SAFE
# ======================================================================

st.markdown("---")

with st.expander("📘 Guidance & Field Appendices", expanded=False):

    st.markdown("### Hydration, Acclimatization, Work–Rest & Warning Signs")

    # --------------------------------------------------
    # Hydration
    # --------------------------------------------------
    with st.expander("🥤 Hydration Guidance (General Field Advice)"):
        st.markdown("""
**Suggested quantities (moderate work)**  
- 250–500 mL every **20 minutes**  
- Avoid > 1.5 L/hour (risk of hyponatremia)  
- Include **electrolytes every 2–3 hours**

**Avoid**
- Alcohol before work  
- Excessive caffeine  
- Energy drinks as fluid replacement  

**Warning signs of dehydration**
- Thirst, dry mouth  
- Dark yellow urine  
- Headache, fatigue  
- Cramps
""")

    # --------------------------------------------------
    # Acclimatization
    # --------------------------------------------------
    with st.expander("⚡ Acclimatization — Practical Field Approach"):
        st.markdown("""
**How acclimatization should be viewed (modern approach)**

Acclimatization is **not a rigid schedule**, but a **period of reduced expectations**
that allows the worker’s body to adapt safely to heat.

• Productivity expectations should be **temporarily lowered**  
• **Rest breaks should be encouraged**, not penalized  
• **Self-pacing** should be allowed wherever feasible  

**Supervisory responsibilities during acclimatization**

Acclimatization is a period of **heightened vigilance**, requiring:

• Frequent or continuous observation by supervisors  
• Buddy systems, especially during the first few shifts  
• Periodic check-ins asking:
– “How are you feeling?”  
– “Can you continue safely?”  
– “Do you need a break or cooling?”  

**Higher-risk situations**
• New workers  
• Workers returning after ≥ 1 week absence  
• Workers recovering from illness  
• Sudden increases in heat, PPE, or workload  

**Key principle**
Acclimatization succeeds when **workers are protected, not pushed**.
""")

    # --------------------------------------------------
    # Work–Rest Prompts
    # --------------------------------------------------
    with st.expander("⏱ Work–Rest / Supervision Prompts"):
        st.markdown("""
These prompts support **field supervisors** and do not replace policy.

**Green Zone**
- Routine work  
- Encourage fluids  
- Normal supervision  

**Amber Zone**
- Enforce breaks  
- Actively monitor symptoms  
- Provide shade  

**Red / Withdrawal Zone**
- Stop routine work  
- Only emergency tasks with medical oversight  
- Mandatory cooling interventions
""")

    # --------------------------------------------------
    # Early Warning Signs
    # --------------------------------------------------
    with st.expander("🚩 Early Warning Signs & First-Aid Triggers"):
        st.markdown("""
*Clinical guidance reflects contemporary **NIOSH** and **ACGIH** interpretations of exertional heat illness
and heat stroke, emphasizing neurologic red-flag symptoms.*

**Red-flag symptoms requiring immediate action**
- Dizziness, collapse, faintness  
- Confusion or altered behavior  
- Vomiting  
- Staggering movement  

**Immediate steps**
- Move to shade/cooling  
- Apply cool water/packs to neck/axilla/groin  
- Provide fluids if conscious  
- Activate emergency medical support if no rapid improvement
""")

    # --------------------------------------------------
    # Medical Endpoints
    # --------------------------------------------------
    with st.expander("🏥 Common Medical End-points (for HSE orientation)"):
        st.markdown("""
**Heat Exhaustion**
- Sweating, nausea, rapid pulse  
- Elevated temperature but < 40°C (104°F)  
- Requires fluid replacement & monitoring  

**Heat Stroke**
- Core temperature ≥ 40°C (≥104°F)  
- CNS dysfunction (confusion, seizure, coma)  
- **Medical emergency — activate EMS**
""")

    st.markdown("---")
    st.caption(
        "This appendix provides field-support content only. It does NOT replace medical assessment, "
        "OSHA/NIOSH procedures, or employer HSE policy."
    )

st.markdown("<div style='height:72px;'></div>", unsafe_allow_html=True)
 
# ======================================================================
# FOOTER (COLLAPSIBLE) — OWNERSHIP + PUBLIC USE + FEEDBACK  [MOBILE SAFE]
# ======================================================================

st.markdown("---")

with st.expander("ℹ About CHSRMT • Disclaimer • Feedback", expanded=False):
    st.markdown(f"""
**© 2026 Dr. Gummanur T. Manjunath — CHSRMT® (Calibrated Heat Stress Risk Management Tool)**

Field Heat-Stress Decision Support System — Integrating **WBGT • MWL • HSP**  
*(Instrument TWL input supported where available)*

**Decision-Support Only:**  
This tool supports occupational heat-stress awareness and field screening.  
It does **not** replace site HSE policy, IH/OH judgement, medical evaluation, or regulatory compliance.  
No organization or professional society endorses this tool unless explicitly stated.

**Feedback & Field Validation:**  
https://forms.gle/7rfrXZXkyCdXqGVs5  

**Build:** `{APP_VERSION}`
""")

