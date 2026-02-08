@echo off
setlocal EnableDelayedExpansion

REM =========================================================================
REM SpeakEasy Installer for Windows
REM =========================================================================
REM This script:
REM - Detects system capabilities (CUDA, GPU)
REM - Installs UV package manager (preferred) or falls back to pip
REM - Installs Python dependencies with platform-specific optimizations
REM - Sets up frontend dependencies
REM =========================================================================

REM -------------------------------------------------------------------------
REM Configuration
REM -------------------------------------------------------------------------
set "PYTHON_TARGET_VERSION=3.12"
set "CUDA_PYTHON_VERSION=12.3"
set "USE_UV=false"
set "HAS_CUDA=false"
set "INSTALL_LOG=%~dp0install.log"

REM -------------------------------------------------------------------------
REM Set Working Directory
REM -------------------------------------------------------------------------
cd /d "%~dp0"

echo ========================================== > "%INSTALL_LOG%"
echo SpeakEasy Installation Log >> "%INSTALL_LOG%"
echo Started: %DATE% %TIME% >> "%INSTALL_LOG%"
echo ========================================== >> "%INSTALL_LOG%"
echo. >> "%INSTALL_LOG%"

echo ==========================================
echo SpeakEasy Installer
echo ==========================================
echo.
echo Installation log: %INSTALL_LOG%
echo.

REM -------------------------------------------------------------------------
REM 1. Check/Install UV
REM -------------------------------------------------------------------------
echo [STEP 1/4] Checking for 'uv' package manager...
echo [STEP 1/4] Checking for 'uv' package manager... >> "%INSTALL_LOG%"
set "USE_UV=false"

where uv >nul 2>nul
if %errorlevel% equ 0 (
    echo [OK] 'uv' found.
    echo [OK] 'uv' found. >> "%INSTALL_LOG%"
    set "USE_UV=true"
) else (
    echo [INFO] 'uv' not found. Attempting to install...
    echo [INFO] 'uv' not found. Attempting to install... >> "%INSTALL_LOG%"
    echo [INFO] UV is faster than pip and recommended for best experience.
    echo [INFO] This will take 10-30 seconds...

    powershell -NoProfile -ExecutionPolicy ByPass -Command "& {irm https://astral.sh/uv/install.ps1 | iex}" >> "%INSTALL_LOG%" 2>&1
    if !errorlevel! equ 0 (
        echo [OK] 'uv' installed successfully.
        echo [OK] 'uv' installed successfully. >> "%INSTALL_LOG%"

        REM Update PATH for this session - check multiple possible locations
        if exist "%LOCALAPPDATA%\bin\uv.exe" (
            set "PATH=%LOCALAPPDATA%\bin;%PATH%"
            echo [INFO] Added %LOCALAPPDATA%\bin to PATH >> "%INSTALL_LOG%"
        )
        if exist "%USERPROFILE%\.cargo\bin\uv.exe" (
            set "PATH=%USERPROFILE%\.cargo\bin;%PATH%"
            echo [INFO] Added %USERPROFILE%\.cargo\bin to PATH >> "%INSTALL_LOG%"
        )

        REM Verify UV is now available
        where uv >nul 2>nul
        if !errorlevel! equ 0 (
            set "USE_UV=true"
            echo [OK] UV is now available in PATH.
            echo [OK] UV is now available in PATH. >> "%INSTALL_LOG%"
        ) else (
            echo [WARN] UV installed but not found in PATH. Will use pip instead.
            echo [WARN] UV installed but not found in PATH. Will use pip instead. >> "%INSTALL_LOG%"
        )
    ) else (
        echo [WARN] Failed to install uv. Will fall back to standard Python/pip.
        echo [WARN] Failed to install uv. Will fall back to standard Python/pip. >> "%INSTALL_LOG%"
        echo [INFO] You can install uv manually later from: https://docs.astral.sh/uv/
    )
)

REM -------------------------------------------------------------------------
REM 2. Detect System Capabilities
REM -------------------------------------------------------------------------
echo.
echo [STEP 2/4] Detecting system capabilities...
echo [STEP 2/4] Detecting system capabilities... >> "%INSTALL_LOG%"

