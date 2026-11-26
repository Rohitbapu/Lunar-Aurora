import os
import asyncio
from typing import List, Dict, Optional, Tuple
from app.config import settings

OFFLINE_QA_BANK = {
    "en": {
        "shade": "Take a shaded break, {name}! Follow the green shaded route on ShadeMap toward Varaha Cave Temple or the hilltop near Mahishasuramardini Mandapa.",
        "history": "The Group of Monuments at Mahabalipuram is a UNESCO World Heritage Site (inscribed 1984) built during the 7th and 8th centuries CE by the Pallava dynasty on the Coromandel Coast, about 60 km south of Chennai.",
        "next": "Here is your next direction, {name}: {next_guidance} Open ShadeMap to compare open sun vs. shaded routes.",
        "secret": "Verified note for {loc}, {name}: {stop_details}",
        "default": "We are at Stop {step}: {loc}, {name}. {stop_details} Tap SCAN RELIC over any printed Mahabalipuram card or ask a question!"
    },
    "ta": {
        "shade": "{name}, வெயிலிலிருந்து ஓய்வெடுக்க பச்சை நிழல் பாதை வழியாக வராக குகைக் கோயில் அல்லது மகிஷாசுரமர்த்தினி மண்டபத்திற்குச் செல்லுங்கள்.",
        "history": "{name}, மாமல்லபுரம் நினைவுச்சின்னங்கள் கி.பி 7 மற்றும் 8-ஆம் நூற்றாண்டுகளில் பல்லவ வம்சத்தால் கட்டப்பட்ட யுனெஸ்கோ உலக பாரம்பரியத் தலமாகும் (1984).",
        "next": "{name}, அடுத்த வழித்தடம்: {next_guidance}",
        "secret": "{name}, {loc} பற்றிய தகவல்: {stop_details}",
        "default": "{name}, நாம் இப்போது நிறுத்தம் {step} ({loc}) இல் இருக்கிறோம். சிற்ப அட்டையை ஸ்கேன் செய்யவும் அல்லது கேள்வி கேட்கவும்!"
    },
    "hi": {
        "shade": "{name}, धूप से बचने के लिए हरे छायादार मार्ग से वराह गुफा मंदिर या महिषासुरमर्दिनी मंडप की ओर चलें।",
        "history": "{name}, महाबलीपुरम के स्मारक समूह पल्लव वंश द्वारा 7वीं और 8वीं शताब्दी ईस्वी में निर्मित यूनेस्को विश्व धरोहर स्थल (1984) हैं।",
        "next": "{name}, आपका अगला मार्ग निर्देश: {next_guidance}",
        "secret": "{name}, {loc} का तथ्य: {stop_details}",
        "default": "{name}, हम अभी पड़ाव {step} ({loc}) पर हैं। शिल्प कार्ड को स्कैन करें या कोई भी प्रश्न पूछें!"
    }
}

