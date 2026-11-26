# Sony Spatial Reality Display (ELF-SR1) Kiosk Guide

**Important Current Status:**
- **Sony `SRDisplayUnityPlugin` is NOT installed** in `src/kiosk_unity/Packages/manifest.json`, and **`SRDISPLAY_SDK_PRESENT` is NOT defined** in `ProjectSettings/ProjectSettings.asset`.
- Consequently, `LunarAurora_Kiosk.exe` runs in **`No-SRD simulation mode`** using `KioskSimulationCameraRig`, `KioskNetworkBridge` (polling `/api/site/telemetry?date=...&hour=...` every 2s), and **`Operator HUD (second display)`** (`KioskOperatorDisplayHUD` on Display 1 when a secondary display exists).
- The three 3D exhibits in `HolographicMonumentPreview.cs` (`Shore Temple`, `Pancha Rathas`, `Krishna's Butterball`) are procedural **Illustrative model** placeholders only — not archaeological 3D scans.

See [docs/sony_srd_integration_todo.md](../../docs/sony_srd_integration_todo.md) for the full step-by-step instructions to import Sony's official SDK, define `SRDISPLAY_SDK_PRESENT`, and check scripts against Sony's SDK class names before hardware deployment.

---

## Unity Kiosk Controls (No-SRD Simulation Mode)

| Control | Function |
| :--- | :--- |
| **Keys `1`, `2`, `3`** | Switch between procedural illustrative models (Shore Temple, Pancha Rathas, Krishna's Butterball) |
| **Key `E`** (or **Explode (E)** button) | Separate architectural layers (Shore Temple tiers/wall posts) |
| **Mouse Drag / Scroll** | Orbit yaw/pitch and zoom scale inside the simulation bounds |
| **NOAA Date + IST Hour Slider** | Query `/api/site/telemetry?date=YYYY-MM-DD&hour=...` to update the directional sun light and courtyard shade estimate |
| **Key `S`** | Toggle simulation state telemetry check |
| **Key `H` / `O`** | Hide / show **`Operator HUD (second display)`** overlay |
