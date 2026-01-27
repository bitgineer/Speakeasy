"""
Comprehensive tests for ModelWrapper and related functions.

Tests cover:
- ModelType enum values
- ModelWrapper initialization for all model types
- Model loading with mocked backends
- Model unloading and cleanup
- Transcription dispatch for each model type
- TranscriptionResult dataclass
- GPU info detection
- Model recommendation logic
"""

import gc
from dataclasses import fields
from unittest.mock import MagicMock, patch

import numpy as np
import pytest


# ============================================================================
# Mock Classes for Model Backends
# ============================================================================


class MockWhisperModel:
    """Mock for faster_whisper.WhisperModel."""

    def __init__(self, model_size_or_path, device="cuda", compute_type="float16"):
        self.model_size_or_path = model_size_or_path
        self.device = device
        self.compute_type = compute_type

    def transcribe(self, audio, beam_size=5, **kwargs):
        """Return mock transcription segments."""

        class MockSegment:
            text = " Test transcription from Whisper "

        return [MockSegment()], {"language": "en"}


class MockASRModel:
    """Mock for nemo.collections.asr.models.ASRModel."""

    @classmethod
    def from_pretrained(cls, model_name, map_location=None):
        instance = cls()
        instance.model_name = model_name
        instance.map_location = map_location
        return instance

    def eval(self):
        return self

    def transcribe(self, audio_list):
        """Return mock transcription results."""

        class MockResult:
            text = "Test transcription from Parakeet"

        return [MockResult()]


class MockEncDecMultiTaskModel:
    """Mock for nemo.collections.asr.models.EncDecMultiTaskModel."""

    @classmethod
    def from_pretrained(cls, model_name, map_location=None):
        instance = cls()
        instance.model_name = model_name
        instance.map_location = map_location
        return instance

    def eval(self):
        return self

    def transcribe(self, audio, source_lang="en", target_lang="en"):
        """Return mock transcription results."""

        class MockResult:
            text = "Test transcription from Canary"

        return [MockResult()]


class MockVoxtralModel:
    """Mock for transformers.VoxtralForConditionalGeneration."""

    device = "cuda"

    @classmethod
    def from_pretrained(cls, model_name, **kwargs):
        instance = cls()
        instance.model_name = model_name
        instance.kwargs = kwargs
        return instance

    def eval(self):
        return self

    def generate(self, input_features, input_ids, **kwargs):
        """Return mock generated token IDs."""
        return [[1, 2, 3, 4, 5]]


class MockAutoProcessor:
    """Mock for transformers.AutoProcessor."""

    class MockTokenizer:
        class MockInnerTokenizer:
            @staticmethod
            def encode_transcription(request):
                class MockTokens:
                    tokens = [1, 2, 3]

                return MockTokens()

        tokenizer = MockInnerTokenizer()

    class MockFeatureExtractor:
        def __call__(self, audio, sampling_rate, return_tensors):
            class MockFeatures:
                input_features = MagicMock()
                input_features.to = MagicMock(return_value=input_features)

            return MockFeatures()

    tokenizer = MockTokenizer()
    feature_extractor = MockFeatureExtractor()

    @classmethod
    def from_pretrained(cls, model_name):
        return cls()

    def batch_decode(self, ids, skip_special_tokens=True):
        return ["Test transcription from Voxtral"]


class MockTranscriptionRequest:
    """Mock for mistral_common TranscriptionRequest."""

    language = None

    @classmethod
    def from_openai(cls, request_dict):
        instance = cls()
        instance.request_dict = request_dict
        return instance


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_torch_cuda():
    """Mock torch.cuda with CUDA available."""
    with (
        patch("torch.cuda.is_available", return_value=True),
        patch("torch.cuda.current_device", return_value=0),
        patch("torch.cuda.get_device_properties") as mock_props,
        patch("torch.cuda.empty_cache"),
    ):
        mock_props.return_value = MagicMock(
            name="NVIDIA GeForce RTX 3080",
            total_memory=10 * 1024**3,  # 10 GB
        )
        yield mock_props


@pytest.fixture
def mock_torch_no_cuda():
    """Mock torch.cuda with CUDA not available."""
    with patch("torch.cuda.is_available", return_value=False):
        yield


@pytest.fixture
def mock_whisper_module():
    """Mock faster_whisper module."""
    mock_module = MagicMock()
    mock_module.WhisperModel = MockWhisperModel
    with patch.dict("sys.modules", {"faster_whisper": mock_module}):
        yield mock_module


