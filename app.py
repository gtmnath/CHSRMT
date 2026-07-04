# ======================================================================
# BLOCK 1 — Imports, page config, utilities, session defaults
# ======================================================================
"""
HART — Heat Assessment & Response Tool
# Proprietary Evaluation License
# July 4 2026 at 3 35 PM
Copyright (c) 2025–2026
Dr. Gummanur T. Manjunath, MD
All Rights Reserved
"""

import math
import pandas as pd
import requests
import streamlit as st
from datetime import datetime

APP_VERSION = "v1.9.75-github-sidebar-font-cleanup"

st.set_page_config(
    page_title="H.A.R.T - HEAT ASSESSMENT & RESPONSE TOOL",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ----------------------------
# Global CSS (compact + mobile-fit improvements)
# ----------------------------
st.markdown("""
<style>

/* ---------- Color scheme variables (mobile dark-mode safe) ---------- */
:root{
  --card-bg: #ffffff;
  --card-fg: #0b2239;
  --card-muted: #334155;
}
@media (prefers-color-scheme: dark){
  :root{
    --card-bg: #0b1220;
    --card-fg: #e5e7eb;
    --card-muted: #cbd5e1;
  }
}


/* ---------- Typography ---------- */
h1 {font-size: 1.40rem !important; margin-bottom: 0.25rem;}
h2 {font-size: 1.20rem !important; margin-bottom: 0.20rem;}
h3 {font-size: 1.00rem !important; margin-bottom: 0.15rem;}

div[data-testid="stMarkdownContainer"] p {
    margin-bottom: 0.12rem;
}

/* ---------- Visibility helpers (dark-mode safe) ---------- */
.ui-strong { color: var(--text-color) !important; font-weight: 800 !important; opacity: 0.95; }
.ui-subtle { color: var(--text-color) !important; font-weight: 600 !important; opacity: 0.94; }
.ui-muted  { color: var(--text-color) !important; opacity: 0.88; }

/* Make horizontal rules visible in both light & dark themes */
hr { border: none !important; border-top: 1px solid rgba(128,128,128,0.50) !important; margin: 0.85rem 0 !important; }

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

.section-sub { color: var(--text-color); opacity: 0.86; font-size: 0.88rem; margin-bottom: 0.15rem; }

/* ---------- Layout Tightening ---------- */
div.block-container {
    padding-top: 0.85rem;
    padding-bottom: 1.10rem;
}

div[data-testid="stVerticalBlock"] {
    gap: 0.22rem;
}

div[data-testid="stHorizontalBlock"] {
    gap: 0.50rem;
}

/* ---------- Mobile Optimization ---------- */
@media (max-width: 700px) {

  /* Keep sidebar available on Streamlit Cloud and desktop/tablet layouts. */
  section[data-testid="stSidebar"], div[data-testid="stSidebar"] { display: block !important; }

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


/* =========================
   Mobile + Dark-mode contrast fixes (v3)
   ========================= */
@media (prefers-color-scheme: dark) {
  .ui-strong, .ui-subtle, .ui-note, .ui-caption, .ui-help, .stMarkdown, .stMarkdown p, .stMarkdown li, .stMarkdown span, label, .stCaption {
    color: rgba(255,255,255,0.92) !important;
    opacity: 1 !important;
  }
  .ui-subtle, .ui-caption, .ui-help {
    color: rgba(255,255,255,0.78) !important;
  }
  .ui-divider {
    border-top: 1px solid rgba(255,255,255,0.25) !important;
  }
  .stExpander, .stExpanderHeader, .stExpander p, .stExpander span {
    color: rgba(255,255,255,0.90) !important;
  }
}
@media (prefers-color-scheme: light) {
  .ui-strong, .ui-subtle, .ui-note, .ui-caption, .ui-help, .stMarkdown, .stMarkdown p, .stMarkdown li, .stMarkdown span, label, .stCaption {
    color: rgba(20,20,20,0.96) !important;
    opacity: 1 !important;
  }
  .ui-subtle, .ui-caption, .ui-help {
    color: rgba(40,40,40,0.84) !important;
  }
  .ui-divider {
    border-top: 1px solid rgba(0,0,0,0.18) !important;
  }
}



/* =========================
   Mobile readability boost + optional sidebar hide
   ========================= */
@media (max-width: 700px) {
  /* Make key headers + workflow line stand out more on phones */
  .ui-strong, .ui-subtle {
    opacity: 1 !important;
    font-weight: 800 !important;
    letter-spacing: 0.1px;
  }
  .ui-subtle { font-weight: 700 !important; }

  /* Welcome box body text: slightly larger + fully opaque */
  .welcome-box p {
    font-size: 0.92rem !important;
    opacity: 1 !important;
    line-height: 1.35 !important;
  }

  /* Reduce “washed out” look of plain markdown text in dark mode phones */
  div[data-testid="stMarkdownContainer"] p,
  div[data-testid="stMarkdownContainer"] span,
  div[data-testid="stMarkdownContainer"] li {
    opacity: 1 !important;
  }

  /* Keep sidebar toggle visible; do not force-hide sidebar on Streamlit Cloud. */
  section[data-testid="stSidebar"] { display: block !important; }
  div[data-testid="collapsedControl"] { display: block !important; }
}



/* ---------- Force white text inside the blue welcome box (beats light-mode overrides) ---------- */
.welcome-box,
.welcome-box h2,
.welcome-box h2 span,
.welcome-box p,
.welcome-box p span,
.welcome-box li,
.welcome-box li span,
.welcome-box b,
.welcome-box strong,
.welcome-box a {
    color: rgba(255,255,255,0.97) !important;
    opacity: 1 !important;
    text-shadow: 0 1px 1px rgba(0,0,0,0.28);
}
.welcome-box b, .welcome-box strong { font-weight: 800 !important; }


/* --- Mobile visibility fix: ensure text is visible inside white cards (risk summary / supervisor actions) --- */
.white-card, .white-card * { color: #0b2239 !important; }
.white-card .ui-muted { color: #334155 !important; }  /* muted text inside white cards */
.sa-card, .sa-card * { color: var(--card-fg) !important; }
.kpi-card, .kpi-card * { color: #0b2239 !important; }
/* keep colored emphasis when explicitly set inline */

/* ---------- Global readability + breathing space ---------- */
body, .stMarkdown, .stText { color: #1a202c !important; }
.block-container {
    padding-top: 1.35rem !important;
    padding-bottom: 4rem !important;
}
h2, h3 {
    margin-top: 0.85rem !important;
    margin-bottom: 0.30rem !important;
}
div[data-testid="stExpander"] {
    margin-top: 0.25rem;
    margin-bottom: 0.25rem;
}
div.stButton > button {
    border-radius: 10px !important;
    font-weight: 700 !important;
}

/* landing-page mode button emphasis */
.mode-title { color:#17324d !important; font-weight:800 !important; margin-bottom:0.10rem !important; }
.mode-caption { color:#34495e !important; font-weight:600 !important; margin-top:0 !important; }

/* make the Professional Analysis button clearly intentional on the landing page */
div[data-testid="stHorizontalBlock"] div[data-testid="column"]:nth-of-type(2) div.stButton > button,
div[data-testid="stHorizontalBlock"] > div:nth-child(2) div.stButton > button {
    background-color: #2b6cb0 !important;
    color: #ffffff !important;
    border: 1px solid #2b6cb0 !important;
}
div[data-testid="stHorizontalBlock"] div[data-testid="column"]:nth-of-type(2) div.stButton > button p,
div[data-testid="stHorizontalBlock"] > div:nth-child(2) div.stButton > button p {
    color: #ffffff !important;
}

/* Prevent clipped top content */
header[data-testid="stHeader"] { background: transparent !important; }

/* Hide floating bottom-right overlays that can block content */
div[data-testid="stDecoration"],
button[title="Deploy"],
button[kind="header"],
[data-testid="stStatusWidget"],
[data-testid="stChatFloatingInputContainer"],
[data-testid="stToolbar"] {
    display: none !important;
}


/* ---------- Elegant compact desktop sidebar (v1.9.42) ---------- */
section[data-testid="stSidebar"] {
    width: 300px !important;
    min-width: 300px !important;
    max-width: 300px !important;
    padding-bottom: 2.4rem !important;
}
section[data-testid="stSidebar"] h1 {
    font-size: 1.08rem !important;
    line-height: 1.22 !important;
    margin-top: 0.55rem !important;
    margin-bottom: 0.75rem !important;
}
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {
    font-size: 0.92rem !important;
    line-height: 1.20 !important;
    margin-top: 0.45rem !important;
    margin-bottom: 0.30rem !important;
}
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] div[data-testid="stMarkdownContainer"] {
    font-size: 0.78rem !important;
    line-height: 1.28 !important;
}
section[data-testid="stSidebar"] hr {
    margin: 0.55rem 0 !important;
}
section[data-testid="stSidebar"] .sidebar-selected-box {
    background: rgba(46, 204, 113, 0.14);
    border-radius: 10px;
    padding: 0.48rem 0.58rem;
    margin: 0.22rem 0 0.48rem 0;
    line-height: 1.22 !important;
}
section[data-testid="stSidebar"] .sidebar-selected-box .selected-caption {
    font-size: 0.70rem !important;
    opacity: 0.78;
    margin-bottom: 0.15rem;
}
section[data-testid="stSidebar"] .sidebar-selected-box .selected-value {
    color: #078b3e !important;
    font-size: 0.82rem !important;
    font-weight: 800 !important;
}
section[data-testid="stSidebar"] .sidebar-note {
    font-size: 0.70rem !important;
    opacity: 0.74;
    line-height: 1.25 !important;
    margin: 0.12rem 0 0.55rem 0;
}
section[data-testid="stSidebar"] .sidebar-band-legend {
    font-size: 0.70rem !important;
    line-height: 1.14 !important;
    margin-top: 0.20rem !important;
}
section[data-testid="stSidebar"] .sidebar-band-legend div {
    font-size: 0.70rem !important;
    line-height: 1.14 !important;
    margin: 0.07rem 0 !important;
    white-space: normal !important;
    overflow-wrap: normal !important;
    word-break: normal !important;
}
section[data-testid="stSidebar"] .sidebar-band-legend .band-title {
    font-size: 0.74rem !important;
    font-weight: 850 !important;
    margin: 0.18rem 0 0.22rem 0 !important;
}
section[data-testid="stSidebar"] .sidebar-band-legend .band-thr {
    font-size: 0.66rem !important;
    opacity: 0.82 !important;
    padding-left: 1.05rem !important;
    margin-bottom: 0.12rem !important;
}


/* ---------- Compact technical detail boxes (v1.9.75) ---------- */
.ecce-detail-box {
    background: #e8f3ff;
    border-radius: 12px;
    padding: 0.72rem 0.95rem;
    color: #0755a3 !important;
    font-size: 0.88rem !important;
    line-height: 1.35 !important;
    font-weight: 500 !important;
}
.ecce-detail-box b { font-weight: 800 !important; }
@media (max-width: 900px) {
  .ecce-detail-box {
      font-size: 0.78rem !important;
      line-height: 1.28 !important;
      padding: 0.62rem 0.78rem !important;
  }
  .ecce-detail-box p { margin-bottom: 0.18rem !important; }
}

/* Slightly reduce large HSP advisory text on narrower cloud/mobile views */
@media (max-width: 900px) {
  .sa-card { font-size: 0.90rem !important; line-height: 1.32 !important; }
  .sa-card ul { margin-top: 0.30rem !important; margin-bottom: 0.25rem !important; }
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

def go_to_mode_select():
    """Return to the mode-selection page reliably without wiping the app state."""
    ss["force_mode_select"] = True
    ss["app_mode"] = None
    ss["landing_open"] = False
    ss["confirm_reset"] = False
    st.rerun()

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
# HART input validation guardrails (v1.9.72)
# ----------------------------
# Hard limits are aligned with the TWL-1SV-style instrument/sensor specification
# where applicable: DB -20 to 90 °C, globe -40 to 120 °C, RH 0 to 100%,
# wind 0 to 70 m/s, and heat-index style temperature outputs 0 to 66 °C.
# Warning limits are occupational plausibility / decision-quality checks, not
# sensor capability limits. This separates "can the sensor measure this?" from
# "does this value make sense for heat-stress decision support?"
HART_VALIDATION_LIMITS = {
    "db_c": {"label": "Dry Bulb Temperature (DB)", "hard_min": -20.0, "hard_max": 90.0, "warn_min": 10.0, "warn_max": 55.0, "unit": "°C"},
    "rh_pct": {"label": "Relative Humidity (RH)", "hard_min": 0.0, "hard_max": 100.0, "warn_min": 5.0, "warn_max": 100.0, "unit": "%"},
    "gt_c": {"label": "Globe Temperature (GT)", "hard_min": -40.0, "hard_max": 120.0, "warn_min": 10.0, "warn_max": 80.0, "unit": "°C"},
    "ws_ms": {"label": "Wind Speed (WS)", "hard_min": 0.0, "hard_max": 70.0, "warn_min": 0.0, "warn_max": 20.0, "unit": "m/s"},
    "p_kpa": {"label": "Barometric Pressure", "hard_min": 60.0, "hard_max": 110.0, "warn_min": 75.0, "warn_max": 105.0, "unit": "kPa"},
    "wbgt_instr": {"label": "Instrument WBGT", "hard_min": 0.0, "hard_max": 66.0, "warn_min": 15.0, "warn_max": 45.0, "unit": "°C"},
    "twl_measured": {"label": "Instrument TWL", "hard_min": 0.0, "hard_max": 500.0, "warn_min": 50.0, "warn_max": 450.0, "unit": "W/m²"},
}

def hart_clamp_value(key, value):
    """Clamp an existing session value before feeding it into Streamlit number_input."""
    spec = HART_VALIDATION_LIMITS.get(key)
    if not spec:
        return value
    try:
        v = float(value)
    except Exception:
        return spec["hard_min"]
    return max(spec["hard_min"], min(spec["hard_max"], v))

def hart_validate_value(key: str, value: float):
    """Return (is_valid, message_type, message). message_type = 'error', 'warning', or None."""
    spec = HART_VALIDATION_LIMITS.get(key)
    if spec is None:
        return True, None, ""
    try:
        v = float(value)
    except Exception:
        return False, "error", f"{spec['label']} must be a number."
    unit = spec["unit"]
    if v < spec["hard_min"] or v > spec["hard_max"]:
        return (False, "error", f"{spec['label']} = {v:g} {unit} is outside the allowed range ({spec['hard_min']:g}–{spec['hard_max']:g} {unit}). Please check the entry.")
    if v < spec["warn_min"] or v > spec["warn_max"]:
        return (True, "warning", f"{spec['label']} = {v:g} {unit} is unusual for routine field use. Please make sure the value and units are correct before proceeding.")
    return True, None, ""

def hart_validate_all_inputs(db_c, rh_pct, gt_c, ws_ms, p_kpa, wbgt_instr=0.0, twl_measured=0.0):
    checks = [("db_c", db_c), ("rh_pct", rh_pct), ("gt_c", gt_c), ("ws_ms", ws_ms), ("p_kpa", p_kpa)]
    try:
        if wbgt_instr and float(wbgt_instr) > 0:
            checks.append(("wbgt_instr", wbgt_instr))
    except Exception:
        checks.append(("wbgt_instr", wbgt_instr))
    try:
        if twl_measured and float(twl_measured) > 0:
            checks.append(("twl_measured", twl_measured))
    except Exception:
        checks.append(("twl_measured", twl_measured))
    errors, warnings = [], []
    for key, value in checks:
        ok, msg_type, msg = hart_validate_value(key, value)
        if msg_type == "error":
            errors.append(msg)
        elif msg_type == "warning":
            warnings.append(msg)
    return errors, warnings

def hart_add_context_validation_warnings(db_c, rh_pct, gt_c, ws_ms, p_kpa, weather_fetched=False):
    """Add field-practical warnings that are not simple min/max checks.

    These messages are intentionally advisory. They do not block calculation,
    but they help field users avoid common interpretation errors such as using
    10-m weather-station wind as worker-level air movement, accepting an
    estimated globe temperature as if it were measured, or missing unit-entry
    mistakes.
    """
    warnings = []
    try:
        db = float(db_c)
        rh = float(rh_pct)
        gt = float(gt_c)
        ws = float(ws_ms)
        p = float(p_kpa)
    except Exception:
        return warnings

    # Unit-entry / decimal-place reminders. Hard limits now follow instrument-style
    # sensor capability. These messages catch occupationally unusual but possible
    # values before they are accepted as decision-quality inputs.
    if db >= 55.0:
        warnings.append(
            "Dry Bulb temperature is extremely high for occupational field use. Please make sure this is °C and not °F, Kelvin, or a misplaced decimal entry before proceeding."
        )
    elif db <= 0.0:
        warnings.append(
            "Dry Bulb temperature is at or below freezing. HART is a heat-stress decision-support tool; confirm that a heat-stress assessment is appropriate for this scenario."
        )
    if gt >= 80.0:
        warnings.append(
            "Globe temperature is very high. Please make sure this is a measured globe temperature and not a unit or decimal-place error before proceeding."
        )

    # Weather-station wind is often measured at 10 m height and may not represent
    # worker-level air movement, especially indoors or in sheltered workplaces.
    if ws >= 10.0:
        warnings.append(
            "Wind speed is very high for most occupational settings. Please make sure the value, units, and whether it reflects worker-level air movement or open-air weather-station wind before proceeding."
        )
    elif ws >= 5.0:
        if weather_fetched:
            warnings.append(
                "Wind speed is from local weather data and may represent 10-m open-air wind. Worker-level air movement in a workplace, vehicle, shelter, potline, workshop, or enclosed area may be lower."
            )
        else:
            warnings.append(
                "Wind speed is brisk. Confirm whether this is worker-level air movement or open-air weather-station wind if the assessment is for a sheltered or indoor workplace."
            )
    elif ws <= 0.2:
        warnings.append(
            "Very low air movement entered. This can materially reduce cooling capacity in enclosed or stagnant work areas; make sure the value is correct if measured."
        )

    # Relative humidity / evaporation caution.
    if rh >= 90.0:
        warnings.append(
            "Relative humidity is very high. Sweat evaporation may be less effective even when WBGT is in a low policy band; review wet-bulb/evaporation details if workers report discomfort."
        )

    # Globe temperature context.
    if weather_fetched and abs(gt - (db + 3.0)) < 0.11:
        warnings.append(
            "Globe temperature appears to be the app's weather-based estimate (DB + 3 °C), not an instrument reading. Replace it with measured globe temperature when available, especially in direct sun or radiant-heat areas."
        )
    if gt < db - 2.0:
        warnings.append(
            "Globe temperature is below dry bulb temperature. This may occur in shade/rain/evaporative settings, but please make sure the instrument reading and units are correct before proceeding."
        )
    if gt > db + 20.0:
        warnings.append(
            "Globe temperature is substantially higher than dry bulb temperature, suggesting strong radiant or solar heat load. Make sure globe thermometer placement and controls for radiant/solar exposure are correct; consider measured WBGT/TWL where available."
        )

    if p < 90.0 or p > 104.0:
        warnings.append(
            "Barometric pressure differs from sea-level default. This may be appropriate at altitude or unusual weather; make sure pressure units and source are correct if manually entered."
        )

    # Deduplicate while preserving order.
    seen = set()
    out = []
    for w in warnings:
        if w not in seen:
            out.append(w)
            seen.add(w)
    return out

def hart_show_validation_messages(errors, warnings):
    # Deduplicate after combining range-based and context-based warnings.
    errors = list(dict.fromkeys(errors or []))
    warnings = list(dict.fromkeys(warnings or []))
    if errors:
        st.error("Please correct the following input issue(s) before calculation:")
        for e in errors:
            st.write(f"• {e}")
        st.stop()
    for w in warnings:
        st.warning(w)

def hart_supervisory_advice(final_risk, hsp=None):
    risk = str(final_risk or "").upper()

    emergency = (
        "Confusion, collapse, seizure, fainting, altered behavior, or inability to continue "
        "must be treated as a medical emergency: stop work, start active cooling, and call site medical/emergency response."
    )

    if "WITHDRAWAL" in risk or "EXTREME" in risk:
        return {
            "headline": "⛔ Withdraw / Stop Exposure",
            "action": "Immediately reduce exposure by stopping non-essential work and implementing maximum controls.",
            "controls": "Move to shade/cooling area, remove unnecessary PPE when safe, increase air movement, provide active cooling, and reassess before restart.",
            "monitoring": "Do not allow lone work. Supervisor or medic review is recommended before return.",
            "emergency": emergency,
        }

    if "HIGH" in risk:
        return {
            "headline": "🔴 High Strain – Escalate Controls",
            "action": "Reduce work pace or duration and increase recovery opportunities.",
            "controls": "Review PPE/PPC, radiant heat, enclosure/vehicle exposure, airflow, hydration access, and cooling arrangements.",
            "monitoring": "Use buddy monitoring and closer supervisor observation. Reassess if conditions worsen or symptoms appear.",
            "emergency": emergency,
        }

    if "CAUTION" in risk or "MODERATE" in risk:
        return {
            "headline": "🟠 Caution – Narrowing Safety Margin",
            "action": "Continue only with enhanced attention to hydration, pacing, acclimatization, and rest access.",
            "controls": "Confirm workers are acclimatized and fit for task. Avoid unnecessary PPE burden and improve shade/airflow where possible.",
            "monitoring": "Increase supervisor checks, especially for new, returning, older, or symptomatic workers.",
            "emergency": emergency,
        }

    return {
        "headline": "🟢 Low – Routine Controls",
        "action": "Continue work under routine heat-stress controls.",
        "controls": "Maintain hydration, shade/rest access, and normal supervision.",
        "monitoring": "Reassess if weather, workload, PPE, radiant heat, or worker condition changes.",
        "emergency": emergency,
    }


def hart_hsp_threshold_advisory(hsp):
    """Graduated HSP advisory layer for field supervisors.

    This does not replace WBGT/TWL policy. It displays only the current
    HSP escalation band plus the next escalation trigger.
    """
    if hsp is None:
        return {
            "icon": "⚪",
            "title": "HSP Advisory Not Available",
            "band": "HSP not computed",
            "border": "#64748b",
            "bg": "#f8fafc",
            "message": "Calculate baseline and adjusted conditions to display HSP-driven supervisor guidance.",
            "actions": ["Follow site HSE policy / SOP for WBGT- or TWL-based controls until HSP is available."],
            "next": "—",
        }

    try:
        h = float(hsp)
    except Exception:
        h = None

    if h is None:
        return hart_hsp_threshold_advisory(None)

    if h < 1.10:
        return {
            "icon": "🟢",
            "title": "HSP Advisory — Adequate Cooling Margin",
            "band": "HSP < 1.10",
            "border": "#16a34a",
            "bg": "#f0fdf4",
            "message": "Adequate cooling margin is available for current modeled conditions.",
            "actions": [
                "Maintain routine heat-stress controls, hydration access, and supervision.",
                "Reassess if workload, PPE, radiant heat, wind, or worker condition changes.",
            ],
            "next": "Next escalation at HSP ≥ 1.10 — cooling margin starts narrowing.",
        }
    if h < 1.15:
        return {
            "icon": "🟡",
            "title": "HSP Advisory — Cooling Margin Narrowing",
            "band": "HSP 1.10–1.14",
            "border": "#eab308",
            "bg": "#fefce8",
            "message": "Body may not be cooling as effectively. Cooling-capacity margin is narrowing.",
            "actions": [
                "Do not wait for symptoms.",
                "Review task intensity, PPE/PPC burden, radiant heat, enclosure exposure, and air movement.",
                "Consider advancing recovery breaks and closer buddy/supervisor observation.",
            ],
            "next": "Next escalation at HSP ≥ 1.15 — active supervisor intervention.",
        }
    if h < 1.20:
        return {
            "icon": "🟡",
            "title": "HSP Advisory — Cooling Margin Narrowing",
            "band": "HSP 1.15–1.19",
            "border": "#f59e0b",
            "bg": "#fffbeb",
            "message": "Cooling margin is narrowing. Supervisory control should become active, not passive.",
            "actions": [
                "Do not wait for symptoms.",
                "Reduce pace where feasible and rotate workers through cooler areas.",
                "Improve shade, airflow, local cooling, or exposure controls where possible.",
                "Check workers closely for fatigue, dizziness, confusion, cramps, or reduced performance.",
            ],
            "next": "Next escalation at HSP ≥ 1.20 — cooling margin becoming inadequate.",
        }
    if h < 1.25:
        return {
            "icon": "🟠",
            "title": "HSP Advisory — Cooling Margin Becoming Inadequate",
            "band": "HSP 1.20–1.24",
            "border": "#f97316",
            "bg": "#fff7ed",
            "message": "Cooling margin is becoming inadequate. Avoid prolonged continuous exposure.",
            "actions": [
                "Do not wait for symptoms.",
                "Escalate cooling, recovery, and supervision immediately.",
                "Shorten exposure duration or reduce workload where feasible.",
                "Reassess whether the task should continue under current controls.",
            ],
            "next": "Next escalation at HSP ≥ 1.25 — near withdrawal boundary.",
        }
    if h < 1.30:
        return {
            "icon": "🟠",
            "title": "HSP Advisory — Near Withdrawal Boundary",
            "band": "HSP 1.25–1.29",
            "border": "#ea580c",
            "bg": "#fff7ed",
            "message": "Near withdrawal boundary. The task should not continue without strong controls and recovery planning.",
            "actions": [
                "Do not wait for symptoms.",
                "Prepare to suspend or stop the task unless essential and tightly controlled.",
                "Move recovery arrangements, active cooling, and supervisor/medical readiness into position.",
                "Avoid lone work and prolonged continuous exposure.",
            ],
            "next": "Next escalation at HSP ≥ 1.30 — cooling capacity insufficient.",
        }
    return {
        "icon": "🔴",
        "title": "HSP Advisory — Cooling Capacity Insufficient",
        "band": "HSP ≥ 1.30",
        "border": "#dc2626",
        "bg": "#fef2f2",
        "message": "Cooling capacity appears insufficient under modeled operational conditions.",
        "actions": [
            "Stop or suspend work.",
            "Move exposed workers to a cooling/recovery area.",
            "Assess for heat illness symptoms and follow site medical/emergency procedures.",
            "Restart only after reassessment and stronger controls, in line with site policy.",
        ],
        "next": "Highest HSP cooling-margin escalation band reached.",
    }

def render_hsp_threshold_advisory(hsp):
    adv = hart_hsp_threshold_advisory(hsp)
    actions_html = "".join([f"<li>{a}</li>" for a in adv["actions"]])
    hsp_text = "—" if hsp is None else f"{float(hsp):.2f}"
    st.markdown(f"""
    <div class="sa-card" style="
        border-left:7px solid {adv['border']};
        background:{adv['bg']};
        margin-top:0.35rem;
        margin-bottom:0.55rem;
        padding:0.80rem 0.95rem;
        border-radius:12px;
        box-shadow:0 1px 3px rgba(15,23,42,0.08);
    ">
      <div style="display:flex; align-items:center; justify-content:space-between; gap:0.65rem; flex-wrap:wrap;">
        <div style="font-size:1.02rem; font-weight:850; color:#0f172a !important;">
          {adv['icon']} {adv['title']}
        </div>
        <div style="font-size:0.92rem; font-weight:800; color:#0f172a !important;">
          HSP: {hsp_text} &nbsp;|&nbsp; {adv['band']}
        </div>
      </div>
      <div style="margin-top:0.35rem; font-size:0.94rem; font-weight:650; color:#1e293b !important;">
        {adv['message']}
      </div>
      <ul style="margin-top:0.45rem; margin-bottom:0.35rem; color:#0f172a !important; font-size:0.92rem;">
        {actions_html}
      </ul>
      <div style="font-size:0.82rem; color:#475569 !important; font-weight:650;">
        {adv['next']}<br>
        HSP reflects heat load versus ECCE, the modeled cooling capacity of the environment. Follow site HSE policy / SOP for WBGT- or TWL-based controls; use HSP as an additional cooling-margin indicator.
      </div>
    </div>
    """, unsafe_allow_html=True)

# ----------------------------
# Locked HSP band edges (DO NOT change per run)
# ----------------------------
HSP_GREEN = 6.0   # Unrestricted
HSP_AMBER = 4.0   # Caution
# else -> Withdrawal

# ----------------------------
# ECCE (Estimated Cooling Capacity of the Environment — modeled estimate of environmental cooling capacity) model parameters
# These are "calibration knobs" that we will tune using your field scenarios.
# ----------------------------
ss_default("ECCE_A0", 450.0)     # base W/m²
ss_default("ECCE_A_wb", 12.0)    # wet-bulb adjustment weight
ss_default("ECCE_A_rad", 4.0)    # radiant adjustment weight (GT-DB)
ss_default("ECCE_A_wind", 10.0)  # wind benefit weight (sqrt(ws))
ss_default("ECCE_MIN", 60.0)     # clamp
ss_default("ECCE_MAX", 450.0)    # clamp

# Penalty → ECCE capacity reductions (W/m² per °C-penalty bucket)
ss_default("ECCE_PPE_W", 18.0)
ss_default("ECCE_VEH_W", 12.0)
ss_default("ECCE_RAD_W", 10.0)
ss_default("ECCE_ADH_W",  8.0)




def _sanitize_temp_c(x):
    """Guardrail against unit mistakes (e.g., Kelvin accidentally treated as °C)."""
    try:
        v = float(x)
    except Exception:
        return x
    # Kelvin-like values
    if v > 150.0:
        v = v - 273.15
    # Occasionally values get scaled x10
    if v > 100.0:
        v = v / 10.0
    return v
def estimate_mwl_wm2(db_c: float, rh_pct: float, ws_ms: float, gt_c: float, wbgt_c: float) -> float:
    """Estimate ECCE — Estimated Cooling Capacity of the Environment — in W/m².

    Design intent for the ACGIH-aligned discussion update:
    - Preserve the ACGIH-aligned WBGT/OEL threshold workflow elsewhere in the app.
    - Use ECCE/HSP only as a cooling-capacity cross-check, not as a replacement threshold system.
    - Avoid an excessively steep ECCE collapse at higher WBGT values; the decline is intentionally
      smooth and moderated so HSP remains field-interpretable instead of behaving like a hard TWL band.
    - Keep the physiological direction correct: higher WBGT, higher RH/wet-bulb burden, and radiant
      loading reduce capacity; air movement improves capacity.

    Note: This remains a conservative proxy, not a full physiological TWL engine.
    """
    # Guard rails
    db_c = float(db_c)
    rh_pct = float(max(0.0, min(100.0, rh_pct)))
    ws_ms = float(max(0.0, ws_ms))
    gt_c = float(gt_c)
    wbgt_c = float(wbgt_c)

    # ── 1) Base ECCE from WBGT (smooth, high-WBGT decline deliberately flattened) ──
    # Earlier versions used a stronger quadratic drop. That made HSP rise too abruptly
    # at high WBGT and unintentionally resemble a TWL numeric threshold. This curve
    # preserves monotonic decline while keeping HSP as a decision-support margin signal.
    if wbgt_c <= 30.0:
        mwl_base = 405.0 - 5.5 * (wbgt_c - 25.0)
    else:
        # Above 30 °C WBGT, decline continues but is flattened progressively.
        mwl_base = 377.5 - 4.0 * (wbgt_c - 30.0) - 0.35 * ((max(0.0, wbgt_c - 33.0)) ** 1.35)
    mwl_base = max(150.0, min(430.0, mwl_base))

    # ── 2) Wind / air-movement modifier (reference = 1.0 m/s) ──
    # v1.9.61 correction:
    # Earlier code treated 0 m/s as "neutral" and 1 m/s as a bonus. That made
    # very low air movement look too favorable in enclosed workshops, potlines,
    # casting areas, rodding shops, and similar indoor locations.
    #
    # This version uses 1.0 m/s as the neutral reference point. Below 1.0 m/s,
    # cooling capacity is reduced smoothly; above 1.0 m/s, added air movement
    # improves capacity with a conservative plateau.
    if ws_ms < 1.0:
        # 0.0 m/s ≈ 0.86, 0.5 m/s ≈ 0.93, 1.0 m/s = 1.00
        wind_mod = 0.86 + 0.14 * (max(0.0, ws_ms) ** 0.55)
    else:
        # 1.0 m/s = 1.00, 2.0 m/s ≈ 1.06, 4.0 m/s ≈ 1.14
        wind_mod = 1.0 + 0.13 * math.log1p(ws_ms - 1.0) / math.log1p(3.0)
    wind_mod = max(0.84, min(1.18, wind_mod))

    # ── 3) Radiant modifier (GT above DB reduces cooling capacity) ──
    # v1.9.65 refinement:
    # Ordinary radiant load is handled gently. When globe temperature exceeds
    # dry bulb by more than ~15 °C, the reduction becomes slightly stronger.
    # This better reflects casting furnace, rodding shop, potline and similar
    # high-radiant environments without disturbing routine field scenarios.
    delta_gt = max(0.0, gt_c - db_c)
    if delta_gt <= 15.0:
        rad_mod = 1.0 - 0.0045 * delta_gt
    else:
        rad_mod = 1.0 - (0.0045 * 15.0) - (0.0060 * (delta_gt - 15.0))
    rad_mod = max(0.76, min(1.04, rad_mod))

    # ── 4) RH modifier (higher RH suppresses evaporation) ──
    if rh_pct <= 20.0:
        rh_mod = 1.0 + 0.06 * (20.0 - rh_pct) / 20.0   # up to +6%
    elif rh_pct <= 60.0:
        rh_mod = 1.0 - 0.08 * (rh_pct - 20.0) / 40.0   # down to 0.92
    else:
        rh_mod = 0.92 - 0.24 * (rh_pct - 60.0) / 40.0  # down to 0.68 at RH 100
    rh_mod = max(0.68, min(1.06, rh_mod))

    # ── 5) Extra penalty when Wet Bulb is high (evaporation ceiling signal) ──
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
    ss["wb_mwl_c"] = wb_c  # diagnostic only; do not overwrite the main WB used elsewhere
    if wb_c > 25.0:
        wb_pen = 1.0 - 0.010 * (wb_c - 25.0)
        wb_pen = max(0.70, min(1.0, wb_pen))
    else:
        wb_pen = 1.0

    mwl = mwl_base * wind_mod * rad_mod * rh_mod * wb_pen
    mwl = max(120.0, min(430.0, mwl))
    return float(mwl)

def apply_capacity_penalties(mwl_env: float, ppe_c: float, veh_c: float, rad_c: float, adh_c: float) -> float:
    """
    Convert your °C-style penalties into a reduction in metabolic capacity (W/m²).
    This is the key link that lets HSP change meaningfully AFTER penalties.
    """
    loss = (
        float(ss["ECCE_PPE_W"]) * max(0.0, ppe_c) +
        float(ss["ECCE_VEH_W"]) * max(0.0, veh_c) +
        float(ss["ECCE_RAD_W"]) * max(0.0, rad_c) +
        float(ss["ECCE_ADH_W"]) * max(0.0, adh_c)
    )
    mwl_op = max(float(ss["ECCE_MIN"]), mwl_env - loss)
    return float(mwl_op)


# ======================================================================
# Task / metabolic-rate and physiological projection helpers (v1.9.55)
# ======================================================================
# Values are intentionally transparent and editable. They are used for HART
# decision support, not as a replacement for ACGIH/ISO site policy.
TASK_METABOLIC_PRESETS_W = {
    "Rest / observation only": 115.0,
    "Very light work (standing, inspection, controls)": 180.0,
    "Light work (walking, light hand tools)": 230.0,
    "Moderate work (routine industrial work)": 300.0,
    "Heavy work (manual handling, sustained tools)": 415.0,
    "Very heavy / emergency work": 520.0,
}

CLOTHING_PPE_PRESETS = {
    "Ordinary work clothes / single-layer cotton": {"cav_c": 0.0, "capacity_w": 0.0, "note": "Baseline clothing assumption."},
    "Coveralls / standard workwear": {"cav_c": 1.0, "capacity_w": 12.0, "note": "Adds modest heat-retention burden."},
    "Double-layer clothing or high-visibility overlayer": {"cav_c": 2.0, "capacity_w": 24.0, "note": "Higher insulation and reduced evaporation."},
    "Chemical-resistant / low-permeability clothing": {"cav_c": 3.0, "capacity_w": 42.0, "note": "Evaporative cooling may be substantially restricted."},
    "Impermeable / vapor-barrier clothing": {"cav_c": 4.0, "capacity_w": 60.0, "note": "High risk of uncompensable strain; use specialist program/site policy."},
    "Aluminized / radiant-heat protective clothing": {"cav_c": 3.0, "capacity_w": 48.0, "note": "Protects from radiant heat but may restrict body heat loss."},
}

MET_THRESHOLDS_ACGIH_STYLE = [
    # metabolic W, OAL, OEL, OEL+3, OEL+6, all °C WBGT, ordinary woven clothing baseline
    (115.0, 30.0, 33.0, 36.0, 39.0),
    (180.0, 28.0, 31.0, 34.0, 37.0),
    (300.0, 25.0, 28.0, 31.0, 34.0),
    (350.0, 24.0, 27.0, 30.0, 33.0),
    (415.0, 23.0, 26.0, 29.0, 32.0),
    (520.0, 21.5, 24.5, 27.5, 30.5),
]

def _interp_met_thresholds(met_w: float):
    """Return ACGIH-style threshold tuple for selected metabolic rate.

    The anchor row at 350 W intentionally preserves the existing ACGIH branch
    behavior: OAL 24, OEL 27, OEL+3 30, OEL+6 33 °C.
    """
    met = float(max(90.0, min(600.0, met_w)))
    cols = []
    for idx in range(1, 5):
        anchors = [(row[0], row[idx]) for row in MET_THRESHOLDS_ACGIH_STYLE]
        cols.append(_linear_interp(met, anchors))
    return tuple(cols)

def metabolic_hsp_multiplier(met_w: float) -> float:
    """Task heat-production multiplier for HSP.

    Uses 350 W as the reference because the ACGIH discussion branch currently
    uses the 350 W ordinary-work-clothing example as its baseline. A square-root
    response is deliberate: it makes task intensity visible without producing an
    overconfident physiology prediction.
    """
    try:
        met = float(met_w)
    except Exception:
        met = 350.0
    return max(0.70, min(1.30, math.sqrt(max(90.0, met) / 350.0)))

def estimate_sweat_demand_lph(hsp: float | None, met_w: float, wbgt_c: float | None, clothing_cav: float = 0.0) -> float | None:
    """Coarse hydration-burden estimate for supervisor messaging only."""
    if hsp is None or wbgt_c is None:
        return None
    base = 0.35 + 0.00135 * max(0.0, float(met_w) - 115.0)
    heat = 0.045 * max(0.0, float(wbgt_c) - 24.0)
    strain = 0.30 * max(0.0, float(hsp) - 0.8)
    clothing = 0.06 * max(0.0, float(clothing_cav))
    return max(0.2, min(2.2, base + heat + strain + clothing))

def hart_consequence_projection(hsp: float | None, final_risk: str, met_w: float, wbgt_c: float | None, clothing_cav: float = 0.0):
    """Qualitative projection if advice is not followed or only partly followed.

    This avoids claiming a precise heart-rate or core-temperature prediction.
    It uses directional physiology: heat storage, cardiovascular strain, sweat
    demand, dehydration, and delayed recovery.
    """
    try:
        h = float(hsp) if hsp is not None else None
    except Exception:
        h = None
    risk = str(final_risk or "").upper()
    sweat = estimate_sweat_demand_lph(h, met_w, wbgt_c, clothing_cav)

    if h is None:
        level = "Not available"
        summary = "Compute HSP to display a consequence projection."
    elif h < 0.80 and "LOW" in risk:
        level = "Low projected strain"
        summary = "If conditions remain stable, cooling margin appears adequate; routine supervision should continue."
    elif h < 1.00:
        level = "Body may not be cooling as effectively"
        summary = "If work continues without adequate recovery, the body may not cool as effectively; heart rate may gradually rise and recovery may slow."
    elif h < 1.15:
        level = "Cooling margin narrowing"
        summary = "If advice is ignored, heat storage and cardiovascular strain are likely to increase, especially with sustained work or PPE."
    elif h < 1.30:
        level = "High strain / low cooling-margin trajectory"
        summary = "Continued exposure may lead to rapid fatigue, rising heart rate, heavy sweating, impaired judgment, and heat-exhaustion symptoms."
    else:
        level = "Withdrawal-level cooling-margin trajectory"
        summary = "Continuing work without controls may progress toward uncompensable heat strain and medical emergency."

    if sweat is None:
        sweat_txt = "Sweat demand cannot be estimated until HSP is computed."
    elif sweat < 0.7:
        sweat_txt = f"Estimated sweat demand: about {sweat:.1f} L/hour — maintain planned drinking access."
    elif sweat < 1.2:
        sweat_txt = f"Estimated sweat demand: about {sweat:.1f} L/hour — active hydration planning is needed."
    else:
        sweat_txt = f"Estimated sweat demand: about {sweat:.1f} L/hour — high hydration burden; rest/cooling is also required."

    scenarios = [
        ("Drinks water but does not rest", "Hydration may reduce dehydration risk, but heat storage and cardiovascular strain can continue."),
        ("Rests/cools but does not drink", "Core heat may fall, but fluid deficit may persist and next work period may begin with reduced reserve."),
        ("Uses shade/air movement only", "Radiant and convective load may improve, but metabolic heat from heavy work can still drive strain."),
        ("No controls followed", "Risk may escalate from fatigue and performance loss to heat exhaustion or emergency warning signs."),
        ("Full controls followed", "Best chance of reducing heat storage, supporting cardiovascular recovery, and preserving work capacity."),
    ]
    return {"level": level, "summary": summary, "sweat_txt": sweat_txt, "scenarios": scenarios}

def render_consequence_projection(hsp, final_risk, met_w, wbgt_c, clothing_cav):
    proj = hart_consequence_projection(hsp, final_risk, met_w, wbgt_c, clothing_cav)
    rows = "".join([f"<li><b>{a}:</b> {b}</li>" for a, b in proj["scenarios"]])
    with st.expander("🫀 Consequence projection if controls are missed or only partly followed", expanded=False):
        st.markdown(f"""
        <div class="sa-card" style="border-left:6px solid #7c3aed; margin-top:0.20rem;">
          <div style="font-weight:800; margin-bottom:0.20rem;">{proj['level']}</div>
          <div>{proj['summary']}</div>
          <div style="margin-top:0.25rem;"><b>{proj['sweat_txt']}</b></div>
          <ul style="margin-top:0.40rem;">{rows}</ul>
          <div style="font-size:0.84rem; opacity:0.86; margin-top:0.25rem;">
            This is a qualitative supervisor warning, not an individual medical prediction. Individual response depends on acclimatization,
            hydration, health status, medications, sleep, prior heat exposure, and actual compliance with controls.
          </div>
        </div>
        """, unsafe_allow_html=True)

def _linear_interp(x: float, anchors: list[tuple[float, float]]) -> float:
    """Simple linear interpolation/extrapolation over sorted (x, y) anchors."""
    anchors = sorted(anchors, key=lambda t: t[0])
    x = float(x)
    if x <= anchors[0][0]:
        x0, y0 = anchors[0]
        x1, y1 = anchors[1]
    elif x >= anchors[-1][0]:
        x0, y0 = anchors[-2]
        x1, y1 = anchors[-1]
    else:
        for i in range(len(anchors) - 1):
            x0, y0 = anchors[i]
            x1, y1 = anchors[i + 1]
            if x0 <= x <= x1:
                break
    if abs(x1 - x0) < 1e-9:
        return float(y0)
    return float(y0 + (y1 - y0) * ((x - x0) / (x1 - x0)))

def smooth_mwl_capacity_cap(wbgt_env: float, gt_c: float, ws_ms: float, db_c: float | None = None) -> float:
    """
    Smooth wind-responsive ECCE ceiling for HSP stability.

    v1.9.53 ACGIH-discussion update:
    - Carries forward the v1.9.52 GitHub wind-visible tuning into this
      ACGIH-aligned / Dr Bernard discussion branch.
    - Removes artificial step behavior while allowing air movement to visibly
      improve modeled cooling capacity.
    - Adds a modest nonlinear wind bonus from ~0.5 to 3–4 m/s, followed by a
      conservative plateau so high wind does not make hot/radiant work appear
      automatically safe.
    - Keeps extreme radiant / very low air-movement conservatism.

    This ceiling is not a WBGT threshold system and does not change the ACGIH
    threshold logic elsewhere in the app.
    """
    wbgt_env = float(wbgt_env)
    gt = float(gt_c)
    ws = float(max(0.0, ws_ms))

    # Smooth WBGT-based environmental ceiling (same structure as GitHub v1.9.52).
    wbgt_excess_28 = max(0.0, wbgt_env - 28.0)
    wbgt_excess_32 = max(0.0, wbgt_env - 32.0)
    mwl_cap = 332.0 - (6.5 * wbgt_excess_28) - (1.8 * (wbgt_excess_32 ** 1.35))

    # Visible air-movement behavior using 1.0 m/s as neutral reference.
    # v1.9.62 retune after WS sweep against TWL reference screenshots:
    # - 1.0 m/s remains the neutral reference.
    # - Below 1.0 m/s, use a monotonic interpolated reduction so enclosed / low-air
    #   movement industrial areas do not look too favorable.
    # - The curve is intentionally stronger below ~0.5 m/s, where convective and
    #   evaporative assistance is sharply restricted in practical field conditions.
    if ws < 1.0:
        low_wind_reduction = _linear_interp(
            ws,
            [
                (0.0, 110.0),
                (0.1, 108.0),
                (0.2, 96.0),
                (0.3, 65.0),
                (0.5, 30.0),
                (0.75, 14.0),
                (0.8, 10.0),
                (1.0, 0.0),
            ],
        )
        mwl_cap -= low_wind_reduction
    else:
        wind_cap_bonus = 34.0 * math.log1p(ws - 1.0) / math.log1p(3.0)
        wind_cap_bonus = max(0.0, min(38.0, wind_cap_bonus))
        mwl_cap += wind_cap_bonus

    # Radiant-heat correction (v1.9.64).
    # June 19, 2026 testing showed good wind-speed alignment but under-response
    # when globe temperature was much higher than dry bulb temperature, e.g.
    # DB 34 / RH 60 / WS 1.0 with GT 44 or 54 °C. Casting furnaces, potlines
    # and anode rodding shops can have this pattern: air movement may help, but
    # radiant heat continues to add heat load to the worker.
    #
    # Use GT-DB when DB is available. Fall back to the older absolute-GT check
    # when called without DB, so older internal calls remain safe.
    if db_c is not None:
        try:
            radiant_delta = max(0.0, gt - float(db_c))
        except Exception:
            radiant_delta = max(0.0, gt - 45.0)
    else:
        radiant_delta = max(0.0, gt - 45.0)

    # Mild radiant difference is already partly represented in WBGT. Additional
    # reduction begins beyond about GT-DB = 5 °C and strengthens nonlinearly.
    radiant_excess_delta = max(0.0, radiant_delta - 5.0)
    mwl_cap -= 13.5 * math.sqrt(radiant_excess_delta) + 2.3 * radiant_excess_delta

    # Safety backstop for very high absolute globe temperature even when DB is
    # unavailable or radiant_delta is understated.
    absolute_gt_excess = max(0.0, gt - 45.0)
    mwl_cap -= 1.2 * absolute_gt_excess

    return max(180.0, min(430.0, float(mwl_cap)))


def stabilized_hsp_capacity(
    mwl_op: float,
    floor_wm2: float = 115.0,
    softening_start_wm2: float = 200.0,
    softening_fraction: float = 0.50,
) -> float:
    """Return the ECCE denominator used for HSP calculation.

    v1.9.48 severe-end softening:
    - HSP is heat load divided by modeled cooling capacity.
    - At high heat load, small changes in ECCE-op can over-amplify HSP because
      the denominator becomes small.
    - Below 200 W/m², only 50% of the further ECCE decline is passed into the
      HSP denominator. The displayed ECCE-op is NOT changed.
    - A 115 W/m² absolute floor is retained as a final guardrail.

    This does NOT change WBGT, exposure adjustments, ECCE display, or policy bands.
    It only stabilizes the HSP ratio denominator.
    """
    try:
        cap = float(mwl_op)
    except Exception:
        cap = floor_wm2

    floor = float(floor_wm2)
    soft_start = float(softening_start_wm2)
    frac = float(softening_fraction)

    if cap < soft_start:
        cap = soft_start - frac * (soft_start - cap)

    return max(floor, cap)

def build_hsp_validation_table(rh_values=(60,), db_min=30, db_max=40, ppe_values=(0.0, 1.0, 2.0)):
    """Create a small developer validation table for HSP smoothness checks."""
    rows = []
    for rh_v in rh_values:
        for ppe_v in ppe_values:
            prev_hsp = None
            for db_v in range(int(db_min), int(db_max) + 1):
                gt_v = db_v + 3.0
                ws_v = 1.0
                twb_v = (
                    db_v * math.atan(0.151977 * math.sqrt(rh_v + 8.313659))
                    + math.atan(db_v + rh_v)
                    - math.atan(rh_v - 1.676331)
                    + 0.00391838 * (rh_v ** 1.5) * math.atan(0.023101 * rh_v)
                    - 4.686035
                )
                f_v = 1.0 / (1.0 + 0.4 * math.sqrt(max(ws_v, 0.1)))
                gt_adj_v = db_v + (gt_v - db_v) * f_v
                wbgt_env_v = 0.7 * twb_v + 0.2 * gt_adj_v + 0.1 * db_v
                wbgt_op_v = wbgt_env_v + ppe_v
                mwl_raw_v = estimate_mwl_wm2(db_c=db_v, rh_pct=rh_v, ws_ms=ws_v, gt_c=gt_v, wbgt_c=wbgt_env_v)
                mwl_cap_v = smooth_mwl_capacity_cap(wbgt_env_v, gt_v, ws_v, db_c=db_v)
                mwl_env_v = min(mwl_raw_v, mwl_cap_v)
                mwl_op_v = max(float(ss["ECCE_MIN"]), mwl_env_v - (float(ss["ECCE_PPE_W"]) * ppe_v))
                # GitHub-matched HSP calculation: direct use of displayed operational ECCE.
                hsp_capacity_v = max(1.0, mwl_op_v)
                hsp_v = (wbgt_op_v * 200.0) / (hsp_capacity_v * 30.0)
                rows.append({
                    "DB °C": db_v,
                    "RH %": rh_v,
                    "GT °C": gt_v,
                    "Wind m/s": ws_v,
                    "PPE +°C": ppe_v,
                    "WBGT env °C": round(wbgt_env_v, 2),
                    "WBGT adj °C": round(wbgt_op_v, 2),
                    "Wet Bulb °C": round(twb_v, 2),
                    "ECCE raw": round(mwl_raw_v, 0),
                    "ECCE cap": round(mwl_cap_v, 0),
                    "ECCE env": round(mwl_env_v, 0),
                    "ECCE op": round(mwl_op_v, 0),
                    "HSP denominator": round(hsp_capacity_v, 0),
                    "HSP": round(hsp_v, 2),
                    "ΔHSP / +1°C": "—" if prev_hsp is None else round(hsp_v - prev_hsp, 2),
                })
                prev_hsp = hsp_v
    return pd.DataFrame(rows)

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

# Risk thresholds — public GitHub branch keeps the existing NIOSH/OSHA-style cut-points
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
# Launch mode + landing gate
# ----------------------------
ss_default("app_mode", None)        # "field" or "professional"
ss_default("landing_open", False)   # professional-mode welcome gate latch
ss_default("force_mode_select", False)
ss_default("force_reopen_welcome", False)

# Safety latch: if the user has already computed (baseline frozen or effective WBGT present),
# do NOT drop back to the Welcome Gate on a normal Streamlit rerun.
try:
    if not ss.get("force_mode_select", False) and not ss.get("force_reopen_welcome", False):
        if (ss.get("wbgt_base_frozen") is not None) or (ss.get("wbgt_eff_c") is not None):
            if ss.get("app_mode") is None:
                ss["app_mode"] = "field"
            ss["landing_open"] = True
except Exception:
    pass

if ss.get("app_mode") is None:
    ss["force_mode_select"] = False
    ss["force_reopen_welcome"] = False
    st.markdown("""
    <h2 style='margin-bottom:0.2rem;'>HART — Heat Assessment & Response Tool</h2>
    <p class='ui-strong' style='margin-top:0; color:#2f3e4e; font-weight:800;'>
    Choose how you want to use HART today
    </p>
    """, unsafe_allow_html=True)

    st.markdown('<div style="height:0.35rem;"></div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="welcome-box" style="color: rgba(255,255,255,0.96) !important; padding-top:0.85rem; padding-bottom:0.95rem;">
        <h2 style="margin-bottom:0.15rem; color: rgba(255,255,255,0.98) !important;">
          ☀️ Select User Mode
        </h2>
        <p style="margin-top:0.10rem; margin-bottom:0; color: rgba(255,255,255,0.92) !important; line-height:1.35;">
          <span style="font-weight:800;">Field Supervisor Mode</span> = Quick entry • Instant decision • Supervisor actions.<br>
          <span style="font-weight:800;">Professional Analysis Mode</span> = Full workflow • Interpretation • Validation context.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div style="height:0.25rem;"></div>', unsafe_allow_html=True)

    m1, m2 = st.columns(2)

    with m1:
        st.markdown("**👷 Field Supervisor Mode**")
        st.markdown(
            "<div style='color:#5c5c5c; font-weight:600; font-size:0.96rem; margin-top:-0.2rem;'>"
            "Quick entry • Instant decision • Supervisor actions."
            "</div>",
            unsafe_allow_html=True
        )
        st.markdown("<div style='height:0.5rem;'></div>", unsafe_allow_html=True)
        if st.button("Open Field Supervisor Mode", type="primary", use_container_width=True):
            ss["app_mode"] = "field"
            ss["landing_open"] = True
            st.rerun()
        st.markdown("<div style='height:0.3rem;'></div>", unsafe_allow_html=True)

    with m2:
        st.markdown("**🧪 Professional Analysis Mode**")
        st.markdown(
            "<div style='color:#5c5c5c; font-weight:600; font-size:0.96rem; margin-top:-0.2rem;'>"
            "Full workflow • Interpretation • Validation context."
            "</div>",
            unsafe_allow_html=True
        )
        st.markdown("<div style='height:0.5rem;'></div>", unsafe_allow_html=True)
        if st.button("🔬 Open Professional Analysis Mode", use_container_width=True):
            ss["app_mode"] = "professional"
            ss["landing_open"] = False
            st.rerun()
        st.markdown("<div style='height:0.3rem;'></div>", unsafe_allow_html=True)

    st.stop()


if ss.get("app_mode") == "professional" and not ss["landing_open"]:
    ss["force_reopen_welcome"] = False
    st.markdown("""
    <h2 style='margin-bottom:0.2rem;'>HART — Heat Assessment & Response Tool</h2>
    <p class='ui-strong' style='margin-top:0; opacity:0.95;'>
    Field-Ready Decision Support For Occupational Heat Stress And Heat Strain
    </p>
    """, unsafe_allow_html=True)

    st.markdown("<div style=\"border-top:1px solid rgba(0,0,0,0.10); margin:0.20rem 0 0.40rem 0;\"></div>", unsafe_allow_html=True)

    st.markdown("""
    <div class="welcome-box" style="color: rgba(255,255,255,0.96) !important;">
        <h2 style="margin-bottom:0.25rem; color: rgba(255,255,255,0.98) !important;">
          ☀️ HART — Heat Assessment & Response Tool
        </h2>
        <p style="margin-top:0.15rem; color: rgba(255,255,255,0.92) !important; line-height:1.35;">
          <span style="font-weight:800;">Wet Bulb Globe Temperature (WBGT)</span> = Screening heat-stress index used to guide permissible exposure limits in occupational standards.<br>
          <span style="font-weight:800;">Heat-Strain Profile (HSP)</span> = Heat load versus available cooling capacity; an additional cooling-margin indicator.
        </p>
        <p style="margin-bottom:0; color: rgba(255,255,255,0.92) !important; line-height:1.35;">
          <span style="font-weight:800;">Workflow:</span> Inputs → Baseline WBGT → Worksite Additional Factors → Adjusted WBGT → HSP → Guidance → Logging
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### What This Tool Does")
    st.markdown("""
- Computes **Baseline WBGT** and **Adjusted WBGT** (after clothing/PPE, vehicle/enclosure, radiant/hot-surface, and site-specific additional factors)
- Uses **Estimated Cooling Capacity of the Environment (ECCE, HART model)** internally to support HSP interpretation
- Computes **HSP** (Heat-Strain Profile) to express **Human Cooling Margin** under current conditions
- Provides **Supervisor Guidance** and maintains an **Audit Log**
""")

    st.info("""
**Scientific Basis (High-Level)**  
**Wet Bulb Globe Temperature (WBGT)** supports screening and policy-level heat-hazard decisions.  
**Estimated Cooling Capacity of the Environment (ECCE, HART model)** is used internally as a modeled environmental cooling-capacity value.  
**Heat-Strain Profile (HSP)** compares heat load against available cooling capacity and serves as an additional cooling-margin indicator.
""")

    st.info("""
**Standards Positioning**  
HART is designed primarily as an occupational heat-stress decision-support tool aligned with the principles of **ACGIH® Heat Stress & Strain TLVs®** and **ISO 7243** WBGT-based assessment.  

HART uses **WBGT as the primary environmental screening indicator**, while adding practical interpretation through **Wet-Bulb / evaporation guidance**, **HSP**, and worksite additional factors such as PPE/clothing, enclosure effects, radiant heat exposure, air movement, and acclimatization.  

Site-specific regulations, procedures, policies, and professional judgment always take precedence.
""")

    # Collapsible definitions / explanations (compact welcome screen)
    with st.expander("📘 Definitions & Explanations (Tap To Expand)", expanded=False):
        st.markdown("""
**Core Terms**
- **Heat Stress**: External Thermal Load from the environment and work conditions
- **Heat Strain**: The Body’s Physiological Response while trying to maintain thermal balance
- **Wet-Bulb Temperature (WB)**: Reflects evaporative cooling potential and sweat evaporation efficiency (a key physiological limiter)
- **Wet Bulb Globe Temperature (WBGT)**: Screening heat-stress index used to guide permissible exposure limits and baseline decisions in occupational practice
- **Thermal Work Limit (TWL)**: Instrument-measured cooling capacity of the environment (W/m²)
- **Estimated Cooling Capacity of the Environment (ECCE, W/m²)**: modeled estimate of how much heat the surrounding environment can remove from a worker under prevailing conditions  
  – Higher ECCE → wider cooling margin  
  – Lower ECCE → narrowing cooling margin  
  – Previously referred to as MWL during development
- **Heat-Strain Profile (HSP)**: Heat load relative to available cooling capacity  
  – Lower HSP = Wider Cooling Margin  
  – Higher HSP = Narrowing Cooling Margin
- **Acclimatization**: Improves Sweat Efficiency, Cardiovascular Stability, And Overall Heat Tolerance

- **Heat Assessment & Response Tool (HART)**: a memorable short name for this field-deployable pilot system dashboard.

**HSP interpretation (Practical)**
- 🟢 **HSP < 0.80** → Adequate Cooling Margin Available  
- 🟠 **0.80–0.99** → Cooling Margin Narrowing  
- 🔴 **HSP ≥ 1.00** → Cooling Margin Becoming Inadequate
""")

    # Sources / standards reference (lightweight list to reassure reviewers)
    with st.expander("📚 Sources & Standards (Summary)", expanded=False):
        st.markdown("""
**Sources of Screening Thresholds and Adjustment Concepts (High-Level):**
- **Standards alignment**: HART is designed primarily as an occupational heat-stress decision-support tool aligned with the principles of **ACGIH® Heat Stress & Strain TLVs®** and **ISO 7243** WBGT-based assessment.
- **WBGT policy layer**: the public GitHub branch uses the existing NIOSH/OSHA-style WBGT guideline bands, while HSP/ECCE provides a separate cooling-capacity cross-check. Site-specific ACGIH TLV/Action Limit values, NIOSH/OSHA guidance, employer policy, and professional judgement remain controlling.
- **Worksite Additional Factors**: Practical correction concepts aligned with published guidance on **clothing/PPE impacts, air movement, radiant heat, and enclosure effects**.
- **HSP (Heat-Strain Profile)**: an additional **cooling-margin indicator** that compares heat load with estimated cooling capacity (ECCE proxy).

**Note:** This app is a decision-support field-deployable pilot system. Site policy, IH/OH judgement, and medical protocols always override.
""")

    # When To Use The Tool (addresses  “shift start vs mid-shift” question)
    with st.expander("🕒 When To Use This Tool (Practical Field Workflow)", expanded=False):
        st.markdown("""
**Recommended usage moments**
- **Shift start / toolbox talk (Preferred):** run a **Baseline WBGT** check (environment only) to set expectations and controls for the shift.
- **Before task execution:** run an **Adjusted WBGT** assessment for the **specific task/crew/PPE/enclosure/radiant condition** (use the **SEG** idea — Similar Exposure Groups).
- **Mid‑shift or whenever conditions change:** repeat if **sun/radiant load rises, wind drops, PPE changes, enclosure changes,** or workers report symptoms.
- **After an event / near‑miss:** document conditions in the **audit log** for learning and prevention.

**If Baseline WBGT is already in the “Extremely High — Essential Work Only” zone at shift start**
- Treat it as a **stop‑and‑think trigger**, not an automatic “work cessation” signal.
- Consider **rescheduling, engineering controls (shade/ventilation), site-approved work–rest controls, additional supervision, medical screening,** and **task re‑planning** before starting.
- Then run **Adjusted WBGT** separately for the *highest‑risk tasks* (e.g., heavy PPE, confined/enclosed, high radiant zones).

**Centralized Deployment (Optional)**
- For large operations, baseline environmental measurements and standard task scenarios may be reviewed centrally.
- HART outputs can then be communicated to field supervisors to guide safe work execution in line with site policy.

**Crew differences**
- Do **separate assessments** when PPE or task intensity differs (at least: **(1) light PPE/low radiant** vs **(2) heavy PPE/high radiant** groups).
- If time is limited, start with the **worst‑case SEG** and apply controls broadly, then refine.

**Inputs that often get questions**
- **Pressure (kPa):** affects air density and some heat‑exchange terms; changes matter mainly at **high altitude** (or unusual environments). If unsure, keep default or allow auto‑fill.
- **Globe temperature:** if you have a measured GT, enter it. If not, the app uses a practical baseline assumption that can be overridden.
""")


    st.warning("Decision-Support Only. Does Not Replace Site HSE Policy, IH / OH Judgement, Or Medical Protocols.")

    # Make the start action prominent and near the bottom (but not buried)
    st.markdown("---")
    if st.button("🚀 Start Heat-Stress Assessment", type="primary", use_container_width=True):
        ss["landing_open"] = True
        st.rerun()

    st.stop()

# ----------------------------
# Working page header
# ----------------------------
if ss.get("app_mode") == "field":
    page_title = "HART — Heat Assessment & Response Tool"
    page_subtitle = "Field Supervisor Mode — rapid input → compute → supervisor action guidance"
    workflow_line = "Units → Location / Weather → Inputs → Baseline → Worksite Additional Factors → Adjusted WBGT → HSP → Supervisor Actions → Logging"
else:
    page_title = "HART — Heat Assessment & Response Tool"
    page_subtitle = "Professional Analysis Mode — field-ready decision support for occupational heat stress and heat strain"
    workflow_line = "Location → Weather → Baseline → Worksite Additional Factors → Adjusted WBGT → HSP (before/after) → Guidance → Logging"

st.markdown(f"""
    <h2 style='margin-bottom:0.2rem;'>{page_title}</h2>
    <p class='ui-subtle' style='margin-top:0; margin-bottom:0.20rem; color:#2f3e4e; font-weight:700;'>
    {page_subtitle}
    </p>
""", unsafe_allow_html=True)

# Small breathing space above the navigation buttons.
st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

mode_c1, mode_c2 = st.columns([1,1])
with mode_c1:
    if st.button("↩ Change User Mode", use_container_width=True, key="change_user_mode_top"):
        go_to_mode_select()
with mode_c2:
    if ss.get("app_mode") == "professional":
        if st.button("ℹ️ Reopen Welcome Page", use_container_width=True, key="reopen_welcome_page_top"):
            ss["force_reopen_welcome"] = True
            ss["landing_open"] = False
            st.rerun()
    else:
        st.markdown(
            "<div style='color:#3f4f60;font-weight:600; padding:0.55rem 0 0 0;'>"
            "Field Supervisor Mode keeps the same calculations and shows the faster workflow."
            "</div>",
            unsafe_allow_html=True
        )

# Small breathing space below the navigation buttons.
st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

st.markdown(
    f"<div style='margin-top:0.15rem; margin-bottom:0.25rem; color:#2f3e4e; font-weight:650; line-height:1.45; word-break:break-word;'>"
    f"{workflow_line}"
    f"</div>",
    unsafe_allow_html=True
)

# ----------------------------
# Quick Reference (WBGT bands + HSP) — mobile friendly (no sidebar needed)
# ----------------------------
with st.expander("📌 Quick Reference (WBGT policy bands + HSP interpretation)", expanded=False):
    A = ss.get("thr_A_c", 29.0)
    B = ss.get("thr_B_c", 32.0)
    C = ss.get("thr_C_c", 35.0)

    st.markdown("**WBGT guideline bands aligned to NIOSH/OSHA-style public GitHub thresholds (Adjusted WBGT uses these same thresholds):**")
    st.write(f"🟢 LOW RISK: < {fmt_temp(A, ss.get('units','metric'))}")
    st.write(f"🟠 CAUTION: {fmt_temp(A, ss.get('units','metric'))} – {fmt_temp(B, ss.get('units','metric'))}")
    st.write(f"🔴 HIGH STRAIN: {fmt_temp(B, ss.get('units','metric'))} – {fmt_temp(C, ss.get('units','metric'))}")
    st.write(f"⛔ WITHDRAWAL: ≥ {fmt_temp(C, ss.get('units','metric'))}")

    st.markdown("**HSP (Heat-Strain Profile):**")
    st.write("🟢 **HSP < 0.80** → Cooling capacity exceeds heat load (good margin)")
    st.write("🟠 **0.80 – 0.99** → Marginal heat balance (close monitoring)")
    st.write("🔴 **HSP ≥ 1.00** → Heat gain likely exceeds heat loss (rapid risk escalation)")

    st.markdown("**What HSP means in practice:**")
    st.write("• Environmental HSP = before worksite additional factors")
    st.write("• Operational HSP = after worksite additional factors")
    st.write("• Lower HSP = better cooling margin")

    st.caption("Tip: On phones, the sidebar is hidden automatically. All key references are here.")


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

# Detect a display-unit change before rendering the environmental widgets.
# This prevents stale hidden widget keys (e.g., old Imperial values) from overwriting
# the canonical internal metric values when the user toggles units.
_prev_units_for_sync = ss.get("_last_display_units", ss.get("units", "metric"))
_new_units = "metric" if unit_choice_main.startswith("Metric") else "imperial"

# Preserve the current visible widget values into canonical metric storage before switching.
# Then repopulate the newly visible widget keys from the canonical values.
if _new_units != _prev_units_for_sync:
    try:
        if _prev_units_for_sync == "metric":
            if "env_db_c_input" in ss: ss["db_c"] = float(ss["env_db_c_input"])
            if "env_ws_ms_input" in ss: ss["ws_ms"] = float(ss["env_ws_ms_input"])
            if "env_p_kpa_input" in ss: ss["p_kpa"] = float(ss["env_p_kpa_input"])
            if "env_gt_c_input" in ss: ss["gt_c"] = float(ss["env_gt_c_input"])
        else:
            if "env_db_f_input" in ss: ss["db_c"] = float(f_to_c(ss["env_db_f_input"]))
            if "env_ws_mph_input" in ss: ss["ws_ms"] = float(mph_to_ms(ss["env_ws_mph_input"]))
            if "env_p_inhg_input" in ss: ss["p_kpa"] = float(inhg_to_kpa(ss["env_p_inhg_input"]))
            if "env_gt_f_input" in ss: ss["gt_c"] = float(f_to_c(ss["env_gt_f_input"]))
        if "env_rh_pct_input" in ss: ss["rh_pct"] = float(ss["env_rh_pct_input"])

        ss["env_db_c_input"] = float(hart_clamp_value("db_c", ss.get("db_c", 32.0)))
        ss["env_db_f_input"] = float(c_to_f(hart_clamp_value("db_c", ss.get("db_c", 32.0))))
        ss["env_ws_ms_input"] = float(hart_clamp_value("ws_ms", ss.get("ws_ms", 1.0)))
        ss["env_ws_mph_input"] = float(ms_to_mph(hart_clamp_value("ws_ms", ss.get("ws_ms", 1.0))))
        ss["env_p_kpa_input"] = float(hart_clamp_value("p_kpa", ss.get("p_kpa", 101.3)))
        ss["env_p_inhg_input"] = float(kpa_to_inhg(hart_clamp_value("p_kpa", ss.get("p_kpa", 101.3))))
        ss["env_gt_c_input"] = float(hart_clamp_value("gt_c", ss.get("gt_c", ss.get("db_c", 32.0) + 3.0)))
        ss["env_gt_f_input"] = float(c_to_f(hart_clamp_value("gt_c", ss.get("gt_c", ss.get("db_c", 32.0) + 3.0))))
        ss["env_dirty"] = True
    except Exception:
        pass

ss["units"] = _new_units
ss["_last_display_units"] = _new_units

st.markdown(
    "<div style='color:#25384a;font-weight:650; line-height:1.5; margin:0.20rem 0 0.35rem 0;'>"
    "Enter site measured values in the <b>Environmental Inputs</b> fields to replace the default values; "
    "otherwise, retrieve local weather (Open-Meteo) through the <b>Location Search</b> function."
    "</div>",
    unsafe_allow_html=True
)

# -------------------------
# Reset Assessment (main page, confirmed)
# -------------------------
st.markdown("---")
if st.button("🔄 Reset Assessment (Clear Current Inputs & Results)", key="main_reset_btn"):
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
                "env_db_c_input","env_db_f_input","env_rh_pct_input","env_ws_ms_input","env_ws_mph_input","env_p_kpa_input","env_p_inhg_input","env_gt_c_input","env_gt_f_input","_last_display_units",
                # Baseline / adjusted WBGT
                "wbgt_raw_c","wbgt_base_c","wbgt_base_frozen","wbgt_eff_c",
                # Exposure adjustments selections + totals
                "adj_ppe_pcls","adj_enclosure_c","adj_radiant_c","adj_solar_c","adj_misc_c",
                "penalties_applied","total_penalty_c",
                # HSP / ECCE computed values and status flags
                "mwl_env_sig","mwl_env_prev","hsp_calib_ready","ecce_raw","ecce_cap","ecce_env_used","ecce_operational_used","hsp_capacity",
                # Optional instrument field
                "wbgt_instr",
                # Any cached geo results
                "geo_results","geo_query_sig","place_query","place_label",
                # Audit/history state — reset starts a clean saved-history table
                "audit_log", "save_counter", "last_saved_id",
                # Diagnostics (safe to clear)
                "wb_mwl_c",
            ]
            for k in keys_to_clear:
                if k in ss:
                    del ss[k]

            # Return to the appropriate entry point after reset
            if ss.get("app_mode") == "professional":
                ss["landing_open"] = False
            elif ss.get("app_mode") == "field":
                ss["landing_open"] = True

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
    units_now = ss.get("units", "metric")
    unit_label = "Metric (°C, m/s, kPa)" if units_now == "metric" else "Imperial (°F, mph, inHg)"

    st.markdown("""
    <div style="font-weight:800; margin-bottom:0.10rem;">Display Units</div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="sidebar-selected-box">
        <div class="selected-caption">Currently selected</div>
        <div class="selected-value">{unit_label}</div>
    </div>
    <div class="sidebar-note">Change units from the main screen.</div>
    """, unsafe_allow_html=True)

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

    # Compact legend: avoids sidebar clipping on smaller laptop screens
    st.markdown(f"""
    <div class="sidebar-band-legend">
      <div class="band-title">WBGT Policy Band Reference</div>
      <div>🟢 <b>LOW RISK</b></div>
      <div class="band-thr">&lt; {fmt_temp(A, ss['band_units'])}</div>
      <div>🟠 <b>CAUTION</b></div>
      <div class="band-thr">{fmt_temp(A, ss['band_units'])} – {fmt_temp(B, ss['band_units'])}</div>
      <div>🔴 <b>HIGH STRAIN</b></div>
      <div class="band-thr">{fmt_temp(B, ss['band_units'])} – {fmt_temp(C, ss['band_units'])}</div>
      <div>⛔ <b>WITHDRAWAL</b></div>
      <div class="band-thr">≥ {fmt_temp(C, ss['band_units'])}</div>
    </div>
    """, unsafe_allow_html=True)

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

st.markdown("<br>", unsafe_allow_html=True)
st.markdown("## 🌡 Environmental Inputs")

# -----------------------------------------
# Retrieve live weather
# -----------------------------------------


fetch_btn = st.button(
    "🌤 Retrieve Local Weather",
    use_container_width=True,
    key="fetch_local_weather_btn"
)

# fetch_btn = False
# if ss.get("app_mode") != "field":
  #  fetch_btn = st.button("🌤 Retrieve Local Weather")

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

        # Keep the manual-input widget keys synchronized with fetched weather.
        # Streamlit reruns the script after every widget edit; using dedicated
        # widget keys prevents manual entries from being overwritten by startup
        # defaults on the next rerun.
        ss["env_db_c_input"] = float(ss["db_c"])
        ss["env_db_f_input"] = float(c_to_f(ss["db_c"]))
        ss["env_rh_pct_input"] = float(ss["rh_pct"])
        ss["env_ws_ms_input"] = float(ss["ws_ms"])
        ss["env_ws_mph_input"] = float(ms_to_mph(ss["ws_ms"]))
        ss["env_p_kpa_input"] = float(ss["p_kpa"])
        ss["env_p_inhg_input"] = float(kpa_to_inhg(ss["p_kpa"]))
        ss["env_gt_c_input"] = float(ss["gt_c"])
        ss["env_gt_f_input"] = float(c_to_f(ss["gt_c"]))

        # Flag environment changed → forces baseline reset in Block 5
        ss["env_dirty"] = True
        ss["weather_fetched"] = True
        ss["weather_provider"] = "Open-Meteo"

        st.success(
            f"Weather loaded from Open-Meteo ({datetime.utcnow().strftime('%H:%M UTC')})"
        )

# -----------------------------------------
# Manual input fields (unit aware)
# -----------------------------------------
# IMPORTANT STREAMLIT STATE FIX:
# Use stable widget keys separate from the canonical calculation variables.
# Without explicit keys, Streamlit can recreate number inputs on rerun and the
# app may revert to startup defaults (DB 32, RH 60, WS 1, GT 35) after pressing
# Enter. The canonical ss["db_c"], ss["rh_pct"], ss["ws_ms"], ss["p_kpa"],
# and ss["gt_c"] are updated only from these persistent widget keys.
ss_default("env_db_c_input", float(hart_clamp_value("db_c", ss.get("db_c", 32.0))))
ss_default("env_db_f_input", float(c_to_f(hart_clamp_value("db_c", ss.get("db_c", 32.0)))))
ss_default("env_rh_pct_input", float(hart_clamp_value("rh_pct", ss.get("rh_pct", 60.0))))
ss_default("env_ws_ms_input", float(hart_clamp_value("ws_ms", ss.get("ws_ms", 1.0))))
ss_default("env_ws_mph_input", float(ms_to_mph(hart_clamp_value("ws_ms", ss.get("ws_ms", 1.0)))))
ss_default("env_p_kpa_input", float(hart_clamp_value("p_kpa", ss.get("p_kpa", 101.3))))
ss_default("env_p_inhg_input", float(kpa_to_inhg(hart_clamp_value("p_kpa", ss.get("p_kpa", 101.3)))))
ss_default("env_gt_c_input", float(hart_clamp_value("gt_c", ss.get("gt_c", ss.get("db_c", 32.0) + 3.0))))
ss_default("env_gt_f_input", float(c_to_f(hart_clamp_value("gt_c", ss.get("gt_c", ss.get("db_c", 32.0) + 3.0)))))

col1, col2, col3, col4, col5 = st.columns(5)

# --- Dry bulb ---
with col1:
    if ss["units"] == "metric":
        st.number_input("Dry Bulb (°C)", min_value=-20.0, max_value=90.0, step=0.1, key="env_db_c_input")
        ss["db_c"] = float(ss["env_db_c_input"])
        ss["env_db_f_input"] = float(c_to_f(ss["db_c"]))
    else:
        st.number_input("Dry Bulb (°F)", min_value=float(c_to_f(-20.0)), max_value=float(c_to_f(90.0)), step=0.1, key="env_db_f_input")
        ss["db_c"] = float(f_to_c(ss["env_db_f_input"]))
        ss["env_db_c_input"] = float(ss["db_c"])

# --- RH ---
with col2:
    st.number_input("RH (%)", min_value=0.0, max_value=100.0, step=1.0, key="env_rh_pct_input")
    ss["rh_pct"] = float(ss["env_rh_pct_input"])

# --- Wind ---
with col3:
    if ss["units"] == "metric":
        st.number_input("Wind (m/s)", min_value=0.0, max_value=70.0, step=0.1, key="env_ws_ms_input")
        ss["ws_ms"] = float(ss["env_ws_ms_input"])
        ss["env_ws_mph_input"] = float(ms_to_mph(ss["ws_ms"]))
    else:
        st.number_input("Wind (mph)", min_value=0.0, max_value=float(ms_to_mph(70.0)), step=0.1, key="env_ws_mph_input")
        ss["ws_ms"] = float(mph_to_ms(ss["env_ws_mph_input"]))
        ss["env_ws_ms_input"] = float(ss["ws_ms"])

# --- Pressure ---
with col4:
    if ss["units"] == "metric":
        st.number_input("Pressure (kPa)", min_value=60.0, max_value=110.0, step=0.1, key="env_p_kpa_input", help="Default is sea level (~101.3 kPa). Enter local pressure if known or if working at higher elevation; otherwise leave default.")
        ss["p_kpa"] = float(ss["env_p_kpa_input"])
        ss["env_p_inhg_input"] = float(kpa_to_inhg(ss["p_kpa"]))
    else:
        st.number_input("Pressure (inHg)", min_value=float(kpa_to_inhg(60.0)), max_value=float(kpa_to_inhg(110.0)), step=0.05, key="env_p_inhg_input", help="Default is sea level (~29.92 inHg). Enter local pressure if known; otherwise leave default.")
        ss["p_kpa"] = float(inhg_to_kpa(ss["env_p_inhg_input"]))
        ss["env_p_kpa_input"] = float(ss["p_kpa"])

with col5:
    if ss["units"] == "metric":
        st.number_input("Globe Temp (°C)", min_value=-40.0, max_value=120.0, step=0.1, key="env_gt_c_input")
        ss["gt_c"] = float(ss["env_gt_c_input"])
        ss["env_gt_f_input"] = float(c_to_f(ss["gt_c"]))
    else:
        st.number_input("Globe Temp (°F)", min_value=float(c_to_f(-40.0)), max_value=float(c_to_f(120.0)), step=0.1, key="env_gt_f_input")
        ss["gt_c"] = float(f_to_c(ss["env_gt_f_input"]))
        ss["env_gt_c_input"] = float(ss["gt_c"])

# Validate environmental inputs before baseline/WBGT/HSP calculations.
_val_errors, _val_warnings = hart_validate_all_inputs(
    ss.get("db_c"), ss.get("rh_pct"), ss.get("gt_c"), ss.get("ws_ms"), ss.get("p_kpa"),
    ss.get("wbgt_instr", 0.0), ss.get("twl_measured", 0.0)
)
_val_warnings.extend(hart_add_context_validation_warnings(
    ss.get("db_c"), ss.get("rh_pct"), ss.get("gt_c"), ss.get("ws_ms"), ss.get("p_kpa"),
    weather_fetched=bool(ss.get("weather_fetched", False))
))
hart_show_validation_messages(_val_errors, _val_warnings)

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


# ======================================================================
# BLOCK 5 — OPTIONAL LOOKUP (Baseline WBGT + Instrument Reference)
# ======================================================================

with st.expander("🧭 Optional Lookup (Baseline WBGT + Instrument Reference)", expanded=False):

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
    st.subheader("Computed Baseline (Before additional worksite factors)")
    c1, c2, c3 = st.columns(3)
    c1.metric("WBGT Baseline (Frozen)", fmt_temp(ss["wbgt_base_frozen"], ss["units"]))
    c2.metric("Globe Temp", fmt_temp(gt_c, ss["units"]))
    c3.metric(
        "Wind",
        f"{ws_ms:.1f} m/s" if ss["units"] == "metric" else f"{ms_to_mph(ws_ms):.1f} mph"
    )
    with st.expander("Advanced Environmental Details (includes Wet-Bulb)", expanded=False):
        st.write(f"**Dry Bulb (DB):** {fmt_temp(db_c, ss['units'])}")
        st.write(f"**Relative Humidity (RH):** {rh:.0f} %")
        st.write(f"**Estimated psychrometric wet-bulb from DB/RH (not wind-adjusted):** {fmt_temp(twb_c, ss['units'])}")
        st.write(f"**Globe Temperature (GT):** {fmt_temp(gt_c, ss['units'])}")
        st.write(f"**Wind Speed (WS):** {ws_ms:.2f} m/s" if ss['units'] == 'metric' else f"**Wind Speed (WS):** {ms_to_mph(ws_ms):.2f} mph")
        st.caption("This wet-bulb estimate is derived from DB/RH and is not wind-adjusted. Routine supervisor decisions should use WBGT/HSP guidance and site policy.")

    st.markdown("---")
    st.markdown("**Instrument Reference (Optional)**")
    st.markdown(
        "<span style='color:#222;'>Optional: Enter instrument TWL or WBGT values for side-by-side reference. These values do <b>not</b> change the modelled baseline or worksite additional factors.</span>",
        unsafe_allow_html=True
    )

    colA, colB = st.columns(2)
    with colA:
        ss["twl_measured"] = st.number_input(
            "Instrument TWL (W/m²)",
            min_value=0.0,
            value=float(hart_clamp_value("twl_measured", ss.get("twl_measured", 0.0))),
            max_value=500.0,
            step=5.0
        )
    with colB:
        ss["wbgt_instr"] = st.number_input(
            "Instrument WBGT (°C)",
            min_value=0.0,
            value=float(hart_clamp_value("wbgt_instr", ss.get("wbgt_instr", 0.0))),
            max_value=66.0,
            step=0.1
        )

# Flag if calibration is available (for Block 7 HSP display)
ss["hsp_calib_ready"] = bool(ss.get("twl_measured", 0.0) > 0 and ss.get("wbgt_instr", 0.0) > 0)


# ======================================================================
# Task and metabolic-rate refinement layer (v1.9.57)
# ======================================================================
st.markdown("## 🧰 Task & Metabolic Rate")
st.caption("Optional refinement layer. The 350 W setting preserves the previous ACGIH branch behavior. Apply clothing/PPE burden once in the Worksite Additional Factors section below.")

colT1, colT2 = st.columns([1.45, 0.85])
with colT1:
    task_choice = st.selectbox(
        "Primary task / workload",
        list(TASK_METABOLIC_PRESETS_W.keys()),
        index=3,
        key="task_metabolic_choice",
        help="Select the closest sustained task. Use manual override if you have a better site estimate."
    )
with colT2:
    manual_met = st.number_input(
        "Manual metabolic rate (W)",
        min_value=0.0,
        max_value=700.0,
        value=float(ss.get("manual_metabolic_w", 0.0)),
        step=5.0,
        key="manual_metabolic_w",
        help="Optional. Enter 0 to use the selected task category."
    )

selected_met_w = float(manual_met) if float(manual_met) > 0 else float(TASK_METABOLIC_PRESETS_W[task_choice])
ss["metabolic_w"] = selected_met_w
ss["metabolic_task"] = task_choice

# Clothing/PPE burden is applied only once in Worksite Additional Factors.
# These zero values are retained for backwards compatibility with downstream functions.
ss["clothing_cav_c"] = 0.0
ss["clothing_capacity_w"] = 0.0
ss["clothing_note"] = "Clothing/PPE burden is handled in Worksite Additional Factors below."

met_multiplier = metabolic_hsp_multiplier(selected_met_w)
st.info(
    f"Selected workload: **{selected_met_w:.0f} W** | HSP task multiplier: **{met_multiplier:.2f}** | "
    "Apply clothing/PPE burden below under **Worksite Additional Factors**."
)
st.caption(
    "Workload increases body heat production (HSP numerator). Cooling Capacity is determined separately by environmental conditions. "
    "Clothing/PPE is entered only once in the Worksite Additional Factors section."
)

# ======================================================================
# Exposure adjustments (°C internal truth)
# ======================================================================

PPE_PRESETS     = {"None": 0.0, "Light": 1.0, "Moderate": 2.0, "Heavy": 3.0}
VEHICLE_PRESETS = {"None": 0.0, "Open": 1.0, "Enclosed": 2.0, "Poorly ventilated": 3.0}
RADIANT_PRESETS = {"None": 0.0, "Hot surfaces": 2.0, "Direct radiant": 4.0, "Extreme radiant": 5.0}
ADHOC_PRESETS   = {"None": 0.0, "Minor": 1.0, "Moderate": 2.0, "Severe": 4.0}

st.markdown("## 🔥 Worksite Additional Factors (PPE, Enclosure, Radiant/Solar Heat, Other Site Factors)")

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
    st.subheader("PPE / Clothing")
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
    st.subheader("Radiant / Solar Heat")
    labels = {f"{k} (+{delta_label(v)})": float(v) for k, v in RADIANT_PRESETS.items()}
    choice = st.selectbox("", list(labels.keys()), key="rad_preset")
    preset_c = float(labels[choice])
    _ensure_number_follows_preset("rad_preset", "rad_delta_input", preset_c)
    ss["pen_rad_c"] = number_delta("rad_delta_input")

# ---------------- Adhoc ----------------
with col4:
    st.subheader("Other Site Factors")
    labels = {f"{k} (+{delta_label(v)})": float(v) for k, v in ADHOC_PRESETS.items()}
    choice = st.selectbox("", list(labels.keys()), key="adhoc_preset")
    preset_c = float(labels[choice])
    _ensure_number_follows_preset("adhoc_preset", "adhoc_delta_input", preset_c)
    ss["pen_adhoc_c"] = number_delta("adhoc_delta_input")

# ======================================================================
# BLOCK 5B — APPLY PENALTIES SAFELY (unit-aware, clamped, no negatives)
# ======================================================================

st.markdown("## 🚀 Apply Worksite Additional Factors & Compute")
st.caption("Complete environmental inputs, then apply worksite additional factors and compute to display the heat status, supervisor actions, and snapshot numbers.")

if st.button("Apply Worksite Additional Factors & Compute"):

    wbgt_base_c = ss.get("wbgt_base_frozen", None)  # use frozen baseline

    if wbgt_base_c is None:
        st.error("No frozen baseline WBGT available — set environmental inputs first.")
    else:
        # Values coming from UI are stored internally in °C
        ppe_c  = max(float(ss.get("pen_clo_c", 0.0)), float(ss.get("clothing_cav_c", 0.0)))
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

        # Adjusted WBGT (°C)
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
            f"Adjusted WBGT = {wbgt_display}. "
            "Scroll down for Heat-Stress Classification."
        )


