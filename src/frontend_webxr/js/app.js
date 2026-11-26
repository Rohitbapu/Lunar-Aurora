/**
 * Master Application Controller for Lunar Aurora Mobile WebXR (Mahabalipuram Edition)
 */
let chatHistory = [];
let audioUnlocked = false;
let subtitleFallbackTimer = null;
let speechRecognition = null;
let gpsTapCount = 0;
let gpsTapTimer = null;

document.addEventListener('DOMContentLoaded', async () => {
  console.log("[LunarAurora] Booting up Mahabalipuram WebXR experience...");
  setupUI();

  try {
    window.arScene.init('ar-viewport-container');
  } catch (e) {
    console.error("[LunarAurora] Three.js init error:", e);
  }

  if (window.tourManager) {
    await window.tourManager.init();
    window.tourManager.setupInterruptionListeners();
    if (window.tourManager.currentStopData) {
      displaySubtitlesAndSpeak("Luna", "", window.tourManager.currentStopData.personalized_welcome, null, false);
    }
  }

  const params = new URLSearchParams(window.location.search);
  const isDemoQuery = params.get('demo') === '1';

  if (window.locationTracker) {
    window.locationTracker.onLocationUpdated = (gpsData) => {
      const gpsLabel = document.getElementById('gps-coords-label');
      if (gpsLabel) {
        gpsLabel.textContent = window.locationTracker.isSimulated
          ? `DEMO MODE (±${gpsData.accuracy}m)`
          : `GPS: ±${gpsData.accuracy}m`;
      }
      const mapModal = document.getElementById('modal-map');
      if (mapModal && mapModal.classList.contains('open') && window.renderInteractiveBlueprintMap) {
        window.renderInteractiveBlueprintMap();
      }
    };

    window.locationTracker.onStopArrived = (stop, dist) => {
      showNotification(`📍 Arrived near ${stop.name} (${dist}m)!`);
    };

    if (isDemoQuery) {
      window.locationTracker.activateDemoMode((window.tourManager && window.tourManager.currentStep) || 1);
    } else {
      window.locationTracker.checkPermissionStatus();
    }
  }

  // Auto-open Demo Mode drawer if ?demo=1 in URL
  if (isDemoQuery) {
    const drawer = document.getElementById('jury-demo-drawer');
    if (drawer) drawer.style.display = 'block';
  }

  fetchScavengerQuests();
  checkSecurityAndCamera();
});

