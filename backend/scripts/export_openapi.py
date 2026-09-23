"""Write or verify the committed OpenAPI schema.

Usage:
    python scripts/export_openapi.py
    python scripts/export_openapi.py --check
"""

import argparse
import sys
from pathlib import Path


def main() -> int:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from speakeasy import openapi_export

    parser = argparse.ArgumentParser(description="Export the SpeakEasy OpenAPI schema.")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit nonzero instead of writing when the committed schema is out of date.",
    )
    args = parser.parse_args()

    if args.check:
        return 0 if openapi_export.check() else 1

    path = openapi_export.write()
    print(f"Wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
