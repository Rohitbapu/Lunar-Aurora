# Lunar Aurora — Open-Air Mahabalipuram WebXR & Tabletop Kiosk Prototype

[![License: MIT](https://img.shields.io/badge/License-MIT-00e5ff.svg)](LICENSE)
[![Site: Mahabalipuram](https://img.shields.io/badge/UNESCO%20Site-Mahabalipuram%2012.6165%C2%B0N-f4c430.svg)](docs/architecture.md)
[![Unity Mode: No-SRD Sim](https://img.shields.io/badge/Unity%20Kiosk-No--SRD%20Simulation%20Mode-ffca28.svg)](docs/sony_srd_integration_todo.md)

**Team Lunar Aurora** — *Ayyappan Ayyanan, Vikrant R M, Rohit Bapu S B* (Sethu Institute of Technology)  
**Target Milestone:** XR Innovation Challenge 2026 (Phase 2: Dec 25, 2026 | Finale: Jan 11, 2027)

---

## What Currently Works in This Repository
1. **Zero-CDN Mobile WebXR & QR Ticketing (`src/frontend_webxr/` + `src/backend/`):**
   - Counter ticket portal (`/ticket`, `/qr`) generates URL-encoded QR launch links in **English (`EN`)**, **Tamil (`TA`)**, or **Hindi (`HI`)** with self-signed LAN TLS (`generate_ssl_certs.py --ip`) so mobile browsers can access camera and orientation sensors over `:8443`.
   - Runtime libraries (`three.min.js`, `GLTFLoader.js`, `tf.min.js`, `qrcode.min.js`, Font Awesome `6.5.1`) are vendored locally inside `src/frontend_webxr/vendor/`.
   - 7 Mahabalipuram stops with OpenStreetMap (ODbL) coordinates (`node/1138027422`, `way/370135158`, `way/103082949`, `node/353978523`, `way/753671961`, `node/353978532`, `node/353978541`), real OpenStreetMap one-way walking distances (`4128.3 m` / `4.13 km` total across 6 legs, `~59 min` walking at `70.0 m/min`), per-stop DB `arrival_radius_m` (`20, 45, 75, 25, 25, 25, 30` — all **UNVERIFIED** until field-tested), manual **`I'M HERE`** check-in buttons for all stops, Wikipedia/UNESCO sources, interactive `+45 XP` riddles, **`54`** pre-cached EN/TA/HI MP3s, `DeviceOrientationEvent` WebAudio panner alignment, watermarked snapshots, and `fpdf2` PDF Travel Journals.
   - Verified Wikimedia photographs + sourced facts panels render for all 5 monument classes (`Grand_Solstice_Sun_Temple.glb` is hidden in WebXR UI and Demo Mode).
2. **Real NOAA Solar Geometry + Assumed-Shade Dijkstra Graph (`routing_service.py` + `shadeMap.js`):**
   - Computes solar declination, equation of time, hour angle, solar elevation, and solar azimuth for `12.6165° N, 80.19° E` (IST) via the **NOAA General Solar Position Equations**, defaulting to **`2027-01-11`** and exposing `?date=` & `?hour=`.
   - Verified in `test_suite.py` (`09:00`: `30.75°` elev / `125.36°` azim; `12:00`: `55.22°` elev / `173.33°` azim; `16:00`: `25.23°` elev / `238.13°` azim — within `< 0.26°` of independent Meeus reference).
   - **Important Modeling Disclosure:** While graph coordinates & walking distances come from OpenStreetMap, **the route graph shade weights and penalties are ASSUMED / ILLUSTRATIVE** (not physical pyranometer measurements). Using those assumed weights on `2027-01-11 12:00 IST` from Stop 1 -> Stop 7, shortest OSM walking (`[1, 4, 7]`, `1229.6 m`) vs assumed-shade OSM walking (`[1, 6, 7]`, `1369.7 m`) yields an **illustrative relative model score of `81.4%`** (do **not** interpret this as measured sun exposure).
3. **Unity 6 Desktop Kiosk (`src/kiosk_unity/` — `No-SRD simulation mode`):**
   - Compiles cleanly to standalone Windows x64 (`LunarAurora_Kiosk.exe`) distributed on **[GitHub Releases](https://github.com/Rohitbapu/Lunar-Aurora/releases)** (`Builds/` is gitignored).
   - Defaults to **`3840x2160` fullscreen**, with a **`-windowed`** command-line switch (`LunarAurora_Kiosk.exe -windowed`) for desktop development.
   - Displays 3 procedural Mahabalipuram **Illustrative model** placeholders, drives directional sunlight from `/api/site/telemetry?date=...&hour=...`, and mirrors controls onto **`Operator HUD (second display)`**.

---

## Assumed / Illustrative Route Graph & Shade Weights
All shade weights below in `src/backend/init_db.py` and `src/backend/app/services/routing_service.py` are **assumed placeholders**, not empirical canopy/radiometer measurements:

| Edge Category / Parameter | Assumed Value / Rule |
| :--- | :--- |
| `cave_shelter` (`6->7`) | `base_shade_factor = 0.88`; `compute_dynamic_shade` clamps `[0.88, 0.95]` |
| `cave_approach` (`5->6`) / `colonnade` | `base_shade_factor = 0.90`; `max(0.55, base_shade - 0.12 * sin(elev))` |
| `tree_avenue` (`2->3: 0.72`, `2->4: 0.75`, `4->5: 0.78`, `3->4: 0.80`, `5->7: 0.82`, `1->6: 0.94`) | `max(0.45, base_shade - 0.15 * sin(elev))` |
| `coastal_walk` (`1->2`) | `base_shade_factor = 0.65`; `max(0.20, base_shade * (1 - 0.45 * sin(elev)))` |
| `open_stone` (`1->4: 0.10`, `4->7: 0.12`, `1->3: 0.12`, `3->7: 0.15`) | `max(0.05, base_shade * (1 - 0.55 * sin(elev)))` |
| `monument_shadow` | `0.30` if `elev > 72°`, `max(base_shade, 0.78)` if `15°..72°`, else `0.55` |
| Dijkstra shade penalty weight | `weight_shaded = distance_m * (1.0 + (1.0 - shade) * 2.8)` |
| Assumed walking speed | `70.0 m/min` |

### How to Calibrate
1. **Canopy Sky-View Factor (SVF) Survey:** Capture hemispherical fisheye photos or LiDAR SVF along each Mahabalipuram OSM walkway edge connecting Stops `1`–`7` every `25–50 m`.
2. **Irradiance Ratio Measurements:** Sample direct + diffuse solar irradiance (`W/m²`) under each tree canopy, cave entrance, and coastal wall relative to open reference `open_stone` at `09:00`, `12:00`, and `16:00 IST`.
3. **Fit Empirical Shade Functions:** Replace assumed `base_shade_factor` values in `init_db.py` and the `sin(elev)` attenuation constants in `compute_dynamic_shade()` with measured attenuation by segment azimuth and solar elevation.
4. **Tune Walk Speed & Detour Weight:** Replace `70.0 m/min` and `2.8` based on observed tourist walking speed and acceptable detour tolerance.

---

## Verified Backend Benchmarks (`benchmark_kpis.py` — 20 Iterations)
Latest timestamped JSON: `src/backend/benchmark_results_20261126_154923.json`.

| Operation | Measured Mean | Measured P95 | Status |
| :--- | :---: | :---: | :--- |
| Dijkstra shaded-route compute (DB graph) | `0.37 ms` | `0.54 ms` | MEASURED |
| NOAA solar calculation (`2027-01-11 12:00 IST`) | `0.01 ms` | `0.01 ms` | MEASURED |
| Cached-audio hit (`GET /static/audio_cache/stop_1_en.mp3`) | `3.43 ms` | `4.01 ms` | MEASURED |
| Online AI latency (`Groq + Edge-TTS`) | — | — | `NOT MEASURED - no API key` |
| Vision metadata lookup (`POST /api/vision/identify`) | `6.66 ms` | `7.18 ms` | MEASURED |
| Dual-route NOAA telemetry (`GET /api/site/telemetry`) | `6.49 ms` | `15.61 ms` | MEASURED |
| PDF Travel Journal export (`POST /api/tour/{sid}/journal`) | `14.27 ms` | `15.43 ms` | MEASURED |
| Backend E2E & NOAA API test suite (`test_suite.py`) | `9/9` (`100.0%`) in `2642.38 ms` | — | MEASURED |

Pending hardware measurements (tagged **`MEASURE ON DEVICE`** in JSON): `mobile_fps`, `qr_to_ar_launch_ms`, `vision_on_device_ms`, and `unity_frame_time_ms`.

---

## Known Limitations
See full details in **[docs/known_limitations.md](docs/known_limitations.md)**:
- **Sony ELF-SR1 Plugin Absent (`No-SRD simulation mode`):** `SRDisplayUnityPlugin` is not installed (`SRDISPLAY_SDK_PRESENT` undefined); eye-tracked lenticular 3D is not active yet ([docs/sony_srd_integration_todo.md](docs/sony_srd_integration_todo.md)).
- **Vision Classifier Untrained (`Vision model not installed`):** `data/cards/` captures have not been filmed yet, so `model.json` does not exist; `SCAN RELIC` displays `"Vision model not installed"` rather than guessing.
- **Procedural 3D Placeholders (Hidden in WebXR UI):** `Grand_Solstice_Sun_Temple.glb` is hidden across WebXR UI and Demo Mode; all 5 carving classes display verified Wikimedia photographs and sourced facts panels until team-authored meshes are added. Unity renders 3 procedural placeholders labeled `"Illustrative model"`.
- **Unverified Per-Stop Geofence Radii:** `arrival_radius_m` (`20, 45, 75, 25, 25, 25, 30`) are non-overlapping starting estimates (`UNVERIFIED until field-tested`); manual **`I'M HERE`** buttons exist for all stops.
- **Assumed Route Shade Weights:** Distances come from OpenStreetMap (ODbL), but edge shade factors and penalties are illustrative placeholders, not measured irradiance/heat.
- **Unmeasured Groq Benchmark & Hardware KPIs:** Groq AI latency is `NOT MEASURED - no API key`; phone FPS, QR launch time, mobile vision ms, and ELF-SR1 frame time remain `MEASURE ON DEVICE`.
- **Self-Signed TLS Prompt:** Mobile HTTPS on `:8443` displays a browser warning for the local development certificate from `generate_ssl_certs.py`.

---

## Documentation & Deliverables
- **[Known Limitations (`docs/known_limitations.md`)](docs/known_limitations.md)**
- **[Accelerator & Technical Report (`docs/ax.md`)](docs/ax.md)**
- **[System Architecture (`docs/architecture.md`)](docs/architecture.md)**
- **[Open-Source Software, OSM & Media Attribution (`docs/oss_attribution.md`)](docs/oss_attribution.md)** *(OSM coordinates © OpenStreetMap contributors under ODbL 1.0; Wikimedia Commons images retain their licenses in `docs/carving_cards/images/LICENSE-NOTICE.md`)*
- **[Sony SRDisplay Integration TODO (`docs/sony_srd_integration_todo.md`)](docs/sony_srd_integration_todo.md)**
- **[XR Domain Justification (`docs/xr_domain_justification.md`)](docs/xr_domain_justification.md)**
- **[Setup & User Guide (`docs/setup_and_user_guide.md`)](docs/setup_and_user_guide.md)**
- **[Printable 5-Card Mahabalipuram Sheet (`docs/carving_cards/print_5_carving_cards.html`)](docs/carving_cards/print_5_carving_cards.html)**
- **[Standalone Windows Kiosk EXE (GitHub Releases)](https://github.com/Rohitbapu/Lunar-Aurora/releases)**

---

## Quick Start
```powershell
cd src/backend
python init_db.py
python test_suite.py
python start_servers.py
```
Then open `http://localhost:8000/ticket` or `http://localhost:8000/app/?demo=1`.

## Tooling Disclosure & License
Software repository code is released under the [MIT License](LICENSE) — Team Lunar Aurora (2026) *(excluding third-party libraries, OpenStreetMap data under ODbL 1.0, and Wikimedia Commons images governed by `docs/oss_attribution.md`)*. **Antigravity** was used as an AI coding assistant during development.
