using System;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.Build.Reporting;
using UnityEngine;

namespace LunarAurora.Editor
{
    /// <summary>
    /// Builds MainKioskScene and the standalone Windows Kiosk executable.
    /// Runs in "No-SRD simulation mode" until Sony's SRDisplayUnityPlugin is installed
    /// and SRDISPLAY_SDK_PRESENT is defined per docs/sony_srd_integration_todo.md.
    /// </summary>
    public class BuildScript
    {
        private const string SRD_DEFINE = "SRDISPLAY_SDK_PRESENT";

        [MenuItem("Lunar Aurora/Check SRDisplay Define Status")]
        public static void CheckSrdDefineStatus()
        {
            var targetGroup = BuildTargetGroup.Standalone;
            string currentDefines = PlayerSettings.GetScriptingDefineSymbolsForGroup(targetGroup);
            bool hasDefine = currentDefines.Split(';').Contains(SRD_DEFINE);
            Debug.Log(hasDefine
                ? "[BuildScript] SRDISPLAY_SDK_PRESENT is currently defined in Player Settings."
                : "[BuildScript] No-SRD simulation mode: SRDISPLAY_SDK_PRESENT is NOT defined. See docs/sony_srd_integration_todo.md.");
        }

        [MenuItem("Lunar Aurora/Import Sony SRDisplay Package (.unitypackage)...")]
        public static void ImportSonyPackageMenu()
        {
            string pkgPath = EditorUtility.OpenFilePanel("Select Sony srdisplay-unity-plugin.unitypackage", "", "unitypackage");
            if (!string.IsNullOrEmpty(pkgPath))
            {
                AssetDatabase.ImportPackage(pkgPath, true);
            }
        }

        [MenuItem("Lunar Aurora/Build Kiosk Standalone EXE")]
        public static void BuildStandaloneWindows()
        {
            Debug.Log("[BuildScript] Starting Standalone Windows Build (No-SRD simulation mode unless SRDISPLAY_SDK_PRESENT is defined)...");
            CheckSrdDefineStatus();

            string buildDir = Path.Combine(Application.dataPath, "..", "Builds", "Windows_SonySRDisplay");
            if (Directory.Exists(buildDir))
            {
                Directory.Delete(buildDir, true);
            }
            Directory.CreateDirectory(buildDir);

            string exePath = Path.Combine(buildDir, "LunarAurora_Kiosk.exe");

            QualitySettings.vSyncCount = 0;
            PlayerSettings.defaultScreenWidth = 1920;
            PlayerSettings.defaultScreenHeight = 1080;
            PlayerSettings.fullScreenMode = FullScreenMode.Windowed;
            PlayerSettings.runInBackground = true;
            PlayerSettings.productName = "Lunar Aurora - Holographic Kiosk";
            PlayerSettings.companyName = "Lunar Aurora Team";

            string scenePath = "Assets/Scenes/MainKioskScene.unity";
            CreateDefaultKioskScene(scenePath);

            BuildPlayerOptions buildPlayerOptions = new BuildPlayerOptions
            {
                scenes = new string[] { scenePath },
                locationPathName = exePath,
                target = BuildTarget.StandaloneWindows64,
                options = BuildOptions.None
            };

            BuildReport report = BuildPipeline.BuildPlayer(buildPlayerOptions);
            BuildSummary summary = report.summary;

            if (summary.result == BuildResult.Succeeded)
            {
                Debug.Log($"[BuildScript] Build SUCCESS! Output: {exePath} ({summary.totalSize / (1024 * 1024):F1} MB)");
            }
            else if (summary.result == BuildResult.Failed)
            {
                Debug.LogError($"[BuildScript] Build FAILED with {summary.totalErrors} errors.");
            }
        }

        [MenuItem("Lunar Aurora/Generate & Wire Kiosk Scene")]
        public static void GenerateSceneMenu()
        {
            CreateDefaultKioskScene("Assets/Scenes/MainKioskScene.unity");
        }