@pytest.fixture
def mock_nemo_module():
    """Mock nemo.collections.asr.models module."""
    mock_asr = MagicMock()
    mock_asr.ASRModel = MockASRModel
    mock_asr.EncDecMultiTaskModel = MockEncDecMultiTaskModel

    mock_collections = MagicMock()
    mock_collections.asr = MagicMock()
    mock_collections.asr.models = mock_asr

    mock_nemo = MagicMock()
    mock_nemo.collections = mock_collections

    with patch.dict(
        "sys.modules",
        {
            "nemo": mock_nemo,
            "nemo.collections": mock_collections,
            "nemo.collections.asr": mock_collections.asr,
            "nemo.collections.asr.models": mock_asr,
        },
    ):
        yield mock_asr


@pytest.fixture
def mock_transformers_module():
    """Mock transformers module for Voxtral."""
    mock_module = MagicMock()
    mock_module.VoxtralForConditionalGeneration = MockVoxtralModel
    mock_module.AutoProcessor = MockAutoProcessor
    mock_module.BitsAndBytesConfig = MagicMock()

    with patch.dict("sys.modules", {"transformers": mock_module}):
        yield mock_module


@pytest.fixture
def mock_mistral_module():
    """Mock mistral_common module."""
    mock_request = MagicMock()
    mock_request.TranscriptionRequest = MockTranscriptionRequest

    mock_protocol = MagicMock()
    mock_protocol.transcription = MagicMock()
    mock_protocol.transcription.request = mock_request

    mock_mistral = MagicMock()
    mock_mistral.protocol = mock_protocol

    mock_pydantic = MagicMock()
    mock_pydantic.LanguageAlpha2 = str

    with patch.dict(
        "sys.modules",
        {
            "mistral_common": mock_mistral,
            "mistral_common.protocol": mock_protocol,
            "mistral_common.protocol.transcription": mock_protocol.transcription,
            "mistral_common.protocol.transcription.request": mock_request,
            "pydantic_extra_types": mock_pydantic,
            "pydantic_extra_types.language_code": mock_pydantic,
        },
    ):
        yield


@pytest.fixture
def mock_hf_download():
    """Mock huggingface_hub.snapshot_download."""
    with patch("huggingface_hub.snapshot_download", return_value="/mock/model/path") as mock:
        yield mock


@pytest.fixture
def sample_audio():
    """Provide sample audio data for transcription tests."""
    return np.random.randn(16000).astype(np.float32)


# ============================================================================
# Test: ModelType Enum
# ============================================================================


class TestModelTypeEnum:
    """Tests for ModelType enum."""

    def test_model_type_enum_values(self):
        """Test that all 4 model types exist with correct values."""
        from speakeasy.core.models import ModelType

        assert ModelType.WHISPER.value == "whisper"
        assert ModelType.PARAKEET.value == "parakeet"
        assert ModelType.CANARY.value == "canary"
        assert ModelType.VOXTRAL.value == "voxtral"

        # Verify exactly 4 types
        assert len(ModelType) == 4


# ============================================================================
# Test: ModelWrapper Initialization
# ============================================================================


class TestModelWrapperInit:
    """Tests for ModelWrapper initialization."""

    def test_init_whisper(self):
        """Test creating wrapper with WHISPER type."""
        from speakeasy.core.models import ModelType, ModelWrapper

        wrapper = ModelWrapper(
            model_type="whisper",
            model_name="tiny",
            device="cuda",
            compute_type="float16",
        )

        assert wrapper.model_type == ModelType.WHISPER
        assert wrapper.model_name == "tiny"
        assert wrapper.device == "cuda"
        assert wrapper.compute_type == "float16"
        assert wrapper._model is None
        assert wrapper._loaded is False

    def test_init_parakeet(self):
        """Test creating wrapper with PARAKEET type."""
        from speakeasy.core.models import ModelType, ModelWrapper

        wrapper = ModelWrapper(
            model_type="parakeet",
            model_name="nvidia/parakeet-tdt-0.6b-v3",
            device="cuda",
        )

        assert wrapper.model_type == ModelType.PARAKEET
        assert wrapper.model_name == "nvidia/parakeet-tdt-0.6b-v3"

    def test_init_canary(self):
        """Test creating wrapper with CANARY type."""
        from speakeasy.core.models import ModelType, ModelWrapper

        wrapper = ModelWrapper(
            model_type="canary",
            model_name="nvidia/canary-1b-v2",
            device="cuda",
        )

        assert wrapper.model_type == ModelType.CANARY
        assert wrapper.model_name == "nvidia/canary-1b-v2"

    def test_init_voxtral(self):
        """Test creating wrapper with VOXTRAL type."""
        from speakeasy.core.models import ModelType, ModelWrapper

        wrapper = ModelWrapper(
            model_type="voxtral",
            model_name="mistralai/Voxtral-Mini-3B-2507",
            device="cuda",
        )

        assert wrapper.model_type == ModelType.VOXTRAL
        assert wrapper.model_name == "mistralai/Voxtral-Mini-3B-2507"

    def test_is_loaded_false_initially(self):
        """Test that is_loaded property returns False before load()."""
        from speakeasy.core.models import ModelWrapper

        wrapper = ModelWrapper(
            model_type="whisper",
            model_name="tiny",
        )

        assert wrapper.is_loaded is False


