using System;
using System.Collections;
using UnityEngine;
using UnityEngine.Networking;

namespace LunarAurora.Kiosk
{
    [Serializable]
    public class SolarStatusResponse
    {
        public float solar_elevation_deg;
        public float solar_azimuth_deg;
        public string sun_intensity;
        public string shade_recommendation;
    }

    /// <summary>
    /// Synchronizes the Sony Kiosk with the FastAPI backend.
    /// Pulls live sun status, shade metrics, and site overview.
    /// </summary>
    public class KioskNetworkBridge : MonoBehaviour
    {
        [Header("Backend Connection")]
        public string backendBaseUrl = "http://localhost:8000";
        public float pollIntervalSeconds = 15.0f;

        [Header("Live Site Metrics")]
        public float currentSolarElevation = 45.0f;
        public string currentSunIntensity = "MODERATE";
        public string shadeRecommendation = "Comfortable walking conditions";

        void Start()
        {
            StartCoroutine(PollSiteStatusLoop());
        }

        private IEnumerator PollSiteStatusLoop()
        {
            while (true)
            {
                yield return FetchSolarStatus();
                yield return new WaitForSeconds(pollIntervalSeconds);
            }
        }

        private IEnumerator FetchSolarStatus()
        {
            string url = $"{backendBaseUrl}/api/routing/solar-status";
            using (UnityWebRequest req = UnityWebRequest.Get(url))
            {
                req.timeout = 5;
                yield return req.SendWebRequest();

                if (req.result == UnityWebRequest.Result.Success)
                {
                    try
                    {
                        SolarStatusResponse status = JsonUtility.FromJson<SolarStatusResponse>(req.downloadHandler.text);
                        if (status != null)
                        {
                            currentSolarElevation = status.solar_elevation_deg;
                            currentSunIntensity = status.sun_intensity;
                            shadeRecommendation = status.shade_recommendation;
                            Debug.Log($"[KioskNetworkBridge] Live Sun Status Updated: {status.sun_intensity}, Elev: {status.solar_elevation_deg} deg");
                        }
                    }
                    catch (Exception ex)
                    {
                        Debug.LogWarning($"[KioskNetworkBridge] JSON parse error: {ex.Message}");
                    }
                }
                else
                {
                    // Fallback to offline defaults
                }
            }
        }
    }
}

