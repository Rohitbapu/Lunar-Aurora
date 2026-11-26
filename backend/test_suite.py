import sys
from urllib.parse import urlparse, parse_qs
from fastapi.testclient import TestClient
from app.main import app

def run_tests():
    client = TestClient(app)

    print("1. Testing Root & Health:")
    assert client.get("/").status_code == 200
    assert client.get("/health").status_code == 200
    print("   -> OK")

    print("2. Testing Ticketing Counter Portal & URL-Encoded QR URL:")
    r_ticket_page = client.get("/ticket")
    assert r_ticket_page.status_code == 200 and "Ticketing Counter" in r_ticket_page.text
    r_create_ticket = client.post("/api/ticket/create", json={"customer_name": "Priya Patel", "preferred_language": "en"})
    assert r_create_ticket.status_code == 200
    ticket_data = r_create_ticket.json()
    parsed = parse_qs(urlparse(ticket_data["https_url"]).query)
    assert parsed["name"][0] == "Priya Patel"
    print(f"   -> OK (Issued Ticket #{ticket_data['ticket_id']}, properly encoded URL)")

    print("3. Testing Personalized Session Start & Stop 1 Audio Synthesis:")
    session_id = ticket_data["session_id"]
    r_start = client.post("/api/session/start", json={"session_id": session_id, "customer_name": "Priya Patel", "generate_audio": True})
    assert r_start.status_code == 200
    sess = r_start.json()
    assert sess["current_step"] == 1
    assert "Priya Patel" in sess["current_stop"]["personalized_welcome"]
    assert sess["current_stop"]["audio_url"] is not None
    print(f"   -> OK (Personalized Welcome + Audio URL ready: {sess['current_stop']['audio_url']})")

    print("4. Testing Sequential Stop Advancement (Stop 1 -> Stop 2):")
    r_adv = client.post("/api/session/advance", json={"session_id": session_id})
    assert r_adv.status_code == 200
    adv = r_adv.json()
    assert adv["current_step"] == 2
    assert "Priya Patel" in adv["stop"]["personalized_welcome"]
    print(f"   -> OK (Advanced to Stop 2: {adv['stop']['title']}, Total XP: {adv['total_xp']})")

    print("5. Testing Blueprint Live Map Data:")
    r_bp = client.get(f"/api/session/{session_id}/blueprint")
    assert r_bp.status_code == 200
    bp = r_bp.json()
    assert bp["total_steps"] == 7
    assert bp["current_step"] == 2
    print(f"   -> OK ({bp['total_steps']} Blueprint Stations, Current Step: {bp['current_step']})")

    print("6. Testing Shaded Path & True Tree-Shade Rest Routing:")
    r_path = client.get("/api/routing/path?start_id=1&target_id=7&mode=shaded&hour=13.0")
    assert r_path.status_code == 200 and r_path.json()["found"] is True
    r_rest = client.get("/api/routing/take-a-rest?current_node_id=1&hour=12.0")
    assert r_rest.status_code == 200 and r_rest.json()["found"] is True
    rest_dest = r_rest.json()["path_nodes"][-1]["name"]
    assert "Gallery" in rest_dest or "Bastion" in rest_dest
    print(f"   -> OK (Rest Stop routes to true shaded pavilion: {rest_dest})")

    print("7. Testing Context-Aware Point & Know + Scavenger Auto-Unlock:")
    r_vis = client.post("/api/vision/identify", json={
        "detected_labels": ["elephant", "carving"],
        "current_step": 2,
        "session_id": session_id,
        "language": "en"
    })
    assert r_vis.status_code == 200
    vis_data = r_vis.json()
    assert vis_data["artifact"]["code"] == "carved_elephant"
    assert vis_data["quest_unlocked"] is not None
    print(f"   -> OK (Identified: {vis_data['artifact']['name']} + Unlocked Quest: {vis_data['quest_unlocked']['badge_name']})")

    print("8. Testing Personalized AI Chat + Session Chat Persistence:")
    r_chat = client.post("/api/chat", json={
        "message": "Where should I walk next?",
        "customer_name": "Priya Patel",
        "current_step": 2,
        "session_id": session_id,
        "language": "en",
        "generate_audio": False
    })
    assert r_chat.status_code == 200
    r_resume = client.get(f"/api/session/{session_id}")
    assert r_resume.status_code == 200
    assert len(r_resume.json()["chat_history"]) >= 2
    print(f"   -> OK (Chat persisted in session DB: {r_chat.json()['reply'][:60]}...)")

    print("9. Testing Tour End & Certificate Generation:")
    r_end = client.post("/api/session/end", json={"session_id": session_id})
    assert r_end.status_code == 200
    cert = r_end.json()
    assert cert["status"] == "completed" and "Priya Patel" in cert["farewell_message"]
    print(f"   -> OK (Issued Certificate for {cert['customer_name']} with {cert['total_xp']} XP)")

    print("\n[SUCCESS] ALL 9 END-TO-END MULTIMODAL & SESSION TESTS PASSED!")

if __name__ == "__main__":
    run_tests()
