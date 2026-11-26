from sqlalchemy import Column, Integer, String, Float, Boolean, Text, ForeignKey, JSON, DateTime
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()

class POINode(Base):
    __tablename__ = "poi_nodes"

    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String(64), unique=True, index=True)
    name = Column(String(128), nullable=False)
    category = Column(String(64), default="monument")
    description = Column(Text, nullable=False)
    historical_era = Column(String(64), default="8th Century CE Pallava Dynasty")

    # Local coordinate frame (meters from Shore Temple entry) and GPS
    x = Column(Float, nullable=False)
    y = Column(Float, nullable=False)
    z = Column(Float, default=0.0)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    has_benches = Column(Boolean, default=False)
    has_water = Column(Boolean, default=False)
    has_tree_shade = Column(Boolean, default=False)
    average_ambient_temp_c = Column(Float, default=33.5)

    model_asset_url = Column(String(256), nullable=True)
    audio_story_url = Column(String(256), nullable=True)

class PathEdge(Base):
    __tablename__ = "path_edges"

    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, ForeignKey("poi_nodes.id"), nullable=False)
    target_id = Column(Integer, ForeignKey("poi_nodes.id"), nullable=False)
    distance_meters = Column(Float, nullable=False)
    base_shade_factor = Column(Float, default=0.2)
    path_type = Column(String(32), default="colonnade")
    is_accessible = Column(Boolean, default=True)

class RelicArtifact(Base):
    __tablename__ = "relic_artifacts"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(64), unique=True, index=True)
    name = Column(String(128), nullable=False)
    poi_id = Column(Integer, ForeignKey("poi_nodes.id"), nullable=True)
    detection_labels = Column(JSON, default=list)
    architectural_style = Column(String(128), default="Pallava Dravidian Granite")
    period = Column(String(64), default="700–728 CE")
    story = Column(Text, nullable=False)
    fun_fact = Column(Text, nullable=True)
    audio_narrative = Column(Text, nullable=True)

class ScavengerQuest(Base):
    __tablename__ = "scavenger_quests"

    id = Column(Integer, primary_key=True, index=True)
    quest_id = Column(String(64), unique=True, index=True)
    title = Column(String(128), nullable=False)
    riddle = Column(Text, nullable=False)
    target_poi_slug = Column(String(64), nullable=False)
    target_relic_code = Column(String(64), nullable=True)
    hint = Column(Text, nullable=False)
    badge_name = Column(String(128), nullable=False)
    badge_icon = Column(String(64), default="fa-trophy")
    points = Column(Integer, default=100)

class BlueprintStop(Base):
    __tablename__ = "blueprint_stops"

    id = Column(Integer, primary_key=True, index=True)
    step_number = Column(Integer, unique=True, index=True)
    poi_id = Column(Integer, ForeignKey("poi_nodes.id"), nullable=False)
    title = Column(String(128), nullable=False)
    subtitle = Column(String(128), nullable=False)
    era = Column(String(64), default="8th Century CE")
    script_welcome = Column(Text, nullable=False)
    script_details = Column(Text, nullable=False)
    next_step_guidance = Column(Text, nullable=False)
    distance_to_next = Column(Float, default=45.0)
    walking_time_mins = Column(Float, default=1.5)
    shade_rating = Column(String(32), default="HIGH SHADE")
    target_relic_code = Column(String(64), nullable=True)
    badge_reward = Column(String(64), nullable=True)
    xp_reward = Column(Integer, default=50)
    # Per-stop interactive riddle
    riddle_question = Column(Text, nullable=True)
    riddle_options = Column(JSON, default=list)
    riddle_answer = Column(String(128), nullable=True)

class TourSession(Base):
    __tablename__ = "tour_sessions"

    session_id = Column(String(64), primary_key=True, index=True)
    ticket_id = Column(String(32), unique=True, index=True)
    customer_name = Column(String(128), nullable=False)
    preferred_language = Column(String(16), default="en")

    current_step = Column(Integer, default=1)
    visited_steps = Column(JSON, default=list)
    completed_relics = Column(JSON, default=list)
    solved_riddles = Column(JSON, default=list)
    unlocked_badges = Column(JSON, default=list)
    captured_photos = Column(JSON, default=list)
    chat_history = Column(JSON, default=list)
    total_xp = Column(Integer, default=50)

    status = Column(String(32), default="in_progress")
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
