# Mahabalipuram Carving Card Classifier — Training Guide

This guide explains how to film real carving card sessions, extract frames, verify preprocessing parity, and export the **MobileNetV2 TensorFlow.js** classifier for mobile WebXR (`src/frontend_webxr/assets/vision_model/`).

> **Strict Rule:** Do **NOT** generate synthetic renders, cropped web downloads, or augmented copies to replace real printed-card videos (`train_classifier.py` refuses incomplete/single-session folders and never fabricates data).

---

## 1. Canonical 6-Class Schema (`carving_signatures.json` Order)

`src/backend/train_classifier.py` and `src/frontend_webxr/js/visionEngine.js` enforce exact index order (`0..5`) matching `src/frontend_webxr/assets/vision_model/carving_signatures.json`:

| Index | Class ID | Card Code | Monument / Surface |
| :---: | :--- | :--- | :--- |
| `0` | `background` | — | Blank white/ivory cardstock, printed card **backs** (attribution pages), hands, tabletops, walls, sky, auditorium background |
| `1` | `shore_temple_vimana` | `LUNA-CARD-01` | Shore Temple, Mahabalipuram (`01_shore_temple_vimana.jpg`) |
| `2` | `pancha_rathas` | `LUNA-CARD-02` | Pancha Rathas, Mahabalipuram (`02_pancha_rathas.jpg`) |
| `3` | `arjunas_penance` | `LUNA-CARD-03` | Arjuna's Penance / Descent of the Ganges (`03_arjunas_penance.jpg`) |
| `4` | `krishnas_butter_ball` | `LUNA-CARD-04` | Krishna's Butterball (`04_krishnas_butter_ball.jpg`) |
| `5` | `mahishasuramardini_cave` | `LUNA-CARD-05` | Mahishasuramardini Mandapa Panel (`05_mahishasuramardini_cave.jpg`) |

---

## 2. Filming Real Card Videos (`<class>__session_XX.mp4`)

1. Print [`docs/carving_cards/print_5_carving_cards.html`](carving_cards/print_5_carving_cards.html) double-sided on heavy matte A4 cardstock (250+ GSM).
2. Film **at least 3 independent capture sessions** per class (`>= 2` sessions are required by `GroupShuffleSplit`, `>= 3` recommended so lighting, angle, distance, and background clutter differ cleanly between sessions):
   - Vary surface (desk, floor, hand-held), tilt (`±25°`), distance (`20–60 cm`), and indoor/outdoor lighting across `session_01`, `session_02`, `session_03`, ...
   - **Mandatory `background` recordings:** Film dedicated `background__session_01.mp4`, `background__session_02.mp4`, `background__session_03.mp4` videos covering **blank cardstock**, **card backs** (so printed license/source text never false-triggers as a monument), tables, walls, hands, and moving crowd frames.
3. Name every video using `<class>__session_XX.mp4` (examples):
   - `shore_temple_vimana__session_01.mp4`, `shore_temple_vimana__session_02.mp4`
   - `pancha_rathas__session_01.mp4`, `pancha_rathas__session_02.mp4`
   - `arjunas_penance__session_01.mp4`, `arjunas_penance__session_02.mp4`
   - `krishnas_butter_ball__session_01.mp4`, `krishnas_butter_ball__session_02.mp4`
   - `mahishasuramardini_cave__session_01.mp4`, `mahishasuramardini_cave__session_02.mp4`
   - `background__session_01.mp4`, `background__session_02.mp4`

---

## 3. Session Split & Held-Out Test Rule

- `tools/extract_frames.py` writes extracted JPEG frames every **`0.25s`** into **`data/cards/<class>/session_XX/frame_XXXXXX.jpg`**.
- `train_classifier.py` groups strictly by the `session_XX` folder using `sklearn.model_selection.GroupShuffleSplit(n_splits=1, test_size=0.25, random_state=42)` per class:
  - Every frame from a held-out `session_XX` video stays **100% unseen during training**.
  - An explicit `assert not (train_groups & test_groups)` check blocks random-frame leakage.
  - Because `data/cards/` and `.mp4` videos can be large, keep raw training media outside tracked git commits (already `.gitignore`d under `data/`).

---

## 4. Exact Extraction & Training Commands

Install the dedicated ML training dependencies (separate from the lean runtime `src/backend/requirements.txt`):

```powershell
pip install -r src/backend/requirements-train.txt
```

Extract frames every `0.25 s` from your raw video folder:

```powershell
python tools/extract_frames.py path/to/raw_card_videos --out-dir data/cards --interval 0.25
```

Train MobileNetV2, verify exported TF.js accuracy, and export artifacts:

```powershell
python src/backend/train_classifier.py --data-dir data/cards --epochs 12 --batch-size 16
```

### Generated Output Files
- **TF.js Model & Shards (`< 4.0 MB` uint8-quantized):** `src/frontend_webxr/assets/vision_model/model.json` + `.bin` shard files
- **Ordered Class Manifest:** `src/frontend_webxr/assets/vision_model/model_classes.json`
- **Confusion Matrix Plot:** `docs/screenshots/vision_confusion_matrix.png`
- **Held-Out & TF.js Parity Metrics:** `docs/screenshots/vision_metrics.json`

---

## 5. Preprocessing Parity (`[-1, 1]`, Applied Once) & Quantization Check

- **Python (`train_classifier.py`, `load_image_tensor`):** Resizes RGB frame to `224x224` and normalizes `(arr / 127.5) - 1.0` -> **`[-1.0, +1.0]`**. The Keras graph feeds directly into `MobileNetV2(include_top=False, weights="imagenet")` with **no** internal `Rescaling` or `preprocess_input` layer.
- **Browser (`src/frontend_webxr/js/visionEngine.js`, `scanCurrentTarget`):** Resizes camera frame to `224x224` and computes `resized.toFloat().div(127.5).sub(1.0).expandDims(0)` -> **`[-1.0, +1.0]`**.
- **No Double Normalization:** Because scaling runs identically once in `load_image_tensor()` and once in `scanCurrentTarget()`, training and inference tensors match identically.
- **Post-Export Quantization Gate:** After exporting uint8 TF.js weights, `verify_exported_tfjs_accuracy()` reloads `model.json` via `tfjs.converters.load_keras_model()` and evaluates it on the exact held-out `x_test, y_test` sessions. If accuracy drifts by more than **`3.0` percentage points** relative to the pre-export Keras model, training aborts with a non-zero `RuntimeError`.
- **Runtime Confidence Gate:** In `visionEngine.js`, predictions only succeed when softmax confidence `>= 0.82` **and** `is_relic === true` (`background` triggers a non-match notice). Until `model.json` is generated and placed in `src/frontend_webxr/assets/vision_model/`, tapping **`SCAN RELIC`** displays **`"Vision model not installed"`**.
