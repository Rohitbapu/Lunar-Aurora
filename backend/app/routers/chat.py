from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.entities import BlueprintStop
from app.services.groq_service import groq_service
from app.services.tts_service import tts_service
from app.services.session_service import session_service

router = APIRouter(prefix="/api/chat", tags=["AI Tour Guide Chat"])

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[Dict[str, str]]] = []
    context_poi: Optional[str] = None
    relic_name: Optional[str] = None
    language: str = "en"
    customer_name: Optional[str] = None
    current_step: Optional[int] = None
    session_id: Optional[str] = None
    generate_audio: bool = True

class ChatResponse(BaseModel):
    reply: str
    audio_url: Optional[str] = None
    language: str
    voice_used: str

@router.post("", response_model=ChatResponse)
async def chat_with_guide(req: ChatRequest, db: Session = Depends(get_db)):
    """
    Real-time conversational response with Groq Llama 3 and Edge-TTS voice generation.
    Injects live blueprint stop context and saves chat history into the visitor's session.
    """
    try:
        stop_details = None
        next_guidance = None
        context_poi = req.context_poi

        if req.current_step:
            stop = db.query(BlueprintStop).filter(BlueprintStop.step_number == req.current_step).first()
            if stop:
                context_poi = context_poi or stop.title
                stop_details = stop.script_details
                next_guidance = stop.next_step_guidance

        reply_text = await groq_service.get_response(
            user_message=req.message,
            history=req.history,
            context_poi=context_poi,
            relic_name=req.relic_name,
            language=req.language,
            customer_name=req.customer_name,
            current_step=req.current_step,
            stop_details=stop_details,
            next_guidance=next_guidance
        )

        # Persist conversation turn inside active visitor session
        if req.session_id:
            session_service.append_chat_turn(db, req.session_id, req.message, reply_text)

        audio_url = ""
        if req.generate_audio:
            audio_url = await tts_service.generate_speech(reply_text, language=req.language)

        return ChatResponse(
            reply=reply_text,
            audio_url=audio_url,
            language=req.language,
            voice_used="edge-tts"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
