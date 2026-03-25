#!/usr/bin/env python3
"""
Test validation script - verifies hotspot test files are properly structured.
"""

import ast
import sys
from pathlib import Path


def validate_test_file(file_path: Path) -> dict:
    """Validate a test file structure."""
    with open(file_path, "r") as f:
        content = f.read()

    try:
        tree = ast.parse(content)
    except SyntaxError as e:
        return {"valid": False, "error": f"Syntax error: {e}", "test_count": 0, "class_count": 0}

    test_functions = []
    test_classes = []

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            if node.name.startswith("test_"):
                test_functions.append(node.name)
        elif isinstance(node, ast.ClassDef):
            if node.name.startswith("Test"):
                test_classes.append(node.name)

    return {
        "valid": True,
        "test_count": len(test_functions),
        "class_count": len(test_classes),
        "test_functions": test_functions[:5],  # First 5
        "test_classes": test_classes[:5],  # First 5
    }


def main():
    backend_dir = Path(__file__).parent
    test_files = [
        backend_dir / "tests" / "test_hotspot_transcription_pipeline.py",
        backend_dir / "tests" / "test_hotspot_model_loading.py",
    ]

    print("🧪 Validating Hotspot Test Suite\n")
    print("=" * 60)

    total_tests = 0
    total_classes = 0
    all_valid = True

    for test_file in test_files:
        if not test_file.exists():
            print(f"\n❌ {test_file.name}")
            print(f"   File not found!")
            all_valid = False
            continue

        result = validate_test_file(test_file)

        if result["valid"]:
            print(f"\n✅ {test_file.name}")
            print(f"   Test classes: {result['class_count']}")
            print(f"   Test functions: {result['test_count']}")

            if result["test_classes"]:
                print(f"   Sample classes: {', '.join(result['test_classes'])}")

            if result["test_functions"]:
                print(f"   Sample tests: {', '.join(result['test_functions'])}")

            total_tests += result["test_count"]
            total_classes += result["class_count"]
        else:
            print(f"\n❌ {test_file.name}")
            print(f"   {result['error']}")
            all_valid = False

    print("\n" + "=" * 60)
    print(f"\n📊 Summary:")
    print(f"   Total test classes: {total_classes}")
    print(f"   Total test functions: {total_tests}")

    if all_valid:
        print(f"\n✅ All test files are valid and ready to run!")
        print(f"\n🚀 Run tests with:")
        print(f"   cd backend")
        print(f"   uv run pytest tests/test_hotspot_*.py -v")
        return 0
    else:
        print(f"\n❌ Some test files have errors")
        return 1


if __name__ == "__main__":
    sys.exit(main())
