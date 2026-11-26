import socket
from urllib.parse import urlencode
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.session_service import session_service

router = APIRouter(prefix="/api/ticket", tags=["Ticketing Counter"])

class CreateTicketRequest(BaseModel):
    customer_name: str
    preferred_language: str = "en"

def get_lan_ip() -> str:
    """
    Returns active LAN IPv4 address (preferring private Wi-Fi/Ethernet 192.168/10/172 over VPNs).
    """
    candidates = []
    try:
        hostname = socket.gethostname()
        for info in socket.getaddrinfo(hostname, None, socket.AF_INET):
            ip = info[4][0]
            if not ip.startswith("127."):
                candidates.append(ip)
    except Exception:
        pass

    # Prefer standard private Wi-Fi subnets first
    for prefix in ("192.168.", "10.", "172."):
        for ip in candidates:
            if ip.startswith(prefix):
                return ip

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.5)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return candidates[0] if candidates else "localhost"

@router.post("/create")
def create_customer_ticket(req: CreateTicketRequest, request: Request, db: Session = Depends(get_db)):
    """
    Called by the ticket counter / kiosk after visitor registers/pays.
    Returns personalized ticket, session, and properly URL-encoded mobile tour URLs.
    """
    ticket_data = session_service.create_ticket(db, req.customer_name, req.preferred_language)
    req_host = request.url.hostname or "localhost"
    lan_ip = get_lan_ip() if req_host in ("localhost", "127.0.0.1", "0.0.0.0") else req_host

    query = urlencode({
        "ticket_id": ticket_data["ticket_id"],
        "session_id": ticket_data["session_id"],
        "name": ticket_data["customer_name"],
        "lang": ticket_data["language"],
    })
    ticket_data["https_url"] = f"https://{lan_ip}:8443/app/?{query}"
    ticket_data["http_url"] = f"http://{lan_ip}:8000/app/?{query}"

    return ticket_data

@router.get("/counter", response_class=HTMLResponse)
def ticket_counter_portal():
    """
    Web portal for the ticketing gate / cashier.
    Allows entering visitor name, language, and generating a personalized QR code on screen.
    """
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Lunar Aurora - Ticketing Counter</title>
        <link rel="stylesheet" href="/app/vendor/fontawesome/css/all.min.css">
        <style>
            body {
                background: #070b12; color: #fff; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                margin: 0; padding: 24px; display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 100vh;
            }
            .panel {
                background: rgba(18, 26, 42, 0.95); border: 1.5px solid #00e5ff; border-radius: 24px;
                padding: 32px; max-width: 500px; width: 100%; box-shadow: 0 12px 40px rgba(0, 229, 255, 0.25); box-sizing: border-box;
            }
            h1 { font-size: 1.5rem; color: #f4c430; margin-top: 0; display: flex; align-items: center; gap: 10px; }
            label { display: block; font-size: 0.85rem; color: #8ba2bd; margin-top: 14px; margin-bottom: 6px; font-weight: 600; }
            input, select {
                width: 100%; padding: 12px 14px; border-radius: 12px; border: 1px solid rgba(0, 229, 255, 0.4);
                background: rgba(255, 255, 255, 0.06); color: #fff; font-size: 0.95rem; box-sizing: border-box; outline: none;
            }
            select option { background: #101725; color: #fff; }
            input:focus, select:focus { border-color: #f4c430; }
            button {
                width: 100%; margin-top: 20px; padding: 14px; background: linear-gradient(135deg, #00e5ff, #00b4d8);
                color: #000; font-weight: 800; font-size: 1rem; border: none; border-radius: 20px; cursor: pointer;
                transition: transform 0.15s;
            }
            button:active { transform: scale(0.97); }
            #ticket-result {
                display: none; margin-top: 24px; padding-top: 20px; border-top: 1px solid rgba(255,255,255,0.1); text-align: center;
            }
            #qrcode {
                display: flex; justify-content: center; margin: 16px auto; background: #fff; padding: 14px; border-radius: 16px; width: fit-content;
            }
            .ticket-badge {
                display: inline-block; background: rgba(244, 196, 48, 0.15); border: 1px solid #f4c430;
                color: #f4c430; padding: 4px 12px; border-radius: 12px; font-weight: 700; font-size: 0.85rem; margin-bottom: 8px;
            }
            .direct-link {
                color: #00e5ff; font-size: 0.82rem; word-break: break-all; text-decoration: none; display: block; margin-top: 10px;
            }
        </style>
        <script src="/app/vendor/qrcode/qrcode.min.js"></script>
    </head>
    <body>
        <div class="panel">
            <h1><i class="fa-solid fa-ticket"></i> Ticketing Counter & Kiosk</h1>
            <p style="font-size: 0.85rem; color: #8ba2bd; margin-bottom: 18px;">
                Issue personalized tickets for arriving visitors. Generates a unique QR code encoded with their name and session token.
            </p>

            <label for="cust-name">Visitor Name</label>
            <input type="text" id="cust-name" placeholder="e.g. Rahul Sharma" value="Rahul Sharma">

            <label for="cust-lang">Preferred Tour Language</label>
            <select id="cust-lang">
                <option value="en">English (US)</option>
                <option value="hi">हिंदी (Hindi)</option>
                <option value="es">Español (Spanish)</option>
                <option value="fr">Français (French)</option>
                <option value="de">Deutsch (German)</option>
                <option value="ja">日本語 (Japanese)</option>
                <option value="ta">தமிழ் (Tamil)</option>
            </select>

            <button id="btn-issue-ticket"><i class="fa-solid fa-qrcode"></i> Issue Ticket & Generate QR</button>

            <div id="ticket-result">
                <div class="ticket-badge" id="res-ticket-id">TICKET #LUNA-0000</div>
                <h3 style="color: #fff; margin: 6px 0;" id="res-greeting">Welcome, Rahul!</h3>
                <p style="font-size: 0.78rem; color: #b0bec5; margin: 4px 0;">Scan with phone camera to begin your personal tour:</p>
                <div id="qrcode"></div>
                <a class="direct-link" id="res-direct-link" target="_blank" href="#">Click here to launch tour directly</a>
            </div>
        </div>

        <script>
            document.getElementById('btn-issue-ticket').addEventListener('click', async () => {
                const name = document.getElementById('cust-name').value.trim() || 'Honored Traveler';
                const lang = document.getElementById('cust-lang').value;

                try {
                    const res = await fetch('/api/ticket/create', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ customer_name: name, preferred_language: lang })
                    });

                    if (res.ok) {
                        const data = await res.json();
                        document.getElementById('ticket-result').style.display = 'block';
                        document.getElementById('res-ticket-id').textContent = `TICKET #${data.ticket_id}`;
                        document.getElementById('res-greeting').textContent = `Welcome, ${data.customer_name}!`;
                        document.getElementById('res-direct-link').href = data.https_url;
                        document.getElementById('res-direct-link').textContent = `Open ${data.customer_name}'s Tour (HTTPS)`;

                        const qrContainer = document.getElementById('qrcode');
                        qrContainer.innerHTML = '';
                        new QRCode(qrContainer, {
                            text: data.https_url,
                            width: 200,
                            height: 200,
                            colorDark : "#0a0e17",
                            colorLight : "#ffffff",
                            correctLevel : QRCode.CorrectLevel.M
                        });
                    }
                } catch (e) {
                    alert('Error creating ticket: ' + e);
                }
            });
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)