function setupUI() {
  const unlockAudioAndSensors = async () => {
    if (!audioUnlocked && window.spatialAudio) {
      await window.spatialAudio.resumeOnUserGesture();
      audioUnlocked = true;
      if (window.tourManager && !window.tourManager.hasPlayedInitialWelcome) {
        window.tourManager.playCurrentStopNarration();
      }
    }
    if (window.arScene) {
      window.arScene.enableOrientationTracking();
    }
    if (window.locationTracker && !window.locationTracker.hasGpsFix) {
      window.locationTracker.requestGpsFix(true);
    }
  };
  document.body.addEventListener('click', unlockAudioAndSensors, { once: true });
  document.body.addEventListener('touchstart', unlockAudioAndSensors, { once: true });

  // GPS Pill: Tap once = GPS fix; Triple-tap = Jury Table Demo Mode
  const gpsPill = document.getElementById('gps-status-pill');
  if (gpsPill) {
    gpsPill.addEventListener('click', (e) => {
      e.stopPropagation();
      gpsTapCount++;
      clearTimeout(gpsTapTimer);
      gpsTapTimer = setTimeout(() => { gpsTapCount = 0; }, 750);

      if (gpsTapCount >= 3) {
        gpsTapCount = 0;
        const drawer = document.getElementById('jury-demo-drawer');
        if (drawer) {
          const opening = drawer.style.display === 'none';
          drawer.style.display = opening ? 'block' : 'none';
          if (opening && window.locationTracker) {
            window.locationTracker.activateDemoMode((window.tourManager && window.tourManager.currentStep) || 1);
          }
          showNotification("🎛️ DEMO MODE toggled");
        }
        return;
      }

      if (window.locationTracker) window.locationTracker.requestGpsFix(true);
    });
  }

  // Jury Demo Drawer controls
  const closeDemoBtn = document.getElementById('btn-close-demo-drawer');
  if (closeDemoBtn) {
    closeDemoBtn.addEventListener('click', () => {
      document.getElementById('jury-demo-drawer').style.display = 'none';
    });
  }

  document.querySelectorAll('.demo-stop-btn[data-step]').forEach(btn => {
    btn.addEventListener('click', async (e) => {
      e.stopPropagation();
      const step = Number(btn.getAttribute('data-step'));
      if (window.locationTracker) window.locationTracker.teleportToStop(step, true);
      if (window.tourManager) {
        window.tourManager.currentStep = step;
        if (!window.tourManager.visitedSteps.includes(step)) window.tourManager.visitedSteps.push(step);
        const matchStop = window.tourManager.blueprintStops.find(s => s.step_number === step);
        if (matchStop) {
          window.tourManager.currentStopData = {
            ...window.tourManager.currentStopData,
            ...matchStop
          };
        }
        window.tourManager.updateTopHUD();
        window.tourManager.renderManualCheckinButtons();
        await renderInteractiveBlueprintMap();
      }
    });
  });

  const demoHourSlider = document.getElementById('demo-hour-slider');
  const demoHourLabel = document.getElementById('demo-hour-label');
  const demoDateInput = document.getElementById('demo-date-input');
  const mapHourSlider = document.getElementById('map-hour-slider');
  const mapHourLabel = document.getElementById('map-hour-label');
  const mapDateInput = document.getElementById('map-date-input');

  async function syncSolarTimeControls(hr, dateVal) {
    const clampedHr = Math.max(0, Math.min(24, parseFloat(hr)));
    const hh = Math.floor(clampedHr);
    const mm = clampedHr % 1 >= 0.5 ? '30' : '00';
    const timeLabel = `${String(hh).padStart(2, '0')}:${mm}`;
    const effDate = dateVal || (window.locationTracker && window.locationTracker.simulatedDate) || '2027-01-11';

    if (demoHourLabel) demoHourLabel.textContent = timeLabel;
    if (mapHourLabel) mapHourLabel.textContent = timeLabel;
    if (demoHourSlider) demoHourSlider.value = String(clampedHr);
    if (mapHourSlider) mapHourSlider.value = String(clampedHr);
    if (demoDateInput && demoDateInput.value !== effDate) demoDateInput.value = effDate;
    if (mapDateInput && mapDateInput.value !== effDate) mapDateInput.value = effDate;

    if (window.locationTracker) {
      window.locationTracker.simulatedHour = clampedHr;
      window.locationTracker.simulatedDate = effDate;
    }
    const mapModal = document.getElementById('modal-map');
    if (mapModal && mapModal.classList.contains('open')) {
      await renderInteractiveBlueprintMap();
    }
  }

  if (demoHourSlider) {
    demoHourSlider.addEventListener('input', () => syncSolarTimeControls(demoHourSlider.value, demoDateInput ? demoDateInput.value : null));
  }
  if (mapHourSlider) {
    mapHourSlider.addEventListener('input', () => syncSolarTimeControls(mapHourSlider.value, mapDateInput ? mapDateInput.value : null));
  }
  if (demoDateInput) {
    demoDateInput.addEventListener('change', () => syncSolarTimeControls(demoHourSlider ? demoHourSlider.value : 12, demoDateInput.value));
  }
  if (mapDateInput) {
    mapDateInput.addEventListener('change', () => syncSolarTimeControls(mapHourSlider ? mapHourSlider.value : 12, mapDateInput.value));
  }

  const demo3dBtn = document.getElementById('btn-demo-inspect-3d');
  if (demo3dBtn) {
    demo3dBtn.addEventListener('click', () => openCurrentReconstruction());
  }

  // Toggleable [3D GUIDE] corner avatar
  const btnGuide = document.getElementById('btn-toggle-3d-guide');
  if (btnGuide) {
    btnGuide.addEventListener('click', (e) => {
      e.stopPropagation();
      if (!window.arScene) return;
      const active = window.arScene.toggleGuideAvatar();
      btnGuide.classList.toggle('active', active);
      showNotification(active ? "🧊 3D Hologram Guide ON" : "3D Guide hidden (Camera clear)");
    });
  }

  // Stop Riddle Challenge
  const btnRiddle = document.getElementById('btn-open-riddle');
  if (btnRiddle) {
    btnRiddle.addEventListener('click', (e) => {
      e.stopPropagation();
      if (window.tourManager) window.tourManager.openCurrentStopRiddle();
    });
  }

  // AR Memory Snapshot
  const btnSnap = document.getElementById('btn-snap-memory');
  if (btnSnap) {
    btnSnap.addEventListener('click', async (e) => {
      e.stopPropagation();
      if (window.tourManager) await window.tourManager.snapMemoryPhoto();
    });
  }

  // Era Slider & Close (wire both input and change for mobile touch sliders)
  const eraSlider = document.getElementById('era-slider-input');
  if (eraSlider) {
    const onEraChange = () => {
      if (window.arScene) window.arScene.setEraFactor(Number(eraSlider.value) / 100.0);
    };
    eraSlider.addEventListener('input', onEraChange);
    eraSlider.addEventListener('change', onEraChange);
  }
  const closeEraBtn = document.getElementById('btn-close-era-panel');
  if (closeEraBtn) {
    closeEraBtn.addEventListener('click', () => {
      document.getElementById('era-reconstruction-panel').style.display = 'none';
      if (window.arScene) window.arScene.hideRelicModel();
    });
  }
  const closeInfoBtn = document.getElementById('btn-close-relic-info');
  if (closeInfoBtn) {
    closeInfoBtn.addEventListener('click', () => {
      document.getElementById('relic-info-panel').style.display = 'none';
    });
  }

  // Primary Bottom Dock actions
  const btnScanRelic = document.getElementById('btn-scan-relic');
  if (btnScanRelic) {
    btnScanRelic.addEventListener('click', async (e) => {
      e.stopPropagation();
      await handleScanRelicClick();
    });
  }

  const btnAdvance = document.getElementById('btn-advance-stop');
  if (btnAdvance) {
    btnAdvance.addEventListener('click', async (e) => {
      e.stopPropagation();
      if (window.tourManager) await window.tourManager.advanceToNextStop();
    });
  }

  const btnImHere = document.getElementById('btn-im-here-current');
  if (btnImHere) {
    btnImHere.addEventListener('click', async (e) => {
      e.stopPropagation();
      if (window.tourManager) await window.tourManager.manualCheckIn(window.tourManager.currentStep);
    });
  }

  const restBtn = document.getElementById('btn-take-rest');
  if (restBtn) {
    restBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      handleTakeARest();
    });
  }

  const btnMute = document.getElementById('btn-mute-speech');
  if (btnMute) {
    btnMute.addEventListener('click', (e) => {
      e.stopPropagation();
      if (window.spatialAudio) window.spatialAudio.stopSpeech();
      clearSubtitleTimers();
      const container = document.getElementById('yt-subtitle-container');
      if (container) container.classList.remove('active');
    });
  }

  const btnEndTourTop = document.getElementById('btn-end-tour-top');
  if (btnEndTourTop) {
    btnEndTourTop.addEventListener('click', (e) => {
      e.stopPropagation();
      if (window.tourManager) window.tourManager.endTourEarly();
    });
  }

  const btnDownloadPdf = document.getElementById('btn-download-journal');
  if (btnDownloadPdf) {
    btnDownloadPdf.addEventListener('click', async () => {
      if (window.tourManager) await window.tourManager.downloadPdfJournal();
    });
  }

  const btnRestart = document.getElementById('btn-restart-tour');
  if (btnRestart) {
    btnRestart.addEventListener('click', () => {
      window.location.href = window.location.pathname;
    });
  }

  setupModal('btn-open-chat', 'modal-chat', 'btn-close-chat');
  setupModal('btn-open-map-top', 'modal-map', 'btn-close-map');
  setupModal('btn-open-scavenger', 'modal-scavenger', 'btn-close-scavenger');
  setupModal(null, 'modal-riddle', 'btn-close-riddle');

  const langSelect = document.getElementById('lang-select');
  if (langSelect) {
    langSelect.addEventListener('change', (e) => {
      const newLang = e.target.value;
      window.currentLanguage = newLang;
      if (window.tourManager) {
        window.tourManager.language = newLang;
        window.tourManager.saveToStorage();
      }
      showNotification(`Language: ${e.target.options[e.target.selectedIndex].text}`);
    });
  }

  document.querySelectorAll('.quick-q-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      const q = btn.getAttribute('data-q');
      const input = document.getElementById('chat-input-text');
      if (input) {
        input.value = q;
        submitChatMessage();
      }
    });
  });

  setupVoiceMicButton();

  const chatSendBtn = document.getElementById('btn-chat-send');
  const chatInput = document.getElementById('chat-input-text');
  if (chatSendBtn && chatInput) {
    chatSendBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      submitChatMessage();
    });
    chatInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') submitChatMessage();
    });
  }

  const btnEnableCam = document.getElementById('btn-enable-camera');
  if (btnEnableCam) {
    btnEnableCam.addEventListener('click', async (e) => {
      e.stopPropagation();
      await requestCameraPermission();
    });
  }
}

