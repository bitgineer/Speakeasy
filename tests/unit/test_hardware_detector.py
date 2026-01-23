"""
Unit tests for hardware detection across different configurations.

This test suite validates the HardwareDetector's ability to correctly
identify and recommend settings for various hardware configurations.
"""

import platform
import pytest
from unittest.mock import Mock, MagicMock, patch
from dataclasses import asdict

from faster_whisper_hotkey.flet_gui.hardware_detector import (
    HardwareDetector,
    HardwareInfo,
    detect_hardware,
    format_vram_size,
)


class TestHardwareDetector:
    """Test hardware detection functionality."""

    def test_init(self):
        """Test HardwareDetector initialization."""
        detector = HardwareDetector()
        assert detector._torch_available is False
        assert detector._cuda_available is False
        assert detector._gpu_info is None
        assert detector._cpu_features == []
        assert detector._platform == platform.system()

    def test_detect_without_torch(self):
        """Test detection when torch is not available."""
        detector = HardwareDetector()
        with patch('builtins.__import__', side_effect=ImportError):
            detector._detect_cuda()

        assert detector._torch_available is False
        assert detector._cuda_available is False

    def test_detect_with_torch_no_cuda(self):
        """Test detection when torch is available but CUDA is not."""
        detector = HardwareDetector()
        mock_torch = MagicMock()
        mock_torch.cuda.is_available.return_value = False
        mock_torch.cuda.device_count.return_value = 0

        with patch('builtins.__import__', return_value=mock_torch):
            detector._detect_cuda()

        assert detector._torch_available is True
        assert detector._cuda_available is False

    def test_detect_with_cuda_gpu(self):
        """Test detection with CUDA GPU available."""
        detector = HardwareDetector()

        # Mock torch with CUDA
        mock_torch = MagicMock()
        mock_torch.cuda.is_available.return_value = True
        mock_torch.cuda.device_count.return_value = 1

        # Mock GPU properties
        mock_props = MagicMock()
        mock_props.total_memory = 8 * 1024 * 1024 * 1024  # 8GB
        mock_props.major = 8
        mock_props.minor = 6
        mock_props.multi_processor_count = 28

        mock_torch.cuda.get_device_name.return_value = "NVIDIA GeForce RTX 3070"
        mock_torch.cuda.get_device_properties.return_value = mock_props
        mock_torch.cuda.mem_get_info.return_value = (7 * 1024 * 1024 * 1024, 8 * 1024 * 1024 * 1024)

        with patch('builtins.__import__', return_value=mock_torch):
            detector._detect_cuda()

        assert detector._torch_available is True
        assert detector._cuda_available is True
        assert detector._gpu_info is not None
        assert detector._gpu_info["name"] == "NVIDIA GeForce RTX 3070"
        assert detector._gpu_info["vram_total_mb"] == 8192
        assert detector._gpu_info["vram_free_mb"] == 7168
        assert detector._gpu_info["compute_capability"] == (8, 6)

    def test_detect_with_multi_gpu(self):
        """Test detection with multiple GPUs."""
        detector = HardwareDetector()

        mock_torch = MagicMock()
        mock_torch.cuda.is_available.return_value = True
        mock_torch.cuda.device_count.return_value = 2

        mock_props = MagicMock()
        mock_props.total_memory = 8 * 1024 * 1024 * 1024
        mock_props.major = 8
        mock_props.minor = 6
        mock_props.multi_processor_count = 28

        mock_torch.cuda.get_device_name.return_value = "NVIDIA GeForce RTX 3070"
        mock_torch.cuda.get_device_properties.return_value = mock_props
        mock_torch.cuda.mem_get_info.return_value = (7 * 1024 * 1024 * 1024, 8 * 1024 * 1024 * 1024)

        with patch('builtins.__import__', return_value=mock_torch):
            detector._detect_cuda()

        assert detector._gpu_info["count"] == 2

    def test_detect_cpu_features_with_cpuinfo(self):
        """Test CPU feature detection with py-cpuinfo available."""
        detector = HardwareDetector()

        mock_cpuinfo = MagicMock()
        mock_cpuinfo.get_cpu_info.return_value = {
            "flags": ["sse", "sse2", "avx", "avx2", "fma"]
        }

        with patch('builtins.__import__', return_value=mock_cpuinfo):
            detector._detect_cpu_features()

        assert "SSE" in detector._cpu_features
        assert "SSE2" in detector._cpu_features
        assert "AVX" in detector._cpu_features
        assert "AVX2" in detector._cpu_features
        assert "FMA" in detector._cpu_features

    def test_detect_cpu_features_arm(self):
        """Test CPU feature detection for ARM processors."""
        detector = HardwareDetector()
        detector._platform = "aarch64"

        mock_cpuinfo = MagicMock()
        mock_cpuinfo.get_cpu_info.return_value = {
            "flags": ["neon", "asimd"]
        }

        with patch('builtins.__import__', return_value=mock_cpuinfo):
            detector._detect_cpu_features()

        assert "NEON" in detector._cpu_features

    def test_detect_cpu_features_fallback_x86(self):
        """Test CPU feature detection fallback for x86_64."""
        detector = HardwareDetector()
        detector._platform = "x86_64"

        with patch('builtins.__import__', side_effect=ImportError):
            detector._detect_cpu_features()

        assert "SSE" in detector._cpu_features
        assert "SSE2" in detector._cpu_features

    def test_detect_cpu_features_fallback_arm(self):
        """Test CPU feature detection fallback for ARM64."""
        detector = HardwareDetector()
        detector._platform = "aarch64"

        with patch('builtins.__import__', side_effect=ImportError):
            detector._detect_cpu_features()

        assert "NEON" in detector._cpu_features


