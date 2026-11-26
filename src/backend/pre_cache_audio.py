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
    1: "வணக்கம்! 1984-இல் யுனெஸ்கோ பாரம்பரியத் தலமாக அறிவிக்கப்பட்ட மாமல்லபுரம் நினைவுச்சின்னங்களுக்கு நல்வரவு.",
    2: "இரண்டாம் நரசிம்மவர்மன் காலத்தில் கி.பி 725 அளவில் கருங்கற்களால் கட்டப்பட்ட கடற்கரைக் கோயில் முன்பு நீங்கள் நிற்கிறீர்கள்.",
    3: "பஞ்ச ரதங்கள்! ஒரே சரிவான கருங்கல்லில் செதுக்கப்பட்ட ஐந்து ஒற்றைக்கல் ரதங்கள் இவை.",
    4: "அர்ஜுனன் தபசு அல்லது கங்காவதரணம்! 96 அடி அகலமும் 43 அடி உயரமும் கொண்ட பிரம்மாண்ட திறந்தவெளி புடைப்புச் சிற்பம்.",
    5: "கிருஷ்ணரின் வெண்ணெய் உருண்டை எனப்படும் வானிறைக் கல், மாமல்லபுரம் மலையோரச் சரிவில் அமைந்துள்ள பாதுகாக்கப்பட்ட பாறை ஆகும்.",
    6: "வராக குகைக் கோயில்! ஏழாம் நூற்றாண்டின் பிற்பகுதியைச் சேர்ந்த குடைவரைக் கோயிலும் வராகப் பெருமாள் சிற்பமும் இங்கு உள்ளன.",
    7: "மகிஷாசுரமர்த்தினி மண்டபம்! ஏழாம் நூற்றாண்டைச் சேர்ந்த இக்குடைவரைக் கோயிலில் துர்க்கை, அனந்தசயன விஷ்ணு மற்றும் சிவன் சிற்பங்கள் உள்ளன."
}

HINDI_STOP_OVERRIDES = {
    1: "नमस्ते! 1984 में यूनेस्को विश्व धरोहर स्थल घोषित महाबलीपुरम के पल्लव स्मारक समूह में आपका स्वागत है।",
    2: "आप शोर मंदिर के सामने हैं, जिसे पल्लव राजा नरसिंहवर्मन द्वितीय के शासनकाल में लगभग 725 ईस्वी में ग्रेनाइट पत्थरों से बनाया गया था।",
    3: "पंच रथ! उत्तर-दक्षिण ढलान वाली एकल ग्रेनाइट चट्टानों को तराशकर बनाए गए पाँच एकाश्म रथ स्मारक यहाँ स्थित हैं।",
    4: "अर्जुन की तपस्या या गंगावतरण! दो विशाल चट्टानों पर 96 गुणा 43 फीट में उकेरी गई भव्य खुली शिला-कलाकृति यहाँ है।",
    5: "कृष्ण की माखन गेंद या वान इरै कल महाबलीपुरम की ढलान पर टिका एक विशाल संरक्षित ग्रेनाइट शिलाखंड है।",
    6: "वराह गुफा मंदिर! सातवीं शताब्दी के उत्तरार्ध की इस शैल-गुफा में भगवान विष्णु के वराह अवतार का प्रसिद्ध पैनल स्थित है।",
    7: "महिषासुरमर्दिनी मंडप! सातवीं शताब्दी की इस पहाड़ी गुफा में दुर्गा, शेषशायी विष्णु और शिव के शिल्प पैनल बने हैं।"
}

RELIC_LOCALIZED_SCRIPTS = {
    "shore_temple_vimana": {
        "ta": "மாமல்லபுரம் கடற்கரைக் கோயில். வங்காள விரிகுடா ஓரத்தில் இரண்டாம் நரசிம்மவர்மன் காலத்தில் கருங்கற்களால் கட்டப்பட்ட பழைமையான கோயில்.",
        "hi": "महाबलीपुरम शोर मंदिर। बंगाल की खाड़ी के किनारे नरसिंहवर्मन द्वितीय के समय ग्रेनाइट पत्थरों से बना प्राचीन संरचनात्मक मंदिर।"
    },
    "pancha_rathas": {
        "ta": "பஞ்ச ரதங்கள். பாண்டவர்கள் மற்றும் திரௌபதியின் பெயரால் அழைக்கப்படும் ஐந்து ஒற்றைக்கல் பல்லவ ரதங்கள்.",
        "hi": "पंच रथ, महाबलीपुरम। पांडवों और द्रौपदी के नाम पर प्रसिद्ध पाँच एकाश्म पल्लव रथ स्मारक।"
    },
    "arjunas_penance": {
        "ta": "அர்ஜுனன் தபசு. பகீரதன் கங்கையை பூமிக்குக் கொண்டு வரும் புராணக் காட்சியைக் காட்டும் 96 அடி அகல புடைப்புச் சிற்பம்.",
        "hi": "अर्जुन की तपस्या। भगीरथ द्वारा पृथ्वी पर गंगा के अवतरण को दर्शाती 96 गुणा 43 फीट की विशाल पाषाण कलाकृति।"
    },
    "krishnas_butter_ball": {
        "ta": "கிருஷ்ணரின் வெண்ணெய் உருண்டை எனப்படும் வானிறைக் கல். இந்திய தொல்லியல் துறையால் பாதுகாக்கப்பட்ட பிரம்மாண்ட பாறை.",
        "hi": "कृष्ण की माखन गेंद या वान इरै कल। भारतीय पुरातत्व सर्वेक्षण द्वारा संरक्षित विशाल संतुलित ग्रेनाइट शिलाखंड।"
    },
    "mahishasuramardini_cave": {
        "ta": "மகிஷாசுரமர்த்தினி குகைக் கோயில் சிற்பம். மகிஷாசுரனை வதம் செய்யும் துர்க்கையின் பல்லவ குடைவரைச் சிற்பம்.",
        "hi": "महिषासुरमर्दिनी गुफा मंदिर शिल्प। सातवीं शताब्दी के पल्लव गुफा मंदिर में महिषासुर का वध करती देवी दुर्गा की मूर्ति।"
    }
}