# ======================================================================
# BLOCK 6 — NIOSH / OSHA WBGT & Wet-Bulb Thresholds (with Acclimatization)
# ======================================================================

with st.expander("🎯 Heat-Stress Thresholds & Acclimatization (Tap To Expand)", expanded=False):

    # Worker acclimatization toggle
    accl_status = st.radio(
        "Worker acclimatization status",
        ["Acclimatized", "Not acclimatized"],
        horizontal=True,
        key="accl_status",
    )

    # ---------------------------
    # NIOSH/OSHA-style WBGT base cut-points (°C)
    # Public GitHub branch keeps these thresholds intentionally separate from
    # the ACGIH-discussion branch. HSP/ECCE logic is shared; only WBGT policy
    # banding differs.
    # ---------------------------
    A_base = 29.0   # Info / low-risk boundary
    B_base = 32.0   # Caution boundary
    C_base = 35.0   # Withdrawal boundary

    # Conservative non-acclimatized shift
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

    # Legacy keys used by Block 7 and sidebar display
    ss["thr_A_c"] = A
    ss["thr_B_c"] = B
    ss["thr_C_c"] = C

    # Remove ACGIH-branch severity ladder keys if present from a previous run/session.
    # This prevents downstream code from accidentally reading OAL/OEL values in the
    # public GitHub threshold branch.
    for _k in ("thr_OAL_c", "thr_OEL_c", "thr_OEL3_c", "thr_OEL6_c"):
        ss.pop(_k, None)

    # ---------------------------
    # Wet-Bulb physiological bands
    # (used by ECCE + HSP ceiling logic)
    # ---------------------------
    ss["wb_safe_c"]     = 26.0 + wb_shift   # sweat evaporation effective
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

    st.caption(
        "Public GitHub branch: WBGT policy banding follows the existing NIOSH/OSHA-style "
        "guideline cut-points. HSP/ECCE is a shared cooling-capacity cross-check and does not "
        "relax the WBGT policy band."
    )

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
            "Values approximate NIOSH/OSHA-style WBGT guidance and physiological wet-bulb limits "
            "for acclimatized industrial workers. Site policy remains controlling."
        )
    else:
        st.caption(
            "All WBGT and Wet-Bulb thresholds are shifted lower for **Non-Acclimatized** workers "
            "to provide a conservative safety margin."
        )
