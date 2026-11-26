using UnityEngine;

namespace LunarAurora.Kiosk
{
    /// <summary>
    /// Display & Simulation Camera Rig Controller for Lunar Aurora Unity Kiosk.
    /// Currently runs in "No-SRD simulation mode" because the Sony SRDisplayUnityPlugin
    /// is not installed in Packages/manifest.json and SRDISPLAY_SDK_PRESENT is unset.
    /// See docs/sony_srd_integration_todo.md for Sony hardware integration steps.
    /// </summary>
    public class SRDisplayViewerController : MonoBehaviour
    {
        [Header("Simulated Holographic Box Bounds (Meters)")]
        public Vector3 holographicBoxSize = new Vector3(0.35f, 0.20f, 0.20f);
        public float frontClippingOffset = 0.04f;
        public float focalDistance = 0.45f;

        [Header("Simulation & Multi-Display State")]
        public bool hardwareSdkActive = false;
        public bool forceNoSrdSimulation = true;
        public bool dualDisplayActive = false;
        public Camera fallbackHoloCamera;
        public Transform watcherTargetTransform;

        void Awake()
        {
            QualitySettings.vSyncCount = 0;
            Application.targetFrameRate = 60;

            if (Display.displays.Length > 1)
            {
                Display.displays[1].Activate();
                dualDisplayActive = true;
            }

            ApplyTrackingMode();
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
