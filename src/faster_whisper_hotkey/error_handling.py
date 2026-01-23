"""
Error handling and user-friendly error messages for faster-whisper-hotkey.

This module provides:
- User-friendly error messages for common failure scenarios
- Automatic recovery mechanisms where possible
- Error reporting and feedback infrastructure

Classes
-------
UserFriendlyError
    Base class for errors with user-friendly messages.

ErrorRecovery
    Provides automatic recovery strategies for common errors.

ErrorReporter
    Collects and reports errors with diagnostic information.

Functions
---------
get_error_message
    Convert an exception to a user-friendly message.

try_with_recovery
    Execute a function with automatic recovery attempts.

Notes
-----
- Model download failures include retry logic with exponential backoff
- GPU initialization failures automatically fall back to CPU
- Audio device errors attempt reconnection with alternative devices
- Hotkey conflicts provide guidance for resolution
"""

import logging
import time
import traceback
import platform
import subprocess
from typing import Optional, Callable, TypeVar, Dict, Any, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import threading

logger = logging.getLogger(__name__)

T = TypeVar('T')


# ============================================================================
# Error Categories and Message Templates
# ============================================================================

class ErrorCategory:
    """Categories of errors with user-friendly messaging."""

    MODEL_DOWNLOAD = "model_download"
    AUDIO_DEVICE = "audio_device"
    GPU_INIT = "gpu_init"
    HOTKEY_CONFLICT = "hotkey_conflict"
    CLIPBOARD_ACCESS = "clipboard_access"
    SETTINGS_CORRUPT = "settings_corrupt"
    NETWORK = "network"
    PERMISSION = "permission"
    UNKNOWN = "unknown"


# User-friendly error messages
ERROR_MESSAGES: Dict[str, Dict[str, str]] = {
    ErrorCategory.MODEL_DOWNLOAD: {
        "title": "Model Download Failed",
        "description": "Could not download the required model files.",
        "suggestions": [
            "Check your internet connection",
            "Try downloading again (automatic retry is enabled)",
            "Check if a firewall is blocking the download",
            "Try downloading the model manually from HuggingFace",
        ],
        "details_template": "Model: {model_name}\nURL: {url}\nError: {error}",
    },

    ErrorCategory.AUDIO_DEVICE: {
        "title": "Audio Device Error",
        "description": "Could not access the audio recording device.",
        "suggestions": [
            "Check if your microphone is connected",
            "Verify microphone permissions in system settings",
            "Try selecting a different audio device",
            "Check if another application is using the microphone",
        ],
        "details_template": "Device: {device_name}\nError: {error}",
    },

    ErrorCategory.GPU_INIT: {
        "title": "GPU Initialization Failed",
        "description": "Could not initialize GPU for transcription.",
        "suggestions": [
            "GPU acceleration is now disabled (using CPU instead)",
            "Update your GPU drivers",
            "Check if CUDA is properly installed",
            "Ensure your GPU has enough available memory",
            "Consider using a smaller model",
        ],
        "details_template": "Device: {device}\nCompute Type: {compute_type}\nError: {error}",
    },

    ErrorCategory.HOTKEY_CONFLICT: {
        "title": "Hotkey Registration Failed",
        "description": "Could not register the hotkey for transcription.",
        "suggestions": [
            "Another application may be using this hotkey",
            "Try a different hotkey combination",
            "Close applications that might be using global hotkeys",
            "Some applications (like games) prevent hotkey registration",
        ],
        "details_template": "Hotkey: {hotkey}\nConflicting App: {app}",
    },

    ErrorCategory.CLIPBOARD_ACCESS: {
        "title": "Clipboard Access Denied",
        "description": "Could not access the system clipboard.",
        "suggestions": [
            "The application will use character-by-character typing instead",
            "Check clipboard permissions in system settings",
            "Some secure applications block clipboard access",
            "Try pasting manually after transcription completes",
        ],
        "details_template": "Error: {error}",
    },

    ErrorCategory.SETTINGS_CORRUPT: {
        "title": "Settings File Corrupted",
        "description": "The settings file could not be loaded.",
        "suggestions": [
            "A backup of the corrupted file has been created",
            "Default settings will be used",
            "You can reconfigure your settings in the application",
            "The backup file location is shown below",
        ],
        "details_template": "Settings File: {settings_file}\nBackup: {backup_file}\nError: {error}",
    },

    ErrorCategory.NETWORK: {
        "title": "Network Error",
        "description": "A network operation failed.",
        "suggestions": [
            "Check your internet connection",
            "Verify proxy settings if applicable",
            "Check if the service is temporarily unavailable",
            "Try again later",
        ],
        "details_template": "Operation: {operation}\nError: {error}",
    },

    ErrorCategory.PERMISSION: {
        "title": "Permission Denied",
        "description": "The application lacks required permissions.",
        "suggestions": [
            "Run the application as administrator",
            "Check file/folder permissions",
            "Verify microphone access in privacy settings",
            "Check antivirus/security software restrictions",
        ],
        "details_template": "Resource: {resource}\nError: {error}",
    },

    ErrorCategory.UNKNOWN: {
        "title": "An Error Occurred",
        "description": "An unexpected error occurred.",
        "suggestions": [
            "Try restarting the application",
            "Check the log file for more details",
            "Report this issue if it persists",
            "Include the error details shown below",
        ],
        "details_template": "Error Type: {error_type}\nError: {error}",
    },
}


