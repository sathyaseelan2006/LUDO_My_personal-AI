@echo off
REM LUDO Desktop Launcher
REM Activates virtual environment and runs LUDO

cd /d "%~dp0"
echo.
echo ========================================
echo    Starting L.U.D.O AI Assistant
echo ========================================
echo.

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Run LUDO
python HUD\JarvisHUD.py

REM Keep window open if there's an error
if errorlevel 1 (
    echo.
    echo ========================================
    echo    LUDO encountered an error
    echo ========================================
    pause
)
