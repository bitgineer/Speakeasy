#!/usr/bin/env python3
"""
Stability test runner for faster-whisper-hotkey.

This script runs comprehensive stability and reliability tests to verify
the application can handle extended use, rapid operations, and edge cases.

Usage:
    python run_stability_tests.py                    # Run quick smoke tests
    python run_stability_tests.py --full             # Run full test suite
    python run_stability_tests.py --rapid 500        # Run 500 rapid cycles
    python run_stability_tests.py --duration 3600    # Run 1-hour stability test
    python run_stability_tests.py --memory-only      # Run memory leak tests only

Environment Variables:
    STRESS_RAPID_COUNT          - Number of rapid transcription cycles (default: 100)
    STRESS_RECORDING_SECONDS    - Long recording duration in seconds (default: 300)
    STRESS_STABILITY_SECONDS    - Stability test duration in seconds (default: 60)
    STRESS_MEMORY_ITERATIONS    - Memory leak test iterations (default: 50)
"""

import argparse
import os
import sys
import time
import json
import logging
from datetime import datetime
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('stability_test.log')
    ]
)
logger = logging.getLogger(__name__)


def run_pytest(test_args: list) -> dict:
    """Run pytest with specified arguments and return results."""
    import subprocess

    cmd = [sys.executable, "-m", "pytest"] + test_args
    logger.info(f"Running: {' '.join(cmd)}")

    start_time = time.time()
    result = subprocess.run(cmd, capture_output=True, text=True)
    elapsed = time.time() - start_time

    return {
        "command": " ".join(cmd),
        "elapsed_seconds": elapsed,
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "success": result.returncode == 0,
    }


def parse_output_for_stats(output: str) -> dict:
    """Parse pytest output for test statistics."""
    stats = {
        "total": 0,
        "passed": 0,
        "failed": 0,
        "skipped": 0,
        "errors": 0,
    }

    lines = output.split('\n')
    for line in lines:
        if ' passed' in line or ' failed' in line:
            # Parse pytest summary line
            parts = line.split()
            for i, part in enumerate(parts):
                if 'passed' in part:
                    stats["passed"] = int(parts[i-1]) if i > 0 else 0
                elif 'failed' in part:
                    stats["failed"] = int(parts[i-1]) if i > 0 else 0
                elif 'skipped' in part:
                    stats["skipped"] = int(parts[i-1]) if i > 0 else 0
                elif 'error' in part:
                    stats["errors"] = int(parts[i-1]) if i > 0 else 0

    stats["total"] = stats["passed"] + stats["failed"] + stats["skipped"] + stats["errors"]
    return stats


def run_quick_smoke_test() -> dict:
    """Run quick smoke tests (~2 minutes)."""
    logger.info("=" * 60)
    logger.info("Running Quick Smoke Test Suite")
    logger.info("=" * 60)

    test_args = [
        "tests/stress/test_stability.py",
        "-v",
        "-m", "stress",
        "-k", "test_rapid_transcription_10_cycles or test_concurrent",
        "--tb=short",
    ]

    return run_pytest(test_args)


def run_rapid_transcription_test(cycles: int = 100) -> dict:
    """Run rapid transcription test."""
    logger.info("=" * 60)
    logger.info(f"Running Rapid Transcription Test ({cycles} cycles)")
    logger.info("=" * 60)

    os.environ["STRESS_RAPID_COUNT"] = str(cycles)

    test_args = [
        "tests/stress/test_stability.py::TestRapidTranscription::test_rapid_transcription_100_cycles",
        "-v",
        "-s",
        "--tb=short",
    ]

    return run_pytest(test_args)


def run_memory_leak_test(iterations: int = 50) -> dict:
    """Run memory leak detection tests."""
    logger.info("=" * 60)
    logger.info(f"Running Memory Leak Detection Test ({iterations} iterations)")
    logger.info("=" * 60)

    os.environ["STRESS_MEMORY_ITERATIONS"] = str(iterations)

    test_args = [
        "tests/stress/test_stability.py::TestMemoryLeaks",
        "-v",
        "-s",
        "--tb=short",
    ]

    return run_pytest(test_args)


def run_long_recording_test(duration_seconds: int = 300) -> dict:
    """Run long recording transcription test."""
    logger.info("=" * 60)
    logger.info(f"Running Long Recording Test ({duration_seconds} seconds)")
    logger.info("=" * 60)

    os.environ["STRESS_RECORDING_SECONDS"] = str(duration_seconds)

    test_args = [
        "tests/stress/test_stability.py::TestLongRecordings::test_long_audio_transcription",
        "-v",
        "-s",
        "--tb=short",
    ]

    return run_pytest(test_args)


def run_stability_test(duration_seconds: int = 3600) -> dict:
    """Run extended stability test."""
    logger.info("=" * 60)
    logger.info(f"Running Extended Stability Test ({duration_seconds} seconds)")
    logger.info("=" * 60)

    os.environ["STRESS_STABILITY_SECONDS"] = str(duration_seconds)

    test_args = [
        "tests/stress/test_stability.py::TestStability::test_stability_extended_operation",
        "-v",
        "-s",
        "--tb=short",
    ]

    return run_pytest(test_args)


