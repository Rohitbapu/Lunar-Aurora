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

def run_tests():
    seed_database(force_reset=True)
    client = TestClient(app)

    print("1. Testing Root, Health & Mahabalipuram Site Overview:")
    assert client.get("/").status_code == 200
    assert client.get("/health").status_code == 200
    ov = client.get("/api/site/overview")
    assert ov.status_code == 200 and "Mahabalipuram" in ov.json()["site_name"]
    print("   -> OK")

    print("2. Testing Ticketing Counter Portal & URL-Encoded QR URL (EN/TA/HI):")
    r_ticket_page = client.get("/ticket")
    assert r_ticket_page.status_code == 200 and "Ticketing Counter" in r_ticket_page.text
    r_create_ticket = client.post("/api/ticket/create", json={"customer_name": "Priya Patel", "preferred_language": "en"})
    assert r_create_ticket.status_code == 200
    ticket_data = r_create_ticket.json()
    parsed = parse_qs(urlparse(ticket_data["https_url"]).query)
    assert parsed["name"][0] == "Priya Patel"
    print(f"   -> OK (Ticket #{ticket_data['ticket_id']})")

    print("3. Testing Personalized Session Start, Riddle Quiz & Audio Failsafe:")
    session_id = ticket_data["session_id"]
    r_start = client.post("/api/session/start", json={"session_id": session_id, "customer_name": "Priya Patel", "generate_audio": True})
    assert r_start.status_code == 200
    sess = r_start.json()
    assert sess["current_step"] == 1
    assert "Priya Patel" in sess["current_stop"]["personalized_welcome"]
    assert sess["current_stop"]["riddle"] is not None
    r_riddle = client.post("/api/session/riddle", json={
        "session_id": session_id,
        "step_number": 1,
        "answer": sess["current_stop"]["riddle"]["answer"]
    })
    assert r_riddle.status_code == 200 and r_riddle.json()["correct"] is True
    assert r_riddle.json()["xp_awarded"] == 45
    print("   -> OK (Session Start + Riddle +45 XP verified)")

    print("4. Testing Sequential Stop Advancement (Stop 1 -> Stop 2):")
    r_adv = client.post("/api/session/advance", json={"session_id": session_id})
    assert r_adv.status_code == 200
    adv = r_adv.json()
    assert adv["current_step"] == 2
    assert "Priya Patel" in adv["stop"]["personalized_welcome"]
    print(f"   -> OK (Advanced to Stop 2: {adv['stop']['title']}, XP: {adv['total_xp']})")

    print("5. Testing 7-Stop Blueprint Map Data:")
    r_bp = client.get(f"/api/session/{session_id}/blueprint")
    assert r_bp.status_code == 200 and r_bp.json()["total_steps"] == 7
    print("   -> OK")

    print("6. Testing Dual Telemetry (Shortest Sun vs Shaded Green Route) & Rest Routing:")
    r_tel = client.get("/api/site/telemetry?start_id=1&target_id=7&hour=13.0")
    assert r_tel.status_code == 200
    tel = r_tel.json()
    assert tel["found"] is True
    assert len(tel["shortest_path"]["path_node_ids"]) >= 2
    assert len(tel["shaded_path"]["path_node_ids"]) >= 2
    assert tel["heat_exposure_saved_pct"] >= 0.0
    r_rest = client.get("/api/routing/take-a-rest?current_node_id=1&hour=12.0")
    assert r_rest.status_code == 200 and r_rest.json()["found"] is True
    rest_dest = r_rest.json()["path_nodes"][-1]["name"]
    assert "Banyan" in rest_dest or "Bastion" in rest_dest
    print(f"   -> OK (Heat Saved: {tel['heat_exposure_saved_pct']}%, Rest: {rest_dest})")

    print("7. Testing Custom Carving Card Recognition & Scavenger Unlock:")
    r_vis = client.post("/api/vision/identify", json={
        "detected_labels": ["yali_pillar"],
        "current_step": 2,
        "session_id": session_id,
        "language": "en"
    })
    assert r_vis.status_code == 200
    vis_data = r_vis.json()
    assert vis_data["artifact"]["code"] == "yali_pillar"
    assert vis_data["quest_unlocked"] is not None
    print(f"   -> OK (Identified: {vis_data['artifact']['name']} + Quest: {vis_data['quest_unlocked']['badge_name']})")

    print("8. Testing Multilingual Chat (2.5s Timeout Safety) & Session Persistence:")
    r_chat = client.post("/api/chat", json={
        "message": "Where is the nearest shaded rest area?",
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
        "stop_title": "Monolithic Yali Pillars Gallery",
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

    print("\n[SUCCESS] ALL 9 END-TO-END MAHABALIPURAM BACKEND TESTS PASSED!")

if __name__ == "__main__":
    run_tests()
