# 🏛️ LUNAR AURORA
### Multimodal Spatial Historical AI Guide for WebXR & Sony Spatial Reality Display

Lunar Aurora solves tourist exhaustion, language barriers, and lack of artifact labeling at monumental heritage sites by pairing an instant **Zero-Install WebXR Mobile Tour Guide** with a glasses-free **Sony Spatial Reality Display (ELF-SR1) 3D Holographic Kiosk**.

---

## 🛠️ System Components & Architecture

| Component | Target Environment | Key Stack / Deliverables |
| :--- | :--- | :--- |
| **Holographic Kiosk** | Windows Workstation + Sony ELF-SR1 | Unity 6, Sony SRDisplay SDK, Standalone `.exe` Build |
| **Backend & AI Services** | Linux (Ubuntu 24.04) / Windows / Docker | Python 3.11+, FastAPI, Groq (Llama 3), Edge-TTS, PostGIS |
| **Mobile WebXR Client** | Mobile Web Browser (Android / iOS) | Three.js, WebXR API, TensorFlow.js, Web Audio HRTF |

---

## 📂 Project Structure

```
LUNA/
├── backend/                        # FastAPI Backend & AI Services
│   ├── app/
│   │   ├── main.py                 # FastAPI Application & Static Mounts
│   │   ├── config.py               # Settings (Groq API, DB, Voices)
│   │   ├── database.py             # SQLite & PostgreSQL/PostGIS Engine
│   │   ├── models/entities.py      # POINodes, PathEdges, Relics, Quests, Sessions
│   │   ├── services/
│   │   │   ├── groq_service.py     # Llama 3 Conversational Historical Guide
│   │   │   ├── tts_service.py      # Edge-TTS Audio Generation & Caching
│   │   │   ├── routing_service.py  # Solar Shade & "Take a Rest" A*/Dijkstra
│   │   │   ├── session_service.py  # Personalized Ticket & Stop Progression
│   │   │   └── vision_knowledge.py # Point & Know Archaeological DB
│   │   └── routers/                # chat, routing, vision, scavenger, site, ticket, session
│   ├── static/audio/               # Cached synthesized audio narratives
│   ├── init_db.py                  # Database Seeding Script
│   ├── test_suite.py               # Comprehensive Integration Tests
│   ├── Dockerfile                  # Container build for Linux deployment
│   ├── docker-compose.yml          # PostGIS + Backend Compose Stack
│   ├── run_backend.bat             # 1-Click Launch on Windows
│   └── run_backend.sh              # 1-Click Launch on Linux
│
├── frontend_webxr/                 # Zero-Install Mobile WebXR PWA
│   ├── index.html                  # Clean Camera-First AR Interface & YouTube Subtitles
│   ├── css/style.css               # Luminous dark archaeology theme
│   └── js/
│       ├── app.js                  # Master application orchestrator
│       ├── arScene.js              # Three.js transparent camera passthrough
│       ├── locationTracker.js      # Real-time mobile GPS & geofence arrival
│       ├── spatialAudio.js         # Web Audio API HRTF PannerNode
│       ├── tourManager.js          # Curated 7-stop tour & interruption recovery
│       └── visionEngine.js         # TensorFlow.js COCO-SSD detection
│
└── kiosk_unity/                    # Sony Spatial Reality Display Project
    ├── Assets/
    │   ├── Editor/BuildScript.cs   # Automated Standalone Windows .exe Compiler
    │   └── Scripts/
    │       ├── SRDisplayViewerController.cs   # Sony ELF-SR1 Hologram Rig & Eye Tracking
    │       ├── HolographicMonumentPreview.cs  # 3D Turntable, Exploded View, Solstice Sun
    │       ├── KioskAvatarGuide.cs            # Holographic Welcome Guide Avatar
    │       ├── KioskNetworkBridge.cs          # Live Sync with Backend (Shade & Sun)
    │       └── KioskUIManager.cs              # Sony Holographic Overlay & HUD
    ├── Packages/manifest.json      # Unity package dependencies
    ├── ProjectSettings/            # Unity project configuration
    ├── open_in_unity.bat           # 1-Click Launch in Unity Editor
    └── build_kiosk.bat             # 1-Click Standalone Windows .exe Compiler
```

---

## 🚀 Quickstart Guide

### 1. Launching the Backend & WebXR Server

On your **Backend Server (Linux / Windows)**:
```bash
cd backend
# Optional: Copy .env.example to .env and add your Groq API key
cp .env.example .env

# Run initialization & dual HTTP/HTTPS servers
python start_servers.py
```
Or double-click `run_backend.bat` (Windows) or run `./run_backend.sh` (Ubuntu).

### 2. Testing on a Mobile Device

1. Open the ticketing portal or QR page on your server machine:
   - **Ticketing Counter:** `http://localhost:8000/ticket`
   - **Direct QR Page:** `http://localhost:8000/qr`
2. Scan the displayed QR code with your smartphone camera.
3. Accept the local HTTPS prompt and grant Camera & Location permissions when prompted.
4. **Core Features:**
   - **Clean AR Camera & Subtitles:** Fullscreen live viewfinder with dynamic audio-synced subtitles.
   - **Point & Know (`SCAN RELIC`):** TensorFlow.js identifies carvings/monuments on-device and narrates their history.
   - **Live GPS & Blueprint Map:** Tracks visitor position across the 7 curated stations with automatic arrival alerts.
   - **Smart Shaded Rest (`SHADE`):** Calculates the coolest route to a shaded bench based on solar position.
   - **Interactive Q&A (`ASK`):** Voice microphone & multilingual chat powered by Groq Llama 3 and Edge-TTS.

---

### 3. Compiling the Sony Spatial Reality Display Kiosk

On **Windows (Unity 6)**:

1. **Automated CLI Compilation:**
   Run `kiosk_unity/build_kiosk.bat` to compile the standalone 4K executable to:
   ```
   kiosk_unity/Builds/Windows_SonySRDisplay/LunarAurora_Kiosk.exe
   ```
2. **Unity Editor:**
   Run `kiosk_unity/open_in_unity.bat`, then select **`Lunar Aurora` -> `Build Sony SRDisplay Standalone EXE`**.
3. **Deployment:**
   Copy the `Windows_SonySRDisplay` folder onto the PC connected to the Sony Spatial Reality Display ELF-SR1 and launch `LunarAurora_Kiosk.exe`.

---

## 🧪 Verifying the Implementation

Run the automated integration test suite anytime:
```bash
cd backend
python init_db.py
python test_suite.py
```
