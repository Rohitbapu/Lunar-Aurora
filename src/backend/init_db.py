from sqlalchemy import inspect
from app.database import engine, SessionLocal, init_db
from app.models.entities import Base, POINode, PathEdge, RelicArtifact, ScavengerQuest, BlueprintStop

SRC_UNESCO = "https://whc.unesco.org/en/list/249/"
SRC_GROUP = "https://en.wikipedia.org/wiki/Group_of_Monuments_at_Mahabalipuram"
SRC_SHORE = "https://en.wikipedia.org/wiki/Shore_Temple"
SRC_RATHAS = "https://en.wikipedia.org/wiki/Pancha_Rathas"
SRC_ARJUNA = "https://en.wikipedia.org/wiki/Descent_of_the_Ganges_(Mahabalipuram)"
SRC_BUTTERBALL = "https://en.wikipedia.org/wiki/Krishna%27s_Butterball"
SRC_VARAHA = "https://en.wikipedia.org/wiki/Varaha_Cave_Temple"
SRC_MAHISHASURA = "https://en.wikipedia.org/wiki/Mahishasuramardini_Mandapa"


def ensure_schema(force_reset: bool = False):
    """Ensures SQLite tables include the 'source' column cleanly without stale schema."""
    inspector = inspect(engine)
    existing = inspector.get_table_names()
    needs_rebuild = force_reset
    for tbl, required_cols in (
        ("poi_nodes", {"source", "coordinate_source", "arrival_radius_m", "arrival_radius_source"}),
        ("path_edges", {"distance_source"}),
        ("blueprint_stops", {"source"}),
        ("relic_artifacts", {"source"}),
        ("scavenger_quests", {"source"}),
    ):
        if tbl in existing and not needs_rebuild:
            cols = {c["name"] for c in inspector.get_columns(tbl)}
            if not required_cols.issubset(cols):
                needs_rebuild = True
    if "tour_sessions" in existing and not needs_rebuild:
        cols = {c["name"] for c in inspector.get_columns("tour_sessions")}
        if "solved_riddles" not in cols or "captured_photos" not in cols:
            needs_rebuild = True

    if needs_rebuild:
        print("[Database] Rebuilding schema cleanly for sourced Mahabalipuram models...")
        Base.metadata.drop_all(bind=engine)
    init_db()