class GroqGuideService:
    def __init__(self):
        self.api_key = settings.GROQ_API_KEY or os.getenv("GROQ_API_KEY", "")
        self.client = None
        if self.api_key:
            try:
                from groq import Groq
                self.client = Groq(api_key=self.api_key)
                print("[GroqGuideService] Initialized Groq client with model:", settings.GROQ_MODEL)
            except Exception as e:
                print(f"[GroqGuideService] Groq init warning: {e}")

    def build_system_prompt(
        self,
        context_poi: Optional[str] = None,
        relic_name: Optional[str] = None,
        language: str = "en",
        customer_name: Optional[str] = None,
        current_step: Optional[int] = None,
        stop_details: Optional[str] = None,
        next_guidance: Optional[str] = None
    ) -> str:
        visitor_name = customer_name or "visitor"
        lang_names = {"en": "English", "ta": "Tamil", "hi": "Hindi"}
        lang_label = lang_names.get(language, language)
        prompt = (
            "You are Luna Aurora, an accurate historical guide for "
            f"{visitor_name} at the Group of Monuments at Mahabalipuram (UNESCO World Heritage Site inscribed 1984, Tamil Nadu, India).\n"
            "Rules:\n"
            f"- Address {visitor_name} concisely in 2 to 3 clear spoken sentences.\n"
            f"- Respond strictly in {lang_label}.\n"
            "- Only state documented 7th-8th century Pallava heritage facts (Shore Temple, Pancha Rathas, Descent of the Ganges / Arjuna's Penance, Krishna's Butterball, Varaha Cave Temple, Mahishasuramardini Mandapa); do not invent dates or dimensions.\n"
        )
        if current_step:
            prompt += f"\nCurrent Tour Stop: {current_step} of 7."
        if context_poi:
            prompt += f"\nLocation: {context_poi}."
        if stop_details:
            prompt += f"\nVerified Context: {stop_details}"
        if next_guidance:
            prompt += f"\nNext Step Guidance: {next_guidance}"
        if relic_name:
            prompt += f"\nScanned Carving Card: {relic_name}."
        return prompt

    async def get_response(
        self,
        user_message: str,
        history: Optional[List[Dict[str, str]]] = None,
        context_poi: Optional[str] = None,
        relic_name: Optional[str] = None,
        language: str = "en",
        customer_name: Optional[str] = None,
        current_step: Optional[int] = None,
        stop_details: Optional[str] = None,
        next_guidance: Optional[str] = None
    ) -> Tuple[str, str, bool]:
        if history is None:
            history = []

        system_prompt = self.build_system_prompt(
            context_poi, relic_name, language, customer_name, current_step, stop_details, next_guidance
        )

        if self.client:
            try:
                messages = [{"role": "system", "content": system_prompt}]
                for msg in history[-6:]:
                    messages.append(msg)
                messages.append({"role": "user", "content": user_message})

                def _call_groq():
                    resp = self.client.chat.completions.create(
                        model=settings.GROQ_MODEL,
                        messages=messages,
                        temperature=0.65,
                        max_tokens=200,
                        top_p=0.9
                    )
                    return resp.choices[0].message.content.strip()

                reply = await asyncio.wait_for(asyncio.to_thread(_call_groq), timeout=settings.AI_TIMEOUT_SECONDS)
                return reply, "qa_default", False
            except Exception as e:
                print(f"[GroqGuideService] 2.5s timeout / network fallback ({e})")

        text, topic_key = self._generate_fallback(
            user_message, context_poi, relic_name, language, customer_name, current_step, stop_details, next_guidance
        )
        return text, f"qa_{topic_key}", True

    def _generate_fallback(
        self,
        query: str,
        context_poi: Optional[str],
        relic_name: Optional[str],
        language: str,
        customer_name: Optional[str] = None,
        current_step: Optional[int] = None,
        stop_details: Optional[str] = None,
        next_guidance: Optional[str] = None
    ) -> Tuple[str, str]:
        name = customer_name or "Traveler"
        q = query.lower()
        loc = context_poi or "Mahabalipuram Monument Complex"
        bank = OFFLINE_QA_BANK.get(language, OFFLINE_QA_BANK["en"])

        if relic_name and language == "en":
            return (
                f"{name}, you scanned {relic_name}. It belongs to the 7th-8th century CE Pallava dynasty monuments at Mahabalipuram, classified by UNESCO in 1984."
            ), "secret"

        if any(k in q for k in ("shade", "tired", "rest", "hot", "sun", "cool", "water", "நிழல்", "धूप")):
            topic = "shade"
        elif any(k in q for k in ("next", "where", "go", "walk", "map", "direction", "அடுத்த", "अगले")):
            topic = "next"
        elif any(k in q for k in ("secret", "mystery", "hidden", "fact", "special", "why", "ரகசிய", "रहस्य")):
            topic = "secret"
        elif any(k in q for k in ("who", "built", "history", "when", "era", "pallava", "யார்", "किसने")):
            topic = "history"
        else:
            topic = "default"

        template = bank.get(topic, bank["default"])
        text = template.format(
            name=name,
            loc=loc,
            step=current_step or 1,
            stop_details=stop_details or "Part of the 7th-8th century CE Group of Monuments at Mahabalipuram (UNESCO, 1984).",
            next_guidance=next_guidance or "Follow the shaded pathway marked in green on ShadeMap."
        )
        return text, topic

groq_service = GroqGuideService()
