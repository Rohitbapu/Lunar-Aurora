import uuid
import random
from datetime import datetime
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from app.models.entities import TourSession, BlueprintStop, POINode, RelicArtifact
from app.services.tts_service import tts_service

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
            unlocked_badges=["Explorer Crest"],
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
        """
        Recovers a session if user refreshed, closed the browser, or was interrupted by a phone call.
        Synthesizes TTS audio for the active stop so welcome/resume always has voice playback.
        """
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

        # Fetch current blueprint stop
        stop = db.query(BlueprintStop).filter(BlueprintStop.step_number == session.current_step).first()
        poi = db.query(POINode).filter(POINode.id == (stop.poi_id if stop else 1)).first()

        stop_data = None
        if stop:
            stop_data = self._format_stop(stop, poi, session.customer_name, session.preferred_language)
            if generate_audio:
                audio_url = await tts_service.generate_speech(
                    stop_data["personalized_welcome"],
                    language=session.preferred_language
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
            "unlocked_badges": session.unlocked_badges or [],
            "chat_history": session.chat_history or [],
            "total_xp": session.total_xp,
            "status": session.status,
            "current_stop": stop_data
        }

    async def advance_stop(self, db: Session, session_id: str) -> Dict[str, Any]:
        """
        Progresses user to the next blueprint stop in the curated tour.
        """
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

        # Generate personalized narration audio matching the spoken subtitle script
        audio_url = await tts_service.generate_speech(
            stop_data["personalized_welcome"],
            language=session.preferred_language
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
        """
        Finalizes the tour and returns a summary certificate.
        """
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
            f"Thank you, {session.customer_name}! You have completed the grand tour of the Solstice Sanctuary. "
            f"You discovered {completed_count} of {total_stops} historical stations and earned {session.total_xp} XP. "
            "May the wisdom of the ancient artisans stay with you always!"
        )

        audio_url = await tts_service.generate_speech(farewell, language=session.preferred_language)

        return {
            "session_id": session.session_id,
            "customer_name": session.customer_name,
            "ticket_id": session.ticket_id,
            "status": "completed",
            "stops_completed": completed_count,
            "total_stops": total_stops,
            "total_xp": session.total_xp,
            "badges": session.unlocked_badges or ["Master Heritage Seeker"],
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
            "audio_url": None
        }

session_service = SessionService()
