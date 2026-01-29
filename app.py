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

APP_VERSION = "v2.0-WBGT-Field"

st.set_page_config(
    page_title="CHSRMT",
    layout="wide",
)

st.markdown("""
<style>
h1 {font-size: 1.45rem !important; margin-bottom: 0.3rem;}
h2 {font-size: 1.25rem !important; margin-bottom: 0.25rem;}
h3 {font-size: 1.05rem !important; margin-bottom: 0.2rem;}
div[data-testid="stMarkdownContainer"] p {margin-bottom: 0.15rem;}

.welcome-box {
    background: linear-gradient(90deg, #0f4c75, #3282b8);
    padding: 1rem;
    border-radius: 10px;
    color: white;
    margin-bottom: 0.55rem;
}
.welcome-box h2 {
    font-size: 1.35rem;
    margin-bottom: 0.2rem;
}
.welcome-box p {
    font-size: 0.9rem;
    opacity: 0.92;
}

.section-title {
    color: #1f6fb2;
    font-weight: 700;
    font-size: 1.12rem;
    margin-top: 0.45rem;
    margin-bottom: 0.12rem;
}
.section-sub {
    color: #5f7f9c;
    font-size: 0.90rem;
    margin-bottom: 0.2rem;
}
div.block-container {padding-top: 1rem; padding-bottom: 1rem;}
div[data-testid="stVerticalBlock"] {gap: 0.35rem;}
</style>
""", unsafe_allow_html=True)

ss = st.session_state

def subtle_divider():
    """Small visual separator between major result cards."""
    st.markdown(
        '<div style="border-top:1px solid rgba(0,0,0,0.10); margin:10px 0 12px 0;"></div>',
        unsafe_allow_html=True
    )

def result_header(label: str = "Results below correspond to the inputs entered above."):
    subtle_divider()
    st.caption(label)


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

def ss_default(key, val):
    if key not in ss:
        ss[key] = val

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
ss_default("MWL_A_wb", 12.0)     # wet-bulb adjustment weight
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
    # Tuned to avoid "berserk" values and to stay in a realistic 0–450 W/m² band.
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
    # Mild boost at very low RH, increasing penalty above ~60%.
    if rh_pct <= 20.0:
        rh_mod = 1.0 + 0.08 * (20.0 - rh_pct) / 20.0   # up to +8%
    elif rh_pct <= 60.0:
        rh_mod = 1.0 - 0.10 * (rh_pct - 20.0) / 40.0   # down to 0.90
    else:
        rh_mod = 0.90 - 0.35 * (rh_pct - 60.0) / 40.0  # down to 0.55 at RH 100
    rh_mod = max(0.55, min(1.08, rh_mod))

    # ── 5) Extra penalty when Wet Bulb is high (evaporation “ceiling”) ──
    # Use Stull-style approximation (sufficient for a penalty term).
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
    ss["wb_c"] = wb_c
    if wb_c > 25.0:
        wb_pen = 1.0 - 0.015 * (wb_c - 25.0)   # 30°C WB → ~0.925
        wb_pen = max(0.55, min(1.0, wb_pen))
    else:
        wb_pen = 1.0

    mwl = mwl_base * wind_mod * rad_mod * rh_mod * wb_pen

    # Final clamp (keep stable)
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