# ============================================================================
# Test: Model Loading
# ============================================================================


class TestModelLoading:
    """Tests for model loading functionality."""

    def test_load_whisper(self, mock_whisper_module, mock_torch_cuda):
        """Test loading Whisper model calls faster_whisper.WhisperModel."""
        from speakeasy.core.models import ModelWrapper

        wrapper = ModelWrapper(
            model_type="whisper",
            model_name="tiny",
            device="cuda",
            compute_type="float16",
        )

        wrapper.load()

        assert wrapper.is_loaded is True
        assert wrapper._model is not None
        assert isinstance(wrapper._model, MockWhisperModel)
        assert wrapper._model.model_size_or_path == "tiny"
        assert wrapper._model.device == "cuda"
        assert wrapper._model.compute_type == "float16"

    def test_load_parakeet(self, mock_nemo_module, mock_torch_cuda):
        """Test loading Parakeet model calls nemo ASRModel.from_pretrained."""
        from speakeasy.core.models import ModelWrapper

        wrapper = ModelWrapper(
            model_type="parakeet",
            model_name="nvidia/parakeet-tdt-0.6b-v3",
            device="cuda",
        )

        wrapper.load()

        assert wrapper.is_loaded is True
        assert wrapper._model is not None
        assert isinstance(wrapper._model, MockASRModel)
        assert wrapper._model.model_name == "nvidia/parakeet-tdt-0.6b-v3"

    def test_load_canary(self, mock_nemo_module, mock_torch_cuda):
        """Test loading Canary model calls nemo EncDecMultiTaskModel."""
        from speakeasy.core.models import ModelWrapper

        wrapper = ModelWrapper(
            model_type="canary",
            model_name="nvidia/canary-1b-v2",
            device="cuda",
        )

        wrapper.load()

        assert wrapper.is_loaded is True
        assert wrapper._model is not None
        assert isinstance(wrapper._model, MockEncDecMultiTaskModel)
        assert wrapper._model.model_name == "nvidia/canary-1b-v2"

    def test_load_voxtral(
        self,
        mock_transformers_module,
        mock_mistral_module,
        mock_torch_cuda,
    ):
        """Test loading Voxtral model calls transformers with config."""
        from speakeasy.core.models import ModelWrapper

        # Patch torch for dtype mapping
        with patch("torch.float16", "float16"):
            wrapper = ModelWrapper(
                model_type="voxtral",
                model_name="mistralai/Voxtral-Mini-3B-2507",
                device="cuda",
                compute_type="float16",
            )

            wrapper.load()

            assert wrapper.is_loaded is True
            assert wrapper._model is not None
            assert wrapper._processor is not None

    def test_load_already_loaded(self, mock_whisper_module, mock_torch_cuda, caplog):
        """Test that loading an already loaded model is a no-op and logs info."""
        from speakeasy.core.models import ModelWrapper

        wrapper = ModelWrapper(
            model_type="whisper",
            model_name="tiny",
            device="cuda",
        )

        # First load
        wrapper.load()
        first_model = wrapper._model

        # Second load should be no-op
        import logging

        with caplog.at_level(logging.INFO):
            wrapper.load()

        assert "already loaded" in caplog.text
        assert wrapper._model is first_model  # Same instance


# ============================================================================
# Test: Model Unloading
# ============================================================================


