# Accelerator & Technical Report (`ax.md`)

**Project:** Lunar Aurora — Open-Air Mobile WebXR & Holographic Kiosk Prototype  
**Team:** Lunar Aurora — Ayyappan Ayyanan, Vikrant R M, Rohit Bapu S B (Sethu Institute of Technology)  
**Target Event:** XR Innovation Challenge 2026 (Phase 2 Deadline: Dec 25, 2026 | Finale: Jan 11, 2027)  
**Target Site:** Group of Monuments at Mahabalipuram (12.6165° N, 80.19° E, Tamil Nadu, India)

---

## 1. Current Implementation Status (Honest Audit)
1. **Mobile WebXR Frontend (`src/frontend_webxr/`):** Implemented and served over local HTTP (`:8000`) and self-signed LAN HTTPS (`:8443`). Camera-first HUD with 7 sourced Mahabalipuram tour stops, interactive NOAA ShadeMap (`shadeMap.js`), QR ticketing (`/ticket`, `/qr`), binaural WebAudio panner (`spatialAudio.js`), stop riddles, snapshot capture, and multi-page PDF Travel Journal export (`fpdf2`).
2. **Computer Vision Classifier (`visionEngine.js` + `src/backend/train_classifier.py`):** Training pipeline (`train_classifier.py`) and card frame extractor (`tools/extract_frames.py`) are implemented, **but the classifier is not trained yet** (`data/cards/` video sessions are pending user recording and `model.json` does not exist). Tapping `SCAN RELIC` displays `"Vision model not installed"` and never guesses.
3. **3D Assets (`src/frontend_webxr/assets/models/`):** Bundled `.glb` meshes are procedural placeholders from `generate_glb_exhibits.py`. Only `Grand_Solstice_Sun_Temple.glb` (`2,700` triangles, `92,520` bytes) is rendered for `shore_temple_vimana` and labeled **`"Illustrative model"`**. Cards 02–05 show their Wikimedia photograph and sourced facts panel.
4. **Unity 6 Kiosk (`src/kiosk_unity/`):** Compiles standalone Windows x64 (`LunarAurora_Kiosk.exe`) defaulting to `3840x2160` fullscreen with `-windowed` CLI switch for development, **running strictly in `No-SRD simulation mode`**. Sony `SRDisplayUnityPlugin` is **not** installed and `SRDISPLAY_SDK_PRESENT` is **not** defined; secondary controls render on **`Operator HUD (second display)`**. See [sony_srd_integration_todo.md](sony_srd_integration_todo.md) and [known_limitations.md](known_limitations.md).

---

## 2. Real OpenStreetMap Geometry + NOAA Solar Equations + Assumed Shade Weights

### 2.1 Verified OpenStreetMap Coordinates & Walking Distances (`ODbL 1.0`)
Node coordinates (`lat/lon`) and all 13 `PathEdge` walking distances (`distance_meters`) in `src/backend/init_db.py` come directly from OpenStreetMap (`api.openstreetmap.org/api/0.6/map?bbox=80.188,12.607,80.201,12.621`):

| Stop | Stop Name | Latitude | Longitude | Source Coordinate Reference |
| :---: | :--- | :---: | :---: | :--- |
| `1` | Shore Temple Coastal Entry | `12.6165181` | `80.1982844` | OpenStreetMap `node/1138027422` (`barrier=gate`, west entry to `way/390473765`) |
| `2` | Shore Temple Shrines | `12.6164535` | `80.1993500` | OpenStreetMap `way/370135158` (`Mamallapuram Shore Temple`) |
| `3` | Pancha Rathas Monolithic Complex | `12.6090647` | `80.1897016` | OpenStreetMap `way/103082949` (`Pancha Rathas`) |
| `4` | Arjuna's Penance | `12.6179087` | `80.1926969` | OpenStreetMap `node/353978523` (`Arjuna's Penance`) |
| `5` | Krishna's Butterball | `12.6190890` | `80.1924032` | OpenStreetMap `way/753671961` (`Krishna's Butterball`) |
| `6` | Varaha Cave Temple | `12.6180857` | `80.1922234` | OpenStreetMap `node/353978532` (`Varaha Mandapam / Cave`) |
| `7` | Mahishasuramardini Mandapa | `12.6152265` | `80.1915388` | OpenStreetMap `node/353978541` (`Mahishamadhini Cave`) |

Walkway edge distances (`1->2`: `255.0 m`, `2->3`: `1831.2 m`, `3->4`: `1124.8 m`, `4->5`: `238.8 m`, `5->6`: `167.3 m`, `5->7`: `652.3 m`, `1->6`: `858.5 m`, `2->4`: `992.5 m`, `6->7`: `511.2 m`, `1->4`: `737.5 m`, `4->7`: `492.1 m`, `1->3`: `1576.1 m`, `3->7`: `789.9 m`) are shortest-path distances along OSM walkable ways (`footway`, `path`, `pedestrian`, `residential`, `service`, `tertiary`).

### 2.2 NOAA General Solar Position Equations (`routing_service.py`)
Solar coordinates use `lat = 12.6165° N`, `lon = 80.19° E`, `IST UTC+5:30`, defaulting to `2027-01-11`:

| IST Hour | NOAA Elevation | Ref Elevation | NOAA Azimuth | Ref Azimuth | Declination | EoT (min) | Hour Angle |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `09:00` | `30.75°` | `30.68°` (`0.07°` diff) | `125.36°` | `125.18°` (`0.18°` diff) | `-21.95°` | `-7.08` | `-49.08°` |
| `12:00` | `55.22°` | `55.31°` (`0.09°` diff) | `173.33°` | `173.07°` (`0.26°` diff) | `-21.93°` | `-7.13` | `-4.09°` |
| `16:00` | `25.23°` | `25.40°` (`0.17°` diff) | `238.13°` | `238.16°` (`0.03°` diff) | `-21.90°` | `-7.20` | `55.89°` |

