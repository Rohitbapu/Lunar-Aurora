using System.Collections.Generic;
using UnityEngine;

namespace LunarAurora.Kiosk
{
    public enum HeritageExhibitType
    {
        ShoreTemple = 0,
        PanchaRathas = 1,
        KrishnasButterball = 2
    }

    /// <summary>
    /// Procedural illustrative 3D placeholders scaled for the Kiosk viewport.
    /// Explicitly labeled "Illustrative model" — NOT archaeological scans.
    /// Aligned to the UNESCO Mahabalipuram set (Shore Temple, Pancha Rathas, Krishna's Butterball).
    /// </summary>
    public class HolographicMonumentPreview : MonoBehaviour
    {
        [Header("Exhibit Control")]
        public HeritageExhibitType activeExhibit = HeritageExhibitType.ShoreTemple;
        public bool autoRotate = true;
        public float rotationSpeed = 14.0f;

        [Header("Exploded Layer Inspection")]
        public bool isExploded = false;
        public float animationSpeed = 3.5f;

        [Header("Directional Light & NOAA Telemetry")]
        public Light directionalSunLight;
        public string simulatedDate = "2027-01-11";
        [Range(6.0f, 18.0f)]
        public float simulatedHour = 12.0f;
        public bool animateSunCycle = true;
        public KioskNetworkBridge telemetryBridge;
        private float lastBridgePushHour = -1.0f;

        private Transform exhibitContainer;
        private GameObject[] exhibitRoots = new GameObject[3];

        private Transform templeSpireGroup;
        private Transform templePillarsGroup;
        private Vector3 spireBaseLocalPos;

        private Transform[] visitorPins = new Transform[7];
        private List<Renderer> shadeHeatmapTiles = new List<Renderer>();

        private float currentYaw = 25f;
        private float currentPitch = 8f;
        private bool isDragging = false;
        private Vector3 lastMousePos;

        private Material sandstoneMat;
        private Material darkGraniteMat;
        private Material accentGoldMat;
        private Material glowingCyanMat;
        private Material shadeEmeraldMat;
        private Material sunHeatMat;

        void Start()
        {
            CreateMaterials();

            GameObject containerObj = new GameObject("ExhibitTurntableRoot");
            containerObj.transform.SetParent(this.transform, false);
            containerObj.transform.localPosition = new Vector3(-0.02f, -0.02f, 0f);
            exhibitContainer = containerObj.transform;

            BuildShoreTempleIllustrative();
            BuildPanchaRathasIllustrative();
            BuildButterballIllustrative();
            BuildCourtyardShadeHeatmap();
            BuildLiveCrowdTelemetryPins();

            SelectExhibit(activeExhibit);
        }

        void Update()
        {
            HandleManualInspection();

            if (autoRotate && !isDragging && exhibitContainer != null)
            {
                currentYaw += rotationSpeed * Time.deltaTime;
            }
            if (exhibitContainer != null)
            {
                exhibitContainer.localRotation = Quaternion.Euler(currentPitch, currentYaw, 0f);
            }

            HandleExplodedView();
            UpdateTelemetryVisuals();

            if (directionalSunLight != null)
            {
                if (animateSunCycle)
                {
                    simulatedHour += Time.deltaTime * 0.45f;
                    if (simulatedHour > 18.0f) simulatedHour = 6.0f;
                }
                if (telemetryBridge != null && Mathf.Abs(simulatedHour - lastBridgePushHour) >= 0.25f)
                {
                    lastBridgePushHour = simulatedHour;
                    telemetryBridge.SetSolarQuery(simulatedDate, simulatedHour, true);
                }
                UpdateSunLightAngle();
            }
        }

        public void SelectExhibit(HeritageExhibitType exhibit)
        {
            activeExhibit = exhibit;
            for (int i = 0; i < exhibitRoots.Length; i++)
            {
                if (exhibitRoots[i] != null) exhibitRoots[i].SetActive(i == (int)exhibit);
            }
        }

        public string GetActiveExhibitTitle()
        {
            switch (activeExhibit)
            {
                case HeritageExhibitType.ShoreTemple: return "Illustrative model: Shore Temple (procedural)";
                case HeritageExhibitType.PanchaRathas: return "Illustrative model: Pancha Rathas (procedural)";
                case HeritageExhibitType.KrishnasButterball: return "Illustrative model: Krishna's Butterball (procedural)";
                default: return "Illustrative model";
            }
        }

        public void ToggleExplodedView() => isExploded = !isExploded;

