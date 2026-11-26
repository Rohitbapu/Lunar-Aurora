using UnityEngine;

namespace LunarAurora.Kiosk
{
    /// <summary>
    /// Exhibition & Operator HUD Controller.
    /// - Runs honestly in "No-SRD simulation mode" until the Sony SRDisplay plugin is installed.
    /// - Mirrors telemetry and interactive controls onto "Operator HUD (second display)" when Display 1 exists.
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
        private string dateEditBuffer = "2027-01-11";

        void Start()
        {
            if (networkBridge != null && !string.IsNullOrEmpty(networkBridge.queryDate))
            {
                dateEditBuffer = networkBridge.queryDate;
            }
        }

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
            GUI.backgroundColor = new Color(0.04f, 0.08f, 0.15f, 0.92f);
            GUILayout.BeginArea(areaRect, GUI.skin.box);
            GUILayout.Label("<size=16><b><color=#00e5ff>LUNAR AURORA • Operator HUD (second display)</color></b></size>");

            string sdkState = "<color=#f4c430>No-SRD simulation mode (Sony plugin not installed)</color>";
            GUILayout.Label($"<size=12>{sdkState} • <b>{smoothedFps:F0} FPS</b> • VSync={QualitySettings.vSyncCount}</size>");
            GUILayout.Space(4);

            if (monumentPreview != null)
            {
                GUILayout.Label($"<size=12><b>3D View:</b> <color=#ffffff>{monumentPreview.GetActiveExhibitTitle()}</color></size>");
            }

            if (networkBridge != null)
            {
                if (networkBridge.backendConnected)
                {
                    GUILayout.Label(
                        $"<size=12><b>Telemetry (<color=#00e676>ONLINE NOAA</color>):</b> {networkBridge.currentDate} | Elev {networkBridge.currentSolarElevation:F1}° | Azim {networkBridge.currentSolarAzimuth:F1}°</size>"
                    );
                    GUILayout.Label(
                        $"<size=12><b>Illustrative Shade Score (<color=#ffca28>ASSUMED WEIGHTS</color>):</b> {networkBridge.heatExposureSavedPct:F1}% | Tourists: {networkBridge.activeTouristsTotal}</size>"
                    );
                    GUILayout.Label("<size=10><color=#b0bec5>Distances from OpenStreetMap; canopy weights assumed/illustrative (not measured sun)</color></size>");
                    GUILayout.Label($"<size=11><b>Advice:</b> {networkBridge.shadeRecommendation}</size>");
                }
                else
                {
                    GUILayout.Label("<size=12><b>Telemetry (<color=#ff8a65>SERVER OFFLINE - STANDBY</color>):</b> Start FastAPI backend on :8000 for live NOAA solar arc.</size>");
                }
            }

            GUILayout.Space(6);
            GUILayout.BeginHorizontal();
            if (GUILayout.Button("1. Shore (Illust.)", GUILayout.Height(26)) && monumentPreview != null) monumentPreview.SelectExhibit(HeritageExhibitType.ShoreTemple);
            if (GUILayout.Button("2. Rathas (Illust.)", GUILayout.Height(26)) && monumentPreview != null) monumentPreview.SelectExhibit(HeritageExhibitType.PanchaRathas);
            if (GUILayout.Button("3. Boulder (Illust.)", GUILayout.Height(26)) && monumentPreview != null) monumentPreview.SelectExhibit(HeritageExhibitType.KrishnasButterball);
            GUILayout.EndHorizontal();

            GUILayout.Space(4);
            GUILayout.BeginHorizontal();
            if (GUILayout.Button(monumentPreview != null && monumentPreview.isExploded ? "Assemble" : "Explode (E)", GUILayout.Height(26)) && monumentPreview != null)
                monumentPreview.ToggleExplodedView();
            if (GUILayout.Button(monumentPreview != null && monumentPreview.autoRotate ? "Pause Spin" : "Auto Spin", GUILayout.Height(26)) && monumentPreview != null)
                monumentPreview.autoRotate = !monumentPreview.autoRotate;
            if (GUILayout.Button("Guide Greet", GUILayout.Height(26)) && avatarGuide != null)
                avatarGuide.PlayWelcomeGreeting();
            GUILayout.EndHorizontal();

            if (monumentPreview != null)
            {
                GUILayout.Space(4);
                GUILayout.BeginHorizontal();
                GUILayout.Label("<size=11>NOAA Date:</size>", GUILayout.Width(68));
                dateEditBuffer = GUILayout.TextField(dateEditBuffer, 10, GUILayout.Width(90));
                if (GUILayout.Button("Apply Date", GUILayout.Width(80)) && networkBridge != null)
                {
                    monumentPreview.simulatedDate = dateEditBuffer;
                    networkBridge.SetSolarQuery(dateEditBuffer, monumentPreview.simulatedHour, true);
                }
                if (GUILayout.Button("Finale Jan 11", GUILayout.Width(85)) && networkBridge != null)
                {
                    dateEditBuffer = "2027-01-11";
                    monumentPreview.simulatedDate = dateEditBuffer;
                    networkBridge.SetSolarQuery(dateEditBuffer, monumentPreview.simulatedHour, true);
                }
                GUILayout.EndHorizontal();

                GUILayout.BeginHorizontal();
                GUILayout.Label($"<size=11>IST Hour ({monumentPreview.simulatedHour:F1}h):</size>", GUILayout.Width(115));
                float newHour = GUILayout.HorizontalSlider(monumentPreview.simulatedHour, 6.0f, 18.0f);
                if (Mathf.Abs(newHour - monumentPreview.simulatedHour) > 0.05f)
                {
                    monumentPreview.animateSunCycle = false;
                    monumentPreview.simulatedHour = newHour;
                    if (networkBridge != null) networkBridge.SetSolarQuery(monumentPreview.simulatedDate, newHour, true);
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
            if (!showOverlayInSimulation || !showOperatorPanel) return;

            DrawOperatorControlsRect(new Rect(24, 24, 485, 365));

            GUI.Box(new Rect(24, Screen.height - 74, 485, 50),
                "<size=11><color=#00e676><b>Drag Orbit • Scroll Zoom • [1-3] Illustrative Models • [S] No-SRD Sim • [H] Hide HUD</b></color>\nNo-SRD simulation mode • Operator HUD (second display) mirrors onto Display 1 if connected.</size>");
        }
    }

    /// <summary>
    /// Secondary Display (Display 1) Operator HUD (second display) GUI component.
    /// Renders operator telemetry & controls on Display 1 when a secondary monitor is attached.
    /// </summary>
    public class KioskOperatorDisplayHUD : MonoBehaviour
    {
        public KioskUIManager uiManager;

        void OnGUI()
        {
            if (uiManager == null || !uiManager.showOperatorPanel) return;
            if (Display.displays.Length <= 1) return;
            uiManager.DrawOperatorControlsRect(new Rect(24, 24, 520, 365));
        }
    }
}
