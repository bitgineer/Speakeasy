#!/bin/bash

# =========================================================================
# SpeakEasy Installer for Linux/macOS
# =========================================================================
# This script:
# - Detects system capabilities (CUDA, GPU)
# - Installs UV package manager (preferred) or falls back to pip
# - Installs Python dependencies with platform-specific optimizations
# - Sets up frontend dependencies
# =========================================================================

set -e

PYTHON_VERSION="3.12"
CUDA_PYTHON_VERSION="12.3"
USE_UV=false
HAS_CUDA=false

echo "=========================================="
echo "SpeakEasy Installer"
echo "=========================================="
echo ""

# -------------------------------------------------------------------------
# 1. Check/Install UV
# -------------------------------------------------------------------------
echo "[STEP 1/3] Checking for 'uv' package manager..."

if command -v uv &> /dev/null; then
    echo "[OK] 'uv' found."
    USE_UV=true
else
    echo "[INFO] 'uv' not found. Attempting to install..."
    echo "[INFO] UV is faster than pip and recommended for best experience."
    if curl -LsSf https://astral.sh/uv/install.sh | sh; then
        echo "[OK] 'uv' installed successfully."
        # Source the cargo env to get uv in path immediately
        if [ -f "$HOME/.cargo/env" ]; then
            . "$HOME/.cargo/env"
        else
            export PATH="$HOME/.cargo/bin:$PATH"
        fi
        USE_UV=true
    else
        echo "[WARN] Failed to install 'uv'. Will fall back to standard Python/pip."
        echo "[INFO] You can install uv manually later from: https://docs.astral.sh/uv/"
    fi
fi

# -------------------------------------------------------------------------
# 1.5. Detect System Capabilities
# -------------------------------------------------------------------------
echo ""
echo "[INFO] Detecting system capabilities..."

# Check for NVIDIA GPU and CUDA
if command -v nvidia-smi &> /dev/null; then
    echo "[OK] NVIDIA GPU detected."
    HAS_CUDA=true

    # Try to get GPU info
    GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | head -n 1)
    if [ -n "$GPU_NAME" ]; then
        echo "[INFO] GPU: $GPU_NAME"
    fi

    # Try to get CUDA version
    CUDA_VERSION=$(nvidia-smi --query-gpu=driver_version --format=csv,noheader 2>/dev/null | head -n 1)
    if [ -n "$CUDA_VERSION" ]; then
        echo "[INFO] NVIDIA Driver Version: $CUDA_VERSION"
    fi
else
    echo "[INFO] No NVIDIA GPU detected. Will use CPU-only mode."
    HAS_CUDA=false
fi

# Detect OS
OS_TYPE=$(uname -s)
echo "[INFO] Operating System: $OS_TYPE"

# -------------------------------------------------------------------------
# 1.6. Check System Prerequisites
# -------------------------------------------------------------------------
echo ""
echo "[INFO] Checking System Prerequisites..."

if ! command -v ffmpeg &> /dev/null; then
    echo "[ERROR] FFmpeg not found in PATH."
    echo "[ERROR] SpeakEasy requires FFmpeg for audio processing."
    if [ "$OS_TYPE" = "Linux" ]; then
        echo "[INFO] Install with: sudo apt install ffmpeg (Debian/Ubuntu) or sudo pacman -S ffmpeg (Arch)"
    elif [ "$OS_TYPE" = "Darwin" ]; then
        echo "[INFO] Install with: brew install ffmpeg"
    fi
    exit 1
