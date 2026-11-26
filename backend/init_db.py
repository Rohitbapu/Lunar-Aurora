from app.database import engine, SessionLocal, init_db
from app.models.entities import POINode, PathEdge, RelicArtifact, ScavengerQuest, BlueprintStop, TourSession

def seed_database():
    print("[Database] Creating tables...")
    init_db()
    db = SessionLocal()

    # Clear existing
    db.query(BlueprintStop).delete()
    db.query(PathEdge).delete()
    db.query(RelicArtifact).delete()
    db.query(ScavengerQuest).delete()
    db.query(POINode).delete()
    db.commit()

    print("[Database] Seeding POINodes for the Master Blueprint...")
    nodes_data = [
        POINode(
            id=1, slug="grand_gate", name="Imperial Sun Gate (Ticketing & Entrance)", 
            category="entrance", description="The ceremonial entrance guarded by monumental sentinels and the Holographic Kiosk.",
            x=0.0, y=0.0, z=0.0, has_benches=True, has_water=True, has_tree_shade=False
        ),
        POINode(
            id=2, slug="colonnade_walk", name="Avenue of 1,000 Pillars (Colonnade)", 
            category="monument", description="Deep covered stone corridor providing continuous cool shade and intricate Yali carvings.",
            x=25.0, y=40.0, z=0.0, has_benches=True, has_water=False, has_tree_shade=False
        ),
        POINode(
            id=3, slug="chrono_terrace", name="Celestial Chariot Wheel & Solstitial Gnomon", 
            category="monument", description="High eastern terrace featuring the monumental 24-spoke solar chronometer and gnomon.",
            x=75.0, y=85.0, z=4.0, has_benches=False, has_water=False, has_tree_shade=False
        ),
        POINode(
            id=4, slug="central_sanctum", name="Grand Sanctuary Vimana & Inner Sanctum", 
            category="monument", description="The central 60-meter monolithic granite tower aligned with the equinox dawn sunrise.",
            x=30.0, y=110.0, z=2.0, has_benches=False, has_water=False, has_tree_shade=False
        ),
        POINode(
            id=5, slug="lotus_pool", name="Sacred Royal Lotus Hydraulic Basin", 
            category="monument", description="Hexagonal cooling basin engineered with subterranean gravity-fed terracotta conduits.",
            x=-20.0, y=120.0, z=0.0, has_benches=True, has_water=True, has_tree_shade=False
        ),
        POINode(
            id=6, slug="banyan_grove", name="Whispering Gallery of Celestial Dancers", 
            category="monument", description="Ancient banyan grove and stone pavilion adorned with friezes of celestial Nataraja dancers.",
            x=-40.0, y=65.0, z=0.0, has_benches=True, has_water=True, has_tree_shade=True
        ),
        POINode(
            id=7, slug="sunset_bastion", name="Sunset Bastion & Shaded Overlook", 
            category="shade_rest", description="Highest terrace overlooking the valley with shaded pergolas, cold water, and scenic benches.",
            x=60.0, y=140.0, z=6.0, has_benches=True, has_water=True, has_tree_shade=True
        )
    ]
    for n in nodes_data:
        db.add(n)
    db.commit()

    print("[Database] Seeding BlueprintStops (The 7-Step Curated Route)...")
    stops_data = [
        BlueprintStop(
            step_number=1,
            poi_id=1,
            title="Imperial Sun Gate",
            subtitle="Ticketing & Orientation Hub",
            era="1040 CE • Dynasty Inception",
            script_welcome="Welcome to Lunar Aurora, {name}! I am Luna, your personal historical guide. Stand before the Imperial Sun Gate where ancient envoys once surrendered their credentials before entering. Notice the dual lion guards flanking the arch: their open jaws symbolize vigilance over sacred cosmic knowledge. Look at your live map below: our tour follows a 7-stop master route. When you are ready, follow me forward along the shaded Avenue of 1,000 Pillars!",
            script_details="The Sun Gate faces due east at an inclination angle of 13.5 degrees, allowing dawn light during spring solstice to cast no shadow on the entry threshold.",
            next_step_guidance="Proceed forward 47 meters into the covered stone corridor of the Avenue of 1,000 Pillars.",
            distance_to_next=47.0,
            walking_time_mins=1.0,
            shade_rating="HIGH SHADE",
            target_relic_code="carved_elephant",
            badge_reward="Gatekeeper Seal",
            xp_reward=50
        ),
        BlueprintStop(
            step_number=2,
            poi_id=2,
            title="Avenue of 1,000 Pillars",
            subtitle="Covered Granite Colonnade",
            era="1055 CE • High Classical Era",
            script_welcome="{name}, welcome beneath the Avenue of 1,000 Pillars. Notice how the temperature drops comfortably beneath these interlocking granite slabs. Each pillar is chiseled with mythical Yalis—part lion, part elephant—believed to guard the sanctuary against seismic vibrations. Run your fingers over the smooth stone to feel centuries of preserved history.",
            script_details="Over 400 masons worked in parallel to assemble these monolithic columns using iron mortise-and-tenon joints without a single drop of mortar.",
            next_step_guidance="Follow the eastern pathway 67 meters toward the Astronomical Chariot Wheel Terrace.",
            distance_to_next=67.0,
            walking_time_mins=1.5,
            shade_rating="COOL COLONNADE",
            target_relic_code="carved_elephant",
            badge_reward="Pillar Scholar",
            xp_reward=75
        ),
        BlueprintStop(
            step_number=3,
            poi_id=3,
            title="Celestial Chariot Wheel",
            subtitle="Solstitial Chrono Gnomon",
            era="1070 CE • Archaeo-Astronomy",
            script_welcome="Behold this monumental 24-spoke stone wheel, {name}! It is far more than art—it is a functional precision chronometer. The eight major spokes denote the ancient three-hour intervals of the solar day, and the shadow cast by the central axle tells time within a margin of two minutes. Point your camera at the axle gnomon to inspect its intricate calendar dials.",
            script_details="Priest-astronomers used the outer rim carvings to track lunar eclipses and calculate the exact moment of the monsoon arrival.",
            next_step_guidance="Ascend the grand ceremonial stone ramp 70 meters toward the Grand Sanctuary Vimana.",
            distance_to_next=70.0,
            walking_time_mins=1.8,
            shade_rating="PARTIAL SUN",
            target_relic_code="sundial_pillar",
            badge_reward="Master of Time",
            xp_reward=100
        ),
        BlueprintStop(
            step_number=4,
            poi_id=4,
            title="Grand Sanctuary Vimana",
            subtitle="The Inner Sanctum",
            era="1100 CE • Imperial Zenith",
            script_welcome="You now stand before the majestic heart of the entire complex, {name}. The central spire soars sixty meters high without mortar, stabilized purely by gravitational balance and precision-cut interlocking stone wedges. On the equinox mornings, the sunrise passes through three aligned entryways to illuminate the emerald heart of the inner altar.",
            script_details="The crowning stone alone weighs fifty-two tons. Ancient engineers built a four-kilometer earthen ramp to haul it into place using trained war elephants.",
            next_step_guidance="Descend the western steps 51 meters toward the Sacred Royal Lotus Hydraulic Basin.",
            distance_to_next=51.0,
            walking_time_mins=1.2,
            shade_rating="COURTYARD SHADE",
            target_relic_code="dancing_shiva",
            badge_reward="Sanctuary Master",
            xp_reward=100
        ),
        BlueprintStop(
            step_number=5,
            poi_id=5,
            title="Royal Lotus Hydraulic Basin",
            subtitle="Ancient Water Engineering",
            era="1120 CE • Hydraulic Innovation",
            script_welcome="Take a refreshing breath of the cool air here, {name}. Master hydraulic engineers sculpted this hexagonal lotus pool to circulate mountain snowmelt through subterranean terracotta conduits. As water evaporates across the lotus petals, natural convection creates a cooling microclimate that chills the stone terrace by six degrees Celsius even at midday.",
            script_details="Royal envoys cleansed their hands in rose-scented spring water here before entering the imperial council hall.",
            next_step_guidance="Stroll 58 meters beneath the ancient banyan trees toward the Gallery of Celestial Dancers.",
            distance_to_next=58.0,
            walking_time_mins=1.4,
            shade_rating="TREE SHADE & COOL MIST",
            target_relic_code="lotus_fountain",
            badge_reward="Hydraulic Sage",
            xp_reward=80
        ),
        BlueprintStop(
            step_number=6,
            poi_id=6,
            title="Gallery of Celestial Dancers",
            subtitle="Classical Natya Arts Frieze",
            era="1145 CE • Arts Renaissance",
            script_welcome="Look upon these exquisite stone musicians and celestial dancers, {name}. In the center stands the Nataraja—the cosmic dancer of creation. Each gesture or mudra conveys a full philosophical teaching: the raised palm offers freedom from fear, while the drum in the upper hand sounds the heartbeat of time itself.",
            script_details="The acoustic resonance of this pavilion was tuned so that a soft whisper at one end reverberates distinctly to the opposite corner.",
            next_step_guidance="Follow the shaded terrace ramp 42 meters up to the final overlook at Sunset Bastion.",
            distance_to_next=42.0,
            walking_time_mins=1.0,
            shade_rating="CANOPY SHADE",
            target_relic_code="dancing_shiva",
            badge_reward="Cosmic Harmony",
            xp_reward=90
        ),
        BlueprintStop(
            step_number=7,
            poi_id=7,
            title="Sunset Bastion & Overlook",
            subtitle="Grand Panorama & Tour Culmination",
            era="1180 CE • Valley Vantage",
            script_welcome="Magnificent achievement, {name}! You have traversed the entire curated journey of our sacred acropolis. From this vantage point, gaze across the full site below: see how the Sun Gate, the Colonnade, the Chariot Wheel, and the Vimana form a golden spiral aligned with the celestial solstices. You have unlocked the Grand Master Heritage Crest!",
            script_details="Visitors traditionally gather here at dusk to watch the setting sun paint the granite sanctuary in deep crimson gold.",
            next_step_guidance="You have completed all 7 stops! Tap 'Finish Tour' to view your official Certificate of Completion.",
            distance_to_next=0.0,
            walking_time_mins=0.0,
            shade_rating="COVERED PERGOLA",
            target_relic_code="sundial_pillar",
            badge_reward="Grand Master Heritage Crest",
            xp_reward=150
        )
    ]
    for s in stops_data:
        db.add(s)
    db.commit()

    print("[Database] Seeding PathEdges...")
    edges_data = [
        PathEdge(source_id=1, target_id=2, distance_meters=47.0, base_shade_factor=0.9, path_type="colonnade"),
        PathEdge(source_id=2, target_id=3, distance_meters=67.0, base_shade_factor=0.7, path_type="colonnade"),
        PathEdge(source_id=3, target_id=4, distance_meters=70.0, base_shade_factor=0.8, path_type="covered_corridor"),
        PathEdge(source_id=4, target_id=5, distance_meters=51.0, base_shade_factor=0.6, path_type="tree_avenue"),
        PathEdge(source_id=5, target_id=6, distance_meters=58.0, base_shade_factor=0.85, path_type="tree_avenue"),
        PathEdge(source_id=6, target_id=7, distance_meters=42.0, base_shade_factor=0.8, path_type="colonnade"),
        # Additional connecting paths
        PathEdge(source_id=1, target_id=6, distance_meters=76.0, base_shade_factor=0.85, path_type="tree_avenue"),
        PathEdge(source_id=2, target_id=4, distance_meters=70.0, base_shade_factor=0.7, path_type="monument_shadow"),
        PathEdge(source_id=5, target_id=7, distance_meters=90.0, base_shade_factor=0.6, path_type="tree_avenue"),
        PathEdge(source_id=3, target_id=7, distance_meters=57.0, base_shade_factor=0.3, path_type="open_stone")
    ]
    for e in edges_data:
        db.add(e)
    db.commit()

    print("[Database] Seeding RelicArtifacts...")
    relics_data = [
        RelicArtifact(
            code="carved_elephant",
            name="Celestial Airavata Relief",
            poi_id=2,
            detection_labels=["elephant", "animal", "statue", "sculpture", "carving"],
            architectural_style="High Chalukya Monolith",
            period="1040 CE",
            story="Monolithic carving representing Airavata carrying celestial rain clouds. Its trunk holds an unfolding lotus of renewal.",
            fun_fact="Notice the tiny chisel hatch marks indicating diamond-tip iron chisels were utilized.",
            audio_narrative="Touch your finger toward the crown to witness the imperial dynasty seal."
        ),
        RelicArtifact(
            code="sundial_pillar",
            name="Solstitial Chrono Gnomon",
            poi_id=3,
            detection_labels=["pillar", "column", "clock", "sundial", "obelisk"],
            architectural_style="Archaeo-Astronomy",
            period="1070 CE",
            story="Fluted granite gnomon whose shadow aligns to mark solstice and equinox days precisely.",
            fun_fact="Priest astronomers predicted monsoons within 48 hours using this terrace.",
            audio_narrative="At solar noon, step over the brass marker line to observe zero shadow."
        ),
        RelicArtifact(
            code="dancing_shiva",
            name="Nataraja Cosmic Sanctuary",
            poi_id=6,
            detection_labels=["person", "dancer", "statue", "figure", "deity", "sculpture"],
            architectural_style="Classical Bronze-Stone Synthesis",
            period="1145 CE",
            story="Captures the rhythm of the cosmos. The circle of fire represents the cycle of time and cosmic rebirth.",
            fun_fact="The sculpture's center of gravity is engineered directly through the center base.",
            audio_narrative="Every mudra hand gesture tells a complete philosophical story."
        ),
        RelicArtifact(
            code="lotus_fountain",
            name="Sacred Hexagonal Lotus Basin",
            poi_id=5,
            detection_labels=["fountain", "basin", "bowl", "flower", "water", "sink"],
            architectural_style="Hydraulic Gravitational Engineering",
            period="1120 CE",
            story="Gravity fed mountain runoff cooled the inner sanctum through natural evaporative cooling.",
            fun_fact="The water stays 6 degrees cooler than outside stone all day.",
            audio_narrative="Royal ambassadors refreshed here before council audiences."
        )
    ]
    for r in relics_data:
        db.add(r)
    db.commit()

    print("[Database] Seeding ScavengerQuests...")
    quests_data = [
        ScavengerQuest(
            quest_id="quest_elephant",
            title="Guardian of Rains",
            riddle="I have four legs of granite and a trunk that cradles a sacred blossom. Find me where a thousand stone pillars whisper in cool shadows.",
            target_poi_slug="colonnade_walk",
            target_relic_code="carved_elephant",
            hint="Walk along the Avenue of 1,000 Pillars and point your camera at the stone relief.",
            badge_name="Cloud Rider Crest",
            badge_icon="fa-shield-halved",
            points=150
        ),
        ScavengerQuest(
            quest_id="quest_sundial",
            title="Shadow of the Solstice",
            riddle="I cast no shadow at high noon on the longest day of the year. Climb the eastern stairs where priests watched the turning heavens.",
            target_poi_slug="chrono_terrace",
            target_relic_code="sundial_pillar",
            hint="Head to the Celestial Chariot Wheel Terrace and inspect the fluted gnomon.",
            badge_name="Time Master Crest",
            badge_icon="fa-hourglass-start",
            points=200
        ),
        ScavengerQuest(
            quest_id="quest_lotus",
            title="The Cool Oasis",
            riddle="Where terracotta pipes once sang and stone petals never wither, cool waters bring rest to weary travelers.",
            target_poi_slug="lotus_pool",
            target_relic_code="lotus_fountain",
            hint="Visit the Royal Lotus Basin and scan the hexagonal pool carving.",
            badge_name="Hydraulic Sage Crest",
            badge_icon="fa-water",
            points=120
        )
    ]
    for q in quests_data:
        db.add(q)
    db.commit()

    print("[Database] Database successfully initialized with 7 Master Blueprint Stops, 10 Paths, 4 Relics, 3 Quests!")
    db.close()

if __name__ == "__main__":
    seed_database()
