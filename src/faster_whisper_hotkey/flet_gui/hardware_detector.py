"""
Hardware detection system for faster-whisper-hotkey.

This module provides automatic detection of GPU/CPU capabilities and recommends
optimal configuration settings based on available hardware.

Classes
-------
HardwareInfo
    Data class containing detected hardware information.

HardwareDetector
    Main hardware detection class with CUDA and CPU capability detection.

Functions
---------
detect_hardware
    Convenience function to perform hardware detection and return HardwareInfo.
"""

import logging
import platform
from dataclasses import dataclass
from typing import Optional, List, Dict, Tuple

logger = logging.getLogger(__name__)


@dataclass
class HardwareInfo:
    """
    Detected hardware information and recommended settings.

    Attributes
    ----------
    has_cuda
        True if NVIDIA GPU with CUDA support is detected.
    gpu_name
        Name of the detected GPU, or None if no GPU.
    vram_total_mb
        Total VRAM in megabytes, or None if not detected.
    vram_free_mb
        Free VRAM in megabytes, or None if not detected.
    compute_capability
        GPU compute capability as tuple (major, minor), or None.
    cpu_features
        List of detected CPU features (AVX, AVX2, etc.).
    recommended_device
        Recommended device setting ("cuda" or "cpu").
    recommended_compute_type
        Recommended compute type ("float16", "int8", "int8_float16", etc.).
    recommended_model
        Recommended model based on available VRAM/CPU.
    reason
        Human-readable explanation of recommendations.
    """
    has_cuda: bool = False
    gpu_name: Optional[str] = None
    vram_total_mb: Optional[int] = None
    vram_free_mb: Optional[int] = None
    compute_capability: Optional[Tuple[int, int]] = None
    cpu_features: List[str] = None
    recommended_device: str = "cpu"
    recommended_compute_type: str = "int8"
    recommended_model: str = "base"
    reason: str = ""

    def __post_init__(self):
        if self.cpu_features is None:
            self.cpu_features = []


