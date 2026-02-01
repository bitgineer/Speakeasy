#!/bin/bash

# SpeakEasy Startup Script for Linux/macOS

echo "=========================================="
echo "SpeakEasy Startup Script"
echo "=========================================="

# Trap to kill background processes on exit
trap 'kill 0' SIGINT

# -------------------------------------------------------------------------
# 1. Start Backend
# -------------------------------------------------------------------------
echo "[INFO] Starting Backend Server..."
if [ -d "backend" ]; then
    cd backend
    uv run uvicorn speakeasy.main:app --reload &
    BACKEND_PID=$!
    cd ..
else
    echo "[ERROR] 'backend' directory not found!"
    exit 1
fi

# -------------------------------------------------------------------------
# 2. Start Frontend
# -------------------------------------------------------------------------
echo "[INFO] Starting Frontend (GUI)..."
if [ -d "gui" ]; then
    cd gui
    
    # Check node_modules
    if [ ! -d "node_modules" ]; then
        echo "[WARN] node_modules not found in gui. Running npm install..."
        npm install
    fi
    
    npm run dev &
    FRONTEND_PID=$!
    cd ..
else
    echo "[ERROR] 'gui' directory not found!"
    kill $BACKEND_PID
    exit 1
fi

echo ""
echo "[SUCCESS] Services launched."
echo "Press Ctrl+C to stop all services."

wait
