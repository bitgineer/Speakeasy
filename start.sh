#!/bin/bash

# SpeakEasy Startup Script for Linux/macOS

echo "=========================================="
echo "SpeakEasy Startup Script"
echo "=========================================="

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