function openCurrentReconstruction(title = null, modelUrl = null, latencyMs = null) {
  const stopData = window.tourManager && window.tourManager.currentStopData;
  const resolvedTitle = title || (stopData && stopData.title) || 'Mahabalipuram Monument';
  const relicCode = (stopData && stopData.target_relic_code) || null;

  const eraPanel = document.getElementById('era-reconstruction-panel');
  if (eraPanel) eraPanel.style.display = 'none';
  if (window.arScene) window.arScene.hideRelicModel();

  const cardImageMap = {
    shore_temple_vimana: '/static/cards/01_shore_temple_vimana.jpg',
    pancha_rathas: '/static/cards/02_pancha_rathas.jpg',
    arjunas_penance: '/static/cards/03_arjunas_penance.jpg',
    krishnas_butter_ball: '/static/cards/04_krishnas_butter_ball.jpg',
    mahishasuramardini_cave: '/static/cards/05_mahishasuramardini_cave.jpg'
  };

  showRelicPhotoInfoPanel({
    name: resolvedTitle,
    period: (stopData && stopData.era) || '7th-8th century CE',
    style: (stopData && stopData.subtitle) || 'Mahabalipuram Heritage Monument',
    story: (stopData && stopData.script_details) || 'Verified Mahabalipuram historical notes.',
    image_url: relicCode ? (cardImageMap[relicCode] || null) : null,
    source: stopData && stopData.source
  }, latencyMs);
}