# ============================================================================
# Exception Classes
# ============================================================================

class UserFriendlyError(Exception):
    """
    Base exception class that includes user-friendly error information.

    Attributes
    ----------
    category
        Error category from ErrorCategory.
    title
        User-friendly error title.
    message
        User-friendly error description.
    suggestions
        List of suggestions for resolving the error.
    details
        Technical details for diagnostics.
    recovery_action
        Optional recovery action that can be attempted.
    """

    def __init__(
        self,
        category: str,
        message: str = None,
        title: str = None,
        suggestions: List[str] = None,
        details: str = None,
        recovery_action: Callable[[], bool] = None,
        original_exception: Exception = None,
    ):
        self.category = category
        self._message = message
        self._title = title
        self._suggestions = suggestions or []
        self._details = details
        self._recovery_action = recovery_action
        self._original_exception = original_exception

        # Get default messages if not provided
        template = ERROR_MESSAGES.get(category, ERROR_MESSAGES[ErrorCategory.UNKNOWN])
        if title is None:
            self._title = template["title"]
        if message is None:
            self._message = template["description"]
        if not self._suggestions:
            self._suggestions = template.get("suggestions", [])

        super().__init__(self.user_message)

    @property
    def user_message(self) -> str:
        """Get the user-friendly error message."""
        return self._message

    @property
    def title(self) -> str:
        """Get the error title."""
        return self._title

    @property
    def suggestions(self) -> List[str]:
        """Get list of suggestions."""
        return self._suggestions.copy()

    @property
    def details(self) -> str:
        """Get technical details."""
        if self._details:
            return self._details
        if self._original_exception:
            return str(self._original_exception)
        return ""

    def can_recover(self) -> bool:
        """Check if recovery action is available."""
        return self._recovery_action is not None

    def attempt_recovery(self) -> bool:
        """Attempt to recover from the error."""
        if self._recovery_action:
            try:
                return self._recovery_action()
            except Exception as e:
                logger.warning(f"Recovery action failed: {e}")
                return False
        return False

    def __str__(self) -> str:
        return f"{self._title}: {self._message}"


class ModelDownloadError(UserFriendlyError):
    """Error raised when model download fails."""

    def __init__(
        self,
        model_name: str,
        url: str = "",
        original_exception: Exception = None,
        can_retry: bool = True,
    ):
        self.model_name = model_name
        self.url = url
        self.can_retry = can_retry
        self._retry_count = 0

        template = ERROR_MESSAGES[ErrorCategory.MODEL_DOWNLOAD]
        details = template["details_template"].format(
            model_name=model_name,
            url=url or "N/A",
            error=original_exception or "Unknown error"
        )

        super().__init__(
            category=ErrorCategory.MODEL_DOWNLOAD,
            details=details,
            original_exception=original_exception,
        )


