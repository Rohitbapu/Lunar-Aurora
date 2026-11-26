# Accelerator & Technical Report (`ax.md`)

**Project:** Lunar Aurora — Open-Air Mobile WebXR & Holographic Kiosk Prototype  
**Team:** Lunar Aurora — Ayyappan Ayyanan, Vikrant R M, Rohit Bapu S B (Sethu Institute of Technology)  
**Target Event:** XR Innovation Challenge 2026 (Phase 2 Deadline: Dec 25, 2026 | Finale: Jan 11, 2027)  
**Target Site:** Group of Monuments at Mahabalipuram (12.6165° N, 80.19° E, Tamil Nadu, India)

---

## 1. Current Implementation Status (Honest Audit)
1. **Mobile WebXR Frontend (`src/frontend_webxr/`):** Implemented and served over local HTTP (`:8000`) and self-signed LAN HTTPS (`:8443`). Camera-first HUD with 7 sourced Mahabalipuram tour stops, interactive NOAA ShadeMap (`shadeMap.js`), QR ticketing (`/ticket`, `/qr`), binaural WebAudio panner (`spatialAudio.js`), stop riddles, snapshot capture, and multi-page PDF Travel Journal export (`fpdf2`).
2. **Computer Vision Classifier (`visionEngine.js` + `src/backend/train_classifier.py`):** The MobileNetV2 training pipeline (`train_classifier.py`) and card frame extractor (`tools/extract_frames.py`) are implemented, **but the 6-class classifier is not trained yet** (`data/cards/` captures have not been recorded and `src/frontend_webxr/assets/vision_model/model.json` does not exist). At runtime, tapping `SCAN RELIC` displays `"Vision model not installed"` and does not guess.
3. **3D Assets (`src/frontend_webxr/assets/models/`):** All bundled `.glb` files are procedural primitive placeholders created by `src/kiosk_unity/generate_glb_exhibits.py`. Only `Grand_Solstice_Sun_Temple.glb` (`2,700` triangles, `92,520` bytes) is attached to `shore_temple_vimana` and labeled **`"Illustrative model"`**. Cards 02–05 render their verified Wikimedia Commons photograph and sourced Wikipedia/UNESCO facts panel until team-made `.glb` models are added.
4. **Unity 6 Kiosk (`src/kiosk_unity/`):** Compiles cleanly to standalone Windows x64 (`LunarAurora_Kiosk.exe`), **currently running strictly in `No-SRD simulation mode`**. Sony `SRDisplayUnityPlugin` is **not** installed in `Packages/manifest.json` and `SRDISPLAY_SDK_PRESENT` is **not** defined in `ProjectSettings.asset`. Secondary controls route to **`Operator HUD (second display)`** (`KioskOperatorDisplayHUD` on Display 1 when present). See `docs/sony_srd_integration_todo.md` for hardware integration steps.

---

## 2. NOAA Solar Geometry & Shaded Dijkstra Model
### 2.1 NOAA General Solar Position Equations (`src/backend/app/services/routing_service.py`)
Solar position is computed for Mahabalipuram (`lat = 12.6165° N`, `lon = 80.19° E`, IST `UTC+5:30`) using `date` (default `2027-01-11`, Finale date) and decimal `hour` (`0.0–24.0`):
- Fractional year ($\gamma$ in radians):
  $$\gamma = \frac{2\pi}{\text{days\_in\_year}} \left(\text{doy} - 1 + \frac{\text{hour} - 12}{24}\right)$$
- Equation of time (`eq_time_min`) and solar declination ($\delta$ in radians) via standard NOAA Fourier expansions.
- True solar time ($\text{TST} = \text{hour} \cdot 60 + \text{eq\_time\_min} + 4 \cdot \text{lon} - 60 \cdot 5.5 \bmod 1440$) and solar hour angle ($H = \text{TST}/4 - 180^\circ$).
- Solar zenith $\Phi$ from $\cos\Phi = \sin\phi\sin\delta + \cos\phi\cos\delta\cos H$, yielding `solar_elevation_deg = max(0, 90 - deg(Phi))` and azimuth clockwise from North.

