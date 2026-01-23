#!/usr/bin/env python3
"""
Build script for faster-whisper-hotkey Windows distribution.

This script orchestrates the complete build process:
1. Cleans previous build artifacts
2. Generates the app icon
3. Builds the executable with PyInstaller
4. Packages the NSIS installer
5. Creates portable ZIP package
6. Generates checksums
7. Creates release notes

Usage:
    python scripts/build.py [options]

Options:
    --clean-only     Only clean build artifacts
    --no-installer   Skip NSIS installer creation
    --no-portable    Skip portable ZIP creation
    --no-checksums   Skip checksum generation
"""

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Optional

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DIST_DIR = PROJECT_ROOT / "dist"
BUILD_DIR = PROJECT_ROOT / "build"
INSTALLER_DIR = PROJECT_ROOT / "installer"
SPEC_FILE_FLET = PROJECT_ROOT / "faster-whisper-hotkey-flet.spec"
SPEC_FILE_QT = PROJECT_ROOT / "faster-whisper-hotkey.spec"
ICON_FILE = INSTALLER_DIR / "app_icon.ico"
PORTABLE_DIR = DIST_DIR / "portable"

# Version from pyproject.toml
PYPROJECT_TOML = PROJECT_ROOT / "pyproject.toml"


def get_version() -> str:
    """Extract version from pyproject.toml."""
    if PYPROJECT_TOML.exists():
        content = PYPROJECT_TOML.read_text()
        for line in content.split('\n'):
            if line.startswith('version ='):
                version = line.split('=')[1].strip().strip('"\'')
                return version
    return "0.4.3"  # Fallback


