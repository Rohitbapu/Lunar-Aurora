using System;
using UnityEngine;
#if SRDISPLAY_SDK_PRESENT
using SRD.Core;
#endif

namespace LunarAurora.Kiosk
{
    /// <summary>
    /// Controller for Sony Spatial Reality Display (ELF-SR1 / ELF-SR2).
    /// Enforces VSync Count = 0 ("Don't Sync") per Sony SRDisplay hardware spec,
    /// activates secondary operator display when connected, and supports No-SRD Simulation Mode.
    /// </summary>
    public class SRDisplayViewerController : MonoBehaviour
    {
        [Header("Sony ELF-SR1 Holographic Box Bounds (Meters)")]
        public Vector3 holographicBoxSize = new Vector3(0.35f, 0.20f, 0.20f);
        public float frontClippingOffset = 0.04f;
        public float focalDistance = 0.45f;

        [Header("Tracking, VSync & Simulation Modes")]
        public bool hardwareSdkActive = false;
        public bool forceNoSrdSimulation = false;
        public bool dualDisplayActive = false;
        public Camera fallbackHoloCamera;
        public Transform watcherTargetTransform;

        void Awake()
        {
            // Mandatory Sony ELF-SR1 spec: VSync MUST be 0 to prevent stereo lenticular ghosting
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
            var srdManager = SRDSceneEnvironment.GetSRDManager();
            if (srdManager != null && !forceNoSrdSimulation)
            {
                hardwareSdkActive = true;
                if (fallbackHoloCamera != null) fallbackHoloCamera.gameObject.SetActive(false);

                Transform watcher = srdManager.transform.Find("WatcherAnchor");
                if (watcher != null) watcherTargetTransform = watcher;

                Debug.Log("[SRDisplayViewerController] Sony SRDisplay SDK eye-tracking active (VSync=0).");
                return;
            }
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
            Gizmos.color = hardwareSdkActive ? new Color(0f, 1f, 0.5f, 0.6f) : new Color(0f, 0.9f, 1f, 0.45f);
            Gizmos.DrawWireCube(Vector3.zero, holographicBoxSize);
        }
    }
}
