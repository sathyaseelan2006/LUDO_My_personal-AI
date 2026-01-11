@echo off
REM LUDO Desktop Launcher (No Console Window)
REM Runs LUDO in background without showing terminal

cd /d "%~dp0"

REM Activate virtual environment and run LUDO silently
start /B .venv\Scripts\pythonw.exe HUD\JarvisHUD.py