def run_command(cmd: list[str], cwd: Optional[Path] = None) -> int:
    """Run a command and return exit code."""
    print(f"\n> Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd or PROJECT_ROOT)
    return result.returncode


def clean_build_artifacts() -> None:
    """Clean previous build artifacts."""
    print("\n" + "=" * 60)
    print("Cleaning build artifacts...")
    print("=" * 60)

    dirs_to_clean = [BUILD_DIR, DIST_DIR, PORTABLE_DIR]
    for dir_path in dirs_to_clean:
        if dir_path.exists():
            print(f"Removing: {dir_path}")
            shutil.rmtree(dir_path)

    # Clean PyInstaller cache
    pyinstaller_cache = PROJECT_ROOT / "__pycache__"
    for cache_dir in PROJECT_ROOT.rglob("__pycache__"):
        if cache_dir.is_dir():
            print(f"Removing cache: {cache_dir}")
            shutil.rmtree(cache_dir, ignore_errors=True)

    print("Clean complete.")


def generate_icon() -> bool:
    """Generate the app icon."""
    print("\n" + "=" * 60)
    print("Generating app icon...")
    print("=" * 60)

    icon_script = INSTALLER_DIR / "create_icon.py"
    if not icon_script.exists():
        print(f"Warning: Icon script not found: {icon_script}")
        return False

    if run_command([sys.executable, str(icon_script)]) != 0:
        print("Warning: Icon generation failed, continuing without icon")
        return False

    print("Icon generated successfully.")
    return True


def build_executable(spec_file: Path) -> bool:
    """Build the executable with PyInstaller."""
    print("\n" + "=" * 60)
    print(f"Building executable with spec: {spec_file.name}")
    print("=" * 60)

    if not spec_file.exists():
        print(f"Error: Spec file not found: {spec_file}")
        return False

    if run_command([sys.executable, "-m", "PyInstaller", str(spec_file), "--clean"]) != 0:
        print(f"Error: PyInstaller build failed for {spec_file}")
        return False

    print("Executable built successfully.")
    return True


def create_portable_package(version: str) -> bool:
    """Create a portable ZIP package."""
    print("\n" + "=" * 60)
    print("Creating portable package...")
    print("=" * 60)

    PORTABLE_DIR.mkdir(parents=True, exist_ok=True)

    # Find the built executable
    exe_name = "faster-whisper-hotkey.exe"
    source_exe = DIST_DIR / exe_name

    if not source_exe.exists():
        print(f"Error: Executable not found: {source_exe}")
        return False

    # Create portable ZIP
    zip_name = f"faster-whisper-hotkey-portable-{version}-windows.zip"
    zip_path = DIST_DIR / zip_name

    print(f"Creating portable ZIP: {zip_name}")

    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        # Add executable
        zf.write(source_exe, exe_name)

        # Add README and LICENSE
        readme = PROJECT_ROOT / "README.md"
        if readme.exists():
            zf.write(readme, "README.md")

        license_file = PROJECT_ROOT / "LICENSE.txt"
        if license_file.exists():
            zf.write(license_file, "LICENSE.txt")

        # Add a portable launcher stub (simple batch file)
        launcher_content = f"""@echo off
REM faster-whisper-hotkey Portable Launcher
REM This launcher ensures settings are stored locally

setlocal
set APPDATA=%~dp0settings
set LOCALAPPDATA=%~dp0settings

REM Create settings directory if it doesn't exist
if not exist "%~dp0settings" mkdir "%~dp0settings"

REM Launch the application
start "" "%~dp0{exe_name}"

endlocal
"""
        zf.writestr("START-portable.bat", launcher_content)

    print(f"Portable package created: {zip_path}")
    return True


def build_installer(version: str) -> bool:
    """Build the NSIS installer."""
    print("\n" + "=" * 60)
    print("Building NSIS installer...")
    print("=" * 60)

    # Try to find makensis
    makensis_paths = [
        r"C:\Program Files (x86)\NSIS\makensis.exe",
        r"C:\Program Files\NSIS\makensis.exe",
        r"C:\NSIS\makensis.exe",
    ]

    makensis = None
    for path in makensis_paths:
        if Path(path).exists():
            makensis = path
            break

    if makensis is None:
        # Try to find in PATH
        result = subprocess.run(["where", "makensis"], capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip():
            makensis = result.stdout.strip().split('\n')[0]

    if makensis is None:
        print("Warning: NSIS not found. Skipping installer creation.")
        print("To create installers, install NSIS from: https://nsis.sourceforge.io/")
        return False

    installer_script = INSTALLER_DIR / "installer.nsi"
    if not installer_script.exists():
        print(f"Error: Installer script not found: {installer_script}")
        return False

    # Ensure dist directory exists
    DIST_DIR.mkdir(parents=True, exist_ok=True)

    if run_command([makensis, str(installer_script)]) != 0:
        print("Warning: NSIS installer build failed")
        return False

    print("NSIS installer created successfully.")
    return True


def generate_checksums() -> dict:
    """Generate SHA256 checksums for all distribution files."""
    print("\n" + "=" * 60)
    print("Generating checksums...")
    print("=" * 60)

    checksums = {}

    for file_path in DIST_DIR.glob("*"):
        if file_path.is_file() and not file_path.name.endswith('.sha256'):
            sha256 = hashlib.sha256()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b''):
                    sha256.update(chunk)

            checksum = sha256.hexdigest()
            checksums[file_path.name] = checksum

            # Write checksum file
            checksum_file = file_path.with_suffix('.sha256')
            checksum_file.write_text(f"{checksum}  {file_path.name}\n")
            print(f"{file_path.name}: {checksum[:16]}...")

    return checksums


def generate_release_notes(version: str, checksums: dict) -> bool:
    """Generate release notes from git log."""
    print("\n" + "=" * 60)
    print("Generating release notes...")
    print("=" * 60)

    notes_path = DIST_DIR / "RELEASE_NOTES.md"

    # Get git log (if available)
    git_log = []
    try:
        result = subprocess.run(
            ["git", "log", "--oneline", "-10"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            git_log = result.stdout.strip().split('\n')
    except FileNotFoundError:
        pass

    # Build release notes
    content = f"""# Release Notes - Version {version}

**Release Date:** {datetime.now().strftime('%Y-%m-%d')}

## Distribution Files

"""

    for filename, checksum in sorted(checksums.items()):
        if not filename.endswith('.sha256'):
            content += f"- **{filename}**\n"
            content += f"  - SHA256: `{checksum}`\n"
            content += f"  - Size: {Path(DIST_DIR / filename).stat().st_size / (1024*1024):.1f} MB\n\n"

    content += """## Installation

### Windows Installer

1. Download `faster-whisper-hotkey-setup-x.x.x.exe`
2. Run the installer
3. Follow the installation wizard
4. Launch the application from the Start menu

### Portable Version

1. Download `faster-whisper-hotkey-portable-x.x.x-windows.zip`
2. Extract to a folder of your choice
3. Run `faster-whisper-hotkey.exe` or `START-portable.bat`

## What's New

"""

    if git_log:
        content += "### Recent Changes\n\n"
        for entry in git_log[:10]:
            content += f"- {entry}\n"
    else:
        content += "See the [GitHub repository](https://github.com/blakkd/faster-whisper-hotkey) for full commit history.\n"

    content += f"""

## System Requirements

- Windows 10 or later (64-bit)
- 4 GB RAM minimum (8 GB recommended)
- 2 GB free disk space for application
- Additional disk space for AI models (varies by model)

## Known Issues

See the [GitHub Issues](https://github.com/blakkd/faster-whisper-hotkey/issues) page.

## Support

- GitHub: https://github.com/blakkd/faster-whisper-hotkey
- Issues: https://github.com/blakkd/faster-whisper-hotkey/issues
"""

    notes_path.write_text(content)
    print(f"Release notes saved to: {notes_path}")
    return True


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Build script for faster-whisper-hotkey Windows distribution"
    )
    parser.add_argument("--clean-only", action="store_true",
                       help="Only clean build artifacts")
    parser.add_argument("--no-installer", action="store_true",
                       help="Skip NSIS installer creation")
    parser.add_argument("--no-portable", action="store_true",
                       help="Skip portable ZIP creation")
    parser.add_argument("--no-checksums", action="store_true",
                       help="Skip checksum generation")
    parser.add_argument("--spec", choices=["flet", "qt"], default="flet",
                       help="Which spec file to build (default: flet)")

    args = parser.parse_args()

    # Get version
    version = get_version()
    print(f"\nBuilding faster-whisper-hotkey version {version}")
    print(f"Project root: {PROJECT_ROOT}")

    # Clean build artifacts
    clean_build_artifacts()
    if args.clean_only:
        return 0

    # Generate icon
    generate_icon()

    # Build executable
    spec_file = SPEC_FILE_FLET if args.spec == "flet" else SPEC_FILE_QT
    if not build_executable(spec_file):
        print("Error: Failed to build executable")
        return 1

    # Create portable package
    checksums = {}
    if not args.no_portable:
        if create_portable_package(version):
            # Generate checksums so far
            if not args.no_checksums:
                checksums = generate_checksums()

    # Build NSIS installer
    if not args.no_installer:
        if build_installer(version):
            # Regenerate checksums with installer
            if not args.no_checksums:
                checksums = generate_checksums()

    # Generate release notes
    if checksums or not args.no_checksums:
        generate_release_notes(version, checksums)

    print("\n" + "=" * 60)
    print("Build complete!")
    print("=" * 60)
    print(f"\nDistribution files in: {DIST_DIR}")

    # List distribution files
    if DIST_DIR.exists():
        for file_path in sorted(DIST_DIR.iterdir()):
            if file_path.is_file():
                size_mb = file_path.stat().st_size / (1024 * 1024)
                print(f"  {file_path.name:40} ({size_mb:.1f} MB)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
