import logging
import json
from datetime import datetime
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QListWidget, 
    QListWidgetItem, QPushButton, QLabel, QHBoxLayout,
    QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtGui import QFont, QIcon, QClipboard, QGuiApplication

from ..settings import load_history, save_history, load_settings, save_settings

logger = logging.getLogger(__name__)

class HistoryWindow(QMainWindow):
    """
    Window to display transcription history.
    """
    def __init__(self, settings, max_items=50):
        super().__init__()
        self.settings = settings
        self.max_items = max_items
        self.history = load_history()
        
        self.setWindowTitle("Transcription History")
        self.resize(600, 400)
        
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        
        # Privacy Mode Indicator
        self.privacy_label = QLabel("Privacy Mode Active - No history is being saved")
        self.privacy_label.setStyleSheet("background-color: #F44336; color: white; padding: 5px; font-weight: bold;")
        self.privacy_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.privacy_label.hide()
        self.layout.addWidget(self.privacy_label)
        
        # History List
        self.list_widget = QListWidget()
        self.list_widget.setFont(QFont("Consolas", 10))
        self.list_widget.itemDoubleClicked.connect(self._copy_selected_item)
        self.layout.addWidget(self.list_widget)
        
        # Buttons
        self.button_layout = QHBoxLayout()
        
        self.copy_btn = QPushButton("Copy Selected")
        self.copy_btn.clicked.connect(self._copy_selected_item)
        self.button_layout.addWidget(self.copy_btn)
        
        self.clear_btn = QPushButton("Clear History")
        self.clear_btn.clicked.connect(self._clear_history)
        self.button_layout.addWidget(self.clear_btn)
        
        self.button_layout.addStretch()
        self.layout.addLayout(self.button_layout)
        
        # Status Label
        self.status_label = QLabel("Double-click to copy")
        self.layout.addWidget(self.status_label)
        
        self._refresh_list()
        self._update_privacy_mode()

    def update_privacy_mode(self, enabled: bool):
        self.settings.privacy_mode = enabled
        self._update_privacy_mode()

    def _update_privacy_mode(self):
        enabled = getattr(self.settings, 'privacy_mode', False)
        if enabled:
            self.privacy_label.show()
            self.history = []  # Clear in-memory history
            self._refresh_list()
        else:
            self.privacy_label.hide()

    def add_transcription(self, text: str):
        if getattr(self.settings, 'privacy_mode', False):
            return
            
        entry = {
            "timestamp": datetime.now().isoformat(),
            "text": text
        }
        self.history.append(entry)
        if len(self.history) > self.max_items:
            self.history = self.history[-self.max_items:]
        
        save_history(self.history, self.max_items)
        self._refresh_list()

    def _refresh_list(self):
        self.list_widget.clear()
        for entry in reversed(self.history):
            timestamp = entry.get("timestamp", "")
            text = entry.get("text", "")
            try:
                dt = datetime.fromisoformat(timestamp)
                time_str = dt.strftime("%H:%M:%S")
            except Exception:
                time_str = "??"
            
            preview = text[:80].replace("\n", " ")
            if len(text) > 80:
                preview += "..."
                
            display_text = f"[{time_str}] {preview}"
            item = QListWidgetItem(display_text)
            item.setData(Qt.ItemDataRole.UserRole, text)  # Store full text
            self.list_widget.addItem(item)

    def _copy_selected_item(self):
        item = self.list_widget.currentItem()
        if item:
            text = item.data(Qt.ItemDataRole.UserRole)
            clipboard = QGuiApplication.clipboard()
            clipboard.setText(text)
            self.status_label.setText("✓ Copied to clipboard!")
            # Reset status after 2 seconds (using QTimer would be better but simple works)

    def _clear_history(self):
        reply = QMessageBox.question(
            self, 'Clear History', 
            "Are you sure you want to clear all history?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.history = []
            save_history(self.history, self.max_items)
            self._refresh_list()
            self.status_label.setText("History cleared")
