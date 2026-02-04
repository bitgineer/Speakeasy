"""
SpeakEasy Backend - Entry point.

Run with: python -m speakeasy
"""

import argparse
import logging
import sys


def setup_logging(verbose: bool = False) -> None:
    """Configure logging."""
    level = logging.DEBUG if verbose else logging.INFO

    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
    )

    # Reduce noise from libraries
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    # Suppress noisy NeMo/ML library logs (only show errors)
    logging.getLogger("nemo").setLevel(logging.ERROR)
    logging.getLogger("nemo_logger").setLevel(logging.ERROR)
    logging.getLogger("nv_one_logger").setLevel(logging.ERROR)
    logging.getLogger("numexpr").setLevel(logging.WARNING)
    logging.getLogger("pytorch_lightning").setLevel(logging.WARNING)
    logging.getLogger("transformers").setLevel(logging.WARNING)
    logging.getLogger("filelock").setLevel(logging.WARNING)

    # Also set the NeMo internal logging filter
    import os

    os.environ.setdefault("NEMO_LOG_LEVEL", "ERROR")


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="SpeakEasy - Open Source Voice Transcription Backend",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host to bind to (default: 127.0.0.1)",
    )

    parser.add_argument(
        "--port",
        type=int,
        default=8765,
        help="Port to bind to (default: 8765)",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    parser.add_argument(
        "--version",
        action="version",
        version="SpeakEasy Backend v0.1.0",
    )

    args = parser.parse_args()

    setup_logging(verbose=args.verbose)

    logger = logging.getLogger(__name__)
    logger.info(f"Starting SpeakEasy backend on {args.host}:{args.port}")

    try:
        from .server import run

        run(host=args.host, port=args.port)
        return 0

    except KeyboardInterrupt:
        logger.info("Shutting down...")
        return 0

    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