# ======================================================================
# BLOCK 7 — HEAT STRESS RISK CLASSIFICATION (WBGT guideline + HSP + Wet-Bulb)
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
.kpi-grid{ display:grid; grid-template-columns: 1fr 1fr; gap:0.6rem; }
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

/* keep Block 7 focused on cards and snapshot layout; landing-page button styling lives in the global CSS block */
</style>
""", unsafe_allow_html=True)

st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("## 🧭 Heat-Stress Snapshot (WBGT Guideline + HSP)")
st.markdown(
    "<div style='color:#2f3e4e; font-weight:600; margin-top:0.25rem; margin-bottom:0.35rem;'>"
    "HART shows when heat risk is increasing and what to do next. "
    "It does not replace supervisor judgment or site procedures."
    "</div>",
    unsafe_allow_html=True
)
# -----------------------------
# WBGT guideline banding (4-level)
# -----------------------------
def _wbgt_band_from_eff(wbgt_eff_c, A, B, C):
    """NIOSH/OSHA-style public GitHub WBGT guideline banding.
    LOW <A; CAUTION <B; HIGH STRAIN <C; WITHDRAWAL >=C.
    HSP/ECCE remains an additional cooling-capacity cross-check only.
    """
    if wbgt_eff_c < A:
        return ("🟢", "LOW RISK", "Routine work acceptable. Maintain hydration and routine supervision.", 0, "#2ecc71")
    if wbgt_eff_c < B:
        return ("🟠", "CAUTION", "Increase supervision. Maintain hydration and follow site-approved work–rest practices and heat-stress control measures.", 1, "#f39c12")
    if wbgt_eff_c < C:
        return ("🔴", "HIGH STRAIN", "Reduce heat exposure. Move to cooler or shaded areas where feasible. Apply site-approved work–rest controls. Support cooling and maintain close worker monitoring.", 2, "#e74c3c")
    return ("⛔", "WITHDRAWAL", "Avoid routine work. Only essential tasks should proceed under site policy, with strict controls and close monitoring.", 3, "#800000")

wbgt_eff = ss.get("wbgt_eff_c", None)
wbgt_base = ss.get("wbgt_base_frozen", None)

if ss.get("app_mode") == "field" and not ss.get("penalties_applied", False):
    st.info("Complete environmental inputs, then apply worksite additional factors and compute to see the risk band and supervisor actions.")
    st.stop()

if wbgt_eff is None:
    st.info("Press **Apply Additional Factors & Compute** to calculate Adjusted WBGT, HSP, and guidance.")
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
        wb_phys_icon, wb_phys_msg, wb_phys_color = "🟢", "Cooling Effective (Evaporation Adequate)", "#2ecc71"
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

    # Tuned smooth ECCE cap. No step changes; additional factors remain unchanged.
    mwl_cap = smooth_mwl_capacity_cap(wbgt_env=wbgt_env, gt_c=gt, ws_ms=ws, db_c=db)
    ss["ecce_raw"] = float(mwl_raw)
    ss["ecce_cap"] = float(mwl_cap)

    env_sig = (round(db,2), round(rh,2), round(ws,2), round(gt,2), round(wbgt_env,2), round(pen_c,2))
    if ss.get("mwl_env_sig") != env_sig:
        ss["mwl_env_sig"] = env_sig
        ss.pop("mwl_env_prev", None)

    # GitHub-matched ECCE handling: use current raw estimate and smooth cap only.
    # Do not carry a lower prior ECCE forward; otherwise HSP can appear sticky after edits.
    # The value actually used for HSP is the lower of the raw ECCE estimate and
    # the smooth environmental ceiling. Older GitHub display sections sometimes
    # showed the ceiling while HSP used the lower value, creating apparent
    # ECCE/HSP denominator mismatch. Here, display and denominator are aligned.
    mwl_env = min(float(mwl_raw), float(mwl_cap))
    ss["mwl_env_prev"] = mwl_env
    ss["ecce_env_used"] = float(mwl_env)

    mwl_op = float(apply_capacity_penalties(
        mwl_env,
        ppe_c=max(float(ss.get("pen_clo_c", 0) or 0), float(ss.get("clothing_cav_c", 0) or 0)),
        veh_c=float(ss.get("pen_veh_c", 0) or 0),
        rad_c=float(ss.get("pen_rad_c", 0) or 0),
        adh_c=float(ss.get("pen_adhoc_c", 0) or 0),
    ))
    # Additional capacity burden from selected clothing library (W/m²), kept separate
    # from the °C-style PPE adjustment for transparency.
    mwl_op = max(float(ss["ECCE_MIN"]), mwl_op - float(ss.get("clothing_capacity_w", 0.0) or 0.0))
    ss["ecce_operational_used"] = float(mwl_op)

    # GitHub-matched HSP calculation: direct denominator = displayed operational ECCE.
    # This disables the extra severe-end denominator softening used in the ACGIH branch.
    hsp_capacity = max(1.0, mwl_op)
    ss["hsp_capacity"] = hsp_capacity
    met_w = float(ss.get("metabolic_w", 350.0) or 350.0)
    hsp_met_multiplier = metabolic_hsp_multiplier(met_w)
    ss["hsp_met_multiplier"] = hsp_met_multiplier
    hsp = (wbgt_op * 200.0 * hsp_met_multiplier) / (hsp_capacity * 30.0)
    ss["hsp"] = hsp

    if hsp < 0.8:
        h_icon, h_band, h_color = "🟢", "Adequate Cooling Margin Available", "#2ecc71"
    elif hsp < 1.0:
        h_icon, h_band, h_color = "🟠", "Cooling Margin Narrowing", "#f39c12"
    else:
        h_icon, h_band, h_color = "🔴", "Cooling Margin Becoming Inadequate", "#e74c3c"

# -----------------------------
# Override logic (conservative): policy first; HSP only if more protective
# -----------------------------
use_phys = st.checkbox(
    "Use HSP to escalate risk only when it is more protective than the WBGT guideline",
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
# ------------------------------------------------------------
# HART Decision Layer (compact supervisory guidance)
# ------------------------------------------------------------
advice = hart_supervisory_advice(
    ss.get("final_risk"),
    ss.get("hsp", None)
)

# Duplicate compact supervisory block removed in v1.9.74.
# The visible Supervisor Decision Banner below remains the always-visible field layer;
# detailed action/controls/monitoring text remains inside this expander.

with st.expander("🧭 View Detailed Supervisory Guidance", expanded=False):
    st.markdown(f"""
    <div class="sa-card" style="border-left:6px solid #d97706; margin-top:0.20rem;">
      <div class="sa-title">{advice["headline"]}</div>
      <ul>
        <li><b>Action:</b> {advice["action"]}</li>
        <li><b>Controls:</b> {advice["controls"]}</li>
        <li><b>Monitoring:</b> {advice["monitoring"]}</li>
      </ul>
      <div style="margin-top:6px; font-size:0.88rem; color:#b91c1c;">
        <b>Emergency trigger:</b> {advice["emergency"]}
      </div>
    </div>
    """, unsafe_allow_html=True)

render_consequence_projection(
    hsp if hsp is not None else ss.get("hsp", None),
    ss.get("final_risk", ""),
    float(ss.get("metabolic_w", 350.0) or 350.0),
    float(ss.get("wbgt_eff_c", wbgt_op) if ss.get("wbgt_eff_c", None) is not None else wbgt_op),
    float(ss.get("pen_clo_c", 0.0) or 0.0),
)
# -----------------------------
# KPI display label
# -----------------------------
# Keep wbgt_policy_band as the internal scientific/policy key, but do not show it
# beside the field-friendly label in the main UI.
wbgt_policy_display_map = {
    "LOW": "LOW — NORMAL OPERATIONS",
    "CAUTION": "CAUTION — MONITOR CONDITIONS",
    "MODERATE": "MODERATE — CONTROL REQUIRED",
    "HIGH STRAIN": "HIGH — TIGHT CONTROL ZONE",
    "WITHDRAWAL": "EXTREMELY HIGH — ESSENTIAL WORK ONLY",
}
wbgt_policy_display = wbgt_policy_display_map.get(wbgt_policy_band, wbgt_policy_band)

hsp_value_disp = f"{hsp:.2f}" if hsp is not None else "—"
hsp_sub = f"{h_icon} {h_band}" if hsp is not None else "Baseline WBGT not available (HSP not computed)"
hsp_foot = f"ECCE — Estimated Cooling Capacity of the Environment: {mwl_op:.0f} W/m²; HSP denominator: {ss.get('hsp_capacity', mwl_op):.0f} W/m²; Task: {float(ss.get('metabolic_w',350.0)):.0f} W; workload multiplier: {float(ss.get('hsp_met_multiplier', 1.0)):.2f}" if mwl_op is not None else "Provide baseline WBGT to enable HSP."
mwl_loss = (float(mwl_env) - float(mwl_op)) if (mwl_env is not None and mwl_op is not None) else None

# -----------------------------
# Sticky Supervisor Action Bar (COMPACT; NO emergency line)
# -----------------------------
risk_icon_map = {"LOW":"🟢","CAUTION":"🟠","MODERATE":"🟡","HIGH STRAIN":"🔴","WITHDRAWAL":"⛔"}
risk_display_map = {
    "LOW": "LOW — NORMAL OPERATIONS",
    "CAUTION": "CAUTION — MONITOR CONDITIONS",
    "MODERATE": "MODERATE — CONTROL REQUIRED",
    "HIGH STRAIN": "HIGH — TIGHT CONTROL ZONE",
    "WITHDRAWAL": "EXTREMELY HIGH — ESSENTIAL WORK ONLY",
}

def display_risk_label(risk_key: str) -> str:
    """Return the field-friendly public label while preserving internal risk keys."""
    return risk_display_map.get((risk_key or "").strip().upper(), risk_key or "—")

risk_icon = risk_icon_map.get(final_risk, "⚪")
current_label = f"Current: {risk_icon} {display_risk_label(final_risk)} • {wbgt_disp}"

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
# Shared display labels (used by actions + summary + snapshot)
# -----------------------------
label = final_risk  # internal key retained for logic/backward compatibility
public_label = display_risk_label(final_risk)
_label = (label or "").strip().upper()

if _label.startswith("LOW"):
    _level = "LOW"
elif _label.startswith("CAUTION"):
    _level = "CAUTION"
elif _label.startswith("MODERATE"):
    _level = "CAUTION"
else:
    _level = "HIGH"

# Fallback-safe display values (avoid NameError if upstream variable name changes)
wbgt_disp = locals().get("wbgt_disp", None) or locals().get("wbgt_eff_disp", None) or locals().get("wbgt_eff_display", None) or "—"
hsp_value_disp = locals().get("hsp_value_disp", None) or locals().get("hsp_disp", None) or "—"

# Default summary line (kept constant & field-friendly)
summary_line = locals().get("summary_line", None) or "Follow site HSE policy / SOP for WBGT- or TWL-based controls. Use HSP as an additional cooling-margin indicator."

# -----------------------------
# Control-panel decision banner
# -----------------------------
decision_title = ""
decision_message = ""
if _label.startswith("LOW"):
    decision_title = "🟢 LOW — NORMAL OPERATIONS"
    decision_message = "Maintain hydration and routine supervision."
elif _label.startswith("CAUTION"):
    decision_title = "🟠 CAUTION — MONITOR CONDITIONS"
    decision_message = "Enforce hydration and follow site-approved work–rest practices."
elif _label.startswith("MODERATE"):
    decision_title = "🟡 MODERATE — CONTROL REQUIRED"
    decision_message = "Moderate heat stress. Increase vigilance, use site-approved rest/cooling practices, and reduce exposure where feasible."
elif _label.startswith("HIGH"):
    decision_title = "🔴 HIGH — TIGHT CONTROL ZONE"
    decision_message = "Reduce heat exposure. Apply site-approved work–rest controls. Provide cooling opportunities and maintain close worker monitoring."
else:
    decision_title = "⛔ EXTREMELY HIGH — ESSENTIAL WORK ONLY"
    decision_message = "Avoid routine work. Only essential tasks should proceed under site policy, with strict heat controls and continuous monitoring."
st.markdown(
    "<div style='color:#3a3a3a; font-weight:600; margin-top:0.30rem;'>"
    "This is not an automatic stop-work rule. Only essential work should proceed under strict controls and supervision when this level is reached."
    "</div>",
    unsafe_allow_html=True
)
st.markdown("### 🎛 Supervisor Decision Banner")
if _label.startswith("LOW"):
    st.success(f"**{decision_title}**\n\n{decision_message}\n\nAdjusted WBGT: {wbgt_disp} | HSP: {hsp_value_disp}")
elif _label.startswith("CAUTION"):
    st.warning(f"**{decision_title}**\n\n{decision_message}\n\nAdjusted WBGT: {wbgt_disp} | HSP: {hsp_value_disp}")
else:
    st.error(f"**{decision_title}**\n\n{decision_message}\n\nAdjusted WBGT: {wbgt_disp} | HSP: {hsp_value_disp}")

# -----------------------------
# HSP graduated threshold advisory (current band only)
# -----------------------------
render_hsp_threshold_advisory(hsp if hsp is not None else ss.get("hsp", None))

# -----------------------------
# Supervisor actions FIRST (field-friendly ordering)
# -----------------------------
st.markdown(
    "<div style='color:#2f3e4e; font-weight:600; margin-bottom:0.25rem;'>"
    "Use these actions as guidance. Follow site HSE policy / SOP for WBGT- or TWL-based controls. Use HSP as an additional cooling-margin indicator."
    "</div>",
    unsafe_allow_html=True
)

st.markdown("### 👷 Supervisor Actions (Tap To Expand)")

# Helper for bullets
def _bullets(lines):
    return "\n".join([f"- {x}" for x in lines if str(x).strip()])

# Action content by risk
if _label.startswith("LOW"):
    hydration_lines = [
        "Ensure availability of cool potable drinking water",
        "Encourage regular fluid intake aligned with site hydration practices",
        "Reinforce hydration through supervisory prompts (e.g., safe-start / toolbox routines)",
    ]
    workrest_lines = [
        "Continuous self-paced work acceptable where permitted",
        "Follow normal site work–rest practice and routine breaks",
    ]
    cooling_lines = [
        "Shade and airflow preferred for comfort",
        "Encourage use of shaded or cooler areas during normal breaks",
    ]
    monitoring_lines = [
        "Routine observation by supervisor / buddy",
        "Pay attention to new/returning workers and those reporting fatigue",
    ]
elif _label.startswith("CAUTION"):
    hydration_lines = [
        "Reinforce regular fluid intake aligned with site hydration practices",
        "Consider site-approved electrolyte replacement when sweating is heavy or prolonged",
        "Use structured supervisory prompts to support hydration adherence",
    ]
    workrest_lines = [
        "Follow site work–rest practice with rest breaks in shade / cool area",
        "Reduce peak workload; encourage self-pacing",
    ]
    cooling_lines = [
        "Prioritize shade, airflow, and cooler rest areas",
        "Encourage use of site-provided cooling aids where available",
        "Consider fans or air-conditioned recovery areas where feasible",
    ]
    monitoring_lines = [
        "Active checks by supervisor / buddy",
        "Extra attention to new/returning workers and other higher-risk individuals",
        "Encourage early reporting of symptoms or reduced tolerance",
    ]
elif _label.startswith("MODERATE"):
    hydration_lines = [
        "Reinforce regular fluid intake aligned with site hydration practices",
        "Use structured supervisory prompts to support hydration adherence",
        "Consider site-approved electrolyte replacement when sweating is heavy or prolonged",
    ]
    workrest_lines = [
        "Add site-approved work–rest controls; increase recovery opportunities",
        "Reduce peak workload where feasible and encourage self-pacing",
        "Rotate harder tasks among the crew when practical",
    ]
    cooling_lines = [
        "Prioritize shade, airflow, and cooler rest areas",
        "Use site-provided cooling aids where available",
        "Review engineering or administrative controls before continuing prolonged exposure",
    ]
    monitoring_lines = [
        "Increase supervisor/buddy checks; risk is rising",
        "Watch new, returning, unwell, or fatigued workers closely",
        "Stop work and escalate if symptoms appear",
    ]
elif _label.startswith("HIGH"):
    hydration_lines = [
        "Maintain ready access to cool drinking water in recovery areas",
        "Reinforce hydration through structured prompts (e.g., start-of-shift and break-time drinking)",
        "Consider site-approved electrolyte replacement when sweating is heavy or prolonged",
    ]
    workrest_lines = [
        "Use site-approved work–rest controls and enforce recovery breaks",
        "Move to cooler/shaded areas when possible",
        "Reduce physical intensity; rotate workers",
    ]
    cooling_lines = [
        "Use active cooling measures where feasible (fans, A/C, cooled rest areas)",
        "Use site-provided cooling aids where available",
        "Ensure adequate cooling before re-entry when repeated exposure is unavoidable",
    ]
    monitoring_lines = [
        "Maintain close monitoring with frequent symptom checks",
        "Stop work and notify medical/HSE support if symptoms develop",
        "Keep heat-illness response arrangements ready",
    ]
else:  # WITHDRAWAL
    hydration_lines = [
        "Provide frequent hydration at the work location and ensure access to a cool recovery area for structured cooling and observation.",
        "Follow site medical/HSE protocols when sweating continues or repeated unavoidable short exposures occur",
        "Seek medical review if symptoms develop, recovery is delayed, or complaints continue",
    ]
    workrest_lines = [
        "Restrict activity to absolutely essential work only",
        "Avoid routine, non-urgent, or deferrable tasks",
        "Any unavoidable exposure should follow site policy, with the shortest practical exposure and protected recovery in a cool zone between exposure periods",
        "Maintain strong self-pacing and close supervision throughout",
    ]
    cooling_lines = [
        "Provide immediate cooling in the coolest available area",
        "Use active cooling before any unavoidable re-entry if permitted by site policy",
    ]
    monitoring_lines = [
        "Buddy system and close supervisor observation are required",
        "Allow additional recovery time with hydration and cooling support; notify medical/HSE support if symptoms develop or recovery is delayed",
        "Escalate promptly for confusion, collapse, severe cramps, vomiting, or other severe symptoms",
    ]

# Use expanders for compactness. Keep collapsed by default because the same guidance is repeated in the quick-card below.
_expand = False
c1, c2 = st.columns(2)
with c1:
    with st.expander("Hydration", expanded=_expand):
        st.markdown(_bullets(hydration_lines))
    with st.expander("Cooling", expanded=_expand):
        st.markdown(_bullets(cooling_lines))
with c2:
    with st.expander("Work-Rest", expanded=_expand):
        st.markdown(_bullets(workrest_lines))
    with st.expander("Worker Monitoring", expanded=_expand):
        st.markdown(_bullets(monitoring_lines))

# -----------------------------
# Supervisor quick card (exportable summary)
# -----------------------------
st.markdown("### 📋 Supervisor Snapshot — Field Use")

supervisor_guidance_lines = []
for section, lines in [
    ("Hydration", hydration_lines),
    ("Work-Rest", workrest_lines),
    ("Cooling", cooling_lines),
    ("Worker Monitoring", monitoring_lines),
]:
    supervisor_guidance_lines.append(f"{section}:")
    supervisor_guidance_lines.extend([f"  - {x}" for x in lines if str(x).strip()])

wet_bulb_quick = fmt_temp(ss.get("wb_c"), ss.get("units","metric")) if ss.get("wb_c") is not None else "—"

status_label_map = {
    "LOW": "LOW — NORMAL OPERATIONS",
    "CAUTION": "CAUTION — MONITOR CONDITIONS",
    "MODERATE": "MODERATE — CONTROL REQUIRED",
    "HIGH STRAIN": "HIGH — TIGHT CONTROL ZONE",
    "WITHDRAWAL": "EXTREMELY HIGH — ESSENTIAL WORK ONLY",
}

decision_label_map = {
    "LOW": "SAFE FOR ROUTINE WORK",
    "CAUTION": "MONITOR CONDITIONS",
    "MODERATE": "CONTROL REQUIRED",
    "HIGH STRAIN": "TIGHT CONTROL ZONE",
    "WITHDRAWAL": "ESSENTIAL WORK ONLY",
}

status_label = status_label_map.get(final_risk, final_risk)
decision_label = decision_label_map.get(final_risk, decision_title.replace("🟢 ","").replace("🟠 ","").replace("🔴 ","").replace("⛔ ",""))

status_icon_map = {
    "LOW": "🟢",
    "CAUTION": "🟠",
    "MODERATE": "🟡",
    "HIGH STRAIN": "🔴",
    "WITHDRAWAL": "⛔",
}
status_icon = status_icon_map.get(final_risk, "•")

quick_card = (
    f"HART — Heat Assessment & Response Tool\n"
    f"Mode: {'Field Supervisor Mode' if ss.get('app_mode') == 'field' else 'Professional Analysis Mode'}\n"
    f"Build: {APP_VERSION}\n"
    f"{'-'*42}\n"
    f"{status_icon} Current Status: {status_label}\n"
    f"Decision: {decision_label}\n"
    f"Adjusted WBGT: {wbgt_disp}\n"
    f"HSP: {hsp_value_disp}\n"
    f"Wet Bulb: {wet_bulb_quick}\n"
    f"Assessment Time: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
    f"{'-'*42}\n"
    f"Supervisor Guidance\n" + "\n".join(supervisor_guidance_lines) +
    "\n\nFollow site HSE policy / SOP for WBGT- or TWL-based controls. Use HSP as an additional cooling-margin indicator."
)

quick_card_html_lines = [
    f"<div style='font-weight:800;font-size:1.15rem;margin-bottom:0.25rem;'>HART — Heat Assessment &amp; Response Tool</div>",
    f"<div><b>Mode:</b> {'Field Supervisor Mode' if ss.get('app_mode') == 'field' else 'Professional Analysis Mode'} &nbsp;&nbsp; <b>Build:</b> {APP_VERSION}</div>",
    "<hr style='margin:0.45rem 0;'>",
    f"<div style='font-size:1.05rem;font-weight:800;'>{status_icon} <b>Current Status:</b> {status_label}</div>",
    f"<div style='font-size:1.05rem;font-weight:800;'><b>Decision:</b> {decision_label}</div>",
    f"<div><b>Adjusted WBGT:</b> {wbgt_disp} &nbsp;|&nbsp; <b>HSP:</b> {hsp_value_disp} &nbsp;|&nbsp; <b>Wet Bulb:</b> {wet_bulb_quick}</div>",
    f"<div><b>Assessment Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}</div>",
    "<div style='margin-top:0.8rem;font-weight:700;'>Supervisor Guidance</div>",
]
for section, lines in [("Hydration", hydration_lines), ("Work-Rest", workrest_lines), ("Cooling", cooling_lines), ("Worker Monitoring", monitoring_lines)]:
    quick_card_html_lines.append(f"<div style='margin-top:0.35rem;'><b>{section}:</b></div>")
    quick_card_html_lines.append("<ul style='margin-top:0.15rem;'>" + "".join([f"<li>{x}</li>" for x in lines if str(x).strip()]) + "</ul>")
quick_card_html_lines.append("<div style='margin-top:0.65rem;font-size:0.90rem;font-weight:700;'>Follow site HSE policy / SOP for WBGT- or TWL-based controls. Use HSP as an additional cooling-margin indicator.</div>")

st.markdown(
    "<div style='background:#dfeaf6;border-radius:10px;padding:14px 18px;color:#0a4f9b;'>" + "".join(quick_card_html_lines) + "</div>",
    unsafe_allow_html=True,
)
st.download_button(
    label="⬇ Download Quick Card",
    data=quick_card,
    file_name="HART_supervisor_quick_card.txt",
    mime="text/plain",
    use_container_width=True,
)

# -----------------------------
# Consolidated risk summary (mobile-safe, theme-neutral)
# -----------------------------
st.markdown("### 🧾 Risk Summary (Context-Relevant Significance)")

def _risk_box(level: str, body_md: str):
    """Theme-aware summary box that stays readable in dark/light mode (desktop + mobile)."""
    if level == "LOW":
        st.success(body_md)
    elif level == "CAUTION":
        st.warning(body_md)
    else:
        # HIGH STRAIN / WITHDRAWAL
        st.error(body_md)

_title = f"**{public_label}**"
_metrics = f"- **Adjusted WBGT:** {wbgt_disp}\n- **HSP:** {hsp_value_disp}"
_note = f"- {summary_line}" if summary_line else ""

_risk_box(_level, f"{_title}\n\n{_metrics}\n{_note}")

# -----------------------------
# Risk snapshot numbers AFTER actions + summary
# -----------------------------
st.markdown("### 🔢 Heat-Stress Snapshot Numbers")
st.markdown(
f"""
<div class="kpi-grid">

  <div class="kpi-card" style="border-left:7px solid {h_color};">
    <div class="kpi-label">Heat-Strain Profile (HSP)</div>
    <div class="kpi-value">{hsp_value_disp}</div>
    <div class="kpi-sub"><b>{hsp_sub}</b></div>
    <div class="kpi-foot">{hsp_foot}</div>
  </div>

  <div class="kpi-card" style="border-left:7px solid {band_color};">
    <div class="kpi-label">Adjusted WBGT (Guideline)</div>
    <div class="kpi-value">{wbgt_disp}</div>
    <div class="kpi-sub">{icon} <b>{wbgt_policy_display}</b></div>
    <div class="kpi-foot">{wbgt_policy_msg}<br>Worksite additional factors applied: <b>{pen_disp}</b></div>
  </div>

