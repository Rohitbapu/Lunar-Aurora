using System;
using UnityEngine;

namespace LunarAurora.Kiosk
{
    /// <summary>
    /// Display & Simulation Camera Rig Controller for Lunar Aurora Unity Kiosk.
    /// Defaults to 3840x2160 FullScreenWindow (standalone build target), with a "-windowed"
    /// (or "--windowed") command-line flag to launch windowed during development.
    /// Currently runs in "No-SRD simulation mode" until Sony SRDisplayUnityPlugin is installed.
    /// See docs/sony_srd_integration_todo.md for Sony hardware integration steps.
    /// </summary>
    public class SRDisplayViewerController : MonoBehaviour
    {
        [Header("Simulated Holographic Box Bounds (Meters)")]
        public Vector3 holographicBoxSize = new Vector3(0.35f, 0.20f, 0.20f);
        public float frontClippingOffset = 0.04f;
        public float focalDistance = 0.45f;

        [Header("Display & Simulation Mode")]
        public bool hardwareSdkActive = false;
        public bool forceNoSrdSimulation = true;
        public bool dualDisplayActive = false;
        public bool launchedWindowed = false;
        public Camera fallbackHoloCamera;
        public Transform watcherTargetTransform;

        void Awake()
        {
            QualitySettings.vSyncCount = 0;
            Application.targetFrameRate = 60;

            ApplyDisplayModeFromCli();

            if (Display.displays.Length > 1)
            {
                Display.displays[1].Activate();
                dualDisplayActive = true;
            }

            ApplyTrackingMode();
        }

        private void ApplyDisplayModeFromCli()
        {
            string[] args = Environment.GetCommandLineArgs();
            launchedWindowed = false;
            for (int i = 0; i < args.Length; i++)
            {
                if (string.Equals(args[i], "-windowed", StringComparison.OrdinalIgnoreCase)
                    || string.Equals(args[i], "--windowed", StringComparison.OrdinalIgnoreCase))
                {
                    launchedWindowed = true;
                    break;
                }
            }

            if (launchedWindowed)
            {
                int w = Mathf.Max(960, Mathf.Min(1600, Display.main.systemWidth - 120));
                int h = Mathf.Max(540, Mathf.Min(900, Display.main.systemHeight - 120));
                Screen.SetResolution(w, h, FullScreenMode.Windowed);
                Debug.Log($"[SRDisplayViewerController] CLI -windowed switch active: {w}x{h} Windowed (No-SRD simulation mode).");
            }
            else
            {
                Screen.SetResolution(3840, 2160, FullScreenMode.FullScreenWindow);
                Debug.Log("[SRDisplayViewerController] Default display mode active: 3840x2160 FullScreenWindow (No-SRD simulation mode). Pass -windowed for dev.");
            }
        }

        public void ApplyTrackingMode()
        {
#if SRDISPLAY_SDK_PRESENT
            // TODO (see docs/sony_srd_integration_todo.md):
            // Once Sony's official SRDisplayUnityPlugin is imported and symbol names are verified
            // against the installed Sony package, bind the Sony SDK camera/rig active state here.
            Debug.Log("[SRDisplayViewerController] SRDISPLAY_SDK_PRESENT defined; check docs/sony_srd_integration_todo.md to bind Sony SDK types.");
#endif
            hardwareSdkActive = false;
            if (fallbackHoloCamera == null) fallbackHoloCamera = Camera.main;
            if (fallbackHoloCamera != null)
            {
                fallbackHoloCamera.gameObject.SetActive(true);
                ConfigureFallbackViewport();
            }
        }

        public void ToggleNoSrdSimulation()
        {
            forceNoSrdSimulation = !forceNoSrdSimulation;
            ApplyTrackingMode();
        }

        void Update()
        {
            if (hardwareSdkActive) return;

            float t = Time.time;
            float simEyeX = Mathf.Sin(t * 0.65f) * 0.035f;
            float simEyeY = Mathf.Cos(t * 0.50f) * 0.015f;

            if (fallbackHoloCamera != null)
            {
                Vector3 basePos = new Vector3(0f, 0.05f, -focalDistance);
                fallbackHoloCamera.transform.position = basePos + new Vector3(simEyeX, simEyeY, 0f);
                fallbackHoloCamera.transform.LookAt(new Vector3(0f, 0.02f, 0f));

                if (watcherTargetTransform != null)
                {
                    watcherTargetTransform.position = fallbackHoloCamera.transform.position;
                }
            }
        }

        void ConfigureFallbackViewport()
        {
            if (fallbackHoloCamera != null)
            {
                fallbackHoloCamera.nearClipPlane = Mathf.Max(0.02f, focalDistance - holographicBoxSize.z * 0.5f - frontClippingOffset);
                fallbackHoloCamera.farClipPlane = focalDistance + holographicBoxSize.z * 0.5f + 2.0f;
                fallbackHoloCamera.fieldOfView = 36f;
            }
        }

        void OnDrawGizmos()
        {
            Gizmos.color = new Color(0f, 0.9f, 1f, 0.45f);
            Gizmos.DrawWireCube(Vector3.zero, holographicBoxSize);
        }
    }
}
