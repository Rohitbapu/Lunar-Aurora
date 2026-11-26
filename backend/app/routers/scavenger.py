from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.entities import ScavengerQuest

router = APIRouter(prefix="/api/scavenger", tags=["Gamified AR Scavenger Hunt"])

class VerifySolveRequest(BaseModel):
    quest_id: str
    detected_code: str
    user_points: int = 0

@router.get("/quests")
def get_all_quests(db: Session = Depends(get_db)):
    quests = db.query(ScavengerQuest).all()
    return quests

@router.post("/verify")
def verify_quest_solution(req: VerifySolveRequest, db: Session = Depends(get_db)):
    quest = db.query(ScavengerQuest).filter(ScavengerQuest.quest_id == req.quest_id).first()
    if not quest:
        raise HTTPException(status_code=404, detail="Quest not found")

    is_correct = (quest.target_relic_code.lower() == req.detected_code.lower())

    if is_correct:
        return {
            "success": True,
            "badge_unlocked": quest.badge_name,
            "badge_icon": quest.badge_icon,
            "points_earned": quest.points,
            "total_points": req.user_points + quest.points,
            "celebration_message": f"Splendid discovery! You unlocked the '{quest.badge_name}'!"
        }
    else:
        return {
            "success": False,
            "message": "Not quite this one! Read the riddle carefully and check your surroundings.",
            "hint": quest.hint
        }

