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
    this.originLat = null;
    this.originLon = null;
    this.isTracking = false;
    this.hasGpsFix = false;
    this.isSimulated = false;
    this.simulatedHour = null;
    this.permissionState = 'unknown';
    this.lastArrivedStep = null;

    this.userSiteX = 0;
    this.userSiteY = 0;

    // Authentic 7-Stop Mahabalipuram Shore Temple coordinates
    this.stopsReference = [
      { step: 1, name: "Shore Temple East Gopuram", x: 0, y: 0, lat: 12.6165, lon: 80.1993 },
      { step: 2, name: "Monolithic Yali Pillars Gallery", x: 25, y: 40, lat: 12.6169, lon: 80.1995 },
      { step: 3, name: "Chariot Wheel Solar Chronometer", x: 75, y: 85, lat: 12.6173, lon: 80.1999 },
      { step: 4, name: "Rajasimhesvara Shore Vimana", x: 30, y: 110, lat: 12.6175, lon: 80.1994 },
      { step: 5, name: "Royal Lotus Hydraulic Basin", x: -20, y: 120, lat: 12.6176, lon: 80.1989 },
      { step: 6, name: "Arjuna's Penance Banyan Canopy", x: -40, y: 65, lat: 12.6171, lon: 80.1986 },
      { step: 7, name: "Coromandel Sunset Bastion", x: 60, y: 140, lat: 12.6178, lon: 80.1997 }
    ];

    this.onLocationUpdated = null;
    this.onStopArrived = null;
  }

  async checkPermissionStatus() {
    if (navigator.permissions && navigator.permissions.query) {
      try {
        const result = await navigator.permissions.query({ name: 'geolocation' });
        this.permissionState = result.state;
        if (result.state === 'granted') this.requestGpsFix();
        result.onchange = () => {
          this.permissionState = result.state;
          if (result.state === 'granted') this.requestGpsFix();
        };
        return result.state;
      } catch (e) {}
    }
    return 'unknown';
  }

  requestGpsFix(highAccuracy = true) {
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

  /**
   * Jury Table Indoor Demo Mode: simulates physical walk to target station with +/-2.5m GPS lock
   */
  teleportToStop(stepNumber, fireArrival = true) {
    const target = this.stopsReference.find(s => s.step === Number(stepNumber));
    if (!target) return null;

    this.isSimulated = true;
    this.hasGpsFix = true;
    this.accuracyMeters = 2.5;
    this.currentLat = target.lat;
    this.currentLon = target.lon;
    this.userSiteX = target.x;
    this.userSiteY = target.y;

    const gpsLabel = document.getElementById('gps-coords-label');
    if (gpsLabel) gpsLabel.textContent = `DEMO: ±2.5m`;

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
    let nearestStop = null;
    let minDistance = Infinity;

    for (const stop of this.stopsReference) {
      const dist = Math.hypot(this.userSiteX - stop.x, this.userSiteY - stop.y);
      if (dist < minDistance) {
        minDistance = dist;
        nearestStop = stop;
      }
    }

    const currentTourStep = window.tourManager ? window.tourManager.currentStep : 1;
    if (nearestStop && minDistance <= 15 && nearestStop.step !== currentTourStep && nearestStop.step !== this.lastArrivedStep) {
      this.lastArrivedStep = nearestStop.step;
      if (this.onStopArrived) {
        this.onStopArrived(nearestStop, Math.round(minDistance));
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
