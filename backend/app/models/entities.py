from sqlalchemy import Column, Integer, String, Float, Boolean, Text, ForeignKey, JSON, DateTime
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()

class POINode(Base):
    __tablename__ = "poi_nodes"

    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String(64), unique=True, index=True)
    name = Column(String(128), nullable=False)
    category = Column(String(64), default="monument") # monument, shade_rest, water, entrance
    description = Column(Text, nullable=False)
    historical_era = Column(String(64), default="Ancient Dynasty")
    
    # Local coordinate frame (meters from site origin) and GPS
    x = Column(Float, nullable=False)
    y = Column(Float, nullable=False)
    z = Column(Float, default=0.0)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    
    # Amenities & Environmental state
    has_benches = Column(Boolean, default=False)
    has_water = Column(Boolean, default=False)
    has_tree_shade = Column(Boolean, default=False)
    average_ambient_temp_c = Column(Float, default=32.0)
    
    model_asset_url = Column(String(256), nullable=True)
    audio_story_url = Column(String(256), nullable=True)

class PathEdge(Base):
    __tablename__ = "path_edges"

    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, ForeignKey("poi_nodes.id"), nullable=False)
    target_id = Column(Integer, ForeignKey("poi_nodes.id"), nullable=False)
    distance_meters = Column(Float, nullable=False)
    base_shade_factor = Column(Float, default=0.2) # 0.0 = fully exposed sun, 1.0 = deep canopy/colonnade
    path_type = Column(String(32), default="colonnade") # open_stone, tree_avenue, covered_corridor
    is_accessible = Column(Boolean, default=True)

class RelicArtifact(Base):
    __tablename__ = "relic_artifacts"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(64), unique=True, index=True)
    name = Column(String(128), nullable=False)
    poi_id = Column(Integer, ForeignKey("poi_nodes.id"), nullable=True)
    detection_labels = Column(JSON, default=list)
    architectural_style = Column(String(128), default="Classical Monolithic")
    period = Column(String(64), default="11th Century CE")
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
    step_number = Column(Integer, unique=True, index=True) # 1 to 7
    poi_id = Column(Integer, ForeignKey("poi_nodes.id"), nullable=False)
    title = Column(String(128), nullable=False)
    subtitle = Column(String(128), nullable=False)
    era = Column(String(64), default="11th Century CE")
    script_welcome = Column(Text, nullable=False) # Personalized welcome/history
    script_details = Column(Text, nullable=False) # In-depth archaeological narrative
    next_step_guidance = Column(Text, nullable=False) # "Now walk through the shaded colonnade to Stop 2..."
    distance_to_next = Column(Float, default=45.0)
    walking_time_mins = Column(Float, default=1.5)
    shade_rating = Column(String(32), default="HIGH SHADE")
    target_relic_code = Column(String(64), nullable=True)
    badge_reward = Column(String(64), nullable=True)
    xp_reward = Column(Integer, default=50)

class TourSession(Base):
    __tablename__ = "tour_sessions"

    session_id = Column(String(64), primary_key=True, index=True) # UUID
    ticket_id = Column(String(32), unique=True, index=True) # e.g. TKT-7482
    customer_name = Column(String(128), nullable=False)
    preferred_language = Column(String(16), default="en")
    
    current_step = Column(Integer, default=1)
    visited_steps = Column(JSON, default=list) # e.g. [1, 2]
    completed_relics = Column(JSON, default=list) # e.g. ["carved_elephant"]
    unlocked_badges = Column(JSON, default=list)
    chat_history = Column(JSON, default=list)
    total_xp = Column(Integer, default=0)
    
    status = Column(String(32), default="in_progress") # in_progress, paused, completed
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
