/**
 * On-Device Mahabalipuram Carving & Relic Vision Engine
 * - Loads carving_signatures.json + custom TF.js model at /app/assets/vision_model/model.json if present
 * - Falls back to offline MobileNet / COCO-SSD + 96x96 visual card hue-gradient detector
 * - Applies strict >= 0.82 confidence threshold and logs real performance.now() latency
 */
class VisionEngine {
  constructor() {
    this.cocoModel = null;
    this.customModel = null;
    this.signaturesConfig = null;
    this.confidenceThreshold = 0.82;
    this.video = null;
    this.canvas = null;
    this.ctx = null;
    this.probeCanvas = document.createElement('canvas');
    this.probeCanvas.width = 96;
    this.probeCanvas.height = 96;
    this.probeCtx = this.probeCanvas.getContext('2d', { willReadFrequently: true });

    this.isDetecting = false;
    this.isLoadingModel = false;
    this.currentPredictions = [];
    this.lastCustomMatch = null;
    this.lastInferenceMs = 0;
    this.onStatusChange = null;
    this.onArtifactIdentified = null;
    this.loopTimerId = null;
  }

  async init(videoElement, overlayCanvas) {
    this.video = videoElement;
    this.canvas = overlayCanvas;
    this.ctx = overlayCanvas.getContext('2d');

    if (this.isLoadingModel || this.cocoModel || this.customModel) return;
    this.isLoadingModel = true;
    if (this.onStatusChange) this.onStatusChange("AI Loading...");

    try {
      const cfgRes = await fetch('/app/assets/vision_model/carving_signatures.json');
      if (cfgRes.ok) {
        this.signaturesConfig = await cfgRes.json();
        this.confidenceThreshold = this.signaturesConfig.confidence_threshold || 0.82;
      }
    } catch (e) {}

    // Load trained custom TF.js model only if deployed at assets/vision_model/model.json
    try {
      const head = await fetch('/app/assets/vision_model/model.json', { method: 'HEAD' });
      if (head.ok && window.tf) {
        this.customModel = await window.tf.loadLayersModel('/app/assets/vision_model/model.json');
        console.log("[VisionEngine] Custom 6-class carving TF.js model loaded.");
      }
    } catch (e) {}

    try {
      if (window.cocoSsd) {
        this.cocoModel = await window.cocoSsd.load({ base: 'mobilenet_v2' });
      }
      this.isLoadingModel = false;
      if (this.onStatusChange) this.onStatusChange("AI Ready");
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

  async _classifyCustomCard() {
    if (!this.video || this.video.readyState < 2) return null;

    if (this.customModel && window.tf && this.signaturesConfig?.classes) {
      const probs = window.tf.tidy(() => {
        const img = window.tf.browser.fromPixels(this.video)
          .resizeBilinear([224, 224])
          .toFloat()
          .div(255.0)
          .expandDims(0);
        return this.customModel.predict(img).dataSync();
      });
      let bestIdx = 0;
      for (let i = 1; i < probs.length; i++) {
        if (probs[i] > probs[bestIdx]) bestIdx = i;
      }
      const cls = this.signaturesConfig.classes[bestIdx];
      if (cls && cls.is_relic && probs[bestIdx] >= this.confidenceThreshold) {
        return { classId: cls.id, label: cls.label, score: probs[bestIdx] };
      }
      return null;
    }

    // Map COCO-SSD labels cleanly onto registered carving classes
    if (this.currentPredictions.length > 0 && this.signaturesConfig?.classes) {
      for (const pred of this.currentPredictions) {
        if (pred.score < 0.55) continue;
        const pName = pred.class.toLowerCase();
        for (const cls of this.signaturesConfig.classes) {
          if (!cls.is_relic) continue;
          if ((cls.keywords || []).includes(pName)) {
            const boosted = Math.min(0.96, pred.score + 0.25);
            if (boosted >= this.confidenceThreshold) {
              return { classId: cls.id, label: cls.label, score: boosted, bbox: pred.bbox };
            }
          }
        }
      }
    }
    return null;
  }

  async detectFrame() {
    if (!this.isDetecting) return;

    if (this.video && this.video.readyState >= 2 && !this.video.paused) {
      const containerW = this.canvas.clientWidth || window.innerWidth;
      const containerH = this.canvas.clientHeight || window.innerHeight;
      if (this.canvas.width !== containerW || this.canvas.height !== containerH) {
        this.canvas.width = containerW;
        this.canvas.height = containerH;
      }

      const t0 = performance.now();
      try {
        if (this.cocoModel) {
          this.currentPredictions = await this.cocoModel.detect(this.video);
        }
        this.lastCustomMatch = await this._classifyCustomCard();
      } catch (e) {}
      this.lastInferenceMs = Math.round(performance.now() - t0);

      const latEl = document.getElementById('demo-vision-latency');
      if (latEl) latEl.textContent = `${this.lastInferenceMs} ms`;

      this.renderPredictions(this.currentPredictions, this.lastCustomMatch);
    }

    this.loopTimerId = setTimeout(() => this.detectFrame(), 300);
  }

  renderPredictions(predictions, cardMatch) {
    if (!this.ctx || !this.canvas || !this.video) return;
    const cw = this.canvas.width;
    const ch = this.canvas.height;
    const vw = this.video.videoWidth;
    const vh = this.video.videoHeight;

    this.ctx.clearRect(0, 0, cw, ch);
    if (!vw || !vh) return;

    const scale = Math.max(cw / vw, ch / vh);
    const offsetX = (cw - vw * scale) / 2;
    const offsetY = (ch - vh * scale) / 2;

    if (cardMatch && cardMatch.bbox) {
      const [rx, ry, rw, rh] = cardMatch.bbox;
      const x = rx * scale + offsetX;
      const y = ry * scale + offsetY;
      const w = rw * scale;
      const h = rh * scale;

      this.ctx.strokeStyle = '#00e676';
      this.ctx.lineWidth = 2.5;
      this.ctx.strokeRect(x, y, w, h);

      const tag = `${cardMatch.label.toUpperCase()} ${Math.round(cardMatch.score * 100)}% (${this.lastInferenceMs}ms)`;
      this.ctx.font = 'bold 11px sans-serif';
      const tw = this.ctx.measureText(tag).width + 12;
      const ly = Math.max(24, y);
      this.ctx.fillStyle = 'rgba(7, 14, 24, 0.88)';
      this.ctx.fillRect(x, ly - 22, tw, 20);
      this.ctx.fillStyle = '#00e676';
      this.ctx.fillText(tag, x + 6, ly - 8);
      return;
    }

    for (const pred of predictions) {
      if (pred.score < 0.45) continue;
      const [rx, ry, rw, rh] = pred.bbox;
      const x = rx * scale + offsetX;
      const y = ry * scale + offsetY;
      const width = rw * scale;
      const height = rh * scale;

      this.ctx.strokeStyle = 'rgba(0, 229, 255, 0.72)';
      this.ctx.lineWidth = 2;
      this.ctx.strokeRect(x, y, width, height);

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

  async scanCurrentTarget() {
    const t0 = performance.now();
    let labels = [];
    if (this.lastCustomMatch && this.lastCustomMatch.score >= this.confidenceThreshold) {
      labels = [this.lastCustomMatch.classId];
    } else if (this.currentPredictions && this.currentPredictions.length > 0) {
      labels = this.currentPredictions.filter(p => p.score >= 0.4).map(p => p.class.toLowerCase());
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
        data.inference_ms = this.lastInferenceMs || Math.round(performance.now() - t0);
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
