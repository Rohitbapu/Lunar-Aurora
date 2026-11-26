from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.entities import RelicArtifact, BlueprintStop

class VisionKnowledgeService:
    def match_detection(
        self,
        db: Session,
        detected_labels: List[str],
        current_step: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Matches detected camera labels to registered archaeological artifacts.
        If labels are generic or the visitor is standing at a curated blueprint stop,
        prioritizes matching the relic located at their current stop!
        """
        detected_set = {lbl.lower().strip() for lbl in detected_labels if lbl}

        relics = db.query(RelicArtifact).all()
        if not relics:
            return None

        best_relic = None
        best_overlap = 0

        for r in relics:
            relic_labels = [l.lower().strip() for l in (r.detection_labels or [])]
            overlap = len(detected_set.intersection(relic_labels))
            if overlap > best_overlap:
                best_overlap = overlap
                best_relic = r

        # If exact TF.js label match found (e.g. elephant, clock/sundial, fountain/bowl, person/dancer)
        if best_relic and best_overlap > 0:
            return {
                "code": best_relic.code,
                "name": best_relic.name,
                "style": best_relic.architectural_style,
                "period": best_relic.period,
                "story": best_relic.story,
                "fun_fact": best_relic.fun_fact,
                "audio_narrative": best_relic.audio_narrative,
                "confidence_match": True
            }

        # Context-aware matching: if tourist is standing at a stop with a target relic
        if current_step:
            stop = db.query(BlueprintStop).filter(BlueprintStop.step_number == current_step).first()
            if stop and stop.target_relic_code:
                stop_relic = db.query(RelicArtifact).filter(RelicArtifact.code == stop.target_relic_code).first()
                if stop_relic:
                    return {
                        "code": stop_relic.code,
                        "name": stop_relic.name,
                        "style": stop_relic.architectural_style,
                        "period": stop_relic.period,
                        "story": stop_relic.story,
                        "fun_fact": stop_relic.fun_fact,
                        "audio_narrative": stop_relic.audio_narrative,
                        "confidence_match": True
                    }

        # Informative non-match response
        return {
            "code": "unregistered_feature",
            "name": "Ancient Stonework",
            "style": "Classical Granite Masonry",
            "period": "11th–12th Century CE",
            "story": f"You are scanning carved stonework in the courtyard ({', '.join(detected_labels[:2]) if detected_labels else 'granite surface'}). Aim directly at the elephant relief, solar dial, lotus basin, or dancer frieze to unlock its hidden story!",
            "fun_fact": "Every granite block was fitted using dry interlocking mortise-and-tenon joints without mortar.",
            "audio_narrative": "Look along the surrounding colonnade pillars for sculpted reliefs.",
            "confidence_match": False
        }

vision_service = VisionKnowledgeService()
