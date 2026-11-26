/**
 * Tour Manager for Lunar Aurora
 * Manages personalized visitor sessions, 7-stop curated blueprint progression,
 * real phone-call / browser-close recovery, chat history restoration, and adaptive blueprint maps.
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
    this.unlockedBadges = [];
    this.totalXp = 50;
    this.blueprintStops = [];
    this.currentStopData = null;
    this.activeShadedPathIds = null;
    this.hiddenTimestamp = null;
    this.hasPlayedInitialWelcome = false;

    this.STORAGE_KEY = "lunar_aurora_session";
  }

  async init() {
    console.log("[TourManager] Initializing visitor tour session...");

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

    // If QR scan brings a new ticket/session, prefer URL params; otherwise resume saved session
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
        this.unlockedBadges = data.unlocked_badges || [];
        this.totalXp = data.total_xp || 50;
        this.currentStopData = data.current_stop;

        // Sync global language everywhere
        window.currentLanguage = this.language;
        const langSelect = document.getElementById('lang-select');
        if (langSelect) langSelect.value = this.language;

        this.saveToStorage();
        this.restoreChatHistory(data.chat_history || []);
        await this.loadBlueprint();
        this.updateTopHUD();

        // Sync GPS simulator if indoors
        if (window.locationTracker) {
          window.locationTracker.syncToCurrentStop();
        }

        // If returning to an already-started tour (closed tab / reopened), show welcome banner
        if (savedSession && savedSession.sessionId === this.sessionId && (this.currentStep > 1 || (data.chat_history || []).length > 0)) {
          if (typeof showNotification === 'function') {
            showNotification(`Welcome back, ${this.customerName}! Resuming Stop ${this.currentStep}.`);
          }
        }

        console.log(`[TourManager] Session ready for ${this.customerName} (${this.language}) at Stop ${this.currentStep}.`);
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
    // Only trigger resume notification if page was genuinely hidden >= 4 seconds (phone call / app switch)
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
      const stopTitle = this.currentStopData.title;
      const returnMsg = `Welcome back, ${this.customerName}! Resuming at Stop ${this.currentStep}: ${stopTitle}.`;
      if (typeof showNotification === 'function') showNotification(returnMsg);
      if (typeof displaySubtitlesAndSpeak === 'function') {
        displaySubtitlesAndSpeak("Luna", "", returnMsg, null, false);
      }
    }
  }

  async loadBlueprint() {
    if (!this.sessionId) return;
    try {
      const res = await fetch(`/api/session/${this.sessionId}/blueprint`);
      if (res.ok) {
        const data = await res.json();
        this.blueprintStops = data.stops || [];
      }
    } catch (e) {}
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
      guidanceMeta.textContent = `Next: ~${this.currentStopData.distance_to_next}m (${this.currentStopData.walking_time_mins} min) • ${this.currentStopData.shade_rating}`;
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
    this.activeShadedPathIds = null;
    if (typeof showNotification === 'function') showNotification(`Advancing to next station...`);

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
        this.totalXp = data.total_xp;
        this.currentStopData = data.stop;
        this.saveToStorage();

        if (window.locationTracker) {
          window.locationTracker.syncToCurrentStop();
        }

        await this.loadBlueprint();
        this.updateTopHUD();
        this.playCurrentStopNarration();

        const mapModal = document.getElementById('modal-map');
        if (mapModal && mapModal.classList.contains('open')) {
          renderInteractiveBlueprintMap();
        }
        if (typeof showNotification === 'function') {
          showNotification(`✨ Stop ${this.currentStep}: ${data.stop.title} (+75 XP)`);
        }
      }
    } catch (e) {
      console.warn("Advance stop error:", e);
    }
  }

  async endTourEarly() {
    if (!confirm(`Conclude your tour now, ${this.customerName}?`)) return;
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

    try {
      localStorage.removeItem(this.STORAGE_KEY);
    } catch (e) {}
  }
}

/**
 * Dynamically scales & centers the 7-station blueprint onto any screen width,
 * and highlights either the active tour leg or a requested Shaded Rest Route.
 */
