using System.Collections;
using UnityEngine;

namespace LunarAurora.Kiosk
{
    /// <summary>
    /// 3D Holographic Guide Avatar on the Sony Spatial Reality Display.
    /// Welcomes visitors at the ticketing entrance with gaze tracking, holographic rings, and gestures.
    /// </summary>
    public class KioskAvatarGuide : MonoBehaviour
    {
        [Header("Avatar Components")]
        public Transform avatarHead;
        public Transform avatarBody;
        public Transform orbitingHoloRings;

        [Header("Animation States")]
        public bool isSpeaking = false;
        public float breathingSpeed = 1.8f;
        public float ringRotationSpeed = 35.0f;

        [Header("Visitor Tracking (Sony Eye Tracking integration)")]
        public Transform visitorFaceTarget;

        private Vector3 initialHeadPos;

        void Start()
        {
            if (avatarBody == null || avatarHead == null)
            {
                GenerateProceduralGuide();
            }
            if (avatarHead != null)
            {
                initialHeadPos = avatarHead.localPosition;
            }
        }

        void Update()
        {
            float t = Time.time;

            if (avatarBody != null)
            {
                avatarBody.localPosition = new Vector3(0, Mathf.Sin(t * breathingSpeed) * 0.004f, 0);
            }

            if (orbitingHoloRings != null)
            {
                orbitingHoloRings.Rotate(Vector3.up, ringRotationSpeed * Time.deltaTime, Space.Self);
            }

            if (avatarHead != null)
            {
                if (visitorFaceTarget != null)
                {
                    avatarHead.LookAt(visitorFaceTarget);
                }
                else
                {
                    float gazeX = Mathf.Sin(t * 0.6f) * 4.0f;
                    float gazeY = Mathf.Cos(t * 0.4f) * 6.0f;
                    avatarHead.localRotation = Quaternion.Euler(gazeX, gazeY, 0);
                }

                if (isSpeaking)
                {
                    float nod = Mathf.Sin(t * 8.0f) * 0.004f;
                    avatarHead.localPosition = initialHeadPos + new Vector3(0, nod, 0);
                }
            }
        }

        void GenerateProceduralGuide()
        {
            GameObject guideRoot = new GameObject("ProceduralHoloGuide");
            guideRoot.transform.SetParent(this.transform, false);

            // Stylized Body / Robe
            GameObject bodyObj = GameObject.CreatePrimitive(PrimitiveType.Capsule);
            bodyObj.name = "GuideBody";
            bodyObj.transform.SetParent(guideRoot.transform, false);
            bodyObj.transform.localScale = new Vector3(0.055f, 0.075f, 0.055f);
            bodyObj.transform.localPosition = new Vector3(0, 0.075f, 0);
            var bodyMat = bodyObj.GetComponent<Renderer>().material;
            bodyMat.color = new Color(0.05f, 0.25f, 0.45f);
            avatarBody = bodyObj.transform;

            // Stylized Head
            GameObject headObj = GameObject.CreatePrimitive(PrimitiveType.Sphere);
            headObj.name = "GuideHead";
            headObj.transform.SetParent(guideRoot.transform, false);
            headObj.transform.localScale = new Vector3(0.042f, 0.045f, 0.042f);
            headObj.transform.localPosition = new Vector3(0, 0.165f, 0);
            var headMat = headObj.GetComponent<Renderer>().material;
            headMat.color = new Color(0.95f, 0.77f, 0.19f);
            avatarHead = headObj.transform;

            // Orbiting Hologram Pedestal Ring
            GameObject ringObj = GameObject.CreatePrimitive(PrimitiveType.Cylinder);
            ringObj.name = "HoloRing";
            ringObj.transform.SetParent(guideRoot.transform, false);
            ringObj.transform.localScale = new Vector3(0.11f, 0.004f, 0.11f);
            ringObj.transform.localPosition = new Vector3(0, 0.005f, 0);
            var ringMat = ringObj.GetComponent<Renderer>().material;
            ringMat.color = new Color(0f, 0.9f, 1f);
            orbitingHoloRings = ringObj.transform;
        }

        public void PlayWelcomeGreeting()
        {
            StartCoroutine(GreetingRoutine());
        }

        private IEnumerator GreetingRoutine()
        {
            isSpeaking = true;
            Debug.Log("[KioskAvatarGuide] 'Welcome to Lunar Aurora! Inspect the monument preview in glasses-free 3D, or scan the QR code to take me along on your phone.'");
            yield return new WaitForSeconds(6.0f);
            isSpeaking = false;
        }
    }
}
