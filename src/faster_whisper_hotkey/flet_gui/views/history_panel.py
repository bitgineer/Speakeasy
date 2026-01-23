"""
History panel view for the Flet GUI.

This module provides the history viewer interface with search functionality,
item details, copy/paste operations, and export capabilities.
"""

import logging
from typing import Callable, Optional, List
from datetime import datetime

import flet as ft

from ..history_manager import HistoryManager, HistoryItem
from ..slash_search import SlashSearch
from ..app_state import AppState

logger = logging.getLogger(__name__)


class HistoryPanel:
    """
    History panel with searchable transcription history.

    This panel provides:
    - Search/command bar for filtering transcriptions
    - List view of history items with timestamps and previews
    - Detail view panel for selected items
    - Copy to clipboard functionality
    - Paste to active window button
    - Delete individual items with confirmation
    - Clear all history with safety confirmation
    - Export to JSON/TXT functionality
    - Statistics display

    Attributes
    ----------
    history_manager
        History storage and search service.
    app_state
        Shared application state.
    on_paste
        Callback when paste to active window is requested.
    """

    def __init__(
        self,
        history_manager: HistoryManager,
        app_state: AppState,
        on_paste: Optional[Callable[[str], None]] = None,
        on_close: Optional[Callable[[], None]] = None,
    ):
        """
        Initialize the history panel.

        Parameters
        ----------
        history_manager
            History management service.
        app_state
            Shared application state.
        on_paste
            Callback when paste to active window is requested.
        on_close
            Callback when close button is clicked.
        """
        self.history_manager = history_manager
        self.app_state = app_state
        self._on_paste = on_paste
        self._on_close = on_close

        # Search functionality
        self._slash_search = SlashSearch(history_manager)

        # UI components
        self._search_field: Optional[ft.TextField] = None
        self._history_list: Optional[ft.ListView] = None
        self._detail_panel: Optional[ft.Container] = None
        self._stats_text: Optional[ft.Text] = None
        self._selected_item: Optional[HistoryItem] = None
        self._current_items: List[HistoryItem] = []

        # Detail view components
        self._detail_text: Optional[ft.TextField] = None
        self._detail_timestamp: Optional[ft.Text] = None
        self._detail_model: Optional[ft.Text] = None
        self._detail_language: Optional[ft.Text] = None
        self._detail_device: Optional[ft.Text] = None
        self._detail_tags: Optional[ft.Row] = None  # Tags display row
        self._tag_input: Optional[ft.TextField] = None  # Tag input field

    def build(self) -> ft.Container:
        """
        Build the history panel UI.

        Returns
        -------
        ft.Container
            The history panel container.
        """
        # Search field
        self._search_field = ft.TextField(
            hint_text="Search history... (try /text:, /date:, /model:)",
            prefix_icon=ft.icons.SEARCH,
            suffix=ft.IconButton(
                icon=ft.icons.CLEAR,
                icon_size=16,
                tooltip="Clear search",
                on_click=self._on_clear_search,
            ),
            on_change=self._on_search_change,
            on_submit=self._on_search_submit,
            expand=True,
        )

        # Statistics text
        self._stats_text = ft.Text(
            "Loading...",
            color=ft.colors.ON_SURFACE_VARIANT,
            size=12,
        )

        # History list
        self._history_list = ft.ListView(
            expand=True,
            spacing=4,
            padding=ft.padding.all(8),
        )

        # Detail panel (hidden by default)
        self._detail_panel = self._build_detail_panel()

        # Main content area with split view
        main_content = ft.Row(
            [
                # Left side: list view
                ft.Container(
                    content=ft.Column(
                        [
                            # Search bar
                            ft.Container(
                                content=self._search_field,
                                padding=ft.padding.symmetric(horizontal=8, vertical=8),
                            ),
                            # Stats row
                            ft.Container(
                                content=ft.Row(
                                    [
                                        self._stats_text,
                                        ft.Container(expand=True),
                                        ft.TextButton(
                                            "Export",
                                            icon=ft.icons.DOWNLOAD,
                                            on_click=self._on_export_click,
                                        ),
                                        ft.TextButton(
                                            "Clear All",
                                            icon=ft.icons.DELETE_SWEEP,
                                            on_click=self._on_clear_all_click,
                                        ),
                                    ],
                                    spacing=8,
                                ),
                                padding=ft.padding.symmetric(horizontal=8, vertical=4),
                            ),
                            # History list
                            ft.Container(
                                content=self._history_list,
                                expand=True,
                                border=ft.border.all(1, ft.colors.OUTLINE_VARIANT),
                                border_radius=8,
                            ),
                        ],
                        spacing=0,
                        expand=True,
                    ),
                    expand=3,
                ),

                # Right side: detail view
                ft.Container(
                    content=self._detail_panel,
                    expand=2,
                    visible=False,
                ),
            ],
            expand=True,
            spacing=8,
        )

        # Build the panel layout
        panel = ft.Container(
            content=ft.Column(
                [
                    # Header
                    ft.Row(
                        [
                            ft.Icon(ft.icons.HISTORY, size=24, color=ft.colors.PRIMARY),
                            ft.Text(
                                "History",
                                size=20,
                                weight=ft.FontWeight.BOLD,
                                color=ft.colors.ON_SURFACE,
                            ),
                            ft.Container(expand=True),
                            ft.IconButton(
                                icon=ft.icons.ANALYTICS_OUTLINE,
                                tooltip="View statistics",
                                on_click=self._on_stats_click,
                            ),
                            ft.IconButton(
                                icon=ft.icons.HELP_OUTLINE,
                                tooltip="Search help",
                                on_click=self._on_help_click,
                            ),
                        ],
                        spacing=12,
                    ),
                    ft.Divider(height=20),

                    # Main content
                    main_content,
                ],
                spacing=12,
                horizontal_alignment=ft.CrossAxisAlignment.START,
            ),
            padding=ft.padding.all(24),
            expand=True,
        )

        # Load initial data
        self._load_history()
        self._update_stats()

        return panel

    def _build_detail_panel(self) -> ft.Container:
        """Build the detail view panel."""
        # Track edit mode
        self._edit_mode = False

        # Detail text area
        self._detail_text = ft.TextField(
            value="",
            multiline=True,
            min_lines=10,
            max_lines=15,
            read_only=True,
            border_color=ft.colors.OUTLINE,
            border_radius=8,
            bgcolor=ft.colors.SURFACE_CONTAINER_LOW,
        )

        # Edit button (hidden by default)
        self._edit_button = ft.IconButton(
            icon=ft.icons.EDIT_OUTLINE,
            tooltip="Edit transcription",
            on_click=self._on_edit_click,
        )

        # Save button (hidden by default)
        self._save_button = ft.IconButton(
            icon=ft.icons.SAVE,
            tooltip="Save changes",
            on_click=self._on_save_click,
            visible=False,
        )

        # Metadata labels
        self._detail_timestamp = ft.Text(
            "",
            color=ft.colors.ON_SURFACE_VARIANT,
            size=12,
        )
        self._detail_model = ft.Text(
            "",
            color=ft.colors.ON_SURFACE_VARIANT,
            size=12,
        )
        self._detail_language = ft.Text(
            "",
            color=ft.colors.ON_SURFACE_VARIANT,
            size=12,
        )
        self._detail_device = ft.Text(
            "",
            color=ft.colors.ON_SURFACE_VARIANT,
            size=12,
        )

        # Tags display row
        self._detail_tags = ft.Row(
            [],
            spacing=4,
            wrap=True,
        )

        # Tag management section
        self._tag_input = ft.TextField(
            hint_text="Add a tag...",
            width=150,
            height=36,
            text_size=11,
            visible=False,
        )

        self._add_tag_button = ft.IconButton(
            icon=ft.icons.ADD,
            tooltip="Add tag",
            icon_size=16,
            on_click=self._on_add_tag_click,
            visible=False,
        )

        return ft.Container(
            content=ft.Column(
                [
                    # Detail header
                    ft.Row(
                        [
                            ft.Text(
                                "Details",
                                size=16,
                                weight=ft.FontWeight.MEDIUM,
                                color=ft.colors.ON_SURFACE,
                            ),
                            ft.Container(expand=True),
                            self._edit_button,
                            self._save_button,
                            ft.IconButton(
                                icon=ft.icons.CLOSE,
                                tooltip="Close details",
                                on_click=self._on_close_detail,
                            ),
                        ],
                    ),
                    ft.Divider(height=10),

                    # Metadata section
                    ft.Column(
                        [
                            ft.Text(
                                "Metadata",
                                size=12,
                                weight=ft.FontWeight.MEDIUM,
                                color=ft.colors.ON_SURFACE_VARIANT,
                            ),
                            self._detail_timestamp,
                            self._detail_model,
                            self._detail_language,
                            self._detail_device,
                        ],
                        spacing=4,
                    ),
                    ft.Divider(height=15),

                    # Tags section
                    ft.Column(
                        [
                            ft.Row(
                                [
                                    ft.Text(
                                        "Tags",
                                        size=12,
                                        weight=ft.FontWeight.MEDIUM,
                                        color=ft.colors.ON_SURFACE_VARIANT,
                                    ),
                                    ft.Container(expand=True),
                                    ft.IconButton(
                                        icon=ft.icons.EDIT_OUTLINE,
                                        tooltip="Manage tags",
                                        icon_size=16,
                                        on_click=self._on_toggle_tag_edit,
                                    ),
                                ],
                            ),
                            self._detail_tags,
                            ft.Row(
                                [
                                    self._tag_input,
                                    self._add_tag_button,
                                ],
                                visible=False,
                            ),
                        ],
                        spacing=4,
                    ),
                    ft.Divider(height=15),

                    # Text section
                    ft.Text(
                        "Transcription",
                        size=12,
                        weight=ft.FontWeight.MEDIUM,
                        color=ft.colors.ON_SURFACE_VARIANT,
                    ),
                    self._detail_text,

                    ft.Divider(height=20),

                    # Action buttons
                    ft.Column(
                        [
                            ft.ElevatedButton(
                                "Copy to Clipboard",
                                icon=ft.icons.COPY,
                                on_click=self._on_copy_click,
                                style=ft.ButtonStyle(
                                    bgcolor=ft.colors.PRIMARY,
                                    color=ft.colors.ON_PRIMARY,
                                ),
                                width=200,
                            ),
                            ft.ElevatedButton(
                                "Paste to Window",
                                icon=ft.icons.CONTENT_PASTE,
                                on_click=self._on_paste_click,
                                style=ft.ButtonStyle(
                                    bgcolor=ft.colors.SECONDARY_CONTAINER,
                                    color=ft.colors.ON_SECONDARY_CONTAINER,
                                ),
                                width=200,
                            ),
                            ft.ElevatedButton(
                                "Delete",
                                icon=ft.icons.DELETE,
                                on_click=self._on_delete_click,
                                style=ft.ButtonStyle(
                                    bgcolor=ft.colors.ERROR_CONTAINER,
                                    color=ft.colors.ON_ERROR_CONTAINER,
                                ),
                                width=200,
                            ),
                        ],
                        spacing=8,
                        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                    ),
                ],
                spacing=8,
                expand=True,
            ),
            padding=ft.padding.all(16),
            border=ft.border.all(1, ft.colors.OUTLINE_VARIANT),
            border_radius=8,
            bgcolor=ft.colors.SURFACE_CONTAINER_LOW,
        )

    def _load_history(self, items: Optional[List[HistoryItem]] = None):
        """
        Load history items into the list view.

        Parameters
        ----------
        items
            Optional list of items to display. If None, loads all items.
        """
        if items is not None:
            self._current_items = items
        else:
            self._current_items = self.history_manager.get_all(limit=100)

        self._refresh_list()

    def _refresh_list(self):
        """Refresh the list view with current items."""
        if not self._history_list:
            return

        self._history_list.controls.clear()

        if not self._current_items:
            self._history_list.controls.append(
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Icon(ft.icons.SEARCH_OFF, size=48, color=ft.colors.ON_SURFACE_VARIANT),
                            ft.Text(
                                "No history found",
                                color=ft.colors.ON_SURFACE_VARIANT,
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=8,
                    ),
                    padding=ft.padding.all(40),
                    alignment=ft.alignment.center,
                )
            )
        else:
            for item in self._current_items:
                self._history_list.controls.append(
                    self._create_history_item_card(item)
                )

        if self._history_list.page:
            self._history_list.update()

    def _create_history_item_card(self, item: HistoryItem) -> ft.Container:
        """
        Create a card widget for a history item.

        Parameters
        ----------
        item
            The history item to create a card for.

        Returns
        -------
        ft.Container
            A card container for the history item.
        """
        # Format timestamp
        try:
            dt = datetime.fromisoformat(item.timestamp)
            time_str = dt.strftime("%Y-%m-%d %H:%M")
        except (ValueError, TypeError):
            time_str = item.timestamp[:16] if item.timestamp else "Unknown"

        # Create preview text (truncate if too long)
        preview = item.text[:80] + "..." if len(item.text) > 80 else item.text

        # Model badge
        model_badge = None
        if item.model:
            model_badge = ft.Container(
                content=ft.Text(
                    item.model[:10],
                    size=10,
                    color=ft.colors.ON_PRIMARY_CONTAINER,
                ),
                bgcolor=ft.colors.PRIMARY_CONTAINER,
                padding=ft.padding.symmetric(horizontal=6, vertical=2),
                border_radius=4,
            )

        # Language badge
        lang_badge = None
        if item.language:
            lang_badge = ft.Container(
                content=ft.Text(
                    item.language.upper(),
                    size=10,
                    color=ft.colors.ON_SECONDARY_CONTAINER,
                ),
                bgcolor=ft.colors.SECONDARY_CONTAINER,
                padding=ft.padding.symmetric(horizontal=6, vertical=2),
                border_radius=4,
            )

        # Main card
        card = ft.Container(
            content=ft.Column(
                [
                    # Header row
                    ft.Row(
                        [
                            ft.Text(
                                time_str,
                                size=11,
                                color=ft.colors.ON_SURFACE_VARIANT,
                                weight=ft.FontWeight.MEDIUM,
                            ),
                            ft.Container(expand=True),
                            *(model_badge.controls if model_badge else []),
                            *(lang_badge.controls if lang_badge else []),
                        ],
                    ),
                    # Preview text
                    ft.Text(
                        preview,
                        size=13,
                        color=ft.colors.ON_SURFACE,
                        max_lines=2,
                        overflow=ft.TextOverflow.ELLIPSIS,
                    ),
                ],
                spacing=4,
            ),
            padding=ft.padding.all(12),
            bgcolor=ft.colors.SURFACE_CONTAINER_LOW,
            border_radius=8,
            border=ft.border.all(1, ft.colors.OUTLINE_VARIANT),
            on_click=lambda e, i=item: self._on_item_click(i),
        )

        return card

    def _update_stats(self):
        """Update the statistics display."""
        if not self._stats_text:
            return

        stats = self.history_manager.get_statistics()
        total = stats.get("total_items", 0)
        today = stats.get("today_count", 0)

        if self.history_manager.privacy_mode:
            self._stats_text.value = "Privacy mode enabled - no history saved"
        else:
            self._stats_text.value = f"{total} total items • {today} today"

        if self._stats_text.page:
            self._stats_text.update()

    def _on_item_click(self, item: HistoryItem):
        """
        Handle clicking on a history item.

        Parameters
        ----------
        item
            The history item that was clicked.
        """
        self._selected_item = item
        self._show_detail_panel(item)

    def _show_detail_panel(self, item: HistoryItem):
        """
        Show the detail panel for an item.

        Parameters
        ----------
        item
            The history item to show details for.
        """
        # Update detail fields
        self._detail_text.value = item.text

        # Format timestamp
        try:
            dt = datetime.fromisoformat(item.timestamp)
            self._detail_timestamp.value = f"Created: {dt.strftime('%Y-%m-%d at %H:%M:%S')}"
        except (ValueError, TypeError):
            self._detail_timestamp.value = f"Created: {item.timestamp}"

        # Model info
        if item.model:
            self._detail_model.value = f"Model: {item.model}"
        else:
            self._detail_model.value = "Model: Unknown"

        # Language info
        if item.language:
            self._detail_language.value = f"Language: {item.language.upper()}"
        else:
            self._detail_language.value = "Language: Unknown"

        # Device info
        if item.device:
            self._detail_device.value = f"Device: {item.device.upper()}"
        else:
            self._detail_device.value = "Device: Unknown"

        # Update tags display
        self._update_tags_display(item.tags or [])

        # Reset tag edit mode
        self._tag_input.visible = False
        self._add_tag_button.visible = False
        if self._tag_input.page:
            self._tag_input.update()
            self._add_tag_button.update()

        # Make detail panel visible
        if self._detail_panel:
            self._detail_panel.visible = True

        # Update UI
        if self._detail_panel.page:
            self._detail_panel.update()
            if self._detail_text.page:
                self._detail_text.update()
            self._detail_timestamp.update()
            self._detail_model.update()
            self._detail_language.update()
            self._detail_device.update()
            self._detail_tags.update()

    def _on_close_detail(self, e):
        """Close the detail panel."""
        # Exit edit mode if active
        if self._edit_mode:
            self._exit_edit_mode()

        if self._detail_panel:
            self._detail_panel.visible = False
            if self._detail_panel.page:
                self._detail_panel.update()
        self._selected_item = None

    def _on_search_change(self, e):
        """
        Handle search field changes.

        Parameters
        ----------
        e
            The change event.
        """
        # Debounce search - don't search on every keystroke
        # Search is triggered on submit or after a delay
        pass

    def _on_search_submit(self, e):
        """
        Handle search field submission.

        Parameters
        ----------
        e
            The submit event.
        """
        if not self._search_field:
            return

        query = self._search_field.value.strip()

        if not query:
            # Show all items
            self._load_history()
        else:
            # Perform search
            results = self._slash_search.search(query)
            self._current_items = [r.item for r in results]
            self._refresh_list()

        # Update stats to show result count
        if self._stats_text:
            if query:
                self._stats_text.value = f"{len(self._current_items)} results for '{query}'"
            else:
                self._update_stats()

            if self._stats_text.page:
                self._stats_text.update()

    def _on_clear_search(self, e):
        """Clear the search field and show all items."""
        if self._search_field:
            self._search_field.value = ""
            if self._search_field.page:
                self._search_field.update()
        self._load_history()
        self._update_stats()

    def _on_copy_click(self, e):
        """Handle copy button click."""
        if self._selected_item and self._detail_text:
            text = self._selected_item.text
            if self._detail_text.page:
                self._detail_text.page.set_clipboard(text)
                self._show_snackbar("Copied to clipboard")

    def _on_paste_click(self, e):
        """Handle paste button click."""
        if self._selected_item and self._on_paste:
            self._on_paste(self._selected_item.text)
            self._show_snackbar("Paste triggered")

    def _on_delete_click(self, e):
        """Handle delete button click."""
        if not self._selected_item:
            return

        # Show confirmation dialog
        if self._detail_text and self._detail_text.page:
            page = self._detail_text.page

            def confirm_delete(e):
                if self._selected_item and self._selected_item.id:
                    if self.history_manager.delete_item(self._selected_item.id):
                        self._show_snackbar("Item deleted")
                        # Remove from current items
                        self._current_items = [
                            item for item in self._current_items
                            if item.id != self._selected_item.id
                        ]
                        self._refresh_list()
                        self._update_stats()
                        self._on_close_detail(None)
                    else:
                        self._show_snackbar("Failed to delete item")
                page.close(dialog)

            def cancel_dialog(e):
                page.close(dialog)

            dialog = ft.AlertDialog(
                title=ft.Text("Delete Item"),
                content=ft.Text("Are you sure you want to delete this transcription?"),
                actions=[
                    ft.TextButton("Cancel", on_click=cancel_dialog),
                    ft.TextButton("Delete", on_click=confirm_delete),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )

            page.dialog = dialog
            dialog.open = True
            page.update()

    def _on_clear_all_click(self, e):
        """Handle clear all history button click."""
        # Show confirmation dialog
        if self._search_field and self._search_field.page:
            page = self._search_field.page

            def confirm_clear(e):
                if self.history_manager.clear_all():
                    self._show_snackbar("History cleared")
                    self._load_history()
                    self._update_stats()
                    self._on_close_detail(None)
                else:
                    self._show_snackbar("Failed to clear history")
                page.close(dialog)

            def cancel_dialog(e):
                page.close(dialog)

            dialog = ft.AlertDialog(
                title=ft.Text("Clear All History"),
                content=ft.Text("Are you sure you want to delete ALL transcription history? This cannot be undone."),
                actions=[
                    ft.TextButton("Cancel", on_click=cancel_dialog),
                    ft.TextButton("Clear All", on_click=confirm_clear),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )

            page.dialog = dialog
            dialog.open = True
            page.update()

    def _on_export_click(self, e):
        """Handle export button click."""
        if not self._search_field or not self._search_field.page:
            return

        page = self._search_field.page

        # Simple format selection
        def export_json(e):
            if self.history_manager.export_to_json():
                self._show_snackbar("Exported to JSON")
            else:
                self._show_snackbar("Export failed")
            page.close(format_dialog)

        def export_txt(e):
            # For TXT export, we'd need a file picker - just use default for now
            from ..history_manager import LEGACY_HISTORY_FILE
            txt_path = LEGACY_HISTORY_FILE.replace('.json', '.txt')
            if self.history_manager.export_to_txt(txt_path):
                self._show_snackbar(f"Exported to {txt_path}")
            else:
                self._show_snackbar("Export failed")
            page.close(format_dialog)

        def cancel_dialog(e):
            page.close(format_dialog)

        format_dialog = ft.AlertDialog(
            title=ft.Text("Export History"),
            content=ft.Text("Choose export format:"),
            actions=[
                ft.TextButton("Cancel", on_click=cancel_dialog),
                ft.TextButton("JSON", on_click=export_json),
                ft.TextButton("Text", on_click=export_txt),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        page.dialog = format_dialog
        format_dialog.open = True
        page.update()

    def _on_help_click(self, e):
        """Show search help dialog."""
        if not self._search_field or not self._search_field.page:
            return

        page = self._search_field.page

        commands = self._slash_search.get_quick_commands()

        command_list = ft.Column(
            [
                ft.Text(
                    cmd["example"],
                    weight=ft.FontWeight.MEDIUM,
                    color=ft.colors.PRIMARY,
                )
                for cmd in commands
            ],
            spacing=8,
        )

        description_list = ft.Column(
            [ft.Text(cmd["description"], size=12) for cmd in commands],
            spacing=8,
        )

        def close_help(e):
            page.close(dialog)

        dialog = ft.AlertDialog(
            title=ft.Text("Search Commands"),
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Text(
                            "Use slash commands to filter your history:",
                            size=12,
                            weight=ft.FontWeight.MEDIUM,
                        ),
                        ft.Divider(height=10),
                        ft.Row([command_list, description_list], spacing=16, expand=True),
                    ],
                    spacing=4,
                ),
                width=500,
            ),
            actions=[
                ft.TextButton("Close", on_click=close_help),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        page.dialog = dialog
        dialog.open = True
        page.update()

    def _show_snackbar(self, message: str):
        """Show a snackbar message."""
        if self._search_field and self._search_field.page:
            self._search_field.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text(message),
                    duration=2000,
                )
            )

    def _on_stats_click(self, e):
        """Show statistics dialog with detailed history statistics."""
        if not self._search_field or not self._search_field.page:
            return

        page = self._search_field.page
        stats = self.history_manager.get_statistics()

        # Build statistics content
        total_items = stats.get("total_items", 0)
        today_count = stats.get("today_count", 0)
        week_count = stats.get("week_count", 0)
        most_used_model = stats.get("most_used_model", "N/A")
        most_used_language = stats.get("most_used_language", "N/A")
        oldest_item = stats.get("oldest_item", "N/A")
        newest_item = stats.get("newest_item", "N/A")

        # Format dates
        def format_date(date_str):
            if not date_str or date_str == "N/A":
                return "N/A"
            try:
                dt = datetime.fromisoformat(date_str)
                return dt.strftime("%Y-%m-%d")
            except (ValueError, TypeError):
                return date_str[:10] if len(date_str) >= 10 else date_str

        # Create stats rows
        stats_rows = [
            ft.DataRow(
                [
                    ft.DataCell(ft.Text("Total Items", weight=ft.FontWeight.BOLD)),
                    ft.DataCell(ft.Text(str(total_items), size=14)),
                ]
            ),
            ft.DataRow(
                [
                    ft.DataCell(ft.Text("Today", weight=ft.FontWeight.BOLD)),
                    ft.DataCell(ft.Text(str(today_count), size=14)),
                ]
            ),
            ft.DataRow(
                [
                    ft.DataCell(ft.Text("This Week", weight=ft.FontWeight.BOLD)),
                    ft.DataCell(ft.Text(str(week_count), size=14)),
                ]
            ),
            ft.DataRow(
                [
                    ft.DataCell(ft.Text("Most Used Model", weight=ft.FontWeight.BOLD)),
                    ft.DataCell(ft.Text(most_used_model, size=14)),
                ]
            ),
            ft.DataRow(
                [
                    ft.DataCell(ft.Text("Most Used Language", weight=ft.FontWeight.BOLD)),
                    ft.DataCell(ft.Text(most_used_language.upper() if most_used_language != "N/A" else "N/A", size=14)),
                ]
            ),
            ft.DataRow(
                [
                    ft.DataCell(ft.Text("Oldest Entry", weight=ft.FontWeight.BOLD)),
                    ft.DataCell(ft.Text(format_date(oldest_item), size=14)),
                ]
            ),
            ft.DataRow(
                [
                    ft.DataCell(ft.Text("Newest Entry", weight=ft.FontWeight.BOLD)),
                    ft.DataCell(ft.Text(format_date(newest_item), size=14)),
                ]
            ),
        ]

        def close_stats(e):
            page.close(dialog)

        dialog = ft.AlertDialog(
            title=ft.Row(
                [
                    ft.Icon(ft.icons.ANALYTICS, color=ft.colors.PRIMARY),
                    ft.Text("History Statistics", size=18),
                ],
                spacing=8,
            ),
            content=ft.Container(
                content=ft.DataTable(
                    columns=[
                        ft.DataColumn(ft.Text("Metric", size=12, weight=ft.FontWeight.BOLD)),
                        ft.DataColumn(ft.Text("Value", size=12, weight=ft.FontWeight.BOLD)),
                    ],
                    rows=stats_rows,
                    border=ft.border.all(1, ft.colors.OUTLINE_VARIANT),
                    border_radius=8,
                    horizontal_lines=ft.border.BorderSide(1, ft.colors.OUTLINE_VARIANT),
                    data_row_color=ft.colors.SURFACE_CONTAINER_LOW,
                ),
                width=350,
                padding=ft.padding.all(10),
            ),
            actions=[
                ft.TextButton("Close", on_click=close_stats),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        page.dialog = dialog
        dialog.open = True
        page.update()

    def _on_edit_click(self, e):
        """Handle edit button click - enable edit mode."""
        if not self._selected_item:
            return

        self._edit_mode = True

        # Enable editing on the text field
        self._detail_text.read_only = False
        self._detail_text.border_color = ft.colors.PRIMARY
        self._detail_text.bgcolor = ft.colors.SURFACE

        # Toggle button visibility
        self._edit_button.visible = False
        self._save_button.visible = True

        # Update UI
        if self._detail_text.page:
            self._detail_text.update()
            self._edit_button.update()
            self._save_button.update()

        # Focus the text field
        if self._detail_text.page:
            self._detail_text.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text("Edit mode enabled - make your changes and click Save"),
                    duration=3000,
                )
            )

    def _on_save_click(self, e):
        """Handle save button click - save edited text."""
        if not self._selected_item or not self._selected_item.id:
            return

        new_text = self._detail_text.value

        # Update the history item
        self._selected_item.text = new_text
        self._selected_item.edited = True

        if self.history_manager.update_item(self._selected_item.id, self._selected_item):
            self._show_snackbar("Changes saved successfully")

            # Update the list item preview
            for control in self._history_list.controls:
                if hasattr(control, 'content') and hasattr(control.content, 'controls'):
                    # This is a card, find the text control
                    for inner_control in control.content.controls:
                        if isinstance(inner_control, ft.Column):
                            for col_control in inner_control.controls:
                                if isinstance(col_control, ft.Text) and len(col_control.value) > 20:
                                    # This is likely the preview text
                                    preview = new_text[:80] + "..." if len(new_text) > 80 else new_text
                                    col_control.value = preview
                                    col_control.update()
        else:
            self._show_snackbar("Failed to save changes")

        # Exit edit mode
        self._exit_edit_mode()

        # Refresh the list
        self._refresh_list()

    def _exit_edit_mode(self):
        """Exit edit mode and return to view mode."""
        self._edit_mode = False

        # Disable editing on the text field
        self._detail_text.read_only = True
        self._detail_text.border_color = ft.colors.OUTLINE
        self._detail_text.bgcolor = ft.colors.SURFACE_CONTAINER_LOW

        # Toggle button visibility
        self._edit_button.visible = True
        self._save_button.visible = False

        # Update UI
        if self._detail_text.page:
            self._detail_text.update()
            self._edit_button.update()
            self._save_button.update()

    def _update_tags_display(self, tags: List[str]):
        """Update the tags display chips."""
        self._detail_tags.controls.clear()

        if not tags:
            # Show "No tags" message
            self._detail_tags.controls.append(
                ft.Text(
                    "No tags",
                    color=ft.colors.ON_SURFACE_VARIANT,
                    size=11,
                    italic=True,
                )
            )
        else:
            # Create a chip for each tag
            for tag in tags:
                chip = ft.Container(
                    content=ft.Row(
                        [
                            ft.Text(tag, size=11, color=ft.colors.ON_PRIMARY_CONTAINER),
                            ft.IconButton(
                                icon=ft.icons.CLOSE,
                                icon_size=12,
                                tooltip="Remove tag",
                                on_click=lambda e, t=tag: self._on_remove_tag_click(t),
                            ),
                        ],
                        spacing=4,
                    ),
                    bgcolor=ft.colors.PRIMARY_CONTAINER,
                    padding=ft.padding.symmetric(horizontal=8, vertical=4),
                    border_radius=12,
                )
                self._detail_tags.controls.append(chip)

        if self._detail_tags.page:
            self._detail_tags.update()

    def _on_toggle_tag_edit(self, e):
        """Toggle tag edit mode."""
        is_visible = self._tag_input.visible
        self._tag_input.visible = not is_visible
        self._add_tag_button.visible = not is_visible

        if self._tag_input.page:
            self._tag_input.update()
            self._add_tag_button.update()

    def _on_add_tag_click(self, e):
        """Add a new tag to the current item."""
        if not self._selected_item:
            return

        new_tag = self._tag_input.value.strip().lower()
        if not new_tag:
            return

        # Check if tag already exists
        if self._selected_item.tags and new_tag in self._selected_item.tags:
            self._show_snackbar(f"Tag '{new_tag}' already exists")
            return

        # Add the tag
        if not self._selected_item.tags:
            self._selected_item.tags = []
        self._selected_item.tags.append(new_tag)

        # Save to database
        if self.history_manager.update_item(self._selected_item.id, self._selected_item):
            self._update_tags_display(self._selected_item.tags)
            self._tag_input.value = ""
            if self._tag_input.page:
                self._tag_input.update()
            self._show_snackbar(f"Tag '{new_tag}' added")
        else:
            self._show_snackbar("Failed to add tag")

    def _on_remove_tag_click(self, tag: str):
        """Remove a tag from the current item."""
        if not self._selected_item or not self._selected_item.tags:
            return

        # Remove the tag
        if tag in self._selected_item.tags:
            self._selected_item.tags.remove(tag)

            # Save to database
            if self.history_manager.update_item(self._selected_item.id, self._selected_item):
                self._update_tags_display(self._selected_item.tags)
                self._show_snackbar(f"Tag '{tag}' removed")
            else:
                self._show_snackbar("Failed to remove tag")

    # Public properties for accessing UI components
    @property
    def search_field(self) -> Optional[ft.TextField]:
        """Get the search field for external focus control."""
        return self._search_field

    def refresh(self):
        """Refresh the history display."""
        self._load_history()
        self._update_stats()
