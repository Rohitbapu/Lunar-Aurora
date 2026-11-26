import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from app.config import settings
from app.routers import chat, routing, vision, scavenger, site, ticket, session

app = FastAPI(
    title="Lunar Aurora API",
    description="Multimodal Spatial Historical AI Guide Backend for WebXR & Sony Spatial Reality Display",
    version="1.0.0"
)

# Enable CORS for mobile WebXR browsers & Unity Kiosk integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(chat.router)
app.include_router(routing.router)
app.include_router(vision.router)
app.include_router(scavenger.router)
app.include_router(site.router)
app.include_router(ticket.router)
app.include_router(session.router)

# Direct route for ticketing counter
@app.get("/ticket", response_class=HTMLResponse)
def ticket_page():
    return ticket.ticket_counter_portal()

# Mount static audio cache
os.makedirs(settings.AUDIO_CACHE_DIR, exist_ok=True)
app.mount("/static/audio", StaticFiles(directory=settings.AUDIO_CACHE_DIR), name="static_audio")

# Mount frontend_webxr as static web application
webxr_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend_webxr"))
if os.path.exists(webxr_dir):
    app.mount("/app", StaticFiles(directory=webxr_dir, html=True), name="frontend_webxr")

@app.get("/qr", response_class=HTMLResponse)
def get_qr_page():
    local_ip = ticket.get_lan_ip()

    http_url = f"http://{local_ip}:8000/app/"
    https_url = f"https://{local_ip}:8443/app/"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Lunar Aurora - Mobile AR QR Code</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{
                background: #0a0e17; color: #fff; font-family: sans-serif;
                display: flex; flex-direction: column; align-items: center; justify-content: center;
                min-height: 100vh; margin: 0; padding: 20px; box-sizing: border-box; text-align: center;
            }}
            .card {{
                background: rgba(18, 26, 42, 0.92); border: 1px solid #00e5ff;
                border-radius: 24px; padding: 28px; box-shadow: 0 8px 32px rgba(0,229,255,0.3);
                max-width: 440px; width: 100%;
            }}
            h2 {{ color: #f4c430; margin-bottom: 6px; letter-spacing: 1px; }}
            p {{ color: #8ba2bd; font-size: 0.88rem; margin-bottom: 16px; line-height: 1.4; }}
            .notice-box {{
                background: rgba(0, 229, 255, 0.1); border: 1px solid rgba(0, 229, 255, 0.3);
                padding: 10px 14px; border-radius: 12px; font-size: 0.8rem; color: #e0f7fa; margin-bottom: 18px; text-align: left;
            }}
            #qrcode {{
                display: flex; justify-content: center; margin: 12px 0;
                background: #fff; padding: 14px; border-radius: 16px;
            }}
            .url-btn {{
                display: block; background: #00e5ff; color: #000; font-weight: 700;
                padding: 10px 16px; border-radius: 20px; text-decoration: none; font-size: 0.88rem;
                margin-top: 14px; transition: transform 0.2s;
            }}
            .url-box {{
                background: rgba(255,255,255,0.06); padding: 8px 12px;
                border-radius: 8px; font-family: monospace; font-size: 0.78rem;
                color: #8ba2bd; word-break: break-all; margin-top: 10px;
            }}
        </style>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/qrcodejs/1.0.0/qrcode.min.js"></script>
    </head>
    <body>
        <div class="card">
            <h2>LUNAR AURORA</h2>
            <p>Scan with your <strong>mobile camera</strong> to launch the Zero-Install AR tour.</p>
            
            <div class="notice-box">
                🔒 <strong>For Camera & WebXR on Android Chrome:</strong><br>
                Android requires HTTPS for camera access. When scanning, Chrome may show "Your connection is not private" for local SSL — simply tap <em>Advanced &rarr; Proceed to {local_ip}</em>.
            </div>

            <div id="qrcode"></div>
            <a class="url-btn" href="{https_url}">Open HTTPS WebXR Tour</a>
            <div class="url-box">Direct Link: {https_url}</div>
        </div>
        <script>
            new QRCode(document.getElementById("qrcode"), {{
                text: "{https_url}",
                width: 220,
                height: 220,
                colorDark : "#0a0e17",
                colorLight : "#ffffff",
                correctLevel : QRCode.CorrectLevel.M
            }});
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/")
def root():
    return {
        "project": "Lunar Aurora",
        "tagline": "Glasses-Free Holographic & Zero-Install WebXR Archaeological Guide",
        "status": "online",
        "endpoints": {
            "webxr_app": "/app/",
            "api_docs": "/docs",
            "chat": "/api/chat",
            "routing": "/api/routing/path",
            "take_a_rest": "/api/routing/take-a-rest",
            "vision": "/api/vision/identify",
            "scavenger": "/api/scavenger/quests",
            "site_overview": "/api/site/overview"
        }
    }

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "lunar_aurora_backend"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
