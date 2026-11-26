@echo off
echo ========================================================
echo   Connecting Android Mobile Device via ADB Reverse
echo ========================================================
echo.
echo Make sure:
echo 1. Your Android phone is plugged in via USB cable
echo 2. "USB Debugging" is enabled in Developer Options
echo.
adb devices
echo.
echo Forwarding port 8000 to phone...
adb reverse tcp:8000 tcp:8000

if %ERRORLEVEL% equ 0 (
    echo.
    echo [SUCCESS] Port 8000 forwarded to phone!
    echo Now open Chrome on your mobile device and visit:
    echo    http://localhost:8000/app/
    echo (Because it uses localhost, Chrome grants full camera, WebXR, and audio permissions!)
) else (
    echo.
    echo [NOTICE] If ADB is not found, install Android Platform Tools or use HTTPS over Wi-Fi (run_backend_https.bat).
)
pause
