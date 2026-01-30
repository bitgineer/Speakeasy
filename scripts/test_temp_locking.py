import sys
import os
import time
import json
import threading
from unittest.mock import MagicMock
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

# Mock missing dependencies
sys.modules["torch"] = MagicMock()
sys.modules["numpy"] = MagicMock()
sys.modules["numpy.typing"] = MagicMock()
sys.modules["soundfile"] = MagicMock()
sys.modules["sounddevice"] = MagicMock()
sys.modules["faster_whisper"] = MagicMock()
sys.modules["nemo"] = MagicMock()
sys.modules["nemo.collections"] = MagicMock()
sys.modules["nemo.collections.asr"] = MagicMock()
sys.modules["nemo.collections.asr.models"] = MagicMock()

# Avoid importing TranscriberService via __init__
# We need to import models.py directly.
# However, Python imports work better if we just mock the things models.py needs.

from backend.speakeasy.core.models import safe_write_manifest, safe_delete


def test_safe_manifest_handling():
    print("Testing safe manifest handling...")

    data = [{"audio_filepath": "test.wav", "text": "hello"}]

    # 1. Create manifest
    print("1. Creating manifest...")
    path = safe_write_manifest(data)
    print(f"   Manifest created at: {path}")

    if not os.path.exists(path):
        print("FAIL: File not created")
        return False

    # 2. Verify we can open it (simulate Lhotse reading)
    print("2. Verifying read access...")
    try:
        with open(path, "r") as f:
            content = f.read()
            print("   Read successful.")
            loaded = json.loads(content.strip())
            if loaded != data[0]:
                print(f"FAIL: Content mismatch. Got {loaded}, expected {data[0]}")
                return False
    except PermissionError:
        print("FAIL: PermissionError when reading - file is locked!")
        return False
    except Exception as e:
        print(f"FAIL: Error reading file: {e}")
        return False

    # 3. Simulate transient lock and delete
    print("3. Testing safe_delete with simulated lock...")

    # Create a lock by opening the file
    lock_file = open(path, "r")

    def release_lock_after_delay():
        time.sleep(0.2)
        print("   Releasing lock...")
        lock_file.close()

    # Start thread to release lock
    t = threading.Thread(target=release_lock_after_delay)
    t.start()

    # Try to delete - should retry until lock is released
    start_time = time.time()
    safe_delete(path)
    end_time = time.time()

    t.join()

    if os.path.exists(path):
        print("FAIL: File still exists after safe_delete")
        return False

    print(f"   Deletion successful (took {end_time - start_time:.2f}s)")

    print("SUCCESS: All checks passed.")
    return True


if __name__ == "__main__":
    success = test_safe_manifest_handling()
    sys.exit(0 if success else 1)
