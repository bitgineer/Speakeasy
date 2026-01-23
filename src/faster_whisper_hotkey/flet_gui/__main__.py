"""
Main entry point for the Flet GUI application.

This module provides the command-line entry point for launching the
faster-whisper-hotkey Flet GUI application.
"""

import logging
import sys

import flet as ft

from .app import FletApp
from ..settings import load_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    """Main entry point for the Flet GUI application."""
    logger.info("Starting faster-whisper-hotkey Flet GUI...")

    # Check if settings exist
    settings = load_settings()
    if settings is None:
        logger.warning(
            "No settings found. Please run 'faster-whisper-hotkey' first "
            "to complete initial setup."
        )
        print("\n" + "=" * 60)
        print("  faster-whisper-hotkey - Initial Setup Required")
        print("=" * 60)
        print("\nNo settings file found.")
        print("Please run the main application first to complete setup:")
        print("  faster-whisper-hotkey")
        print("\nOr launch the GUI with onboarding:")
        print("  faster-whisper-hotkey-gui")
        print("\n" + "=" * 60 + "\n")
        sys.exit(1)

    # Create the Flet app
    app = FletApp()

    def run_app(page: ft.Page):
        """Build and run the app on the given page."""
        try:
            app.build(page)
        except Exception as e:
            logger.error(f"Failed to build Flet app: {e}", exc_info=True)
            page.clean()
            page.add(
                ft.Column(
                    [
                        ft.Icon(ft.icons.ERROR_outline, size=48, color=ft.colors.ERROR),
                        ft.Text("Failed to start application", size=20, weight=ft.FontWeight.BOLD),
                        ft.Text(str(e), color=ft.colors.ON_SURFACE_VARIANT),
                        ft.ElevatedButton(
                            "Close",
                            on_click=lambda _: page.window_close(),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAlignment.CENTER,
                    spacing=16,
                )
            )

    # Run the Flet app
    try:
        ft.app(target=run_app)
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
    except Exception as e:
        logger.error(f"Application error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        app.shutdown()


if __name__ == "__main__":
    main()