function showRelicPhotoInfoPanel(art, latencyMs = null) {
  const panel = document.getElementById('relic-info-panel');
  if (!panel || !art) return;
  document.getElementById('relic-info-title').textContent = art.name || 'Mahabalipuram Monument';
  document.getElementById('relic-info-latency').textContent = latencyMs ? `(${latencyMs} ms)` : '';
  document.getElementById('relic-info-meta').textContent = [art.period, art.style].filter(Boolean).join(' • ');
  document.getElementById('relic-info-story').textContent = art.story || '';

  const imgEl = document.getElementById('relic-info-photo');
  if (imgEl) {
    if (art.image_url) {
      imgEl.src = art.image_url;
      imgEl.style.display = 'block';
    } else {
      imgEl.removeAttribute('src');
      imgEl.style.display = 'none';
    }
  }

  const srcEl = document.getElementById('relic-info-source');
  if (srcEl) {
    if (art.source) {
      srcEl.href = art.source;
      srcEl.style.display = 'inline-block';
    } else {
      srcEl.style.display = 'none';
    }
  }
  panel.style.display = 'block';
}

function setupVoiceMicButton() {
  const micBtn = document.getElementById('btn-mic-speak');
  if (!micBtn) return;
  const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRec) {
    micBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      showNotification("Voice mic unsupported in this browser; please type below.");
    });
    return;
  }

  micBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    if (window.spatialAudio) window.spatialAudio.stopSpeech();
    try {
      speechRecognition = new SpeechRec();
      const langMap = { en: 'en-IN', hi: 'hi-IN', ta: 'ta-IN' };
      const currLang = (window.tourManager && window.tourManager.language) || window.currentLanguage || 'en';
      speechRecognition.lang = langMap[currLang] || 'en-IN';
      speechRecognition.interimResults = false;
      speechRecognition.maxAlternatives = 1;

      micBtn.style.background = '#ff5252';
      micBtn.style.color = '#fff';
      showNotification("🎤 Listening... Ask Luna!");

      speechRecognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        const input = document.getElementById('chat-input-text');
        if (input && transcript) {
          input.value = transcript;
          submitChatMessage();
        }
      };
      speechRecognition.onerror = () => showNotification("Couldn't catch that. Try typing below.");
      speechRecognition.onend = () => {
        micBtn.style.background = 'rgba(244, 196, 48, 0.2)';
        micBtn.style.color = '#f4c430';
      };
      speechRecognition.start();
    } catch (err) {
      showNotification("Mic permission needed to speak.");
    }
  });
}

