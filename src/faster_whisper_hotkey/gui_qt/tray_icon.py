from PyQt6.QtWidgets import QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QAction, QPixmap, QPainter, QColor, QBrush, QPen
from PyQt6.QtCore import pyqtSignal, QObject, QTimer, Qt
import math

class TrayIcon(QSystemTrayIcon):
    """
    System tray icon with dynamic status indication.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.pulse_phase = 0.0
        self.current_state = "idle"
        self.privacy_mode = False
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_pulse)
        
        # Initial Icon
        self.update_icon("idle")

    def update_icon(self, state: str, privacy_mode: bool = False):
        self.current_state = state
        self.privacy_mode = privacy_mode
        
        if state == "recording":
            if not self.timer.isActive():
                self.timer.start(50) # 20 FPS
        else:
            self.timer.stop()
            self.pulse_phase = 0.0
            self._draw_icon()

    def _update_pulse(self):
        self.pulse_phase += 0.15
        if self.pulse_phase > math.pi:
            self.pulse_phase = 0.0
        self._draw_icon()

    def _draw_icon(self):
        # 64x64 icon size
        size = 64
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Colors
        colors = {
            "idle": QColor("#4CAF50"),       # Green
            "recording": QColor("#F44336"),  # Red
            "transcribing": QColor("#FF9800"),  # Orange
        }
        base_color = colors.get(self.current_state, colors["idle"])
        
        # Draw Pulse
        if self.current_state == "recording":
            pulse_val = (math.sin(self.pulse_phase) + 1) / 2
            pulse_radius = 4 + (10 * pulse_val)
            opacity = int(255 * (1.0 - pulse_val))
            
            pulse_color = QColor(base_color)
            pulse_color.setAlpha(opacity)
            
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(pulse_color))
            
            margin = int(pulse_radius)
            # Center is 32,32
            # Draw ring? or just a larger circle fading out
            painter.drawEllipse(32 - 28, 32 - 28, 56, 56) # Simpler pulse for now
        
        # Draw Main Circle
        painter.setPen(QPen(Qt.GlobalColor.white, 2))
        painter.setBrush(QBrush(base_color))
        painter.drawEllipse(4, 4, 56, 56)
        
        # Draw Mic Icon (Simplified)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(Qt.GlobalColor.white))
        
        # Mic Body
        painter.drawRoundedRect(24, 16, 16, 24, 8, 8)
        
        # Mic Stand
        pen = QPen(Qt.GlobalColor.white, 3)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawArc(18, 28, 28, 24, 0 * 16, -180 * 16)
        painter.drawLine(32, 52, 32, 58)
        
        # Privacy Shield
        if self.privacy_mode:
            painter.setPen(QPen(Qt.GlobalColor.white, 1))
            painter.setBrush(QBrush(QColor("#2196F3")))
            
            # Draw shield shape at bottom right
            # ... simplified shield
            painter.drawRect(40, 40, 20, 20)
            
        painter.end()
        
        self.setIcon(QIcon(pixmap))