if not ss["landing_open"]:
    st.markdown("""
    <h2 style='margin-bottom:0.2rem;'>Calibrated Heat Stress Risk Management Tool (CHSRMT)</h2>
    <p style='margin-top:0; color: #555;'>
    Field-ready decision support for occupational heat stress and heat strain
    </p>
    """, unsafe_allow_html=True)
    
    st.markdown("---")

    st.markdown("""
    <div class="welcome-box">
        <h2>☀️ Field Heat-Stress Assessment Dashboard</h2>
        <p><b>WBGT</b> - Regulatory Guide For Env.Heat Hazard. <b>Heat Strain Profile(HSP)</b> - Human Cooling Ability -vs-Heat load By MWL (W/m²).</p>
        <p><b>Workflow:</b> Inputs → Baseline WBGT → Exposure Adjustments → Effective WBGT → HSP (before/after) → Guidance → Logging</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### What this tool does")
    st.markdown("""
• Computes WBGT baseline and Effective WBGT (after PPE/enclosure/radiant adjustments)  
• Estimates **MWL (Metabolic Work Load, W/m²)** when an instrument **TWL(Thermal Work Limits) reading** is not available  
• Computes **HSP** before and after exposure adjustments  to reflect **Human Cooling Margin**

### Definitions / Explanations

• **Heat stress**: external thermal load from the environment and work conditions  

• **Heat strain**: the body’s physiological response as it attempts to maintain thermal balance  

• **Wet-Bulb (WB)**: reflects evaporative potential and how effectively sweat can evaporate — a true physiological limit  

• **WBGT**: screening and regulatory heat-hazard index used for compliance and baseline decisions  

• **TWL (Thermal Work Limits)**: instrument-measured cooling capacity of the environment  

• **MWL (Metabolic Work Load, W/m²)**: modeled cooling capacity when TWL instrumentation is not available  
  – Higher MWL → longer sustainable work duration  
  – Lower MWL → shorter sustainable work duration  

• **HSP (Heat-Strain Profile)**: heat demand relative to human cooling capacity  
  – Lower HSP = safer  
  – Higher HSP = reduced ability to dissipate heat  

• **Acclimatization**: improves sweat-gland efficiency, cardiovascular stability, and overall heat tolerance


**HSP interpretation (Practical):**  
• 🟢 **HSP < 0.80** → Cooling exceeds heaload  
• 🟠 **0.80–0.99** → Heat balance marginal  
• 🔴 **HSP ≥ 1.00** → Heat gain exceeds heat loss  

• Provides supervisor guidance + audit logging  
""")

    st.warning("Decision-Support only. Does Not Replace Site HSE policy, IH judgement, or Medical Protocols.")

    if st.button("🚀 Start Heat-Stress Assessment"):
        ss["landing_open"] = True
        st.rerun()

    st.stop()

# ----------------------------
# Working page header
# ----------------------------
st.markdown("""
<h2 style='margin-bottom:0.2rem;'>Calibrated Heat Stress Risk Management Tool (CHSRMT)</h2>
<p style='margin-top:0; color: #555;'>
Field-ready decision support for occupational heat stress and heat strain
</p>
""", unsafe_allow_html=True)

st.markdown(
    "<span style='color:#444;'>Location → Weather → Baseline → Exposure adjustments → Effective WBGT → HSP (before/after) → Guidance → Logging</span>",
    unsafe_allow_html=True
)

# st.markdown("---")
# st.caption("Location → Weather → Baseline → Exposure adjustments → Effective WBGT → HSP (before/after) → Guidance → Logging")

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

Higher HSP = **Better Cooling Margin**.
""")

# -------------------------
# Reset assessment (main page, confirmed)
# -------------------------
st.markdown("---")
if st.button("🔄 Reset assessment (clear current inputs & results)"):
    ss["confirm_reset"] = True

if ss.get("confirm_reset", False):
    st.warning("Are you sure you want to reset the current assessment? Please save or export current results before resetting.")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("✅ Yes, reset now"):
            keys_to_clear = [
                # Location / weather
                "city_query","place_name","lat","lon","weather_fetched","weather_provider",
                # Environmental inputs
                "db_c","rh_pct","ws_ms","pressure_kpa","gt_c","twb_c","wb_c",
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
                "geo_results","geo_query_sig","place_query"
            ]
            for k in keys_to_clear:
                if k in ss:
                    del ss[k]
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

    st.caption("Change units from the main screen (mobile-safe).")

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
    st.write(f"🟢 Low Risk: < {fmt_temp(A, ss['band_units'])}")
    st.write(f"🟠 Caution: {fmt_temp(A, ss['band_units'])} – {fmt_temp(B, ss['band_units'])}")
    st.write(f"🔴 Withdrawal: ≥ {fmt_temp(C, ss['band_units'])}")

    st.markdown("---")
    
st.markdown("<div style='height:0.75rem;'></div>", unsafe_allow_html=True)
# ======================================================================
# BLOCK 3 — LOCATION SEARCH (OPEN-METEO GEOCODER)
# ======================================================================