</div>
""",
unsafe_allow_html=True
)

with st.expander("💧 View Wet-Bulb / Evaporation Details", expanded=False):
    st.write(f"**Estimated psychrometric wet-bulb from DB/RH (not wind-adjusted):** {wb_disp}")
    st.write(f"**Wet-Bulb interpretation:** {wb_phys_icon} {wb_phys_msg}")
    st.write(f"• Cooling Effective: WB < {wb1}")
    st.write(f"• Cooling Starting to Limit: {wb1}–{wb2}")
    st.write(f"• Cooling Limited: {wb2}–{wb3}")
    st.write(f"• Cooling Compromised: ≥ {wb3}")
    st.caption("This value is hidden from the main supervisor snapshot to reduce confusion. It remains available for IH/OH technical review.")

with st.expander("📘 View HSP Field Guide", expanded=False):
    st.markdown("**HSP Field Guide**")
    st.caption("HSP is an additional cooling-margin indicator. It can escalate the WBGT policy band when it is more protective, but it does not relax the NIOSH/OSHA-style WBGT policy band.")
    st.caption("Cooling margin refers to the remaining capacity to dissipate heat under the current environmental and work conditions. As cooling margin narrows, heat-strain risk increases.")

    st.markdown("""
**Understanding WBGT, ECCE and HSP**