        void HandleManualInspection()
        {
            if (Input.GetMouseButtonDown(0))
            {
                if (Input.mousePosition.x > 460 || Input.mousePosition.y < Screen.height - 340)
                {
                    isDragging = true;
                    lastMousePos = Input.mousePosition;
                }
            }
            else if (Input.GetMouseButtonUp(0)) isDragging = false;

            if (isDragging && Input.GetMouseButton(0))
            {
                Vector3 delta = Input.mousePosition - lastMousePos;
                lastMousePos = Input.mousePosition;
                currentYaw -= delta.x * 0.35f;
                currentPitch = Mathf.Clamp(currentPitch + delta.y * 0.25f, -20f, 35f);
            }

            float scroll = Input.GetAxis("Mouse ScrollWheel");
            if (Mathf.Abs(scroll) > 0.001f && exhibitContainer != null)
            {
                float s = Mathf.Clamp(exhibitContainer.localScale.x + scroll * 0.25f, 0.7f, 1.35f);
                exhibitContainer.localScale = new Vector3(s, s, s);
            }
        }

        void HandleExplodedView()
        {
            if (templeSpireGroup != null)
            {
                Vector3 target = isExploded ? spireBaseLocalPos + Vector3.up * 0.055f : spireBaseLocalPos;
                templeSpireGroup.localPosition = Vector3.Lerp(templeSpireGroup.localPosition, target, Time.deltaTime * animationSpeed);
            }
            if (templePillarsGroup != null)
            {
                float targetScale = isExploded ? 1.22f : 1.0f;
                float s = Mathf.Lerp(templePillarsGroup.localScale.x, targetScale, Time.deltaTime * animationSpeed);
                templePillarsGroup.localScale = new Vector3(s, 1f, s);
            }
        }

        void UpdateSunLightAngle()
        {
            if (telemetryBridge != null && telemetryBridge.backendConnected)
            {
                float elevDeg = telemetryBridge.currentSolarElevation;
                float azimDeg = telemetryBridge.currentSolarAzimuth;
                float elRad = elevDeg * Mathf.Deg2Rad;
                float azRad = azimDeg * Mathf.Deg2Rad;

                // World coords: +X East, +Y Up, +Z North (azimuth clockwise from North)
                Vector3 sunDir = new Vector3(
                    Mathf.Cos(elRad) * Mathf.Sin(azRad),
                    Mathf.Sin(elRad),
                    Mathf.Cos(elRad) * Mathf.Cos(azRad)
                );
                if (elevDeg <= 0.1f)
                {
                    directionalSunLight.intensity = 0.08f;
                }
                else
                {
                    directionalSunLight.intensity = Mathf.Lerp(0.45f, 1.55f, Mathf.Clamp01(elevDeg / 65.0f));
                    directionalSunLight.transform.rotation = Quaternion.LookRotation(-sunDir.normalized, Vector3.up);
                }
                return;
            }

            // Offline standby: neutral fixed key lighting until backend NOAA endpoint is reachable
            directionalSunLight.intensity = 1.15f;
            directionalSunLight.transform.rotation = Quaternion.Euler(50f, -30f, 0f);
        }

        void UpdateTelemetryVisuals()
        {
            float heatNorm = (telemetryBridge != null && telemetryBridge.backendConnected)
                ? Mathf.Clamp01(telemetryBridge.currentSolarElevation / 65.0f)
                : 0.35f;
            for (int i = 0; i < shadeHeatmapTiles.Count; i++)
            {
                if (shadeHeatmapTiles[i] == null) continue;
                bool isCoolZone = (i % 2 == 0);
                shadeHeatmapTiles[i].material.color = isCoolZone
                    ? Color.Lerp(new Color(0f, 0.6f, 0.35f, 0.55f), new Color(0f, 0.95f, 0.45f, 0.85f), heatNorm)
                    : Color.Lerp(new Color(0.95f, 0.65f, 0.1f, 0.45f), new Color(1f, 0.25f, 0.15f, 0.78f), heatNorm);
            }

            if (telemetryBridge != null)
            {
                for (int i = 0; i < 7; i++)
                {
                    if (visitorPins[i] == null) continue;
                    int count = telemetryBridge.activeVisitorCountsPerStop[i];
                    float bob = Mathf.Sin(Time.time * 3.0f + i) * 0.0025f;
                    float scale = count > 0 ? Mathf.Clamp(1.0f + count * 0.35f, 1.0f, 2.2f) : 0.65f;
                    visitorPins[i].localScale = new Vector3(0.006f * scale, 0.012f * scale, 0.006f * scale);
                    Vector3 p = visitorPins[i].localPosition;
                    visitorPins[i].localPosition = new Vector3(p.x, -0.025f + bob, p.z);
                }
            }
        }

