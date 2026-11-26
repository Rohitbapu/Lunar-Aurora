# Open-Source Software (OSS) & Asset Attribution Disclosure

Team **Lunar Aurora** (XR Innovation Challenge 2026) documents every third-party library, photograph, encyclopedic text source, 3D model, and authored artifact below.

## 1. Vendored Frontend Libraries (`src/frontend_webxr/vendor/`)

| Library | Version | Source URL | License | Modifications |
| :--- | :---: | :--- | :--- | :--- |
| **Three.js (`three.min.js`)** | `r128` (`0.128.0`) | https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js | MIT License | unmodified |
| **Three.js GLTFLoader (`GLTFLoader.js`)** | `r128` (`0.128.0`) | https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/loaders/GLTFLoader.js | MIT License | unmodified |
| **TensorFlow.js (`tf.min.js`)** | `4.17.0` | https://cdn.jsdelivr.net/npm/@tensorflow/tfjs@4.17.0/dist/tf.min.js | Apache-2.0 License | unmodified |
| **Font Awesome Free (CSS + 8 Webfont files)** | `6.5.1` | https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css | Icons: CC BY 4.0 / Fonts: SIL OFL 1.1 / Code: MIT | unmodified |
| **QRCode.js (`qrcode.min.js`)** | `1.0.0` | https://cdnjs.cloudflare.com/ajax/libs/qrcodejs/1.0.0/qrcode.min.js | MIT License | unmodified |

## 2. Carving Card Photographs (`docs/carving_cards/images/`)

*(Original full-resolution Wikimedia Commons downloads; governed by each image's Creative Commons license in `docs/carving_cards/images/LICENSE-NOTICE.md` — **NOT** the repository's root MIT license.)*

| Local Image File | Resolution | Title & Monument | Author | License | Source URL | Modifications |
| :--- | :---: | :--- | :--- | :--- | :--- | :--- |
| `01_shore_temple_vimana.jpg` | `3000x1996` | Mahabalipuram - Shore Temple | `xiquinhosilva` | **CC BY 4.0** | https://commons.wikimedia.org/wiki/File:Mahabalipuram_-_55439857496.jpg | unmodified (original file) |
| `02_pancha_rathas.jpg` | `4032x2688` | Mahabalipuram, Pancha Rathas, India | `Vyacheslav Argenberg` | **CC BY 4.0** | https://commons.wikimedia.org/wiki/File:Mahabalipuram,_Pancha_Rathas,_India.jpg | unmodified (original file) |
| `03_arjunas_penance.jpg` | `6016x4000` | Arjuna's Penance (Descent of the Ganges), Mamallapuram | `Deepak2885` | **CC BY-SA 4.0** *(ShareAlike required for derivatives)* | https://commons.wikimedia.org/wiki/File:Arjuna%E2%80%99s_Penance-Mamallapuram-unesco.jpg | unmodified (original file) |
| `04_krishnas_butter_ball.jpg` | `2592x1944` | India - Temples & Towers - 019 - Mamallapuram - Krishna's Butterball | `McKay Savage` | **CC BY 2.0** | https://commons.wikimedia.org/wiki/File:India_-_Temples_%26_Towers_-_019_-_Mamallapuram_-_Krishna%27s_Butterball.jpg | unmodified (original file) |
| `05_mahishasuramardini_cave.jpg` | `6000x4000` | Mahabalipuram - Mahishasuramardini Cave Temple Panel | `Rainer Halama` | **CC BY-SA 4.0** *(ShareAlike required for derivatives)* | https://commons.wikimedia.org/wiki/File:Mahabalipuram-Mahishasuramardini_Cave_Temple-WUS01941.jpg | unmodified (original file) |

## 3. Encyclopedic Text & Narration Sources (Wikipedia — CC BY-SA 4.0)

Historical descriptions, monument dates, dimensions, riddles, and audio narration summaries stored in `src/backend/init_db.py`, `src/backend/app/services/groq_service.py`, and synthesized into `src/backend/static/audio_cache/*.mp3` were derived from English Wikipedia articles licensed under **Creative Commons Attribution-ShareAlike 4.0 (CC BY-SA 4.0)**:

| Subject / Database Entries | Article Title & Source URL | License |
| :--- | :--- | :--- |
| Mahabalipuram UNESCO Overview (Stop 1) | Group of Monuments at Mahabalipuram — https://en.wikipedia.org/wiki/Group_of_Monuments_at_Mahabalipuram | CC BY-SA 4.0 |
| Shore Temple (`shore_temple_vimana`, Stop 2, Quest 1) | Shore Temple — https://en.wikipedia.org/wiki/Shore_Temple | CC BY-SA 4.0 |
| Pancha Rathas (`pancha_rathas`, Stop 3, Quest 2) | Pancha Rathas — https://en.wikipedia.org/wiki/Pancha_Rathas | CC BY-SA 4.0 |
| Arjuna's Penance (`arjunas_penance`, Stop 4, Quest 3) | Descent of the Ganges (Mahabalipuram) — https://en.wikipedia.org/wiki/Descent_of_the_Ganges_(Mahabalipuram) | CC BY-SA 4.0 |
| Krishna's Butterball (`krishnas_butter_ball`, Stop 5) | Krishna's Butterball — https://en.wikipedia.org/wiki/Krishna%27s_Butterball | CC BY-SA 4.0 |
| Varaha Cave Temple (Stop 6 shaded cave shelter) | Varaha Cave Temple — https://en.wikipedia.org/wiki/Varaha_Cave_Temple | CC BY-SA 4.0 |
| Mahishasuramardini Mandapa (`mahishasuramardini_cave`, Stop 7) | Mahishasuramardini Mandapa — https://en.wikipedia.org/wiki/Mahishasuramardini_Mandapa | CC BY-SA 4.0 |