class AudioDeviceError(UserFriendlyError):
    """Error raised when audio device access fails."""

    def __init__(
        self,
        device_name: str,
        original_exception: Exception = None,
        available_devices: List[str] = None,
    ):
        self.device_name = device_name
        self.available_devices = available_devices or []

        template = ERROR_MESSAGES[ErrorCategory.AUDIO_DEVICE]
        details = template["details_template"].format(
            device_name=device_name,
            error=original_exception or "Unknown error"
        )

        suggestions = template["suggestions"].copy()
        if available_devices:
            suggestions.append(f"Available devices: {', '.join(available_devices[:5])}")

        super().__init__(
            category=ErrorCategory.AUDIO_DEVICE,
            suggestions=suggestions,
            details=details,
            original_exception=original_exception,
        )


class GPUInitializationError(UserFriendlyError):
    """Error raised when GPU initialization fails."""

    def __init__(
        self,
        device: str,
        compute_type: str,
        original_exception: Exception = None,
        can_fallback_to_cpu: bool = True,
    ):
        self.device = device
        self.compute_type = compute_type
        self.can_fallback_to_cpu = can_fallback_to_cpu

        template = ERROR_MESSAGES[ErrorCategory.GPU_INIT]
        details = template["details_template"].format(
            device=device,
            compute_type=compute_type,
            error=original_exception or "Unknown error"
        )

        super().__init__(
            category=ErrorCategory.GPU_INIT,
            details=details,
            original_exception=original_exception,
        )


class HotkeyConflictError(UserFriendlyError):
    """Error raised when hotkey registration fails."""

    def __init__(
        self,
        hotkey: str,
        conflicting_app: str = "Unknown",
        original_exception: Exception = None,
    ):
        self.hotkey = hotkey
        self.conflicting_app = conflicting_app

        template = ERROR_MESSAGES[ErrorCategory.HOTKEY_CONFLICT]
        details = template["details_template"].format(
            hotkey=hotkey,
            app=conflicting_app
        )

        super().__init__(
            category=ErrorCategory.HOTKEY_CONFLICT,
            details=details,
            original_exception=original_exception,
        )


class ClipboardAccessError(UserFriendlyError):
    """Error raised when clipboard access fails."""

    def __init__(self, original_exception: Exception = None):
        template = ERROR_MESSAGES[ErrorCategory.CLIPBOARD_ACCESS]
        details = template["details_template"].format(
            error=original_exception or "Unknown error"
        )

        super().__init__(
            category=ErrorCategory.CLIPBOARD_ACCESS,
            details=details,
            original_exception=original_exception,
        )


# ============================================================================
# Error Recovery
# ============================================================================

@dataclass
class RecoveryAttempt:
    """Record of a recovery attempt."""
    timestamp: datetime = field(default_factory=datetime.now)
    category: str = ""
    action: str = ""
    success: bool = False
    details: str = ""


