import sys
import threading
import logging
from PyQt6.QtWidgets import QApplication, QMenu, QMessageBox
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtCore import pyqtSlot

from ..settings import load_settings
from ..transcriber import MicrophoneTranscriber
from .tray_icon import TrayIcon
from .history_window import HistoryWindow
from .settings_dialog import SettingsDialog
from .signals import TranscriberSignals

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FasterWhisperHotkeyQt:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)
        
        self.settings = load_settings()
        if not self.settings:
            QMessageBox.critical(None, "Error", "Failed to load settings.")
            sys.exit(1)
            
        # Components
        self.tray_icon = TrayIcon()
        self.history_window = HistoryWindow(self.settings)
        self.settings_dialog = None
        
        # Signals
        self.signals = TranscriberSignals()
        self.signals.state_changed.connect(self.on_state_changed)
        self.signals.transcription_finished.connect(self.on_transcription_finished)
        
        # Transcriber
        self.transcriber = None
        self.transcriber_thread = None
        self.is_running = False
        
        # Setup UI
        self._setup_tray_menu()
        self.tray_icon.show()
        
        # Start Transcriber
        self.start_transcriber()

    def _setup_tray_menu(self):
        menu = QMenu()
        
        self.action_history = QAction("History", self.app)
        self.action_history.triggered.connect(self.show_history)
        menu.addAction(self.action_history)
        
        self.action_settings = QAction("Settings", self.app)
        self.action_settings.triggered.connect(self.show_settings)
        menu.addAction(self.action_settings)
        
        menu.addSeparator()
        
        self.action_restart = QAction("Restart Transcriber", self.app)
        self.action_restart.triggered.connect(self.restart_transcriber)
        menu.addAction(self.action_restart)
        
        self.action_exit = QAction("Exit", self.app)
        self.action_exit.triggered.connect(self.exit_app)
        menu.addAction(self.action_exit)
        
        self.tray_icon.setContextMenu(menu)
        self.tray_icon.activated.connect(self.on_tray_activated)

    def on_tray_activated(self, reason):
        if reason == TrayIcon.ActivationReason.DoubleClick:
            self.show_history()

    def start_transcriber(self):
        if self.is_running: return
        
        try:
            # We pass callbacks that emit signals to bridge threads
            self.transcriber = MicrophoneTranscriber(
                self.settings,
                on_state_change=lambda state: self.signals.state_changed.emit(state),
                on_transcription=lambda text: self.signals.transcription_finished.emit(text),
                on_transcription_start=lambda duration: self.signals.transcription_start.emit(duration),
                on_audio_level=lambda level: self.signals.audio_level.emit(level)
            )
            
            self.transcriber_thread = threading.Thread(
                target=self.transcriber.run,
                daemon=True
            )
            self.transcriber_thread.start()
            self.is_running = True
            self.tray_icon.update_icon("idle", self.settings.privacy_mode)
            logger.info("Transcriber started")
            
        except Exception as e:
            QMessageBox.critical(None, "Error", f"Failed to start transcriber: {e}")
            logger.error(f"Failed to start transcriber: {e}")

    def stop_transcriber(self):
        if self.transcriber:
            self.transcriber.stop()
            # Wait for thread?
            self.transcriber = None
            self.is_running = False
            self.tray_icon.update_icon("idle")

    def restart_transcriber(self):
        self.stop_transcriber()
        # Reload settings
        self.settings = load_settings()
        self.history_window.settings = self.settings
        self.start_transcriber()

    def show_history(self):
        self.history_window.show()
        self.history_window.activateWindow()

    def show_settings(self):
        self.settings_dialog = SettingsDialog()
        if self.settings_dialog.exec():
            # Settings saved
            self.restart_transcriber()
            self.history_window.update_privacy_mode(self.settings.privacy_mode)

    @pyqtSlot(str)
    def on_state_changed(self, state):
        self.tray_icon.update_icon(state, self.settings.privacy_mode)

    @pyqtSlot(str)
    def on_transcription_finished(self, text):
        self.history_window.add_transcription(text)
        self.tray_icon.showMessage(
            "Transcription Complete",
            text[:100] + "..." if len(text) > 100 else text,
            QIcon(),
            2000
        )

    def exit_app(self):
        self.stop_transcriber()
        self.app.quit()

    def run(self):
        sys.exit(self.app.exec())

def main():
    app = FasterWhisperHotkeyQt()
    app.run()

if __name__ == "__main__":
    main()
