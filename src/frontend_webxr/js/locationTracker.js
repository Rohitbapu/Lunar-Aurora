/**
 * Real-Time Mobile GPS & Mahabalipuram Demo Simulator for Lunar Aurora
 * Includes indoor network fallback, de-duplicated stop arrival events,
 * and Jury Table Indoor Demo Mode teleportation (+/-2.5m accuracy & solar hour override).
 */
class LocationTracker {
  constructor() {
    this.watchId = null;
    this.currentLat = null;
    this.currentLon = null;
    this.accuracyMeters = null;
    this.originLat = 12.6165181;
    this.originLon = 80.1982844;
    this.isTracking = false;
    this.hasGpsFix = false;
    this.isSimulated = false;
    this.demoModeActive = false;
    this.simulatedHour = 12.0;
    this.simulatedDate = '2027-01-11';
    this.permissionState = 'unknown';
    this.lastArrivedStep = null;

    this.userSiteX = 0;
    this.userSiteY = 0;

    // 7 Mahabalipuram stops (coordinates from OpenStreetMap ODbL; arrivalRadiusM loaded from backend API)
    this.stopsReference = [
      { step: 1, name: "Shore Temple Coastal Entry", x: 0.0, y: 0.0, lat: 12.6165181, lon: 80.1982844, arrivalRadiusM: null },
      { step: 2, name: "Shore Temple Shrines", x: 115.8, y: -7.2, lat: 12.6164535, lon: 80.1993500, arrivalRadiusM: null },
      { step: 3, name: "Pancha Rathas Monolithic Complex", x: -932.4, y: -829.7, lat: 12.6090647, lon: 80.1897016, arrivalRadiusM: null },
      { step: 4, name: "Arjuna's Penance (Descent of the Ganges)", x: -607.0, y: 154.8, lat: 12.6179087, lon: 80.1926969, arrivalRadiusM: null },
      { step: 5, name: "Krishna's Butterball (Vaan Irai Kal)", x: -638.9, y: 286.2, lat: 12.6190890, lon: 80.1924032, arrivalRadiusM: null },
      { step: 6, name: "Varaha Cave Temple", x: -658.4, y: 174.5, lat: 12.6180857, lon: 80.1922234, arrivalRadiusM: null },
      { step: 7, name: "Mahishasuramardini Mandapa", x: -732.8, y: -143.8, lat: 12.6152265, lon: 80.1915388, arrivalRadiusM: null }
    ];
    this.radiiLoadedFromApi = false;

    this.onLocationUpdated = null;
    this.onStopArrived = null;
  }

  /**
   * Populates per-stop coordinates and arrival_radius_m directly from backend API (/api/site/overview or /blueprint).
   */
  loadRadiiFromApi(apiItems) {
    if (!Array.isArray(apiItems) || apiItems.length === 0) return false;
    let updated = 0;
    for (const item of apiItems) {
      const step = Number(item.step_number || item.id);
      const target = this.stopsReference.find(s => s.step === step);
      if (!target) continue;
      if (Number.isFinite(Number(item.latitude))) target.lat = Number(item.latitude);
      if (Number.isFinite(Number(item.longitude))) target.lon = Number(item.longitude);
      if (Number.isFinite(Number(item.x))) target.x = Number(item.x);
      if (Number.isFinite(Number(item.y))) target.y = Number(item.y);
      if (item.arrival_radius_m !== null && item.arrival_radius_m !== undefined && Number.isFinite(Number(item.arrival_radius_m))) {
        target.arrivalRadiusM = Number(item.arrival_radius_m);
        updated++;
      }
    }
    if (updated > 0) this.radiiLoadedFromApi = true;
    return updated > 0;
  }

  _haversineMeters(lat1, lon1, lat2, lon2) {
    const R = 6371000.0;
    const p1 = (lat1 * Math.PI) / 180.0;
    const p2 = (lat2 * Math.PI) / 180.0;
    const dp = ((lat2 - lat1) * Math.PI) / 180.0;
    const dl = ((lon2 - lon1) * Math.PI) / 180.0;
    const a = Math.sin(dp / 2) ** 2 + Math.cos(p1) * Math.cos(p2) * Math.sin(dl / 2) ** 2;
    return 2.0 * R * Math.asin(Math.sqrt(a));
  }

  /**
   * Evaluates a lat/lon point against every stop's API-supplied arrival_radius_m.
   * Returns { stop, distanceMeters, radiusMeters } if inside a zone, otherwise null.
   */
  findArrivedStop(lat, lon) {
    if (!Number.isFinite(lat) || !Number.isFinite(lon)) return null;
    let bestMatch = null;
    for (const stop of this.stopsReference) {
      if (!Number.isFinite(stop.arrivalRadiusM)) continue;
      const distM = this._haversineMeters(lat, lon, stop.lat, stop.lon);
      if (distM <= stop.arrivalRadiusM) {
        if (!bestMatch || distM < bestMatch.distanceMeters) {
          bestMatch = { stop, distanceMeters: distM, radiusMeters: stop.arrivalRadiusM };
        }
      }
    }
    return bestMatch;
  }

  async checkPermissionStatus() {
    if (this.demoModeActive) return 'denied';
    if (navigator.permissions && navigator.permissions.query) {
      try {
        const result = await navigator.permissions.query({ name: 'geolocation' });
        this.permissionState = result.state;
        if (result.state === 'granted' && !this.demoModeActive) this.requestGpsFix();
        result.onchange = () => {
          this.permissionState = result.state;
          if (result.state === 'granted' && !this.demoModeActive) this.requestGpsFix();
        };
        return result.state;
      } catch (e) {}
    }
    return 'unknown';
  }

