
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'src'))

print("Importing Qt modules...")
try:
    from faster_whisper_hotkey.gui_qt.main import FasterWhisperHotkeyQt, main
    from faster_whisper_hotkey.gui_qt.tray_icon import TrayIcon
    from faster_whisper_hotkey.gui_qt.settings_dialog import SettingsDialog
    from faster_whisper_hotkey.gui_qt.hotkey_dialog import HotkeyDialog
    from faster_whisper_hotkey.gui_qt.history_window import HistoryWindow
    from faster_whisper_hotkey.gui_qt.signals import TranscriberSignals
    print("SUCCESS: All Qt modules imported successfully.")
except Exception as e:
    print(f"ERROR: Import failed: {e}")
    sys.exit(1)
