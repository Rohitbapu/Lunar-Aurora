# Open-Source Software (OSS) & Asset Attribution Disclosure

Team **Lunar Aurora** (XR Innovation Challenge 2026) maintains strict transparency between third-party open-source dependencies, partner SDKs, and original source code/3D assets authored by our team.

| Component / Library | License | Role in System | What Was Reused vs. Original Team Lunar Aurora Engineering |
| :--- | :--- | :--- | :--- |
| **FastAPI & Uvicorn** | MIT / BSD-3 | REST & HTTPS Application Server | Reused HTTP framework; authored custom dual HTTP/HTTPS launcher (`start_servers.py`), Mahabalipuram schema, 2.5s timeout middleware, PDF Travel Journal API (`/api/tour/{id}/journal`), and `/api/site/telemetry`. |
| **NetworkX & SQLAlchemy** | BSD-3 / MIT | Spatial Graph Routing & Persistence | Reused Dijkstra shortest-path primitive and ORM; authored original NOAA solar declination/elevation-azimuth calculator and thermal shade penalty weighting `$w_{\text{shaded}}(e)$` in `routing_service.py`. |
| **Three.js (r128) + GLTFLoader** | MIT | WebXR 3D Viewport & `.glb` Loader | Reused WebGL renderer and glTF parser; authored camera-first transparent AR overlay, Era Slider material cross-fader (`arScene.js`), toggleable corner 3D Guide avatar, and `DeviceOrientationEvent` quaternion coupling. |
| **TensorFlow.js & COCO-SSD** | Apache 2.0 | On-Device Object Recognition | Reused runtime inference engine; authored 6-class Mahabalipuram carving signature configuration (`carving_signatures.json`), `>= 0.82` confidence gate, and optional custom `model.json` hot-loader (`visionEngine.js`). |
| **Web Audio API (HRTF `PannerNode`)** | W3C Web Standard | Binaural 3D Spatial Audio | Reused browser audio graph primitives; authored listener head-orientation updater coupled to live mobile gyroscope quaternions and YouTube-style audio progress subtitle synchronizer (`spatialAudio.js`). |
| **Edge-TTS (`en-IN`, `ta-IN`, `hi-IN`)** | LGPL-3.0 | Multilingual Neural Voice Synthesis | Reused Python Edge-TTS synthesis client; authored 44-clip pre-cache generator (`pre_cache_audio.py`) and explicit `2.5s` offline failsafe resolver (`tts_service.py`). |
| **Groq Llama-3.3-70B API** | Proprietary API / MIT SDK | Conversational Historical AI | Reused Groq inference SDK; authored coastal Pallava prompt engineering, `2.5s` async timeout guard, and deterministic EN/TA/HI offline Q&A bank (`groq_service.py`). |
| **fpdf2 & Pillow** | LGPL-3.0 / HPND | Travel Journal PDF Export | Reused PDF layout primitives; authored watermarked photo embed pipeline and multi-section Heritage Travel Journal exporter (`session_service.py`). |
| **Unity 6 Engine** | Unity Personal / Free | Sony ELF-SR1 Kiosk Application | Reused Unity Player runtime; authored `SRDisplayViewerController.cs` (VSync=0 enforcement, Dual-Display isolation, No-SRD Simulation Mode), `HolographicMonumentPreview.cs` (shade heatmap + live crowd pins), and `KioskNetworkBridge.cs` (2s telemetry polling). |
| **Procedural `.glb` 3D Heritage Assets** | Original (MIT) | Monument Reconstructions | 100% original glTF 2.0 binary meshes generated and scaled for both the Sony ELF-SR1 volumetric box and mobile WebXR Era Slider. |
