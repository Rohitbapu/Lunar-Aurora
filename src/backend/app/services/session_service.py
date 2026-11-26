import os
import uuid
import base64
import random
from datetime import datetime
from typing import Dict, Any, Optional, List
from fpdf import FPDF
from sqlalchemy.orm import Session
from app.config import settings
from app.models.entities import TourSession, BlueprintStop, POINode, RelicArtifact
from app.services.tts_service import tts_service

def _pdf_safe(text: str) -> str:
    """Sanitizes text so built-in FPDF Helvetica never fails on Unicode symbols."""
    if not text:
        return ""
    replacements = {
        "\u2022": "-",
        "\u2014": "--",
        "\u2013": "-",
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u00b0": " deg",
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    return text.encode("latin-1", "replace").decode("latin-1")

class SessionService:
    def create_ticket(self, db: Session, customer_name: str, language: str = "en") -> Dict[str, Any]:
        """
        Generates a new ticket at the ticketing counter / kiosk.
        """
        clean_name = customer_name.strip() if customer_name else "Honored Traveler"
        ticket_id = f"LUNA-{random.randint(1000, 9999)}"
        session_id = str(uuid.uuid4())

        new_session = TourSession(
            session_id=session_id,
            ticket_id=ticket_id,
            customer_name=clean_name,
            preferred_language=language,
            current_step=1,
            visited_steps=[1],
            completed_relics=[],
            solved_riddles=[],
            unlocked_badges=["Pallava Pilgrim Seal"],
            captured_photos=[],
            chat_history=[],
            total_xp=50,
            status="in_progress",
            created_at=datetime.utcnow(),
            last_active_at=datetime.utcnow()
        )
        db.add(new_session)
        db.commit()
        db.refresh(new_session)

        return {
            "ticket_id": ticket_id,
            "session_id": session_id,
            "customer_name": clean_name,
            "language": language,
            "current_step": 1,
            "total_xp": 50,
            "status": "in_progress"
        }

    async def get_or_resume_session(
        self,
        db: Session,
        session_id: Optional[str] = None,
        ticket_id: Optional[str] = None,
        generate_audio: bool = True
    ) -> Optional[Dict[str, Any]]:
        query = db.query(TourSession)
        session = None
        if session_id:
            session = query.filter(TourSession.session_id == session_id).first()
        elif ticket_id:
            session = query.filter(TourSession.ticket_id == ticket_id).first()

        if not session:
            return None

        session.last_active_at = datetime.utcnow()
        db.commit()

        stop = db.query(BlueprintStop).filter(BlueprintStop.step_number == session.current_step).first()
        poi = db.query(POINode).filter(POINode.id == (stop.poi_id if stop else 1)).first()

        stop_data = None
        if stop:
            stop_data = self._format_stop(stop, poi, session.customer_name, session.preferred_language)
            if generate_audio:
                audio_url = await tts_service.generate_speech(
                    stop_data["personalized_welcome"],
                    language=session.preferred_language,
                    fallback_cache_key=f"stop_{stop.step_number}"
                )
                stop_data["audio_url"] = audio_url

        return {
            "session_id": session.session_id,
            "ticket_id": session.ticket_id,
            "customer_name": session.customer_name,
            "language": session.preferred_language,
            "current_step": session.current_step,
            "visited_steps": session.visited_steps or [],
            "completed_relics": session.completed_relics or [],
            "solved_riddles": session.solved_riddles or [],
            "unlocked_badges": session.unlocked_badges or [],
            "captured_photos": session.captured_photos or [],
            "chat_history": session.chat_history or [],
            "total_xp": session.total_xp,
            "status": session.status,
            "current_stop": stop_data
        }

    async def advance_stop(self, db: Session, session_id: str) -> Dict[str, Any]:
        session = db.query(TourSession).filter(TourSession.session_id == session_id).first()
        if not session:
            raise ValueError("Session not found")

        total_stops = db.query(BlueprintStop).count()
        next_step = session.current_step + 1

        if next_step > total_stops:
            session.status = "completed"
            session.completed_at = datetime.utcnow()
            db.commit()
            return await self.end_session(db, session_id)

        session.current_step = next_step
        visited = list(session.visited_steps or [])
        if next_step not in visited:
            visited.append(next_step)
        session.visited_steps = visited
        session.total_xp += 75
        session.last_active_at = datetime.utcnow()
        db.commit()

        stop = db.query(BlueprintStop).filter(BlueprintStop.step_number == next_step).first()
        poi = db.query(POINode).filter(POINode.id == stop.poi_id).first()

        stop_data = self._format_stop(stop, poi, session.customer_name, session.preferred_language)
        audio_url = await tts_service.generate_speech(
            stop_data["personalized_welcome"],
            language=session.preferred_language,
            fallback_cache_key=f"stop_{stop.step_number}"
        )
        stop_data["audio_url"] = audio_url

        return {
            "session_id": session.session_id,
            "customer_name": session.customer_name,
            "current_step": next_step,
            "total_stops": total_stops,
            "total_xp": session.total_xp,
            "status": session.status,
            "stop": stop_data
        }

    def answer_riddle(self, db: Session, session_id: str, step_number: int, selected_answer: str) -> Dict[str, Any]:
        session = db.query(TourSession).filter(TourSession.session_id == session_id).first()
        if not session:
            raise ValueError("Session not found")
        stop = db.query(BlueprintStop).filter(BlueprintStop.step_number == step_number).first()
        if not stop:
            raise ValueError("Stop not found")

        expected = (stop.riddle_answer or "").strip().lower()
        chosen = (selected_answer or "").strip().lower()
        is_correct = bool(expected) and (chosen == expected or expected in chosen)

        solved = list(session.solved_riddles or [])
        newly_solved = False
        badge_name = f"Stop {step_number} Chronicle Solver"

        if is_correct and step_number not in solved:
            solved.append(step_number)
            session.solved_riddles = solved
            session.total_xp += 45
            badges = list(session.unlocked_badges or [])
            if badge_name not in badges:
                badges.append(badge_name)
                session.unlocked_badges = badges
            newly_solved = True

        session.last_active_at = datetime.utcnow()
        db.commit()

        return {
            "correct": is_correct,
            "newly_solved": newly_solved,
            "correct_answer": stop.riddle_answer,
            "xp_awarded": 45 if newly_solved else 0,
            "total_xp": session.total_xp,
            "solved_riddles": session.solved_riddles or [],
            "unlocked_badges": session.unlocked_badges or []
        }

    def save_photo(
        self,
        db: Session,
        session_id: str,
        stop_step: int,
        stop_title: str,
        image_base64: str
    ) -> Dict[str, Any]:
        session = db.query(TourSession).filter(TourSession.session_id == session_id).first()
        if not session:
            raise ValueError("Session not found")

        raw = image_base64 or ""
        if "," in raw:
            raw = raw.split(",", 1)[1]

        photo_id = f"snap_{session.ticket_id}_s{stop_step}_{uuid.uuid4().hex[:6]}.jpg"
        filepath = os.path.join(settings.PHOTOS_DIR, photo_id)
        try:
            img_bytes = base64.b64decode(raw, validate=False)
            if len(img_bytes) > 0:
                with open(filepath, "wb") as f:
                    f.write(img_bytes)
        except Exception as e:
            print(f"[SessionService] Photo decode warning: {e}")

        photos = list(session.captured_photos or [])
        entry = {
            "photo_id": photo_id,
            "photo_url": f"/static/photos/{photo_id}",
            "filepath": filepath,
            "stop_step": stop_step,
            "stop_title": stop_title,
            "captured_at": datetime.utcnow().isoformat(timespec="seconds") + "Z"
        }
        photos.append(entry)
        session.captured_photos = photos[-10:]
        session.total_xp += 20
        session.last_active_at = datetime.utcnow()
        db.commit()

        return {
            "saved": True,
            "photo_url": entry["photo_url"],
            "photo_count": len(session.captured_photos),
            "total_xp": session.total_xp
        }

    def generate_pdf_journal(
        self,
        db: Session,
        session_id: str,
        inline_photos: Optional[List[Dict[str, Any]]] = None
    ) -> bytes:
        session = db.query(TourSession).filter(TourSession.session_id == session_id).first()
        if not session:
            raise ValueError("Session not found")

        stops = db.query(BlueprintStop).order_by(BlueprintStop.step_number).all()
        relics = {r.code: r for r in db.query(RelicArtifact).all()}

        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()

        # Header banner
        pdf.set_fill_color(10, 14, 23)
        pdf.rect(0, 0, 210, 40, style="F")
        pdf.set_text_color(0, 229, 255)
        pdf.set_font("Helvetica", "B", 20)
        pdf.set_xy(14, 10)
        pdf.cell(0, 10, _pdf_safe("LUNAR AURORA - HERITAGE TRAVEL JOURNAL"), ln=True)
        pdf.set_text_color(244, 196, 48)
        pdf.set_font("Helvetica", "", 11)
        pdf.set_x(14)
        pdf.cell(0, 7, _pdf_safe("Mahabalipuram Shore Temple Heritage Sanctuary (UNESCO World Heritage Site)"), ln=True)

        pdf.ln(14)
        pdf.set_text_color(20, 28, 42)
        pdf.set_font("Helvetica", "B", 13)
        pdf.cell(0, 8, _pdf_safe(f"Visitor Profile: {session.customer_name}"), ln=True)
        pdf.set_font("Helvetica", "", 11)
        pdf.cell(0, 7, _pdf_safe(f"Ticket ID: {session.ticket_id}   |   Language: {session.preferred_language.upper()}   |   Total XP: {session.total_xp}"), ln=True)
        pdf.cell(0, 7, _pdf_safe(f"Stations Explored: {len(session.visited_steps or [])} of {len(stops)}   |   Riddles Solved: {len(session.solved_riddles or [])}"), ln=True)
        pdf.ln(4)

        # Badges
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(0, 100, 130)
        pdf.cell(0, 8, _pdf_safe("Earned Heritage Badges & Seals"), ln=True)
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(40, 48, 60)
        badges_str = ", ".join(session.unlocked_badges or ["Pallava Pilgrim Seal"])
        pdf.multi_cell(0, 6, _pdf_safe(badges_str))
        pdf.ln(4)

        # Discovered Carvings
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(0, 100, 130)
        pdf.cell(0, 8, _pdf_safe("Scanned Monument Carvings & Inscriptions"), ln=True)
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(40, 48, 60)
        completed_relics = session.completed_relics or []
        if not completed_relics:
            pdf.set_x(pdf.l_margin)
            pdf.multi_cell(pdf.epw, 6, _pdf_safe("No carving cards scanned yet. Scan any of the 5 Mahabalipuram cards during your walk!"))
        else:
            for code in completed_relics:
                art = relics.get(code)
                if art:
                    pdf.set_x(pdf.l_margin)
                    pdf.set_font("Helvetica", "B", 10)
                    pdf.cell(pdf.epw, 6, _pdf_safe(f"- {art.name} ({art.period})"), new_x="LMARGIN", new_y="NEXT")
                    pdf.set_x(pdf.l_margin)
                    pdf.set_font("Helvetica", "", 9)
                    pdf.multi_cell(pdf.epw, 5, _pdf_safe(art.story))
                    if art.source:
                        pdf.set_x(pdf.l_margin)
                        pdf.multi_cell(pdf.epw, 4.5, _pdf_safe(f"Source: {art.source}"), wrapmode="CHAR")
                    pdf.ln(1)
        pdf.ln(3)

        # Itinerary Progress
        pdf.set_x(pdf.l_margin)
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(0, 100, 130)
        pdf.cell(pdf.epw, 8, _pdf_safe("7-Stop Mahabalipuram Itinerary Log"), new_x="LMARGIN", new_y="NEXT")
        visited_set = set(session.visited_steps or [])
        solved_set = set(session.solved_riddles or [])
        for s in stops:
            mark = "[VISITED]" if s.step_number in visited_set else "[PLANNED]"
            riddle_mark = " | Riddle Solved" if s.step_number in solved_set else ""
            pdf.set_x(pdf.l_margin)
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(20, 28, 42)
            pdf.cell(pdf.epw, 6, _pdf_safe(f"{s.step_number}. {s.title} ({s.era}) {mark}{riddle_mark}"), new_x="LMARGIN", new_y="NEXT")
            pdf.set_x(pdf.l_margin)
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(70, 80, 95)
            pdf.multi_cell(pdf.epw, 5, _pdf_safe(s.script_details))
            if s.source:
                pdf.set_x(pdf.l_margin)
                pdf.multi_cell(pdf.epw, 4.5, _pdf_safe(f"Source: {s.source}"), wrapmode="CHAR")
            pdf.ln(1)

        # Captured Memory Snapshots
        all_photos = list(session.captured_photos or [])
        if inline_photos:
            for idx, item in enumerate(inline_photos[:4]):
                raw = item.get("image_base64", "")
                if "," in raw:
                    raw = raw.split(",", 1)[1]
                tmp_path = os.path.join(settings.PHOTOS_DIR, f"inline_{session.ticket_id}_{idx}.jpg")
                try:
                    data = base64.b64decode(raw, validate=False)
                    if data:
                        with open(tmp_path, "wb") as tf:
                            tf.write(data)
                        all_photos.append({
                            "filepath": tmp_path,
                            "stop_title": item.get("stop_title", "Shore Temple Memory"),
                            "captured_at": item.get("captured_at", "")
                        })
                except Exception:
                    pass

        valid_imgs = [p for p in all_photos if p.get("filepath") and os.path.exists(p["filepath"])]
        if valid_imgs:
            pdf.add_page()
            pdf.set_font("Helvetica", "B", 13)
            pdf.set_text_color(0, 100, 130)
            pdf.cell(0, 8, _pdf_safe("Captured Field Photographs"), ln=True)
            pdf.ln(3)
            for p in valid_imgs[:4]:
                try:
                    pdf.set_font("Helvetica", "B", 10)
                    pdf.set_text_color(30, 40, 55)
                    pdf.cell(0, 6, _pdf_safe(f"{p.get('stop_title', 'Station Snapshot')} ({p.get('captured_at', '')})"), ln=True)
                    pdf.image(p["filepath"], w=120)
                    pdf.ln(4)
                except Exception as img_err:
                    print(f"[SessionService] PDF photo embed warning: {img_err}")

        out = pdf.output()
        return bytes(out)

    def append_chat_turn(self, db: Session, session_id: str, user_msg: str, guide_reply: str) -> None:
        session = db.query(TourSession).filter(TourSession.session_id == session_id).first()
        if not session:
            return
        history = list(session.chat_history or [])
        history.append({"role": "user", "content": user_msg})
        history.append({"role": "assistant", "content": guide_reply})
        session.chat_history = history[-20:]
        session.last_active_at = datetime.utcnow()
        db.commit()

    def record_relic_discovery(self, db: Session, session_id: str, relic_code: str, xp_bonus: int = 40, badge_name: Optional[str] = None) -> Dict[str, Any]:
        session = db.query(TourSession).filter(TourSession.session_id == session_id).first()
        if not session:
            return {"total_xp": 0, "newly_discovered": False}

        completed = list(session.completed_relics or [])
        newly_discovered = relic_code not in completed and relic_code != "unregistered_feature"
        if newly_discovered:
            completed.append(relic_code)
            session.completed_relics = completed
            session.total_xp += xp_bonus

        if badge_name:
            badges = list(session.unlocked_badges or [])
            if badge_name not in badges:
                badges.append(badge_name)
                session.unlocked_badges = badges

        session.last_active_at = datetime.utcnow()
        db.commit()
        return {
            "total_xp": session.total_xp,
            "newly_discovered": newly_discovered,
            "completed_relics": session.completed_relics,
            "unlocked_badges": session.unlocked_badges
        }

    async def end_session(self, db: Session, session_id: str) -> Dict[str, Any]:
        session = db.query(TourSession).filter(TourSession.session_id == session_id).first()
        if not session:
            raise ValueError("Session not found")

        session.status = "completed"
        if not session.completed_at:
            session.completed_at = datetime.utcnow()
        db.commit()

        total_stops = db.query(BlueprintStop).count()
        completed_count = len(session.visited_steps or [])

        farewell = (
            f"Thank you, {session.customer_name}! You have completed the 7-stop Pallava journey across Mahabalipuram Shore Temple. "
            f"You explored {completed_count} of {total_stops} sacred stations and earned {session.total_xp} XP. "
            "Download your illustrated PDF Travel Journal below!"
        )

        audio_url = await tts_service.generate_speech(
            farewell,
            language=session.preferred_language,
            fallback_cache_key="farewell"
        )

        return {
            "session_id": session.session_id,
            "customer_name": session.customer_name,
            "ticket_id": session.ticket_id,
            "status": "completed",
            "stops_completed": completed_count,
            "total_stops": total_stops,
            "total_xp": session.total_xp,
            "badges": session.unlocked_badges or ["Pallava Pilgrim Seal"],
            "solved_riddles": session.solved_riddles or [],
            "completed_relics": session.completed_relics or [],
            "photo_count": len(session.captured_photos or []),
            "farewell_message": farewell,
            "audio_url": audio_url
        }

    def _format_stop(self, stop: BlueprintStop, poi: POINode, customer_name: str, language: str) -> Dict[str, Any]:
        welcome = stop.script_welcome.replace("{name}", customer_name)
        details = stop.script_details.replace("{name}", customer_name)
        guidance = stop.next_step_guidance.replace("{name}", customer_name)

        return {
            "step_number": stop.step_number,
            "poi_id": stop.poi_id,
            "title": stop.title,
            "subtitle": stop.subtitle,
            "era": stop.era,
            "poi_name": poi.name if poi else stop.title,
            "x": poi.x if poi else 0.0,
            "y": poi.y if poi else 0.0,
            "latitude": poi.latitude if poi else 12.6165,
            "longitude": poi.longitude if poi else 80.1993,
            "has_benches": poi.has_benches if poi else False,
            "has_water": poi.has_water if poi else False,
            "personalized_welcome": welcome,
            "script_details": details,
            "next_step_guidance": guidance,
            "distance_to_next": stop.distance_to_next,
            "walking_time_mins": stop.walking_time_mins,
            "shade_rating": stop.shade_rating,
            "target_relic_code": stop.target_relic_code,
            "badge_reward": stop.badge_reward,
            "model_asset_url": poi.model_asset_url if poi else None,
            "source": stop.source,
            "riddle": {
                "question": stop.riddle_question,
                "options": stop.riddle_options or [],
                "answer": stop.riddle_answer
            } if stop.riddle_question else None,
            "audio_url": None
        }

session_service = SessionService()
