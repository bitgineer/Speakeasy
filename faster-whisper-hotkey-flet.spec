# -*- mode: python ; coding: utf-8 -*-
#
# PyInstaller spec file for faster-whisper-hotkey (Flet GUI version)
#
# This configuration creates a Windows executable with:
# - One-file mode for single .exe distribution
# - Proper metadata (version, description, company info)
# - Hidden imports for Flet and all dependencies
# - Optimized exclusions to reduce size
# - Windows-specific configuration
#
# Usage:
#   pyinstaller faster-whisper-hotkey-flet.spec --clean
#
# Output:
#   dist/faster-whisper-hotkey.exe (single file executable)
#

import os
import sys
from pathlib import Path

# Project metadata
APP_NAME = 'faster-whisper-hotkey'
APP_VERSION = '0.4.3'
APP_DESCRIPTION = 'Push-to-talk transcription powered by cutting-edge ASR models'
APP_AUTHOR = 'blakkd'
APP_COPYRIGHT = f'Copyright (c) 2024 {APP_AUTHOR}'

# Paths
block_cipher = None
src_path = Path('src/faster_whisper_hotkey')
root_path = Path(__file__).parent

# Icon file - will be created separately
icon_path = root_path / 'installer' / 'app_icon.ico'

# Data files to include
datas = [
    # Include any config files from the package
    (str(src_path / '*.json'), 'faster_whisper_hotkey'),
]

# Hidden imports required by Flet and dependencies
hiddenimports = [
    # Flet core
    'flet',
    'flet._pyodide',
    'flet._project',
    'flet.utils',

    # Flet dependencies
    'flet_runtime',
    'flet_runtime.web',

    # Faster whisper
    'faster_whisper',
    'faster_whisper.tokenizer',
    'faster_whisper.audio',

    # Audio processing
    'sounddevice',
    'soundfile',
    'numpy',
    'scipy',
    'scipy.special',
    'scipy.special.cython_special',
    'scipy.io.wavfile',

    # PyInput for hotkeys
    'pynput',
    'pynput.keyboard',
    'pynput.keyboard._win32',
    'pynput.mouse',
    'pynput.mouse._win32',

    # Machine learning
    'torch',
    'transformers',
    'huggingface_hub',
    'tokenizers',

    # Nemo toolkit
    'nemo',
    'nemo.collections.asr',
    'nemo_toolkit',

    # Qt for system tray
    'PyQt6',
    'PyQt6.QtCore',
    'PyQt6.QtGui',
    'PyQt6.QtWidgets',

    # System tray
    'pystray',
    'PIL',
    'PIL._imaging',

    # Clipboard
    'pyperclip',

    # Networking
    'urllib3',
    'requests',
    'certifi',
    'httpx',
    'httpcore',

    # Scikit-learn for some models
    'sklearn',
    'sklearn.utils._cython_blas',
    'sklearn.neighbors._typedefs',
    'sklearn.neighbors._quad_tree',
    'sklearn.tree._utils',
    'sklearn.cluster._hierarchical',
    'sklearn.metrics._dist_metrics',

    # Cython
    'cython',
    'pyamg',

    # Windows-specific
    'windows',
    'win32api',
    'win32con',
    'win32gui',
    'win32process',
    'pywintypes',

    # Mistral audio support
    'mistral_common',
    'mistral_common.audio',
    'mistral_common.protocol',

    # Bitsandbytes for quantization
    'bitsandbytes',

    # JSON and config
    'json',
    'yaml',
    'tomli',
    'tomli_w',

    # Importlib for resources
    'importlib_resources',
    'importlib_resources.backends',
    'importlib_resources._adapters',
    'importlib_resources._common',
    'importlib_resources._compat',
    'importlib_resources._itertools',
    'importlib_resources._meta',

    # Async support
    'asyncio',
    'concurrent.futures',
    'threading',
    'queue',

    # Logging
    'logging',
    'logging.handlers',
]

# Packages to exclude to reduce size
excludes = [
    # Test frameworks
    'unittest',
    'pytest',
    'nose',
    'doctest',

    # Development tools
    'pdb',
    'profile',
    'pstats',
    'timeit',
    'trace',
    'tracemalloc',

    # Unused scientific packages
    'matplotlib',
    'matplotlib.pyplot',
    'IPython',
    'jupyter',

    # Documentation
    'pydoc',
    'pydoc_data',
    'pyflakes',
    'flake8',

    # Email/HTML/XML parsing (not needed)
    'email',
    'html',
    'html.parser',
    'xml',
    'xmlrpc',
    'xmlrpc.client',
    'xmlrpc.server',

    # GUI frameworks we don't use
    'tkinter',
    'cv2',
    'caffe2',
    'curses',

    # Web frameworks
    'flask',
    'django',
    'tornado',

    # Database
    'sqlite3',
    'mysql',
    'psycopg2',
    'mongoengine',

    # Large ML datasets
    'sklearn.datasets',
    'torchvision.datasets',
    'torchtext',

    # Other unused
    'pytz',
    'babel',
]

# PyInstaller Analysis
a = Analysis(
    ['src\\faster_whisper_hotkey\\flet_gui\\__main__.py'],
    pathex=[str(root_path)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
    optimize=2,  # Enable bytecode optimization
)

# Remove duplicate files from binaries/datas to reduce size
### a.binaries = sorted(set(a.binaries), key=lambda x: x[0])
### a.datas = sorted(set(a.datas), key=lambda x: x[0])

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name=APP_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,  # Keep debug symbols for troubleshooting
    upx=True,  # Use UPX compression (if available)
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Windowed application (no console)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(icon_path) if icon_path.exists() else None,
    version_file=None,  # Will add version info separately
)

# Windows version information
# This is embedded in the exe for proper Windows properties display
version_info = VSVersionInfo(
    ffi=FixedFileInfo(
        filevers=(int(APP_VERSION.split('.')[0]) if '.' in APP_VERSION else 0,
                  int(APP_VERSION.split('.')[1]) if len(APP_VERSION.split('.')) > 1 else 4,
                  int(APP_VERSION.split('.')[2]) if len(APP_VERSION.split('.')) > 2 else 3,
                  0),
        prodvers=(int(APP_VERSION.split('.')[0]) if '.' in APP_VERSION else 0,
                  int(APP_VERSION.split('.')[1]) if len(APP_VERSION.split('.')) > 1 else 4,
                  int(APP_VERSION.split('.')[2]) if len(APP_VERSION.split('.')) > 2 else 3,
                  0),
        mask=0x3f,
        flags=0x0,
        OS=0x40004,
        fileType=0x1,
        subtype=0x0,
        date=(0, 0)
    ),
    kids=[
        StringFileInfo(
            [
                StringTable(
                    u'040904B0',
                    [
                        StringStruct(u'CompanyName', APP_AUTHOR),
                        StringStruct(u'FileDescription', APP_DESCRIPTION),
                        StringStruct(u'FileVersion', APP_VERSION),
                        StringStruct(u'InternalName', APP_NAME),
                        StringStruct(u'LegalCopyright', APP_COPYRIGHT),
                        StringStruct(u'OriginalFilename', f'{APP_NAME}.exe'),
                        StringStruct(u'ProductName', APP_NAME),
                        StringStruct(u'ProductVersion', APP_VERSION),
                    ])
            ]
        ),
        VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
    ]
)
