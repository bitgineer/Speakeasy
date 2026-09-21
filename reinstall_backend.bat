@echo off
setlocal EnableDelayedExpansion

echo ==========================================
echo SpeakEasy Backend Reinstall
echo ==========================================
echo.

cd /d "%~dp0"

echo [INFO] Detecting system capabilities...
set "HAS_CUDA=false"

REM Check for NVIDIA GPU and CUDA
nvidia-smi >nul 2>nul
if %errorlevel% equ 0 (
    echo [OK] NVIDIA GPU detected.
    set "HAS_CUDA=true"

    REM Get driver version
    nvidia-smi --query-gpu=driver_version --format=csv,noheader > "%TEMP%\nvsmi_version.txt" 2>nul
    if exist "%TEMP%\nvsmi_version.txt" (
        set /p DRIVER_VERSION=<"%TEMP%\nvsmi_version.txt"
        del "%TEMP%\nvsmi_version.txt" 2>nul
        if defined DRIVER_VERSION (
            echo [INFO] NVIDIA Driver Version: !DRIVER_VERSION!
        )
    )
) else (
    echo [INFO] No NVIDIA GPU detected. Will use CPU-only mode.
)

echo.
echo [INFO] Attempting to close lingering processes...
taskkill /F /IM uvicorn.exe >nul 2>&1
taskkill /F /IM python.exe >nul 2>&1

timeout /t 2 >nul

if exist "backend" (
    cd backend

    echo [INFO] Removing old lock file...
    if exist "uv.lock" del "uv.lock" 2>nul

    echo [INFO] Removing old environment...
    if exist ".venv" (
        rmdir /s /q ".venv"
        if exist ".venv" (
            echo.
            echo [ERROR] Failed to delete '.venv' directory.
            echo [ERROR] Access is denied. A process is still locking the files.
            echo [ERROR] Please manually close all Command Prompts, VS Code terminals,
            echo [ERROR] and ensure no 'python.exe' is running in Task Manager.
            echo.
            pause
            exit /b 1
        )
    )

    REM Check for uv
    where uv >nul 2>nul
    if !errorlevel! equ 0 (
        echo [INFO] Using 'uv' to reinstall...
        echo.
        call uv venv
        if !errorlevel! neq 0 (
            echo [ERROR] Failed to create virtual environment.
            pause
            exit /b 1
        )

        REM Install dependencies
        echo [INFO] Installing dependencies...
        if "!HAS_CUDA!"=="true" (
            echo [INFO] GPU detected - enabling CUDA optimization...
            call uv pip install -e ".[cuda]"
        ) else (
            echo [INFO] Installing in CPU mode...
            call uv pip install -e .
        )

        if !errorlevel! neq 0 (
            echo [ERROR] Failed to install dependencies.
            pause
            exit /b 1
        )

        if "!HAS_CUDA!"=="true" (
            echo.
            echo [OK] CUDA optimizations enabled for 20-30%% faster transcription.
        )
    ) else (
        echo [WARN] 'uv' not found! Falling back to pip.
        python -m venv .venv
        if !errorlevel! neq 0 (
            echo [ERROR] Failed to create virtual environment.
            pause
            exit /b 1
        )

        call .venv\Scripts\activate.bat

        echo [INFO] Installing dependencies...
        if "!HAS_CUDA!"=="true" (
            echo [INFO] GPU detected - enabling CUDA optimization...
            pip install -e ".[cuda]"
        ) else (
            echo [INFO] Installing in CPU mode...
            pip install -e .
        )

        if !errorlevel! neq 0 (
            echo [ERROR] Failed to install dependencies.
            pause
            exit /b 1
        )

        if "!HAS_CUDA!"=="true" (
            echo.
            echo [OK] CUDA optimizations enabled for 20-30%% faster transcription.
        )
    )

    cd ..

    echo.
    echo ==========================================
    echo [SUCCESS] Backend reinstalled!
    echo ==========================================
    echo.
    if "!HAS_CUDA!"=="true" (
        echo GPU: NVIDIA GPU with CUDA support
        echo Optimization: CUDA enabled for faster transcription
    ) else (
        echo GPU: None detected ^(CPU mode^)
    )
) else (
    echo [ERROR] 'backend' directory not found in current location.
    echo [INFO] Current directory: %CD%
)

echo.
pause
