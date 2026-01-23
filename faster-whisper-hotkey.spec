# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['src\\faster_whisper_hotkey\\gui_qt\\main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['faster_whisper', 'pynput.keyboard._win32', 'pynput.mouse._win32', 'scipy.special.cython_special', 'sklearn.utils._cython_blas', 'sklearn.neighbors._typedefs', 'sklearn.neighbors._quad_tree', 'sklearn.tree._utils', 'cython', 'pyamg'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['matplotlib', 'tkinter', 'notebook', 'scipy.notebook', 'cv2', 'caffe2', 'curses', 'email', 'html', 'http', 'xml', 'pydoc', 'unittest', 'xmlrpc'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='faster-whisper-hotkey',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
