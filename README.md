# Lunar Aurora — Glasses-Free Sony ELF-SR1 & WebXR Heritage Sanctuary Guide

[![License: MIT](https://img.shields.io/badge/License-MIT-00e5ff.svg)](LICENSE)
[![Domain: Mahabalipuram Heritage](https://img.shields.io/badge/UNESCO%20Site-Mahabalipuram%2012.6165%C2%B0N-f4c430.svg)](docs/architecture.md)
[![Offline Failsafe](https://img.shields.io/badge/Cloud%20Timeout%20SLA-2.5s%20%2B%2044%20MP3%20Cache-00e676.svg)](docs/ax.md)

**Team Lunar Aurora** — *Ayyappan Ayyanan, Vikrant R M, Rohit Bapu S B* (Sethu Institute of Technology)

> **Video Showcase Placeholders:**
> - **90-Second Pitch & Live Demo:** `[YouTube Pitch Video Link — Pending Final Capture before Dec 25 Submission]`
> - **Technical Walkthrough (Sony ELF-SR1 + WebXR + ShadeMap):** `[YouTube Walkthrough Video Link — Pending Final Capture before Dec 25 Submission]`

---

## What Is Lunar Aurora?
**Lunar Aurora** is an open-air spatial computing guide designed for India's coastal stone monuments (**Mahabalipuram Shore Temple Complex**). It pairs:
1. **Zero-Install Mobile WebXR Companion (`src/frontend_webxr/`):** Camera-first AR viewport keeping stone carvings unobstructed while walking, featuring on-demand `.glb` **3D Era Slider** reconstruction (`Present Ruin <-> 700 CE Zenith`), toggleable corner **`[3D GUIDE]`**, **HRTF Binaural Audio** linked to mobile `DeviceOrientationEvent`, **6-class carving card recognition (`>= 0.82` threshold)**, interactive **Stop Riddles (`+45 XP`)**, watermarked **`[SNAP]`** photography, and a downloadable **PDF Travel Journal**.
2. **Dual-Route Solar ShadeMap (`shadeMap.js` + `routing_service.py`):** Compares **Shortest Sun-Exposed Paths (Red)** against **Solar-Optimized Shaded Canopy Paths (Green)** using NOAA solar geometry calibrated to `12.6165° N` and NetworkX Dijkstra optimization (**76.0% Heat Exposure Saved** across the Shore Temple courtyard).
3. **Glasses-Free Sony ELF-SR1 Holographic Kiosk (`src/kiosk_unity/`):** Unity 6 standalone visitor-center exhibit (`VSync = 0`, Dual-Display lenticular UI isolation, `No-SRD Simulation Mode` toggle) that polls `GET /api/site/telemetry` every **2 seconds** to display live courtyard crowd pins and solar shade heatmaps.

---

## Verified KPI Benchmarks (20-Iteration TestClient Run)

| Operation / Subsystem | Measured Mean Latency | Measured P95 Latency | Notes / SLA Target |
| :--- | :---: | :---: | :--- |
| **Solar Dual-Route Telemetry** (`GET /api/site/telemetry`) | **4.89 ms** | **20.55 ms** | Returns both Shortest vs. Shaded paths + `76.0%` heat saved |
| **Vision Identification & Audio** (`POST /api/vision/identify`) | **9.71 ms** | **43.16 ms** | Matches 5 Mahabalipuram carving classes + Quest badge unlock |
| **Personalized Session Start** (`POST /api/session/start`) | **6.62 ms** | **7.87 ms** | Backed by 2.5s cloud timeout & 44 offline EN/TA/HI MP3s |
| **Historical Stop Riddle Quiz** (`POST /api/session/riddle`) | **6.61 ms** | **7.53 ms** | Instant XP award & badge persistence |
| **PDF Travel Journal Export** (`POST /api/tour/{id}/journal`) | **11.44 ms** | **24.39 ms** | Multi-section illustrated PDF with embedded memory snapshots |

All 9 automated end-to-end backend tests (`python src/backend/test_suite.py`) pass cleanly.

---

## Documentation & Deliverables
- **[Accelerator & MathWorks Formulation Report](docs/ax.md)** (Mandatory partner & algorithmic report)
- **[Open-Source Software & Asset Attribution](docs/oss_attribution.md)** (Mandatory OSS disclosure)
- **[System Architecture & API Design](docs/architecture.md)**
- **[XR Domain Justification (WebXR + Sony ELF-SR1 vs. HMD)](docs/xr_domain_justification.md)**
- **[Setup, Jury Table Demo Mode & User Guide](docs/setup_and_user_guide.md)**
- **[Printable 5-Card Mahabalipuram Carving Sheet](docs/carving_cards/print_5_carving_cards.html)**

---

## Quick Start
```powershell
cd src/backend
python init_db.py
python test_suite.py
python start_servers.py
```
Then open `http://localhost:8000/ticket` for counter onboarding or `http://localhost:8000/app/?demo=1` to test **Jury Table Demo Mode** immediately.

## License
Released under the [MIT License](LICENSE) — Team Lunar Aurora (2026).
