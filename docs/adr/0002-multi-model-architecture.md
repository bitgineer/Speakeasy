# ADR-0002: Multi-Model ASR Architecture

**Status:** Accepted

**Date:** 2026-01-20

**Decision Makers:** Project maintainers

**Related:** N/A

---

## Context

The application needs to support multiple Automatic Speech Recognition (ASR) models with different characteristics:
- **faster-whisper:** Efficient Whisper implementation, good general-purpose transcription
- **NVIDIA NeMo (Parakeet, Canary):** State-of-the-art models with punctuation and capitalization
- **Voxtral:** Open-weight model from Fixie AI

Each model has different dependencies, APIs, and performance characteristics. The architecture needs to accommodate this diversity without becoming unmaintainable.

## Decision

Implement a **wrapper-based model architecture** with:
1. A base model interface/protocol
2. Model-specific wrapper implementations
3. Lazy loading of heavy dependencies
4. Configuration-driven model selection
5. Model-specific settings (quantization, device, etc.)

## Options Considered

### Option 1: Single model support
- **Description:** Support only faster-whisper
- **Pros:**
  - Simpler implementation
  - Lower dependency footprint
  - Easier to maintain
- **Cons:**
  - Limited to Whisper's capabilities
  - Users cannot choose best model for their use case
  - Missing out on newer/better models

### Option 2: Separate code paths for each model
- **Description:** Implement each model independently in the main code
- **Pros:**
  - Maximum flexibility per model
  - No abstraction overhead
- **Cons:**
  - Massive code duplication
  - Difficult to maintain
  - Adding new models requires touching many files

### Option 3: Wrapper-based architecture (Selected)
- **Description:** Abstract model interface with model-specific wrapper implementations
- **Pros:**
  - Clean separation of concerns
  - Easy to add new models
  - Consistent API across models
  - Model-specific optimizations isolated
- **Cons:**
  - More complex initial design
  - Need to maintain interface compatibility

## Rationale

Option 3 was selected because:
1. **Extensibility:** Adding a new ASR model only requires creating a new wrapper
2. **Maintainability:** Each model's quirks are isolated in its wrapper
3. **Consistency:** All models expose the same interface to the rest of the application
4. **Performance:** Lazy loading ensures only selected model's dependencies are loaded
5. **User Choice:** Users can select the best model for their hardware and use case

The wrapper pattern in `models.py` abstracts differences between:
- faster-whisper (CTranslate2-based)
- NeMo models (PyTorch-based, require nemo_toolkit)
- Transformers-based models (Hugging Face)

## Consequences

- **Positive:**
  - Easy to add new ASR models
  - Consistent behavior regardless of model
  - Model-specific settings handled cleanly
  - Lazy loading reduces startup time

- **Negative:**
  - Need to maintain interface compatibility
  - Some models' advanced features may be hidden behind abstraction
  - Testing burden increases with each model

- **Risk Mitigation:**
  - Well-defined model interface
  - Model-specific tests
  - Documentation for each model's capabilities

## Implementation

- [x] Define model interface in `models.py`
- [x] Implement WhisperModel wrapper
- [x] Implement ParakeetModel wrapper
- [x] Implement CanaryModel wrapper
- [x] Implement VoxtralModel wrapper
- [x] Lazy loading of heavy dependencies (torch, nemo_toolkit, transformers)
- [x] Model configuration in `config.py`
- [x] Model selection in settings

## References

- `src/faster_whisper_hotkey/models.py` - Model wrapper implementations
- `src/faster_whisper_hotkey/config.py` - Model definitions and configurations
