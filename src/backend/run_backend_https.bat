@echo off
echo ========================================================
echo   Starting Lunar Aurora Backend with HTTPS (for Mobile WebXR)
echo ========================================================
cd /d "%~dp0"
python generate_ssl_certs.py
python -m uvicorn app.main:app --host 0.0.0.0 --port 8443 --ssl-keyfile key.pem --ssl-certfile cert.pem --reload
pause