**Verified against independent Meeus astronomical calculation on `2027-01-11` (`test_suite.py` Step 6b):**

| IST Hour | Computed Elevation | Ref Elevation | Computed Azimuth | Ref Azimuth | Declination | EoT (min) | Hour Angle |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `09:00` | `30.75°` | `30.68°` (`0.07°` diff) | `125.36°` | `125.18°` (`0.18°` diff) | `-21.95°` | `-7.08` | `-49.08°` |
| `12:00` | `55.22°` | `55.31°` (`0.09°` diff) | `173.33°` | `173.07°` (`0.26°` diff) | `-21.93°` | `-7.13` | `-4.09°` |
| `16:00` | `25.23°` | `25.40°` (`0.17°` diff) | `238.13°` | `238.16°` (`0.03°` diff) | `-21.90°` | `-7.20` | `55.89°` |

Both the WebXR ShadeMap date/time controls and Unity's `KioskNetworkBridge.cs` -> `HolographicMonumentPreview.cs` directional sun light query `GET /api/site/telemetry?date=...&hour=...` dynamically.

### 2.2 Courtyard Shade Weighting & Heat Saved Model Estimate
For each graph edge $e = (u, v)$ with length $d_e$ (meters), base canopy factor $s_e$, and path category (`cave_shelter`, `cave_approach`, `tree_avenue`, `coastal_walk`, `open_stone`), `compute_dynamic_shade` computes dynamic shade $s_{\text{eff}}(e, t) \in [0.05, 0.95]$ using `sin(elevation_deg)`. Shaded Dijkstra minimizes $\sum d_e \cdot (1 + 2.8 (1 - s_{\text{eff}}))$, while Shortest Dijkstra minimizes $\sum d_e$.

- **`Heat Exposure Saved` is a model estimate, not a radiometric field measurement:**
  $$\text{Heat Saved (\%)} = \left(1 - \frac{\sum_{e \in P_{\text{shaded}}} d_e(1 - s_{\text{eff}})}{\sum_{e \in P_{\text{shortest}}} d_e(1 - s_{\text{eff}})}\right) \times 100$$
- Measured backend model estimate from Stop 1 -> Stop 7 at `2027-01-11 12:00 IST` (`55.22°` solar elevation): **`80.5%` (model estimate)** (`test_suite.py`).

---

## 3. Measured Backend KPIs & Pending Device Measurements
From `src/backend/benchmark_kpis.py` (20 measured iterations after 1 warmup call, saved to `src/backend/benchmark_results_20261126_134622.json`):

| Benchmark | Mean Latency | P95 Latency | Status |
| :--- | :---: | :---: | :--- |
| Dijkstra shaded-route compute | `0.33 ms` | `0.42 ms` | MEASURED |
| NOAA solar calculation (`2027-01-11 12:00 IST`) | `0.01 ms` | `0.01 ms` | MEASURED |
| Cached-audio hit (`GET /static/audio_cache/stop_1_en.mp3`) | `2.95 ms` | `3.22 ms` | MEASURED |
| Online AI latency (`Groq + Edge-TTS`) | — | — | `NOT MEASURED - no API key` |
| Vision metadata lookup (`POST /api/vision/identify`) | `5.80 ms` | `6.37 ms` | MEASURED |
| Dual-route NOAA telemetry (`GET /api/site/telemetry`) | `5.44 ms` | `5.12 ms` | MEASURED |
| PDF Travel Journal export (`POST /api/tour/{sid}/journal`) | `12.77 ms` | `13.40 ms` | MEASURED |
| API test suite pass rate (`test_suite.py`) | `9/9 (100.0%)` in `1658.05 ms` | — | MEASURED |

**Device/Hardware KPIs (not measured yet):** `mobile_fps`, `qr_to_ar_launch_ms`, `vision_on_device_ms`, and `unity_frame_time_ms` remain tagged **`MEASURE ON DEVICE`**.

---

## 4. Development Tooling Disclosure
Portions of software architecture refactoring, NOAA solar implementation, documentation cleanup, and test verification were developed with assistance from **Antigravity** (AI coding assistant), with all source code, attributions, and test results reviewed and run locally.