class TestHardwareRecommendations:
    """Test hardware recommendation logic."""

    def test_recommend_high_vram_gpu(self):
        """Test recommendations for high-VRAM GPU."""
        detector = HardwareDetector()
        detector._cuda_available = True
        detector._gpu_info = {
            "name": "NVIDIA GeForce RTX 4090",
            "vram_total_mb": 24 * 1024,
            "vram_free_mb": 22 * 1024,
            "compute_capability": (8, 9),
        }

        info = detector._build_recommendations()

        assert info.has_cuda is True
        assert info.recommended_device == "cuda"
        assert info.recommended_compute_type == "float16"
        assert info.recommended_model == "large-v3"
        assert "24GB VRAM" in info.reason

    def test_recommend_mid_vram_gpu(self):
        """Test recommendations for mid-range VRAM GPU."""
        detector = HardwareDetector()
        detector._cuda_available = True
        detector._gpu_info = {
            "name": "NVIDIA GeForce RTX 3060",
            "vram_total_mb": 12 * 1024,
            "vram_free_mb": 11 * 1024,
            "compute_capability": (8, 6),
        }

        info = detector._build_recommendations()

        assert info.recommended_device == "cuda"
        assert info.recommended_model == "distil-large-v3"
        assert "11GB VRAM" in info.reason

    def test_recommend_low_vram_gpu(self):
        """Test recommendations for low-VRAM GPU."""
        detector = HardwareDetector()
        detector._cuda_available = True
        detector._gpu_info = {
            "name": "NVIDIA GeForce GTX 1050 Ti",
            "vram_total_mb": 4 * 1024,
            "vram_free_mb": 3 * 1024,
            "compute_capability": (6, 1),
        }

        info = detector._build_recommendations()

        assert info.recommended_device == "cuda"
        assert info.recommended_model == "small"
        assert "3GB VRAM" in info.reason

    def test_recommend_very_low_vram_gpu(self):
        """Test recommendations for very low-VRAM GPU."""
        detector = HardwareDetector()
        detector._cuda_available = True
        detector._gpu_info = {
            "name": "NVIDIA GeForce GT 1030",
            "vram_total_mb": 2 * 1024,
            "vram_free_mb": 1500,
            "compute_capability": (6, 1),
        }

        info = detector._build_recommendations()

        assert info.recommended_device == "cuda"
        assert info.recommended_compute_type == "int8"
        assert info.recommended_model == "base"

    def test_recommend_cpu_with_avx2(self):
        """Test CPU recommendations with AVX2 support."""
        detector = HardwareDetector()
        detector._cuda_available = False
        detector._cpu_features = ["SSE", "SSE2", "AVX", "AVX2"]

        info = detector._build_recommendations()

        assert info.recommended_device == "cpu"
        assert info.recommended_compute_type == "int8"
        assert info.recommended_model == "small"
        assert "AVX2" in info.reason

    def test_recommend_cpu_with_avx_only(self):
        """Test CPU recommendations with AVX but not AVX2."""
        detector = HardwareDetector()
        detector._cuda_available = False
        detector._cpu_features = ["SSE", "SSE2", "AVX"]

        info = detector._build_recommendations()

        assert info.recommended_device == "cpu"
        assert info.recommended_model == "base"

    def test_recommend_cpu_basic(self):
        """Test CPU recommendations with basic features."""
        detector = HardwareDetector()
        detector._cuda_available = False
        detector._cpu_features = ["SSE", "SSE2"]

        info = detector._build_recommendations()

        assert info.recommended_device == "cpu"
        assert info.recommended_model == "tiny"