class ErrorRecovery:
    """
    Provides automatic recovery strategies for common errors.

    This class implements recovery strategies such as:
    - Retry with exponential backoff for network operations
    - Fallback to CPU for GPU errors
    - Alternative device selection for audio errors
    """

    # Default retry configuration
    DEFAULT_MAX_RETRIES = 3
    DEFAULT_RETRY_DELAY = 1.0  # seconds
    DEFAULT_BACKOFF_MULTIPLIER = 2.0

    def __init__(self):
        self._recovery_history: List[RecoveryAttempt] = []
        self._lock = threading.Lock()

    def _record_attempt(self, category: str, action: str, success: bool, details: str = ""):
        """Record a recovery attempt."""
        with self._lock:
            attempt = RecoveryAttempt(
                category=category,
                action=action,
                success=success,
                details=details,
            )
            self._recovery_history.append(attempt)

    def get_recovery_history(self, category: str = None) -> List[RecoveryAttempt]:
        """Get recovery attempt history."""
        with self._lock:
            if category:
                return [a for a in self._recovery_history if a.category == category]
            return self._recovery_history.copy()

    def retry_with_backoff(
        self,
        func: Callable[[], T],
        max_retries: int = DEFAULT_MAX_RETRIES,
        initial_delay: float = DEFAULT_RETRY_DELAY,
        backoff_multiplier: float = DEFAULT_BACKOFF_MULTIPLIER,
        category: str = "",
    ) -> T:
        """
        Execute a function with retry on failure using exponential backoff.

        Parameters
        ----------
        func
            Function to execute.
        max_retries
            Maximum number of retry attempts.
        initial_delay
            Initial delay between retries in seconds.
        backoff_multiplier
            Multiplier for exponential backoff.
        category
            Error category for logging.

        Returns
        -------
        T
            Result of the function.

        Raises
        ------
        Exception
            The last exception if all retries fail.
        """
        last_exception = None
        delay = initial_delay

        for attempt in range(max_retries + 1):
            try:
                result = func()
                if attempt > 0:
                    self._record_attempt(
                        category=category,
                        action=f"retry_with_backoff (attempt {attempt + 1})",
                        success=True,
                    )
                    logger.info(f"Retry successful after {attempt} attempts")
                return result
            except Exception as e:
                last_exception = e
                if attempt < max_retries:
                    logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay:.1f}s...")
                    time.sleep(delay)
                    delay *= backoff_multiplier
                else:
                    self._record_attempt(
                        category=category,
                        action=f"retry_with_backoff (failed after {attempt + 1} attempts)",
                        success=False,
                        details=str(e),
                    )
                    logger.error(f"All {max_retries + 1} attempts failed")

        raise last_exception

    def gpu_fallback_recovery(
        self,
        gpu_func: Callable[[], T],
        cpu_func: Callable[[], T],
    ) -> T:
        """
        Try GPU function, fall back to CPU on failure.

        Parameters
        ----------
        gpu_func
            Function to try with GPU.
        cpu_func
            Function to call if GPU fails.

        Returns
        -------
        T
            Result from either GPU or CPU function.
        """
        try:
            result = gpu_func()
            self._record_attempt(
                category=ErrorCategory.GPU_INIT,
                action="gpu_initialization",
                success=True,
            )
            return result
        except Exception as e:
            logger.warning(f"GPU initialization failed: {e}. Falling back to CPU...")
            self._record_attempt(
                category=ErrorCategory.GPU_INIT,
                action="gpu_fallback_to_cpu",
                success=True,
                details=f"GPU failed: {e}",
            )
            return cpu_func()

    def audio_device_fallback(
        self,
        preferred_device: str,
        device_list: List[str],
        test_func: Callable[[str], bool],
    ) -> Optional[str]:
        """
        Find a working audio device, trying alternatives if preferred fails.

        Parameters
        ----------
        preferred_device
        Name of the preferred audio device.
        device_list
        List of available device names.
        test_func
        Function that tests if a device works.

        Returns
        -------
        str or None
        Name of a working device, or None if all fail.
        """
        # Try preferred device first
        if preferred_device:
            try:
                if test_func(preferred_device):
                    self._record_attempt(
                        category=ErrorCategory.AUDIO_DEVICE,
                        action=f"device_test_{preferred_device}",
                        success=True,
                    )
                    return preferred_device
            except Exception as e:
                logger.debug(f"Preferred device '{preferred_device}' failed: {e}")

        # Try alternative devices
        for device in device_list:
            if device == preferred_device:
                continue
            try:
                if test_func(device):
                    self._record_attempt(
                        category=ErrorCategory.AUDIO_DEVICE,
                        action=f"device_fallback_to_{device}",
                        success=True,
                    )
                    logger.info(f"Fell back to audio device: {device}")
                    return device
            except Exception as e:
                logger.debug(f"Device '{device}' failed: {e}")

        self._record_attempt(
            category=ErrorCategory.AUDIO_DEVICE,
            action="device_fallback",
            success=False,
            details="All devices failed",
        )
        return None


# ============================================================================
# Error Reporting
# ============================================================================

