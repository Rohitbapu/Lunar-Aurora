/**
 * Master Application Controller for Lunar Aurora Mobile WebXR
 * Minimalist, camera-first, GPS-enabled, voice-interactive, and audio-synced YouTube subtitles.
 */

let chatHistory = [];
let audioUnlocked = false;
let subtitleFallbackTimer = null;
let speechRecognition = null;

document.addEventListener('DOMContentLoaded', async () => {
  console.log("[LunarAurora] Booting up clean Camera-First WebXR tour...");

  // 1. Setup UI listeners immediately
  setupUI();

  // 2. Initialize transparent AR camera scene
  try {
    window.arScene.init('ar-viewport-container');
  } catch (e) {
    console.error("[LunarAurora] Three.js init error:", e);
  }

  // 3. Initialize Tour Manager (Session, QR name/lang, 7-stop curated flow)
  if (window.tourManager) {
    await window.tourManager.init();
    window.tourManager.setupInterruptionListeners();
    // Show Stop 1 subtitle preview silently until user taps to unlock audio
    if (window.tourManager.currentStopData) {
      displaySubtitlesAndSpeak("Luna", "", window.tourManager.currentStopData.personalized_welcome, null, false);
    }
  }

  // 4. Initialize Mobile GPS Tracking
  if (window.locationTracker) {
    window.locationTracker.onLocationUpdated = (gpsData) => {
      const gpsLabel = document.getElementById('gps-coords-label');
      if (gpsLabel) gpsLabel.textContent = `GPS: ±${gpsData.accuracy}m`;
      const mapModal = document.getElementById('modal-map');
      if (mapModal && mapModal.classList.contains('open') && window.renderInteractiveBlueprintMap) {
        window.renderInteractiveBlueprintMap();
      }
    };

    window.locationTracker.onStopArrived = (stop, dist) => {
      showNotification(`📍 GPS: Arrived near ${stop.name} (${dist}m)! Tap NEXT to continue.`);
    };

    window.locationTracker.checkPermissionStatus();
  }

  // 5. Load Scavenger Quests
  fetchScavengerQuests();

  // 6. Check Security Context & Camera
  checkSecurityAndCamera();
});