class TestModelUnloading:
    """Tests for model unloading functionality."""

    def test_unload_clears_model(self, mock_whisper_module, mock_torch_cuda):
        """Test that unload() sets _model to None and calls gc.collect."""
        from speakeasy.core.models import ModelWrapper

        wrapper = ModelWrapper(
            model_type="whisper",
            model_name="tiny",
            device="cuda",
        )

        wrapper.load()
        assert wrapper._model is not None
        assert wrapper.is_loaded is True

        with patch("gc.collect") as mock_gc:
            wrapper.unload()

            assert wrapper._model is None
            assert wrapper._processor is None
            assert wrapper.is_loaded is False
            mock_gc.assert_called_once()


# ============================================================================
# Test: Transcription
# ============================================================================


class TestTranscription:
    """Tests for transcription functionality."""

    def test_transcribe_whisper(self, mock_whisper_module, mock_torch_cuda, sample_audio):
        """Test transcription with Whisper dispatches to correct method."""
        from speakeasy.core.models import ModelWrapper

        wrapper = ModelWrapper(
            model_type="whisper",
            model_name="tiny",
            device="cuda",
        )
        wrapper.load()

        result = wrapper.transcribe(sample_audio, sample_rate=16000, language="en")

        assert result.text == "Test transcription from Whisper"
        assert result.model_used == "tiny"
        assert result.duration_ms >= 0

    def test_transcribe_parakeet(self, mock_nemo_module, mock_torch_cuda, sample_audio):
        """Test transcription with Parakeet dispatches to correct method."""
        from speakeasy.core.models import ModelWrapper

        # Mock torch.inference_mode
        with patch("torch.inference_mode"):
            wrapper = ModelWrapper(
                model_type="parakeet",
                model_name="nvidia/parakeet-tdt-0.6b-v3",
                device="cuda",
            )
            wrapper.load()

            result = wrapper.transcribe(sample_audio, sample_rate=16000)

            assert result.text == "Test transcription from Parakeet"
            assert result.model_used == "nvidia/parakeet-tdt-0.6b-v3"

    def test_transcribe_canary(self, mock_nemo_module, mock_torch_cuda, sample_audio):
        """Test transcription with Canary dispatches to correct method."""
        from speakeasy.core.models import ModelWrapper

        # Mock soundfile for temp file writing
        with patch("soundfile.write"):
            wrapper = ModelWrapper(
                model_type="canary",
                model_name="nvidia/canary-1b-v2",
                device="cuda",
            )
            wrapper.load()

            result = wrapper.transcribe(sample_audio, sample_rate=16000, language="en-en")

            assert result.text == "Test transcription from Canary"
            assert result.model_used == "nvidia/canary-1b-v2"

    def test_transcribe_voxtral(
        self,
        mock_transformers_module,
        mock_mistral_module,
        mock_torch_cuda,
        sample_audio,
    ):
        """Test transcription with Voxtral dispatches to correct method."""
        from speakeasy.core.models import ModelWrapper

        with (
            patch("torch.float16", "float16"),
            patch("torch.no_grad"),
            patch("torch.tensor") as mock_tensor,
            patch("soundfile.write"),
        ):
            mock_tensor.return_value = MagicMock()

            wrapper = ModelWrapper(
                model_type="voxtral",
                model_name="mistralai/Voxtral-Mini-3B-2507",
                device="cuda",
                compute_type="float16",
            )
            wrapper.load()

            # Mock the processor's batch_decode
            wrapper._processor.batch_decode = MagicMock(
                return_value=["Test transcription from Voxtral"]
            )

            result = wrapper.transcribe(sample_audio, sample_rate=16000)

            assert "Voxtral" in result.text or result.text != ""
            assert result.model_used == "mistralai/Voxtral-Mini-3B-2507"

    def test_transcribe_not_loaded(self, sample_audio):
        """Test that transcribing without loading raises RuntimeError."""
        from speakeasy.core.models import ModelWrapper

        wrapper = ModelWrapper(
            model_type="whisper",
            model_name="tiny",
        )

        with pytest.raises(RuntimeError, match="Model not loaded"):
            wrapper.transcribe(sample_audio)


# ============================================================================
# Test: TranscriptionResult Dataclass
# ============================================================================


