# Setup, Deployment & Jury Demo Guide

## 1. Prerequisites
- Python 3.11+ (`fastapi`, `uvicorn`, `sqlalchemy`, `networkx`, `edge-tts`, `groq`, `fpdf2`, `pillow`, `qrcode`, `cryptography`)
- Optional `GROQ_API_KEY` environment variable (the system operates cleanly offline even without an external key via the 2.5s failsafe & 44-MP3 local cache).
- Unity 6 (`6000.6.9f1`) if recompiling `src/kiosk_unity/` from source (a precompiled `Builds/Windows_SonySRDisplay/LunarAurora_Kiosk.exe` binary is included).

## 2. Backend Initialization & Verification
Run from `src/backend/`:

```powershell
# 1. Seed 7 Mahabalipuram stops, riddles, dual-route edges, and 5 carving cards
python init_db.py

# 2. (Optional) Regenerate 44 offline EN/TA/HI audio cache MP3s
python pre_cache_audio.py

# 3. Verify all 9 end-to-end multimodal & PDF journal tests
python test_suite.py

# 4. Run 20-iteration KPI latency benchmark
python benchmark_kpis.py

# 5. Start dual HTTP (:8000) & SSL HTTPS (:8443) servers
python start_servers.py
```

## 3. Launching Mobile WebXR & Jury Table Demo Mode
1. Open the ticketing portal on your server browser: `http://localhost:8000/ticket` (or scan `/qr` with your phone over LAN Wi-Fi).
2. Create a ticket in **English (`EN`)**, **Tamil (`TA`)**, or **Hindi (`HI`)** and scan the QR code on an Android Chrome mobile device (tap *Advanced -> Proceed* for the local self-signed HTTPS camera certificate on port `8443`).
3. **Indoors at a Jury Table? Activate Demo Mode (`?demo=1` or triple-tap the top GPS pill):**
   - **Teleport Stops S1-S7:** Jump between all 7 Mahabalipuram stations with simulated **`+-2.5m` GPS accuracy**.
   - **Sun Time Slider (`09:00` - `16:00`):** Open **ShadeMap** to watch the red exposed sun path vs. green shaded canopy route recompute live heat savings (`~76%`).
   - **Print Carving Cards:** Print `docs/carving_cards/print_5_carving_cards.html` on matte cardstock, aim your camera, tap **SCAN RELIC**, and scrub the **Era Slider (`Present Ruin <-> 700 CE Zenith`)**.
   - **AR Snapshots & PDF Travel Journal:** Tap **SNAP** at any stop and download your multi-page **PDF Travel Journal** upon completing or ending the tour.

## 4. Running the Sony ELF-SR1 Kiosk (`No-SRD Simulation Mode` Included)
1. Ensure the backend server (`http://localhost:8000`) is running so live telemetry (`2.0s` poll interval) syncs automatically.
2. Launch `src/kiosk_unity/Builds/Windows_SonySRDisplay/LunarAurora_Kiosk.exe`.
3. Keyboard Controls: `1` / `2` / `3` switch 3D exhibits, `E` toggles exploded layers, `S` toggles **No-SRD Simulation Mode** / hardware SDK parity, and `H` hides the overlay GUI.
