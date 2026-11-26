# Lunar Aurora — Open-Air Mahabalipuram WebXR & Tabletop Kiosk Prototype

[![License: MIT](https://img.shields.io/badge/License-MIT-00e5ff.svg)](LICENSE)
[![Site: Mahabalipuram](https://img.shields.io/badge/UNESCO%20Site-Mahabalipuram%2012.6165%C2%B0N-f4c430.svg)](docs/architecture.md)
[![Unity Mode: No-SRD Sim](https://img.shields.io/badge/Unity%20Kiosk-No--SRD%20Simulation%20Mode-ffca28.svg)](docs/sony_srd_integration_todo.md)

**Team Lunar Aurora** — *Ayyappan Ayyanan, Vikrant R M, Rohit Bapu S B* (Sethu Institute of Technology)  
**Target Milestone:** XR Innovation Challenge 2026 (Phase 2: Dec 25, 2026 | Finale: Jan 11, 2027)

---

## What Currently Works in This Repository
1. **Zero-CDN Mobile WebXR & QR Ticketing (`src/frontend_webxr/` + `src/backend/`):**
   - Counter ticket portal (`/ticket`, `/qr`) generates URL-encoded QR launch links in **English (`EN`)**, **Tamil (`TA`)**, or **Hindi (`HI`)** with self-signed LAN TLS (`generate_ssl_certs.py --ip`) so mobile browsers can access camera/orientation sensors over port `:8443`.
   - All frontend runtime libraries (`three.min.js`, `GLTFLoader.js`, `tf.min.js`, `qrcode.min.js`, Font Awesome `6.5.1`) are vendored locally inside `src/frontend_webxr/vendor/`.
   - 7 seeded Mahabalipuram monuments (`init_db.py`) with Wikipedia/UNESCO source URLs, interactive `+45 XP` riddles, **`54`** pre-synthesized EN/TA/HI fallback MP3s (`static/audio_cache/`), `DeviceOrientationEvent` WebAudio panner alignment (`spatialAudio.js`), AR photo capture, and downloadable multi-page `fpdf2` PDF Travel Journals.
2. **Real NOAA Solar Geometry & Dual-Route ShadeMap (`routing_service.py` + `shadeMap.js`):**
   - Computes real solar declination, equation of time, hour angle, solar elevation, and solar azimuth for `12.6165° N, 80.19° E` (IST) via the **NOAA General Solar Position Equations**, defaulting to **`2027-01-11`** and exposing `?date=` & `?hour=`.
   - Verified in `test_suite.py` (`09:00`: `30.75°` elev / `125.36°` azim; `12:00`: `55.22°` elev / `173.33°` azim; `16:00`: `25.23°` elev / `238.13°` azim — within `< 0.26°` of independent Meeus reference).
   - Both WebXR ShadeMap date/hour controls and Unity `KioskNetworkBridge.cs` consume `/api/site/telemetry?date=...&hour=...` to update shortest sun vs. shaded Dijkstra routes (`80.5%` Heat Exposure Saved **model estimate** at `2027-01-11 12:00 IST`).
3. **Unity 6 Desktop Kiosk (`src/kiosk_unity/` — `No-SRD simulation mode`):**
   - Builds cleanly to a standalone Windows x64 executable (`LunarAurora_Kiosk.exe`) distributed on **[GitHub Releases](https://github.com/Rohitbapu/Lunar-Aurora/releases)** (`Builds/` is gitignored).
   - Displays 3 procedural Mahabalipuram **Illustrative model** placeholders (`Shore Temple`, `Pancha Rathas`, `Krishna's Butterball`), drives directional sunlight from the backend NOAA endpoint, and mirrors telemetry onto **`Operator HUD (second display)`**.

---

## Verified Backend Benchmarks (`benchmark_kpis.py` — 20 Iterations)
Latest timestamped measurement file: `src/backend/benchmark_results_20261126_134622.json`.

| Operation | Measured Mean | Measured P95 | Status |
| :--- | :---: | :---: | :--- |
| Dijkstra shaded-route compute (DB graph) | `0.33 ms` | `0.42 ms` | MEASURED |
| NOAA solar calculation (`2027-01-11 12:00 IST`) | `0.01 ms` | `0.01 ms` | MEASURED |
| Cached-audio hit (`GET /static/audio_cache/stop_1_en.mp3`) | `2.95 ms` | `3.22 ms` | MEASURED |
| Online AI latency (`Groq + Edge-TTS`) | — | — | `NOT MEASURED - no API key` |
| Vision metadata lookup (`POST /api/vision/identify`) | `5.80 ms` | `6.37 ms` | MEASURED |
| Dual-route NOAA telemetry (`GET /api/site/telemetry`) | `5.44 ms` | `5.12 ms` | MEASURED |
| PDF Travel Journal export (`POST /api/tour/{sid}/journal`) | `12.77 ms` | `13.40 ms` | MEASURED |
| Backend E2E & NOAA API test suite (`test_suite.py`) | `9/9` (`100.0%`) in `1658.05 ms` | — | MEASURED |

Pending hardware measurements (tagged **`MEASURE ON DEVICE`** in JSON): `mobile_fps`, `qr_to_ar_launch_ms`, `vision_on_device_ms`, and `unity_frame_time_ms`.

---

## Known Limitations
- **Sony ELF-SR1 Plugin Not Installed (`No-SRD simulation mode`):** Neither Sony's `SRDisplayUnityPlugin` nor `SRDISPLAY_SDK_PRESENT` is installed in `src/kiosk_unity/`. Eyetracked lenticular 3D output is **not** active yet; Unity runs only in `No-SRD simulation mode` until an engineer completes [docs/sony_srd_integration_todo.md](docs/sony_srd_integration_todo.md).
- **On-Device Carving Classifier Not Trained (`Vision model not installed`):** `data/cards/` training video frames have not yet been captured from printed cards, so `src/frontend_webxr/assets/vision_model/model.json` does not exist yet. Tapping `SCAN RELIC` displays `"Vision model not installed"` rather than guessing (`train_classifier.py` + `tools/extract_frames.py` are ready once card videos are filmed).
- **3D `.glb` Assets Are Procedural Placeholders:** Only `Grand_Solstice_Sun_Temple.glb` (labeled `"Illustrative model"`) is shown for `shore_temple_vimana`; `pancha_rathas`, `arjunas_penance`, `krishnas_butter_ball`, and `mahishasuramardini_cave` display verified Wikimedia photographs and sourced historical cards until team-authored meshes are placed in `src/frontend_webxr/assets/models/`.
- **Heat Exposure Saved Is a Model Estimate:** Courtyard shade percentages (`80.5%`) come from `distance * (1 - dynamic_shade_factor)`, not physical pyranometer measurements.
- **Groq Online AI Latency Unmeasured Locally:** `GROQ_API_KEY` was not set during benchmarking, so `benchmark_kpis.py` marked Groq + Edge-TTS as `NOT MEASURED - no API key`; offline fallback responses and pre-cached MP3s were tested instead.
- **On-Device Phone & Unity Hardware Timing Unmeasured:** Mobile WebXR frame rate, QR launch time, TF.js mobile inference ms, and ELF-SR1 hardware frame time remain `MEASURE ON DEVICE`.
- **Self-Signed TLS Certificate Prompt:** Visiting `https://<LAN-IP>:8443` from mobile browsers requires accepting the local self-signed development certificate warning generated by `generate_ssl_certs.py`.

---

## Documentation & Deliverables
- **[Accelerator & Technical Report (`docs/ax.md`)](docs/ax.md)**
- **[System Architecture (`docs/architecture.md`)](docs/architecture.md)**
- **[Open-Source Software & Media Attribution (`docs/oss_attribution.md`)](docs/oss_attribution.md)** *(Wikimedia Commons photos retain their individual CC BY / CC BY-SA licenses in `docs/carving_cards/images/LICENSE-NOTICE.md`)*
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
Software repository code is released under the [MIT License](LICENSE) — Team Lunar Aurora (2026) *(excluding third-party libraries and Wikimedia Commons images governed by their licenses in `docs/oss_attribution.md`)*. **Antigravity** was used as an AI coding assistant during development.
