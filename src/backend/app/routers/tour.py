from fastapi import APIRouter, Depends, HTTPException, Body
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.session_service import session_service

router = APIRouter(prefix="/api/tour", tags=["Travel Journal & Memories"])

class PhotoCaptureRequest(BaseModel):
    stop_step: int = 1
    stop_title: str = "Mahabalipuram Station"
    image_base64: str

class JournalExportRequest(BaseModel):
    photos: Optional[List[Dict[str, Any]]] = None

@router.post("/{session_id}/photo")
def upload_tour_photo(session_id: str, req: PhotoCaptureRequest, db: Session = Depends(get_db)):
    """Stores a timestamped + watermarked AR snapshot for the PDF Travel Journal."""
    try:
        return session_service.save_photo(
            db,
            session_id=session_id,
            stop_step=req.stop_step,
            stop_title=req.stop_title,
            image_base64=req.image_base64
        )
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{session_id}/journal")
def export_pdf_journal(
    session_id: str,
    req: Optional[JournalExportRequest] = Body(default=None),
    db: Session = Depends(get_db)
):
    """Generates and streams a downloadable multi-page PDF Heritage Travel Journal."""
    try:
        inline_photos = req.photos if req else None
        pdf_bytes = session_service.generate_pdf_journal(db, session_id=session_id, inline_photos=inline_photos)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="LunarAurora_Journal_{session_id[:8]}.pdf"'}
        )
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{session_id}/journal")
def download_pdf_journal(session_id: str, db: Session = Depends(get_db)):
    try:
        pdf_bytes = session_service.generate_pdf_journal(db, session_id=session_id)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="LunarAurora_Journal_{session_id[:8]}.pdf"'}
        )
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
