/**
 * Tour Manager for Lunar Aurora (Mahabalipuram Heritage Edition)
 * Coordinates personalized visitor sessions, 7-stop progression, per-stop riddles,
 * dual solar/shaded route telemetry, watermarked memory snapshots, and PDF journal export.
 */
class TourManager {
  constructor() {
    this.sessionId = null;
    this.ticketId = null;
    this.customerName = "Honored Traveler";
    this.language = "en";
    this.currentStep = 1;
    this.visitedSteps = [1];
    this.completedRelics = [];
    this.solvedRiddles = [];
    this.unlockedBadges = [];
    this.localPhotos = [];
    this.totalXp = 50;
    this.blueprintStops = [];
    this.siteEdges = [];
    this.currentStopData = null;
    this.hiddenTimestamp = null;
    this.hasPlayedInitialWelcome = false;
    this.shadeMapRenderer = null;

    this.STORAGE_KEY = "lunar_aurora_session";
  }

  async init() {
    const urlParams = new URLSearchParams(window.location.search);
    const paramName = urlParams.get('name');
    const paramTicket = urlParams.get('ticket_id');
    const paramSession = urlParams.get('session_id');
    const paramLang = urlParams.get('lang');

    let savedSession = null;
    try {
      const saved = localStorage.getItem(this.STORAGE_KEY);
      if (saved) savedSession = JSON.parse(saved);
    } catch (e) {}

    const sessionToResume = paramSession || (savedSession ? savedSession.sessionId : null);
    const ticketToResume = paramTicket || (savedSession ? savedSession.ticketId : null);
    const visitorName = paramName || (savedSession ? savedSession.customerName : "Honored Traveler");
    const lang = paramLang || (savedSession ? savedSession.language : "en");

    try {
      const response = await fetch('/api/session/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionToResume,
          ticket_id: ticketToResume,
          customer_name: visitorName,
          preferred_language: lang,
          generate_audio: true
        })
      });

      if (response.ok) {
        const data = await response.json();
        this.sessionId = data.session_id;
        this.ticketId = data.ticket_id;
        this.customerName = data.customer_name;
        this.language = data.language || 'en';
        this.currentStep = data.current_step || 1;
        this.visitedSteps = data.visited_steps || [this.currentStep];
        this.completedRelics = data.completed_relics || [];
        this.solvedRiddles = data.solved_riddles || [];
        this.unlockedBadges = data.unlocked_badges || [];
        this.totalXp = data.total_xp || 50;
        this.currentStopData = data.current_stop;

        window.currentLanguage = this.language;
        const langSelect = document.getElementById('lang-select');
        if (langSelect) langSelect.value = this.language;

        this.saveToStorage();
        this.restoreChatHistory(data.chat_history || []);
        await this.loadBlueprint();
        this.updateTopHUD();

        if (window.locationTracker) {
          window.locationTracker.syncToCurrentStop();
        }
        return true;
      }
    } catch (err) {
      console.warn("[TourManager] Backend session error:", err);
    }
    return false;
  }

  saveToStorage() {
    try {
      localStorage.setItem(this.STORAGE_KEY, JSON.stringify({
        sessionId: this.sessionId,
        ticketId: this.ticketId,
        customerName: this.customerName,
        language: this.language,
        currentStep: this.currentStep,
        totalXp: this.totalXp,
        timestamp: Date.now()
      }));
    } catch (e) {}
  }

  restoreChatHistory(historyList) {
    if (!historyList || historyList.length === 0) return;
    const msgContainer = document.getElementById('chat-messages-container');
    if (!msgContainer) return;

    msgContainer.innerHTML = '';
    historyList.forEach(item => {
      const sender = item.role === 'user' ? 'user' : 'guide';
      const bubble = document.createElement('div');
      bubble.className = `chat-bubble ${sender}`;
      bubble.textContent = item.content;
      msgContainer.appendChild(bubble);
    });
    msgContainer.scrollTop = msgContainer.scrollHeight;
  }

  setupInterruptionListeners() {
    document.addEventListener('visibilitychange', () => {
      if (document.visibilityState === 'hidden') {
        this.hiddenTimestamp = Date.now();
      } else if (document.visibilityState === 'visible' && this.hiddenTimestamp) {
        const awayMs = Date.now() - this.hiddenTimestamp;
        this.hiddenTimestamp = null;
        if (awayMs >= 4000) {
          this.handleReturnFromInterruption();
        }
      }
    });
  }

  handleReturnFromInterruption() {
    if (this.currentStopData) {
      const returnMsg = `Welcome back, ${this.customerName}! Resuming at Stop ${this.currentStep}: ${this.currentStopData.title}.`;
      if (typeof showNotification === 'function') showNotification(returnMsg);
      if (typeof displaySubtitlesAndSpeak === 'function') {
        displaySubtitlesAndSpeak("Luna", "", returnMsg, null, false);
      }
    }
  }

  async loadBlueprint() {
    if (!this.sessionId) return;
    try {
      const [bpRes, ovRes] = await Promise.all([
        fetch(`/api/session/${this.sessionId}/blueprint`),
        fetch('/api/site/overview')
      ]);
      if (bpRes.ok) {
        const data = await bpRes.json();
        this.blueprintStops = data.stops || [];
      }
      if (ovRes.ok) {
        const ov = await ovRes.json();
        this.siteEdges = ov.edges || [];
        this.siteNodes = ov.nodes || [];
      }
      if (window.locationTracker) {
        if (this.siteNodes && this.siteNodes.length > 0) {
          window.locationTracker.loadRadiiFromApi(this.siteNodes);
        } else if (this.blueprintStops && this.blueprintStops.length > 0) {
          window.locationTracker.loadRadiiFromApi(this.blueprintStops);
        }
      }
      this.renderManualCheckinButtons();
    } catch (e) {}
  }

  renderManualCheckinButtons() {
    const grid = document.getElementById('manual-checkin-grid');
    if (!grid || !Array.isArray(this.blueprintStops) || this.blueprintStops.length === 0) return;
    grid.innerHTML = '';
    for (const s of this.blueprintStops) {
      const btn = document.createElement('button');
      const isCurrent = s.step_number === this.currentStep;
      const isVisited = this.visitedSteps.includes(s.step_number);
      const radLabel = Number.isFinite(Number(s.arrival_radius_m)) ? `${s.arrival_radius_m}m` : '';
      btn.className = 'manual-checkin-btn';
      btn.setAttribute('data-checkin-step', String(s.step_number));
      btn.style.cssText = isCurrent
        ? 'background: rgba(0,229,255,0.22); border: 1px solid #00e5ff; color: #ffffff; font-size: 0.68rem; padding: 5px 6px; border-radius: 8px; cursor: pointer;'
        : (isVisited
          ? 'background: rgba(0,230,118,0.14); border: 1px solid #00e676; color: #e0f7fa; font-size: 0.68rem; padding: 5px 6px; border-radius: 8px; cursor: pointer;'
          : 'background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.2); color: #cfd8dc; font-size: 0.68rem; padding: 5px 6px; border-radius: 8px; cursor: pointer;');
      const shortTitle = (s.title || '').split('(')[0].trim().split(' ').slice(0, 2).join(' ');
      btn.textContent = `S${s.step_number} ${shortTitle}: I'm here${radLabel ? ` (${radLabel})` : ''}`;
      btn.onclick = async (e) => {
        e.stopPropagation();
        await this.manualCheckIn(s.step_number);
      };
      grid.appendChild(btn);
    }
  }

  async manualCheckIn(stepNumber) {
    const step = Number(stepNumber);
    if (!this.sessionId) return;
    try {
      const res = await fetch('/api/session/checkin', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: this.sessionId, step_number: step })
      });
      if (res.ok) {
        const data = await res.json();
        this.currentStep = data.current_step;
        this.visitedSteps = data.visited_steps || this.visitedSteps;
        this.totalXp = data.total_xp;
        this.currentStopData = data.stop;
        this.saveToStorage();

        if (window.locationTracker) {
          window.locationTracker.teleportToStop(step, false);
        }
        if (window.arScene) window.arScene.hideRelicModel();
        const eraPanel = document.getElementById('era-reconstruction-panel');
        if (eraPanel) eraPanel.style.display = 'none';

        this.updateTopHUD();
        this.renderManualCheckinButtons();
        this.playCurrentStopNarration();
        if (typeof renderInteractiveBlueprintMap === 'function') {
          await renderInteractiveBlueprintMap();
        }
        if (typeof showNotification === 'function') {
          showNotification(`📍 Checked in at Stop ${step}: ${data.stop.title}`);
        }
      }
    } catch (e) {
      console.warn("Manual check-in error:", e);
    }
  }

  updateTopHUD() {
    const stopLabel = document.getElementById('tour-stop-label');
    if (stopLabel && this.currentStopData) {
      stopLabel.textContent = `Stop ${this.currentStep}/7: ${this.currentStopData.title}`;
    }

    const xpBadge = document.getElementById('user-points-badge');
    if (xpBadge) xpBadge.textContent = `${this.totalXp} XP`;

    const guidanceMeta = document.getElementById('next-stop-meta');
    if (guidanceMeta && this.currentStopData) {
      const nextPart = (this.currentStopData.distance_to_next || 0) > 0
        ? `Next: ~${this.currentStopData.distance_to_next}m (${this.currentStopData.walking_time_mins} min) • ${this.currentStopData.shade_rating}`
        : `Final Stop (7/7) • ${this.currentStopData.shade_rating}`;
      guidanceMeta.textContent = `${nextPart} | One-way trail: 4.13 km (~59 min walk)`;
    }
  }

  playCurrentStopNarration() {
    if (!this.currentStopData) return;
    this.hasPlayedInitialWelcome = true;
    const spokenText = this.currentStopData.personalized_welcome;
    displaySubtitlesAndSpeak("Luna", "", spokenText, this.currentStopData.audio_url, true);
  }

  async advanceToNextStop() {
    if (!this.sessionId) return;
    if (typeof showNotification === 'function') showNotification("Advancing to next Mahabalipuram station...");

    try {
      const res = await fetch('/api/session/advance', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: this.sessionId })
      });

      if (res.ok) {
        const data = await res.json();
        if (data.status === 'completed') {
          this.showTourCertificate(data);
          return;
        }

        this.currentStep = data.current_step;
        if (!this.visitedSteps.includes(this.currentStep)) this.visitedSteps.push(this.currentStep);
        this.totalXp = data.total_xp;
        this.currentStopData = data.stop;
        this.saveToStorage();

        if (window.locationTracker) {
          window.locationTracker.syncToCurrentStop();
        }
        if (window.arScene) {
          window.arScene.hideRelicModel();
          const eraPanel = document.getElementById('era-reconstruction-panel');
          if (eraPanel) eraPanel.style.display = 'none';
        }

        await this.loadBlueprint();
        this.updateTopHUD();
        this.playCurrentStopNarration();

        const mapModal = document.getElementById('modal-map');
        if (mapModal && mapModal.classList.contains('open')) {
          await renderInteractiveBlueprintMap();
        }
        if (typeof showNotification === 'function') {
          showNotification(`✨ Stop ${this.currentStep}: ${data.stop.title} (+75 XP)`);
        }
      }
    } catch (e) {
      console.warn("Advance stop error:", e);
    }
  }

  openCurrentStopRiddle() {
    const modal = document.getElementById('modal-riddle');
    if (!modal || !this.currentStopData) return;

    const riddle = this.currentStopData.riddle;
    document.getElementById('riddle-stop-title').textContent = `Stop ${this.currentStep}: ${this.currentStopData.title}`;
    const qEl = document.getElementById('riddle-question-text');
    const optsEl = document.getElementById('riddle-options-container');
    const fbEl = document.getElementById('riddle-feedback');
    fbEl.textContent = '';
    optsEl.innerHTML = '';

    if (!riddle || !riddle.question) {
      qEl.textContent = "Complete more stops to unlock a historical chronicle challenge.";
    } else {
      qEl.textContent = riddle.question;
      (riddle.options || []).forEach(opt => {
        const btn = document.createElement('button');
        btn.className = 'riddle-opt-btn';
        btn.textContent = opt;
        btn.onclick = () => this.submitRiddleAnswer(opt, fbEl);
        optsEl.appendChild(btn);
      });
    }
    modal.classList.add('open');
  }

  async submitRiddleAnswer(selectedAnswer, fbEl) {
    if (!this.sessionId) return;
    try {
      const res = await fetch('/api/session/riddle', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: this.sessionId,
          step_number: this.currentStep,
          answer: selectedAnswer
        })
      });
      if (res.ok) {
        const data = await res.json();
        this.totalXp = data.total_xp;
        this.solvedRiddles = data.solved_riddles || this.solvedRiddles;
        this.unlockedBadges = data.unlocked_badges || this.unlockedBadges;
        this.updateTopHUD();
        this.saveToStorage();
        if (data.correct) {
          fbEl.style.color = '#00e676';
          fbEl.textContent = data.newly_solved
            ? `✓ Correct! Unlocked Chronicle Solver badge (+${data.xp_awarded} XP).`
            : `✓ Correct! You already mastered this station riddle.`;
        } else {
          fbEl.style.color = '#ff5252';
          fbEl.textContent = `✗ Close! Hint: Think about 8th-century Pallava coastal heritage.`;
        }
      }
    } catch (e) {}
  }

  async snapMemoryPhoto() {
    const video = document.getElementById('camera-video');
    const threeCanvas = document.getElementById('three-canvas');
    const offscreen = document.createElement('canvas');
    const w = 720;
    const h = 480;
    offscreen.width = w;
    offscreen.height = h;
    const ctx = offscreen.getContext('2d');

    ctx.fillStyle = '#070b12';
    ctx.fillRect(0, 0, w, h);

    if (video && video.readyState >= 2) {
      ctx.drawImage(video, 0, 0, w, h);
    }
    if (threeCanvas) {
      try { ctx.drawImage(threeCanvas, 0, 0, w, h); } catch (e) {}
    }

    // Heritage Stamp Watermark
    ctx.fillStyle = 'rgba(7, 11, 18, 0.78)';
    ctx.fillRect(0, h - 54, w, 54);
    ctx.fillStyle = '#f4c430';
    ctx.font = 'bold 18px sans-serif';
    const title = this.currentStopData ? this.currentStopData.title : "Mahabalipuram Shore Temple";
    ctx.fillText(`LUNAR AURORA • ${title}`, 18, h - 26);
    ctx.fillStyle = '#00e5ff';
    ctx.font = '13px sans-serif';
    ctx.fillText(`${this.customerName} | Ticket #${this.ticketId || 'LUNA'} | Stop ${this.currentStep}/7`, 18, h - 8);

    const dataUrl = offscreen.toDataURL('image/jpeg', 0.86);
    const stopTitle = this.currentStopData ? this.currentStopData.title : "Shore Temple";
    this.localPhotos.push({ stop_title: stopTitle, image_base64: dataUrl, captured_at: new Date().toISOString() });

    if (this.sessionId) {
      try {
        const res = await fetch(`/api/tour/${this.sessionId}/photo`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            stop_step: this.currentStep,
            stop_title: stopTitle,
            image_base64: dataUrl
          })
        });
        if (res.ok) {
          const d = await res.json();
          this.totalXp = d.total_xp;
          this.updateTopHUD();
        }
      } catch (e) {}
    }
    if (typeof showNotification === 'function') {
      showNotification(`📸 AR Memory saved to your Travel Journal! (+20 XP)`);
    }
  }

  async downloadPdfJournal() {
    if (!this.sessionId) return;
    if (typeof showNotification === 'function') showNotification("Generating PDF Travel Journal...");
    try {
      const res = await fetch(`/api/tour/${this.sessionId}/journal`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ photos: this.localPhotos })
      });
      if (res.ok) {
        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `LunarAurora_Journal_${this.ticketId || this.sessionId.slice(0, 6)}.pdf`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        setTimeout(() => URL.revokeObjectURL(url), 4000);
      }
    } catch (e) {
      if (typeof showNotification === 'function') showNotification("Unable to download PDF right now.");
    }
  }

  async endTourEarly() {
    if (window.spatialAudio) window.spatialAudio.stopSpeech();
    try {
      const res = await fetch('/api/session/end', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: this.sessionId })
      });
      if (res.ok) {
        const data = await res.json();
        this.showTourCertificate(data);
      }
    } catch (e) {
      console.warn("End tour error:", e);
    }
  }

  showTourCertificate(summary) {
    const certModal = document.getElementById('modal-certificate');
    if (!certModal) return;

    document.getElementById('cert-name').textContent = summary.customer_name;
    document.getElementById('cert-ticket').textContent = summary.ticket_id || this.ticketId;
    document.getElementById('cert-stops').textContent = `${summary.stops_completed || this.currentStep} of ${summary.total_stops || 7} Stations`;
    document.getElementById('cert-xp').textContent = `${summary.total_xp} Total XP`;
    document.getElementById('cert-farewell').textContent = summary.farewell_message;

    certModal.classList.add('open');

    if (summary.audio_url && window.spatialAudio) {
      window.spatialAudio.playSpeech(summary.audio_url, null, null);
    }

    try { localStorage.removeItem(this.STORAGE_KEY); } catch (e) {}
  }
}

