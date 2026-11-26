import os
import asyncio
import edge_tts
from app.config import settings
from app.database import SessionLocal
from app.models.entities import BlueprintStop, RelicArtifact
from app.services.groq_service import OFFLINE_QA_BANK
from app.services.tts_service import VOICE_MAP
from init_db import seed_database

TAMIL_STOP_OVERRIDES = {
    1: "வணக்கம்! மாமல்லபுரம் கடற்கரைக் கோயிலுக்கு நல்வரவு. பல்லவ மன்னர் ராஜசிம்மன் கி.பி 700-இல் அமைத்த கிழக்கு வாயிலில் நீங்கள் நிற்கிறீர்கள்.",
    2: "யாளி தூண் மண்டபத்திற்கு வருக. இங்குள்ள நிழலும் கடற்காற்றும் வெப்பத்தைக் குறைக்கும். சிற்ப அட்டையை ஸ்கேன் செய்யவும்!",
    3: "பல்லவ சூரிய ரதச் சக்கரம்! இதன் இருபத்தி நான்கு ஆரங்கள் நேரத்தையும் பருவநிலைகளையும் துல்லியமாகக் கணிக்கின்றன.",
    4: "ராஜசிம்மேஸ்வர கடற்கரை விமானம்! சுண்ணாம்புக் கலவையின்றி கருங்கற்களால் கட்டப்பட்ட இந்தக் கோபுரம் கடல் அலைகளைத் தாண்டி நிற்கிறது.",
    5: "அரச தாமரை நீர்த் தொட்டி. இயற்கை ஆவியாதல் மூலம் வெப்பநிலையை ஆறு டிகிரி செல்சியஸ் வரை குறைக்கிறது.",
    6: "அர்ஜுனன் தபசு அரசமர நிழல் மண்டபம்! இங்கு நடராஜர் சிற்பத்தையும் குளிர்ந்த ஓய்விடத்தையும் காணலாம்.",
    7: "மாமல்லபுரம் கோரமண்டல் சூரிய அஸ்தமனக் கோட்டை! ஏழு நிறுத்தங்களையும் வெற்றிகரமாக முடித்துவிட்டீர்கள். வாழ்த்துகள்!"
}

HINDI_STOP_OVERRIDES = {
    1: "नमस्ते! महाबलीपुरम के शोर मंदिर में आपका स्वागत है। आप पल्लव राजा राजसिंह द्वारा 700 ईस्वी में निर्मित पूर्वी द्वार पर खड़े हैं।",
    2: "याली स्तंभ गलियारे में आपका स्वागत है। यहाँ की शीतल छाया धूप से बचाती है। शिल्प कार्ड को स्कैन करें!",
    3: "सूर्य रथ चक्र वेदिका! इसके चौबीस आरे प्राचीन काल में समय और ऋतुओं की सटीक गणना करते थे।",
    4: "राजसिम्हेश्वर शोर मंदिर विमान! बिना चूने के ग्रेनाइट पत्थरों से बना यह शिखर सदियों से समुद्र की लहरों के सामने अडिग है।",
    5: "शाही कमल जल कुंड। वाष्पीकरण द्वारा यह चबूतरा आस-पास के तापमान को छह डिग्री तक ठंडा रखता है।",
    6: "बरगद छाया विश्राम मंडप! यहाँ आप नटराज की मूर्ति और शीतल पेयजल का आनंद ले सकते हैं।",
    7: "कोरोमंडल सूर्यास्त बुर्ज! आपने सभी सात ऐतिहासिक पड़ाव सफलतापूर्वक पूरे कर लिए हैं। बधाई हो!"
}

async def _synth(text: str, voice: str, out_path: str):
    if os.path.exists(out_path) and os.path.getsize(out_path) > 0:
        return
    try:
        comm = edge_tts.Communicate(text, voice)
        await asyncio.wait_for(comm.save(out_path), timeout=8.0)
    except Exception as e:
        print(f"  [Skip] {os.path.basename(out_path)}: {e}")

async def pre_cache_all():
    seed_database(force_reset=False)
    db = SessionLocal()
    precache_dir = settings.AUDIO_PRECACHE_DIR
    os.makedirs(precache_dir, exist_ok=True)

    tasks = []
    stops = db.query(BlueprintStop).order_by(BlueprintStop.step_number).all()
    for s in stops:
        en_text = s.script_welcome.replace("{name}", "Traveler")
        tasks.append(("stop", s.step_number, "en", en_text))
        tasks.append(("stop", s.step_number, "ta", TAMIL_STOP_OVERRIDES.get(s.step_number, en_text)))
        tasks.append(("stop", s.step_number, "hi", HINDI_STOP_OVERRIDES.get(s.step_number, en_text)))

    relics = db.query(RelicArtifact).all()
    for r in relics:
        en_rel = f"{r.name}. {r.story}"
        tasks.append(("relic", r.code, "en", en_rel))

    for lang in ("en", "ta", "hi"):
        bank = OFFLINE_QA_BANK[lang]
        for topic, tmpl in bank.items():
            txt = tmpl.format(
                name="Traveler",
                loc="Shore Temple",
                step=1,
                stop_details="Built around 700 CE by Pallava king Rajasimha without mortar.",
                next_guidance="Follow the emerald shaded colonnade path on your map."
            )
            tasks.append(("qa", topic, lang, txt))

    tasks.append(("farewell", "clip", "en", "Thank you for completing the 7-stop Mahabalipuram heritage expedition with Lunar Aurora!"))
    tasks.append(("farewell", "clip", "ta", "லூனார் அரோராவுடன் மாமல்லபுரம் பயணத்தை முடித்ததற்கு நன்றி!"))
    tasks.append(("farewell", "clip", "hi", "लूनर ऑरोरा के साथ महाबलीपुरम यात्रा पूरी करने के लिए धन्यवाद!"))

    print(f"[PreCache] Generating {len(tasks)} offline audio clips in {precache_dir}...")
    sem = asyncio.Semaphore(4)

    async def _worker(kind, key, lang, txt):
        async with sem:
            if kind == "farewell":
                fname = f"farewell_{lang}.mp3"
            else:
                fname = f"{kind}_{key}_{lang}.mp3"
            voice = VOICE_MAP.get(lang, settings.DEFAULT_VOICE)
            await _synth(txt, voice, os.path.join(precache_dir, fname))

    await asyncio.gather(*[_worker(*t) for t in tasks])
    db.close()
    generated = len([f for f in os.listdir(precache_dir) if f.endswith(".mp3")])
    print(f"[PreCache] Complete! {generated} offline MP3 files ready in static/audio_cache/.")

if __name__ == "__main__":
    asyncio.run(pre_cache_all())