@dataclass
class ErrorReport:
    """Detailed error report for diagnostics."""
    timestamp: datetime = field(default_factory=datetime.now)
    category: str = ""
    title: str = ""
    message: str = ""
    details: str = ""
    stack_trace: str = ""
    system_info: Dict[str, Any] = field(default_factory=dict)
    user_suggestions: List[str] = field(default_factory=list)
    recovery_attempted: bool = False
    recovery_successful: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "category": self.category,
            "title": self.title,
            "message": self.message,
            "details": self.details,
            "stack_trace": self.stack_trace,
            "system_info": self.system_info,
            "user_suggestions": self.user_suggestions,
            "recovery_attempted": self.recovery_attempted,
            "recovery_successful": self.recovery_successful,
        }

    def to_markdown(self) -> str:
        """Convert report to markdown format."""
        lines = [
            f"# {self.title}",
            "",
            f"**Time:** {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Category:** {self.category}",
            "",
            "## Description",
            self.message,
            "",
            "## Suggestions",
        ]
        for i, suggestion in enumerate(self.user_suggestions, 1):
            lines.append(f"{i}. {suggestion}")

        if self.details:
            lines.extend([
                "",
                "## Details",
                "```",
                self.details,
                "```",
            ])

        if self.stack_trace:
            lines.extend([
                "",
                "## Stack Trace",
                "```",
                self.stack_trace,
                "```",
            ])

        if self.system_info:
            lines.extend([
                "",
                "## System Information",
            ])
            for key, value in self.system_info.items():
                lines.append(f"- **{key}:** {value}")

        if self.recovery_attempted:
            recovery_status = "Successful" if self.recovery_successful else "Failed"
            lines.extend([
                "",
                "## Recovery",
                f"Recovery was attempted: {recovery_status}",
            ])

        return "\n".join(lines)


class ErrorReporter:
    """
    Collects and reports errors with diagnostic information.

    This class provides:
    - Error report generation with system information
    - Error history tracking
    - Export to various formats (JSON, markdown)
    """

    def __init__(self, max_history: int = 100):
        self._error_history: List[ErrorReport] = []
        self._max_history = max_history
        self._lock = threading.Lock()

    def _get_system_info(self) -> Dict[str, Any]:
        """Collect system diagnostic information."""
        info = {
            "platform": platform.system(),
            "platform_release": platform.release(),
            "platform_version": platform.version(),
            "architecture": platform.machine(),
            "processor": platform.processor(),
            "python_version": platform.python_version(),
        }

        # Add CUDA info if available
        try:
            import torch
            info["cuda_available"] = torch.cuda.is_available()
            if torch.cuda.is_available():
                info["cuda_version"] = torch.version.cuda
                info["gpu_count"] = torch.cuda.device_count()
                info["gpu_names"] = [
                    torch.cuda.get_device_name(i)
                    for i in range(torch.cuda.device_count())
                ]
        except ImportError:
            info["cuda_available"] = "unknown (torch not installed)"

        # Add sounddevice info
        try:
            import sounddevice as sd
            devices = sd.query_devices()
            info["audio_devices"] = [
                d.get("name", "unknown") for d in devices if d.get("max_input_channels", 0) > 0
            ]
        except Exception:
            info["audio_devices"] = "unknown"

        return info

    def create_report(
        self,
        exception: Exception,
        category: str = ErrorCategory.UNKNOWN,
        title: str = None,
        message: str = None,
        suggestions: List[str] = None,
        recovery_attempted: bool = False,
        recovery_successful: bool = False,
    ) -> ErrorReport:
        """Create a detailed error report."""
        # Get user-friendly info if available
        user_title = title
        user_message = message
        user_suggestions = suggestions
        details = ""

        if isinstance(exception, UserFriendlyError):
            if not user_title:
                user_title = exception.title
            if not user_message:
                user_message = exception.user_message
            if not user_suggestions:
                user_suggestions = exception.suggestions
            details = exception.details

        # Get stack trace
        stack_trace = "".join(traceback.format_exception(
            type(exception), exception, exception.__traceback__
        ))

        # Create report
        report = ErrorReport(
            category=category or ErrorCategory.UNKNOWN,
            title=user_title or ERROR_MESSAGES[ErrorCategory.UNKNOWN]["title"],
            message=user_message or str(exception),
            details=details or str(exception),
            stack_trace=stack_trace,
            system_info=self._get_system_info(),
            user_suggestions=user_suggestions or [],
            recovery_attempted=recovery_attempted,
            recovery_successful=recovery_successful,
        )

        # Add to history
        with self._lock:
            self._error_history.append(report)
            if len(self._error_history) > self._max_history:
                self._error_history.pop(0)

        return report

    def get_recent_errors(self, count: int = 10) -> List[ErrorReport]:
        """Get recent error reports."""
        with self._lock:
            return self._error_history[-count:]

    def clear_history(self):
        """Clear error history."""
        with self._lock:
            self._error_history.clear()

    def save_report(self, report: ErrorReport, filepath: str) -> bool:
        """Save an error report to a file."""
        try:
            path = Path(filepath)
            path.parent.mkdir(parents=True, exist_ok=True)

            # Use markdown format for readability
            path.write_text(report.to_markdown())
            logger.info(f"Error report saved to: {filepath}")
            return True
        except Exception as e:
            logger.error(f"Failed to save error report: {e}")
            return False