        void CreateMaterials()
        {
            Shader std = Shader.Find("Standard")
                ?? Shader.Find("Unlit/Color")
                ?? Resources.GetBuiltinResource<Material>("Default-Material.mat")?.shader;
            if (std == null)
            {
                GameObject tmp = GameObject.CreatePrimitive(PrimitiveType.Cube);
                std = tmp.GetComponent<Renderer>()?.sharedMaterial?.shader;
                Destroy(tmp);
            }
            if (std == null) return;

            sandstoneMat = new Material(std) { color = new Color(0.76f, 0.64f, 0.48f) };
            darkGraniteMat = new Material(std) { color = new Color(0.28f, 0.26f, 0.29f) };
            accentGoldMat = new Material(std) { color = new Color(0.85f, 0.68f, 0.28f) };
            glowingCyanMat = new Material(std) { color = new Color(0.0f, 0.90f, 1.0f) };
            if (glowingCyanMat.HasProperty("_EmissionColor"))
            {
                glowingCyanMat.EnableKeyword("_EMISSION");
                glowingCyanMat.SetColor("_EmissionColor", new Color(0.0f, 0.75f, 1.0f) * 1.4f);
            }

            shadeEmeraldMat = new Material(std) { color = new Color(0.0f, 0.9f, 0.45f) };
            sunHeatMat = new Material(std) { color = new Color(1.0f, 0.35f, 0.20f) };
        }

        void CreatePart(PrimitiveType type, Transform parent, string name, Vector3 pos, Vector3 scale, Material mat, Vector3 euler = default)
        {
            GameObject obj = GameObject.CreatePrimitive(type);
            obj.name = name;
            obj.transform.SetParent(parent, false);
            obj.transform.localPosition = pos;
            obj.transform.localScale = scale;
            if (euler != default) obj.transform.localRotation = Quaternion.Euler(euler);
            Renderer rend = obj.GetComponent<Renderer>();
            if (rend != null && mat != null) rend.material = mat;
        }

        void BuildCourtyardShadeHeatmap()
        {
            GameObject hmRoot = new GameObject("CourtyardShadeHeatmap");
            hmRoot.transform.SetParent(exhibitContainer, false);
            Vector3[] offsets = {
                new Vector3(-0.08f, -0.056f, 0.08f),
                new Vector3(0.08f, -0.056f, 0.08f),
                new Vector3(-0.08f, -0.056f, -0.08f),
                new Vector3(0.08f, -0.056f, -0.08f)
            };
            for (int i = 0; i < offsets.Length; i++)
            {
                GameObject tile = GameObject.CreatePrimitive(PrimitiveType.Cylinder);
                tile.name = $"HeatmapZone_{i}";
                tile.transform.SetParent(hmRoot.transform, false);
                tile.transform.localPosition = offsets[i];
                tile.transform.localScale = new Vector3(0.042f, 0.002f, 0.042f);
                var rend = tile.GetComponent<Renderer>();
                if (rend != null && shadeEmeraldMat != null && sunHeatMat != null)
                {
                    rend.material = new Material(i % 2 == 0 ? shadeEmeraldMat : sunHeatMat);
                    shadeHeatmapTiles.Add(rend);
                }
            }
        }

        void BuildLiveCrowdTelemetryPins()
        {
            GameObject pinsRoot = new GameObject("LiveCrowdTelemetryPins");
            pinsRoot.transform.SetParent(exhibitContainer, false);
            Vector3[] stopCoords = {
                new Vector3(0.00f, -0.025f, -0.09f),
                new Vector3(0.04f, -0.025f, -0.05f),
                new Vector3(0.09f, -0.025f, 0.01f),
                new Vector3(0.02f, -0.025f, 0.03f),
                new Vector3(-0.05f, -0.025f, 0.05f),
                new Vector3(-0.08f, -0.025f, -0.02f),
                new Vector3(0.07f, -0.025f, 0.08f)
            };
            for (int i = 0; i < 7; i++)
            {
                GameObject pin = GameObject.CreatePrimitive(PrimitiveType.Capsule);
                pin.name = $"VisitorPin_Stop{i + 1}";
                pin.transform.SetParent(pinsRoot.transform, false);
                pin.transform.localPosition = stopCoords[i];
                pin.transform.localScale = new Vector3(0.005f, 0.010f, 0.005f);
                var pinRend = pin.GetComponent<Renderer>();
                if (pinRend != null && glowingCyanMat != null) pinRend.material = glowingCyanMat;
                visitorPins[i] = pin.transform;
            }
        }

