from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.entities import RelicArtifact

CARD_IMAGE_MAP = {
    "shore_temple_vimana": "/static/cards/01_shore_temple_vimana.jpg",
    "pancha_rathas": "/static/cards/02_pancha_rathas.jpg",
    "arjunas_penance": "/static/cards/03_arjunas_penance.jpg",
    "krishnas_butter_ball": "/static/cards/04_krishnas_butter_ball.jpg",
    "mahishasuramardini_cave": "/static/cards/05_mahishasuramardini_cave.jpg",
}

class VisionKnowledgeService:
    def _serialize(self, relic: RelicArtifact, confident: bool = True) -> Dict[str, Any]:
        return {
            "code": relic.code,
            "name": relic.name,
            "style": relic.architectural_style,
            "period": relic.period,
            "story": relic.story,
            "fun_fact": relic.fun_fact,
            "audio_narrative": relic.audio_narrative,
            "image_url": CARD_IMAGE_MAP.get(relic.code),
            "source": relic.source,
            "confidence_match": confident
        }

    def match_detection(
        self,
        db: Session,
        detected_labels: List[str],
        current_step: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Matches verified classifier class IDs strictly against registered Mahabalipuram RelicArtifacts.
        Never guesses a relic from current_step when vision labels are empty or background.
        """
        detected_list = [lbl.lower().strip() for lbl in detected_labels if lbl]
        relics = db.query(RelicArtifact).all()
        if not relics:
            return None

        relic_by_code = {r.code: r for r in relics}

        for lbl in detected_list:
            if lbl in relic_by_code:
                return self._serialize(relic_by_code[lbl], confident=True)

        return {
            "code": "unregistered_feature",
            "name": "Unrecognized Monument Feature",
            "style": "Not matched to a registered carving card",
            "period": "Unknown",
            "story": "No registered Mahabalipuram carving class matched cleanly. Point at one of the 5 printed carving cards and tap SCAN RELIC.",
            "fun_fact": "",
            "audio_narrative": "",
            "image_url": None,
            "source": None,
            "confidence_match": False
        }

vision_service = VisionKnowledgeService()