function renderInteractiveBlueprintMap(shadedPathIds = null) {
  const canvas = document.getElementById('map-canvas');
  if (!canvas || !window.tourManager || !window.tourManager.blueprintStops || window.tourManager.blueprintStops.length === 0) return;

  if (shadedPathIds) {
    window.tourManager.activeShadedPathIds = shadedPathIds;
  }
  const activeShadeRoute = shadedPathIds || window.tourManager.activeShadedPathIds;

  const ctx = canvas.getContext('2d');
  const w = canvas.width = canvas.clientWidth || 320;
  const h = canvas.height = canvas.clientHeight || 300;
  const stops = window.tourManager.blueprintStops;
  const currentStep = window.tourManager.currentStep;

  ctx.clearRect(0, 0, w, h);

  // Blueprint grid
  ctx.strokeStyle = 'rgba(0, 229, 255, 0.08)';
  ctx.lineWidth = 1;
  for (let x = 0; x < w; x += 25) {
    ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, h); ctx.stroke();
  }
  for (let y = 0; y < h; y += 25) {
    ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(w, y); ctx.stroke();
  }

  // Compute dynamic bounding box so labels never clip off screen
  const xs = stops.map(s => s.x);
  const ys = stops.map(s => s.y);
  const minX = Math.min(...xs);
  const maxX = Math.max(...xs);
  const minY = Math.min(...ys);
  const maxY = Math.max(...ys);

  const padLeft = 42;
  const padRight = 95; // Extra room for station labels on right
  const padY = 36;
  const spanX = Math.max(1, maxX - minX);
  const spanY = Math.max(1, maxY - minY);
  const scale = Math.min((w - padLeft - padRight) / spanX, (h - padY * 2) / spanY);

  const toScreen = (x, y) => ({
    x: padLeft + (x - minX) * scale,
    y: h - padY - (y - minY) * scale
  });

  // 1. Draw sequential tour paths (1 -> 2 -> ... -> 7)
  for (let i = 0; i < stops.length - 1; i++) {
    const s1 = stops[i];
    const s2 = stops[i + 1];
    const p1 = toScreen(s1.x, s1.y);
    const p2 = toScreen(s2.x, s2.y);

    const isCurrentLeg = (s1.step_number === currentStep && s2.step_number === currentStep + 1);
    const isPastLeg = (s2.step_number <= currentStep);

    ctx.beginPath();
    ctx.moveTo(p1.x, p1.y);
    ctx.lineTo(p2.x, p2.y);

    if (isCurrentLeg && !activeShadeRoute) {
      ctx.lineWidth = 4.5;
      ctx.strokeStyle = '#00e5ff';
      ctx.shadowColor = '#00e5ff';
      ctx.shadowBlur = 10;
      ctx.stroke();
      ctx.shadowBlur = 0;
    } else if (isPastLeg) {
      ctx.lineWidth = 3;
      ctx.strokeStyle = 'rgba(0, 230, 118, 0.55)';
      ctx.stroke();
    } else {
      ctx.lineWidth = 2;
      ctx.setLineDash([4, 4]);
      ctx.strokeStyle = 'rgba(139, 162, 189, 0.35)';
      ctx.stroke();
      ctx.setLineDash([]);
    }
  }

  // 2. Highlight Shaded Rest Route if requested via SHADE button
  if (activeShadeRoute && activeShadeRoute.length >= 2) {
    ctx.beginPath();
    for (let i = 0; i < activeShadeRoute.length; i++) {
      const nodeStop = stops.find(s => (s.poi_id || s.step_number) === activeShadeRoute[i]);
      if (!nodeStop) continue;
      const pt = toScreen(nodeStop.x, nodeStop.y);
      if (i === 0) ctx.moveTo(pt.x, pt.y);
      else ctx.lineTo(pt.x, pt.y);
    }
    ctx.lineWidth = 6;
    ctx.strokeStyle = '#00e676';
    ctx.shadowColor = '#00e676';
    ctx.shadowBlur = 14;
    ctx.stroke();
    ctx.shadowBlur = 0;
  }

  // 3. Draw Stop Stations
  stops.forEach(s => {
    const pt = toScreen(s.x, s.y);
    const isCurrent = (s.step_number === currentStep);
    const isVisited = s.is_visited;
    const isShadeDest = activeShadeRoute && activeShadeRoute[activeShadeRoute.length - 1] === (s.poi_id || s.step_number);

    ctx.beginPath();
    ctx.arc(pt.x, pt.y, isCurrent || isShadeDest ? 12 : 9, 0, Math.PI * 2);

    if (isShadeDest) {
      ctx.fillStyle = '#00e676';
      ctx.shadowColor = '#00e676';
      ctx.shadowBlur = 14;
      ctx.fill();
      ctx.shadowBlur = 0;
      ctx.strokeStyle = '#ffffff';
      ctx.lineWidth = 2.5;
      ctx.stroke();
    } else if (isCurrent) {
      ctx.fillStyle = '#f4c430';
      ctx.shadowColor = '#f4c430';
      ctx.shadowBlur = 14;
      ctx.fill();
      ctx.shadowBlur = 0;
      ctx.strokeStyle = '#ffffff';
      ctx.lineWidth = 2.5;
      ctx.stroke();
    } else if (isVisited) {
      ctx.fillStyle = '#00e676';
      ctx.fill();
      ctx.strokeStyle = '#ffffff';
      ctx.lineWidth = 1.5;
      ctx.stroke();
    } else {
      ctx.fillStyle = '#1c283d';
      ctx.fill();
      ctx.strokeStyle = '#00e5ff';
      ctx.lineWidth = 1.5;
      ctx.stroke();
    }

    ctx.fillStyle = (isCurrent || isShadeDest) ? '#000000' : '#ffffff';
    ctx.font = (isCurrent || isShadeDest) ? 'bold 10px sans-serif' : '10px sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(isVisited && !isCurrent ? '✓' : `${s.step_number}`, pt.x, pt.y);

    // Label placement clamped cleanly inside canvas
    const shortTitle = s.title.length > 16 ? s.title.slice(0, 15) + '…' : s.title;
    ctx.fillStyle = isCurrent ? '#f4c430' : (isShadeDest ? '#00e676' : (isVisited ? '#e0e0e0' : '#8ba2bd'));
    ctx.font = (isCurrent || isShadeDest) ? 'bold 10px sans-serif' : '9px sans-serif';
    ctx.textAlign = 'left';
    ctx.fillText(shortTitle, pt.x + 15, pt.y);
  });

  // 4. Draw Live GPS Position Marker
  if (window.locationTracker && window.locationTracker.hasGpsFix) {
    const gpsPt = toScreen(window.locationTracker.userSiteX, window.locationTracker.userSiteY);

    ctx.beginPath();
    ctx.arc(gpsPt.x, gpsPt.y, Math.min(32, Math.max(10, window.locationTracker.accuracyMeters * scale * 0.6)), 0, Math.PI * 2);
    ctx.fillStyle = 'rgba(0, 229, 255, 0.16)';
    ctx.fill();
    ctx.strokeStyle = 'rgba(0, 229, 255, 0.5)';
    ctx.lineWidth = 1;
    ctx.stroke();

    ctx.beginPath();
    ctx.arc(gpsPt.x, gpsPt.y, 5.5, 0, Math.PI * 2);
    ctx.fillStyle = '#00e5ff';
    ctx.shadowColor = '#00e5ff';
    ctx.shadowBlur = 10;
    ctx.fill();
    ctx.shadowBlur = 0;
    ctx.strokeStyle = '#ffffff';
    ctx.lineWidth = 2;
    ctx.stroke();
  }
}

window.renderInteractiveBlueprintMap = renderInteractiveBlueprintMap;
window.tourManager = new TourManager();