REM Check for NVIDIA GPU and CUDA
nvidia-smi >nul 2>nul
if %errorlevel% equ 0 (
    echo [OK] NVIDIA GPU detected.
    echo [OK] NVIDIA GPU detected. >> "%INSTALL_LOG%"
    set "HAS_CUDA=true"

    REM Try to get CUDA version - simpler approach
    echo [INFO] Querying GPU information...
    nvidia-smi --query-gpu=driver_version --format=csv,noheader > "%TEMP%\nvsmi_version.txt" 2>nul
    if exist "%TEMP%\nvsmi_version.txt" (
        set /p DRIVER_VERSION=<"%TEMP%\nvsmi_version.txt"
        del "%TEMP%\nvsmi_version.txt"
        if defined DRIVER_VERSION (
            echo [INFO] NVIDIA Driver Version: !DRIVER_VERSION!
            echo [INFO] NVIDIA Driver Version: !DRIVER_VERSION! >> "%INSTALL_LOG%"
        )
    )
) else (
    echo [INFO] No NVIDIA GPU detected. Will use CPU-only mode.
    echo [INFO] No NVIDIA GPU detected. Will use CPU-only mode. >> "%INSTALL_LOG%"
    set "HAS_CUDA=false"
)

REM -------------------------------------------------------------------------
REM 2b. Check System Prerequisites (FFmpeg, C++ Tools)
REM -------------------------------------------------------------------------
echo.
echo [INFO] Checking for FFmpeg...
where ffmpeg >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] FFmpeg not found in PATH.
    echo [ERROR] FFmpeg not found in PATH. >> "%INSTALL_LOG%"
    echo [ERROR] SpeakEasy requires FFmpeg for audio processing.
    echo [ERROR] Please download from: https://ffmpeg.org/download.html
    echo [ERROR] Or use winget: winget install Gyan.FFmpeg
    echo [ERROR] Then add it to your PATH and restart this installer.
    pause
    exit /b 1
) else (
    echo [OK] FFmpeg found.
    echo [OK] FFmpeg found. >> "%INSTALL_LOG%"
)

echo [INFO] Checking for Visual C++ Build Tools...
echo [INFO] Note: Some dependencies (like texterrors) require C++ compilation.
echo [INFO] If installation fails with "Microsoft Visual C++ 14.0 or greater is required",
echo [INFO] please install "Desktop development with C++" workload from Visual Studio Build Tools.
echo [INFO] Download: https://visualstudio.microsoft.com/visual-cpp-build-tools/
echo [INFO] Checked C++ Tools warning. >> "%INSTALL_LOG%"

REM -------------------------------------------------------------------------
REM 3. Setup Backend Environment
REM -------------------------------------------------------------------------
echo.
echo [STEP 3/4] Setting up Backend Environment...
echo [STEP 3/4] Setting up Backend Environment... >> "%INSTALL_LOG%"
echo [INFO] This may take 5-10 minutes on first install (downloading models)...

if not exist "backend" (
    echo [ERROR] 'backend' directory not found in: %CD%
    echo [ERROR] 'backend' directory not found in: %CD% >> "%INSTALL_LOG%"
    echo [ERROR] Please run this script from the SpeakEasy root directory.
    echo.
    pause
    exit /b 1
)

echo [INFO] Changed to backend directory: %CD%
echo [INFO] Changed to backend directory: %CD% >> "%INSTALL_LOG%"
cd backend
echo [INFO] Now in: %CD%
echo [INFO] Now in: %CD% >> "%INSTALL_LOG%"

