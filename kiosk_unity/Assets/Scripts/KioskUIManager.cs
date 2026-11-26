using UnityEngine;

namespace LunarAurora.Kiosk
{
    /// <summary>
    /// Displays holographic HUD and controls on the Sony Spatial Reality Display.
    /// Uses IMGUI / World-Space Canvas within the ELF-SR1 depth bounds.
    /// </summary>
    public class KioskUIManager : MonoBehaviour
    {
        public HolographicMonumentPreview monumentPreview;
        public KioskAvatarGuide avatarGuide;
        public KioskNetworkBridge networkBridge;

        private bool showControls = true;

        void OnGUI()
        {
            if (!showControls) return;

            // Sleek Kiosk Overlay for Sony Spatial Reality Display
            GUI.backgroundColor = new Color(0.04f, 0.08f, 0.15f, 0.85f);
            
            // Header
            GUILayout.BeginArea(new Rect(20, 20, 420, 260), GUI.skin.box);
            GUILayout.Label("<size=18><b><color=#00e5ff>LUNAR AURORA</color></b></size>");
            GUILayout.Label("<size=12><color=#f4c430>Glasses-Free Holographic Kiosk (Sony SRDisplay)</color></size>");
            GUILayout.Space(8);

            if (networkBridge != null)
            {
                GUILayout.Label($"<b>Sun Intensity:</b> {networkBridge.currentSunIntensity} ({networkBridge.currentSolarElevation:F1}°)");
                GUILayout.Label($"<b>Advice:</b> {networkBridge.shadeRecommendation}");
            }

            GUILayout.Space(10);
            GUILayout.BeginHorizontal();
            if (GUILayout.Button("Toggle Exploded View", GUILayout.Height(36)))
            {
                if (monumentPreview != null) monumentPreview.ToggleExplodedView();
            }
            if (GUILayout.Button(monumentPreview != null && monumentPreview.autoRotate ? "Pause Rotation" : "Auto Rotate", GUILayout.Height(36)))
            {
                if (monumentPreview != null) monumentPreview.autoRotate = !monumentPreview.autoRotate;
            }
            GUILayout.EndHorizontal();

            GUILayout.Space(6);
            if (GUILayout.Button("Guide Welcome Greeting", GUILayout.Height(32)))
            {
                if (avatarGuide != null) avatarGuide.PlayWelcomeGreeting();
            }

            GUILayout.EndArea();

            // QR Code Notice at bottom
            GUI.Box(new Rect(20, Screen.height - 70, 420, 50), 
                "<size=12><color=#00e676><b>Scan the entrance QR code with your phone</b>\nto open the Zero-Install WebXR Tour Guide!</color></size>");
        }
    }
}