- **WBGT** = Environmental heat-stress indicator used for policy guidance.
- **ECCE** = Estimated Cooling Capacity of the Environment.
- **HSP** = Heat load versus available cooling-capacity indicator.

These indicators serve different purposes and should not be compared directly. Follow site-specific HSE policy / SOP and regulatory requirements for WBGT- or TWL-based controls. Use HSP as an additional decision-support signal to recognize when cooling margin may be narrowing.
""")

    st.markdown(
        "- 🟢 **HSP < 0.55** → Adequate cooling margin available; routine control measures remain appropriate  \n"
        "- 🟢 **0.55–0.59** → Cooling margin still available; continue hydration and supervision  \n"
        "- 🟢 **0.60–0.64** → Cooling margin still available, but PPE or worksite factors may be narrowing reserve  \n"
        "- 🟢 **0.65–0.69** → Cooling margin narrowing further; confirm control measures before prolonged work  \n"
        "- 🟢 **0.70–0.74** → Cooling margin reducing; increase attention to hydration, rest access and symptom monitoring  \n"
        "- 🟢 **0.75–0.79** → Approaching marginal cooling; prepare to escalate if exposure continues or conditions worsen  \n"
        "- 🟠 **0.80–0.99** → Cooling margin narrowing; increase supervision and heat-stress control measures  \n"
        "- 🔴 **HSP ≥ 1.00** → Cooling margin may be inadequate for the current heat load"
    )

if (mwl_env is not None) and (mwl_op is not None):
    with st.expander("🔧 View Cooling Capacity Details", expanded=False):
        _raw_disp = ss.get("ecce_raw", mwl_env)
        _cap_disp = ss.get("ecce_cap", mwl_env)
        _denom_disp = ss.get("hsp_capacity", mwl_op)
        st.markdown(
            f"""
            <div class="ecce-detail-box">
              <p><b>ECCE used for HSP:</b> {mwl_op:.0f} W/m² &nbsp;|&nbsp; <b>Environmental ECCE:</b> {mwl_env:.0f} W/m² &nbsp;|&nbsp; <b>HSP denominator:</b> {_denom_disp:.0f} W/m²</p>
              <p><b>Diagnostics:</b> raw ECCE {_raw_disp:.0f} W/m²; smooth environmental ceiling {_cap_disp:.0f} W/m². The lower applicable value is used for HSP.</p>
              <p><b>Workload:</b> HSP applies the selected task/workload multiplier ({float(ss.get('hsp_met_multiplier', 1.0)):.2f}); workload increases heat production relative to available cooling capacity.</p>
              <p><b>Interpretation:</b> WBGT indicates environmental heat-stress severity; ECCE indicates estimated cooling capacity; HSP indicates heat load relative to available cooling capacity.</p>
              <p><b>Use:</b> Follow site HSE policy/SOP for WBGT- or TWL-based controls. HSP is an additional cooling-margin indicator. ECCE is modeled decision support, not an instrument measurement. Source: {mwl_source}.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

