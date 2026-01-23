from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, QTabWidget,
    QWidget, QFormLayout, QLineEdit, QCheckBox, QComboBox,
    QHBoxLayout, QSpinBox, QMessageBox
)
from .hotkey_dialog import show_hotkey_dialog
from ..settings import load_settings, save_settings

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.resize(500, 400)
        self.settings = load_settings()
        
        layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # --- General Tab ---
        self.tab_general = QWidget()
        self.tabs.addTab(self.tab_general, "General")
        self._init_general_tab()
        
        # --- Text Processing Tab ---
        self.tab_text = QWidget()
        self.tabs.addTab(self.tab_text, "Text Processing")
        self._init_text_tab()
        
        # --- Buttons ---
        btn_layout = QHBoxLayout()
        self.btn_save = QPushButton("Save")
        self.btn_save.clicked.connect(self.save_settings)
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self.reject)
        
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_save)
        btn_layout.addWidget(self.btn_cancel)
        layout.addLayout(btn_layout)

    def _init_general_tab(self):
        layout = QFormLayout(self.tab_general)
        
        # Model
        self.cb_model_size = QComboBox()
        self.cb_model_size.addItems(["tiny", "base", "small", "medium", "large-v3"])
        self.cb_model_size.setCurrentText(self.settings.model_name)
        layout.addRow("Model Size:", self.cb_model_size)
        
        self.cb_language = QComboBox()
        self.cb_language.addItems(["en", "fr", "de", "es", "it", "ja", "zh", "ru"]) # Add more as needed or make editable
        self.cb_language.setEditable(True)
        self.cb_language.setCurrentText(self.settings.language)
        layout.addRow("Language:", self.cb_language)
        
        self.cb_device = QComboBox()
        self.cb_device.addItems(["cuda", "cpu"])
        self.cb_device.setCurrentText(self.settings.device)
        layout.addRow("Device:", self.cb_device)
        
        # Hotkey
        hotkey_layout = QHBoxLayout()
        self.lbl_hotkey = QLabel(f"{self.settings.hotkey} ({self.settings.activation_mode})")
        self.btn_hotkey = QPushButton("Configure...")
        self.btn_hotkey.clicked.connect(self.open_hotkey_dialog)
        hotkey_layout.addWidget(self.lbl_hotkey)
        hotkey_layout.addWidget(self.btn_hotkey)
        layout.addRow("Hotkey:", hotkey_layout)
        
        # History
        self.sb_history = QSpinBox()
        self.sb_history.setRange(0, 500)
        self.sb_history.setValue(self.settings.history_max_items)
        layout.addRow("Max History Items:", self.sb_history)
        
        self.chk_privacy = QCheckBox("Privacy Mode (Do not save history)")
        self.chk_privacy.setChecked(self.settings.privacy_mode)
        layout.addRow("", self.chk_privacy)

    def _init_text_tab(self):
        layout = QFormLayout(self.tab_text)
        
        tp = self.settings.text_processing or {}
        
        self.chk_filler = QCheckBox("Remove Filler Words (um, uh)")
        self.chk_filler.setChecked(tp.get('remove_filler_words', True))
        layout.addRow(self.chk_filler)
        
        self.chk_capitalize = QCheckBox("Auto Capitalize")
        self.chk_capitalize.setChecked(tp.get('auto_capitalize', True))
        layout.addRow(self.chk_capitalize)
        
        self.chk_punctuate = QCheckBox("Auto Punctuate")
        self.chk_punctuate.setChecked(tp.get('auto_punctuate', True))
        layout.addRow(self.chk_punctuate)

    def open_hotkey_dialog(self):
        hotkey, mode = show_hotkey_dialog(
            self, 
            self.settings.hotkey, 
            self.settings.activation_mode
        )
        if hotkey and mode:
            self.settings.hotkey = hotkey
            self.settings.activation_mode = mode
            self.lbl_hotkey.setText(f"{hotkey} ({mode})")

    def save_settings(self):
        # Update settings object
        self.settings.model_name = self.cb_model_size.currentText()
        self.settings.language = self.cb_language.currentText()
        self.settings.device = self.cb_device.currentText()
        self.settings.history_max_items = self.sb_history.value()
        self.settings.privacy_mode = self.chk_privacy.isChecked()
        
        # Text processing
        tp = self.settings.text_processing
        tp['remove_filler_words'] = self.chk_filler.isChecked()
        tp['auto_capitalize'] = self.chk_capitalize.isChecked()
        tp['auto_punctuate'] = self.chk_punctuate.isChecked()
        self.settings.text_processing = tp
        
        # Save to disk
        save_settings(self.settings.__dict__)
        self.accept()
        
        QMessageBox.information(self, "Settings Saved", "Settings saved. Some changes may require a restart.")

