# CHSRMT
Calibrated Heat Stress Risk Management Tool — Field WBGT + HSP Decision Support
## ⚠️ Weather Data Source and Interpretation

CHSRMT uses **Open-Meteo** as a global numerical weather reanalysis and forecast source to provide *baseline environmental inputs* when on-site measurements are unavailable.

**Important considerations:**
- Open-Meteo values represent **area-averaged modeled conditions**, not point measurements from a specific workplace.
- Temperatures may differ from nearby airport or city weather stations due to:
  - Urban heat island effects
  - Terrain and coastal influences
  - Time-averaging and model resolution
- In industrial settings, **local microclimate and process heat often exceed regional weather station readings**.

**Recommended practice:**
- Use **on-site measured dry bulb, wet bulb, globe temperature, and air velocity** whenever available.
- Weather-fetched values should be treated as **screening or fallback inputs**, not replacements for local industrial hygiene measurements.

CHSRMT is designed to **interpret environmental heat in relation to human cooling capacity**, not to replace workplace heat measurements. Divergence between regional weather data and local site conditions is expected and clinically meaningful.