class TestModelVramRequirements:
    """Test model VRAM requirement calculations."""

    def test_get_vram_requirement_known_model(self):
        """Test VRAM requirement for known models."""
        detector = HardwareDetector()

        assert detector.get_model_vram_requirement("large-v3") == 10000
        assert detector.get_model_vram_requirement("medium") == 5000
        assert detector.get_model_vram_requirement("small") == 2000
        assert detector.get_model_vram_requirement("base") == 1000
        assert detector.get_model_vram_requirement("tiny") == 750

    def test_get_vram_requirement_unknown_model(self):
        """Test VRAM requirement for unknown models."""
        detector = HardwareDetector()

        assert detector.get_model_vram_requirement("unknown-model") is None

    def test_can_run_model_sufficient_vram(self):
        """Test if model can run with sufficient VRAM."""
        detector = HardwareDetector()

        assert detector.can_run_model("tiny", 1000) is True
        assert detector.can_run_model("base", 2000) is True
        assert detector.can_run_model("large-v3", 12000) is True

    def test_can_run_model_insufficient_vram(self):
        """Test if model can run with insufficient VRAM."""
        detector = HardwareDetector()

        assert detector.can_run_model("large-v3", 5000) is False
        assert detector.can_run_model("medium", 3000) is False

    def test_can_run_model_unknown_model(self):
        """Test if unknown model can run (should return True)."""
        detector = HardwareDetector()

        assert detector.can_run_model("unknown-model", 100) is True


class TestOptimalComputeType:
    """Test optimal compute type selection."""

    def test_optimal_compute_cuda_high_vram(self):
        """Test compute type for CUDA with high VRAM."""
        detector = HardwareDetector()

        compute_type = detector.get_optimal_compute_type("cuda", 8000)
        assert compute_type == "float16"

    def test_optimal_compute_cuda_low_vram(self):
        """Test compute type for CUDA with low VRAM."""
        detector = HardwareDetector()

        compute_type = detector.get_optimal_compute_type("cuda", 3000)
        assert compute_type == "int8_float16"

    def test_optimal_compute_cuda_no_vram_specified(self):
        """Test compute type for CUDA without VRAM specified."""
        detector = HardwareDetector()

        compute_type = detector.get_optimal_compute_type("cuda", None)
        assert compute_type == "int8_float16"

    def test_optimal_compute_cpu(self):
        """Test compute type for CPU."""
        detector = HardwareDetector()

        compute_type = detector.get_optimal_compute_type("cpu", None)
        assert compute_type == "int8"


