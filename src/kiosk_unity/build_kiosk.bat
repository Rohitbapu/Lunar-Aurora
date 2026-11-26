@echo off
set UNITY_EXE=C:\Program Files\Unity\Hub\Editor\6000.6.9f1\Editor\Unity.exe
set PROJECT_DIR=%~dp0

echo ========================================================
echo   Lunar Aurora - Compiling Unity Kiosk Standalone EXE
echo   Mode: No-SRD simulation mode (unless Sony plugin added)
echo ========================================================
echo Unity Path: "%UNITY_EXE%"
echo Project:    "%PROJECT_DIR%"

if not exist "%UNITY_EXE%" (
    echo [ERROR] Unity executable not found at "%UNITY_EXE%".
    echo Please verify your Unity installation path.
    pause
    exit /b 1
)

echo Starting compilation in headless batchmode...
"%UNITY_EXE%" -quit -batchmode -nographics -projectPath "%PROJECT_DIR%" -executeMethod LunarAurora.Editor.BuildScript.BuildStandaloneWindows -logFile "%PROJECT_DIR%build.log"

if %ERRORLEVEL% equ 0 (
    echo.
    echo [SUCCESS] Standalone EXE compiled cleanly!
    echo Build Output Folder: "%PROJECT_DIR%Builds\Windows_SonySRDisplay\"
) else (
    echo.
    echo [NOTICE] Build process finished with code %ERRORLEVEL%. Check build.log for details.
)

pause