async function handleScanRelicClick() {
  const btn = document.getElementById('btn-scan-relic');
  if (btn) btn.style.transform = 'scale(0.95)';
  setTimeout(() => { if (btn) btn.style.transform = 'none'; }, 200);
  if (window.visionEngine) {
    return await window.visionEngine.scanCurrentTarget();
  }
  return null;
}

async function checkSecurityAndCamera() {
  const isHttps = (window.location.protocol === 'https:');
  const isLocalhost = (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1');
  const banner = document.getElementById('camera-security-banner');
  if (!isHttps && !isLocalhost) {
    if (banner) {
      banner.style.display = 'block';
      const httpsUrl = `https://${window.location.hostname}:8443/app/${window.location.search}`;
      const httpsLink = document.getElementById('banner-https-link');
      if (httpsLink) {
        httpsLink.href = httpsUrl;
        httpsLink.textContent = `Open in HTTPS: ${httpsUrl}`;
      }
    }
  } else {
    await requestCameraPermission();
  }
}

async function requestCameraPermission() {
  const videoElem = document.getElementById('camera-video');
  const overlayCanvas = document.getElementById('vision-overlay-canvas');
  const result = await window.arScene.startCameraFeed(videoElem);
  if (result.success) {
    const banner = document.getElementById('camera-security-banner');
    if (banner) banner.style.display = 'none';
    if (window.visionEngine) {
      window.visionEngine.onArtifactIdentified = onArtifactIdentified;
      window.visionEngine.onStatusChange = (status) => {
        if (status === "Vision model not installed") {
          showNotification("Vision model not installed");
        }
      };
      await window.visionEngine.init(videoElem, overlayCanvas);
    }
  } else {
    console.warn("[LunarAurora] Camera feed error:", result.reason);
  }
}

function setupModal(triggerId, modalId, closeId) {
  const trigger = triggerId ? document.getElementById(triggerId) : null;
  const modal = document.getElementById(modalId);
  const closeBtn = document.getElementById(closeId);
  if (trigger && modal) {
    trigger.addEventListener('click', (e) => {
      e.stopPropagation();
      modal.classList.add('open');
      if (modalId === 'modal-map' && window.renderInteractiveBlueprintMap) {
        window.renderInteractiveBlueprintMap();
      }
      if (modalId === 'modal-scavenger') fetchScavengerQuests();
    });
  }
  if (closeBtn && modal) {
    closeBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      modal.classList.remove('open');
    });
  }
}

function clearSubtitleTimers() {
  if (subtitleFallbackTimer) {
    clearInterval(subtitleFallbackTimer);
    subtitleFallbackTimer = null;
  }
}

