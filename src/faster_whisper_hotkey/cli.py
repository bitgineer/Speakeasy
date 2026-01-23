"""
Comprehensive CLI for faster-whisper-hotkey.

This module provides a command-line interface for all application functionality,
including real-time recording, file transcription, settings management, and
history operations.

Commands
--------
record
    Start real-time audio recording with hotkey activation.

transcribe
    Transcribe audio files and save the output.

settings
    Manage configuration settings (list, get, set, reset).

history
    View and manage transcription history (view, clear, export, delete).

batch
    Batch process multiple audio files in parallel.

wizard
    Run the interactive settings wizard.

devices
    List available audio input devices.

models
    List available ASR models.

languages
    List supported language codes.

completion
    Generate shell completion scripts.

Functions
---------
create_parser
    Create the main argument parser.

main
    Main CLI entry point.
"""

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Optional

from . import __version__
from .settings import (
    Settings,
    SETTINGS_FILE,
    HISTORY_FILE,
    save_settings,
    load_settings,
    load_history,
    save_history,
    clear_history,
)
from .models import ModelWrapper
from .config import (
    accepted_models_whisper,
    accepted_languages_whisper,
    canary_source_target_languages,
    canary_allowed_language_pairs,
)

logger = logging.getLogger(__name__)


# Output formatting helpers
def print_success(msg: str):
    """Print success message in green."""
    print(f"\033[92m{msg}\033[0m")


def print_error(msg: str):
    """Print error message in red."""
    print(f"\033[91m{msg}\033[0m", file=sys.stderr)


def print_warning(msg: str):
    """Print warning message in yellow."""
    print(f"\033[93m{msg}\033[0m", file=sys.stderr)


def print_info(msg: str):
    """Print info message in blue."""
    print(f"\033[94m{msg}\033[0m")


def print_table(headers: list, rows: list, max_col_width: int = 50):
    """Print a formatted table.

    Args:
        headers: List of column headers
        rows: List of rows, each row is a list of values
        max_col_width: Maximum width for text columns
    """
    if not rows:
        return

    # Calculate column widths
    num_cols = len(headers)
    col_widths = []
    for i in range(num_cols):
        header_len = len(str(headers[i]))
        max_row_len = max((len(str(row[i])) for row in rows), default=0)
        col_widths.append(min(max(header_len, max_row_len), max_col_width))

    # Print header separator
    separator = "-" * (sum(col_widths) + (num_cols * 3) + 1)
    print(separator)

    # Print headers
    header_parts = []
    for i, h in enumerate(headers):
        header_parts.append(f" {str(h).ljust(col_widths[i])} ")
    print("|" + "|".join(header_parts) + "|")
    print(separator)

    # Print rows
    for row in rows:
        row_parts = []
        for i, cell in enumerate(row):
            cell_str = str(cell)
            if len(cell_str) > col_widths[i]:
                cell_str = cell_str[: col_widths[i] - 3] + "..."
            row_parts.append(f" {cell_str.ljust(col_widths[i])} ")
        print("|" + "|".join(row_parts) + "|")

    print(separator)


# -----------------------------------------------------------------------------
# Command: record
# -----------------------------------------------------------------------------

def cmd_record(args: argparse.Namespace):
    """Start real-time recording with hotkey activation."""
    from .transcriber import MicrophoneTranscriber

    settings = load_settings()
    if settings is None:
        print_error("No settings found. Run 'faster-whisper-hotkey wizard' first.")
        return 1

    # Override settings from command line if provided
    if args.device:
        settings.device = args.device
    if args.model:
        settings.model_name = args.model
    if args.language:
        settings.language = args.language
    if args.hotkey:
        settings.hotkey = args.hotkey
    if args.hold:
        settings.activation_mode = "hold"
    elif args.toggle:
        settings.activation_mode = "toggle"

    print_info(f"Starting transcription with hotkey: {settings.hotkey.upper()}")
    print_info(f"Model: {settings.model_name} | Language: {settings.language}")
    print_info(f"Mode: {settings.activation_mode}")
    print_info("Press the hotkey to start/stop recording. Press Ctrl+C to exit.")

    try:
        transcriber = MicrophoneTranscriber(settings)
        transcriber.run()
    except KeyboardInterrupt:
        print_info("\nExiting...")
    except Exception as e:
        print_error(f"Error: {e}")
        logger.exception("Transcription error")
        return 1

    return 0


# -----------------------------------------------------------------------------
# Command: transcribe
# -----------------------------------------------------------------------------