        private static void CreateDefaultKioskScene(string scenePath)
        {
            var scene = UnityEditor.SceneManagement.EditorSceneManager.NewScene(
                UnityEditor.SceneManagement.NewSceneSetup.EmptyScene,
                UnityEditor.SceneManagement.NewSceneMode.Single
            );

            // 1. Display Camera Rig + SRDisplayViewerController (No-SRD simulation mode until Sony plugin is installed)
            GameObject camObj = new GameObject("KioskSimulationCameraRig");
            Camera cam = camObj.AddComponent<Camera>();
            cam.clearFlags = CameraClearFlags.SolidColor;
            cam.backgroundColor = new Color(0.015f, 0.025f, 0.055f, 1f);
            cam.transform.position = new Vector3(0, 0.05f, -0.45f);
            cam.transform.LookAt(Vector3.zero);
            camObj.AddComponent<AudioListener>();
            var srController = camObj.AddComponent<LunarAurora.Kiosk.SRDisplayViewerController>();
            srController.fallbackHoloCamera = cam;

            // 2. Solar Directional Lighting + Cyan Rim Light
            GameObject lightObj = new GameObject("SolsticeSunLight");
            Light sun = lightObj.AddComponent<Light>();
            sun.type = LightType.Directional;
            sun.color = new Color(1f, 0.95f, 0.82f);
            sun.intensity = 1.45f;
            lightObj.transform.rotation = Quaternion.Euler(50f, -30f, 0);

            GameObject rimObj = new GameObject("CyanHoloRimLight");
            Light rim = rimObj.AddComponent<Light>();
            rim.type = LightType.Point;
            rim.color = new Color(0f, 0.9f, 1f);
            rim.intensity = 1.8f;
            rim.range = 2.5f;
            rimObj.transform.position = new Vector3(-0.25f, 0.25f, 0.2f);

            // 3. Backend NOAA Telemetry Bridge + Illustrative Monument Turntable
            GameObject bridgeObj = new GameObject("KioskNetworkBridge");
            var bridge = bridgeObj.AddComponent<LunarAurora.Kiosk.KioskNetworkBridge>();

            GameObject monumentObj = new GameObject("HolographicMonument");
            var monumentPreview = monumentObj.AddComponent<LunarAurora.Kiosk.HolographicMonumentPreview>();
            monumentPreview.directionalSunLight = sun;
            monumentPreview.telemetryBridge = bridge;

            // 4. Holographic Avatar Guide (tracks simulated camera or operator anchor)
            GameObject avatarObj = new GameObject("KioskAvatarGuide");
            avatarObj.transform.position = new Vector3(0.135f, -0.06f, -0.02f);
            var avatarGuide = avatarObj.AddComponent<LunarAurora.Kiosk.KioskAvatarGuide>();
            avatarGuide.visitorFaceTarget = camObj.transform;

            // 5. Kiosk UI Manager + Operator HUD (second display) on Display 1
            GameObject uiObj = new GameObject("KioskUIManager");
            var uiMgr = uiObj.AddComponent<LunarAurora.Kiosk.KioskUIManager>();
            uiMgr.srDisplayController = srController;
            uiMgr.monumentPreview = monumentPreview;
            uiMgr.avatarGuide = avatarGuide;
            uiMgr.networkBridge = bridge;

            GameObject opCamObj = new GameObject("OperatorHUDSecondDisplay");
            Camera opCam = opCamObj.AddComponent<Camera>();
            opCam.targetDisplay = 1;
            opCam.clearFlags = CameraClearFlags.SolidColor;
            opCam.backgroundColor = new Color(0.03f, 0.05f, 0.09f, 1f);
            var opHud = opCamObj.AddComponent<LunarAurora.Kiosk.KioskOperatorDisplayHUD>();
            opHud.uiManager = uiMgr;

            Directory.CreateDirectory(Path.GetDirectoryName(scenePath));
            UnityEditor.SceneManagement.EditorSceneManager.SaveScene(scene, scenePath);
            Debug.Log($"[BuildScript] Saved Kiosk scene (No-SRD simulation mode) at: {scenePath}");
        }
    }
}