class TestHardwareInfoDataclass:
    """Test HardwareInfo dataclass."""

    def test_hardware_info_creation(self):
        """Test creating a HardwareInfo object."""
        info = HardwareInfo(
            has_cuda=True,
            gpu_name="RTX 3070",
            vram_total_mb=8192,
            vram_free_mb=7000,
            compute_capability=(8, 6),
            cpu_features=["AVX2"],
            recommended_device="cuda",
            recommended_compute_type="float16",
            recommended_model="large-v3",
            reason="High-end GPU detected"
        )

        assert info.has_cuda is True
        assert info.gpu_name == "RTX 3070"
        assert info.vram_total_mb == 8192
        assert info.vram_free_mb == 7000
        assert info.compute_capability == (8, 6)
        assert info.cpu_features == ["AVX2"]
        assert info.recommended_device == "cuda"
        assert info.recommended_compute_type == "float16"
        assert info.recommended_model == "large-v3"
        assert info.reason == "High-end GPU detected"

    def test_hardware_info_defaults(self):
        """Test HardwareInfo default values."""
        info = HardwareInfo()

        assert info.has_cuda is False
        assert info.gpu_name is None
        assert info.vram_total_mb is None
        assert info.vram_free_mb is None
        assert info.compute_capability is None
        assert info.cpu_features == []  # Set by __post_init__
        assert info.recommended_device == "cpu"
        assert info.recommended_compute_type == "int8"
        assert info.recommended_model == "base"
        assert info.reason == ""


class TestUtilityFunctions:
    """Test utility functions."""

    def test_format_vram_size_gb(self):
        """Test formatting VRAM in GB."""
        assert format_vram_size(8192) == "8.0 GB"
        assert format_vram_size(1024) == "1.0 GB"
        assert format_vram_size(11264) == "11.0 GB"

    def test_format_vram_size_mb(self):
        """Test formatting VRAM in MB."""
        assert format_vram_size(512) == "512 MB"
        assert format_vram_size(100) == "100 MB"

    def test_format_vram_size_none(self):
        """Test formatting None VRAM."""
        assert format_vram_size(None) == "Unknown"

    def test_detect_hardware_convenience_function(self):
        """Test the convenience detect_hardware function."""
        with patch.object(HardwareDetector, 'detect') as mock_detect:
            mock_info = HardwareInfo(has_cuda=False, recommended_model="tiny")
            mock_detect.return_value = mock_info

            result = detect_hardware()
            assert result == mock_info


