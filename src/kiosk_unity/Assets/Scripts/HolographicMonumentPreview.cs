using System.Collections.Generic;
using UnityEngine;

namespace LunarAurora.Kiosk
{
    public enum HeritageExhibitType
    {
        SolsticeSunTemple = 0,
        AiravataSculpture = 1,
        LotusGnomonSanctuary = 2
    }

    /// <summary>
    /// High-detail multi-exhibit 3D Holographic Showcase for Mahabalipuram on the Sony ELF-SR1 (15.6").
    /// Renders courtyard shade heatmap indicators, live visitor crowd pins synced from telemetry,
    /// exploded architectural layers, and real-time solstice sun sweeps.
    /// </summary>
    public class HolographicMonumentPreview : MonoBehaviour
    {
        [Header("Exhibit Control")]
        public HeritageExhibitType activeExhibit = HeritageExhibitType.SolsticeSunTemple;
        public bool autoRotate = true;
        public float rotationSpeed = 14.0f;

        [Header("Exploded Architectural Layer Mode")]
        public bool isExploded = false;
        public float animationSpeed = 3.5f;

        [Header("Solstice Sunlight & Shade Simulation")]
        public Light directionalSunLight;
        [Range(6.0f, 18.0f)]
        public float simulatedHour = 13.0f;
        public bool animateSunCycle = true;
        public KioskNetworkBridge telemetryBridge;

        private Transform exhibitContainer;
        private GameObject[] exhibitRoots = new GameObject[3];

        private Transform templeSpireGroup;
        private Transform templePillarsGroup;
        private Transform templeCoreOrb;
        private List<Transform> chariotWheels = new List<Transform>();

        private Transform[] visitorPins = new Transform[7];
        private List<Renderer> shadeHeatmapTiles = new List<Renderer>();

        private Vector3 spireBaseLocalPos;
        private float currentYaw = 25f;
        private float currentPitch = 8f;
        private bool isDragging = false;
        private Vector3 lastMousePos;

        private Material sandstoneMat;
        private Material darkGraniteMat;
        private Material goldAccentMat;
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

            BuildSunTempleExhibit();
            BuildAiravataExhibit();
            BuildLotusGnomonExhibit();
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

            foreach (var wheel in chariotWheels)
            {
                if (wheel != null) wheel.Rotate(Vector3.right, 12f * Time.deltaTime, Space.Self);
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
                case HeritageExhibitType.SolsticeSunTemple: return "Shore Temple Vimana (700 CE Pallava)";
                case HeritageExhibitType.AiravataSculpture: return "Monolithic Roaring Yali Relief (705 CE)";
                case HeritageExhibitType.LotusGnomonSanctuary: return "Solar Chariot Wheel & Lotus Cistern";
                default: return "Mahabalipuram Showcase";
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
                Vector3 target = isExploded ? spireBaseLocalPos + Vector3.up * 0.065f : spireBaseLocalPos;
                templeSpireGroup.localPosition = Vector3.Lerp(templeSpireGroup.localPosition, target, Time.deltaTime * animationSpeed);
            }
            if (templePillarsGroup != null)
            {
                float targetScale = isExploded ? 1.25f : 1.0f;
                float s = Mathf.Lerp(templePillarsGroup.localScale.x, targetScale, Time.deltaTime * animationSpeed);
                templePillarsGroup.localScale = new Vector3(s, 1f, s);
            }
            if (templeCoreOrb != null)
            {
                templeCoreOrb.gameObject.SetActive(isExploded);
                templeCoreOrb.Rotate(Vector3.up, 60f * Time.deltaTime);
            }
        }

        void UpdateSunLightAngle()
        {
            float progress = (simulatedHour - 6.0f) / 12.0f;
            float elev = Mathf.Sin(progress * Mathf.PI) * 75.0f + 10.0f;
            float azim = -80.0f + progress * 160.0f;
            directionalSunLight.transform.rotation = Quaternion.Euler(elev, azim, 0f);
        }

