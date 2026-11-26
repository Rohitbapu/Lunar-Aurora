/**
 * On-Device MobileNetV2 TF.js Carving Classifier for Lunar Aurora
 * - Strictly runs ONLY on [SCAN RELIC] tap (no background loop, no COCO-SSD keywords, no score boosts, no step fallback)
 * - Verifies exact class order alignment with carving_signatures.json & model_classes.json
 * - If model.json is missing or fails to load, displays "Vision model not installed" and refuses to guess
 */
class VisionEngine {
  constructor() {
    this.customModel = null;
    this.modelInstalled = false;
    this.signaturesConfig = null;
    this.classes = [];
    this.confidenceThreshold = 0.82;
    this.inputWidth = 224;
    this.inputHeight = 224;

    this.video = null;
    this.canvas = null;
    this.ctx = null;
    this.lastInferenceMs = 0;
    this.onStatusChange = null;
    this.onArtifactIdentified = null;
  }

  async init(videoElement, overlayCanvas) {
    this.video = videoElement;
    this.canvas = overlayCanvas;
    this.ctx = overlayCanvas ? overlayCanvas.getContext('2d') : null;
    this.modelInstalled = false;
    this.customModel = null;

    // 1. Load canonical ordered classes from carving_signatures.json
    try {
      const cfgRes = await fetch('/app/assets/vision_model/carving_signatures.json');
      if (!cfgRes.ok) {
        throw new Error(`carving_signatures.json returned HTTP ${cfgRes.status}`);
      }
      this.signaturesConfig = await cfgRes.json();
      this.confidenceThreshold = Number(this.signaturesConfig.confidence_threshold ?? 0.82);

      const sorted = [...(this.signaturesConfig.classes || [])].sort((a, b) => a.class_index - b.class_index);
      for (let i = 0; i < sorted.length; i++) {
        if (sorted[i].class_index !== i) {
          throw new Error(`Class index mismatch in carving_signatures.json at index ${i}`);
        }
      }
      this.classes = sorted;
      if (Array.isArray(this.signaturesConfig.input_size) && this.signaturesConfig.input_size.length === 2) {
        this.inputWidth = this.signaturesConfig.input_size[0];
        this.inputHeight = this.signaturesConfig.input_size[1];
      }
    } catch (err) {
      console.error("[VisionEngine] Config load error:", err);
      if (this.onStatusChange) this.onStatusChange("Vision model not installed");
      return false;
    }

    // 2. Load custom MobileNetV2 TF.js model strictly (no fallback hacks)
    const modelUrl = this.signaturesConfig.tfjs_model_url || '/app/assets/vision_model/model.json';
    try {
      const headRes = await fetch(modelUrl, { method: 'HEAD' });
      if (!headRes.ok || !window.tf) {
        this._reportNotInstalled("model.json missing");
        return false;
      }

      this.customModel = await window.tf.loadLayersModel(modelUrl);

      // Assert model output units match carving_signatures.json class count
      const outShape = this.customModel.outputs[0].shape;
      const numOutputs = outShape[outShape.length - 1];
      if (numOutputs !== this.classes.length) {
        this.customModel = null;
        throw new Error(
          `Model output dimension (${numOutputs}) != carving_signatures.json classes (${this.classes.length}).`
        );
      }

      // Verify exact class order against exported model_classes.json if present
      const classesUrl = this.signaturesConfig.classes_manifest_url || '/app/assets/vision_model/model_classes.json';
      const clsRes = await fetch(classesUrl);
      if (clsRes.ok) {
        const exported = await clsRes.json();
        const exportedOrder = exported.classes || [];
        const expectedOrder = this.classes.map(c => c.id);
        if (
          exportedOrder.length !== expectedOrder.length ||
          exportedOrder.some((name, idx) => name !== expectedOrder[idx])
        ) {
          this.customModel = null;
          throw new Error(
            `Class order mismatch! Exported=${JSON.stringify(exportedOrder)} vs signatures=${JSON.stringify(expectedOrder)}`
          );
        }
      }

      this.modelInstalled = true;
      console.log("[VisionEngine] MobileNetV2 TF.js classifier loaded:", this.classes.map(c => c.id));
      if (this.onStatusChange) this.onStatusChange("Vision Model Ready");
      return true;
    } catch (err) {
      console.error("[VisionEngine] Vision model load failure:", err);
      this._reportNotInstalled(err.message);
      return false;
    }
  }

