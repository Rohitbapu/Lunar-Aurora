/**
 * Interactive Camera-First AR Viewport for Lunar Aurora
 * - Keeps rear camera 100% unobstructed while walking
 * - Supports on-demand 3D .glb Architectural Reconstruction + Era Slider cross-fade
 * - Toggleable [3D GUIDE] corner avatar synced to voice playback
 * - DeviceOrientationEvent -> camera.quaternion -> HRTF binaural SpatialAudio listener
 * - Real-time FPS telemetry for Jury Demo Mode
 */
class ARScene {
  constructor() {
    this.container = null;
    this.scene = null;
    this.camera = null;
    this.renderer = null;
    this.cameraActive = false;

    this.reconstructionGroup = null;
    this.solidMeshes = [];
    this.wireMeshes = [];
    this.eraFactor = 1.0;

    this.guideGroup = null;
    this.guideVisible = false;

    this.gltfLoader = null;
    this.clock = new THREE.Clock();
    this._fpsFrames = 0;
    this._fpsLastTime = performance.now();
    this.currentFps = 60;
    this._euler = new THREE.Euler(0, 0, 0, 'YXZ');
    this._orientBound = false;
  }

  init(containerId) {
    this.container = document.getElementById(containerId);
    const width = window.innerWidth;
    const height = window.innerHeight;

    this.scene = new THREE.Scene();
    this.camera = new THREE.PerspectiveCamera(65, width / height, 0.05, 100);
    this.camera.position.set(0, 1.4, 0);

    // Three-point ambient & directional lighting for .glb sculptures
    const ambient = new THREE.AmbientLight(0xffffff, 0.85);
    this.scene.add(ambient);
    const sunLight = new THREE.DirectionalLight(0xfff2cc, 1.4);
    sunLight.position.set(3, 5, 4);
    this.scene.add(sunLight);
    const rimLight = new THREE.DirectionalLight(0x00e5ff, 0.7);
    rimLight.position.set(-3, 2, -3);
    this.scene.add(rimLight);

    this.renderer = new THREE.WebGLRenderer({
      antialias: true,
      alpha: true,
      preserveDrawingBuffer: true,
      powerPreference: "high-performance"
    });
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

    if (THREE.GLTFLoader) {
      this.gltfLoader = new THREE.GLTFLoader();
    }

    this._buildCornerGuideAvatar();

    window.addEventListener('resize', () => this.onWindowResize());
    this.renderer.setAnimationLoop(() => this.render());
    console.log("[ARScene] Interactive WebXR 3D overlay initialized.");
  }

  enableOrientationTracking() {
    if (this._orientBound) return;
    const bindListener = () => {
      if (this._orientBound) return;
      this._orientBound = true;
      window.addEventListener('deviceorientation', (ev) => {
        if (ev.alpha === null || ev.beta === null || ev.gamma === null) return;
        const alpha = THREE.MathUtils.degToRad(ev.alpha || 0);
        const beta = THREE.MathUtils.degToRad((ev.beta || 0) - 70);
        const gamma = THREE.MathUtils.degToRad(-(ev.gamma || 0));
        this._euler.set(beta * 0.45, alpha, gamma * 0.45, 'YXZ');
        this.camera.quaternion.setFromEuler(this._euler);
      });
    };

    if (typeof DeviceOrientationEvent !== 'undefined' && typeof DeviceOrientationEvent.requestPermission === 'function') {
      DeviceOrientationEvent.requestPermission()
        .then(state => { if (state === 'granted') bindListener(); })
        .catch(() => {});
    } else if (typeof window.DeviceOrientationEvent !== 'undefined') {
      bindListener();
    }
  }

  _buildCornerGuideAvatar() {
    const group = new THREE.Group();
    group.position.set(-0.55, 0.92, -1.65);
    group.visible = false;

    const coreGeo = new THREE.OctahedronGeometry(0.11, 0);
    const coreMat = new THREE.MeshStandardMaterial({
      color: 0x00e5ff,
      emissive: 0x004d66,
      metalness: 0.35,
      roughness: 0.25,
      transparent: true,
      opacity: 0.92
    });
    const core = new THREE.Mesh(coreGeo, coreMat);
    group.add(core);

    const ringGeo = new THREE.TorusGeometry(0.16, 0.012, 10, 32);
    const ringMat = new THREE.MeshBasicMaterial({ color: 0xf4c430, transparent: true, opacity: 0.85 });
    const ring = new THREE.Mesh(ringGeo, ringMat);
    ring.rotation.x = Math.PI / 2.6;
    group.add(ring);

    group.userData = { core, ring };
    this.guideGroup = group;
    this.scene.add(group);
  }

  toggleGuideAvatar(forceState = null) {
    this.guideVisible = forceState !== null ? Boolean(forceState) : !this.guideVisible;
    if (this.guideGroup) {
      this.guideGroup.visible = this.guideVisible;
    }
    return this.guideVisible;
  }

