# System Architecture & Technical Design

**Lunar Aurora** connects a **Mobile WebXR companion** (`src/frontend_webxr/`) and a **Unity 6 desktop kiosk** (`src/kiosk_unity/`) to an offline-resilient **FastAPI + SQLite** backend (`src/backend/`).

## High-Level Architecture

```mermaid
flowchart LR
    V["Mobile WebXR Browser<br/>(Three.js r128 + TF.js 4.17 + WebAudio)<br/>Self-hosted vendor assets"] <-->|"HTTPS :8443<br/>REST + Static Media"| API["FastAPI Backend<br/>HTTP :8000 / Self-Signed HTTPS :8443"]
    K["Unity 6 Desktop Kiosk<br/>(No-SRD simulation mode +<br/>Operator HUD second display)"] -->|"Poll 2.0s GET /api/site/telemetry?date=&hour="| API
    API --> DB[("SQLite Database<br/>lunar_aurora.db")]
    API --> SOLAR["NOAA Solar + OSM Footpath Graph<br/>(NetworkX + ODbL distances + Assumed shade weights)"]
    API --> AI["Groq Llama-3.3-70B & Edge-TTS<br/>(2.5s Timeout + 54 EN/TA/HI MP3 Cache)"]
    API --> PDF["PDF Travel Journal Export<br/>(fpdf2 + Pillow Photo Embeds)"]
```

## Directory Layout
- `src/backend/`:
  - `app/main.py` & `app/models/entities.py`: FastAPI setup, zero-CDN static mounts, SQLAlchemy models storing `source`, `coordinate_source`, and `distance_source`.
  - `app/services/routing_service.py`: Full **NOAA General Solar Position Equations** (`date` default `2027-01-11`, `hour`, lat `12.6165° N`, lon `80.19° E`) + NetworkX Dijkstra dual-path solver over OpenStreetMap walking distances and **assumed/illustrative** canopy shade weights (`not measured sun exposure`).
  - `app/services/groq_service.py` & `app/services/tts_service.py`: `2.5s` async timeout with `OFFLINE_QA_BANK` and `54` pre-synthesized EN/TA/HI MP3s (`src/backend/static/audio_cache/`).
  - `app/services/vision_knowledge.py`: Sourced metadata for the 5 Mahabalipuram carving classes (`shore_temple_vimana`, `pancha_rathas`, `arjunas_penance`, `krishnas_butter_ball`, `mahishasuramardini_cave`); never guesses on empty/background labels.
  - `init_db.py`: Seeds 7 Mahabalipuram stops with OpenStreetMap ODbL coordinates, 13 OSM walkway distances (`255.0 m`–`1831.2 m`) with assumed shade factors (`0.10`–`0.94`), and Wikipedia/UNESCO source URLs.
  - `train_classifier.py` & `requirements-train.txt`: MobileNetV2 pipeline (untrained until real `data/cards/` captures are recorded).
  - `generate_ssl_certs.py`, `test_suite.py`, `benchmark_kpis.py`.
- `src/frontend_webxr/`:
  - Locally vendored `three.min.js`, `GLTFLoader.js`, `tf.min.js`, `qrcode.min.js`, Font Awesome `6.5.1` (`src/frontend_webxr/vendor/`).
  - `js/visionEngine.js`: Reports `"Vision model not installed"` until `model.json` exists.
  - `js/shadeMap.js`, `js/locationTracker.js`, `js/tourManager.js`: OpenStreetMap metric `(x, y)` coordinates with dynamic SVG viewport framing, NOAA date/hour controls, and explicit `"assumed weights"` disclosure.
  - `js/arScene.js` & `js/spatialAudio.js`: Procedural `Grand_Solstice_Sun_Temple.glb` (`Illustrative model`) for Shore Temple only + `DeviceOrientationEvent` binaural panner alignment.
- `src/kiosk_unity/`:
  - Unity `6000.6.9f1` standalone Windows x64 project (`No-SRD simulation mode`; `SRDISPLAY_SDK_PRESENT` undefined).
  - Defaults to `3840x2160` `FullScreenWindow`, with CLI `-windowed` switch for development, `KioskNetworkBridge.cs` polling `/api/site/telemetry?date=...&hour=...`, and `Operator HUD (second display)`.
- `docs/`: Documentation, `oss_attribution.md`, `known_limitations.md`, `sony_srd_integration_todo.md`, and A4 printable cards.

## Core API Endpoints
- `GET /ticket`, `GET /qr`, `POST /api/ticket/create`: QR ticketing in `EN`, `TA`, or `HI`.
- `POST /api/session/start`, `/advance`, `/end`, `/riddle`: Session persistence & `+45 XP` riddles.
- `GET /api/routing/solar-status?date=YYYY-MM-DD&hour=HH.H`: NOAA declination, equation of time, hour angle, solar elevation, azimuth.
- `GET /api/site/telemetry?start_id=1&target_id=7&date=YYYY-MM-DD&hour=HH.H`: Shortest vs. assumed-shade Dijkstra routes (OSM distances + assumed weights), NOAA geometry, active stop visitor counts.
- `POST /api/vision/identify`: Matches card class labels without guessing.
- `POST /api/tour/{session_id}/photo` & `/journal`: Watermarked AR snapshots + `fpdf2` PDF journals.

## Tooling Disclosure
Developed by Team Lunar Aurora with **Antigravity** used as an AI coding assistant during system debugging, refactoring, and verification.
