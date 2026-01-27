import os
from pathlib import Path
import json


def check_env():
    print(f"Home: {Path.home()}")
    print(f"CWD: {os.getcwd()}")

    settings_dir = Path.home() / ".speakeasy"
    settings_file = settings_dir / "settings.json"

    print(f"\nChecking {settings_dir}...")
    if settings_dir.exists():
        print(f"  Exists. Contents: {[x.name for x in settings_dir.iterdir()]}")
    else:
        print("  Does not exist.")

    if settings_file.exists():
        print(f"\nSettings file found. Content:")
        try:
            with open(settings_file, "r") as f:
                print(json.dumps(json.load(f), indent=2))
        except Exception as e:
            print(f"  Error reading file: {e}")

    hf_cache = Path.home() / ".cache/huggingface/hub"
    print(f"\nChecking HF Cache: {hf_cache}...")
    if hf_cache.exists():
        print(f"  Exists. Models found:")
        for item in hf_cache.iterdir():
            if item.is_dir() and item.name.startswith("models--"):
                print(f"    - {item.name}")
    else:
        print("  Does not exist.")


if __name__ == "__main__":
    check_env()
