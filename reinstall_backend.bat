@echo off
setlocal EnableDelayedExpansion

echo ==========================================
echo SpeakEasy Backend Reinstall
echo ==========================================

echo [INFO] Attempting to close lingering processes...
taskkill /F /IM uvicorn.exe >nul 2>&1
taskkill /F /IM python.exe >nul 2>&1

timeout /t 2 >nul

if exist "backend" (
    cd backend
    
    echo [INFO] Removing old lock file...
    if exist "uv.lock" del "uv.lock"
    
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
        echo [INFO] Using 'uv' to reinstall with CUDA support...
        call uv venv
        call uv pip install -e .
    ) else (
        echo [WARN] 'uv' not found! Falling back to pip.
        python -m venv .venv
        call .venv\Scripts\activate.bat
        pip install -e . --extra-index-url https://download.pytorch.org/whl/cu124
    )
    
    cd ..
    echo [SUCCESS] Backend reinstalled.
) else (
    echo [ERROR] 'backend' directory not found.
)

pause
