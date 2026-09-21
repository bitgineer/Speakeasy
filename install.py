#!/usr/bin/env python3
"""SpeakEasy setup and launcher.

One entry point that prepares a machine to run SpeakEasy and starts it:
checks the toolchain, creates the backend environment, installs backend and
GUI dependencies, and launches the desktop app. Every step is idempotent, so
running it again is safe and fast.

Usage:
    python install.py              install, then offer to start the app
    python install.py --launch     install and start without asking
    python install.py --no-launch  install only
    python install.py --check      report what is missing, change nothing
    python install.py --cpu        skip CUDA even when an NVIDIA GPU exists
    python install.py --reinstall  rebuild the backend environment
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BACKEND = ROOT / "backend"
GUI = ROOT / "gui"
PYTHON_VERSION = "3.12"
MIN_NODE_MAJOR = 18
SETTINGS_PATH = Path.home() / ".speakeasy" / "settings.json"

IS_WINDOWS = os.name == "nt"
IS_MAC = sys.platform == "darwin"
IS_LINUX = sys.platform.startswith("linux")

STEP = 0


def say(message: str) -> None:
    print(message, flush=True)


def step(message: str) -> None:
    global STEP
    STEP += 1
    say(f"\n[{STEP}] {message}")


def ok(message: str) -> None:
    say(f"    ok: {message}")


def warn(message: str) -> None:
    say(f"    warn: {message}")


def fail(message: str) -> None:
    say(f"    error: {message}")


def die(message: str, hint: str | None = None) -> None:
    fail(message)
    if hint:
        say(f"    hint: {hint}")
    sys.exit(1)


def run(
    args: list[str],
    cwd: Path | None = None,
    capture: bool = False,
    check: bool = True,
) -> subprocess.CompletedProcess:
    if IS_WINDOWS and args and args[0] in {"npm", "npx"}:
        args = ["cmd", "/c", *args]
    result = subprocess.run(
        args,
        cwd=str(cwd) if cwd else None,
        capture_output=capture,
        text=True,
    )
    if check and result.returncode != 0:
        raise RuntimeError(f"command failed ({result.returncode}): {' '.join(args)}")
    return result


def have(command: str) -> bool:
    return shutil.which(command) is not None


def refresh_path() -> None:
    candidates = [
        Path.home() / ".local" / "bin",
        Path.home() / ".cargo" / "bin",
        Path(os.environ.get("LOCALAPPDATA", "")) / "bin",
    ]
    current = os.environ.get("PATH", "")
    extra = [str(p) for p in candidates if p.is_dir() and str(p) not in current]
    if extra:
        os.environ["PATH"] = os.pathsep.join(extra) + os.pathsep + current


def venv_python() -> Path:
    if IS_WINDOWS:
        return BACKEND / ".venv" / "Scripts" / "python.exe"
    return BACKEND / ".venv" / "bin" / "python"


def python_version(python: Path) -> tuple[int, int] | None:
    if not python.exists():
        return None
    result = run(
        [str(python), "-c", "import sys; print(f'{sys.version_info[0]}.{sys.version_info[1]}')"],
        capture=True,
        check=False,
    )
    if result.returncode != 0:
        return None
    try:
        major, minor = result.stdout.strip().split(".")
        return int(major), int(minor)
    except ValueError:
        return None


def venv_is_valid() -> bool:
    python = venv_python()
    return (BACKEND / ".venv" / "pyvenv.cfg").exists() and python_version(python) == (3, 12)


def has_nvidia_gpu() -> bool:
    if IS_MAC or not have("nvidia-smi"):
        return False
    result = run(["nvidia-smi"], capture=True, check=False)
    return result.returncode == 0


def ensure_uv() -> None:
    refresh_path()
    if have("uv"):
        version = run(["uv", "--version"], capture=True, check=False).stdout.strip()
        ok(version or "uv found")
        return
    say("    installing uv...")
    if IS_WINDOWS:
        command = (
            "irm https://astral.sh/uv/install.ps1 | iex"
        )
        run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", command])
    else:
        run(["sh", "-c", "curl -LsSf https://astral.sh/uv/install.sh | sh"])
    refresh_path()
    if not have("uv"):
        die(
            "uv was installed but is not on PATH",
            "open a new terminal and run this script again",
        )
    ok("uv installed")


def ensure_python() -> None:
    say(f"    ensuring Python {PYTHON_VERSION} (managed by uv)...")
    result = run(["uv", "python", "install", PYTHON_VERSION], capture=True, check=False)
    if result.returncode != 0:
        die(
            f"could not install Python {PYTHON_VERSION}",
            (result.stderr or result.stdout or "").strip() or None,
        )
    ok(f"Python {PYTHON_VERSION} available")


def install_backend(reinstall: bool, use_cuda: bool) -> None:
    if reinstall and (BACKEND / ".venv").exists():
        say("    removing the existing backend environment...")
        shutil.rmtree(BACKEND / ".venv", ignore_errors=True)

    if not venv_is_valid():
        if (BACKEND / ".venv").exists():
            warn("existing backend environment is unusable, recreating it")
            shutil.rmtree(BACKEND / ".venv", ignore_errors=True)
        say("    creating the backend environment...")
        run(["uv", "venv", "--python", PYTHON_VERSION], cwd=BACKEND)
    else:
        ok("backend environment is ready")

    extra = ".[cuda]" if use_cuda else "."
    say(f"    installing backend dependencies ({extra})...")
    started = time.monotonic()
    result = run(
        ["uv", "pip", "install", "--python", str(venv_python()), "-e", extra],
        cwd=BACKEND,
        capture=True,
        check=False,
    )
    if result.returncode != 0:
        die(
            "backend dependency install failed",
            (result.stderr or result.stdout or "").strip()[-600:] or None,
        )
    ok(f"dependencies installed in {time.monotonic() - started:.0f}s")


def check_backend(use_cuda: bool) -> list[str]:
    problems: list[str] = []
    python = venv_python()
    if not venv_is_valid():
        return ["backend environment is missing (run without --check to create it)"]

    check = run(["uv", "pip", "check", "--python", str(python)], capture=True, check=False)
    if check.returncode != 0:
        problems.append("backend dependencies are incomplete (uv pip check failed)")

    probe = (
        "import importlib.util as u, sys\n"
        "names = ['fastapi', 'uvicorn', 'numpy', 'scipy', 'torch', 'faster_whisper', "
        "'sounddevice', 'aiosqlite']\n"
        "missing = [n for n in names if u.find_spec(n) is None]\n"
        "if missing:\n"
        "    print('missing: ' + ', '.join(missing)); sys.exit(1)\n"
        "if sys.argv[1] == 'cuda':\n"
        "    import torch\n"
        "    print('cuda: ' + str(torch.cuda.is_available()))\n"
    )
    result = run([str(python), "-c", probe, "cuda" if use_cuda else "cpu"], capture=True, check=False)
    if result.returncode != 0:
        problems.append((result.stdout or result.stderr or "backend import check failed").strip())
    elif use_cuda and "cuda: True" not in result.stdout:
        problems.append("CUDA was requested but torch cannot see the GPU")
    return problems


def install_gui() -> None:
    node = run(["node", "--version"], capture=True, check=False).stdout.strip()
    major = int(node.lstrip("v").split(".")[0]) if node.startswith("v") else 0
    if major < MIN_NODE_MAJOR:
        die(
            f"Node.js {MIN_NODE_MAJOR}+ is required (found {node or 'nothing'})",
            "install it from https://nodejs.org",
        )
    ok(f"Node {node}")

    if (GUI / "node_modules" / "electron" / "package.json").exists():
        ok("GUI dependencies are installed")
        return
    say("    installing GUI dependencies (this can take a few minutes)...")
    result = run(["npm", "install"], cwd=GUI, capture=True, check=False)
    if result.returncode != 0:
        die(
            "npm install failed",
            (result.stderr or result.stdout or "").strip()[-600:] or None,
        )
    ok("GUI dependencies installed")


def check_ffmpeg() -> None:
    if have("ffmpeg"):
        ok("ffmpeg found")
        return
    hints = {
        "nt": "winget install Gyan.FFmpeg",
        "darwin": "brew install ffmpeg",
    }
    hint = hints.get(os.name if IS_WINDOWS else sys.platform, "install ffmpeg with your package manager")
    warn(f"ffmpeg is not installed; audio file transcription needs it ({hint})")


def write_first_run_settings(use_cuda: bool) -> None:
    if SETTINGS_PATH.exists():
        return
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(SETTINGS_PATH, "w") as handle:
        json.dump({"device": "cuda" if use_cuda else "cpu"}, handle, indent=2)
    ok(f"wrote first-run settings ({'cuda' if use_cuda else 'cpu'} device) to {SETTINGS_PATH}")


def launch() -> None:
    say("\nStarting SpeakEasy. Press Ctrl+C to stop.\n")
    run(["npm", "run", "dev"], cwd=GUI)


def main() -> None:
    parser = argparse.ArgumentParser(description="Set up and start SpeakEasy.")
    parser.add_argument("--check", action="store_true", help="report what is missing, change nothing")
    parser.add_argument("--no-launch", action="store_true", help="install without starting the app")
    parser.add_argument("--launch", action="store_true", help="start the app without asking")
    parser.add_argument("--cpu", action="store_true", help="skip CUDA even when an NVIDIA GPU exists")
    parser.add_argument("--reinstall", action="store_true", help="rebuild the backend environment")
    args = parser.parse_args()

    say("SpeakEasy setup")
    say(f"  root: {ROOT}")
    say(f"  platform: {platform.system()} {platform.machine()}")

    if not BACKEND.is_dir() or not GUI.is_dir():
        die("backend/ and gui/ must sit next to this script")

    use_cuda = has_nvidia_gpu() and not args.cpu
    say(f"  device: {'cuda' if use_cuda else 'cpu'}"
        + (" (no NVIDIA GPU detected)" if not use_cuda and not IS_MAC else ""))

    if args.check:
        problems: list[str] = []
        step("Checking the toolchain")
        if have("uv"):
            ok("uv found")
        else:
            problems.append("uv is not installed")
        if venv_is_valid():
            ok(f"backend Python {PYTHON_VERSION}")
        else:
            problems.append("backend environment is missing or not Python 3.12")
        step("Checking dependencies")
        backend_problems = check_backend(use_cuda)
        if backend_problems:
            problems.extend(backend_problems)
        else:
            ok("backend dependencies verified")
        node = run(["node", "--version"], capture=True, check=False).stdout.strip()
        if node:
            ok(f"Node {node}")
        else:
            problems.append("Node.js is not installed")
        if (GUI / "node_modules").is_dir():
            ok("GUI dependencies present")
        else:
            problems.append("GUI dependencies are missing (run without --check)")
        check_ffmpeg()
        if problems:
            say("\nMissing or broken:")
            for problem in problems:
                say(f"  - {problem}")
            sys.exit(1)
        say("\nEverything is ready.")
        return

    step("Checking the toolchain")
    ensure_uv()
    ensure_python()

    step("Preparing the backend")
    install_backend(args.reinstall, use_cuda)
    problems = check_backend(use_cuda)
    if problems:
        die("backend verification failed", "; ".join(problems))
    ok("backend verified")

    step("Preparing the desktop app")
    install_gui()

    step("Checking optional tools")
    check_ffmpeg()

    step("First-run settings")
    write_first_run_settings(use_cuda)

    say("\nSetup complete.")
    say("The first launch downloads the default speech model (about 2 GB).")

    if args.no_launch:
        return
    if args.launch:
        launch()
        return
    if sys.stdin.isatty():
        answer = input("\nStart SpeakEasy now? [Y/n] ").strip().lower()
        if answer in {"", "y", "yes"}:
            launch()
    else:
        say("Run `npm run dev` in gui/ to start the app.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        say("\nStopped.")
        sys.exit(130)
    except RuntimeError as error:
        die(str(error))
