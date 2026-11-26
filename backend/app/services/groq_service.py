import os
from typing import List, Dict, Optional
from app.config import settings

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
                print(f"[GroqGuideService] Groq initialization warning: {e}")

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
        prompt = (
            "You are Luna Aurora, a warm, knowledgeable human-like historical tour guide "
            f"walking alongside {visitor_name} through the Grand Solstice Sun Temple Complex.\n"
            "Style guidelines:\n"
            f"- Address {visitor_name} naturally and conversationally.\n"
            "- Keep answers concise (2 to 3 crisp sentences) because your words are spoken aloud and shown as subtitles.\n"
            "- Mention concrete architectural details, sunlight alignments, and cooling shade spots.\n"
            f"- Respond strictly in language code '{language}'.\n"
        )
        if current_step:
            prompt += f"\nTour Progression: Currently at Stop {current_step} of 7."
        if context_poi:
            prompt += f"\nCurrent Visitor Location: {context_poi}."
        if stop_details:
            prompt += f"\nSite Historical Fact: {stop_details}"
        if next_guidance:
            prompt += f"\nNext Walking Guidance: {next_guidance}"
        if relic_name:
            prompt += f"\nCurrently Looking At: {relic_name} (Recognized by camera)."
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
    ) -> str:
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

                response = self.client.chat.completions.create(
                    model=settings.GROQ_MODEL,
                    messages=messages,
                    temperature=0.7,
                    max_tokens=220,
                    top_p=0.9
                )
                return response.choices[0].message.content.strip()
            except Exception as e:
                print(f"[GroqGuideService] Groq request error: {e}. Falling back to local contextual guide.")

        return self._generate_fallback(
            user_message, context_poi, relic_name, language, customer_name, current_step, stop_details, next_guidance
        )

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
    ) -> str:
        name = customer_name or "my friend"
        q = query.lower()
        loc = context_poi or "the Grand Solstice Sanctuary"

        if relic_name:
            return (
                f"{name}, behold this remarkable {relic_name}! Chiseled by master artisans over eight centuries ago, "
                "every contour was calibrated to catch the dawn sunlight."
            )
        if any(k in q for k in ("shade", "tired", "rest", "hot", "sun", "cool", "water")):
            return (
                f"Take it easy, {name}! Tap the green Shade button at the bottom and I'll guide you straight "
                "to the coolest banyan canopy and spring-fed rest benches."
            )
        if any(k in q for k in ("next", "where", "go", "walk", "map", "direction")):
            if next_guidance:
                return f"Here is your next direction, {name}: {next_guidance}"
            return (
                f"Follow our glowing cyan path on the live map, {name}. You can tap Next Stop whenever you arrive!"
            )
        if any(k in q for k in ("secret", "mystery", "hidden", "fact", "special", "why")):
            if stop_details:
                return f"Here is a hidden insight about {loc}, {name}: {stop_details}"
        if any(k in q for k in ("who", "built", "history", "when", "era", "old")):
            detail_part = f" {stop_details}" if stop_details else ""
            return (
                f"{loc} was crafted during the 11th-century Classical Era, {name}, aligned geometrically with the solstices.{detail_part}"
            )

        extra = f" {stop_details}" if stop_details else ""
        return (
            f"Right now we are at Stop {current_step or 1}: {loc}, {name}.{extra} Feel free to tap Scan Relic or ask me anything!"
        )

groq_service = GroqGuideService()
