# 3-Minute Live Jury Demo Script & Backup Video Plan (`docs/demo_script.md`)

**Total Live Duration:** `3:00` (`180 seconds`)  
**Pre-Demo Check (2 minutes before jury arrives):**
1. From `src/backend/`, run `python generate_ssl_certs.py --ip <LAN_IP> && python start_servers.py` (starts HTTP `:8000` & self-signed LAN HTTPS `:8443`).
2. Launch Unity standalone kiosk on Windows (`.\LunarAurora_Kiosk.exe -windowed` on single-screen presentation laptops, or default `3840x2160` fullscreen on a 4K booth display + secondary operator screen), confirming **`No-SRD simulation mode`** and **`ONLINE NOAA`** appear on **`Operator HUD (second display)`**.
3. Place the printed matte A4 Mahabalipuram carving cards (`docs/carving_cards/print_5_carving_cards.html`) on the table and pre-open two browser tabs: `http://localhost:8000/ticket` and `https://localhost:8443/app/?demo=1`.

---

## 1. Step-by-Step 3-Minute Live Demo Flow

### `0:00 – 0:30` | Ticketing Counter, Multilingual QR & Self-Hosted WebXR Launch
- **Presenter Actions:**
  1. On `http://localhost:8000/ticket`, enter a juror's name, choose **English (`EN`)**, **Tamil (`TA`)**, or **Hindi (`HI`)**, and generate a ticket.
  2. Scan the QR code on an Android phone over LAN Wi-Fi (`https://<LAN-IP>:8443`) OR switch immediately to the pre-opened laptop tab (`https://localhost:8443/app/?demo=1`).
- **What the Jury Sees:** Instant local QR generation (`qrcode.min.js`) with zero CDN calls, personalized session header with language badge (`EN`/`TA`/`HI`), and unobstructed rear camera viewport (`Live Camera Feed`).
- **Exact Fallback (Hardware / Network Failure):**
  - *External internet blocked:* System operates 100% offline over a local laptop Wi-Fi hotspot (vendor JS/fonts + `54` cached MP3s are local).
  - *Phone Wi-Fi fails or self-signed TLS prompt blocks Android Chrome:* Switch immediately to the laptop Chromium tab at `http://localhost:8000/app/?demo=1` or `https://localhost:8443/app/?demo=1` and run the entire tour there.

---

### `0:30 – 1:10` | Indoor `DEMO MODE`, 7-Stop Progression, Manual **`I'M HERE`**, Audio & **`3D GUIDE`**
- **Presenter Actions:**
  1. Point to the yellow **`DEMO MODE (±2.5m)`** indicator pill and Demo Drawer buttons (`S1 Coast` through `S7 Durga`).
  2. Click `S2 Shore`, then `S4 Penance`, and tap **`I'M HERE`** in the bottom dock (or the `I'm here (25m)` check-in buttons inside ShadeMap) to demonstrate manual arrival fallback.
  3. Toggle **`3D GUIDE`** (top-right side pill) and tap **`RIDDLE`** (`+45 XP`), triggering offline audio + live subtitles.
- **What the Jury Sees:** Immediate stop updates across the **`4.13 km` one-way trail** (`~59 min` at assumed `70.0 m/min` walking speed), per-stop XP counter incrementing, glowing cyan wireframe corner avatar pulsing with audio narration, and synchronized subtitle bar (`#yt-subtitle-box`).
- **Exact Fallback (Hardware / Network Failure):**
  - *API geofence radii fetch fails / GPS blocked indoors:* Red fallback banner `"Auto-arrival unavailable, use I'M HERE"` triggers; tap **`I'M HERE`** in the bottom bar to advance normally.
  - *No `GROQ_API_KEY` or audio hardware muted:* Tap **`ASK`** -> `"Coolest shade?"`; backend trips its `2.5s` timeout cleanly into `OFFLINE_QA_BANK` while `#yt-subtitle-box` shows full text visually.

---

### `1:10 – 1:55` | NOAA Solar Geometry & Assumed-Shade OpenStreetMap **ShadeMap**
- **Presenter Actions:**
  1. Open **ShadeMap** (top HUD map icon) or scrub the **Demo Drawer IST Slider**. Set date to **`2027-01-11`** and slide hour **`09:00` -> `12:00` -> `16:00`**.
  2. Click **`SHADE`** in the bottom action dock to highlight the cave-rest route (`[1, 6, 7]` toward Varaha Cave).
- **What the Jury Sees:** Interactive SVG trail across all 7 OpenStreetMap (ODbL) stops with red shortest-path (`1229.6 m`) vs green shaded-path (`1369.7 m`) lines, live NOAA solar elevation (`30.75° -> 55.22° -> 25.23°`) and azimuth (`125.36° -> 173.33° -> 238.13°`), and clear disclosure banner showing **`assumed/illustrative weights (not measured sun exposure)`** (`81.4%` illustrative noon model score).
- **Exact Fallback (Hardware / Network Failure):**
  - *Camera feed denied / desktop lacks webcam:* ShadeMap SVG, telemetry API, NOAA slider, and check-in buttons function completely independently of WebRTC camera hardware.

---

