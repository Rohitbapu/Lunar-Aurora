@echo off
echo ========================================================
echo   Starting Lunar Aurora Multimodal Backend & AI Service
echo   (Both HTTP :8000 and HTTPS :8443 for Mobile WebXR)
echo ========================================================
cd /d "%~dp0"
python start_servers.py
pause