## 4. 3D Models (`src/frontend_webxr/assets/models/` & `src/kiosk_unity/`)

- Zero `CC BY-NC` assets are included anywhere in this repository.
- Three procedural `.glb` files (`Grand_Solstice_Sun_Temple.glb`, `Celestial_Airavata_Sculpture.glb`, `Solstitial_Lotus_Gnomon.glb`) remain stored in the repository (`src/kiosk_unity/generate_glb_exhibits.py`, MIT), **with `Grand_Solstice_Sun_Temple.glb` hidden from the WebXR UI and Demo Mode** so all 5 card classes display their verified Wikimedia photograph and facts panel until team-made meshes are added per `src/frontend_webxr/assets/models/README_MODELS_TODO.md`.

## 5. Backend & Training Dependencies (`requirements.txt` & `requirements-train.txt`)

| Library | Source | License | Role & Modifications |
| :--- | :--- | :--- | :--- |
| **FastAPI & Starlette** | https://github.com/fastapi/fastapi | MIT | REST API framework; unmodified. |
| **Uvicorn** | https://github.com/encode/uvicorn | BSD-3-Clause | ASGI HTTP/HTTPS server; unmodified. |
| **SQLAlchemy** | https://github.com/sqlalchemy/sqlalchemy | MIT | ORM & SQLite schema; unmodified. |
| **NetworkX** | https://github.com/networkx/networkx | BSD-3-Clause | Dijkstra graph routing engine (paired with OpenStreetMap walking distances and assumed/illustrative canopy shade weights); unmodified. |
| **Groq Python SDK (`groq`)** | https://github.com/groq/groq-python | Apache-2.0 | LLM client wrapped with `2.5s` async timeout in `groq_service.py`. |
| **Edge-TTS (`edge-tts`)** | https://github.com/rany2/edge-tts | LGPL-3.0 | Neural voice synthesis; unmodified. |
| **fpdf2 & Pillow** | https://github.com/py-pdf/fpdf2 / https://python-pillow.github.io/ | LGPL-3.0 / HPND | Travel Journal PDF export & image inspection; unmodified. |
| **cryptography** | https://github.com/pyca/cryptography | Apache-2.0 / BSD-3-Clause | Self-signed TLS certificates with LAN IP SANs; unmodified. |
| **HTTPX / Pydantic / Pydantic-Settings / aiofiles / psycopg2-binary** | PyPI upstream releases | BSD / MIT / LGPL | Test transport, validation, async I/O, optional Postgres driver; unmodified. |
| **OpenCV (`opencv-python-headless`) / TensorFlow / TFJS / scikit-learn / Matplotlib** *(training only)* | PyPI upstream releases | Apache-2.0 / BSD | Frame extraction & MobileNetV2 classifier training pipeline (`requirements-train.txt`); unmodified. |

## 6. Map Coordinates & Walking Network Distances (OpenStreetMap — ODbL 1.0)

Stop coordinates and inter-stop walking distances in `src/backend/init_db.py` and `src/frontend_webxr/js/locationTracker.js` are derived from OpenStreetMap map data via the OpenStreetMap API (`bbox=80.188,12.607,80.201,12.621`), licensed under the **Open Database License (ODbL 1.0)** — © OpenStreetMap contributors (`https://www.openstreetmap.org/copyright`).

| Stop | Database Slug | Latitude | Longitude | OpenStreetMap Source Object |
| :---: | :--- | :---: | :---: | :--- |
| `1` | `shore_temple_entry` | `12.6165181` | `80.1982844` | `node/1138027422` (`barrier=gate`, West Shore Temple entry footway `way/98366350`) |
| `2` | `shore_temple_vimana` | `12.6164535` | `80.1993500` | `way/370135158` (`Mamallapuram Shore Temple` within `way/390473765`) |
| `3` | `pancha_rathas` | `12.6090647` | `80.1897016` | `way/103082949` (`Pancha Rathas`) |
| `4` | `arjunas_penance` | `12.6179087` | `80.1926969` | `node/353978523` (`Arjuna's Penance`) |
| `5` | `krishnas_butter_ball` | `12.6190890` | `80.1924032` | `way/753671961` (`Krishna's Butterball`) |
| `6` | `varaha_cave` | `12.6180857` | `80.1922234` | `node/353978532` (`Varaha Mandapam / Cave`) |
| `7` | `mahishasuramardini_cave` | `12.6152265` | `80.1915388` | `node/353978541` (`Mahishamadhini Cave`) |

*(Note: While node coordinates and Dijkstra footway distances on `path_edges` come from OpenStreetMap ODbL data, the per-edge `path_type` and `base_shade_factor` shade weights used for routing are **assumed/illustrative values** created by Team Lunar Aurora, not OSM tags or physical measurements.)*
