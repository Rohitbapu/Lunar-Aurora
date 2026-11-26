# Sony Spatial Reality Display (ELF-SR1) Integration TODO

**Current Status in Repository:** **No-SRD simulation mode**
- `src/kiosk_unity/Packages/manifest.json` does **not** include any Sony SRDisplay package.
- `src/kiosk_unity/ProjectSettings/ProjectSettings.asset` has **empty** `scriptingDefineSymbols` (`SRDISPLAY_SDK_PRESENT` is **not** defined).
- Therefore, all builds currently compiled from `src/kiosk_unity` run strictly in **No-SRD simulation mode** on standard monitors, with secondary-screen telemetry routed to **`Operator HUD (second display)`** (`KioskOperatorDisplayHUD`).

Do **not** claim ELF-SR1 eye tracking or lenticular 3D output works until every step below has been completed and verified on physical Sony ELF-SR1 hardware.

---

## Step 1: Obtain and Install Official Sony Software & Unity Plugin
1. Download the official Sony **Spatial Reality Display Settings** (`.msi` driver/runtime) and **`SRDisplayUnityPlugin` (`.unitypackage`)** from the official Sony developer portal: https://xyn.sony.net/
2. Connect the ELF-SR1 to a Windows 10/11 (64-bit) PC with a discrete NVIDIA GPU:
   - HDMI output to the discrete GPU HDMI port
   - USB 3.2 Gen 1 (or higher) data cable for eye-tracking camera telemetry
   - Windows Multiple Displays set to **Extend these displays** at **3840x2160 (4K)** and **100% scaling**
3. Confirm eye tracking works inside Sony's **Spatial Reality Display Settings** utility before opening Unity.

## Step 2: Import the Plugin Into `src/kiosk_unity`
1. Open `src/kiosk_unity` in Unity `6000.3.11f1` (or open via `src/kiosk_unity/open_in_unity.bat`).
2. Use **`Assets -> Import Package -> Custom Package...`** (or **`Lunar Aurora -> Import Sony SRDisplay Package (.unitypackage)...`**) and select Sony's `.unitypackage`.
3. Inspect the imported package folder (for example `Assets/SRDisplayUnityPlugin/...`) to record exact Sony C# namespaces, class names, prefab names, and 2D second-display prefab names shipped with your downloaded SDK version.

## Step 3: Define `SRDISPLAY_SDK_PRESENT`
1. In Unity Editor, open **`Edit -> Project Settings -> Player -> Other Settings -> Scripting Define Symbols`**.
2. Add `SRDISPLAY_SDK_PRESENT` for the **Standalone** (`Windows, Mac, Linux`) build target and click **Apply** (which persists it inside `src/kiosk_unity/ProjectSettings/ProjectSettings.asset`).
3. Confirm in `Edit -> Project Settings -> Quality` that **`VSync Count = Don't Sync` (`0`)** per Sony's SRDisplay hardware requirements.

## Step 4: Scripts That Must Be Checked Against Sony's Actual Class Names
Because Sony's SDK is proprietary and not bundled in this repository, **do not guess** Sony API symbols (`SRDManager`, `SRD2DView`, `SRDSceneEnvironment`, `SRDisplayBox`, etc.). After importing the package, verify Sony's actual C# types, methods, and prefabs and update the following files inside `#if SRDISPLAY_SDK_PRESENT`:

1. **`src/kiosk_unity/Assets/Scripts/SRDisplayViewerController.cs`**
   - Update `ApplyTrackingMode()` inside `#if SRDISPLAY_SDK_PRESENT` to instantiate/locate Sony's verified SDK rig manager/eye-tracking component, bind `watcherTargetTransform` to Sony's actual viewer/head anchor transform, and disable `fallbackHoloCamera` when Sony stereo rendering is active.
2. **`src/kiosk_unity/Assets/Editor/BuildScript.cs`**
   - Update `CreateDefaultKioskScene(string scenePath)` to place Sony's actual camera-box/manager prefab and second-screen prefab (if provided by your SDK version) into `Assets/Scenes/MainKioskScene.unity`, and update `PlayerSettings.defaultScreenWidth = 3840; PlayerSettings.defaultScreenHeight = 2160;` when building for hardware ELF-SR1 4K output.
3. **`src/kiosk_unity/Assets/Scripts/KioskUIManager.cs`**
   - Verify whether Sony's hardware camera/rig handles Display 0 fullscreen lenticular rendering exclusively so `KioskUIManager.OnGUI()` automatically yields Display 0 to the 3D scene while **`Operator HUD (second display)`** (`KioskOperatorDisplayHUD`) continues rendering on Display 1.
4. **`src/kiosk_unity/Assets/Scripts/KioskAvatarGuide.cs`**
   - Confirm `visitorFaceTarget` receives the live head/eye world transform from Sony's tracking node bound in `SRDisplayViewerController.cs`.

## Step 5: Hardware Verification Checklist Before Finals
- Re-run `BuildScript.BuildStandaloneWindows()` with `SRDISPLAY_SDK_PRESENT` defined and verify zero compiler errors.
- Launch `LunarAurora_Kiosk.exe` with ELF-SR1 connected on Display 0 and a monitor on Display 1 (`Operator HUD (second display)`).
- Confirm lenticular stereo focus, zero ghosting (`VSync = 0`), and measure real Unity frame time (ms) on hardware before quoting any performance figure.
