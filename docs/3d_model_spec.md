# WebXR 3D Monument Model Specification (`src/frontend_webxr/assets/models/`)

**Lunar Aurora** shows verified Wikimedia photographs + Wikipedia/UNESCO facts panels by default until genuine team-authored `.glb` meshes are provided for each monument card class. No procedural placeholder (including hidden `Grand_Solstice_Sun_Temple.glb`) is displayed in WebXR UI or Demo Mode.

---

## 1. Required File Naming (`<class_id>.glb`)

Place finished binary glTF 2.0 files directly inside `src/frontend_webxr/assets/models/` using the exact class ID:

| Class ID | Target Filename | Stop / Card |
| :--- | :--- | :--- |
| `shore_temple_vimana` | `src/frontend_webxr/assets/models/shore_temple_vimana.glb` | `LUNA-CARD-01` / Stop 2 (Shore Temple) |
| `pancha_rathas` | `src/frontend_webxr/assets/models/pancha_rathas.glb` | `LUNA-CARD-02` / Stop 3 (Pancha Rathas) |
| `arjunas_penance` | `src/frontend_webxr/assets/models/arjunas_penance.glb` | `LUNA-CARD-03` / Stop 4 (Arjuna's Penance) |
| `krishnas_butter_ball` | `src/frontend_webxr/assets/models/krishnas_butter_ball.glb` | `LUNA-CARD-04` / Stop 5 (Krishna's Butterball) |
| `mahishasuramardini_cave` | `src/frontend_webxr/assets/models/mahishasuramardini_cave.glb` | `LUNA-CARD-05` / Stop 7 (Mahishasuramardini Mandapa) |

Files not matching one of these exact `<class_id>.glb` names (such as `Grand_Solstice_Sun_Temple.glb`, `Celestial_Airavata_Sculpture.glb`, or `Solstitial_Lotus_Gnomon.glb`) are ignored by `/api/site/overview` (`available_class_models`) and will **never** be rendered in WebXR UI or Demo Mode.

---

## 2. Geometry, Size & Coordinate Rules

| Constraint | Target Requirement |
| :--- | :--- |
| **Format** | Binary **glTF 2.0 (`.glb`)** |
| **Max Polygon Budget** | **`< 15,000` triangles** per `<class_id>.glb` |
| **Max File Size** | **`< 1.5 MB` (Draco-compressed)** |
| **Compression Support** | `src/frontend_webxr/js/arScene.js` bundles local Three.js r128 `GLTFLoader.js` + `DRACOLoader.js` (`vendor/three/draco/`), supporting both Draco-compressed and standard uncompressed `.glb` meshes offline without CDNs |
| **Units & Origin** | **`1 unit = 1 meter`**; base center placed cleanly near `(0, 0, 0)` on the floor plane (`Y >= 0` resting base); `arScene.js` auto-normalizes display bounding size to `0.85 m` in the AR viewport |
| **Orientation** | **glTF right-handed Y-up** (`+Y` up, `+Z` facing the viewer/front facade, upright monument elevation) |
| **Licensing** | Original team-authored work or compatible open license recorded in [`docs/oss_attribution.md`](oss_attribution.md); **zero `CC BY-NC` assets** |

---

## 3. How the Runtime Loader Works (Honest Option B)

1. `GET /api/site/overview` inspects `src/frontend_webxr/assets/models/<class_id>.glb` on disk and returns `available_class_models` for files that genuinely exist.
2. When a user taps **`Photo + Facts`** (in Demo Mode) or scans a recognized card class via **`SCAN RELIC`**, the frontend checks `available_class_models[classId]`:
   - **If `<class_id>.glb` exists:** `arScene.showRelicModel()` loads and displays it with the mandatory UI label **`"Model by Team Lunar Aurora - stylised"`** and note **`"Not a survey-accurate reconstruction."`** plus the Wireframe/Solid Era slider.
   - **If `<class_id>.glb` is missing (or fails to parse):** WebXR automatically displays the **Photo + Facts** panel with verified Wikimedia photography and Wikipedia/UNESCO facts.

---

## 4. Local Drop-In & Verification Steps

1. Export your mesh in Blender (`File -> Export -> glTF 2.0 (.glb)`, `+Y Up`, optional `Compression / Draco`, check triangle count `< 15,000` and size `< 1.5 MB`) as `src/frontend_webxr/assets/models/<class_id>.glb` (for example `pancha_rathas.glb`).
2. Start the backend from `src/backend/`:
   ```powershell
   python start_servers.py
   ```
3. Verify `/api/site/overview` lists `"available_class_models": {"<class_id>": "/app/assets/models/<class_id>.glb"}`.
4. Open `http://localhost:8000/app/?demo=1` in Chrome, open Demo Drawer, select the matching stop (e.g., `S3 Rathas` for `pancha_rathas.glb`), and tap **`Photo + Facts`**.
5. Confirm in the HUD & DevTools:
   - Zero HTTP `404` or Three.js console errors.
   - Top of `#era-reconstruction-panel` displays **`Model by Team Lunar Aurora - stylised`** and **`Not a survey-accurate reconstruction.`**.
   - Scrubbing **`Wireframe <-> Solid`** updates the 3D canvas cleanly; other stops without `<class_id>.glb` still display the Photo + Facts panel.
6. Update [`docs/oss_attribution.md`](oss_attribution.md) if any third-party reference geometry or texture was incorporated.