class HardwareDetector:
    """
    Hardware detection with automatic configuration recommendation.

    This class detects:
    - NVIDIA GPU presence using torch.cuda
    - GPU VRAM and compute capability
    - CPU features (AVX, AVX2, etc.)
    - Recommends optimal settings based on detected hardware
    """

    # Model VRAM requirements (approximate, in MB)
    MODEL_VRAM_REQUIREMENTS = {
        "large-v3": 10000,
        "large-v2": 10000,
        "large-v1": 10000,
        "medium": 5000,
        "medium.en": 5000,
        "small": 2000,
        "small.en": 2000,
        "base": 1000,
        "base.en": 1000,
        "tiny": 750,
        "tiny.en": 750,
        "distil-large-v3": 6000,
        "distil-large-v2": 6000,
        "distil-medium.en": 3000,
        "distil-small.en": 1500,
    }

    def __init__(self):
        """Initialize the hardware detector."""
        self._torch_available = False
        self._cuda_available = False
        self._gpu_info: Optional[Dict] = None
        self._cpu_features: List[str] = []
        self._platform = platform.system()

    def detect(self) -> HardwareInfo:
        """
        Perform full hardware detection and return recommendations.

        Returns
        -------
        HardwareInfo
            Detected hardware information and recommendations.
        """
        # Check for torch/CUDA
        self._detect_cuda()

        # Detect CPU features
        self._detect_cpu_features()

        # Build recommendations
        return self._build_recommendations()

    def _detect_cuda(self) -> None:
        """Detect CUDA availability and GPU information."""
        try:
            import torch

            self._torch_available = True
            self._cuda_available = torch.cuda.is_available()

            if self._cuda_available:
                gpu_count = torch.cuda.device_count()
                if gpu_count > 0:
                    # Get primary GPU info
                    gpu_name = torch.cuda.get_device_name(0)
                    props = torch.cuda.get_device_properties(0)

                    self._gpu_info = {
                        "name": gpu_name,
                        "count": gpu_count,
                        "vram_total_mb": props.total_memory // (1024 * 1024),
                        "compute_capability": (props.major, props.minor),
                        "multi_processor_count": props.multi_processor_count,
                    }

                    # Try to get free memory
                    try:
                        free_memory = torch.cuda.mem_get_info(0)[0]
                        self._gpu_info["vram_free_mb"] = free_memory // (1024 * 1024)
                    except Exception as e:
                        logger.debug(f"Could not get free VRAM: {e}")
                        self._gpu_info["vram_free_mb"] = None

                    logger.info(f"Detected CUDA GPU: {gpu_name}")
                else:
                    logger.info("CUDA available but no GPU devices found")
            else:
                logger.info("CUDA not available, will use CPU")

        except ImportError:
            logger.warning("PyTorch not available, cannot detect GPU")
            self._torch_available = False
            self._cuda_available = False
        except Exception as e:
            logger.error(f"Error detecting CUDA: {e}")
            self._cuda_available = False

    def _detect_cpu_features(self) -> None:
        """Detect CPU instruction set features."""
        self._cpu_features = []

        try:
            import cpuinfo

            info = cpuinfo.get_cpu_info()
            flags = info.get("flags", [])

            # Common feature flags across platforms
            feature_map = {
                # x86/x64 features
                "sse": "SSE",
                "sse2": "SSE2",
                "sse3": "SSE3",
                "ssse3": "SSSE3",
                "sse4_1": "SSE4.1",
                "sse4_2": "SSE4.2",
                "avx": "AVX",
                "avx2": "AVX2",
                "avx512f": "AVX512",
                "fma": "FMA",
                # ARM features
                "neon": "NEON",
                "asimd": "ASIMD",
                # Other
                "vmx": "VMX (AltiVec)",
            }

            for flag, name in feature_map.items():
                if flag.lower() in [f.lower() for f in flags]:
                    self._cpu_features.append(name)

            logger.info(f"Detected CPU features: {', '.join(self._cpu_features)}")

        except ImportError:
            # Fallback: basic detection by platform
            if self._platform == "x86_64" or self._platform == "AMD64":
                # Assume at least SSE2 on x86_64
                self._cpu_features = ["SSE", "SSE2"]
            elif self._platform == "arm64" or self._platform == "aarch64":
                self._cpu_features = ["NEON"]
            logger.debug("cpuinfo not available, using basic detection")
        except Exception as e:
            logger.warning(f"Error detecting CPU features: {e}")

    def _build_recommendations(self) -> HardwareInfo:
        """
        Build hardware recommendations based on detection results.

        Returns
        -------
        HardwareInfo
            Complete hardware info with recommendations.
        """
        info = HardwareInfo()
        info.has_cuda = self._cuda_available

        if self._gpu_info:
            info.gpu_name = self._gpu_info["name"]
            info.vram_total_mb = self._gpu_info["vram_total_mb"]
            info.vram_free_mb = self._gpu_info.get("vram_free_mb")
            info.compute_capability = self._gpu_info["compute_capability"]

        info.cpu_features = self._cpu_features

        # Determine recommendations
        if self._cuda_available and self._gpu_info:
            vram_mb = info.vram_free_mb or info.vram_total_mb

            # GPU available - recommend CUDA
            info.recommended_device = "cuda"
            info.recommended_compute_type = "float16"

            # Recommend model based on VRAM
            if vram_mb >= 10000:
                info.recommended_model = "large-v3"
                info.reason = f"GPU detected ({info.gpu_name}) with {vram_mb // 1024}GB VRAM. Large model recommended for best accuracy."
            elif vram_mb >= 6000:
                info.recommended_model = "distil-large-v3"
                info.reason = f"GPU detected ({info.gpu_name}) with {vram_mb // 1024}GB VRAM. Distil Large model offers good balance of speed and accuracy."
            elif vram_mb >= 5000:
                info.recommended_model = "medium"
                info.reason = f"GPU detected ({info.gpu_name}) with {vram_mb // 1024}GB VRAM. Medium model recommended."
            elif vram_mb >= 3000:
                info.recommended_model = "small"
                info.reason = f"GPU detected ({info.gpu_name}) with {vram_mb // 1024}GB VRAM. Small model recommended for this GPU."
            else:
                info.recommended_model = "base"
                info.recommended_compute_type = "int8"
                info.reason = f"GPU detected ({info.gpu_name}) with limited VRAM. Base model with int8 quantization recommended."
        else:
            # CPU only
            info.recommended_device = "cpu"
            info.recommended_compute_type = "int8"

            # CPU model recommendation based on features
            if "AVX2" in self._cpu_features or "AVX512" in self._cpu_features:
                info.recommended_model = "small"
                info.reason = "CPU detected with AVX2 support. Small model recommended for good performance."
            elif "AVX" in self._cpu_features:
                info.recommended_model = "base"
                info.reason = "CPU detected with AVX support. Base model recommended."
            else:
                info.recommended_model = "tiny"
                info.reason = "CPU detected. Tiny model recommended for compatibility."

        return info

    def get_optimal_compute_type(self, device: str, vram_mb: Optional[int] = None) -> str:
        """
        Get the optimal compute type for a given device.

        Parameters
        ----------
        device
            Target device ("cuda" or "cpu").
        vram_mb
            Available VRAM in MB (for CUDA devices).

        Returns
        -------
        str
            Recommended compute type.
        """
        if device == "cuda":
            if vram_mb and vram_mb >= 4000:
                return "float16"
            else:
                return "int8_float16"
        else:
            # CPU always uses int8 for performance
            return "int8"

    def get_model_vram_requirement(self, model: str) -> Optional[int]:
        """
        Get the VRAM requirement for a model.

        Parameters
        ----------
        model
            Model name.

        Returns
        -------
        int or None
            VRAM requirement in MB, or None if unknown.
        """
        return self.MODEL_VRAM_REQUIREMENTS.get(model)

    def can_run_model(self, model: str, vram_mb: int) -> bool:
        """
        Check if a model can run with available VRAM.

        Parameters
        ----------
        model
            Model name to check.
        vram_mb
            Available VRAM in MB.

        Returns
        -------
        bool
            True if model can run with available VRAM.
        """
        requirement = self.get_model_vram_requirement(model)
        if requirement is None:
            # Unknown model, assume it can run
            return True
        return vram_mb >= requirement


def detect_hardware() -> HardwareInfo:
    """
    Convenience function to perform hardware detection.

    Returns
    -------
    HardwareInfo
        Detected hardware information and recommendations.
    """
    detector = HardwareDetector()
    return detector.detect()


def format_vram_size(mb: Optional[int]) -> str:
    """
    Format VRAM size for display.

    Parameters
    ----------
    mb
        VRAM in megabytes.

    Returns
    -------
    str
        Formatted VRAM string (e.g., "8.0 GB", "Unknown").
    """
    if mb is None:
        return "Unknown"
    if mb >= 1024:
        return f"{mb / 1024:.1f} GB"
    return f"{mb} MB"
