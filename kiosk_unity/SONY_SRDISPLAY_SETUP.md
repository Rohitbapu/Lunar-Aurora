# Sony Spatial Reality Display (ELF-SR1) Kiosk Setup Guide

This Unity 6 project implements the **Zero-Wearable Holographic Cultural Heritage Showcase** for the **Sony Spatial Reality Display (ELF-SR1)** — a 15.6-inch 4K glasses-free volumetric 3D display.

---

## 1. Prerequisites on Target Display PC (Windows)

1. **Sony Runtime & Drivers:**
   Download and install the **Spatial Reality Display Settings Installer** (`.msi`) from Sony's official developer portal:  
   https://xyn.sony.net/
2. **Sony Unity SDK Plugin:**
   Download `srdisplay-unity-plugin.unitypackage` from **For Application Developers -> Plug-ins for Development** on https://xyn.sony.net/.

---

## 2. Import Sony SDK & Auto-Wire the Scene

1. Open **`kiosk_unity/`** in Unity (`open_in_unity.bat`).
2. In Unity's top menu bar, click:
   **`Lunar Aurora` -> `Import Sony SRDisplay Package (.unitypackage)...`**
   *(or `Assets` -> `Import Package` -> `Custom Package...`)* and select the downloaded `srdisplay-unity-plugin.unitypackage`.
3. Once imported, **`BuildScript.cs` automatically:**
   - Detects `SRD.Core.SRDManager` and enables the `SRDISPLAY_SDK_PRESENT` scripting define.
   - Click **`Lunar Aurora` -> `Generate & Wire Sony Kiosk Scene`** to instantiate `SRDisplayManager` and `SRDisplayBox` into `MainKioskScene.unity` and connect the `WatcherAnchor` eye-tracking transform directly to `KioskAvatarGuide` and `SRDisplayViewerController`.

---

## 3. Build Standalone 4K `.exe`

- **From Unity Editor:**  
  Click **`Lunar Aurora` -> `Build Sony SRDisplay Standalone EXE`**
- **From Command Line:**  
  Run `build_kiosk.bat`

Output executable:
```
kiosk_unity/Builds/Windows_SonySRDisplay/LunarAurora_Kiosk.exe
```

---

## 4. Exhibition Booth Controls

| Control | Function |
| :--- | :--- |
| **Keys `1`, `2`, `3`** (or HUD buttons) | Switch between 3D Temple Reconstruction, Celestial Airavata Monolith, and Lotus Sundial Gnomon |
| **Key `E`** (or **Exploded View**) | Separate roof spire, colonnade, and inner equinox core layers |
| **Mouse Drag / Touch** | 360° manual inspection inside the ELF-SR1 depth box |
| **Scroll Wheel** | Zoom scale within safe front-clipping bounds |
| **Sun Slider** | Sweep solstice sunlight from `06:00` to `18:00` across carvings |
| **Key `H`** | Hide / show exhibition HUD overlay |
