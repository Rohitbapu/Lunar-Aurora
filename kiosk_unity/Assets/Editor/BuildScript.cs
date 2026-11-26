using System;
using System.IO;
using UnityEditor;
using UnityEditor.Build.Reporting;
using UnityEngine;

namespace LunarAurora.Editor
{
    public class BuildScript
    {
        [MenuItem("Lunar Aurora/Build Sony SRDisplay Standalone EXE")]
        public static void BuildStandaloneWindows()
        {
            Debug.Log("[BuildScript] Starting Standalone Windows Build for Sony Spatial Reality Display...");

            string buildDir = Path.Combine(Application.dataPath, "..", "Builds", "Windows_SonySRDisplay");
            Directory.CreateDirectory(buildDir);

            string exePath = Path.Combine(buildDir, "LunarAurora_Kiosk.exe");

            // Configure Player Settings for Sony SRDisplay (4K Resolution, Desktop Fullscreen)
            PlayerSettings.defaultScreenWidth = 3840;
            PlayerSettings.defaultScreenHeight = 2160;
            PlayerSettings.fullScreenMode = FullScreenMode.FullScreenWindow;
            PlayerSettings.runInBackground = true;
            PlayerSettings.productName = "Lunar Aurora - Holographic Kiosk";
            PlayerSettings.companyName = "Lunar Aurora Team";

            // Find or create default scene if not already set in build settings
            string[] scenes = new string[] { "Assets/Scenes/MainKioskScene.unity" };
            
            // If scene doesn't exist on disk yet, create and save it
            if (!File.Exists(scenes[0]))
            {
                CreateDefaultKioskScene(scenes[0]);
            }

            BuildPlayerOptions buildPlayerOptions = new BuildPlayerOptions
            {
                scenes = scenes,
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

        [MenuItem("Lunar Aurora/Generate Kiosk Scene")]
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

            // 1. Camera & SRDisplay Rig
            GameObject camObj = new GameObject("SRDisplayCameraRig");
            Camera cam = camObj.AddComponent<Camera>();
            cam.clearFlags = CameraClearFlags.SolidColor;
            cam.backgroundColor = new Color(0.02f, 0.04f, 0.08f, 1f);
            cam.transform.position = new Vector3(0, 0, -0.45f);
            cam.transform.LookAt(Vector3.zero);
            camObj.AddComponent<AudioListener>();
            var srController = camObj.AddComponent<LunarAurora.Kiosk.SRDisplayViewerController>();
            srController.mainHoloCamera = cam;

            // 2. Solstice Lighting
            GameObject lightObj = new GameObject("SolsticeSunLight");
            Light sun = lightObj.AddComponent<Light>();
            sun.type = LightType.Directional;
            sun.color = new Color(1f, 0.96f, 0.85f);
            sun.intensity = 1.3f;
            lightObj.transform.rotation = Quaternion.Euler(50f, -30f, 0);

            // Ambient Rim Light
            GameObject rimObj = new GameObject("CyanRimLight");
            Light rim = rimObj.AddComponent<Light>();
            rim.type = LightType.Point;
            rim.color = new Color(0f, 0.9f, 1f);
            rim.intensity = 1.8f;
            rim.range = 3f;
            rimObj.transform.position = new Vector3(-0.3f, 0.3f, 0.2f);

            // 3. Holographic Monument
            GameObject monumentObj = new GameObject("HolographicMonument");
            var monumentPreview = monumentObj.AddComponent<LunarAurora.Kiosk.HolographicMonumentPreview>();
            monumentPreview.directionalSunLight = sun;

            // 4. Holographic Avatar Guide
            GameObject avatarObj = new GameObject("KioskAvatarGuide");
            avatarObj.transform.position = new Vector3(0.2f, -0.05f, 0f);
            var avatarGuide = avatarObj.AddComponent<LunarAurora.Kiosk.KioskAvatarGuide>();

            // 5. Backend Network Bridge
            GameObject bridgeObj = new GameObject("KioskNetworkBridge");
            var bridge = bridgeObj.AddComponent<LunarAurora.Kiosk.KioskNetworkBridge>();

            // 6. UI Manager
            GameObject uiObj = new GameObject("KioskUIManager");
            var uiMgr = uiObj.AddComponent<LunarAurora.Kiosk.KioskUIManager>();
            uiMgr.monumentPreview = monumentPreview;
            uiMgr.avatarGuide = avatarGuide;
            uiMgr.networkBridge = bridge;

            // Save Scene
            Directory.CreateDirectory(Path.GetDirectoryName(scenePath));
            UnityEditor.SceneManagement.EditorSceneManager.SaveScene(scene, scenePath);
            Debug.Log($"[BuildScript] Created default Sony SRDisplay scene at: {scenePath}");
        }
    }
}

