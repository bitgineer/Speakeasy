#!/usr/bin/env python3
"""
Cross-Configuration Test Runner for faster-whisper-hotkey

This script provides an interactive menu for running manual cross-configuration
tests on different Windows versions, hardware configurations, and audio devices.

Usage:
    python scripts/cross_config_test.py
"""

import os
import sys
import platform
import subprocess
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


class SystemInfoCollector:
    """Collects system information for test reporting."""

    @staticmethod
    def get_windows_version() -> Dict[str, str]:
        """Get detailed Windows version information."""
        info = {
            "platform": platform.platform(),
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
        }

        # Try to get edition and build using wmic
        try:
            result = subprocess.run(
                ["wmic", "os", "get", "Caption,BuildNumber,OSArchitecture", "/format:list"],
                capture_output=True,
                text=True,
                timeout=10
            )
            output = result.stdout
            for line in output.split('\n'):
                if '=' in line:
                    key, value = line.split('=', 1)
                    info[key.strip().lower()] = value.strip()
        except Exception as e:
            info["wmic_error"] = str(e)

        return info

    @staticmethod
    def get_gpu_info() -> List[Dict[str, str]]:
        """Get GPU information using wmic."""
        gpus = []

        try:
            result = subprocess.run(
                ["wmic", "path", "win32_VideoController", "get", "name,AdapterRAM,DriverVersion", "/format:list"],
                capture_output=True,
                text=True,
                timeout=10
            )
            output = result.stdout

            current_gpu = {}
            for line in output.split('\n'):
                line = line.strip()
                if not line:
                    if current_gpu:
                        gpus.append(current_gpu)
                        current_gpu = {}
                    continue

                if '=' in line:
                    key, value = line.split('=', 1)
                    current_gpu[key.strip().lower()] = value.strip()

            if current_gpu:
                gpus.append(current_gpu)

        except Exception as e:
            gpus.append({"error": str(e)})

        return gpus

    @staticmethod
    def get_cpu_info() -> Dict[str, str]:
        """Get CPU information."""
        info = {
            "processor": platform.processor(),
            "machine": platform.machine(),
        }

        try:
            result = subprocess.run(
                ["wmic", "cpu", "get", "Name,NumberOfCores,NumberOfLogicalProcessors,MaxClockSpeed", "/format:list"],
                capture_output=True,
                text=True,
                timeout=10
            )
            output = result.stdout
            for line in output.split('\n'):
                if '=' in line:
                    key, value = line.split('=', 1)
                    info[key.strip().lower()] = value.strip()
        except Exception as e:
            info["wmic_error"] = str(e)

        return info

    @staticmethod
    def get_ram_info() -> Dict[str, str]:
        """Get RAM information."""
        info = {}

        try:
            result = subprocess.run(
                ["wmic", "memorychip", "get", "Capacity", "/format:list"],
                capture_output=True,
                text=True,
                timeout=10
            )
            output = result.stdout
            capacities = []
            for line in output.split('\n'):
                line = line.strip()
                if line and line.isdigit():
                    capacities.append(int(line) // (1024 * 1024 * 1024))

            if capacities:
                info["sticks"] = str(len(capacities))
                info["per_stick_gb"] = str(capacities[0])
                info["total_gb"] = str(sum(capacities))

        except Exception as e:
            info["error"] = str(e)

        return info

    @staticmethod
    def get_audio_devices() -> List[str]:
        """Get list of audio input devices."""
        devices = []

        try:
            # Try using PowerShell to get audio devices
            ps_cmd = """
            Add-Type -AssemblyName System.Runtime.WindowsRuntime
            $asTaskGeneric = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object { $_.ToString() -eq 'AsTask`1' -and $_.IsGenericMethod -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' })[0]
            $asTask = $asTaskGeneric.MakeGenericMethod([Windows.Media.Devices.DeviceInformationCollection])
            [Windows.Media.Capture.MediaCapture, Windows.Media.Capture.MediaCaptureContract, ContentType = WindowsRuntime] | Out-Null
            $capture = New-Object Windows.Media.Capture.MediaCapture
            $task = $asTask.Invoke($null, @([Windows.Media.Capture.MediaCapture]::FindAllAsync([Windows.Media.Devices.DeviceClass]::AudioCapture)))
            $task.AsTask().Wait() | Out-Null
            $devices = $task.AsTask().Result
            $devices | ForEach-Object { Write-Output $_.Name }
            """
            result = subprocess.run(
                ["powershell", "-Command", ps_cmd],
                capture_output=True,
                text=True,
                timeout=15
            )
            devices = [d.strip() for d in result.stdout.split('\n') if d.strip()]

        except Exception as e:
            devices = [f"Error: {e}"]

        return devices

    @staticmethod
    def collect_all() -> Dict:
        """Collect all system information."""
        return {
            "timestamp": datetime.now().isoformat(),
            "windows": SystemInfoCollector.get_windows_version(),
            "cpu": SystemInfoCollector.get_cpu_info(),
            "gpu": SystemInfoCollector.get_gpu_info(),
            "ram": SystemInfoCollector.get_ram_info(),
            "audio_devices": SystemInfoCollector.get_audio_devices(),
        }


class CrossConfigTestRunner:
    """Interactive test runner for cross-configuration testing."""

    def __init__(self):
        self.results = []
        self.current_test = None
        self.system_info = None

    def print_header(self, title: str):
        """Print a section header."""
        print("\n" + "=" * 60)
        print(f"  {title}")
        print("=" * 60)

    def print_section(self, title: str):
        """Print a subsection header."""
        print("\n" + "-" * 40)
        print(f"  {title}")
        print("-" * 40)

    def collect_system_info(self):
        """Collect and display system information."""
        self.print_header("SYSTEM INFORMATION COLLECTION")
        self.system_info = SystemInfoCollector.collect_all()

        print("\nWindows Information:")
        for key, value in self.system_info["windows"].items():
            if value:
                print(f"  {key}: {value}")

        print("\nCPU Information:")
        for key, value in self.system_info["cpu"].items():
            if value:
                print(f"  {key}: {value}")

        print("\nGPU Information:")
        for i, gpu in enumerate(self.system_info["gpu"], 1):
            print(f"  GPU {i}:")
            for key, value in gpu.items():
                if value:
                    print(f"    {key}: {value}")

        print("\nRAM Information:")
        for key, value in self.system_info["ram"].items():
            if value:
                print(f"  {key}: {value}")

        print("\nAudio Devices:")
        for i, device in enumerate(self.system_info["audio_devices"], 1):
            print(f"  {i}. {device}")

        print("\n\nIs this information correct? (Press Enter to continue)")

    def run_quick_smoke_test(self):
        """Run the quick smoke test suite."""
        self.print_section("QUICK SMOKE TEST (15 minutes)")

        tests = [
            ("Application launches", self._test_launch),
            ("Settings can be opened", self._test_settings_open),
            ("Hardware is detected correctly", self._test_hardware_detection),
            ("Model can be downloaded/loaded", self._test_model_load),
            ("Recording works", self._test_recording),
            ("Transcription completes", self._test_transcription),
            ("Text is pasted correctly", self._test_paste),
        ]

        results = {}
        for test_name, test_func in tests:
            print(f"\n[?] Test: {test_name}")
            result = input("    Result (p=pass, f=fail, s=skip): ").strip().lower()
            results[test_name] = {"status": result, "notes": ""}

            if result == 'f':
                notes = input("    Notes (what failed): ")
                results[test_name]["notes"] = notes

        self.results.append({"suite": "quick_smoke", "tests": results})
        self._print_summary(results)

    def run_standard_test(self):
        """Run the standard test suite."""
        self.print_section("STANDARD TEST (30 minutes)")

        tests = [
            # Quick smoke tests first
            ("Application launches", self._test_launch),
            ("Settings can be opened", self._test_settings_open),
            ("Hardware is detected correctly", self._test_hardware_detection),
            ("Model can be downloaded/loaded", self._test_model_load),
            ("Recording works", self._test_recording),
            ("Transcription completes", self._test_transcription),
            ("Text is pasted correctly", self._test_paste),
            # Standard tests
            ("Settings persist after restart", self._test_settings_persist),
            ("Multiple consecutive transcriptions work", self._test_multiple_transcriptions),
            ("Hotkey can be changed", self._test_hotkey_change),
            ("Audio device can be changed", self._test_audio_device_change),
            ("History panel opens and shows entries", self._test_history),
            ("System tray icon menu works", self._test_tray),
            ("Application exits cleanly", self._test_clean_exit),
        ]

        results = {}
        for test_name, test_func in tests:
            print(f"\n[?] Test: {test_name}")
            result = input("    Result (p=pass, f=fail, s=skip): ").strip().lower()
            results[test_name] = {"status": result, "notes": ""}

            if result == 'f':
                notes = input("    Notes (what failed): ")
                results[test_name]["notes"] = notes

        self.results.append({"suite": "standard", "tests": results})
        self._print_summary(results)

    def run_comprehensive_test(self):
        """Run the comprehensive test suite."""
        self.print_section("COMPREHENSIVE TEST (1-2 hours)")

        tests = [
            # All standard tests
            ("Application launches", self._test_launch),
            ("Settings can be opened", self._test_settings_open),
            ("Hardware is detected correctly", self._test_hardware_detection),
            ("Model can be downloaded/loaded", self._test_model_load),
            ("Recording works", self._test_recording),
            ("Transcription completes", self._test_transcription),
            ("Text is pasted correctly", self._test_paste),
            ("Settings persist after restart", self._test_settings_persist),
            ("Multiple consecutive transcriptions work", self._test_multiple_transcriptions),
            ("Hotkey can be changed", self._test_hotkey_change),
            ("Audio device can be changed", self._test_audio_device_change),
            ("History panel opens and shows entries", self._test_history),
            ("System tray icon menu works", self._test_tray),
            ("Application exits cleanly", self._test_clean_exit),
            # Comprehensive tests
            ("Each model type loads correctly", self._test_all_models),
            ("Each compute type works", self._test_compute_types),
            ("Clipboard backup/restore works", self._test_clipboard),
            ("Text processing features work", self._test_text_processing),
            ("Paste rules work for different apps", self._test_paste_rules),
            ("Memory usage is stable over time", self._test_memory_stability),
            ("No errors in logs", self._test_logs),
            ("Application survives suspend/resume", self._test_suspend_resume),
        ]

        results = {}
        for test_name, test_func in tests:
            print(f"\n[?] Test: {test_name}")
            result = input("    Result (p=pass, f=fail, s=skip): ").strip().lower()
            results[test_name] = {"status": result, "notes": ""}

            if result == 'f':
                notes = input("    Notes (what failed): ")
                results[test_name]["notes"] = notes

        self.results.append({"suite": "comprehensive", "tests": results})
        self._print_summary(results)

    def run_gpu_specific_test(self):
        """Run GPU-specific tests."""
        self.print_section("GPU-SPECIFIC TESTS")

        if not self.system_info["gpu"]:
            print("\nNo GPU detected. Skipping GPU tests.")
            return

        tests = [
            ("GPU is correctly identified", None),
            ("VRAM amount is correct", None),
            ("CUDA is available", None),
            ("Transcription works with CUDA", None),
            ("float16 compute type works", None),
            ("int8_float16 compute type works", None),
            ("int8 compute type works", None),
            ("No VRAM leaks after transcription", None),
            ("Recommended model for VRAM tier works", None),
        ]

        results = {}
        for test_name in tests:
            print(f"\n[?] Test: {test_name[0]}")
            result = input("    Result (p=pass, f=fail, s=skip): ").strip().lower()
            results[test_name[0]] = {"status": result, "notes": ""}

            if result == 'f':
                notes = input("    Notes (what failed): ")
                results[test_name[0]]["notes"] = notes

        self.results.append({"suite": "gpu_specific", "tests": results})
        self._print_summary(results)

    def run_audio_device_test(self):
        """Run audio device tests."""
        self.print_section("AUDIO DEVICE TESTS")

        print("\nAvailable audio devices:")
        for i, device in enumerate(self.system_info["audio_devices"], 1):
            print(f"  {i}. {device}")

        tests = [
            ("Default audio device records correctly", None),
            ("Audio level indicator moves during recording", None),
            ("No clipping/distortion in recording", None),
            ("USB microphone works (if present)", None),
            ("Bluetooth headset works (if present)", None),
            ("Analog headset works (if present)", None),
            ("Device switching works correctly", None),
            ("Disconnect/reconnect handled gracefully", None),
        ]

        results = {}
        for test_name in tests:
            print(f"\n[?] Test: {test_name[0]}")
            result = input("    Result (p=pass, f=fail, s=skip, n=not applicable): ").strip().lower()
            results[test_name[0]] = {"status": result, "notes": ""}

            if result == 'f':
                notes = input("    Notes (what failed): ")
                results[test_name[0]]["notes"] = notes

        self.results.append({"suite": "audio_devices", "tests": results})
        self._print_summary(results)

    def run_paste_targets_test(self):
        """Run paste target application tests."""
        self.print_section("PASTE TARGET APPLICATION TESTS")

        print("\nYou will test pasting into various applications.")
        print("Keep this script open and switch between applications.")

        applications = [
            "Notepad",
            "Notepad++ (if installed)",
            "VS Code (editor)",
            "VS Code (terminal) - KNOWN ISSUE",
            "Windows Terminal / PowerShell",
            "Discord (if installed)",
            "Slack (if installed)",
            "Chrome/Firefox (address bar)",
            "Chrome/Firefox (text input in page)",
        ]

        results = {}
        for app in applications:
            print(f"\n[?] Test: Paste into {app}")
            print("    1. Switch to the application")
            print("    2. Focus on a text input area")
            print("    3. Press hotkey and speak")
            print("    4. Verify text appears")
            result = input("    Result (p=pass, f=fail, s=skip, n=not installed): ").strip().lower()
            results[app] = {"status": result, "notes": ""}

            if result == 'f':
                notes = input("    Notes (what failed): ")
                results[app]["notes"] = notes

        self.results.append({"suite": "paste_targets", "tests": results})
        self._print_summary(results)

    def _print_summary(self, results: dict):
        """Print test summary."""
        passed = sum(1 for v in results.values() if v["status"] == "p")
        failed = sum(1 for v in results.values() if v["status"] == "f")
        skipped = sum(1 for v in results.values() if v["status"] == "s")
        total = len(results)

        print("\n" + "-" * 40)
        print(f"Summary: {passed}/{total} passed, {failed} failed, {skipped} skipped")
        if failed > 0:
            print("\nFailed tests:")
            for test_name, result in results.items():
                if result["status"] == "f":
                    print(f"  - {test_name}: {result['notes']}")

    def save_results(self):
        """Save test results to a file."""
        self.print_header("SAVE RESULTS")

        filename = input(f"\nEnter filename (or press Enter for default): ").strip()
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"cross_config_test_{timestamp}.json"

        output_path = Path.cwd() / filename

        report = {
            "system_info": self.system_info,
            "test_results": self.results,
            "timestamp": datetime.now().isoformat(),
        }

        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"\nResults saved to: {output_path}")

    # Test instruction methods
    def _test_launch(self):
        print("\nInstructions:")
        print("  1. Launch faster-whisper-hotkey")
        print("  2. Verify the window appears")
        print("  3. Check for any error messages")

    def _test_settings_open(self):
        print("\nInstructions:")
        print("  1. Open Settings dialog")
        print("  2. Verify all settings categories are visible")

    def _test_hardware_detection(self):
        print("\nInstructions:")
        print("  1. Check Settings > Hardware/Device")
        print("  2. Verify GPU/CPU is detected correctly")
        print("  3. Verify recommended model is appropriate")

    def _test_model_load(self):
        print("\nInstructions:")
        print("  1. Select a model")
        print("  2. Wait for download/load to complete")
        print("  3. Verify success indicator")

    def _test_recording(self):
        print("\nInstructions:")
        print("  1. Press hotkey to start recording")
        print("  2. Verify recording indicator appears")
        print("  3. Check audio level indicator moves")
        print("  4. Release hotkey to stop")

    def _test_transcription(self):
        print("\nInstructions:")
        print("  1. Record a test phrase")
        print("  2. Wait for transcription to complete")
        print("  3. Verify text appears")

    def _test_paste(self):
        print("\nInstructions:")
        print("  1. Focus on Notepad (or other text editor)")
        print("  2. Record a test phrase")
        print("  3. Verify text is pasted correctly")

    def _test_settings_persist(self):
        print("\nInstructions:")
        print("  1. Change a setting")
        print("  2. Close and reopen the application")
        print("  3. Verify setting is preserved")

    def _test_multiple_transcriptions(self):
        print("\nInstructions:")
        print("  1. Perform 5 consecutive transcriptions")
        print("  2. Verify all complete successfully")

    def _test_hotkey_change(self):
        print("\nInstructions:")
        print("  1. Change the hotkey to a different key")
        print("  2. Test new hotkey works")
        print("  3. Change back to original")

    def _test_audio_device_change(self):
        print("\nInstructions:")
        print("  1. Change audio device in settings")
        print("  2. Test recording with new device")
        print("  3. Verify it works correctly")

    def _test_history(self):
        print("\nInstructions:")
        print("  1. Open History panel")
        print("  2. Verify previous transcriptions appear")
        print("  3. Test search/filter if available")

    def _test_tray(self):
        print("\nInstructions:")
        print("  1. Right-click system tray icon")
        print("  2. Verify menu options appear")
        print("  3. Test minimize/restore from tray")

    def _test_clean_exit(self):
        print("\nInstructions:")
        print("  1. Close the application")
        print("  2. Check task manager for lingering processes")
        print("  3. Verify clean exit")

    def _test_all_models(self):
        print("\nInstructions:")
        print("  1. Test each available model type")
        print("  2. For each: load, record, transcribe")
        print("  3. Note any failures")

    def _test_compute_types(self):
        print("\nInstructions:")
        print("  1. Test float16 (if GPU available)")
        print("  2. Test int8_float16")
        print("  3. Test int8")

    def _test_clipboard(self):
        print("\nInstructions:")
        print("  1. Copy text to clipboard")
        print("  2. Record transcription")
        print("  3. Verify clipboard behavior")

    def _test_text_processing(self):
        print("\nInstructions:")
        print("  1. Enable auto-punctuation")
        print("  2. Test filler word removal")
        print("  3. Test other text processing features")

    def _test_paste_rules(self):
        print("\nInstructions:")
        print("  1. Configure paste rules for different apps")
        print("  2. Test paste into each app type")
        print("  3. Verify correct paste method")

    def _test_memory_stability(self):
        print("\nInstructions:")
        print("  1. Open Task Manager")
        print("  2. Perform 10 transcriptions")
        print("  3. Check memory doesn't grow significantly")

    def _test_logs(self):
        print("\nInstructions:")
        print("  1. Check log file location")
        print("  2. Look for errors or warnings")
        print("  3. Report any critical issues")

    def _test_suspend_resume(self):
        print("\nInstructions:")
        print("  1. Start a recording")
        print("  2. Suspend computer (sleep)")
        print("  3. Resume and verify app still works")

    def run_menu(self):
        """Display main menu and handle user selection."""
        while True:
            self.print_header("CROSS-CONFIGURATION TEST RUNNER")
            print("\nMain Menu:")
            print("  1. Collect System Information")
            print("  2. Run Quick Smoke Test (15 min)")
            print("  3. Run Standard Test (30 min)")
            print("  4. Run Comprehensive Test (1-2 hours)")
            print("  5. Run GPU-Specific Tests")
            print("  6. Run Audio Device Tests")
            print("  7. Run Paste Target Tests")
            print("  8. Save Results")
            print("  9. View Current Results")
            print("  0. Exit")

            choice = input("\nSelect option: ").strip()

            if choice == "1":
                self.collect_system_info()
            elif choice == "2":
                self.run_quick_smoke_test()
            elif choice == "3":
                self.run_standard_test()
            elif choice == "4":
                self.run_comprehensive_test()
            elif choice == "5":
                self.run_gpu_specific_test()
            elif choice == "6":
                self.run_audio_device_test()
            elif choice == "7":
                self.run_paste_targets_test()
            elif choice == "8":
                self.save_results()
            elif choice == "9":
                self._view_results()
            elif choice == "0":
                print("\nExiting...")
                break
            else:
                print("\nInvalid selection. Please try again.")

            input("\nPress Enter to continue...")

    def _view_results(self):
        """View current test results."""
        if not self.results:
            print("\nNo test results yet.")
            return

        self.print_section("CURRENT RESULTS")
        for suite in self.results:
            print(f"\nSuite: {suite['suite']}")
            for test_name, result in suite['tests'].items():
                status_symbol = {"p": "[PASS]", "f": "[FAIL]", "s": "[SKIP]"}.get(result["status"], "[?]")
                print(f"  {status_symbol} {test_name}")
                if result.get("notes"):
                    print(f"        Notes: {result['notes']}")


def main():
    """Main entry point."""
    print("""
╔════════════════════════════════════════════════════════════╗
║     Cross-Configuration Test Runner                        ║
║     for faster-whisper-hotkey                               ║
╚════════════════════════════════════════════════════════════╝
    """)

    runner = CrossConfigTestRunner()

    try:
        runner.run_menu()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user.")
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
