import os
import sys
import json
import importlib.util
from pathlib import Path


def check_package(package_name, display_name=None):
    """Checks if a package is installed and returns its version if found."""
    name = display_name or package_name
    try:
        if package_name in sys.modules:
            module = sys.modules[package_name]
        else:
            spec = importlib.util.find_spec(package_name)
            if spec is None:
                print(f"❌ {name}: Not installed")
                return None
            module = importlib.import_module(package_name)

        version = getattr(module, "__version__", "Unknown version")
        print(f"✅ {name}: {version}")
        return module
    except ImportError:
        print(f"❌ {name}: Not installed (ImportError)")
        return None
    except Exception as e:
        print(f"⚠️ {name}: Error checking - {e}")
        return None


def check_gpu(torch_module):
    """Checks for GPU availability using Torch."""
    print("\n--- GPU/CUDA Check ---")
    if not torch_module:
        print("Skipping GPU check (torch not installed)")
        return

    try:
        is_available = torch_module.cuda.is_available()
        print(f"CUDA Available: {is_available}")

        if is_available:
            count = torch_module.cuda.device_count()
            print(f"GPU Count: {count}")
            for i in range(count):
                print(f"  GPU {i}: {torch_module.cuda.get_device_name(i)}")

            current_device = torch_module.cuda.current_device()
            print(f"Current Device ID: {current_device}")
    except Exception as e:
        print(f"Error checking GPU: {e}")


def check_audio():
    """Checks available audio devices."""
    print("\n--- Audio Devices ---")
    try:
        import sounddevice as sd

        devices = sd.query_devices()
        print(devices)

        # Filter for input devices
        print("\nInput Devices:")
        input_devices = [d for d in sd.query_devices() if d["max_input_channels"] > 0]
        for i, d in enumerate(input_devices):
            print(f"  {i}: {d['name']} (Channels: {d['max_input_channels']})")

    except ImportError:
        print("❌ sounddevice: Not installed - Cannot check audio devices")
    except Exception as e:
        print(f"Error checking audio devices: {e}")


def check_env():
    print("========================================")
    print("      Speakeasy Environment Check       ")
    print("========================================")

    # 1. System Info
    print(f"\n--- System Info ---")
    print(f"Platform: {sys.platform}")
    print(f"Python: {sys.version.split()[0]}")
    print(f"Home: {Path.home()}")
    print(f"CWD: {os.getcwd()}")

    # 2. Dependencies
    print(f"\n--- Dependencies ---")

    # Core AI/ML
    torch_mod = check_package("torch", "PyTorch")
    check_package("numpy", "NumPy")
    check_package("faster_whisper", "Faster Whisper")
    check_package("nemo_toolkit", "NeMo Toolkit")

    # Web/API
    check_package("fastapi", "FastAPI")
    check_package("uvicorn", "Uvicorn")
    check_package("websockets", "Websockets")

    # Audio/Utils
    check_package("sounddevice", "SoundDevice")
    check_package("pynput", "Pynput")

    # 3. GPU Check
    check_gpu(torch_mod)

    # 4. Audio Check
    check_audio()

    # 5. Config Files
    print(f"\n--- Configuration ---")
    settings_dir = Path.home() / ".speakeasy"
    settings_file = settings_dir / "settings.json"

    print(f"Settings Dir: {settings_dir}")
    if settings_dir.exists():
        print(f"  ✅ Exists. Contents: {[x.name for x in settings_dir.iterdir()]}")
    else:
        print("  ❌ Does not exist.")

    if settings_file.exists():
        print(f"Settings File: {settings_file}")
        print(f"  ✅ Found. Content:")
        try:
            with open(settings_file, "r") as f:
                print(json.dumps(json.load(f), indent=2))
        except Exception as e:
            print(f"  ⚠️ Error reading file: {e}")
    else:
        print(f"Settings File: {settings_file}")
        print("  ❌ Not found.")

    # 6. HF Cache
    hf_cache = Path.home() / ".cache/huggingface/hub"
    print(f"\n--- Hugging Face Cache ---")
    print(f"Path: {hf_cache}")
    if hf_cache.exists():
        print(f"  ✅ Exists. Models found:")
        found_models = False
        for item in hf_cache.iterdir():
            if item.is_dir() and item.name.startswith("models--"):
                print(f"    - {item.name}")
                found_models = True
        if not found_models:
            print("    (No 'models--' directories found)")
    else:
        print("  ❌ Does not exist.")


if __name__ == "__main__":
    check_env()
