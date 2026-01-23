"""
Core transcription engine for faster-whisper-hotkey.

This module provides the main transcription functionality, handling audio
recording from the microphone, hotkey-based activation control, and
text output via clipboard and paste operations.

Classes
-------
MicrophoneTranscriber
    Manages audio recording, hotkey detection, and transcription.

Constants
----------
MIN_RECORDING_DURATION
    Minimum recording duration in seconds to prevent noise transcriptions.

Notes
-----
- Supports both "hold" and "toggle" activation modes.
- Complex hotkey combinations with modifiers are supported.
- Audio recording uses sounddevice with a 16kHz sample rate.
- On Linux (non-Windows), uses pulsectl for audio device management.
"""

import time
import threading
import logging
import numpy as np
import sounddevice as sd
import platform

from pynput import keyboard
from threading import Lock, RLock

from .settings import Settings
from .models import ModelWrapper
from .clipboard import backup_clipboard, set_clipboard, restore_clipboard
from .paste import paste_to_active_window
from .text_processor import TextProcessor, TextProcessorConfig, Correction
from .snippets_manager import get_snippets_manager
from .app_rules_manager import get_app_rules_manager
from .app_detector import AppDetector

# Voice command import
try:
    from .voice_command import (
        VoiceCommandParser,
        VoiceCommandExecutor,
        VoiceCommandConfig,
        process_with_commands
    )
    VOICE_COMMAND_AVAILABLE = True
except ImportError:
    VOICE_COMMAND_AVAILABLE = False

# Analytics import (optional - may not be available in all contexts)
try:
    from .analytics import get_analytics_tracker
    ANALYTICS_AVAILABLE = True
except ImportError:
    ANALYTICS_AVAILABLE = False

# Accuracy tracking import (optional - may not be available in all contexts)
try:
    from .accuracy_tracker import load_accuracy_tracker, AccuracyEntry
    ACCURACY_TRACKING_AVAILABLE = True
except ImportError:
    ACCURACY_TRACKING_AVAILABLE = False

if platform.system() != "Windows":
    import pulsectl
else:
    pulsectl = None

logger = logging.getLogger(__name__)

accepted_compute_types = ["float16", "int8"]
accepted_devices = ["cuda", "cpu"]
accepted_device_voxtral = ["cuda"]

# Minimum recording duration to prevent short noise transcriptions
MIN_RECORDING_DURATION = 1.0  # seconds