with st.expander("🧪 HSP Validation Table — Developer Check", expanded=False):
    st.caption(
        "Internal consistency check for HSP smoothness. Fixed test condition: GT = DB + 3°C, wind = 1.0 m/s. "
        "Additional-factor logic is unchanged; PPE is applied after environmental cooling capacity is estimated."
    )
    _val_rh = st.selectbox("Validation RH (%)", [50, 60, 65, 70, 75], index=1, key="hsp_validation_rh")
    _val_df = build_hsp_validation_table(rh_values=(_val_rh,), db_min=30, db_max=40, ppe_values=(0.0, 1.0, 2.0))
    st.dataframe(_val_df, use_container_width=True, hide_index=True)
    st.caption("Review ΔHSP / +1°C to detect unwanted cliffs. Target behavior is progressive, not stepwise.")

 
 
   
   

with st.expander("🧑‍🏭 Worker Messages (Tap To Expand)", expanded=False):
    st.markdown("**English (simple)**")
    st.markdown(
        """
- Drink small amounts regularly (Do not wait for thirst). Follow team hydration practices when prompted.
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
st.caption("This table shows records that have been explicitly saved. After changing city or inputs, click **Apply Worksite Additional Factors & Compute**, then **Save Current Assessment** to add the new assessment. Reset now clears this saved-history table for a fresh assessment session.")

# Ensure audit log exists
if "audit_log" not in ss:
    ss["audit_log"] = []

# Monotonic save counter to avoid duplicate appends on Streamlit reruns
if "save_counter" not in ss:
    ss["save_counter"] = 0
if "last_saved_id" not in ss:
    ss["last_saved_id"] = -1

# Controls
colA, colB, colC = st.columns([1.0, 1.0, 1.0], vertical_alignment="center")
with colA:
    save_now = st.button(
        "💾 Save Current Assessment",
        type="primary",
        use_container_width=True,
        key="btn_save_record_block8",
    )
with colB:
    st.caption("Compute updates the on-screen snapshot. Save adds the current snapshot to this audit table.")
with colC:
    if st.button("🧹 Clear Audit History", use_container_width=True, key="btn_clear_audit_block8"):
        ss["audit_log"] = []
        ss["save_counter"] = 0
        ss["last_saved_id"] = -1
        st.rerun()

if save_now:
    if ss.get("wbgt_eff_c") is None:
        st.warning("Please apply worksite additional factors and compute before saving a record.")
    else:
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

    # Display-units for Adjusted WBGT in the saved record
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
        "Adjusted WBGT (°C)": f"{wbgt_eff_c:.1f}",
        f"Adjusted WBGT ({wbgt_eff_disp_unit})": f"{wbgt_eff_disp_val:.1f}",

        "HSP": f"{float(hsp_val):.2f}" if hsp_val is not None else "",
        "Final Risk": display_risk_label(risk_final) if callable(locals().get("display_risk_label", None)) else risk_final,
    }

    ss["audit_log"].append(log_entry)
    ss["last_saved_id"] = current_save_id
    st.success(f"Saved to Audit History. Adjusted WBGT: {wbgt_eff_disp_val:.1f} {wbgt_eff_disp_unit}")

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
- Follow site-approved work–rest practice  
- Actively monitor symptoms  
- Provide shade  

**Red / Extremely High — Essential Work Only Zone**
- Stop routine work  
- Only essential or emergency tasks under site policy and medical / HSE oversight  
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

with st.expander("ℹ About HART • Disclaimer • Feedback", expanded=False):
    st.markdown(f"""
**© 2026 Dr. Gummanur T. Manjunath — Developer of HART® (Heat Assessment & Response Tool)**

Field Heat-Stress Decision Support System integrating **WBGT • ECCE • HSP**  
*(Instrument TWL input supported where available)*

**Purpose:**  
HART is designed as a **field decision-support tool** to assist supervisors and occupational health professionals in assessing workplace heat risk.

**Disclaimer:**  
This tool supports occupational heat-stress awareness and field screening.  
It does **not** replace site HSE policy, IH/OH judgement, medical evaluation, or regulatory requirements.  
No professional organization or institution endorses this tool unless explicitly stated.

**Feedback & Field Validation:**  
https://forms.gle/7rfrXZXkyCdXqGVs5  

**Build:** `{APP_VERSION}`
""")
