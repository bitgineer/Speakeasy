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
echo [STEP 1/5] Checking for 'uv' package manager...
where uv >nul 2>nul
if %errorlevel% neq 0 (
    echo [INFO] 'uv' not found in PATH. Installing...
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install uv.
        pause
        exit /b 1
    )
    REM Add likely install locations to PATH for this session
    set "PATH=%LOCALAPPDATA%\bin;%USERPROFILE%\.cargo\bin;%PATH%"
) else (
    echo [OK] 'uv' found.
)

REM -------------------------------------------------------------------------
REM 2. Install Python
REM -------------------------------------------------------------------------
echo.
echo [STEP 2/5] Ensuring Python %PYTHON_TARGET_VERSION% is installed...
call uv python install %PYTHON_TARGET_VERSION%
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install Python %PYTHON_TARGET_VERSION% via uv.
    pause
    exit /b 1
)
echo [OK] Python %PYTHON_TARGET_VERSION% is ready.

REM -------------------------------------------------------------------------
REM 3. Setup Backend Environment
REM -------------------------------------------------------------------------
echo.
echo [STEP 3/5] Setting up Backend Virtual Environment...

if not exist "backend" (
    echo [ERROR] 'backend' directory not found in: %CD%
    pause
    exit /b 1
)

cd backend

echo [INFO] Creating venv (Python %PYTHON_TARGET_VERSION%)...
call uv venv --python %PYTHON_TARGET_VERSION% --allow-existing
if %errorlevel% neq 0 (
    echo [ERROR] Failed to create virtual environment.
    cd ..
    pause
    exit /b 1
)

REM -------------------------------------------------------------------------
REM 4. Install Dependencies
REM -------------------------------------------------------------------------
echo.
echo [STEP 4/5] Installing dependencies...
echo [INFO] This might take a few minutes. Please wait.

call uv pip install -e .
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Failed to install backend dependencies.
    echo [INFO] Please check the error message above.
    cd ..
    pause
    exit /b 1
)

cd ..

REM -------------------------------------------------------------------------
REM 5. Install Frontend Dependencies
REM -------------------------------------------------------------------------
echo.
echo [STEP 5/5] Installing Frontend Dependencies (npm)...
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
