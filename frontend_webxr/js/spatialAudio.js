/**
 * Spatial Audio Engine for Lunar Aurora
 * Uses Web Audio API HRTF PannerNode with clean fallback and accurate timeupdate callbacks
 * for tight YouTube-style subtitle synchronization.
 */
class SpatialAudioEngine {
  constructor() {
    this.ctx = null;
    this.listener = null;
    this.panner = null;
    this.currentAudioElement = null;
    this.currentSourceNode = null;
    this.isInitialized = false;
    this.isPlaying = false;
    this.playbackId = 0;
  }

  init() {
    if (this.isInitialized) return;
    const AudioContextClass = window.AudioContext || window.webkitAudioContext;
    if (!AudioContextClass) {
      console.warn("[SpatialAudio] Web Audio API not supported; using standard Audio element.");
      return;
    }

    try {
      this.ctx = new AudioContextClass();
      this.listener = this.ctx.listener;

      this.panner = this.ctx.createPanner();
      this.panner.panningModel = 'HRTF';
      this.panner.distanceModel = 'inverse';
      this.panner.refDistance = 1.0;
      this.panner.maxDistance = 50.0;
      this.panner.rolloffFactor = 1.0;

      // Anchor guide audio naturally slightly ahead of listener at ear height
      if (this.panner.positionX) {
        this.panner.positionX.value = 0;
        this.panner.positionY.value = 1.4;
        this.panner.positionZ.value = -1.2;
      } else {
        this.panner.setPosition(0, 1.4, -1.2);
      }

      this.panner.connect(this.ctx.destination);
      this.isInitialized = true;
      console.log("[SpatialAudio] AudioContext & HRTF Panner initialized.");
    } catch (e) {
      console.warn("[SpatialAudio] Init fallback:", e);
    }
  }

  async resumeOnUserGesture() {
    if (!this.isInitialized) this.init();
    if (this.ctx && this.ctx.state === 'suspended') {
      try {
        await this.ctx.resume();
      } catch (e) {}
    }
  }

  updateListener(camera) {
    if (!this.ctx || !this.listener || !camera) return;

    const pos = camera.position;
    if (this.listener.positionX) {
      this.listener.positionX.value = pos.x;
      this.listener.positionY.value = pos.y;
      this.listener.positionZ.value = pos.z;
    } else if (this.listener.setPosition) {
      this.listener.setPosition(pos.x, pos.y, pos.z);
    }

    const forward = new THREE.Vector3(0, 0, -1).applyQuaternion(camera.quaternion);
    const up = new THREE.Vector3(0, 1, 0).applyQuaternion(camera.quaternion);

    if (this.listener.forwardX) {
      this.listener.forwardX.value = forward.x;
      this.listener.forwardY.value = forward.y;
      this.listener.forwardZ.value = forward.z;
      this.listener.upX.value = up.x;
      this.listener.upY.value = up.y;
      this.listener.upZ.value = up.z;
    } else if (this.listener.setOrientation) {
      this.listener.setOrientation(forward.x, forward.y, forward.z, up.x, up.y, up.z);
    }
  }

  stopSpeech() {
    this.playbackId++;
    this.isPlaying = false;
    if (this.currentSourceNode) {
      try { this.currentSourceNode.disconnect(); } catch (e) {}
      this.currentSourceNode = null;
    }
    if (this.currentAudioElement) {
      try {
        this.currentAudioElement.onplay = null;
        this.currentAudioElement.ontimeupdate = null;
        this.currentAudioElement.onended = null;
        this.currentAudioElement.onerror = null;
        this.currentAudioElement.pause();
        this.currentAudioElement.src = "";
      } catch (e) {}
      this.currentAudioElement = null;
    }
  }

  async playSpeech(audioUrl, onStart, onEnd, onTimeUpdate) {
    this.stopSpeech();
    if (!audioUrl) return false;

    const myId = this.playbackId;
    await this.resumeOnUserGesture();
    if (myId !== this.playbackId) return false;

    const audio = new Audio();
    audio.crossOrigin = "anonymous";
    audio.preload = "auto";
    audio.src = audioUrl;
    this.currentAudioElement = audio;

    // Route through HRTF Panner when Web Audio is active
    if (this.ctx && this.panner) {
      try {
        const source = this.ctx.createMediaElementSource(audio);
        source.connect(this.panner);
        this.currentSourceNode = source;
      } catch (e) {
        console.warn("[SpatialAudio] Direct audio element fallback:", e);
      }
    }

    audio.onplay = () => {
      if (myId !== this.playbackId) return;
      this.isPlaying = true;
      if (onStart) onStart();
    };

    audio.ontimeupdate = () => {
      if (myId !== this.playbackId) return;
      if (onTimeUpdate && audio.duration > 0) {
        onTimeUpdate(audio.currentTime, audio.duration);
      }
    };

    audio.onended = () => {
      if (myId !== this.playbackId) return;
      this.isPlaying = false;
      if (onEnd) onEnd();
    };

    audio.onerror = (e) => {
      if (myId !== this.playbackId) return;
      console.warn("[SpatialAudio] Audio playback failed:", e);
      this.isPlaying = false;
      if (onEnd) onEnd();
    };

    try {
      await audio.play();
      return true;
    } catch (err) {
      console.warn("[SpatialAudio] Autoplay blocked until user tap:", err);
      this.isPlaying = false;
      return false;
    }
  }
}

window.spatialAudio = new SpatialAudioEngine();