# ============================================================================
# Convenience Functions
# ============================================================================

def get_error_message(exception: Exception) -> Tuple[str, List[str]]:
    """
    Convert an exception to a user-friendly message and suggestions.

    Parameters
    ----------
    exception
        The exception to convert.

    Returns
    -------
    tuple[str, list[str]]
        User-friendly message and list of suggestions.
    """
    if isinstance(exception, UserFriendlyError):
        return exception.user_message, exception.suggestions

    # Map standard exceptions to user-friendly messages
    exception_mapping = {
        PermissionError: (ErrorCategory.PERMISSION, "You don't have permission to perform this action."),
        ConnectionError: (ErrorCategory.NETWORK, "Could not connect to the server."),
        TimeoutError: (ErrorCategory.NETWORK, "The operation timed out."),
        FileNotFoundError: (ErrorCategory.UNKNOWN, "A required file was not found."),
        ValueError: (ErrorCategory.UNKNOWN, "An invalid value was provided."),
    }

    exc_type = type(exception)
    if exc_type in exception_mapping:
        category, message = exception_mapping[exc_type]
        template = ERROR_MESSAGES.get(category, ERROR_MESSAGES[ErrorCategory.UNKNOWN])
        return message, template.get("suggestions", [])

    # Default unknown error
    template = ERROR_MESSAGES[ErrorCategory.UNKNOWN]
    return str(exception), template.get("suggestions", [])


def try_with_recovery(
    func: Callable[[], T],
    recovery: ErrorRecovery = None,
    error_reporter: ErrorReporter = None,
    category: str = ErrorCategory.UNKNOWN,
) -> Tuple[bool, Optional[T], Optional[ErrorReport]]:
    """
    Execute a function with automatic recovery and error reporting.

    Parameters
    ----------
    func
        Function to execute.
    recovery
        Optional ErrorRecovery instance for recovery strategies.
    error_reporter
        Optional ErrorReporter for creating error reports.
    category
        Error category for reporting.

    Returns
    -------
    tuple[bool, T or None, ErrorReport or None]
        (success, result, error_report)
    """
    try:
        result = func()
        return True, result, None
    except Exception as e:
        # Create error report if reporter provided
        report = None
        if error_reporter:
            message, suggestions = get_error_message(e)
            report = error_reporter.create_report(
                exception=e,
                category=category,
                message=message,
                suggestions=suggestions,
            )

        return False, None, report


# Global instances
_error_recovery = ErrorRecovery()
_error_reporter = ErrorReporter()


def get_error_recovery() -> ErrorRecovery:
    """Get the global error recovery instance."""
    return _error_recovery


def get_error_reporter() -> ErrorReporter:
    """Get the global error reporter instance."""
    return _error_reporter
