using UnityEngine;

namespace LunarAurora.Kiosk
{
    /// <summary>
    /// Exhibition HUD Controller for Sony ELF-SR1 Kiosk.
    /// Keeps the 3D lenticular screen (Display 0) completely free of floating 2D text when hardware SDK is active,
    /// rendering telemetry controls on a secondary operator display or in No-SRD Simulation Mode.
    /// </summary>
    public class KioskUIManager : MonoBehaviour
    {
        public SRDisplayViewerController srDisplayController;
        public HolographicMonumentPreview monumentPreview;
        public KioskAvatarGuide avatarGuide;
        public KioskNetworkBridge networkBridge;

        [Header("Sony Spec: Never draw 2D GUI over 3D lenticular viewport when hardware SDK is live")]
        public bool showOverlayInSimulation = true;
        public bool forceOperatorHudOnPrimary = false;

        private float smoothedFps = 60.0f;

        void Update()
        {
            float instFps = Time.deltaTime > 0.0001f ? (1.0f / Time.deltaTime) : 60.0f;
            smoothedFps = Mathf.Lerp(smoothedFps, instFps, 0.08f);

            if (Input.GetKeyDown(KeyCode.Alpha1) && monumentPreview != null) monumentPreview.SelectExhibit(HeritageExhibitType.SolsticeSunTemple);
            if (Input.GetKeyDown(KeyCode.Alpha2) && monumentPreview != null) monumentPreview.SelectExhibit(HeritageExhibitType.AiravataSculpture);
            if (Input.GetKeyDown(KeyCode.Alpha3) && monumentPreview != null) monumentPreview.SelectExhibit(HeritageExhibitType.LotusGnomonSanctuary);
            if (Input.GetKeyDown(KeyCode.E) && monumentPreview != null) monumentPreview.ToggleExplodedView();
            if (Input.GetKeyDown(KeyCode.H)) showOverlayInSimulation = !showOverlayInSimulation;
            if (Input.GetKeyDown(KeyCode.S) && srDisplayController != null) srDisplayController.ToggleNoSrdSimulation();
        }

        void OnGUI()
        {
            bool hardwareActive = srDisplayController != null && srDisplayController.hardwareSdkActive;
            if (hardwareActive && !forceOperatorHudOnPrimary)
            {
                // Display 0 stays 100% pure lenticular 3D hologram per Sony SRDisplay best practices
                return;
            }
            if (!showOverlayInSimulation) return;

            GUI.backgroundColor = new Color(0.04f, 0.08f, 0.15f, 0.88f);
            GUILayout.BeginArea(new Rect(24, 24, 455, 360), GUI.skin.box);
            GUILayout.Label($"<size=19><b><color=#00e5ff>LUNAR AURORA • MAHABALIPURAM KIOSK</color></b></size>");

            string sdkState = hardwareActive
                ? "<color=#00e676>Sony ELF-SR1 Eye-Tracking Active (VSync=0)</color>"
                : "<color=#f4c430>No-SRD Simulation Mode (VSync=0) • Toggle [S]</color>";
            GUILayout.Label($"<size=12>{sdkState} • <b>{smoothedFps:F0} FPS</b></size>");
            GUILayout.Space(6);

            if (monumentPreview != null)
            {
                GUILayout.Label($"<size=13><b>3D Exhibit:</b> <color=#ffffff>{monumentPreview.GetActiveExhibitTitle()}</color></size>");
            }

            if (networkBridge != null)
            {
                string conn = networkBridge.backendConnected ? "<color=#00e676>ONLINE</color>" : "<color=#ffb74d>STANDBY</color>";
                GUILayout.Label($"<size=12><b>Telemetry ({conn}, 2s poll):</b> Sun {networkBridge.currentSolarElevation:F1}° • <b>Heat Saved: {networkBridge.heatExposureSavedPct:F0}%</b></size>");
                GUILayout.Label($"<size=12><b>Live Sanctuary Visitors:</b> {networkBridge.activeTouristsTotal} active sessions</size>");
                GUILayout.Label($"<size=12><b>Advice:</b> {networkBridge.shadeRecommendation}</size>");
            }

            GUILayout.Space(8);
            GUILayout.BeginHorizontal();
            if (GUILayout.Button("1. Shore Vimana", GUILayout.Height(30)) && monumentPreview != null) monumentPreview.SelectExhibit(HeritageExhibitType.SolsticeSunTemple);
            if (GUILayout.Button("2. Yali Relief", GUILayout.Height(30)) && monumentPreview != null) monumentPreview.SelectExhibit(HeritageExhibitType.AiravataSculpture);
            if (GUILayout.Button("3. Wheel & Basin", GUILayout.Height(30)) && monumentPreview != null) monumentPreview.SelectExhibit(HeritageExhibitType.LotusGnomonSanctuary);
            GUILayout.EndHorizontal();

            GUILayout.Space(5);
            GUILayout.BeginHorizontal();
            if (GUILayout.Button(monumentPreview != null && monumentPreview.isExploded ? "Assemble Layers" : "Exploded View (E)", GUILayout.Height(30)) && monumentPreview != null)
                monumentPreview.ToggleExplodedView();
            if (GUILayout.Button(monumentPreview != null && monumentPreview.autoRotate ? "Pause Spin" : "Auto Spin", GUILayout.Height(30)) && monumentPreview != null)
                monumentPreview.autoRotate = !monumentPreview.autoRotate;
            if (GUILayout.Button("Guide Greet", GUILayout.Height(30)) && avatarGuide != null)
                avatarGuide.PlayWelcomeGreeting();
            GUILayout.EndHorizontal();

            if (monumentPreview != null)
            {
                GUILayout.Space(6);
                GUILayout.BeginHorizontal();
                GUILayout.Label($"<size=11>Sun Time ({monumentPreview.simulatedHour:F1}h):</size>", GUILayout.Width(115));
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

            GUI.Box(new Rect(24, Screen.height - 74, 455, 50),
                "<size=12><color=#00e676><b>Drag Orbit • Scroll Depth • [E] Explode • [S] Sim Mode • [H] Hide HUD</b></color>\nDual-Screen Ready: Lenticular 3D isolated when Sony ELF-SR1 SDK active.</size>");
        }
    }
}
