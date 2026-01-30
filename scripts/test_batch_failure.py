import sys
import os
import time
import json
import numpy as np
from unittest.mock import MagicMock, patch
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

# Mock missing dependencies
sys.modules["torch"] = MagicMock()
sys.modules["soundfile"] = MagicMock()
sys.modules["sounddevice"] = MagicMock()
sys.modules["faster_whisper"] = MagicMock()
sys.modules["nemo"] = MagicMock()
sys.modules["nemo.collections"] = MagicMock()
sys.modules["nemo.collections.asr"] = MagicMock()
sys.modules["nemo.collections.asr.models"] = MagicMock()
sys.modules["transformers"] = MagicMock()
sys.modules["mistral_common.protocol.transcription.request"] = MagicMock()
sys.modules["pydantic_extra_types.language_code"] = MagicMock()

from backend.speakeasy.core.models import (
    ModelWrapper,
    ModelType,
    safe_write_manifest,
    safe_delete,
)


def test_canary_failure_cleanup():
    print("Testing Canary cleanup on failure...")

    wrapper = ModelWrapper(model_type="canary", model_name="test-canary")
    wrapper._model = MagicMock()
    wrapper._loaded = True

    # Mock model to raise exception
    wrapper._model.transcribe.side_effect = RuntimeError("Simulated model crash")

    captured_paths = []

    with patch("soundfile.write") as mock_write:

        def side_effect(file, data, rate):
            # Track the file created
            captured_paths.append(file)
            with open(file, "w") as f:
                f.write("dummy audio")

        mock_write.side_effect = side_effect

        # Spy on safe_write_manifest to catch manifest path
        original_write_manifest = safe_write_manifest

        def side_effect_manifest(data):
            path = original_write_manifest(data)
            captured_paths.append(path)
            return path

        with patch(
            "backend.speakeasy.core.models.safe_write_manifest",
            side_effect=side_effect_manifest,
        ):
            audio_data = np.zeros(16000, dtype=np.float32)

            try:
                wrapper._transcribe_canary(audio_data, 16000, "en")
                print("FAIL: Exception not raised")
                return False
            except RuntimeError as e:
                print(f"   Caught expected exception: {e}")

            # Verify cleanup
            if not captured_paths:
                print("FAIL: No files captured?")
                return False

            print(
                f"   Checking cleanup for {len(captured_paths)} files: {captured_paths}"
            )

            for path in captured_paths:
                if os.path.exists(path):
                    print(f"FAIL: File {path} was not deleted")
                    return False

    print("SUCCESS: Canary cleanup passed.")
    return True


if __name__ == "__main__":
    success = test_canary_failure_cleanup()
    sys.exit(0 if success else 1)