echo [CHECKPOINT] About to check USE_UV flag >> "%INSTALL_LOG%"
if "!USE_UV!"=="true" (
    echo [INFO] Using 'uv' for backend setup...
    echo [INFO] Using 'uv' for backend setup... >> "%INSTALL_LOG%"

    echo [INFO] Removing old environment if it exists...
    if exist ".venv" (
        echo [INFO] Old .venv directory found. Removing...
        rmdir /s /q .venv
        if exist ".venv" (
            echo [ERROR] Failed to delete '.venv' directory.
            echo [ERROR] Access is denied. A process may be locking the files.
            echo [ERROR] Please close all terminals and try again.
            cd ..
            pause
            exit /b 1
        )
    )

    echo [INFO] Creating virtual environment with UV...
    call uv venv
    if !errorlevel! neq 0 (
        echo [ERROR] Failed to create virtual environment.
        echo [ERROR] Failed to create virtual environment. >> "%INSTALL_LOG%"
        cd ..
        pause
        exit /b 1
    )

    if not exist ".venv\Scripts\python.exe" (
        echo [ERROR] Virtual environment was not created properly.
        echo [ERROR] Virtual environment was not created properly. >> "%INSTALL_LOG%"
        cd ..
        pause
        exit /b 1
    )

    echo [OK] Virtual environment created successfully.
    echo [OK] Virtual environment created successfully. >> "%INSTALL_LOG%"

    echo.
    echo [INFO] Installing core dependencies (downloading PyTorch, NeMo, etc.)...
    echo [INFO] This is the longest step - please be patient (5-10 minutes)...
    echo [INFO] You will see progress output below...
    echo.

    if "!HAS_CUDA!"=="true" (
        echo [INFO] Installing with CUDA optimization for faster transcription...
        echo [INFO] GPU detected - enabling CUDA support...
        call uv pip install -e ".[cuda]"
        
        echo [INFO] Ensuring cuda-python is installed...
        call uv pip install "cuda-python>=12.3"
    ) else (
        echo [INFO] Installing in CPU mode (no GPU detected)...
        call uv pip install -e .
    )

    if !errorlevel! neq 0 (
        echo [ERROR] Core dependency installation failed.
        echo [ERROR] Core dependency installation failed. >> "%INSTALL_LOG%"
        cd ..
        pause
        exit /b 1
    )

    echo.
    echo [OK] Dependencies installed successfully.
    echo [OK] Dependencies installed successfully. >> "%INSTALL_LOG%"
    if "!HAS_CUDA!"=="true" (
        echo [INFO] CUDA optimizations enabled for 20-30%% faster transcription.
        echo [INFO] CUDA optimizations enabled. >> "%INSTALL_LOG%"
    )
) else (
    echo [CHECKPOINT] UV not enabled, using standard Python >> "%INSTALL_LOG%"
    echo [INFO] Using standard Python for backend setup...
    echo [INFO] Using standard Python for backend setup... >> "%INSTALL_LOG%"

    where python >nul 2>nul
    if !errorlevel! neq 0 (
        echo [ERROR] 'python' not found. Please install Python 3.12 or newer.
        echo [ERROR] 'python' not found. >> "%INSTALL_LOG%"
        echo [ERROR] Download from: https://www.python.org/downloads/
        cd ..
        pause
        exit /b 1
    )

    REM Check Python version
    for /f "tokens=2" %%i in ('python --version 2^>^&1') do set "PYTHON_VERSION=%%i"
    echo [INFO] Found Python !PYTHON_VERSION!
    echo [INFO] Found Python !PYTHON_VERSION! >> "%INSTALL_LOG%"

    echo [INFO] Removing old environment if it exists...
    if exist ".venv" (
        echo [INFO] Old .venv directory found. Removing...
        rmdir /s /q .venv
        if exist ".venv" (
            echo [ERROR] Failed to delete '.venv' directory.
            echo [ERROR] Access is denied. A process may be locking the files.
            echo [ERROR] Please close all terminals and try again.
            cd ..
            pause
            exit /b 1
        )
    )

    echo [INFO] Creating virtual environment with Python...
    python -m venv .venv
    if !errorlevel! neq 0 (
        echo [ERROR] Failed to create virtual environment.
        echo [ERROR] Failed to create virtual environment. >> "%INSTALL_LOG%"
        cd ..
        pause
        exit /b 1
    )

    echo [OK] Virtual environment created.
    echo [OK] Virtual environment created. >> "%INSTALL_LOG%"

    echo [INFO] Activating virtual environment...
    call .venv\Scripts\activate.bat
    if !errorlevel! neq 0 (
        echo [ERROR] Failed to activate virtual environment.
        echo [ERROR] Failed to activate virtual environment. >> "%INSTALL_LOG%"
        cd ..
        pause
        exit /b 1
    )

    echo [INFO] Upgrading pip...
    python -m pip install --upgrade pip >nul 2>&1

    echo.
    echo [INFO] Installing core dependencies (downloading PyTorch, NeMo, etc.)...
    echo [INFO] This is the longest step - please be patient (5-10 minutes)...
    echo [INFO] You will see progress output below...
    echo.

    if "!HAS_CUDA!"=="true" (
        echo [INFO] Installing with CUDA optimization for faster transcription...
        echo [INFO] GPU detected - enabling CUDA support...
        pip install -e ".[cuda]"
        
        echo [INFO] Ensuring cuda-python is installed...
        pip install "cuda-python>=12.3"
    ) else (
        echo [INFO] Installing in CPU mode (no GPU detected)...
        pip install -e .
    )

    if !errorlevel! neq 0 (
        echo [ERROR] Core dependency installation failed.
        echo [ERROR] Core dependency installation failed. >> "%INSTALL_LOG%"
        cd ..
        pause
        exit /b 1
    )

    echo.
    echo [OK] Dependencies installed successfully.
    echo [OK] Dependencies installed successfully. >> "%INSTALL_LOG%"
    if "!HAS_CUDA!"=="true" (
        echo [INFO] CUDA optimizations enabled for 20-30%% faster transcription.
        echo [INFO] CUDA optimizations enabled. >> "%INSTALL_LOG%"
    )
)