with st.expander("📍 Location Search (City Lookup)", expanded=False):

    st.markdown("## 🛰 Location Search (City Lookup)")

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
            url = (
                "https://geocoding-api.open-meteo.com/v1/search?"
                f"name={place_query}&count=10&language=en&format=json"
            )
            resp = requests.get(url, timeout=8).json()
            results = resp.get("results", [])
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
                "&pressure_unit=hpa"
            )
            data = requests.get(url, timeout=8).json()
            current = data.get("current", {})
        except Exception:
            current = {}

        # Extract values (Open-Meteo always returns °C and m/s)
        temp_c = float(current.get("temperature_2m", ss["db_c"]))
        rh_pct = float(current.get("relative_humidity_2m", ss["rh_pct"]))
        ws_ms  = float(current.get("wind_speed_10m", ss["ws_ms"]))

        # Pressure not provided → use standard
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
        ss["db_c"] = st.number_input("Dry Bulb (°C)", value=float(ss["db_c"]))
    else:
        db_f = st.number_input("Dry Bulb (°F)", value=float(c_to_f(ss["db_c"])))
        ss["db_c"] = f_to_c(db_f)

# --- RH ---
with col2:
    ss["rh_pct"] = st.number_input(
        "RH (%)", value=float(ss["rh_pct"]), min_value=0.0, max_value=100.0
    )

# --- Wind ---
with col3:
    if ss["units"] == "metric":
        ss["ws_ms"] = st.number_input("Wind (m/s)", value=float(ss["ws_ms"]))
    else:
        ws_mph = st.number_input("Wind (mph)", value=float(ms_to_mph(ss["ws_ms"])))
        ss["ws_ms"] = mph_to_ms(ws_mph)

# --- Pressure ---
with col4:
    if ss["units"] == "metric":
        ss["p_kpa"] = st.number_input("Pressure (kPa)", value=float(ss["p_kpa"]))
    else:
        p_inhg = st.number_input("Pressure (inHg)", value=float(kpa_to_inhg(ss["p_kpa"])))
        ss["p_kpa"] = inhg_to_kpa(p_inhg)

# --- Globe temperature ---
with col5:
    if ss["units"] == "metric":
        ss["gt_c"] = st.number_input("Globe Temp (°C)", value=float(ss["gt_c"]))
    else:
        gt_f = st.number_input("Globe Temp (°F)", value=float(c_to_f(ss["gt_c"])))
        ss["gt_c"] = f_to_c(gt_f)

# Mark environment dirty if user edits anything
ss["env_dirty"] = True

st.markdown(
    "<span style='color:#444;'>If you entered weather manually, adjust Globe Temperature to reflect sun and radiant load.</span>",
    unsafe_allow_html=True
)

# st.caption(
  #  "If you entered weather manually, adjust Globe Temperature to reflect sun and radiant load."
# )
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

    env_now = {"db": db_c, "rh": rh, "gt": gt_c, "ws": ws_ms, "p": p_kpa}

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
    "<span style='color:#444;'>Optional: enter instrument values to display Heat Strain Profile (HSP). These values do NOT affect WBGT baseline or exposure adjustments.</span>",
    unsafe_allow_html=True
)

# st.markdown("### 📟 Instrument Reference (Calibration Mode)")
# st.caption(
  #  "Optional: enter instrument values to display Heat Strain Profile (HSP). "
   # "These values do NOT affect WBGT baseline or exposure adjustments."
# )

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

st.markdown("## 🚀 Apply exposure adjustments & compute Effective WBGT")

