import logging
import os
import gc
from typing import Optional

logger = logging.getLogger(__name__)

# Global state in worker process
_wrapper = None
_last_model_config = {}  # Store last loaded model config for potential reload


def init_worker():
    """Initialize worker process environment."""
    if "PYTORCH_CUDA_ALLOC_CONF" not in os.environ:
        os.environ["PYTORCH_CUDA_ALLOC_CONF"] = (
            "expandable_segments:True,garbage_collection_threshold:0.8"
        )

    # Optional: set low priority so UI stays responsive?


def load_model(model_type: str, model_name: str, device: str, compute_type: Optional[str] = None):
    """Load model into global worker state."""
    global _wrapper, _last_model_config

    from speakeasy.core.models import ModelWrapper

    if _wrapper is not None:
        if _wrapper.model_name == model_name and _wrapper.model_type.value == model_type:
            return True  # Already loaded
        # Unload old
        _wrapper.unload()
        _wrapper = None
        gc.collect()

    logger.info(f"[Worker] Loading model {model_type}/{model_name}...")
    _wrapper = ModelWrapper(
        model_type=model_type, model_name=model_name, device=device, compute_type=compute_type
    )
    # Load without progress callback as it's hard to pickle
    _wrapper.load(progress_callback=None)
    logger.info("[Worker] Model loaded.")

    # Store config for potential reload
    _last_model_config = {
        "model_type": model_type,
        "model_name": model_name,
        "device": device,
        "compute_type": compute_type,
    }

    return True


def reload_model():
    """Reload the current model to recover from errors (e.g. CUDA, NeMo state corruption)."""
    global _wrapper, _last_model_config

    if not _last_model_config:
        logger.warning("[Worker] Cannot reload model: no model was previously loaded")
        return False

    logger.info("[Worker] Reloading model to recover from error...")

    # Unload current model
    if _wrapper:
        try:
            _wrapper.unload()
        except Exception as e:
            logger.warning(f"[Worker] Error unloading model during reload: {e}")
        _wrapper = None

    # Force aggressive cleanup
    gc.collect()
    try:
        import torch

        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.synchronize()  # Ensure all CUDA operations complete
    except Exception as e:
        logger.warning(f"[Worker] Failed to clear CUDA cache during reload: {e}")

    # Reload model
    try:
        from speakeasy.core.models import ModelWrapper

        _wrapper = ModelWrapper(**_last_model_config)
        _wrapper.load(progress_callback=None)
        logger.info("[Worker] Model reloaded successfully.")
        return True
    except Exception as e:
        logger.error(f"[Worker] Failed to reload model: {e}")
        _wrapper = None
        return False


def transcribe(
    audio_data, sample_rate: int, language: Optional[str] = None, instruction: Optional[str] = None
):
    """Transcribe using global worker state."""
    global _wrapper
    if _wrapper is None:
        raise RuntimeError("Model not loaded in worker")

    # Check if this is a NeMo model (Parakeet or Canary) which has known issues
    # with internal state corruption between transcriptions
    is_nemo_model = _wrapper.model_type.value in ("parakeet", "canary")

    logger.info(f"[Worker] Transcribing {len(audio_data)} samples...")

    try:
        res = _wrapper.transcribe(audio_data, sample_rate, language, instruction)

        # For NeMo models, unload and reload to prevent state corruption
        # This is a workaround for the STATUS_STACK_BUFFER_OVERRUN issue (0xC0000409)
        # that occurs on the second transcription with NeMo models
        if is_nemo_model:
            logger.info("[Worker] NeMo model detected - reloading to prevent state corruption")
            reload_model()
        else:
            # For non-NeMo models, just clear CUDA cache
            try:
                import torch

                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
            except Exception as e:
                logger.warning(f"[Worker] Failed to clear CUDA cache: {e}")

        return res

    except Exception as e:
        logger.error(f"[Worker] Transcription failed: {e}")
        # Attempt to reload model for recovery
        if is_nemo_model:
            logger.info("[Worker] Attempting model reload after transcription failure")
            reload_model()
        raise


def unload_model():
    """Unload model from worker state."""
    global _wrapper, _last_model_config
    if _wrapper:
        _wrapper.unload()
        _wrapper = None
        gc.collect()
        try:
            import torch

            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except:
            pass
    _last_model_config = {}
    return True


def is_model_loaded():
    """Check if model is loaded."""
    global _wrapper
    if _wrapper is None:
        return False
    return _wrapper.is_loaded


def get_model_info():
    """Get loaded model info."""
    global _wrapper
    if _wrapper is None or not _wrapper.is_loaded:
        return None
    return {"model_type": _wrapper.model_type.value, "model_name": _wrapper.model_name}


def get_last_model_config():
    """Get the configuration of the last loaded model."""
    global _last_model_config
    return _last_model_config.copy() if _last_model_config else None
