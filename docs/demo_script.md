# 3-Minute Live Jury Demo Script (`docs/demo_script.md`)

**Total Duration:** `3:00` (`180 seconds`)  
**Pre-Demo Check (2 minutes before jury arrives):**
1. From `src/backend/`, run `python start_servers.py` (starts HTTP `:8000` & self-signed HTTPS `:8443`).
2. Launch Unity standalone kiosk in desktop window (`.\LunarAurora_Kiosk.exe -windowed`) or `3840x2160` fullscreen if on booth screen, confirming `ONLINE NOAA` appears in `Operator HUD (second display)`.
3. Have printed A4 Mahabalipuram carving cards (`docs/carving_cards/print_5_carving_cards.html`) on the table and open `http://localhost:8000/ticket` + `https://<LAN-IP>:8443/app/?demo=1` in browser tabs ready to show.

---

## Step-by-Step Timed Flow & Fallbacks

### `0:00 – 0:30` | Ticketing Counter, Multilingual QR & Self-Hosted WebXR Launch
- **Action:**
  1. On laptop browser at `http://localhost:8000/ticket`, type a juror's name, pick language (`EN`, `TA`, or `HI`), and issue a ticket.
  2. Scan the offline `qrcode.min.js` QR code on a phone (over LAN Wi-Fi on HTTPS `:8443`), OR click directly on the laptop demo browser tab (`?demo=1`).
- **What to state honestly:** Zero external CDN dependencies; TLS cert includes LAN IP SAN (`generate_ssl_certs.py`).
- **Fallbacks:**
  - *Internet / External Wi-Fi down:* Works completely over an isolated local Wi-Fi hotspot (`python start_servers.py`); QR generation (`qrcode.min.js`) and UI icons/libs are vendored locally.
  - *Phone fails to connect over LAN Wi-Fi / cert blocked:* Switch directly to laptop Chromium tab at `https://localhost:8443/app/?demo=1` or `http://localhost:8000/app/?demo=1`.

### `0:30 – 1:10` | Indoor `DEMO MODE` (`?demo=1`), 7-Stop Trail & Sourced Audio + Riddles
- **Action:**
  1. Point out the explicit **`DEMO MODE (±2.5m)`** pill and drawer showing buttons `S1`–`S7`.
  2. Tap `S2 Shore` and `S4 Penance` to simulate walking progression across the **`4.13 km` one-way trail** (`~59 min` total walking across all 7 monuments) without outdoor GPS, or tap manual **`I'M HERE`** in the bottom bar / ShadeMap check-in grid for any stop `S1–S7`.
  3. Tap **RIDDLE** to answer the monument question (`+45 XP`) and show offline EN/TA/HI audio narration playback (`54` pre-cached MP3s) & `3D GUIDE` corner avatar toggle.
- **Fallbacks:**
  - *Internet down / `GROQ_API_KEY` missing:* Tap `ASK` -> ask *"Coolest shade?"* or preset chips. Backend enforces a `2.5s` timeout failsafe and serves `OFFLINE_QA_BANK` + local MP3 cache immediately.
  - *Device audio muted / Bluetooth speaker disconnects:* Live subtitle bar (`#yt-subtitle-box`) renders synchronized transcript text continuously.

### `1:10 – 1:55` | Real NOAA Solar Geometry + OpenStreetMap ShadeMap
- **Action:**
  1. Open **ShadeMap** (`btn-open-map-top`). Set Date = **`2027-01-11`** (Finale date) and scrub the **IST Hour** slider (`09:00` -> `12:00` -> `16:00`).
  2. Point out live recalculation from `GET /api/site/telemetry?date=2027-01-11&hour=...`: elevation changes (`30.75°` -> `55.22°` -> `25.23°`), azimuth changes (`125.36°` -> `173.33°` -> `238.13°`), shortest OSM walk (`1229.6 m`) vs. assumed-shade route (`1369.7 m`).
- **What to state honestly:** Coordinates and distances come from OpenStreetMap (ODbL); shade weights (`81.4%` illustrative score at noon) are **assumed/illustrative model weights — not measured sun exposure**.
- **Fallbacks:**
  - *Camera fails / `getUserMedia` blocked:* ShadeMap SVG, telemetry sliders, and tour state run 100% independently of camera access.

### `1:55 – 2:30` | Honest Vision Card Handling, Illustrative 3D & PDF Travel Journal
- **Action:**
  1. Hold printed Mahabalipuram cards (`print_5_carving_cards.html`) in front of camera and tap **`SCAN RELIC`**.
  2. Explain openly: **`"Vision model not installed"`** appears because card training videos (`data/cards/`) have not yet been captured; there are zero fake keyword/confidence boosts.
  3. Tap **`Photo + Facts`** in `DEMO MODE` (shows verified Wikimedia monument photography + Wikipedia/UNESCO historical notes for every stop; `Grand_Solstice_Sun_Temple.glb` placeholder mesh is hidden from WebXR UI), capture a **`SNAP`** photo, and tap **Finish -> Download PDF Travel Journal** (`fpdf2`).
- **Fallbacks:**
  - *Camera hardware fails / no webcam:* Skip live scan, show `docs/carving_cards/print_5_carving_cards.html` physical printbacks (with Wikimedia Commons attribution) and trigger PDF Travel Journal export directly.

### `2:30 – 3:00` | Unity 6 Tabletop Kiosk (`No-SRD Simulation Mode`) & Known Limitations
- **Action:**
  1. Bring `LunarAurora_Kiosk.exe` into focus (`-windowed` on single laptop screen, or dual screen showing **`Operator HUD (second display)`**).
  2. Toggle exhibits `1`/`2`/`3` (procedural Mahabalipuram **Illustrative model** placeholders), press `E` (Exploded view), and move the Unity **NOAA Date & IST Hour** slider to show synchronized `SolsticeSunLight` direction and `ONLINE NOAA` telemetry matching the WebXR app.
  3. Close cleanly with `docs/known_limitations.md` summary (Sony plugin pending install -> `No-SRD simulation mode`; classifier pending card videos; hardware KPIs marked `MEASURE ON DEVICE`).
- **Fallbacks:**
  - *Unity Kiosk crashes / GPU unavailable on venue laptop:* Show pre-verified build logs + fall back directly to WebXR `Photo + Facts` + ShadeMap running on the FastAPI server (`http://localhost:8000/app/?demo=1`).
  - *FastAPI backend stops while Kiosk runs:* Unity drops gracefully into **`SERVER OFFLINE (STANDBY)`** with neutral key lighting and zero crash while offline controls (`1`/`2`/`3`, `E`, orbit) continue working.
