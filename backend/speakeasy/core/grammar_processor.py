"""
Grammar correction processor for post-processing transcriptions.

Uses T5-based models to correct grammar and improve fluency while preserving
the original meaning. Supports lazy loading, sentence-level processing,
and graceful fallback on errors.
"""

import logging
import os
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class ModelStatus(str, Enum):
    """Status of a grammar model."""

    NOT_DOWNLOADED = "not_downloaded"
    DOWNLOADING = "downloading"
    DOWNLOADED = "downloaded"
    LOADING = "loading"
    LOADED = "loaded"
    ERROR = "error"


@dataclass
class GrammarModelInfo:
    """Information about a grammar correction model."""

    id: str
    name: str
    size_mb: int
    vram_gb: float
    description: str
    default: bool = False
    use_safetensors: bool = True
    prompt_template: str = "{text}"  # Default template for input text
    supported_tasks: dict[str, str] = field(default_factory=dict)  # Map task name to template


# Available grammar correction models
# Note: Models must support safetensors format due to torch security requirements
GRAMMAR_MODELS: dict[str, GrammarModelInfo] = {
    "vennify/t5-base-grammar-correction": GrammarModelInfo(
        id="vennify/t5-base-grammar-correction",
        name="T5 Base Grammar Correction",
        size_mb=890,
        vram_gb=2,
        description="Good balance of speed and quality (recommended)",
        default=True,
        use_safetensors=True,
        prompt_template="grammar: {text}",
        supported_tasks={"fix": "grammar: {text}"},
    ),
    "pszemraj/flan-t5-large-grammar-synthesis": GrammarModelInfo(
        id="pszemraj/flan-t5-large-grammar-synthesis",
        name="Flan T5 Large Grammar Synthesis",
        size_mb=3000,
        vram_gb=4,
        description="High quality, larger model",
        default=False,
        use_safetensors=True,
        prompt_template="Instruction: Correct the grammar and spelling mistakes in the following text.\nText: {text}\nCorrection:",
        supported_tasks={
            "fix": "Instruction: Correct the grammar and spelling mistakes in the following text.\nText: {text}\nCorrection:"
        },
    ),
    "grammarly/coedit-xl": GrammarModelInfo(
        id="grammarly/coedit-xl",
        name="Grammarly CoEdit XL",
        size_mb=3000,
        vram_gb=4,
        description="High quality from Grammarly (larger)",
        default=False,
        use_safetensors=True,
        prompt_template="Fix grammatical errors in this sentence: {text}",
        supported_tasks={
            "fix": "Fix grammatical errors in this sentence: {text}",
            "coherence": "Make this sentence more coherent: {text}",
        },
    ),
    "grammarly/coedit-large": GrammarModelInfo(
        id="grammarly/coedit-large",
        name="Grammarly CoEdit Large",
        size_mb=1000,
        vram_gb=2,
        description="Fast & high quality (recommended)",
        default=False,
        use_safetensors=True,
        prompt_template="Fix grammatical errors in this sentence: {text}",
        supported_tasks={
            "fix": "Fix grammatical errors in this sentence: {text}",
            "coherence": "Make this sentence more coherent: {text}",
        },
    ),
    "google/flan-t5-small": GrammarModelInfo(
        id="google/flan-t5-small",
        name="Google Flan T5 Small",
        size_mb=300,
        vram_gb=1,
        description="Fast & lightweight (CPU friendly)",
        default=False,
        use_safetensors=True,
        prompt_template="Instruction: Correct the grammar and spelling mistakes in the following text.\nText: {text}\nCorrection:",
        supported_tasks={
            "fix": "Instruction: Correct the grammar and spelling mistakes in the following text.\nText: {text}\nCorrection:"
        },
    ),
    "google/flan-t5-base": GrammarModelInfo(
        id="google/flan-t5-base",
        name="Google Flan T5 Base",
        size_mb=990,
        vram_gb=2,
        description="Balanced speed/quality",
        default=False,
        use_safetensors=True,
        prompt_template="Instruction: Correct the grammar and spelling mistakes in the following text.\nText: {text}\nCorrection:",
        supported_tasks={
            "fix": "Instruction: Correct the grammar and spelling mistakes in the following text.\nText: {text}\nCorrection:"
        },
    ),
}


def get_cache_dir() -> Path:
    """Get the HuggingFace cache directory."""
    cache_dir = os.environ.get("HF_HOME", None)
    if cache_dir:
        return Path(cache_dir) / "hub"

    # Default HuggingFace cache location
    return Path.home() / ".cache" / "huggingface" / "hub"


