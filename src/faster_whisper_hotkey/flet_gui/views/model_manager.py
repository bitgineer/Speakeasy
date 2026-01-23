"""
Model management interface for faster-whisper-hotkey.

This module provides a modern UI for browsing, selecting, and managing
ASR models with installation status, download progress, and recommendations.

Classes
-------
ModelCard
    Data class for model card display information.

ModelManagerPanel
    Main model management interface with grid of model cards.
"""

import logging
from typing import Optional, List, Dict, Callable

import flet as ft

from ..hardware_detector import HardwareDetector, HardwareInfo, format_vram_size
from ..model_download import ModelDownloadManager, get_model_download_manager, ModelInfo, DownloadProgress

logger = logging.getLogger(__name__)


class ModelCard:
    """
    Model card display information.

    Attributes
    ----------
    model_info
        Information about the model.
    is_installed
        Whether the model is currently installed.
    is_recommended
        Whether this model is recommended for the user's system.
    download_progress
        Active download progress if downloading.
    """

    def __init__(
        self,
        model_info: ModelInfo,
        is_installed: bool = False,
        is_recommended: bool = False,
        download_progress: Optional[DownloadProgress] = None,
    ):
        self.model_info = model_info
        self.is_installed = is_installed
        self.is_recommended = is_recommended
        self.download_progress = download_progress