if st.button("Apply adjustments & compute"):

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

        total_penalty_c = ppe_c + encl_c + rad_c + ahoc_c
        total_penalty_c = min(total_penalty_c, 10.0)  # global cap

        wbgt_eff_c = wbgt_base_c + total_penalty_c

        ss["total_penalty_c"] = total_penalty_c
        ss["wbgt_eff_c"] = wbgt_eff_c
        ss["penalties_applied"] = True

        # ------------------------------------------------------------
        # CRITICAL: log-safe compute trigger (prevents Streamlit spam)
        # ------------------------------------------------------------
        ss["compute_counter"] = ss.get("compute_counter", 0) + 1
        ss["last_compute_ts"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Display with correct units
        if ss["units"] == "imperial":
            penalty_str = f"+{(total_penalty_c * 9/5):.1f} °F"
        else:
            penalty_str = f"+{total_penalty_c:.1f} °C"

        st.success(
            f"Exposure adjustments applied ({penalty_str}) → Effective WBGT = {fmt_temp(wbgt_eff_c, ss['units'])}. "
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
        st.metric("WB – Sweat evaporation effective", fmt_temp(ss["wb_safe_c"], ss["units"]))
    with colW2:
        st.metric("WB – Rising strain", fmt_temp(ss["wb_strain_c"], ss["units"]))
    with colW3:
        st.metric("WB – Evaporation ceiling", fmt_temp(ss["wb_danger_c"], ss["units"]))

    if accl_status == "Acclimatized":
        st.caption(
            "Values approximate **NIOSH/OSHA WBGT guidance** and **physiological wet-bulb limits** "
            "for acclimatized industrial workers."
        )
    else:
        st.caption(
            "All WBGT and Wet-Bulb thresholds are shifted lower for **non-acclimatized** workers "
            "to provide a conservative safety margin."
        )

# ======================================================================
# BLOCK 7 — WBGT RISK CLASSIFICATION + HEAT STRAIN PROFILE (HSP)
# ======================================================================

ss = st.session_state

st.markdown("## 🧭 Heat-Stress Classification & Worker Guidance")

# ------------------------------------------------------------------
# WBGT policy banding
# ------------------------------------------------------------------
def _wbgt_band_from_eff(wbgt_eff_c, A, B, C):
    if wbgt_eff_c < A:
        return ("🟢", "LOW RISK", "Normal work acceptable. Maintain hydration and routine supervision.", 0, "#2ecc71")
    if wbgt_eff_c < B:
        return ("🟠", "CAUTION", "Increase supervision. Enforce hydration and basic work–rest cycles.", 1, "#f39c12")
    if wbgt_eff_c < C:
        return ("🔴", "HIGH STRAIN", "Reduce  exposure; move workers to cooler shaded areas; cool  using ventilation/climate control where available; encourage drinking cool water. Use short work–rest cycles.", 2, "#e74c3c")
    return ("🚫", "WITHDRAWAL", "Stop routine work. Only emergency tasks with medical monitoring.", 3, "#7f0000")

# ------------------------------------------------------------------
# Inputs
# ------------------------------------------------------------------
wbgt_eff  = ss.get("wbgt_eff_c")
wbgt_base = ss.get("wbgt_base_frozen")

if wbgt_eff is None:
    st.info("Press **Apply adjustments & compute** to calculate WBGT and heat strain.")
    st.stop()

A = float(ss.get("thr_A_c", 29))
B = float(ss.get("thr_B_c", 32))
C = float(ss.get("thr_C_c", 35))

icon, band, msg, wbgt_sev, band_color = _wbgt_band_from_eff(float(wbgt_eff), A, B, C)
ss["risk_band"] = band

# ------------------------------------------------------------------
# Wet-bulb lookup (Primary truth = natural wet-bulb computed in Block-5)
# ------------------------------------------------------------------
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

# ------------------------------------------------------------------
# Wet-bulb thresholds from Block-6 (fallback to defaults if missing)
# ------------------------------------------------------------------
wb_safe_c   = float(ss.get("wb_safe_c", 26.0))
wb_strain_c = float(ss.get("wb_strain_c", 28.0))
wb_danger_c = float(ss.get("wb_danger_c", 30.0))

# Units display helpers
units_mode = ss.get("units", "metric")
if units_mode == "imperial":
    wbgt_disp = f"{(float(wbgt_eff) * 9/5 + 32):.1f} °F"
    pen_disp  = f"+{(pen_c * 9/5):.1f} °F"
    wb_disp   = f"{(wb_info_c * 9/5 + 32):.1f} °F" if wb_info_c is not None else "—"
    wb_thr_disp = f"{(wb_safe_c*9/5+32):.0f} / {(wb_strain_c*9/5+32):.0f} / {(wb_danger_c*9/5+32):.0f} °F"
else:
    wbgt_disp = f"{float(wbgt_eff):.1f} °C"
    pen_disp  = f"+{pen_c:.1f} °C"
    wb_disp   = f"{wb_info_c:.1f} °C" if wb_info_c is not None else "—"
    wb_thr_disp = f"{wb_safe_c:.0f} / {wb_strain_c:.0f} / {wb_danger_c:.0f} °C"


# Display strings for WB physiology band edges (for card)
if units_mode == "imperial":
    wb1 = f"{(wb_safe_c*9/5+32):.0f} °F"
    wb2 = f"{(wb_strain_c*9/5+32):.0f} °F"
    wb3 = f"{(wb_danger_c*9/5+32):.0f} °F"
else:
    wb1 = f"{wb_safe_c:.0f} °C"
    wb2 = f"{wb_strain_c:.0f} °C"
    wb3 = f"{wb_danger_c:.0f} °C"
# ------------------------------------------------------------------
# Wet-bulb physiological meaning (uses thresholds)
# ------------------------------------------------------------------
wb_msg = "Wet-bulb not available"
wb_color = "#666"

if wb_info_c is not None:
    if wb_info_c < wb_safe_c:
        wb_msg   = "🟢 Body Heat dissipation effective"
        wb_color = "#2ecc71"
    elif wb_info_c < wb_strain_c:
        wb_msg   = "🟡 Body Heat dissipation becoming limited"
        wb_color = "#f1c40f"
    elif wb_info_c < wb_danger_c:
        wb_msg   = "🟠 Body Cooling inadequate / insufficient"
        wb_color = "#f39c12"
    else:
        wb_msg   = "🔴 Body Heat dissipation compromised"
        wb_color = "#e74c3c"

# ------------------------------------------------------------------
# WBGT Display Card (with WB thresholds)
# ------------------------------------------------------------------
subtle_divider()
st.markdown(
f"""
<div style="padding:16px;border-radius:14px;background:#eef4fb;border-left:8px solid {band_color};">
  <b style="font-size:28px;color:#0b2239;">Effective WBGT  {wbgt_disp}</b><br>
  <span style="color:#444;">Exposure adjustments:</span> <b>{pen_disp}</b><br>
  <span style="color:#444;">Wet-bulb:</span> <b>{wb_disp}</b><br>
  <div style="margin-top:6px;font-size:0.92rem;line-height:1.25;">
    <span style="color:#2ecc71;font-weight:700;">🟢 {wb1} to {wb2}</span> <span style="color:#555;">→ Heat dissipation effective</span><br>
    <span style="color:#f1c40f;font-weight:700;">🟡 {wb2} to {wb3}</span> <span style="color:#555;">→ Heat dissipation becoming limited</span><br>
    <span style="color:#e74c3c;font-weight:700;">🔴 ≥ {wb3}</span> <span style="color:#555;">→ Heat dissipation compromised</span>
  </div><br>
  <span style="font-weight:700;color:{wb_color};">{wb_msg}</span><br><br>
  <b style="font-size:20px;color:{band_color};">{icon} {band}</b><br>
  <span style="color:#222;">{msg}</span>
</div>
""", unsafe_allow_html=True
)

# =====================================================================
# HSP — HUMAN COOLING CAPACITY
# =====================================================================

subtle_divider()
st.markdown("### 🧬 Heat-Strain Profile (HSP) — Body's ability to lose heat & cope")

if not wbgt_base:
    st.info("Baseline WBGT not available.")
    st.stop()

db = float(ss.get("db_c", 0))
rh = float(ss.get("rh_pct", 0))
ws = float(ss.get("ws_ms", 0))
gt = float(ss.get("gt_c", 0))
wbgt_env = float(wbgt_base)
wbgt_op  = float(wbgt_eff)

inst_twl = float(ss.get("twl_measured", 0))
if inst_twl > 0:
    mwl_raw = inst_twl
    mwl_source = "Instrument TWL"
else:
    mwl_raw = float(estimate_mwl_wm2(db_c=db, rh_pct=rh, ws_ms=ws, gt_c=gt, wbgt_c=wbgt_env))
    mwl_source = "Model"

# --- physiological caps ---
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

env_sig = (round(db,2),round(rh,2),round(ws,2),round(gt,2),round(wbgt_env,2),round(pen_c,2))
if ss.get("mwl_env_sig") != env_sig:
    ss["mwl_env_sig"] = env_sig
    ss.pop("mwl_env_prev", None)

prev_mwl = ss.get("mwl_env_prev", 9999.0)
mwl_env = min(mwl_raw, mwl_cap, prev_mwl)
ss["mwl_env_prev"] = mwl_env

mwl_op = float(apply_capacity_penalties(
    mwl_env,
    ppe_c=float(ss.get("pen_clo_c",0)),
    veh_c=float(ss.get("pen_veh_c",0)),
    rad_c=float(ss.get("pen_rad_c",0)),
    adh_c=float(ss.get("pen_adhoc_c",0)),
))

hsp = (wbgt_op * 200.0) / (max(1.0, mwl_op) * 30.0)

# Interpretation
if hsp < 0.8:
    h_icon = "🟢"; h_band="Cooling exceeds heat load"; h_color="#2ecc71"
elif hsp < 1.0:
    h_icon = "🟠"; h_band="Heat balance marginal"; h_color="#f39c12"
else:
    h_icon = "🔴"; h_band="Heat gain exceeds heat loss"; h_color="#e74c3c"

# HSP Card (field-friendly)
st.markdown(
f"""
<div style="padding:14px;border-radius:12px;background:#ffffff;border-left:8px solid {h_color};">
  <b style="font-size:18px;color:{h_color};">{h_icon} {h_band}</b><br>
  <span style="color:#222;">HSP (heat demand ÷ cooling ability): <b>{hsp:.2f}</b></span><br>
  <span style="color:#666;font-size:0.92rem;">Wet-bulb influences sweat evaporation — HSP helps show whether human cooling can keep up.</span>
</div>
""", unsafe_allow_html=True
)

with st.expander("Show MWL / cooling capacity details", expanded=False):
    st.markdown(
        f"""<div style="padding:12px;border-radius:10px;background:#f7f7f7;">
        Cooling capacity (MWL, environmental): <b>{mwl_env:.0f} W/m²</b><br>
        Cooling capacity (MWL, operational): <b>{mwl_op:.0f} W/m²</b><br>
        MWL source: <b>{mwl_source}</b> | MWL cap applied: <b>{mwl_cap:.0f} W/m²</b>
        </div>""", unsafe_allow_html=True
    )


# Bottom warnings
if hsp >= 1.0:
    st.error("⛔ **Likely heat gain exceeds heat loss — workers must be removed or actively cooled.**")
elif hsp >= 0.8:
    st.warning("⚠ **Heat balance marginal — small increases in heat, PPE or workload may cause heat storage.**")
else:
    st.success("✅ **Cooling is adequate.**")

# Policy override
st.markdown("### ⚖ Workplace Policy (WBGT) vs Human Ability to Withstand Heat (HSP)")
use_phys = st.checkbox("Determine work continuity based on HSP when more protective than WBGT", value=True)
if use_phys and (hsp >= 1.0 or wbgt_sev < 2):
    st.warning("Human heat-tolerance capacity (HSP) indicates greater danger than WBGT alone, suggesting increased protection is required.")
# ------------------------------------------------------------------
# FINAL RISK RESOLUTION (WBGT + HSP, conservative)
# ------------------------------------------------------------------

# Start with WBGT-derived band
final_risk = ss.get("risk_band", "LOW")

# Normalize wording (safety)
final_risk = final_risk.upper()

# Physiological override (HSP more protective than WBGT)
if use_phys:
    if hsp >= 1.30:
        final_risk = "WITHDRAWAL"
    elif hsp >= 1.00:
        final_risk = "HIGH STRAIN"
    elif hsp >= 0.80 and final_risk == "LOW":
        final_risk = "CAUTION"

# Store for logging / downstream use
ss["final_risk"] = final_risk

st.markdown("### 🧭 Worker Guidance (Field Actions)")

if final_risk == "LOW":
    st.success(
        "✅ **Normal work acceptable**\n\n"
        "• Maintain hydration (cool water, regular intake)\n"
        "• Routine supervision\n"
        "• Continue work with standard rest breaks"
    )

elif final_risk == "CAUTION":
    st.warning(
        "⚠️ **Caution required**\n\n"
        "• Increase hydration frequency\n"
        "• Encourage shaded rest periods\n"
        "• Monitor workers for early heat strain symptoms\n"
        "• Adjust work pace if possible"
    )

elif final_risk == "HIGH STRAIN":
    st.error(
        "🔴 **High heat strain**\n\n"
        "• Reduce exposure immediately\n"
        "• Move workers to shaded or cooled areas\n"
        "• Use ventilation or cooling where available\n"
        "• Enforce short work–rest cycles\n"
        "• Active supervision required"
    )

elif final_risk == "WITHDRAWAL":
    st.error(
        "⛔ **WITHDRAWAL**\n\n"
        "• Stop routine work\n"
        "• Only emergency tasks permitted\n"
        "• Medical monitoring mandatory\n"
        "• Active cooling required\n"
        "• Remove workers if cooling cannot be ensured"
    )

# ======================================================================
# BLOCK 8 — LOGGING OF COMPUTED DECISIONS (AUDIT TRAIL) — SAFE (NO RERUN SPAM)
# ======================================================================

st.markdown("---")
st.markdown("## 📜 Heat-Stress Audit History")

# Ensure audit log exists
if "audit_log" not in ss:
    ss["audit_log"] = []

# IMPORTANT: log only once per "Apply adjustments & compute" click
# We do this by tracking a monotonically increasing compute counter.
if "compute_counter" not in ss:
    ss["compute_counter"] = 0

# Block 5B must set: ss["compute_counter"] += 1 when the button is clicked.
# If you haven't added that yet, scroll down — I show the 2-line patch.
current_compute_id = ss.get("compute_counter", 0)

if "last_logged_compute_id" not in ss:
    ss["last_logged_compute_id"] = -1

# Only log when penalties were applied AND a new compute event happened
if (
    ss.get("penalties_applied", False)
    and ss.get("wbgt_eff_c") is not None
    and current_compute_id != ss["last_logged_compute_id"]
):

    # Pull values safely
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    place = ss.get("place_label", "")

    db_c = float(ss.get("db_c", 0.0))
    rh = float(ss.get("rh_pct", 0.0))
    gt_c = float(ss.get("gt_c", 0.0))
    ws_ms = float(ss.get("ws_ms", 0.0))

    wbgt_base_frozen = ss.get("wbgt_base_frozen", None)
    wbgt_eff_c = float(ss.get("wbgt_eff_c", 0.0))
    total_penalty_c = float(ss.get("total_penalty_c", 0.0))

    # HSP values (may or may not exist)
    hsp_env = ss.get("hsp_env", None)
    hsp_op = ss.get("hsp_op", None)

    # NOTE: CHSI is suppressed; do not log misleading values
    chsi_scaled = None

    log_entry = {
        "timestamp": ts,
        "location": place,

        # Environment inputs
        "DB (°C)": f"{db_c:.1f}",
        "RH (%)": f"{rh:.0f}",
        "GT (°C)": f"{gt_c:.1f}",
        "Wind (m/s)": f"{ws_ms:.2f}",

        # WBGT outputs
        "WBGT baseline frozen (°C)": f"{float(wbgt_base_frozen):.1f}" if wbgt_base_frozen is not None else "",
        "Exposure adjustment total (°C)": f"{total_penalty_c:.1f}",
        "Effective WBGT (°C)": f"{wbgt_eff_c:.1f}",

        # Risk
        "Risk": ss.get("risk_band", ""),

        # HSP outputs (if available)
        "HSP env (TWL/WBGTbase)": f"{float(hsp_env):.2f}" if hsp_env is not None else "",
        "HSP op (TWL/WBGTeff)": f"{float(hsp_op):.2f}" if hsp_op is not None else "",

        # CHSI suppressed
        "CHSI (suppressed)": "" if chsi_scaled is None else f"{chsi_scaled:.0f}",
    }

    ss["audit_log"].append(log_entry)
    ss["last_logged_compute_id"] = current_compute_id

# -----------------------------
# Audit Log Display & Export
# -----------------------------
has_log = bool(ss["audit_log"])

if has_log:
    df = pd.DataFrame(ss["audit_log"])
    st.dataframe(df, use_container_width=True)
    csv_data = df.to_csv(index=False).encode("utf-8")
else:
    st.info(
        "No computed decisions yet. Records appear after you press "
        "**Apply adjustments & compute**."
    )
    csv_data = b""

st.caption("Export saves a CSV file without leaving the assessment screen.")
st.download_button(
    label="📤 Export Audit Log (CSV)",
    data=csv_data,
    file_name=f"CHSRMT_Audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
    mime="text/csv",
    disabled=not has_log,
)

# Display log
# has_log = bool(ss["audit_log"])

# # if has_log:
  #  df = pd.DataFrame(ss["audit_log"])
   # st.dataframe(df, use_container_width=True)
    # csv_data = df.to_csv(index=False).encode("utf-8")
# else:
  #  st.info("No computed decisions yet. Records appear after you press **Apply adjustments & compute**.")
   # csv_data = b""

# st.download_button(
  #  label="📥 Download Audit Log as CSV",
   # data=csv_data,
    # file_name=f"CHSRMT_Audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
    # mime="text/csv",
    # disabled=not has_log,
# )

# ======================================================================
# BLOCK 9 — APPENDIX & FIELD GUIDANCE (MASTER COLLAPSIBLE) + FOOTER SAFE
# ======================================================================

st.markdown("---")

with st.expander("📘 Guidance & Field Appendices", expanded=False):

    st.markdown("### Hydration, Acclimatization, Work–Rest & Warning Signs")

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

    with st.expander("⚡ Acclimatization Expectations (OSHA/NIOSH style)"):
        st.markdown("""
        **Typical timeline**
        - 5–7 shifts of increasing exposure  
        - Begin at **20% of usual duration** on day 1, add **20% per day**
        
        **High-risk when**
        - New workers  
        - Returning after > 1 week absence  
        - Workers recently ill
        
        **Supervision**
        - Buddy system during first 1–3 days  
        - Observe for confusion or loss of coordination
        """)

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

    with st.expander("🚩 Early Warning Signs & First-Aid Triggers"):
        st.markdown("""
        **Red-flag symptoms requiring immediate action**
        - Dizziness, collapse, faintness  
        - Confusion or altered behavior  
        - Vomiting  
        - Hot, red, dry skin  
        - Staggering movement
        
        **Immediate steps**
        - Move to shade/cooling  
        - Apply cool water/packs to neck/axilla/groin  
        - Provide fluids if conscious  
        - Activate emergency medical support if no rapid improvement
        """)

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
        "This appendix provides field-support content only. It does **not replace medical assessment, OSHA/NIOSH procedures, or employer HSE policy.**"
    )

# Add bottom padding so footer does not cover buttons/tables
st.markdown(
    "<div style='height: 72px;'></div>",
    unsafe_allow_html=True
)

# ======================================================================
# FIXED PROFESSIONAL FOOTER — OWNERSHIP + PUBLIC USE + FEEDBACK
# ======================================================================

st.markdown(f"""
<style>
.footer {{
    position: fixed;
    bottom: 0;
    left: 0;
    width: 100%;
    background: rgba(15, 18, 22, 0.94);
    color: #ddd;
    text-align: center;
    padding: 4px 8px;
    font-size: 11px;
    line-height: 1.2;
    border-top: 1px solid rgba(255,255,255,0.08);
    z-index: 9999;
}}
.footer a {{
    color: #9fd3ff;
    text-decoration: none;
}}
.footer a:hover {{
    text-decoration: underline;
}}
</style>

<div class="footer">
<b>© 2026 Dr. Gummanur T. Manjunath — CHSRMT® (Calibrated Heat Stress Risk Management Tool)</b><br>
Field Heat-Stress Decision Support System — Integrating <b>WBGT • TWL • MWL • HSP</b><br>

<span style="opacity:0.9;">
Free public-use decision-support tool for occupational heat-stress awareness & field screening.<br>
Not a substitute for site HSE policy, IH judgment, medical evaluation, or regulatory compliance.
No organization or professional society endorses this tool unless explicitly stated.
</span><br>

<span style="opacity:0.9;">
Feedback & Field Validation:
<a href="https://forms.gle/7rfrXZXkyCdXqGVs5" target="_blank">https://forms.gle/7rfrXZXkyCdXqGVs5</a>
&nbsp; | &nbsp; Build: {APP_VERSION}
</span>
</div>
""", unsafe_allow_html=True)