def is_model_downloaded(model_id: str) -> bool:
    """
    Check if a model is already downloaded.

    Args:
        model_id: HuggingFace model identifier

    Returns:
        True if model files exist in cache
    """
    cache_dir = get_cache_dir()
    # HuggingFace stores models with -- instead of /
    model_folder = f"models--{model_id.replace('/', '--')}"
    model_path = cache_dir / model_folder

    if not model_path.exists():
        return False

    # Check if there are snapshot files
    snapshots_dir = model_path / "snapshots"
    if not snapshots_dir.exists():
        return False

    # Check if any snapshot has model files
    for snapshot in snapshots_dir.iterdir():
        if snapshot.is_dir():
            # Look for model weights
            has_weights = (
                any(snapshot.glob("*.safetensors"))
                or any(snapshot.glob("*.bin"))
                or any(snapshot.glob("pytorch_model*"))
            )
            if has_weights:
                return True

    return False


def get_model_download_size(model_id: str) -> Optional[int]:
    """
    Get the download size of a model in bytes.

    Args:
        model_id: HuggingFace model identifier

    Returns:
        Size in bytes or None if unknown
    """
    if model_id in GRAMMAR_MODELS:
        return GRAMMAR_MODELS[model_id].size_mb * 1024 * 1024
    return None