        void UpdateTelemetryVisuals()
        {
            float noonIntensity = Mathf.Clamp01(Mathf.Sin(((simulatedHour - 6.0f) / 12.0f) * Mathf.PI));
            for (int i = 0; i < shadeHeatmapTiles.Count; i++)
            {
                if (shadeHeatmapTiles[i] == null) continue;
                bool isCoolZone = (i % 2 == 0);
                shadeHeatmapTiles[i].material.color = isCoolZone
                    ? Color.Lerp(new Color(0f, 0.6f, 0.35f, 0.55f), new Color(0f, 0.95f, 0.45f, 0.85f), noonIntensity)
                    : Color.Lerp(new Color(0.95f, 0.65f, 0.1f, 0.45f), new Color(1f, 0.25f, 0.15f, 0.78f), noonIntensity);
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
            Shader std = Shader.Find("Standard");
            sandstoneMat = new Material(std) { color = new Color(0.76f, 0.62f, 0.44f) };
            darkGraniteMat = new Material(std) { color = new Color(0.24f, 0.22f, 0.25f) };
            goldAccentMat = new Material(std) { color = new Color(0.95f, 0.76f, 0.18f) };
            goldAccentMat.SetFloat("_Metallic", 0.78f);
            goldAccentMat.SetFloat("_Glossiness", 0.68f);

            glowingCyanMat = new Material(std) { color = new Color(0.0f, 0.90f, 1.0f) };
            glowingCyanMat.EnableKeyword("_EMISSION");
            glowingCyanMat.SetColor("_EmissionColor", new Color(0.0f, 0.75f, 1.0f) * 1.4f);

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
            obj.GetComponent<Renderer>().material = mat;
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
                rend.material = new Material(i % 2 == 0 ? shadeEmeraldMat : sunHeatMat);
                shadeHeatmapTiles.Add(rend);
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
                pin.GetComponent<Renderer>().material = glowingCyanMat;
                visitorPins[i] = pin.transform;
            }
        }

