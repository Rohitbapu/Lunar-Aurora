using System;
using UnityEngine;
#if SRDISPLAY_SDK_PRESENT
using SRD.Core;
#endif

namespace LunarAurora.Kiosk
{
    /// <summary>
    /// Controller for Sony Spatial Reality Display (ELF-SR1 / ELF-SR2).
    /// Integrates directly with Sony's SRDManager & SRDisplayBox when SRDisplayUnityPlugin is imported,
    /// and provides a calibrated 4K glasses-free parallax preview camera for standalone desktop testing.
    /// </summary>
    public class SRDisplayViewerController : MonoBehaviour
    {
        [Header("Sony ELF-SR1 Holographic Box Bounds (Meters)")]
        [Tooltip("Physical 15.6-inch ELF-SR1 volumetric projection space: ~0.35m W x 0.20m H x 0.20m D")]
        public Vector3 holographicBoxSize = new Vector3(0.35f, 0.20f, 0.20f);

        [Tooltip("Front clipping safety margin so geometry stays cleanly inside the volumetric prism")]
        public float frontClippingOffset = 0.04f;

        [Tooltip("Nominal viewer distance in front of the 15.6-inch lenticular lens")]
        public float focalDistance = 0.45f;

        [Header("Tracking & Camera References")]
        public bool hardwareSdkActive = false;
        public Camera fallbackHoloCamera;
        public Transform watcherTargetTransform;

        void Awake()
        {
#if SRDISPLAY_SDK_PRESENT
            var srdManager = SRDSceneEnvironment.GetSRDManager();
            if (srdManager != null)
            {
                hardwareSdkActive = true;
                if (fallbackHoloCamera != null) fallbackHoloCamera.gameObject.SetActive(false);

                Transform watcher = srdManager.transform.Find("WatcherAnchor");
                if (watcher != null) watcherTargetTransform = watcher;

                Debug.Log("[SRDisplayViewerController] Sony SRDisplay SDK hardware tracking active.");
                return;
            }
#endif
            hardwareSdkActive = false;
            if (fallbackHoloCamera == null)
            {
                fallbackHoloCamera = Camera.main;
            }
            ConfigureFallbackViewport();
        }

        void Update()
        {
            if (hardwareSdkActive) return;

            // Gentle breathing eye-parallax simulation when running on a standard monitor without ELF-SR1 hardware
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
            // Draw Sony ELF-SR1 15.6" physical volumetric prism gizmo in Scene View
            Gizmos.color = hardwareSdkActive ? new Color(0f, 1f, 0.5f, 0.6f) : new Color(0f, 0.9f, 1f, 0.45f);
            Gizmos.DrawWireCube(Vector3.zero, holographicBoxSize);
        }
    }
}
