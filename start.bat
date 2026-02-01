@echo off
setlocal EnableDelayedExpansion

echo ==========================================
echo SpeakEasy Startup Script
echo ==========================================

REM -------------------------------------------------------------------------
REM 1. Start Backend
REM -------------------------------------------------------------------------
echo [INFO] Starting Backend Server...
if exist "backend" (
    cd backend
    REM Start backend in a new command window
    start "SpeakEasy Backend" cmd /k "uv run uvicorn speakeasy.server:app --reload"
    cd ..
) else (
    echo [ERROR] 'backend' directory not found!
    pause
    exit /b 1
)

REM -------------------------------------------------------------------------
REM 2. Start Frontend
REM -------------------------------------------------------------------------
echo [INFO] Starting Frontend (GUI)...
if exist "gui" (
    cd gui
    REM Check if node_modules exists, offer to install if missing
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
    
    REM Start frontend in a new command window
    start "SpeakEasy Frontend" cmd /k "npm run dev"
    cd ..
) else (
    echo [ERROR] 'gui' directory not found!
    pause
    exit /b 1
)

echo.
echo [SUCCESS] Both services launched in separate windows.
echo You can close this window now.
timeout /t 5 >nul
exit
