import asyncio
import numpy as np
import logging
import sys
import os
from unittest.mock import MagicMock

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

# --- MOCKS ---
mock_torch = MagicMock()
mock_torch.cuda.is_available.return_value = True
sys.modules["torch"] = mock_torch

sys.modules["sounddevice"] = MagicMock()
sys.modules["soundfile"] = MagicMock()

# Mock faster_whisper
mock_fw = MagicMock()
sys.modules["faster_whisper"] = mock_fw
sys.modules["faster_whisper.audio"] = MagicMock()

# Mock internal models module to avoid heavy imports there too
# But TranscriberService imports ModelWrapper from .models
# We can let it import .models if .models just imports torch/etc which are already mocked.
# Let's check backend/speakeasy/core/models.py dependencies.
# It imports faster_whisper, huggingface_hub, etc.
# Better to mock speakeasy.core.models completely?
# No, we want to test TranscriberService logic.
# TranscriberService uses ModelWrapper.
# We should allow speakeasy.core.models to be imported, but ensure its deps are mocked.

sys.modules["huggingface_hub"] = MagicMock()
sys.modules["ctranslate2"] = MagicMock()
sys.modules["nemo"] = MagicMock()
sys.modules["nemo.collections.asr.models"] = MagicMock()
sys.modules["mistral_common"] = MagicMock()
sys.modules["mistral_common.protocol.transcription.request"] = MagicMock()
sys.modules["pydantic_extra_types"] = MagicMock()
sys.modules["pydantic_extra_types.language_code"] = MagicMock()

# --- END MOCKS ---

from speakeasy.core.transcriber import TranscriberService, TranscriberState

# Setup logging
logging.basicConfig(level=logging.INFO)


async def main():
    print("Initializing TranscriberService...")
    try:
        service = TranscriberService()
    except Exception as e:
        print(f"Failed to init service: {e}")
        import traceback

        traceback.print_exc()
        return

    print("Loading model (mocked)...")
    try:
        service.load_model(model_type="whisper", model_name="tiny", device="cuda")
    except Exception as e:
        print(f"Failed to load model: {e}")
        import traceback

        traceback.print_exc()
        return

    # Verify state
    print(f"State after load: {service.state}")

    print("Creating dummy audio...")
    dummy_audio = np.zeros(16000 * 1, dtype=np.float32)  # 1 sec silence

    print("Transcribing 1...")
    try:
        # Mock the model's transcribe method
        if service._model:
            service._model.transcribe = MagicMock()
            result_mock = MagicMock()
            result_mock.text = "Mock transcription"
            service._model.transcribe.return_value = result_mock

        result = service.transcribe(dummy_audio, sample_rate=16000)
        print(f"Result 1: {result.text}")
    except Exception as e:
        print(f"Transcription failed: {e}")
        import traceback

        traceback.print_exc()
        return

    print("Reloading model...")
    if hasattr(service, "reload_model"):
        try:
            # We want to verify reload_model calls load_model again
            # Mock load_model to track calls?
            # Or just check if _model is recreated.
            old_model = service._model

            service.reload_model()
            print("Model reloaded.")

            if service._model is not old_model:
                print("Confirmed: New model instance created.")
            else:
                print(
                    "Warning: Model instance matches (might be expected if mock returns same?)"
                )
                # With real ModelWrapper, it would be new.
        except Exception as e:
            print(f"Reload failed: {e}")
            import traceback

            traceback.print_exc()
            return
    else:
        print("reload_model not implemented yet.")
        return

    print("Transcribing 2...")
    try:
        # Re-mock the new model's transcribe method
        if service._model:
            service._model.transcribe = MagicMock()
            result_mock = MagicMock()
            result_mock.text = "Mock transcription 2"
            service._model.transcribe.return_value = result_mock

        result = service.transcribe(dummy_audio, sample_rate=16000)
        print(f"Result 2: {result.text}")
    except Exception as e:
        print(f"Transcription 2 failed: {e}")
        return

    print("Success!")


if __name__ == "__main__":
    asyncio.run(main())
