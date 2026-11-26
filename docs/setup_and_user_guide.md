# Setup, Deployment & Jury Demo Guide

## 1. Prerequisites
- **Python 3.11+** with dependencies in `src/backend/requirements.txt`.
- **Training Dependencies (only when ready to train the card classifier):** `src/backend/requirements-train.txt`.
- **Optional `GROQ_API_KEY` environment variable:** Without an API key, live Groq AI benchmark is skipped (`NOT MEASURED - no API key`), while guided sessions remain operational offline via the `2.5s` failsafe, `OFFLINE_QA_BANK`, and **`54`** pre-cached EN/TA/HI MP3s in `src/backend/static/audio_cache/`.
- **Unity `6000.6.9f1` (optional):** Only required to recompile `src/kiosk_unity/` from source. Compiled Windows builds are distributed via [GitHub Releases](https://github.com/Rohitbapu/Lunar-Aurora/releases) (`Builds/` is gitignored).

---

## 2. Backend Setup, Tests & Benchmarks
Run inside your Python environment from `src/backend/`:

```powershell
# 1. Seed 7 OSM-located Mahabalipuram stops, 13 OSM walkway distances (assumed shade weights), and 5 cards
python init_db.py

# 2. (Optional) Regenerate the 54 offline EN/TA/HI audio cache MP3s
python pre_cache_audio.py

# 3. Verify all 9 API tests + OSM attribution + NOAA solar reference table (09:00, 12:00, 16:00 IST)
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
2. Issue a ticket in **English (`EN`)**, **Tamil (`TA`)**, or **Hindi (`HI`)** and open `https://<LAN-IP>:8443/app/...` on mobile Chrome (accept the local self-signed TLS prompt for camera/sensor permissions).
3. **Indoors at a Jury Table? Open Demo Mode (`?demo=1` or triple-tap the top GPS pill):**
   - **Stops S1–S7 Teleport:** Jump across all 7 OpenStreetMap-referenced Mahabalipuram monuments.
   - **NOAA Date & Time Slider:** Adjust date (defaults to Finale **`2027-01-11`**) and IST hour (`06:00–18:00`) in the demo drawer or **Mahabalipuram ShadeMap**. Walking distances come from OpenStreetMap; relative shade scores are labeled as **assumed/illustrative weights (not measured sun exposure)**.
   - **Printed Carving Cards:** Print `docs/carving_cards/print_5_carving_cards.html` (double-sided A4 matte). Until `model.json` is trained from user-recorded card videos, `visionEngine.js` reports **`"Vision model not installed"`**.

---

## 4. Running the Unity 6 Kiosk (`No-SRD Simulation Mode`)
1. Start the FastAPI backend (`python start_servers.py`) so `GET /api/site/telemetry` responds on `http://localhost:8000`.
2. Download or build `LunarAurora_Kiosk.exe` ([GitHub Releases](https://github.com/Rohitbapu/Lunar-Aurora/releases)).
3. **Display Modes:**
   - Default launch opens **`3840x2160` fullscreen** (`FullScreenWindow`) for exhibition kiosks.
   - Pass **`-windowed`** (or `--windowed`) for desktop development & debugging:
     ```powershell
     .\LunarAurora_Kiosk.exe -windowed
     ```
4. Because Sony's `SRDisplayUnityPlugin` is not installed (`SRDISPLAY_SDK_PRESENT` undefined), the app runs in **`No-SRD simulation mode`** with **`Operator HUD (second display)`** on Display 1 when present.
5. **Controls:** `1`/`2`/`3` switch procedural **Illustrative model** placeholders, `E` toggles exploded layers, the **NOAA Date & IST Hour Slider** queries `/api/site/telemetry?date=...&hour=...`, and `H`/`O` toggle HUD panels.

---

## 5. Training the 6-Class Carving Classifier (After Video Capture)
1. Print `docs/carving_cards/print_5_carving_cards.html`.
2. Record short phone videos per card (`<class>__session_XX.mp4`) plus a `background` clip covering blank cardstock, card backs, tables, and room clutter. Do **not** use synthetic training data.
3. Extract frames (`0.25s` interval) & train (`requirements-train.txt`):
   ```powershell
   python tools/extract_frames.py path/to/videos_folder
   cd src/backend
   python train_classifier.py
   ```