def run_full_suite() -> dict:
    """Run complete stability test suite."""
    logger.info("=" * 60)
    logger.info("Running Full Stability Test Suite")
    logger.info("=" * 60)

    test_args = [
        "tests/stress/test_stability.py",
        "-v",
        "-m", "stress",
        "--tb=short",
    ]

    return run_pytest(test_args)


def save_report(results: dict, output_path: str = None):
    """Save test results to a JSON report file."""
    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"stability_report_{timestamp}.json"

    report = {
        "timestamp": datetime.now().isoformat(),
        "results": results,
        "summary": {
            "total_tests_run": sum(r.get("stats", {}).get("total", 0) for r in results.values()),
            "total_passed": sum(r.get("stats", {}).get("passed", 0) for r in results.values()),
            "total_failed": sum(r.get("stats", {}).get("failed", 0) for r in results.values()),
            "total_duration_seconds": sum(r.get("elapsed_seconds", 0) for r in results.values()),
            "all_passed": all(r.get("success", False) for r in results.values()),
        }
    }

    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)

    logger.info(f"Report saved to: {output_path}")
    return output_path


def main():
    parser = argparse.ArgumentParser(
        description="Run stability and reliability tests for faster-whisper-hotkey"
    )
    parser.add_argument(
        "--full", "-f",
        action="store_true",
        help="Run full stability test suite"
    )
    parser.add_argument(
        "--rapid", "-r",
        type=int,
        metavar="COUNT",
        help="Run rapid transcription test with COUNT cycles"
    )
    parser.add_argument(
        "--memory", "-m",
        type=int,
        metavar="ITERATIONS",
        help="Run memory leak test with ITERATIONS cycles"
    )
    parser.add_argument(
        "--memory-only",
        action="store_true",
        help="Run only memory leak tests"
    )
    parser.add_argument(
        "--duration", "-d",
        type=int,
        metavar="SECONDS",
        help="Run stability test for SECONDS duration"
    )
    parser.add_argument(
        "--long-recording",
        type=int,
        metavar="SECONDS",
        help="Run long recording test with SECONDS duration"
    )
    parser.add_argument(
        "--quick", "-q",
        action="store_true",
        help="Run quick smoke tests (default if no other option specified)"
    )
    parser.add_argument(
        "--output", "-o",
        metavar="FILE",
        help="Save report to FILE (default: stability_report_TIMESTAMP.json)"
    )
    parser.add_argument(
        "--no-report",
        action="store_true",
        help="Don't save JSON report file"
    )

    args = parser.parse_args()

    # Default to quick test if no other option specified
    run_quick = args.quick or not any([
        args.full, args.rapid, args.memory, args.duration,
        args.long_recording, args.memory_only
    ])

    results = {}
    start_time = time.time()

    try:
        if args.full:
            result = run_full_suite()
            result["stats"] = parse_output_for_stats(result["stdout"])
            results["full_suite"] = result

        if args.memory_only or args.memory:
            iterations = args.memory or 50
            result = run_memory_leak_test(iterations)
            result["stats"] = parse_output_for_stats(result["stdout"])
            results["memory_leak"] = result

            if args.memory_only:
                # If only memory tests, skip others
                pass

        if args.rapid:
            result = run_rapid_transcription_test(args.rapid)
            result["stats"] = parse_output_for_stats(result["stdout"])
            results["rapid_transcription"] = result

        if args.duration:
            result = run_stability_test(args.duration)
            result["stats"] = parse_output_for_stats(result["stdout"])
            results["stability"] = result

        if args.long_recording:
            result = run_long_recording_test(args.long_recording)
            result["stats"] = parse_output_for_stats(result["stdout"])
            results["long_recording"] = result

        if run_quick and not results:
            result = run_quick_smoke_test()
            result["stats"] = parse_output_for_stats(result["stdout"])
            results["quick_smoke"] = result

    except KeyboardInterrupt:
        logger.warning("\nTest run interrupted by user")
        return 1

    total_elapsed = time.time() - start_time

    # Print summary
    logger.info("=" * 60)
    logger.info("STABILITY TEST SUMMARY")
    logger.info("=" * 60)

    for test_name, result in results.items():
        stats = result.get("stats", {})
        status = "PASSED" if result.get("success") else "FAILED"
        logger.info(f"{test_name}: {status}")
        logger.info(f"  Duration: {result.get('elapsed_seconds', 0):.1f}s")
        if stats:
            logger.info(f"  Tests: {stats.get('passed', 0)} passed, "
                       f"{stats.get('failed', 0)} failed")

    logger.info(f"\nTotal duration: {total_elapsed:.1f}s")

    # Save report
    if not args.no_report and results:
        save_report(results, args.output)

    # Return exit code
    all_passed = all(r.get("success", False) for r in results.values())
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
