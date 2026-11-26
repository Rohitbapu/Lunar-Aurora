from sqlalchemy import inspect
from app.database import engine, SessionLocal, init_db
from app.models.entities import Base, POINode, PathEdge, RelicArtifact, ScavengerQuest, BlueprintStop, TourSession

def ensure_schema(force_reset: bool = False):
    """Ensures SQLite tables include new Mahabalipuram columns without manual migrations."""
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    needs_rebuild = force_reset
    if "blueprint_stops" in existing_tables and not needs_rebuild:
        cols = {c["name"] for c in inspector.get_columns("blueprint_stops")}
        if "riddle_question" not in cols:
            needs_rebuild = True
    if "tour_sessions" in existing_tables and not needs_rebuild:
        cols = {c["name"] for c in inspector.get_columns("tour_sessions")}
        if "solved_riddles" not in cols or "captured_photos" not in cols:
            needs_rebuild = True

    if needs_rebuild:
        print("[Database] Rebuilding schema cleanly for updated Mahabalipuram models...")
        Base.metadata.drop_all(bind=engine)
    init_db()

def seed_database(force_reset: bool = False):
    print("[Database] Initializing Mahabalipuram Shore Temple Complex database...")
    ensure_schema(force_reset=force_reset)
    db = SessionLocal()

    db.query(BlueprintStop).delete()
    db.query(PathEdge).delete()
    db.query(RelicArtifact).delete()
    db.query(ScavengerQuest).delete()
    db.query(POINode).delete()
    db.commit()

    print("[Database] Seeding POINodes (Mahabalipuram Shore Temple Complex, 12.6165 deg N)...")
    nodes_data = [
        POINode(
            id=1, slug="shore_gopuram", name="Shore Temple East Gopuram (Entrance)",
            category="entrance",
            historical_era="700-728 CE Pallava Dynasty",
            description="East-facing coastal entrance overlooking the Bay of Bengal, built by Rajasimha (Narasimhavarman II).",
            x=0.0, y=0.0, z=0.0, latitude=12.6165, longitude=80.1993,
            has_benches=True, has_water=True, has_tree_shade=False, average_ambient_temp_c=33.0,
            model_asset_url="/app/assets/models/Grand_Solstice_Sun_Temple.glb"
        ),
        POINode(
            id=2, slug="yali_courtyard", name="Monolithic Yali Pillars Gallery",
            category="monument",
            historical_era="705 CE Pallava Dravidian",
            description="Covered granite prakara corridor featuring roaring Pallava lion-elephant Yali guardians and cool colonnade shade.",
            x=25.0, y=40.0, z=0.0, latitude=12.6169, longitude=80.1995,
            has_benches=True, has_water=False, has_tree_shade=False, average_ambient_temp_c=29.5,
            model_asset_url="/app/assets/models/Celestial_Airavata_Sculpture.glb"
        ),
        POINode(
            id=3, slug="chariot_terrace", name="Chariot Wheel Solar Chronometer",
            category="monument",
            historical_era="712 CE Pallava Astronomy",
            description="Open eastern plinth aligned with the coastal equinox sunrise featuring a 24-spoke carved stone chronometer.",
            x=75.0, y=85.0, z=4.0, latitude=12.6173, longitude=80.1999,
            has_benches=False, has_water=False, has_tree_shade=False, average_ambient_temp_c=35.5,
            model_asset_url="/app/assets/models/Solstitial_Lotus_Gnomon.glb"
        ),
        POINode(
            id=4, slug="central_sanctum", name="Rajasimhesvara Shore Vimana",
            category="monument",
            historical_era="715 CE Twin Granite Spires",
            description="Twin pyramid granite vimanas fitted without mortar, standing against Bay of Bengal salt winds for 1,300 years.",
            x=30.0, y=110.0, z=2.0, latitude=12.6175, longitude=80.1994,
            has_benches=False, has_water=False, has_tree_shade=False, average_ambient_temp_c=32.5,
            model_asset_url="/app/assets/models/Grand_Solstice_Sun_Temple.glb"
        ),
        POINode(
            id=5, slug="lotus_basin", name="Royal Lotus Hydraulic Basin",
            category="monument",
            historical_era="720 CE Pallava Hydraulics",
            description="Evaporative hexagonal stone tank linked to ancient coastal groundwater channels to chill the inner sanctuary.",
            x=-20.0, y=120.0, z=0.0, latitude=12.6176, longitude=80.1989,
            has_benches=True, has_water=True, has_tree_shade=False, average_ambient_temp_c=28.0,
            model_asset_url="/app/assets/models/Solstitial_Lotus_Gnomon.glb"
        ),
        POINode(
            id=6, slug="banyan_canopy", name="Arjuna's Penance Banyan Canopy & Gallery",
            category="shade_rest",
            historical_era="725 CE Pallava Sculptural Gallery",
            description="Deep banyan tree canopy shading cosmic Nataraja dance reliefs, cool drinking fountains, and resting benches.",
            x=-40.0, y=65.0, z=0.0, latitude=12.6171, longitude=80.1986,
            has_benches=True, has_water=True, has_tree_shade=True, average_ambient_temp_c=27.2,
            model_asset_url="/app/assets/models/Celestial_Airavata_Sculpture.glb"
        ),
        POINode(
            id=7, slug="sunset_bastion", name="Coromandel Sunset Bastion",
            category="shade_rest",
            historical_era="728 CE Western Terrace",
            description="Elevated shaded bastion overlooking the Shore Temple silhouette and Coromandel coastline with cooling breezes.",
            x=60.0, y=140.0, z=6.0, latitude=12.6178, longitude=80.1997,
            has_benches=True, has_water=True, has_tree_shade=True, average_ambient_temp_c=28.5,
            model_asset_url="/app/assets/models/Grand_Solstice_Sun_Temple.glb"
        )
    ]
    for n in nodes_data:
        db.add(n)
    db.commit()

    print("[Database] Seeding BlueprintStops (7 Authentic Mahabalipuram Stations + Riddles)...")
    stops_data = [
        BlueprintStop(
            step_number=1, poi_id=1,
            title="Shore Temple East Gopuram",
            subtitle="Pallava Coastal Gateway",
            era="700 CE • Rajasimha Reign",
            script_welcome=(
                "Vanakkam and welcome to Mahabalipuram Shore Temple, {name}! "
                "I am Luna, your Spatial AI Guide. Notice how this eastern gateway frames the rising Bay of Bengal sun. "
                "Commissioned by Pallava king Narasimhavarman II around 700 CE, these basalt-hard granite slabs were interlocked without mortar. "
                "Follow our shaded master trail when you are ready!"
            ),
            script_details="The Shore Temple faces due east at 12.6165 deg N so solstice dawn light pierces straight into the Somaskanda sanctum.",
            next_step_guidance="Walk 47 meters north along the cool stone colonnade toward the Monolithic Yali Pillars Gallery.",
            distance_to_next=47.0, walking_time_mins=1.0, shade_rating="HIGH SHADE",
            target_relic_code="shore_temple_vimana", badge_reward="Pallava Gateway Seal", xp_reward=50,
            riddle_question="Which Pallava monarch commissioned the structural Shore Temple around 700 CE?",
            riddle_options=["Narasimhavarman II (Rajasimha)", "Ashoka the Great", "Krishnadevaraya"],
            riddle_answer="Narasimhavarman II (Rajasimha)"
        ),
        BlueprintStop(
            step_number=2, poi_id=2,
            title="Monolithic Yali Pillars Gallery",
            subtitle="Sculpted Prakara Colonnade",
            era="705 CE • Pallava Dravidian",
            script_welcome=(
                "Step beneath the covered granite colonnade, {name}. Here temperatures drop noticeably beside the roaring Pallava Yali pillars—mythical guardians combining lion strength and elephant grace. "
                "Point your camera at the Yali Pillar card to trigger its 3D reconstruction!"
            ),
            script_details="Unlike soft sandstone inland, Pallava guild carvers shaped ultra-dense charnockite granite using tempered iron chisels.",
            next_step_guidance="Continue 67 meters northeast toward the Chariot Wheel Solar Chronometer Terrace.",
            distance_to_next=67.0, walking_time_mins=1.5, shade_rating="COOL COLONNADE",
            target_relic_code="yali_pillar", badge_reward="Yali Guardian Crest", xp_reward=75,
            riddle_question="What mythic creatures flank the Shore Temple prakara columns to symbolize royal vigilance?",
            riddle_options=["Yali (Lion-Elephant guardians)", "Winged Pegasi", "Sphinxes"],
            riddle_answer="Yali (Lion-Elephant guardians)"
        ),
        BlueprintStop(
            step_number=3, poi_id=3,
            title="Chariot Wheel Solar Chronometer",
            subtitle="Coastal Equinox Sundial",
            era="712 CE • Archaeo-Astronomy",
            script_welcome=(
                "Behold the carved solar chariot chronometer, {name}. Its spokes divide daylight into ritual prahars using the shadow of the central gnomon. "
                "Scan the Chariot Wheel card or scrub the Era Slider to inspect its full 8th-century relief."
            ),
            script_details="Maritime navigators and temple astronomers tracked seasonal wind reversals from this elevated eastern plinth.",
            next_step_guidance="Move 70 meters west into the covered corridor leading to Rajasimhesvara Shore Vimana.",
            distance_to_next=70.0, walking_time_mins=1.6, shade_rating="PARTIAL SUN",
            target_relic_code="chariot_wheel", badge_reward="Equinox Astronomer", xp_reward=100,
            riddle_question="How many radial spokes form the main solar timekeeping wheel?",
            riddle_options=["24 Spokes", "8 Spokes", "60 Spokes"],
            riddle_answer="24 Spokes"
        ),
        BlueprintStop(
            step_number=4, poi_id=4,
            title="Rajasimhesvara Shore Vimana",
            subtitle="Twin Structural Granite Spires",
            era="715 CE • Pallava Engineering Zenith",
            script_welcome=(
                "You stand before the iconic twin granite spires of the Shore Temple, {name}! Built from interlocking stone blocks with zero lime mortar, "
                "this five-tiered Dravidian vimana even withstood the 2004 Indian Ocean tsunami thanks to its stepped coastal bedrock foundation."
            ),
            script_details="Its tall eastern tower honors Shiva while a subtle horizontal shrine nestled between the spires preserves sleeping Anantasayana Vishnu.",
            next_step_guidance="Descend 51 meters along the tree-shaded avenue toward the Royal Lotus Hydraulic Basin.",
            distance_to_next=51.0, walking_time_mins=1.2, shade_rating="COURTYARD SHADE",
            target_relic_code="shore_temple_vimana", badge_reward="Vimana Architect", xp_reward=100,
            riddle_question="How are the load-bearing granite blocks of the Shore Temple Vimana held together?",
            riddle_options=["Dry interlocking stone joinery without mortar", "Roman volcanic cement", "Cast iron rivets"],
            riddle_answer="Dry interlocking stone joinery without mortar"
        ),
        BlueprintStop(
            step_number=5, poi_id=5,
            title="Royal Lotus Hydraulic Basin",
            subtitle="Passive Evaporative Cooling Tank",
            era="720 CE • Coastal Hydrology",
            script_welcome=(
                "Feel the cooling sea breeze skimming across the Royal Lotus Basin, {name}. "
                "Pallava engineers designed stepped stone cisterns around the sanctum to capture monsoon freshwater and push back saline intrusion."
            ),
            script_details="Evaporation across the sculpted lotus rim creates a microclimate up to 5 to 6 degrees Celsius cooler than exposed flagstones.",
            next_step_guidance="Walk 58 meters south beneath the thick Arjuna's Penance Banyan Canopy.",
            distance_to_next=58.0, walking_time_mins=1.3, shade_rating="COOL MIST & SHADE",
            target_relic_code="lotus_basin", badge_reward="Hydrology Sage", xp_reward=80,
            riddle_question="Approximately how much cooler does the shaded lotus basin terrace stay compared to open midday stone?",
            riddle_options=["Around 6 degrees Celsius cooler", "0.5 degrees Celsius cooler", "25 degrees Celsius cooler"],
            riddle_answer="Around 6 degrees Celsius cooler"
        ),
        BlueprintStop(
            step_number=6, poi_id=6,
            title="Arjuna's Penance Banyan Canopy",
            subtitle="Shaded Sanctuary & Nataraja Reliefs",
            era="725 CE • Pallava Fine Arts",
            script_welcome=(
                "Welcome into deep emerald tree shade, {name}! This banyan grove cools weary pilgrims beside cosmic Nataraja dance reliefs. "
                "Point your camera at the Nataraja Relief card or rest beside the drinking fountain while enjoying spatial 3D acoustics."
            ),
            script_details="In Pallava choreography, the raised Abhaya mudra hand offers fearless protection while the upper drum keeps cosmic rhythm.",
            next_step_guidance="Take the final shaded colonnade ramp 42 meters northeast to Coromandel Sunset Bastion.",
            distance_to_next=42.0, walking_time_mins=1.0, shade_rating="DEEP BANYAN SHADE",
            target_relic_code="nataraja_relief", badge_reward="Nataraja Rhythm Crest", xp_reward=90,
            riddle_question="In the Nataraja relief, what instrument in the upper right hand sounds the pulse of creation?",
            riddle_options=["Damaru (Hourglass Drum)", "Veena Lute", "Conch Horn"],
            riddle_answer="Damaru (Hourglass Drum)"
        ),
        BlueprintStop(
            step_number=7, poi_id=7,
            title="Coromandel Sunset Bastion",
            subtitle="Bay of Bengal Overlook & Finale",
            era="728 CE • UNESCO Panorama",
            script_welcome=(
                "Bravo, {name}! You have completed all seven heritage stations across Mahabalipuram Shore Temple! "
                "Snap a commemorative AR memory photo here and download your official illustrated PDF Travel Journal."
            ),
            script_details="Declared a UNESCO World Heritage Group of Monuments in 1984, Mahabalipuram inspired Southeast Asian stone temples across Cambodia and Java.",
            next_step_guidance="Tap Finish Tour or Download PDF Travel Journal to seal your Pallava expedition!",
            distance_to_next=0.0, walking_time_mins=0.0, shade_rating="COVERED PERGOLA",
            target_relic_code="chariot_wheel", badge_reward="Shore Temple Master Seal", xp_reward=150,
            riddle_question="In what year were the Group of Monuments at Mahabalipuram inscribed as a UNESCO World Heritage Site?",
            riddle_options=["1984", "1947", "2008"],
            riddle_answer="1984"
        )
    ]
    for s in stops_data:
        db.add(s)
    db.commit()

    print("[Database] Seeding PathEdges (Dual Route Sun vs Shaded Topology)...")
    edges_data = [
        # Shaded Perimeter Sanctuary Ring
        PathEdge(source_id=1, target_id=2, distance_meters=47.0, base_shade_factor=0.92, path_type="colonnade"),
        PathEdge(source_id=2, target_id=3, distance_meters=67.0, base_shade_factor=0.72, path_type="colonnade"),
        PathEdge(source_id=3, target_id=4, distance_meters=51.0, base_shade_factor=0.80, path_type="covered_corridor"),
        PathEdge(source_id=4, target_id=5, distance_meters=51.0, base_shade_factor=0.78, path_type="tree_avenue"),
        PathEdge(source_id=5, target_id=6, distance_meters=58.0, base_shade_factor=0.90, path_type="tree_avenue"),
        PathEdge(source_id=5, target_id=7, distance_meters=82.0, base_shade_factor=0.82, path_type="tree_avenue"),
        PathEdge(source_id=1, target_id=6, distance_meters=76.0, base_shade_factor=0.94, path_type="tree_avenue"),
        PathEdge(source_id=2, target_id=4, distance_meters=70.0, base_shade_factor=0.75, path_type="monument_shadow"),
        # Direct Unshaded Open-Sun Courtyard Diagonals (Shortest physical distance, high solar heat)
        PathEdge(source_id=1, target_id=4, distance_meters=114.0, base_shade_factor=0.10, path_type="open_courtyard"),
        PathEdge(source_id=4, target_id=7, distance_meters=42.0, base_shade_factor=0.12, path_type="open_stone"),
        PathEdge(source_id=1, target_id=3, distance_meters=113.0, base_shade_factor=0.12, path_type="open_courtyard"),
        PathEdge(source_id=3, target_id=7, distance_meters=57.0, base_shade_factor=0.15, path_type="open_stone"),
        PathEdge(source_id=6, target_id=7, distance_meters=125.0, base_shade_factor=0.85, path_type="colonnade"),
    ]
    for e in edges_data:
        db.add(e)
    db.commit()

    print("[Database] Seeding 5 Printable Carving Cards / RelicArtifacts...")
    relics_data = [
        RelicArtifact(
            code="shore_temple_vimana",
            name="Rajasimhesvara Shore Temple Vimana",
            poi_id=4,
            detection_labels=["shore_temple_vimana", "vimana", "spire", "temple", "sanctum"],
            architectural_style="Pallava Dravidian Granite (700-728 CE)",
            period="700-728 CE",
            story="Built of interlocking coastal granite without mortar, the five-tiered Rajasimhesvara Vimana anchors one of South India's earliest structural stone temples.",
            fun_fact="This structural stone shrine survived centuries of cyclone surges including the December 2004 Indian Ocean tsunami.",
            audio_narrative="Drag the Era Slider to watch eroded coastal blocks reconstruct into painted Pallava plaster towers."
        ),
        RelicArtifact(
            code="chariot_wheel",
            name="Solar Chariot Wheel & Gnomon",
            poi_id=3,
            detection_labels=["chariot_wheel", "sundial_pillar", "wheel", "clock", "sundial", "gnomon"],
            architectural_style="Pallava Archaeo-Astronomy",
            period="712 CE",
            story="Twenty-four finely chiseled stone spokes transform sunlight angles into ritual time intervals and seasonal solstitial warnings for Coromandel mariners.",
            fun_fact="At solar noon around the summer solstice, the vertical gnomon shadow shrinks right down onto the brass plinth axis.",
            audio_narrative="Notice how each spoke corresponds to a daily solar watch interval."
        ),
        RelicArtifact(
            code="yali_pillar",
            name="Monolithic Roaring Yali Pillar",
            poi_id=2,
            detection_labels=["yali_pillar", "carved_elephant", "yali", "elephant", "pillar", "lion", "statue"],
            architectural_style="Pallava Charonockite Pillar Carving",
            period="705 CE",
            story="Seated at the base of tall octagonal granite shafts, the rearing Yali fuses lion ferocity, elephant wisdom, and serpentine agility to guard sacred precincts.",
            fun_fact="Pillar galleries along the outer prakara cut midday stone surface heat while framing ocean breezes.",
            audio_narrative="Inspect the carved mane curls chiseled by 8th-century Pallava master guilds."
        ),
        RelicArtifact(
            code="nataraja_relief",
            name="Cosmic Nataraja Sanctuary Frieze",
            poi_id=6,
            detection_labels=["nataraja_relief", "dancing_shiva", "nataraja", "dancer", "person", "statue"],
            architectural_style="Pallava Classical Dance Sculpture",
            period="725 CE",
            story="Framed inside an arching stone aureole, the four-armed Nataraja balances creation (damaru drum) and transformation while calming seekers beneath the Abhaya gesture.",
            fun_fact="Notice how the center of gravity aligns vertically down through the supporting lotus pedestal.",
            audio_narrative="Each finger mudra in this granite panel encodes a classic verse of Bharatanatyam."
        ),
        RelicArtifact(
            code="lotus_basin",
            name="Royal Lotus Hydraulic Cistern",
            poi_id=5,
            detection_labels=["lotus_basin", "lotus_fountain", "lotus", "fountain", "basin", "bowl"],
            architectural_style="Pallava Passive Evaporative Hydrology",
            period="720 CE",
            story="Fed by rainwater catchment troughs and granite conduits, the carved eight-petaled lotus cistern chills coastal winds naturally before they sweep the temple hall.",
            fun_fact="Evaporative convection drops terrace air temperatures by roughly 6 degrees Celsius under peak afternoon sun.",
            audio_narrative="Take a moment beside these cooling lotus petals before finishing the final leg."
        )
    ]
    for r in relics_data:
        db.add(r)
    db.commit()

    print("[Database] Seeding ScavengerQuests...")
    quests_data = [
        ScavengerQuest(
            quest_id="quest_yali",
            title="Guardian of the Colonnade",
            riddle="Half lion, half elephant, I roar silently beneath a cool granite colonnade. Scan my pillar card!",
            target_poi_slug="yali_courtyard",
            target_relic_code="yali_pillar",
            hint="Stop 2: Monolithic Yali Pillars Gallery",
            badge_name="Cloud Rider Yali Crest",
            badge_icon="fa-shield-halved",
            points=150
        ),
        ScavengerQuest(
            quest_id="quest_chariot",
            title="Shadow of the Solstice",
            riddle="Twenty-four granite spokes measure Coromandel noon shadows with silent precision.",
            target_poi_slug="chariot_terrace",
            target_relic_code="chariot_wheel",
            hint="Stop 3: Chariot Wheel Solar Chronometer",
            badge_name="Solstice Timekeeper",
            badge_icon="fa-hourglass-start",
            points=200
        ),
        ScavengerQuest(
            quest_id="quest_lotus",
            title="Cooling Oasis of Pallava Waters",
            riddle="Eight carved stone petals hold chilled rainwater steps away from ocean salt spray.",
            target_poi_slug="lotus_basin",
            target_relic_code="lotus_basin",
            hint="Stop 5: Royal Lotus Hydraulic Basin",
            badge_name="Hydraulic Sage Crest",
            badge_icon="fa-water",
            points=120
        )
    ]
    for q in quests_data:
        db.add(q)
    db.commit()

    print("[Database] Seeded 7 Mahabalipuram Stops, 12 Dual-Route Edges, 5 Carving Cards, and 3 Quests!")
    db.close()

if __name__ == "__main__":
    seed_database(force_reset=True)
