"""
Automatic model selector for faster-whisper-hotkey.

This module provides intelligent model selection based on hardware,
language preferences, and usage patterns.

Classes
-------
ModelRecommendation
    Data class containing model recommendation details.

ModelSelector
    Smart recommendation engine for model selection.
"""

import logging
from dataclasses import dataclass
from typing import Optional, List, Dict

from .hardware_detector import HardwareDetector, HardwareInfo
from .model_download import ModelDownloadManager, get_model_download_manager, ModelInfo

logger = logging.getLogger(__name__)


@dataclass
class ModelRecommendation:
    """
    Model recommendation with reasoning.

    Attributes
    ----------
    model_name
        Recommended model identifier.
    display_name
        Human-readable model name.
    reason
        Explanation for this recommendation.
    confidence
        Confidence score (0-1) for this recommendation.
    alternatives
        List of alternative model recommendations.
    estimated_speed
        Estimated transcription speed rating (1-10).
    estimated_accuracy
        Estimated transcription accuracy rating (1-10).
    """
    model_name: str
    display_name: str
    reason: str
    confidence: float = 1.0
    alternatives: List[str] = None
    estimated_speed: int = 5
    estimated_accuracy: int = 5

    def __post_init__(self):
        if self.alternatives is None:
            self.alternatives = []


