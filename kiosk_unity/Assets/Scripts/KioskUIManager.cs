using UnityEngine;

namespace LunarAurora.Kiosk
{
    /// <summary>
    /// Exhibition-grade Holographic HUD overlay for the Sony Spatial Reality Display (ELF-SR1) booth.
    /// Allows visitors to switch 3D exhibits, inspect exploded architectural layers, scrub solstice sun time, and check live shade conditions.
    /// </summary>
    public class KioskUIManager : MonoBehaviour
    {
        public SRDisplayViewerController srDisplayController;
        public HolographicMonumentPreview monumentPreview;
        public KioskAvatarGuide avatarGuide;
        public KioskNetworkBridge networkBridge;

        private bool showControls = true;

        void Update()
        {
            // Quick keyboard shortcuts for exhibition demo booths
            if (Input.GetKeyDown(KeyCode.Alpha1) && monumentPreview != null) monumentPreview.SelectExhibit(HeritageExhibitType.SolsticeSunTemple);
            if (Input.GetKeyDown(KeyCode.Alpha2) && monumentPreview != null) monumentPreview.SelectExhibit(HeritageExhibitType.AiravataSculpture);
            if (Input.GetKeyDown(KeyCode.Alpha3) && monumentPreview != null) monumentPreview.SelectExhibit(HeritageExhibitType.LotusGnomonSanctuary);
            if (Input.GetKeyDown(KeyCode.E) && monumentPreview != null) monumentPreview.ToggleExplodedView();
            if (Input.GetKeyDown(KeyCode.H)) showControls = !showControls;
        }

        void OnGUI()
        {
            if (!showControls) return;

            // Sleek Kiosk Overlay for Sony Spatial Reality Display
            GUI.backgroundColor = new Color(0.04f, 0.08f, 0.15f, 0.88f);

            GUILayout.BeginArea(new Rect(24, 24, 430, 330), GUI.skin.box);
            GUILayout.Label("<size=20><b><color=#00e5ff>LUNAR AURORA</color></b></size>");

            string sdkState = (srDisplayController != null && srDisplayController.hardwareSdkActive)
                ? "<color=#00e676>Sony ELF-SR1 Eye-Tracking Active</color>"
                : "<color=#f4c430>Holographic Preview (Ready for Sony SRDisplay SDK)</color>";
            GUILayout.Label($"<size=12>{sdkState}</size>");
            GUILayout.Space(6);

            if (monumentPreview != null)
            {
                GUILayout.Label($"<size=13><b>Exhibit:</b> <color=#ffffff>{monumentPreview.GetActiveExhibitTitle()}</color></size>");
            }

            if (networkBridge != null)
            {
                GUILayout.Label($"<size=12><b>Live Site Sun:</b> {networkBridge.currentSunIntensity} ({networkBridge.currentSolarElevation:F1}°)</size>");
                GUILayout.Label($"<size=12><b>Shade Advice:</b> {networkBridge.shadeRecommendation}</size>");
            }

            GUILayout.Space(8);
            GUILayout.Label("<size=11><color=#8ba2bd>Switch Volumetric Exhibit (Keys 1-3):</color></size>");
            GUILayout.BeginHorizontal();
            if (GUILayout.Button("1. Sun Temple", GUILayout.Height(32)))
                if (monumentPreview != null) monumentPreview.SelectExhibit(HeritageExhibitType.SolsticeSunTemple);
            if (GUILayout.Button("2. Airavata", GUILayout.Height(32)))
                if (monumentPreview != null) monumentPreview.SelectExhibit(HeritageExhibitType.AiravataSculpture);
            if (GUILayout.Button("3. Lotus Dial", GUILayout.Height(32)))
                if (monumentPreview != null) monumentPreview.SelectExhibit(HeritageExhibitType.LotusGnomonSanctuary);
            GUILayout.EndHorizontal();

            GUILayout.Space(6);
            GUILayout.BeginHorizontal();
            if (GUILayout.Button(monumentPreview != null && monumentPreview.isExploded ? "Assemble Layers" : "Exploded View (E)", GUILayout.Height(32)))
                if (monumentPreview != null) monumentPreview.ToggleExplodedView();
            if (GUILayout.Button(monumentPreview != null && monumentPreview.autoRotate ? "Pause Spin" : "Auto Spin", GUILayout.Height(32)))
                if (monumentPreview != null) monumentPreview.autoRotate = !monumentPreview.autoRotate;
            if (GUILayout.Button("Guide Greet", GUILayout.Height(32)))
                if (avatarGuide != null) avatarGuide.PlayWelcomeGreeting();
            GUILayout.EndHorizontal();

            if (monumentPreview != null)
            {
                GUILayout.Space(6);
                GUILayout.BeginHorizontal();
                GUILayout.Label($"<size=11>Sun Time ({monumentPreview.simulatedHour:F1}h):</size>", GUILayout.Width(110));
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

            // Visitor Interaction Prompt at Bottom
            GUI.Box(new Rect(24, Screen.height - 76, 430, 52),
                "<size=12><color=#00e676><b>Drag to Orbit 360° • Scroll to Zoom Depth • Press H to Hide UI</b></color>\nScan your ticket QR code on mobile for your personal guided tour!</size>");
        }
    }
}
