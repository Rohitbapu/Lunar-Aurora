import io
import base64
from urllib.parse import urlparse, parse_qs
from PIL import Image
from fastapi.testclient import TestClient
from app.main import app
from init_db import seed_database

def _make_sample_jpeg_b64() -> str:
    buf = io.BytesIO()
    Image.new("RGB", (64, 48), color=(14, 42, 68)).save(buf, format="JPEG")
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode("ascii")

TINY_JPEG_B64 = _make_sample_jpeg_b64()

NEW_CARD_CLASSES = [
    "shore_temple_vimana",
    "pancha_rathas",
    "arjunas_penance",
    "krishnas_butter_ball",
    "mahishasuramardini_cave",
]

def run_tests():
    seed_database(force_reset=True)
    client = TestClient(app)

    print("1. Testing Root, Health, Overview & /static/cards Images:")
    assert client.get("/").status_code == 200
    assert client.get("/health").status_code == 200
    ov = client.get("/api/site/overview")
    assert ov.status_code == 200 and "Mahabalipuram" in ov.json()["site_name"]
    for img_name in [
        "01_shore_temple_vimana.jpg",
        "02_pancha_rathas.jpg",
        "03_arjunas_penance.jpg",
        "04_krishnas_butter_ball.jpg",
        "05_mahishasuramardini_cave.jpg",
    ]:
        assert client.get(f"/static/cards/{img_name}").status_code == 200
    print("   -> OK (all 5 Wikimedia card photos served locally)")

    print("2. Testing Ticketing Counter Portal & URL-Encoded QR URL (EN/TA/HI):")
    r_ticket_page = client.get("/ticket")
    assert r_ticket_page.status_code == 200 and "Ticketing Counter" in r_ticket_page.text
    r_create_ticket = client.post("/api/ticket/create", json={"customer_name": "Priya Patel", "preferred_language": "en"})
    assert r_create_ticket.status_code == 200
    ticket_data = r_create_ticket.json()
    parsed = parse_qs(urlparse(ticket_data["https_url"]).query)
    assert parsed["name"][0] == "Priya Patel"
    print(f"   -> OK (Ticket #{ticket_data['ticket_id']})")

    print("3. Testing Personalized Session Start, Sourced Riddle Quiz & Audio Failsafe:")
    session_id = ticket_data["session_id"]
    r_start = client.post("/api/session/start", json={"session_id": session_id, "customer_name": "Priya Patel", "generate_audio": True})
    assert r_start.status_code == 200
    sess = r_start.json()
    assert sess["current_step"] == 1
    assert "Priya Patel" in sess["current_stop"]["personalized_welcome"]
    assert sess["current_stop"]["source"].startswith("https://")
    r_riddle = client.post("/api/session/riddle", json={
        "session_id": session_id,
        "step_number": 1,
        "answer": sess["current_stop"]["riddle"]["answer"]
    })
    assert r_riddle.status_code == 200 and r_riddle.json()["correct"] is True
    assert r_riddle.json()["xp_awarded"] == 45
    print("   -> OK (Session Start + Sourced Riddle +45 XP verified)")

    print("4. Testing Sequential Stop Advancement (Stop 1 -> Stop 2 Shore Temple Shrines):")
    r_adv = client.post("/api/session/advance", json={"session_id": session_id})
    assert r_adv.status_code == 200
    adv = r_adv.json()
    assert adv["current_step"] == 2
    assert "Shore Temple" in adv["stop"]["title"]
    assert adv["stop"]["source"].startswith("https://")
    print(f"   -> OK (Advanced to Stop 2: {adv['stop']['title']}, XP: {adv['total_xp']})")

    print("5. Testing 7-Stop Blueprint Map Data & Source URLs:")
    r_bp = client.get(f"/api/session/{session_id}/blueprint")
    assert r_bp.status_code == 200 and r_bp.json()["total_steps"] == 7
    assert all(s["source"] and s["source"].startswith("https://") for s in r_bp.json()["stops"])
    print("   -> OK (all 7 stops have valid source URLs)")

    print("6. Testing Dual Telemetry (Shortest Sun vs NOAA-Shaded Route) & Cave Shade Rest Routing:")
    r_tel = client.get("/api/site/telemetry?start_id=1&target_id=7&hour=12.0&date=2027-01-11")
    assert r_tel.status_code == 200
    tel = r_tel.json()
    assert tel["found"] is True
    assert tel["date"] == "2027-01-11"
    assert tel["solar_model"] == "NOAA General Solar Position Equations"
    assert "model estimate" in tel["heat_estimate_note"]
    assert tel["heat_exposure_saved_pct"] > 0.0
    r_rest = client.get("/api/routing/take-a-rest?current_node_id=1&hour=12.0&date=2027-01-11")
    assert r_rest.status_code == 200 and r_rest.json()["found"] is True
    rest_dest = r_rest.json()["path_nodes"][-1]["name"]
    assert "Varaha" in rest_dest or "Mahishasuramardini" in rest_dest
    print(f"   -> OK (2027-01-11 12:00 IST | Elev: {tel['solar_elevation_deg']} deg | Heat Saved [model estimate]: {tel['heat_exposure_saved_pct']}%, Rest: {rest_dest})")

    print("6b. Verifying NOAA Solar Position Equations vs Meeus Reference (2027-01-11 @ 09:00, 12:00, 16:00 IST):")
    # Hand-verified Meeus Julian Day reference values for Mahabalipuram (12.6165 N, 80.19 E, IST UTC+5:30) on 2027-01-11:
    noaa_ref = [
        (9.0, 30.68, 125.18),
        (12.0, 55.31, 173.07),
        (16.0, 25.40, 238.16),
    ]
    print("   Hour(IST) | NOAA Elev | Ref Elev | Diff  | NOAA Azim | Ref Azim | Diff  | Decl   | EoT(m) | HA")
    for h, ref_el, ref_az in noaa_ref:
        r_sol = client.get(f"/api/routing/solar-status?date=2027-01-11&hour={h}")
        assert r_sol.status_code == 200
        s = r_sol.json()
        el, az = s["solar_elevation_deg"], s["solar_azimuth_deg"]
        el_diff = abs(el - ref_el)
        az_diff = abs(az - ref_az)
        assert el_diff < 0.5 and az_diff < 0.5, f"Solar mismatch at {h}: {s}"
        print(
            f"   {h:9.1f} | {el:9.2f} | {ref_el:8.2f} | {el_diff:5.2f} | "
            f"{az:9.2f} | {ref_az:8.2f} | {az_diff:5.2f} | "
            f"{s['declination_deg']:6.2f} | {s['equation_of_time_min']:6.2f} | {s['hour_angle_deg']:6.2f}"
        )
    # Invalid date check
    assert client.get("/api/routing/solar-status?date=invalid-date").status_code == 400

    print("7. Testing All 5 Mahabalipuram Card Classes, Scavenger Unlock & No-Guessing Check:")
    for card_cls in NEW_CARD_CLASSES:
        r_cls = client.post("/api/vision/identify", json={
            "detected_labels": [card_cls],
            "session_id": session_id,
            "language": "en"
        })
        assert r_cls.status_code == 200
        art = r_cls.json()["artifact"]
        assert art["code"] == card_cls and art["confidence_match"] is True
        assert art["source"] and art["source"].startswith("https://")
        assert art["image_url"] and client.get(art["image_url"]).status_code == 200

    # Empty/background labels must never guess a relic
    for invalid in ([], ["background"]):
        r_empty = client.post("/api/vision/identify", json={
            "detected_labels": invalid,
            "current_step": 2,
            "session_id": session_id,
            "language": "en"
        })
        assert r_empty.status_code == 200
        assert r_empty.json()["artifact"]["confidence_match"] is False
        assert r_empty.json()["artifact"]["code"] == "unregistered_feature"
    print("   -> OK (all 5 classes verified + background/empty never guess)")

    print("8. Testing Multilingual Chat & Session Persistence:")
    r_chat = client.post("/api/chat", json={
        "message": "Where is the nearest shaded cave rest stop?",
        "customer_name": "Priya Patel",
        "current_step": 2,
        "session_id": session_id,
        "language": "en",
        "generate_audio": False
    })
    assert r_chat.status_code == 200
    assert len(client.get(f"/api/session/{session_id}").json()["chat_history"]) >= 2
    print("   -> OK")

    print("9. Testing AR Memory Photo Snapshot & PDF Travel Journal Export:")
    r_photo = client.post(f"/api/tour/{session_id}/photo", json={
        "stop_step": 2,
        "stop_title": "Shore Temple Shrines",
        "image_base64": TINY_JPEG_B64
    })
    assert r_photo.status_code == 200 and r_photo.json()["saved"] is True
    r_end = client.post("/api/session/end", json={"session_id": session_id})
    assert r_end.status_code == 200 and r_end.json()["status"] == "completed"
    r_pdf = client.post(f"/api/tour/{session_id}/journal", json={})
    assert r_pdf.status_code == 200
    assert r_pdf.headers["content-type"].startswith("application/pdf")
    assert r_pdf.content.startswith(b"%PDF")
    print(f"   -> OK (PDF Travel Journal generated: {len(r_pdf.content)} bytes)")

    print("\n[SUCCESS] ALL 9 END-TO-END MAHABALIPURAM TESTS PASSED!")

if __name__ == "__main__":
    run_tests()