        void BuildShoreTempleIllustrative()
        {
            GameObject root = new GameObject("Illustrative_ShoreTemple");
            root.transform.SetParent(exhibitContainer, false);
            exhibitRoots[0] = root;

            CreatePart(PrimitiveType.Cube, root.transform, "GranitePlinth1", new Vector3(0, -0.052f, 0), new Vector3(0.22f, 0.012f, 0.16f), darkGraniteMat);
            CreatePart(PrimitiveType.Cube, root.transform, "SanctumBody", new Vector3(0.01f, -0.01f, 0), new Vector3(0.095f, 0.042f, 0.095f), sandstoneMat);

            GameObject spireObj = new GameObject("StructuralSpirePlaceholder");
            spireObj.transform.SetParent(root.transform, false);
            templeSpireGroup = spireObj.transform;
            spireBaseLocalPos = Vector3.zero;

            float[] widths = { 0.086f, 0.070f, 0.056f, 0.042f, 0.030f };
            for (int i = 0; i < widths.Length; i++)
            {
                CreatePart(
                    PrimitiveType.Cube, spireObj.transform, $"Tier_{i}",
                    new Vector3(0.01f, 0.020f + i * 0.014f, 0),
                    new Vector3(widths[i], 0.013f, widths[i]),
                    i % 2 == 0 ? sandstoneMat : darkGraniteMat
                );
            }
            // Secondary smaller western shrine silhouette
            CreatePart(PrimitiveType.Cube, spireObj.transform, "SmallShrineTier1", new Vector3(-0.068f, 0.005f, 0), new Vector3(0.048f, 0.032f, 0.048f), sandstoneMat);
            CreatePart(PrimitiveType.Cube, spireObj.transform, "SmallShrineTier2", new Vector3(-0.068f, 0.030f, 0), new Vector3(0.032f, 0.018f, 0.032f), darkGraniteMat);
            CreatePart(PrimitiveType.Sphere, spireObj.transform, "Finial", new Vector3(0.01f, 0.092f, 0), new Vector3(0.012f, 0.016f, 0.012f), accentGoldMat);

            GameObject pillarsObj = new GameObject("BoundaryEnclosurePlaceholder");
            pillarsObj.transform.SetParent(root.transform, false);
            templePillarsGroup = pillarsObj.transform;
            for (int i = -1; i <= 1; i++)
            {
                for (int j = -1; j <= 1; j++)
                {
                    if (i == 0 && j == 0) continue;
                    CreatePart(PrimitiveType.Cylinder, pillarsObj.transform, $"WallPost_{i}_{j}",
                        new Vector3(i * 0.078f, -0.025f, j * 0.058f),
                        new Vector3(0.009f, 0.018f, 0.009f), sandstoneMat);
                }
            }
        }

        void BuildPanchaRathasIllustrative()
        {
            GameObject root = new GameObject("Illustrative_PanchaRathas");
            root.transform.SetParent(exhibitContainer, false);
            exhibitRoots[1] = root;

            // Sloping granite bedrock ridge placeholder
            CreatePart(PrimitiveType.Cube, root.transform, "MonolithRidge", new Vector3(0, -0.046f, 0), new Vector3(0.24f, 0.014f, 0.14f), darkGraniteMat, new Vector3(0, 0, 2f));

            // 3 stepped chariot-shaped monolith silhouettes
            float[] xs = { -0.07f, 0.0f, 0.07f };
            float[] hs = { 0.048f, 0.072f, 0.060f };
            for (int i = 0; i < 3; i++)
            {
                CreatePart(PrimitiveType.Cube, root.transform, $"RathaBase_{i}", new Vector3(xs[i], -0.020f, 0), new Vector3(0.048f, hs[i] * 0.5f, 0.056f), sandstoneMat);
                CreatePart(PrimitiveType.Cube, root.transform, $"RathaRoof_{i}", new Vector3(xs[i], 0.010f + i * 0.004f, 0), new Vector3(0.036f, hs[i] * 0.35f, 0.042f), i == 1 ? accentGoldMat : darkGraniteMat);
            }
        }

        void BuildButterballIllustrative()
        {
            GameObject root = new GameObject("Illustrative_KrishnasButterball");
            root.transform.SetParent(exhibitContainer, false);
            exhibitRoots[2] = root;

            // Sloped hillock granite slab + oversized balanced sphere silhouette
            CreatePart(PrimitiveType.Cube, root.transform, "SlopedHillock", new Vector3(0, -0.042f, 0), new Vector3(0.21f, 0.018f, 0.15f), darkGraniteMat, new Vector3(0, 0, -10f));
            CreatePart(PrimitiveType.Sphere, root.transform, "BalancedGraniteBoulder", new Vector3(-0.005f, 0.018f, 0), new Vector3(0.095f, 0.088f, 0.090f), sandstoneMat);
        }
    }
}