function setupUI() {
  // Global Audio & GPS Unlock on first tap
  const unlockAudioAndGps = async () => {
    if (!audioUnlocked && window.spatialAudio) {
      await window.spatialAudio.resumeOnUserGesture();
      audioUnlocked = true;
      if (window.tourManager && !window.tourManager.hasPlayedInitialWelcome) {
        window.tourManager.playCurrentStopNarration();
      }
    }
    if (window.locationTracker && !window.locationTracker.hasGpsFix) {
      window.locationTracker.requestGpsFix(true);
    }
  };
  document.body.addEventListener('click', unlockAudioAndGps, { once: true });
  document.body.addEventListener('touchstart', unlockAudioAndGps, { once: true });

  // GPS Pill Tap
  const gpsPill = document.getElementById('gps-status-pill');
  if (gpsPill) {
    gpsPill.addEventListener('click', (e) => {
      e.stopPropagation();
      showNotification("🛰️ Requesting GPS fix...");
      if (window.locationTracker) {
        window.locationTracker.requestGpsFix(true);
      }
    });
  }

  // 1. SCAN RELIC
  const btnScanRelic = document.getElementById('btn-scan-relic');
  if (btnScanRelic) {
    btnScanRelic.addEventListener('click', async (e) => {
      e.stopPropagation();
      await handleScanRelicClick();
    });
  }

  // 2. NEXT STOP
  const btnAdvance = document.getElementById('btn-advance-stop');
  if (btnAdvance) {
    btnAdvance.addEventListener('click', async (e) => {
      e.stopPropagation();
      if (window.tourManager) {
        await window.tourManager.advanceToNextStop();
      }
    });
  }

  // 3. SHADE / REST ROUTE
  const restBtn = document.getElementById('btn-take-rest');
  if (restBtn) {
    restBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      handleTakeARest();
    });
  }

  // 4. MUTE / STOP SUBTITLE VOICE
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

  // 5. TOP END TOUR BUTTON
  const btnEndTourTop = document.getElementById('btn-end-tour-top');
  if (btnEndTourTop) {
    btnEndTourTop.addEventListener('click', (e) => {
      e.stopPropagation();
      if (window.tourManager) window.tourManager.endTourEarly();
    });
  }

  // Restart Tour in Certificate Modal
  const btnRestart = document.getElementById('btn-restart-tour');
  if (btnRestart) {
    btnRestart.addEventListener('click', () => {
      window.location.href = window.location.pathname;
    });
  }

  // Single clean modal wiring (no duplicate listeners!)
  setupModal('btn-open-chat', 'modal-chat', 'btn-close-chat');
  setupModal('btn-open-map-top', 'modal-map', 'btn-close-map');
  setupModal('btn-open-scavenger', 'modal-scavenger', 'btn-close-scavenger');

  // Language Selector inside Ask Luna
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

  // Quick Suggestion Chips
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

  // Microphone Voice Input (Web Speech API)
  setupVoiceMicButton();

  // Chat Send
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

  // Camera Activate Retry
  const btnEnableCam = document.getElementById('btn-enable-camera');
  if (btnEnableCam) {
    btnEnableCam.addEventListener('click', async (e) => {
      e.stopPropagation();
      await requestCameraPermission();
    });
  }
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
      const langMap = { en: 'en-US', hi: 'hi-IN', es: 'es-ES', fr: 'fr-FR', de: 'de-DE', ja: 'ja-JP', ta: 'ta-IN' };
      const currLang = (window.tourManager && window.tourManager.language) || window.currentLanguage || 'en';
      speechRecognition.lang = langMap[currLang] || 'en-US';
      speechRecognition.interimResults = false;
      speechRecognition.maxAlternatives = 1;

      micBtn.style.background = '#ff5252';
      micBtn.style.color = '#fff';
      showNotification("🎤 Listening... Ask your question!");

      speechRecognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        const input = document.getElementById('chat-input-text');
        if (input && transcript) {
          input.value = transcript;
          submitChatMessage();
        }
      };

      speechRecognition.onerror = () => {
        showNotification("Couldn't catch that. Try again or type.");
      };

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

  showNotification("🔍 Scanning monument carving...");

  if (window.visionEngine) {
    const result = await window.visionEngine.scanCurrentTarget();
    if (!result) {
      showNotification("Aim camera at the carving or pillar and try again.");
    }
  }
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
      await window.visionEngine.init(videoElem, overlayCanvas);
      window.visionEngine.startDetectionLoop();
    }
  } else {
    console.warn("[LunarAurora] Camera feed error:", result.reason);
  }
}