### 2.3 ASSUMED / ILLUSTRATIVE Route Shade Weights (Not Measured)
Whereas graph distances are real OpenStreetMap measurements, **every shade weight and path penalty is an ASSUMED / ILLUSTRATIVE placeholder** authored by Team Lunar Aurora (zero pyranometer, canopy fisheye, or UV radiometer readings have been recorded):

| Graph Parameter | Where Defined | Assumed / Illustrative Value |
| :--- | :--- | :--- |
| `cave_shelter` (`6->7`) | `init_db.py` + `compute_dynamic_shade` | `base_shade_factor = 0.88`; clamped `[0.88, 0.95]` |
| `cave_approach` (`5->6`) / `colonnade` | `init_db.py` + `compute_dynamic_shade` | `base_shade_factor = 0.90`; `max(0.55, base_shade - 0.12 * sin(elev))` |
| `tree_avenue` (`2->3`, `3->4`, `4->5`, `5->7`, `1->6`, `2->4`) | `init_db.py` + `compute_dynamic_shade` | `base_shade_factor = 0.72` to `0.94`; `max(0.45, base_shade - 0.15 * sin(elev))` |
| `coastal_walk` (`1->2`) | `init_db.py` + `compute_dynamic_shade` | `base_shade_factor = 0.65`; `max(0.20, base_shade * (1 - 0.45 * sin(elev)))` |
| `open_stone` (`1->4`, `4->7`, `1->3`, `3->7`) | `init_db.py` + `compute_dynamic_shade` | `base_shade_factor = 0.10` to `0.15`; `max(0.05, base_shade * (1 - 0.55 * sin(elev)))` |
| `monument_shadow` (fallback category) | `compute_dynamic_shade` | `0.30` if `elev > 72°`, `max(base_shade, 0.78)` if `15°..72°`, else `0.55` |
| Dijkstra shade penalty multiplier | `build_graph` | `weight_shaded = distance_m * (1.0 + (1.0 - shade) * 2.8)` |
| Assumed walking speed | `find_path` | `70.0 m/min` |

Using these assumed weights over the OSM distance graph at `2027-01-11 12:00 IST` (`55.22°` solar elevation):
- Shortest OSM path `[1, 4, 7]`: `1229.6 m` (average assumed shade index `0.06`)
- Assumed-shade path `[1, 6, 7]`: `1369.7 m` (`+140.1 m`, average assumed shade index `0.84`)
- Relative illustrative route score (`heat_exposure_saved_pct` API field): **`81.4%`** *(computed solely from assumed graph weights, **not** measured sun exposure)*.

---

## 3. How to Calibrate the Shade Weights on Site
1. **Canopy & Structural Obstruction Survey:** Capture upward-facing hemispherical (fisheye) photographs or LiDAR sky-view factor (SVF) scans every `25–50 m` along the OSM walkways connecting `node/1138027422` through `node/353978541`.
2. **Irradiance & Microclimate Sampling:** Measure synchronized direct/diffuse solar irradiance (`W/m²`, e.g., calibrated pyranometer or solar power meter) and shaded black-globe temperature along each walkway segment relative to an unobstructed coastal reference (`open_stone` near Shore Temple) at `09:00`, `12:00`, and `16:00 IST`.
3. **Fit Empirical Attenuation Curves:** Replace `base_shade_factor` and the linear `sin(elev)` formulas in `compute_dynamic_shade()` with empirical attenuation per segment orientation/azimuth and observed SVF.
4. **Update Speed & Penalty Preferences:** Measure tourist median walking speed on slopes vs flat paved streets (`find_path`) and tune the `2.8` detour-aversion multiplier using visitor route-acceptance trials.

---

## 4. Measured Backend KPIs (`benchmark_results_20261126_145557.json`, 20 Iterations)

| Benchmark | Mean Latency | P95 Latency | Status |
| :--- | :---: | :---: | :--- |
| Dijkstra shaded-route compute | `0.37 ms` | `0.55 ms` | MEASURED |
| NOAA solar calculation (`2027-01-11 12:00 IST`) | `0.01 ms` | `0.01 ms` | MEASURED |
| Cached-audio hit (`GET /static/audio_cache/stop_1_en.mp3`) | `4.02 ms` | `4.47 ms` | MEASURED |
| Online AI latency (`Groq + Edge-TTS`) | — | — | `NOT MEASURED - no API key` |
| Vision metadata lookup (`POST /api/vision/identify`) | `7.26 ms` | `7.42 ms` | MEASURED |
| Dual-route NOAA telemetry (`GET /api/site/telemetry`) | `6.09 ms` | `5.26 ms` | MEASURED |
| PDF Travel Journal export (`POST /api/tour/{sid}/journal`) | `14.03 ms` | `14.94 ms` | MEASURED |
| API test suite pass rate (`test_suite.py`) | `9/9 (100.0%)` in `1845.43 ms` | — | MEASURED |

Hardware/device fields (`mobile_fps`, `qr_to_ar_launch_ms`, `vision_on_device_ms`, `unity_frame_time_ms`) remain **`MEASURE ON DEVICE`**.

---

## 5. Development Tooling Disclosure
Portions of software architecture refactoring, NOAA solar implementation, OSM coordinate verification, documentation updates, and test verification were developed with assistance from **Antigravity** (AI coding assistant).
