# Core Services

This directory contains the core services for SpeakEasy transcription:

## Models (`models.py`)
Model wrapper and inference engine using CTranslate2/ONNX.
Supports:
- Whisper (faster-whisper)
- NVIDIA NeMo (parakeet, canary)
- Mistral Voxtral

Features:
- Lazy loading for fast startup
- Device management (CUDA/CPU)
- Download progress tracking
- Automatic GPU error detection and recovery

## Transcriber (`transcriber.py`)
Audio recording and transcription coordination.

Key features:
- Real-time audio recording with native sample rate support
- Model loading/unloading with state management
- Chunked transcription for long recordings (>5 min)
- Progress callbacks for real-time updates
- Device selection and management
- Automatic resampling when needed

State machine:
- IDLE: No model loaded
- LOADING: Model is being downloaded/loaded
- READY: Model loaded, ready to record
- RECORDING: Audio capture in progress
- TRANSCRIBING: Processing audio
- ERROR: Error occurred

## Config (`config.py`)
Model configuration and metadata.

Contains:
- Available models for each type (whisper, parakeet, canary, voxtral)
- Supported languages per model
- Compute types (float16, int8, etc.)
- Model VRAM requirements

## Text Cleanup (`text_cleanup.py`)
AI-powered text enhancement.

Features:
- Automatic filler word removal
- Custom filler word lists
- Grammar correction integration
- Preserves original text for comparison

## Grammar Processor (`grammar_processor.py`)
AI grammar correction using LLM instructions.

Features:
- Model selection (GPT-4, Claude, etc.)
- Custom instruction support
- Text comparison before/after
- Optional per-transcription or global setting
