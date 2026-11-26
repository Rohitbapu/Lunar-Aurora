# Accelerator & Partner Attribution Report (`ax.md`)

**Project:** Lunar Aurora — Glasses-Free Sony ELF-SR1 & Zero-Install Mobile WebXR Heritage Sanctuary  
**Team:** Lunar Aurora (Ayyappan Ayyanan, Vikrant R M, Rohit Bapu S B)  
**Institution:** Sethu Institute of Technology  
**Submission Track:** XR Innovation Challenge 2026 (GIEC / Partners Track)

---

## 1. Executive Summary
**Lunar Aurora** unites a zero-install Mobile WebXR outdoor companion with a zero-wearable **Sony Spatial Reality Display (ELF-SR1)** holographic kiosk tuned specifically for UNESCO-listed coastal stone heritage sites such as **Mahabalipuram Shore Temple** ($12.6165^\circ\text{ N}, 80.1993^\circ\text{ E}$). Rather than enclosing tourists in heat-trapping HMDs under $35^\circ\text{C+}$ South Indian sun, our architecture balances solar geometry thermal safety routing, offline-resilient multilingual voice synthesis, and volumetric lenticular inspection.

---

## 2. Algorithmic Modeling & Solar Formulation (MathWorks Alignment)
### 2.1 NOAA Solar Declination & Elevation-Azimuth Geometry
In `src/backend/app/services/routing_service.py`, solar coordinates are calibrated continuously to Mahabalipuram's coastal latitude ($\phi = 12.6165^\circ\text{ N}$) across local hour $t \in [6.0, 18.0]$:
- Day-of-year solar declination $\delta = 23.44^\circ \sin\left(\frac{360}{365}(d - 81)\right)$
- Hour angle $H = 15^\circ (t - 12)$
- Solar elevation $\alpha_s$:
$$\sin(\alpha_s) = \sin(\phi)\sin(\delta) + \cos(\phi)\cos(\delta)\cos(H)$$

### 2.2 Solar-Weighted Dijkstra Edge Cost Function
For every walkway graph edge $e = (u, v)$ of physical distance $d_e$ (meters) and structural canopy/colonnade base shade $s_e \in [0, 1]$, dynamic effective shade at time $t$ scales with peak overhead solar glare:
$$s_{\text{eff}}(e, t) = \text{clamp}\Big(s_e \cdot \big(1 - 0.35\sin(\alpha_s)\big),\; 0.05,\; 0.98\Big)$$
Two distinct Dijkstra passes run inside `RoutingService.get_dual_telemetry`:
1. **Standard Shortest Route (Sun-Exposed Red Path):**
   $$w_{\text{shortest}}(e) = d_e$$
2. **Solar-Optimized Shaded Route (Cool Emerald Path):**
   $$w_{\text{shaded}}(e) = d_e \cdot \big(1 + \beta \cdot (1 - s_{\text{eff}}(e, t))\big)$$
   where midday solar penalty weight $\beta = 3.2$ when $\alpha_s > 55^\circ$ (or $\beta = 1.6$ under milder sun), and total radiative walk exposure is measured as $\sum_{e \in P} d_e (1 - s_{\text{eff}}(e, t))$.

Across the Mahabalipuram 7-station sanctuary graph (`src/backend/init_db.py`), routing visitors through covered colonnades (`yali_courtyard`) and `Arjuna's Penance Banyan Canopy` instead of open courtyard stone shortcuts yields **76.0% Heat Exposure Saved** at 13:00 IST with sub-`5 ms` backend computation (`4.89 ms` mean).

---

## 3. 3D Reconstruction & Asset Optimization Pipeline
- **Shared Asset Target:** Compact glTF 2.0 `.glb` meshes stored in both `src/kiosk_unity/SonyPlayer_3DAssets/` and `src/frontend_webxr/assets/models/`:
  - `Grand_Solstice_Sun_Temple.glb`
  - `Celestial_Airavata_Sculpture.glb`
  - `Solstitial_Lotus_Gnomon.glb`
- **Mobile Era Slider (700 CE Zenith $\leftrightarrow$ Present Eroded Stone):** WebXR `ARScene` (`src/frontend_webxr/js/arScene.js`) renders synchronized solid textured meshes over an emissive cyan architectural blueprint wireframe, letting visitors scrub reconstruction completeness on top of live rear-camera stone walls.

---

## 4. Sony Spatial Reality Display (ELF-SR1) & Unity 6 Integration
Our Windows standalone kiosk (`src/kiosk_unity/`) follows Sony's dual-display and lenticular optical engineering guidelines:
- **Zero Lenticular Tear (`VSync = 0`):** All quality tiers in `ProjectSettings/QualitySettings.asset` and `SRDisplayViewerController.cs` force `QualitySettings.vSyncCount = 0; Application.targetFrameRate = 60;`.
- **Clean 3D Stereoscopic Box Isolation:** `KioskUIManager.cs` suppresses floating 2D `OnGUI` text on the primary eye-tracked lenticular display (`Display 0`) when `hardwareSdkActive == true`, routing operator controls to secondary displays and offering an instant **`No-SRD Simulation Mode`** (`[S]`) for non-hardware demonstrations.
- **Real-Time Crowd & Solar Telemetry:** `KioskNetworkBridge.cs` polls `GET /api/site/telemetry` every `2.0s` to drive animated courtyard thermal tiles and 7 stop occupancy beacons inside `HolographicMonumentPreview.cs`.

---

## 5. Edge AI Vision, Voice & Offline Failsafe Engineering
- **On-Device Carving Card Classifier (`visionEngine.js`):** Supports hot-loading a trained TensorFlow.js classifier (`assets/vision_model/model.json`) alongside offline MobileNet/COCO-SSD detection and `carving_signatures.json` with a strict `>= 0.82` confidence threshold and live `performance.now()` latency telemetry.
- **2.5s Cloud Timeout + Zero-Drop Offline Continuity:** Both `groq_service.py` (Groq Llama-3.3-70B) and `tts_service.py` (Edge-TTS `en-IN-NeerjaNeural`, `ta-IN-PallaviNeural`, `hi-IN-SwaraNeural`) enforce `asyncio.wait_for(..., timeout=2.5)`. If rural/coastal mobile connectivity drops, responses degrade transparently to `static/audio_cache/` (44 pre-synthesized EN/TA/HI MP3s) and `OFFLINE_QA_BANK`.

---

## 6. Key Engineering Learnings
1. **Never Obstruct Real Heritage Stone:** Early full-screen 3D widgets felt cluttered outdoors; shifting to a camera-first HUD with an on-demand Era Slider and toggleable `[3D GUIDE]` corner spirit improved readability during live movement.
2. **Lenticular Hardware Discipline:** Blocking `VSync` and keeping flat 2D text off the lenticular Display 0 surface eliminates eye strain and ghosting artifacts documented in Sony SRD developer guidelines.
3. **Deterministic Failover Wins Field Demos:** Coastal ruins suffer cellular dead zones; strict `2.5s` timeouts paired with pre-cached local MP3s guarantee sub-`10 ms` offline responses when networks stall.