OBSOLETE_PREFIXES = (
    "relic_chariot_wheel",
    "relic_lotus_basin",
    "relic_nataraja_relief",
    "relic_yali_pillar",
)


def remove_obsolete_and_stale_cache(precache_dir: str):
    if not os.path.isdir(precache_dir):
        return []
    removed = []
    for fname in sorted(os.listdir(precache_dir)):
        if fname.endswith(".mp3"):
            os.remove(os.path.join(precache_dir, fname))
            removed.append(fname)
    return removed


async def _synth(text: str, voice: str, out_path: str):
    try:
        comm = edge_tts.Communicate(text, voice)
        await asyncio.wait_for(comm.save(out_path), timeout=10.0)
    except Exception as e:
        print(f"  [Error] {os.path.basename(out_path)}: {e}")


async def pre_cache_all():
    seed_database(force_reset=False)
    db = SessionLocal()
    precache_dir = settings.AUDIO_PRECACHE_DIR
    os.makedirs(precache_dir, exist_ok=True)

    removed = remove_obsolete_and_stale_cache(precache_dir)
    print(f"[PreCache] Removed {len(removed)} old MP3 files (including obsolete chariot/yali/nataraja/lotus clips): {removed}")

    tasks = []
    stops = db.query(BlueprintStop).order_by(BlueprintStop.step_number).all()
    for s in stops:
        en_text = s.script_welcome.replace("{name}", "Traveler")
        tasks.append(("stop", str(s.step_number), "en", en_text))
        tasks.append(("stop", str(s.step_number), "ta", TAMIL_STOP_OVERRIDES.get(s.step_number, en_text)))
        tasks.append(("stop", str(s.step_number), "hi", HINDI_STOP_OVERRIDES.get(s.step_number, en_text)))

    relics = db.query(RelicArtifact).all()
    for r in relics:
        en_rel = f"{r.name}. {r.story}"
        loc = RELIC_LOCALIZED_SCRIPTS.get(r.code, {})
        tasks.append(("relic", r.code, "en", en_rel))
        tasks.append(("relic", r.code, "ta", loc.get("ta", en_rel)))
        tasks.append(("relic", r.code, "hi", loc.get("hi", en_rel)))

    for lang in ("en", "ta", "hi"):
        bank = OFFLINE_QA_BANK[lang]
        for topic, tmpl in bank.items():
            txt = tmpl.format(
                name="Traveler",
                loc="Shore Temple",
                step=1,
                stop_details="Part of the 7th-8th century CE Group of Monuments at Mahabalipuram (UNESCO 1984).",
                next_guidance="Follow the shaded route on ShadeMap."
            )
            tasks.append(("qa", topic, lang, txt))

    tasks.append(("farewell", "clip", "en", "Thank you for completing the 4.13 km one-way Mahabalipuram heritage trail with Lunar Aurora!"))
    tasks.append(("farewell", "clip", "ta", "லூனார் அரோராவுடன் மாமல்லபுரம் பயணத்தை முடித்ததற்கு நன்றி!"))
    tasks.append(("farewell", "clip", "hi", "लूनर ऑरोरा के साथ महाबलीपुरम यात्रा पूरी करने के लिए धन्यवाद!"))

    print(f"[PreCache] Synthesizing {len(tasks)} sourced EN/TA/HI audio clips in {precache_dir}...")
    sem = asyncio.Semaphore(4)

    async def _worker(kind, key, lang, txt):
        async with sem:
            fname = f"farewell_{lang}.mp3" if kind == "farewell" else f"{kind}_{key}_{lang}.mp3"
            voice = VOICE_MAP.get(lang, settings.DEFAULT_VOICE)
            await _synth(txt, voice, os.path.join(precache_dir, fname))

    await asyncio.gather(*[_worker(*t) for t in tasks])
    db.close()
    generated = sorted(f for f in os.listdir(precache_dir) if f.endswith(".mp3"))
    print(f"[PreCache] Generated {len(generated)} MP3 files cleanly.")
    print("[PreCache] Relic MP3s:", [f for f in generated if f.startswith("relic_")])


if __name__ == "__main__":
    asyncio.run(pre_cache_all())