class TestTranscriptionResult:
    """Tests for TranscriptionResult dataclass."""

    def test_transcription_result_dataclass(self):
        """Test that TranscriptionResult fields are accessible."""
        from speakeasy.core.models import TranscriptionResult

        result = TranscriptionResult(
            text="Hello world",
            duration_ms=150,
            language="en",
            model_used="tiny",
        )

        assert result.text == "Hello world"
        assert result.duration_ms == 150
        assert result.language == "en"
        assert result.model_used == "tiny"

        # Verify it's a dataclass with expected fields
        field_names = {f.name for f in fields(result)}
        assert field_names == {"text", "duration_ms", "language", "model_used"}

    def test_transcription_result_optional_fields(self):
        """Test TranscriptionResult with optional fields as None."""
        from speakeasy.core.models import TranscriptionResult

        result = TranscriptionResult(
            text="Test",
            duration_ms=100,
        )

        assert result.text == "Test"
        assert result.duration_ms == 100
        assert result.language is None
        assert result.model_used is None


# ============================================================================
# Test: GPU Info Detection
# ============================================================================


class TestGPUInfo:
    """Tests for get_gpu_info function."""

    def test_get_gpu_info_with_cuda(self):
        """Test get_gpu_info returns GPU details when CUDA is available."""
        from speakeasy.core.models import get_gpu_info

        mock_props = MagicMock()
        mock_props.name = "NVIDIA GeForce RTX 3080"
        mock_props.total_memory = 10 * 1024**3  # 10 GB

        with (
            patch("torch.cuda.is_available", return_value=True),
            patch("torch.cuda.current_device", return_value=0),
            patch("torch.cuda.get_device_properties", return_value=mock_props),
            patch("torch.version.cuda", "12.1"),
        ):
            info = get_gpu_info()

            assert info["available"] is True
            assert info["name"] == "NVIDIA GeForce RTX 3080"
            assert info["vram_gb"] == 10.0
            assert info["cuda_version"] == "12.1"

    def test_get_gpu_info_no_cuda(self):
        """Test get_gpu_info returns available=False when no CUDA."""
        from speakeasy.core.models import get_gpu_info

        with patch("torch.cuda.is_available", return_value=False):
            info = get_gpu_info()

            assert info["available"] is False
            assert info["name"] is None
            assert info["vram_gb"] == 0


# ============================================================================
# Test: Model Recommendation
# ============================================================================


class TestModelRecommendation:
    """Tests for recommend_model function."""

    def test_recommend_model_high_vram(self):
        """Test voxtral is recommended for 10GB+ VRAM."""
        from speakeasy.core.models import recommend_model

        model_type, model_name = recommend_model(vram_gb=12.0)

        assert model_type == "voxtral"
        assert "Voxtral" in model_name

    def test_recommend_model_medium_vram(self):
        """Test parakeet is recommended for 4-6GB VRAM."""
        from speakeasy.core.models import recommend_model

        model_type, model_name = recommend_model(vram_gb=5.0)

        assert model_type == "parakeet"
        assert "parakeet" in model_name

    def test_recommend_model_low_vram(self):
        """Test whisper tiny is recommended for <2GB VRAM."""
        from speakeasy.core.models import recommend_model

        model_type, model_name = recommend_model(vram_gb=1.5)

        assert model_type == "whisper"
        assert model_name == "tiny"

    def test_recommend_model_translation(self):
        """Test canary is recommended when translation is needed."""
        from speakeasy.core.models import recommend_model

        model_type, model_name = recommend_model(vram_gb=8.0, needs_translation=True)

        assert model_type == "canary"
        assert "canary" in model_name

    def test_recommend_model_2gb_vram(self):
        """Test whisper small is recommended for 2-4GB VRAM."""
        from speakeasy.core.models import recommend_model

        model_type, model_name = recommend_model(vram_gb=3.0)

        assert model_type == "whisper"
        assert model_name == "small"

    def test_recommend_model_boundary_10gb(self):
        """Test boundary condition at exactly 10GB VRAM."""
        from speakeasy.core.models import recommend_model

        model_type, model_name = recommend_model(vram_gb=10.0)

        assert model_type == "voxtral"

    def test_recommend_model_boundary_6gb_no_translation(self):
        """Test 6GB without translation gets parakeet, not canary."""
        from speakeasy.core.models import recommend_model

        model_type, model_name = recommend_model(vram_gb=6.0, needs_translation=False)

        # 6GB >= 4GB threshold, so parakeet
        assert model_type == "parakeet"
