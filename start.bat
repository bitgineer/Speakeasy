@echo off
setlocal EnableDelayedExpansion

echo ==========================================
echo SpeakEasy Startup Script
echo ==========================================

REM -------------------------------------------------------------------------
REM Pre-flight Checks
REM -------------------------------------------------------------------------
echo [CHECK] Verifying environment...

REM Check Python
python --version >nul 2>&1
if !errorlevel! neq 0 (
    echo [ERROR] Python is not installed or not in PATH.
    echo [INFO] Please install Python 3.10-3.12 from https://python.org
    pause
    exit /b 1
)

REM Check Node.js
node --version >nul 2>&1
if !errorlevel! neq 0 (
    echo [ERROR] Node.js is not installed or not in PATH.
    echo [INFO] Please install Node.js 18+ from https://nodejs.org
    pause
    exit /b 1
)

REM Check FFmpeg (optional but recommended)
ffmpeg -version >nul 2>&1
if !errorlevel! neq 0 (
    echo [WARN] FFmpeg not found. Audio file transcription will not work.
    echo [INFO] Install from https://ffmpeg.org
    timeout /t 3 >nul
)

REM Check UV package manager
uv --version >nul 2>&1
if !errorlevel! neq 0 (
    echo [INFO] Installing UV package manager...
    pip install uv
    if !errorlevel! neq 0 (
        echo [WARN] Failed to install UV. Continuing with pip...
    )
)

REM -------------------------------------------------------------------------
REM Setup Backend if needed
REM -------------------------------------------------------------------------
if exist "backend" (
    cd backend
    
    REM Check virtual environment
    if not exist ".venv" (
        echo [INFO] Creating Python virtual environment...
        uv venv --python 3.12 2>nul || uv venv --python 3.11 2>nul || uv venv --python 3.10
    )
    
    REM Activate and install
    call .venv\Scripts\activate.bat
    
    REM Check if dependencies are installed
    python -c "import speakeasy" >nul 2>&1
    if !errorlevel! neq 0 (
        echo [INFO] Installing backend dependencies...
        uv pip install -e ".[cuda]" 2>nul || uv pip install -e .
    )
    
    cd ..
)

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