class ModelSelector:
    """
    Smart model recommendation engine.

    This class analyzes:
    - Available hardware (GPU/CPU, VRAM)
    - User's language preference
    - Whether translation is needed
    - Performance requirements (speed vs accuracy)

    And provides intelligent model recommendations.
    """

    # Model characteristics for recommendation
    MODEL_CHARACTERISTICS = {
        "large-v3": {
            "speed": 3,
            "accuracy": 10,
            "vram_requirement": 10000,
            "is_multilingual": True,
            "best_for": "highest_accuracy",
        },
        "large-v2": {
            "speed": 3,
            "accuracy": 9,
            "vram_requirement": 10000,
            "is_multilingual": True,
            "best_for": "high_accuracy",
        },
        "medium": {
            "speed": 5,
            "accuracy": 8,
            "vram_requirement": 5000,
            "is_multilingual": True,
            "best_for": "balanced",
        },
        "medium.en": {
            "speed": 6,
            "accuracy": 8,
            "vram_requirement": 5000,
            "is_multilingual": False,
            "best_for": "english_balanced",
        },
        "small": {
            "speed": 7,
            "accuracy": 7,
            "vram_requirement": 2000,
            "is_multilingual": True,
            "best_for": "fast",
        },
        "small.en": {
            "speed": 8,
            "accuracy": 7,
            "vram_requirement": 2000,
            "is_multilingual": False,
            "best_for": "english_fast",
        },
        "base": {
            "speed": 8,
            "accuracy": 6,
            "vram_requirement": 1000,
            "is_multilingual": True,
            "best_for": "very_fast",
        },
        "base.en": {
            "speed": 9,
            "accuracy": 6,
            "vram_requirement": 1000,
            "is_multilingual": False,
            "best_for": "english_very_fast",
        },
        "tiny": {
            "speed": 10,
            "accuracy": 4,
            "vram_requirement": 750,
            "is_multilingual": True,
            "best_for": "realtime",
        },
        "tiny.en": {
            "speed": 10,
            "accuracy": 4,
            "vram_requirement": 750,
            "is_multilingual": False,
            "best_for": "english_realtime",
        },
        "distil-large-v3": {
            "speed": 7,
            "accuracy": 9,
            "vram_requirement": 6000,
            "is_multilingual": False,
            "best_for": "optimized_accuracy",
        },
        "distil-large-v2": {
            "speed": 7,
            "accuracy": 8,
            "vram_requirement": 6000,
            "is_multilingual": False,
            "best_for": "optimized",
        },
        "distil-medium.en": {
            "speed": 8,
            "accuracy": 7,
            "vram_requirement": 3000,
            "is_multilingual": False,
            "best_for": "optimized_fast",
        },
        "distil-small.en": {
            "speed": 9,
            "accuracy": 6,
            "vram_requirement": 1500,
            "is_multilingual": False,
            "best_for": "optimized_very_fast",
        },
    }

    def __init__(self):
        """Initialize the model selector."""
        self._hardware_detector = HardwareDetector()
        self._download_manager = get_model_download_manager()

    def get_recommendation(
        self,
        language: str = "en",
        prefer_speed: bool = False,
        prefer_accuracy: bool = False,
        vram_override_mb: Optional[int] = None,
    ) -> ModelRecommendation:
        """
        Get a model recommendation based on system and preferences.

        Parameters
        ----------
        language
            Primary language code ("auto" for multilingual).
        prefer_speed
            If True, prioritize faster models.
        prefer_accuracy
            If True, prioritize more accurate models.
        vram_override_mb
            Override detected VRAM for testing.

        Returns
        -------
        ModelRecommendation
            Recommended model with reasoning.
        """
        # Detect hardware
        hardware_info = self._hardware_detector.detect()

        # Use override if provided
        available_vram = vram_override_mb or (
            hardware_info.vram_free_mb or hardware_info.vram_total_mb
        )

        # Determine if user needs multilingual support
        needs_multilingual = language == "auto" or language not in ("en", "en-US", "en-GB")

        # Get suitable models
        suitable_models = self._get_suitable_models(
            has_cuda=hardware_info.has_cuda,
            vram_mb=available_vram,
            needs_multilingual=needs_multilingual,
            prefer_speed=prefer_speed,
            prefer_accuracy=prefer_accuracy,
        )

        if not suitable_models:
            # Fallback to smallest model
            suitable_models = ["tiny"]

        # Pick the best model
        recommended_model = suitable_models[0]

        # Get model characteristics
        chars = self.MODEL_CHARACTERISTICS.get(recommended_model, {})

        # Build recommendation
        model_info = self._download_manager.get_model_info(recommended_model)
        display_name = model_info.display_name if model_info else recommended_model

        # Generate reason
        reason = self._generate_reason(
            hardware_info,
            recommended_model,
            needs_multilingual,
            prefer_speed,
            prefer_accuracy,
        )

        # Get alternatives
        alternatives = suitable_models[1:4] if len(suitable_models) > 1 else []

        return ModelRecommendation(
            model_name=recommended_model,
            display_name=display_name,
            reason=reason,
            confidence=0.9,
            alternatives=alternatives,
            estimated_speed=chars.get("speed", 5),
            estimated_accuracy=chars.get("accuracy", 5),
        )

    def _get_suitable_models(
        self,
        has_cuda: bool,
        vram_mb: int,
        needs_multilingual: bool,
        prefer_speed: bool = False,
        prefer_accuracy: bool = False,
    ) -> List[str]:
        """
        Get list of suitable models sorted by preference.

        Parameters
        ----------
        has_cuda
            Whether CUDA GPU is available.
        vram_mb
            Available VRAM in MB (use RAM for CPU).
        vram_mb
            Available VRAM/RAM in MB.
        needs_multilingual
            Whether multilingual support is needed.
        prefer_speed
            Prioritize faster models.
        prefer_accuracy
            Prioritize more accurate models.

        Returns
        -------
        List[str]
            Sorted list of suitable model names.
        """
        suitable = []

        for model_name, chars in self.MODEL_CHARACTERISTICS.items():
            # Check multilingual requirement
            if needs_multilingual and not chars["is_multilingual"]:
                continue

            # Check VRAM requirement
            if has_cuda:
                required_vram = chars["vram_requirement"]
                if vram_mb < required_vram * 0.8:  # Allow some overhead
                    continue
            else:
                # CPU mode - all models work but larger ones are slow
                if vram_mb < chars["vram_requirement"] * 0.5:
                    continue

            suitable.append(model_name)

        # Sort by preference
        if prefer_accuracy:
            suitable.sort(key=lambda m: (
                -self.MODEL_CHARACTERISTICS[m]["accuracy"],
                self.MODEL_CHARACTERISTICS[m]["speed"],
            ))
        elif prefer_speed:
            suitable.sort(key=lambda m: (
                -self.MODEL_CHARACTERISTICS[m]["speed"],
                self.MODEL_CHARACTERISTICS[m]["accuracy"],
            ))
        else:
            # Balanced approach
            suitable.sort(key=lambda m: (
                -(self.MODEL_CHARACTERISTICS[m]["speed"] + self.MODEL_CHARACTERISTICS[m]["accuracy"]) / 2,
            ))

        return suitable

    def _generate_reason(
        self,
        hardware_info: HardwareInfo,
        model_name: str,
        needs_multilingual: bool,
        prefer_speed: bool,
        prefer_accuracy: bool,
    ) -> str:
        """Generate human-readable explanation for recommendation."""
        chars = self.MODEL_CHARACTERISTICS.get(model_name, {})

        parts = []

        if hardware_info.has_cuda:
            parts.append(f"GPU detected ({hardware_info.gpu_name})")
            if hardware_info.vram_total_mb:
                parts.append(f"with {hardware_info.vram_total_mb // 1024}GB VRAM")
        else:
            parts.append("CPU-only mode detected")

        if needs_multilingual:
            parts.append("multilingual support needed")
        else:
            parts.append("English-only optimization available")

        if prefer_speed:
            parts.append("speed prioritized")
        elif prefer_accuracy:
            parts.append("accuracy prioritized")
        else:
            parts.append("balanced configuration")

        # Add model-specific info
        best_for = chars.get("best_for", "general_use")
        parts.append(f"selected {model_name} for {best_for.replace('_', ' ')}")

        return ". ".join(p.capitalize() for p in parts) + "."

    def get_first_run_recommendation(self) -> ModelRecommendation:
        """
        Get recommendation for first-time users.

        This is a simpler recommendation that prioritizes reliability
        and ease of use over optimization.

        Returns
        -------
        ModelRecommendation
            Recommended model for first-time setup.
        """
        hardware_info = self._hardware_detector.detect()

        # For first run, prioritize reliability
        if hardware_info.has_cuda and hardware_info.vram_total_mb and hardware_info.vram_total_mb >= 6000:
            return ModelRecommendation(
                model_name="distil-large-v3",
                display_name="Distil Large v3",
                reason="Great balance of speed and accuracy for your GPU. Recommended for most users.",
                confidence=0.95,
                alternatives=["medium", "small"],
                estimated_speed=7,
                estimated_accuracy=9,
            )
        elif hardware_info.has_cuda:
            return ModelRecommendation(
                model_name="small",
                display_name="Small",
                reason="Optimized for your GPU. Fast and accurate for everyday use.",
                confidence=0.9,
                alternatives=["base", "medium"],
                estimated_speed=7,
                estimated_accuracy=7,
            )
        else:
            return ModelRecommendation(
                model_name="base",
                display_name="Base",
                reason="Good balance of speed and accuracy for CPU. Transcribes multilingual audio.",
                confidence=0.85,
                alternatives=["tiny", "small"],
                estimated_speed=8,
                estimated_accuracy=6,
            )


def get_model_selector() -> ModelSelector:
    """
    Get or create the singleton model selector.

    Returns
    -------
    ModelSelector
        The model selector instance.
    """
    if not hasattr(get_model_selector, "_instance"):
        get_model_selector._instance = ModelSelector()
    return get_model_selector._instance
