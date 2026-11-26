import os
import hashlib
import asyncio
import edge_tts
from typing import Optional
from app.config import settings

VOICE_MAP = {
    "en": "en-IN-NeerjaNeural",
    "ta": "ta-IN-PallaviNeural",
    "hi": "hi-IN-SwaraNeural",
    "es": "es-ES-AlvaroNeural",
    "fr": "fr-FR-HenriNeural",
    "de": "de-DE-ConradNeural",
    "ja": "ja-JP-KeitaNeural",
}

class TTSService:
    def __init__(self):
        self.cache_dir = settings.AUDIO_CACHE_DIR
        self.precache_dir = settings.AUDIO_PRECACHE_DIR
        os.makedirs(self.cache_dir, exist_ok=True)
        os.makedirs(self.precache_dir, exist_ok=True)

    def _get_filename(self, text: str, voice: str) -> str:
        key = f"{voice}:{text.strip()}"
        file_hash = hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]
        return f"narrative_{file_hash}.mp3"

    def resolve_precached_url(self, cache_key: str, language: str = "en") -> Optional[str]:
        """
        Checks pre-generated static audio_cache MP3s (e.g., stop_1_en.mp3, relic_chariot_wheel_ta.mp3).
        """
        filename = f"{cache_key}_{language}.mp3"
        path = os.path.join(self.precache_dir, filename)
        if os.path.exists(path) and os.path.getsize(path) > 0:
            return f"/static/audio_cache/{filename}"
        # Fallback to English precache if requested language not cached
        en_filename = f"{cache_key}_en.mp3"
        en_path = os.path.join(self.precache_dir, en_filename)
        if os.path.exists(en_path) and os.path.getsize(en_path) > 0:
            return f"/static/audio_cache/{en_filename}"
        return None

    async def generate_speech(
        self,
        text: str,
        language: str = "en",
        voice_override: Optional[str] = None,
        fallback_cache_key: Optional[str] = None,
        timeout_sec: float = None
    ) -> str:
        """
        Synthesizes text to MP3 using Edge-TTS with an explicit 2.5s timeout failsafe.
        Falls back immediately to pre-cached static audio_cache MP3 on timeout or offline state.
        """
        if not text or not text.strip():
            return ""

        timeout = timeout_sec if timeout_sec is not None else settings.AI_TIMEOUT_SECONDS
        voice = voice_override or VOICE_MAP.get(language, settings.DEFAULT_VOICE)
        filename = self._get_filename(text, voice)
        filepath = os.path.join(self.cache_dir, filename)

        if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
            return f"/static/audio/{filename}"

        # Also check precache before hitting network if key provided
        precached = self.resolve_precached_url(fallback_cache_key, language) if fallback_cache_key else None

        try:
            communicate = edge_tts.Communicate(text, voice)
            await asyncio.wait_for(communicate.save(filepath), timeout=timeout)
            if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
                return f"/static/audio/{filename}"
        except Exception as e:
            print(f"[TTSService] Timeout/offline fallback triggered ({e})")

        return precached or ""

tts_service = TTSService()
