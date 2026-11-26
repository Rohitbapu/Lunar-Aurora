from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.session_service import session_service
from app.models.entities import BlueprintStop, TourSession, POINode

router = APIRouter(prefix="/api/session", tags=["Tour Session & Curated Progression"])

class StartSessionRequest(BaseModel):
    ticket_id: Optional[str] = None
    session_id: Optional[str] = None
    customer_name: Optional[str] = "Traveler"
    preferred_language: str = "en"
    generate_audio: bool = True

class AdvanceStopRequest(BaseModel):
    session_id: str

class EndSessionRequest(BaseModel):
    session_id: str

class RiddleAnswerRequest(BaseModel):
    session_id: str
    step_number: int
    answer: str

@router.post("/start")
async def start_or_resume_tour(req: StartSessionRequest, db: Session = Depends(get_db)):
    """
    Called when visitor scans QR code or returns after interruption (phone call / app reload).
    Recovers or initializes session with their personalized name, progress, and audio narration.
    """
    session_data = None
    if req.session_id or req.ticket_id:
        session_data = await session_service.get_or_resume_session(
            db, req.session_id, req.ticket_id, generate_audio=req.generate_audio
        )

    # If no session existed, create a new one automatically
    if not session_data:
        ticket = session_service.create_ticket(db, req.customer_name or "Honored Traveler", req.preferred_language)
        session_data = await session_service.get_or_resume_session(
            db, session_id=ticket["session_id"], generate_audio=req.generate_audio
        )

    return session_data

@router.get("/{session_id}")
async def get_session_status(session_id: str, db: Session = Depends(get_db)):
    session_data = await session_service.get_or_resume_session(db, session_id=session_id, generate_audio=False)
    if not session_data:
        raise HTTPException(status_code=404, detail="Tour session not found")
    return session_data

@router.post("/advance")
async def advance_to_next_stop(req: AdvanceStopRequest, db: Session = Depends(get_db)):
    """
    Moves visitor to the next blueprint stop in the curated sequence.
    """
    try:
        result = await session_service.advance_stop(db, req.session_id)
        return result
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/end")
async def end_tour(req: EndSessionRequest, db: Session = Depends(get_db)):
    """
    Visitor ends the tour. Returns certificate and completion stats.
    """
    try:
        result = await session_service.end_session(db, req.session_id)
        return result
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/riddle")
def submit_riddle_answer(req: RiddleAnswerRequest, db: Session = Depends(get_db)):
    try:
        return session_service.answer_riddle(db, req.session_id, req.step_number, req.answer)
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{session_id}/blueprint")
def get_full_blueprint(session_id: str, db: Session = Depends(get_db)):
    """
    Returns all 7 stops of the master blueprint with coordinates for rendering the live interactive map.
    """
    session = db.query(TourSession).filter(TourSession.session_id == session_id).first()
    stops = db.query(BlueprintStop).order_by(BlueprintStop.step_number).all()

    blueprint_list = []
    for s in stops:
        poi = db.query(POINode).filter(POINode.id == s.poi_id).first()
        is_visited = bool(session and (s.step_number in (session.visited_steps or [])))
        is_current = bool(session and (s.step_number == session.current_step))

        blueprint_list.append({
            "step_number": s.step_number,
            "poi_id": s.poi_id,
            "title": s.title,
            "subtitle": s.subtitle,
            "era": s.era,
            "poi_name": poi.name if poi else s.title,
            "x": poi.x if poi else 0.0,
            "y": poi.y if poi else 0.0,
            "latitude": poi.latitude if poi else 12.6165,
            "longitude": poi.longitude if poi else 80.1993,
            "model_asset_url": poi.model_asset_url if poi else None,
            "target_relic_code": s.target_relic_code,
            "source": s.source,
            "riddle": {
                "question": s.riddle_question,
                "options": s.riddle_options or [],
                "answer": s.riddle_answer
            } if s.riddle_question else None,
            "has_benches": poi.has_benches if poi else False,
            "has_water": poi.has_water if poi else False,
            "shade_rating": s.shade_rating,
            "is_visited": is_visited,
            "is_current": is_current,
            "distance_to_next": s.distance_to_next,
            "walking_time_mins": s.walking_time_mins
        })

    return {
        "total_steps": len(blueprint_list),
        "current_step": session.current_step if session else 1,
        "customer_name": session.customer_name if session else "Traveler",
        "stops": blueprint_list
    }