function setupModal(triggerId, modalId, closeId) {
  const trigger = document.getElementById(triggerId);
  const modal = document.getElementById(modalId);
  const closeBtn = document.getElementById(closeId);

  if (trigger && modal) {
    trigger.addEventListener('click', (e) => {
      e.stopPropagation();
      modal.classList.add('open');
      if (modalId === 'modal-map' && window.renderInteractiveBlueprintMap) {
        window.renderInteractiveBlueprintMap();
      }
      if (modalId === 'modal-scavenger') {
        fetchScavengerQuests();
      }
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

/**
 * YouTube-Style Live Subtitles synchronized tightly to spoken Edge-TTS audio duration & character weights.
 */
function displaySubtitlesAndSpeak(speaker, subtitle, fullText, audioUrl, recordInChat = true) {
  const container = document.getElementById('yt-subtitle-container');
  const speakerTag = document.getElementById('yt-speaker');
  const textElem = document.getElementById('yt-subtitle-text');

  if (!container || !textElem || !fullText) return;

  clearSubtitleTimers();
  speakerTag.textContent = `${speaker}:`;
  container.classList.add('active');

  // Build balanced 8-10 word YouTube caption chunks + cumulative character fractions
  const words = fullText.trim().split(/\s+/);
  const chunks = [];
  const chunkSize = 9;
  for (let i = 0; i < words.length; i += chunkSize) {
    chunks.push(words.slice(i, i + chunkSize).join(' '));
  }

  const totalChars = Math.max(1, chunks.reduce((sum, c) => sum + c.length, 0));
  const thresholds = [];
  let running = 0;
  chunks.forEach(c => {
    running += c.length;
    thresholds.push(running / totalChars);
  });

  textElem.textContent = chunks[0] || fullText;

  if (recordInChat) {
    appendChatMessage(speaker.toLowerCase().includes('luna') ? 'guide' : 'user', fullText);
  }

  if (window.spatialAudio && audioUrl) {
    window.spatialAudio.playSpeech(
      audioUrl,
      () => {
        textElem.textContent = chunks[0];
      },
      () => {
        setTimeout(() => {
          if (!window.spatialAudio.isPlaying) {
            container.classList.remove('active');
          }
        }, 1800);
      },
      (currentTime, duration) => {
        // Real-time progress sync!
        const progress = Math.min(1, currentTime / duration);
        let idx = thresholds.findIndex(th => progress <= th);
        if (idx === -1) idx = chunks.length - 1;
        if (textElem.textContent !== chunks[idx]) {
          textElem.textContent = chunks[idx];
        }
      }
    );
  } else if (chunks.length > 1) {
    // Fallback reading pace when audio isn't active
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
      if (!window.spatialAudio || !window.spatialAudio.isPlaying) {
        container.classList.remove('active');
      }
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
  const visitorName = tm ? tm.customerName : "Traveler";
  const currentStep = tm ? tm.currentStep : 1;
  const sessionId = tm ? tm.sessionId : null;
  const activeLang = (tm && tm.language) || window.currentLanguage || 'en';

  try {
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: userText,
        history: chatHistory,
        customer_name: visitorName,
        current_step: currentStep,
        session_id: sessionId,
        context_poi: tm && tm.currentStopData ? tm.currentStopData.title : "Imperial Sun Gate",
        language: activeLang,
        generate_audio: true
      })
    });

    if (res.ok) {
      const data = await res.json();
      chatHistory.push({ role: 'assistant', content: data.reply });
      displaySubtitlesAndSpeak("Luna", "", data.reply, data.audio_url, true);
    }
  } catch (e) {
    displaySubtitlesAndSpeak("Luna", "", "I am listening! Check connection to the site server.", null, false);
  }
}

function onArtifactIdentified(data) {
  const art = data.artifact;
  showNotification(`✨ Identified: ${art.name}!`);
  displaySubtitlesAndSpeak(art.name, '', `${art.story} ${art.fun_fact || ''}`, data.audio_url, true);

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
  showNotification("Calculating coolest shaded route to rest pavilion...");
  const tm = window.tourManager;
  const currNode = (tm && tm.currentStopData && tm.currentStopData.poi_id) ? tm.currentStopData.poi_id : (tm ? tm.currentStep : 1);

  try {
    const res = await fetch(`/api/routing/take-a-rest?current_node_id=${currNode}`);
    if (res.ok) {
      const data = await res.json();
      if (data.found) {
        const destNode = data.path_nodes[data.path_nodes.length - 1];
        const msg = `Follow the green shaded route to ${destNode.name} (${data.total_distance_meters}m, ~${data.estimated_walk_minutes} min). Shade index: ${Math.round(data.average_shade_index * 100)}%!`;
        displaySubtitlesAndSpeak("Luna", "", msg, null, false);

        const routeDetail = document.getElementById('map-route-detail');
        if (routeDetail) {
          routeDetail.innerHTML = `<strong style="color:#00e676;">Shaded Rest Route:</strong> ${destNode.name} (${data.total_distance_meters}m • ${Math.round(data.average_shade_index * 100)}% Shade)`;
        }

        const mapModal = document.getElementById('modal-map');
        if (mapModal) {
          mapModal.classList.add('open');
          if (window.renderInteractiveBlueprintMap) {
            window.renderInteractiveBlueprintMap(data.path_node_ids);
          }
        }
      }
    }
  } catch (e) {
    showNotification("Rest route: Proceed to Whispering Gallery / Banyan Grove.");
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
  setTimeout(() => {
    toast.style.opacity = '0';
  }, 3500);
}
