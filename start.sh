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
    
    # Create venv if needed
    if [ ! -d ".venv" ]; then
        echo "[INFO] Creating Python virtual environment..."
        uv venv --python 3.12 2>/dev/null || uv venv --python 3.11 2>/dev/null || uv venv --python 3.10
    fi
    
    # Activate and check dependencies
    source .venv/bin/activate
    
    if ! python -c "import speakeasy" 2>/dev/null; then
        echo "[INFO] Installing backend dependencies..."
        uv pip install -e ".[cuda]" 2>/dev/null || uv pip install -e .
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