function displaySubtitlesAndSpeak(speaker, subtitle, fullText, audioUrl, recordInChat = true) {
  const container = document.getElementById('yt-subtitle-container');
  const speakerTag = document.getElementById('yt-speaker');
  const textElem = document.getElementById('yt-subtitle-text');
  if (!container || !textElem || !fullText) return;

  clearSubtitleTimers();
  speakerTag.textContent = `${speaker}:`;
  container.classList.add('active');

  const words = fullText.trim().split(/\s+/);
  const chunks = [];
  for (let i = 0; i < words.length; i += 9) {
    chunks.push(words.slice(i, i + 9).join(' '));
  }
  const totalChars = Math.max(1, chunks.reduce((sum, c) => sum + c.length, 0));
  const thresholds = [];
  let running = 0;
  chunks.forEach(c => {
    running += c.length;
    thresholds.push(running / totalChars);
  });

  textElem.textContent = chunks[0] || fullText;
  if (recordInChat) appendChatMessage(speaker.toLowerCase().includes('luna') ? 'guide' : 'user', fullText);

  if (window.spatialAudio && audioUrl) {
    window.spatialAudio.playSpeech(
      audioUrl,
      () => { textElem.textContent = chunks[0]; },
      () => {
        setTimeout(() => {
          if (!window.spatialAudio.isPlaying) container.classList.remove('active');
        }, 1800);
      },
      (currentTime, duration) => {
        const progress = Math.min(1, currentTime / duration);
        let idx = thresholds.findIndex(th => progress <= th);
        if (idx === -1) idx = chunks.length - 1;
        if (textElem.textContent !== chunks[idx]) textElem.textContent = chunks[idx];
      }
    );
  } else if (chunks.length > 1) {
    let idx = 0;
    subtitleFallbackTimer = setInterval(() => {
      idx++;
      if (idx < chunks.length) {
        textElem.textContent = chunks[idx];
      } else {
        clearSubtitleTimers();
        setTimeout(() => container.classList.remove('active'), 1800);
      }
    }, 2600);
  } else {
    setTimeout(() => {
      if (!window.spatialAudio || !window.spatialAudio.isPlaying) container.classList.remove('active');
    }, 4500);
  }
}

function appendChatMessage(sender, text) {
  const msgContainer = document.getElementById('chat-messages-container');
  if (!msgContainer) return;
  const bubble = document.createElement('div');
  bubble.className = `chat-bubble ${sender}`;
  bubble.textContent = text;
  msgContainer.appendChild(bubble);
  msgContainer.scrollTop = msgContainer.scrollHeight;
}

async function submitChatMessage() {
  const input = document.getElementById('chat-input-text');
  if (!input || !input.value.trim()) return;
  const userText = input.value.trim();
  input.value = '';
  appendChatMessage('user', userText);
  chatHistory.push({ role: 'user', content: userText });

  const modalChat = document.getElementById('modal-chat');
  if (modalChat) modalChat.classList.remove('open');
  showNotification("Luna is answering...");

  const tm = window.tourManager;
  try {
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: userText,
        history: chatHistory,
        customer_name: tm ? tm.customerName : "Traveler",
        current_step: tm ? tm.currentStep : 1,
        session_id: tm ? tm.sessionId : null,
        context_poi: tm && tm.currentStopData ? tm.currentStopData.title : "Shore Temple Complex",
        language: (tm && tm.language) || window.currentLanguage || 'en',
        generate_audio: true
      })
    });
    if (res.ok) {
      const data = await res.json();
      chatHistory.push({ role: 'assistant', content: data.reply });
      displaySubtitlesAndSpeak("Luna", "", data.reply, data.audio_url, true);
    }
  } catch (e) {
    displaySubtitlesAndSpeak("Luna", "", "Offline standby active: ask about shade, Pallava history, or next stop!", null, false);
  }
}

function onArtifactIdentified(data) {
  const art = data.artifact;
  showNotification(`Identified: ${art.name}`);
  displaySubtitlesAndSpeak(art.name, '', `${art.story} ${art.fun_fact || ''}`, data.audio_url, true);

  // Grand_Solstice_Sun_Temple.glb is hidden from UI; all 5 carving classes display verified photo + facts panel
  if (window.arScene) window.arScene.hideRelicModel();
  const eraPanel = document.getElementById('era-reconstruction-panel');
  if (eraPanel) eraPanel.style.display = 'none';
  showRelicPhotoInfoPanel(art, data.inference_ms || null);

  if (data.session_progress && window.tourManager) {
    window.tourManager.totalXp = data.session_progress.total_xp;
    window.tourManager.completedRelics = data.session_progress.completed_relics || [];
    window.tourManager.unlockedBadges = data.session_progress.unlocked_badges || [];
    window.tourManager.updateTopHUD();
    window.tourManager.saveToStorage();
  }

  if (data.quest_unlocked) {
    setTimeout(() => {
      showNotification(`🏆 Quest Solved! Unlocked "${data.quest_unlocked.badge_name}" (+${data.quest_unlocked.points} XP)!`);
    }, 1200);
  }
}

