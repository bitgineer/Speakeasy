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
echo "[STEP 1/4] Checking for 'uv' package manager..."
if ! command -v uv &> /dev/null; then
    echo "[INFO] 'uv' not found. Installing..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    
    # Source the cargo env to get uv in path immediately if possible
    if [ -f "$HOME/.cargo/env" ]; then
        . "$HOME/.cargo/env"
    else
        # Fallback for path
        export PATH="$HOME/.cargo/bin:$PATH"
    fi
else
    echo "[OK] 'uv' found."
fi

# -------------------------------------------------------------------------
# 2. Install Python
# -------------------------------------------------------------------------
echo ""
echo "[STEP 2/4] Ensuring Python $PYTHON_VERSION is installed..."
uv python install $PYTHON_VERSION
echo "[OK] Python $PYTHON_VERSION is ready."

# -------------------------------------------------------------------------
# 3. Setup Backend Environment
# -------------------------------------------------------------------------
echo ""
echo "[STEP 3/4] Setting up Backend Virtual Environment..."

if [ ! -d "backend" ]; then
    echo "[ERROR] 'backend' directory not found in: $(pwd)"
    exit 1
fi

cd backend

echo "[INFO] Creating venv..."
# Using the version specified in .python-version or variable
uv venv --python $PYTHON_VERSION --allow-existing

# -------------------------------------------------------------------------
# 4. Install Dependencies
# -------------------------------------------------------------------------
echo ""
echo "[STEP 4/4] Installing dependencies..."
echo "[INFO] This might take a few minutes..."

uv pip install -e .

cd ..

# -------------------------------------------------------------------------
# 5. Install Frontend Dependencies
# -------------------------------------------------------------------------
echo ""
echo "[STEP 5/5] Installing Frontend Dependencies (npm)..."
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
