using System;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.Build.Reporting;
using UnityEngine;

namespace LunarAurora.Editor
{
    /// <summary>
    /// Automatically detects Sony's official SRDisplayUnityPlugin when imported from https://xyn.sony.net/,
    /// sets the SRDISPLAY_SDK_PRESENT scripting define, wires SRDisplayManager & SRDisplayBox into MainKioskScene,
    /// and compiles the 4K standalone executable for the Sony ELF-SR1.
    /// </summary>
    [InitializeOnLoad]
    public class BuildScript
    {
        private const string SRD_DEFINE = "SRDISPLAY_SDK_PRESENT";

        static BuildScript()
        {
            SyncSonySdkDefineSymbol();
        }

        [MenuItem("Lunar Aurora/Detect & Enable Sony SRDisplay SDK")]
        public static void SyncSonySdkDefineSymbol()
        {
            bool hasSonyPlugin = AppDomain.CurrentDomain.GetAssemblies()
                .Any(a => a.GetType("SRD.Core.SRDManager") != null || a.GetType("SRD.Core.SRDSceneEnvironment") != null);

            var targetGroup = BuildTargetGroup.Standalone;
            string currentDefines = PlayerSettings.GetScriptingDefineSymbolsForGroup(targetGroup);
            bool hasDefine = currentDefines.Split(';').Contains(SRD_DEFINE);

            if (hasSonyPlugin && !hasDefine)
            {
                string updated = string.IsNullOrEmpty(currentDefines) ? SRD_DEFINE : $"{currentDefines};{SRD_DEFINE}";
                PlayerSettings.SetScriptingDefineSymbolsForGroup(targetGroup, updated);
                Debug.Log("[LunarAurora] Sony SRDisplay SDK detected! Enabled SRDISPLAY_SDK_PRESENT.");
            }
            else if (!hasSonyPlugin && hasDefine)
            {
                var cleaned = string.Join(";", currentDefines.Split(';').Where(d => d != SRD_DEFINE && !string.IsNullOrEmpty(d)));
                PlayerSettings.SetScriptingDefineSymbolsForGroup(targetGroup, cleaned);
            }
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

        [MenuItem("Lunar Aurora/Build Sony SRDisplay Standalone EXE")]
        public static void BuildStandaloneWindows()
        {
            Debug.Log("[BuildScript] Starting Standalone Windows Build for Sony Spatial Reality Display (ELF-SR1)...");
            SyncSonySdkDefineSymbol();

            string buildDir = Path.Combine(Application.dataPath, "..", "Builds", "Windows_SonySRDisplay");
            Directory.CreateDirectory(buildDir);

            string exePath = Path.Combine(buildDir, "LunarAurora_Kiosk.exe");

            // Official Sony ELF-SR1 4K Display Player Settings (VSync MUST be 0 per Sony hardware guide)
            QualitySettings.vSyncCount = 0;
            PlayerSettings.defaultScreenWidth = 3840;
            PlayerSettings.defaultScreenHeight = 2160;
            PlayerSettings.fullScreenMode = FullScreenMode.FullScreenWindow;
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

        [MenuItem("Lunar Aurora/Generate & Wire Sony Kiosk Scene")]
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

            // 1. Sony SRDisplay SDK Prefabs (auto-wired if imported from Sony XYN portal)
            GameObject watcherTarget = null;
            string[] srdManagerGuids = AssetDatabase.FindAssets("SRDisplayManager t:Prefab");
            if (srdManagerGuids.Length > 0)
            {
                string prefabPath = AssetDatabase.GUIDToAssetPath(srdManagerGuids[0]);
                GameObject srdPrefab = AssetDatabase.LoadAssetAtPath<GameObject>(prefabPath);
                if (srdPrefab != null)
                {
                    GameObject srdInstance = (GameObject)PrefabUtility.InstantiatePrefab(srdPrefab);
                    srdInstance.name = "SRDisplayManager";
                    Transform anchor = srdInstance.transform.Find("WatcherAnchor");
                    if (anchor != null) watcherTarget = anchor.gameObject;
                    Debug.Log($"[BuildScript] Wired official Sony prefab: {prefabPath}");
                }
            }

            string[] srdBoxGuids = AssetDatabase.FindAssets("SRDisplayBox t:Prefab");
            if (srdBoxGuids.Length > 0)
            {
                string boxPath = AssetDatabase.GUIDToAssetPath(srdBoxGuids[0]);
                GameObject boxPrefab = AssetDatabase.LoadAssetAtPath<GameObject>(boxPath);
                if (boxPrefab != null)
                {
                    GameObject boxInstance = (GameObject)PrefabUtility.InstantiatePrefab(boxPrefab);
                    boxInstance.name = "SRDisplayBox";
                }
            }

            // 2. Fallback Camera + SRDisplayViewerController (auto-disabled if SRDisplayManager is active)
            GameObject camObj = new GameObject("SRDisplayCameraRig");
            Camera cam = camObj.AddComponent<Camera>();
            cam.clearFlags = CameraClearFlags.SolidColor;
            cam.backgroundColor = new Color(0.015f, 0.025f, 0.055f, 1f);
            cam.transform.position = new Vector3(0, 0.05f, -0.45f);
            cam.transform.LookAt(Vector3.zero);
            camObj.AddComponent<AudioListener>();
            var srController = camObj.AddComponent<LunarAurora.Kiosk.SRDisplayViewerController>();
            srController.fallbackHoloCamera = cam;
            if (watcherTarget != null) srController.watcherTargetTransform = watcherTarget.transform;

            // 3. Solstice Lighting
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

            // 4. Holographic Monument Showcase (centered inside ELF-SR1 0.35m x 0.20m x 0.20m prism)
            GameObject bridgeObj = new GameObject("KioskNetworkBridge");
            var bridge = bridgeObj.AddComponent<LunarAurora.Kiosk.KioskNetworkBridge>();

            GameObject monumentObj = new GameObject("HolographicMonument");
            var monumentPreview = monumentObj.AddComponent<LunarAurora.Kiosk.HolographicMonumentPreview>();
            monumentPreview.directionalSunLight = sun;
            monumentPreview.telemetryBridge = bridge;

            // 5. Holographic Avatar Guide (tracks visitor's eye position via WatcherAnchor)
            GameObject avatarObj = new GameObject("KioskAvatarGuide");
            avatarObj.transform.position = new Vector3(0.135f, -0.06f, -0.02f);
            var avatarGuide = avatarObj.AddComponent<LunarAurora.Kiosk.KioskAvatarGuide>();
            if (watcherTarget != null) avatarGuide.visitorFaceTarget = watcherTarget.transform;

            // 7. SRD2DView / Secondary Operator Panel Rig (Display 1) + Kiosk UI Manager
            string[] srd2dGuids = AssetDatabase.FindAssets("SRD2DView t:Prefab");
            if (srd2dGuids.Length > 0)
            {
                string view2dPath = AssetDatabase.GUIDToAssetPath(srd2dGuids[0]);
                GameObject view2dPrefab = AssetDatabase.LoadAssetAtPath<GameObject>(view2dPath);
                if (view2dPrefab != null)
                {
                    GameObject view2dInstance = (GameObject)PrefabUtility.InstantiatePrefab(view2dPrefab);
                    view2dInstance.name = "SRD2DView";
                    Debug.Log($"[BuildScript] Wired official Sony prefab: {view2dPath}");
                }
            }

            GameObject uiObj = new GameObject("KioskUIManager");
            var uiMgr = uiObj.AddComponent<LunarAurora.Kiosk.KioskUIManager>();
            uiMgr.srDisplayController = srController;
            uiMgr.monumentPreview = monumentPreview;
            uiMgr.avatarGuide = avatarGuide;
            uiMgr.networkBridge = bridge;

            GameObject opCamObj = new GameObject("OperatorDisplayCamera");
            Camera opCam = opCamObj.AddComponent<Camera>();
            opCam.targetDisplay = 1;
            opCam.clearFlags = CameraClearFlags.SolidColor;
            opCam.backgroundColor = new Color(0.03f, 0.05f, 0.09f, 1f);
            var opHud = opCamObj.AddComponent<LunarAurora.Kiosk.KioskOperatorDisplayHUD>();
            opHud.uiManager = uiMgr;

            Directory.CreateDirectory(Path.GetDirectoryName(scenePath));
            UnityEditor.SceneManagement.EditorSceneManager.SaveScene(scene, scenePath);
            Debug.Log($"[BuildScript] Saved Sony ELF-SR1 Kiosk scene at: {scenePath}");
        }
    }
}
