#!/usr/bin/env python3
"""
Dependency verification script for SpeakEasy backend.
Checks all required dependencies from pyproject.toml and attempts repair if missing.
"""

import importlib
import subprocess
import sys
import tomllib
from pathlib import Path


def get_required_packages():
    """Parse pyproject.toml and return list of required packages (import names)."""
    pyproject_path = Path(__file__).parent / "pyproject.toml"

    with open(pyproject_path, "rb") as f:
        config = tomllib.load(f)

    deps = config.get("project", {}).get("dependencies", [])

    # Map package names to import names
    package_import_map = {
        "fastapi": "fastapi",
        "uvicorn": "uvicorn",
        "websockets": "websockets",
        "slowapi": "slowapi",
        "sounddevice": "sounddevice",
        "numpy": "numpy",
        "scipy": "scipy",
        "faster-whisper": "faster_whisper",
        "torch": "torch",
        "nemo_toolkit": "nemo",
        "transformers": "transformers",
        "huggingface_hub": "huggingface_hub",
        "pynput": "pynput",
        "pyperclip": "pyperclip",
        "aiosqlite": "aiosqlite",
        "pydantic": "pydantic",
        "pydantic-settings": "pydantic_settings",
        "cuda-python": "cuda",
        "dill": "dill",
    }

    packages = []
    for dep in deps:
        # Extract package name (handle extras and version specs)
        pkg_name = dep.split("[")[0].split(">=")[0].split("<")[0].strip()
        import_name = package_import_map.get(pkg_name, pkg_name.replace("-", "_"))
        packages.append((pkg_name, import_name))

    return packages


def check_import(import_name):
    """Try to import a module."""
    try:
        importlib.import_module(import_name)
        return True
    except ImportError:
        return False


def check_dependencies():
    """Check all dependencies and return missing ones."""
    print("[CHECK] Verifying backend dependencies...")

    packages = get_required_packages()
    missing = []

    for pkg_name, import_name in packages:
        if check_import(import_name):
            print(f"  [OK] {pkg_name}")
        else:
            print(f"  [MISSING] {pkg_name}")
            missing.append(pkg_name)

    return missing


def repair_dependencies():
    """Attempt to reinstall missing dependencies."""
    print("\n[INFO] Attempting to repair dependencies...")

    # Try to detect CUDA
    has_cuda = False
    try:
        result = subprocess.run(
            ["nvidia-smi"],
            capture_output=True,
            text=True,
            shell=True if sys.platform == "win32" else False,
        )
        has_cuda = result.returncode == 0
    except:
        pass

    # Build install command
    if has_cuda:
        print("[INFO] CUDA detected - installing with GPU support...")
        extras = "[cuda]"
    else:
        print("[INFO] No CUDA detected - installing in CPU mode...")
        extras = ""

    cmd = [sys.executable, "-m", "pip", "install", f"-e{extras}", "."]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=Path(__file__).parent)
        if result.returncode == 0:
            print("[OK] Dependencies installed successfully.")
            return True
        else:
            print(f"[ERROR] Failed to install dependencies:\n{result.stderr}")
            return False
    except Exception as e:
        print(f"[ERROR] Installation failed: {e}")
        return False


def main():
    """Main entry point."""
    missing = check_dependencies()

    if missing:
        print(f"\n[WARN] {len(missing)} dependencies are missing!")

        if repair_dependencies():
            # Re-check
            print("\n[CHECK] Verifying after repair...")
            still_missing = check_dependencies()

            if still_missing:
                print(f"\n[ERROR] Still missing {len(still_missing)} packages after repair:")
                for pkg in still_missing:
                    print(f"  - {pkg}")
                return 1
            else:
                print("\n[OK] All dependencies are now installed.")
                return 0
        else:
            print("\n[ERROR] Failed to repair dependencies.")
            return 1
    else:
        print("\n[OK] All dependencies verified.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