def seed_database(force_reset: bool = False):
    print("[Database] Seeding Group of Monuments at Mahabalipuram (UNESCO 1984)...")
    ensure_schema(force_reset=force_reset)
    db = SessionLocal()

    db.query(BlueprintStop).delete()
    db.query(PathEdge).delete()
    db.query(RelicArtifact).delete()
    db.query(ScavengerQuest).delete()
    db.query(POINode).delete()
    db.commit()

    # 7 Mahabalipuram stops with OpenStreetMap (ODbL) coordinates and Wiki/UNESCO historical sources.
    # Local (x, y) offsets are metric East/North displacements relative to Stop 1 (12.6165181 N, 80.1982844 E).
    # Note: S4 & S6 starting radii adjusted from 30 m to 25 m so their 55.02 m separation stays strictly non-overlapping (25+25=50 m < 55.02 m).
    OSM_DIST_SRC = "OpenStreetMap footpath/street graph Dijkstra (ODbL)"
    RAD_SRC_UNVERIFIED = "UNVERIFIED until field-tested"
    nodes_data = [
        POINode(
            id=1, slug="shore_temple_entry", name="Shore Temple Coastal Entry",
            category="entrance",
            historical_era="7th-8th century CE (Pallava Dynasty)",
            description="Coastal approach to the Group of Monuments at Mahabalipuram on the Bay of Bengal, about 60 km south of Chennai.",
            source=SRC_GROUP,
            x=0.0, y=0.0, z=0.0, latitude=12.6165181, longitude=80.1982844,
            coordinate_source="OpenStreetMap node/1138027422 (barrier=gate, ODbL)",
            arrival_radius_m=20.0, arrival_radius_source=RAD_SRC_UNVERIFIED,
            has_benches=True, has_water=True, has_tree_shade=False, average_ambient_temp_c=32.5,
            model_asset_url=None
        ),
        POINode(
            id=2, slug="shore_temple_vimana", name="Shore Temple Shrines",
            category="monument",
            historical_era="c. 725 AD (Narasimhavarman II)",
            description="Structural granite temple complex overlooking the Bay of Bengal, one of Southern India's oldest structural stone temples.",
            source=SRC_SHORE,
            x=115.8, y=-7.2, z=0.0, latitude=12.6164535, longitude=80.1993500,
            coordinate_source="OpenStreetMap way/370135158 (Mamallapuram Shore Temple, ODbL)",
            arrival_radius_m=45.0, arrival_radius_source=RAD_SRC_UNVERIFIED,
            has_benches=False, has_water=False, has_tree_shade=False, average_ambient_temp_c=33.0,
            model_asset_url=None
        ),
        POINode(
            id=3, slug="pancha_rathas", name="Pancha Rathas Monolithic Complex",
            category="monument",
            historical_era="7th-8th century CE (Pallava Dynasty)",
            description="Five monolithic rock-cut chariot-shaped monuments carved over single north-south sloping granite stones, named after the Pandavas and Draupadi.",
            source=SRC_RATHAS,
            x=-932.4, y=-829.7, z=2.0, latitude=12.6090647, longitude=80.1897016,
            coordinate_source="OpenStreetMap way/103082949 (Pancha Rathas, ODbL)",
            arrival_radius_m=75.0, arrival_radius_source=RAD_SRC_UNVERIFIED,
            has_benches=False, has_water=False, has_tree_shade=False, average_ambient_temp_c=34.0,
            model_asset_url=None
        ),
        POINode(
            id=4, slug="arjunas_penance", name="Arjuna's Penance (Descent of the Ganges)",
            category="monument",
            historical_era="7th-8th century CE (Pallava Dynasty)",
            description="Open-air bas-relief measuring 96 by 43 feet (29 m x 13 m) carved across two monolithic boulders depicting the descent of the Ganges led by Bhagiratha.",
            source=SRC_ARJUNA,
            x=-607.0, y=154.8, z=2.0, latitude=12.6179087, longitude=80.1926969,
            coordinate_source="OpenStreetMap node/353978523 (Arjuna's Penance, ODbL)",
            arrival_radius_m=25.0, arrival_radius_source=f"{RAD_SRC_UNVERIFIED} (adjusted from 30m for S4-S6 non-overlap)",
            has_benches=False, has_water=False, has_tree_shade=False, average_ambient_temp_c=33.0,
            model_asset_url=None
        ),
        POINode(
            id=5, slug="krishnas_butter_ball", name="Krishna's Butterball (Vaan Irai Kal)",
            category="monument",
            historical_era="Protected ASI Monument (Mamallapuram)",
            description="Gigantic granite erratic boulder resting on a short rocky incline near the cave monuments, listed as a protected monument by the ASI.",
            source=SRC_BUTTERBALL,
            x=-638.9, y=286.2, z=4.0, latitude=12.6190890, longitude=80.1924032,
            coordinate_source="OpenStreetMap way/753671961 (Krishna's Butterball, ODbL)",
            arrival_radius_m=25.0, arrival_radius_source=RAD_SRC_UNVERIFIED,
            has_benches=True, has_water=False, has_tree_shade=False, average_ambient_temp_c=33.0,
            model_asset_url=None
        ),
        POINode(
            id=6, slug="varaha_cave", name="Varaha Cave Temple (Adivaraha Mandapa)",
            category="shade_rest",
            historical_era="Late 7th century CE (Pallava Rock-Cut Cave)",
            description="Rock-cut cave temple providing indoor stone shade, noted for the carved panel of Vishnu as Varaha lifting Bhudevi from the sea.",
            source=SRC_VARAHA,
            x=-658.4, y=174.5, z=3.0, latitude=12.6180857, longitude=80.1922234,
            coordinate_source="OpenStreetMap node/353978532 (Varaha Mandapam / Cave, ODbL)",
            arrival_radius_m=25.0, arrival_radius_source=f"{RAD_SRC_UNVERIFIED} (adjusted from 30m for S4-S6 non-overlap)",
            has_benches=True, has_water=True, has_tree_shade=True, average_ambient_temp_c=28.0,
            model_asset_url=None
        ),
        POINode(
            id=7, slug="mahishasuramardini_cave", name="Mahishasuramardini Mandapa (Yampuri)",
            category="shade_rest",
            historical_era="Late 7th century CE (Pallava Cave Temple)",
            description="Shaded rock-cut cave temple located near the hill lighthouse with three sculpted panels: Durga slaying Mahishasura, reclining Vishnu, and Shiva.",
            source=SRC_MAHISHASURA,
            x=-732.8, y=-143.8, z=6.0, latitude=12.6152265, longitude=80.1915388,
            coordinate_source="OpenStreetMap node/353978541 (Mahishamadhini Cave, ODbL)",
            arrival_radius_m=30.0, arrival_radius_source=RAD_SRC_UNVERIFIED,
            has_benches=True, has_water=True, has_tree_shade=True, average_ambient_temp_c=28.5,
            model_asset_url=None
        )
    ]
    for n in nodes_data:
        db.add(n)
    db.commit()

    stops_data = [
        BlueprintStop(
            step_number=1, poi_id=1,
            title="Shore Temple Coastal Entry",
            subtitle="UNESCO Group of Monuments at Mahabalipuram",
            era="7th-8th century CE (UNESCO 1984)",
            script_welcome=(
                "Vanakkam and welcome to Mahabalipuram, {name}! "
                "The Group of Monuments at Mahabalipuram was built during the 7th and 8th centuries CE by the Pallava dynasty on the Coromandel Coast, about 60 kilometres south of Chennai, and was inscribed as a UNESCO World Heritage Site in 1984."
            ),
            script_details="The heritage group includes rock-cut rathas, cave mandapas, open-air bas-reliefs, and structural stone-cut temples managed after 1960 under the Archaeological Survey of India.",
            next_step_guidance="Walk ~255 m along the Shore Temple garden pathway to inspect the structural Shore Temple shrines.",
            distance_to_next=255.0, walking_time_mins=3.6, shade_rating="ASSUMED COASTAL PATH",
            target_relic_code=None, badge_reward="Mahabalipuram Pilgrim Seal", xp_reward=50,
            riddle_question="In which year was the Group of Monuments at Mahabalipuram classified as a UNESCO World Heritage Site?",
            riddle_options=["1984", "1956", "2001"],
            riddle_answer="1984",
            source=SRC_GROUP
        ),
        BlueprintStop(
            step_number=2, poi_id=2,
            title="Shore Temple Shrines",
            subtitle="Oldest Structural Stone Temple in South India",
            era="c. 725 AD (Narasimhavarman II)",
            script_welcome=(
                "{name}, you are standing beside the Shore Temple, dating from the 8th century AD (c. 725 AD) during the reign of Pallava king Narasimhavarman II. "
                "Point at Card 1 and tap SCAN RELIC to view its monument photograph and sourced architecture notes."
            ),
            script_details="Unlike rock-cut caves cut into living hill rock, the Shore Temple is a structural temple built from blocks of granite overlooking the Bay of Bengal.",
            next_step_guidance="Walk ~1831 m southwest via town streets to reach the Pancha Rathas monolithic rock-cut complex.",
            distance_to_next=1831.2, walking_time_mins=26.2, shade_rating="ASSUMED EXPOSED ROUTE",
            target_relic_code="shore_temple_vimana", badge_reward="Structural Granite Crest", xp_reward=75,
            riddle_question="Which Pallava ruler reigned during the creation of the structural Shore Temple (c. 725 AD)?",
            riddle_options=["Narasimhavarman II", "Ashoka Maurya", "Krishnadevaraya"],
            riddle_answer="Narasimhavarman II",
            source=SRC_SHORE
        ),
        BlueprintStop(
            step_number=3, poi_id=3,
            title="Pancha Rathas Complex",
            subtitle="Monolithic Processional Chariots",
            era="7th-8th century CE (Pallava)",
            script_welcome=(
                "Welcome to Pancha Rathas, {name}. Each of these five monuments resembles a chariot or ratha carved from a single sloping north-south granite monolith and named after the Pancha Pandavas and Draupadi. "
                "Scan Card 2 (pancha_rathas) to unlock your verified photo card and historical facts."
            ),
            script_details="Historians note these monolithic structures were never consecrated because construction stopped; scholars associate the site with Narasimhavarman I (630-668 CE) or Narasimhavarman II (c. 690-725 CE).",
            next_step_guidance="Walk ~1125 m north along Five Rathas Road and West Raja Street to Arjuna's Penance.",
            distance_to_next=1124.8, walking_time_mins=16.1, shade_rating="ASSUMED PARTIAL SHADE",
            target_relic_code="pancha_rathas", badge_reward="Ratha Monolith Crest", xp_reward=100,
            riddle_question="Why were the five monolithic structures at Pancha Rathas never consecrated as temples?",
            riddle_options=["They were never completed", "They sank underwater", "They were made of wood"],
            riddle_answer="They were never completed",
            source=SRC_RATHAS
        ),
        BlueprintStop(
            step_number=4, poi_id=4,
            title="Arjuna's Penance (Descent of the Ganges)",
            subtitle="96 by 43 ft Open-Air Bas-Relief",
            era="7th-8th century CE (UNESCO 1984)",
            script_welcome=(
                "Behold the giant open-air rock relief known locally as Arjuna's Penance, {name}! Measuring 96 by 43 feet (29 m by 13 m) across two monolithic rock boulders, it depicts the legend of the river Ganges descending from heaven led by Bhagiratha."
            ),
            script_details="The sculptural panel pairs stories from the Mahabharata and the Descent of the Ganges across an unbroken granite cliff canvas.",
            next_step_guidance="Walk ~239 m north up the hillock path toward Krishna's Butterball.",
            distance_to_next=238.8, walking_time_mins=3.4, shade_rating="ASSUMED LIGHT CANOPY",
            target_relic_code="arjunas_penance", badge_reward="Ganges Relief Observer", xp_reward=100,
            riddle_question="Approximately how wide and tall is the Descent of the Ganges (Arjuna's Penance) open-air rock relief?",
            riddle_options=["96 by 43 feet (29 m x 13 m)", "15 by 8 feet (4.5 m x 2.4 m)", "400 by 200 feet (120 m x 60 m)"],
            riddle_answer="96 by 43 feet (29 m x 13 m)",
            source=SRC_ARJUNA
        ),
        BlueprintStop(
            step_number=5, poi_id=5,
            title="Krishna's Butterball (Vaan Irai Kal)",
            subtitle="Protected Balanced Granite Boulder",
            era="Natural ASI Protected Monument",
            script_welcome=(
                "Here stands Krishna's Butterball, also called Vaan Irai Kal, {name}. It is a gigantic granite boulder resting on a short rocky incline on the Mahabalipuram hillock."
            ),
            script_details="Surrounding the hillock's Pallava cave shrines, the balanced boulder is listed by the Archaeological Survey of India as a protected national monument.",
            next_step_guidance="Walk ~167 m southwest across the hillock footpaths to Varaha Cave Temple.",
            distance_to_next=167.3, walking_time_mins=2.4, shade_rating="ASSUMED EXPOSED HILLTOP",
            target_relic_code="krishnas_butter_ball", badge_reward="Vaan Irai Kal Explorer", xp_reward=80,
            riddle_question="By what Tamil name is Krishna's Butterball also locally known?",
            riddle_options=["Vaan Irai Kal", "Pancha Ratha", "Yampuri"],
            riddle_answer="Vaan Irai Kal",
            source=SRC_BUTTERBALL
        ),
        BlueprintStop(
            step_number=6, poi_id=6,
            title="Varaha Cave Temple (Adivaraha Mandapa)",
            subtitle="Late 7th-Century Rock-Cut Cave Shelter",
            era="Late 7th century CE (Pallava)",
            script_welcome=(
                "Step into the cool carved shade of Varaha Cave Temple, {name}. Dating from the late 7th century, this rock-cut cave mandapa highlights Vishnu in the boar incarnation of Varaha lifting Bhudevi, the earth goddess, from the sea."
            ),
            script_details="Located in the hill area north of the Pancha Rathas and Shore Temple, the mandapa showcases classic late-7th-century Pallava rock-cut cave architecture.",
            next_step_guidance="Walk ~511 m south along the ridge footpaths toward Mahishasuramardini Mandapa near the lighthouse.",
            distance_to_next=511.2, walking_time_mins=7.3, shade_rating="ASSUMED CAVE SHELTER",
            target_relic_code=None, badge_reward="Varaha Cave Scholar", xp_reward=90,
            riddle_question="Which prominent carved scene appears inside Varaha Cave Temple?",
            riddle_options=["Vishnu as Varaha lifting Bhudevi from the sea", "Chariot Wheel of Konark", "Sanchi Torana Gateway"],
            riddle_answer="Vishnu as Varaha lifting Bhudevi from the sea",
            source=SRC_VARAHA
        ),
        BlueprintStop(
            step_number=7, poi_id=7,
            title="Mahishasuramardini Mandapa (Yampuri)",
            subtitle="Late 7th-Century Hilltop Cave Temple",
            era="Late 7th century CE (Pallava)",
            script_welcome=(
                "Congratulations on reaching Stop 7, Mahishasuramardini Mandapa (also called Yampuri), {name}! Dating from the late 7th century near the lighthouse hill, its cave sanctums preserve carved panels of Durga slaying Mahishasura, Vishnu reclining on Adishesha, and Shiva."
            ),
            script_details="Three carved panels inside the cave mandapa walls remain hallmark achievements of Pallava rock-cut art within the UNESCO site inscribed in 1984.",
            next_step_guidance="Scan Card 5 (mahishasuramardini_cave) and tap Download PDF Travel Journal to export your completed journey.",
            distance_to_next=0.0, walking_time_mins=0.0, shade_rating="CAVE INTERIOR SHADE",
            target_relic_code="mahishasuramardini_cave", badge_reward="Mahabalipuram Heritage Crest", xp_reward=150,
            riddle_question="Which three iconic sculptural panels occupy the cave walls of Mahishasuramardini Mandapa?",
            riddle_options=[
                "Durga slaying Mahishasura, reclining Vishnu on Adishesha, and Shiva",
                "Rama, Lakshmana, and Ravana's aerial chariot",
                "Ashokan Lion Capital and Buddhist wheel"
            ],
            riddle_answer="Durga slaying Mahishasura, reclining Vishnu on Adishesha, and Shiva",
            source=SRC_MAHISHASURA
        )
    ]
    for s in stops_data:
        db.add(s)
    db.commit()

    # Real walking network distances computed on OpenStreetMap ODbL footways & streets (mahabalipuram bbox),
    # paired with ASSUMED/ILLUSTRATIVE base_shade_factor & path_type weights (not empirically measured).
    edges_data = [
        PathEdge(source_id=1, target_id=2, distance_meters=255.0, distance_source=OSM_DIST_SRC, base_shade_factor=0.65, path_type="coastal_walk"),
        PathEdge(source_id=2, target_id=3, distance_meters=1831.2, distance_source=OSM_DIST_SRC, base_shade_factor=0.72, path_type="tree_avenue"),
        PathEdge(source_id=3, target_id=4, distance_meters=1124.8, distance_source=OSM_DIST_SRC, base_shade_factor=0.80, path_type="tree_avenue"),
        PathEdge(source_id=4, target_id=5, distance_meters=238.8, distance_source=OSM_DIST_SRC, base_shade_factor=0.78, path_type="tree_avenue"),
        PathEdge(source_id=5, target_id=6, distance_meters=167.3, distance_source=OSM_DIST_SRC, base_shade_factor=0.90, path_type="cave_approach"),
        PathEdge(source_id=5, target_id=7, distance_meters=652.3, distance_source=OSM_DIST_SRC, base_shade_factor=0.82, path_type="tree_avenue"),
        PathEdge(source_id=1, target_id=6, distance_meters=858.5, distance_source=OSM_DIST_SRC, base_shade_factor=0.94, path_type="tree_avenue"),
        PathEdge(source_id=2, target_id=4, distance_meters=992.5, distance_source=OSM_DIST_SRC, base_shade_factor=0.75, path_type="tree_avenue"),
        PathEdge(source_id=6, target_id=7, distance_meters=511.2, distance_source=OSM_DIST_SRC, base_shade_factor=0.88, path_type="cave_shelter"),
        # Direct OSM street diagonals (assumed unshaded weights)
        PathEdge(source_id=1, target_id=4, distance_meters=737.5, distance_source=OSM_DIST_SRC, base_shade_factor=0.10, path_type="open_stone"),
        PathEdge(source_id=4, target_id=7, distance_meters=492.1, distance_source=OSM_DIST_SRC, base_shade_factor=0.12, path_type="open_stone"),
        PathEdge(source_id=1, target_id=3, distance_meters=1576.1, distance_source=OSM_DIST_SRC, base_shade_factor=0.12, path_type="open_stone"),
        PathEdge(source_id=3, target_id=7, distance_meters=789.9, distance_source=OSM_DIST_SRC, base_shade_factor=0.15, path_type="open_stone"),
    ]
    for e in edges_data:
        db.add(e)
    db.commit()

    # Exact 5 Carving Card RelicArtifacts matching carving_signatures.json classes 1..5
    relics_data = [
        RelicArtifact(
            code="shore_temple_vimana",
            name="Shore Temple, Mahabalipuram",
            poi_id=2,
            detection_labels=["shore_temple_vimana"],
            architectural_style="Structural Granite Temple (Dravidian Pallava)",
            period="c. 725 AD (8th century AD)",
            story="Built with granite blocks overlooking the Bay of Bengal under Pallava king Narasimhavarman II, the Shore Temple is one of Southern India's oldest structural stone temples.",
            fun_fact="Classified as part of the UNESCO World Heritage Site at Mahabalipuram since 1984.",
            audio_narrative="Observe the structural granite tower overlooking the Bay of Bengal.",
            source=SRC_SHORE
        ),
        RelicArtifact(
            code="pancha_rathas",
            name="Pancha Rathas, Mahabalipuram",
            poi_id=3,
            detection_labels=["pancha_rathas"],
            architectural_style="Monolithic Indian Rock-Cut Architecture",
            period="7th-8th century CE",
            story="Five monolithic chariot-shaped monuments carved over single north-south sloping granite boulders, named after the Pandavas and Draupadi.",
            fun_fact="Though often called temples, the structures were never consecrated because they were never completed.",
            audio_narrative="Each ratha is carved out of a single sloping granite stone monolith.",
            source=SRC_RATHAS
        ),
        RelicArtifact(
            code="arjunas_penance",
            name="Arjuna's Penance (Descent of the Ganges)",
            poi_id=4,
            detection_labels=["arjunas_penance"],
            architectural_style="Pallava Open-Air Bas-Relief Sculpture",
            period="7th-8th century CE",
            story="Measuring 96 by 43 feet (29 m by 13 m) across two monolithic rock boulders, this relief portrays the descent of the river Ganges led by Bhagiratha and Arjuna's Penance.",
            fun_fact="Inscribed in 1984 as part of the UNESCO Group of Monuments at Mahabalipuram.",
            audio_narrative="Look at the narrative figures sculpted across two monumental boulders.",
            source=SRC_ARJUNA
        ),
        RelicArtifact(
            code="krishnas_butter_ball",
            name="Krishna's Butterball (Vaan Irai Kal)",
            poi_id=5,
            detection_labels=["krishnas_butter_ball"],
            architectural_style="Protected Natural Granite Boulder",
            period="ASI Protected National Monument",
            story="A gigantic balancing granite boulder resting on a short rocky incline at Mamallapuram alongside 7th- and 8th-century Pallava monuments.",
            fun_fact="Known locally as Vaan Irai Kal and listed as a protected monument by the Archaeological Survey of India.",
            audio_narrative="Notice how the boulder rests stably along the smooth granite incline.",
            source=SRC_BUTTERBALL
        ),
        RelicArtifact(
            code="mahishasuramardini_cave",
            name="Mahishasuramardini Mandapa (Cave Panel)",
            poi_id=7,
            detection_labels=["mahishasuramardini_cave"],
            architectural_style="Pallava Rock-Cut Cave Temple",
            period="Late 7th century CE",
            story="Known also as Yampuri, this rock-cut cave temple near the lighthouse hill preserves three iconic wall reliefs: Durga slaying Mahishasura, Vishnu reclining on Adishesha, and Shiva.",
            fun_fact="Part of the UNESCO Group of Monuments at Mahabalipuram inscribed in 1984.",
            audio_narrative="Inspect the sculpted multi-armed Durga panel carved inside the cave sanctum.",
            source=SRC_MAHISHASURA
        ),
    ]
    for r in relics_data:
        db.add(r)
    db.commit()

    quests_data = [
        ScavengerQuest(
            quest_id="quest_shore",
            title="By the Bay of Bengal",
            riddle="Built with blocks of granite rather than carved out of bedrock, my structural shrines face the sea since Narasimhavarman II's reign.",
            target_poi_slug="shore_temple_vimana",
            target_relic_code="shore_temple_vimana",
            hint="Scan Card LUNA-CARD-01 (shore_temple_vimana)",
            badge_name="Shore Temple Keeper",
            badge_icon="fa-landmark",
            points=120,
            source=SRC_SHORE
        ),
        ScavengerQuest(
            quest_id="quest_rathas",
            title="Five Unconsecrated Chariots",
            riddle="Five monolithic granite chariots resting on a north-south sloping stone ridge, named after the Pandavas and Draupadi.",
            target_poi_slug="pancha_rathas",
            target_relic_code="pancha_rathas",
            hint="Scan Card LUNA-CARD-02 (pancha_rathas)",
            badge_name="Ratha Monolith Seeker",
            badge_icon="fa-compass",
            points=150,
            source=SRC_RATHAS
        ),
        ScavengerQuest(
            quest_id="quest_penance",
            title="Stone Canvas of the Ganges",
            riddle="Measuring 96 by 43 feet across two granite boulders, I recount Bhagiratha guiding the sacred river down to earth.",
            target_poi_slug="arjunas_penance",
            target_relic_code="arjunas_penance",
            hint="Scan Card LUNA-CARD-03 (arjunas_penance)",
            badge_name="Bas-Relief Chronicler",
            badge_icon="fa-scroll",
            points=160,
            source=SRC_ARJUNA
        )
    ]
    for q in quests_data:
        db.add(q)
    db.commit()

    print("[Database] Seeded 7 Sourced Mahabalipuram Stops, 13 Paths, 5 Carving Cards, and 3 Quests!")
    db.close()


if __name__ == "__main__":
    seed_database(force_reset=True)