class MicrophoneTranscriber:
    def __init__(self, settings: Settings, on_state_change=None, on_transcription=None, on_transcription_start=None, on_audio_level=None, on_streaming_update=None):
        self.settings = settings
        self.sample_rate = 16000
        self.max_buffer_length = 10 * 60 * self.sample_rate
        self.audio_buffer = np.zeros(self.max_buffer_length, dtype=np.float32)
        self.buffer_index = 0

        # Load the requested model wrapper
        self.model_wrapper = ModelWrapper(self.settings)

        self.stop_event = threading.Event()
        self._is_recording = False  # Private for thread-safe property
        self._recording_lock = Lock()  # Lock for recording state
        self._state_lock = RLock()  # Reentrant lock for state changes
        self._queue_lock = Lock()  # Lock for transcription queue
        self._modifiers_lock = Lock()  # Lock for active modifiers
        self._buffer_overflow_warned = False  # Track if we've warned about buffer overflow

        self.device_name = self.settings.device_name
        self.keyboard_controller = keyboard.Controller()
        self.language = self.settings.language

        # Parse hotkey (supports combos like "ctrl+shift+h")
        self.hotkey_combo = self._parse_hotkey(self.settings.hotkey)
        self.active_modifiers = set()

        # Activation mode: "hold" or "toggle"
        self.activation_mode = getattr(self.settings, 'activation_mode', 'hold')

        # GUI callbacks
        self.on_state_change = on_state_change
        self.on_transcription = on_transcription
        self.on_transcription_start = on_transcription_start
        self.on_audio_level = on_audio_level  # Callback for real-time audio level
        self.on_streaming_update = on_streaming_update  # Callback for streaming transcription updates

        # Initialize text processor
        self.text_processor = self._init_text_processor()

        # Initialize voice command parser and executor
        self.voice_command_parser = None
        self.voice_command_executor = None
        self._init_voice_commands()

        self.is_transcribing = False
        self.last_transcription_end_time = 0.0
        self.transcription_queue = []
        self.timer = None
        self.recording_start_time = 0.0
        self.should_stop = False
        self.listener = None

        # Debounce settings - prevent rapid-fire transcriptions but allow quick re-recording
        self._debounce_interval = 0.05  # Reduced from 0.1s to 50ms for better responsiveness
        self._last_hotkey_press_time = 0.0  # Track last hotkey press time for debouncing

        # Audio level tracking for visualization
        self.current_audio_level = 0.0
        self.audio_level_update_time = 0.0
        self._audio_level_thread = None
        self._stop_audio_level_thread = False

        # Analytics and app tracking
        self.app_detector = AppDetector()
        self._current_app_info = None  # Store app info when recording starts

        # Accuracy tracking (optional)
        self.accuracy_tracker = None
        if ACCURACY_TRACKING_AVAILABLE:
            try:
                self.accuracy_tracker = load_accuracy_tracker()
                logger.info("Accuracy tracking enabled")
            except Exception as e:
                logger.warning(f"Failed to initialize accuracy tracker: {e}")
                self.accuracy_tracker = None

    def _init_voice_commands(self):
        """Initialize voice command parser and executor from settings."""
        if not VOICE_COMMAND_AVAILABLE:
            logger.debug("Voice command module not available")
            return

        try:
            voice_settings = self.settings.get_voice_command_settings()
            config = VoiceCommandConfig(
                enabled=voice_settings.get('enabled', True),
                command_prefixes=voice_settings.get('command_prefixes', [""]),
                require_prefix_space=voice_settings.get('require_prefix_space', False),
                confidence_threshold=voice_settings.get('confidence_threshold', 0.5),
                key_press_delay=voice_settings.get('key_press_delay', 0.01),
                action_delay=voice_settings.get('action_delay', 0.05),
                case_sensitive=voice_settings.get('case_sensitive', False),
                fuzzy_matching=voice_settings.get('fuzzy_matching', True),
            )
            self.voice_command_parser = VoiceCommandParser(config)
            self.voice_command_executor = VoiceCommandExecutor(config)
            logger.info(f"Voice commands initialized (enabled: {config.enabled})")
        except Exception as e:
            logger.warning(f"Failed to initialize voice commands: {e}")
            self.voice_command_parser = None
            self.voice_command_executor = None

    def reload_voice_commands(self):
        """Reload voice command processor from settings (call after settings update)."""
        self._init_voice_commands()

    # ------------------------------------------------------------------
    # Thread-safe properties
    # ------------------------------------------------------------------
    @property
    def is_recording(self) -> bool:
        """Thread-safe getter for is_recording state."""
        with self._recording_lock:
            return self._is_recording

    @is_recording.setter
    def is_recording(self, value: bool):
        """Thread-safe setter for is_recording state."""
        with self._recording_lock:
            self._is_recording = value

    # ------------------------------------------------------------------
    # Hotkey mapping - supports single keys and combos like "ctrl+f1"
    # ------------------------------------------------------------------
    def _parse_hotkey(self, hotkey_str: str):
        """Parse hotkey string into (modifiers, main_key) tuple."""
        # Key mappings
        key_mapping = {
            "pause": keyboard.Key.pause,
            "f1": keyboard.Key.f1,
            "f2": keyboard.Key.f2,
            "f3": keyboard.Key.f3,
            "f4": keyboard.Key.f4,
            "f5": keyboard.Key.f5,
            "f6": keyboard.Key.f6,
            "f7": keyboard.Key.f7,
            "f8": keyboard.Key.f8,
            "f9": keyboard.Key.f9,
            "f10": keyboard.Key.f10,
            "f11": keyboard.Key.f11,
            "f12": keyboard.Key.f12,
            "insert": keyboard.Key.insert,
            "home": keyboard.Key.home,
            "end": keyboard.Key.end,
            "pageup": keyboard.Key.page_up,
            "pagedown": keyboard.Key.page_down,
            "space": keyboard.Key.space,
            "enter": keyboard.Key.enter,
            "tab": keyboard.Key.tab,
            "backspace": keyboard.Key.backspace,
            "delete": keyboard.Key.delete,
            "up": keyboard.Key.up,
            "down": keyboard.Key.down,
            "left": keyboard.Key.left,
            "right": keyboard.Key.right,
        }
        
        modifier_mapping = {
            "ctrl": {keyboard.Key.ctrl_l, keyboard.Key.ctrl_r},
            "alt": {keyboard.Key.alt_l, keyboard.Key.alt_r},
            "shift": {keyboard.Key.shift_l, keyboard.Key.shift_r},
            "win": {keyboard.Key.cmd, keyboard.Key.cmd_l, keyboard.Key.cmd_r},
        }
        
        parts = hotkey_str.lower().split("+")
        modifiers = set()
        main_key = None
        
        for part in parts:
            part = part.strip()
            if part in modifier_mapping:
                modifiers.update(modifier_mapping[part])
            elif part in key_mapping:
                main_key = key_mapping[part]
            elif len(part) == 1:
                # Single character key
                main_key = keyboard.KeyCode.from_char(part)
            else:
                # Try as-is
                main_key = key_mapping.get(part, keyboard.Key.pause)
        
        return (modifiers, main_key)
    
    def _check_modifiers_active(self):
        """Check if required modifiers are currently pressed (thread-safe)."""
        required_modifiers = self.hotkey_combo[0]
        if not required_modifiers:
            return True
        with self._modifiers_lock:
            # Check if at least one key from each modifier group is active
            for mod in required_modifiers:
                if mod in self.active_modifiers:
                    return True
            return len(required_modifiers) == 0 or bool(required_modifiers & self.active_modifiers)

    def _notify_state(self, state: str):
        """Notify GUI of state change."""
        if self.on_state_change:
            try:
                self.on_state_change(state)
            except Exception as e:
                logger.debug(f"State change callback error: {e}")

    def _init_text_processor(self):
        """Initialize text processor from settings."""
        try:
            tp_settings = self.settings.get_text_processing_settings()
            config = TextProcessorConfig(
                remove_filler_words=tp_settings.remove_filler_words,
                auto_capitalize=tp_settings.auto_capitalize,
                auto_punctuate=tp_settings.auto_punctuate,
                format_numbers=tp_settings.format_numbers,
                expand_acronyms=tp_settings.expand_acronyms,
                use_dictionary=getattr(tp_settings, 'use_dictionary', True),
                filler_aggressiveness=tp_settings.filler_aggressiveness,
                capitalization_style=tp_settings.capitalization_style,
                punctuation_style=tp_settings.punctuation_style,
                number_style=tp_settings.number_style,
                dictionary_fuzzy_matching=getattr(tp_settings, 'dictionary_fuzzy_matching', True),
                tone_preset=getattr(tp_settings, 'tone_preset', 'neutral'),
                tone_preset_enabled=getattr(tp_settings, 'tone_preset_enabled', False),
            )
            return TextProcessor(config)
        except Exception as e:
            logger.warning(f"Failed to initialize text processor: {e}")
            # Return a default processor with all features disabled
            return TextProcessor(TextProcessorConfig(
                remove_filler_words=False,
                auto_capitalize=False,
                auto_punctuate=False,
                format_numbers=False,
                expand_acronyms=False,
                use_dictionary=False,
            ))

    def reload_text_processor(self):
        """Reload text processor from settings (call after settings update)."""
        self.text_processor = self._init_text_processor()
        logger.info("Text processor reloaded")

    # ------------------------------------------------------------------
    # App-specific settings
    # ------------------------------------------------------------------
    def get_app_settings(self) -> dict:
        """Get settings with app-specific overrides applied.

        Returns settings dictionary with per-app configuration applied
        based on the currently active window.
        """
        try:
            rules_manager = get_app_rules_manager()
            global_settings = {
                "hotkey": self.settings.hotkey,
                "model_type": self.settings.model_type,
                "model_name": self.settings.model_name,
                "compute_type": self.settings.compute_type,
                "device": self.settings.device,
                "language": self.settings.language,
                "text_processing": self.settings.text_processing or {},
            }
            return rules_manager.get_app_settings(global_settings)
        except Exception as e:
            logger.debug(f"Failed to get app settings: {e}")
            return {
                "hotkey": self.settings.hotkey,
                "model_type": self.settings.model_type,
                "model_name": self.settings.model_name,
                "compute_type": self.settings.compute_type,
                "device": self.settings.device,
                "language": self.settings.language,
            }

    def get_current_app_rule_name(self) -> str:
        """Get the name of the currently matching app rule.

        Returns the rule name if a rule matches, empty string otherwise.
        """
        try:
            rules_manager = get_app_rules_manager()
            rule = rules_manager.match_active_window()
            return rule.name if rule else ""
        except Exception as e:
            logger.debug(f"Failed to get current app rule: {e}")
            return ""

    def _process_text(self, text: str) -> str:
        """Process transcribed text through the text processing pipeline."""
        try:
            processed = self.text_processor.process(text)

            # Check for snippet expansion
            snippets_manager = get_snippets_manager()
            expanded, was_expanded = snippets_manager.check_and_expand(processed)

            if was_expanded:
                logger.info(f"Snippet expanded: '{text}' -> '{expanded}'")

            return expanded
        except Exception as e:
            logger.warning(f"Text processing error: {e}")
            return text

    def _process_text_with_tracking(self, text: str) -> tuple[str, list[Correction]]:
        """
        Process transcribed text and track corrections made.

        Returns
        -------
        tuple[str, list[Correction]]
            The processed text and list of corrections made.
        """
        try:
            processed, corrections = self.text_processor.process_with_tracking(text)

            # Check for snippet expansion
            snippets_manager = get_snippets_manager()
            expanded, was_expanded = snippets_manager.check_and_expand(processed)

            if was_expanded:
                logger.info(f"Snippet expanded: '{text}' -> '{expanded}'")
                # Add snippet expansion as a correction
                corrections.append(Correction(
                    correction_type="snippet_expansion",
                    original=processed,
                    corrected=expanded,
                    processor="SnippetsManager"
                ))

            return expanded, corrections
        except Exception as e:
            logger.warning(f"Text processing error: {e}")
            return text, []

    # ------------------------------------------------------------------
    # Set default audio source
    # ------------------------------------------------------------------
    def set_default_audio_source(self):
        if platform.system() == "Windows":
            # On Windows, audio device selection is handled differently
            logger.info(
                "Audio source management not available on Windows - using system default"
            )
            return

        try:
            if pulsectl is not None:
                with pulsectl.Pulse("set-default-source") as pulse:
                    for source in pulse.source_list():
                        if source.name == self.device_name:
                            pulse.source_default_set(source)
                            logger.info(f"Default source set to: {source.name}")
                            return
                    logger.warning(f"Source '{self.device_name}' not found")
        except Exception as e:
            logger.debug(f"Failed to set default source: {e}")

    # ------------------------------------------------------------------
    # Audio callback
    # ------------------------------------------------------------------
    def audio_callback(self, indata, frames, time_, status):
        if status:
            logger.warning(f"Status: {status}")
        audio_data = (
            np.mean(indata, axis=1)
            if indata.ndim > 1 and indata.shape[1] == 2
            else indata.flatten()
        ).astype(np.float32)
        if not np.isclose(audio_data.max(), 0):
            audio_data /= np.abs(audio_data).max()

        # Calculate audio level for visualization (RMS)
        rms = np.sqrt(np.mean(audio_data ** 2))
        self.current_audio_level = min(1.0, rms * 10)  # Amplify for visualization

        new_index = self.buffer_index + len(audio_data)
        if new_index > self.max_buffer_length:
            # Warn only once per recording session
            if not self._buffer_overflow_warned:
                logger.warning(
                    f"Audio buffer overflow! Recording exceeds maximum length "
                    f"({self.max_buffer_length / self.sample_rate / 60:.1f} minutes). "
                    f"Audio is being truncated. For longer recordings, increase max_buffer_length."
                )
                self._buffer_overflow_warned = True
            audio_data = audio_data[: self.max_buffer_length - self.buffer_index]
            new_index = self.max_buffer_length
        self.audio_buffer[self.buffer_index : new_index] = audio_data
        self.buffer_index = new_index

    # ------------------------------------------------------------------
    # Transcription and sending
    # ------------------------------------------------------------------
    def transcribe_streaming(self, audio_data):
        """
        Stream transcription results with real-time updates.
        Yields (text, confidence, is_final) tuples as segments are transcribed.
        """
        try:
            self.is_transcribing = True

            # Notify GUI that transcription is starting
            if self.on_transcription_start:
                try:
                    self.on_transcription_start(len(audio_data) / self.sample_rate)
                except Exception as e:
                    logger.debug(f"Transcription start callback error: {e}")

            # Use the streaming transcription method
            for text, confidence, is_final in self.model_wrapper.transcribe_streaming(
                audio_data,
                sample_rate=self.sample_rate,
                language=self.settings.language,
            ):
                # Call the streaming update callback for GUI
                if self.on_streaming_update:
                    try:
                        self.on_streaming_update(text, confidence, is_final)
                    except Exception as e:
                        logger.debug(f"Streaming update callback error: {e}")
                yield (text, confidence, is_final)

        except Exception as e:
            logger.error(f"Streaming transcription error: {e}")
            yield ("", 0.0, True)
        finally:
            self.is_transcribing = False
            self.last_transcription_end_time = time.time()
            self.process_next_transcription()

    def transcribe_and_send(self, audio_data):
        # Calculate audio duration for progress feedback
        audio_duration = len(audio_data) / self.sample_rate

        try:
            self.is_transcribing = True

            # Notify GUI that transcription is starting (with audio duration)
            if self.on_transcription_start:
                try:
                    self.on_transcription_start(audio_duration)
                except Exception as e:
                    logger.debug(f"Transcription start callback error: {e}")

            transcribed_text = self.model_wrapper.transcribe(
                audio_data,
                sample_rate=self.sample_rate,
                language=self.settings.language,
            )

            # ---------- process the text through pipeline ----------
            processed_text, corrections = self._process_text_with_tracking(transcribed_text)

            # ---------- check for voice commands ----------
            is_command = False
            text_to_send = processed_text

            if self.voice_command_parser and self.voice_command_executor:
                try:
                    command = self.voice_command_parser.parse(processed_text)
                    if not command.is_dictation():
                        is_command = True
                        success = self.voice_command_executor.execute(command)
                        if success:
                            logger.info(f"Voice command executed: {command.command_type.value}")
                            # Notify GUI with command indicator
                            if self.on_transcription:
                                try:
                                    self.on_transcription(f"[Command: {command.command_type.value}]")
                                except Exception:
                                    pass
                        else:
                            logger.warning(f"Voice command execution failed: {command.command_type.value}")
                            # Treat as dictation if command failed
                            is_command = False
                except Exception as e:
                    logger.warning(f"Voice command processing error: {e}")

            # ---------- send the text ----------
            if not is_command and text_to_send.strip():
                # Notify GUI of transcription (send both original and processed)
                if self.on_transcription:
                    try:
                        # Send the processed text for history/callback
                        self.on_transcription(text_to_send)
                    except Exception as e:
                        logger.debug(f"Transcription callback error: {e}")

                if not set_clipboard:
                    # fallback typing - preserves case / punctuation
                    for char in text_to_send:
                        self.keyboard_controller.press(char)
                        self.keyboard_controller.release(char)
                        time.sleep(0.001)
                else:
                    original_clip = backup_clipboard()
                    if not set_clipboard(text_to_send):
                        logger.error("Could not set clipboard - falling back to typing")
                        for char in text_to_send:
                            self.keyboard_controller.press(char)
                            self.keyboard_controller.release(char)
                            time.sleep(0.001)
                    else:
                        time.sleep(0.01)  # give clipboard time to settle
                        paste_to_active_window()
                        # Keep transcript in clipboard instead of restoring original
                        # if original_clip is not None:
                        #     time.sleep(0.05)
                        #     restore_clipboard(original_clip)

                logger.info(f"Transcribed text: {transcribed_text}")
                if transcribed_text != text_to_send:
                    logger.debug(f"Processed text: {text_to_send}")

                # ---------- record analytics data ----------
                if ANALYTICS_AVAILABLE:
                    try:
                        analytics_tracker = get_analytics_tracker()
                        if self._current_app_info:
                            analytics_tracker.record_transcription(
                                text=text_to_send,
                                original_text=transcribed_text,
                                duration_seconds=audio_duration,
                                model_used=self.settings.model_name,
                                language=self.settings.language,
                                app_window_class=self._current_app_info.window_class,
                                app_window_title=self._current_app_info.window_title,
                                app_process_name=getattr(self._current_app_info, 'process_name', ''),
                            )
                    except Exception as e:
                        logger.debug(f"Analytics recording error: {e}")

                # ---------- record accuracy tracking data ----------
                if ACCURACY_TRACKING_AVAILABLE and self.accuracy_tracker:
                    try:
                        # Convert text_processor.Correction to accuracy_tracker.Correction
                        from .accuracy_tracker import Correction as AccuracyCorrection
                        accuracy_corrections = [
                            AccuracyCorrection(
                                correction_type=c.correction_type,
                                original=c.original,
                                corrected=c.corrected,
                                position=c.position,
                                confidence=c.confidence,
                                processor=c.processor
                            )
                            for c in corrections
                        ]

                        # Create accuracy entry
                        accuracy_entry = AccuracyEntry(
                            raw_text=transcribed_text,
                            processed_text=processed_text,
                            final_text=text_to_send,  # Will be updated if manual edits are made
                            automatic_corrections=accuracy_corrections,
                            has_manual_edits=False,  # Will be updated if manual edits are detected
                            word_count=len(transcribed_text.split()),
                            audio_duration=audio_duration,
                        )

                        # Save to accuracy tracker
                        self.accuracy_tracker.add_entry(accuracy_entry)
                        logger.debug(f"Recorded accuracy entry with {len(corrections)} corrections")
                    except Exception as e:
                        logger.debug(f"Accuracy tracking recording error: {e}")

        except Exception as e:
            logger.error(f"Transcription error: {e}")
        finally:
            self.is_transcribing = False
            self.last_transcription_end_time = time.time()

            # Clean up audio data from memory
            try:
                import gc
                gc.collect()
            except Exception:
                pass

            self.process_next_transcription()

    def process_next_transcription(self):
        if self.transcription_queue and not self.is_transcribing:
            audio_data = self.transcription_queue.pop(0)
            self.is_transcribing = True
            threading.Thread(
                target=self.transcribe_and_send, args=(audio_data,), daemon=True
            ).start()

    # ------------------------------------------------------------------
    # Recording control
    # ------------------------------------------------------------------
    def _update_audio_levels(self):
        """Background thread to update audio level callbacks."""
        while not self._stop_audio_level_thread:
            if self.is_recording and self.on_audio_level:
                try:
                    self.on_audio_level(self.current_audio_level)
                except Exception as e:
                    logger.debug(f"Audio level callback error: {e}")
            time.sleep(0.05)  # Update at 20 FPS

    def start_recording(self):
        if not self.is_recording:
            logger.info("Starting recording...")
            self.stop_event.clear()
            self.is_recording = True
            self.recording_start_time = time.time()
            self.current_audio_level = 0.0
            self._buffer_overflow_warned = False  # Reset overflow warning for new recording

            # Capture active app info for analytics
            try:
                self._current_app_info = self.app_detector.get_active_window_info()
            except Exception as e:
                logger.debug(f"Failed to capture app info: {e}")
                self._current_app_info = None

            # Start audio level update thread
            self._stop_audio_level_thread = False
            self._audio_level_thread = threading.Thread(
                target=self._update_audio_levels, daemon=True
            )
            self._audio_level_thread.start()

            device_to_use = None
            if self.device_name and self.device_name != "default":
                try:
                    devices = sd.query_devices()
                    for i, device_info in enumerate(devices):
                        if (
                            device_info.get("name") == self.device_name
                            and device_info.get("max_input_channels", 0) > 0
                        ):
                            device_to_use = i
                            break
                except Exception as e:
                    logger.warning(f"Could not find device '{self.device_name}': {e}")

            self.stream = sd.InputStream(
                callback=self.audio_callback,
                channels=1,
                samplerate=self.sample_rate,
                blocksize=4000,
                device=device_to_use,  # None will use system default
            )
            self.stream.start()

    def stop_recording_and_transcribe(self):
        if hasattr(self, "timer") and self.timer:
            self.timer.cancel()
        if self.is_recording:
            logger.info("Stopping recording and starting transcription...")
            self.stop_event.set()
            self.is_recording = False

            # Stop audio level update thread
            self._stop_audio_level_thread = True
            try:
                self.stream.stop()
                self.stream.close()
            except Exception:
                pass
            if self.buffer_index > 0:
                audio_data = self.audio_buffer[: self.buffer_index]
                recording_duration = time.time() - self.recording_start_time

                if recording_duration >= MIN_RECORDING_DURATION:
                    self.audio_buffer = np.zeros(
                        self.max_buffer_length, dtype=np.float32
                    )
                    self.buffer_index = 0
                    self.transcription_queue.append(audio_data)
                    self.process_next_transcription()
                    logger.info(
                        f"Recording duration: {recording_duration:.2f}s - processing transcription"
                    )
                else:
                    self.audio_buffer = np.zeros(
                        self.max_buffer_length, dtype=np.float32
                    )
                    self.buffer_index = 0
                    logger.info(
                        f"Recording duration: {recording_duration:.2f}s - too short, skipping transcription"
                    )
            else:
                self.buffer_index = 0
                self.is_transcribing = False
                self.last_transcription_end_time = time.time()
                self.process_next_transcription()

    # ------------------------------------------------------------------
    # Hotkey handlers
    # ------------------------------------------------------------------
    def _is_modifier(self, key):
        """Check if key is a modifier."""
        modifier_keys = {
            keyboard.Key.ctrl_l, keyboard.Key.ctrl_r,
            keyboard.Key.alt_l, keyboard.Key.alt_r,
            keyboard.Key.shift_l, keyboard.Key.shift_r,
            keyboard.Key.cmd, keyboard.Key.cmd_l, keyboard.Key.cmd_r,
        }
        return key in modifier_keys

    def _matches_hotkey(self, key):
        """Check if current key + active modifiers match the hotkey combo (thread-safe)."""
        required_modifiers, main_key = self.hotkey_combo

        # Check if main key matches
        if key != main_key:
            return False

        # Check modifiers (if any required)
        if required_modifiers:
            with self._modifiers_lock:
                return bool(required_modifiers & self.active_modifiers)

        return True

    def on_press(self, key):
        try:
            # Track modifier keys (thread-safe)
            if self._is_modifier(key):
                with self._modifiers_lock:
                    self.active_modifiers.add(key)
                return True

            current_time = time.time()

            # Improved debounce: Only block if we're actively transcribing AND within debounce window
            # This allows quick re-recording after transcription completes
            if self.is_transcribing and (current_time - self.last_transcription_end_time < self._debounce_interval):
                logger.debug(f"Debouncing hotkey press - transcription in progress")
                return True

            # Also check if hotkey was pressed very recently (prevent accidental double-press)
            if current_time - self._last_hotkey_press_time < 0.05:  # 50ms double-press protection
                return True

            # Check if hotkey matches
            if self._matches_hotkey(key):
                self._last_hotkey_press_time = current_time
                if self.activation_mode == "toggle":
                    # Toggle mode: press to start, press again to stop
                    if self.is_recording:
                        self.stop_recording_and_transcribe()
                    else:
                        self.start_recording()
                        self._notify_state("recording")
                else:
                    # Hold mode: start recording on press
                    if not self.is_recording:
                        self.start_recording()
                        self._notify_state("recording")
                return True

        except AttributeError:
            pass
        except Exception as e:
            logger.error(f"Error in on_press: {e}")
        return True

    def on_release(self, key):
        """
        Release the hotkey to stop recording (in hold mode).
        In toggle mode, release does nothing.
        """
        try:
            # Track modifier keys (thread-safe)
            if self._is_modifier(key):
                with self._modifiers_lock:
                    self.active_modifiers.discard(key)
                return True

            # In hold mode, release stops recording
            if self.activation_mode == "hold":
                _, main_key = self.hotkey_combo
                if key == main_key and self.is_recording:
                    self._notify_state("transcribing")
                    self.stop_recording_and_transcribe()
                    return True

        except AttributeError:
            pass
        except Exception as e:
            logger.error(f"Error in on_release: {e}")
        return True

    def stop(self):
        """Stop the transcriber gracefully."""
        self.should_stop = True
        if self.is_recording:
            self.stop_recording_and_transcribe()
        if self.listener:
            self.listener.stop()

    def cleanup(self):
        """
        Clean up resources and free memory.

        Call this before destroying the transcriber to ensure proper cleanup.
        """
        try:
            # Stop recording if active
            if self.is_recording:
                self.stop_recording_and_transcribe()

            # Stop the listener
            if self.listener:
                self.listener.stop()
                self.listener = None

            # Clean up model resources
            if hasattr(self, 'model_wrapper') and self.model_wrapper:
                self.model_wrapper.cleanup()

            # Clear audio buffer
            self.audio_buffer = None
            self.transcription_queue = None

            # Stop audio level thread
            self._stop_audio_level_thread = True

            logger.debug("Transcriber resources cleaned up")

        except Exception as e:
            logger.warning(f"Error during transcriber cleanup: {e}")

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------
    def run(self):
        try:
            self.set_default_audio_source()
        except Exception:
            pass

        self.listener = keyboard.Listener(
            on_press=self.on_press, on_release=self.on_release
        )
        self.listener.start()
        
        mode_desc = "toggle" if self.activation_mode == "toggle" else "hold"
        logger.info(
            f"Ready! Hotkey: {self.settings.hotkey.upper()} ({mode_desc} mode). Press Ctrl+C to exit."
        )
        
        try:
            while not self.should_stop:
                self.listener.join(timeout=0.5)
                if not self.listener.is_alive():
                    break
        except KeyboardInterrupt:
            if self.is_recording:
                self.stop_recording_and_transcribe()
            logger.info("Program terminated by user")
        finally:
            self._notify_state("idle")

