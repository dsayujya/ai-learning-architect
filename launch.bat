@echo off
color 0b
echo ====================================================
echo      AI LEARNING ARCHITECT - AUTO LAUNCHER
echo ====================================================
echo.

echo [1] Starting Python FastAPI Backend Engine...
start cmd /k "title AI-Backend & cd /d %~dp0 & python -m uvicorn app.main:app --reload --host localhost --port 8000"

:: Adding a small 2-second delay to ensure backend binds to port first
ping 127.0.0.1 -n 3 >nul

echo [2] Starting ReactJS Vite Frontend...
start cmd /k "title AI-Frontend & cd /d %~dp0frontend & npm run dev"

echo.
echo Launch sequence initiated! The services are booting up in separate terminal windows.
echo You can safely close this launcher window.
ping 127.0.0.1 -n 6 >nul
exit