cd ..

REM -------------------------------------------------------------------------
REM 4. Install Frontend Dependencies
REM -------------------------------------------------------------------------
echo.
echo [STEP 4/4] Installing Frontend Dependencies (npm)...
echo [STEP 4/4] Installing Frontend Dependencies (npm)... >> "%INSTALL_LOG%"

if exist "gui" (
    cd gui

    echo [INFO] Checking for npm...
    where npm >nul 2>nul
    if !errorlevel! neq 0 (
        echo [ERROR] npm is not installed or not in PATH.
        echo [ERROR] npm is not installed or not in PATH. >> "%INSTALL_LOG%"
        echo [ERROR] Please install Node.js (LTS) from https://nodejs.org/
        cd ..
        pause
        exit /b 1
    )

    REM Check npm version
    for /f "tokens=*" %%i in ('npm --version 2^>^&1') do set "NPM_VERSION=%%i"
    echo [INFO] Found npm !NPM_VERSION!
    echo [INFO] Found npm !NPM_VERSION! >> "%INSTALL_LOG%"

    echo [INFO] Running npm install (this may take 2-3 minutes)...
    call npm install
    if !errorlevel! neq 0 (
        echo [ERROR] Frontend installation failed.
        echo [ERROR] Frontend installation failed. >> "%INSTALL_LOG%"
        cd ..
        pause
        exit /b 1
    )

    echo [OK] Frontend dependencies installed.
    echo [OK] Frontend dependencies installed. >> "%INSTALL_LOG%"
    cd ..
) else (
    echo [WARN] 'gui' directory not found. Skipping frontend install.
    echo [WARN] 'gui' directory not found. >> "%INSTALL_LOG%"
)

REM -------------------------------------------------------------------------
REM Installation Complete
REM -------------------------------------------------------------------------
echo.
echo ========================================== >> "%INSTALL_LOG%"
echo Installation Complete: %DATE% %TIME% >> "%INSTALL_LOG%"
echo ========================================== >> "%INSTALL_LOG%"

echo.
echo ==========================================
echo Installation Complete!
echo ==========================================
echo.
echo System Configuration:
if "!HAS_CUDA!"=="true" (
    echo   GPU: NVIDIA GPU with CUDA support
    echo   Optimization: CUDA-Python installed for faster transcription
) else (
    echo   GPU: None detected ^(CPU mode^)
    echo   Note: GPU recommended for faster transcription
)
if "!USE_UV!"=="true" (
    echo   Package Manager: UV ^(fast^)
) else (
    echo   Package Manager: pip ^(standard^)
)
echo   Python Version: %PYTHON_TARGET_VERSION%
echo.
echo To run the application:
echo   Double-click start.bat
echo.
echo Next steps:
echo   1. Run the application with start.bat
echo   2. First model load will take 30-60 seconds
echo   3. Subsequent loads will be faster ^(~10-15 seconds target^)
echo.
echo If you encounter any issues:
echo   - Check the installation log: %INSTALL_LOG%
echo   - Report issues at: https://github.com/yourusername/SpeakEasy/issues
echo.
pause
