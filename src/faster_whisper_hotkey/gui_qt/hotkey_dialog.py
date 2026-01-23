from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, QRadioButton, 
    QHBoxLayout, QButtonGroup, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QObject
from pynput import keyboard

class HotkeySignals(QObject):
    hotkey_captured = pyqtSignal(str)

class HotkeyDialog(QDialog):
    def __init__(self, parent=None, current_hotkey="pause", current_mode="hold"):
        super().__init__(parent)
        self.setWindowTitle("Hotkey Settings")
        self.resize(400, 300)
        
        self.hotkey = current_hotkey
        self.mode = current_mode
        self.captured_hotkey = None
        self.capturing = False
        
        self.signals = HotkeySignals()
        self.signals.hotkey_captured.connect(self.on_hotkey_captured)
        
        self._init_ui()
        
        # Pynput Listener
        self.listener = None
        self.current_keys = set()
        
        # Key Mapping (pynput -> string)
        self.KEY_NAMES = {
            keyboard.Key.f1: "F1", keyboard.Key.f2: "F2", keyboard.Key.f3: "F3",
            keyboard.Key.f4: "F4", keyboard.Key.f5: "F5", keyboard.Key.f6: "F6",
            keyboard.Key.f7: "F7", keyboard.Key.f8: "F8", keyboard.Key.f9: "F9",
            keyboard.Key.f10: "F10", keyboard.Key.f11: "F11", keyboard.Key.f12: "F12",
            keyboard.Key.pause: "Pause", keyboard.Key.insert: "Insert",
            keyboard.Key.home: "Home", keyboard.Key.end: "End",
            keyboard.Key.page_up: "PageUp", keyboard.Key.page_down: "PageDown",
            keyboard.Key.space: "Space", keyboard.Key.enter: "Enter",
            keyboard.Key.tab: "Tab", keyboard.Key.backspace: "Backspace",
            keyboard.Key.delete: "Delete", keyboard.Key.up: "Up",
            keyboard.Key.down: "Down", keyboard.Key.left: "Left",
            keyboard.Key.right: "Right", keyboard.Key.ctrl_l: "Ctrl",
            keyboard.Key.ctrl_r: "Ctrl", keyboard.Key.alt_l: "Alt",
            keyboard.Key.alt_r: "Alt", keyboard.Key.shift_l: "Shift",
            keyboard.Key.shift_r: "Shift", keyboard.Key.cmd: "Win",
            keyboard.Key.cmd_l: "Win", keyboard.Key.cmd_r: "Win",
        }
        self.MODIFIER_KEYS = {
            keyboard.Key.ctrl_l, keyboard.Key.ctrl_r,
            keyboard.Key.alt_l, keyboard.Key.alt_r,
            keyboard.Key.shift_l, keyboard.Key.shift_r,
            keyboard.Key.cmd, keyboard.Key.cmd_l, keyboard.Key.cmd_r,
        }

    def _init_ui(self):
        layout = QVBoxLayout(self)
        
        # Current Hotkey
        layout.addWidget(QLabel("Current Hotkey:"))
        self.lbl_current = QLabel(self.hotkey.upper())
        self.lbl_current.setStyleSheet("font-size: 16pt; font-weight: bold;")
        self.lbl_current.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl_current)
        
        layout.addSpacing(10)
        
        # Capture Button
        self.btn_capture = QPushButton("Click to Set New Hotkey")
        self.btn_capture.setMinimumHeight(40)
        self.btn_capture.clicked.connect(self.start_capture)
        layout.addWidget(self.btn_capture)
        
        self.lbl_instruction = QLabel("Press your key combination now...")
        self.lbl_instruction.setStyleSheet("color: #2196F3; font-weight: bold;")
        self.lbl_instruction.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_instruction.hide()
        layout.addWidget(self.lbl_instruction)
        
        layout.addSpacing(20)
        
        # Mode
        layout.addWidget(QLabel("Activation Mode:"))
        self.group_mode = QButtonGroup(self)
        
        self.rb_hold = QRadioButton("Hold-to-talk (hold key while speaking)")
        self.rb_toggle = QRadioButton("Toggle (press to start, press again to stop)")
        
        self.group_mode.addButton(self.rb_hold)
        self.group_mode.addButton(self.rb_toggle)
        
        if self.mode == "toggle":
            self.rb_toggle.setChecked(True)
        else:
            self.rb_hold.setChecked(True)
            
        layout.addWidget(self.rb_hold)
        layout.addWidget(self.rb_toggle)
        
        layout.addStretch()
        
        # Dialog Buttons
        btn_layout = QHBoxLayout()
        self.btn_ok = QPushButton("Save")
        self.btn_ok.clicked.connect(self.accept)
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self.reject)
        
        btn_layout.addWidget(self.btn_ok)
        btn_layout.addWidget(self.btn_cancel)
        layout.addLayout(btn_layout)

    def start_capture(self):
        self.capturing = True
        self.btn_capture.setEnabled(False)
        self.btn_capture.setText("Listening...")
        self.lbl_instruction.show()
        self.current_keys = set()
        self.captured_hotkey = None
        
        self.listener = keyboard.Listener(
            on_press=self.on_key_press,
            on_release=self.on_key_release
        )
        self.listener.start()
        
    def stop_capture(self):
        if self.listener:
            self.listener.stop()
            self.listener = None
        self.capturing = False
        self.btn_capture.setEnabled(True)
        self.btn_capture.setText("Click to Set New Hotkey")
        self.lbl_instruction.hide()
        
    def on_key_press(self, key):
        if not self.capturing:
            return
        self.current_keys.add(key)
        # Optional: Emit signal for live preview if desired
        
    def on_key_release(self, key):
        if not self.capturing:
            return
            
        # Ignore if just releasing a modifier while others are held?
        # For simplicity, we capture on first release of a non-modifier
        # OR if only modifiers were held and one was released.
        
        is_modifier = key in self.MODIFIER_KEYS
        
        if not is_modifier or (is_modifier and len(self.current_keys) == 1):
             # Capture
            combo = self._keys_to_string(self.current_keys)
            if combo:
                self.signals.hotkey_captured.emit(combo)
            
        if key in self.current_keys:
            self.current_keys.discard(key)
            
    def on_hotkey_captured(self, combo):
        self.captured_hotkey = combo.lower()
        self.lbl_current.setText(combo)
        self.stop_capture()

    def _keys_to_string(self, keys: set) -> str:
        modifiers = []
        main_key = None
        
        for key in keys:
            if key in self.MODIFIER_KEYS:
                name = self.KEY_NAMES.get(key, str(key))
                if name not in modifiers:
                    modifiers.append(name)
            else:
                main_key = self.KEY_NAMES.get(key, str(key))
                if main_key and main_key.startswith("Key."):
                     main_key = main_key.replace("Key.", "").title()
                elif hasattr(key, 'char') and key.char:
                     main_key = key.char.upper()
        
        # Sort modifiers
        mod_order = ["Ctrl", "Alt", "Shift", "Win"]
        modifiers.sort(key=lambda m: mod_order.index(m) if m in mod_order else 99)
        
        parts = modifiers + ([main_key] if main_key else [])
        return "+".join(parts) if parts else ""

    def get_result(self):
        mode = "toggle" if self.rb_toggle.isChecked() else "hold"
        hotkey = self.captured_hotkey if self.captured_hotkey else self.hotkey
        
        # Ensure we return valid hotkey string
        if not hotkey: hotkey = "pause"
        
        return hotkey, mode

def show_hotkey_dialog(parent, current_hotkey="pause", current_mode="hold"):
    dialog = HotkeyDialog(parent, current_hotkey, current_mode)
    if dialog.exec():
        return dialog.get_result()
    return None, None
