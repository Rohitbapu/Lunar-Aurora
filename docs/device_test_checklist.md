# Android Phone & Field Geofence Test Checklist (`NEEDS DEVICE TEST`)

All hardware/field test results remain **blank (`[ ]` / empty cells)** until Team Lunar Aurora runs these checks on **two physical Android phones** over LAN HTTPS (`https://<LAN-IP>:8443`) and onsite at Mahabalipuram.

> **Do NOT pre-fill, estimate, or copy desktop values into these blanks.**

---

## 1. Pre-Flight Setup (Server + Two Android Chrome Devices)
- [ ] Start backend from `src/backend/`: `python generate_ssl_certs.py --ip <LAN_IP> && python start_servers.py`
- [ ] Confirm both phones sit on the same LAN / mobile hotspot as the host laptop.
- [ ] Phone A & Phone B models / Android & Chrome versions recorded below:
  - **Phone A (Model / OS / Chrome):** `____________________`
  - **Phone B (Model / OS / Chrome):** `____________________`
  - **LAN IP & Port Tested:** `https://____________________:8443`

---

## 2. Core Functional Checklist (Phone A & Phone B Over HTTPS `:8443`)

| Check Item | Phone A Pass/Fail | Phone B Pass/Fail | Observed Notes / Issues |
| :--- | :---: | :---: | :--- |
| **QR Scan -> LAN HTTPS TLS Accept -> App Interactive (`QR-to-AR` stopwatch)** | `___` (`_____ ms`) | `___` (`_____ ms`) | |
| **Camera Permission & Live Rear Camera Feed (`getUserMedia`)** | | | |
| **Outdoor GPS Lock (`watchPosition` active GPS badge)** | | | |
| **Manual Check-In Button (`I'M HERE`) Updates Stop & XP** | | | |
| **Demo Mode Toggle (`?demo=1` or triple-tap GPS pill) & `S1–S7` Teleport** | | | |
| **UI Mode Behavior: `Photo + Facts` Panel (or Stylised `<class_id>.glb` + Disclaimer + Wireframe/Solid Slider if present)** | | | |
| **Corner Avatar Toggle (`3D GUIDE` button shows/hides animated wireframe guide)** | | | |
| **EN / TA / HI Narration Playback + Subtitles (`#yt-subtitle-box`)** | | | |
| **Head/Phone Rotation Moves Binaural Sound (`DeviceOrientationEvent` -> HRTF WebAudio Panner)** | | | |
| **HUD FPS Counter (`hud-fps-counter`) Sustained Frame Rate While Walking** | `____ FPS` | `____ FPS` | |
| **Watermark Photo Snapshot (`SNAP`) + PDF Travel Journal Export (`POST /journal`)** | | | |
| **Trained Vision Classifier (`SCAN RELIC` Latency & Recognition — once `model.json` installed)** | `____ ms` | `____ ms` | |

---

## 3. Stopwatch QR-to-AR Launch Timing (`qr_to_ar_launch_ms`)

Start stopwatch at QR camera scan tap on `/ticket` or `/qr`; stop when rear camera feed + Stop 1 welcome HUD are interactive (note whether TLS warning was already accepted vs cold first-time visit):

| Trial | Device | Cold TLS vs Repeat Visit | Measured Time (`ms`) |
| :---: | :--- | :--- | :---: |
| `1` | Phone A | | |
| `2` | Phone A | | |
| `3` | Phone B | | |
| `4` | Phone B | | |

---

## 4. Mahabalipuram Per-Stop Geofence Field Test (`UNVERIFIED -> CALIBRATE ON SITE`)

For each monument stop `S1–S7`, test **once standing at the real monument center/viewing zone** and **once stepping outside the configured `arrival_radius_m`**, recording the Android GPS reported accuracy (`± m`), true distance error, and whether auto-arrival triggered cleanly without adjacent-stop false triggers (especially `S4 Arjuna's Penance` vs `S6 Varaha Cave`, `55.02 m` apart, and granite interiors at `S6`/`S7`):

| Stop | Name | Configured `arrival_radius_m` | Center Position GPS Acc (`± m`) | Center Arrival Fired? (`Y/N`) | Outside Position Distance Beyond Radius (`m`) | Outside Arrival Stayed Clear? (`Y/N`) | Recommended Radius Adjustment (`m`) |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `S1` | Shore Temple Coastal Entry | `20 m` | | | | | |
| `S2` | Shore Temple Shrines | `45 m` | | | | | |
| `S3` | Pancha Rathas Monolithic Complex | `75 m` | | | | | |
| `S4` | Arjuna's Penance | `25 m` | | | | | |
| `S5` | Krishna's Butterball | `25 m` | | | | | |
| `S6` | Varaha Cave Temple | `25 m` | | | | | |
| `S7` | Mahishasuramardini Mandapa | `30 m` | | | | | |

---

## 5. Companion Hardware / KPI Sign-Off Table (Matches `benchmark_kpis.py` Placeholders)

- `mobile_fps` (Android Chrome): `________________` (`NEEDS DEVICE TEST`)
- `qr_to_ar_launch_ms` (Android Chrome): `________________` (`NEEDS DEVICE TEST`)
- `vision_on_device_ms` (`TF.js MobileNetV2`, after card training): `________________` (`NEEDS DEVICE TEST`)
- `unity_frame_time_ms` (Sony ELF-SR1 4K Display): `________________` (`NEEDS DEVICE TEST`)
