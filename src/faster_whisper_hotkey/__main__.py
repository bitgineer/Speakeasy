"""
Entry point for the faster-whisper-hotkey module.

This module provides the entry point when the package is run as a Python module
(`python -m faster_whisper_hotkey`). For backward compatibility, running without
any arguments launches the interactive wizard.

Functions
---------
main
    Main entry point that dispatches to CLI or wizard.

Notes
-----
When invoked with no arguments, automatically runs the wizard subcommand
for backward compatibility with earlier versions.
"""

import sys
from faster_whisper_hotkey.cli import main as cli_main

# For backward compatibility: if no args provided, run wizard
def main():
    """Main entry point that dispatches to CLI or wizard."""
    if len(sys.argv) <= 1:
        # No arguments: run the interactive wizard (backward compatible)
        sys.argv.insert(1, "wizard")
    return cli_main()

if __name__ == "__main__":
    sys.exit(main())
