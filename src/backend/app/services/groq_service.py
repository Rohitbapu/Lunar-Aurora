import os
import asyncio
from typing import List, Dict, Optional, Tuple
from app.config import settings

OFFLINE_QA_BANK = {
    "en": {
        "shade": "Take it easy, {name}! Follow the emerald-green shaded colonnade route on your map toward Arjuna's Penance Banyan Canopy to cut sun exposure significantly.",
        "history": "Mahabalipuram's Shore Temple was commissioned around 700 CE by Pallava king Narasimhavarman II (Rajasimha), {name}, crafted from solid coastal granite without mortar.",
        "next": "Here is your next direction, {name}: {next_guidance} Check the glowing cyan leg on your live site map!",
        "secret": "Here is a hidden architectural detail about {loc}, {name}: {stop_details}",
        "default": "We are at Stop {step}: {loc}, {name}. {stop_details} Tap Scan Relic on any carving card or ask me anything!"
    },
    "ta": {
        "shade": "{name}, வெயிலின் தாக்கத்தைக் குறைக்க வரைபடத்தில் உள்ள பச்சை நிழல் வழித்தடத்தைப் பின்பற்றி அரசமர நிழல் மண்டபத்திற்குச் செல்லுங்கள்.",
        "history": "{name}, மாமல்லபுரம் கடற்கரைக் கோயில் கி.பி 700-இல் பல்லவ மன்னர் இரண்டாம் நரசிம்மவர்மன் (ராஜசிம்மன்) காலத்தில் கருங்கற்களால் கட்டப்பட்டது.",
        "next": "{name}, அடுத்த இடத்திற்குச் செல்ல வரைபடத்தில் உள்ள நீலப் பாதையைப் பின்பற்றுங்கள்: {next_guidance}",
        "secret": "{name}, {loc} பற்றிய சிறப்புத் தகவல்: {stop_details}",
        "default": "{name}, நாம் இப்போது நிறுத்தம் {step} ({loc}) இல் இருக்கிறோம். சிற்ப அட்டையை ஸ்கேன் செய்யவும் அல்லது கேள்வி கேட்கவும்!"
    },
    "hi": {
        "shade": "{name}, धूप से बचने के लिए मानचित्र पर हरे रंग के छायादार मार्ग का अनुसरण करें और शीतल विश्राम मंडप की ओर बढ़ें।",
        "history": "{name}, महाबलीपुरम का शोर मंदिर लगभग 700 ईस्वी में पल्लव राजा नरसिंहवर्मन द्वितीय (राजसिंह) द्वारा ठोस ग्रेनाइट पत्थरों से बिना चूने के बनाया गया था।",
        "next": "{name}, अगले स्थान पर जाने के लिए मानचित्र पर चमकते नीले मार्ग का पालन करें: {next_guidance}",
        "secret": "{name}, {loc} का रोचक रहस्य: {stop_details}",
        "default": "{name}, हम अभी पड़ाव {step} ({loc}) पर हैं। शिल्प कार्ड को स्कैन करें या मुझसे कोई भी प्रश्न पूछें!"
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
            "You are Luna Aurora, a warm, authoritative historical guide walking alongside "
            f"{visitor_name} at Mahabalipuram Shore Temple Complex (UNESCO Heritage Site, Tamil Nadu).\n"
            "Rules:\n"
            f"- Address {visitor_name} naturally in 2 to 3 crisp spoken sentences.\n"
            f"- Respond strictly in {lang_label}.\n"
            "- Include real Pallava architectural facts, sunlight geometry, or cooling shade guidance.\n"
        )
        if current_step:
            prompt += f"\nCurrent Tour Stop: {current_step} of 7."
        if context_poi:
            prompt += f"\nLocation: {context_poi}."
        if stop_details:
            prompt += f"\nVerified Fact: {stop_details}"
        if next_guidance:
            prompt += f"\nNext Step Guidance: {next_guidance}"
        if relic_name:
            prompt += f"\nScanned Carving/Artifact: {relic_name}."
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
        """
        Returns (reply_text, fallback_cache_key, used_offline_fallback).
        Enforces strict 2.5s timeout on cloud API calls.
        """
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
        loc = context_poi or "Shore Temple Complex"
        bank = OFFLINE_QA_BANK.get(language, OFFLINE_QA_BANK["en"])

        if relic_name and language == "en":
            return (
                f"{name}, behold {relic_name}! Chiseled by 8th-century Pallava sculptors out of living coastal granite, "
                "its reliefs balance cosmic geometry with maritime endurance."
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
            stop_details=stop_details or "Built by Pallava artisans around 700 CE without mortar.",
            next_guidance=next_guidance or "Proceed to the next station along the shaded gallery."
        )
        return text, topic

groq_service = GroqGuideService()
