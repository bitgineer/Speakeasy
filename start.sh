#!/bin/bash

# SpeakEasy Startup Script for Linux/macOS

set -e

echo "=========================================="
echo "SpeakEasy Startup Script"
echo "=========================================="

# -------------------------------------------------------------------------
# Pre-flight Checks
# -------------------------------------------------------------------------
echo "[CHECK] Verifying environment..."

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python 3 is not installed."
    echo "[INFO] Please install Python 3.10-3.12 from https://python.org"
    exit 1
fi

# Check Node.js
if ! command -v node &> /dev/null; then
    echo "[ERROR] Node.js is not installed."
    echo "[INFO] Please install Node.js 18+ from https://nodejs.org"
    exit 1
fi

# Check FFmpeg (optional)
if ! command -v ffmpeg &> /dev/null; then
    echo "[WARN] FFmpeg not found. Audio file transcription will not work."
    echo "[INFO] Install with: brew install ffmpeg (macOS) or apt-get install ffmpeg (Linux)"
    sleep 3
fi

# Check UV
if ! command -v uv &> /dev/null; then
    echo "[INFO] Installing UV package manager..."
    pip3 install uv
fi

# -------------------------------------------------------------------------
# Setup Backend if needed
# -------------------------------------------------------------------------
if [ -d "backend" ]; then
    cd backend
    
    # Check virtual environment - must exist AND be valid
    VENV_VALID=false
    if [ -d ".venv" ] && [ -f ".venv/pyvenv.cfg" ] && [ -f ".venv/bin/python" ]; then
        VENV_VALID=true
    fi
    
    if [ "$VENV_VALID" = false ]; then
        echo "[INFO] Creating Python virtual environment..."
        if [ -d ".venv" ]; then
            echo "[INFO] Removing broken virtual environment..."
            rm -rf .venv
        fi
        uv venv --python 3.12 2>/dev/null || uv venv --python 3.11 2>/dev/null || uv venv --python 3.10
        if [ $? -ne 0 ]; then
            echo "[ERROR] Failed to create virtual environment."
            exit 1
        fi
    fi
    
    # Use venv Python directly (no need to activate)
    VENV_PYTHON=".venv/bin/python"
    
    # Check if dependencies are installed using comprehensive check
    if ! "$VENV_PYTHON" check_deps.py 2>/dev/null; then
        echo "[INFO] Installing backend dependencies..."
        "$VENV_PYTHON" -m pip install -e ".[cuda]" 2>/dev/null || "$VENV_PYTHON" -m pip install -e .
        
        # Re-check after install
        if ! "$VENV_PYTHON" check_deps.py 2>/dev/null; then
            echo "[ERROR] Failed to install all dependencies."
            echo "[INFO] Please run reinstall_backend.sh to repair the installation."
            exit 1
        fi
    fi
    
    cd ..
fi

# Ensure we are in the script directory
cd "$(dirname "$0")"

# -------------------------------------------------------------------------
# 1. Start Frontend (which handles Backend)
# -------------------------------------------------------------------------
echo "[INFO] Starting Application..."

if [ -d "gui" ]; then
    cd gui
    
    # Check node_modules
    if [ ! -d "node_modules" ]; then
        echo "[WARN] node_modules not found in gui. Running npm install..."
        npm install
    fi
    
    echo "[INFO] Starting Electron App..."
    npm run dev
    cd ..
else
    echo "[ERROR] 'gui' directory not found!"
    exit 1
fi

echo ""
echo "[SUCCESS] Application exited."
