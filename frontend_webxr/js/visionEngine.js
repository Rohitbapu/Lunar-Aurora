/**
 * On-Device Computer Vision Engine for Lunar Aurora
 * Projects bounding boxes accurately onto object-fit: cover video streams
 * and runs battery-friendly throttled TensorFlow.js inference (~3-4 FPS).
 */
class VisionEngine {
  constructor() {
    this.model = null;
    this.video = null;
    this.canvas = null;
    this.ctx = null;
    this.isDetecting = false;
    this.isLoadingModel = false;
    this.currentPredictions = [];
    this.onStatusChange = null;
    this.onArtifactIdentified = null;
    this.loopTimerId = null;
  }

  async init(videoElement, overlayCanvas) {
    this.video = videoElement;
    this.canvas = overlayCanvas;
    this.ctx = overlayCanvas.getContext('2d');

    if (this.isLoadingModel || this.model) return;
    this.isLoadingModel = true;

    if (this.onStatusChange) this.onStatusChange("AI Loading...");

    try {
      if (window.cocoSsd) {
        this.model = await window.cocoSsd.load({ base: 'mobilenet_v2' });
        this.isLoadingModel = false;
        console.log("[VisionEngine] TensorFlow.js COCO-SSD model ready.");
        if (this.onStatusChange) this.onStatusChange("AI Ready");
      } else {
        this.isLoadingModel = false;
        if (this.onStatusChange) this.onStatusChange("AI Standby");
      }
    } catch (err) {
      console.warn("[VisionEngine] Model load warning:", err);
      this.isLoadingModel = false;
      if (this.onStatusChange) this.onStatusChange("AI Standby");
    }
  }

  startDetectionLoop() {
    if (this.isDetecting) return;
    this.isDetecting = true;
    this.detectFrame();
  }

  stopDetection() {
    this.isDetecting = false;
    if (this.loopTimerId) {
      clearTimeout(this.loopTimerId);
      this.loopTimerId = null;
    }
    if (this.ctx && this.canvas) {
      this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
    }
  }

  async detectFrame() {
    if (!this.isDetecting) return;

    if (this.model && this.video && this.video.readyState >= 2 && !this.video.paused) {
      const containerW = this.canvas.clientWidth || window.innerWidth;
      const containerH = this.canvas.clientHeight || window.innerHeight;
      if (this.canvas.width !== containerW || this.canvas.height !== containerH) {
        this.canvas.width = containerW;
        this.canvas.height = containerH;
      }

      try {
        const predictions = await this.model.detect(this.video);
        this.currentPredictions = predictions;
        this.renderPredictions(predictions);
      } catch (e) {}
    }

    // Throttle to ~300ms so mobile devices remain cool and responsive
    this.loopTimerId = setTimeout(() => this.detectFrame(), 300);
  }

  renderPredictions(predictions) {
    if (!this.ctx || !this.canvas || !this.video) return;
    const cw = this.canvas.width;
    const ch = this.canvas.height;
    const vw = this.video.videoWidth;
    const vh = this.video.videoHeight;

    this.ctx.clearRect(0, 0, cw, ch);
    if (!vw || !vh) return;

    // Exact CSS `object-fit: cover` coordinate transform so boxes align on portrait/landscape screens
    const scale = Math.max(cw / vw, ch / vh);
    const offsetX = (cw - vw * scale) / 2;
    const offsetY = (ch - vh * scale) / 2;

    for (const pred of predictions) {
      if (pred.score < 0.4) continue;
      const [rx, ry, rw, rh] = pred.bbox;
      const x = rx * scale + offsetX;
      const y = ry * scale + offsetY;
      const width = rw * scale;
      const height = rh * scale;

      this.ctx.strokeStyle = 'rgba(0, 229, 255, 0.75)';
      this.ctx.lineWidth = 2;
      this.ctx.strokeRect(x, y, width, height);

      const cornerSize = 12;
      this.ctx.fillStyle = '#f4c430';
      this.ctx.fillRect(x - 1, y - 1, cornerSize, 3);
      this.ctx.fillRect(x - 1, y - 1, 3, cornerSize);
      this.ctx.fillRect(x + width - cornerSize + 1, y - 1, cornerSize, 3);
      this.ctx.fillRect(x + width - 2, y - 1, 3, cornerSize);

      const labelText = `${pred.class.toUpperCase()} ${Math.round(pred.score * 100)}%`;
      this.ctx.font = 'bold 11px sans-serif';
      const textWidth = this.ctx.measureText(labelText).width + 12;
      const labelY = Math.max(24, y);
      this.ctx.fillStyle = 'rgba(10, 14, 23, 0.85)';
      this.ctx.fillRect(x, labelY - 22, textWidth, 20);

      this.ctx.fillStyle = '#f4c430';
      this.ctx.fillText(labelText, x + 6, labelY - 8);
    }
  }

  /**
   * Explicitly scan whatever is currently in view (called when user taps "SCAN RELIC")
   */
  async scanCurrentTarget() {
    let labels = [];
    if (this.currentPredictions && this.currentPredictions.length > 0) {
      labels = this.currentPredictions
        .filter(p => p.score > 0.35)
        .map(p => p.class.toLowerCase());
    }

    const sessionId = window.tourManager ? window.tourManager.sessionId : null;
    const currentStep = window.tourManager ? window.tourManager.currentStep : 1;
    const lang = (window.tourManager && window.tourManager.language) || window.currentLanguage || 'en';

    try {
      const response = await fetch('/api/vision/identify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          detected_labels: labels,
          current_step: currentStep,
          session_id: sessionId,
          language: lang
        })
      });

      if (response.ok) {
        const data = await response.json();
        if (this.onArtifactIdentified) {
          this.onArtifactIdentified(data);
        }
        return data;
      }
    } catch (err) {
      console.warn("[VisionEngine] API identify error:", err);
    }
    return null;
  }
}

window.visionEngine = new VisionEngine();
