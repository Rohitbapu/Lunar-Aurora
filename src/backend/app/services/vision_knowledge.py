from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.entities import RelicArtifact, BlueprintStop

# Aliases mapping custom carving card labels & COCO-SSD fallbacks to canonical Mahabalipuram relic codes
CARD_ALIASES = {
    "shore_temple_vimana": "shore_temple_vimana",
    "vimana": "shore_temple_vimana",
    "spire": "shore_temple_vimana",
    "temple": "shore_temple_vimana",
    "sanctum": "shore_temple_vimana",
    "chariot_wheel": "chariot_wheel",
    "sundial_pillar": "chariot_wheel",
    "wheel": "chariot_wheel",
    "sundial": "chariot_wheel",
    "gnomon": "chariot_wheel",
    "clock": "chariot_wheel",
    "yali_pillar": "yali_pillar",
    "carved_elephant": "yali_pillar",
    "yali": "yali_pillar",
    "elephant": "yali_pillar",
    "pillar": "yali_pillar",
    "lion": "yali_pillar",
    "nataraja_relief": "nataraja_relief",
    "dancing_shiva": "nataraja_relief",
    "nataraja": "nataraja_relief",
    "dancer": "nataraja_relief",
    "shiva": "nataraja_relief",
    "person": "nataraja_relief",
    "lotus_basin": "lotus_basin",
    "lotus_fountain": "lotus_basin",
    "lotus": "lotus_basin",
    "fountain": "lotus_basin",
    "basin": "lotus_basin",
    "bowl": "lotus_basin",
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
            "confidence_match": confident
        }

    def match_detection(
        self,
        db: Session,
        detected_labels: List[str],
        current_step: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Matches detected carving card classes or COCO-SSD labels to registered Mahabalipuram artifacts.
        Supports both canonical card IDs and legacy aliases.
        """
        detected_list = [lbl.lower().strip() for lbl in detected_labels if lbl]
        relics = db.query(RelicArtifact).all()
        if not relics:
            return None

        relic_by_code = {r.code: r for r in relics}

        # 1. Direct alias or exact carving-card class match
        for lbl in detected_list:
            canonical = CARD_ALIASES.get(lbl)
            if canonical and canonical in relic_by_code:
                return self._serialize(relic_by_code[canonical], confident=True)
            if lbl in relic_by_code:
                return self._serialize(relic_by_code[lbl], confident=True)

        # 2. Label overlap match against RelicArtifact.detection_labels
        detected_set = set(detected_list)
        best_relic = None
        best_overlap = 0
        for r in relics:
            relic_labels = [l.lower().strip() for l in (r.detection_labels or [])]
            overlap = len(detected_set.intersection(relic_labels))
            if overlap > best_overlap:
                best_overlap = overlap
                best_relic = r

        if best_relic and best_overlap > 0:
            return self._serialize(best_relic, confident=True)

        # 3. Context-aware fallback: match the relic stationed at visitor's current stop
        if current_step:
            stop = db.query(BlueprintStop).filter(BlueprintStop.step_number == current_step).first()
            if stop and stop.target_relic_code and stop.target_relic_code in relic_by_code:
                return self._serialize(relic_by_code[stop.target_relic_code], confident=True)

        # 4. Informative non-match response
        return {
            "code": "unregistered_feature",
            "name": "Pallava Coastal Granite Masonry",
            "style": "Dry-Jointed Dravidian Stone",
            "period": "700-728 CE",
            "story": (
                f"Scanned courtyard masonry ({', '.join(detected_labels[:2]) if detected_labels else 'granite surface'}). "
                "Aim steadily at one of the 5 printable carving cards: Shore Temple Vimana, Chariot Wheel, Yali Pillar, Nataraja Relief, or Royal Lotus Basin."
            ),
            "fun_fact": "Every Mahabalipuram granite block was interlocked without lime mortar to resist sea-salt winds.",
            "audio_narrative": "Center your camera over a sacred Pallava relief card for 3D architectural reconstruction.",
            "confidence_match": False
        }

vision_service = VisionKnowledgeService()
