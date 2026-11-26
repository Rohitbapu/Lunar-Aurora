using System;
using System.Collections;
using System.Text.RegularExpressions;
using UnityEngine;
using UnityEngine.Networking;

namespace LunarAurora.Kiosk
{
    [Serializable]
    public class TelemetryResponse
    {
        public float solar_elevation_deg;
        public float solar_azimuth_deg;
        public float heat_exposure_saved_pct;
        public string sun_intensity;
        public string shade_recommendation;
        public int active_tourists_total;
    }

    /// <summary>
    /// Polls GET /api/site/telemetry every 2 seconds to synchronize the Sony ELF-SR1
    /// 3D showcase with real-time Mahabalipuram solar elevation, shade savings, and active visitor crowd counts.
    /// </summary>
    public class KioskNetworkBridge : MonoBehaviour
    {
        [Header("Backend Connection")]
        public string backendBaseUrl = "http://localhost:8000";
        public float pollIntervalSeconds = 2.0f;

        [Header("Live Mahabalipuram Telemetry")]
        public bool backendConnected = false;
        public float currentSolarElevation = 58.0f;
        public float currentSolarAzimuth = 145.0f;
        public float heatExposureSavedPct = 76.0f;
        public string currentSunIntensity = "HIGH (Peak Midday)";
        public string shadeRecommendation = "Use Shaded Colonnade & Banyan Canopy";
        public int activeTouristsTotal = 0;
        public int[] activeVisitorCountsPerStop = new int[7];

        void Start()
        {
            StartCoroutine(PollTelemetryLoop());
        }

        private IEnumerator PollTelemetryLoop()
        {
            while (true)
            {
                yield return FetchSiteTelemetry();
                yield return new WaitForSeconds(pollIntervalSeconds);
            }
        }

        private IEnumerator FetchSiteTelemetry()
        {
            string url = $"{backendBaseUrl}/api/site/telemetry?start_id=1&target_id=7";
            using (UnityWebRequest req = UnityWebRequest.Get(url))
            {
                req.timeout = 2;
                yield return req.SendWebRequest();

                if (req.result == UnityWebRequest.Result.Success)
                {
                    try
                    {
                        string rawJson = req.downloadHandler.text;
                        TelemetryResponse data = JsonUtility.FromJson<TelemetryResponse>(rawJson);
                        if (data != null)
                        {
                            backendConnected = true;
                            currentSolarElevation = data.solar_elevation_deg;
                            currentSolarAzimuth = data.solar_azimuth_deg;
                            heatExposureSavedPct = data.heat_exposure_saved_pct;
                            currentSunIntensity = data.sun_intensity;
                            shadeRecommendation = data.shade_recommendation;
                            activeTouristsTotal = data.active_tourists_total;
                            ParseStopCounts(rawJson);
                        }
                    }
                    catch (Exception ex)
                    {
                        Debug.LogWarning($"[KioskNetworkBridge] Telemetry parse error: {ex.Message}");
                    }
                }
                else
                {
                    backendConnected = false;
                }
            }
        }

        private void ParseStopCounts(string json)
        {
            for (int i = 0; i < 7; i++) activeVisitorCountsPerStop[i] = 0;
            Match blockMatch = Regex.Match(json, "\"active_visitor_nodes\"\\s*:\\s*\\{([^}]*)\\}");
            if (!blockMatch.Success) return;

            string inner = blockMatch.Groups[1].Value;
            foreach (Match m in Regex.Matches(inner, "\"(\\d+)\"\\s*:\\s*(\\d+)"))
            {
                if (int.TryParse(m.Groups[1].Value, out int stopIdx) && int.TryParse(m.Groups[2].Value, out int count))
                {
                    if (stopIdx >= 1 && stopIdx <= 7)
                    {
                        activeVisitorCountsPerStop[stopIdx - 1] = count;
                    }
                }
            }
        }
    }
}