async function renderInteractiveBlueprintMap(targetOverrideId = null) {
  const svg = document.getElementById('shade-map-svg');
  const badge = document.getElementById('shade-savings-badge');
  const tm = window.tourManager;
  if (!svg || !tm) return;

  if (!tm.shadeMapRenderer && window.ShadeMapRenderer) {
    tm.shadeMapRenderer = new window.ShadeMapRenderer(svg, badge);
  }
  if (!tm.shadeMapRenderer) return;

  if (tm.siteNodes && tm.siteEdges) {
    tm.shadeMapRenderer.setSiteGeometry(tm.siteNodes, tm.siteEdges);
  }

  const startId = (tm.currentStopData && tm.currentStopData.poi_id) || tm.currentStep || 1;
  const targetId = targetOverrideId || (tm.currentStep < 7 ? 7 : 6);
  const simHour = window.locationTracker && window.locationTracker.simulatedHour !== null
    ? `&hour=${window.locationTracker.simulatedHour}`
    : '';
  const simDate = (window.locationTracker && window.locationTracker.simulatedDate) || '2027-01-11';

  try {
    const res = await fetch(`/api/site/telemetry?start_id=${startId}&target_id=${targetId}&date=${encodeURIComponent(simDate)}${simHour}`);
    if (res.ok) {
      const tel = await res.json();
      tm.shadeMapRenderer.setTelemetry(tel);
      const detail = document.getElementById('map-route-detail');
      if (detail) {
        detail.innerHTML =
          `<span style="color:#ff5252;">Shortest OSM Walk: ${tel.shortest_path.total_distance_meters}m (avg assumed shade ${tel.shortest_path.average_shade_index})</span> vs ` +
          `<span style="color:#00e676;">Assumed-Shade Route: ${tel.shaded_path.total_distance_meters}m (avg assumed shade ${tel.shaded_path.average_shade_index})</span> ` +
          `<span style="color:#b0bec5;">(illustrative weights, not measured sun)</span>`;
      }
    }
  } catch (e) {}

  tm.shadeMapRenderer.setProgress({
    currentStep: tm.currentStep,
    visitedSteps: tm.visitedSteps,
    playerPos: window.locationTracker
      ? { x: window.locationTracker.userSiteX, y: window.locationTracker.userSiteY }
      : { x: 0, y: 0 }
  });
}

window.renderInteractiveBlueprintMap = renderInteractiveBlueprintMap;
window.tourManager = new TourManager();
