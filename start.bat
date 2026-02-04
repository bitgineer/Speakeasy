@echo off
setlocal EnableDelayedExpansion

echo ==========================================
echo SpeakEasy Startup Script
echo ==========================================

REM -------------------------------------------------------------------------
REM 1. Start Frontend (which handles Backend)
REM -------------------------------------------------------------------------
echo [INFO] Starting Application...

cd /d "%~dp0"

if exist "gui" (
    cd gui
    REM Check if node_modules exists
    if not exist "node_modules" (
        echo [WARN] node_modules not found in gui.
        echo [INFO] Running npm install...
        call npm install
        if !errorlevel! neq 0 (
            echo [ERROR] npm install failed.
            pause
            exit /b 1
        )
    )
    
    echo [INFO] Starting Electron App...
    REM This will start the electron app, which spawns the backend
    npm run dev
    
    cd ..
) else (
    echo [ERROR] 'gui' directory not found!
    pause
    exit /b 1
)

echo.
echo [SUCCESS] Application exited.
timeout /t 3 >nul
exit
