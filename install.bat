@echo off
setlocal EnableDelayedExpansion

REM -------------------------------------------------------------------------
REM Configuration
REM -------------------------------------------------------------------------
set "PYTHON_TARGET_VERSION=3.12"

REM -------------------------------------------------------------------------
REM Admin Privileges Check & Self-Elevation
REM -------------------------------------------------------------------------
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Requesting Administrative Privileges...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

echo ==========================================
echo SpeakEasy Installer
echo ==========================================
echo.

REM -------------------------------------------------------------------------
REM 1. Check/Install UV
REM -------------------------------------------------------------------------
echo [STEP 1/3] Checking for 'uv' package manager...
set "USE_UV=false"

where uv >nul 2>nul
if %errorlevel% equ 0 (
    echo [OK] 'uv' found.
    set "USE_UV=true"
) else (
    echo [INFO] 'uv' not found. Attempting to install...
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    if !errorlevel! equ 0 (
        echo [OK] 'uv' installed.
        set "USE_UV=true"
        REM Update PATH locally for this session
        set "PATH=%LOCALAPPDATA%\bin;%USERPROFILE%\.cargo\bin;%PATH%"
    ) else (
        echo [WARN] Failed to install uv. Will fall back to standard Python.
    )
)

REM -------------------------------------------------------------------------
REM 2. Setup Backend Environment
REM -------------------------------------------------------------------------
echo.
echo [STEP 2/3] Setting up Backend Environment...

if not exist "backend" (
    echo [ERROR] 'backend' directory not found in: %CD%
    pause
    exit /b 1
)

cd backend

if "!USE_UV!"=="true" (
    echo [INFO] Using 'uv' for backend setup...
    
    echo [INFO] Ensuring Python %PYTHON_TARGET_VERSION%...
    call uv python install %PYTHON_TARGET_VERSION%
    
    echo [INFO] Creating venv...
    call uv venv --python %PYTHON_TARGET_VERSION% --allow-existing
    
    echo [INFO] Installing dependencies...
    call uv pip install -e .
    if !errorlevel! neq 0 (
        echo [ERROR] Dependency installation failed.
        cd ..
        pause
        exit /b 1
    )
) else (
    echo [INFO] Using standard Python for backend setup...
    
    where python >nul 2>nul
    if !errorlevel! neq 0 (
        echo [ERROR] 'python' not found. Please install Python manually.
        cd ..
        pause
        exit /b 1
    )
    
    echo [INFO] Creating venv...
    python -m venv .venv
    
    echo [INFO] Installing dependencies...
    call .venv\Scripts\activate.bat
    pip install -e .
    if !errorlevel! neq 0 (
        echo [ERROR] Dependency installation failed.
        cd ..
        pause
        exit /b 1
    )
)

cd ..

REM -------------------------------------------------------------------------
REM 3. Install Frontend Dependencies
REM -------------------------------------------------------------------------
echo.
echo [STEP 3/3] Installing Frontend Dependencies (npm)...
if exist "gui" (
    cd gui
    
    echo [INFO] Checking for npm...
    where npm >nul 2>nul
    if !errorlevel! neq 0 (
        echo [ERROR] npm is not installed or not in PATH.
        echo [INFO] Please install Node.js (LTS) from https://nodejs.org/
        cd ..
        pause
        exit /b 1
    )

    echo [INFO] Running npm install...
    call npm install
    if !errorlevel! neq 0 (
        echo [ERROR] Frontend installation failed.
        cd ..
        pause
        exit /b 1
    )
    cd ..
) else (
    echo [WARN] 'gui' directory not found. Skipping frontend install.
)

echo.
echo ==========================================
echo Installation Complete!
echo ==========================================
echo.
echo To run the application:
echo   Double-click start.bat
echo.
echo Press any key to exit...
pause
