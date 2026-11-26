using System;
using System.Collections;
using UnityEngine;

namespace LunarAurora.Kiosk
{
    /// <summary>
    /// Controller for Sony Spatial Reality Display (ELF-SR1 / ELF-SR2).
    /// Manages glasses-free 3D holographic volume, eye-tracking bounds, and depth clipping.
    /// </summary>
    public class SRDisplayViewerController : MonoBehaviour
    {
        [Header("Sony SRDisplay Holographic Box Settings")]
        [Tooltip("Depth scale of the 3D projection box (ELF-SR1 standard volume is approx 0.35m x 0.20m x 0.20m)")]
        public Vector3 holographicBoxSize = new Vector3(0.35f, 0.20f, 0.20f);
        
        [Tooltip("Near clipping plane offset to prevent hologram breaking out past the physical glass")]
        public float frontClippingOffset = 0.05f;

        [Tooltip("Target focal distance in meters")]
        public float focalDistance = 0.45f;

        [Header("Eye Tracking Status")]
        public bool isEyeTracked = false;
        public Vector3 currentFacePosition = new Vector3(0, 0, -0.45f);

        [Header("Camera Rig References")]
        public Camera mainHoloCamera;
        public Camera leftEyeCamera;
        public Camera rightEyeCamera;

        void Awake()
        {
            if (mainHoloCamera == null)
            {
                mainHoloCamera = Camera.main;
            }
            ConfigureHolographicViewport();
        }

        void Start()
        {
            Debug.Log("[SRDisplayViewerController] Initialized Sony Spatial Reality Display Kiosk Manager.");
        }

        void Update()
        {
            // Simulate / update face tracking parallax when testing on desktop or using Sony eye sensor
            UpdateEyeTrackingParallax();
        }

        void ConfigureHolographicViewport()
        {
            if (mainHoloCamera != null)
            {
                mainHoloCamera.nearClipPlane = Mathf.Max(0.01f, focalDistance - holographicBoxSize.z * 0.5f - frontClippingOffset);
                mainHoloCamera.farClipPlane = focalDistance + holographicBoxSize.z * 0.5f + 1.0f;
                mainHoloCamera.fieldOfView = 45f;
            }
        }

        void UpdateEyeTrackingParallax()
        {
            // On desktop test mode without Sony ELF-SR1 connected, provide subtle gentle parallax rotation
            // On real Sony device, the Sony SRDisplay SDK plugin overrides eye position directly via native plugin
            float t = Time.time;
            float simulatedEyeX = Mathf.Sin(t * 0.8f) * 0.04f;
            float simulatedEyeY = Mathf.Cos(t * 0.6f) * 0.02f;

            if (mainHoloCamera != null)
            {
                Vector3 basePos = new Vector3(0, 0, -focalDistance);
                mainHoloCamera.transform.position = basePos + new Vector3(simulatedEyeX, simulatedEyeY, 0);
                mainHoloCamera.transform.LookAt(Vector3.zero);
            }
        }

        void OnDrawGizmos()
        {
            // Draw holographic viewing frustum and volume box in Unity Scene view
            Gizmos.color = new Color(0f, 0.9f, 1f, 0.4f);
            Gizmos.DrawWireCube(Vector3.zero, holographicBoxSize);

            Gizmos.color = Color.yellow;
            Gizmos.DrawWireSphere(currentFacePosition, 0.04f);
        }
    }
}

