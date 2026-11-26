from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.vision_knowledge import vision_service
from app.services.tts_service import tts_service
from app.services.session_service import session_service
from app.models.entities import RelicArtifact, ScavengerQuest

router = APIRouter(prefix="/api/vision", tags=["Point and Know Discovery"])

class VisionDetectRequest(BaseModel):
    detected_labels: List[str]
    poi_id: Optional[int] = None
    current_step: Optional[int] = None
    session_id: Optional[str] = None
    language: str = "en"

@router.post("/identify")
async def identify_object(req: VisionDetectRequest, db: Session = Depends(get_db)):
    """
    Matches camera object detections from TensorFlow.js to monument knowledge base.
    Generates tailored audio narration, records discovery in session, and checks Scavenger Quests.
    """
    relic = vision_service.match_detection(db, req.detected_labels, current_step=req.current_step)
    if not relic:
        raise HTTPException(status_code=404, detail="No historical artifact matching detection found.")

    quest_unlocked = None
    session_progress = None

    # Check if this relic solves any Scavenger Quest
    matching_quest = db.query(ScavengerQuest).filter(
        ScavengerQuest.target_relic_code == relic["code"]
    ).first()

    badge_to_award = matching_quest.badge_name if matching_quest else None
    xp_to_award = matching_quest.points if matching_quest else 40

    if req.session_id and relic.get("confidence_match"):
        session_progress = session_service.record_relic_discovery(
            db, req.session_id, relic["code"], xp_bonus=xp_to_award, badge_name=badge_to_award
        )
        if matching_quest and session_progress.get("newly_discovered"):
            quest_unlocked = {
                "quest_id": matching_quest.quest_id,
                "title": matching_quest.title,
                "badge_name": matching_quest.badge_name,
                "points": matching_quest.points
            }

    audio_text = f"{relic['name']}. {relic['story']}"
    audio_url = await tts_service.generate_speech(audio_text, language=req.language)

    return {
        "artifact": relic,
        "audio_url": audio_url,
        "quest_unlocked": quest_unlocked,
        "session_progress": session_progress
    }

@router.get("/artifacts")
def list_artifacts(db: Session = Depends(get_db)):
    relics = db.query(RelicArtifact).all()
    return relics
