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
        public string date;
        public float hour;
        public float solar_elevation_deg;
        public float solar_azimuth_deg;
        public float declination_deg;
        public float equation_of_time_min;
        public float hour_angle_deg;
        public float heat_exposure_saved_pct;
        public string heat_estimate_note;
        public string solar_model;
        public string sun_intensity;
        public string shade_recommendation;
        public int active_tourists_total;
    }

    /// <summary>
    /// Polls GET /api/site/telemetry?date=...&hour=... to synchronize the Unity Kiosk
    /// sun arc and courtyard metrics with real backend NOAA solar geometry calculations.
    /// </summary>
    public class KioskNetworkBridge : MonoBehaviour
    {
        [Header("Backend Connection")]
        public string backendBaseUrl = "http://localhost:8000";
        public float pollIntervalSeconds = 2.0f;

        [Header("NOAA Solar Query Parameters")]
        public string queryDate = "2027-01-11";
        [Range(0.0f, 24.0f)]
        public float queryHour = 12.0f;
        public bool sendQueryHour = true;

        [Header("Live Mahabalipuram Telemetry (from Backend NOAA Endpoint)")]
        public bool backendConnected = false;
        public string currentSolarModel = "NOAA General Solar Position Equations";
        public string currentDate = "2027-01-11";
        public float currentSolarElevation = 0.0f;
        public float currentSolarAzimuth = 0.0f;
        public float currentDeclinationDeg = 0.0f;
        public float currentEquationOfTimeMin = 0.0f;
        public float currentHourAngleDeg = 0.0f;
        public float heatExposureSavedPct = 0.0f;
        public string currentSunIntensity = "OFFLINE STANDBY";
        public string shadeRecommendation = "Connect to FastAPI backend on localhost:8000 for live NOAA telemetry";
        public int activeTouristsTotal = 0;
        public int[] activeVisitorCountsPerStop = new int[7];

        private bool requestInFlight = false;
        private float lastManualFetchTime = -10.0f;

        void Start()
        {
            StartCoroutine(PollTelemetryLoop());
        }

        public void SetSolarQuery(string dateStr, float hourVal, bool forceFetchNow = false)
        {
            if (!string.IsNullOrEmpty(dateStr)) queryDate = dateStr.Trim();
            queryHour = Mathf.Clamp(hourVal, 0.0f, 24.0f);
            sendQueryHour = true;

            if (forceFetchNow && !requestInFlight && Time.time - lastManualFetchTime > 0.12f)
            {
                lastManualFetchTime = Time.time;
                StartCoroutine(FetchSiteTelemetry());
            }
        }

        private IEnumerator PollTelemetryLoop()
        {
            while (true)
            {
                if (!requestInFlight)
                {
                    yield return FetchSiteTelemetry();
                }
                yield return new WaitForSeconds(pollIntervalSeconds);
            }
        }

        private IEnumerator FetchSiteTelemetry()
        {
            requestInFlight = true;
            string dateParam = UnityWebRequest.EscapeURL(string.IsNullOrEmpty(queryDate) ? "2027-01-11" : queryDate);
            string hourParam = sendQueryHour ? $"&hour={queryHour:F2}" : "";
            string url = $"{backendBaseUrl}/api/site/telemetry?start_id=1&target_id=7&date={dateParam}{hourParam}";

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
                            currentDate = string.IsNullOrEmpty(data.date) ? queryDate : data.date;
                            currentSolarElevation = data.solar_elevation_deg;
                            currentSolarAzimuth = data.solar_azimuth_deg;
                            currentDeclinationDeg = data.declination_deg;
                            currentEquationOfTimeMin = data.equation_of_time_min;
                            currentHourAngleDeg = data.hour_angle_deg;
                            heatExposureSavedPct = data.heat_exposure_saved_pct;
                            currentSolarModel = string.IsNullOrEmpty(data.solar_model) ? "NOAA General Solar Position Equations" : data.solar_model;
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
            requestInFlight = false;
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