  requestGpsFix(highAccuracy = true) {
    if (this.demoModeActive) return;
    if (!navigator.geolocation) {
      this.useSimulatedGps();
      return;
    }

    const gpsLabel = document.getElementById('gps-coords-label');
    if (gpsLabel && !this.hasGpsFix) gpsLabel.textContent = "GPS: Locating...";

    navigator.geolocation.getCurrentPosition(
      (pos) => {
        this.isSimulated = false;
        this.handleGpsUpdate(pos);
        this.startContinuousWatch(highAccuracy);
      },
      (err) => {
        if (highAccuracy && (err.code === 2 || err.code === 3)) {
          this.requestGpsFix(false);
          return;
        }
        this.handleGpsError(err);
      },
      { enableHighAccuracy: highAccuracy, maximumAge: highAccuracy ? 1000 : 10000, timeout: 8000 }
    );
  }

  startContinuousWatch(highAccuracy = true) {
    if (this.watchId !== null) return;
    this.watchId = navigator.geolocation.watchPosition(
      (pos) => {
        if (!this.isSimulated) this.handleGpsUpdate(pos);
      },
      (err) => { if (err.code === 1) this.handleGpsError(err); },
      { enableHighAccuracy: highAccuracy, maximumAge: 2500, timeout: 12000 }
    );
    this.isTracking = true;
  }

  handleGpsUpdate(position) {
    const lat = position.coords.latitude;
    const lon = position.coords.longitude;
    const accuracy = Math.round(position.coords.accuracy || 10);

    this.hasGpsFix = true;
    this.permissionState = 'granted';
    this.currentLat = lat;
    this.currentLon = lon;
    this.accuracyMeters = accuracy;

    if (this.originLat === null) {
      this.originLat = lat;
      this.originLon = lon;
    }

    const deltaLatMeters = (lat - this.originLat) * 111320.0;
    const deltaLonMeters = (lon - this.originLon) * (111320.0 * Math.cos((lat * Math.PI) / 180.0));
    this.userSiteX = deltaLonMeters;
    this.userSiteY = deltaLatMeters;

    this.evaluateNearbyStops();

    const gpsLabel = document.getElementById('gps-coords-label');
    if (gpsLabel) gpsLabel.textContent = `GPS: ±${accuracy}m`;

    if (this.onLocationUpdated) {
      this.onLocationUpdated({
        lat: this.currentLat,
        lon: this.currentLon,
        accuracy: this.accuracyMeters,
        siteX: this.userSiteX,
        siteY: this.userSiteY
      });
    }
  }

  handleGpsError(error) {
    const gpsLabel = document.getElementById('gps-coords-label');
    if (error.code === 1) {
      this.permissionState = 'denied';
      if (gpsLabel) gpsLabel.textContent = "GPS: Demo Mode";
      this.useSimulatedGps();
    } else {
      if (gpsLabel) gpsLabel.textContent = "GPS: Site Sync";
      this.useSimulatedGps();
    }
  }

  useSimulatedGps() {
    this.hasGpsFix = true;
    this.isSimulated = true;
    this.accuracyMeters = 2.5;
    this.syncToCurrentStop();
  }

  syncToCurrentStop() {
    if (!this.isSimulated && this.currentLat !== null) return;
    if (window.tourManager && window.tourManager.currentStopData) {
      const s = window.tourManager.currentStopData;
      this.userSiteX = s.x;
      this.userSiteY = s.y;
    }
  }

  activateDemoMode(initialStep = 1) {
    this.demoModeActive = true;
    this.isSimulated = true;
    if (this.watchId !== null && navigator.geolocation) {
      navigator.geolocation.clearWatch(this.watchId);
      this.watchId = null;
    }
    return this.teleportToStop(initialStep, false);
  }

  /**
   * Jury Table Indoor Demo Mode: simulates physical walk to target station with +/-2.5m GPS lock
   */
  teleportToStop(stepNumber, fireArrival = true) {
    const target = this.stopsReference.find(s => s.step === Number(stepNumber));
    if (!target) return null;

    this.demoModeActive = true;
    this.isSimulated = true;
    this.hasGpsFix = true;
    this.accuracyMeters = 2.5;
    this.currentLat = target.lat;
    this.currentLon = target.lon;
    this.userSiteX = target.x;
    this.userSiteY = target.y;

    const gpsLabel = document.getElementById('gps-coords-label');
    if (gpsLabel) gpsLabel.textContent = `DEMO MODE (±2.5m)`;

    if (this.onLocationUpdated) {
      this.onLocationUpdated({
        lat: this.currentLat,
        lon: this.currentLon,
        accuracy: 2.5,
        siteX: this.userSiteX,
        siteY: this.userSiteY
      });
    }

    if (fireArrival && this.onStopArrived) {
      this.lastArrivedStep = target.step;
      this.onStopArrived(target, 2);
    }
    return target;
  }

  evaluateNearbyStops() {
    if (!Number.isFinite(this.currentLat) || !Number.isFinite(this.currentLon)) return;
    const match = this.findArrivedStop(this.currentLat, this.currentLon);
    const currentTourStep = window.tourManager ? window.tourManager.currentStep : 1;
    if (match && match.stop.step !== currentTourStep && match.stop.step !== this.lastArrivedStep) {
      this.lastArrivedStep = match.stop.step;
      if (this.onStopArrived) {
        this.onStopArrived(match.stop, Math.round(match.distanceMeters));
      }
    }
  }

  getDistanceToStop(stepNumber) {
    const target = this.stopsReference.find(s => s.step === stepNumber);
    if (!target) return 50;
    return Math.round(Math.hypot(this.userSiteX - target.x, this.userSiteY - target.y));
  }
}

window.locationTracker = new LocationTracker();