  _reportNotInstalled(reason) {
    this.modelInstalled = false;
    this.customModel = null;
    console.warn("[VisionEngine] Vision model not installed:", reason);
    if (this.onStatusChange) this.onStatusChange("Vision model not installed");
  }

  /**
   * Runs inference strictly once when user taps [SCAN RELIC].
   */
  async scanCurrentTarget() {
    if (!this.modelInstalled || !this.customModel) {
      if (typeof showNotification === 'function') {
        showNotification("Vision model not installed");
      }
      if (this.onStatusChange) this.onStatusChange("Vision model not installed");
      return { recognized: false, error: "Vision model not installed" };
    }

    if (!this.video || this.video.readyState < 2 || !window.tf) {
      if (typeof showNotification === 'function') {
        showNotification("Camera stream not ready yet.");
      }
      return { recognized: false, error: "Camera not ready" };
    }

    const t0 = performance.now();
    const probs = window.tf.tidy(() => {
      const frame = window.tf.browser.fromPixels(this.video);
      const resized = window.tf.image.resizeBilinear(frame, [this.inputHeight, this.inputWidth]);
      // Match tf.keras.applications.mobilenet_v2.preprocess_input: scale [0,255] -> [-1, 1]
      const normalized = resized.toFloat().div(127.5).sub(1.0).expandDims(0);
      return this.customModel.predict(normalized).dataSync();
    });
    this.lastInferenceMs = Math.round((performance.now() - t0) * 100) / 100;

    const latEl = document.getElementById('demo-vision-latency');
    if (latEl) latEl.textContent = `${this.lastInferenceMs} ms`;

    if (probs.length !== this.classes.length) {
      throw new Error(`Softmax length (${probs.length}) != expected class count (${this.classes.length})`);
    }

    let bestIdx = 0;
    for (let i = 1; i < probs.length; i++) {
      if (probs[i] > probs[bestIdx]) bestIdx = i;
    }

    const bestScore = Number(probs[bestIdx]);
    const bestClass = this.classes[bestIdx];

    console.log(
      `[VisionEngine] Inference ${this.lastInferenceMs} ms | top=${bestClass.id} (${(bestScore * 100).toFixed(2)}%)`
    );

    if (bestScore < this.confidenceThreshold || !bestClass.is_relic) {
      if (typeof showNotification === 'function') {
        showNotification(
          `No carving recognized (${bestClass.id}: ${Math.round(bestScore * 100)}% < ${Math.round(this.confidenceThreshold * 100)}%, ${this.lastInferenceMs}ms)`
        );
      }
      return {
        recognized: false,
        topClass: bestClass.id,
        score: bestScore,
        inference_ms: this.lastInferenceMs
      };
    }

    const sessionId = window.tourManager ? window.tourManager.sessionId : null;
    const lang = (window.tourManager && window.tourManager.language) || window.currentLanguage || 'en';

    try {
      const response = await fetch('/api/vision/identify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          detected_labels: [bestClass.id],
          session_id: sessionId,
          language: lang
        })
      });

      if (response.ok) {
        const data = await response.json();
        data.inference_ms = this.lastInferenceMs;
        data.softmax_score = bestScore;
        if (this.onArtifactIdentified) {
          this.onArtifactIdentified(data);
        }
        return { recognized: true, ...data };
      }
    } catch (err) {
      console.warn("[VisionEngine] API identify error:", err);
    }
    return { recognized: false, error: "Backend identify error" };
  }
}

window.visionEngine = new VisionEngine();
