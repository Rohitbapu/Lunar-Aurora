# Sony Spatial Reality Display (ELF-SR1) Kiosk & Player Guide

This Unity 6 project implements the **Zero-Wearable Holographic Cultural Heritage Showcase** for the **Sony Spatial Reality Display (ELF-SR1)** — a 15.6-inch 4K glasses-free volumetric 3D display.

You have **two ways** to present Lunar Aurora on the ELF-SR1 at the exhibition booth:
1. **Option A (Zero-Code Instant Showcase):** Drop our exported `.glb` models directly into **Sony Spatial Reality Display Player**.
2. **Option B (Custom Interactive Unity Kiosk `.exe`):** Run `LunarAurora_Kiosk.exe` wired with Sony's `SRDisplayUnityPlugin`.

---

## 1. Physical ELF-SR1 Hardware Setup (Critical Checklist)

Connect the ports on the rear of the ELF-SR1 stand to a Windows 10/11 (64-bit) PC with a discrete NVIDIA RTX GPU (`>= RTX 2070 Super / RTX 3060`) and `>= 16 GB RAM`:

1. **Power Cable:** Connect the AC power adapter to the display.
2. **HDMI Video Cable:** Connect from ELF-SR1 HDMI to the **dedicated Graphics Card (GPU)** — *never* plug into the motherboard integrated graphics port.
3. **USB Data Cable:** Connect from ELF-SR1 USB-C to a **USB 3.2 Gen 1 (or higher)** port on the PC (streams high-speed eye-tracking sensor data).
4. **Windows Display Settings:**
   - Set multiple displays to **Extend these displays**.
   - Confirm ELF-SR1 resolution is **3840 × 2160 (4K)** and set Windows Display Scaling to **100%** to prevent clipping.
5. **Sony Runtime Drivers:**
   - Install **Spatial Reality Display Settings** (`.msi`) from https://xyn.sony.net/ and verify the face-tracking mesh follows your eyes inside the Settings utility.

---

## 2. Option A: Instant Showcase via Sony Spatial Reality Display Player

Using **Sony Spatial Reality Display Player** (available from https://xyn.sony.net/):
1. Launch **Spatial Reality Display Player** on the ELF-SR1 extended monitor.
2. Drag and drop any of our exported glTF 2.0 `.glb` assets from `kiosk_unity/SonyPlayer_3DAssets/`:
   - `Grand_Solstice_Sun_Temple.glb`
   - `Celestial_Airavata_Sculpture.glb`
   - `Solstitial_Lotus_Gnomon.glb`
3. Enable **Turntable Auto-Rotation**, adjust environment lighting, and attach informational panels right inside Sony's Player.

*(To regenerate the `.glb` models anytime, run `python kiosk_unity/generate_glb_exhibits.py`.)*

---

## 3. Option B: Interactive Unity 6 Kiosk + Official SDK Integration

1. Download `srdisplay-unity-plugin.unitypackage` from **For Application Developers -> Plug-ins for Development** on https://xyn.sony.net/.
2. Open **`kiosk_unity/`** in Unity (`open_in_unity.bat`).
3. Click **`Lunar Aurora` -> `Import Sony SRDisplay Package (.unitypackage)...`** and import the package.
4. **`BuildScript.cs` automatically:**
   - Detects `SRD.Core.SRDManager` and enables the `SRDISPLAY_SDK_PRESENT` scripting define.
   - Click **`Lunar Aurora` -> `Generate & Wire Sony Kiosk Scene`** to place `SRDisplayManager` and `SRDisplayBox` into `MainKioskScene.unity` and connect `WatcherAnchor` eye-tracking to `KioskAvatarGuide` and `SRDisplayViewerController`.
5. Build the 4K executable via **`Lunar Aurora` -> `Build Sony SRDisplay Standalone EXE`** (or `build_kiosk.bat`):
   ```
   kiosk_unity/Builds/Windows_SonySRDisplay/LunarAurora_Kiosk.exe
   ```

---

## 4. Unity Kiosk Booth Controls

| Control | Function |
| :--- | :--- |
| **Keys `1`, `2`, `3`** (or HUD buttons) | Switch between 3D Temple Reconstruction, Celestial Airavata Monolith, and Lotus Sundial Gnomon |
| **Key `E`** (or **Exploded View**) | Separate roof spire, colonnade, and inner equinox core layers |
| **Mouse Drag / Touch** | 360° manual inspection inside the ELF-SR1 depth box |
| **Scroll Wheel** | Zoom scale within safe front-clipping bounds |
| **Sun Slider** | Sweep solstice sunlight from `06:00` to `18:00` across carvings |
| **Key `H`** | Hide / show exhibition HUD overlay |