class TestFullDetection:
    """Test full detection pipeline with mocked dependencies."""

    def test_full_detection_gpu(self):
        """Test full detection with GPU."""
        detector = HardwareDetector()

        # Mock torch with CUDA
        mock_torch = MagicMock()
        mock_torch.cuda.is_available.return_value = True
        mock_torch.cuda.device_count.return_value = 1

        mock_props = MagicMock()
        mock_props.total_memory = 6 * 1024 * 1024 * 1024
        mock_props.major = 7
        mock_props.minor = 5
        mock_props.multi_processor_count = 20

        mock_torch.cuda.get_device_name.return_value = "NVIDIA GeForce RTX 2060"
        mock_torch.cuda.get_device_properties.return_value = mock_props
        mock_torch.cuda.mem_get_info.return_value = (5 * 1024 * 1024 * 1024, 6 * 1024 * 1024 * 1024)

        # Mock cpuinfo
        mock_cpuinfo = MagicMock()
        mock_cpuinfo.get_cpu_info.return_value = {
            "flags": ["sse", "sse2", "avx", "avx2"]
        }

        def import_side_effect(name, *args, **kwargs):
            if name == "torch":
                return mock_torch
            elif name == "cpuinfo":
                return mock_cpuinfo
            raise ImportError(f"No module named '{name}'")

        with patch('builtins.__import__', side_effect=import_side_effect):
            info = detector.detect()

        assert info.has_cuda is True
        assert "RTX 2060" in info.gpu_name
        assert info.vram_total_mb == 6144
        assert info.recommended_device == "cuda"
        assert "AVX2" in info.cpu_features

    def test_full_detection_cpu_only(self):
        """Test full detection without GPU (CPU only)."""
        detector = HardwareDetector()

        # Mock torch without CUDA
        mock_torch = MagicMock()
        mock_torch.cuda.is_available.return_value = False
        mock_torch.cuda.device_count.return_value = 0

        # Mock cpuinfo
        mock_cpuinfo = MagicMock()
        mock_cpuinfo.get_cpu_info.return_value = {
            "flags": ["sse", "sse2", "avx"]
        }

        def import_side_effect(name, *args, **kwargs):
            if name == "torch":
                return mock_torch
            elif name == "cpuinfo":
                return mock_cpuinfo
            raise ImportError(f"No module named '{name}'")

        with patch('builtins.__import__', side_effect=import_side_effect):
            info = detector.detect()

        assert info.has_cuda is False
        assert info.recommended_device == "cpu"
        assert info.recommended_model == "base"
        assert "AVX" in info.cpu_features


class TestConfigurationCompatibilityMatrix:
    """Test compatibility matrix for different configurations."""

    @pytest.mark.parametrize("vram_gb,expected_models", [
        (24, ["large-v3", "distil-large-v3", "medium", "small", "base", "tiny"]),
        (12, ["large-v3", "distil-large-v3", "medium", "small", "base", "tiny"]),
        (8, ["distil-large-v3", "medium", "small", "base", "tiny"]),
        (6, ["medium", "small", "base", "tiny"]),
        (4, ["small", "base", "tiny"]),
        (2, ["base", "tiny"]),
        (1, ["tiny"]),
    ])
    def test_vram_model_compatibility(self, vram_gb, expected_models):
        """Test which models can run with different VRAM configurations."""
        detector = HardwareDetector()
        vram_mb = vram_gb * 1024

        compatible_models = []
        for model in detector.MODEL_VRAM_REQUIREMENTS.keys():
            if detector.can_run_model(model, vram_mb):
                compatible_models.append(model)

        # All expected models should be compatible
        for expected_model in expected_models:
            assert expected_model in compatible_models, \
                f"Model {expected_model} should run with {vram_gb}GB VRAM"

    @pytest.mark.parametrize("cpu_features,expected_model", [
        (["AVX2", "AVX512"], "small"),
        (["AVX2"], "small"),
        (["AVX"], "base"),
        (["SSE2"], "tiny"),
    ])
    def test_cpu_feature_recommendations(self, cpu_features, expected_model):
        """Test CPU-based model recommendations."""
        detector = HardwareDetector()
        detector._cuda_available = False
        detector._cpu_features = cpu_features

        info = detector._build_recommendations()
        assert info.recommended_model == expected_model


@pytest.mark.unit
class TestCrossPlatformDetection:
    """Tests for cross-platform hardware detection."""

    @pytest.mark.parametrize("platform_name,expected_features", [
        ("x86_64", ["SSE", "SSE2"]),
        ("AMD64", ["SSE", "SSE2"]),
        ("aarch64", ["NEON"]),
        ("arm64", ["NEON"]),
    ])
    def test_platform_detection(self, platform_name, expected_features):
        """Test hardware detection on different platforms."""
        detector = HardwareDetector()
        detector._platform = platform_name

        with patch('builtins.__import__', side_effect=ImportError):
            detector._detect_cpu_features()

        for feature in expected_features:
            assert feature in detector._cpu_features, \
                f"Platform {platform_name} should have {feature}"