def cmd_transcribe(args: argparse.Namespace):
    """Transcribe audio file(s)."""
    import soundfile as sf
    import numpy as np

    settings = load_settings()
    if settings is None:
        print_error("No settings found. Run 'faster-whisper-hotkey wizard' first.")
        return 1

    # Override settings from command line if provided
    if args.device:
        settings.device = args.device
    if args.model:
        settings.model_name = args.model
        # Determine model type from model name
        if "parakeet" in args.model.lower():
            settings.model_type = "parakeet"
        elif "canary" in args.model.lower():
            settings.model_type = "canary"
        elif "voxtral" in args.model.lower():
            settings.model_type = "voxtral"
        else:
            settings.model_type = "whisper"
    if args.language:
        settings.language = args.language

    # Load model
    try:
        print_info(f"Loading model: {settings.model_name}...")
        model_wrapper = ModelWrapper(settings)
        print_success("Model loaded!")
    except Exception as e:
        print_error(f"Failed to load model: {e}")
        return 1

    files = args.files
    if args.input_dir:
        input_dir = Path(args.input_dir)
        extensions = args.extensions.split(",") if args.extensions else [".wav", ".mp3", ".flac", ".ogg", ".m4a"]
        for ext in extensions:
            files.extend(input_dir.glob(f"*{ext}"))
            files.extend(input_dir.glob(f"*{ext.upper()}"))

    if not files:
        print_warning("No audio files found to transcribe.")
        return 0

    results = []
    for file_path in files:
        file_path = Path(file_path)
        if not file_path.exists():
            print_warning(f"File not found: {file_path}")
            continue

        print_info(f"\nTranscribing: {file_path.name}")

        try:
            # Load audio
            audio_data, sample_rate = sf.read(file_path)

            # Convert to mono if needed
            if len(audio_data.shape) > 1:
                audio_data = np.mean(audio_data, axis=1)

            # Convert to float32 and normalize
            audio_data = audio_data.astype(np.float32)
            if not np.isclose(audio_data.max(), 0):
                audio_data /= np.abs(audio_data).max()

            # Transcribe
            start_time = time.time()
            transcribed_text = model_wrapper.transcribe(
                audio_data,
                sample_rate=sample_rate,
                language=settings.language,
            )
            elapsed = time.time() - start_time

            results.append({
                "file": str(file_path),
                "text": transcribed_text,
                "duration": len(audio_data) / sample_rate,
                "processing_time": elapsed,
            })

            print_success(f"Transcribed in {elapsed:.2f}s")
            print(f"  {transcribed_text}")

            # Save to output file if specified
            if args.output:
                output_path = Path(args.output)
                if len(files) > 1 and output_path.is_dir():
                    # For multiple files, save each to separate file in output dir
                    out_file = output_path / f"{file_path.stem}.txt"
                    out_file.write_text(transcribed_text, encoding="utf-8")
                    print_info(f"  Saved to: {out_file}")
                elif output_path.is_dir():
                    output_path.mkdir(parents=True, exist_ok=True)
                    out_file = output_path / f"{file_path.stem}.txt"
                    out_file.write_text(transcribed_text, encoding="utf-8")
                    print_info(f"  Saved to: {out_file}")

        except Exception as e:
            print_error(f"Failed to transcribe {file_path.name}: {e}")
            logger.exception(f"Transcription error for {file_path}")

    # Save summary if multiple files
    if len(files) > 1 and args.summary:
        summary_path = Path(args.summary)
        with summary_path.open("w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print_success(f"\nSummary saved to: {summary_path}")

    return 0


# -----------------------------------------------------------------------------
# Command: settings
# -----------------------------------------------------------------------------

def cmd_settings(args: argparse.Namespace):
    """Manage settings."""
    if args.action == "list":
        return _settings_list(args)
    elif args.action == "get":
        return _settings_get(args)
    elif args.action == "set":
        return _settings_set(args)
    elif args.action == "reset":
        return _settings_reset(args)
    else:
        print_error(f"Unknown action: {args.action}")
        return 1


def _settings_list(args: argparse.Namespace):
    """List all settings."""
    settings = load_settings()
    if settings is None:
        print_warning("No settings found. Configuration file does not exist.")
        return 0

    print_info("Current Settings:")
    print(f"  Device Name:       {settings.device_name}")
    print(f"  Model Type:        {settings.model_type}")
    print(f"  Model Name:        {settings.model_name}")
    print(f"  Compute Type:      {settings.compute_type}")
    print(f"  Device:            {settings.device}")
    print(f"  Language:          {settings.language}")
    print(f"  Hotkey:            {settings.hotkey}")
    print(f"  Activation Mode:   {settings.activation_mode}")
    print(f"  Max History Items: {settings.history_max_items}")
    print(f"  Privacy Mode:      {settings.privacy_mode}")
    print(f"\n  Settings File: {SETTINGS_FILE}")
    return 0


def _settings_get(args: argparse.Namespace):
    """Get a specific setting value."""
    settings = load_settings()
    if settings is None:
        print_warning("No settings found.")
        return 1

    if not hasattr(settings, args.key):
        print_error(f"Unknown setting: {args.key}")
        return 1

    value = getattr(settings, args.key)
    if args.json:
        print(json.dumps({args.key: value}, indent=2))
    else:
        print(value)

    return 0


def _settings_set(args: argparse.Namespace):
    """Set a specific setting value."""
    import json

    settings = load_settings()
    if settings is None:
        print_warning("No existing settings found. Creating new settings.")
        # Create default settings
        settings = Settings(
            device_name="default",
            model_type="whisper",
            model_name="large-v3",
            compute_type="float16",
            device="cuda",
            language="en",
        )

    # Parse the value (try JSON first, then string)
    try:
        value = json.loads(args.value)
    except json.JSONDecodeError:
        value = args.value

    # Convert to appropriate type based on setting
    type_conversions = {
        "history_max_items": int,
        "privacy_mode": lambda x: x.lower() in ("true", "1", "yes"),
        "activation_mode": str,
    }

    if args.key in type_conversions:
        try:
            value = type_conversions[args.key](value)
        except (ValueError, TypeError) as e:
            print_error(f"Invalid value for {args.key}: {e}")
            return 1

    if not hasattr(settings, args.key):
        print_error(f"Unknown setting: {args.key}")
        return 1

    setattr(settings, args.key, value)

    # Save settings
    settings_dict = {
        "device_name": settings.device_name,
        "model_type": settings.model_type,
        "model_name": settings.model_name,
        "compute_type": settings.compute_type,
        "device": settings.device,
        "language": settings.language,
        "hotkey": settings.hotkey,
        "activation_mode": settings.activation_mode,
        "history_max_items": settings.history_max_items,
        "privacy_mode": settings.privacy_mode,
    }
    save_settings(settings_dict)

    print_success(f"Setting updated: {args.key} = {value}")
    return 0


def _settings_reset(args: argparse.Namespace):
    """Reset settings to defaults."""
    if os.path.exists(SETTINGS_FILE):
        os.remove(SETTINGS_FILE)
        print_success("Settings reset to defaults.")
        print_info("Run 'faster-whisper-hotkey wizard' to configure.")
    else:
        print_warning("No settings file found.")
    return 0


# -----------------------------------------------------------------------------
# Command: history
# -----------------------------------------------------------------------------

def cmd_history(args: argparse.Namespace):
    """Manage transcription history."""
    if args.action == "view":
        return _history_view(args)
    elif args.action == "clear":
        return _history_clear(args)
    elif args.action == "export":
        return _history_export(args)
    elif args.action == "delete":
        return _history_delete(args)
    else:
        print_error(f"Unknown action: {args.action}")
        return 1


def _history_view(args: argparse.Namespace):
    """View transcription history."""
    history = load_history()

    if not history:
        print_info("No history found.")
        return 0

    # Apply limit
    if args.limit and args.limit > 0:
        history = history[-args.limit :]

    print_info(f"Transcription History ({len(history)} items):")
    print()

    for i, entry in enumerate(reversed(history), 1):
        timestamp = entry.get("timestamp", "Unknown")
        text = entry.get("text", "")

        # Show offset/page info if available
        extra = []
        if "offset" in entry:
            extra.append(f"offset: {entry['offset']}")
        if "page" in entry:
            extra.append(f"page: {entry['page']}")
        extra_str = f" [{', '.join(extra)}]" if extra else ""

        print(f"{i}. [{timestamp}]{extra_str}")
        print(f"   {text[:200]}{'...' if len(text) > 200 else ''}")
        print()

    return 0


def _history_clear(args: argparse.Namespace):
    """Clear transcription history."""
    if not args.force:
        response = input("Are you sure you want to clear all history? [y/N] ")
        if response.lower() != "y":
            print_info("Cancelled.")
            return 0

    clear_history()
    print_success("History cleared.")
    return 0


def _history_export(args: argparse.Namespace):
    """Export transcription history to file."""
    history = load_history()

    if not history:
        print_warning("No history to export.")
        return 0

    output_path = Path(args.output)

    # Determine format from extension
    fmt = output_path.suffix.lstrip(".")

    if fmt == "json":
        with output_path.open("w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
    elif fmt == "txt":
        with output_path.open("w", encoding="utf-8") as f:
            for entry in history:
                timestamp = entry.get("timestamp", "Unknown")
                text = entry.get("text", "")
                f.write(f"[{timestamp}] {text}\n\n")
    elif fmt == "csv":
        import csv
        with output_path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp", "text"])
            for entry in history:
                writer.writerow([entry.get("timestamp", ""), entry.get("text", "")])
    elif fmt == "md":
        with output_path.open("w", encoding="utf-8") as f:
            f.write("# Transcription History\n\n")
            for i, entry in enumerate(reversed(history), 1):
                timestamp = entry.get("timestamp", "Unknown")
                text = entry.get("text", "")
                f.write(f"## {i}. [{timestamp}]\n\n{text}\n\n")
    else:
        print_error(f"Unsupported format: {fmt}")
        return 1

    print_success(f"Exported {len(history)} items to {output_path}")
    return 0


def _history_delete(args: argparse.Namespace):
    """Delete specific history entries."""
    history = load_history()

    if not history:
        print_warning("No history found.")
        return 0

    # Parse indices (1-based, from newest)
    indices = [int(i) for i in args.indices]
    indices_to_delete = []
    for idx in indices:
        if idx <= len(history):
            # Convert 1-based from newest to 0-based from oldest
            actual_idx = len(history) - idx
            indices_to_delete.append(actual_idx)

    # Delete in reverse order to preserve indices
    for idx in sorted(indices_to_delete, reverse=True):
        deleted = history.pop(idx)
        print_info(f"Deleted: {deleted.get('text', '')[:50]}...")

    save_history(history, max_items=len(history))
    print_success(f"Deleted {len(indices_to_delete)} entries.")
    return 0


# -----------------------------------------------------------------------------
# Command: batch
# -----------------------------------------------------------------------------

def cmd_batch(args: argparse.Namespace):
    """Batch process audio files."""
    import soundfile as sf
    import numpy as np
    from concurrent.futures import ThreadPoolExecutor, as_completed

    settings = load_settings()
    if settings is None:
        print_error("No settings found. Run 'faster-whisper-hotkey wizard' first.")
        return 1

    # Override settings from command line
    if args.device:
        settings.device = args.device
    if args.model:
        settings.model_name = args.model
    if args.language:
        settings.language = args.language

    # Collect files
    files = []
    for pattern in args.patterns:
        path = Path(pattern)
        if path.is_file():
            files.append(path)
        elif path.is_dir():
            files.extend(path.glob("*"))
        else:
            # Glob pattern
            files.extend(Path().glob(pattern))

    # Filter by extension if specified
    if args.extensions:
        extensions = args.extensions.lower().split(",")
        files = [f for f in files if f.suffix.lower() in extensions]

    # Filter audio files
    audio_extensions = {".wav", ".mp3", ".flac", ".ogg", ".m4a", ".aac", ".wma"}
    files = [f for f in files if f.is_file() and f.suffix.lower() in audio_extensions]

    if not files:
        print_warning("No audio files found.")
        return 0

    print_info(f"Found {len(files)} audio files to process.")

    # Load model
    try:
        print_info("Loading model...")
        model_wrapper = ModelWrapper(settings)
        print_success("Model loaded!")
    except Exception as e:
        print_error(f"Failed to load model: {e}")
        return 1

    # Process files
    results = []
    failed = []

    def process_file(file_path):
        try:
            audio_data, sample_rate = sf.read(file_path)
            if len(audio_data.shape) > 1:
                audio_data = np.mean(audio_data, axis=1)
            audio_data = audio_data.astype(np.float32)
            if not np.isclose(audio_data.max(), 0):
                audio_data /= np.abs(audio_data).max()

            start_time = time.time()
            text = model_wrapper.transcribe(
                audio_data,
                sample_rate=sample_rate,
                language=settings.language,
            )
            elapsed = time.time() - start_time

            return {
                "file": str(file_path),
                "text": text,
                "success": True,
                "duration": len(audio_data) / sample_rate,
                "processing_time": elapsed,
            }
        except Exception as e:
            return {
                "file": str(file_path),
                "error": str(e),
                "success": False,
            }

    max_workers = args.workers if args.workers else min(4, os.cpu_count() or 1)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(process_file, f): f for f in files}
        for future in as_completed(futures):
            file_path = futures[future]
            try:
                result = future.result()
                if result["success"]:
                    results.append(result)
                    print_success(f"  {file_path.name}: {result['text'][:50]}...")
                else:
                    failed.append(result)
                    print_error(f"  {file_path.name}: {result['error']}")
            except Exception as e:
                print_error(f"  {file_path.name}: {e}")

    # Print summary
    print()
    print_info(f"Batch processing complete:")
    print(f"  Successful: {len(results)}")
    print(f"  Failed: {len(failed)}")

    # Save results
    if args.output:
        output_path = Path(args.output)
        with output_path.open("w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print_success(f"Results saved to: {output_path}")

    return 0


# -----------------------------------------------------------------------------
# Command: wizard
# -----------------------------------------------------------------------------

def cmd_wizard(args: argparse.Namespace):
    """Run the interactive settings wizard."""
    from .transcribe import main as transcribe_main
    return transcribe_main()


# -----------------------------------------------------------------------------
# Command: devices
# -----------------------------------------------------------------------------

def cmd_devices(args: argparse.Namespace):
    """List available audio devices."""
    import sounddevice as sd

    print_info("Available Audio Devices:")
    print()

    devices = sd.query_devices()
    for i, device in enumerate(devices):
        name = device.get("name", "Unknown")
        max_inputs = device.get("max_input_channels", 0)
        max_outputs = device.get("max_output_channels", 0)
        sample_rate = device.get("default_samplerate", 0)

        if max_inputs > 0:
            print(f"  [{i}] {name}")
            print(f"      Inputs: {max_inputs} | Outputs: {max_outputs} | Sample Rate: {sample_rate}Hz")

    print()
    print_info("Use the device index or name in settings.")
    return 0


# -----------------------------------------------------------------------------
# Command: models
# -----------------------------------------------------------------------------

def cmd_models(args: argparse.Namespace):
    """List available models."""
    print_info("Available Models:")
    print()

    if args.model_type == "whisper" or args.model_type == "all":
        print("\033[96mWhisper Models:\033[0m")
        for model in accepted_models_whisper:
            print(f"  - {model}")

    if args.model_type == "canary" or args.model_type == "all":
        print("\n\033[96mCanary Models:\033[0m")
        print("  - nvidia/canary-1b-v2")

    if args.model_type == "parakeet" or args.model_type == "all":
        print("\n\033[96mParakeet Models:\033[0m")
        print("  - nvidia/parakeet-tdt-0.6b-v3")

    if args.model_type == "voxtral" or args.model_type == "all":
        print("\n\033[96mVoxtral Models:\033[0m")
        print("  - fixie-ai/voxtral-mini-3b-2507")

    return 0


# -----------------------------------------------------------------------------
# Command: languages
# -----------------------------------------------------------------------------

def cmd_languages(args: argparse.Namespace):
    """List supported languages."""
    print_info("Supported Languages:")
    print()

    if args.model_type == "whisper" or args.model_type == "all":
        print("\033[96mWhisper Languages:\033[0m")
        for lang in sorted(accepted_languages_whisper):
            print(f"  - {lang}")

    if args.model_type == "canary" or args.model_type == "all":
        print("\n\033[96mCanary Language Pairs:\033[0m")
        for pair in canary_allowed_language_pairs:
            print(f"  - {pair}")

    return 0


# -----------------------------------------------------------------------------
# Command: completion
# -----------------------------------------------------------------------------

def cmd_completion(args: argparse.Namespace):
    """Generate shell completion script."""
    shell = args.shell

    if shell == "bash":
        bash_completion = """# faster-whisper-hotkey bash completion
_fwh_completion() {
    local cur prev words cword
    _init_completion || return

    case ${prev} in
        faster-whisper-hotkey)
            COMPREPLY=($(compgen -W "record transcribe settings history batch wizard devices models languages completion --help --version" -- "${cur}"))
            ;;
        record)
            COMPREPLY=($(compgen -W "--device --model --language --hotkey --hold --toggle --help" -- "${cur}"))
            ;;
        transcribe)
            COMPREPLY=($(compgen -W "--output --input-dir --extensions --summary --device --model --language --help" -- "${cur}"))
            ;;
        settings)
            COMPREPLY=($(compgen -W "list get set reset" -- "${cur}"))
            ;;
        history)
            COMPREPLY=($(compgen -W "view clear export delete --help" -- "${cur}"))
            ;;
        batch)
            COMPREPLY=($(compgen -W "--output --extensions --workers --device --model --language --help" -- "${cur}"))
            ;;
        --device)
            COMPREPLY=($(compgen -W "cuda cpu" -- "${cur}"))
            ;;
        --model)
            COMPREPLY=($(compgen -W "tiny base small medium large-v3" -- "${cur}"))
            ;;
        --language)
            COMPREPLY=($(compgen -W "en es fr de it pt ru ja zh ko auto" -- "${cur}"))
            ;;
        --shell)
            COMPREPLY=($(compgen -W "bash zsh fish" -- "${cur}"))
            ;;
        *)
            ;;
    esac
}

complete -F _fwh_completion faster-whisper-hotkey
"""
        print(bash_completion)

    elif shell == "zsh":
        zsh_completion = """#compdef faster-whisper-hotkey
# zsh completion for faster-whisper-hotkey

_fwh() {
    local -a commands
    commands=(
        'record:Start real-time recording with hotkey'
        'transcribe:Transcribe audio files'
        'settings:Manage configuration settings'
        'history:View and manage transcription history'
        'batch:Batch process multiple audio files'
        'wizard:Run interactive settings wizard'
        'devices:List available audio devices'
        'models:List available models'
        'languages:List supported languages'
        'completion:Generate shell completion script'
    )

    if (( CURRENT == 2 )); then
        _describe 'command' commands
    else
        case ${words[2]} in
            record)
                _arguments -s \\
                    '--device[Compute device (cuda/cpu)]:device:(cuda cpu)' \\
                    '--model[Model name]:model' \\
                    '--language[Language code]:language:(en es fr de it pt ru ja zh auto)' \\
                    '--hotkey[Hotkey combination]:hotkey' \\
                    '--hold[Use hold activation mode]' \\
                    '--toggle[Use toggle activation mode]' \\
                    '--help[Show help]'
                ;;
            transcribe)
                _arguments -s \\
                    '--output[Output file or directory]:output:_files' \\
                    '--input-dir[Input directory]:dir:_directories' \\
                    '--extensions[File extensions]:extensions' \\
                    '--summary[Summary output file]:file:_files' \\
                    '--device[Compute device]:device:(cuda cpu)' \\
                    '--model[Model name]:model' \\
                    '--language[Language code]:language:(en es fr de it pt ru ja zh auto)' \\
                    '--help[Show help]'
                ;;
            settings)
                _arguments -s \\
                    ':action:(list get set reset)' \\
                    '--json[Output as JSON]' \\
                    '--force[Bypass confirmation]' \\
                    '--help[Show help]'
                ;;
            history)
                _arguments -s \\
                    ':action:(view clear export delete)' \\
                    '--limit[Limit number of entries]:number' \\
                    '--output[Output file]:file:_files' \\
                    '--force[Bypass confirmation]' \\
                    '--help[Show help]'
                ;;
            batch)
                _arguments -s \\
                    '--output[Output file]:file:_files' \\
                    '--extensions[File extensions]:extensions' \\
                    '--workers[Number of workers]:number' \\
                    '--device[Compute device]:device:(cuda cpu)' \\
                    '--model[Model name]:model' \\
                    '--language[Language code]:language:(en es fr de it pt ru ja zh auto)' \\
                    '--help[Show help]'
                ;;
            completion)
                _arguments -s \\
                    '--shell[Shell type]:shell:(bash zsh fish)'
                ;;
        esac
    fi
}

_fwh "$@"
"""
        print(zsh_completion)

    elif shell == "fish":
        fish_completion = """# faster-whisper-hotkey fish completion

complete -c faster-whisper-hotkey -f

complete -c faster-whisper-hotkey -n "__fish_use_subcommand" -a record -d "Start real-time recording with hotkey"
complete -c faster-whisper-hotkey -n "__fish_use_subcommand" -a transcribe -d "Transcribe audio files"
complete -c faster-whisper-hotkey -n "__fish_use_subcommand" -a settings -d "Manage configuration settings"
complete -c faster-whisper-hotkey -n "__fish_use_subcommand" -a history -d "View and manage transcription history"
complete -c faster-whisper-hotkey -n "__fish_use_subcommand" -a batch -d "Batch process multiple audio files"
complete -c faster-whisper-hotkey -n "__fish_use_subcommand" -a wizard -d "Run interactive settings wizard"
complete -c faster-whisper-hotkey -n "__fish_use_subcommand" -a devices -d "List available audio devices"
complete -c faster-whisper-hotkey -n "__fish_use_subcommand" -a models -d "List available models"
complete -c faster-whisper-hotkey -n "__fish_use_subcommand" -a languages -d "List supported languages"
complete -c faster-whisper-hotkey -n "__fish_use_subcommand" -a completion -d "Generate shell completion script"

# record options
complete -c faster-whisper-hotkey -n "__fish_seen_subcommand_from record" -l device -d "Compute device (cuda/cpu)" -x -a "cuda cpu"
complete -c faster-whisper-hotkey -n "__fish_seen_subcommand_from record" -l model -d "Model name"
complete -c faster-whisper-hotkey -n "__fish_seen_subcommand_from record" -l language -d "Language code" -x -a "en es fr de it pt ru ja zh auto"
complete -c faster-whisper-hotkey -n "__fish_seen_subcommand_from record" -l hotkey -d "Hotkey combination"
complete -c faster-whisper-hotkey -n "__fish_seen_subcommand_from record" -l hold -d "Use hold activation mode"
complete -c faster-whisper-hotkey -n "__fish_seen_subcommand_from record" -l toggle -d "Use toggle activation mode"

# transcribe options
complete -c faster-whisper-hotkey -n "__fish_seen_subcommand_from transcribe" -l output -d "Output file or directory" -r
complete -c faster-whisper-hotkey -n "__fish_seen_subcommand_from transcribe" -l input-dir -d "Input directory" -r
complete -c faster-whisper-hotkey -n "__fish_seen_subcommand_from transcribe" -l extensions -d "File extensions (comma-separated)"
complete -c faster-whisper-hotkey -n "__fish_seen_subcommand_from transcribe" -l summary -d "Summary output file" -r
complete -c faster-whisper-hotkey -n "__fish_seen_subcommand_from transcribe" -l device -d "Compute device" -x -a "cuda cpu"
complete -c faster-whisper-hotkey -n "__fish_seen_subcommand_from transcribe" -l model -d "Model name"
complete -c faster-whisper-hotkey -n "__fish_seen_subcommand_from transcribe" -l language -d "Language code" -x -a "en es fr de it pt ru ja zh auto"

# settings subcommands
complete -c faster-whisper-hotkey -n "__fish_seen_subcommand_from settings" -x -a "list get set reset"
complete -c faster-whisper-hotkey -n "__fish_seen_subcommand_from settings" -l json -d "Output as JSON"
complete -c faster-whisper-hotkey -n "__fish_seen_subcommand_from settings" -l force -d "Bypass confirmation"

# history subcommands
complete -c faster-whisper-hotkey -n "__fish_seen_subcommand_from history" -x -a "view clear export delete"
complete -c faster-whisper-hotkey -n "__fish_seen_subcommand_from history" -l limit -d "Limit number of entries" -x
complete -c faster-whisper-hotkey -n "__fish_seen_subcommand_from history" -l output -d "Output file" -r
complete -c faster-whisper-hotkey -n "__fish_seen_subcommand_from history" -l force -d "Bypass confirmation"

# batch options
complete -c faster-whisper-hotkey -n "__fish_seen_subcommand_from batch" -l output -d "Output file" -r
complete -c faster-whisper-hotkey -n "__fish_seen_subcommand_from batch" -l extensions -d "File extensions"
complete -c faster-whisper-hotkey -n "__fish_seen_subcommand_from batch" -l workers -d "Number of workers" -x
complete -c faster-whisper-hotkey -n "__fish_seen_subcommand_from batch" -l device -d "Compute device" -x -a "cuda cpu"
complete -c faster-whisper-hotkey -n "__fish_seen_subcommand_from batch" -l model -d "Model name"
complete -c faster-whisper-hotkey -n "__fish_seen_subcommand_from batch" -l language -d "Language code" -x -a "en es fr de it pt ru ja zh auto"

# completion options
complete -c faster-whisper-hotkey -n "__fish_seen_subcommand_from completion" -l shell -d "Shell type" -x -a "bash zsh fish"
"""
        print(fish_completion)

    else:
        print_error(f"Unsupported shell: {shell}")
        return 1

    print()
    print_info(f"To install, save to appropriate location and source the file.")
    print_info(f"  bash: ~/.local/share/bash-completion/completions/faster-whisper-hotkey")
    print_info(f"  zsh:  ~/.zfunc/_faster-whisper-hotkey")
    print_info(f"  fish: ~/.config/fish/completions/faster-whisper-hotkey.fish")

    return 0


# -----------------------------------------------------------------------------
# Main entry point
# -----------------------------------------------------------------------------

def create_parser() -> argparse.ArgumentParser:
    """Create the main argument parser."""
    parser = argparse.ArgumentParser(
        prog="faster-whisper-hotkey",
        description="Push-to-talk transcription with hotkey activation.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  faster-whisper-hotkey record
  faster-whisper-hotkey transcribe audio.wav -o output.txt
  faster-whisper-hotkey settings list
  faster-whisper-hotkey history view
  faster-whisper-hotkey batch *.wav -o results.json
  faster-whisper-hotkey completion --shell bash > ~/.local/share/bash-completion/completions/faster-whisper-hotkey

For more help on each command:
  faster-whisper-hotkey COMMAND --help
        """,
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # record command
    record_parser = subparsers.add_parser(
        "record",
        help="Start real-time recording with hotkey activation",
        description="Start real-time audio recording with hotkey-activated transcription.",
    )
    record_parser.add_argument("--device", choices=["cuda", "cpu"], help="Compute device")
    record_parser.add_argument("--model", help="Model name")
    record_parser.add_argument("--language", help="Language code (e.g., en, es, auto)")
    record_parser.add_argument("--hotkey", help="Hotkey combination (e.g., pause, ctrl+shift+h)")
    record_parser.add_argument(
        "--hold", action="store_true", help="Use hold activation mode (default)"
    )
    record_parser.add_argument(
        "--toggle", action="store_true", help="Use toggle activation mode"
    )
    record_parser.set_defaults(func=cmd_record)

    # transcribe command
    transcribe_parser = subparsers.add_parser(
        "transcribe",
        help="Transcribe audio file(s)",
        description="Transcribe one or more audio files and output the text.",
    )
    transcribe_parser.add_argument(
        "files", nargs="*", type=Path, help="Audio file(s) to transcribe"
    )
    transcribe_parser.add_argument(
        "-o", "--output", help="Output file or directory for transcription results"
    )
    transcribe_parser.add_argument(
        "-i", "--input-dir", help="Input directory containing audio files"
    )
    transcribe_parser.add_argument(
        "-e", "--extensions", default="wav,mp3,flac,ogg,m4a",
        help="File extensions to process (comma-separated)"
    )
    transcribe_parser.add_argument(
        "--summary", help="Save summary JSON to file"
    )
    transcribe_parser.add_argument("--device", choices=["cuda", "cpu"], help="Compute device")
    transcribe_parser.add_argument("--model", help="Model name")
    transcribe_parser.add_argument("--language", help="Language code")
    transcribe_parser.set_defaults(func=cmd_transcribe)

    # settings command
    settings_parser = subparsers.add_parser(
        "settings",
        help="Manage configuration settings",
        description="View or modify configuration settings.",
    )
    settings_parser.add_argument(
        "action", choices=["list", "get", "set", "reset"],
        help="Action to perform"
    )
    settings_parser.add_argument("key", nargs="?", help="Setting key (for get/set)")
    settings_parser.add_argument("value", nargs="?", help="Setting value (for set)")
    settings_parser.add_argument("--json", action="store_true", help="Output as JSON")
    settings_parser.add_argument("--force", "-f", action="store_true", help="Bypass confirmation")
    settings_parser.set_defaults(func=cmd_settings)

    # history command
    history_parser = subparsers.add_parser(
        "history",
        help="View and manage transcription history",
        description="View, export, or clear transcription history.",
    )
    history_parser.add_argument(
        "action", choices=["view", "clear", "export", "delete"],
        help="Action to perform"
    )
    history_parser.add_argument("--limit", "-n", type=int, help="Limit number of entries")
    history_parser.add_argument(
        "-o", "--output", help="Output file (for export)"
    )
    history_parser.add_argument(
        "indices", nargs="*", type=int,
        help="Entry indices to delete (1-based, from newest)"
    )
    history_parser.add_argument("--force", "-f", action="store_true", help="Bypass confirmation")
    history_parser.set_defaults(func=cmd_history)

    # batch command
    batch_parser = subparsers.add_parser(
        "batch",
        help="Batch process multiple audio files",
        description="Process multiple audio files in parallel.",
    )
    batch_parser.add_argument(
        "patterns", nargs="+", help="File patterns or directories"
    )
    batch_parser.add_argument(
        "-o", "--output", help="Output JSON file for results"
    )
    batch_parser.add_argument(
        "-e", "--extensions", help="File extensions to process (comma-separated)"
    )
    batch_parser.add_argument(
        "-j", "--workers", type=int, help="Number of parallel workers"
    )
    batch_parser.add_argument("--device", choices=["cuda", "cpu"], help="Compute device")
    batch_parser.add_argument("--model", help="Model name")
    batch_parser.add_argument("--language", help="Language code")
    batch_parser.set_defaults(func=cmd_batch)

    # wizard command
    wizard_parser = subparsers.add_parser(
        "wizard",
        help="Run interactive settings wizard",
        description="Launch the interactive configuration wizard.",
    )
    wizard_parser.set_defaults(func=cmd_wizard)

    # devices command
    devices_parser = subparsers.add_parser(
        "devices",
        help="List available audio devices",
        description="List all available audio input devices.",
    )
    devices_parser.set_defaults(func=cmd_devices)

    # models command
    models_parser = subparsers.add_parser(
        "models",
        help="List available models",
        description="List all available ASR models.",
    )
    models_parser.add_argument(
        "--model-type", choices=["whisper", "canary", "parakeet", "voxtral", "all"],
        default="all", help="Filter by model type"
    )
    models_parser.set_defaults(func=cmd_models)

    # languages command
    languages_parser = subparsers.add_parser(
        "languages",
        help="List supported languages",
        description="List all supported language codes.",
    )
    languages_parser.add_argument(
        "--model-type", choices=["whisper", "canary", "all"],
        default="all", help="Filter by model type"
    )
    languages_parser.set_defaults(func=cmd_languages)

    # completion command
    completion_parser = subparsers.add_parser(
        "completion",
        help="Generate shell completion script",
        description="Generate shell completion script for bash, zsh, or fish.",
    )
    completion_parser.add_argument(
        "--shell", choices=["bash", "zsh", "fish"],
        required=True, help="Shell type"
    )
    completion_parser.set_defaults(func=cmd_completion)

    return parser


def setup_logging(verbose: bool = False):
    """Configure logging."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def main(argv: Optional[list] = None, standalone: bool = True) -> int:
    """Main CLI entry point.

    Args:
        argv: Command line arguments (defaults to sys.argv[1:])
        standalone: If True, handle SystemExit and print errors

    Returns:
        Exit code
    """
    parser = create_parser()

    # Parse args
    if argv is None:
        argv = sys.argv[1:]

    args = parser.parse_args(argv)

    # Setup logging
    verbose = getattr(args, "verbose", False)
    setup_logging(verbose)

    # Show help if no command
    if not args.command:
        parser.print_help()
        return 0

    # Run command
    try:
        return args.func(args)
    except KeyboardInterrupt:
        print_info("\nInterrupted.")
        return 130
    except Exception as e:
        if standalone:
            print_error(f"Error: {e}")
            logger.exception("Command error")
            return 1
        else:
            raise


if __name__ == "__main__":
    sys.exit(main())
