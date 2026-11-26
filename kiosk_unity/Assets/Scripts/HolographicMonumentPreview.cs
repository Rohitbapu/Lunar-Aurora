using System.Collections;
using System.Collections.Generic;
using UnityEngine;

namespace LunarAurora.Kiosk
{
    /// <summary>
    /// Interactive 3D Monument Hologram for the ticketing gate kiosk.
    /// Rotates smoothly, shows architectural highlights, and simulates solstice lighting.
    /// </summary>
    public class HolographicMonumentPreview : MonoBehaviour
    {
        [Header("Monument Structure")]
        public Transform rootMonumentModel;
        public Transform templeSpire;
        public Transform mainSanctum;
        public Transform basePedestal;
        public Transform colonnadePillars;

        [Header("Rotation Settings")]
        public bool autoRotate = true;
        public float rotationSpeed = 15.0f; // deg per sec

        [Header("Exploded View Mode")]
        public bool isExploded = false;
        public float explodeDistance = 0.08f;
        public float animationSpeed = 2.5f;

        private Vector3 initialSpirePos;
        private Vector3 initialSanctumPos;
        private Vector3 initialPillarsPos;

        [Header("Solstice Sunlight Simulation")]
        public Light directionalSunLight;
        public float simulatedHour = 12.0f;
        public bool animateSunCycle = true;

        void Start()
        {
            if (rootMonumentModel == null)
            {
                rootMonumentModel = this.transform;
            }

            // If subcomponents are null, generate procedural monument structure
            if (templeSpire == null || mainSanctum == null)
            {
                GenerateProceduralMonument();
            }

            if (templeSpire != null) initialSpirePos = templeSpire.localPosition;
            if (mainSanctum != null) initialSanctumPos = mainSanctum.localPosition;
            if (colonnadePillars != null) initialPillarsPos = colonnadePillars.localPosition;
        }

        void Update()
        {
            // 1. Turntable Rotation
            if (autoRotate && rootMonumentModel != null)
            {
                rootMonumentModel.Rotate(Vector3.up, rotationSpeed * Time.deltaTime, Space.World);
            }

            // 2. Exploded View Lerp
            HandleExplodedView();

            // 3. Sun Solstice Lighting
            if (animateSunCycle && directionalSunLight != null)
            {
                simulatedHour += Time.deltaTime * 0.5f;
                if (simulatedHour > 18.0f) simulatedHour = 6.0f;
                UpdateSunLightAngle();
            }
        }

        public void ToggleExplodedView()
        {
            isExploded = !isExploded;
        }

        void HandleExplodedView()
        {
            if (templeSpire != null)
            {
                Vector3 targetSpire = isExploded ? initialSpirePos + Vector3.up * (explodeDistance * 1.5f) : initialSpirePos;
                templeSpire.localPosition = Vector3.Lerp(templeSpire.localPosition, targetSpire, Time.deltaTime * animationSpeed);
            }

            if (colonnadePillars != null)
            {
                Vector3 targetPillars = isExploded ? initialPillarsPos + Vector3.right * explodeDistance : initialPillarsPos;
                colonnadePillars.localPosition = Vector3.Lerp(colonnadePillars.localPosition, targetPillars, Time.deltaTime * animationSpeed);
            }
        }

        void UpdateSunLightAngle()
        {
            float angle = ((simulatedHour - 6.0f) / 12.0f) * 180.0f;
            directionalSunLight.transform.rotation = Quaternion.Euler(angle * 0.7f, angle, 0);
        }

        void GenerateProceduralMonument()
        {
            GameObject monumentRoot = new GameObject("ProceduralTempleMonument");
            monumentRoot.transform.SetParent(this.transform, false);

            // Base Pedestal
            GameObject baseObj = GameObject.CreatePrimitive(PrimitiveType.Cube);
            baseObj.name = "BasePedestal";
            baseObj.transform.SetParent(monumentRoot.transform, false);
            baseObj.transform.localScale = new Vector3(0.24f, 0.03f, 0.24f);
            baseObj.transform.localPosition = new Vector3(0, -0.05f, 0);
            basePedestal = baseObj.transform;

            // Main Sanctum
            GameObject sanctumObj = GameObject.CreatePrimitive(PrimitiveType.Cube);
            sanctumObj.name = "MainSanctum";
            sanctumObj.transform.SetParent(monumentRoot.transform, false);
            sanctumObj.transform.localScale = new Vector3(0.16f, 0.08f, 0.16f);
            sanctumObj.transform.localPosition = new Vector3(0, 0.005f, 0);
            mainSanctum = sanctumObj.transform;

            // Temple Spire / Vimana (Pyramidal cylinder)
            GameObject spireObj = GameObject.CreatePrimitive(PrimitiveType.Cylinder);
            spireObj.name = "TempleSpire";
            spireObj.transform.SetParent(monumentRoot.transform, false);
            spireObj.transform.localScale = new Vector3(0.10f, 0.07f, 0.10f);
            spireObj.transform.localPosition = new Vector3(0, 0.08f, 0);
            templeSpire = spireObj.transform;

            // Colonnade Pillars
            GameObject pillarsGroup = new GameObject("ColonnadePillars");
            pillarsGroup.transform.SetParent(monumentRoot.transform, false);
            for (int i = -1; i <= 1; i += 2)
            {
                for (int j = -1; j <= 1; j += 2)
                {
                    GameObject p = GameObject.CreatePrimitive(PrimitiveType.Cylinder);
                    p.transform.SetParent(pillarsGroup.transform, false);
                    p.transform.localScale = new Vector3(0.015f, 0.04f, 0.015f);
                    p.transform.localPosition = new Vector3(i * 0.10f, -0.015f, j * 0.10f);
                }
            }
            colonnadePillars = pillarsGroup.transform;
            rootMonumentModel = monumentRoot.transform;
        }
    }
}

