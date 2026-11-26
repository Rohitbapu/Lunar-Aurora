using UnityEngine;

namespace LunarAurora.Kiosk
{
    /// <summary>
    /// Exhibition & Operator HUD Controller.
    /// - Display 0 stays free of 2D GUI when Sony hardware eye-tracking is live.
    /// - Secondary display (Display 1 / SRD2DView Operator Panel) renders operator controls and telemetry.
    /// - When running on a standard monitor (No-SRD Simulation Mode, toggle [S]), displays controls directly.
    /// </summary>
    public class KioskUIManager : MonoBehaviour
    {
        public SRDisplayViewerController srDisplayController;
        public HolographicMonumentPreview monumentPreview;
        public KioskAvatarGuide avatarGuide;
        public KioskNetworkBridge networkBridge;

        [Header("Display & Simulation Mode")]
        public bool showOverlayInSimulation = true;
        public bool showOperatorPanel = true;
        public bool forceOperatorHudOnPrimary = false;

        private float smoothedFps = 60.0f;

        void Update()
        {
            float instFps = Time.deltaTime > 0.0001f ? (1.0f / Time.deltaTime) : 60.0f;
            smoothedFps = Mathf.Lerp(smoothedFps, instFps, 0.08f);

            if (Input.GetKeyDown(KeyCode.Alpha1) && monumentPreview != null) monumentPreview.SelectExhibit(HeritageExhibitType.ShoreTemple);
            if (Input.GetKeyDown(KeyCode.Alpha2) && monumentPreview != null) monumentPreview.SelectExhibit(HeritageExhibitType.PanchaRathas);
            if (Input.GetKeyDown(KeyCode.Alpha3) && monumentPreview != null) monumentPreview.SelectExhibit(HeritageExhibitType.KrishnasButterball);
            if (Input.GetKeyDown(KeyCode.E) && monumentPreview != null) monumentPreview.ToggleExplodedView();
            if (Input.GetKeyDown(KeyCode.H)) showOverlayInSimulation = !showOverlayInSimulation;
            if (Input.GetKeyDown(KeyCode.O)) showOperatorPanel = !showOperatorPanel;
            if (Input.GetKeyDown(KeyCode.S) && srDisplayController != null) srDisplayController.ToggleNoSrdSimulation();
        }