else
    echo "[OK] FFmpeg found."
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

    # Install core dependencies
    echo "[INFO] Installing core dependencies..."
    echo "[INFO] This may take 5-10 minutes on first install..."
    uv pip install --python .venv/bin/python -e .

    if [ $? -ne 0 ]; then
        echo "[ERROR] Core dependency installation failed."
        cd ..
        exit 1
    fi

    # Explicitly ensure critical backend dependencies are installed
    echo ""
    echo "[INFO] Ensuring critical backend dependencies are installed..."
    uv pip install --python .venv/bin/python "fastapi>=0.109.0" "uvicorn[standard]>=0.27.0" "websockets>=12.0" "slowapi>=0.1.9"
    if [ $? -ne 0 ]; then
        echo "[ERROR] Failed to install critical backend dependencies."
        cd ..
        exit 1
    fi

    # Verify FastAPI installation
    echo ""
    echo "[INFO] Verifying FastAPI installation..."
    .venv/bin/python -c "import fastapi; print('FastAPI version:', fastapi.__version__)"
    if [ $? -ne 0 ]; then
        echo "[ERROR] FastAPI was not installed correctly."
        echo "[ERROR] This is a critical dependency for the web server."
        cd ..
        exit 1
    fi
    echo "[OK] FastAPI verified successfully."

    # Install CUDA-specific optimizations if GPU detected
    if [ "$HAS_CUDA" = true ]; then
        echo ""
        echo "[INFO] Installing CUDA optimizations for faster transcription..."
        echo "[INFO] Installing cuda-python>=$CUDA_PYTHON_VERSION..."
        uv pip install "cuda-python>=$CUDA_PYTHON_VERSION"

        if [ $? -eq 0 ]; then
            echo "[OK] CUDA-Python installed successfully."
            echo "[INFO] This enables CUDA graph optimizations for 20-30% faster transcription."
        else
            echo "[WARN] Failed to install cuda-python. Transcription will still work but may be slower."
        fi
    else
        echo "[INFO] Skipping CUDA optimizations (no GPU detected)."
    fi

    # Install Linux-specific dependencies
    if [ "$OS_TYPE" = "Linux" ]; then
        echo ""
        echo "[INFO] Installing Linux-specific audio dependencies..."
        uv pip install "pulsectl>=23.5.0"
        if [ $? -eq 0 ]; then
            echo "[OK] PulseAudio control installed."
        fi
    fi
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
    echo "[INFO] This may take 5-10 minutes on first install..."
    # We must activate in the current shell to use pip
    . .venv/bin/activate
    pip install -e .

    if [ $? -ne 0 ]; then
        echo "[ERROR] Core dependency installation failed."
        cd ..
        exit 1
    fi

    # Explicitly ensure critical backend dependencies are installed
    echo ""
    echo "[INFO] Ensuring critical backend dependencies are installed..."
    pip install "fastapi>=0.109.0" "uvicorn[standard]>=0.27.0" "websockets>=12.0" "slowapi>=0.1.9"
    if [ $? -ne 0 ]; then
        echo "[ERROR] Failed to install critical backend dependencies."
        cd ..
        exit 1
    fi

    # Verify FastAPI installation
    echo ""
    echo "[INFO] Verifying FastAPI installation..."
    .venv/bin/python -c "import fastapi; print('FastAPI version:', fastapi.__version__)"
    if [ $? -ne 0 ]; then
        echo "[ERROR] FastAPI was not installed correctly."
        echo "[ERROR] This is a critical dependency for the web server."
        cd ..
        exit 1
    fi
    echo "[OK] FastAPI verified successfully."

    # Install CUDA-specific optimizations if GPU detected
    if [ "$HAS_CUDA" = true ]; then
        echo ""
        echo "[INFO] Installing CUDA optimizations for faster transcription..."
        echo "[INFO] Installing cuda-python>=$CUDA_PYTHON_VERSION..."
        pip install "cuda-python>=$CUDA_PYTHON_VERSION"

        if [ $? -eq 0 ]; then
            echo "[OK] CUDA-Python installed successfully."
            echo "[INFO] This enables CUDA graph optimizations for 20-30% faster transcription."
        else
            echo "[WARN] Failed to install cuda-python. Transcription will still work but may be slower."
        fi
    else
        echo "[INFO] Skipping CUDA optimizations (no GPU detected)."
    fi

    # Install Linux-specific dependencies
    if [ "$OS_TYPE" = "Linux" ]; then
        echo ""
        echo "[INFO] Installing Linux-specific audio dependencies..."
        pip install "pulsectl>=23.5.0"
        if [ $? -eq 0 ]; then
            echo "[OK] PulseAudio control installed."
        fi
    fi
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
echo "System Configuration:"
if [ "$HAS_CUDA" = true ]; then
    echo "  GPU: NVIDIA GPU with CUDA support"
    echo "  Optimization: CUDA-Python installed for faster transcription"
else
    echo "  GPU: None detected (CPU mode)"
    echo "  Note: GPU recommended for faster transcription"
fi
echo "  Package Manager: $([ "$USE_UV" = true ] && echo "uv" || echo "pip")"
echo "  Python Version: $PYTHON_VERSION"
echo "  OS: $OS_TYPE"
echo ""
echo "To run the application:"
echo "  ./start.sh"
echo ""
echo "Next steps:"
echo "  1. Run the application"
echo "  2. First model load will take 30-60 seconds"
echo "  3. Subsequent loads will be faster (~10-15 seconds target)"
echo ""
