/**
 * Minimalist Camera-First AR Viewport for Lunar Aurora
 * Keeps the physical monument view 100% unobstructed.
 */
class ARScene {
  constructor() {
    this.container = null;
    this.scene = null;
    this.camera = null;
    this.renderer = null;
    this.cameraActive = false;
  }

  init(containerId) {
    this.container = document.getElementById(containerId);
    const width = window.innerWidth;
    const height = window.innerHeight;

    this.scene = new THREE.Scene();
    this.camera = new THREE.PerspectiveCamera(65, width / height, 0.05, 100);
    this.camera.position.set(0, 1.4, 0);

    this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: "high-performance" });
    this.renderer.setSize(width, height);
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.setClearColor(0x000000, 0);
    this.renderer.domElement.id = 'three-canvas';
    this.renderer.domElement.style.position = 'absolute';
    this.renderer.domElement.style.top = '0';
    this.renderer.domElement.style.left = '0';
    this.renderer.domElement.style.width = '100%';
    this.renderer.domElement.style.height = '100%';
    this.renderer.domElement.style.pointerEvents = 'none';
    this.container.appendChild(this.renderer.domElement);

    window.addEventListener('resize', () => this.onWindowResize());
    this.renderer.setAnimationLoop(() => this.render());
    console.log("[ARScene] Clean camera-first AR viewport ready.");
  }

  render() {
    if (window.spatialAudio) {
      window.spatialAudio.updateListener(this.camera);
    }
    this.renderer.render(this.scene, this.camera);
  }

  onWindowResize() {
    const w = window.innerWidth;
    const h = window.innerHeight;
    this.camera.aspect = w / h;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(w, h);
  }

  async startCameraFeed(videoElement) {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      console.warn("[ARScene] Camera getUserMedia not supported or origin insecure.");
      return { success: false, reason: "INSECURE_CONTEXT" };
    }

    try {
      const constraints = {
        video: {
          facingMode: { ideal: "environment" },
          width: { ideal: 1920 },
          height: { ideal: 1080 }
        },
        audio: false
      };
      const stream = await navigator.mediaDevices.getUserMedia(constraints);
      videoElement.srcObject = stream;
      videoElement.style.display = 'block';
      await videoElement.play();
      this.cameraActive = true;
      console.log("[ARScene] Fullscreen rear camera active!");
      return { success: true };
    } catch (e) {
      console.warn("[ARScene] Camera permission denied:", e);
      return { success: false, reason: e.name || e.message };
    }
  }
}

window.arScene = new ARScene();