        void BuildSunTempleExhibit()
        {
            GameObject root = new GameObject("Exhibit_SolsticeSunTemple");
            root.transform.SetParent(exhibitContainer, false);
            exhibitRoots[0] = root;

            CreatePart(PrimitiveType.Cube, root.transform, "JagatiTier1", new Vector3(0, -0.055f, 0), new Vector3(0.22f, 0.012f, 0.22f), darkGraniteMat);
            CreatePart(PrimitiveType.Cube, root.transform, "JagatiTier2", new Vector3(0, -0.043f, 0), new Vector3(0.19f, 0.012f, 0.19f), sandstoneMat);
            CreatePart(PrimitiveType.Cube, root.transform, "JagatiTier3", new Vector3(0, -0.031f, 0), new Vector3(0.16f, 0.010f, 0.16f), darkGraniteMat);
            CreatePart(PrimitiveType.Cube, root.transform, "SanctumBase", new Vector3(0, -0.004f, 0), new Vector3(0.105f, 0.044f, 0.105f), sandstoneMat);

            GameObject orb = GameObject.CreatePrimitive(PrimitiveType.Cube);
            orb.name = "EquinoxLightCore";
            orb.transform.SetParent(root.transform, false);
            orb.transform.localPosition = new Vector3(0, 0.015f, 0);
            orb.transform.localRotation = Quaternion.Euler(45f, 45f, 45f);
            orb.transform.localScale = new Vector3(0.024f, 0.024f, 0.024f);
            orb.GetComponent<Renderer>().material = glowingCyanMat;
            orb.SetActive(false);
            templeCoreOrb = orb.transform;

            GameObject spireObj = new GameObject("VimanaSpireGroup");
            spireObj.transform.SetParent(root.transform, false);
            spireObj.transform.localPosition = Vector3.zero;
            templeSpireGroup = spireObj.transform;
            spireBaseLocalPos = Vector3.zero;

            float[] widths = { 0.095f, 0.080f, 0.065f, 0.050f, 0.036f };
            for (int i = 0; i < widths.Length; i++)
            {
                CreatePart(
                    PrimitiveType.Cube, spireObj.transform, $"SpireTier_{i}",
                    new Vector3(0, 0.025f + i * 0.014f, 0),
                    new Vector3(widths[i], 0.013f, widths[i]),
                    i % 2 == 0 ? sandstoneMat : darkGraniteMat
                );
            }
            CreatePart(PrimitiveType.Cylinder, spireObj.transform, "AmalakaDisc", new Vector3(0, 0.096f, 0), new Vector3(0.038f, 0.004f, 0.038f), goldAccentMat);
            CreatePart(PrimitiveType.Sphere, spireObj.transform, "KalashaFinial", new Vector3(0, 0.108f, 0), new Vector3(0.014f, 0.020f, 0.014f), goldAccentMat);

            GameObject pillarsObj = new GameObject("ColonnadePillarsGroup");
            pillarsObj.transform.SetParent(root.transform, false);
            templePillarsGroup = pillarsObj.transform;

            for (int i = -1; i <= 1; i++)
            {
                for (int j = -1; j <= 1; j++)
                {
                    if (i == 0 && j == 0) continue;
                    CreatePart(PrimitiveType.Cylinder, pillarsObj.transform, $"Pillar_{i}_{j}",
                        new Vector3(i * 0.068f, -0.005f, j * 0.068f),
                        new Vector3(0.011f, 0.022f, 0.011f), sandstoneMat);
                }
            }

            for (int side = -1; side <= 1; side += 2)
            {
                GameObject wheelRoot = new GameObject($"SolarChariotWheel_{side}");
                wheelRoot.transform.SetParent(root.transform, false);
                wheelRoot.transform.localPosition = new Vector3(side * 0.088f, -0.026f, 0f);
                CreatePart(PrimitiveType.Cylinder, wheelRoot.transform, "WheelRim", Vector3.zero, new Vector3(0.042f, 0.004f, 0.042f), goldAccentMat, new Vector3(0, 0, 90));
                CreatePart(PrimitiveType.Sphere, wheelRoot.transform, "AxleHub", Vector3.zero, new Vector3(0.012f, 0.012f, 0.012f), darkGraniteMat);
                chariotWheels.Add(wheelRoot.transform);
            }
        }