class ModelManagerPanel:
    """
    Model management interface with grid of model cards.

    This panel provides:
    - Grid layout showing all available models
    - Model cards with name, size, features, status
    - Download/install/update/remove buttons
    - Model detail view
    - Filter and sort options
    - "Recommended for your system" badges
    """

    # Filter options
    FILTER_ALL = "all"
    FILTER_INSTALLED = "installed"
    FILTER_AVAILABLE = "available"
    FILTER_RECOMMENDED = "recommended"
    FILTER_MULTILINGUAL = "multilingual"
    FILTER_ENGLISH_ONLY = "english_only"

    # Sort options
    SORT_NAME = "name"
    SORT_SIZE = "size"
    SORT_SPEED = "speed"

    def __init__(
        self,
        on_model_selected: Optional[Callable[[str], None]] = None,
        on_close: Optional[Callable[[], None]] = None,
    ):
        """
        Initialize the model manager panel.

        Parameters
        ----------
        on_model_selected
            Callback when a model is selected for use.
        on_close
            Callback when panel is closed.
        """
        self._on_model_selected = on_model_selected
        self._on_close = on_close

        # Services
        self._hardware_detector = HardwareDetector()
        self._download_manager = get_model_download_manager()

        # State
        self._hardware_info: Optional[HardwareInfo] = None
        self._model_cards: Dict[str, ModelCard] = {}
        self._current_filter = self.FILTER_ALL
        self._current_sort = self.SORT_NAME
        self._selected_model: Optional[str] = None

        # UI components
        self._grid: Optional[ft.GridView] = None
        self._filter_dropdown: Optional[ft.Dropdown] = None
        self._sort_dropdown: Optional[ft.Dropdown] = None
        self._hardware_status_text: Optional[ft.Text] = None
        self._detail_dialog: Optional[ft.AlertDialog] = None

        # Register download progress callback
        self._download_manager.register_progress_callback(self._on_download_progress)

    def build(self) -> ft.Container:
        """
        Build the model manager UI.

        Returns
        -------
        ft.Container
            The model manager container.
        """
        # Detect hardware
        self._hardware_info = self._hardware_detector.detect()

        # Build hardware status section
        hardware_section = self._build_hardware_section()

        # Build filter/sort controls
        controls_section = self._build_controls_section()

        # Build model grid
        self._grid = ft.GridView(
            runs_count=3,
            max_extent=300,
            spacing=16,
            run_spacing=16,
            child_aspect_ratio=1.0,
            expand=True,
        )

        # Populate grid with models
        self._refresh_model_grid()

        # Main layout
        content = ft.Column(
            [
                # Header
                ft.Row(
                    [
                        ft.Icon(ft.icons.MODEL_TRAINING, size=28, color=ft.colors.PRIMARY),
                        ft.Text(
                            "Model Manager",
                            size=22,
                            weight=ft.FontWeight.BOLD,
                            color=ft.colors.ON_SURFACE,
                        ),
                    ],
                    spacing=12,
                ),
                ft.Divider(height=20),

                # Hardware status
                hardware_section,
                ft.Divider(height=20),

                # Controls
                controls_section,
                ft.Divider(height=16),

                # Model grid
                ft.Container(
                    content=self._grid,
                    expand=True,
                ),
            ],
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

        return ft.Container(
            content=content,
            padding=ft.padding.all(24),
            expand=True,
        )

    def _build_hardware_section(self) -> ft.Container:
        """Build the hardware detection status section."""
        status_color = ft.colors.GREEN if self._hardware_info.has_cuda else ft.colors.AMBER

        gpu_status = (
            f"Detected: {self._hardware_info.gpu_name}"
            if self._hardware_info.has_cuda
            else "Not Detected (CPU only)"
        )

        recommended_text = (
            f"Device: {self._hardware_info.recommended_device.upper()}, "
            f"Compute: {self._hardware_info.recommended_compute_type}, "
            f"Model: {self._hardware_info.recommended_model}"
        )

        vram_text = ""
        if self._hardware_info.vram_total_mb:
            vram_text = f"VRAM: {format_vram_size(self._hardware_info.vram_total_mb)}"
            if self._hardware_info.vram_free_mb:
                vram_text += f" ({format_vram_size(self._hardware_info.vram_free_mb)} free)"

        self._hardware_status_text = ft.Text(
            f"{gpu_status}\n{recommended_text}\n{vram_text}\n{self._hardware_info.reason}",
            color=ft.colors.ON_SURFACE_VARIANT,
            size=12,
            max_lines=4,
        )

        section = ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Container(
                                width=12,
                                height=12,
                                border_radius=6,
                                bgcolor=status_color,
                            ),
                            ft.Text(
                                "Hardware Detection",
                                size=14,
                                weight=ft.FontWeight.MEDIUM,
                                color=ft.colors.ON_SURFACE,
                            ),
                        ],
                        spacing=8,
                    ),
                    self._hardware_status_text,
                ],
            ),
            padding=ft.padding.symmetric(horizontal=16, vertical=12),
            bgcolor=ft.colors.SURFACE_CONTAINER_LOW,
            border_radius=12,
        )

        return section

    def _build_controls_section(self) -> ft.Row:
        """Build filter and sort controls."""
        self._filter_dropdown = ft.Dropdown(
            label="Filter",
            options=[
                ft.dropdown_option(self.FILTER_ALL, "All Models"),
                ft.dropdown_option(self.FILTER_INSTALLED, "Installed"),
                ft.dropdown_option(self.FILTER_AVAILABLE, "Available"),
                ft.dropdown_option(self.FILTER_RECOMMENDED, "Recommended"),
                ft.dropdown_option(self.FILTER_MULTILINGUAL, "Multilingual"),
                ft.dropdown_option(self.FILTER_ENGLISH_ONLY, "English Only"),
            ],
            width=150,
            value=self.FILTER_ALL,
            on_change=self._on_filter_change,
        )

        self._sort_dropdown = ft.Dropdown(
            label="Sort",
            options=[
                ft.dropdown_option(self.SORT_NAME, "Name"),
                ft.dropdown_option(self.SORT_SIZE, "Size"),
                ft.dropdown_option(self.SORT_SPEED, "Speed"),
            ],
            width=120,
            value=self.SORT_NAME,
            on_change=self._on_sort_change,
        )

        return ft.Row(
            [
                self._filter_dropdown,
                self._sort_dropdown,
                ft.Container(expand=True),
                ft.IconButton(
                    icon=ft.icons.REFRESH,
                    tooltip="Refresh status",
                    on_click=self._on_refresh,
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

    def _refresh_model_grid(self) -> None:
        """Refresh the model grid with current filter/sort settings."""
        if not self._grid:
            return

        # Get all models
        all_models = self._download_manager.get_available_models()

        # Create model cards
        self._model_cards = {}
        for model_info in all_models:
            is_installed = self._download_manager.is_model_installed(model_info.name)
            is_recommended = (
                model_info.name == self._hardware_info.recommended_model
                if self._hardware_info
                else False
            )
            download_progress = self._download_manager.get_download_progress(model_info.name)

            self._model_cards[model_info.name] = ModelCard(
                model_info=model_info,
                is_installed=is_installed,
                is_recommended=is_recommended,
                download_progress=download_progress,
            )

        # Apply filters
        filtered_models = self._apply_filters(list(self._model_cards.values()))

        # Apply sorting
        sorted_models = self._apply_sorting(filtered_models)

        # Build UI cards
        self._grid.controls = [self._build_model_card(card) for card in sorted_models]

    def _apply_filters(self, cards: List[ModelCard]) -> List[ModelCard]:
        """Apply current filter to model cards."""
        if self._current_filter == self.FILTER_ALL:
            return cards
        elif self._current_filter == self.FILTER_INSTALLED:
            return [c for c in cards if c.is_installed]
        elif self._current_filter == self.FILTER_AVAILABLE:
            return [c for c in cards if not c.is_installed]
        elif self._current_filter == self.FILTER_RECOMMENDED:
            return [c for c in cards if c.is_recommended]
        elif self._current_filter == self.FILTER_MULTILINGUAL:
            return [c for c in cards if c.model_info.is_multilingual]
        elif self._current_filter == self.FILTER_ENGLISH_ONLY:
            return [c for c in cards if c.model_info.is_english_only]
        return cards

    def _apply_sorting(self, cards: List[ModelCard]) -> List[ModelCard]:
        """Apply current sorting to model cards."""
        if self._current_sort == self.SORT_NAME:
            return sorted(cards, key=lambda c: c.model_info.display_name)
        elif self._current_sort == self.SORT_SIZE:
            return sorted(cards, key=lambda c: c.model_info.size_mb)
        elif self._current_sort == self.SORT_SPEED:
            # Sort by size (smaller = faster)
            return sorted(cards, key=lambda c: c.model_info.size_mb)
        return cards

    def _build_model_card(self, card: ModelCard) -> ft.Container:
        """Build a UI card for a model."""
        # Status indicator
        status_badge = self._build_status_badge(card)

        # Recommendation badge
        recommend_badge = ft.Container() if not card.is_recommended else ft.Container(
            content=ft.Row(
                [
                    ft.Icon(ft.icons.STAR, size=14, color=ft.colors.AMBER),
                    ft.Text("Recommended", size=11, color=ft.colors.AMBER),
                ],
                spacing=4,
            ),
            padding=ft.padding.symmetric(horizontal=8, vertical=4),
            bgcolor=ft.colors.AMBER_CONTAINER,
            border_radius=12,
        )

        # Action button
        action_button = self._build_action_button(card)

        # Size display
        size_text = ft.Text(
            f"{card.model_info.size_mb} MB",
            size=12,
            color=ft.colors.ON_SURFACE_VARIANT,
        )

        # Memory requirement
        memory_text = ft.Text(
            f"~{card.model_info.memory_mb // 1024} GB RAM",
            size=11,
            color=ft.colors.ON_SURFACE_VARIANT,
        )

        # Features tags
        features_row = ft.Row(
            [
                ft.Container(
                    content=ft.Text(feature, size=10),
                    padding=ft.padding.symmetric(horizontal=6, vertical=2),
                    bgcolor=ft.colors.SURFACE_CONTAINER_HIGH,
                    border_radius=4,
                )
                for feature in card.model_info.features[:3]
            ],
            spacing=4,
            wrap=True,
        )

        # Main card content
        card_content = ft.Container(
            content=ft.Column(
                [
                    # Header with name and status
                    ft.Row(
                        [
                            ft.Text(
                                card.model_info.display_name,
                                size=16,
                                weight=ft.FontWeight.BOLD,
                                color=ft.colors.ON_SURFACE,
                                expand=True,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    recommend_badge,
                    ft.Divider(height=8),

                    # Description
                    ft.Text(
                        card.model_info.description,
                        size=12,
                        color=ft.colors.ON_SURFACE_VARIANT,
                        max_lines=2,
                        overflow=ft.TextOverflow.ELLIPSIS,
                    ),
                    ft.Divider(height=8),

                    # Stats
                    ft.Row(
                        [size_text, memory_text],
                        spacing=12,
                    ),
                    ft.Divider(height=8),

                    # Features
                    features_row,
                    ft.Divider(height=12),

                    # Status badge
                    status_badge,
                    ft.Divider(height=8),

                    # Action button
                    action_button,
                ],
                spacing=0,
                alignment=ft.CrossAxisAlignment.START,
            ),
            padding=ft.padding.all(16),
            bgcolor=ft.colors.SURFACE,
            border_radius=12,
            border=ft.border.all(1, ft.colors.OUTLINE_VARIANT),
        )

        # Make clickable for details
        return ft.GestureDetector(
            content=card_content,
            on_tap=lambda _, c=card: self._show_model_details(c),
        )

    def _build_status_badge(self, card: ModelCard) -> ft.Container:
        """Build status badge for a model card."""
        if card.download_progress and card.download_progress.status == "downloading":
            progress = card.download_progress
            return ft.Container(
                content=ft.Column(
                    [
                        ft.Text(
                            f"Downloading {progress.percentage:.0f}%",
                            size=12,
                            color=ft.colors.PRIMARY,
                        ),
                        ft.ProgressBar(
                            value=progress.percentage / 100,
                            bgcolor=ft.colors.SURFACE_CONTAINER_HIGH,
                            color=ft.colors.PRIMARY,
                        ),
                        ft.Text(
                            f"{progress.speed_formatted} - {progress.eta_formatted}",
                            size=10,
                            color=ft.colors.ON_SURFACE_VARIANT,
                        ),
                    ],
                    spacing=4,
                ),
            )
        elif card.download_progress and card.download_progress.status == "error":
            return ft.Container(
                content=ft.Text(
                    f"Error: {card.download_progress.error_message}",
                    size=11,
                    color=ft.colors.ERROR,
                ),
            )
        elif card.is_installed:
            return ft.Container(
                content=ft.Row(
                    [
                        ft.Icon(ft.icons.CHECK_CIRCLE, size=14, color=ft.colors.GREEN),
                        ft.Text("Installed", size=12, color=ft.colors.GREEN),
                    ],
                    spacing=4,
                ),
            )
        else:
            return ft.Container(
                content=ft.Row(
                    [
                        ft.Icon(ft.icons.DOWNLOAD, size=14, color=ft.colors.ON_SURFACE_VARIANT),
                        ft.Text("Not installed", size=12, color=ft.colors.ON_SURFACE_VARIANT),
                    ],
                    spacing=4,
                ),
            )

    def _build_action_button(self, card: ModelCard) -> ft.ElevatedButton:
        """Build action button for a model card."""
        if card.download_progress and card.download_progress.status == "downloading":
            return ft.ElevatedButton(
                "Cancel",
                icon=ft.icons.CANCEL,
                bgcolor=ft.colors.ERROR_CONTAINER,
                color=ft.colors.ERROR,
                on_click=lambda _, m=card.model_info.name: self._cancel_download(m),
            )
        elif card.is_installed:
            return ft.ElevatedButton(
                "Select",
                icon=ft.icons.CHECK,
                bgcolor=ft.colors.SUCCESS_CONTAINER,
                color=ft.colors.SUCCESS,
                on_click=lambda _, m=card.model_info.name: self._select_model(m),
            )
        else:
            return ft.ElevatedButton(
                "Install",
                icon=ft.icons.DOWNLOAD,
                bgcolor=ft.colors.PRIMARY,
                color=ft.colors.ON_PRIMARY,
                on_click=lambda _, m=card.model_info.name: self._download_model(m),
            )

    def _show_model_details(self, card: ModelCard) -> None:
        """Show detailed information about a model."""
        if not self._grid or not self._grid.page:
            return

        # Build details dialog
        model = card.model_info

        details = ft.Column(
            [
                ft.Text(model.display_name, size=20, weight=ft.FontWeight.BOLD),
                ft.Divider(height=16),

                ft.Text("Description", size=14, weight=ft.FontWeight.MEDIUM),
                ft.Text(model.description, size=13),

                ft.Divider(height=12),
                ft.Text("Specifications", size=14, weight=ft.FontWeight.MEDIUM),
                ft.Text(f"Download Size: {model.size_mb} MB ({model.size_mb / 1024:.1f} GB)"),
                ft.Text(f"Memory Requirement: ~{model.memory_mb // 1024} GB RAM"),
                ft.Text(f"Type: {'Multilingual' if model.is_multilingual else 'English-only'}"),
                ft.Text(f"Features: {', '.join(model.features)}"),

                ft.Divider(height=12),
                ft.Text("Language Support", size=14, weight=ft.FontWeight.MEDIUM),
                ft.Text(f"{len(model.languages)} languages supported" if model.languages else "Multilingual model"),

                ft.Divider(height=12),
                ft.Text("Recommended Hardware", size=14, weight=ft.FontWeight.MEDIUM),
                ft.Text(f"Minimum: {model.memory_mb // 1024} GB RAM"),
                ft.Text(f"Recommended: GPU with {model.memory_mb // 1024 + 2} GB VRAM" if model.memory_mb > 2000 else "Runs well on CPU"),
            ],
            spacing=4,
            horizontal_alignment=ft.CrossAxisAlignment.START,
        )

        dialog = ft.AlertDialog(
            title=ft.Row(
                [
                    ft.Icon(ft.icons.INFO, color=ft.colors.PRIMARY),
                    ft.Text("Model Details"),
                ],
                spacing=8,
            ),
            content=details,
            actions=[
                ft.TextButton("Close", on_click=lambda _: self._close_detail_dialog()),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self._detail_dialog = dialog
        self._grid.page.dialog = dialog
        dialog.open = True
        self._grid.page.update()

    def _close_detail_dialog(self) -> None:
        """Close the detail dialog."""
        if self._detail_dialog and self._grid and self._grid.page:
            self._detail_dialog.open = False
            self._grid.page.update()

    # Event handlers
    def _on_filter_change(self, e) -> None:
        """Handle filter change."""
        self._current_filter = self._filter_dropdown.value
        self._refresh_model_grid()
        if self._grid:
            self._grid.update()

    def _on_sort_change(self, e) -> None:
        """Handle sort change."""
        self._current_sort = self._sort_dropdown.value
        self._refresh_model_grid()
        if self._grid:
            self._grid.update()

    def _on_refresh(self, e) -> None:
        """Handle refresh button."""
        self._hardware_info = self._hardware_detector.detect()
        self._refresh_model_grid()
        if self._grid:
            self._grid.update()

    def _download_model(self, model_name: str) -> None:
        """Start downloading a model."""
        progress = self._download_manager.download_model(model_name)
        self._model_cards[model_name].download_progress = progress
        self._refresh_model_grid()
        if self._grid:
            self._grid.update()

    def _cancel_download(self, model_name: str) -> None:
        """Cancel a download."""
        self._download_manager.cancel_download(model_name)
        self._refresh_model_grid()
        if self._grid:
            self._grid.update()

    def _select_model(self, model_name: str) -> None:
        """Select a model for use."""
        if self._on_model_selected:
            self._on_model_selected(model_name)

    def _on_download_progress(self, progress: DownloadProgress) -> None:
        """Handle download progress updates."""
        if progress.model_name in self._model_cards:
            self._model_cards[progress.model_name].download_progress = progress
            # Refresh only if visible (to avoid excessive updates)
            if self._grid and progress.status == "downloading":
                self._refresh_model_grid()
                self._grid.update()
            elif progress.status in ("completed", "error"):
                self._refresh_model_grid()
                if self._grid:
                    self._grid.update()

    def destroy(self) -> None:
        """Clean up resources."""
        self._download_manager.unregister_progress_callback(self._on_download_progress)