class GrammarProcessor:
    """
    Grammar correction processor using T5-based models.

    Features:
    - Lazy loading (model loads on first use)
    - Sentence-level processing for speed
    - Graceful fallback on errors
    - Manual unloading to free VRAM
    - Download progress tracking
    """

    def __init__(
        self,
        model_name: str = "grammarly/coedit-base",
        device: str = "auto",
    ):
        """
        Initialize the grammar processor.

        Args:
            model_name: HuggingFace model identifier
            device: Device to use ('auto', 'cuda', or 'cpu')
        """
        self.model_name = model_name
        self.device = device
        self._model = None
        self._tokenizer = None
        self._status = ModelStatus.NOT_DOWNLOADED
        self._error_message: Optional[str] = None
        self._download_progress: float = 0.0

        # Check if already downloaded
        if is_model_downloaded(model_name):
            self._status = ModelStatus.DOWNLOADED

    @property
    def status(self) -> ModelStatus:
        """Get current model status."""
        return self._status

    @property
    def error_message(self) -> Optional[str]:
        """Get error message if status is ERROR."""
        return self._error_message

    @property
    def download_progress(self) -> float:
        """Get download progress (0.0 to 1.0)."""
        return self._download_progress

    @property
    def is_loaded(self) -> bool:
        """Check if the model is loaded."""
        return self._status == ModelStatus.LOADED

    @property
    def is_downloaded(self) -> bool:
        """Check if the model is downloaded."""
        return self._status in (ModelStatus.DOWNLOADED, ModelStatus.LOADING, ModelStatus.LOADED)

    def _get_model_info(self) -> Optional[GrammarModelInfo]:
        """Get model info for current model."""
        return GRAMMAR_MODELS.get(self.model_name)

    def load(self) -> None:
        """
        Load the grammar model and tokenizer.

        Called on first use when grammar correction is enabled.
        """
        # Prevent re-loading if already loaded or currently loading
        if self._status in (ModelStatus.LOADED, ModelStatus.LOADING, ModelStatus.DOWNLOADING):
            return

        try:
            self._status = ModelStatus.LOADING
            self._error_message = None
            model_info = self._get_model_info()

            # Check if we need to download first
            if not is_model_downloaded(self.model_name):
                self._status = ModelStatus.DOWNLOADING
                self._download_progress = 0.0
                logger.info(f"Downloading grammar model: {self.model_name}")
            else:
                self._status = ModelStatus.LOADING

            # Lazy import to avoid loading torch unless needed
            from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
            import torch

            # Determine device
            device = self._get_device()

            logger.info(f"Loading grammar model: {self.model_name} on {device}")

            # Load with safetensors if supported
            load_kwargs = {}
            if model_info and model_info.use_safetensors:
                load_kwargs["use_safetensors"] = True

            # Load tokenizer and model (downloads if not cached)
            self._tokenizer = AutoTokenizer.from_pretrained(self.model_name)

            # Update status after tokenizer download
            if self._status == ModelStatus.DOWNLOADING:
                self._download_progress = 0.3
                logger.info("Tokenizer downloaded, downloading model weights...")

            self._model = AutoModelForSeq2SeqLM.from_pretrained(
                self.model_name,
                torch_dtype=torch.float16 if device == "cuda" else torch.float32,
                **load_kwargs,
            )

            if self._status == ModelStatus.DOWNLOADING:
                self._download_progress = 0.9
                logger.info("Model weights downloaded, loading to device...")

            self._status = ModelStatus.LOADING
            self._model.to(device)
            self._model.eval()  # Set to evaluation mode

            self._status = ModelStatus.LOADED
            self._download_progress = 1.0
            logger.info(f"Grammar model loaded successfully on {device}")

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Failed to load grammar model: {error_msg}")
            self._model = None
            self._tokenizer = None
            self._status = ModelStatus.ERROR
            self._error_message = error_msg
            raise

    def unload(self) -> None:
        """Unload the model and free memory."""
        if self._model is not None:
            # Clear CUDA cache if using GPU
            try:
                import torch

                if torch.cuda.is_available():
                    del self._model
                    del self._tokenizer
                    torch.cuda.empty_cache()
            except Exception:
                pass

        self._model = None
        self._tokenizer = None

        # Reset to downloaded state if files still exist
        if is_model_downloaded(self.model_name):
            self._status = ModelStatus.DOWNLOADED
        else:
            self._status = ModelStatus.NOT_DOWNLOADED

        self._error_message = None
        logger.info("Grammar model unloaded")

    def _get_device(self) -> str:
        """
        Determine which device to use.

        Returns:
            'cuda' if available, 'cpu' otherwise
        """
        if self.device == "cpu":
            return "cpu"

        if self.device == "cuda":
            import torch

            if not torch.cuda.is_available():
                logger.warning("CUDA requested but not available, falling back to CPU")
                return "cpu"
            return "cuda"

        # Auto: try CUDA first
        import torch

        if torch.cuda.is_available():
            return "cuda"
        return "cpu"

    def _split_into_sentences(self, text: str) -> list[str]:
        """
        Split text into sentences for batch processing.

        Uses a simple approach with sentence-ending punctuation.
        This is fast and works well for most cases.

        Args:
            text: Input text

        Returns:
            List of sentences
        """
        import re

        # Split on sentence boundaries while keeping the delimiter
        # This preserves punctuation in the output
        sentences = re.split(r"(?<=[.!?])\s+", text.strip())
        return [s.strip() for s in sentences if s.strip()]

    def correct(
        self,
        text: str,
        task: str = "fix",
        max_length: int = 512,
        num_beams: int = 1,
    ) -> str:
        """
        Correct grammar in the given text.

        Processes text using batching for better performance on GPUs.
        Falls back to original text if model fails.

        Args:
            text: Input text to correct
            task: Task to perform ("fix", "coherence", etc.)
            max_length: Maximum output length per sentence
            num_beams: Number of beams for beam search (1 = greedy, faster)

        Returns:
            Grammar-corrected text, or original text on error
        """
        if not text or not text.strip():
            return text

        # Ensure model is loaded
        if not self.is_loaded:
            try:
                self.load()
            except Exception as e:
                logger.warning(f"Failed to load grammar model, using original text: {e}")
                return text

        # Get model info for prompt template
        model_info = self._get_model_info()
        template = "{text}"

        if model_info:
            if task in model_info.supported_tasks:
                template = model_info.supported_tasks[task]
            else:
                logger.warning(
                    f"Task '{task}' not supported by model '{self.model_name}', falling back to default"
                )
                template = model_info.prompt_template

        # Split into sentences
        sentences = self._split_into_sentences(text)
        if not sentences:
            return text

        device = self._get_device()

        try:
            # Prepare batch inputs
            input_texts = [template.format(text=s) for s in sentences]

            # Tokenize batch
            inputs = self._tokenizer(
                input_texts,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=512,
            )

            # Move to correct device
            inputs = {k: v.to(device) for k, v in inputs.items()}

            # Generate correction (no gradient computation needed)
            import torch

            with torch.no_grad():
                outputs = self._model.generate(
                    **inputs,
                    max_length=max_length,
                    num_beams=num_beams,
                    early_stopping=(num_beams > 1),
                    do_sample=False,
                )

            # Decode batch output
            corrected_sentences = self._tokenizer.batch_decode(outputs, skip_special_tokens=True)

            # Fallback for empty generations (shouldn't happen often)
            final_sentences = []
            for original, corrected in zip(sentences, corrected_sentences):
                if corrected and corrected.strip():
                    final_sentences.append(corrected)
                else:
                    final_sentences.append(original)

            # Rejoin sentences
            corrected_text = " ".join(final_sentences)
            return corrected_text

        except Exception as e:
            logger.error(f"Failed to correct batch, using original: {e}")
            return text


def get_available_grammar_models() -> dict[str, dict]:
    """
    Get information about available grammar correction models.

    Returns:
        Dictionary of model info keyed by model name
    """
    result = {}
    for model_id, info in GRAMMAR_MODELS.items():
        result[model_id] = {
            "id": info.id,
            "name": info.name,
            "size_mb": info.size_mb,
            "vram_gb": info.vram_gb,
            "description": info.description,
            "default": info.default,
            "downloaded": is_model_downloaded(model_id),
        }
    return result


def get_default_grammar_model() -> str:
    """
    Get the default grammar model.

    Returns:
        Default model name
    """
    for model_id, info in GRAMMAR_MODELS.items():
        if info.default:
            return model_id
    return "vennify/t5-base-grammar-correction"