        void BuildAiravataExhibit()
        {
            GameObject root = new GameObject("Exhibit_AiravataSculpture");
            root.transform.SetParent(exhibitContainer, false);
            exhibitRoots[1] = root;

            CreatePart(PrimitiveType.Cube, root.transform, "SculpturePlinth", new Vector3(0, -0.048f, 0), new Vector3(0.18f, 0.018f, 0.14f), darkGraniteMat);
            CreatePart(PrimitiveType.Cube, root.transform, "LotusTrim", new Vector3(0, -0.036f, 0), new Vector3(0.16f, 0.008f, 0.12f), goldAccentMat);
            CreatePart(PrimitiveType.Sphere, root.transform, "Torso", new Vector3(0, 0.012f, 0), new Vector3(0.085f, 0.068f, 0.115f), sandstoneMat);
            CreatePart(PrimitiveType.Sphere, root.transform, "Head", new Vector3(0, 0.028f, 0.062f), new Vector3(0.058f, 0.056f, 0.058f), sandstoneMat);
            CreatePart(PrimitiveType.Cylinder, root.transform, "RoyalCrown", new Vector3(0, 0.062f, 0.060f), new Vector3(0.028f, 0.012f, 0.028f), goldAccentMat);
            CreatePart(PrimitiveType.Cube, root.transform, "Caparison", new Vector3(0, 0.028f, -0.005f), new Vector3(0.088f, 0.025f, 0.055f), goldAccentMat);
            CreatePart(PrimitiveType.Cube, root.transform, "EarL", new Vector3(-0.036f, 0.032f, 0.050f), new Vector3(0.008f, 0.038f, 0.028f), sandstoneMat, new Vector3(0, -20, 0));
            CreatePart(PrimitiveType.Cube, root.transform, "EarR", new Vector3(0.036f, 0.032f, 0.050f), new Vector3(0.008f, 0.038f, 0.028f), sandstoneMat, new Vector3(0, 20, 0));
            CreatePart(PrimitiveType.Cylinder, root.transform, "TuskL", new Vector3(-0.018f, 0.014f, 0.095f), new Vector3(0.007f, 0.020f, 0.007f), goldAccentMat, new Vector3(65, 0, 0));
            CreatePart(PrimitiveType.Cylinder, root.transform, "TuskR", new Vector3(0.018f, 0.014f, 0.095f), new Vector3(0.007f, 0.020f, 0.007f), goldAccentMat, new Vector3(65, 0, 0));
            CreatePart(PrimitiveType.Cylinder, root.transform, "TrunkUpper", new Vector3(0, 0.002f, 0.092f), new Vector3(0.015f, 0.022f, 0.015f), sandstoneMat, new Vector3(15, 0, 0));
            CreatePart(PrimitiveType.Sphere, root.transform, "LotusBud", new Vector3(0, -0.018f, 0.105f), new Vector3(0.018f, 0.018f, 0.018f), glowingCyanMat);

            CreatePart(PrimitiveType.Cylinder, root.transform, "LegFL", new Vector3(-0.024f, -0.018f, 0.032f), new Vector3(0.022f, 0.020f, 0.022f), sandstoneMat);
            CreatePart(PrimitiveType.Cylinder, root.transform, "LegFR", new Vector3(0.024f, -0.018f, 0.032f), new Vector3(0.022f, 0.020f, 0.022f), sandstoneMat);
            CreatePart(PrimitiveType.Cylinder, root.transform, "LegBL", new Vector3(-0.024f, -0.018f, -0.035f), new Vector3(0.022f, 0.020f, 0.022f), sandstoneMat);
            CreatePart(PrimitiveType.Cylinder, root.transform, "LegBR", new Vector3(0.024f, -0.018f, -0.035f), new Vector3(0.022f, 0.020f, 0.022f), sandstoneMat);
        }

        void BuildLotusGnomonExhibit()
        {
            GameObject root = new GameObject("Exhibit_LotusGnomon");
            root.transform.SetParent(exhibitContainer, false);
            exhibitRoots[2] = root;

            CreatePart(PrimitiveType.Cylinder, root.transform, "OuterBasin", new Vector3(0, -0.045f, 0), new Vector3(0.20f, 0.012f, 0.20f), darkGraniteMat);
            CreatePart(PrimitiveType.Cylinder, root.transform, "CoolingWater", new Vector3(0, -0.032f, 0), new Vector3(0.175f, 0.004f, 0.175f), glowingCyanMat);

            for (int i = 0; i < 8; i++)
            {
                float ang = i * 45f * Mathf.Deg2Rad;
                Vector3 pos = new Vector3(Mathf.Cos(ang) * 0.055f, -0.022f, Mathf.Sin(ang) * 0.055f);
                CreatePart(PrimitiveType.Cube, root.transform, $"LotusPetal_{i}", pos, new Vector3(0.032f, 0.010f, 0.020f), sandstoneMat, new Vector3(0, -i * 45f, 20));
            }

            CreatePart(PrimitiveType.Cylinder, root.transform, "ChronoPillar", new Vector3(0, 0.035f, 0), new Vector3(0.024f, 0.068f, 0.024f), sandstoneMat);
            CreatePart(PrimitiveType.Cube, root.transform, "BrassMeridianLine", new Vector3(0, -0.028f, 0), new Vector3(0.004f, 0.003f, 0.17f), goldAccentMat);
            CreatePart(PrimitiveType.Sphere, root.transform, "SolarApex", new Vector3(0, 0.106f, 0), new Vector3(0.022f, 0.022f, 0.022f), goldAccentMat);
        }
    }
}
