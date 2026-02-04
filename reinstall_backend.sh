#!/bin/bash

# SpeakEasy Backend Reinstaller (for CUDA fix)

echo "=========================================="
echo "SpeakEasy Backend Reinstall"
echo "=========================================="

if [ -d "backend" ]; then
    cd backend
    
    echo "[INFO] Removing old lock file..."
    rm -f uv.lock
    
    echo "[INFO] Removing old environment..."
    rm -rf .venv
    
    # Check if uv is installed
    if command -v uv &> /dev/null; then
        echo "[INFO] Using 'uv' to reinstall with CUDA support..."
        uv venv
        uv pip install -e .
    else
        echo "[WARN] 'uv' not found! Falling back to pip."
        echo "[INFO] Note: Pip might install CPU version unless --index-url is used manually."
        python3 -m venv .venv
        source .venv/bin/activate
        pip install -e . --extra-index-url https://download.pytorch.org/whl/cu124
    fi
    
    cd ..
    echo "[SUCCESS] Backend reinstalled."
else
    echo "[ERROR] 'backend' directory not found."
fi
