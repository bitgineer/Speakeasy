#!/bin/bash

# SpeakEasy Installer for Linux/macOS

set -e

PYTHON_VERSION="3.12"

echo "=========================================="
echo "SpeakEasy Installer"
echo "=========================================="
echo ""

# -------------------------------------------------------------------------
# 1. Check/Install UV
# -------------------------------------------------------------------------
echo "[STEP 1/3] Checking for 'uv' package manager..."

USE_UV=false

if command -v uv &> /dev/null; then
    echo "[OK] 'uv' found."
    USE_UV=true
else
    echo "[INFO] 'uv' not found. Attempting to install..."
    if curl -LsSf https://astral.sh/uv/install.sh | sh; then
        echo "[OK] 'uv' installed."
        # Source the cargo env to get uv in path immediately
        if [ -f "$HOME/.cargo/env" ]; then
            . "$HOME/.cargo/env"
        else
            export PATH="$HOME/.cargo/bin:$PATH"
        fi
        USE_UV=true
    else
        echo "[WARN] Failed to install 'uv'. Will fall back to standard Python/pip."
    fi
fi

# -------------------------------------------------------------------------
# 2. Setup Backend (UV or Fallback)
# -------------------------------------------------------------------------
echo ""
echo "[STEP 2/3] Setting up Backend Environment..."

if [ ! -d "backend" ]; then
    echo "[ERROR] 'backend' directory not found in: $(pwd)"
    exit 1
fi

cd backend

if [ "$USE_UV" = true ]; then
    echo "[INFO] Using 'uv' for backend setup..."
    
    # Install Python via uv
    echo "[INFO] Ensuring Python $PYTHON_VERSION..."
    uv python install $PYTHON_VERSION
    
    # Create venv
    echo "[INFO] Creating venv..."
    uv venv --python $PYTHON_VERSION --allow-existing
    
    # Install dependencies
    echo "[INFO] Installing dependencies..."
    echo "[INFO] This might take a few minutes..."
    uv pip install -e .
else
    echo "[INFO] Using standard Python for backend setup..."
    
    # Check for python3
    if ! command -v python3 &> /dev/null; then
        echo "[ERROR] 'python3' is required but not found."
        exit 1
    fi
    
    # Create venv
    echo "[INFO] Creating venv with python3..."
    python3 -m venv .venv
    
    # Activate and install
    echo "[INFO] Activating venv and installing dependencies..."
    # We must activate in the current shell to use pip
    . .venv/bin/activate
    pip install -e .
fi

cd ..

# -------------------------------------------------------------------------
# 3. Install Frontend Dependencies
# -------------------------------------------------------------------------
echo ""
echo "[STEP 3/3] Installing Frontend Dependencies (npm)..."
if [ -d "gui" ]; then
    cd gui
    
    echo "[INFO] Checking for npm..."
    if ! command -v npm &> /dev/null; then
        echo "[ERROR] npm is not installed."
        echo "[INFO] Please install Node.js (LTS) from https://nodejs.org/"
        exit 1
    fi

    echo "[INFO] Running npm install..."
    npm install
    cd ..
else
    echo "[WARN] 'gui' directory not found. Skipping frontend install."
fi

echo ""
echo "=========================================="
echo "Installation Complete!"
echo "=========================================="
echo ""
echo "To run the application:"
echo "  ./start.sh"
echo ""