        public void DrawOperatorControlsRect(Rect areaRect)
        {
            bool hardwareActive = srDisplayController != null && srDisplayController.hardwareSdkActive;
            GUI.backgroundColor = new Color(0.04f, 0.08f, 0.15f, 0.90f);
            GUILayout.BeginArea(areaRect, GUI.skin.box);
            GUILayout.Label($"<size=17><b><color=#00e5ff>LUNAR AURORA • SRD2DView OPERATOR PANEL</color></b></size>");

            string sdkState = hardwareActive
                ? "<color=#00e676>Sony SRDisplay SDK Active (VSync=0)</color>"
                : "<color=#f4c430>No-SRD Simulation Mode (No Sony Plugin)</color>";
            GUILayout.Label($"<size=12>{sdkState} • <b>{smoothedFps:F0} FPS</b> • VSync={QualitySettings.vSyncCount}</size>");
            GUILayout.Space(4);

            if (monumentPreview != null)
            {
                GUILayout.Label($"<size=12><b>3D View:</b> <color=#ffffff>{monumentPreview.GetActiveExhibitTitle()}</color></size>");
            }

            if (networkBridge != null)
            {
                string conn = networkBridge.backendConnected ? "<color=#00e676>ONLINE</color>" : "<color=#ff8a65>SERVER OFFLINE (STANDBY)</color>";
                GUILayout.Label($"<size=12><b>Telemetry ({conn}, 2s poll):</b> Sun Elev {networkBridge.currentSolarElevation:F1}°</size>");
                GUILayout.Label($"<size=12><b>Est. Heat Saved (model estimate):</b> {networkBridge.heatExposureSavedPct:F1}% | Active Tourists: {networkBridge.activeTouristsTotal}</size>");
                GUILayout.Label($"<size=11><b>Advice:</b> {networkBridge.shadeRecommendation}</size>");
            }

            GUILayout.Space(6);
            GUILayout.BeginHorizontal();
            if (GUILayout.Button("1. Shore (Illust.)", GUILayout.Height(28)) && monumentPreview != null) monumentPreview.SelectExhibit(HeritageExhibitType.ShoreTemple);
            if (GUILayout.Button("2. Rathas (Illust.)", GUILayout.Height(28)) && monumentPreview != null) monumentPreview.SelectExhibit(HeritageExhibitType.PanchaRathas);
            if (GUILayout.Button("3. Boulder (Illust.)", GUILayout.Height(28)) && monumentPreview != null) monumentPreview.SelectExhibit(HeritageExhibitType.KrishnasButterball);
            GUILayout.EndHorizontal();

            GUILayout.Space(4);
            GUILayout.BeginHorizontal();
            if (GUILayout.Button(monumentPreview != null && monumentPreview.isExploded ? "Assemble" : "Explode (E)", GUILayout.Height(28)) && monumentPreview != null)
                monumentPreview.ToggleExplodedView();
            if (GUILayout.Button(monumentPreview != null && monumentPreview.autoRotate ? "Pause Spin" : "Auto Spin", GUILayout.Height(28)) && monumentPreview != null)
                monumentPreview.autoRotate = !monumentPreview.autoRotate;
            if (GUILayout.Button("Guide Greet", GUILayout.Height(28)) && avatarGuide != null)
                avatarGuide.PlayWelcomeGreeting();
            GUILayout.EndHorizontal();

            if (monumentPreview != null)
            {
                GUILayout.Space(4);
                GUILayout.BeginHorizontal();
                GUILayout.Label($"<size=11>Sun Sweep ({monumentPreview.simulatedHour:F1}h):</size>", GUILayout.Width(115));
                float newHour = GUILayout.HorizontalSlider(monumentPreview.simulatedHour, 6.0f, 18.0f);
                if (Mathf.Abs(newHour - monumentPreview.simulatedHour) > 0.05f)
                {
                    monumentPreview.animateSunCycle = false;
                    monumentPreview.simulatedHour = newHour;
                }
                if (GUILayout.Button(monumentPreview.animateSunCycle ? "Auto" : "Manual", GUILayout.Width(65)))
                {
                    monumentPreview.animateSunCycle = !monumentPreview.animateSunCycle;
                }
                GUILayout.EndHorizontal();
            }

            GUILayout.EndArea();
        }

        void OnGUI()
        {
            bool hardwareActive = srDisplayController != null && srDisplayController.hardwareSdkActive;
            if (hardwareActive && !forceOperatorHudOnPrimary)
            {
                // Primary Sony ELF-SR1 3D viewport stays clean; secondary SRD2DView operator panel handles UI
                return;
            }
            if (!showOverlayInSimulation || !showOperatorPanel) return;

            DrawOperatorControlsRect(new Rect(24, 24, 465, 345));

            GUI.Box(new Rect(24, Screen.height - 74, 465, 50),
                "<size=11><color=#00e676><b>Drag Orbit • Scroll Zoom • [1-3] Illustrative Models • [S] No-SRD Sim • [H] Hide HUD</b></color>\nSRD2DView Operator Panel mirrors onto secondary Display 1 when connected.</size>");
        }
    }

    /// <summary>
    /// Secondary Display (Display 1) SRD2DView Operator Window GUI component.
    /// Renders operator telemetry & controls on the operator monitor so Display 0 stays 100% pure 3D.
    /// </summary>
    public class KioskOperatorDisplayHUD : MonoBehaviour
    {
        public KioskUIManager uiManager;

        void OnGUI()
        {
            if (uiManager == null || !uiManager.showOperatorPanel) return;
            if (Display.displays.Length <= 1) return;
            uiManager.DrawOperatorControlsRect(new Rect(24, 24, 520, 360));
        }
    }
}