  _clearReconstruction() {
    if (this.reconstructionGroup) {
      this.scene.remove(this.reconstructionGroup);
      this.reconstructionGroup = null;
    }
    this.solidMeshes = [];
    this.wireMeshes = [];
  }

  hideRelicModel() {
    this._clearReconstruction();
  }

  showRelicModel(modelUrl, title = "Monument") {
    this._clearReconstruction();
    const container = new THREE.Group();
    container.position.set(0, 1.32, -2.1);
    this.reconstructionGroup = container;
    this.scene.add(container);

    const finalizeObject = (obj) => {
      // Auto-normalize scale to fit ~0.75m hologram viewport
      const box = new THREE.Box3().setFromObject(obj);
      const size = new THREE.Vector3();
      box.getSize(size);
      const maxDim = Math.max(size.x, size.y, size.z, 0.1);
      const normScale = 0.85 / maxDim;
      obj.scale.multiplyScalar(normScale);

      const center = new THREE.Vector3();
      new THREE.Box3().setFromObject(obj).getCenter(center);
      obj.position.sub(center);

      const wireClone = obj.clone();
      obj.traverse((c) => {
        if (c.isMesh && c.material) {
          c.material = c.material.clone();
          c.material.transparent = true;
          c.material.color = new THREE.Color(0xf4c430);
          this.solidMeshes.push(c);
        }
      });

      const cyanWireMat = new THREE.MeshBasicMaterial({
        color: 0x00e5ff,
        wireframe: true,
        transparent: true,
        opacity: 0.75
      });
      wireClone.traverse((c) => {
        if (c.isMesh) {
          c.material = cyanWireMat.clone();
          this.wireMeshes.push(c);
        }
      });

      container.add(obj);
      container.add(wireClone);
      this.setEraFactor(this.eraFactor);
    };

    if (this.gltfLoader && modelUrl) {
      this.gltfLoader.load(
        modelUrl,
        (gltf) => finalizeObject(gltf.scene),
        undefined,
        () => finalizeObject(this._createFallbackSculpture(title))
      );
    } else {
      finalizeObject(this._createFallbackSculpture(title));
    }
  }

  _createFallbackSculpture(title) {
    const g = new THREE.Group();
    const tiers = 4;
    for (let i = 0; i < tiers; i++) {
      const w = 0.55 - i * 0.11;
      const h = 0.16;
      const m = new THREE.Mesh(
        new THREE.BoxGeometry(w, h, w),
        new THREE.MeshStandardMaterial({ color: 0xf4c430, roughness: 0.4, metalness: 0.25 })
      );
      m.position.y = i * h;
      g.add(m);
    }
    const kalasa = new THREE.Mesh(
      new THREE.ConeGeometry(0.11, 0.24, 12),
      new THREE.MeshStandardMaterial({ color: 0xf4c430 })
    );
    kalasa.position.y = tiers * 0.16 + 0.08;
    g.add(kalasa);
    return g;
  }

  /**
   * 0.0 = Eroded Present Wireframe Scan | 1.0 = 700 CE Pallava Solid Reconstruction
   */
  setEraFactor(factor) {
    this.eraFactor = Math.max(0, Math.min(1, Number(factor)));
    const solidOp = 0.15 + 0.82 * this.eraFactor;
    const wireOp = 0.9 - 0.72 * this.eraFactor;

    for (const m of this.solidMeshes) {
      if (m.material) {
        m.material.opacity = solidOp;
        m.material.needsUpdate = true;
      }
    }
    for (const w of this.wireMeshes) {
      if (w.material) {
        w.material.opacity = Math.max(0.08, wireOp);
        w.material.needsUpdate = true;
      }
    }
  }

  render() {
    const dt = Math.min(0.1, this.clock.getDelta());
    const t = this.clock.elapsedTime;

    if (this.reconstructionGroup) {
      this.reconstructionGroup.rotation.y += dt * 0.45;
      this.reconstructionGroup.position.y = 1.32 + Math.sin(t * 1.8) * 0.03;
    }

    if (this.guideGroup && this.guideGroup.visible) {
      const speaking = window.spatialAudio && window.spatialAudio.isPlaying;
      const { core, ring } = this.guideGroup.userData;
      core.rotation.y += dt * (speaking ? 2.4 : 0.7);
      ring.rotation.z += dt * (speaking ? 3.0 : 0.9);
      const pulse = speaking ? 1.0 + 0.14 * Math.sin(t * 10) : 1.0;
      core.scale.setScalar(pulse);
    }

    if (window.spatialAudio) {
      window.spatialAudio.updateListener(this.camera);
    }

    this._fpsFrames++;
    const now = performance.now();
    if (now - this._fpsLastTime >= 1000) {
      this.currentFps = Math.round((this._fpsFrames * 1000) / (now - this._fpsLastTime));
      this._fpsFrames = 0;
      this._fpsLastTime = now;
      const fpsEl = document.getElementById('demo-fps-readout');
      if (fpsEl) fpsEl.textContent = `${this.currentFps} FPS`;
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
