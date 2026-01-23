from PyQt6.QtCore import QObject, pyqtSignal

class TranscriberSignals(QObject):
    """
    Defines the signals available for the transcriber.
    """
    state_changed = pyqtSignal(str)
    transcription_finished = pyqtSignal(str)
    transcription_start = pyqtSignal(float)
    audio_level = pyqtSignal(float)  # For audio visualizer
