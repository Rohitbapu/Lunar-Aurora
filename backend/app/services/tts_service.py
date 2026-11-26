import os
import hashlib
import asyncio
import edge_tts
from app.config import settings

VOICE_MAP = {
    "en": "en-US-ChristopherNeural",
    "en-female": "en-US-AvaNeural",
    "hi": "hi-IN-MadhurNeural",
    "es": "es-ES-AlvaroNeural",
    "fr": "fr-FR-HenriNeural",
    "de": "de-DE-ConradNeural",
    "ja": "ja-JP-KeitaNeural",
    "ta": "ta-IN-ValluvarNeural",
}

class TTSService:
    def __init__(self):
        self.cache_dir = settings.AUDIO_CACHE_DIR
        os.makedirs(self.cache_dir, exist_ok=True)

    def _get_filename(self, text: str, voice: str) -> str:
        key = f"{voice}:{text.strip()}"
        file_hash = hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]
        return f"narrative_{file_hash}.mp3"

    async def generate_speech(self, text: str, language: str = "en", voice_override: str = None) -> str:
        """
        Synthesizes text to MP3 using edge-tts and returns the relative static URL.
        """
        if not text or not text.strip():
            return ""

        voice = voice_override or VOICE_MAP.get(language, settings.DEFAULT_VOICE)
        filename = self._get_filename(text, voice)
        filepath = os.path.join(self.cache_dir, filename)

        # Return cached file if already generated
        if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
            return f"/static/audio/{filename}"

        try:
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(filepath)
            return f"/static/audio/{filename}"
        except Exception as e:
            print(f"[TTSService] Edge-TTS generation error: {e}")
            # If offline or rate-limited, create an empty placeholder or return empty
            return ""

tts_service = TTSService()

