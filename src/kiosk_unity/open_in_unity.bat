@echo off
set UNITY_EXE=C:\Program Files\Unity\Hub\Editor\6000.6.9f1\Editor\Unity.exe
set PROJECT_DIR=%~dp0

echo Opening Lunar Aurora Kiosk in Unity Editor...
start "" "%UNITY_EXE%" -projectPath "%PROJECT_DIR%"

