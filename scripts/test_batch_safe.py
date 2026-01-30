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


def test_canary_safe_manifest():
    print("Testing Canary safe manifest usage...")

    # Setup mock model
    wrapper = ModelWrapper(model_type="canary", model_name="test-canary")
    wrapper._model = MagicMock()
    wrapper._loaded = True

    # Mock soundfile.write to just create a dummy file
    with patch("soundfile.write") as mock_write:

        def side_effect(file, data, rate):
            # Create the file so safe_write_manifest can use it
            with open(file, "w") as f:
                f.write("dummy audio")

        mock_write.side_effect = side_effect

        # Test data
        audio_data = np.zeros(16000, dtype=np.float32)  # 1 sec

        # Run transcribe
        wrapper._transcribe_canary(audio_data, 16000, "en")

        # Verify model was called with a JSON file (manifest), not wav
        call_args = wrapper._model.transcribe.call_args
        if not call_args:
            print("FAIL: Model transcribe not called")
            return False

        kwargs = call_args.kwargs
        audio_arg = kwargs.get("audio")

        print(f"   Model called with audio={audio_arg}")

        if not audio_arg:
            print("FAIL: 'audio' arg missing")
            return False

        if not audio_arg.endswith(".json"):
            print(f"FAIL: Expected manifest (.json), got {audio_arg}")
            return False

        # Verify manifest content
        # Note: file should be deleted by now, but maybe we can spy on safe_write_manifest?
        # But we can verify it was a temp file path.

        # Verify cleanup
        if os.path.exists(audio_arg):
            print("FAIL: Manifest file not cleaned up")
            return False

    print("SUCCESS: Canary used manifest and cleaned up.")
    return True


def test_parakeet_safe_manifest():
    print("Testing Parakeet safe manifest usage...")

    # Setup mock model
    wrapper = ModelWrapper(model_type="parakeet", model_name="test-parakeet")
    wrapper._model = MagicMock()
    wrapper._loaded = True

    with patch("soundfile.write") as mock_write:

        def side_effect(file, data, rate):
            with open(file, "w") as f:
                f.write("dummy audio")

        mock_write.side_effect = side_effect

        audio_data = np.zeros(16000, dtype=np.float32)

        wrapper._transcribe_parakeet(audio_data, 16000)

        # Verify model called with manifest path (string)
        call_args = wrapper._model.transcribe.call_args
        arg = call_args[0][0]  # first arg

        print(f"   Model called with arg={arg}")

        if not arg.endswith(".json"):
            print(f"FAIL: Expected manifest (.json), got {arg}")
            return False

        if os.path.exists(arg):
            print("FAIL: Manifest file not cleaned up")
            return False

    print("SUCCESS: Parakeet used manifest and cleaned up.")
    return True


if __name__ == "__main__":
    success = True
    success &= test_canary_safe_manifest()
    success &= test_parakeet_safe_manifest()
    sys.exit(0 if success else 1)
