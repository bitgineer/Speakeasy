"""
Audio device utilities.

Provides functions for listing and selecting audio input devices.
"""

import logging
import platform
from typing import Optional

logger = logging.getLogger(__name__)


def list_audio_devices() -> list[dict]:
    """
    List available audio input devices.

    Returns:
        List of device info dictionaries with keys:
        - id: Device index
        - name: Device name
        - channels: Number of input channels
        - sample_rate: Default sample rate
        - is_default: Whether this is the default device
    """
    import sounddevice as sd

    devices = sd.query_devices()
    input_devices = []

    for i, dev in enumerate(devices):
        if dev["max_input_channels"] > 0:
            input_devices.append(
                {
                    "id": i,
                    "name": dev["name"],
                    "channels": dev["max_input_channels"],
                    "sample_rate": int(dev["default_samplerate"]),
                    "is_default": i == sd.default.device[0],
                }
            )

    return input_devices


def get_default_device() -> Optional[dict]:
    """
    Get the default audio input device.

    Returns:
        Device info dict or None if no device found
    """
    devices = list_audio_devices()
    for dev in devices:
        if dev["is_default"]:
            return dev
    return devices[0] if devices else None


def get_device_by_name(name: str) -> Optional[dict]:
    """
    Find an audio device by name (partial match).

    Args:
        name: Device name to search for (case-insensitive)

    Returns:
        Device info dict or None if not found
    """
    devices = list_audio_devices()
    name_lower = name.lower()

    for dev in devices:
        if name_lower in dev["name"].lower():
            return dev

    return None


def list_audio_devices_linux() -> list[dict]:
    """
    List audio devices using PulseAudio (Linux).

    This provides more user-friendly names on Linux systems.

    Returns:
        List of device info dictionaries
    """
    if platform.system() != "Linux":
        return list_audio_devices()

    try:
        import pulsectl

        devices = []
        with pulsectl.Pulse("speakeasy-device-list") as pulse:
            for source in pulse.source_list():
                # Skip monitor sources (output monitors)
                if ".monitor" in source.name:
                    continue

                devices.append(
                    {
                        "id": source.index,
                        "name": source.description or source.name,
                        "pulse_name": source.name,
                        "channels": source.channel_count,
                        "sample_rate": source.sample_spec.rate,
                        "is_default": source.name == pulse.server_info().default_source_name,
                    }
                )

        return devices

    except ImportError:
        logger.debug("pulsectl not available, using sounddevice")
        return list_audio_devices()
    except Exception as e:
        logger.warning(f"PulseAudio device listing failed: {e}")
        return list_audio_devices()


def set_default_device_linux(device_name: str) -> bool:
    """
    Set the default audio source on Linux via PulseAudio.

    Args:
        device_name: PulseAudio source name

    Returns:
        True if successful
    """
    if platform.system() != "Linux":
        return False

    try:
        import pulsectl

        with pulsectl.Pulse("speakeasy-device-set") as pulse:
            pulse.source_default_set(device_name)
        return True

    except Exception as e:
        logger.error(f"Failed to set default device: {e}")
        return False