async function handleTakeARest() {
  showNotification("Computing assumed-shade Mahabalipuram route (OSM distances)...");
  const tm = window.tourManager;
  const currNode = (tm && tm.currentStopData && tm.currentStopData.poi_id) ? tm.currentStopData.poi_id : (tm ? tm.currentStep : 1);
  const simHour = window.locationTracker && window.locationTracker.simulatedHour !== null
    ? `&hour=${window.locationTracker.simulatedHour}`
    : '';
  const simDate = (window.locationTracker && window.locationTracker.simulatedDate) || '2027-01-11';
  try {
    const res = await fetch(`/api/routing/take-a-rest?current_node_id=${currNode}&date=${encodeURIComponent(simDate)}${simHour}`);
    if (res.ok) {
      const data = await res.json();
      if (data.found) {
        const destNode = data.path_nodes[data.path_nodes.length - 1];
        const msg = `Follow the green assumed-shade route to ${destNode.name} (${data.total_distance_meters}m via OpenStreetMap walkways; illustrative relative score ${data.heat_exposure_saved_pct}% — assumed weights, not measured sun).`;
        displaySubtitlesAndSpeak("Luna", "", msg, null, false);
        const mapModal = document.getElementById('modal-map');
        if (mapModal) {
          mapModal.classList.add('open');
          if (window.renderInteractiveBlueprintMap) await window.renderInteractiveBlueprintMap(destNode.id);
        }
      }
    }
  } catch (e) {
    showNotification("Rest route: Proceed to Varaha Cave Temple for rock-cut stone shade.");
  }
}

async function fetchScavengerQuests() {
  try {
    const res = await fetch('/api/scavenger/quests');
    if (res.ok) {
      const quests = await res.json();
      renderQuestsList(quests);
    }
  } catch (e) {}
}

function renderQuestsList(quests) {
  const container = document.getElementById('scavenger-quests-list');
  if (!container) return;
  const unlockedList = (window.tourManager && window.tourManager.completedRelics) || [];
  container.innerHTML = quests.map(q => {
    const isUnlocked = unlockedList.includes(q.target_relic_code);
    return `
      <div class="badge-card ${isUnlocked ? 'unlocked' : ''}" id="quest-card-${q.quest_id}">
        <i class="fa-solid ${q.badge_icon}"></i>
        <h5>${q.title} ${isUnlocked ? '✓' : ''}</h5>
        <p style="font-style: italic; color: #f4c430;">"${q.riddle}"</p>
        <p>${isUnlocked ? 'UNLOCKED!' : 'Reward: ' + q.points + ' XP'}</p>
      </div>
    `;
  }).join('');
}

function showNotification(msg) {
  let toast = document.getElementById('app-toast');
  if (!toast) {
    toast = document.createElement('div');
    toast.id = 'app-toast';
    toast.style.cssText = `
      position: absolute; bottom: 140px; left: 50%; transform: translateX(-50%);
      background: rgba(10, 14, 23, 0.95); border: 1.5px solid #00e5ff;
      color: #fff; padding: 8px 18px; border-radius: 20px; font-size: 0.8rem;
      font-weight: 600; z-index: 100; box-shadow: 0 4px 18px rgba(0,229,255,0.4); text-align: center;
      transition: opacity 0.3s; pointer-events: none; max-width: 85%;
    `;
    document.body.appendChild(toast);
  }
  toast.textContent = msg;
  toast.style.opacity = '1';
  setTimeout(() => { toast.style.opacity = '0'; }, 3500);
}
