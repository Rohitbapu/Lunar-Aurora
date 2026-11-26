# Setup, Deployment & Jury Demo Guide

## 1. Prerequisites
- **Python 3.11+** with dependencies in `src/backend/requirements.txt` (`fastapi`, `uvicorn`, `sqlalchemy`, `networkx`, `edge-tts`, `groq`, `fpdf2`, `pillow`, `qrcode`, `cryptography`, `httpx`, `aiofiles`, `psycopg2-binary`).
- **Training Dependencies (only if training the carving card classifier):** `src/backend/requirements-train.txt` (`tensorflow`, `tensorflowjs`, `scikit-learn`, `matplotlib`, `opencv-python-headless`).
- **Optional `GROQ_API_KEY` environment variable:** Without an API key, live Groq AI latency is skipped (`NOT MEASURED - no API key`), while guided sessions remain operational offline via the `2.5s` timeout failsafe, `OFFLINE_QA_BANK`, and **`54`** pre-cached EN/TA/HI MP3s in `src/backend/static/audio_cache/`.
- **Unity `6000.6.9f1` (optional):** Only needed if recompiling `src/kiosk_unity/` from source. Compiled Windows binaries are distributed via [GitHub Releases](https://github.com/Rohitbapu/Lunar-Aurora/releases) (`Builds/` is gitignored).

---

## 2. Backend Setup, Tests & Benchmarks
Run inside a clean Python virtual environment from `src/backend/`:

```powershell
# 1. Seed 7 sourced Mahabalipuram stops, 13 path edges, 5 card artifacts, and 3 quests
python init_db.py

# 2. (Optional) Regenerate the 54 offline EN/TA/HI audio cache MP3s
python pre_cache_audio.py

# 3. Verify all 9 API tests + NOAA solar position reference table (09:00, 12:00, 16:00 IST)
python test_suite.py

# 4. Run 20-iteration backend KPI benchmarks (writes timestamped benchmark_results_<ts>.json)
python benchmark_kpis.py

# 5. Generate/refresh TLS certs with your LAN IP SAN for mobile camera HTTPS (:8443)
python generate_ssl_certs.py --ip <YOUR_LAN_IP>

# 6. Start HTTP (:8000) and HTTPS (:8443) servers
python start_servers.py
```

---

## 3. Running Mobile WebXR & Jury Table Demo Mode
1. Open `http://localhost:8000/ticket` (or scan `/qr` over LAN Wi-Fi).
2. Issue a ticket in **English (`EN`)**, **Tamil (`TA`)**, or **Hindi (`HI`)** and open the generated URL (`https://<LAN-IP>:8443/app/...` on mobile Chrome; accept the self-signed local certificate warning for `getUserMedia` camera access).
3. **Indoors at a Jury Table? Open Demo Mode (`?demo=1` or triple-tap the top GPS pill):**
   - **Stops S1–S7 Teleport:** Simulate walking progression across all 7 Mahabalipuram locations.
   - **NOAA Date & Time Slider:** Adjust date (defaults to Finale **`2027-01-11`**) and IST hour (`06:00–18:00`) either in the demo drawer or inside **Mahabalipuram ShadeMap**. Routes and solar elevation/azimuth update dynamically from `/api/site/telemetry`. Heat savings are clearly marked as a **`model estimate`**.
   - **Printed Carving Cards:** Print `docs/carving_cards/print_5_carving_cards.html` (double-sided A4 matte recommended). Note that until card sessions are recorded into `data/cards/` and trained (`train_classifier.py`), `visionEngine.js` will accurately report **`"Vision model not installed"`**.
   - **AR Snapshots & PDF Journal:** Capture `SNAP` photos and export the `fpdf2` PDF Travel Journal upon completion.

---

## 4. Running the Unity 6 Kiosk (`No-SRD Simulation Mode`)
1. Start the FastAPI backend (`python start_servers.py`) so `GET /api/site/telemetry` responds on `http://localhost:8000`.
2. Download or build `LunarAurora_Kiosk.exe` (see [GitHub Releases](https://github.com/Rohitbapu/Lunar-Aurora/releases)).
3. Launch `LunarAurora_Kiosk.exe`. Because Sony's `SRDisplayUnityPlugin` is not installed (`SRDISPLAY_SDK_PRESENT` undefined), the kiosk runs in **`No-SRD simulation mode`** with **`Operator HUD (second display)`** shown in window overlay and mirrored onto Display 1 if a secondary display is attached.
4. **Controls:**
   - `1`, `2`, `3`: Switch procedural **Illustrative model** placeholders (Shore Temple, Pancha Rathas, Krishna's Butterball)
   - `E`: Toggle exploded layers (Shore Temple tiers)
   - **NOAA Date & IST Hour Slider**: Re-queries `/api/site/telemetry?date=...&hour=...` to orient directional sunlight to NOAA elevation/azimuth
   - `H` / `O`: Toggle overlay / operator panel | `S`: Refresh simulation state

---

## 5. Training the 6-Class Carving Classifier (When Cards Are Printed)
1. Print the 5 Wikimedia photo cards (`docs/carving_cards/print_5_carving_cards.html`).
2. Record short phone videos per card (`<class>__session_XX.mp4`) plus a `background` video covering blank cardstock, card backs, tables, and room clutter.
3. Extract frames at `0.25s` intervals:
   ```powershell
   python tools/extract_frames.py path/to/videos_folder
   ```
4. Train and export TF.js weights (using `requirements-train.txt`):
   ```powershell
   cd src/backend
   python train_classifier.py
   ```
   This exports `model.json` + shards into `src/frontend_webxr/assets/vision_model/`, after which `visionEngine.js` automatically enables on-device inference.