### `1:55 – 2:30` | Honest Card Scanning (`SCAN RELIC`), **`Photo + Facts`** & PDF Travel Journal
- **Presenter Actions:**
  1. Aim camera at a printed Mahabalipuram carving card (`docs/carving_cards/print_5_carving_cards.html`) and tap **`SCAN RELIC`**.
  2. Explain transparently if `model.json` is not yet trained: HUD displays **`"Vision model not installed"`** (never fakes or boosts predictions). If trained on real card captures before finale, it loads only above `0.82` confidence and rejects card backs/surfaces (`background`).
  3. Tap **`Photo + Facts`** in the Demo Drawer (shows high-res Wikimedia monument photography + Wikipedia/UNESCO historical facts + clickable source URL; `Grand_Solstice_Sun_Temple.glb` stays hidden unless an optional team `<class_id>.glb` file is installed, in which case it labels **`"Model by Team Lunar Aurora - stylised"`** and **`"Not a survey-accurate reconstruction."`**).
  4. Tap **`SNAP`**, then **`End` -> `Download PDF Travel Journal`**.
- **What the Jury Sees:** Verified monument photography + citation links (and facts-only cards on non-card stops `S1`/`S6`), watermarked snapshot capture, and instant downloadable multi-page `.pdf` expedition souvenir (`fpdf2`).
- **Exact Fallback (Hardware / Network Failure):**
  - *Webcam fails / lighting washed out:* Skip live card scan, display the physical printed A4 duplex cards (front photos + CC attribution backs) in hand while tapping **`Photo + Facts`** and exporting the PDF Travel Journal directly.

---

### `2:30 – 3:00` | Unity 6 Tabletop Kiosk (**`No-SRD simulation mode`**) & Honest Readiness Disclosure
- **Presenter Actions:**
  1. Switch focus to `LunarAurora_Kiosk.exe` (`-windowed` or dual-display `Operator HUD (second display)`).
  2. Press keys `1` / `2` / `3` to inspect the procedural **`Illustrative model`** exhibits, press `E` for exploded layers, and scrub the Unity **NOAA Date & IST Hour** slider to rotate `SolsticeSunLight` in sync with WebXR.
  3. Conclude with [`docs/known_limitations.md`](known_limitations.md): explicitly state Unity runs in **`No-SRD simulation mode`** (`SRDISPLAY_SDK_PRESENT` undefined until official Sony plugin + hardware), geofence radii (`20–75 m`) await Mahabalipuram site validation, and device KPIs await Android field profiling ([`docs/device_test_checklist.md`](device_test_checklist.md)).
- **What the Jury Sees:** Clean 3D temple inspection, second-screen `Operator HUD` displaying live `ONLINE NOAA` telemetry matching the mobile WebXR view, and an authentic engineering transparency posture.
- **Exact Fallback (Hardware / Network Failure):**
  - *Backend server disconnects:* Unity transitions cleanly into **`SERVER OFFLINE (STANDBY)`** with neutral directional lighting while local exhibit switching (`1`/`2`/`3`), exploded view (`E`), and mouse orbit keep working.
  - *Unity window crashes or venue PC lacks DirectX/GPU headroom:* Leave FastAPI + Chrome WebXR open (`Photo + Facts`, `3D GUIDE`, ShadeMap) and walk through verified screenshots/architecture directly.

---

## 2. 60-Second Pre-Recorded Backup Video Plan

Record one continuous `1080p @ 30fps` screen + camera-cut MP4 (`backup_demo_60s.mp4`, stored locally outside git) using OBS / Windows Game Bar **the evening before** Phase 2 judging / Finale in case venue Wi-Fi, projectors, or laptop GPU fail:

| Segment | Content to Capture on Screen & Camera | Spoken Voiceover Focus |
| :---: | :--- | :--- |
| **`0:00 – 0:12`** | Issue a Tamil (`TA`) or English (`EN`) ticket on `/ticket`, scan QR code, show Android Chrome opening `https://<LAN-IP>:8443/app/` with live camera + zero CDN network trace (DevTools Network tab). | Self-hosted zero-CDN WebXR ticketing & LAN TLS for outdoor smartphones. |
| **`0:12 – 0:26`** | Show `?demo=1` **`DEMO MODE`**, tap **`I'M HERE`** & **`RIDDLE`** (`+45 XP`), toggle **`3D GUIDE`**, and show synced EN/TA/HI voice subtitles (`#yt-subtitle-box`). | Hands-free heritage guide with `2.5s` offline failover & manual geofence override. |
| **`0:26 – 0:40`** | Open **ShadeMap**, scrub **`2027-01-11` (`09:00 -> 12:00 -> 16:00`)**, tap **`SHADE`**, pointing out real NOAA solar telemetry + OSM walking graph + explicit **`assumed shade weights`** label. | Physical NOAA solar math + ODbL footways cleanly separating measured facts from uncalibrated weights. |
| **`0:40 – 0:50`** | Hold `LUNA-CARD-02` printed card, tap **`SCAN RELIC`** (show trained recognition or honest `"Vision model not installed"` state), open **`Photo + Facts`** + **`SNAP`** + **`Download PDF Travel Journal`**. | Verified Wikimedia/Wikipedia attribution + PDF souvenir generation. |
| **`0:50 – 0:60`** | Show `LunarAurora_Kiosk.exe -windowed` displaying **`No-SRD simulation mode`**, **`Operator HUD (second display)`**, `E` exploded view, and NOAA sun slider matching WebXR. | Dual-mode Unity 6 kiosk prepared for Sony ELF-SR1 hardware plugin hookup. |
